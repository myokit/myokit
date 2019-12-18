#!/usr/bin/env python3
#
# Tests the CellML importer and exporter.
# More testing of CellML if performed in test_cellml_api.py
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import os
import unittest

import myokit
import myokit.formats as formats
import myokit.formats.cellml

from myokit.formats.cellml import CellMLImporterError

from shared import TemporaryDirectory, DIR_FORMATS

# CellML dir
DIR = os.path.join(DIR_FORMATS, 'cellml')

# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp

# Strings in Python 2 and 3
try:
    basestring
except NameError:   # pragma: no python 2 cover
    basestring = str


class CellMLExporterTest(unittest.TestCase):
    """
    Provides further tests of :class:`myokit.formats.cellml.CellMLExporter`.
    """

    def test_stimulus_generation(self):
        # Test generation of a default stimulus current.

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

        # Test name is adapted if stimulus is already a component
        model.add_component('stimulus')
        model.add_component('stimulus_2')
        with TemporaryDirectory() as d:
            path = d.path('model.cellml')
            e.model(path, model)

            # Import model and check added stimulus works
            m2 = i.model(path)
            self.assertIn('stimulus_3', m2)
            self.assertEqual(m2.get('stimulus_3.ctime').eval(), 0)

    def test_unit_export(self):
        # Test exporting units.

        # Start creating model
        model = myokit.Model()
        engine = model.add_component('engine')
        time = engine.add_variable('time')
        time.set_rhs(0)
        time.set_binding('time')
        three = engine.add_variable('three')
        three.set_rhs(3)

        mad_unit = myokit.Unit()
        mad_unit *= 1.234
        mad_unit *= myokit.units.m
        mad_unit/= myokit.units.s
        mad_unit *= myokit.units.A
        time.set_unit(mad_unit)

        pure_multiplier = myokit.Unit()
        pure_multiplier *= 1000
        three.set_unit(pure_multiplier)

        # Create exporter and importer
        e = myokit.formats.cellml.CellMLExporter()
        i = myokit.formats.cellml.CellMLImporter()

        # Export
        with TemporaryDirectory() as d:
            path = d.path('model.cellml')
            e.model(path, model)

            # Import model and check units
            m2 = i.model(path)
            self.assertEqual(m2.get('engine.three').eval(), 3)
            self.assertEqual(m2.get('engine.three').unit(), pure_multiplier)
            self.assertEqual(m2.get('engine.time').unit(), mad_unit)

    def test_component_name_clashes(self):
        # Test if name clashes in components (due to nested variables parents
        # becoming components) are resolved.

        # Start creating model
        model = myokit.Model()
        engine = model.add_component('x')
        time = engine.add_variable('time')
        time.set_rhs(0)
        time.set_binding('time')
        y = engine.add_variable('y')
        y.set_rhs(1)
        yc = y.add_variable('yc')
        yc.set_rhs(2)

        comp = model.add_component('x_y')
        z = comp.add_variable('z')
        z.set_rhs(2)

        # The model now has a component `x_y` and a variable `x.y` that will be
        # converted to a component `x_y`

        # Create exporter and importer
        e = myokit.formats.cellml.CellMLExporter()
        i = myokit.formats.cellml.CellMLImporter()

        # Export
        with TemporaryDirectory() as d:
            path = d.path('model.cellml')
            e.model(path, model)

            # Import model and check presence of renamed component
            m2 = i.model(path)
            self.assertIn('x_y', m2)
            self.assertIn('x_y_2', m2)

    def test_nested_variables(self):
        # Test export of deep nesting structures.

        # Start creating model
        model = myokit.Model()
        engine = model.add_component('x')
        time = engine.add_variable('time')
        time.set_rhs(0)
        time.set_binding('time')

        def add(parent, name, rhs=0):
            var = parent.add_variable(name)
            var.set_rhs(rhs)
            return var

        p1 = add(engine, 'p1', 1)
        p2 = add(p1, 'p2', 2)
        p3 = add(p2, 'p3', 3)
        p4 = add(p3, 'p4', 4)
        p5 = add(p4, 'p5', 5)
        add(p5, 'p6', 6)

        # Create exporter and importer
        e = myokit.formats.cellml.CellMLExporter()
        i = myokit.formats.cellml.CellMLImporter()

        # Export
        with TemporaryDirectory() as d:
            path = d.path('model.cellml')
            e.model(path, model)

            # Import model and check presence of renamed component
            m2 = i.model(path)
            self.assertIn('x', m2)
            self.assertIn('x_p1', m2)
            self.assertIn('x_p1_p2', m2)
            self.assertIn('x_p1_p2_p3', m2)
            self.assertIn('x_p1_p2_p3_p4', m2)
            self.assertIn('x_p1_p2_p3_p4_p5', m2)
            self.assertNotIn('x_p1_p2_p3_p4_p5_p6', m2)

    def test_component_ordering(self):

        # Create quick model without any nested variables
        m = myokit.Model()
        m.meta['name'] = 'Hello'

        c = m.add_component('C')
        x = c.add_variable('x')
        x.set_rhs('5 [ms]')
        x.set_unit('ms')
        x.set_binding('time')

        a = m.add_component('A')
        x = a.add_variable('x')
        x.set_rhs('2 [ms]')
        x.set_unit('ms')

        d = m.add_component('D')
        x = d.add_variable('x')
        x.set_rhs('1 [ms]')
        x.set_unit('ms')

        b = m.add_component('B')
        x = b.add_variable('x')
        x.set_rhs('3 [ms]')
        x.set_unit('ms')

        e = myokit.formats.cellml.CellMLExporter()
        with TemporaryDirectory() as d:
            path = d.path('model.cellml')
            e.model(path, m)

            comps = []
            with open(path, 'r') as f:
                for line in f.readlines():
                    line = line.strip()
                    if line.startswith('<component name="'):
                        comps.append(line[17:-2])
            sorted_comps = list(comps)
            sorted_comps.sort()
            self.assertTrue(comps == sorted_comps)

    def test_oxmeta_annotation_export(self):
        # Text export of weblab oxmeta annotation

        # Create a test model
        m = myokit.Model()
        m.meta['name'] = 'Hello'

        cc = m.add_component('C')
        t = cc.add_variable('time')
        t.set_rhs('0 [ms]')
        t.set_unit('ms')
        t.set_binding('time')

        ca = m.add_component('A')
        x = ca.add_variable('INa')
        x.set_rhs('2 [ms]')
        x.set_unit('ms')

        cd = m.add_component('D')
        y = cd.add_variable('y')
        y.set_rhs('1 [ms]')
        y.set_unit('ms')

        cb = m.add_component('B')
        z = cb.add_variable('z')
        z.set_rhs('3 [ms]')
        z.set_unit('ms')

        # No oxmeta annotations: No cmeta namespace or RDF annotations
        exporter = myokit.formats.cellml.CellMLExporter()
        importer = myokit.formats.cellml.CellMLImporter()
        with TemporaryDirectory() as d:
            path = d.path('model.cellml')
            exporter.model(path, m)
            with open(path, 'r') as f:
                xml = f.read()
            self.assertTrue('xmlns:cmeta' not in xml)
            self.assertTrue('cmeta:id' not in xml)
            self.assertTrue('<rdf' not in xml)

        # Add oxmeta annotations
        t.meta['oxmeta'] = 'time'
        x.meta['oxmeta'] = 'membrane_fast_sodium_current'
        with TemporaryDirectory() as d:
            path = d.path('model.cellml')
            exporter.model(path, m)
            time_found = ina_found = False
            with open(path, 'r') as f:
                lines = f.readlines()
                for i, line in enumerate(lines):
                    if 'rdf:about="#time"' in line:
                        time_found = True
                        self.assertIn('oxford-metadata#time', lines[i + 1])

                    if 'rdf:about="#INa"' in line:
                        ina_found = True
                        self.assertIn(
                            'oxford-metadata#membrane_fast_sodium_current',
                            lines[i + 1])

                self.assertTrue(time_found)
                self.assertTrue(ina_found)

            # Re-import, check if model can still be read
            m2 = importer.model(path)

    def test_weird_custom_units(self):
        # Test export of units with large/small multipliers

        # Create a test model
        m = myokit.Model()
        m.meta['name'] = 'Hello'

        cc = m.add_component('C')
        t = cc.add_variable('time')
        t.set_rhs('0 [ms]')
        t.set_unit('ms')
        t.set_binding('time')

        ca = m.add_component('A')
        x = ca.add_variable('INa')
        x.set_rhs('2 [N (1e+12)]')
        x.set_unit('N (1e+12)')

        cd = m.add_component('D')
        y = cd.add_variable('y')
        y.set_rhs('1 [s (1e-13)]')
        y.set_unit('s (1e-13)')

        cb = m.add_component('B')
        z = cb.add_variable('z')
        z.set_rhs('3 [1 (1e+06)]')
        z.set_unit('1 (1e+06)')

        # Export and read back in again
        exporter = myokit.formats.cellml.CellMLExporter()
        importer = myokit.formats.cellml.CellMLImporter()
        with TemporaryDirectory() as d:
            path = d.path('model.cellml')
            exporter.model(path, m)
            with open(path, 'r') as f:
                xml = f.read()
            m2 = importer.model(path)


