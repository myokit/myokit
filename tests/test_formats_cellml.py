#!/usr/bin/env python
#
# Tests the CellML importer
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import os
import unittest

import myokit
import myokit.formats as formats
import myokit.formats.cellml

from shared import TemporaryDirectory, DIR_FORMATS

# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:  # pragma: no cover
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp


class CellMLImporterTest(unittest.TestCase):
    """
    Tests the CellML importer.
    """

    def test_capability_reporting(self):
        """ Tests if the right capabilities are reported. """
        i = formats.importer('cellml')
        self.assertFalse(i.supports_component())
        self.assertTrue(i.supports_model())
        self.assertFalse(i.supports_protocol())

    def test_model_simple(self):
        # Beeler-Reuter is a simple model
        i = formats.importer('cellml')
        self.assertTrue(i.supports_model())
        m = i.model(os.path.join(DIR_FORMATS, 'br-1977.cellml'))
        m.validate()

    def test_model_dot(self):
        # This is beeler-reuter but with a dot() in an expression
        i = formats.importer('cellml')
        self.assertTrue(i.supports_model())
        m = i.model(os.path.join(DIR_FORMATS, 'br-1977-dot.cellml'))
        m.validate()

    def test_model_nesting(self):
        # The corrias model has multiple levels of nesting (encapsulation)
        i = formats.importer('cellml')
        self.assertTrue(i.supports_model())
        m = i.model(os.path.join(DIR_FORMATS, 'corrias.cellml'))
        m.validate()

    def test_info(self):
        i = formats.importer('cellml')
        self.assertIn(type(i.info()), [str, unicode])


