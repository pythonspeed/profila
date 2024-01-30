"""
Run Profila as a command-line tool.
"""

from argparse import ArgumentParser, REMAINDER, RawDescriptionHelpFormatter
import asyncio

from ._gdb import run_subprocess
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


def get_stats(python_args: list[str]) -> Stats:
    stats = Stats()

    async def iterate() -> None:
        count = 0
        async for sample in run_subprocess(python_args):
            count += 1
            stats.add_sample(sample)
        assert stats.total_samples() == count

    asyncio.run(iterate())
    return stats


def main() -> None:
    args = PARSER.parse_args()
    if args.rest and args.rest[0] == "--":
        del args.rest[0]
    stats = get_stats(args.rest)
    final_stats = stats.finalize()
    assert -1.0 < final_stats.total_percent() - 100 < 1.0

    print(render_text(final_stats))


if __name__ == "__main__":
    main()
