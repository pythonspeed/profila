"""
A profiler for Numba.
"""

import os
import sys


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

    from ._gdb import GDB_PATH

    if not os.path.exists(GDB_PATH):
        raise UsageError(
            "Profila's custom gdb not found, make sure it is installed by running "
            "'python -m profila setup'."
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
