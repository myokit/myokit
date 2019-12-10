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


class PresentationMathMLTest(unittest.TestCase):
    """
    Tests export of presentation MathML.
    """

    @classmethod
    def setUpClass(cls):
        cls.w = mathml.MathMLExpressionWriter()
        cls.w.set_mode(presentation=True)

        model = myokit.Model()
        component = model.add_component('c')
        cls.avar = component.add_variable('a')

    def test_ewriter(self):
        # Test the presentation MathML expression writer.

        # Name
        a = myokit.Name(self.avar)
        ca = '<mi>c.a</mi>'
        self.assertEqual(self.w.ex(a), ca)
        # Number with unit
        b = myokit.Number('12', 'pF')
        cb = '<mn>12.0</mn>'
        self.assertEqual(self.w.ex(b), cb)
        # Number without unit
        c = myokit.Number(1)
        cc = '<mn>1.0</mn>'
        self.assertEqual(self.w.ex(c), cc)

        # Prefix plus
        x = myokit.PrefixPlus(b)
        self.assertEqual(
            self.w.ex(x), '<mrow><mo>+</mo>' + cb + '</mrow>')
        # Prefix minus
        x = myokit.PrefixMinus(b)
        self.assertEqual(
            self.w.ex(x), '<mrow><mo>-</mo>' + cb + '</mrow>')

        # Plus
        x = myokit.Plus(a, b)
        self.assertEqual(
            self.w.ex(x), '<mrow>' + ca + '<mo>+</mo>' + cb + '</mrow>')
        # Minus
        x = myokit.Minus(a, b)
        self.assertEqual(
            self.w.ex(x), '<mrow>' + ca + '<mo>-</mo>' + cb + '</mrow>')
        # Multiply
        x = myokit.Multiply(a, b)
        self.assertEqual(
            self.w.ex(x), '<mrow>' + ca + '<mo>*</mo>' + cb + '</mrow>')
        # Divide
        x = myokit.Divide(a, b)
        self.assertEqual(self.w.ex(x), '<mfrac>' + ca + cb + '</mfrac>')

        # Power
        x = myokit.Power(a, b)
        self.assertEqual(self.w.ex(x), '<msup>' + ca + cb + '</msup>')
        # Sqrt
        x = myokit.Sqrt(b)
        self.assertEqual(
            self.w.ex(x), '<mrow><mi>root</mi><mfenced>' + cb + '</mfenced></mrow>')
        # Exp
        x = myokit.Exp(a)
        self.assertEqual(self.w.ex(x), '<msup><mi>e</mi>' + ca + '</msup>')
        # Log(a)
        x = myokit.Log(b)
        self.assertEqual(
            self.w.ex(x), '<mrow><mi>ln</mi><mfenced>' + cb + '</mfenced></mrow>')
        # Log(a, b)
        x = myokit.Log(a, b)
        self.assertEqual(
            self.w.ex(x),
            '<mrow><msub><mi>log</mi>' + cb + '</msub>'
            '<mfenced>' + ca + '</mfenced></mrow>'
        )
        # Log10
        x = myokit.Log10(b)
        self.assertEqual(
            self.w.ex(x), '<mrow><mi>log</mi><mfenced>' + cb + '</mfenced></mrow>')

        # Sin
        x = myokit.Sin(b)
        self.assertEqual(
            self.w.ex(x), '<mrow><mi>sin</mi><mfenced>' + cb + '</mfenced></mrow>')
        # Cos
        x = myokit.Cos(b)
        self.assertEqual(
            self.w.ex(x), '<mrow><mi>cos</mi><mfenced>' + cb + '</mfenced></mrow>')
        # Tan
        x = myokit.Tan(b)
        self.assertEqual(
            self.w.ex(x), '<mrow><mi>tan</mi><mfenced>' + cb + '</mfenced></mrow>')
        # ASin
        x = myokit.ASin(b)
        self.assertEqual(
            self.w.ex(x),
            '<mrow><mi>arcsin</mi><mfenced>' + cb + '</mfenced></mrow>')
        # ACos
        x = myokit.ACos(b)
        self.assertEqual(
            self.w.ex(x),
            '<mrow><mi>arccos</mi><mfenced>' + cb + '</mfenced></mrow>')
        # ATan
        x = myokit.ATan(b)
        self.assertEqual(
            self.w.ex(x),
            '<mrow><mi>arctan</mi><mfenced>' + cb + '</mfenced></mrow>')

        # Floor
        x = myokit.Floor(b)
        self.assertEqual(
            self.w.ex(x),
            '<mrow><mi>floor</mi><mfenced>' + cb + '</mfenced></mrow>')
        # Ceil
        x = myokit.Ceil(b)
        self.assertEqual(
            self.w.ex(x),
            '<mrow><mi>ceiling</mi><mfenced>' + cb + '</mfenced></mrow>')
        # Abs
        x = myokit.Abs(b)
        self.assertEqual(
            self.w.ex(x), '<mrow><mi>abs</mi><mfenced>' + cb + '</mfenced></mrow>')

        # Quotient
        x = myokit.Quotient(a, b)
        self.assertEqual(
            self.w.ex(x), '<mrow>' + ca + '<mo>//</mo>' + cb + '</mrow>')
        # Remainder
        x = myokit.Remainder(a, b)
        self.assertEqual(
            self.w.ex(x), '<mrow>' + ca + '<mo>%</mo>' + cb + '</mrow>')

        # Equal
        x = myokit.Equal(a, b)
        self.assertEqual(
            self.w.ex(x), '<mrow>' + ca + '<mo>==</mo>' + cb + '</mrow>')
        # NotEqual
        x = myokit.NotEqual(a, b)
        self.assertEqual(
            self.w.ex(x), '<mrow>' + ca + '<mo>!=</mo>' + cb + '</mrow>')
        # More
        x = myokit.More(a, b)
        self.assertEqual(
            self.w.ex(x), '<mrow>' + ca + '<mo>&gt;</mo>' + cb + '</mrow>')
        # Less
        x = myokit.Less(a, b)
        self.assertEqual(
            self.w.ex(x), '<mrow>' + ca + '<mo>&lt;</mo>' + cb + '</mrow>')
        # MoreEqual
        # Named version &ge; is not output, shows decimal code instead
        x = myokit.MoreEqual(a, b)
        self.assertEqual(
            self.w.ex(x), '<mrow>' + ca + '<mo>&#8805;</mo>' + cb + '</mrow>')
        # LessEqual
        # Named version &le; is not output, shows decimal code instead
        x = myokit.LessEqual(a, b)
        self.assertEqual(
            self.w.ex(x), '<mrow>' + ca + '<mo>&#8804;</mo>' + cb + '</mrow>')

        # Not
        cond1 = myokit.parse_expression('5 > 3')
        cond2 = myokit.parse_expression('2 < 1')
        c1 = '<mrow><mn>5.0</mn><mo>&gt;</mo><mn>3.0</mn></mrow>'
        c2 = '<mrow><mn>2.0</mn><mo>&lt;</mo><mn>1.0</mn></mrow>'
        x = myokit.Not(cond1)
        self.assertEqual(
            self.w.ex(x), '<mrow><mo>(</mo><mo>not</mo>' + c1 + '<mo>)</mo></mrow>')
        # And
        x = myokit.And(cond1, cond2)
        self.assertEqual(
            self.w.ex(x), '<mrow>' + c1 + '<mo>and</mo>' + c2 + '</mrow>')
        # Or
        x = myokit.Or(cond1, cond2)
        self.assertEqual(
            self.w.ex(x), '<mrow>' + c1 + '<mo>or</mo>' + c2 + '</mrow>')

        # If
        x = myokit.If(cond1, a, b)
        self.assertEqual(
            self.w.ex(x),
            '<piecewise>'
            '<piece>' + ca + c1 + '</piece>'
            '<otherwise>' + cb + '</otherwise>'
            '</piecewise>'
        )
        # Piecewise
        x = myokit.Piecewise(cond1, a, cond2, b, c)
        self.assertEqual(
            self.w.ex(x),
            '<piecewise>'
            '<piece>' + ca + c1 + '</piece>'
            '<piece>' + cb + c2 + '</piece>'
            '<otherwise>' + cc + '</otherwise>'
            '</piecewise>'
        )

        # Test fetching using ewriter method
        w = myokit.formats.ewriter('mathml')
        self.assertIsInstance(w, mathml.MathMLExpressionWriter)

        # Test without a Myokit expression
        self.assertRaisesRegex(
            ValueError, 'Unknown expression type', self.w.ex, 7)


if __name__ == '__main__':
    unittest.main()
