"""
Render ``FinalStats`` to human-readable text.
"""

from io import StringIO
from linecache import getline

from ._stats import FinalStats


def render_text(stats: FinalStats) -> str:
    """
    Render stats to text.
    """
    result = StringIO()
    result.write(
        f"# Total samples: {stats.total_samples} "
        + f"({stats.percent_other_samples}% non-Numba samples, "
        + f"{stats.percent_bad_samples}% bad samples)\n"
    )

    for filename, line_percents in stats.numba_samples.items():
        result.write(f"\n## File `{filename}`\n")

        min_line = min(line_percents)
        max_line = max(line_percents)

        result.write(f"Lines {min_line} to {max_line}:\n\n")
        for line_number in range(min_line, max_line + 1):
            code = getline(filename, line_number).rstrip()
            percent = line_percents.get(line_number, 0)
            if percent == 0:
                usage = "      "
            else:
                usage = f"{percent:>5}%"
            result.write(f"{usage} | {code}\n")

    return result.getvalue()
