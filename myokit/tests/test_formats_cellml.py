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
import re
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
    Tests for :class:`myokit.formats.cellml.CellMLExporter`.
    """

    def test_capability_reporting(self):
        # Test if the right capabilities are reported.
        e = formats.exporter('cellml')
        self.assertTrue(e.supports_model())
        self.assertFalse(e.supports_runnable())

    def test_info(self):
        # Test if the exporter implements info()
        e = formats.exporter('cellml')
        self.assertIsInstance(e.info(), basestring)

    def test_stimulus_generation(self):
        # Tests if protocols allow a stimulus current to be added

        e = formats.exporter('cellml')
        i = formats.importer('cellml')

        # Load input model
        m1, p1, _ = myokit.load('example')
        org_code = m1.code()

        # 1. Export without a protocol
        with TemporaryDirectory() as d:
            path = d.path('model.cellml')
            e.model(path, m1)
            m2 = i.model(path)
        self.assertFalse(e.logger().has_warnings())
        self.assertFalse(
            isinstance(m2.get('engine.pace').rhs(), myokit.Piecewise))

        # 2. Export with protocol, but without variable bound to pacing
        m1.get('engine.pace').set_binding(None)
        with TemporaryDirectory() as d:
            path = d.path('model.cellml')
            e.model(path, m1, p1)
            m2 = i.model(path)
        self.assertTrue(e.logger().has_warnings())
        self.assertFalse(
            isinstance(m2.get('engine.pace').rhs(), myokit.Piecewise))

        # 3. Export with protocol and variable bound to pacing
        m1.get('engine.pace').set_binding('pace')
        with TemporaryDirectory() as d:
            path = d.path('model.cellml')
            e.model(path, m1, p1)
            m2 = i.model(path)
        self.assertFalse(e.logger().has_warnings())
        self.assertTrue(
            isinstance(m2.get('engine.pace').rhs(), myokit.Piecewise))

        # Check original model is unchanged
        self.assertEqual(org_code, m1.code())

    def test_version_selection(self):
        # Test choosing between CellML versions

        e = formats.exporter('cellml')
        model = myokit.Model('hello')

        # Write to 1.0 model
        with TemporaryDirectory() as d:
            path = d.path('test.cellml')
            e.model(path, model, version='1.0')
            with open(path, 'r') as f:
                self.assertIn('cellml/1.0#', f.read())

        # Write to 1.1 model
        with TemporaryDirectory() as d:
            path = d.path('test.cellml')
            e.model(path, model, version='1.1')
            with open(path, 'r') as f:
                self.assertIn('cellml/1.1#', f.read())

    '''

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
    '''


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
        cls._math = re.compile(r'^<math [^>]+>(.*)</math>$', re.S)

    def assertWrite(self, expression, xml):
        """ Assert writing an ``expression`` results in the given ``xml``. """
        x = self.w.ex(expression)
        m = self._math.match(x)
        self.assertTrue(m)
        self.assertEqual(m.group(1), xml)

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
        # Test if the importer implements info()
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
