#
# Stan expression writer and keywords
#
# cell.stan:: This will become the stan model definition file
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import myokit

from myokit.formats.python import PythonExpressionWriter


class StanExpressionWriter(PythonExpressionWriter):
    """
    This:class:`ExpressionWriter <myokit.formats.ExpressionWriter>` translates
    Myokit:class:`expressions <myokit.Expression>` to a Stan syntax.
    """
    def __init__(self):
        super().__init__()
        self._function_prefix = ''

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
        # Use floor to round towards minus infinity
        return self.ex(myokit.Floor(myokit.Divide(e[0], e[1])))

    def _ex_remainder(self, e):
        # fmod uses correct convention
        return self._ex_function(e, 'fmod')

    def _ex_power(self, e):
        return self._ex_infix(e, '^')

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
        else:
            return '(log(' + self.ex(e[0]) + ') / log(' + self.ex(e[1]) + '))'

    def _ex_log10(self, e):
        return 'log10(' + self.ex(e[0]) + ')'

    #def _ex_floor(self, e):
    #def _ex_ceil(self, e):

    def _ex_abs(self, e):
        return self._ex_function(e, 'abs')

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

    def _ex_not(self, e):
        return '!(' + self.ex(e[0]) + ')'

    def _ex_if(self, e):
        return ('(' + self.ex(e._i) + ' ? ' + self.ex(e._t) + ' : ' +
                self.ex(e._e) + ')')

    def _ex_piecewise(self, e):
        s = []
        n = len(e._i)
        for i in range(0, n):
            s.append('(%s ? %s : ' % (self.ex(e._i[i]), self.ex(e._e[i])))
        s.append(self.ex(e._e[n]))
        s.append(')' * n)
        return ''.join(s)

