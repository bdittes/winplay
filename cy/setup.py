from setuptools import Extension, setup
from Cython.Build import cythonize
import numpy

extensions = [
    Extension("*", ["cy/cyutils.pyx"], include_dirs=[numpy.get_include()]),
]
setup(
    name="cyutils",
    ext_modules=cythonize(extensions),
)
