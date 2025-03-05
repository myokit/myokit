#
# Ansi-C expression writer
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import myokit

from myokit.formats.python import PythonExpressionWriter


class CBasedExpressionWriter(PythonExpressionWriter):
    """
    Base class for C-style expression writers.
    """
    def __init__(self):
        super().__init__()
        self._function_prefix = ''

    def _ex_prefix(self, e, op):
        # PrefixPlus and PrefixMinus. No simplifications should be made here
        # for PrefixPlus, see https://github.com/myokit/myokit/issues/1054
        x = self.ex(e[0])
        return f'{op}({x})' if e.bracket(e[0]) or x[0] == op else f'{op}{x}'

    def _ex_infix_comparison(self, e, op):
        # For equals etc
        return f'({self.ex(e[0])} {op} {self.ex(e[1])})'

    def _ex_infix_logical(self, e, op):
        # For and and or
        return f'({self.ex(e[0])} {op} {self.ex(e[1])})'

    #def _ex_name(self, e):
    #def _ex_derivative(self, e):
    #def _ex_initial_value(self, e):
    #def _ex_partial_derivative(self, e):

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
        # No extra brackets needed: Function
        return self.ex(myokit.Floor(myokit.Divide(e[0], e[1])))

    def _ex_remainder(self, e):
        # Note that this _must_ use the same round-to-neg-inf convention as
        # myokit.Quotient! Implementation below is consistent with Python
        # convention.
        # Extra brackets needed! Minus has lower precedence than division.
        i = myokit.Minus(e[0], myokit.Multiply(
            e[1], myokit.Floor(myokit.Divide(e[0], e[1]))))
        return f'({self.ex(i)})'

    def _ex_power(self, e):
        return f'pow({self.ex(e[0])}, {self.ex(e[1])})'

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
        # Always add brackets: Parent was expecting a function so will never
        # have added them.
        return f'(log({self.ex(e[0])}) / log({self.ex(e[1])}))'

    #def _ex_log10(self, e):
    #def _ex_floor(self, e):
    #def _ex_ceil(self, e):

    def _ex_abs(self, e):
        return self._ex_function(e, 'fabs')

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
        # C conditions all have brackets, so don't add more
        return f'(!{self.ex(e[0])})'

    def _ex_if(self, e):
        return f'({self.ex(e._i)} ? {self.ex(e._t)} : {self.ex(e._e)})'

    def _ex_piecewise(self, e):
        # Render ifs; add extra bracket if not a condition (see _ex_if)
        _ifs = [self.ex(x) for x in e._i]
        _thens = [self.ex(x) for x in e._e]

        s = []
        n = len(_ifs)
        for _if, _then in zip(_ifs, _thens):
            s.append(f'({_if} ? {_then} : ')
        s.append(_thens[-1])
        s.append(')' * len(_ifs))
        return ''.join(s)


class AnsiCExpressionWriter(CBasedExpressionWriter):
    """
    This :class:`ExpressionWriter <myokit.formats.ExpressionWriter>` writes
    equations for variables in a C-style syntax.
    """
    def __init__(self):
        super().__init__()
        self._fcond = None

    def set_condition_function(self, func=None):
        """
        Sets a function name to use for :class:`myokit.If`; if not set the
        ternary operatur will be used.

        If given, the function arguments should be ``(condition, value_if_true,
        value_if_false)``. To revert to using the ternary operator, call with
        ``func=None``.
        """
        self._fcond = func

    #def _ex_name(self, e):
    #def _ex_derivative(self, e):

    def _ex_initial_value(self, e):
        # These are disabled by default, but enabled here to support CVODES
        # sensitivity calculations.
        return self._flhs(e)

    def _ex_partial_derivative(self, e):
        # These are disabled by default, but enabled here to support CVODES
        # sensitivity calculations.
        return self._flhs(e)

    #def _ex_number(self, e):

    #def _ex_prefix_plus(self, e):
    #def _ex_prefix_minus(self, e):

    #def _ex_plus(self, e):
    #def _ex_minus(self, e):
    #def _ex_multiply(self, e):
    #def _ex_divide(self, e):

    #def _ex_quotient(self, e):
    #def _ex_remainder(self, e):
    #def _ex_power(self, e):
    #def _ex_sqrt(self, e):
    #def _ex_sin(self, e):
    #def _ex_cos(self, e):
    #def _ex_tan(self, e):
    #def _ex_asin(self, e):
    #def _ex_acos(self, e):
    #def _ex_atan(self, e):
    #def _ex_exp(self, e):
    #def _ex_log(self, e):
    #def _ex_log10(self, e):
    #def _ex_floor(self, e):
    #def _ex_ceil(self, e):
    #def _ex_abs(self, e):
    #def _ex_equal(self, e):
    #def _ex_not_equal(self, e):
    #def _ex_more(self, e):
    #def _ex_less(self, e):
    #def _ex_more_equal(self, e):
    #def _ex_less_equal(self, e):
    #def _ex_and(self, e):
    #def _ex_or(self, e):
    #def _ex_not(self, e):

    def _ex_if(self, e):
        _if, _then, _else = self.ex(e._i), self.ex(e._t), self.ex(e._e)

        # Use if-then-else function?
        if self._fcond is not None:
            return f'{self._fcond}({_if}, {_then}, {_else})'

        # Default: use ternary operator
        return f'({_if} ? {_then} : {_else})'

    def _ex_piecewise(self, e):
        # Allow _fcond

        # Render ifs; add extra bracket if not a condition (see _ex_if)
        _ifs = [self.ex(x) for x in e._i]
        _thens = [self.ex(x) for x in e._e]

        s = []
        n = len(_ifs)
        if self._fcond is not None:
            for _if, _then in zip(_ifs, _thens):
                s.append(f'{self._fcond}({_if}, {_then}, ')
        else:
            for _if, _then in zip(_ifs, _thens):
                s.append(f'({_if} ? {_then} : ')
        s.append(_thens[-1])
        s.append(')' * len(_ifs))
        return ''.join(s)

