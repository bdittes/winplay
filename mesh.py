"""Lib to convert xyz zip files to mesh OBJ."""

import os
import zipfile

import ezdxf
import numpy as np
import pymeshlab
import pymeshlab.pmeshlab

import utils as pu


def mesh_path(fname: str, cache_dir=".cache") -> str:
    """Where other functions in this file will write finished PLY files."""
    return pu.cache_path(fname, ext=".ply", cache_dir=cache_dir)


def xyz_to_mesh(fname: str, cache_dir=".cache"):
    """Process xyz data to ply file in cache."""
    if "xyz" not in fname:
        return
    dst_file = mesh_path(fname, cache_dir)
    log_prefix = os.path.basename(fname)
    if os.path.exists(dst_file) and os.path.getsize(dst_file) > 0:
        pu.log(f"[{log_prefix}] Already here: {dst_file}.")
        return

    lines = []
    if fname.endswith("zip"):
        with zipfile.ZipFile(fname) as zf:
            for zfn in zf.namelist():
                if zfn.endswith(".xyz"):
                    lines.extend(zf.read(zfn).decode("utf-8-sig").splitlines())
    else:
        with open(fname, "r") as f:
            lines.extend(f.readlines())
    if not lines:
        return
    pu.log(f"[{log_prefix}] '{lines[0].strip()}'")
    lines = [li.strip() for li in lines if li.strip() and li.strip().lower().split(" ")[0] != "x"]
    a = np.zeros(shape=(len(lines), 3), dtype=np.float64)
    for vi in range(len(lines)):
        a[vi][:] = lines[vi].split(" ")
    del lines
    a = a.T
    pu.log(f"[{log_prefix}] {a.shape}")
    mins = [np.min(a[0]), np.min(a[1]), np.min(a[2])]
    maxs = [np.max(a[0]), np.max(a[1]), np.max(a[2])]
    step = np.min([v for v in a[0] if v > mins[0]]) - mins[0]
    pu.log(f"[{log_prefix}] STEP {step}")

    dim_x = int((maxs[0] - mins[0]) / step + 1)
    dim_y = int((maxs[1] - mins[1]) / step + 1)
    pu.log(f"[{log_prefix}] {dim_x}, {dim_y}")
    h = np.zeros(shape=(dim_x, dim_y), dtype=np.float64)
    for i in range(0, a.shape[1]):
        x = int(np.round((a[0][i] - mins[0]) / step))
        y = int(np.round((a[1][i] - mins[1]) / step))
        h[x][y] = a[2][i]
    del a

    v = [[mins[0], mins[1], 0], [maxs[0], mins[1], 0], [mins[0], maxs[1], 0], [maxs[0], maxs[1], 0]
         ] + [[mins[0] + x * step, mins[1] + y * step, h[x][y]] for x in range(0, dim_x) for y in range(0, dim_y)]
    pu.log(f"[{log_prefix}] {len(v)} vertices")
    del h

    BO = 4
    f = []
    for x in range(0, dim_x - 1):
        for y in range(0, dim_y - 1):
            ixy = x * dim_y + y
            nxy = (x + 1) * dim_y + y
            f.append([ixy + BO, nxy + BO, ixy + 1 + BO])
            f.append([
                ixy + 1 + BO,
                nxy + BO,
                nxy + 1 + BO,
            ])
    pu.log(f"[{log_prefix}] {len(f)} top faces")

    for x in range(0, dim_x):
        ixy = x * dim_y + 0
        ipxy = (x - 1) * dim_y + 0
        ly = dim_y - 1
        if x == 0:
            f.append([0, 1, ixy + BO])
            f.append([3, 2, ixy + ly + BO])
        else:
            f.append([ipxy + BO, 1, ixy + BO])
            f.append([3, ipxy + ly + BO, ixy + ly + BO])

    for y in range(0, dim_y):
        ixy = 0 * dim_y + y
        lxy = (dim_x - 1) * dim_y + y
        if y == 0:
            f.append([2, 0, ixy + BO])
            f.append([1, 3, lxy + BO])
        else:
            f.append([ixy - 1 + BO, ixy + BO, 2])
            f.append([3, lxy + BO, lxy - 1 + BO])

    f.append([0, 2, 1])
    f.append([1, 2, 3])
    pu.log(f"[{log_prefix}] {len(f)} total faces")
    if len(v) == 0:
        return
    ms = pymeshlab.MeshSet()
    ms.add_mesh(pymeshlab.Mesh(v, f))
    # num_v = len(v)
    del v, f
    targetperc = 0.8
    if step >= 1.95:
        targetperc = 0.1
    elif step > 0.45:
        targetperc = 0.05
    pu.log(f"[{log_prefix}] Decimating {targetperc}...")
    ms.meshing_decimation_quadric_edge_collapse(targetperc=targetperc,
                                                qualitythr=0.7,
                                                preserveboundary=True,
                                                preservetopology=True)
    pu.log(f"[{log_prefix}] {ms.current_mesh().vertex_matrix().shape}")
    ms.save_current_mesh(dst_file)
    pu.log(f"[{log_prefix}] Wrote {dst_file}")
    return


def dxf_to_mesh(fname: str, cache_dir=".cache"):
    """Process dxf to ply."""
    if "dxf" not in fname:
        return
    dst_file = mesh_path(fname, cache_dir)
    log_prefix = os.path.basename(fname)
    if os.path.exists(dst_file) and os.path.getsize(dst_file) > 0:
        pu.log(f"[{log_prefix}] Already here: {dst_file}.")
        return

    v = []
    f = []
    if fname.endswith("zip"):
        dxf = ezdxf.readzip(fname).modelspace()
    else:
        dxf = ezdxf.readfile(fname).modelspace()
    pu.log(f"[{log_prefix}] {len(dxf)}")
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
    pu.log(f"[{log_prefix}] {len(v)} vertices, {len(f)} faces")
    if len(v) == 0:
        return
    ms = pymeshlab.MeshSet()
    ms.add_mesh(pymeshlab.Mesh(v, f))
    pu.log(f"[{log_prefix}] {ms.current_mesh().vertex_matrix().shape}")
    ms.save_current_mesh(dst_file)
    pu.log(f"[{log_prefix}] Wrote {dst_file}")


def join_mesh_set(fnames: list[str]) -> pymeshlab.MeshSet:
    """Join given mesh files into a MeshSet with a single mesh."""
    v = np.zeros(shape=(0, 3), dtype=np.float64)
    f = np.zeros(shape=(0, 3), dtype=np.int32)
    vbase = 0
    for fname in fnames:
        ms = pymeshlab.MeshSet()
        ms.load_new_mesh(fname)
        for m in ms:
            pu.log(m.vertex_matrix().shape)
            v = np.append(v, m.vertex_matrix(), axis=0)
            f = np.append(f, m.face_matrix() + vbase, axis=0)
            vbase = len(v)
    pu.log(v.shape)
    pu.log(f.shape)
    ms = pymeshlab.MeshSet()
    ms.add_mesh(pymeshlab.Mesh(v, f))
    pu.log(f"joined into {ms.current_mesh().vertex_matrix().shape}")
    pu.log("Merge close")
    ms.meshing_merge_close_vertices(threshold=pymeshlab.PercentageValue(0.001))
    pu.log(f"{ms.current_mesh().vertex_matrix().shape}")
    return ms
