"""ScratchPad"""

import numpy as np
import pymeshlab

import utils as pu


def test_mesh():
    v = np.ndarray(shape=(3, 3))
    f = np.zeros(shape=(1, 3))
    v[0][:] = (0, 0, 0)
    v[1][:] = (1, 1, 1)
    v[2][:] = (2, 2, 0)
    f[0][:] = (0, 1, 2)
    pu.log(v, f)

    m = pymeshlab.Mesh(v, f)
    m.meshing_merge_close_vertices(threshold=pymeshlab.PercentageValue(0.001))
    pu.log(m)
    ms = pymeshlab.MeshSet()
    ms.add_mesh(m)
    pu.log("Added")
    ms.save_current_mesh("N:\\3d\\build\\test.obj", save_vertex_normal=False, save_vertex_color=False)
    pu.log("OK")


def show_ply():
    # fname = pu.cmdline_input("path", R"N:\code\winplay\.cache\Sample_swissBUILDINGS3D20_LV95.ply")
    fname = pu.cmdline_input("path", R"N:\code\winplay\.cache\SWISSALTI3D_2_XYZ_CHLV95_LN02_2600_1196.ply")

    ms = pymeshlab.MeshSet()
    ms.load_new_mesh(fname)
    ms.show_polyscope()


if __name__ == "__main__":
    show_ply()
