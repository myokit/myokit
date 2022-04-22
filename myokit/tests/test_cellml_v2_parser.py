#!/usr/bin/env python3
#
# Tests the CellML 2.0 parser.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import os
import unittest

import myokit
import myokit.formats.cellml.v2 as v2

from myokit.tests import TemporaryDirectory, DIR_FORMATS, WarningCollector

# CellML directory
DIR = os.path.join(DIR_FORMATS, 'cellml')

# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp

# Strings in Python2 and Python3
try:
    basestring
except NameError:   # pragma: no cover
    basestring = str


class TestCellMLParser(unittest.TestCase):
    """ Tests the CellML 2.0 parser (mostly for errors / model validation). """

    def assertBad(self, xml, message, version='2.0'):
        """
        Inserts the given ``xml`` into a <model> element, parses it, and checks
        that this raises an exception matching ``message``.
        """
        self.assertRaisesRegex(
            v2.CellMLParsingError, message, self.parse, xml, version)

    def parse(self, xml, version='2.0'):
        """
        Inserts the given ``xml`` into a <model> element, parses it, and
        returns the result.
        """
        return v2.parse_string(self.wrap(xml, version))

    def parse_in_file(self, xml):
        """
        Inserts the given ``xml`` into a <model> element, writes it to a
        temporary file, parses it, and returns the result.
        """
        with TemporaryDirectory() as d:
            path = d.path('test.cellml')
            with open(path, 'w') as f:
                f.write(self.wrap(xml))
            return v2.parse_file(path)

    def wrap(self, xml, version='2.0'):
        """
        Wraps the given ``xml`` into a <model> element.
        """
        assert version == '2.0', 'version must be 2.0'
        v = version

        return (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<model name="test"'
            '       xmlns="http://www.cellml.org/cellml/' + v + '#"'
            '       xmlns:cellml="http://www.cellml.org/cellml/' + v + '#"'
            '       >'
            + xml +
            '</model>')

    def test_component(self):
        # Test component parsing

        # Parse component
        m = self.parse('<component name="ernie" />')
        self.assertIn('ernie', m)

        # Component must have name
        self.assertBad('<component />', 'Component element must have a name')

        # CellML errors are converted
        self.assertBad('<component name="1" />', 'identifier')

        # Resets are not supported
        self.assertBad(
            '<component name="c">'
            '<reset />'
            '</component>',
            'Resets are not supported')

        # Component can't have units
        m = (
            '<component name="ernie">'
            '<units name="wooster">'
            '<unit units="meter" />'
            '</units>'
            '</component>'
        )
        self.assertRaisesRegex(
            v2.CellMLParsingError, 'Unexpected content', self.parse, m)

    def test_connection(self):
        # Test connection parsing

        x = ('<component name="a">'
             '  <variable name="x" units="volt" interface="public" />'
             '</component>'
             '<component name="b">'
             '  <variable name="y" units="volt" interface="public"'
             '            initial_value="3" />'
             '</component>')

        # Parse valid connection
        y = ('<connection component_1="a" component_2="b">'
             '  <map_variables variable_1="x" variable_2="y" />'
             '</connection>')
        m = self.parse(x + y)
        self.assertIs(m['a']['x'].initial_value_variable(), m['b']['y'])

        # No map variables
        y = '<connection component_1="a" component_2="b" />'
        self.assertBad(x + y, 'at least one map_variables')

        # Missing component 1 or 2
        y = ('<connection component_2="b">'
             '  <map_variables variable_1="x" variable_2="y" />'
             '</connection>')
        self.assertBad(x + y, 'must define a component_1 attribute')
        y = ('<connection component_1="a">'
             '  <map_variables variable_1="x" variable_2="y" />'
             '</connection>')
        self.assertBad(x + y, 'must define a component_2 attribute')

        # Identical components
        y = ('<connection component_1="a" component_2="a">'
             '  <map_variables variable_1="x" variable_2="y" />'
             '</connection>')
        self.assertBad(x + y, 'must be different')

        # Non-existent components
        y = ('<connection component_1="ax" component_2="b">'
             '  <map_variables variable_1="x" variable_2="y" />'
             '</connection>')
        self.assertBad(x + y, 'component_1 attribute must refer to')
        y = ('<connection component_1="a" component_2="bx">'
             '  <map_variables variable_1="x" variable_2="y" />'
             '</connection>')
        self.assertBad(x + y, 'component_2 attribute must refer to')

        # Connected twice
        y = ('<connection component_1="a" component_2="b">'
             '  <map_variables variable_1="x" variable_2="y" />'
             '</connection>')
        self.assertBad(x + y + y, 'unique pair of components')

    def test_connection_map_variables(self):
        # Test parsing map_variables elements

        x = ('<component name="a">'
             '  <variable name="x" units="volt" interface="public" />'
             '</component>'
             '<component name="b">'
             '  <variable name="y" units="volt" interface="public" />'
             '</component>'
             '<connection component_1="a" component_2="b">')
        z = ('</connection>')

        # Valid connection is already checked

        # Missing variable 1 or 2
        y = '<map_variables variable_2="y" />'
        self.assertBad(x + y + z, 'must define a variable_1 attribute')
        y = '<map_variables variable_1="x" />'
        self.assertBad(x + y + z, 'must define a variable_2 attribute')

        # Non-existent variable 1 & 2
        y = '<map_variables variable_1="y" variable_2="y" />'
        self.assertBad(x + y + z, 'variable_1 attribute must refer to')
        y = '<map_variables variable_1="x" variable_2="z" />'
        self.assertBad(x + y + z, 'variable_2 attribute must refer to')

        # Connecting twice is not OK
        y = '<map_variables variable_1="x" variable_2="y" />'
        self.assertRaisesRegex(
            v2.CellMLParsingError, 'connected twice',
            self.parse, x + y + y + z)

        # Bad interfaces etc. propagate from cellml API
        q = ('<component name="a">'
             '  <variable name="x" units="volt" interface="public" />'
             '</component>'
             '<component name="b">'
             '  <variable name="y" units="volt" interface="private" />'
             '</component>'
             '<connection component_1="a" component_2="b">'
             '  <map_variables variable_1="x" variable_2="y" />'
             '</connection>')
        self.assertRaisesRegex(
            v2.CellMLParsingError, 'Unable to connect',
            self.parse, q)

    def test_evaluated_derivatives(self):
        # Test parsing a simple model; compare RHS derivatives to known ones

        # Load myokit model
        org_model = myokit.load_model('example')
        org_states = [x.qname() for x in org_model.states()]
        org_values = org_model.evaluate_derivatives()

        # Load exported version
        path = os.path.join(DIR, 'lr-1991-exported-2.cellml')
        cm = v2.parse_file(path)
        new_model = cm.myokit_model()
        new_states = [x.qname() for x in new_model.states()]
        new_values = new_model.evaluate_derivatives()

        # Compare each state (loop unrolled for easier debugging)
        org_i = 0
        new_i = new_states.index(org_states[org_i])
        self.assertEqual(org_values[org_i], new_values[new_i])

        org_i = 1
        new_i = new_states.index(org_states[org_i])
        self.assertEqual(org_values[org_i], new_values[new_i])

        org_i = 2
        new_i = new_states.index(org_states[org_i])
        self.assertEqual(org_values[org_i], new_values[new_i])

        org_i = 3
        new_i = new_states.index(org_states[org_i])
        self.assertEqual(org_values[org_i], new_values[new_i])

        org_i = 4
        new_i = new_states.index(org_states[org_i])
        self.assertEqual(org_values[org_i], new_values[new_i])

        org_i = 5
        new_i = new_states.index(org_states[org_i])
        self.assertEqual(org_values[org_i], new_values[new_i])

        org_i = 6
        new_i = new_states.index(org_states[org_i])
        self.assertEqual(org_values[org_i], new_values[new_i])

        org_i = 7
        new_i = new_states.index(org_states[org_i])
        self.assertEqual(org_values[org_i], new_values[new_i])

    def test_encapsulation(self):
        # Tests parsing an encapsulation element.

        x = ('<component name="a" />'
             '<component name="b" />'
             '<component name="c" />'
             )

        # Parse valid encapsulation
        y = ('<encapsulation>'
             '  <component_ref component="a">'
             '    <component_ref component="b">'
             '      <component_ref component="c" />'
             '    </component_ref>'
             '  </component_ref>'
             '</encapsulation>')
        m = self.parse(x + y)
        self.assertEqual(m['c'].parent(), m['b'])
        self.assertEqual(m['b'].parent(), m['a'])
        self.assertIsNone(m['a'].parent())

        # Missing component ref
        y = '<encapsulation />'
        self.assertBad(x + y, 'at least one component_ref')

        # The first component_ref must have at least one child
        y = ('<encapsulation>'
             '  <component_ref component="a" />'
             '</encapsulation>')
        self.assertBad(x + y, 'must have at least one child')

        # Only one encapsulation is allowed
        y = '<encapsulation /><encapsulation />'
        self.assertBad(y, 'cannot contain more than one encapsulation')

    def test_encapsulation_component_ref(self):
        # Tests parsing a component_ref element.

        # Valid has already been checked

        x = ('<component name="a" />'
             '<component name="b" />'
             '<component name="c" />'
             '<encapsulation>'
             '  <component_ref component="a">'
             '    <component_ref component="b" />')
        z = ('  </component_ref>'
             '</encapsulation>')

        # Missing component attribute
        y = '<component_ref />'
        self.assertBad(x + y + z, 'must define a component attribute')

        # Non-existent component
        y = '<component_ref component="jane" />'
        self.assertBad(x + y + z, 'must reference a component')

        # Two parents
        y = ('</component_ref>'
             '<component_ref component="c">'
             '  <component_ref component="b" />')
        self.assertBad(x + y + z, 'only have a single encapsulation parent')

        # CellML errors propagate
        y = ('</component_ref>'
             '<component_ref component="b">'
             '  <component_ref component="a" />')
        self.assertBad(x + y + z, 'hierarchy cannot be circular')

    def test_extension(self):
        # Extension elements or attributes are no longer a thing

        # Element
        self.assertBad(
            '<zzz:hiya xmlns:zzz="https://zzzx" />',
            'Unexpected content')

        # Attribute
        self.assertBad(
            '<component name="x" xmlns:rdf="rdf" rdf:attr="value" />',
            'Unexpected attribute')

    def test_id(self):
        # Test id attribute functionality

        # Ids can appear on any element
        x = (
            '<component id="hiya" name="a">'
            '  <variable name="x" units="volt" id="x" initial_value="0.1" />'
            '</component>'
            '<units name="wooster" id="woops">'
            '  <unit units="volt" id="yes" />'
            '</units>'
        )
        self.parse(x)

        # Empty ids are not allowed
        x = '<component name="x" id="" />'
        self.assertBad(x, 'id must be a non-empty')

        # Duplicate ids are not allowed
        x = ('<component name="x" id="x">'
             '  <variable name="a" units="volt" id="x" />'
             '</component>')
        self.assertBad(x, 'uplicate id')

    def test_import(self):
        # Import elements are not supported

        self.assertBad(
            '<import />', 'Imports are not supported', version='2.0')

    def test_math(self):
        # Tests parsing math elements
        x = ('<component name="a">'
             '  <variable name="x" units="volt" />'
             '  <math xmlns="http://www.w3.org/1998/Math/MathML">')
        z = ('  </math>'
             '</component>'
             '<component name="b">'
             '  <variable name="y" units="volt" initial_value="12.3" />'
             '</component>')

        # Test parsing valid equation
        y = '<apply><eq /><ci>x</ci><cn cellml:units="volt">-80</cn></apply>'
        m = self.parse(x + y + z)
        var = m['a']['x']
        self.assertEqual(var.rhs(), myokit.Number(-80, myokit.units.volt))

        # Constants
        m = self.parse(x + '<apply><eq /><ci>x</ci> <pi /> </apply>' + z)
        var = m['a']['x']
        self.assertEqual(var.rhs().unit(), myokit.units.dimensionless)

        # Variable doesn't exist
        y = '<apply><eq /><ci>y</ci><cn cellml:units="volt">-80</cn></apply>'
        self.assertBad(x + y + z, 'Variable references in equations must name')
        y = '<apply><eq /><ci>x</ci><ci>y</ci></apply>'
        self.assertBad(x + y + z, 'Variable references in equations must name')

        # No units in number
        y = '<apply><eq /><ci>x</ci><cn>-80</cn></apply>'
        self.assertBad(x + y + z, 'must define a cellml:units')

        # Non-existent units
        y = '<apply><eq /><ci>x</ci><cn cellml:units="vlop">-80</cn></apply>'
        self.assertBad(x + y + z, 'Unknown unit "vlop" referenced')

        # Items outside of MathML namespace
        y = '<cellml:component name="bertie" />'
        self.assertBad(x + y + z, 'must be in the mathml namespace')

        # Doesn't start with an apply
        y = '<ci>x</ci>'
        self.assertBad(x + y + z, 'Expecting mathml:apply but found')

        # Not an equality
        y = '<apply><plus /><ci>x</ci></apply>'
        self.assertBad(x + y + z, 'expecting a list of equations')

        # Not in assignment form
        y = ('<apply>'
             ' <eq />'
             ' <apply><plus /><ci>x</ci><cn cellml:units="volt">1</cn></apply>'
             ' <cn cellml:units="volt">10</cn>'
             '</apply>')
        self.assertBad(x + y + z, 'Invalid expression found on the left-hand')

        # MathML inside the model element
        self.assertBad(
            '<math xmlns="http://www.w3.org/1998/Math/MathML" />',
            'element of type mathml:math',
        )

        # Attributes from the MathML namespace
        self.assertBad(
            '<component name="c" mathml:name="d" '
            ' xmlns:mathml="http://www.w3.org/1998/Math/MathML" />',
            'Unexpected attribute mathml:name',
        )

    def test_model(self):
        # Tests parsing a model element.

        # Valid one is already tested

        # Invalid namespace
        x = '<?xml version="1.0" encoding="UTF-8"?>'
        y = '<model name="x" xmlns="http://example.com" />'
        self.assertRaisesRegex(
            v2.CellMLParsingError, 'must be in CellML',
            v2.parse_string, x + y)

        # CellML 2.0 is ok
        y = '<model name="x" xmlns="http://www.cellml.org/cellml/2.0#" />'
        m = v2.parse_string(x + y)
        self.assertEqual(m.version(), '2.0')

        # Not a model
        y = '<module name="x" xmlns="http://www.cellml.org/cellml/2.0#" />'
        self.assertRaisesRegex(
            v2.CellMLParsingError, 'must be a CellML model',
            v2.parse_string, x + y)

        # No name
        y = '<model xmlns="http://www.cellml.org/cellml/2.0#" />'
        self.assertRaisesRegex(
            v2.CellMLParsingError, 'Model element must have a name',
            v2.parse_string, x + y)

        # CellML API errors are wrapped
        y = '<model name="123" xmlns="http://www.cellml.org/cellml/2.0#" />'
        self.assertRaisesRegex(
            v2.CellMLParsingError, 'valid CellML identifier',
            v2.parse_string, x + y)

        # Too many free variables
        self.assertBad(
            '<component name="a">'
            '  <variable name="x" units="dimensionless" initial_value="0.1" />'
            '  <variable name="y" units="dimensionless" initial_value="2.3" />'
            '  <variable name="time1" units="dimensionless" />'
            '  <variable name="time2" units="dimensionless" />'
            '  <math xmlns="http://www.w3.org/1998/Math/MathML">'
            '    <apply>'
            '      <eq />'
            '      <apply>'
            '        <diff/>'
            '        <bvar>'
            '          <ci>time1</ci>'
            '        </bvar>'
            '        <ci>x</ci>'
            '      </apply>'
            '      <cn cellml:units="dimensionless">1</cn>'
            '    </apply>'
            '    <apply>'
            '      <eq />'
            '      <apply>'
            '        <diff/>'
            '        <bvar>'
            '          <ci>time2</ci>'
            '        </bvar>'
            '        <ci>y</ci>'
            '      </apply>'
            '      <cn cellml:units="dimensionless">2</cn>'
            '    </apply>'
            '  </math>'
            '</component>',
            'derivatives with respect to more than one variable')

    def test_overdefined(self):
        # Tests for overdefined variables

        # Initial value and equation for state
        x = ('<component name="overdefined">'
             '  <variable name="time" units="dimensionless" />'
             '  <variable name="x" units="dimensionless" initial_value="2" />'
             '  <math xmlns="http://www.w3.org/1998/Math/MathML">')
        a = ('    <apply>'
             '      <eq />'
             '      <apply>'
             '        <diff/>'
             '        <bvar>'
             '          <ci>time</ci>'
             '        </bvar>'
             '        <ci>x</ci>'
             '      </apply>'
             '      <cn cellml:units="dimensionless">3</cn>'
             '    </apply>')
        z = ('  </math>'
             '</component>')
        m = self.parse(x + a + z)
        v = m['overdefined']['x']
        self.assertEqual(v.rhs(), myokit.Number(3))
        self.assertEqual(v.initial_value(), myokit.Number(2))

        # Initial value and equation for a non-state
        b = ('    <apply>'
             '      <eq /><ci>time</ci><cn cellml:units="dimensionless">1</cn>'
             '    </apply>'
             '    <apply>'
             '      <eq /><ci>x</ci><cn cellml:units="dimensionless">2</cn>'
             '    </apply>')
        self.assertBad(x + b + z, 'equation and an initial value')

        # Two equations
        self.assertBad(x + a + a + z, 'Two defining equations')

    def test_parse_file(self):
        # Tests the parse file method

        # Parse a valid file
        m = self.parse_in_file('<component name="a" />')
        self.assertIn('a', m)

        # Parse invalid XML: errors must be wrapped
        self.assertRaisesRegex(
            v2.CellMLParsingError,
            'Unable to parse XML',
            self.parse_in_file,
            '<component',
        )

    def test_parse_string(self):
        # Tests the parse string method

        # Valid version is already tested

        # Parse invalid XML: errors must be wrapped
        self.assertRaisesRegex(
            v2.CellMLParsingError,
            'Unable to parse XML',
            v2.parse_string,
            'Hello there',
        )

    def test_text_in_elements(self):
        # Test for text inside (and after) elements

        self.assertBad(
            '<component name="c">Hiya</component>',
            'Text found in cellml:component')
        self.assertBad(
            '<component name="c"></component>Hiya',
            'Text found in cellml:model')

    def test_unexpected(self):
        # Test for unexpected elements and attributes

        self.assertBad('<wooster />', 'Unexpected content type')
        self.assertBad(
            '<component name="c" food="nice" />', 'Unexpected attribute')

    def test_unit(self):
        # Test parsing a unit row

        # Parse a valid set of units (that needs sorting)
        x = ('<units name="megawooster">'
             '  <unit units="wooster" prefix="mega" />'
             '</units>'
             '<units name="wooster">'
             '  <unit units="volt"'
             '        prefix="milli"'
             '        exponent="2"'
             '        multiplier="1.2" />'
             '</units>')
        m = self.parse(x)
        wooster_ref = m.find_units('wooster')
        wooster_myo = ((myokit.units.volt * 1e-3) ** 2) * 1.2
        self.assertEqual(wooster_myo, wooster_ref.myokit_unit())
        megawooster_ref = m.find_units('megawooster')
        self.assertEqual(wooster_myo * 1e6, megawooster_ref.myokit_unit())

        # Test that CellML errors are wrapped
        x = ('<units name="wooster">'
             '  <unit units="volt" prefix="woopsie" />'
             '</units>')
        self.assertBad(x, 'must be a string from the list')

        # No units definition
        x = ('<units name="wooster">'
             '  <unit />'
             '</units>')
        self.assertBad(x, 'must have a units attribute')

        # Non-integer exponents are supported
        x = ('<units name="unsup">'
             '  <unit units="ampere" exponent="2.34" />'
             '</units>')
        m = self.parse(x)
        self.assertEqual(
            m.find_units('unsup').myokit_unit(),
            myokit.units.ampere**2.34
        )

    def test_units(self):
        # Test parsing a units definition

        # Valid has already been testsed

        # New base units are not supported
        x = '<units name="base" />'
        with WarningCollector() as w:
            m = self.parse(x)
        self.assertIn('new base units', w.text())
        self.assertEqual(
            m.find_units('base').myokit_unit(), myokit.units.dimensionless)

        # CellML errors are converted to parse errors
        x = '<units name="123"><unit units="volt" /></units>'
        self.assertBad(x, 'valid CellML identifier')

        # Missing name
        x = '<units><unit units="volt" /></units>'
        self.assertBad(x, 'must have a name')

        # Name overlaps with predefined
        x = '<units name="metre"><unit units="volt" /></units>'
        self.assertBad(x, 'overlaps with a predefined name')

        # Duplicate name (handled in sorting)
        x = '<units name="wooster"><unit units="volt" /></units>'
        self.assertBad(x + x, 'Duplicate units definition')

        # Missing units definitions
        x = ('<units name="wooster"><unit units="fluther" /></units>')
        self.assertBad(x, 'Unable to resolve network of units')

        # Circular units definitions
        x = ('<units name="wooster"><unit units="fluther" /></units>'
             '<units name="fluther"><unit units="wooster" /></units>')
        self.assertBad(x, 'Unable to resolve network of units')

    def test_units_predefined(self):
        # Tests parsing all the predefined units

        def u(units):
            m = self.parse(
                '<component name="c">'
                '  <variable name="x" units="' + units + '"'
                '   initial_value="1" />'
                '</component>'
            )
            return m['c']['x'].units().myokit_unit()

        self.assertEqual(u('ampere'), myokit.units.ampere)
        self.assertEqual(u('becquerel'), myokit.units.becquerel)
        self.assertEqual(u('candela'), myokit.units.candela)
        self.assertEqual(u('coulomb'), myokit.units.coulomb)
        self.assertEqual(u('dimensionless'), myokit.units.dimensionless)
        self.assertEqual(u('farad'), myokit.units.farad)
        self.assertEqual(u('gram'), myokit.units.g)
        self.assertEqual(u('gray'), myokit.units.gray)
        self.assertEqual(u('henry'), myokit.units.henry)
        self.assertEqual(u('hertz'), myokit.units.hertz)
        self.assertEqual(u('joule'), myokit.units.joule)
        self.assertEqual(u('katal'), myokit.units.katal)
        self.assertEqual(u('kelvin'), myokit.units.kelvin)
        self.assertEqual(u('kilogram'), myokit.units.kg)
        self.assertEqual(u('litre'), myokit.units.liter)
        self.assertEqual(u('lumen'), myokit.units.lumen)
        self.assertEqual(u('lux'), myokit.units.lux)
        self.assertEqual(u('metre'), myokit.units.meter)
        self.assertEqual(u('mole'), myokit.units.mole)
        self.assertEqual(u('newton'), myokit.units.newton)
        self.assertEqual(u('ohm'), myokit.units.ohm)
        self.assertEqual(u('pascal'), myokit.units.pascal)
        self.assertEqual(u('radian'), myokit.units.radian)
        self.assertEqual(u('second'), myokit.units.second)
        self.assertEqual(u('siemens'), myokit.units.siemens)
        self.assertEqual(u('sievert'), myokit.units.sievert)
        self.assertEqual(u('steradian'), myokit.units.steradian)
        self.assertEqual(u('tesla'), myokit.units.tesla)
        self.assertEqual(u('volt'), myokit.units.volt)
        self.assertEqual(u('watt'), myokit.units.watt)
        self.assertEqual(u('weber'), myokit.units.weber)

    def test_variable(self):
        # Tests parsing variables

        # Must have a name
        x = '<component name="a"><variable units="volt"/></component>'
        self.assertBad(x, 'must have a name attribute')

        # Must have units
        x = '<component name="a"><variable name="a" /></component>'
        self.assertBad(x, 'must have a units attribute')

        # CellML errors are converted to parsing errors
        x = '<variable name="1" units="volt"/>'
        x = '<component name="a">' + x + '</component>'
        self.assertBad(x, 'valid CellML identifier')


if __name__ == '__main__':
    import warnings
    warnings.simplefilter('always')
    unittest.main()