class CellMLExpressionWriterTest(unittest.TestCase):
    """
    Tests :class:`myokit.formats.cellml.CellMLExpressionWriter`.
    """

    def test_all(self):
        # CellML requires unit mapping
        units = {
            myokit.parse_unit('pF'): 'picofarad',
        }
        w = myokit.formats.cellml.CellMLExpressionWriter(units)

        model = myokit.Model()
        component = model.add_component('c')
        avar = component.add_variable('a')

        # Requires valid model with unames set
        avar.set_rhs(0)
        avar.set_binding('time')
        model.validate()

        # Name
        a = myokit.Name(avar)
        ca = '<ci>a</ci>'
        self.assertEqual(w.ex(a), ca)
        # Number with unit
        b = myokit.Number('12', 'pF')
        cb = '<cn cellml:units="picofarad">12.0</cn>'
        self.assertEqual(w.ex(b), cb)
        # Number without unit
        c = myokit.Number(1)
        cc = '<cn cellml:units="dimensionless">1.0</cn>'
        self.assertEqual(w.ex(c), cc)

        # Prefix plus
        x = myokit.PrefixPlus(b)
        self.assertEqual(w.ex(x), '<apply><plus />' + cb + '</apply>')
        # Prefix minus
        x = myokit.PrefixMinus(b)
        self.assertEqual(w.ex(x), '<apply><minus />' + cb + '</apply>')

        # Plus
        x = myokit.Plus(a, b)
        self.assertEqual(w.ex(x), '<apply><plus />' + ca + cb + '</apply>')
        # Minus
        x = myokit.Minus(a, b)
        self.assertEqual(w.ex(x), '<apply><minus />' + ca + cb + '</apply>')
        # Multiply
        x = myokit.Multiply(a, b)
        self.assertEqual(w.ex(x), '<apply><times />' + ca + cb + '</apply>')
        # Divide
        x = myokit.Divide(a, b)
        self.assertEqual(w.ex(x), '<apply><divide />' + ca + cb + '</apply>')

        # Power
        x = myokit.Power(a, b)
        self.assertEqual(w.ex(x), '<apply><power />' + ca + cb + '</apply>')
        # Sqrt
        x = myokit.Sqrt(b)
        self.assertEqual(w.ex(x), '<apply><root />' + cb + '</apply>')
        # Exp
        x = myokit.Exp(a)
        self.assertEqual(w.ex(x), '<apply><exp />' + ca + '</apply>')
        # Log(a)
        x = myokit.Log(b)
        self.assertEqual(w.ex(x), '<apply><ln />' + cb + '</apply>')
        # Log(a, b)
        x = myokit.Log(a, b)
        self.assertEqual(
            w.ex(x),
            '<apply><log /><logbase>' + cb + '</logbase>' + ca + '</apply>'
        )
        # Log10
        x = myokit.Log10(b)
        self.assertEqual(w.ex(x), '<apply><log />' + cb + '</apply>')

        # Sin
        x = myokit.Sin(b)
        self.assertEqual(w.ex(x), '<apply><sin />' + cb + '</apply>')
        # Cos
        x = myokit.Cos(b)
        self.assertEqual(w.ex(x), '<apply><cos />' + cb + '</apply>')
        # Tan
        x = myokit.Tan(b)
        self.assertEqual(w.ex(x), '<apply><tan />' + cb + '</apply>')
        # ASin
        x = myokit.ASin(b)
        self.assertEqual(w.ex(x), '<apply><arcsin />' + cb + '</apply>')
        # ACos
        x = myokit.ACos(b)
        self.assertEqual(w.ex(x), '<apply><arccos />' + cb + '</apply>')
        # ATan
        x = myokit.ATan(b)
        self.assertEqual(w.ex(x), '<apply><arctan />' + cb + '</apply>')

        # Floor
        x = myokit.Floor(b)
        self.assertEqual(w.ex(x), '<apply><floor />' + cb + '</apply>')
        # Ceil
        x = myokit.Ceil(b)
        self.assertEqual(w.ex(x), '<apply><ceiling />' + cb + '</apply>')
        # Abs
        x = myokit.Abs(b)
        self.assertEqual(w.ex(x), '<apply><abs />' + cb + '</apply>')

        # Quotient
        # Uses custom implementation: CellML doesn't have these operators.
        x = myokit.Quotient(a, b)
        self.assertEqual(
            w.ex(x),
            '<apply><floor /><apply><divide />' + ca + cb + '</apply></apply>')
        # Remainder
        x = myokit.Remainder(a, b)
        self.assertEqual(
            w.ex(x),
            '<apply><minus />' + ca +
            '<apply><times />' + cb +
            '<apply><floor /><apply><divide />' + ca + cb + '</apply></apply>'
            '</apply>'
            '</apply>'
        )

        # Equal
        x = myokit.Equal(a, b)
        self.assertEqual(w.ex(x), '<apply><eq />' + ca + cb + '</apply>')
        # NotEqual
        x = myokit.NotEqual(a, b)
        self.assertEqual(w.ex(x), '<apply><neq />' + ca + cb + '</apply>')
        # More
        x = myokit.More(a, b)
        self.assertEqual(w.ex(x), '<apply><gt />' + ca + cb + '</apply>')
        # Less
        x = myokit.Less(a, b)
        self.assertEqual(w.ex(x), '<apply><lt />' + ca + cb + '</apply>')
        # MoreEqual
        x = myokit.MoreEqual(a, b)
        self.assertEqual(w.ex(x), '<apply><geq />' + ca + cb + '</apply>')
        # LessEqual
        x = myokit.LessEqual(a, b)
        self.assertEqual(w.ex(x), '<apply><leq />' + ca + cb + '</apply>')

        # Not
        cond1 = myokit.parse_expression('5 > 3')
        cond2 = myokit.parse_expression('2 < 1')
        c1 = ('<apply><gt />'
              '<cn cellml:units="dimensionless">5.0</cn>'
              '<cn cellml:units="dimensionless">3.0</cn>'
              '</apply>')
        c2 = ('<apply><lt />'
              '<cn cellml:units="dimensionless">2.0</cn>'
              '<cn cellml:units="dimensionless">1.0</cn>'
              '</apply>')
        x = myokit.Not(cond1)
        self.assertEqual(w.ex(x), '<apply><not />' + c1 + '</apply>')
        # And
        x = myokit.And(cond1, cond2)
        self.assertEqual(w.ex(x), '<apply><and />' + c1 + c2 + '</apply>')
        # Or
        x = myokit.Or(cond1, cond2)
        self.assertEqual(w.ex(x), '<apply><or />' + c1 + c2 + '</apply>')
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
        w = myokit.formats.ewriter('cellml')
        self.assertIsInstance(w, myokit.formats.cellml.CellMLExpressionWriter)

        # Content mode not allowed
        self.assertRaises(RuntimeError, w.set_mode, True)

        # Lhs function setting not allowed
        self.assertRaises(NotImplementedError, w.set_lhs_function, None)

        # Test without a Myokit expression
        self.assertRaisesRegex(
            ValueError, 'Unknown expression type', w.ex, 7)


