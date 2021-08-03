#
# Functions related to floating point numbers. Imported by default.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import sys

import myokit

# Store ref to built-in `round` and `str` functions
_round = round
_str = str


def close(a, b, reltol=1e-9, abstol=1e-9):
    """
    Test whether two numbers are close enough to be considered equal.

    Differs from :meth:`myokit.float.eq` in that it tries to answer the
    question "are two numbers resulting from various calculations close enough
    to be considered equal". Whereas :meth`myokit.float.eq` aims to deal with
    umbers that are numerically indistinguishable but still have a slightly
    different floating point representation.
    """
    # Note the initial == check handles infinity
    return a == b or abs(a - b) < max(reltol * max(abs(a), abs(b)), abstol)


def cround(x, reltol=1e-9, abstol=1e-9):
    """
    Checks if a float ``x`` is close to an integer with :meth:`close()`, and if
    so, returns that integer.
    """
    ix = int(_round(x))
    return ix if close(x, ix, reltol, abstol) else x


def eq(a, b):
    """
    Checks if floating point numbers ``a`` and ``b`` are equal, or so close to
    each other that the difference could be a single rounding error.
    """
    # Note the initial == check handles infinity
    return a == b or abs(a - b) < max(abs(a), abs(b)) * sys.float_info.epsilon


def geq(a, b):
    """
    Checks if ``a >= b``, but using :meth:`myokit.float.eq` instead of ``==``.
    """
    return a >= b or abs(a - b) < max(abs(a), abs(b)) * sys.float_info.epsilon


def round(x):
    """
    Checks if a float ``x`` is within a single rounding error of an integer,
    and if so, returns that integer.
    """
    ix = int(_round(x))
    return ix if eq(x, ix) else x


def str(number, full=False, precision=myokit.DOUBLE_PRECISION):
    """
    Converts the given number to a string, using a full-precision
    representation if needed.

    Arguments:

    ``full``
        Set to ``True`` to force full precision output.
    ``precision``
        Set to ``myokit.SINGLE_PRECISION`` to assume single-precision numbers
        when formatting with full precision.

    """
    # Force full precision output
    if full:
        if precision == myokit.SINGLE_PRECISION:
            return myokit.SFSINGLE.format(float(number))
        else:
            return myokit.SFDOUBLE.format(float(number))

    # Pass through strings
    if isinstance(number, _str):
        return number

    # Handle myokit.Numbers
    if isinstance(number, myokit.Number):
        number = number.eval()

    # For most numbers, allow python to format the float
    s = _str(number)
    if len(s) < 10:
        return s

    # But if the number is given with lots of decimals, use the representation
    # with enough digits to prevent loss of information
    if precision == myokit.SINGLE_PRECISION:
        return myokit.SFSINGLE.format(float(number))
    else:
        return myokit.SFDOUBLE.format(float(number))

