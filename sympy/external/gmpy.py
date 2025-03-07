import os
from ctypes import c_long, sizeof
from functools import reduce
from typing import Tuple as tTuple, Type

from sympy.external import import_module

from .pythonmpq import PythonMPQ

from .ntheory import (
    bit_scan1 as python_bit_scan1,
    bit_scan0 as python_bit_scan0,
    factorial as python_factorial,
    sqrt as python_sqrt,
    sqrtrem as python_sqrtrem,
    gcd as python_gcd,
    lcm as python_lcm,
    is_square as python_is_square,
    invert as python_invert,
    legendre as python_legendre,
    jacobi as python_jacobi,
    kronecker as python_kronecker,
    iroot as python_iroot,
    is_fermat_prp as python_is_fermat_prp,
    is_euler_prp as python_is_euler_prp,
    is_strong_prp as python_is_strong_prp,
)


__all__ = [
    # GROUND_TYPES is either 'gmpy' or 'python' depending on which is used. If
    # gmpy is installed then it will be used unless the environment variable
    # SYMPY_GROUND_TYPES is set to something other than 'auto', 'gmpy', or
    # 'gmpy2'.
    'GROUND_TYPES',

    # If HAS_GMPY is 0, no supported version of gmpy is available. Otherwise,
    # HAS_GMPY will be 2 for gmpy2 if GROUND_TYPES is 'gmpy'. It used to be
    # possible for HAS_GMPY to be 1 for gmpy but gmpy is no longer supported.
    'HAS_GMPY',

    # SYMPY_INTS is a tuple containing the base types for valid integer types.
    # This is either (int,) or (int, type(mpz(0))) depending on GROUND_TYPES.
    'SYMPY_INTS',

    # MPQ is either gmpy.mpq or the Python equivalent from
    # sympy.external.pythonmpq
    'MPQ',

    # MPZ is either gmpy.mpz or int.
    'MPZ',

    'bit_scan1',
    'bit_scan0',
    'factorial',
    'sqrt',
    'is_square',
    'sqrtrem',
    'gcd',
    'lcm',
    'invert',
    'legendre',
    'jacobi',
    'kronecker',
    'iroot',
    'is_fermat_prp',
    'is_euler_prp',
    'is_strong_prp',
]


#
# SYMPY_GROUND_TYPES can be gmpy, gmpy2, python or auto
#
GROUND_TYPES = os.environ.get('SYMPY_GROUND_TYPES', 'auto').lower()


#
# Try to import gmpy2 by default. If gmpy or gmpy2 is specified in
# SYMPY_GROUND_TYPES then warn if gmpy2 is not found. In all cases there is a
# fallback based on pure Python int and PythonMPQ that should still work fine.
#
if GROUND_TYPES in ('auto', 'gmpy', 'gmpy2'):

    # Actually import gmpy2
    gmpy = import_module('gmpy2', min_module_version='2.0.0',
                module_version_attr='version', module_version_attr_call_args=())
    flint = None

    if gmpy is None:
        # Warn if user explicitly asked for gmpy but it isn't available.
        if GROUND_TYPES != 'auto':
            from warnings import warn
            warn("gmpy library is not installed, switching to 'python' ground types")

        # Fall back to Python if gmpy2 is not available
        GROUND_TYPES = 'python'
    else:
        GROUND_TYPES = 'gmpy'

elif GROUND_TYPES == 'flint':

    # Try to use python_flint
    flint = import_module('flint')
    gmpy = None

    if flint is None:
        from warnings import warn
        warn("python_flint is not installed, switching to 'python' ground types")
        GROUND_TYPES = 'python'
    else:
        GROUND_TYPES = 'flint'

elif GROUND_TYPES == 'python':

    # The user asked for Python so ignore gmpy2/flint
    gmpy = None
    flint = None
    GROUND_TYPES = 'python'

else:

    # Invalid value for SYMPY_GROUND_TYPES. Warn and default to Python.
    from warnings import warn
    warn("SYMPY_GROUND_TYPES environment variable unrecognised. "
         "Should be 'python', 'auto', 'gmpy', or 'gmpy2'")
    gmpy = None
    flint = None
    GROUND_TYPES = 'python'


