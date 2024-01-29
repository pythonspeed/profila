"""
Run Profila as a command-line tool.
"""

import asyncio
import os
import sys

from ._gdb import main


if __name__ == "__main__":

    async def iterate():
        async for f in main([os.fsencode(a) for a in sys.argv[1:]]):
            print(f)

    asyncio.run(iterate())
