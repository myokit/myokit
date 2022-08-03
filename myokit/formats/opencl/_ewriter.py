#
# OpenCL expression writer
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import myokit
from myokit.formats.python import PythonExpressionWriter


class OpenCLExpressionWriter(PythonExpressionWriter):
    """
    This :class:`ExpressionWriter <myokit.formats.ExpressionWriter>` translates
    Myokit :class:`expressions <myokit.Expression>` to OpenCL syntax.
    """
    def __init__(self, precision=myokit.SINGLE_PRECISION, native_math=True):
        super(OpenCLExpressionWriter, self).__init__()
        self._function_prefix = ''
        self._sp = (precision == myokit.SINGLE_PRECISION)
        self._nm = bool(native_math)

    def _exc(self, e):
        """Returns ``ex(e)`` if ``e`` is a Condition, else ``ex(e != 0)``."""
        if isinstance(e, myokit.Condition):
            return self.ex(e)
        return self.ex(myokit.NotEqual(e, myokit.Number(0)))

    def _ex_infix_condition(self, e, op):
        """Handles ex() for infix condition operators (==, !=, > etc.)."""
        c1 = isinstance(e[0], myokit.Condition)
        c2 = isinstance(e[1], myokit.Condition)
        if (c1 and c2) or not (c1 or c2):
            a = self.ex(e[0])
            b = self.ex(e[1])
        else:
            a = self._exc(e[0])
            b = self._exc(e[1])
        return '(' + a + ' ' + op + ' ' + b + ')'

    def _ex_infix_logical(self, e, op):
        """Handles ex() for infix logical operators."""
        return '(' + self._exc(e[0]) + ' ' + op + ' ' + self._exc(e[1]) + ')'

    #def _ex_name(self, e):
    #def _ex_derivative(self, e):

    def _ex_number(self, e):
        return myokit.float.str(e) + 'f' if self._sp else myokit.float.str(e)

    #def _ex_prefix_plus(self, e):
    #def _ex_prefix_minus(self, e):
    #def _ex_plus(self, e):
    #def _ex_minus(self, e):
    #def _ex_multiply(self, e):

    def _ex_divide(self, e):
        # Native divide seemed to cause some issues
        #if self._nm:
        #    return 'native_divide(' + self.ex(e[0]) +', '+ self.ex(e[1]) + ')'
        #else:
        return self._ex_infix(e, '/')

    def _ex_quotient(self, e):
        # Note that this _must_ round towards minus infinity.
        # See myokit.Quotient.
        # Assuming it follows C and so we need a custom implementation.
        return self.ex(myokit.Floor(myokit.Divide(e[0], e[1])))

    def _ex_remainder(self, e):
        # Note that this _must_ use the same round-to-neg-inf convention as
        # myokit.Quotient.
        # Assuming it follows C and so we need a custom implementation.
        return self.ex(myokit.Minus(
            e[0], myokit.Multiply(e[1], myokit.Quotient(e[0], e[1]))))

    def _ex_power(self, e):
        if e[1] == myokit.Number(2):
            if e.bracket(e[0]):
                return '((' + self.ex(e[0]) + ') * (' + self.ex(e[0]) + '))'
            else:
                return '(' + self.ex(e[0]) + ' * ' + self.ex(e[0]) + ')'
        else:
            return 'pow(' + self.ex(e[0]) + ', ' + self.ex(e[1]) + ')'

    def _ex_sqrt(self, e):
        f = 'native_sqrt' if self._nm else 'sqrt'
        return self._ex_function(e, f)

    def _ex_sin(self, e):
        f = 'native_sin' if self._nm else 'sin'
        return self._ex_function(e, f)

    def _ex_cos(self, e):
        f = 'native_cos' if self._nm else 'cos'
        return self._ex_function(e, f)

    def _ex_tan(self, e):
        f = 'native_tan' if self._nm else 'tan'
        return self._ex_function(e, f)

    def _ex_asin(self, e):
        return self._ex_function(e, 'asin')

    def _ex_acos(self, e):
        return self._ex_function(e, 'acos')

    def _ex_atan(self, e):
        return self._ex_function(e, 'atan')

    def _ex_exp(self, e):
        f = 'native_exp' if self._nm else 'exp'
        return self._ex_function(e, f)

    def _ex_log(self, e):
        f = 'native_log' if self._nm else 'log'
        if len(e) == 1:
            return self._ex_function(e, f)
        return '(' + f + '(' + self.ex(e[0]) + ') / ' + f + '(' \
            + self.ex(e[1]) + '))'

    def _ex_log10(self, e):
        f = 'native_log10' if self._nm else 'log10'
        return self._ex_function(e, f)

    def _ex_floor(self, e):
        return self._ex_function(e, 'floor')

    def _ex_ceil(self, e):
        return self._ex_function(e, 'ceil')

    def _ex_abs(self, e):
        return self._ex_function(e, 'fabs')

    def _ex_not(self, e):
        return '!(' + self._exc(e[0]) + ')'

    #def _ex_equal(self, e):
    #def _ex_not_equal(self, e):
    #def _ex_more(self, e):
    #def _ex_less(self, e):
    #def _ex_more_equal(self, e):
    #def _ex_less_equal(self, e):

    def _ex_and(self, e):
        return self._ex_infix_logical(e, '&&')

    def _ex_or(self, e):
        return self._ex_infix_logical(e, '||')

    def _ex_if(self, e):
        return '(%s ? %s : %s)' % (
            self._exc(e._i), self.ex(e._t), self.ex(e._e))

    def _ex_piecewise(self, e):
        s = []
        n = len(e._i)
        for i in range(0, n):
            s.append('(')
            s.append(self._exc(e._i[i]))
            s.append(' ? ')
            s.append(self.ex(e._e[i]))
            s.append(' : ')
        s.append(self.ex(e._e[n]))
        s.append(')' * n)
        return ''.join(s)

