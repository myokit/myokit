#
# Ansi-C expression writer
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import myokit
from myokit.formats.python import PythonExpressionWriter


class AnsiCExpressionWriter(PythonExpressionWriter):
    """
    This :class:`ExpressionWriter <myokit.formats.ExpressionWriter>` writes
    equations for variables in a C-style syntax.
    """
    def __init__(self):
        super(AnsiCExpressionWriter, self).__init__()
        self._function_prefix = ''
        self._fcond = None

    def set_condition_function(self, func=None):
        """
        Sets a function name to use for if statements

        By setting func to None you can revert back to the default behavior
         (the ternary operator). Any other value will be interpreted as the
         name of a C function taking arguments (condition, value_if_true,
         value_if_false).
        """
        self._fcond = func

    #def _ex_name(self, e):
    #def _ex_derivative(self, e):
    #def _ex_number(self, e):
    #def _ex_prefix_plus(self, e):
    #def _ex_prefix_minus(self, e):
    #def _ex_plus(self, e):
    #def _ex_minus(self, e):
    #def _ex_multiply(self, e):
    #def _ex_divide(self, e):

    def _ex_quotient(self, e):
        # Note that this _must_ round towards minus infinity!
        # See myokit.Quotient !
        return self.ex(myokit.Floor(myokit.Divide(e[0], e[1])))

    def _ex_remainder(self, e):
        # Note that this _must_ use the same round-to-neg-inf convention as
        # myokit.Quotient! Implementation below is consistent with Python
        # convention:
        return self.ex(myokit.Minus(
            e[0], myokit.Multiply(e[1], myokit.Quotient(e[0], e[1]))))

    def _ex_power(self, e):
        return 'pow(' + self.ex(e[0]) + ', ' + self.ex(e[1]) + ')'

    #def _ex_sqrt(self, e):
    #def _ex_sin(self, e):
    #def _ex_cos(self, e):
    #def _ex_tan(self, e):
    #def _ex_asin(self, e):
    #def _ex_acos(self, e):
    #def _ex_atan(self, e):
    #def _ex_exp(self, e):

    def _ex_log(self, e):
        if len(e) == 1:
            return self._ex_function(e, 'log')
        return '(log(' + self.ex(e[0]) + ') / log(' + self.ex(e[1]) + '))'

    #def _ex_log10(self, e):
    #def _ex_floor(self, e):
    #def _ex_ceil(self, e):

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
        return self._ex_infix_condition(e, '&&')

    def _ex_or(self, e):
        return self._ex_infix_condition(e, '||')

    def _ex_if(self, e):
        ite = (self.ex(e._i), self.ex(e._t), self.ex(e._e))
        if self._fcond is None:
            return '(%s ? %s : %s)' % ite
        else:
            return '%s(%s, %s, %s)' % ((self._fcond,) + ite)

    def _ex_piecewise(self, e):
        s = []
        n = len(e._i)
        if self._fcond is None:
            for i in range(0, n):
                s.append('(%s ? %s : ' % (self.ex(e._i[i]), self.ex(e._e[i])))
            s.append(self.ex(e._e[n]))
            s.append(')' * n)
        else:
            for i in range(0, n):
                s.append(
                    '%s(%s, %s, ' % (
                        self._fcond, self.ex(e._i[i]), self.ex(e._e[i])))
            s.append(self.ex(e._e[n]))
            s.append(')' * n)
        return ''.join(s)

