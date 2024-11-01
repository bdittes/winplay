"""Lib to convert xyz zip files to mesh OBJ."""

import hashlib
import os
import zipfile

import ezdxf
from lxml import etree
import networkx
import numpy as np
import pymeshlab
import pymeshlab.pmeshlab
# import rasterio
from tifffile import imread

import utils as pu
import cyutils
import triangulate


def mesh_path(fname: str, cache_dir=".cache") -> str:
    """Where other functions in this file will write finished PLY files."""
    return pu.cache_path(fname, ext=".ply", cache_dir=cache_dir)


def add_line(a: np.array, i: int, li: str):
    """Add one line to the XYZ array."""
    l = li.strip()
    if not l.strip() or l.strip().lower().split(" ")[0] == "x":
        return 0
    if a.shape[0] <= i:
        a.resize((a.shape[0] + 10000000, a.shape[1]), refcheck=False)
        pu.log(f"add_line {a.shape}")
    a[i][:] = l.split(" ")
    return 1


def joinvf(vf1, vf2):
    """Join two vertex/face arrays."""
    if not vf1:
        return vf2
    if not vf2:
        return vf1
    v1, f1 = vf1
    v2, f2 = vf2
    return np.append(v1, v2, axis=0), np.append(f1, f2 + v1.shape[0], axis=0)


def polygonvf(x, y, z):
    v = np.zeros(shape=(len(x), 3), dtype=np.float64)
    ps = []
    for i in range(len(x)):
        v[i][:] = [x[i], y[i], z[i]]
        ps.append([x[i], y[i], z[i], i])
    triangles, _ = triangulate.triangulate(ps)
    f = np.zeros(shape=(len(triangles), 3), dtype=np.float64)
    for i in range(len(triangles)):
        i0, i1, i2 = triangles[i]
        f[i][:] = [i0, i1, i2]
    pu.log(f"polygonvf {len(x)} {len(f)}")
    return v, f


def grid_sides(h: np.array, minx, miny, step):
    dim_x, dim_y = h.shape
    maxx = minx + step * dim_x
    maxy = miny + step * dim_y
    vf = None
    vf = joinvf(vf, polygonvf([minx, maxx, maxx, minx], [miny, miny, maxy, maxy], [0, 0, 0, 0]))
    vf = joinvf(
        vf,
        polygonvf(
            [minx + i * step for i in range(dim_x)] + [maxx, minx],  #
            [miny for i in range(dim_x + 2)],
            [h[i][0] for i in range(dim_x)] + [0, 0]))
    vf = joinvf(
        vf,
        polygonvf(
            [minx + i * step for i in range(dim_x)] + [maxx, minx],  #
            [maxy for i in range(dim_x + 2)],
            [h[i][dim_y - 1] for i in range(dim_x)] + [0, 0]))
    vf = joinvf(
        vf,
        polygonvf(
            [minx for i in range(dim_y + 2)],  #
            [miny + i * step for i in range(dim_y)] + [maxy, miny],
            [h[0][i] for i in range(dim_y)] + [0, 0]))
    vf = joinvf(
        vf,
        polygonvf(
            [maxx for i in range(dim_y + 2)],  #
            [miny + i * step for i in range(dim_y)] + [maxy, miny],
            [h[dim_x - 1][i] for i in range(dim_y)] + [0, 0]))
    return vf


