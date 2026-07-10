#
# FPGA expression writer
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import myokit

from myokit.formats.ansic import CBasedExpressionWriter


class FPGAExpressionWriter(CBasedExpressionWriter):
    """
    This :class:`ExpressionWriter <myokit.formats.ExpressionWriter>` translates
    Myokit :class:`expressions <myokit.Expression>` to a C99 syntax with
    support for single precision, and with small integer powers replaced by
    multiplication.

    Arguments:

    ``precision``
        By default, numbers are shown as e.g. ``1.23f``, denoting single
        precision literals. To use double precision instead, set ``precision``
        to ``myokit.DOUBLE_PRECISION``.

    """
    def __init__(self, precision=myokit.SINGLE_PRECISION, rewrite_pow=True):
        super().__init__()
        self._sp = (precision == myokit.SINGLE_PRECISION)
        self._rp = bool(rewrite_pow)

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
    #def _ex_divide(self, e):
    #def _ex_quotient(self, e):
    #def _ex_remainder(self, e):

    def _ex_power(self, e):
        if self._rp:
            i = myokit.float.round(e[1].value())
            if isinstance(i, int):
                expr = ' * '.join([self.ex(e[0])] * i)
                return f'({expr})'  # Expecting function, so add brackets
        return super()._exp_power(e)

    def _ex_sqrt(self, e):
        return self._ex_function(e, 'sqrtf' if self._sp else 'sqrt')

    def _ex_sin(self, e):
        return self._ex_function(e, 'sinf' if self._sp else 'sin')

    def _ex_cos(self, e):
        return self._ex_function(e, 'cosf' if self._sp else 'cos')

    def _ex_tan(self, e):
        return self._ex_function(e, 'tanf' if self._sp else 'tan')

    def _ex_asin(self, e):
        return self._ex_function(e, 'asinf' if self._sp else 'asin')

    def _ex_acos(self, e):
        return self._ex_function(e, 'acosf' if self._sp else 'acos')

    def _ex_atan(self, e):
        return self._ex_function(e, 'atanf' if self._sp else 'atan')

    def _ex_exp(self, e):
        return self._ex_function(e, 'expf' if self._sp else 'exp')

    def _ex_log(self, e):
        log = 'logf' if self._sp else 'log'
        if len(e) == 1:
            return self._ex_function(e, log)
        # Always add brackets: parent was expecting a function so will never
        # have added them.
        return f'({log}({self.ex(e[0])}) / {log}({self.ex(e[1])}))'

    def _ex_log10(self, e):
        return self._ex_function(e, 'log10f' if self._sp else 'log10')

    def _ex_floor(self, e):
        return self._ex_function(e, 'floorf' if self._sp else 'floor')

    def _ex_ceil(self, e):
        return self._ex_function(e, 'ceilf' if self._sp else 'ceil')

    def _ex_abs(self, e):
        return self._ex_function(e, 'absf' if self._sp else 'abs')

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

