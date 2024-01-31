"""
Run Profila as a command-line tool.
"""

from argparse import ArgumentParser, REMAINDER, RawDescriptionHelpFormatter
import asyncio
from asyncio.subprocess import Process
from shutil import which
from typing import Any
from collections.abc import Coroutine

from ._gdb import run_subprocess, read_samples
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


def get_stats(process: Coroutine[Any, Any, Process]) -> Stats:
    stats = Stats()

    async def iterate(future_process: Coroutine[Any, Any, Process]) -> None:
        process = await future_process
        count = 0
        async for sample in read_samples(process):
            count += 1
            stats.add_sample(sample)
        assert stats.total_samples() == count

    asyncio.run(iterate(process))
    return stats


def main() -> None:
    args = PARSER.parse_args()
    process = None
    if args.command == "annotate":
        if args.rest and args.rest[0] == "--":
            del args.rest[0]

        if not which("gdb"):
            raise SystemExit(
                "gdb not found, make sure it is installed, e.g. "
                "run 'apt install gdb' on Ubuntu."
            )

        process = run_subprocess(args.rest)
    else:
        raise NotImplementedError("TODO")

    assert process is not None
    stats = get_stats(process)
    final_stats = stats.finalize()
    assert -1.0 < final_stats.total_percent() - 100 < 1.0

    print(render_text(final_stats))


if __name__ == "__main__":
    main()
