#
# Matlab expression writer and keywords
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import myokit

from myokit.formats.python import PythonExpressionWriter


class MatlabExpressionWriter(PythonExpressionWriter):
    """
    This :class:`ExpressionWriter <myokit.formats.ExpressionWriter>` translates
    Myokit :class:`expressions <myokit.Expression>` to a Matlab syntax.
    """
    def __init__(self):
        super().__init__()
        self._function_prefix = ''
        self._fcond = 'ifthenelse'

    def set_condition_function(self, func):
        """
        Sets a function name to output to handle :class:`myokit.If`.

        The function must take arguments ``(condition, value_if_true,
        value_if_false)`` and will be used to handle both :class:`myokit.If`
        and :class:`myokit.Piecewise`.

        By default, `ifthenelse` is used, which the user is expected to define
        if ``If`` or ``Piecewise`` will be used. For example::

            function y = ifthenelse(condition, value_if_true, value_if_false)
                if (condition)
                    y = value_if_true;
                else
                    y = value_if_false;
                end
            end

        """
        if func is not None:
            func = str(func).strip()
        if func is None or func == '':
            raise ValueError(
                'The MatlabExpressionWriter needs a condition function to be'
                ' set.')
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
        # Round towards minus infinity
        return self.ex(myokit.Floor(myokit.Divide(e[0], e[1])))

    def _ex_remainder(self, e):
        # Uses the round-towards-minus-infinity convention!
        return f'mod({self.ex(e[0])}, {self.ex(e[1])})'

    def _ex_power(self, e):
        # Same associativity as Myokit, not Python! So override
        e1 = f'({self.ex(e[0])})' if e.bracket(e[0]) else f'{self.ex(e[0])}'
        e2 = f'({self.ex(e[1])})' if e.bracket(e[1]) else f'{self.ex(e[1])}'
        return f'{e1}^{e2}'

    #def _ex_sqrt(self, e):
    #    Ignore imaginary part
    #    return 'real(' + self._ex_function(e, 'sqrt') + ')'
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
        # Always add brackets: Parent was expecting a function so will never
        # have added them.
        return f'(log({self.ex(e[0])}) / log({self.ex(e[1])}))'

    #def _ex_log10(self, e):
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
        return f'(!{self.ex(e[0])})'

    def _ex_if(self, e):
        _if, _then, _else = self.ex(e._i), self.ex(e._t), self.ex(e._e)
        return f'{self._fcond}({_if}, {_then}, {_else})'

    def _ex_piecewise(self, e):
        # Render ifs; add extra bracket if not a condition (see _ex_if)
        _ifs = [self.ex(x) for x in e._i]
        _thens = [self.ex(x) for x in e._e]

        s = []
        n = len(_ifs)
        for _if, _then in zip(_ifs, _thens):
            s.append(f'{self._fcond}({_if}, {_then}, ')
        s.append(_thens[-1])
        s.append(')' * len(_ifs))
        return ''.join(s)

