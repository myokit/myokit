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
        # Extra brackets needed: Minus has lower precedence than division.
        i = myokit.Minus(e[0], myokit.Multiply(
            e[1], myokit.Floor(myokit.Divide(e[0], e[1]))))
        return f'({self.ex(i)})'

    def _ex_power(self, e):
        # Like Python (and unlike Myokit), Stan uses a right-associative power
        # operator.
        if e.bracket(e[0]) or isinstance(e[0], myokit.Power):
            out = f'({self.ex(e[0])})'
        else:
            out = f'{self.ex(e[0])}'
        if e.bracket(e[1]) and not isinstance(e[1], myokit.Power):
            return f'{out}^({self.ex(e[1])})'
        else:
            return f'{out}^{self.ex(e[1])}'

    #def _ex_sqrt(self, e):
    #def _ex_sin(self, e):
    #def _ex_cos(self, e):
    #def _ex_tan(self, e):
    #def _ex_asin(self, e):
    #def _ex_acos(self, e):
    #def _ex_atan(self, e):
    #def _ex_exp(self, e):

    def _ex_log(self, e):
        if len(e) == 2:
            return f'(log({self.ex(e[0])}) / log({self.ex(e[1])}))'
        return f'log({self.ex(e[0])})'

    def _ex_log10(self, e):
        return f'log10({self.ex(e[0])})'

    #def _ex_floor(self, e):
    #def _ex_ceil(self, e):
    #def _ex_abs(self, e):

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
        return f'(!{self.ex(e[0])})'

    def _ex_if(self, e):
        return f'({self.ex(e._i)} ? {self.ex(e._t)} : {self.ex(e._e)})'

    def _ex_piecewise(self, e):
        s = []
        for _if, _then in zip(e._i, e._e):
            s.append(f'({self.ex(_if)} ? {self.ex(_then)} : ')
        s.append(self.ex(e._e[-1]))
        s.append(')' * len(e._i))
        return ''.join(s)

