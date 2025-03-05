#
# Latex expression writer
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import myokit.formats


class LatexExpressionWriter(myokit.formats.ExpressionWriter):
    """
    This :class:`ExpressionWriter <myokit.formats.ExpressionWriter>` translates
    Myokit :class:`expressions <myokit.Expression>` to their Tex equivalent.
    """
    def __init__(self):
        super().__init__()

        # Default time variable
        self._time = None
        self.set_time_variable_name()

        # Default lhs function
        def flhs(lhs):
            v = r'\text{' + self._prepare_name(lhs.var().uname()) + '}'
            if isinstance(lhs, myokit.Name):
                return v
            elif isinstance(lhs, myokit.Derivative):
                return r'\frac{d' + v + r'}{d\text{' + self._time + '}}'
            elif isinstance(lhs, myokit.PartialDerivative):
                v2 = self._prepare_name(
                    lhs.independent_expression().var().uname())
                return r'\frac{\partial' + v + r'}{\partial\text{' + v2 + '}}'
            elif isinstance(lhs, myokit.InitialValue):
                return v + r'(\text{' + self._time + '} = 0)'
            else:   # pragma: no cover
                raise ValueError(f'Unsupported LHS type {type(lhs)}')

        self._flhs = None
        self.set_lhs_function(flhs)

    def set_lhs_function(self, f):
        """
        Sets a naming function, will be called to get the variable name from a
         :class:`myokit.LhsExpression`. This function is also responsible for
         converting it to a suitable Latex form (e.g. adding `\\text{}`).

        The argument ``f`` should be a function that takes an ``LhsExpression``
        as input and returns a string.
        """
        self._flhs = f

    def set_time_variable_name(self, name='t'):
        """ Sets a name to use for the time variable in derivatives. """
        self._time = self._prepare_name(name)

    def eq(self, eq):
        """ See :meth:`myokit.formats.ExpressionWriter.eq()`. """
        return self.ex(eq.lhs) + ' = ' + self.ex(eq.rhs)

    def ex(self, e):
        """ See :meth:`myokit.formats.ExpressionWriter.ex()`. """
        b = []
        self._ex(e, b)
        return ''.join(b)

    def _prepare_name(self, text):
        """ Sanitises a name for use in latex. """
        return str(text).replace('_', r'\_')

    def _ex(self, e, b):
        try:
            action = self._op_map[type(e)]
        except KeyError:
            raise ValueError('Unknown expression type: ' + str(type(e)))
        action(e, b)

    def _ex_prefix(self, e, b, op):
        """ Handles _ex() for prefix operators. """
        b.append(op)
        if e.bracket(e[0]):
            b.append(r'\left(')
        self._ex(e[0], b)
        if e.bracket(e[0]):
            b.append(r'\right)')

    def _ex_infix(self, e, b, op):
        """ Handles _ex() for infix operators. """
        if e.bracket(e[0]):
            b.append(r'\left(')
        self._ex(e[0], b)
        if e.bracket(e[0]):
            b.append(r'\right)')
        b.append(op)
        if e.bracket(e[1]):
            b.append(r'\left(')
        self._ex(e[1], b)
        if e.bracket(e[1]):
            b.append(r'\right)')

    def _ex_function(self, e, b, func):
        """ Handles _ex() for function operators. """
        b.append(func)
        b.append(r'\left(')
        b.append(','.join([self.ex(x) for x in e]))
        b.append(r'\right)')

    def _ex_infix_condition(self, e, b, op):
        """ Handles _ex() for infix condition operators. """
        b.append(r'\left(')
        self._ex(e[0], b)
        b.append(op)
        self._ex(e[1], b)
        b.append(r'\right)')

    def _ex_name(self, e, b):
        b.append(self._flhs(e))

    def _ex_derivative(self, e, b):
        b.append(self._flhs(e))

    def _ex_partial_derivative(self, e, b):
        b.append(self._flhs(e))

    def _ex_initial_value(self, e, b):
        b.append(self._flhs(e))

    def _ex_number(self, e, b):
        b.append(myokit.float.str(e).strip())
        u = e.unit()
        if u is not None and u is not myokit.units.dimensionless:
            u = str(u)[1:-1]
            b.append(r' \text{' + u + '}')

    def _ex_prefix_plus(self, e, b):
        self._ex_prefix(e, b, '+')

    def _ex_prefix_minus(self, e, b):
        self._ex_prefix(e, b, '-')

    def _ex_plus(self, e, b):
        self._ex_infix(e, b, '+')

    def _ex_minus(self, e, b):
        self._ex_infix(e, b, '-')

    def _ex_multiply(self, e, b):
        self._ex_infix(e, b, r'\cdot')

    def _ex_divide(self, e, b):
        b.append(r'\frac{')
        self._ex(e[0], b)
        b.append('}{')
        self._ex(e[1], b)
        b.append('}')

    def _ex_quotient(self, e, b):
        # Note: Quotient in myokit uses round-to-zero (like Python does!)
        # See: myokit.Quotient
        b.append(r'\left\lfloor')
        self._ex_divide(e, b)
        b.append(r'\right\rfloor')

    def _ex_remainder(self, e, b):
        self._ex_infix(e, b, r'\bmod')

    def _ex_power(self, e, b):
        if e.bracket(e[0]) or isinstance(e[0], myokit.Power):
            b.append(r'\left(')
        self._ex(e[0], b)
        if e.bracket(e[0]) or isinstance(e[0], myokit.Power):
            b.append(r'\right)')
        b.append('^')
        if e.bracket(e[1]) or isinstance(e[1], myokit.Power):
            b.append('{')
        self._ex(e[1], b)
        if e.bracket(e[1]) or isinstance(e[1], myokit.Power):
            b.append('}')

    def _ex_sqrt(self, e, b):
        b.append(r'\sqrt{')
        self._ex(e[0], b)
        b.append('}')

    def _ex_sin(self, e, b):
        self._ex_function(e, b, r'\sin')

    def _ex_cos(self, e, b):
        self._ex_function(e, b, r'\cos')

    def _ex_tan(self, e, b):
        self._ex_function(e, b, r'\tan')

    def _ex_asin(self, e, b):
        self._ex_function(e, b, r'\arcsin')

    def _ex_acos(self, e, b):
        self._ex_function(e, b, r'\arccos')

    def _ex_atan(self, e, b):
        self._ex_function(e, b, r'\arctan')

    def _ex_exp(self, e, b):
        self._ex_function(e, b, r'\exp')

    def _ex_log(self, e, b):
        b.append(r'\log')
        if len(e) > 1:
            b.append('_{')
            self._ex(e[1], b)
            b.append('}')
        b.append(r'\left(')
        self._ex(e[0], b)
        b.append(r'\right)')

    def _ex_log10(self, e, b):
        b.append(r'\log_{10}')
        b.append(r'\left(')
        self._ex(e[0], b)
        b.append(r'\right)')

    def _ex_floor(self, e, b):
        b.append(r'\left\lfloor{')
        self._ex(e[0], b)
        b.append(r'}\right\rfloor')

    def _ex_ceil(self, e, b):
        b.append(r'\left\lceil{')
        self._ex(e[0], b)
        b.append(r'}\right\rceil')

    def _ex_abs(self, e, b):
        b.append(r'\lvert{')
        self._ex(e[0], b)
        b.append(r'}\rvert')

    def _ex_equal(self, e, b):
        self._ex_infix_condition(e, b, '=')

    def _ex_not_equal(self, e, b):
        self._ex_infix_condition(e, b, r'\neq')

    def _ex_more(self, e, b):
        self._ex_infix_condition(e, b, '>')

    def _ex_less(self, e, b):
        self._ex_infix_condition(e, b, '<')

    def _ex_more_equal(self, e, b):
        self._ex_infix_condition(e, b, r'\geq')

    def _ex_less_equal(self, e, b):
        self._ex_infix_condition(e, b, r'\leq')

    def _ex_not(self, e, b):
        b.append(r'\left(\not')
        self._ex(e[0], b)
        b.append(r'\right)')

    def _ex_and(self, e, b):
        self._ex_infix_condition(e, b, r'\and')

    def _ex_or(self, e, b):
        self._ex_infix_condition(e, b, r'\or')

    def _ex_if(self, e, b):
        # Not suported
        self._ex_function(e, b, r'\text{if}')

    def _ex_piecewise(self, e, b):
        # Not suported
        self._ex_function(e, b, r'\text{piecewise}')
