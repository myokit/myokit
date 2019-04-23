#
# EasyML expression writer
#
# This file is part of Myokit
#  Copyright 2011-2019 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

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
        s = myokit.strfloat(e)
        if '.' not in s:
            return s + '.'
        return s

    #def _ex_prefix_plus(self, e):
    #def _ex_prefix_minus(self, e):
    #def _ex_plus(self, e):
    #def _ex_minus(self, e):
    #def _ex_multiply(self, e):
    #def _ex_divide(self, e):

    def _ex_quotient(self, e):
        # Note that this _must_ round towards minus infinity!
        # See myokit.Quotient !
        self.warn('Potentially unsupported operator: Quotient')
        return self.ex(myokit.Floor(myokit.Divide(e[0], e[1])))

    def _ex_remainder(self, e):
        # Note that this _must_ use the same round-to-neg-inf convention as
        # myokit.Quotient! Implementation below is consistent with Python
        # convention:
        self.warn('Potentially unsupported operator: Remainder')
        return self.ex(myokit.Minus(
            e[0], myokit.Multiply(e[1], myokit.Quotient(e[0], e[1]))))

    def _ex_power(self, e):
        return 'pow(' + self.ex(e[0]) + ', ' + self.ex(e[1]) + ')'

    #def _ex_sqrt(self, e):

    def _ex_sin(self, e):
        self.warn('Potentially unsupported function: sin()')
        super(EasyMLExpressionWriter, self)._ex_sin(e)

    def _ex_cos(self, e):
        self.warn('Potentially unsupported function: cos()')
        super(EasyMLExpressionWriter, self)._ex_cos(e)

    def _ex_tan(self, e):
        self.warn('Potentially unsupported function: tan()')
        super(EasyMLExpressionWriter, self)._ex_tan(e)

    def _ex_asin(self, e):
        self.warn('Potentially unsupported function: asin()')
        super(EasyMLExpressionWriter, self)._ex_asin(e)

    #def _ex_acos(self, e):

    def _ex_atan(self, e):
        self.warn('Potentially unsupported function: atan()')
        super(EasyMLExpressionWriter, self)._ex_atan(e)

    #def _ex_exp(self, e):

    def _ex_log(self, e):
        if len(e) == 1:
            return self._ex_function(e, 'log')
        return '(log(' + self.ex(e[0]) + ') / log(' + self.ex(e[1]) + '))'

    #def _ex_log10(self, e):

    def _ex_floor(self, e):
        self.warn('Potentially unsupported function: floor()')
        super(EasyMLExpressionWriter, self)._ex_floor(e)

    def _ex_ceil(self, e):
        self.warn('Potentially unsupported function: ceil()')
        super(EasyMLExpressionWriter, self)._ex_ceil(e)

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
        self.warn('Potentially unsupported operator: and')
        return self._ex_infix_condition(e, '&&')

    def _ex_or(self, e):
        self.warn('Potentially unsupported operator: or')
        return self._ex_infix_condition(e, '||')

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

