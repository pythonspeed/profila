"""
A profiler for Numba.
"""

import os


def load_ipython_extension(ipython):
    """Load our IPython magic"""
    from IPython.core.error import UsageError

    # TODO various sanity checks

    os.environ["NUMBA_DEBUGINFO"] = "1"

    from ._ipython import ProfilaMagics

    ipython.register_magics(ProfilaMagics)
