"""
A profiler for Numba.
"""

import os
import sys
from shutil import which


def load_ipython_extension(ipython: object) -> None:
    """Load our IPython magic"""
    from IPython.core.error import UsageError
    from IPython.core.display import display, Markdown

    if "numba" in sys.modules:
        raise UsageError(
            "Numba is already imported. "
            "Please load this extension _before_ importing numba."
        )

    if not which("gdb") and not which("lldb-mi"):
        raise UsageError(
            """\
Both gdb and lldb-mi not found, please make sure one of the other is installed.

On Ubuntu: apt install gdb

On macOS:
1. brew install llvm cmake
2. export LLVM_DIR=export LLVM_DIR=/opt/homebrew/Cellar/llvm/*/lib/cmake
3. Checkout code at https://github.com/lldb-tools/lldb-mi
4. cd lldb-mi; cmake .; cmake --build .; cp src/llvm-mi /opt/homebrew/bin/
"""
        )

    os.environ["NUMBA_DEBUGINFO"] = "1"

    from ._ipython import ProfilaMagics

    ipython.register_magics(ProfilaMagics)  # type: ignore[attr-defined]

    display(
        Markdown(  # type: ignore[no-untyped-call]
            "> **Note:** loading the `profila` extension can impact Numba's performance. "
            "Make sure to disable it once you're done profiling!"
        )
    )
