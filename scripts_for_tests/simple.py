import numpy as np
from numba import njit

DATA = np.random.random((1_000_000,))


@njit
def simple(timeseries):
    result = np.empty_like(timeseries)
    for i in range(len(timeseries)):
        # This should be the most expensive line:
        result[i] = (7 + timeseries[i] / 9 + (timeseries[i] ** 2) / 7) / 5
    for i in range(len(result)):
        # This should be cheaper:
        result[i] -= 1
    return result


# Make sure the Numba code is pre-compiled
simple(DATA)

# This is the part we want to profile:
for i in range(500):
    simple(DATA)
