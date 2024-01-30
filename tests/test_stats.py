"""
Tests for ``profila._stats``.
"""

from typing import Optional
from hypothesis import given, strategies as st

from profila._stats import Stats
from profila._gdb import Frame

import pytest


@given(
    samples=st.lists(
        st.none()
        | st.lists(
            st.builds(
                Frame,
                file=st.just("a.py")
                | st.just("b.py")
                | st.just("c.py")
                | st.just("file.c")
                | st.just("file2.c"),
                line=st.integers(min_value=1, max_value=20),
            ),
            max_size=10,
        ),
        max_size=20,
    ),
)
def test_create_stats(samples: list[Optional[list[Frame]]]) -> None:
    """
    A list of ``Frame`` or ``None`` added to a ``Stats`` are processed
    creately.
    """
    stats = Stats()
    for sample in samples:
        stats.add_sample(sample)
    assert stats.total_samples() == len(samples)
    assert stats.bad_samples == len([s for s in samples if s is None])
    assert stats.other_samples == sum(
        [
            files <= {"file.c", "file2.c"}
            for files in [
                {f.file for f in sample} for sample in samples if sample is not None
            ]
        ]
    )
    assert stats.path_to_line_counts.keys() <= {"a.py", "b.py", "c.py"}

    # Drop all non-Python frames, and all but first frames, compare:
    samples2 = [s[:] for s in samples if s is not None]
    for frames in samples2:
        while frames and not frames[0].file.endswith(".py"):
            frames.pop(0)
        if len(frames) > 1:
            del frames[1:]
    samples2 = [s for s in samples2 if s]

    expected: dict[str, dict[int, float]] = {}
    for s in samples2:
        expected.setdefault(s[0].file, {}).setdefault(s[0].line, 0)
        expected[s[0].file][s[0].line] += 1
    stats2 = Stats()
    for sample in samples2:
        stats2.add_sample(sample)
    assert stats.path_to_line_counts == stats2.path_to_line_counts
    assert stats.path_to_line_counts == expected

    # Check FinalStats conversion.
    final_stats = stats.finalize()
    total = final_stats.total_samples
    assert total == stats.total_samples()
    assert (final_stats.percent_bad_samples / 100) * total == pytest.approx(
        stats.bad_samples, 0.01
    )
    assert (final_stats.percent_other_samples / 100) * total == pytest.approx(
        stats.other_samples, 0.01
    )
    assert final_stats.numba_samples.keys() == stats.path_to_line_counts.keys()
    for path, line_to_pct in final_stats.numba_samples.items():
        assert line_to_pct.keys() == stats.path_to_line_counts[path].keys()
        for line, pct in line_to_pct.items():
            assert (pct / 100) * total == pytest.approx(
                stats.path_to_line_counts[path][line], 0.01
            )
