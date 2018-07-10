#!/usr/bin/env python
#
# Tests the Jacobian calculator.
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import os
import unittest
import numpy as np

import myokit

from shared import DIR_DATA


class JacobianCalculatorTest(unittest.TestCase):
    """
    Tests the JacobianCalculator.
    """
    def test_simple(self):
        # Load model
        m = os.path.join(DIR_DATA, 'lr-1991.mmt')
        m, p, x = myokit.load(m)

        # Run a simple simulation
        c = myokit.JacobianCalculator(m)
        x, f, j, e = c.newton_root(damping=0.01, max_iter=50)

        # Test if still works with initial x all zero (Enno's bug)
        x = np.array(m.state()) * 0
        x, f, j, e = c.newton_root(x, damping=0.01, max_iter=50)

        # Test if still works with a single zero
        x = np.array(m.state())
        x[0] = 0
        x, f, j, e = c.newton_root(x, damping=0.01, max_iter=50)

        # Test quick return
        x = np.array(m.state())
        x[0] = 0
        x2, f, j, e = c.newton_root(damping=0.01, max_iter=1)
        self.assertTrue(np.sum((x2 - x)**2) > 10)

        # Invalid damping value
        self.assertRaisesRegexp(
            ValueError, 'Damping', c.newton_root, damping=0)
        self.assertRaisesRegexp(
            ValueError, 'Damping', c.newton_root, damping=1.1)

        # Missing a state
        x = m.state()[:-1]
        self.assertRaisesRegexp(
            ValueError, 'must have length', c.calculate, x)

        # Non-numbers in state
        x = m.state()
        x[0] = 'Hello'
        self.assertRaisesRegexp(
            ValueError, 'floats', c.calculate, x)


if __name__ == '__main__':
    unittest.main()