#
# At this point gmpy will be None if gmpy2 was not successfully imported or if
# the environment variable SYMPY_GROUND_TYPES was set to 'python' (or some
# unrecognised value). The two blocks below define the values exported by this
# module in each case.
#
SYMPY_INTS: tTuple[Type, ...]

#
# In gmpy2 and flint, there are functions that take a long (or unsigned long) argument.
# That is, it is not possible to input a value larger than that.
#
LONG_MAX = (1 << (8*sizeof(c_long) - 1)) - 1

if GROUND_TYPES == 'gmpy':

    HAS_GMPY = 2
    GROUND_TYPES = 'gmpy'
    SYMPY_INTS = (int, type(gmpy.mpz(0)))
    MPZ = gmpy.mpz
    MPQ = gmpy.mpq

    bit_scan1 = gmpy.bit_scan1
    bit_scan0 = gmpy.bit_scan0
    factorial = gmpy.fac
    sqrt = gmpy.isqrt
    is_square = gmpy.is_square
    sqrtrem = gmpy.isqrt_rem
    gcd = gmpy.gcd
    lcm = gmpy.lcm
    invert = gmpy.invert
    legendre = gmpy.legendre
    jacobi = gmpy.jacobi
    kronecker = gmpy.kronecker

    def iroot(x, n):
        # In the latest gmpy2, the threshold for n is ULONG_MAX,
        # but adjust to the older one.
        if n <= LONG_MAX:
            return gmpy.iroot(x, n)
        return python_iroot(x, n)

    is_fermat_prp = gmpy.is_fermat_prp
    is_euler_prp = gmpy.is_euler_prp
    is_strong_prp = gmpy.is_strong_prp

elif GROUND_TYPES == 'flint':

    HAS_GMPY = 0
    GROUND_TYPES = 'flint'
    SYMPY_INTS = (int, flint.fmpz) # type: ignore
    MPZ = flint.fmpz # type: ignore
    MPQ = flint.fmpq # type: ignore

    bit_scan1 = python_bit_scan1
    bit_scan0 = python_bit_scan0
    factorial = python_factorial

    def sqrt(x):
        return flint.fmpz(x).isqrt()

    def is_square(x):
        if x < 0:
            return False
        return flint.fmpz(x).sqrtrem()[1] == 0

    def sqrtrem(x):
        return flint.fmpz(x).sqrtrem()

    def gcd(*args):
        return reduce(flint.fmpz.gcd, args, flint.fmpz(0))

    def lcm(*args):
        return reduce(flint.fmpz.lcm, args, flint.fmpz(1))

    invert = python_invert
    legendre = python_legendre

    def jacobi(x, y):
        if y <= 0 or not y % 2:
            raise ValueError("y should be an odd positive integer")
        return flint.fmpz(x).jacobi(y)

    kronecker = python_kronecker

    def iroot(x, n):
        if n <= LONG_MAX:
            y = flint.fmpz(x).root(n)
            return y, y**n == x
        return python_iroot(x, n)

    is_fermat_prp = python_is_fermat_prp
    is_euler_prp = python_is_euler_prp
    is_strong_prp = python_is_strong_prp

elif GROUND_TYPES == 'python':

    HAS_GMPY = 0
    GROUND_TYPES = 'python'
    SYMPY_INTS = (int,)
    MPZ = int
    MPQ = PythonMPQ

    bit_scan1 = python_bit_scan1
    bit_scan0 = python_bit_scan0
    factorial = python_factorial
    sqrt = python_sqrt
    is_square = python_is_square
    sqrtrem = python_sqrtrem
    gcd = python_gcd
    lcm = python_lcm
    invert = python_invert
    legendre = python_legendre
    jacobi = python_jacobi
    kronecker = python_kronecker
    iroot = python_iroot
    is_fermat_prp = python_is_fermat_prp
    is_euler_prp = python_is_euler_prp
    is_strong_prp = python_is_strong_prp

else:
    assert False
