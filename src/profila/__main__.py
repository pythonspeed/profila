"""
Run Profila as a command-line tool.
"""

import asyncio
import os
import sys

from ._gdb import main


if __name__ == "__main__":
    asyncio.run(main([os.fsencode(a) for a in sys.argv[1:]]))
