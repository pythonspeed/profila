from subprocess import Popen, PIPE
import os

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
    final_stats = get_stats([simple_py]).finalize()
    simple_py = os.path.abspath(simple_py)

    simple_stats = final_stats.numba_samples[simple_py]
    # Comments should have zero cost:
    assert simple_stats.get(14, 0) == 0
    assert simple_stats.get(11, 0) == 0
    # These two lines should be the bulk of the work:
    expensive = simple_stats[12]
    assert expensive > 5
    cheap = simple_stats[15]
    assert expensive * 2 > cheap > 1
