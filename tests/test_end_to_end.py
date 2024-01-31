import asyncio
from subprocess import Popen, PIPE, check_output
import os

from profila._stats import FinalStats
from profila._gdb import run_subprocess
from profila.__main__ import get_stats


def test_stdout_and_stderr_passthrough() -> None:
    """
    stdout and stderr are passed from the subprocess.
    """
    p = Popen(
        [
            "python",
            "-m",
            "profila",
            "annotate",
            "--",
            "-c",
            "import sys; sys.stderr.write('err1@@\nXX\n'); sys.stdout.write('out2@@\nYY\n')",
        ],
        stdout=PIPE,
        stderr=PIPE,
    )
    assert p.stdout is not None
    assert p.stderr is not None
    assert b"err1@@\nXX" in p.stderr.read()
    assert b"out2@@\nYY" in p.stdout.read()


def test_profiling() -> None:
    """
    Plausible costs are assigned to relevant lines of code.
    """
    simple_py = "scripts_for_tests/simple.py"

    async def main() -> FinalStats:
        process = await run_subprocess([simple_py])
        return (await get_stats(process)).finalize()

    final_stats = asyncio.run(main())
    simple_py = os.path.abspath(simple_py)

    simple_stats = final_stats.numba_samples[simple_py]
    # Comments should have zero cost:
    assert simple_stats.get(14, 0) == 0
    assert simple_stats.get(11, 0) == 0
    # These two lines should be the bulk of the work:
    expensive = simple_stats[12]
    assert expensive > 5
    cheap = simple_stats[15]
    assert expensive > cheap * 2
    assert cheap > 0


def test_jupyter() -> None:
    """
    Test rendering a Jupyter notebook that profiles with profila.
    """
    output = check_output(
        "jupyter-nbconvert scripts_for_tests/test.ipynb --execute --to markdown --stdout".split(),
        encoding="utf-8",
    )
    assert "% non-Numba samples" in output
    assert "% |         for j in range(max(i - 6, 0), i + 1):" in output
    assert "% |             total += timeseries[j]" in output
