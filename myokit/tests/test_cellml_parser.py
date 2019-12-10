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

    def assertFail(self, message, name):
        """
        Tests parsing the file with the given ``name`` raises a parsing
        exception that matches ``message``.
        """
        self.assertRaisesRegex(
            parser.CellMLParsingError,
            message,
            parser.parse_file,
            os.path.join(DIR, 'invalid', name + '.cellml'))

    def test_cmeta_ids(self):
        # Test cmeta ids are parsed

        # Test parsing cmeta id
        path = os.path.join(DIR, 'br-1977.cellml')
        model = parser.parse_file(path)
        self.assertEqual(model.cmeta_id(), 'beeler_reuter_1977')

        # Invalid cmeta id
        self.assertFail('non-empty string', 'cmeta_id_empty')
        # Duplicate cmeta id
        self.assertFail('Duplicate cmeta:id', '8.4.1.cmeta_id_duplicate')

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

    def test_text_in_elements(self):
        # Test for text inside elements

        self.assertFail(
            'Text found in cellml:connection', '2.4.4.text_in_connection')
        self.assertFail('Text found in cellml:units', '2.4.4.text_in_units_2')

    def test_unexpected(self):
        # Test for unexpected elements and attributes

        self.assertFail('Unexpected content type', '2.4.2.imaginary_elements')
        self.assertFail('Unexpected attribute', '2.4.2.imaginary_attributes_1')

        # CellML inside extension
        self.assertFail(
            'found inside extension element',
            '2.4.3.cellml_elements_inside_extensions')


if __name__ == '__main__':
    unittest.main()
