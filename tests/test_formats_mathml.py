#!/usr/bin/env python
#
# Tests the importers for various formats
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import unittest
import xml.dom.minidom

import myokit
import myokit.formats.mathml
from myokit.mxml import dom_child


class ContentMathMLTest(unittest.TestCase):
    """ Tests expression writing and parsing of content MathML. """

    def test_content(self):
        """ Test writing and reading of content MathML. """

        # Create mini model
        model = myokit.Model()
        component = model.add_component('c')
        avar = component.add_variable('a')

        w = myokit.formats.mathml.MathMLExpressionWriter()
        w.set_mode(presentation=False)

        def r(ex):
            """ Read a MathML element (e.g. an <apply>) """
            var_table = {'c.a': avar}
            x = dom_child(xml.dom.minidom.parseString(ex))
            return myokit.formats.mathml.parse_mathml_rhs(x, var_table)

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
        """ Tests special cases for the expression writer. """
        # Create mini model
        model = myokit.Model()
        component = model.add_component('c')
        avar = component.add_variable('a')

        w = myokit.formats.mathml.MathMLExpressionWriter()
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
        self.assertIsInstance(w, myokit.formats.mathml.MathMLExpressionWriter)

        # Test without a Myokit expression
        self.assertRaisesRegexp(
            ValueError, 'Unknown expression type', w.ex, 7)

    def test_parse_mathml(self):
        """
        Tests :meth:`myokit.formats.mathml.parse_mathml()`.
        """
        mathml = (
            '<math xmlns="http://www.w3.org/1998/Math/MathML">'
            '<apply><cn>1.0</cn></apply>'
            '</math>'
        )
        self.assertEqual(
            myokit.formats.mathml.parse_mathml(mathml), myokit.Number(1))

    def test_parsing_bad_mathml(self):
        """
        Tests the parser on various invalid bits of mathml.
        """
        def test(s):
            tag1 = '<math xmlns="http://www.w3.org/1998/Math/MathML">'
            tag2 = '</math>'
            myokit.formats.mathml.parse_mathml(tag1 + s + tag2)

        me = myokit.formats.mathml.MathMLError

        # No operands
        self.assertRaisesRegexp(
            me, 'at least one operand', test,
            '<apply><times /></apply>')

        # Only one operand
        self.assertRaisesRegexp(
            me, 'at least two operands', test,
            '<apply><times /><cn>1.0</cn></apply>')

        # Unresolvable reference
        x = '<apply><ci>bert</ci></apply>'
        var_table = {'ernie': 'banaan'}
        logger = myokit.formats.TextLogger()
        x = dom_child(xml.dom.minidom.parseString(x))
        myokit.formats.mathml.parse_mathml_rhs(x, var_table, logger=logger)
        w = list(logger.warnings())
        self.assertEqual(len(w), 1)
        self.assertIn('Unable to resolve', w[0])


