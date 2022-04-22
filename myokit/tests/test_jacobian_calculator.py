#!/usr/bin/env python3
#
# Tests the Jacobian calculator.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import os
import unittest
import numpy as np

import myokit

from myokit.tests import DIR_DATA

# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp


class JacobianCalculatorTest(unittest.TestCase):
    """
    Tests the JacobianCalculator.
    """
    def test_simple(self):
        # Load model
        m = myokit.load_model(os.path.join(DIR_DATA, 'noble-1962.mmt'))

        # Run a simple simulation
        c = myokit.JacobianCalculator(m)
        x, f, j, e = c.newton_root(damping=0.01, max_iter=50)

        # Test if still runs with initial x all zero
        # (But does cause a linear algebra issue in this case)
        x = np.zeros(len(m.state()))
        c.newton_root(x, damping=0.01, max_iter=50)

        # Test if still works with a single zero (Enno's bug)
        x = np.array(m.state())
        x[1] = 0
        x, f, j, e = c.newton_root(x, damping=0.01, max_iter=50)

        # Test quick return
        x = np.array(m.state())
        x[0] = 0
        x2, f, j, e = c.newton_root(damping=0.01, max_iter=1)
        self.assertTrue(np.sum((x2 - x)**2) > 10)

        # Invalid damping value
        self.assertRaisesRegex(
            ValueError, 'Damping', c.newton_root, damping=0)
        self.assertRaisesRegex(
            ValueError, 'Damping', c.newton_root, damping=1.1)

        # Missing a state
        x = m.state()[:-1]
        self.assertRaisesRegex(
            ValueError, 'must have length', c.calculate, x)

        # Non-numbers in state
        x = m.state()
        x[0] = 'Hello'
        self.assertRaisesRegex(
            ValueError, 'floats', c.calculate, x)


if __name__ == '__main__':
    unittest.main()
