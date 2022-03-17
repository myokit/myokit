#!/usr/bin/env python3
#
# Tests the CellML 1.0/1.1 parser.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import os
import unittest

import myokit
import myokit.formats.cellml as cellml
import myokit.formats.cellml.v1 as v1

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
    """ Tests the CellML 1.0/1.1 parser (mostly for errors). """

    def assertBad(self, xml, message, version='1.0'):
        """
        Inserts the given ``xml`` into a <model> element, parses it, and checks
        that this raises an exception matching ``message``.
        """
        self.assertRaisesRegex(
            v1.CellMLParsingError, message, self.parse, xml, version)

    def parse(self, xml, version='1.0'):
        """
        Inserts the given ``xml`` into a <model> element, parses it, and
        returns the result.
        """
        return v1.parse_string(self.wrap(xml, version))

    def parse_in_file(self, xml):
        """
        Inserts the given ``xml`` into a <model> element, writes it to a
        temporary file, parses it, and returns the result.
        """
        with TemporaryDirectory() as d:
            path = d.path('test.cellml')
            with open(path, 'w') as f:
                f.write(self.wrap(xml))
            return v1.parse_file(path)

    def wrap(self, xml, version='1.0'):
        """
        Wraps the given ``xml`` into a <model> element.
        """
        assert version in ('1.0', '1.1'), 'version must be 1.0 or 1.1'
        v = version
        # Note: Meta data stays version 1.0

        return (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<model name="test"'
            '       xmlns="http://www.cellml.org/cellml/' + v + '#"'
            '       xmlns:cellml="http://www.cellml.org/cellml/' + v + '#"'
            '       xmlns:cmeta="http://www.cellml.org/metadata/1.0#"'
            '       xmlns:rdf="' + cellml.NS_RDF + '"'
            '       xmlns:bqbiol="' + cellml.NS_BQBIOL + '">'
            + xml +
            '</model>')

    def test_cellml_namespace(self):
        # Attributes from the CellML namespace are not allowed

        self.assertBad(
            '<component name="c" cellml:name="d" />',
            'Unexpected attribute cellml:name',
        )

    def test_cmeta_ids(self):
        # Test cmeta ids are parsed

        # Test parsing cmeta id
        path = os.path.join(DIR, 'br-1977.cellml')
        model = v1.parse_file(path)
        self.assertEqual(model.cmeta_id(), 'beeler_reuter_1977')

        # Invalid cmeta id
        self.assertBad(
            '<component cmeta:id="" name="c" />',
            'non-empty string')

        # Duplicate cmeta id
        self.assertBad(
            '<component cmeta:id="x" name="c" />'
            '<component cmeta:id="x" name="d" />',
            'Duplicate cmeta:id')

    def test_cmeta_namespace(self):
        # Only the cmeta:id attribute is allowed, no other cmeta attributes or
        # elements.

        # Attribute in cmeta
        self.assertBad(
            '<component name="c" cmeta:ernie="bert" />',
            'Unexpected attribute cmeta:ernie')

        # Element in cmeta
        self.assertBad(
            '<component name="c">'
            '  <cmeta:bert />'
            '</component>',
            'element of type cmeta:bert')

    def test_component(self):
        # Test component parsing

        # Parse component
        m = self.parse('<component name="ernie" />')
        self.assertIn('ernie', m)

        # Component must have name
        self.assertBad('<component />', 'Component element must have a name')

        # CellML errors are converted
        self.assertBad('<component name="1" />', 'identifier')

        # Reactions are not supported
        self.assertBad(
            '<component name="c">'
            '<reaction />'
            '</component>',
            'Reactions are not supported')

        # Component can have units
        m = self.parse(
            '<component name="ernie">'
            '<units name="wooster">'
            '<unit units="meter" />'
            '</units>'
            '</component>'
        )
        e = m['ernie']
        u = e.find_units('wooster')

    def test_connection(self):
        # Test connection parsing

        x = ('<component name="a">'
             '  <variable name="x" units="volt" public_interface="in" />'
             '</component>'
             '<component name="b">'
             '  <variable name="y" units="volt" public_interface="out"'
             '            initial_value="1" />'
             '</component>')

        # Parse valid connection
        y = ('<connection>'
             '  <map_components component_1="a" component_2="b" />'
             '  <map_variables variable_1="x" variable_2="y" />'
             '</connection>')
        m = self.parse(x + y)
        self.assertIs(m['a']['x'].source(), m['b']['y'])
        self.assertIsNone(m['b']['y'].source())

        # No map components
        self.assertBad(x + '<connection />', 'exactly one map_components')

        # No map variables
        y = ('<connection>'
             '  <map_components component_1="a" component_2="b" />'
             '</connection>')
        self.assertBad(x + y, 'at least one map_variables')

    def test_connection_map_components(self):
        # Test parsing map_components elements

        x = ('<component name="a">'
             '  <variable name="x" units="volt" public_interface="in" />'
             '</component>'
             '<component name="b">'
             '  <variable name="y" units="volt" public_interface="out" />'
             '</component>')

        # Valid connection is already checked

        # Missing component 1 or 2
        y = ('<connection>'
             '  <map_components component_2="b" />'
             '  <map_variables variable_1="x" variable_2="y" />'
             '</connection>')
        self.assertBad(x + y, 'must define a component_1 attribute')
        y = ('<connection>'
             '  <map_components component_1="a" />'
             '  <map_variables variable_1="x" variable_2="y" />'
             '</connection>')
        self.assertBad(x + y, 'must define a component_2 attribute')

        # Identical components
        y = ('<connection>'
             '  <map_components component_1="a" component_2="a" />'
             '  <map_variables variable_1="x" variable_2="y" />'
             '</connection>')
        self.assertBad(x + y, 'must be different')

        # Non-existent components
        y = ('<connection>'
             '  <map_components component_1="ax" component_2="b" />'
             '  <map_variables variable_1="x" variable_2="y" />'
             '</connection>')
        self.assertBad(x + y, 'component_1 attribute must refer to')
        y = ('<connection>'
             '  <map_components component_1="a" component_2="bx" />'
             '  <map_variables variable_1="x" variable_2="y" />'
             '</connection>')
        self.assertBad(x + y, 'component_2 attribute must refer to')

        # Connected twice
        y = ('<connection>'
             '  <map_components component_1="a" component_2="b" />'
             '  <map_variables variable_1="x" variable_2="y" />'
             '</connection>')
        self.assertBad(x + y + y, 'unique pair of components')

    def test_connection_map_variables(self):
        # Test parsing map_variables elements

        x = ('<component name="a">'
             '  <variable name="x" units="volt" public_interface="in" />'
             '</component>'
             '<component name="b">'
             '  <variable name="y" units="volt" public_interface="out" />'
             '</component>'
             '<connection>'
             '  <map_components component_1="a" component_2="b" />')
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
            v1.CellMLParsingError, 'already connected to',
            self.parse, x + y + y + z)

        # Bad interfaces etc. propagate from cellml API
        q = ('<component name="a">'
             '  <variable name="x" units="volt" public_interface="out" />'
             '</component>'
             '<component name="b">'
             '  <variable name="y" units="volt" public_interface="out" />'
             '</component>'
             '<connection>'
             '  <map_components component_1="a" component_2="b" />'
             '  <map_variables variable_1="x" variable_2="y" />'
             '</connection>')
        self.assertRaisesRegex(
            v1.CellMLParsingError, 'Invalid connection',
            self.parse, q)

    def test_documentation(self):
        # Tests parsing a <documentation> tag from the cellml temp doc ns

        path = os.path.join(DIR, 'documentation.cellml')
        expected = '\n'.join([
            'Article title',
            '',
            'Michael',
            'Clerx',
            '',
            'University of Oxford',
            '',
            'Model Status',
            'This model is fake.',
            '',
            'This is a paragraph.',
            '',
            'schematic diagram',
            '',
            'A schematic diagram describing the model.',
            '',
            'Here\'s some extra documentation.',
        ])
        m = v1.parse_file(path)
        self.assertEqual(m.meta['documentation'], expected)

    def test_evaluated_derivatives(self):
        # Test parsing a simple model; compare RHS derivatives to known ones

        # Load myokit model
        org_model = myokit.load_model('example')
        org_states = [x.qname() for x in org_model.states()]
        org_values = org_model.evaluate_derivatives()

        # Load exported version
        path = os.path.join(DIR, 'lr-1991-exported-1.cellml')
        cm = v1.parse_file(path)
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

    def test_extensions(self):
        # Test handling of extension elements

        # CellML elements can not appear inside extensions
        self.assertBad(
            '<x:y xmlns:x="x"><component name="c" /></x:y>',
            'found inside extension element')
        self.assertBad(
            '<x:a xmlns:x="xxx">'
            '  <y:b xmlns:y="yyy">'
            '    <z:b xmlns:z="zzz">'
            '      <component name="c" />'
            '    </z:b>'
            '  </y:b>'
            '</x:a>',
            'found inside extension element')

        # CellML attributes can not appear inside extensions
        self.assertBad(
            '<x:y xmlns:x="x" cellml:name="a" />',
            'found in extension element')
        self.assertBad(
            '<x:a xmlns:x="xxx">'
            '  <y:b xmlns:y="yyy">'
            '    <z:b xmlns:z="zzz" cellml:name="b" />'
            '  </y:b>'
            '</x:a>',
            'found in extension element')

    def test_group(self):
        # Tests parsing a group element.

        x = ('<component name="a" />'
             '<component name="b" />'
             '<component name="c" />'
             )

        # Parse valid group
        y = ('<group>'
             '  <relationship_ref relationship="encapsulation"/>'
             '  <component_ref component="a">'
             '    <component_ref component="b">'
             '      <component_ref component="c" />'
             '    </component_ref>'
             '  </component_ref>'
             '</group>')
        m = self.parse(x + y)
        self.assertEqual(m['c'].parent(), m['b'])
        self.assertEqual(m['b'].parent(), m['a'])
        self.assertIsNone(m['a'].parent())

        # Missing component ref
        y = ('<group>'
             '  <relationship_ref relationship="encapsulation"/>'
             '</group>')
        self.assertBad(x + y, 'at least one component_ref')

        # Missing relationship ref
        y = ('<group>'
             '  <component_ref component="a">'
             '    <component_ref component="b" />'
             '  </component_ref>'
             '</group>')
        self.assertBad(x + y, 'at least one relationship_ref')

        # In encapsulation and containment relationships, the first
        # component_ref must have at least one child
        y = ('<group>'
             '  <relationship_ref relationship="encapsulation" />'
             '  <component_ref component="a" />'
             '</group>')
        self.assertBad(x + y, r'must have at least one child \(6.4.3.2\)')
        y = ('<group>'
             '  <relationship_ref relationship="containment" />'
             '  <component_ref component="a" />'
             '</group>')
        self.assertBad(x + y, r'must have at least one child \(6.4.3.2\)')

        # But it's fine for extension types
        y = ('<group xmlns:x="x">'
             '  <relationship_ref x:relationship="family" />'
             '  <component_ref component="a" />'
             '</group>')
        self.parse(x + y)

    def test_group_component_ref(self):
        # Tests parsing a component_ref element.

        # Valid has already been checked

        x = ('<component name="a" />'
             '<component name="b" />'
             '<component name="c" />'
             '<group>'
             '  <relationship_ref relationship="encapsulation"/>'
             '  <component_ref component="a">'
             '    <component_ref component="b" />')
        z = ('  </component_ref>'
             '</group>')

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

    def test_group_relationship_ref(self):
        # Tests parsing a relationsip_ref element.

        # Valid has already been checked

        x = ('<component name="a" />'
             '<component name="b" />'
             '<group>'
             '  <component_ref component="a">'
             '    <component_ref component="b" />'
             '  </component_ref>')
        z = ('</group>')

        # Containment is ok but ignored
        y = '<relationship_ref relationship="containment" />'
        m = self.parse(x + y + z)
        self.assertIsNone(m['a'].parent())
        self.assertIsNone(m['b'].parent())

        # Relationship in other namespace is allowed but ignored
        y = ('<relationship_ref'
             '   xmlns:zippy="http://example.com"'
             '   zippy:relationship="a-loose-affiliation" />')
        m = self.parse(x + y + z)
        self.assertIsNone(m['a'].parent())
        self.assertIsNone(m['b'].parent())

        # Only containment and encapsulation exist within CellML
        y = '<relationship_ref relationship="equal" />'
        self.assertBad(x + y + z, 'Unknown relationship type')

        # Relationship attribute must be present
        y = '<relationship_ref />'
        self.assertBad(x + y + z, 'must define a relationship attribute')

        # Multiple relationship types are allowed
        y = ('<relationship_ref relationship="encapsulation" />'
             '<relationship_ref relationship="containment" />')
        m = self.parse(x + y + z)
        self.assertIsNone(m['a'].parent())
        self.assertEqual(m['b'].parent(), m['a'])

        # Multiple named containment relationship types are allowed
        y = ('<relationship_ref relationship="containment" name="x" />'
             '<relationship_ref relationship="containment" />')
        m = self.parse(x + y + z)
        self.assertIsNone(m['a'].parent())
        self.assertIsNone(m['b'].parent())

        # Duplicate relationships are not allowed
        y = ('<relationship_ref relationship="containment" />'
             '<relationship_ref relationship="containment" />')
        self.assertBad(x + y + z, 'must have a unique pair')
        y = ('<relationship_ref relationship="containment" name="xx" />'
             '<relationship_ref relationship="containment" name="xx" />')
        self.assertBad(x + y + z, 'must have a unique pair')

        # Name must be a valid identifier
        y = '<relationship_ref relationship="containment" name="123" />'
        self.assertBad(x + y + z, 'valid CellML identifier')

        # Encapsulation can't be named
        y = '<relationship_ref relationship="encapsulation" name="betty" />'
        self.assertBad(x + y + z, 'may not define a name')

    def test_import(self):
        # Import elements are not supported

        # Not allowed in 1.0
        self.assertBad(
            '<import />', 'not allowed in CellML 1.0', version='1.0')

        # Not supported in 1.1
        self.assertBad(
            '<import />', 'Imports are not supported', version='1.1')

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

        # Valid equation inside a semantics element
        m = self.parse(x + '<semantics>' + y + '</semantics>' + z)
        var = m['a']['x']
        self.assertEqual(var.rhs(), myokit.Number(-80, myokit.units.volt))

        # Valid equation with some annotations to ignore
        m = self.parse(x + '<annotation />' + y + '<annotation-xml />' + z)
        var = m['a']['x']
        self.assertEqual(var.rhs(), myokit.Number(-80, myokit.units.volt))

        # Constants
        m = self.parse(x + '<apply><eq /><ci>x</ci> <pi /> </apply>' + z)
        var = m['a']['x']
        self.assertEqual(var.rhs().unit(), myokit.units.dimensionless)

        # Variable doesn't exist
        y = '<apply><eq /><ci>y</ci><cn cellml:units="volt">-80</cn></apply>'
        self.assertBad(x + y + z, 'Variable references in equation must name')
        y = '<apply><eq /><ci>x</ci><ci>y</ci></apply>'
        self.assertBad(x + y + z, 'Variable references in equation must name')

        # No units in number
        y = '<apply><eq /><ci>x</ci><cn>-80</cn></apply>'
        self.assertBad(x + y + z, 'must define a cellml:units')

        # Non-existent units
        y = '<apply><eq /><ci>x</ci><cn cellml:units="vlop">-80</cn></apply>'
        self.assertBad(x + y + z, 'Unknown unit "vlop" referenced')

        # Unsupported units: Warning
        y = '<apply><eq /><ci>x</ci><cn cellml:units="celsius">2</cn></apply>'
        with WarningCollector() as w:
            self.parse(x + y + z)
        self.assertIn('celsius', w.text())

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

        # Assignment to a variable with an "in" interface (error should be
        # converted from CellMLError to CellMLParsingError).
        x = ('<component name="a">'
             '  <variable name="x" units="volt" public_interface="in" />'
             '  <math xmlns="http://www.w3.org/1998/Math/MathML">')
        y = '<apply><eq /><ci>x</ci><cn cellml:units="volt">-80</cn></apply>'
        self.assertBad(x + y + z, 'public_interface="in"')

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

    def test_maths_1_1(self):
        # Test setting a variable as initial value, allowed in 1.1

        # Legal case in 1.1
        x = ('<component name="a">'
             '  <variable name="p" units="volt" initial_value="q" />'
             '  <variable name="q" units="volt" initial_value="12.3" />'
             '</component>')

        # Not allowed in 1.0
        self.assertBad(x, r'a real number \(3.4.3.7\)', version='1.0')

        # Not supported in 1.1
        self.assertBad(x, 'not supported', version='1.1')

    def test_model(self):
        # Tests parsing a model element.

        # Valid one is already tested

        # Invalid namespace
        x = '<?xml version="1.0" encoding="UTF-8"?>'
        y = '<model name="x" xmlns="http://example.com" />'
        self.assertRaisesRegex(
            v1.CellMLParsingError, 'must be in CellML',
            v1.parse_string, x + y)

        # CellML 1.0 and 1.1 are ok
        y = '<model name="x" xmlns="http://www.cellml.org/cellml/1.0#" />'
        m = v1.parse_string(x + y)
        self.assertEqual(m.version(), '1.0')
        y = '<model name="x" xmlns="http://www.cellml.org/cellml/1.1#" />'
        m = v1.parse_string(x + y)
        self.assertEqual(m.version(), '1.1')

        # Not a model
        y = '<module name="x" xmlns="http://www.cellml.org/cellml/1.0#" />'
        self.assertRaisesRegex(
            v1.CellMLParsingError, 'must be a CellML model',
            v1.parse_string, x + y)

        # No name
        y = '<model xmlns="http://www.cellml.org/cellml/1.0#" />'
        self.assertRaisesRegex(
            v1.CellMLParsingError, 'Model element must have a name',
            v1.parse_string, x + y)

        # CellML API errors are wrapped
        y = '<model name="123" xmlns="http://www.cellml.org/cellml/1.0#" />'
        self.assertRaisesRegex(
            v1.CellMLParsingError, 'valid CellML identifier',
            v1.parse_string, x + y)

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
        x = ('<component name="a">'
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
        v = m['a']['x']
        self.assertEqual(v.rhs(), myokit.Number(3))
        self.assertEqual(v.initial_value(), 2)

        # Initial value and equation for a non-state
        b = ('    <apply>'
             '      <eq /><ci>x</ci><cn cellml:units="dimensionless">2</cn>'
             '    </apply>')
        self.assertBad(x + b + z, 'Initial value and a defining equation')

        # Two equations
        self.assertBad(x + a + a + z, 'Two defining equations')

    def test_oxmeta_annotations(self):
        # Tests parsing of RDF annotations for the Web Lab

        # Start and end of required tags
        r1 = '<rdf:RDF>'
        r2 = '</rdf:RDF>'
        d1a = '<rdf:Description rdf:about="#'
        d1b = '">'
        d2 = '</rdf:Description>'
        b1 = '<bqbiol:is rdf:resource="' + cellml.NS_OXMETA
        b2 = '"/>'

        # Create mini model with 2 rdf tags and 3 annotations
        x = ('<component name="a">'
             '  <variable name="x" units="volt" cmeta:id="x"'
             '            initial_value="1" />'
             '  <variable name="y" units="volt" cmeta:id="yzie"'
             '            initial_value="1" />'
             '  <variable name="z" units="volt" cmeta:id="zed"'
             '            initial_value="1" />'
             '</component>')
        y = r1
        y += d1a + 'x' + d1b + b1 + 'membrane_voltage' + b2 + d2
        y += d1a + 'yzie' + d1b + b1 + 'sodium_reversal_potential' + b2 + d2
        y += r2
        y += r1
        y += d1a + 'zed' + d1b + b1 + 'calcium_reversal_potential' + b2 + d2
        y += r2

        # Parse
        cm = self.parse(x + y)

        # Check cmeta ids
        x, y, z = cm['a']['x'], cm['a']['y'], cm['a']['z']
        self.assertEqual(x.cmeta_id(), 'x')
        self.assertEqual(y.cmeta_id(), 'yzie')
        self.assertEqual(z.cmeta_id(), 'zed')

        # Check oxmeta annotation
        self.assertIn('oxmeta', x.meta)
        self.assertIn('oxmeta', y.meta)
        self.assertIn('oxmeta', z.meta)
        self.assertEqual(x.meta['oxmeta'], 'membrane_voltage')
        self.assertEqual(y.meta['oxmeta'], 'sodium_reversal_potential')
        self.assertEqual(z.meta['oxmeta'], 'calcium_reversal_potential')

    def test_oxmeta_annotations_bad(self):
        # Tests parsing of RDF annotations for the Web Lab

        # Start and end of required tags
        r1 = '<rdf:RDF>'
        r2 = '</rdf:RDF>'
        d1a = '<rdf:Description rdf:about="#'
        d1b = '">'
        d2 = '</rdf:Description>'
        b1 = '<bqbiol:is rdf:resource="' + cellml.NS_OXMETA
        b2 = '"/>'

        # Model code
        x = ('<component name="a">'
             '  <variable name="x" units="volt" cmeta:id="x"'
             '            initial_value="1" />'
             '</component>')

        # Check that parser survives all kinds of half-formed annotations

        # No content
        y = r1 + r2
        cm = self.parse(x + y)

        # No about attribute
        y = r1 + '<rdf:Description />' + r2
        cm = self.parse(x + y)

        # Unknown cmeta id
        y = r1 + d1a + 'xxx' + d1b + d2 + r2
        cm = self.parse(x + y)

        # No bqbiol:is
        y = r1 + d1a + 'x' + d1b + d2 + r2
        cm = self.parse(x + y)

        # No bqbiol:is
        y = r1 + d1a + 'x' + d1b + d2 + r2
        cm = self.parse(x + y)

        # No resource
        y = r1 + d1a + 'x' + d1b + '<bqbiol:is/>' + d2 + r2
        cm = self.parse(x + y)

        # Non oxmeta-resource
        y = r1 + d1a + 'x' + d1b + '<bqbiol:is rdf:resource="hi"/>' + d2 + r2
        cm = self.parse(x + y)

    def test_parse_file(self):
        # Tests the parse file method

        # Parse a valid file
        m = self.parse_in_file('<component name="a" />')
        self.assertIn('a', m)

        # Parse invalid XML: errors must be wrapped
        self.assertRaisesRegex(
            v1.CellMLParsingError,
            'Unable to parse XML',
            self.parse_in_file,
            '<component',
        )

    def test_parse_string(self):
        # Tests the parse string method

        # Valid version is already tested

        # Parse invalid XML: errors must be wrapped
        self.assertRaisesRegex(
            v1.CellMLParsingError,
            'Unable to parse XML',
            v1.parse_string,
            'Hello there',
        )

    def test_rdf(self):
        # rdf:RDF is allowed, but no other elements or attributes

        # rdf:RDF is ok
        self.parse('<rdf:RDF />')

        # Attribute from rdf namespace
        self.assertBad(
            '<component name="c" rdf:RDF="d" />',
            'Unexpected attribute rdf:RDF')

        # Element from rdf namespace
        self.assertBad(
            '<rdf:robert />',
            'found element of type rdf:robert')

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

        # Zero offsets are OK
        x = ('<units name="wooster">'
             '  <unit units="volt" offset="0.0" />'
             '</units>')
        m = self.parse(x)
        self.assertEqual(
            m.find_units('wooster').myokit_unit(), myokit.units.volt)

        # Non-zero offsets are not supported: treated as dimensionless
        x = ('<units name="nonzero">'
             '  <unit units="meter" />'
             '  <unit units="volt" offset="0.1" />'
             '</units>')
        with WarningCollector() as w:
            m = self.parse(x)
        self.assertIn('non-zero offsets are not supported', w.text())
        self.assertEqual(
            myokit.units.dimensionless, m.find_units('nonzero').myokit_unit())

        # Non-integer exponents are supported
        x = ('<units name="unsup">'
             '  <unit units="ampere" exponent="2.34" />'
             '</units>')
        m = self.parse(x)
        self.assertEqual(
            m.find_units('unsup').myokit_unit(),
            myokit.units.ampere**2.34,
        )

        # Offset must be a number
        x = ('<units name="wooster">'
             '  <unit units="volt" offset="hello" />'
             '</units>')
        self.assertBad(x, 'must be a real number')

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

        # Unsupported base units raise a warning, are treated as dimensionless
        x = ('<units name="wooster">'
             '  <unit units="meter" />'
             '  <unit units="celsius" />'
             '</units>')
        with WarningCollector() as w:
            m = self.parse(x)
        self.assertIn('celsius', w.text())
        self.assertEqual(
            myokit.units.dimensionless, m.find_units('wooster').myokit_unit())

    def test_units(self):
        # Test parsing a units definition

        # Valid has already been testsed

        # Base units attribute is allowed be no
        x = ('<units name="wooster" base_units="no">'
             '  <unit units="volt" />'
             '</units>')
        m = self.parse(x)
        self.assertEqual(
            m.find_units('wooster').myokit_unit(), myokit.units.volt)

        # Base units attribute must be yes or no
        x = ('<units name="wooster" base_units="bjork">'
             '  <unit units="volt" offset="0.0" />'
             '</units>')
        self.assertBad(x, 'must be either "yes" or "no"')

        # New base units are not supported
        x = '<units name="base" base_units="yes" />'
        with WarningCollector() as w:
            m = self.parse(x)
        self.assertIn('new base unit', w.text())
        self.assertEqual(
            m.find_units('base').myokit_unit(), myokit.units.dimensionless)

        # CellML errors are converted to parse errors
        x = '<units name="123"><unit units="volt" /></units>'
        self.assertBad(x, 'valid CellML identifier')

        # Missing name
        x = '<units><unit units="volt" /></units>'
        self.assertBad(x, 'must have a name')

        # Name overlaps with predefined
        x = '<units name="meter"><unit units="volt" /></units>'
        self.assertBad(x, 'overlaps with a predefined name')

        # Same error for celsius (unsupported units)
        x = '<units name="meter"><unit units="celsius" /></units>'
        self.assertBad(x, 'overlaps with a predefined name')

        # Duplicate name (handled in sorting)
        x = '<units name="wooster"><unit units="volt" /></units>'
        self.assertBad(x + x, 'Duplicate units definition')

        # No child unit elements
        x = '<units name="woopster" />'
        self.assertBad(x, 'at least one child unit element')

        # Missing units definitions
        x = ('<units name="wooster"><unit units="fluther" /></units>')
        self.assertBad(x, 'Unable to resolve network of units')

        # Circular units definitions
        x = ('<units name="wooster"><unit units="fluther" /></units>'
             '<units name="fluther"><unit units="wooster" /></units>')
        self.assertBad(x, 'Unable to resolve network of units')

        # Test unit resolving for shadowed units
        x = ('<units name="wooster"><unit units="ampere" /></units>'
             '<component name="a">'
             '  <units name="kilowooster">'
             '    <unit units="wooster" prefix="kilo" />'
             '  </units>'
             '  <units name="wooster"><unit units="volt" /></units>'
             '</component>')
        m = self.parse(x)
        u = m['a'].find_units('kilowooster').myokit_unit()
        self.assertEqual(u, myokit.units.volt * 1000)

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
        self.assertEqual(u('liter'), myokit.units.liter)
        self.assertEqual(u('litre'), myokit.units.liter)
        self.assertEqual(u('lumen'), myokit.units.lumen)
        self.assertEqual(u('lux'), myokit.units.lux)
        self.assertEqual(u('meter'), myokit.units.meter)
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

        # Celsius is not supported
        with WarningCollector() as w:
            self.assertEqual(u('celsius'), myokit.units.dimensionless)
        self.assertIn('celsius', w.text())

    def test_variable(self):
        # Tests parsing variables

        # Valid has already been tested

        # Must have a name
        x = '<component name="a"><variable units="volt"/></component>'
        self.assertBad(x, 'must have a name attribute')

        # Must have units
        x = '<component name="a"><variable name="a" /></component>'
        self.assertBad(x, 'must have a units attribute')

        # CellML errors are converted to parsing errors
        x = '<component name="a"><variable name="1" units="volt"/></component>'
        self.assertBad(x, 'valid CellML identifier')

        # Unsupported units are ignored
        x = '<variable name="x" units="celsius" initial_value="3" />'
        x = '<component name="a">' + x + '</component>'
        with WarningCollector() as w:
            x = self.parse(x)['a']['x']
        self.assertIn('celsius', w.text())

        self.assertEqual(x.units().myokit_unit(), myokit.units.dimensionless)


if __name__ == '__main__':
    import warnings
    warnings.simplefilter('always')
    unittest.main()
