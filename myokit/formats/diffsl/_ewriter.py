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

    # Literals and identifiers
    # def _ex_name(self, e):
    # def _ex_number(self, e):

    # Functions
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

    # Boolean operators
    def _ex_and(self, e):
        warnings.warn('Unsupported boolean operator: and')
        return super()._ex_and(e)

    def _ex_equal(self, e):
        warnings.warn('Unsupported boolean operator: equal')
        return super()._ex_equal(e)

    def _ex_less(self, e):
        warnings.warn('Unsupported boolean operator: less')
        return super()._ex_less(e)

    def _ex_less_equal(self, e):
        warnings.warn('Unsupported boolean operator: less_equal')
        return super()._ex_less_equal(e)

    def _ex_more(self, e):
        warnings.warn('Unsupported boolean operator: more')
        return super()._ex_more(e)

    def _ex_more_equal(self, e):
        warnings.warn('Unsupported boolean operator: more_equal')
        return super()._ex_more_equal(e)

    def _ex_not(self, e):
        warnings.warn('Unsupported boolean operator: not')
        return super()._ex_not(e)

    def _ex_not_equal(self, e):
        warnings.warn('Unsupported boolean operator: not_equal')
        return super()._ex_not_equal(e)

    def _ex_or(self, e):
        warnings.warn('Unsupported boolean operator: or')
        return super()._ex_or(e)

    # Conditional expressions

    def _ex_if(self, e):
        if isinstance(e._i, myokit.Condition):
            if any(isinstance(x, myokit.Condition) for x in e._i):
                # Nested conditions are not supported
                raise NotImplementedError

            # General form: if(a op b) then c else d
            a = self.ex(e._i[0])
            c = self.ex(e._t)
            d = self.ex(e._e)

            # if (a), same as if (a != 0)
            if not isinstance(e._i, myokit.Condition):
                return f'({c} + heaviside({a}) * heaviside(-{a}) * ({d} - {c}))'

            # if (not a), same as if (a == 0)
            if isinstance(e._i, myokit.Not):
                return f'({d} + heaviside({a}) * heaviside(-{a}) * ({c} - {d}))'

            # Need b for binary ops from here on
            b = self.ex(e._i[1])

            # if (a == b)
            if isinstance(e._i, myokit.Equal):
                return f'({d} + heaviside({a} - {b}) * heaviside({b} - {a}) * ({c} - {d}))'

            # if (a != b)
            if isinstance(e._i, myokit.NotEqual):
                return f'({c} + heaviside({a} - {b}) * heaviside({b} - {a}) * ({d} - {c}))'

            # if (a > b)
            if isinstance(e._i, myokit.More):
                return f'({c} + heaviside({b} - {a}) * ({d} - {c}))'

            # if (a >= b)
            if isinstance(e._i, myokit.MoreEqual):
                return f'({d} + heaviside({a} - {b}) * ({c} - {d}))'

            # if (a < b)
            if isinstance(e._i, myokit.Less):
                return f'({c} + heaviside({a} - {b}) * ({d} - {c}))'

            # if (a <= b)
            if isinstance(e._i, myokit.LessEqual):
                return f'({d} + heaviside({b} - {a}) * ({c} - {d}))'

            # Other conditions are not supported
            raise NotImplementedError

    def _ex_piecewise(self, e):
        return super()._ex_piecewise(e)
