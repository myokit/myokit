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
    def _ex_initial_value(self, e):
        raise NotImplementedError(
            'Initial values are not supported by this expression writer.')

    def _ex_partial_derivative(self, e):
        raise NotImplementedError(
            'Partial derivatives are not supported by this expression writer.')
