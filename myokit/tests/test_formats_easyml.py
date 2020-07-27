#!/usr/bin/env python3
#
# Tests the EasyML module.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import os
import unittest

import myokit
import myokit.formats
import myokit.formats.easyml

from shared import TemporaryDirectory, WarningCollector, DIR_DATA

# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:  # pragma: no python 3 cover
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp

# Strings in Python 2 and 3
try:
    basestring
except NameError:   # pragma: no python 2 cover
    basestring = str


class EasyMLExporterTest(unittest.TestCase):
    """ Tests EasyML export. """

    def test_easyml_exporter(self):
        # Tests exporting a model

        model1 = myokit.load_model('example')
        model2 = myokit.load_model(os.path.join(DIR_DATA, 'heijman-2011.mmt'))
        e = myokit.formats.easyml.EasyMLExporter()

        with TemporaryDirectory() as d:
            path = d.path('easy.model')

            # Test with simple model
            e.model(path, model1)

            # Test with model containing markov models
            with WarningCollector() as c:
                e.model(path, model2)
            self.assertIn('unsupported function: atan', c.text())
            self.assertIn('unsupported function: sin', c.text())
            self.assertEqual(c.count(), 6)

            # Test with extra bound variables
            model1.get('membrane.C').set_binding('hello')
            e.model(path, model1)

            # Test without V being a state variable
            v = model1.get('membrane.V')
            v.demote()
            v.set_rhs(3)
            e.model(path, model1)

            # Test with invalid model
            v.set_rhs('2 * V')
            self.assertRaisesRegex(
                myokit.ExportError, 'valid model', e.model, path, model1)

    def test_export_reused_variable(self):
        # Tests exporting when an `inf` or other special variable is used twice

        # Create model re-using tau and inf
        m = myokit.parse_model(
            """
            [[model]]
            m.V = -80
            c.x = 0.1
            c.y = 0.1

            [m]
            time = 0 bind time
            i_ion = c.I
            dot(V) = -i_ion

            [c]
            inf = 0.5
            tau = 3
            dot(x) = (inf - x) / tau
            dot(y) = (inf - y) / tau
            I = x * y * (m.V - 50)
            """)

        # Export, and read back in
        e = myokit.formats.easyml.EasyMLExporter()
        with TemporaryDirectory() as d:
            path = d.path('easy.model')
            e.model(path, m)
            with open(path, 'r') as f:
                x = f.read()

        self.assertIn('x_inf =', x)
        self.assertIn('y_inf =', x)
        self.assertIn('tau_x =', x)
        self.assertIn('tau_y =', x)

    def test_easyml_exporter_fetching(self):
        # Tests getting an EasyML exporter via the 'exporter' interface

        e = myokit.formats.exporter('easyml')
        self.assertIsInstance(e, myokit.formats.easyml.EasyMLExporter)

    def test_capability_reporting(self):
        # Tests if the correct capabilities are reported
        e = myokit.formats.easyml.EasyMLExporter()
        self.assertTrue(e.supports_model())


