"""Convert swiss alti and/or buildings to mesh"""

import os
from functools import partial
from multiprocessing import Pool

import numpy

import mesh
import utils as pu
import cyutils as cy

if __name__ == "__main__":
    print(cy.nptest(numpy.ones(shape=(2, 3), dtype=numpy.float64)))
    cache_dir = R".\.cache"
    # print(os.path.normpath("http://abc.com/file.xyz"))
    # print(os.path.normpath(R".\.cache\abc.xyz.zip"))
    # print(pu.cache_path(R".\.cache\abc.xyz.zip", ".npy"))
    # a = pu.cmdline_input("csv", R"N:\code\winplay\testdata\zh-large.csv")
    # a = pu.cmdline_input("csv", R"N:\code\winplay\testdata\swissbuildings2.csv")
    # a = pu.cmdline_input("csv", R"N:\code\winplay\testdata\xyz.csv")
    a = pu.cmdline_input("csv", R"N:\code\winplay\testdata\Zurich10x10_TOPO.csv")
    # a = pu.cmdline_input("csv", R"N:\code\winplay\testdata\freiburg.csv")
    scale = float(pu.cmdline_input("Scale 1:X", "10000"))
    xy_step_mm = float(pu.cmdline_input("min step in mm XY", "0.05"))
    xy_step_m = xy_step_mm / 1000.0 * scale
    z_step_mm = float(pu.cmdline_input("min step in mm Z", "0"))
    z_step_m = z_step_mm / 1000.0 * scale
    pu.log(f"{a} 1:{scale} XY step {xy_step_m}m Z step {z_step_m}")
    if scale <= 0 or xy_step_m <= 0:
        exit(0)
    o = os.path.splitext(a)[0] + ".stl"
    o = pu.cmdline_input("out", o)
    urls = pu.url_lines(a)
    pu.log(urls)
    urls = pu.download_and_cache(urls, cache_dir=cache_dir)
    pu.log(urls)
    with Pool(20 if len(urls) >= 20 else len(urls)) as pool:
        ddxf = partial(mesh.dxf_to_mesh, cache_dir=cache_dir)
        pool.map(ddxf, urls)
        dgml = partial(mesh.gml_to_mesh, cache_dir=cache_dir)
        pool.map(dgml, urls)
    xyz_cache = mesh.xyz_to_mesh(urls, xy_step_m=xy_step_m, z_step_m=z_step_m, cache_dir=cache_dir)
    urls = [
        mesh.mesh_path(url, cache_dir)
        for url in urls
        if url.endswith(".dxf") or url.endswith(".gml") or pu.zip_has_file(url, ".dxf") or pu.zip_has_file(url, ".gml")
    ]
    if xyz_cache:
        urls.append(xyz_cache)
    pu.log(urls)
    ms = mesh.join_mesh_set(urls)
    pu.log(f"Saving {o}")
    ms.save_current_mesh(o)
    pu.log("Done")
