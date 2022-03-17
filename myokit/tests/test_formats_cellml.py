#!/usr/bin/env python3
#
# Tests the CellML importer, exporter, and expression writer.
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
import myokit.formats.cellml as cellml

from myokit.formats.cellml import CellMLImporterError

from myokit.tests import TemporaryDirectory, DIR_FORMATS, WarningCollector

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
            with WarningCollector() as w:
                e.model(path, m1)
            m2 = i.model(path)
        self.assertFalse(w.has_warnings())
        self.assertTrue(isinstance(m2.get('engine.pace').rhs(), myokit.Number))

        # 2. Export with protocol, but without variable bound to pacing
        m1.get('engine.pace').set_binding(None)
        with TemporaryDirectory() as d:
            path = d.path('model.cellml')
            with WarningCollector() as w:
                e.model(path, m1, p1)
            m2 = i.model(path)
        self.assertTrue(w.has_warnings())
        self.assertTrue(isinstance(m2.get('engine.pace').rhs(), myokit.Number))

        # 3. Export with protocol and variable bound to pacing
        m1.get('engine.pace').set_binding('pace')
        with TemporaryDirectory() as d:
            path = d.path('model.cellml')
            with WarningCollector() as w:
                e.model(path, m1, p1)
            m2 = i.model(path)
        self.assertFalse(w.has_warnings())
        rhs = m2.get('membrane.i_stim').rhs()
        self.assertTrue(rhs, myokit.Multiply)
        self.assertTrue(isinstance(rhs[0], myokit.Piecewise))

        # Check original model is unchanged
        self.assertEqual(org_code, m1.code())

    def test_version_selection(self):
        # Test choosing between CellML versions

        e = formats.exporter('cellml')
        model = myokit.Model('hello')
        t = model.add_component('env').add_variable('time')
        t.set_binding('time')
        t.set_rhs(0)

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

        # Write to 2.0 model
        with TemporaryDirectory() as d:
            path = d.path('test.cellml')
            e.model(path, model, version='2.0')
            with open(path, 'r') as f:
                self.assertIn('cellml/2.0#', f.read())

    def test_version_specific_exporters(self):
        # Test the aliased exporters for specific versions

        model = myokit.Model('hello')
        t = model.add_component('env').add_variable('time')
        t.set_binding('time')
        t.set_rhs(0)

        # Write to 1.0 model
        e = formats.exporter('cellml1')
        with TemporaryDirectory() as d:
            path = d.path('test.cellml')
            e.model(path, model)
            with open(path, 'r') as f:
                self.assertIn('cellml/1.0#', f.read())

        # Write to 2.0 model
        e = formats.exporter('cellml2')
        with TemporaryDirectory() as d:
            path = d.path('test.cellml')
            e.model(path, model)
            with open(path, 'r') as f:
                self.assertIn('cellml/2.0#', f.read())


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
        cls.w = cellml.CellMLExpressionWriter()
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
        self.assertIsInstance(w, cellml.CellMLExpressionWriter)

        # Content mode not allowed
        self.assertRaises(RuntimeError, w.set_mode, True)

    def test_name_and_number(self):
        # Tests writing names and numbers

        # Name
        self.assertWrite(myokit.Name(self.avar), '<ci>a</ci>')

        # Number with unit
        self.assertWrite(
            myokit.Number(-12, 'pF'),
            '<cn cellml:units="picofarad">-12.0</cn>')

        # Number without unit
        self.assertWrite(
            myokit.Number(1), '<cn cellml:units="dimensionless">1.0</cn>')
        self.assertWrite(
            myokit.Number(0), '<cn cellml:units="dimensionless">0.0</cn>')

        # Number with e notation (note that Python will turn e.g. 1e3 into
        # 1000, so must pick tests carefully)
        self.assertWrite(
            myokit.Number(1e3), '<cn cellml:units="dimensionless">1000.0</cn>')
        self.assertWrite(
            myokit.Number(1e-3), '<cn cellml:units="dimensionless">0.001</cn>')

        def write_cn(expression):
            # Write cn and return the code
            x = self.w.ex(expression)
            m = self._math.match(x)
            self.assertTrue(m)
            return m.group(1)

        cn = write_cn(myokit.Number(1e-6))
        a, b = 'type="e-notation"', 'cellml:units="dimensionless"'
        c1 = '<cn ' + a + ' ' + b + '>1<sep/>-6</cn>'
        c2 = '<cn ' + b + ' ' + a + '>1<sep/>-6</cn>'
        self.assertIn(cn, (c1, c2))

        cn = write_cn(myokit.Number(2.1e24))
        c1 = '<cn ' + a + ' ' + b + '>2.1<sep/>24</cn>'
        c2 = '<cn ' + b + ' ' + a + '>2.1<sep/>24</cn>'
        self.assertIn(cn, (c1, c2))

        # myokit.float.str(1.23456789) = 1.23456788999999989e+00
        self.assertWrite(
            myokit.Number(1.23456789),
            '<cn cellml:units="dimensionless">1.23456788999999989</cn>')

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

    def test_versions(self):
        # Tests writing different CellML versions

        # CellML 1.0
        units = {
            myokit.parse_unit('pF'): 'picofarad',
        }
        w = cellml.CellMLExpressionWriter('1.0')
        w.set_unit_function(lambda x: units[x])
        xml = w.ex(myokit.Number(1, myokit.units.pF))
        self.assertIn(cellml.NS_CELLML_1_0, xml)

        # CellML 1.1
        w = cellml.CellMLExpressionWriter('1.1')
        w.set_unit_function(lambda x: units[x])
        xml = w.ex(myokit.Number(1, myokit.units.pF))
        self.assertIn(cellml.NS_CELLML_1_1, xml)

        # CellML 1.2
        self.assertRaisesRegex(
            ValueError, 'Unknown CellML version',
            cellml.CellMLExpressionWriter, '1.2')

        # CellML 2.0
        w = cellml.CellMLExpressionWriter('2.0')
        w.set_unit_function(lambda x: units[x])
        xml = w.ex(myokit.Number(1, myokit.units.pF))
        self.assertIn(cellml.NS_CELLML_2_0, xml)


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

    def test_model_1_0_dot(self):
        # This is beeler-reuter but with a dot() in an expression
        i = formats.importer('cellml')
        m = i.model(os.path.join(DIR, 'br-1977-dot.cellml'))
        m.validate()

    def test_model_1_0_errors(self):
        # Files with errors raise CellMLImporterErrors (not parser errors)
        i = formats.importer('cellml')
        m = os.path.join(DIR, 'invalid-file.cellml')
        self.assertRaisesRegex(
            CellMLImporterError, 'valid CellML identifier', i.model, m)

    def test_model__1_0_nesting(self):
        # The corrias model has multiple levels of nesting (encapsulation)
        i = formats.importer('cellml')
        m = i.model(os.path.join(DIR, 'corrias.cellml'))
        m.validate()

    def test_model_1_0_simple(self):
        # Beeler-Reuter is a simple model
        i = formats.importer('cellml')
        m = i.model(os.path.join(DIR, 'br-1977.cellml'))
        m.validate()

    def test_model_2_0(self):
        # Decker 2009 in CellML 2.0
        i = formats.importer('cellml')
        m = i.model(os.path.join(DIR, 'decker-2009.cellml'))
        m.validate()

    def test_model_2_0_errors(self):
        # CellML 2.0 files with errors should raise CellMLImporterErrors

        # Create model that will generate warnings
        x = ('<?xml version="1.0" encoding="UTF-8"?>'
             '<model name="test" xmlns="http://www.cellml.org/cellml/2.0#">'
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
            self.assertRaisesRegex(
                CellMLImporterError, 'Unexpected attribute',
                i.model, path)

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

    def test_warnings_1_0(self):
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
            with WarningCollector() as w:
                i.model(path)

            # Check warning was raised
            self.assertIn('not connected', w.text())


if __name__ == '__main__':
    import warnings
    warnings.simplefilter('always')
    unittest.main()
