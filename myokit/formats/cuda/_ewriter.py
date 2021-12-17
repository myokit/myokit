#
# CUDA expression writer
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import myokit
from myokit.formats.python import PythonExpressionWriter


class CudaExpressionWriter(PythonExpressionWriter):
    """
    This :class:`ExpressionWriter <myokit.formats.ExpressionWriter>` translates
    Myokit :class:`expressions <myokit.Expression>` to their CUDA equivalents.
    """
    def __init__(self, precision=myokit.SINGLE_PRECISION):
        super(CudaExpressionWriter, self).__init__()
        self._function_prefix = ''
        self._sp = (precision == myokit.SINGLE_PRECISION)

    #def _ex_name(self, e):
    #def _ex_derivative(self, e):

    def _ex_number(self, e):
        return myokit.float.str(e) + 'f' if self._sp else myokit.float.str(e)

    #def _ex_prefix_plus(self, e):
    #def _ex_prefix_minus(self, e):
    #def _ex_plus(self, e):
    #def _ex_minus(self, e):
    #def _ex_multiply(self, e):
    #def _ex_divide(self, e):

    def _ex_quotient(self, e):
        # Note that this _must_ round towards minus infinity.
        # See myokit.Quotient
        # CUDA docs are unclear on convention, so assuming it follows C and
        # so we need a custom implementation.
        return self.ex(myokit.Floor(myokit.Divide(e[0], e[1])))

    def _ex_remainder(self, e):
        # Note that this _must_ use the same round-to-neg-inf convention as
        # myokit.Quotient.
        # CUDA docs are unclear on convention, so assuming it follows C and
        # so we need a custom implementation.
        return self.ex(myokit.Minus(
            e[0], myokit.Multiply(e[1], myokit.Quotient(e[0], e[1]))))

    def _ex_power(self, e):
        if e[1] == myokit.Number(2):
            if e.bracket(e[0]):
                return '((' + self.ex(e[0]) + ') * (' + self.ex(e[0]) + '))'
            else:
                return '(' + self.ex(e[0]) + ' * ' + self.ex(e[0]) + ')'
        else:
            f = 'powf' if self._sp else 'pow'
            return f + '(' + self.ex(e[0]) + ', ' + self.ex(e[1]) + ')'

    def _ex_sqrt(self, e):
        f = 'sqrtf' if self._sp else 'sqrt'
        return self._ex_function(e, f)

    def _ex_sin(self, e):
        f = 'sinf' if self._sp else 'sin'
        return self._ex_function(e, f)

    def _ex_cos(self, e):
        f = 'cosf' if self._sp else 'cos'
        return self._ex_function(e, f)

    def _ex_tan(self, e):
        f = 'tanf' if self._sp else 'tan'
        return self._ex_function(e, f)

    def _ex_asin(self, e):
        f = 'asinf' if self._sp else 'asin'
        return self._ex_function(e, f)

    def _ex_acos(self, e):
        f = 'acosf' if self._sp else 'acos'
        return self._ex_function(e, f)

    def _ex_atan(self, e):
        f = 'atanf' if self._sp else 'atan'
        return self._ex_function(e, f)

    def _ex_exp(self, e):
        f = 'expf' if self._sp else 'exp'
        return self._ex_function(e, f)

    def _ex_log(self, e):
        f = 'logf' if self._sp else 'log'
        if len(e) == 1:
            return self._ex_function(e, f)
        return '(' + f + '(' + self.ex(e[0]) + ') / ' + f + '(' \
            + self.ex(e[1]) + '))'

    def _ex_log10(self, e):
        f = 'log10f' if self._sp else 'log10'
        return self._ex_function(e, f)

    def _ex_floor(self, e):
        f = 'floorf' if self._sp else 'floor'
        return self._ex_function(e, f)

    def _ex_ceil(self, e):
        f = 'ceilf' if self._sp else 'ceil'
        return self._ex_function(e, f)

    def _ex_abs(self, e):
        f = 'fabsf' if self._sp else 'fabs'
        return self._ex_function(e, f)

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
        return '(%s ? %s : %s)' % (self.ex(e._i), self.ex(e._t), self.ex(e._e))

    def _ex_piecewise(self, e):
        s = []
        n = len(e._i)
        for i in range(0, n):
            s.append('(')
            s.append(self.ex(e._i[i]))
            s.append(' ? ')
            s.append(self.ex(e._e[i]))
            s.append(' : ')
        s.append(self.ex(e._e[n]))
        s.append(')' * n)
        return ''.join(s)

