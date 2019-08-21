#!/usr/bin/env python3
#
# Tests the CellML importer
#
# This file is part of Myokit
#  Copyright 2011-2019 Maastricht University, University of Oxford
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
except AttributeError:
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp

# Strings in Python 2 and 3
try:
    basestring
except NameError:   # pragma: no python 2 cover
    basestring = str


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

    def test_model_simple(self):
        # Beeler-Reuter is a simple model
        i = formats.importer('cellml')
        m = i.model(os.path.join(DIR_FORMATS, 'br-1977.cellml'))
        m.validate()

    def test_model_dot(self):
        # This is beeler-reuter but with a dot() in an expression
        i = formats.importer('cellml')
        m = i.model(os.path.join(DIR_FORMATS, 'br-1977-dot.cellml'))
        m.validate()

    def test_model_nesting(self):
        # The corrias model has multiple levels of nesting (encapsulation)
        i = formats.importer('cellml')
        m = i.model(os.path.join(DIR_FORMATS, 'corrias.cellml'))
        m.validate()

    def test_info(self):
        i = formats.importer('cellml')
        self.assertIsInstance(i.info(), basestring)

    def test_import(self):
        # Imports should raise an error
        i = formats.importer('cellml')
        self.assertRaisesRegex(
            myokit.formats.cellml.CellMLError, '<import>',
            i.model, os.path.join(DIR_FORMATS, 'cellml-1-import.cellml'))

    def test_reaction(self):
        # Reaction elements should raise an error
        i = formats.importer('cellml')
        self.assertRaisesRegex(
            myokit.formats.cellml.CellMLError, '<reaction>',
            i.model, os.path.join(DIR_FORMATS, 'cellml-2-reaction.cellml'))

    def test_factorial(self):
        # Test if factorial, partialdiff, and sum elements trigger a warning.

        i = formats.importer('cellml')
        i.model(os.path.join(
            DIR_FORMATS, 'cellml-3-factorial-partialdiff-sum.cellml'))
        w = '\n'.join(i.logger().warnings())
        self.assertIn('<factorial>', w)
        self.assertIn('<partialdiff>', w)
        self.assertIn('<sum>', w)

    def test_unit_errors(self):
        # Test if warnings to do with units are raised.

        i = formats.importer('cellml')
        m = i.model(os.path.join(
            DIR_FORMATS, 'cellml-4-unit-errors.cellml'))
        w = '\n'.join(i.logger().warnings())

        # Some units that can't be parsed can be added as meta data
        self.assertIsNone(m.get('Main.y').unit(), 'hi')
        self.assertIn('cellml_unit', m.get('Main.y').meta)

        # Offset attribute is not supported
        self.assertIn('"offset" attribute', w)

        # Variable refers to a non-existing unit
        self.assertIn('Unable to resolve unit', w)

        # Unit refers to a non-existing unit
        self.assertIn('Unknown base unit', w)

        # Unknown prefix
        # Non-integer prefix
        self.assertIn('Unknown prefix', w)

        # Non-integer exponent
        self.assertIn('Non-integer exponent', w)

        # Non-number exponent
        self.assertIn('Unable to parse exponent', w)

    def test_group_errors(self):
        # Test if warnings related to groups are raised.

        i = formats.importer('cellml')
        self.assertRaisesRegex(
            myokit.formats.cellml.CellMLError,
            'Group registered for unknown component',
            i.model,
            os.path.join(DIR_FORMATS, 'cellml-5-group-errors-1.cellml'))

        self.assertRaisesRegex(
            myokit.formats.cellml.CellMLError,
            'Group registered for unknown component',
            i.model,
            os.path.join(DIR_FORMATS, 'cellml-5-group-errors-2.cellml'))

    def test_connection_errors(self):
        # Test if warnings related to connections are raised.

        # Connection fo component that doesn't exist
        i = formats.importer('cellml')
        self.assertRaisesRegex(
            myokit.formats.cellml.CellMLError,
            'Connection found for unlisted component',
            i.model,
            os.path.join(DIR_FORMATS, 'cellml-6-connection-errors-1.cellml'))

        # Map variables for bad variable_1, bad variable_2, and resulting
        # unresolved references
        i.model(
            os.path.join(DIR_FORMATS, 'cellml-6-connection-errors-2.cellml'))
        w = '\n'.join(i.logger().warnings())
        self.assertIn('No interface found for variable <bikes>', w)
        self.assertIn('No interface found for variable <cars>', w)
        self.assertIn('Unresolved reference <i_x1>', w)
        self.assertIn('Unresolved reference <i_s>', w)

        # Bad public interface
        self.assertIn('Unable to resolve connection', w)

        # RHS with unknown variable
        self.assertIn('Unable to resolve RHS', w)
        # And resulting unkown RHS
        self.assertIn('No expression for variable', w)

        # Unit mismatch between connected variables
        self.assertIn('Unit mismatch between', w)

    def test_equation_errors(self):
        # Test warnings raised in equation handling.

        i = formats.importer('cellml')

        # Two variables of integration
        self.assertRaisesRegex(
            myokit.formats.cellml.CellMLError,
            'Found derivatives to two different variables',
            i.model,
            os.path.join(DIR_FORMATS, 'cellml-7-equation-errors-1.cellml'))

        # Only <apply> is allowed in <maths>
        self.assertRaisesRegex(
            myokit.formats.cellml.CellMLError,
            'expecting <apply>',
            i.model,
            os.path.join(DIR_FORMATS, 'cellml-7-equation-errors-2.cellml'))

        # Only <apply> is allowed in <maths>
        self.assertRaisesRegex(
            myokit.formats.cellml.CellMLError,
            'expecting <eq>',
            i.model,
            os.path.join(DIR_FORMATS, 'cellml-7-equation-errors-3.cellml'))

        # No DAEs
        self.assertRaisesRegex(
            myokit.formats.cellml.CellMLError,
            'Differential algebraic',
            i.model,
            os.path.join(DIR_FORMATS, 'cellml-7-equation-errors-4.cellml'))

        # Equation for non-existent variable
        self.assertRaisesRegex(
            myokit.formats.cellml.CellMLError,
            'Equation found for unknown variable',
            i.model,
            os.path.join(DIR_FORMATS, 'cellml-7-equation-errors-5.cellml'))

        i.model(
            os.path.join(DIR_FORMATS, 'cellml-7-equation-errors-6.cellml'))
        w = '\n'.join(i.logger().warnings())
        self.assertIn('No initial value', w)

    def test_name_errors(self):
        # Test warnings raised in name handling.

        i = formats.importer('cellml')
        i.model(
            os.path.join(DIR_FORMATS, 'cellml-8-invalid-names.cellml'))
        w = '\n'.join(i.logger().warnings())
        self.assertIn('Invalid name', w)


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

        # Test name is adapted if stimulus is already a component
        model.add_component('stimulus')
        model.add_component('stimulus_2')
        with TemporaryDirectory() as d:
            path = d.path('model.cellml')
            e.model(path, model)

            # Import model and check added stimulus works
            m2 = i.model(path)
            m2.get('engine.time').set_binding('time')
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
        mad_unit /= myokit.units.s
        mad_unit *= myokit.units.A
        time.set_unit(mad_unit)

        pure_multiplier = myokit.Unit()
        pure_multiplier *= 1001
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


if __name__ == '__main__':
    unittest.main()
