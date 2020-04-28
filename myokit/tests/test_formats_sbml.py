#!/usr/bin/env python3
#
# Tests the importer for SBML.
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

from shared import DIR_FORMATS

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


class SBMLTest(unittest.TestCase):
    """
    Test SBML import.
    """

    @classmethod
    def setUpClass(cls):
        """
        Tests case 00004 from the SBML test suite
        http://sbml.org/Facilities/Database/.
        """
        i = formats.importer('sbml')
        cls.modelFour = i.model(os.path.join(
            DIR_FORMATS, 'sbml', '00004-sbml-l3v2.xml'))

    def test_capability_reporting(self):
        """ Test if the right capabilities are reported. """
        i = formats.importer('sbml')
        self.assertFalse(i.supports_component())
        self.assertTrue(i.supports_model())
        self.assertFalse(i.supports_protocol())

    def test_model_name(self):
        """Tests whether model name is set properly."""
        name = 'case00004'
        self.assertEqual(self.modelFour.name(), name)

    def test_compartments(self):
        """
        Tests whether compartments have been imported properly. Compartments
        should include the compartments in the SBML file, plus a myokit
        compartment for the global parameters.
        """
        # compartment 1
        comp = 'compartment'
        self.assertTrue(self.modelFour.has_component(comp))

        # compartment 2
        comp = 'myokit'
        self.assertTrue(self.modelFour.has_component(comp))

        # total number of compartments
        number = 2
        self.assertEqual(self.modelFour.count_components(), number)

    def test_time(self):
        """Tests whether the time bound variable was set properly"""
        variable = 'time'
        self.assertTrue(self.modelFour.has_variable('myokit.' + variable))
        variable = self.modelFour.get('myokit.' + variable)
        self.assertTrue(variable.is_bound())

    def test_state_variables(self):
        """Tests whether all dynamic variables were imported properly."""
        # state 1
        state = 'S1'
        self.assertTrue(self.modelFour.has_variable('compartment.' + state))
        state = self.modelFour.get('compartment.' + state)
        self.assertTrue(state.is_state())

        # state 2
        state = 'S2'
        self.assertTrue(self.modelFour.has_variable('compartment.' + state))
        state = self.modelFour.get('compartment.' + state)
        self.assertTrue(state.is_state())

        # total number of states
        number = 2
        self.assertEqual(self.modelFour.count_variables(state=True), number)

    def test_constant_parameters(self):
        """
        Tests whether all constant parameters in the file were properly
        imported.
        """
        # parameter 1
        parameter = 'k1'
        self.assertTrue(self.modelFour.has_variable('myokit.' + parameter))
        parameter = self.modelFour.get('myokit.' + parameter)
        self.assertTrue(parameter.is_constant())

        # parameter 2
        parameter = 'k2'
        self.assertTrue(self.modelFour.has_variable('myokit.' + parameter))
        parameter = self.modelFour.get('myokit.' + parameter)
        self.assertTrue(parameter.is_constant())

        # parameter 3
        parameter = 'size'
        self.assertTrue(
            self.modelFour.has_variable('compartment.' + parameter))
        parameter = self.modelFour.get('compartment.' + parameter)
        self.assertTrue(parameter.is_constant())

        # total number of parameters
        number = 3
        self.assertEqual(self.modelFour.count_variables(const=True), number)

    def test_intermediate_parameters(self):
        """
        Tests whether all intermediate parameters in the file were properly
        imported.
        """
        # parameter 1
        parameter = 'S1_Concentration'
        self.assertTrue(
            self.modelFour.has_variable('compartment.' + parameter))
        parameter = self.modelFour.get('compartment.' + parameter)
        self.assertTrue(parameter.is_intermediary())

        # parameter 2
        parameter = 'S2_Concentration'
        self.assertTrue(
            self.modelFour.has_variable('compartment.' + parameter))
        parameter = self.modelFour.get('compartment.' + parameter)
        self.assertTrue(parameter.is_intermediary())

        # total number of parameters
        number = 2
        self.assertEqual(self.modelFour.count_variables(inter=True), number)

    def test_initial_values(self):
        """
        Tests whether initial values of constant parameters and state variables
        have been set properly.
        """
        # state 1
        state = 'S1'
        state = self.modelFour.get('compartment.' + state)
        initialValue = 0.15
        self.assertEqual(state.state_value(), initialValue)

        # state 2
        state = 'S2'
        state = self.modelFour.get('compartment.' + state)
        initialValue = 0
        self.assertEqual(state.state_value(), initialValue)

        # parameter 1
        parameter = 'k1'
        parameter = self.modelFour.get('myokit.' + parameter)
        initialValue = 0.35
        self.assertEqual(parameter.eval(), initialValue)

        # parameter 2
        parameter = 'k2'
        parameter = self.modelFour.get('myokit.' + parameter)
        initialValue = 180
        self.assertEqual(parameter.eval(), initialValue)

        # parameter 3
        parameter = 'size'
        parameter = self.modelFour.get('compartment.' + parameter)
        initialValue = 1
        self.assertEqual(parameter.eval(), initialValue)

    def test_rate_expressions(self):
        """
        Tests whether state variables have been assigned with the correct
        rate expression. Those may come from a rateRule or reaction.
        """
        # state 1
        state = 'S1'
        state = self.modelFour.get('compartment.' + state)
        expression = str(
            '-1 * (compartment.size * myokit.k1 * '
            + 'compartment.S1_Concentration) + compartment.size * myokit.k2'
            + ' * compartment.S2_Concentration ^ 2')
        self.assertEqual(str(state.rhs()), expression)

        # state 2
        state = 'S2'
        state = self.modelFour.get('compartment.' + state)
        expression = str(
            '2 * (compartment.size * myokit.k1 * '
            + 'compartment.S1_Concentration) - 2 * '
            + '(compartment.size * myokit.k2 '
            + '* compartment.S2_Concentration ^ 2)')
        self.assertEqual(str(state.rhs()), expression)

    def test_info(self):
        i = formats.importer('sbml')
        self.assertIsInstance(i.info(), basestring)


if __name__ == '__main__':
    unittest.main()
