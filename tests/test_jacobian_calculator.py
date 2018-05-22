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


if __name__ == '__main__':
    unittest.main()
