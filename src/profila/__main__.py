"""
Run Profila as a command-line tool.
"""

from argparse import ArgumentParser, REMAINDER, RawDescriptionHelpFormatter, Namespace
import asyncio
from asyncio.subprocess import Process
from dataclasses import asdict
import json
import os
from platform import machine
import subprocess
import sys
import tarfile
from tempfile import TemporaryFile
from urllib.request import urlopen

from ._gdb import (
    run_subprocess,
    read_samples,
    attach_subprocess,
    exit_subprocess,
    GDB_PATH,
)
from ._stats import Stats
from ._render import render_text

PARSER = ArgumentParser(prog="profila", description="A profiler for Numba.")
SUBPARSERS = PARSER.add_subparsers()
ANNOTATE_PARSER = SUBPARSERS.add_parser(
    "annotate",
    help="Run a Python program and annotate the Numba source code.",
    formatter_class=RawDescriptionHelpFormatter,
    description="""To profile "python example.py":

    python -m profila annotate -- example.py

To profile "python -m yourpackage --arg=123":

    python -m profila annotate -m -- yourpackage --arg=123
""",
)
ANNOTATE_PARSER.add_argument(
    "rest",
    nargs=REMAINDER,
    help="The arguments you'd usually pass to the Python command-line.",
)
ANNOTATE_PARSER.set_defaults(command="annotate")
ATTACH_AUTOMATED_PARSER = SUBPARSERS.add_parser(
    "attach_automated",
    help="Attach to an existing process, for use by the Jupyter extension.",
)
ATTACH_AUTOMATED_PARSER.add_argument(
    "pid",
    action="store",
    help="The process PID.",
)
ATTACH_AUTOMATED_PARSER.set_defaults(command="attach_automated")

# Hopefully can go away someday...
SETUP_PARSER = SUBPARSERS.add_parser(
    "setup",
    help="Download some files profila needs to run.",
    formatter_class=RawDescriptionHelpFormatter,
)
SETUP_PARSER.set_defaults(command="setup")
SETUP_PARSER.add_argument(
    "--yes",
    default=False,
    action="store_true",
    help="Download dependencies automatically, without asking permission.",
)


async def get_stats(process: Process) -> Stats:
    stats = Stats()

    count = 0
    async for sample in read_samples(process):
        count += 1
        stats.add_sample(sample)
    assert stats.total_samples() == count

    return stats


def annotate_command(args: Namespace) -> None:
    """
    Run the ``anotate`` command.
    """
    if args.rest and args.rest[0] == "--":
        del args.rest[0]

    if not os.path.exists(GDB_PATH):
        raise SystemExit(
            "Profila's custom gdb not found, make sure it is installed by running "
            "'python -m profila setup'."
        )

    async def main() -> Stats:
        process = await run_subprocess(args.rest)
        return await get_stats(process)

    stats = asyncio.run(main())
    final_stats = stats.finalize()
    print(render_text(final_stats))


def attach_automated_command(args: Namespace) -> None:
    """
    Run the ``attach_automated`` command.

    The other side of this logic is in the ``_ipython.py`` module.
    """

    async def stop_on_stdin_close(process: Process) -> None:
        loop = asyncio.get_event_loop()
        # The Jupyter side will signal it's finished running code by closing
        # stdin.
        await loop.run_in_executor(None, sys.stdin.read)
        await exit_subprocess(process)

    async def main() -> Stats:
        process = await attach_subprocess(args.pid)
        asyncio.create_task(stop_on_stdin_close(process))
        # Tell the Jupyter side it can start running code:
        sys.stdout.write(json.dumps({"message": "attached"}) + "\n")
        sys.stdout.flush()
        return await get_stats(process)

    final_stats = asyncio.run(main()).finalize()
    # The source code is only available inside the Jupyter process (it's cells,
    # not files on the filesystem), so do the source code loading over there.
    sys.stdout.write(
        json.dumps({"message": "stats", "stats": asdict(final_stats)}) + "\n"
    )
    sys.stdout.flush()


STORAGE_PATH = os.path.expanduser("~/.profila-gdb/")
MICROMAMBA_PATH = os.path.join(STORAGE_PATH, "bin/micromamba")


def setup_command(args: Namespace) -> None:
    """
    Run the ``setup`` command.

    Download micromamba, then use micromamba to install gdb v12, that is known
    to work with Numba.

    See https://github.com/numba/numba/issues/9817
    """
    if os.path.exists(GDB_PATH):
        print(
            "Profila's gdb is already downloaded, exiting. "
            "If you think the download is corrupted, delete ~/.profila-gdb "
            "and try again."
        )
        return

    if not args.yes:
        print(
            "In order for Profila to work, it needs to download gdb v12, "
            "since newer versions have some issues with Numba. This will "
            "NOT interfere or break any existing gdb install, it will only be "
            "used for Profila."
        )
        result = input("Download gdb v12? It's about 100MB to download [Y/n] ")
        if result.lower().strip() not in ("y", ""):
            print("OK, not downloading.")
            return

    architecture = machine()
    if architecture == "x86_64":
        microconda_url = "https://micro.mamba.pm/api/micromamba/linux-64/latest"
    elif architecture == "arm64":
        microconda_url = "https://micro.mamba.pm/api/micromamba/linux-aarch64/latest"
    else:
        raise SystemExit("Unsupported CPU architecture")

    if not os.path.exists(MICROMAMBA_PATH):
        with TemporaryFile("rb+") as f:
            f.write(urlopen(microconda_url).read())
            f.seek(0, 0)
            os.makedirs(STORAGE_PATH)
            tarfile.open(fileobj=f).extract("bin/micromamba", STORAGE_PATH)
    os.chmod(MICROMAMBA_PATH, 0o775)
    env = os.environ.copy()
    # Ensure existing Conda environment doesn't break things:
    for key in list(env.keys()):
        if key.startswith("CONDA_") or key.startswith("MAMBA_"):
            env.pop(key)
    env["MAMBA_ROOT_PREFIX"] = STORAGE_PATH
    subprocess.check_call(
        [
            MICROMAMBA_PATH,
            "install",
            "-y",
            "-q",
            "-c",
            "conda-forge",
            "gdb=12",
            "python=3.10",
        ],
        env=env,
    )
    print("Profila is now ready to run.")


def main() -> None:
    args = PARSER.parse_args()
    if args.command == "annotate":
        annotate_command(args)
    elif args.command == "attach_automated":
        attach_automated_command(args)
    elif args.command == "setup":
        setup_command(args)
    else:
        raise NotImplementedError()


if __name__ == "__main__":
    main()
