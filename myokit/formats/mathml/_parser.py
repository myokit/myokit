#
# Converts MathML to Myokit expressions, using an ElementTree implementation.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import myokit
from myokit.formats.xml import split


def parse_mathml_string(s):
    """
    Parses a MathML string that should contain a single expression.
    """
    import xml.etree.ElementTree as etree
    p = MathMLParser(
        lambda x, y: myokit.Name(x),
        lambda x, y: myokit.Number(x),
    )
    return p.parse(etree.fromstring(s))


def parse_mathml_etree(
        element, name_factory, number_factory, free_variables=set()):
    """
    Parses a MathML expression and returns a :class:`myokit.Expression`.

    Arguments:

    ``element``
        An ``xml.etree.ElementTree.Element`` (or similar) to start parsing
        from. Must be an ``<apply>`` element.
    ``name_factory``
        A callable with arguments ``(name_as_string, element)`` that returns
        :class:`myokit.Name` objects.
    ``number_factory``
        A callable with arguments ``(number_as_float, element)`` that returns
        :class:`myokit.Number` objects. Note that ``element`` can be ``None``
        for numbers that have no corresponding ``<cn>`` element.
    ``free_variables``
        All :class:`Name` objects for free variables in derivative expressions
        will be added to this set.

    """
    p = MathMLParser(name_factory, number_factory, free_variables)
    return p.parse(element)


class MathMLError(myokit.ImportError):
    """
    Raised if an error occurs during MathML import.

    The argument ``element`` can be used to pass in an element that caused the
    error.
    """
    def __init__(self, message, element=None):
        if element is not None:
            try:    # pragma: no cover
                line = str(element.sourceline)
                message = 'Error on line ' + line + '. ' + message
            except AttributeError:
                pass
        super(MathMLError, self).__init__(message)


