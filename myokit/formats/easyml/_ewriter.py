#
# EasyML expression writer
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import warnings

import myokit
from myokit.formats.python import PythonExpressionWriter


class EasyMLExpressionWriter(PythonExpressionWriter):
    """
    This :class:`ExpressionWriter <myokit.formats.ExpressionWriter>` writes
    equations for variables in EasyML syntax.
    """
    def __init__(self):
        super(EasyMLExpressionWriter, self).__init__()
        self._function_prefix = ''

    #def _ex_name(self, e):
    #def _ex_derivative(self, e):

    def _ex_number(self, e):
        return myokit.float.str(e)

    #def _ex_prefix_plus(self, e):
    #def _ex_prefix_minus(self, e):
    #def _ex_plus(self, e):

    def _ex_minus(self, e):
        if isinstance(e[0], myokit.Exp) and isinstance(e[1], myokit.Number):
            if e[1].eval() == 1:
                return 'expm1(' + self.ex(e[0][0]) + ')'
        if isinstance(e[1], myokit.Exp) and isinstance(e[0], myokit.Number):
            if e[0].eval() == 1:
                return '-expm1(' + self.ex(e[1][0]) + ')'
        return super(EasyMLExpressionWriter, self)._ex_minus(e)

    #def _ex_multiply(self, e):
    #def _ex_divide(self, e):

    def _ex_quotient(self, e):
        return self.ex(myokit.Floor(myokit.Divide(e[0], e[1])))

    def _ex_remainder(self, e):
        return self.ex(myokit.Minus(
            e[0], myokit.Multiply(e[1], myokit.Quotient(e[0], e[1]))))

    def _ex_power(self, e):
        return 'pow(' + self.ex(e[0]) + ', ' + self.ex(e[1]) + ')'

    #def _ex_sqrt(self, e):

    def _ex_sin(self, e):
        warnings.warn('Potentially unsupported function: sin()')
        return super(EasyMLExpressionWriter, self)._ex_sin(e)

    #def _ex_cos(self, e):

    def _ex_tan(self, e):
        warnings.warn('Potentially unsupported function: tan()')
        return super(EasyMLExpressionWriter, self)._ex_tan(e)

    def _ex_asin(self, e):
        warnings.warn('Potentially unsupported function: asin()')
        return super(EasyMLExpressionWriter, self)._ex_asin(e)

    #def _ex_acos(self, e):

    def _ex_atan(self, e):
        warnings.warn('Potentially unsupported function: atan()')
        return super(EasyMLExpressionWriter, self)._ex_atan(e)

    #def _ex_exp(self, e):

    def _ex_log(self, e):
        if len(e) == 1:
            return self._ex_function(e, 'log')
        return '(log(' + self.ex(e[0]) + ') / log(' + self.ex(e[1]) + '))'

    #def _ex_log10(self, e):

    def _ex_floor(self, e):
        warnings.warn('Potentially unsupported function: floor()')
        return super(EasyMLExpressionWriter, self)._ex_floor(e)

    def _ex_ceil(self, e):
        warnings.warn('Potentially unsupported function: ceil()')
        return super(EasyMLExpressionWriter, self)._ex_ceil(e)

    def _ex_abs(self, e):
        return self._ex_function(e, 'fabs')

    def _ex_not(self, e):
        return '!(' + self.ex(e[0]) + ')'

    #def _ex_equal(self, e):
    #def _ex_not_equal(self, e):
    #def _ex_more(self, e):
    #def _ex_less(self, e):
    #def _ex_more_equal(self, e):
    #def _ex_less_equal(self, e):

    def _ex_and(self, e):
        return self._ex_infix_condition(e, 'and')

    def _ex_or(self, e):
        return self._ex_infix_condition(e, 'or')

    def _ex_if(self, e):
        ite = (self.ex(e._i), self.ex(e._t), self.ex(e._e))
        return '(%s ? %s : %s)' % ite

    def _ex_piecewise(self, e):
        s = []
        n = len(e._i)
        for i in range(0, n):
            s.append('(%s ? %s : ' % (self.ex(e._i[i]), self.ex(e._e[i])))
        s.append(self.ex(e._e[n]))
        s.append(')' * n)
        return ''.join(s)

