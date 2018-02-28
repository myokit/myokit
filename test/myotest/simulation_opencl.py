#!/usr/bin/env python2
#
# Tests the main simulation classes
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


def suite():
    """
    Returns a test suite with all tests in this module
    """
    suite = unittest.TestSuite()
    # Simulation
    suite.addTest(SimulationOpenCL1d('set_state'))
    suite.addTest(SimulationOpenCL1d('sim'))
    suite.addTest(SimulationOpenCL2d('sim'))
    suite.addTest(FiberTissueSimulation('run_simple'))
    # Done!
    return suite


class SimulationOpenCL1d(unittest.TestCase):
    """
    Tests the OpenCL simulation in 1d mode.
    """
    def set_state(self):
        m, p, x = myokit.load('example')
        n = 10
        s = myokit.SimulationOpenCL(m, p, n)
        sm = m.state()
        ss = [s.state(x) for x in xrange(n)]
        for si in ss:
            self.assertEqual(sm, si)
        # Test setting a single, global state
        sx = [0.0] * 8
        self.assertNotEqual(sm, sx)
        s.set_state(sx)
        for i in xrange(n):
            self.assertEqual(sx, s.state(i))
        self.assertEqual(sx * n, s.state())
        s.set_state(sm)
        self.assertEqual(sm * n, s.state())
        # Test setting a single state
        j = 1
        s.set_state(sx, j)
        for i in xrange(n):
            if i == j:
                self.assertEqual(s.state(i), sx)
            else:
                self.assertEqual(s.state(i), sm)

    def sim(self):
        m, p, x = myokit.load('example')
        s = myokit.SimulationOpenCL(m, p, 20)
        s.run(1, log=['engine.time', 'membrane.V'])


class SimulationOpenCL2d(unittest.TestCase):
    """
    Tests the OpenCL simulation in 2d mode.
    """
    def sim(self):
        m, p, x = myokit.load('example')
        n = (8, 8)
        s = myokit.SimulationOpenCL(m, p, n)
        s.set_paced_cells(4, 4)
        s.run(1, log=['engine.time', 'membrane.V'])


class FiberTissueSimulation(unittest.TestCase):
    """
    Tests the fiber-tissue simulation.
    """
    def run_simple(self):
        # Load models
        mf = os.path.join(myotest.DIR_DATA, 'dn-1985-normalised.mmt')
        mt = os.path.join(myotest.DIR_DATA, 'lr-1991.mmt')
        mf = myokit.load_model(mf)
        mt = myokit.load_model(mt)
        # Run times
        run = .1
        # Create pacing protocol
        p = myokit.pacing.blocktrain(1000, 2.0, offset=.01)
        # Fiber/Tissue sizes
        nfx = 8
        nfy = 4
        ntx = 8
        nty = 8
        # Create simulation
        s = myokit.FiberTissueSimulation(
            mf,
            mt,
            p,
            ncells_fiber=(nfx, nfy),
            ncells_tissue=(ntx, nty),
            nx_paced=10,
            g_fiber=(235, 100),
            g_tissue=(9, 5),
            g_fiber_tissue=9
        )
        s.set_step_size(0.0012)
        # Set up logging
        logf = [
            'engine.time',
            'membrane.V',
            'isi.isiCa',
        ]
        logt = [
            'membrane.V',
            'ica.Ca_i',
            'ica.ICa',
        ]
        # Run simulation
        with myokit.PyCapture():
            logf, logt = s.run(run, logf=logf, logt=logt, log_interval=0.01)

