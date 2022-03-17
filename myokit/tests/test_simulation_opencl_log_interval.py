#!/usr/bin/env python3
#
# Tests the OpenCL simulation classes' interpretation of log_interval
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

from myokit.tests import OpenCL_FOUND, DIR_DATA, WarningCollector
from myokit.tests.test_simulation_log_interval import PeriodicTest

debug = False


@unittest.skipIf(not OpenCL_FOUND, 'OpenCL not found on this system.')
class SimulationOpenCLTest(PeriodicTest):
    """
    Tests myokit.SimulationOpenCL for consistent log entry timing.
    """
    def test_periodic(self):
        # Test periodic logging.

        m, p, x = myokit.load(os.path.join(DIR_DATA, 'lr-1991.mmt'))
        s = myokit.SimulationOpenCL(m, p, ncells=1)
        self.periodic(s)


@unittest.skipIf(not OpenCL_FOUND, 'OpenCL not found on this system.')
class FiberTissueSimulationTest(unittest.TestCase):
    """
    Tests myokit.FiberTissueSimulation for consistent log entry timing.
    """
    def test_periodic(self):
        # Test periodic logging.

        m, p, x = myokit.load(os.path.join(DIR_DATA, 'lr-1991.mmt'))
        with WarningCollector():
            s = myokit.FiberTissueSimulation(
                m, m, p, ncells_fiber=(1, 1), ncells_tissue=(1, 1))

        # Set tolerance for equality testing
        emax = 1e-2  # Time steps for logging are approximate

        # Test 1: Simple 5 ms simulation, log_interval 0.5 ms
        d, e = s.run(
            5, logf=['engine.time'], logt=myokit.LOG_NONE, log_interval=0.5)
        d = d.npview()
        t = d['engine.time']
        q = np.arange(0, 5, 0.5)
        if debug:
            print(t)
            print(q)
            print('- ' * 10)
        self.assertEqual(len(t), len(q))
        self.assertTrue(np.max(np.abs(t - q)) < emax)

        # Test 2: Very short simulation
        s.reset()
        d, e = s.run(
            1, logf=['engine.time'], logt=myokit.LOG_NONE, log_interval=0.5)
        d = d.npview()
        t = d['engine.time']
        q = np.arange(0, 1, 0.5)
        if debug:
            print(t)
            print(q)
            print('- ' * 10)
        self.assertEqual(len(t), len(q))
        self.assertTrue(np.max(np.abs(t - q)) < emax)

        # Test 3: Stop and start a simulation
        s.reset()
        d, e = s.run(
            1, logf=['engine.time'], logt=myokit.LOG_NONE, log_interval=0.5)
        d, e = s.run(2, logf=d, logt=myokit.LOG_NONE, log_interval=0.5)
        d, e = s.run(2, logf=d, logt=myokit.LOG_NONE, log_interval=0.5)
        d = d.npview()
        t = d['engine.time']
        q = np.arange(0, 5, 0.5)
        if debug:
            print(t)
            print(q)
            print('- ' * 10)
        self.assertEqual(len(t), len(q))
        self.assertTrue(np.max(np.abs(t - q)) < emax)


if __name__ == '__main__':
    print('Add -v for more debug output')
    import sys
    if '-v' in sys.argv:
        debug = True
    unittest.main()