class CellMLExporterTest(unittest.TestCase):
    """
    Provides further tests of :class:`myokit.formats.cellml.CellMLExporter`.
    """

    def test_stimulus_generation(self):
        """
        Tests generation of a default stimulus current.
        """
        # Start creating model
        model = myokit.Model()
        engine = model.add_component('engine')
        time = engine.add_variable('time')
        time.set_rhs(0)
        time.set_binding('time')

        # Create exporter and importer
        e = myokit.formats.cellml.CellMLExporter()
        i = myokit.formats.cellml.CellMLImporter()

        # Export --> Should generate warning, missing pace variable
        with TemporaryDirectory() as d:
            path = d.path('model.cellml')
            e.model(path, model)
        self.assertIn('No variable bound to "pace"', e.logger().text())

        # Add pace variable, start testing generation
        pace = engine.add_variable('pace')
        pace.set_rhs(0)
        pace.set_binding('pace')
        with TemporaryDirectory() as d:
            path = d.path('model.cellml')
            e.model(path, model)
            self.assertNotIn('No variable bound to "pace"', e.logger().text())

            # Import model and check added stimulus works
            m2 = i.model(path)
            m2.get('engine.time').set_binding('time')
            self.assertIn('stimulus', m2)
            self.assertEqual(m2.get('stimulus.ctime').eval(), 0)
            self.assertEqual(m2.get('stimulus.duration').eval(), 2)
            self.assertEqual(m2.get('stimulus.offset').eval(), 100)
            self.assertEqual(m2.get('stimulus.period').eval(), 1000)
            self.assertEqual(m2.get('stimulus.pace').eval(), 0)
            m2.get('engine.time').set_rhs(101)
            self.assertEqual(m2.get('stimulus.pace').eval(), 1)
            m2.validate()

        # Test with pace variable in seconds
        time.set_unit('s')
        with TemporaryDirectory() as d:
            path = d.path('model.cellml')
            e.model(path, model)
            self.assertNotIn('No variable bound to "pace"', e.logger().text())

            # Import model and check added stimulus works
            m2 = i.model(path)
            m2.get('engine.time').set_binding('time')
            self.assertIn('stimulus', m2)
            self.assertEqual(m2.get('stimulus.ctime').eval(), 0)
            self.assertEqual(m2.get('stimulus.duration').eval(), 0.002)
            self.assertEqual(m2.get('stimulus.offset').eval(), 0.1)
            self.assertEqual(m2.get('stimulus.period').eval(), 1)
            self.assertEqual(m2.get('stimulus.pace').eval(), 0)
            m2.get('engine.time').set_rhs(0.101)
            self.assertEqual(m2.get('stimulus.pace').eval(), 1)
            m2.validate()

        # Test pace variable's children are removed
        pace.add_variable('hello')
        self.assertEqual(len(pace), 1)
        with TemporaryDirectory() as d:
            path = d.path('model.cellml')
            e.model(path, model)
            self.assertNotIn('No variable bound to "pace"', e.logger().text())

            # Import model and check added stimulus works
            m2 = i.model(path)
            m2.get('engine.time').set_binding('time')
            self.assertIn('stimulus', m2)
            self.assertEqual(m2.get('stimulus.ctime').eval(), 0)
            self.assertEqual(m2.get('stimulus.duration').eval(), 0.002)
            self.assertEqual(m2.get('stimulus.offset').eval(), 0.1)
            self.assertEqual(m2.get('stimulus.period').eval(), 1)
            self.assertEqual(m2.get('stimulus.pace').eval(), 0)
            m2.get('engine.time').set_rhs(0.101)
            self.assertEqual(m2.get('stimulus.pace').eval(), 1)
            m2.validate()

            # Check child variables are gone (and pace lives in stimulus now)
            self.assertEqual(len(m2.get('stimulus.pace')), 0)


if __name__ == '__main__':
    unittest.main()
