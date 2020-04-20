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
        Test Hodgkin Huxley model.
        """
        i = formats.importer('sbml')
        cls.hohu = i.model(os.path.join(
            DIR_FORMATS, 'sbml', 'HodgkinHuxley.xml'))

    def test_capability_reporting(self):
        """ Test if the right capabilities are reported. """
        i = formats.importer('sbml')
        self.assertFalse(i.supports_component())
        self.assertTrue(i.supports_model())
        self.assertFalse(i.supports_protocol())

    def test_model(self):
        i = formats.importer('sbml')

        def sbml(fname):
            m = i.model(os.path.join(DIR_FORMATS, 'sbml', fname))
            try:
                m.validate()
            except myokit.MissingTimeVariableError:
                # SBML models don't specify the time variable
                pass

        # Basic Hodgkin-Huxley
        sbml('HodgkinHuxley.xml')

        # Same but without a model name
        sbml('HodgkinHuxley-no-model-name-but-id.xml')
        sbml('HodgkinHuxley-no-model-name-or-id.xml')

        # Same but with funny variable names
        sbml('HodgkinHuxley-funny-names.xml')

        # Model with listOfInitialValues and unit with multiplier
        sbml('Noble1962-initial-assignments-and-weird-unit.xml')

    def test_parameters(self):
        # Test Case: Hodkin Huxley
        # expected
        parameters = [
            'V',
            'V_neg',
            'E',
            'I',
            'i_Na',
            'i_K',
            'i_L',
            'm',
            'h',
            'n',
            'E_R',
            'Cm',
            'g_Na',
            'g_K',
            'g_L',
            'E_Na',
            'E_K',
            'E_L',
            'V_Na',
            'V_K',
            'V_L',
            'alpha_m',
            'beta_m',
            'alpha_h',
            'beta_h',
            'alpha_n',
            'beta_n'
        ]

        # test whether parameters are in myokit model
        for param in parameters:
            self.assertTrue(self.hohu.has_variable('sbml.' + param))

    def test_units(self):
        # Test Case: Hodkin Huxley
        # expected
        param_unit_dict = {
            'V': myokit.units.V * 10 ** (-3),
            'V_neg': myokit.units.V * 10 ** (-3),
            'E': myokit.units.V * 10 ** (-3),
            'I': None,
            'i_Na': None,
            'i_K': None,
            'i_L': None,
            'm': None,
            'h': None,
            'n': None,
            'E_R': myokit.units.V * 10 ** (-3),
            'Cm': None,
            'g_Na': None,
            'g_K': None,
            'g_L': None,
            'E_Na': myokit.units.V * 10 ** (-3),
            'E_K': myokit.units.V * 10 ** (-3),
            'E_L': myokit.units.V * 10 ** (-3),
            'V_Na': myokit.units.V * 10 ** (-3),
            'V_K': myokit.units.V * 10 ** (-3),
            'V_L': myokit.units.V * 10 ** (-3),
            'alpha_m': None,
            'beta_m': None,
            'alpha_h': None,
            'beta_h': None,
            'alpha_n': None,
            'beta_n': None
        }

        # test whether parameters have correct units
        for param in param_unit_dict:
            unit = param_unit_dict[param]
            self.assertEqual(unit, self.hohu.get('sbml.' + param).unit())

    def test_initial_values(self):
        # Test Case: Hodkin Huxley
        # expected
        param_value_dict = {
            'I': 0,
            'E_R': -75,
            'Cm': 1,
            'g_Na': 120,
            'g_K': 36,
            'g_L': 0.3,
            'E_Na': -190,
            'E_K': -63,
            'E_L': -85.613
        }

        # test whether parameters have correct initial values
        for param in param_value_dict:
            value = param_value_dict[param]
            self.assertEqual(value, self.hohu.get('sbml.' + param).value())

    def test_intermediate_expressions(self):
        # Test Case: Hodkin Huxley
        # expected
        param_expr_dict = {
            'V_neg': '-sbml.V',
            'E': 'sbml.V + sbml.E_R',
            'i_Na': 'sbml.g_Na * sbml.m ^ 3 * sbml.h * (sbml.V - sbml.V_Na)',
            'i_K': 'sbml.g_K * sbml.n ^ 4 * (sbml.V - sbml.V_K)',
            'i_L': 'sbml.g_L * (sbml.V - sbml.V_L)',
            'V_Na': 'sbml.E_Na - sbml.E_R',
            'V_K': 'sbml.E_K - sbml.E_R',
            'V_L': 'sbml.E_L - sbml.E_R',
            'alpha_m':
            '0.1 * (sbml.V + 25) / (exp((sbml.V + 25) / 10) - 1)',
            'beta_m': '4 * exp(sbml.V / 18)',
            'alpha_h': '0.07 * exp(sbml.V / 20)',
            'beta_h': '1 / (exp((sbml.V + 30) / 10) + 1)',
            'alpha_n': '0.01 * (sbml.V + 10) / (exp((sbml.V + 10) / 10) - 1)',
            'beta_n': '0.125 * exp(sbml.V / 80)'
        }

        # test whether intermediate expressions are correct
        for param in param_expr_dict:
            expr = param_expr_dict[param]
            self.assertEqual(
                'sbml.' + param, str(self.hohu.get('sbml.' + param).lhs()))
            self.assertEqual(expr, str(self.hohu.get('sbml.' + param).rhs()))

    def test_state_expressions(self):
        # Test Case: Hodkin Huxley
        # expected
        param_expr_dict = {
            'm': 'sbml.alpha_m * (1 - sbml.m) - sbml.beta_m * sbml.m',
            'h': 'sbml.alpha_h * (1 - sbml.h) - sbml.beta_h * sbml.h',
            'n': 'sbml.alpha_n * (1 - sbml.n) - sbml.beta_n * sbml.n'
        }

        # test whether state expressions are correct
        for param in param_expr_dict:
            expr = param_expr_dict[param]
            self.assertEqual(
                'dot(sbml.%s)' % param,
                str(self.hohu.get('sbml.' + param).lhs()))
            self.assertEqual(expr, str(self.hohu.get('sbml.' + param).rhs()))

    def test_info(self):
        i = formats.importer('sbml')
        self.assertIsInstance(i.info(), basestring)


if __name__ == '__main__':
    unittest.main()
