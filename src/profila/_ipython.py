"""
IPython/Jupyter magics.
"""
import ctypes
import json
import sys
import os
from subprocess import Popen, PIPE
from time import time

from ._stats import FinalStats
from ._render import render_text

from IPython.core.magic import Magics, magics_class, cell_magic
from IPython.core.display import display, Markdown

libc = ctypes.CDLL("libc.so.6")
prctl = libc.prctl
prctl.argtypes = [ctypes.c_int]
prctl.restype = ctypes.c_int
# From linux/prctl.h:
PR_SET_PTRACER = ctypes.c_int(0x59616D61)


@magics_class
class ProfilaMagics(Magics):
    """
    IPython/Jupyter magics.
    """

    @cell_magic  # type: ignore[misc]
    def profila(self, line: str, cell: str) -> None:
        """Run the cell under a profiler."""
        del line

        # Allow this process' children to attach via ptrace(), so that gdb works:
        prctl(PR_SET_PTRACER, ctypes.c_long(os.getpid()))
        try:
            self._run_profila(cell)
        finally:
            # Switch back to normal ptrace() policy:
            prctl(PR_SET_PTRACER, ctypes.c_long(0))

    def _run_profila(self, cell: str) -> None:
        start = time()
        profiler = Popen(
            [
                sys.executable,
                "-m",
                "profila",
                "attach_automated",
                str(os.getpid()),
            ],
            stdin=PIPE,
            stdout=PIPE,
        )
        # Wait for it to be ready:
        assert profiler.stdin is not None
        assert profiler.stdout is not None
        assert json.loads(profiler.stdout.readline().rstrip())["message"] == "attached"

        # Run the code:
        assert self.shell is not None
        self.shell.run_cell(cell)

        # Tell the subprocess it can exit:
        profiler.stdin.close()

        # JSON can't have integer keys, so we need to convert strings (line
        # numbers) back to integers.
        message = json.loads(profiler.stdout.readline().rstrip())
        for line_mappings in message["stats"]["numba_samples"].values():
            for line, pct in list(line_mappings.items()):
                del line_mappings[line]
                line_mappings[int(line)] = pct

        assert message["message"] == "stats"
        final_stats = FinalStats(**message["stats"])

        elapsed = time() - start
        text = f"**Elapsed:** {elapsed:.3f} seconds\n\n" + render_text(final_stats)
        display(Markdown(text))  # type: ignore[no-untyped-call]
