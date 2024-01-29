"""
Aggregate call stacks.
"""

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Optional
from ._gdb import Frame


@dataclass
class Stats:
    # Map Python filenames to per-line counts. Should be Numba samples only.
    path_to_line_counts: defaultdict[str, Counter[int]] = field(
        default_factory=lambda: defaultdict(Counter)
    )
    # Samples we couldn't parse:
    bad_samples: int = 0
    # Samples that weren't Numba based:
    other_samples: int = 0

    def total_samples(self) -> int:
        """
        Total number of all samples.
        """
        result = self.bad_samples + self.other_samples
        for line_counts in self.path_to_line_counts.values():
            result += sum(line_counts.values())
        return result

    def add_sample(self, sample: Optional[list[Frame]]):
        """
        Add a sample.
        """
        if sample is None:
            self.bad_samples += 1
            return

        for frame in sample:
            if frame.file.endswith(".py"):
                self.path_to_line_counts[frame.file][frame.line] += 1
                return

        self.other_samples += 1
