import numpy as np

from numba import njit


DATA = np.random.random((1_000_000,))


@njit
def min_and_max(arr):
    a = arr.min()
    b = arr.max()
    return a, b


for _ in range(1000):
    min_and_max(DATA)
