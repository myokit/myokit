#
# OpenCL expression writer
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import myokit

from myokit.formats.ansic import CBasedExpressionWriter


class OpenCLExpressionWriter(CBasedExpressionWriter):
    """
    This :class:`ExpressionWriter <myokit.formats.ExpressionWriter>` translates
    Myokit :class:`expressions <myokit.Expression>` to OpenCL syntax.

    Arguments:

    ``precision``
        By default, numbers are shown as e.g. ``1.23f``, denoting single
        precision literals. To use double precision instead, set ``precision``
        to ``myokit.DOUBLE_PRECISION``.
    ``native_math``
        By default, the software implementations of functions like ``log`` and
        ``exp`` are used. To use the native version instead, set
        ``native_math`` to ``True``.

    """
    def __init__(self, precision=myokit.SINGLE_PRECISION, native_math=True):
        super().__init__()
        self._sp = (precision == myokit.SINGLE_PRECISION)
        self._nm = bool(native_math)

    #def _ex_name(self, e):
    #def _ex_derivative(self, e):
    #def _ex_initial_value(self, e):
    #def _ex_partial_derivative(self, e):

    def _ex_number(self, e):
        x = super()._ex_number(e)
        return x + 'f' if self._sp else x

    #def _ex_prefix_plus(self, e):
    #def _ex_prefix_minus(self, e):
    #def _ex_plus(self, e):
    #def _ex_minus(self, e):
    #def _ex_multiply(self, e):

    # Native divide seemed to cause some issues
    #def _ex_divide(self, e):
    #    if self._nm:
    #        return 'native_divide(' + self.ex(e[0]) +', '+ self.ex(e[1]) + ')'
    #    return self._ex_infix(e, '/')

    #def _ex_quotient(self, e):
    #def _ex_remainder(self, e):
    #def _ex_power(self, e):

    def _ex_sqrt(self, e):
        f = 'native_sqrt' if self._nm else 'sqrt'
        return self._ex_function(e, f)

    def _ex_sin(self, e):
        f = 'native_sin' if self._nm else 'sin'
        return self._ex_function(e, f)

    def _ex_cos(self, e):
        f = 'native_cos' if self._nm else 'cos'
        return self._ex_function(e, f)

    def _ex_tan(self, e):
        f = 'native_tan' if self._nm else 'tan'
        return self._ex_function(e, f)

    #def _ex_asin(self, e):
    #def _ex_acos(self, e):
    #def _ex_atan(self, e):

    def _ex_exp(self, e):
        f = 'native_exp' if self._nm else 'exp'
        return self._ex_function(e, f)

    def _ex_log(self, e):
        log = 'native_log' if self._nm else 'log'
        if len(e) == 1:
            return self._ex_function(e, log)
        # Always add brackets: parent was expecting a function so will never
        # have added them.
        return f'({log}({self.ex(e[0])}) / {log}({self.ex(e[1])}))'

    def _ex_log10(self, e):
        f = 'native_log10' if self._nm else 'log10'
        return self._ex_function(e, f)

    #def _ex_floor(self, e):
    #def _ex_ceil(self, e):
    #def _ex_abs(self, e):

    #def _ex_equal(self, e):
    #def _ex_not_equal(self, e):
    #def _ex_more(self, e):
    #def _ex_less(self, e):
    #def _ex_more_equal(self, e):
    #def _ex_less_equal(self, e):

    #def _ex_and(self, e):
    #def _ex_or(self, e):
    #def _ex_not(self, e):
    #def _ex_if(self, e):
    #def _ex_piecewise(self, e):

