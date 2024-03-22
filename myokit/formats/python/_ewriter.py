#
# Python expression writer and keywords
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import myokit.formats


class PythonExpressionWriter(myokit.formats.ExpressionWriter):
    """
    This :class:`ExpressionWriter <myokit.formats.ExpressionWriter>` translates
    Myokit :class:`expressions <myokit.Expression>` to their Python
    equivalent.
    """
    def __init__(self):
        super().__init__()

        self._flhs = None
        self.set_lhs_function(lambda v: str(v))

        self._function_prefix = 'math.'

    def set_lhs_function(self, f):
        """
        Sets a naming function, will be called to get the variable name from a
         ``myokit.LhsExpression`` object.

        The argument ``f`` should be a function that takes an ``LhsExpression``
        as input and returns a string.
        """
        self._flhs = f

    def _ex_prefix(self, e, op):
        """ Handles ex() for prefix operators. """
        # No simplifications should be made here for PrefixPlus, see
        #   https://github.com/myokit/myokit/issues/1054
        if e.bracket(e[0]):
            return f'{op}({self.ex(e[0])})'
        return f'{op}{self.ex(e[0])}'

    def _ex_infix(self, e, op):
        """ Handles ex() for infix operators, except Power. """
        if e.bracket(e[0]):
            out = f'({self.ex(e[0])}) {op}'
        else:
            out = f'{self.ex(e[0])} {op}'
        if e.bracket(e[1]):
            return f'{out} ({self.ex(e[1])})'
        else:
            return f'{out} {self.ex(e[1])}'

    def _ex_function(self, e, func):
        """ Handles ex() for function operators with operands. """
        args = ', '.join([self.ex(x) for x in e])
        return f'{self._function_prefix}{func}({args})'

    def _ex_infix_comparison(self, e, op):
        """ Handles ex() for infix comparisons (``==``, ``>=``, etc.). """
        return f'({self.ex(e[0])} {op} {self.ex(e[1])})'

    def _ex_infix_logical(self, e, op):
        """ Handles ex() for ``and`` and ``or``. """
        return f'({self.ex(e[0])} {op} {self.ex(e[1])})'

    def _ex_name(self, e):
        return self._flhs(e)

    def _ex_derivative(self, e):
        return self._flhs(e)

    def _ex_initial_value(self, e):
        raise NotImplementedError(
            'Initial values are not supported by this expression writer.')

    def _ex_partial_derivative(self, e):
        raise NotImplementedError(
            'Partial derivatives are not supported by this expression writer.')

    def _ex_number(self, e):
        return myokit.float.str(e).lstrip()

    def _ex_prefix_plus(self, e):
        return self._ex_prefix(e, '+')

    def _ex_prefix_minus(self, e):
        return self._ex_prefix(e, '-')

    def _ex_plus(self, e):
        return self._ex_infix(e, '+')

    def _ex_minus(self, e):
        return self._ex_infix(e, '-')

    def _ex_multiply(self, e):
        return self._ex_infix(e, '*')

    def _ex_divide(self, e):
        return self._ex_infix(e, '/')

    def _ex_quotient(self, e):
        return self._ex_infix(e, '//')

    def _ex_remainder(self, e):
        return self._ex_infix(e, '%')

    def _ex_power(self, e):
        # Note: Python uses a right-to-left order of operations for power, so
        # that a**b**c means a**(b**c). In Myokit, a^b^c means (a^b)^c, so we
        # need to reverse this for powers only.
        if e.bracket(e[0]) or isinstance(e[0], myokit.Power):
            out = f'({self.ex(e[0])})'
        else:
            out = f'{self.ex(e[0])}'
        if e.bracket(e[1]) and not isinstance(e[1], myokit.Power):
            return f'{out}**({self.ex(e[1])})'
        else:
            return f'{out}**{self.ex(e[1])}'

    def _ex_sqrt(self, e):
        return self._ex_function(e, 'sqrt')

    def _ex_sin(self, e):
        return self._ex_function(e, 'sin')

    def _ex_cos(self, e):
        return self._ex_function(e, 'cos')

    def _ex_tan(self, e):
        return self._ex_function(e, 'tan')

    def _ex_asin(self, e):
        return self._ex_function(e, 'asin')

    def _ex_acos(self, e):
        return self._ex_function(e, 'acos')

    def _ex_atan(self, e):
        return self._ex_function(e, 'atan')

    def _ex_exp(self, e):
        return self._ex_function(e, 'exp')

    def _ex_log(self, e):
        return self._ex_function(e, 'log')

    def _ex_log10(self, e):
        return self._ex_function(e, 'log10')

    def _ex_floor(self, e):
        return self._ex_function(e, 'floor')

    def _ex_ceil(self, e):
        return self._ex_function(e, 'ceil')

    def _ex_abs(self, e):
        return f'abs({self.ex(e[0])})'

    def _ex_equal(self, e):
        return self._ex_infix_comparison(e, '==')

    def _ex_not_equal(self, e):
        return self._ex_infix_comparison(e, '!=')

    def _ex_more(self, e):
        return self._ex_infix_comparison(e, '>')

    def _ex_less(self, e):
        return self._ex_infix_comparison(e, '<')

    def _ex_more_equal(self, e):
        return self._ex_infix_comparison(e, '>=')

    def _ex_less_equal(self, e):
        return self._ex_infix_comparison(e, '<=')

    def _ex_and(self, e):
        return self._ex_infix_logical(e, 'and')

    def _ex_or(self, e):
        return self._ex_infix_logical(e, 'or')

    def _ex_not(self, e):
        return f'(not {self.ex(e[0])})'

    def _ex_if(self, e):
        return f'({self.ex(e._t)} if {self.ex(e._i)} else {self.ex(e._e)})'

    def _ex_piecewise(self, e):
        s = ''
        n = len(e) // 2
        for i in range(0, n):
            s += f'({self.ex(e._e[i])} if {self.ex(e._i[i])} else '
        s += self.ex(e._e[n]) + ')' * n
        return s


