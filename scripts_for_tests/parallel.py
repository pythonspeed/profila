import numpy as np
from numba import njit, prange, gdb
from time import time

DATA = np.random.random((1_000_000,))


@njit(parallel=True)
def parallel_sum(timeseries):
    total = 0
    for i in prange(len(timeseries)):
        value = ((7 * timeseries[i]) + 1) / 9
        for j in range(100):
            value = np.sin(value)
            value = np.cos(value)
            value = ((7 * value) + 1) / 9
        total += value
    return total


# Make sure the Numba code is pre-compiled
parallel_sum(DATA)

# This is the part we want to profile:
import os

print(os.getpid())
while True:
    parallel_sum(DATA)