class PresentationMathMLTest(unittest.TestCase):
    """
    Tests export of presentation MathML.
    """

    def test_presentation(self):
        """
        Tests the presentation MathML expression writer.
        """
        w = myokit.formats.mathml.MathMLExpressionWriter()
        w.set_mode(presentation=True)

        model = myokit.Model()
        component = model.add_component('c')
        avar = component.add_variable('a')

        # Name
        a = myokit.Name(avar)
        ca = '<mi>c.a</mi>'
        self.assertEqual(w.ex(a), ca)
        # Number with unit
        b = myokit.Number('12', 'pF')
        cb = '<mn>12.0</mn>'
        self.assertEqual(w.ex(b), cb)
        # Number without unit
        c = myokit.Number(1)
        cc = '<mn>1.0</mn>'
        self.assertEqual(w.ex(c), cc)

        # Prefix plus
        x = myokit.PrefixPlus(b)
        self.assertEqual(
            w.ex(x), '<mrow><mo>+</mo>' + cb + '</mrow>')
        # Prefix minus
        x = myokit.PrefixMinus(b)
        self.assertEqual(
            w.ex(x), '<mrow><mo>-</mo>' + cb + '</mrow>')

        # Plus
        x = myokit.Plus(a, b)
        self.assertEqual(
            w.ex(x), '<mrow>' + ca + '<mo>+</mo>' + cb + '</mrow>')
        # Minus
        x = myokit.Minus(a, b)
        self.assertEqual(
            w.ex(x), '<mrow>' + ca + '<mo>-</mo>' + cb + '</mrow>')
        # Multiply
        x = myokit.Multiply(a, b)
        self.assertEqual(
            w.ex(x), '<mrow>' + ca + '<mo>*</mo>' + cb + '</mrow>')
        # Divide
        x = myokit.Divide(a, b)
        self.assertEqual(w.ex(x), '<mfrac>' + ca + cb + '</mfrac>')

        # Power
        x = myokit.Power(a, b)
        self.assertEqual(w.ex(x), '<msup>' + ca + cb + '</msup>')
        # Sqrt
        x = myokit.Sqrt(b)
        self.assertEqual(
            w.ex(x), '<mrow><mi>root</mi><mfenced>' + cb + '</mfenced></mrow>')
        # Exp
        x = myokit.Exp(a)
        self.assertEqual(w.ex(x), '<msup><mi>e</mi>' + ca + '</msup>')
        # Log(a)
        x = myokit.Log(b)
        self.assertEqual(
            w.ex(x), '<mrow><mi>ln</mi><mfenced>' + cb + '</mfenced></mrow>')
        # Log(a, b)
        x = myokit.Log(a, b)
        self.assertEqual(
            w.ex(x),
            '<mrow><msub><mi>log</mi>' + cb + '</msub>'
            '<mfenced>' + ca + '</mfenced></mrow>'
        )
        # Log10
        x = myokit.Log10(b)
        self.assertEqual(
            w.ex(x), '<mrow><mi>log</mi><mfenced>' + cb + '</mfenced></mrow>')

        # Sin
        x = myokit.Sin(b)
        self.assertEqual(
            w.ex(x), '<mrow><mi>sin</mi><mfenced>' + cb + '</mfenced></mrow>')
        # Cos
        x = myokit.Cos(b)
        self.assertEqual(
            w.ex(x), '<mrow><mi>cos</mi><mfenced>' + cb + '</mfenced></mrow>')
        # Tan
        x = myokit.Tan(b)
        self.assertEqual(
            w.ex(x), '<mrow><mi>tan</mi><mfenced>' + cb + '</mfenced></mrow>')
        # ASin
        x = myokit.ASin(b)
        self.assertEqual(
            w.ex(x),
            '<mrow><mi>arcsin</mi><mfenced>' + cb + '</mfenced></mrow>')
        # ACos
        x = myokit.ACos(b)
        self.assertEqual(
            w.ex(x),
            '<mrow><mi>arccos</mi><mfenced>' + cb + '</mfenced></mrow>')
        # ATan
        x = myokit.ATan(b)
        self.assertEqual(
            w.ex(x),
            '<mrow><mi>arctan</mi><mfenced>' + cb + '</mfenced></mrow>')

        # Floor
        x = myokit.Floor(b)
        self.assertEqual(
            w.ex(x),
            '<mrow><mi>floor</mi><mfenced>' + cb + '</mfenced></mrow>')
        # Ceil
        x = myokit.Ceil(b)
        self.assertEqual(
            w.ex(x),
            '<mrow><mi>ceiling</mi><mfenced>' + cb + '</mfenced></mrow>')
        # Abs
        x = myokit.Abs(b)
        self.assertEqual(
            w.ex(x), '<mrow><mi>abs</mi><mfenced>' + cb + '</mfenced></mrow>')

        # Quotient
        x = myokit.Quotient(a, b)
        self.assertEqual(
            w.ex(x), '<mrow>' + ca + '<mo>//</mo>' + cb + '</mrow>')
        # Remainder
        x = myokit.Remainder(a, b)
        self.assertEqual(
            w.ex(x), '<mrow>' + ca + '<mo>%</mo>' + cb + '</mrow>')

        # Equal
        x = myokit.Equal(a, b)
        self.assertEqual(
            w.ex(x), '<mrow>' + ca + '<mo>==</mo>' + cb + '</mrow>')
        # NotEqual
        x = myokit.NotEqual(a, b)
        self.assertEqual(
            w.ex(x), '<mrow>' + ca + '<mo>!=</mo>' + cb + '</mrow>')
        # More
        x = myokit.More(a, b)
        self.assertEqual(
            w.ex(x), '<mrow>' + ca + '<mo>&gt;</mo>' + cb + '</mrow>')
        # Less
        x = myokit.Less(a, b)
        self.assertEqual(
            w.ex(x), '<mrow>' + ca + '<mo>&lt;</mo>' + cb + '</mrow>')
        # MoreEqual
        # Named version &ge; is not output, shows decimal code instead
        x = myokit.MoreEqual(a, b)
        self.assertEqual(
            w.ex(x), '<mrow>' + ca + '<mo>&#8805;</mo>' + cb + '</mrow>')
        # LessEqual
        # Named version &le; is not output, shows decimal code instead
        x = myokit.LessEqual(a, b)
        self.assertEqual(
            w.ex(x), '<mrow>' + ca + '<mo>&#8804;</mo>' + cb + '</mrow>')

        # Not
        cond1 = myokit.parse_expression('5 > 3')
        cond2 = myokit.parse_expression('2 < 1')
        c1 = '<mrow><mn>5.0</mn><mo>&gt;</mo><mn>3.0</mn></mrow>'
        c2 = '<mrow><mn>2.0</mn><mo>&lt;</mo><mn>1.0</mn></mrow>'
        x = myokit.Not(cond1)
        self.assertEqual(
            w.ex(x), '<mrow><mo>(</mo><mo>not</mo>' + c1 + '<mo>)</mo></mrow>')
        # And
        x = myokit.And(cond1, cond2)
        self.assertEqual(
            w.ex(x), '<mrow>' + c1 + '<mo>and</mo>' + c2 + '</mrow>')
        # Or
        x = myokit.Or(cond1, cond2)
        self.assertEqual(
            w.ex(x), '<mrow>' + c1 + '<mo>or</mo>' + c2 + '</mrow>')

        # If
        x = myokit.If(cond1, a, b)
        self.assertEqual(
            w.ex(x),
            '<piecewise>'
            '<piece>' + ca + c1 + '</piece>'
            '<otherwise>' + cb + '</otherwise>'
            '</piecewise>'
        )
        # Piecewise
        x = myokit.Piecewise(cond1, a, cond2, b, c)
        self.assertEqual(
            w.ex(x),
            '<piecewise>'
            '<piece>' + ca + c1 + '</piece>'
            '<piece>' + cb + c2 + '</piece>'
            '<otherwise>' + cc + '</otherwise>'
            '</piecewise>'
        )

        # Test fetching using ewriter method
        w = myokit.formats.ewriter('mathml')
        self.assertIsInstance(w, myokit.formats.mathml.MathMLExpressionWriter)

        # Test without a Myokit expression
        self.assertRaisesRegexp(
            ValueError, 'Unknown expression type', w.ex, 7)


if __name__ == '__main__':
    unittest.main()
