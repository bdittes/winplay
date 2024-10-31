"""Cython utils"""

import cython
import numpy as np
# from libc.math cimport round, floor
from cython.parallel import prange, parallel

my_type = cython.fused_type(cython.int, cython.double, cython.longlong)


def nptest(a: cython.double[:, :]) -> np.array:
    """Cython numpy test"""
    x = np.sum(a)
    r = np.zeros(shape=(1, 1))
    r[0][0] = x
    return r


@cython.boundscheck(False)
@cython.wraparound(False)
def xyz_to_grid(a: cython.double[:, :], step: cython.double):
    minx: cython.double = np.min(a[0])
    miny: cython.double = np.min(a[1])
    maxs = [np.max(a[0]), np.max(a[1]), np.max(a[2])]
    dim_x: cython.int = int((maxs[0] - minx) / step + 1)
    dim_y: cython.int = int((maxs[1] - miny) / step + 1)
    h = np.zeros(shape=(dim_x, dim_y), dtype=np.float64)
    hv: cython.double[:, ::1] = h
    n = np.zeros(shape=(dim_x, dim_y), dtype=np.float64)
    nv: cython.double[:, ::1] = n

    alen: cython.int = a.shape[1]
    i: cython.int
    x: cython.int
    y: cython.int
    with nogil, parallel(num_threads=8):
        for i in prange(alen):
            x = <int>((a[0][i] - minx) / step)
            y = <int>((a[1][i] - miny) / step)
            hv[x][y] += a[2][i]
            nv[x][y] += 1
        for x in prange(dim_x):
            for y in range(dim_y):
                if nv[x][y] > 1:
                    hv[x][y] /= nv[x][y]
    return h

@cython.boundscheck(False)
@cython.wraparound(False)
@cython.exceptval(check=False)
@cython.cfunc
@cython.nogil
def set3(a: cython.double[:,:], i: cython.int, x: cython.double, y: cython.double, z: cython.double) -> cython.int:
    a[i][0] = x
    a[i][1] = y
    a[i][2] = z
    return i+1


@cython.boundscheck(False)
@cython.wraparound(False)
def grid_to_vf(h: cython.double[:,:], minx: cython.double, miny: cython.double, step: cython.double):
    dim_x: cython.int = h.shape[0]
    dim_y: cython.int = h.shape[1]
    maxx: cython.double = minx + step * dim_x
    maxy: cython.double = miny + step * dim_y
    x: cython.int = 0
    y: cython.int = 0

    v = np.zeros(shape=(4 + dim_x * dim_y, 3), dtype=np.float64)
    vv: cython.double[:, ::1] = v
    vi: cython.int = 0

    BO: cython.int = 4
    f = np.zeros(shape=(2 * (dim_x - 1) * (dim_y - 1) + 2* dim_x + 2* dim_y + 2, 3), dtype=np.float64)
    fv: cython.double[:, ::1] = f
    fi: cython.int = 0

    with nogil:
        vi = set3(vv, vi, minx, miny, 0)
        vi = set3(vv, vi, maxx, miny, 0)
        vi = set3(vv, vi, minx, maxy, 0)
        vi = set3(vv, vi, maxx, maxy, 0)
        for x in range(dim_x):
            for y in range(dim_y):
                vi = set3(vv, vi, minx + x * step, miny + y * step, h[x][y])

        for x in range(dim_x - 1):
            for y in range(dim_y - 1):
                ixy: cython.int = x * dim_y + y
                nxy: cython.int = (x + 1) * dim_y + y
                fi = set3(fv, fi, ixy + BO, nxy + BO, ixy + 1 + BO)
                fi = set3(fv, fi, ixy + 1 + BO, nxy + BO, nxy + 1 + BO)

        for x in range(0, dim_x):
            ixy: cython.int = x * dim_y + 0
            ipxy: cython.int = (x - 1) * dim_y + 0
            ly: cython.int = dim_y - 1
            if x == 0:
                fi = set3(fv, fi, 0, 1, ixy + BO)
                fi = set3(fv, fi, 3, 2, ixy + ly + BO)
            else:
                fi = set3(fv, fi, ipxy + BO, 1, ixy + BO)
                fi = set3(fv, fi, 3, ipxy + ly + BO, ixy + ly + BO)

        for y in range(0, dim_y):
            ixy: cython.int = 0 * dim_y + y
            lxy: cython.int = (dim_x - 1) * dim_y + y
            if y == 0:
                fi = set3(fv, fi, 2, 0, ixy + BO)
                fi = set3(fv, fi, 1, 3, lxy + BO)
            else:
                fi = set3(fv, fi, ixy - 1 + BO, ixy + BO, 2)
                fi = set3(fv, fi, 3, lxy + BO, lxy - 1 + BO)

        fi = set3(fv, fi, 0, 2, 1)
        fi = set3(fv, fi, 1, 2, 3)
    return v, f