class EasyMLExpressionWriterTest(unittest.TestCase):
    """ Tests EasyML expression writer functionality. """

    def test_all(self):
        w = myokit.formats.ewriter('easyml')

        model = myokit.Model()
        component = model.add_component('c')
        avar = component.add_variable('a')

        # Name
        a = myokit.Name(avar)
        self.assertEqual(w.ex(a), 'c.a')
        # Number with unit
        b = myokit.Number('12', 'pF')
        self.assertEqual(w.ex(b), '12.0')
        # Integer
        c = myokit.Number(1)
        self.assertEqual(w.ex(c), '1.0')
        # Integer

        # Prefix plus
        x = myokit.PrefixPlus(b)
        self.assertEqual(w.ex(x), '12.0')
        # Prefix minus
        x = myokit.PrefixMinus(b)
        self.assertEqual(w.ex(x), '(-12.0)')

        # Plus
        x = myokit.Plus(a, b)
        self.assertEqual(w.ex(x), 'c.a + 12.0')
        # Minus
        x = myokit.Minus(a, b)
        self.assertEqual(w.ex(x), 'c.a - 12.0')
        # Multiply
        x = myokit.Multiply(a, b)
        self.assertEqual(w.ex(x), 'c.a * 12.0')
        # Divide
        x = myokit.Divide(a, b)
        self.assertEqual(w.ex(x), 'c.a / 12.0')

        # Quotient
        x = myokit.Quotient(a, b)
        with WarningCollector() as c:
            self.assertEqual(w.ex(x), 'floor(c.a / 12.0)')
        # Remainder
        x = myokit.Remainder(a, b)
        with WarningCollector() as c:
            self.assertEqual(w.ex(x), 'c.a - 12.0 * (floor(c.a / 12.0))')

        # Power
        x = myokit.Power(a, b)
        self.assertEqual(w.ex(x), 'pow(c.a, 12.0)')
        # Sqrt
        x = myokit.Sqrt(b)
        self.assertEqual(w.ex(x), 'sqrt(12.0)')
        # Exp
        x = myokit.Exp(a)
        self.assertEqual(w.ex(x), 'exp(c.a)')
        # Log(a)
        x = myokit.Log(b)
        self.assertEqual(w.ex(x), 'log(12.0)')
        # Log(a, b)
        x = myokit.Log(a, b)
        self.assertEqual(w.ex(x), '(log(c.a) / log(12.0))')
        # Log10
        x = myokit.Log10(b)
        self.assertEqual(w.ex(x), 'log10(12.0)')

        # Sin
        with WarningCollector() as c:
            x = myokit.Sin(b)
            self.assertEqual(w.ex(x), 'sin(12.0)')
            # Cos
            x = myokit.Cos(b)
            self.assertEqual(w.ex(x), 'cos(12.0)')
            # Tan
            x = myokit.Tan(b)
            self.assertEqual(w.ex(x), 'tan(12.0)')
            # ASin
            x = myokit.ASin(b)
            self.assertEqual(w.ex(x), 'asin(12.0)')
            # ACos
            x = myokit.ACos(b)
            self.assertEqual(w.ex(x), 'acos(12.0)')
            # ATan
            x = myokit.ATan(b)
            self.assertEqual(w.ex(x), 'atan(12.0)')

        with WarningCollector() as c:
            # Floor
            x = myokit.Floor(b)
            self.assertEqual(w.ex(x), 'floor(12.0)')
            # Ceil
            x = myokit.Ceil(b)
            self.assertEqual(w.ex(x), 'ceil(12.0)')
            # Abs
            x = myokit.Abs(b)
            self.assertEqual(w.ex(x), 'fabs(12.0)')

        # Equal
        x = myokit.Equal(a, b)
        self.assertEqual(w.ex(x), '(c.a == 12.0)')
        # NotEqual
        x = myokit.NotEqual(a, b)
        self.assertEqual(w.ex(x), '(c.a != 12.0)')
        # More
        x = myokit.More(a, b)
        self.assertEqual(w.ex(x), '(c.a > 12.0)')
        # Less
        x = myokit.Less(a, b)
        self.assertEqual(w.ex(x), '(c.a < 12.0)')
        # MoreEqual
        x = myokit.MoreEqual(a, b)
        self.assertEqual(w.ex(x), '(c.a >= 12.0)')
        # LessEqual
        x = myokit.LessEqual(a, b)
        self.assertEqual(w.ex(x), '(c.a <= 12.0)')

        # Not
        cond1 = myokit.parse_expression('5 > 3')
        cond2 = myokit.parse_expression('2 < 1')
        x = myokit.Not(cond1)
        self.assertEqual(w.ex(x), '!((5.0 > 3.0))')
        # And
        x = myokit.And(cond1, cond2)
        self.assertEqual(w.ex(x), '((5.0 > 3.0) and (2.0 < 1.0))')
        # Or
        x = myokit.Or(cond1, cond2)
        self.assertEqual(w.ex(x), '((5.0 > 3.0) or (2.0 < 1.0))')

        # If
        x = myokit.If(cond1, a, b)
        self.assertEqual(w.ex(x), '((5.0 > 3.0) ? c.a : 12.0)')
        # Piecewise
        c = myokit.Number(1)
        x = myokit.Piecewise(cond1, a, cond2, b, c)
        self.assertEqual(
            w.ex(x),
            '((5.0 > 3.0) ? c.a : ((2.0 < 1.0) ? 12.0 : 1.0))')

        # Test without a Myokit expression
        self.assertRaisesRegex(
            ValueError, 'Unknown expression type', w.ex, 7)

    def test_easyml_ewriter_fetching(self):

        # Test fetching using ewriter method
        w = myokit.formats.ewriter('easyml')
        self.assertIsInstance(w, myokit.formats.easyml.EasyMLExpressionWriter)


if __name__ == '__main__':
    import warnings
    warnings.simplefilter('always')
    unittest.main()
