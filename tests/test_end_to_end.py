from subprocess import Popen, PIPE


def test_stdout_and_stderr_passthrough():
    """
    stdout and stderr are passed from the subprocess.
    """
    p = Popen(
        [
            "python",
            "-m",
            "profila",
            "annotate",
            "-c",
            "import sys; sys.stderr.write('err1@@\nXX\n'); sys.stdout.write('out2@@\nYY\n')",
        ],
        stdout=PIPE,
        stderr=PIPE,
    )
    assert b"err1@@\nXX" in p.stderr.read()
    assert b"out2@@\nYY" in p.stdout.read()
