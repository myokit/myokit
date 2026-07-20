#
# DiffSL expression writer
#
# Supported functions:
#  https://martinjrobins.github.io/diffsl/functions.html
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import warnings

from myokit import And, Equal, LessEqual, Log, MoreEqual, Not, Number
from myokit.formats.ansic import CBasedExpressionWriter


class DiffSLExpressionWriter(CBasedExpressionWriter):
    """
    This :class:`ExpressionWriter <myokit.formats.ExpressionWriter>` writes
    equations for variables in DiffSL syntax.

    For details of the language, see https://martinjrobins.github.io/diffsl/.

    Warnings will be generated if unsupported functions are used in the model.
    Unsupported functions: `acos`, `asin`, `atan`, `ceil`, `floor`.

    Support for logic expressions is implemented with heaviside functions.
    For example, `(a >= b)` is converted to `heaviside(a - b)`.

    """

    def __init__(self):
        super().__init__()

    # -- Literals and identifiers

    # def _ex_name(self, e):
    # def _ex_number(self, e):

    # -- Functions

    def _ex_abs(self, e):
        return self._ex_function(e, 'abs')

    def _ex_acos(self, e):
        warnings.warn('Unsupported function: acos()')
        return super()._ex_acos(e)

    def _ex_asin(self, e):
        warnings.warn('Unsupported function: asin()')
        return super()._ex_asin(e)

    def _ex_atan(self, e):
        warnings.warn('Unsupported function: atan()')
        return super()._ex_atan(e)

    def _ex_ceil(self, e):
        warnings.warn('Unsupported function: ceil()')
        return super()._ex_ceil(e)

    # def _ex_cos(self, e):
    # def _ex_derivative(self, e):
    # def _ex_divide(self, e):
    # def _ex_exp(self, e):

    def _ex_floor(self, e):
        warnings.warn('Unsupported function: floor()')
        return super()._ex_floor(e)

    # def _ex_log(self, e):

    def _ex_log10(self, e):
        # Log10(a) = Log(a, 10.0) -> '(log(a) / log(10.0))'
        return super()._ex_log(Log(e[0], Number(10)))

    # def _ex_minus(self, e):
    # def _ex_multiply(self, e):
    # def _ex_plus(self, e):
    # def _ex_power(self, e):
    # def _ex_prefix_minus(self, e):
    # def _ex_prefix_plus(self, e):
    # def _ex_quotient(self, e):
    # def _ex_remainder(self, e):
    # def _ex_sin(self, e):
    # def _ex_sqrt(self, e):
    # def _ex_tan(self, e):

    # -- Conditional operators

    def _ex_and(self, e):
        # (a and b) == a * b, where a, b are in {0, 1}
        return f'{self.ex(e[0])} * {self.ex(e[1])}'

    def _ex_equal(self, e):
        # (a == b) == heaviside(a - b) * heaviside(b - a)
        return self.ex(And(MoreEqual(e[0], e[1]), LessEqual(e[0], e[1])))

    def _ex_less(self, e):
        # (a < b) == 1 - heaviside(a - b)
        return self.ex(Not(MoreEqual(e[0], e[1])))

    def _ex_less_equal(self, e):
        # (a <= b) == heaviside(b - a)
        return f'heaviside({self.ex(e[1])} - {self.ex(e[0])})'

    def _ex_more(self, e):
        # (a > b) == 1 - heaviside(b - a)
        return self.ex(Not(LessEqual(e[0], e[1])))

    def _ex_more_equal(self, e):
        # (a >= b) == heaviside(a - b)
        return f'heaviside({self.ex(e[0])} - {self.ex(e[1])})'

    def _ex_not(self, e):
        # not(a) == (1 - a), where a is in {0, 1}
        return f'(1 - {self.ex(e[0])})'

    def _ex_not_equal(self, e):
        # (a != b) == 1 - heaviside(a - b) * heaviside(b - a)
        return self.ex(Not(Equal(e[0], e[1])))

    def _ex_or(self, e):
        # a or b == not(not(a) and not(b)), where a, b are in {0, 1}
        return self.ex(Not(And(Not(e[0]), Not(e[1]))))

    # -- Conditional expressions

    def _ex_if(self, e):
        _condition = self.ex(e._i)
        _then = self.ex(e._t)
        _else = self.ex(e._e)

        return f'piecewise({_condition} - 0.5, {_then}, {_else})'

    def _ex_piecewise(self, e):
        n = len(e._i)
        parts = []

        for i in range(n):
            _condition = self.ex(e._i[i])
            _value = self.ex(e._e[i])
            parts.append(f'{_condition} - 0.5')
            parts.append(_value)

        _fallback = self.ex(e._e[n])
        parts.append(_fallback)

        return f'piecewise({", ".join(parts)})'
