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

import myokit

from myokit.formats.ansic import CBasedExpressionWriter


class DiffSLExpressionWriter(CBasedExpressionWriter):
    """
    This :class:`ExpressionWriter <myokit.formats.ExpressionWriter>` writes
    equations for variables in DiffSL syntax.

    For details of the language, see
    https://martinjrobins.github.io/diffsl/introduction.html
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

    # TODO: Implement
    def _ex_derivative(self, e):
        return super()._ex_derivative(e)

    # def _ex_divide(self, e):
    # def _ex_exp(self, e):

    def _ex_floor(self, e):
        warnings.warn('Unsupported function: floor()')
        return super()._ex_floor(e)

    # def _ex_log(self, e):

    def _ex_log10(self, e):
        # Log10(a) = Log(a, 10.0) -> '(log(a) / log(10.0))'
        return super()._ex_log(myokit.Log(e[0], myokit.Number(10)))

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
        return self.ex(myokit.And(myokit.MoreEqual(e[0], e[1]),
                                  myokit.LessEqual(e[0], e[1])))

    def _ex_less(self, e):
        # (a < b) == 1 - heaviside(a - b)
        return self.ex(myokit.Not(myokit.MoreEqual(e[0], e[1])))

    def _ex_less_equal(self, e):
        # (a <= b) == heaviside(b - a)
        return f'heaviside({self.ex(e[1])} - {self.ex(e[0])})'

    def _ex_more(self, e):
        # (a > b) == 1 - heaviside(b - a)
        return self.ex(myokit.Not(myokit.LessEqual(e[0], e[1])))

    def _ex_more_equal(self, e):
        # (a >= b) == heaviside(a - b)
        return f'heaviside({self.ex(e[0])} - {self.ex(e[1])})'

    def _ex_not(self, e):
        if isinstance(e[0], myokit.Not):
            # not(not(a)) == a
            return self.ex(e[0][0])

        if isinstance(e[0], myokit.NotEqual):
            # not(not(a == b)) == (a == b)
            return self.ex(myokit.Equal(e[0][0], e[0][1]))

        if isinstance(e[0], myokit.Less):
            # not(a < b) == (a >= b)
            return self.ex(myokit.MoreEqual(e[0][0], e[0][1]))

        if isinstance(e[0], myokit.More):
            # not(a > b) == (a <= b)
            return self.ex(myokit.LessEqual(e[0][0], e[0][1]))

        if isinstance(e[0], myokit.Or):
            # not(a or b) == not(a) and not(b)
            return self.ex(myokit.And(myokit.Not(e[0][0]), myokit.Not(e[0][1])))

        return f'(1 - {self.ex(e[0])})'

    def _ex_not_equal(self, e):
        # (a != b) == 1 - heaviside(a - b) * heaviside(b - a)
        return self.ex(myokit.Not(myokit.Equal(e[0], e[1])))

    def _ex_or(self, e):
        # a or b == not(not(a) and not(b))
        return self.ex(myokit.Not(myokit.And(myokit.Not(e[0]),
                                             myokit.Not(e[1]))))

    # -- Conditional expressions

    def _ex_if(self, e):
        _if = self.ex(e._i)
        _then = self.ex(e._t)
        _else = self.ex(e._e)

        _not_if = self.ex(myokit.Not(e._i))

        if e._e == myokit.Number(0):
            return f'{_then} * {_if}'

        if e._t == myokit.Number(0):
            return f'{_else} * {_not_if}'

        return f'({_then} * {_if} + {_else} * {_not_if})'

    def _ex_piecewise(self, e):
        # Convert piecewise to nested ifs
        # e.g. piecewise(a, b, c, d, e) -> if(a, b, if(c, d, e))
        n = len(e._i)

        _nested_ifs = None
        _else = e._e[n]

        for i in range(n - 1, -1, -1):
            _nested_ifs = myokit.If(e._i[i], e._e[i], _else)
            _else = _nested_ifs

        return self._ex_if(_nested_ifs)
