#!/usr/bin/env python3
#
# Tests the CModel class.
#
# This file is part of Myokit.
# See https://github.com/myokit/myokit for copyright, sharing, and licensing.
#
import unittest

from shared import DIR_DATA

import myokit


class CModelTest(unittest.TestCase):
    """
    Tests the CModel class.
    """

    @classmethod
    def setUpClass(cls):
        # Test cmodel instantiation.
        m, p, x = myokit.load(DIR_DATA / 'beeler-1977.mmt')
        cls.model = m
        cls.sensitivities = (['ina.INa', 'is.Is'], ['ina.ENa', 'is.gs'])
        cls.pacing_labels = {}
        cls.cmodel = myokit.CModel(
            cls.model, cls.pacing_labels, cls.sensitivities
        )

    def test_sensitivities(self):
        # Test instantiation of cmodel with sensitivities

        # Bad type
        sens = 'Bad type'
        with self.assertRaisesRegex(ValueError, 'argument "sensitivities"'):
            myokit.CModel(self.model, self.pacing_labels, sens)

        # Empty deps or indeps
        sens = ([], ['some parameter'])
        m = myokit.CModel(self.model, self.pacing_labels, sens)
        self.assertFalse(m.has_sensitivities)
        sens = (['some state'], [])
        m = myokit.CModel(self.model, self.pacing_labels, sens)
        self.assertFalse(m.has_sensitivities)

        # Provide sensitivities as Variables
        s1 = self.model.get('ina.INa')
        s2 = self.model.get('is.Is')
        p1 = self.model.get('ina.ENa')
        p2 = self.model.get('is.gs')
        sens = ([s1, s2], [p1, p2])
        m = myokit.CModel(self.model, self.pacing_labels, sens)
        self.assertTrue(m.has_sensitivities)

        # Provide sensitivities as Names
        sens = (
            [myokit.Name(s1), myokit.Name(s2)],
            [myokit.Name(p1), myokit.Name(p2)])
        m = myokit.CModel(self.model, self.pacing_labels, sens)
        self.assertTrue(m.has_sensitivities)

        # Sensitivity of derivative
        s3 = self.model.get('ix1.x1')
        sens = (
            [myokit.Derivative(myokit.Name(s3)), myokit.Name(s2)],
            [myokit.Name(p1), myokit.Name(p2)])
        m = myokit.CModel(self.model, self.pacing_labels, sens)
        self.assertTrue(m.has_sensitivities)
        s3 = 'dot(ix1.x1)'
        sens = (
            [s3, myokit.Name(s2)],
            [myokit.Name(p1), myokit.Name(p2)])
        m = myokit.CModel(self.model, self.pacing_labels, sens)
        self.assertTrue(m.has_sensitivities)

        # Sensitivity of derivative of non-state
        sens = (
            [myokit.Derivative(myokit.Name(s1)), myokit.Name(s2)],
            [myokit.Name(p1), myokit.Name(p2)])
        with self.assertRaisesRegex(ValueError, 'Sensitivity of '):
            myokit.CModel(self.model, self.pacing_labels, sens)

        # Sensitivity of bound variable
        sens = (
            ['engine.time', myokit.Name(s2)],
            [myokit.Name(p1), myokit.Name(p2)])
        with self.assertRaisesRegex(ValueError, 'Sensitivities cannot'):
            myokit.CModel(self.model, self.pacing_labels, sens)

        # Sensitivity w.r.t. Initial value
        s3 = self.model.get('ix1.x1')
        sens = (
            [s3, myokit.Name(s2)],
            [myokit.Name(p1), myokit.InitialValue(myokit.Name(s3))])
        m = myokit.CModel(self.model, self.pacing_labels, sens)
        self.assertTrue(m.has_sensitivities)

        # Sensitivity w.r.t. initial value of non-state
        sens = (
            [myokit.Name(s1), myokit.Name(s2)],
            [myokit.Name(p1), myokit.InitialValue(myokit.Name(p2))])
        with self.assertRaisesRegex(ValueError, 'Sensitivity with respect to'):
            myokit.CModel(self.model, self.pacing_labels, sens)

        # Sensitivity w.r.t. non-literal
        sens = (
            [myokit.Name(s1), myokit.Name(s2)],
            [myokit.Name(p1), 'is.Es'])
        with self.assertRaisesRegex(ValueError, 'Sensitivity with respect to'):
            myokit.CModel(self.model, self.pacing_labels, sens)


if __name__ == '__main__':
    unittest.main()
