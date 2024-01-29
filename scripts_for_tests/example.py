import numpy as np
from numba import njit

DATA = np.random.random((1_000_000,))


@njit
def moving_average(timeseries):
    result = np.empty(timeseries.shape, dtype=np.float64)
    first_day = timeseries[0]
    for i in range(len(timeseries)):
        total = 0
        if i < 6:
            # Fill in missing values for first few days:
            total += (6 - i) * first_day
        for j in range(max(i - 6, 0), i + 1):
            total += timeseries[j]
        result[i] = total / 7
    return result


# Make sure the Numba code is pre-compiled
moving_average(DATA)

# This is the part we want to profile:
for i in range(100):
    moving_average(DATA)
