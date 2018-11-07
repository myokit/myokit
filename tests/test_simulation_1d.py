#!/usr/bin/env python
#
# Tests the Simulation1d class.
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

from shared import DIR_DATA, CancellingReporter

# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp


# Show simulation output
debug = False


class Simulation1dTest(unittest.TestCase):
    """
    Test the non-parallel 1d simulation.
    """
    '''
    def test_basic(self):
        # Test basic usage.

        # Load model
        m, p, _ = myokit.load(os.path.join(DIR_DATA, 'lr-1991.mmt'))

        # Run a simulation
        ncells = 5
        s = myokit.Simulation1d(m, p, ncells=ncells)

        self.assertEqual(s.time(), 0)
        self.assertEqual(s.state(0), m.state())
        self.assertEqual(s.default_state(0), m.state())
        d = s.run(5, log_interval=1)
        self.assertEqual(s.time(), 5)
        self.assertNotEqual(s.state(0), m.state())
        self.assertEqual(s.default_state(0), m.state())

        # Test full state getting and reset
        self.assertEqual(s.default_state(), m.state() * ncells)
        self.assertNotEqual(s.state(), m.state() * ncells)
        s.reset()
        self.assertEqual(s.state(), s.default_state())

        # Test pre updates the default state.
        s.pre(1)
        self.assertNotEqual(s.default_state(0), m.state())

        # Test running without a protocol
        s.set_protocol(None)
        s.run(1)

        # Simulation time can't be negative
        self.assertRaises(ValueError, s.run, -1)

        # Number of cells must be >0
        self.assertRaisesRegex(
            ValueError, 'number of cells', myokit.Simulation1d, m, p, 0)

        # Model must have a membrane potential
        v = m.get('membrane.V')
        v.set_label(None)
        self.assertRaisesRegex(
            ValueError, 'membrane_potential', myokit.Simulation1d, m, p, 5)
        v.set_label('membrane_potential')

        # Model must have a diffusion current
        d = m.binding('diffusion_current')
        d.set_binding(None)
        self.assertRaisesRegex(
            ValueError, 'diffusion_current', myokit.Simulation1d, m, p, 5)

        # Test setting conductance
        s.set_conductance(10)
        self.assertEqual(s.conductance(), 10)
        self.assertRaises(ValueError, s.set_conductance, -1)

        # Test setting paced cells
        s.set_paced_cells(1)
        self.assertEqual(s.paced_cells(), 1)
        self.assertRaises(ValueError, s.set_paced_cells, -1)

        # Test setting step size
        s.set_step_size(0.01)
        self.assertRaises(ValueError, s.set_step_size, 0)

        # Test setting time
        self.assertNotEqual(s.time(), 100)
        s.set_time(100)
        self.assertEqual(s.time(), 100)

    def test_with_progress_reporter(self):
        # Test running with a progress reporter.
        m, p, _ = myokit.load(os.path.join(DIR_DATA, 'lr-1991.mmt'))

        # Test using a progress reporter
        s = myokit.Simulation1d(m, p, ncells=5)
        with myokit.PyCapture() as c:
            s.run(110, progress=myokit.ProgressPrinter())
        c = c.text().splitlines()
        self.assertTrue(len(c) > 0)

        # Not a progress reporter
        self.assertRaisesRegex(
            ValueError, 'ProgressReporter', s.run, 5, progress=12)

        # Cancel from reporter
        self.assertRaises(
            myokit.SimulationCancelledError, s.run, 1,
            progress=CancellingReporter(0))

    def test_set_state(self):
        # Test :meth:`Simulation1d.set_state()`.
        m, p, _ = myokit.load(os.path.join(DIR_DATA, 'lr-1991.mmt'))
        n = 4

        s = myokit.Simulation1d(m, p, n)
        self.assertEqual(s.state(), m.state() * n)

        # Test setting a full state
        sx = [0] * 8 * n
        self.assertNotEqual(sx, s.state())
        s.set_state(sx)
        self.assertEqual(sx, s.state())

        # Test setting a single, global state
        sx = [0] * 8
        s.set_state(sx)
        self.assertEqual(s.state(), sx * n)
        s.set_state(m.state())
        self.assertEqual(s.state(), m.state() * n)

        # Test setting a single state
        j = 1
        s.set_state(sx, j)
        for i in range(n):
            if i == j:
                self.assertEqual(s.state(i), sx)
            else:
                self.assertEqual(s.state(i), m.state())

        # Invalid cell index
        s.set_state(sx, 0)
        self.assertRaises(ValueError, s.set_state, sx, -1)
        self.assertRaises(ValueError, s.set_state, sx, n)
        self.assertRaises(ValueError, s.state, -1)
        self.assertRaises(ValueError, s.state, n)

    def test_set_default_state(self):
        # Test :meth:`Simulation1d.set_default_state()`.
        m, p, _ = myokit.load(os.path.join(DIR_DATA, 'lr-1991.mmt'))
        n = 4

        s = myokit.Simulation1d(m, p, n)
        self.assertEqual(s.state(), m.state() * n)

        # Test setting a full state
        sx = [0] * 8 * n
        self.assertNotEqual(sx, s.default_state())
        s.set_default_state(sx)
        self.assertEqual(sx, s.default_state())

        # Test setting a single, global state
        sx = [0] * 8
        s.set_default_state(sx)
        self.assertEqual(s.default_state(), sx * n)
        s.set_default_state(m.state())
        self.assertEqual(s.default_state(), m.state() * n)

        # Test setting a single state
        j = 1
        s.set_default_state(sx, j)
        for i in range(n):
            if i == j:
                self.assertEqual(s.default_state(i), sx)
            else:
                self.assertEqual(s.default_state(i), m.state())

        # Invalid cell index
        s.set_default_state(sx, 0)
        self.assertRaises(ValueError, s.set_default_state, sx, -1)
        self.assertRaises(ValueError, s.set_default_state, sx, n)
        self.assertRaises(ValueError, s.default_state, -1)
        self.assertRaises(ValueError, s.default_state, n)
    '''

    def test_against_cvode(self):
        # Compare the Simulation1d output with CVODE output
        m, p, _ = myokit.load(os.path.join(DIR_DATA, 'lr-1991.mmt'))

        # Make protocol to compare t=0 event implementations
        e = p.head()
        p = myokit.Protocol()
        p.schedule(level=e.level(), duration=e.duration(), start=0)

        dt = 0.02
        tmax = 3000
        logvars = ['engine.time', 'membrane.V', 'engine.pace']
        s1 = myokit.Simulation1d(m, p, ncells=1, rl=True)
        s1.set_step_size(dt)
        d1 = s1.run(tmax, logvars, log_interval=dt).npview()
        s2 = myokit.Simulation(m, p)
        s2.set_max_step_size(dt)
        s2.set_tolerance(1e-8, 1e-8)
        d2 = s2.run(tmax, logvars, log_interval=dt).npview()

        # Check implementation of logging point selection
        print(d1.time()[:7])
        print(d2.time()[:7])
        print(d1.time()[-7:])
        print(d2.time()[-7:])
        e0 = np.max(np.abs(d1.time() - d2.time()))
        self.assertLess(e0, 1e-14)

        # Check implementation of events (esp. ones that start at t=0)
        e1 = d1['engine.pace', 0] - d2['engine.pace']
        e1 = np.sum(e1**2)
        print(e1)


        if debug:
            import matplotlib.pyplot as plt
            plt.figure()
            plt.plot(d1.time(), d1['engine.pace', 0], label='Euler')
            plt.plot(d2.time(), d2['engine.pace'], label='CVODE')
            plt.legend()

            plt.figure()
            plt.plot(d1.time(), d1['engine.pace', 0] - d2['engine.pace'])

            plt.figure()
            plt.plot(d1.time(), d1.time())
            plt.plot(d1.time(), d2.time())
            plt.show()


if __name__ == '__main__':
    import sys
    if '-v' in sys.argv:
        print('Running in debug/verbose mode')
        debug = True
    else:
        print('Add -v for more debug output')
    unittest.main()
