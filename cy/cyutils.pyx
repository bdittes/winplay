"""Cython utils"""

import cython
import numpy as np
from libc.math cimport round, floor
from cython.parallel import prange, parallel

my_type = cython.fused_type(cython.int, cython.double, cython.longlong)


def nptest(a: cython.double[:, :]) -> np.array:
    """Cython numpy test"""
    x = np.sum(a)
    r = np.zeros(shape=(1, 1))
    r[0][0] = x
    return r


@cython.exceptval(check=False)
@cython.cfunc
def clip(a: my_type, min_value: my_type, max_value: my_type) -> my_type:
    return min(max(a, min_value), max_value)


@cython.boundscheck(False)
@cython.wraparound(False)
def xyz_to_grid(a: cython.double[:, ::1]):
    minx: cython.double = np.min(a[0])
    miny: cython.double = np.min(a[1])
    maxs = [np.max(a[0]), np.max(a[1]), np.max(a[2])]
    step: cython.double = np.min([v for v in a[0] if v > minx]) - minx
    dim_x: cython.int = int((maxs[0] - minx) / step + 1)
    dim_y: cython.int = int((maxs[1] - miny) / step + 1)
    h = np.zeros(shape=(dim_x, dim_y), dtype=np.float64)
    hv: cython.double[:, ::1] = h
    
    n: cython.int = a.shape[1]
    i: cython.int
    with nogil, parallel(num_threads=8):
        for i in range(n):
            x: cython.int = <int>(round((a[0][i] - minx) / step))
            y: cython.int = <int>(round((a[1][i] - miny) / step))
            hv[x][y] = a[2][i]
    return h
