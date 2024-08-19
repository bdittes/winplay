"""Convert swiss alti to mesh"""

import glob

import numpy as np

STEP = 2.0
PATH = "N:\\3d\\alti\\SWISSALTI3D_2_XYZ_CHLV95_LN02_*.xyz"
# PATH = "N:\\3d\\alti\\SWISSALTI3D_2_XYZ_CHLV95_LN02_2683_1248.xyz"
# PATH = "N:\\3d\\alti\\test.xyz"
OUTPATH = "N:\\3d\\alti\\py.obj"

a = np.ndarray(shape=(0, 3), dtype=np.float64)
for fn in glob.glob(PATH):
    print(fn)
    a = np.append(a, np.genfromtxt(
        fname=fn,
        delimiter="",
        skip_header=0,
        dtype=np.float64,
    ), axis=0)
a = a.T
print(a.shape)
mins = [np.min(a[0]), np.min(a[1]), np.min(a[2])]
maxs = [np.max(a[0]), np.max(a[1]), np.max(a[2])]

dimX = int((maxs[0] - mins[0]) / STEP + 1)
dimY = int((maxs[1] - mins[1]) / STEP + 1)

print(dimX, dimY)
h = np.zeros(shape=(dimX, dimY), dtype=np.float64)
n = np.zeros(shape=(dimX, dimY), dtype=np.int16)
for i in range(0, a.shape[1]):
    x = int(np.round((a[0][i] - mins[0]) / STEP))
    y = int(np.round((a[1][i] - mins[1]) / STEP))
    h[x][y] += a[2][i]
    n[x][y] += 1

for x in range(0, dimX):
    for y in range(0, dimY):
        if n[x][y] > 0.1:
            h[x][y] /= n[x][y]
        else:
            h[x][y] = 0

v = [
    str.format("v {0} {1} {2}", mins[0], mins[1], 0),
    str.format("v {0} {1} {2}", maxs[0], mins[1], 0),
    str.format("v {0} {1} {2}", mins[0], maxs[1], 0),
    str.format("v {0} {1} {2}", maxs[0], maxs[1], 0),
] + [
    str.format("v {0} {1} {2}", mins[0] + x * STEP, mins[1] + y * STEP, h[x][y])
    for x in range(0, dimX)
    for y in range(0, dimY)
]
# vc = [[mins[0] + x * STEP, mins[1] + y * STEP] for x in range(0, dimX) for y in range(0, dimY)]
BO = 4 + 1

f = []
for x in range(0, dimX - 1):
    for y in range(0, dimY - 1):
        ixy = x * dimY + y
        nxy = (x + 1) * dimY + y
        f.append(str.format("f {0} {1} {2}", ixy + BO, nxy + BO, ixy + 1 + BO))
        f.append(str.format(
            "f {0} {1} {2}",
            ixy + 1 + BO,
            nxy + BO,
            nxy + 1 + BO,
        ))

for x in range(0, dimX):
    ixy = x * dimY + 0
    ipxy = (x - 1) * dimY + 0
    ly = dimY - 1
    if x == 0:
        f.append(str.format("f {0} {1} {2}", 1, 2, ixy + BO))
        f.append(str.format("f {0} {1} {2}", 4, 3, ixy + ly + BO))
    else:
        f.append(str.format("f {0} {1} {2}", ipxy + BO, 2, ixy + BO))
        f.append(str.format("f {0} {1} {2}", 4, ipxy + ly + BO, ixy + ly + BO))

for y in range(0, dimY):
    ixy = 0 * dimY + y
    lxy = (dimX - 1) * dimY + y
    if y == 0:
        f.append(str.format("f {0} {1} {2}", 3, 1, ixy + BO))
        f.append(str.format("f {0} {1} {2}", 2, 4, lxy + BO))
    else:
        f.append(str.format("f {0} {1} {2}", ixy - 1 + BO, ixy + BO, 3))
        f.append(str.format("f {0} {1} {2}", 4, lxy + BO, lxy - 1 + BO))

f.append("f 1 3 2")
f.append("f 2 3 4")

with open(OUTPATH, "w", encoding="UTF8") as of:
    for line in v:
        of.write(f"{line}\n")
    for line in f:
        of.write(f"{line}\n")
