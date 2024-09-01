"""Convert swiss alti and/or buildings to mesh"""

import os
from functools import partial
from multiprocessing import Pool, cpu_count

import mesh
import utils as pu

if __name__ == "__main__":
    cache_dir = ".cache"
    # a = pu.cmdline_input("csv", R"N:\code\winplay\testdata\zh-large.csv")
    a = pu.cmdline_input("csv", R"N:\code\winplay\testdata\swissbuildings2.csv")
    pu.log(a)
    o = os.path.splitext(a)[0] + ".stl"
    o = pu.cmdline_input("out", o)
    urls = pu.url_lines(a)
    pu.log(urls)
    urls = pu.download_and_cache(urls, cache_dir=cache_dir)
    pu.log(urls)
    with Pool(cpu_count()) as pool:
        dxyz = partial(mesh.xyz_to_mesh, cache_dir=cache_dir)
        ddxf = partial(mesh.dxf_to_mesh, cache_dir=cache_dir)
        pool.map(dxyz, urls)
        pool.map(ddxf, urls)
    urls = [mesh.mesh_path(url, cache_dir) for url in urls]
    pu.log(urls)
    ms = mesh.join_mesh_set(urls)
    pu.log("Saving")
    ms.save_current_mesh(o)
    pu.log("Done")