class NumPyExpressionWriter(PythonExpressionWriter):
    """
    This :class:`ExpressionWriter <myokit.formats.ExpressionWriter>` translates
    Myokit :class:`expressions <myokit.Expression>` to Python expressions
    intended for use in NumPy arrays.
    """
    def __init__(self):
        super().__init__()
        self._function_prefix = 'numpy.'
    #def _ex_name(self, e):
    #def _ex_derivative(self, e):
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

    def _ex_asin(self, e):
        return self._ex_function(e, 'arcsin')

    def _ex_acos(self, e):
        return self._ex_function(e, 'arccos')

    def _ex_atan(self, e):
        return self._ex_function(e, 'arctan')

    #def _ex_exp(self, e):

    def _ex_log(self, e):
        if len(e) == 1:
            return self._ex_function(e, 'log')
        # Always add brackets here: The parent element will have been expecting
        # a function (which never needs brackets) and so won't have added any.
        return f'(numpy.log({self.ex(e[0])}) / numpy.log({self.ex(e[1])}))'

    #def _ex_log10(self, e):
    #def _ex_floor(self, e):
    #def _ex_ceil(self, e):

    def _ex_abs(self, e):
        # Can't use default abs here, must be numpy.abs
        return self._ex_function(e, 'abs')

    #def _ex_equal(self, e):
    #def _ex_not_equal(self, e):
    #def _ex_more(self, e):
    #def _ex_less(self, e):
    #def _ex_more_equal(self, e):
    #def _ex_less_equal(self, e):

    def _ex_and(self, e):
        return self._ex_function(e, 'logical_and')

    def _ex_or(self, e):
        return self._ex_function(e, 'logical_or')

    def _ex_not(self, e):
        return self._ex_function(e, 'logical_not')

    def _ex_if(self, e):
        return (f'{self._function_prefix}select('
                f'[{self.ex(e._i)}], [{self.ex(e._t)}], {self.ex(e._e)})')

    def _ex_piecewise(self, e):
        n = len(e._i)
        s = [self._function_prefix, 'select([']
        s.append(', '.join([self.ex(x) for x in e._i]))
        s.append('], [')
        s.append(', '.join([self.ex(x) for x in e._e[:-1]]))
        s.append('], ')
        s.append(self.ex(e._e[n]))
        s.append(')')
        return ''.join(s)

