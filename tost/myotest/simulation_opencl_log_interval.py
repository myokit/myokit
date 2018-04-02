#!/usr/bin/env python2
#
# Tests the OpenCL simulation classes' interpretation of log_interval
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
from __future__ import print_function
import myokit
import myotest
import os
import unittest
import numpy as np
from simulation_log_interval import PeriodicTest


DEBUG = False


def suite():
    """
    Returns a test suite with all tests in this module
    """
    suite = unittest.TestSuite()
    suite.addTest(SimulationOpenCL('periodic'))
    suite.addTest(FiberTissueSimulation('periodic'))
    return suite


class SimulationOpenCL(PeriodicTest):
    """
    Tests myokit.SimulationOpenCL for consistent log entry timing.
    """
    def sim_for_periodic(self):
        m, p, x = myokit.load(os.path.join(myotest.DIR_DATA, 'lr-1991.mmt'))
        return myokit.SimulationOpenCL(m, p, ncells=1)


class FiberTissueSimulation(unittest.TestCase):
    """
    Tests myokit.FiberTissueSimulation for consistent log entry timing.
    """
    def periodic(self):
        """
        Test periodic logging.
        """
        m, p, x = myokit.load(os.path.join(myotest.DIR_DATA, 'lr-1991.mmt'))
        s = myokit.FiberTissueSimulation(
            m, m, p, ncells_fiber=(1, 1), ncells_tissue=(1, 1))
        if DEBUG:
            print('= ' + s.__class__.__name__ + ' :: Periodic logging =')
        # Set tolerance for equality testing
        emax = 1e-2  # Time steps for logging are approximate
        # Test 1: Simple 5 ms simulation, log_interval 0.5 ms
        d, e = s.run(
            5, logf=['engine.time'], logt=myokit.LOG_NONE, log_interval=0.5)
        d = d.npview()
        t = d['engine.time']
        q = np.arange(0, 5, 0.5)
        if DEBUG:
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
        if DEBUG:
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
        if DEBUG:
            print(t)
            print(q)
            print('- ' * 10)
        self.assertEqual(len(t), len(q))
        self.assertTrue(np.max(np.abs(t - q)) < emax)
