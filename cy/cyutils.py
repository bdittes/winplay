"""Cython utils"""

import cython
import numpy


def fib(n):
    """Print the Fibonacci series up to n."""
    a: cython.int = 0
    b: cython.int = 1
    while b < n:
        print(b, end=" ")
        a, b = b, a + b

    print(numpy.zeros(shape=(2, 3)))


def nptest(a: numpy.array) -> numpy.array:
    x = numpy.sum(a)
    r = numpy.zeros(shape=(1, 1))
    r[0][0] = x
    return r
