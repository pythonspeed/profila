"""
Tests for ``profila._render``.
"""

from syrupy.assertion import SnapshotAssertion

from profila._stats import FinalStats
from profila._render import render_text


def test_render_text(snapshot: SnapshotAssertion) -> None:
    """
    Minimal test for ``render_text()``.
    """
    final_stats = FinalStats(
        total_samples=1000,
        percent_bad_samples=9.9,
        percent_other_samples=15.1,
        numba_samples={"scripts_for_tests/simple.py": {12: 35.0, 15: 40.0}},
    )
    assert render_text(final_stats) == snapshot