class MathMLParser(object):
    """
    Parses MathML expressions into :class:`myokit.Expression` objects.

    Arguments:

    ``name_factory``
        A callable with arguments ``(name_as_string, element)`` that returns
        :class:`myokit.Name` objects.
    ``number_factory``
        A callable with arguments ``(number_as_float, element)`` that returns
        :class:`myokit.Number` objects. Note that ``element`` can be ``None``
        for numbers that have no corresponding ``<cn>`` element.
    ``free_variables``
        All :class:`Name` objects for free variables in derivative expressions
        will be added to this set.

    This is not a validating parser: if the MathML is invalid the method's
    behaviour is undefined.

    The following MathML elements are recognised:

    Literals and references

    ``<ci>``
        Is converted to a :class:`myokit.Name` by passing the contents of the
        ``ci`` tag to the ``name_factory``.
    ``<diff>`` (with ``<bvar>`` and ``<degree>``)
        Becomes a :class:`myokit.Derivative`. Only first-order derivatives are
        supported. To check if the derivatives are all time-derivatives, the
        derivative post-processing function can be used.
    ``<cn>``
        Becomes a :class:`myokit.Number`. To process units which may be present
        in the tag's attributes (esp. in CellML) the number post-processing
        function can be used.
    ``<csymbol>``
        Is converted to a :class:`myokit.Name` by passing the contents of its
        ``definitionURL`` to the ``name_factory``. Note that ``csymbols``
        representing operators or functions are not supported.

    Algebra

    ``<plus>``
        Becomes a :class:`myokit.PrefixPlus`, a :class`myokit.Plus` or a tree
        of :class:`myokit.Plus` elements.
    ``<minus>``
        Becomes a :class:`myokit.PrefixMinus`, a :class`myokit.Minus` or a tree
        of :class:`myokit.Minus` elements.
    ``<times>``
        Becomes a :class:`myokit.Multiply` or a tree of
        :class:`myokit.Multiply` elements.
    ``<divide>``
        Becomes a :class:`myokit.Divide` or a tree of :class:`myokit.Divide`
        elements.
    ``<apply>``
        Used to indicate the tree structure of the equation. These get
        translated but don't have a Myokit counterpart.

    Functions

    ``<power>``
        Becomes a :class:`myokit.Power`.
    ``<root>`` (with ``<degree>``)
        Becomes a :class:`myokit.Sqrt`.
    ``<exp>``
        Becomes a :class:`myokit.Exp`.
    ``<ln>``
        Becomes a :class:`myokit.Log`.
    ``<log>`` (with ``<logbase>``)
        Becomes a :class:`myokit.Log10` or a :class:`myokit.Log`.
    ``<abs>``
        Becomes a :class:`myokit.Abs`.
    ``<floor>``
        Becomes a :class:`myokit.Floor`.
    ``<ceiling>``
        Becomes a :class:`myokit.Ceil`.
    ``<quotient>``
        Becomes a :class:`myokit.Quotient`.
    ``<rem>``
        Becomes a :class:`myokit.Remainder`.

    Trigonometry

    ``<sin>``, ``<cos>`` and ``<tan>``
        Become :class:`myokit.Sin`, :class:`myokit.Cos` and
        :class:`myokit.Tan`.
    ``<arcsin>``, ``<arccos>`` and ``<arctan>``
        Become :class:`myokit.ASin`, :class:`myokit.ACos` and
        :class:`myokit.ATan`.
    ``<csc>``, ``<sec>`` and ``<cot>``
        Become ``1/sin``, ``1/cos`` and ``1/tan``.
    ``<arccsc>``, ``<arcsec>`` and ``<arccot>``
        Become ``asin(1/x)``, ``acos(1/x)`` and ``atan(1/x)``.

    Hyperbolic trigonometry

    ``<sinh>``
        Becomes ``0.5 * (exp(x) - exp(-x))``.
    ``<cosh>``
        Becomes ``0.5 * (exp(x) + exp(-x))``.
    ``<tanh>``
        Becomes ``(exp(2 * x) - 1) / (exp(2 * x) + 1)``.
    ``<arcsinh>``
        Becomes ``log(x + sqrt(x*x + 1))``.
    ``<arccosh>``
        Becomes ``log(x + sqrt(x*x - 1))``.
    ``<arctanh>``
        Becomes ``0.5 * log((1 + x) / (1 - x))``.
    ``<csch>``
        Becomes ``2 / (exp(x) - exp(-x))``.
    ``<sech>``
        Becomes ``2 / (exp(x) + exp(-x))``.
    ``<coth>``
        Becomes ``(exp(2 * x) + 1) / (exp(2 * x) - 1)``.
    ``<arccsch>``
        Becomes ``log(1 / x + sqrt(1 / x^2 + 1))``.
    ``<arcsech>``
        Becomes ``log(1 / x + sqrt(1 / x^2 - 1))``
    ``<arccoth>``
        Becomes ``0.5 * log((x + 1) / (x - 1))``.

    Logic and relations

    ``<piecewise>``, ``<piece>`` and ``<otherwise>``
        Becomes a :class:`myokit.Piecewise`.
    ``<and>``, ``<or>`` and ``<not>``
        Become :class:`myokit.And`, :class:`myokit.Or` and :class:`myokit.Not`.
    ``<xor>``
        Becomes ``(x or y) and not(x and y)``
    ``<eq>`` and ``<neq>``
        Becomes :class:`myokit.Equal` and :class:`NotEqual`.
    ``<lt>`` and ``<gt>``
        Become :class:`myokit.Less` and :class:`myokit.More`.
    ``<leq>`` and ``<geq>``
        Become :class:`myokit.LessEqual` and :class:`myokit.MoreEqual`.

    Constants

    ``<pi>``
        Becomes ``3.14159265358979323846``
    ``<exponentiale>``
        Becomes ``exp(1)``
    ``<true>``
        Becomes ``1``
    ``<false>``
        Becomes ``0``

    """
    def __init__(self, variable_factory, number_factory, free_variables=set()):
        self._vfac = variable_factory
        self._nfac = number_factory
        self._const = lambda x: number_factory(x, None)
        self._free_variables = free_variables

    def _eat(self, element, iterator, nargs=1):
        """
        Takes ``nargs`` elements from the ``iterator``, which should be
        pointing at the first element after ``element``.

        Will complain if there are fewer or more than ``nargs`` elements
        available from the iterator.

        ``element``
            The element just before the iterator (used in error messages).
        ``iterator``
            An iterator pointing at the first element after ``element``.
        ``nargs``
            The required number of arguments that ``iterator`` should still
            contain.

        """
        # Get all operands
        ops = [self._parse_atomic(x) for x in iterator]

        # Check number of operands
        if len(ops) != nargs:
            raise MathMLError(
                'Expecting ' + str(nargs) + ' operand(s), got ' + str(len(ops))
                + ' for ' + split(element.tag)[1] + '.', element)

        return ops

    def _next(self, iterator, tag=None):
        """
        Returns the next element from an ``iterator``.

        If ``tag`` is given, elements will be drawn from the iterator until an
        element with the given tag is found.
        """
        try:
            # Return next element
            if tag is None:
                return next(iterator)

            # Find a specific element
            el = next(iterator)
            while split(el.tag)[1] != tag:
                el = next(iterator)
            return el

        # Ran out of elements
        except StopIteration:
            return None

    def parse(self, element):
        """
        Parses a MathML expression, rooted in the given ``<apply>`` element,
        and returns a :class:`myokit.Expression`.

        Arguments:

        ``element``
            An ``xml.etree.ElementTree.Element`` (or similar) to start parsing
            from. Must be an ``<apply>`` element.

        """
        # Remove <math> element, if found
        ns, el = split(element.tag)
        if el == 'math':
            element = element[0]

        return self._parse_atomic(element)

    def _parse_atomic(self, element):
        """
        Parses a bit of MathML entirely encoded in ``element``, i.e. a number,
        variable, or apply.
        """

        # Get element type, decide what to do
        _, name = split(element.tag)

        # Brackets
        if name == 'apply':
            return self._parse_apply(element)

        # Variable reference
        elif name == 'ci':
            return self._parse_name(element)

        # Number
        elif name == 'cn':
            return self._parse_number(element)

        elif name == 'csymbol':
            return self._parse_symbol(element)

        # Constants
        elif name == 'pi':
            return self._const('3.14159265358979323846')
        elif name == 'exponentiale':
            return myokit.Exp(self._const(1))
        elif name == 'true':
            # This is correct, ``True == 1`` -> False, ``True == 2`` -> False
            return self._const(1)
        elif name == 'false':
            return self._const(0)
        elif name == 'notanumber':
            return self._const(float('nan'))
        elif name == 'infinity':
            return self._const(float('inf'))

        # Piecewise statement
        elif name == 'piecewise':
            return self._parse_piecewise(element)

        # Unexpected element
        else:
            raise MathMLError(
                'Unsupported element: ' + str(element.tag) + '.', element)

    def _parse_apply(self, apply_element):
        """
        Parses an ``<apply>`` element.
        """
        # Apply must have kids
        if len(apply_element) == 0:
            raise MathMLError(
                'Apply must contain at least one child element.',
                apply_element)

        # Get first child
        iterator = iter(apply_element)
        element = self._next(iterator)

        # Decide what to do based on first child
        _, name = split(element.tag)

        # Handle derivative
        if name == 'diff':
            return self._parse_derivative(element, iterator)

        # Algebra (unary/binary/n-ary operators)
        elif name == 'plus':
            return self._parse_nary(
                element, iterator, myokit.Plus, myokit.PrefixPlus)
        elif name == 'minus':
            return self._parse_nary(
                element, iterator, myokit.Minus, myokit.PrefixMinus)
        elif name == 'times':
            return self._parse_nary(element, iterator, myokit.Multiply)
        elif name == 'divide':
            return self._parse_nary(element, iterator, myokit.Divide)

        # Basic functions
        elif name == 'exp':
            return myokit.Exp(*self._eat(element, iterator))
        elif name == 'ln':
            return myokit.Log(*self._eat(element, iterator))
        elif name == 'log':
            return self._parse_log(element, iterator)
        elif name == 'root':
            return self._parse_root(element, iterator)
        elif name == 'power':
            return myokit.Power(*self._eat(element, iterator, 2))
        elif name == 'floor':
            return myokit.Floor(*self._eat(element, iterator))
        elif name == 'ceiling':
            return myokit.Ceil(*self._eat(element, iterator))
        elif name == 'abs':
            return myokit.Abs(*self._eat(element, iterator))
        elif name == 'quotient':
            return myokit.Quotient(*self._eat(element, iterator, 2))
        elif name == 'rem':
            return myokit.Remainder(*self._eat(element, iterator, 2))

        # Logic
        elif name == 'and':
            return self._parse_nary(element, iterator, myokit.And)
        elif name == 'or':
            return self._parse_nary(element, iterator, myokit.Or)
        elif name == 'xor':
            # Becomes ``(x or y) and not(x and y)``
            x, y = self._eat(element, iterator, 2)
            return myokit.And(myokit.Or(x, y), myokit.Not(myokit.And(x, y)))

        elif name == 'not':
            return myokit.Not(*self._eat(element, iterator))
        elif name == 'eq' or name == 'equivalent':
            return myokit.Equal(*self._eat(element, iterator, 2))
        elif name == 'neq':
            return myokit.NotEqual(*self._eat(element, iterator, 2))
        elif name == 'gt':
            return myokit.More(*self._eat(element, iterator, 2))
        elif name == 'lt':
            return myokit.Less(*self._eat(element, iterator, 2))
        elif name == 'geq':
            return myokit.MoreEqual(*self._eat(element, iterator, 2))
        elif name == 'leq':
            return myokit.LessEqual(*self._eat(element, iterator, 2))

        # Trigonometry
        elif name == 'sin':
            return myokit.Sin(*self._eat(element, iterator))
        elif name == 'cos':
            return myokit.Cos(*self._eat(element, iterator))
        elif name == 'tan':
            return myokit.Tan(*self._eat(element, iterator))
        elif name == 'arcsin':
            return myokit.ASin(*self._eat(element, iterator))
        elif name == 'arccos':
            return myokit.ACos(*self._eat(element, iterator))
        elif name == 'arctan':
            return myokit.ATan(*self._eat(element, iterator))

        # Redundant trigonometry (CellML includes this)
        elif name == 'csc':
            # Cosecant: csc(x) = 1 / sin(x)
            return myokit.Divide(
                self._const(1), myokit.Sin(*self._eat(element, iterator)))
        elif name == 'sec':
            # Secant: sec(x) = 1 / cos(x)
            return myokit.Divide(
                self._const(1), myokit.Cos(*self._eat(element, iterator)))
        elif name == 'cot':
            # Contangent: cot(x) = 1 / tan(x)
            return myokit.Divide(
                self._const(1), myokit.Tan(*self._eat(element, iterator)))
        elif name == 'arccsc':
            # ArcCosecant: acsc(x) = asin(1/x)
            return myokit.ASin(
                myokit.Divide(self._const(1), *self._eat(element, iterator)))
        elif name == 'arcsec':
            # ArcSecant: asec(x) = acos(1/x)
            return myokit.ACos(
                myokit.Divide(self._const(1), *self._eat(element, iterator)))
        elif name == 'arccot':
            # ArcCotangent: acot(x) = atan(1/x)
            return myokit.ATan(
                myokit.Divide(self._const(1), *self._eat(element, iterator)))

        # Hyperbolic trig
        elif name == 'sinh':
            # Hyperbolic sine: sinh(x) = 0.5 * (e^x - e^-x)
            x = self._eat(element, iterator)[0]
            return myokit.Multiply(
                self._const(0.5), myokit.Minus(
                    myokit.Exp(x), myokit.Exp(myokit.PrefixMinus(x))))
        elif name == 'cosh':
            # Hyperbolic cosine: cosh(x) = 0.5 * (e^x + e^-x)
            x = self._eat(element, iterator)[0]
            return myokit.Multiply(
                self._const(0.5), myokit.Plus(
                    myokit.Exp(x), myokit.Exp(myokit.PrefixMinus(x))))
        elif name == 'tanh':
            # Hyperbolic tangent: tanh(x) = (e^2x - 1) / (e^2x + 1)
            x = self._eat(element, iterator)[0]
            e2x = myokit.Exp(myokit.Multiply(self._const(2), x))
            return myokit.Divide(
                myokit.Minus(e2x, self._const(1)),
                myokit.Plus(e2x, self._const(1)))
        elif name == 'arcsinh':
            # Inverse hyperbolic sine: asinh(x) = log(x + sqrt(x*x + 1))
            x = self._eat(element, iterator)[0]
            return myokit.Log(myokit.Plus(x, myokit.Sqrt(myokit.Plus(
                myokit.Multiply(x, x), self._const(1)))))
        elif name == 'arccosh':
            # Inverse hyperbolic cosine:
            #   acosh(x) = log(x + sqrt(x*x - 1))
            x = self._eat(element, iterator)[0]
            return myokit.Log(myokit.Plus(x, myokit.Sqrt(myokit.Minus(
                myokit.Multiply(x, x), self._const(1)))))
        elif name == 'arctanh':
            # Inverse hyperbolic tangent:
            #   atanh(x) = 0.5 * log((1 + x) / (1 - x))
            x = self._eat(element, iterator)[0]
            return myokit.Multiply(
                self._const(0.5), myokit.Log(myokit.Divide(
                    myokit.Plus(self._const(1), x),
                    myokit.Minus(self._const(1), x))))

        # Hyperbolic redundant trig
        elif name == 'csch':
            # Hyperbolic cosecant: csch(x) = 2 / (exp(x) - exp(-x))
            x = self._eat(element, iterator)[0]
            return myokit.Divide(
                self._const(2), myokit.Minus(
                    myokit.Exp(x), myokit.Exp(myokit.PrefixMinus(x))))
        elif name == 'sech':
            # Hyperbolic secant: sech(x) = 2 / (exp(x) + exp(-x))
            x = self._eat(element, iterator)[0]
            return myokit.Divide(
                self._const(2), myokit.Plus(
                    myokit.Exp(x), myokit.Exp(myokit.PrefixMinus(x))))
        elif name == 'coth':
            # Hyperbolic cotangent:
            #   coth(x) = (exp(2*x) + 1) / (exp(2*x) - 1)
            x = self._eat(element, iterator)[0]
            e2x = myokit.Exp(myokit.Multiply(self._const(2), x))
            return myokit.Divide(
                myokit.Plus(e2x, self._const(1)),
                myokit.Minus(e2x, self._const(1)))
        elif name == 'arccsch':
            # Inverse hyperbolic cosecant:
            #   arccsch(x) = log(1 / x + sqrt(1 / x^2 + 1))
            x = self._eat(element, iterator)[0]
            return myokit.Log(myokit.Plus(
                myokit.Divide(self._const(1), x),
                myokit.Sqrt(myokit.Plus(
                    myokit.Divide(self._const(1), myokit.Multiply(x, x)),
                    self._const(1)))))
        elif name == 'arcsech':
            # Inverse hyperbolic secant:
            #   arcsech(x) = log(1 / x + sqrt(1 / x^2 - 1))
            x = self._eat(element, iterator)[0]
            return myokit.Log(myokit.Plus(
                myokit.Divide(self._const(1), x),
                myokit.Sqrt(myokit.Minus(
                    myokit.Divide(self._const(1), myokit.Multiply(x, x)),
                    self._const(1)))))
        elif name == 'arccoth':
            # Inverse hyperbolic cotangent:
            #   arccoth(x) = 0.5 * log((x + 1) / (x - 1))
            x = self._eat(element, iterator)[0]
            return myokit.Multiply(
                self._const(0.5), myokit.Log(myokit.Divide(
                    myokit.Plus(x, self._const(1)),
                    myokit.Minus(x, self._const(1)))))

        # Last option: A single atomic inside an apply
        # Do this one last to stop e.g. <apply><times /></apply> returning the
        # error 'Unsupported element' (which is what parse_atomic would call).
        elif len(apply_element) == 1:
            return self._parse_atomic(element)

        # Unexpected element
        else:
            raise MathMLError(
                'Unsupported element in apply: ' + str(element.tag) + '.',
                element)

    def _parse_derivative(self, element, iterator):
        """
        Parses the elements folling a ``<diff>`` element.

        Arguments

        ``element``
            A ``<diff>`` element
        ``iterator``
            An iterator pointing at the next element.

        """

        # Get free variable
        bvar = self._next(iterator, 'bvar')
        if bvar is None:
            raise MathMLError(
                '<diff> element must contain a <bvar>.', element)
        ci = self._next(iter(bvar), 'ci')
        if ci is None:
            raise MathMLError(
                '<bvar> element must contain a <ci>', element)
        self._free_variables.add(self._parse_name(ci))

        # Check degree, if given
        degree = self._next(iter(bvar), 'degree')
        if degree is not None:
            cn = self._next(iter(degree), 'cn')
            if cn is None:
                raise MathMLError(
                    '<degree> element must contain a <cn>.', degree)
            d = self._parse_number(cn)
            if d.eval() != 1:
                raise MathMLError(
                    'Only derivatives of degree one are supported.', cn)

        # Get Name object
        ci = self._next(iterator, 'ci')
        if ci is None:
            raise MathMLError(
                '<diff> element must contain a <ci> after its <bvar>'
                ' element (derivatives of expressions are not supported.',
                element)
        var = self._parse_name(ci)

        return myokit.Derivative(var)

    def _parse_log(self, element, iterator):
        """
        Parses the elements following a ``<log>`` element.

        Arguments:

        ``element``
            The ``<log>`` element.
        ``iterator``
            An iterator pointing at the first element after ``element``.

        """
        # Get next operands
        ops = [x for x in iterator]

        # Check for zero ops
        if len(ops) == 0:
            raise MathMLError(
                'Expecting operand after <log> element.', element)

        # Check if first op is logbase
        if split(ops[0].tag)[1] == 'logbase':

            # Get logbase
            base = ops[0]
            if len(base) != 1:
                raise MathMLError(
                    'Expecting a single operand inside <logbase> element.',
                    base)
            base = self._parse_atomic(base[0])

            # Get main operand
            if len(ops) != 2:
                raise MathMLError(
                    'Expecting a single operand after the <logbase> element'
                    ' inside a <log>.', element)
            op = self._parse_atomic(ops[1])

        # No logbase given
        else:
            base = None

            if len(ops) != 1:
                raise MathMLError(
                    'Expecting a single operand (or a <logbase> followed by a'
                    ' single operand) inside a <log> element.', element)
            op = self._parse_atomic(ops[0])

        if base is None or base.eval() == 10:
            return myokit.Log10(op)
        else:
            return myokit.Log(op, base)

    def _parse_nary(self, element, iterator, binary, unary=None):
        """
        Parses operands for unary, binary, or n-ary operators (for example
        plus, minus, times and division).

        If n-ary expressions (n > 2) are encountered, these are converted to
        Myokit expression trees.

        Arguments:

        ``element``
            The element that determined the operator type.
        ``iterator``
            An iterator pointing at the first element after ``element``.
        ``binary``
            A ``myokit.Expression`` subclass for a binary expression.
        ``unary``
            An optional ``myokit.Expression`` subclass for unary operators.

        """
        # Get all operands
        ops = [self._parse_atomic(x) for x in iterator]

        # Check the number of operands
        n = len(ops)
        if n < 1:
            raise MathMLError(
                'Operator needs at least one operand.', element)
        if n < 2:
            if unary:
                return unary(ops[0])
            else:
                raise MathMLError(
                    'Operator needs at least two operands', element)

        # Create nested binary expressions and return
        ex = binary(ops[0], ops[1])
        for i in range(2, n):
            ex = binary(ex, ops[i])
        return ex

    def _parse_number(self, element):
        """
        Parses a ``<cn>`` element and returns a number object created by the
        number factory.
        """
        # https://www.w3.org/TR/MathML2/chapter4.html#contm.typeattrib
        kind = element.attrib.get('type', 'real')

        # Get value
        if kind == 'real':
            # Float, specified as 123.123 (no exponent!)
            # May be in a different base than 10
            base = element.attrib.get('base', '10').strip()
            try:
                base = float(base)
            except (TypeError, ValueError):
                raise MathMLError(
                    'Invalid base specified on <ci> element.', element)
            if base != 10:
                raise MathMLError(
                    'Numbers in bases other than 10 are not supported.',
                    element)

            # Get value
            # Note: We are being tolerant here and allowing e-notation (which
            # is not consistent with the spec!)
            if element.text is None:
                raise MathMLError('Empty <cn> element', element)
            try:
                value = float(element.text.strip())
            except ValueError:
                raise MathMLError(
                    'Unable to convert contents of <cn> to a real number: "'
                    + str(element.text) + '"', element)

        elif kind == 'integer':
            # Integer in any given base
            base = element.attrib.get('base', '10').strip()
            try:
                base = int(base)
            except ValueError:
                raise MathMLError(
                    'Unable to parse base of <cn> element: "' + base + '"',
                    element)

            # Get value
            if element.text is None:
                raise MathMLError('Empty <cn> element', element)
            try:
                value = int(element.text.strip(), base)
            except ValueError:
                raise MathMLError(
                    'Unable to convert contents of <cn> to an integer: "'
                    + str(element.text) + '"', element)

        elif kind == 'double':
            # Floating point (positive, negative, exponents, etc)

            if element.text is None:
                raise MathMLError('Empty <cn> element', element)
            try:
                value = float(element.text.strip())
            except ValueError:
                raise MathMLError(
                    'Unable to convert contents of <cn> to a real number: "'
                    + str(element.text) + '"', element)

        elif kind == 'e-notation':
            # 1<sep />3 = 1e3

            # Check contents
            parts = [x for x in element]
            if len(parts) != 1 or split(parts[0].tag)[1] != 'sep':
                raise MathMLError(
                    'Number in e-notation should have the format'
                    ' number<sep />number.', element)

            # Get parts of number
            sig = element.text
            exp = parts[0].tail
            if sig is None or not sig.strip():
                raise MathMLError(
                    'Unable to parse number in e-notation: missing part before'
                    ' the separator.', element)
            if exp is None or not exp.strip():
                raise MathMLError(
                    'Unable to parse number in e-notation: missing part after'
                    ' the separator.', element)

            # Get value
            try:
                value = float(sig.strip() + 'e' + exp.strip())
            except ValueError:
                raise MathMLError(
                    'Unable to parse number in e-notation "' + sig + 'e' + exp
                    + '".', element)

        elif kind == 'rational':
            # 1<sep />3 = 1 / 3
            # Check contents
            parts = [x for x in element]
            if len(parts) != 1 or split(parts[0].tag)[1] != 'sep':
                raise MathMLError(
                    'Rational number should have the format'
                    ' number<sep />number.', element)

            # Get parts of number
            numer = element.text
            denom = parts[0].tail
            if numer is None or not numer.strip():
                raise MathMLError(
                    'Unable to parse rational number: missing part before the'
                    ' separator.', element)
            if denom is None or not denom.strip():
                raise MathMLError(
                    'Unable to parse rational number: missing part after the'
                    ' separator.', element)

            # Get value
            try:
                value = float(numer.strip()) / float(denom.strip())
            except ValueError:
                raise MathMLError(
                    'Unable to parse rational number "' + numer + ' / ' + denom
                    + '".', element)

        else:
            raise MathMLError('Unsupported <cn> type: ' + kind, element)

        # Create number and return
        return self._nfac(value, element)

    def _parse_piecewise(self, element):
        """
        Parses a ``<piecewise>`` element.
        """

        # Piecewise contains at least one piece, optionally contains an
        # "otherwise". Syntax doesn't ensure this statement makes sense.
        ops = []
        other = None

        # Scan pieces
        for child in element:
            _, el = split(child.tag)

            if el == 'piece':
                if len(child) != 2:
                    raise MathMLError(
                        '<piece> element must have exactly 2 children.', child)
                ops.append(self._parse_atomic(child[1]))    # Condition
                ops.append(self._parse_atomic(child[0]))    # Value

            elif el == 'otherwise':
                if other is not None:
                    raise MathMLError(
                        'Found more than one <otherwise> inside a <piecewise>'
                        ' element.', child)
                if len(child) != 1:
                    raise MathMLError(
                        '<otherwise> element must have exactly 1 child.',
                        child)
                other = self._parse_atomic(child[0])

            else:
                raise MathMLError(
                    'Unexpected content in <piecewise>. Expecting <piece> or'
                    ' <otherwise>, found <' + el + '>.', child)

        # Add otherwise
        if other is None:
            ops.append(self._const(0))
        else:
            ops.append(other)

        return myokit.Piecewise(*ops)

    def _parse_root(self, element, iterator):
        """
        Parses the elements following a ``<root>`` element.

        Arguments:

        ``element``
            The ``<root>`` element.
        ``iterator``
            An iterator pointing at the first element after ``element``.

        """
        # Get next operands
        ops = [x for x in iterator]

        # Check for zero ops
        if len(ops) == 0:
            raise MathMLError(
                'Expecting operand after <root> element.', element)

        # Check if first op is degree
        if split(ops[0].tag)[1] == 'degree':

            # Get degree
            degree = ops[0]
            if len(degree) != 1:
                raise MathMLError(
                    'Expecting a single operand inside <degree> element.',
                    degree)
            degree = self._parse_atomic(degree[0])

            # Get main operand
            if len(ops) != 2:
                raise MathMLError(
                    'Expecting a single operand after the <degree> element'
                    ' inside a <root>.', element)
            op = self._parse_atomic(ops[1])

            # Return expression
            if degree.eval() == 2:
                return myokit.Sqrt(op)
            return myokit.Power(op, myokit.Divide(self._const(1), degree))

        # No degree given
        if len(ops) != 1:
            raise MathMLError(
                'Expecting a single operand (or a <degree> followed by a'
                ' single operand) inside a <root> element.', element)
        op = self._parse_atomic(ops[0])

        return myokit.Sqrt(op)

    def _parse_name(self, element):
        """
        Parses a ``<ci>`` element and returns a :class:`myokit.Name` created by
        the name factory.
        """
        if element.text is None:
            raise MathMLError(
                '<ci> element must contain a variable name.', element)

        symbol = element.text.strip()
        try:
            return self._vfac(symbol, element)
        except Exception as e:
            raise MathMLError('Unable to create Name: ' + str(e), element)

    def _parse_symbol(self, element):
        """
        Parses only ``<csymbol>`` elements that represent special variables
        and returns a :class:`myokit.Name` created by the name factory.
        """
        symbol = element.get('definitionURL')
        if symbol is None:
            raise MathMLError(
                '<csymbol> element must contain a definitionURL attribute.',
                element)

        symbol = symbol.strip()
        try:
            return self._vfac(symbol, element)
        except Exception as e:
            raise MathMLError(
                'Unable to create Name from csymbol: ' + str(e), element)

