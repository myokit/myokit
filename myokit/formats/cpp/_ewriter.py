#
# C++ expression writer
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from myokit.formats.ansic import AnsiCExpressionWriter


class CppExpressionWriter(AnsiCExpressionWriter):
    """
    This :class:`ExpressionWriter <myokit.formats.ExpressionWriter>` translates
    myokit :class:`expressions <myokit.Expression>` to their C++ equivalent.
    """
    # Note: The set_condition_function is used by the jacobian calculator
    # Once that has gone, this can base off the CBasedExpressionWriter without
    # any modifications (so two methods below can then go).

    def _ex_initial_value(self, e):
        raise NotImplementedError(
            'Initial values are not supported by this expression writer.')

    def _ex_partial_derivative(self, e):
        raise NotImplementedError(
            'Partial derivatives are not supported by this expression writer.')

