"""ScratchPad"""

import os

import numpy as np
import pymeshlab

import mesh
import utils as pu


def test_mesh():
    v = np.ndarray(shape=(3, 3))
    f = np.zeros(shape=(1, 3))
    v[0][:] = (0, 0, 0)
    v[1][:] = (1, 1, 1)
    v[2][:] = (2, 2, 0)
    f[0][:] = (0, 1, 2)
    print(v, f)

    ms = pymeshlab.MeshSet()
    m = pymeshlab.Mesh(v, f)
    print(m)
    ms.add_mesh(m)
    print('Added')
    ms.save_current_mesh("N:\\3d\\build\\test.obj", save_vertex_normal=False, save_vertex_color=False)
    print('OK')


def test_urls():
    # a = pu.cmdline_input("csv", R"N:\code\winplay\testdata\zh-large.csv")
    # a = pu.cmdline_input("csv", R"N:\code\winplay\testdata\zh-large.csv")
    a = pu.cmdline_input("csv", R"N:\code\winplay\testdata\swissbuildings2.csv")
    print(a)
    o = f".cache\\{os.path.splitext(os.path.basename(a))[0]}.ply"
    o = pu.cmdline_input("out", o)
    urls = pu.url_lines(a)
    print(urls)
    urls = pu.download_and_cache(urls)
    print(urls)
    if len([url for url in urls if "xyz" in url]) > 0:
        ms = mesh.xyz_to_mesh(urls)
    else:
        ms = mesh.dxf_to_mesh(urls)
    print("Saving")
    ms.save_current_mesh(o, save_vertex_normal=False, save_vertex_color=False)
    print("Done")


if __name__ == "__main__":
    test_urls()
