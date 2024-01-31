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

    if sys.platform != "linux":
        raise UsageError(
            "Currently only Linux is supported; you can try running in "
            "Docker/Podman/WSL2."
        )

    if not which("gdb"):
        raise UsageError(
            "gdb not found, please make sure it is installed."
            " For example, 'apt install gdb' on Ubuntu."
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
