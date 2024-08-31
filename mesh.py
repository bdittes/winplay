"""Lib to convert xyz zip files to mesh OBJ."""

import zipfile

import ezdxf
import numpy as np
import pymeshlab
import pymeshlab.pmeshlab


def xyz_to_mesh(fnames: list[str]) -> pymeshlab.MeshSet:
    lines = []
    for fname in fnames:
        if "xyz" not in fname:
            continue
        if fname.endswith("zip"):
            with zipfile.ZipFile(fname) as zf:
                for zfn in zf.namelist():
                    if zfn.endswith(".xyz"):
                        lines.extend(zf.read(zfn).decode("utf-8-sig").splitlines())
        else:
            with open(fname, "r") as f:
                lines.extend(f.readlines())
    print(f"'{lines[0]}'")
    lines = [li.strip() for li in lines if li.strip() and li.strip().lower().split(" ")[0] != "x"]
    a = np.zeros(shape=(len(lines), 3), dtype=np.float64)
    for vi in range(len(lines)):
        a[vi][:] = lines[vi].split(" ")
    del lines
    a = a.T
    print(a.shape)
    mins = [np.min(a[0]), np.min(a[1]), np.min(a[2])]
    maxs = [np.max(a[0]), np.max(a[1]), np.max(a[2])]
    STEP = np.min([v for v in a[0] if v > mins[0]]) - mins[0]
    print(f"STEP {STEP}")

    dimX = int((maxs[0] - mins[0]) / STEP + 1)
    dimY = int((maxs[1] - mins[1]) / STEP + 1)
    print(dimX, dimY)
    h = np.zeros(shape=(dimX, dimY), dtype=np.float64)
    for i in range(0, a.shape[1]):
        x = int(np.round((a[0][i] - mins[0]) / STEP))
        y = int(np.round((a[1][i] - mins[1]) / STEP))
        h[x][y] = a[2][i]
    del a

    v = [[mins[0], mins[1], 0], [maxs[0], mins[1], 0], [mins[0], maxs[1], 0], [maxs[0], maxs[1], 0]
         ] + [[mins[0] + x * STEP, mins[1] + y * STEP, h[x][y]] for x in range(0, dimX) for y in range(0, dimY)]
    print(f"{len(v)} vertices")
    del h

    BO = 4
    f = []
    for x in range(0, dimX - 1):
        for y in range(0, dimY - 1):
            ixy = x * dimY + y
            nxy = (x + 1) * dimY + y
            f.append([ixy + BO, nxy + BO, ixy + 1 + BO])
            f.append([
                ixy + 1 + BO,
                nxy + BO,
                nxy + 1 + BO,
            ])
    print(f"{len(f)} top faces")

    for x in range(0, dimX):
        ixy = x * dimY + 0
        ipxy = (x - 1) * dimY + 0
        ly = dimY - 1
        if x == 0:
            f.append([0, 1, ixy + BO])
            f.append([3, 2, ixy + ly + BO])
        else:
            f.append([ipxy + BO, 1, ixy + BO])
            f.append([3, ipxy + ly + BO, ixy + ly + BO])

    for y in range(0, dimY):
        ixy = 0 * dimY + y
        lxy = (dimX - 1) * dimY + y
        if y == 0:
            f.append([2, 0, ixy + BO])
            f.append([1, 3, lxy + BO])
        else:
            f.append([ixy - 1 + BO, ixy + BO, 2])
            f.append([3, lxy + BO, lxy - 1 + BO])

    f.append([0, 2, 1])
    f.append([1, 2, 3])
    print(f"{len(f)} total faces")
    ms = pymeshlab.MeshSet()
    if not len(v):
        return ms
    ms.add_mesh(pymeshlab.Mesh(v, f))
    num_v = len(v)
    del v, f
    targetperc = 0.8
    if num_v > 100000:
        targetperc = 0.5
    if num_v > 1000000:
        targetperc = 0.2
    if num_v > 10000000:
        targetperc = 0.05
    print(f"Decimating {targetperc}...")
    ms.meshing_decimation_quadric_edge_collapse(targetperc=targetperc,
                                                qualitythr=0.7,
                                                preserveboundary=True,
                                                preservetopology=True)
    print(f"{ms.current_mesh().vertex_matrix().shape}")
    return ms


def dxf_to_mesh(fnames: list[str]) -> pymeshlab.MeshSet:
    v = []
    f = []
    for fname in fnames:
        if "dxf" not in fname:
            continue
        if fname.endswith("zip"):
            dxf = ezdxf.readzip(fname).modelspace()
        else:
            dxf = ezdxf.readfile(fname).modelspace()
        print(f"{fname} {len(dxf)}")
        for pf in dxf:
            vbase = len(v)
            for vertex in pf.vertices:
                if vertex.is_face_record:
                    face_indices = [
                        vertex.get_dxf_attrib(name, 0) - 1 + vbase
                        for name in ("vtx0", "vtx1", "vtx2", "vtx3")
                        if vertex.get_dxf_attrib(name, 0) != 0
                    ]
                    f.append(face_indices)
                elif vertex.is_poly_face_mesh_vertex:
                    v.append(vertex.dxf.location)
        print(f"{len(v)} vertices, {len(f)} faces")
    ms = pymeshlab.MeshSet()
    if not len(v):
        return ms
    ms.add_mesh(pymeshlab.Mesh(v, f))
    print(f"{ms.current_mesh().vertex_matrix().shape}")
    print("Merge close")
    ms.meshing_merge_close_vertices(threshold=pymeshlab.PercentageValue(0.01))
    print(f"{ms.current_mesh().vertex_matrix().shape}")
    return ms


def join_mesh_set(ms: pymeshlab.MeshSet) -> pymeshlab.MeshSet:
    v = np.zeros(shape=(0, 3), dtype=np.float64)
    f = np.zeros(shape=(0, 3), dtype=np.int32)
    fbase = 0
    for m in ms:
        v = np.append(v, m.vertex_matrix())
        f = np.append(f, m.face_matrix() + fbase)
        fbase = len(f)
    ms2 = pymeshlab.MeshSet()
    ms2.add_mesh(pymeshlab.Mesh(v, f))
    print(f"joined into {ms.current_mesh().vertex_matrix().shape}")
    print("Merge close")
    ms2.meshing_merge_close_vertices(threshold=pymeshlab.PercentageValue(0.01))
    print(f"{ms.current_mesh().vertex_matrix().shape}")
    return ms2
