"""
Run Profila as a command-line tool.
"""

from argparse import ArgumentParser, REMAINDER, RawDescriptionHelpFormatter, Namespace
import asyncio
from asyncio.subprocess import Process
from dataclasses import asdict
import json
from shutil import which
import sys

from ._gdb import run_subprocess, read_samples, attach_subprocess, exit_subprocess
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

    if not which("gdb"):
        raise SystemExit(
            "gdb not found, make sure it is installed, e.g. "
            "run 'apt install gdb' on Ubuntu."
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


def main() -> None:
    args = PARSER.parse_args()
    if args.command == "annotate":
        annotate_command(args)
    elif args.command == "attach_automated":
        attach_automated_command(args)
    else:
        raise NotImplementedError()


if __name__ == "__main__":
    main()
