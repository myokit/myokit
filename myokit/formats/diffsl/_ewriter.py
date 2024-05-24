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
        return self._ex_function(e, "abs")

    def _ex_acos(self, e):
        warnings.warn("Unsupported function: acos()")
        return super()._ex_acos(e)

    def _ex_asin(self, e):
        warnings.warn("Unsupported function: asin()")
        return super()._ex_asin(e)

    def _ex_atan(self, e):
        warnings.warn("Unsupported function: atan()")
        return super()._ex_atan(e)

    def _ex_ceil(self, e):
        warnings.warn("Unsupported function: ceil()")
        return super()._ex_ceil(e)

    # def _ex_cos(self, e):
    # def _ex_derivative(self, e):
    # def _ex_divide(self, e):
    # def _ex_exp(self, e):

    def _ex_floor(self, e):
        warnings.warn("Unsupported function: floor()")
        return super()._ex_floor(e)

    # def _ex_log(self, e):

    # TODO: log10(x) = (log(x) / log(10))
    def _ex_log10(self, e):
        warnings.warn("Unsupported function: log10()")
        return super()._ex_log10(e)

    def _ex_minus(self, e):
        if isinstance(e[0], myokit.Exp) and isinstance(e[1], myokit.Number):
            if e[1].eval() == 1:
                return f"expm1({self.ex(e[0][0])})"
        if isinstance(e[1], myokit.Exp) and isinstance(e[0], myokit.Number):
            if e[0].eval() == 1:
                return f"-expm1({self.ex(e[1][0])})"
        return super()._ex_minus(e)

    # def _ex_multiply(self, e):
    # def _ex_plus(self, e):

    def _ex_power(self, e):
        return self._ex_function(e, "pow")

    # def _ex_prefix_minus(self, e):
    # def _ex_prefix_plus(self, e):
    # def _ex_quotient(self, e):
    # def _ex_remainder(self, e):
    # def _ex_sin(self, e):
    # def _ex_sqrt(self, e):
    # def _ex_tan(self, e):

    # Boolean operators
    def _ex_and(self, e):
        warnings.warn("Unsupported boolean operator: and")
        return super()._ex_and(e)

    def _ex_equal(self, e):
        warnings.warn("Unsupported boolean operator: equal")
        return super()._ex_equal(e)

    def _ex_less(self, e):
        warnings.warn("Unsupported boolean operator: less")
        return super()._ex_less(e)

    def _ex_less_equal(self, e):
        warnings.warn("Unsupported boolean operator: less_equal")
        return super()._ex_less_equal(e)

    def _ex_more(self, e):
        warnings.warn("Unsupported boolean operator: more")
        return super()._ex_more(e)

    def _ex_more_equal(self, e):
        warnings.warn("Unsupported boolean operator: more_equal")
        return super()._ex_more_equal(e)

    def _ex_not(self, e):
        warnings.warn("Unsupported boolean operator: not")
        return super()._ex_not(e)

    def _ex_not_equal(self, e):
        warnings.warn("Unsupported boolean operator: not_equal")
        return super()._ex_not_equal(e)

    def _ex_or(self, e):
        warnings.warn("Unsupported boolean operator: or")
        return super()._ex_or(e)

    # Conditional expressions

    # TODO: Translate into heaviside()
    def _ex_if(self, e):
        warnings.warn("Unsupported conditional: if")
        return super()._ex_if(e)

    # TODO: Translate into heaviside()
    def _ex_piecewise(self, e):
        warnings.warn("Unsupported conditional: piecewise")
        return super()._ex_piecewise(e)
