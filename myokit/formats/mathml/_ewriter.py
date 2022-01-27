#
# MathML expression writer
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

from lxml import etree

import myokit.formats

# Strings in Python 2 and 3
try:
    basestring
except NameError:   # pragma: no cover
    basestring = str


class MathMLExpressionWriter(myokit.formats.ExpressionWriter):
    """
    This :class:`ExpressionWriter <myokit.formats.ExpressionWriter>` translates
    Myokit :class:`expressions <myokit.Expression>` to Content MathML or
    Presentation MathML.
    """
    def __init__(self):
        super(MathMLExpressionWriter, self).__init__()

        # Default mode
        self._pres = False

        # Default lhs conversion function
        def flhs(lhs):
            var = lhs.var()
            if isinstance(var, basestring):
                # This can happen with time variable of derivative if the
                # proper variable isn't set!
                return var
            return var.qname()
        self._flhs = flhs

        # Default number-to-string conversion function (outputs e.g. "1.0")
        self._fnum = lambda x: myokit.float.str(x.eval()).strip()

        # Default time variable
        self._tvar = myokit.Name('time')

        # Namespaces for element creation
        from myokit.formats.mathml import NS_MATHML_2
        self._nsmap = {None: NS_MATHML_2}

    def set_lhs_function(self, f):
        """
        Sets a naming function, will be called to get the variable name from a
         :class:`myokit.Name` (derivatives will be handled separately).

        The argument ``f`` should be a function that takes a
        :class:`myokit.Name` as input and returns a string.
        """
        self._flhs = f

    def set_mode(self, presentation=False):
        """
        Enables or disables Presentation MathML mode.
        """
        self._pres = bool(presentation)

    def set_time_variable(self, time):
        """
        Sets the time variable to use for this expression writer's derivatives.
        """
        self._tvar = myokit.Name(time)

    def eq(self, eq, element=None):
        """
        Converts an equation to a string.

        The optional argument ``element`` can be used to pass in an
        ``lxml.etree.ElementTree`` element. If given, this element will be
        updated with the generated xml and nothing will be returned.
        """
        if element is None:
            tag = etree.Element('math', nsmap=self._nsmap)
        else:
            tag = element
        if self._pres:
            t = etree.SubElement(tag, 'mrow')
            self.ex(eq.lhs, t)
            x = etree.SubElement(t, 'mo')
            x.text = '='
            self.ex(eq.rhs, t)
        else:
            t = etree.SubElement(tag, 'apply')
            etree.SubElement(t, 'eq')
            self.ex(eq.lhs, t)
            self.ex(eq.rhs, t)
        if element is None:
            # By default et.tostring() will use ascii enconding. This is good,
            # because it creates XML entities (numeric character reference) for
            # special characters.
            enc = 'us-ascii'
            encoded = etree.tostring(tag, encoding=enc)
            return encoded.decode(enc)

    def ex(self, e, element=None):
        """
        Converts an expression to a string.

        The optional argument ``element`` can be used to pass in an
        ``lxml.etree.ElementTree`` element. If given, this element will be
        updated with the generated xml and nothing will be returned.
        """
        if element is None:
            tag = etree.Element('math', nsmap=self._nsmap)
        else:
            tag = element
        self._ex(e, tag)
        if element is None:
            # By default et.tostring() will use ascii enconding. This is good,
            # because it creates XML entities (numeric character reference) for
            # special characters.
            enc = 'us-ascii'
            encoded = etree.tostring(tag, encoding=enc)
            return encoded.decode(enc)

    def _ex(self, e, t):
        """ Writes expression ``e`` to element ``t`` """
        try:
            action = self._op_map[type(e)]
        except KeyError:
            raise ValueError('Unknown expression type: ' + str(type(e)))
        action(e, t)

    def _ex_prefix(self, e, t, cml):
        """
        Exports e as a prefix expression with ContentML representation cml.
        """
        bra = e.bracket(e[0])
        if self._pres:
            row = etree.SubElement(t, 'mrow')
            if bra:
                x = etree.SubElement(row, 'mo')
                x.text = '('
            x = etree.SubElement(row, 'mo')
            x.text = e.operator_rep()
            self._ex(e[0], row)
            if bra:
                x = etree.SubElement(row, 'mo')
                x.text = ')'
        else:
            tag = etree.SubElement(t, 'apply')
            etree.SubElement(tag, cml)
            self._ex(e[0], tag)

    def _ex_infix(self, e, t, cml):
        """
        Exports e as an infix expression with ContentML representation cml.
        """
        if self._pres:
            r = etree.SubElement(t, 'mrow')
            k = etree.SubElement(r, 'mfenced') if e.bracket(e[0]) else r
            self._ex(e[0], k)
            x = etree.SubElement(r, 'mo')
            if isinstance(e, myokit.MoreEqual):
                x.text = '\u2265'
            elif isinstance(e, myokit.LessEqual):
                x.text = '\u2264'
            else:
                x.text = e.operator_rep()
            k = etree.SubElement(r, 'mfenced') if e.bracket(e[1]) else r
            self._ex(e[1], k)
        else:
            a = etree.SubElement(t, 'apply')
            etree.SubElement(a, cml)
            self._ex(e[0], a)
            self._ex(e[1], a)

    def _ex_function(self, e, t, name):
        """ Exports ``e`` as a function called ``name``. """
        if self._pres:
            r = etree.SubElement(t, 'mrow')
            x = etree.SubElement(r, 'mi')
            x.text = name
            r = etree.SubElement(r, 'mfenced')
            for op in e:
                self._ex(op, r)
        else:
            a = etree.SubElement(t, 'apply')
            etree.SubElement(a, name)
            for op in e:
                self._ex(op, a)

    def _ex_name(self, e, t):
        x = etree.SubElement(t, 'mi' if self._pres else 'ci')
        x.text = self._flhs(e)

    def _ex_derivative(self, e, t):
        if self._pres:
            f = etree.SubElement(t, 'mfrac')
            x = etree.SubElement(f, 'mi')
            x.text = 'd' + self._flhs(e[0])
            x = etree.SubElement(f, 'mi')
            x.text = 'dt'
        else:
            a = etree.SubElement(t, 'apply')
            etree.SubElement(a, 'diff')
            self._ex(self._tvar, etree.SubElement(a, 'bvar'))
            self._ex(e[0], a)

    def _ex_number(self, e, t):
        x = etree.SubElement(t, 'mn' if self._pres else 'cn')
        x.text = self._fnum(e)

        if not self._pres:
            try:
                x.text, exp = x.text.split('e', 1)
            except ValueError:
                # Return for overriding
                return x

            exp = int(exp)
            if exp != 0:
                x.attrib['type'] = 'e-notation'
                s = etree.SubElement(x, 'sep')
                s.tail = str(int(exp))

        # Return for overriding
        return x

    def _ex_prefix_plus(self, e, t):
        # Return for overriding
        return self._ex_prefix(e, t, 'plus')

    def _ex_prefix_minus(self, e, t):
        # Return for overriding
        return self._ex_prefix(e, t, 'minus')

    def _ex_plus(self, e, t):
        self._ex_infix(e, t, 'plus')

    def _ex_minus(self, e, t):
        self._ex_infix(e, t, 'minus')

    def _ex_multiply(self, e, t):
        self._ex_infix(e, t, 'times')

    def _ex_divide(self, e, t):
        if self._pres:
            r = etree.SubElement(t, 'mfrac')
            k = etree.SubElement(r, 'mfenced') if e.bracket(e[0]) else r
            self._ex(e[0], k)
            k = etree.SubElement(r, 'mfenced') if e.bracket(e[1]) else r
            self._ex(e[1], k)
        else:
            a = etree.SubElement(t, 'apply')
            etree.SubElement(a, 'divide')
            self._ex(e[0], a)
            self._ex(e[1], a)

    def _ex_quotient(self, e, t):
        self._ex_infix(e, t, 'quotient')

    def _ex_remainder(self, e, t):
        self._ex_infix(e, t, 'rem')

    def _ex_power(self, e, t):
        if self._pres:
            x = etree.SubElement(t, 'msup')
            self._ex(e[0], x)
            self._ex(e[1], x)
        else:
            self._ex_function(e, t, 'power')

    def _ex_sqrt(self, e, t):
        self._ex_function(e, t, 'root')

    def _ex_sin(self, e, t):
        self._ex_function(e, t, 'sin')

    def _ex_cos(self, e, t):
        self._ex_function(e, t, 'cos')

    def _ex_tan(self, e, t):
        self._ex_function(e, t, 'tan')

    def _ex_asin(self, e, t):
        self._ex_function(e, t, 'arcsin')

    def _ex_acos(self, e, t):
        self._ex_function(e, t, 'arccos')

    def _ex_atan(self, e, t):
        self._ex_function(e, t, 'arctan')

    def _ex_exp(self, e, t):
        if self._pres:
            r = etree.SubElement(t, 'msup')
            x = etree.SubElement(r, 'mi')
            x.text = 'e'
            self._ex(e[0], r)
        else:
            a = etree.SubElement(t, 'apply')
            etree.SubElement(a, 'exp')
            self._ex(e[0], a)

    def _ex_log(self, e, t):
        # myokit.log(a)   > ln(a)
        # myokit.log(a,b) > log(b, a)
        # myokit.log10(a) > log(a)
        if self._pres:
            if len(e) == 1:
                r = etree.SubElement(t, 'mrow')
                x = etree.SubElement(r, 'mi')
                x.text = 'ln'
                x = etree.SubElement(r, 'mfenced')
                self._ex(e[0], x)
            else:
                r = etree.SubElement(t, 'mrow')
                s = etree.SubElement(r, 'msub')
                x = etree.SubElement(s, 'mi')
                x.text = 'log'
                self._ex(e[1], s)
                s = etree.SubElement(r, 'mfenced')
                self._ex(e[0], s)
        else:
            if len(e) == 1:
                a = etree.SubElement(t, 'apply')
                etree.SubElement(a, 'ln')
                self._ex(e[0], a)
            else:
                a = etree.SubElement(t, 'apply')
                etree.SubElement(a, 'log')
                x = etree.SubElement(a, 'logbase')
                self._ex(e[1], x)
                self._ex(e[0], a)

    def _ex_log10(self, e, t):
        self._ex_function(e, t, 'log')

    def _ex_floor(self, e, t):
        self._ex_function(e, t, 'floor')

    def _ex_ceil(self, e, t):
        self._ex_function(e, t, 'ceiling')

    def _ex_abs(self, e, t):
        self._ex_function(e, t, 'abs')

    def _ex_not(self, e, t):
        # https://www.w3.org/TR/MathML2/chapter4.html#id.4.4.3.15
        self._ex_prefix(e, t, 'not')

    def _ex_equal(self, e, t):
        self._ex_infix(e, t, 'eq')

    def _ex_not_equal(self, e, t):
        self._ex_infix(e, t, 'neq')

    def _ex_more(self, e, t):
        self._ex_infix(e, t, 'gt')

    def _ex_less(self, e, t):
        self._ex_infix(e, t, 'lt')

    def _ex_more_equal(self, e, t):
        self._ex_infix(e, t, 'geq')

    def _ex_less_equal(self, e, t):
        self._ex_infix(e, t, 'leq')

    def _ex_and(self, e, t):
        self._ex_infix(e, t, 'and')

    def _ex_or(self, e, t):
        self._ex_infix(e, t, 'or')

    def _ex_if(self, e, t):
        self._ex_piecewise(e.piecewise(), t)

    def _ex_piecewise(self, e, t):
        if self._pres:
            w = etree.SubElement(t, 'piecewise')
            for k, cond in enumerate(e._i):
                p = etree.SubElement(w, 'piece')
                self._ex(e._e[k], p)
                self._ex(cond, p)
            p = etree.SubElement(w, 'otherwise')
            self._ex(e._e[-1], p)
        else:
            w = etree.SubElement(t, 'piecewise')
            for k, cond in enumerate(e._i):
                p = etree.SubElement(w, 'piece')
                self._ex(e._e[k], p)
                self._ex(cond, p)
            p = etree.SubElement(w, 'otherwise')
            self._ex(e._e[-1], p)