class CellMLExpressionWriterTest(unittest.TestCase):
    """
    Tests :class:`myokit.formats.cellml.CellMLExpressionWriter`.
    """

    @classmethod
    def setUpClass(cls):
        # CellML requires unit mapping
        units = {
            myokit.parse_unit('pF'): 'picofarad',
        }
        cls.w = myokit.formats.cellml.CellMLExpressionWriter()
        cls.w.set_unit_function(lambda x: units[x])

        model = myokit.Model()
        component = model.add_component('c')
        cls.avar = component.add_variable('a')

        # Requires valid model with unames set
        cls.avar.set_rhs(0)
        cls.avar.set_binding('time')
        model.validate()

        # MathML opening and closing tags
        cls.m1 = ('<math xmlns:cellml="http://www.cellml.org/cellml/1.0#"'
                  ' xmlns="http://www.w3.org/1998/Math/MathML">')
        cls.m2 = ('</math>')

    def assertWrite(self, expression, xml):
        """ Assert writing an ``expression`` results in the given ``xml``. """
        x = self.w.ex(expression)
        self.assertTrue(x.startswith(self.m1))
        x = x[len(self.m1):]
        self.assertTrue(x.endswith(self.m2))
        x = x[:-len(self.m2)]
        self.assertEqual(x, xml)

    def test_creation(self):
        # Tests creating a CellMLExpressionWriter

        # Test fetching using ewriter method
        w = myokit.formats.ewriter('cellml')
        self.assertIsInstance(w, myokit.formats.cellml.CellMLExpressionWriter)

        # Content mode not allowed
        self.assertRaises(RuntimeError, w.set_mode, True)

    def test_name_and_number(self):
        # Tests writing names and numbers

        # Name
        a = myokit.Name(self.avar)
        ca = '<ci>a</ci>'
        self.assertWrite(a, ca)

        # Number with unit
        b = myokit.Number('12', 'pF')
        cb = ('<cn cellml:units="picofarad">12.0</cn>')
        self.assertWrite(b, cb)

        # Number without unit
        c = myokit.Number(1)
        cc = ('<cn cellml:units="dimensionless">1.0</cn>')
        self.assertWrite(c, cc)

    def test_arithmetic(self):
        # Test basic arithmetic

        a = myokit.Name(self.avar)
        b = myokit.Number('12', 'pF')
        ca = '<ci>a</ci>'
        cb = ('<cn cellml:units="picofarad">12.0</cn>')

        # Prefix plus
        x = myokit.PrefixPlus(b)
        self.assertWrite(x, '<apply><plus/>' + cb + '</apply>')
        # Prefix minus
        x = myokit.PrefixMinus(b)
        self.assertWrite(x, '<apply><minus/>' + cb + '</apply>')

        # Plus
        x = myokit.Plus(a, b)
        self.assertWrite(x, '<apply><plus/>' + ca + cb + '</apply>')
        # Minus
        x = myokit.Minus(a, b)
        self.assertWrite(x, '<apply><minus/>' + ca + cb + '</apply>')
        # Multiply
        x = myokit.Multiply(a, b)
        self.assertWrite(x, '<apply><times/>' + ca + cb + '</apply>')
        # Divide
        x = myokit.Divide(a, b)
        self.assertWrite(x, '<apply><divide/>' + ca + cb + '</apply>')

    def test_functions(self):
        # Test printing functions

        a = myokit.Name(self.avar)
        b = myokit.Number('12', 'pF')
        ca = '<ci>a</ci>'
        cb = ('<cn cellml:units="picofarad">12.0</cn>')

        # Power
        x = myokit.Power(a, b)
        self.assertWrite(x, '<apply><power/>' + ca + cb + '</apply>')
        # Sqrt
        x = myokit.Sqrt(b)
        self.assertWrite(x, '<apply><root/>' + cb + '</apply>')
        # Exp
        x = myokit.Exp(a)
        self.assertWrite(x, '<apply><exp/>' + ca + '</apply>')

        # Floor
        x = myokit.Floor(b)
        self.assertWrite(x, '<apply><floor/>' + cb + '</apply>')
        # Ceil
        x = myokit.Ceil(b)
        self.assertWrite(x, '<apply><ceiling/>' + cb + '</apply>')
        # Abs
        x = myokit.Abs(b)
        self.assertWrite(x, '<apply><abs/>' + cb + '</apply>')

    def test_inequalities(self):
        # Tests printing inequalities

        a = myokit.Name(self.avar)
        b = myokit.Number('12', 'pF')
        ca = '<ci>a</ci>'
        cb = ('<cn cellml:units="picofarad">12.0</cn>')

        # Equal
        x = myokit.Equal(a, b)
        self.assertWrite(x, '<apply><eq/>' + ca + cb + '</apply>')
        # NotEqual
        x = myokit.NotEqual(a, b)
        self.assertWrite(x, '<apply><neq/>' + ca + cb + '</apply>')
        # More
        x = myokit.More(a, b)
        self.assertWrite(x, '<apply><gt/>' + ca + cb + '</apply>')
        # Less
        x = myokit.Less(a, b)
        self.assertWrite(x, '<apply><lt/>' + ca + cb + '</apply>')
        # MoreEqual
        x = myokit.MoreEqual(a, b)
        self.assertWrite(x, '<apply><geq/>' + ca + cb + '</apply>')
        # LessEqual
        x = myokit.LessEqual(a, b)
        self.assertWrite(x, '<apply><leq/>' + ca + cb + '</apply>')

    def test_log(self):
        # Tests printing the log function

        a = myokit.Name(self.avar)
        b = myokit.Number('12', 'pF')
        ca = '<ci>a</ci>'
        cb = ('<cn cellml:units="picofarad">12.0</cn>')

        # Log(a)
        x = myokit.Log(b)
        self.assertWrite(x, '<apply><ln/>' + cb + '</apply>')
        # Log(a, b)
        x = myokit.Log(a, b)
        self.assertWrite(
            x, '<apply><log/><logbase>' + cb + '</logbase>' + ca + '</apply>')
        # Log10
        x = myokit.Log10(b)
        self.assertWrite(x, '<apply><log/>' + cb + '</apply>')

    def test_logical(self):
        # Tests printing logical operators and functions

        a = myokit.Name(self.avar)
        b = myokit.Number('12', 'pF')
        c = myokit.Number(1)
        ca = '<ci>a</ci>'
        cb = ('<cn cellml:units="picofarad">12.0</cn>')
        cc = ('<cn cellml:units="dimensionless">1.0</cn>')

        # Not
        cond1 = myokit.parse_expression('5 > 3')
        cond2 = myokit.parse_expression('2 < 1')
        c1 = ('<apply><gt/>'
              '<cn cellml:units="dimensionless">5.0</cn>'
              '<cn cellml:units="dimensionless">3.0</cn>'
              '</apply>')
        c2 = ('<apply><lt/>'
              '<cn cellml:units="dimensionless">2.0</cn>'
              '<cn cellml:units="dimensionless">1.0</cn>'
              '</apply>')
        x = myokit.Not(cond1)
        self.assertWrite(x, '<apply><not/>' + c1 + '</apply>')
        # And
        x = myokit.And(cond1, cond2)
        self.assertWrite(x, '<apply><and/>' + c1 + c2 + '</apply>')
        # Or
        x = myokit.Or(cond1, cond2)
        self.assertWrite(x, '<apply><or/>' + c1 + c2 + '</apply>')
        # If
        x = myokit.If(cond1, a, b)
        self.assertWrite(
            x,
            '<piecewise>'
            '<piece>' + ca + c1 + '</piece>'
            '<otherwise>' + cb + '</otherwise>'
            '</piecewise>'
        )
        # Piecewise
        x = myokit.Piecewise(cond1, a, cond2, b, c)
        self.assertWrite(
            x,
            '<piecewise>'
            '<piece>' + ca + c1 + '</piece>'
            '<piece>' + cb + c2 + '</piece>'
            '<otherwise>' + cc + '</otherwise>'
            '</piecewise>'
        )

    def test_trig_basic(self):
        # Tests printing basic trig

        b = myokit.Number('12', 'pF')
        cb = ('<cn cellml:units="picofarad">12.0</cn>')

        # Sin
        x = myokit.Sin(b)
        self.assertWrite(x, '<apply><sin/>' + cb + '</apply>')
        # Cos
        x = myokit.Cos(b)
        self.assertWrite(x, '<apply><cos/>' + cb + '</apply>')
        # Tan
        x = myokit.Tan(b)
        self.assertWrite(x, '<apply><tan/>' + cb + '</apply>')
        # ASin
        x = myokit.ASin(b)
        self.assertWrite(x, '<apply><arcsin/>' + cb + '</apply>')
        # ACos
        x = myokit.ACos(b)
        self.assertWrite(x, '<apply><arccos/>' + cb + '</apply>')
        # ATan
        x = myokit.ATan(b)
        self.assertWrite(x, '<apply><arctan/>' + cb + '</apply>')

    def test_quotient_remainder(self):
        # Tests printing quotient and remainder

        a = myokit.Name(self.avar)
        b = myokit.Number('12', 'pF')
        ca = '<ci>a</ci>'
        cb = ('<cn cellml:units="picofarad">12.0</cn>')

        # Quotient
        # Uses custom implementation: CellML doesn't have these operators.
        x = myokit.Quotient(a, b)
        self.assertWrite(
            x,
            '<apply><floor/><apply><divide/>' + ca + cb + '</apply></apply>')

        # Remainder
        x = myokit.Remainder(a, b)
        self.assertWrite(
            x,
            '<apply><minus/>' + ca +
            '<apply><times/>' + cb +
            '<apply><floor/><apply><divide/>' + ca + cb + '</apply></apply>'
            '</apply>'
            '</apply>'
        )

    def test_unknown_expression(self):
        # Test without a Myokit expression

        self.assertRaisesRegex(
            ValueError, 'Unknown expression type', self.w.ex, 7)


