#!/usr/bin/env python
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
import myokit.formats.cellml.parser_1 as parser

from shared import DIR_FORMATS

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

    '''
    def assertBadFile(self, message, name):
        """
        Tests parsing the file with the given ``name`` raises a parsing
        exception that matches ``message``.
        """
        self.assertRaisesRegex(
            parser.CellMLParsingError,
            message,
            parser.parse_file,
            os.path.join(DIR, 'invalid', name + '.cellml'))
    '''

    def assertBad(self, xml, message):
        """
        Inserts the given ``xml`` into a <model> element, parses it, and checks
        that this raises an exception matching ``message``.
        """
        self.assertRaisesRegex(
            parser.CellMLParsingError, message, self.parse, xml)

    def parse(self, xml):
        """
        Inserts the given ``xml`` into a <model> element, parses it, and
        returns the result.
        """
        return parser.parse_string(
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<model name="test"'
            '       xmlns="http://www.cellml.org/cellml/1.0#"'
            '       xmlns:cmeta="http://www.cellml.org/metadata/1.0#">'
            + xml +
            '</model>')

    def test_cmeta_ids(self):
        # Test cmeta ids are parsed

        # Test parsing cmeta id
        path = os.path.join(DIR, 'br-1977.cellml')
        model = parser.parse_file(path)
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

    def test_component(self):
        # Test component parsing

        # Parse component
        m = self.parse('<component name="ernie" />')
        self.assertIn('ernie', m)

        # Component must have name
        self.assertBad('<component />', 'Component element must have a name')

        # CellML errors are passed through
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
             '  <variable name="y" units="volt" public_interface="out" />'
             '</component>'
        )

        # Parse valid connection
        y = ('<connection>'
             '  <map_components component_1="a" component_2="b" />'
             '  <map_variables variable_1="x" variable_2="y" />'
             '</connection>')
        m = self.parse(x + y)
        self.assertEqual(m['a']['x'].source(), m['b']['y'])
        self.assertEqual(m['b']['y'].source(), m['b']['y'])

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
             '</component>'
        )

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

    def test_evaluated_derivatives(self):
        # Test parsing a simple model; compare RHS derivatives to known ones

        # Load myokit model
        org_model = myokit.load_model('example')
        org_states = [x.qname() for x in org_model.states()]
        org_values = org_model.eval_state_derivatives()

        # Load exported version
        path = os.path.join(DIR, 'lr-1991-exported.cellml')
        cellml = parser.parse_file(path)
        new_model = cellml.myokit_model()
        new_states = [x.qname() for x in new_model.states()]
        new_values = new_model.eval_state_derivatives()

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

        # CellML inside extension is not allowed
        self.assertBad(
            '<x:y xmlns:x="xyz"><component name="c" /></x:y>',
            'found inside extension element')

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


if __name__ == '__main__':
    unittest.main()
