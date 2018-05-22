#!/usr/bin/env python
#
# Tests the ICSimulation class.
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


class ICSimulationTest(unittest.TestCase):
    """
    Tests the :class:`ICSimulation`.
    """
    def test_simple(self):
        # Load model
        m = os.path.join(DIR_DATA, 'lr-1991.mmt')
        m, p, x = myokit.load(m)

        # Run a simulation
        s = myokit.ICSimulation(m, p)
        d, e = s.run(20, log_interval=5)

        # Create a datablock from the simulation log
        b = s.block(d, e)
        del(d, e)

        # Calculate eigenvalues
        b.eigenvalues('derivatives')


if __name__ == '__main__':
    unittest.main()
