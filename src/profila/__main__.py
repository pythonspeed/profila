"""
Run Profila as a command-line tool.
"""

import asyncio
import os
import sys

from ._gdb import run_subprocess
from ._stats import Stats


def main():
    stats = Stats()

    async def iterate():
        count = 0
        async for sample in run_subprocess([os.fsencode(a) for a in sys.argv[1:]]):
            count += 1
            stats.add_sample(sample)
        assert stats.total_samples() == count

    asyncio.run(iterate())
    print(stats)


if __name__ == "__main__":
    main()