def xyz_to_mesh(fnames: list[str], cache_dir=".cache") -> str:
    """Process xyz data to ply file in cache."""
    a = np.zeros(shape=(0, 3), dtype=np.float64)
    cache_key = hashlib.md5()
    for fname in fnames:
        if fname.endswith(".xyz") or fname.endswith(".tif") or pu.zip_has_file(fname, "xyz"):
            cache_key.update(fname.encode())
    if not cache_key:
        return ""
    log_prefix = f"xyz_{(cache_key.hexdigest())}"
    dst_file = mesh_path(log_prefix, cache_dir)
    if os.path.exists(dst_file) and os.path.getsize(dst_file) > 0:
        pu.log(f"[{log_prefix}] Already here: {dst_file}.")
        return dst_file

    for fname in fnames:
        if not (fname.endswith(".xyz") or fname.endswith(".tif") or pu.zip_has_file(fname, "xyz")):
            continue
        fa = np.zeros(shape=(10000000, 3), dtype=np.float64)
        fai = 0
        np_cache = pu.cache_path(fname, ".npy", cache_dir=cache_dir)
        if os.path.exists(np_cache) and os.path.getsize(np_cache) > 0:
            pu.log(f"[{log_prefix}] {fname} load {np_cache}")
            fa = np.load(np_cache)
            fai = fa.shape[0]
        else:
            pu.log(f"[{log_prefix}] {fname}")
            if fname.endswith("zip"):
                with zipfile.ZipFile(fname) as zf:
                    for zfn in zf.namelist():
                        if zfn.endswith(".xyz"):
                            for li in zf.read(zfn).decode("utf-8-sig").splitlines():
                                fai += add_line(fa, fai, li)
                        # TODO zip .tif
            elif fname.endswith(".xyz"):
                with open(fname, "r") as f:
                    for li in f.readlines():
                        fai += add_line(fa, fai, li)
            elif fname.endswith(".tif"):
                data = imread(fname)
                print(data.shape)
                for x in range(0, data.shape[0]):
                    for y in range(0, data.shape[1]):
                        fai += add_line(fa, fai, f"{x} {y} {data[x][y]}")
            fa.resize((fai, 3))
            pu.log(f"[{log_prefix}] {fname} save {np_cache}")
            np.save(np_cache, fa)
        a = np.append(a, fa, axis=0)
    if a.shape[0] <= 0:
        return
    pu.log(f"[{log_prefix}] {a.shape} lines")

    a = a.T
    pu.log(f"[{log_prefix}] {a.shape}")
    mins = [np.min(a[0]), np.min(a[1]), np.min(a[2])]
    maxs = [np.max(a[0]), np.max(a[1]), np.max(a[2])]
    step = np.min([v for v in a[0] if v > mins[0]]) - mins[0]
    if step < 2.0:
        step = 2.0
    pu.log(f"[{log_prefix}] STEP {step}")

    dim_x = int((maxs[0] - mins[0]) / step + 1)
    dim_y = int((maxs[1] - mins[1]) / step + 1)
    pu.log(f"[{log_prefix}] {dim_x}, {dim_y}")
    if dim_x * dim_y > 10000000000:
        return

    h = cyutils.xyz_to_grid(a, step)
    del a

    vf = cyutils.grid_to_vf(h, mins[0], mins[1], step)
    vf = joinvf(vf, grid_sides(h, mins[0], mins[1], step))
    del h
    pu.log(f"[{log_prefix}] {vf[0].shape} v {vf[1].shape} f")

    if vf[0].shape[0] == 0:
        return
    ms = pymeshlab.MeshSet()
    ms.add_mesh(pymeshlab.Mesh(vf[0], vf[1]))
    # num_v = len(v)
    del vf
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
    return dst_file


def dxf_to_mesh(fname: str, cache_dir=".cache"):
    """Process dxf to ply."""
    if not fname.endswith(".dxf") and not pu.zip_has_file(fname, ".dxf"):
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


def gml_to_mesh(fname: str, cache_dir=".cache"):
    """Process gml to ply."""
    if not fname.endswith(".gml") and not pu.zip_has_file(fname, ".gml"):
        return
    dst_file = mesh_path(fname, cache_dir)
    log_prefix = os.path.basename(fname)
    if os.path.exists(dst_file) and os.path.getsize(dst_file) > 0:
        pu.log(f"[{log_prefix}] Already here: {dst_file}.")
        return

    lines = []
    if fname.endswith(".zip"):
        with zipfile.ZipFile(fname) as zf:
            for zfn in zf.namelist():
                if zfn.endswith(".gml"):
                    lines.extend(zf.read(zfn).decode("utf-8-sig").splitlines())
                # TODO zip .tif
    elif fname.endswith(".gml"):
        with open(fname, "r") as f:
            lines.extend(f.readlines())

    v = []
    f = []
    for line in lines:
        vbase = len(v)
        if "posList" not in line: continue
        a = line.find('>')
        if a < 0: continue
        line = line[a + 1:]
        a = line.find('<')
        if a < 0: continue
        line = line[:a].strip()
        # print(line)
        ps = []
        coords = line.split()
        for i in range(0, len(coords), 3):
            p = [float(coords[i]), float(coords[i + 1]), float(coords[i + 2]), i / 3]
            ps.append(p)
            v.append([p.x, p.y, p.z])
        # print([str(p) for p in ps])
        triangles, _ = triangulate.triangulate(ps)
        for t in triangles:
            f.append([t[0] + vbase, t[1] + vbase, t[2] + vbase])
        # print(triangles)
        # print(normal)

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
    vf = None
    for fname in fnames:
        ms = pymeshlab.MeshSet()
        ms.load_new_mesh(fname)
        if len(fnames) == 1:
            return ms
        for m in ms:
            pu.log(f"join {fname} {m.vertex_matrix().shape}")
            vf = joinvf(vf, (m.vertex_matrix(), m.face_matrix()))
    pu.log(f"joined to {vf[0].shape} {vf[1].shape}")
    ms = pymeshlab.MeshSet()
    ms.add_mesh(pymeshlab.Mesh(vf[0], vf[1]))
    pu.log("Merge close")
    ms.meshing_merge_close_vertices(threshold=pymeshlab.PercentageValue(0.001))
    pu.log(f"{ms.current_mesh().vertex_matrix().shape}")
    return ms
