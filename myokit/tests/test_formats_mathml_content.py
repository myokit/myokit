#!/usr/bin/env python
#
# Tests the importers for various formats
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import unittest
import xml.etree.ElementTree as etree

import myokit
import myokit.formats.mathml as mathml

# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp


def read(xml, var_table=None):
    """ Parse a MathML string. """

    if var_table is None:
        p = mathml.MathMLParser(
            lambda x, y: myokit.Name(x),
            lambda x, y: myokit.Number(x),
        )
    else:
        p = mathml.MathMLParser(
            lambda x, y: myokit.Name(var_table[x]),
            lambda x, y: myokit.Number(x),
        )

    return p.parse(etree.fromstring(xml))


class ContentMathMLTest(unittest.TestCase):
    """ Test expression writing and parsing of content MathML. """

    def test_content(self):
        """ Test writing and reading of content MathML. """
        model = myokit.Model()
        component = model.add_component('c')
        avar = component.add_variable('a')

        w = mathml.MathMLExpressionWriter()
        w.set_mode(presentation=False)

        def r(ex):
            return read(ex, {'c.a': avar})

        # Name
        a = myokit.Name(avar)
        ca = '<ci>c.a</ci>'
        self.assertEqual(w.ex(a), ca)
        self.assertEqual(r(ca), a)

        # Number without unit
        b = myokit.Number(1)
        cb = '<cn>1.0</cn>'
        self.assertEqual(w.ex(b), cb)

        # Number with unit
        c = myokit.Number('12', 'pF')
        cc = '<cn>12.0</cn>'
        self.assertEqual(w.ex(c), cc)
        # Unit isn't exported
        #self.assertEqual(r(cc), c)

        # Prefix plus
        x = myokit.PrefixPlus(b)
        cx = '<apply><plus />' + cb + '</apply>'
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r(cx), x)

        # Prefix minus
        x = myokit.PrefixMinus(b)
        cx = '<apply><minus />' + cb + '</apply>'
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r(cx), x)

        # Plus
        x = myokit.Plus(a, b)
        cx = '<apply><plus />' + ca + cb + '</apply>'
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r(cx), x)

        # Minus
        x = myokit.Minus(a, b)
        cx = '<apply><minus />' + ca + cb + '</apply>'
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r(cx), x)

        # Multiply
        x = myokit.Multiply(a, b)
        cx = '<apply><times />' + ca + cb + '</apply>'
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r(cx), x)

        # Divide
        x = myokit.Divide(a, b)
        cx = '<apply><divide />' + ca + cb + '</apply>'
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r(cx), x)

        # Power
        x = myokit.Power(a, b)
        cx = '<apply><power />' + ca + cb + '</apply>'
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r(cx), x)

        # Sqrt
        x = myokit.Sqrt(b)
        cx = '<apply><root />' + cb + '</apply>'
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r(cx), x)

        # Exp
        x = myokit.Exp(a)
        cx = '<apply><exp />' + ca + '</apply>'
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r(cx), x)

        # Log(a)
        x = myokit.Log(b)
        cx = '<apply><ln />' + cb + '</apply>'
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r(cx), x)

        # Log(a, b)
        x = myokit.Log(a, b)
        cx = '<apply><log /><logbase>' + cb + '</logbase>' + ca + '</apply>'
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r(cx), x)

        # Log10
        x = myokit.Log10(b)
        cx = '<apply><log />' + cb + '</apply>'
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r(cx), x)

        # Sin
        x = myokit.Sin(b)
        cx = '<apply><sin />' + cb + '</apply>'
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r(cx), x)

        # Cos
        x = myokit.Cos(b)
        cx = '<apply><cos />' + cb + '</apply>'
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r(cx), x)

        # Tan
        x = myokit.Tan(b)
        cx = '<apply><tan />' + cb + '</apply>'
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r(cx), x)

        # ASin
        x = myokit.ASin(b)
        cx = '<apply><arcsin />' + cb + '</apply>'
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r(cx), x)

        # ACos
        x = myokit.ACos(b)
        cx = '<apply><arccos />' + cb + '</apply>'
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r(cx), x)

        # ATan
        x = myokit.ATan(b)
        cx = '<apply><arctan />' + cb + '</apply>'
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r(cx), x)

        # Floor
        x = myokit.Floor(b)
        cx = '<apply><floor />' + cb + '</apply>'
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r(cx), x)

        # Ceil
        x = myokit.Ceil(b)
        cx = '<apply><ceiling />' + cb + '</apply>'
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r(cx), x)

        # Abs
        x = myokit.Abs(b)
        cx = '<apply><abs />' + cb + '</apply>'
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r(cx), x)

        # Quotient
        x = myokit.Quotient(a, b)
        cx = '<apply><quotient />' + ca + cb + '</apply>'
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r(cx), x)

        # Remainder
        x = myokit.Remainder(a, b)
        cx = '<apply><rem />' + ca + cb + '</apply>'
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r(cx), x)

        # Equal
        x = myokit.Equal(a, b)
        cx = '<apply><eq />' + ca + cb + '</apply>'
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r(cx), x)

        # NotEqual
        x = myokit.NotEqual(a, b)
        cx = '<apply><neq />' + ca + cb + '</apply>'
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r(cx), x)

        # More
        x = myokit.More(a, b)
        cx = '<apply><gt />' + ca + cb + '</apply>'
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r(cx), x)

        # Less
        x = myokit.Less(a, b)
        cx = '<apply><lt />' + ca + cb + '</apply>'
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r(cx), x)

        # MoreEqual
        x = myokit.MoreEqual(a, b)
        cx = '<apply><geq />' + ca + cb + '</apply>'
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r(cx), x)

        # LessEqual
        x = myokit.LessEqual(a, b)
        cx = '<apply><leq />' + ca + cb + '</apply>'
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r(cx), x)

        # Not
        cond1 = myokit.parse_expression('5 > 3')
        cond2 = myokit.parse_expression('2 < 1')
        c1 = '<apply><gt /><cn>5.0</cn><cn>3.0</cn></apply>'
        c2 = '<apply><lt /><cn>2.0</cn><cn>1.0</cn></apply>'
        x = myokit.Not(cond1)
        cx = '<apply><not />' + c1 + '</apply>'
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r(cx), x)

        # And
        x = myokit.And(cond1, cond2)
        cx = '<apply><and />' + c1 + c2 + '</apply>'
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r(cx), x)

        # Or
        x = myokit.Or(cond1, cond2)
        cx = '<apply><or />' + c1 + c2 + '</apply>'
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r(cx), x)

        # If
        x = myokit.If(cond1, a, b)
        cx = (
            '<piecewise>'
            '<piece>' + ca + c1 + '</piece>'
            '<otherwise>' + cb + '</otherwise>'
            '</piecewise>'
        )
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r(cx), x.piecewise())

        # Piecewise
        x = myokit.Piecewise(cond1, a, cond2, b, myokit.Number(100))
        cx = (
            '<piecewise>'
            '<piece>' + ca + c1 + '</piece>'
            '<piece>' + cb + c2 + '</piece>'
            '<otherwise><cn>100.0</cn></otherwise>'
            '</piecewise>'
        )
        self.assertEqual(w.ex(x), cx)
        self.assertEqual(r(cx), x)

    def test_writer(self):
        # Test special cases for the expression writer.

        # Create mini model
        model = myokit.Model()
        component = model.add_component('c')
        avar = component.add_variable('a')

        w = mathml.MathMLExpressionWriter()
        w.set_mode(presentation=False)

        a = avar.lhs()
        ca = '<ci>c.a</ci>'
        b = myokit.Number(1)
        cb = '<cn>1.0</cn>'

        # Equation
        e = myokit.Equation(a, b)
        ce = '<apply><eq />' + ca + cb + '</apply>'
        self.assertEqual(w.eq(e), ce)

        # Test for unfound variable (invalid cellml model)
        x = myokit.Name('a string')
        self.assertEqual(w.ex(x), '<ci>a string</ci>')

        # Test lhs function
        w.set_lhs_function(lambda v: 'bert')
        x = myokit.Name(avar)
        self.assertEqual(w.ex(x), '<ci>bert</ci>')

        # Unsupported type
        u = myokit.UnsupportedFunction('frog', x)
        self.assertRaises(ValueError, w.ex, u)

        # Test fetching using ewriter method
        w = myokit.formats.ewriter('mathml')
        self.assertIsInstance(w, mathml.MathMLExpressionWriter)

        # Test without a Myokit expression
        self.assertRaisesRegex(
            ValueError, 'Unknown expression type', w.ex, 7)

    def test_parse_mathml_string(self):
        # Test :meth:`mathml.parse_mathml_string()`.

        self.assertEqual(
            mathml.parse_mathml_string('<apply><cn>1.0</cn></apply>'),
            myokit.Number(1)
        )

    def test_parsing_bad_mathml(self):
        # Test the parser on various invalid bits of mathml.

        # No operands
        self.assertRaisesRegex(
            mathml.MathMLError, 'at least one operand', read,
            '<apply><times /></apply>')

        # Only one operand
        self.assertRaisesRegex(
            mathml.MathMLError, 'at least two operands', read,
            '<apply><times /><cn>1.0</cn></apply>')

        # Unresolvable reference
        x = '<apply><ci>bert</ci></apply>'
        self.assertRaisesRegex(
            mathml.MathMLError, 'Unable to create Name', read, x,
            {'ernie': 'banaan'})

        # Normal piecewise
        x = (
            '<piecewise>'
            '  <piece>'
            '    <cn>1</cn><apply><eq /><cn>1</cn><cn>1</cn></apply>'
            '  </piece>'
            '  <otherwise>'
            '    <cn>2</cn>'
            '  </otherwise>'
            '</piecewise>'
        )
        read(x)

        # Piecewise with extra otherwise
        x = (
            '<piecewise>'
            '  <piece>'
            '    <cn>1</cn><apply><eq /><cn>1</cn><cn>1</cn></apply>'
            '  </piece>'
            '  <otherwise>'
            '    <cn>2</cn>'
            '  </otherwise>'
            '  <otherwise>'
            '    <cn>3</cn>'
            '  </otherwise>'
            '</piecewise>'
        )
        self.assertRaisesRegex(
            mathml.MathMLError, 'Found more than one <otherwise>', read, x)

        # Piecewise without otherwise
        x = (
            '<piecewise>'
            '  <piece>'
            '    <cn>2</cn><apply><eq /><cn>1</cn><cn>1</cn></apply>'
            '  </piece>'
            '  <piece>'
            '    <cn>1</cn><apply><eq /><cn>1</cn><cn>1</cn></apply>'
            '  </piece>'
            '</piecewise>'
        )
        x = read(x)
        # Check otherwise is automatically added
        pieces = list(x.pieces())
        self.assertEqual(len(pieces), 3)
        self.assertEqual(pieces[0], myokit.Number(2))
        self.assertEqual(pieces[1], myokit.Number(1))
        self.assertEqual(pieces[2], myokit.Number(0))

        # Unexpected tag in piecwise
        x = (
            '<piecewise>'
            '  <piece>'
            '    <cn>1</cn><apply><eq /><cn>1</cn><cn>1</cn></apply>'
            '  </piece>'
            '  <otherwise>'
            '    <cn>3</cn>'
            '  </otherwise>'
            '  <apply><eq /><cn>1</cn><cn>1</cn></apply>'
            '</piecewise>'
        )
        self.assertRaisesRegex(
            mathml.MathMLError, 'Unexpected content in <piecewise>', read, x)

        # Unknown mathml tag
        self.assertRaisesRegex(
            mathml.MathMLError, 'Unsupported element', read,
            '<apply><yum /><ci>3</ci></apply>')

    def test_derivatives(self):
        # Test parsing of derivatives with degree elements.

        # Basic test
        read(
            '<apply>'
            '  <diff/>'
            '  <bvar>'
            '    <ci>time</ci>'
            '  </bvar>'
            '  <ci>V</ci>'
            '</apply>'
        )

        # Test with degree element
        read(
            '<apply>'
            '  <diff/>'
            '  <bvar>'
            '    <ci>time</ci>'
            '    <degree><cn>1</cn></degree>'
            '  </bvar>'
            '  <ci>V</ci>'
            '</apply>'
        )

        # Test with degree element other than 1
        self.assertRaisesRegex(
            mathml.MathMLError, 'degree one', read,
            '<apply>'
            '  <diff/>'
            '  <bvar>'
            '    <ci>time</ci>'
            '    <degree><cn>2</cn></degree>'
            '  </bvar>'
            '  <ci>V</ci>'
            '</apply>'
        )

        # Derivative of an expression
        self.assertRaisesRegex(
            mathml.MathMLError, '<diff> element must contain a <ci>', read,
            '<apply>'
            '  <diff/>'
            '  <bvar>'
            '    <ci>time</ci>'
            '  </bvar>'
            '  <apply><plus /><cn>1</cn><ci>V</ci></apply>'
            '</apply>'
        )

    def test_extra_trig(self):
        # Tests parsing of the annoying trig functions.

        # Cosecant
        x = read('<apply><csc/><cn>3</cn></apply>')
        y = myokit.parse_expression('1 / sin(3)')
        self.assertEqual(x, y)

        # Secant
        x = read('<apply><sec/><cn>3</cn></apply>')
        y = myokit.parse_expression('1 / cos(3)')
        self.assertEqual(x, y)

        # Cotangent
        x = read('<apply><cot/><cn>3</cn></apply>')
        y = myokit.parse_expression('1 / tan(3)')
        self.assertEqual(x, y)

        # arc-cosecant
        x = read('<apply><arccsc/><cn>3</cn></apply>')
        y = myokit.parse_expression('asin(1 / 3)')
        self.assertEqual(x, y)

        # arc-secant
        x = read('<apply><arcsec/><cn>3</cn></apply>')
        y = myokit.parse_expression('acos(1 / 3)')
        self.assertEqual(x, y)

        # arc-cotangent
        x = read('<apply><arccot/><cn>3</cn></apply>')
        y = myokit.parse_expression('atan(1 / 3)')
        self.assertEqual(x, y)

        # Hyperbolic sine
        x = read('<apply><sinh /><cn>3</cn></apply>')
        y = myokit.parse_expression('0.5 * (exp(3) - exp(-3))')
        self.assertEqual(x, y)

        # Hyperbolic cosine
        x = read('<apply><cosh /><cn>3</cn></apply>')
        y = myokit.parse_expression('0.5 * (exp(3) + exp(-3))')
        self.assertEqual(x, y)

        # Hyperbolic tangent
        x = read('<apply><tanh /><cn>3</cn></apply>')
        y = myokit.parse_expression('(exp(2*3) - 1) / (exp(2*3) + 1)')
        self.assertEqual(x, y)

        # Hyperbolic arc sine
        x = read('<apply><arcsinh /><cn>3</cn></apply>')
        y = myokit.parse_expression('log(3 + sqrt(1 + 3*3))')
        self.assertEqual(x, y)

        # Hyperbolic arc cosine
        x = read('<apply><arccosh /><cn>3</cn></apply>')
        y = myokit.parse_expression('log(3 + sqrt(3 + 1) * sqrt(3 - 1))')
        self.assertEqual(x, y)

        # Hyperbolic arc tangent
        x = read('<apply><arctanh /><cn>3</cn></apply>')
        y = myokit.parse_expression('0.5 * (log(1 + 3) - log(1 - 3))')
        self.assertEqual(x, y)

        # Hyperbolic cosecant
        x = read('<apply><csch /><cn>3</cn></apply>')
        y = myokit.parse_expression('2 / (exp(3) - exp(-3))')
        self.assertEqual(x, y)

        # Hyperbolic secant
        x = read('<apply><sech /><cn>3</cn></apply>')
        y = myokit.parse_expression('2 / (exp(3) + exp(-3))')
        self.assertEqual(x, y)

        # Hyperbolic cotangent
        x = read('<apply><coth /><cn>3</cn></apply>')
        y = myokit.parse_expression('(exp(2*3) + 1) / (exp(2*3) - 1)')
        self.assertEqual(x, y)

        # Hyperbolic arc cosecant
        x = read('<apply><arccsch /><cn>3</cn></apply>')
        y = myokit.parse_expression('log(sqrt(1/(3*3) + 1) + 1/3)')
        self.assertEqual(x, y)

        # Hyperbolic arc secant
        x = read('<apply><arcsech /><cn>3</cn></apply>')
        y = myokit.parse_expression('log(sqrt(1/(3*3) - 1) + 1/3)')
        self.assertEqual(x, y)

        # Hyperbolic arc cotangent
        x = read('<apply><arccoth /><cn>3</cn></apply>')
        y = myokit.parse_expression('0.5 * log((3 + 1) / (3 - 1))')
        self.assertEqual(x, y)

    def test_constants(self):
        # Tests parsing of MathML special constants.

        # Test pi
        import math
        x = read('<pi />')
        self.assertAlmostEqual(math.pi, float(x))

        # Test e
        import math
        x = read('<exponentiale />')
        self.assertAlmostEqual(math.e, float(x))

        # Test booleans
        import math
        x = read('<true />')
        self.assertEqual(float(x), 1)
        x = read('<false />')
        self.assertEqual(float(x), 0)

    def test_numbers(self):
        # Tests parsing of various MathML number types.

        # Real
        x = read('<cn>4</cn>')
        self.assertEqual(x, myokit.Number(4))
        x = read('<cn type="real">4</cn>')
        self.assertEqual(x, myokit.Number(4))
        # Real with base
        x = read('<cn type="real" base="10">4</cn>')
        self.assertEqual(x, myokit.Number(4))
        self.assertRaises(
            mathml.MathMLError, read, '<cn type="real" base="9">4</cn>')
        self.assertRaises(
            mathml.MathMLError, read, '<cn type="real" base="x">4</cn>')

        # Integer
        x = read('<cn type="integer">4</cn>')
        self.assertEqual(x, myokit.Number(4))

        x = read('<cn type="integer" base="2">100</cn>')
        self.assertEqual(x, myokit.Number(4))

        # Double
        x = read('<cn type="double">4</cn>')
        self.assertEqual(x, myokit.Number(4))

        # E-notation
        x = read('<cn type="e-notation">40<sep />-1</cn>')
        self.assertEqual(x, myokit.Number(4))

        # Rational
        x = read('<cn type="rational">16<sep />4</cn>')
        self.assertEqual(x, myokit.Number(4))

        # Unknown type
        self.assertRaisesRegex(
            mathml.MathMLError, 'Unsupported <cn> type',
            read, '<cn type="special">1</cn>')


if __name__ == '__main__':
    unittest.main()
