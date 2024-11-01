from setuptools import Extension, setup
from Cython.Build import cythonize
import numpy

extensions = [
    Extension("*", ["cy/cyutils.pyx"], include_dirs=[numpy.get_include()]),
    Extension("*", ["cy/triangulate.pyx"]),
]
setup(
    name="cyutils",
    ext_modules=cythonize(extensions, compiler_directives={"language_level": "3"}),
)