class CellMLImporterTest(unittest.TestCase):
    """
    Tests the CellML importer.
    """

    def test_capability_reporting(self):
        # Test if the right capabilities are reported.
        i = formats.importer('cellml')
        self.assertFalse(i.supports_component())
        self.assertTrue(i.supports_model())
        self.assertFalse(i.supports_protocol())

    def test_info(self):
        # Test if the reporter implements info()
        i = formats.importer('cellml')
        self.assertIsInstance(i.info(), basestring)

    def test_model_dot(self):
        # This is beeler-reuter but with a dot() in an expression
        i = formats.importer('cellml')
        m = i.model(os.path.join(DIR, 'br-1977-dot.cellml'))
        m.validate()

    def test_model_errors(self):
        # Files with errors raise CellMLImporterErrors (not parser errors)
        i = formats.importer('cellml')
        m = os.path.join(DIR, 'invalid-file.cellml')
        self.assertRaisesRegex(
            CellMLImporterError, 'valid CellML identifier', i.model, m)

    def test_model_nesting(self):
        # The corrias model has multiple levels of nesting (encapsulation)
        i = formats.importer('cellml')
        m = i.model(os.path.join(DIR, 'corrias.cellml'))
        m.validate()

    def test_model_simple(self):
        # Beeler-Reuter is a simple model
        i = formats.importer('cellml')
        m = i.model(os.path.join(DIR, 'br-1977.cellml'))
        m.validate()

    def test_not_a_model(self):
        # Test loading something other than a CellML file

        # Different XML file
        i = formats.importer('cellml')
        self.assertRaisesRegex(
            CellMLImporterError, 'not a CellML document',
            i.model, os.path.join(DIR_FORMATS, 'sbml', 'HodgkinHuxley.xml'))

        # Not an XML file
        self.assertRaisesRegex(
            CellMLImporterError, 'Unable to parse XML',
            i.model, os.path.join(DIR_FORMATS, 'lr-1991.mmt'))

    def test_warnings(self):
        # Tests warnings are logged

        # Create model that will generate warnings
        x = ('<?xml version="1.0" encoding="UTF-8"?>'
             '<model name="test" xmlns="http://www.cellml.org/cellml/1.0#">'
             '<component name="a">'
             '  <variable name="hello" units="ampere"'
             '            public_interface="in"/>'
             '</component>'
             '</model>')

        # Write to disk and import
        with TemporaryDirectory() as d:
            path = d.path('test.celllml')
            with open(path, 'w') as f:
                f.write(x)

            # Import
            i = formats.importer('cellml')
            i.model(path)

            # Check warning was raised
            self.assertIn('not connected', next(i.logger().warnings()))


if __name__ == '__main__':
    unittest.main()
