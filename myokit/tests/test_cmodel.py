#!/usr/bin/env python3
#
# Tests the CModel class.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import os
import unittest

import myokit

from myokit.tests import DIR_DATA

# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp


class CModelTest(unittest.TestCase):
    """
    Tests the CModel class.
    """

    @classmethod
    def setUpClass(cls):
        # Test cmodel instantiation.
        m, p, x = myokit.load(os.path.join(DIR_DATA, 'lr-1991.mmt'))
        cls.model = m
        cls.sensitivities = (['ik1.gK1', 'ikp.IKp'], ['cell.K_o', 'ikp.gKp'])
        cls.cmodel = myokit.CModel(cls.model, cls.sensitivities)

    def test_sensitivities(self):
        # Test instantiation of cmodel with sensitivities

        # Bad type
        sens = 'Bad type'
        with self.assertRaisesRegex(ValueError, 'The argument `sensitivities'):
            myokit.CModel(self.model, sens)

        # Empty deps or indeps
        sens = ([], ['some parameter'])
        m = myokit.CModel(self.model, sens)
        self.assertFalse(m.has_sensitivities)
        sens = (['some state'], [])
        m = myokit.CModel(self.model, sens)
        self.assertFalse(m.has_sensitivities)

        # Provide sensitivies as Variables
        s1 = self.model.get('ik1.gK1')
        s2 = self.model.get('ikp.IKp')
        p1 = self.model.get('cell.K_o')
        p2 = self.model.get('ikp.gKp')
        sens = ([s1, s2], [p1, p2])
        m = myokit.CModel(self.model, sens)
        self.assertTrue(m.has_sensitivities)

        # Provide sensitivities as Names
        sens = (
            [myokit.Name(s1), myokit.Name(s2)],
            [myokit.Name(p1), myokit.Name(p2)])
        m = myokit.CModel(self.model, sens)
        self.assertTrue(m.has_sensitivities)

        # Sensitivity of derivative
        s3 = self.model.get('ik.x')
        sens = (
            [myokit.Derivative(myokit.Name(s3)), myokit.Name(s2)],
            [myokit.Name(p1), myokit.Name(p2)])
        m = myokit.CModel(self.model, sens)
        self.assertTrue(m.has_sensitivities)
        s3 = 'dot(ik.x)'
        sens = (
            [s3, myokit.Name(s2)],
            [myokit.Name(p1), myokit.Name(p2)])
        m = myokit.CModel(self.model, sens)
        self.assertTrue(m.has_sensitivities)

        # Sensitivity of derivative of non-state
        sens = (
            [myokit.Derivative(myokit.Name(s1)), myokit.Name(s2)],
            [myokit.Name(p1), myokit.Name(p2)])
        with self.assertRaisesRegex(ValueError, 'Sensitivity of '):
            myokit.CModel(self.model, sens)

        # Sensitivity of bound variable
        sens = (
            ['engine.time', myokit.Name(s2)],
            [myokit.Name(p1), myokit.Name(p2)])
        with self.assertRaisesRegex(ValueError, 'Sensitivities cannot'):
            myokit.CModel(self.model, sens)

        # Sensitivity w.r.t. Initial value
        s3 = self.model.get('ik.x')
        sens = (
            [s3, myokit.Name(s2)],
            [myokit.Name(p1), myokit.InitialValue(myokit.Name(s3))])
        m = myokit.CModel(self.model, sens)
        self.assertTrue(m.has_sensitivities)

        # Sensitivity w.r.t. initial value of non-state
        sens = (
            [myokit.Name(s1), myokit.Name(s2)],
            [myokit.Name(p1), myokit.InitialValue(myokit.Name(p2))])
        with self.assertRaisesRegex(ValueError, 'Sensitivity with respect to'):
            myokit.CModel(self.model, sens)

        # Sensitivity w.r.t. non-literal
        sens = (
            [myokit.Name(s1), myokit.Name(s2)],
            [myokit.Name(p1), 'ik.E'])
        with self.assertRaisesRegex(ValueError, 'Sensitivity with respect to'):
            myokit.CModel(self.model, sens)


if __name__ == '__main__':
    unittest.main()
