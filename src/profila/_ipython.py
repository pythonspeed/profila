"""
IPython/Jupyter magics.
"""
import json
import sys
import os
from subprocess import Popen, PIPE

from ._stats import FinalStats
from ._render import render_text

from IPython.core.magic import Magics, magics_class, cell_magic
from IPython.core.display import display, Markdown


@magics_class
class ProfilaMagics(Magics):
    @cell_magic
    def profila(self, line, cell):
        """Run the cell under a profiler."""
        del line

        profiler = Popen(
            [
                "pkexec",
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
        self.shell.run_cell(cell)
        profiler.stdin.close()
        message = json.loads(profiler.stdout.readline().rstrip())
        for line_mappings in message["stats"]["numba_samples"].values():
            for line, pct in list(line_mappings.items()):
                del line_mappings[line]
                line_mappings[int(line)] = pct

        assert message["message"] == "stats"
        final_stats = FinalStats(**message["stats"])
        display(Markdown(render_text(final_stats)))
