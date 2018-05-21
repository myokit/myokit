#!/usr/bin/env python
#
# Tests the PSimulation class.
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


class PSimulation(unittest.TestCase):
    """
    Tests the PSimulation.
    """
    def test_simple(self):
        # Load model
        m = os.path.join(DIR_DATA, 'lr-1991.mmt')
        m, p, x = myokit.load(m)
        # Run a tiny simulation
        s = myokit.PSimulation(
            m, p, variables=['membrane.V'], parameters=['ina.gNa', 'ica.gCa'])
        s.set_step_size(0.002)
        d, dp = s.run(10, log_interval=2)


if __name__ == '__main__':
    unittest.main()
