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
        # bool(a) and bool(b), where bool(a) = (a == 0) ? 0 : 1
        a = self.ex(e[0])
        b = self.ex(e[1])

        if not isinstance(e[0], myokit.Condition):
            a = f'(1 - heaviside({a}) * heaviside(-{a}))'

        if not isinstance(e[1], myokit.Condition):
            b = f'(1 - heaviside({b}) * heaviside(-{b}))'

        return f'({a} * {b})'

    def _ex_equal(self, e):
        a = self.ex(e[0])
        b = self.ex(e[1])
        return f'(heaviside({a} - {b}) * heaviside({b} - {a}))'

    def _ex_less(self, e):
        a = self.ex(e[0])
        b = self.ex(e[1])
        return f'(1 - heaviside({a} - {b}))'

    def _ex_less_equal(self, e):
        a = self.ex(e[0])
        b = self.ex(e[1])
        return f'heaviside({b} - {a})'

    def _ex_more(self, e):
        a = self.ex(e[0])
        b = self.ex(e[1])
        return f'(1 - heaviside({b} - {a}))'

    def _ex_more_equal(self, e):
        a = self.ex(e[0])
        b = self.ex(e[1])
        return f'heaviside({a} - {b})'

    def _ex_not(self, e):
        # not(a) = (a == 0) ? 1 : 0
        a = self.ex(e[0])

        if isinstance(e[0], myokit.Condition):
            return f'(1 - {a})'

        return f'(heaviside({a}) * heaviside(-{a}))'

    def _ex_not_equal(self, e):
        a = self.ex(e[0])
        b = self.ex(e[1])
        return f'(1 - heaviside({a} - {b}) * heaviside({b} - {a}))'

    def _ex_or(self, e):
        # bool(a) or bool(b), where bool(a) = (a == 0) ? 0 : 1
        a = self.ex(e[0])
        b = self.ex(e[1])

        # a or b = not(not(a) and not(b))
        if isinstance(e[0], myokit.Condition):
            not_a = f'(1 - {a})'
        else:
            not_a = f'heaviside({a}) * heaviside(-{a})'

        if isinstance(e[1], myokit.Condition):
            not_b = f'(1 - {b})'
        else:
            not_b = f'heaviside({b}) * heaviside(-{b})'

        return f'(1 - {not_a} * {not_b})'

    # -- Conditional expressions

    def _ex_if(self, e):
        if isinstance(e._i, myokit.Condition):
            _if = self.ex(e._i)
        else:
            # `if (a)` is the same as `if (1 - not(a))`
            _if = f'(1 - {self.ex(myokit.Not(e._i))})'

        _then = self.ex(e._t)
        _else = self.ex(e._e)

        return f'({_then} * {_if} + {_else} * (1 - {_if}))'

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
