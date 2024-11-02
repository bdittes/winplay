"""Cython utils"""

# from libc.math import sqrt

import cython as cy
import numpy as np
from cython.parallel import prange, parallel

tmpl_num = cy.fused_type(cy.int, cy.double, cy.longlong)


def nptest(a: cy.double[:, :]) -> np.array:
    """Cython numpy test"""
    x = np.sum(a)
    r = np.zeros(shape=(1, 1))
    r[0][0] = x
    return r


@cy.boundscheck(False)
@cy.wraparound(False)
def xy_step(a: cy.double[:, :]):
    minx: cy.double = np.min(a[0])
    minx2: cy.double = np.max(a[0])
    i: cy.int = 0
    alen: cy.int = a.shape[1]
    with nogil:
        for i in range(alen):
            if a[0][i] < minx2:
                minx2 = a[0][i]
    return minx2 - minx


@cy.boundscheck(False)
@cy.wraparound(False)
def xyz_to_grid(a: cy.double[:, :], xy_step: cy.double, z_step: cy.double):
    minx: cy.double = np.min(a[0])
    miny: cy.double = np.min(a[1])
    maxs = [np.max(a[0]), np.max(a[1]), np.max(a[2])]
    dim_x: cy.int = int((maxs[0] - minx) / xy_step + 1)
    dim_y: cy.int = int((maxs[1] - miny) / xy_step + 1)
    h = np.zeros(shape=(dim_x, dim_y), dtype=np.float64)
    hv: cy.double[:, ::1] = h
    n = np.zeros(shape=(dim_x, dim_y), dtype=np.float64)
    nv: cy.double[:, ::1] = n

    alen: cy.int = a.shape[1]
    i: cy.int
    x: cy.int
    y: cy.int
    with nogil, parallel(num_threads=8):
        for i in prange(alen):
            x = cy.cast(cy.int, (a[0][i] - minx) / xy_step)
            y = cy.cast(cy.int, (a[1][i] - miny) / xy_step)
            hv[x][y] += a[2][i]
            nv[x][y] += 1
        for x in prange(dim_x):
            for y in range(dim_y):
                if nv[x][y] > 1:
                    hv[x][y] /= nv[x][y]
                if z_step > 0:
                    hv[x][y] = cy.cast(cy.int, hv[x][y] / z_step) * z_step
    return h


@cy.boundscheck(False)
@cy.wraparound(False)
@cy.exceptval(check=False)
@cy.cfunc
@cy.nogil
def set3d(a: cy.double[:, :], i: cy.int, x: cy.double, y: cy.double, z: cy.double) -> cy.int:
    a[i][0] = x
    a[i][1] = y
    a[i][2] = z
    return i + 1


@cy.boundscheck(False)
@cy.wraparound(False)
@cy.exceptval(check=False)
@cy.cfunc
@cy.nogil
def set3i(a: cy.int[:, :], i: cy.int, x: cy.int, y: cy.int, z: cy.int) -> cy.int:
    a[i][0] = x
    a[i][1] = y
    a[i][2] = z
    return i + 1


@cy.boundscheck(False)
@cy.wraparound(False)
def grid_to_vf(h: cy.double[:, :], minx: cy.double, miny: cy.double, step: cy.double):
    dim_x: cy.int = h.shape[0]
    dim_y: cy.int = h.shape[1]
    x: cy.int = 0
    y: cy.int = 0

    v = np.zeros(shape=(dim_x * dim_y, 3), dtype=np.float64)
    vv: cy.double[:, ::1] = v
    vi: cy.int = 0

    BO: cy.int = 0
    f = np.zeros(shape=(2 * (dim_x - 1) * (dim_y - 1), 3), dtype=np.int32)
    fv: cy.int[:, ::1] = f
    fi: cy.int = 0

    with nogil:
        for x in range(dim_x):
            for y in range(dim_y):
                vi = set3d(vv, vi, minx + x * step, miny + y * step, h[x][y])

        for x in range(dim_x - 1):
            for y in range(dim_y - 1):
                ixy: cy.int = x * dim_y + y
                nxy: cy.int = (x + 1) * dim_y + y
                fi = set3i(fv, fi, ixy + BO, nxy + BO, ixy + 1 + BO)
                fi = set3i(fv, fi, ixy + 1 + BO, nxy + BO, nxy + 1 + BO)

    return v, f
