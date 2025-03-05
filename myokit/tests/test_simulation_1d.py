#!/usr/bin/env python3
#
# Tests the Simulation1d class.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import os
import unittest

import numpy as np

import myokit

from myokit.tests import DIR_DATA, CancellingReporter

# Show simulation output
debug = False


class Simulation1dTest(unittest.TestCase):
    """
    Test the non-parallel 1d simulation.
    """

    def test_basic(self):
        # Test basic usage.

        # Load model
        m, p, _ = myokit.load(os.path.join(DIR_DATA, 'lr-1991.mmt'))

        # Run a simulation
        ncells = 5
        s = myokit.Simulation1d(m, p, ncells=ncells)
        s.set_step_size(0.05)

        x0 = m.initial_values(True)
        self.assertEqual(s.time(), 0)
        self.assertEqual(s.state(0), x0)
        self.assertEqual(s.default_state(0), x0)
        d = s.run(5, log_interval=1)
        self.assertEqual(s.time(), 5)
        self.assertNotEqual(s.state(0), x0)
        self.assertEqual(s.default_state(0), x0)

        # Test full state getting and reset
        self.assertEqual(s.default_state(), x0 * ncells)
        self.assertNotEqual(s.state(), x0 * ncells)
        s.reset()
        self.assertEqual(s.state(), s.default_state())

        # Test pre updates the default state.
        s.pre(1)
        self.assertNotEqual(s.default_state(0), x0)

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

    def test_initial_value_expressions(self):
        # Test if initial value expressions are converted to floats
        m = myokit.parse_model('''
            [[model]]
            c.x = 1 + sqrt(3)
            c.y = 1 / c.p
            c.z = 3

            [c]
            t = 0 bind time
            dot(x) = 1 label membrane_potential
            dot(y) = 2
            dot(z) = 3
            p = log(3)
            q = 0 bind diffusion_current
        ''')
        s = myokit.Simulation1d(m, ncells=2)
        x = s.state()
        self.assertIsInstance(x[0], float)
        self.assertIsInstance(x[1], float)
        self.assertIsInstance(x[2], float)
        self.assertEqual(x[:3], x[3:])
        self.assertEqual(x, m.initial_values(True) * 2)
        self.assertEqual(x, s.default_state())

    def test_negative_time(self):
        # Test starting at a negative time

        m = myokit.load_model(os.path.join(DIR_DATA, 'lr-1991.mmt'))
        p = myokit.pacing.blocktrain(duration=1, level=1, period=2)
        n = 4
        s = myokit.Simulation1d(m, p, ncells=n)

        s.set_time(-10)
        self.assertEqual(s.time(), -10)
        d = s.run(5, log=['engine.pace']).npview()
        self.assertEqual(s.time(), -5)
        self.assertTrue(np.all(d['engine.pace'] == 0))
        d = s.run(6, log=['engine.time', 'engine.pace']).npview()
        #print(d['engine.time'])
        #print(d['engine.pace'])
        self.assertEqual(s.time(), 1)
        self.assertTrue(np.all(d['engine.pace'][:-1] == 0))
        self.assertEqual(d['engine.pace'][-1], 1)

    def test_no_protocol(self):
        # Test running without a protocol
        m = myokit.load_model(os.path.join(DIR_DATA, 'lr-1991.mmt'))
        x = 0.123
        m.get('engine.pace').set_rhs(x)
        n = 4

        # Create without a protocol
        s = myokit.Simulation1d(m, ncells=n)
        d = s.run(10, log=['engine.pace']).npview()
        self.assertIn('engine.pace', d.keys())
        self.assertTrue(np.all(d['engine.pace'] == 0))

        # Set, then unset
        y = 0.101
        p = myokit.pacing.blocktrain(level=y, duration=100, period=100)
        s.set_protocol(p)
        d = s.run(5, log=['engine.pace']).npview()
        self.assertTrue(np.all(d['engine.pace'] == y))
        self.assertGreater(len(d['engine.pace']), 1)
        s.set_protocol(None)
        d = s.run(5, log=['engine.pace']).npview()
        self.assertTrue(np.all(d['engine.pace'] == 0))

    def test_set_state(self):
        # Test :meth:`Simulation1d.set_state()`.
        m, p, _ = myokit.load(os.path.join(DIR_DATA, 'lr-1991.mmt'))
        n = 4

        s = myokit.Simulation1d(m, p, n)
        x0 = m.initial_values(True)
        self.assertEqual(s.state(), x0 * n)

        # Test setting a full state
        sx = [0] * 8 * n
        self.assertNotEqual(sx, s.state())
        s.set_state(sx)
        self.assertEqual(sx, s.state())

        # Test setting a single, global state
        sx = [0] * 8
        s.set_state(sx)
        self.assertEqual(s.state(), sx * n)
        s.set_state(x0)
        self.assertEqual(s.state(), x0 * n)

        # Test setting a single state
        j = 1
        s.set_state(sx, j)
        for i in range(n):
            if i == j:
                self.assertEqual(s.state(i), sx)
            else:
                self.assertEqual(s.state(i), x0)

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
        self.assertEqual(s.state(), m.initial_values(True) * n)

        # Test setting a full state
        sx = [0] * 8 * n
        self.assertNotEqual(sx, s.default_state())
        s.set_default_state(sx)
        self.assertEqual(sx, s.default_state())

        # Test setting a single, global state
        sx = [0] * 8
        s.set_default_state(sx)
        self.assertEqual(s.default_state(), sx * n)
        sy = m.initial_values(True)
        s.set_default_state(sy)
        self.assertEqual(s.default_state(), sy * n)

        # Test setting a single state
        j = 1
        s.set_default_state(sx, j)
        for i in range(n):
            if i == j:
                self.assertEqual(s.default_state(i), sx)
            else:
                self.assertEqual(s.default_state(i), sy)

        # Invalid cell index
        s.set_default_state(sx, 0)
        self.assertRaises(ValueError, s.set_default_state, sx, -1)
        self.assertRaises(ValueError, s.set_default_state, sx, n)
        self.assertRaises(ValueError, s.default_state, -1)
        self.assertRaises(ValueError, s.default_state, n)

    def test_with_progress_reporter(self):
        # Test running with a progress reporter.
        m, p, _ = myokit.load(os.path.join(DIR_DATA, 'lr-1991.mmt'))

        # Test using a progress reporter
        s = myokit.Simulation1d(m, p, ncells=5)
        s.set_step_size(0.05)
        with myokit.tools.capture() as c:
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

    def test_against_cvode(self):
        # Compare the Simulation1d output with CVODE output

        # Load model and event with appropriate level/duration
        m, p, _ = myokit.load(os.path.join(DIR_DATA, 'lr-1991.mmt'))
        e = p.head()

        #
        # Make protocol to compare t=0 event implementations
        #
        dt = 0.1    # Note: this is too big to be very accurate
        tmax = 1300
        p = myokit.Protocol()
        p.schedule(level=e.level(), duration=e.duration(), period=600, start=0)
        logvars = ['engine.time', 'membrane.V', 'engine.pace', 'ica.ICa']

        s1 = myokit.Simulation1d(m, p, ncells=1, rl=True)
        s1.set_step_size(dt)
        d1 = s1.run(tmax, logvars, log_interval=dt).npview()

        s2 = myokit.Simulation(m, p)
        s2.set_tolerance(1e-8, 1e-8)
        d2 = s2.run(tmax, logvars, log_interval=dt).npview()

        # Check implementation of logging point selection
        e0 = np.max(np.abs(d1.time() - d2.time()))

        # Check implementation of pacing
        r1 = d1['engine.pace'] - d2['engine.pace']
        e1 = np.sum(r1**2)

        # Check membrane potential (will have some error!)
        # Using MRMS from Marsh, Ziaratgahi, Spiteri 2012
        r2 = d1['membrane.V', 0] - d2['membrane.V']
        r2 /= (1 + np.abs(d2['membrane.V']))
        e2 = np.sqrt(np.sum(r2**2) / len(r2))

        # Check logging of intermediary variables
        r3 = d1['ica.ICa', 0] - d2['ica.ICa']
        r3 /= (1 + np.abs(d2['ica.ICa']))
        e3 = np.sqrt(np.sum(r3**2) / len(r3))

        if debug:
            import matplotlib.pyplot as plt
            print('Event at t=0')

            plt.figure()
            plt.suptitle('Time points')
            plt.plot(d1.time(), label='Euler')
            plt.plot(d1.time(), label='CVODE')
            plt.legend()
            print(d1.time()[:7])
            print(d2.time()[:7])
            print(d1.time()[-7:])
            print(d2.time()[-7:])
            print(e0)

            plt.figure()
            plt.suptitle('Pacing signals')
            plt.subplot(2, 1, 1)
            plt.plot(d1.time(), d1['engine.pace'], label='Euler')
            plt.plot(d2.time(), d2['engine.pace'], label='CVODE')
            plt.legend()
            plt.subplot(2, 1, 2)
            plt.plot(d1.time(), r1)
            print(e1)

            plt.figure()
            plt.suptitle('Membrane potential')
            plt.subplot(2, 1, 1)
            plt.plot(d1.time(), d1['membrane.V', 0], label='Euler')
            plt.plot(d2.time(), d2['membrane.V'], label='CVODE')
            plt.legend()
            plt.subplot(2, 1, 2)
            plt.plot(d1.time(), r2)
            print(e2)

            plt.figure()
            plt.suptitle('Calcium current')
            plt.subplot(2, 1, 1)
            plt.plot(d1.time(), d1['ica.ICa', 0], label='Euler')
            plt.plot(d2.time(), d2['ica.ICa'], label='CVODE')
            plt.legend()
            plt.subplot(2, 1, 2)
            plt.plot(d1.time(), r2)
            print(e3)

            plt.show()

        self.assertLess(e0, 1e-14)
        self.assertLess(e1, 1e-14)
        self.assertLess(e2, 0.1)   # Note: The step size is really too big here
        self.assertLess(e3, 0.1)

        #
        # Make protocol to compare with event at step-size multiple
        #
        dt = 0.1   # Note: this is too big to be very accurate
        tmax = 1300
        p = myokit.Protocol()
        p.schedule(
            level=e.level(),
            duration=e.duration(),
            period=600,
            start=10)

        logvars = ['engine.time', 'membrane.V', 'engine.pace', 'ica.ICa']

        s1.reset()
        s1.set_protocol(p)
        s1.set_step_size(dt)
        d1 = s1.run(tmax, logvars, log_interval=dt).npview()

        s2.reset()
        s2.set_protocol(p)
        s2.set_tolerance(1e-8, 1e-8)
        d2 = s2.run(tmax, logvars, log_interval=dt).npview()

        # Check implementation of logging point selection
        e0 = np.max(np.abs(d1.time() - d2.time()))

        # Check implementation of pacing
        r1 = d1['engine.pace'] - d2['engine.pace']
        e1 = np.sum(r1**2)

        # Check membrane potential (will have some error!)
        # Using MRMS from Marsh, Ziaratgahi, Spiteri 2012
        r2 = d1['membrane.V', 0] - d2['membrane.V']
        r2 /= (1 + np.abs(d2['membrane.V']))
        e2 = np.sqrt(np.sum(r2**2) / len(r2))

        # Check logging of intermediary variables
        r3 = d1['ica.ICa', 0] - d2['ica.ICa']
        r3 /= (1 + np.abs(d2['ica.ICa']))
        e3 = np.sqrt(np.sum(r3**2) / len(r3))

        if debug:
            import matplotlib.pyplot as plt
            print('Event at t=0')

            plt.figure()
            plt.suptitle('Time points')
            plt.plot(d1.time(), label='Euler')
            plt.plot(d1.time(), label='CVODE')
            plt.legend()
            print(d1.time()[:7])
            print(d2.time()[:7])
            print(d1.time()[-7:])
            print(d2.time()[-7:])
            print(e0)

            plt.figure()
            plt.suptitle('Pacing signals')
            plt.subplot(2, 1, 1)
            plt.plot(d1.time(), d1['engine.pace'], label='Euler')
            plt.plot(d2.time(), d2['engine.pace'], label='CVODE')
            plt.legend()
            plt.subplot(2, 1, 2)
            plt.plot(d1.time(), r1)
            print(e1)

            plt.figure()
            plt.suptitle('Membrane potential')
            plt.subplot(2, 1, 1)
            plt.plot(d1.time(), d1['membrane.V', 0], label='Euler')
            plt.plot(d2.time(), d2['membrane.V'], label='CVODE')
            plt.legend()
            plt.subplot(2, 1, 2)
            plt.plot(d1.time(), r2)
            print(e2)

            plt.figure()
            plt.suptitle('Calcium current')
            plt.subplot(2, 1, 1)
            plt.plot(d1.time(), d1['ica.ICa', 0], label='Euler')
            plt.plot(d2.time(), d2['ica.ICa'], label='CVODE')
            plt.legend()
            plt.subplot(2, 1, 2)
            plt.plot(d1.time(), r2)
            print(e3)

            plt.show()

        self.assertLess(e0, 1e-14)
        self.assertLess(e1, 1e-14)
        self.assertLess(e2, 0.1)   # Note: The step size is really too big here
        self.assertLess(e3, 0.1)

        #
        # Make protocol to compare with event NOT at step-size multiple
        #
        dt = 0.1   # Note: this is too big to be very accurate
        tmax = 1300
        p = myokit.Protocol()
        p.schedule(
            level=e.level(),
            duration=e.duration(),
            period=600,
            start=1.05)

        logvars = ['engine.time', 'membrane.V', 'engine.pace', 'ica.ICa']

        s1.reset()
        s1.set_protocol(p)
        s1.set_step_size(dt)
        d1 = s1.run(tmax, logvars, log_interval=dt).npview()

        s2.reset()
        s2.set_protocol(p)
        s2.set_tolerance(1e-8, 1e-8)
        d2 = s2.run(tmax, logvars, log_interval=dt).npview()

        # Check implementation of logging point selection
        e0 = np.max(np.abs(d1.time() - d2.time()))

        # Check implementation of pacing
        r1 = d1['engine.pace'] - d2['engine.pace']
        e1 = np.sum(r1**2)

        # Check membrane potential (will have some error!)
        # Using MRMS from Marsh, Ziaratgahi, Spiteri 2012
        r2 = d1['membrane.V', 0] - d2['membrane.V']
        r2 /= (1 + np.abs(d2['membrane.V']))
        e2 = np.sqrt(np.sum(r2**2) / len(r2))

        # Check logging of intermediary variables
        r3 = d1['ica.ICa', 0] - d2['ica.ICa']
        r3 /= (1 + np.abs(d2['ica.ICa']))
        e3 = np.sqrt(np.sum(r3**2) / len(r3))

        if debug:
            import matplotlib.pyplot as plt
            print('Event at t=0')

            plt.figure()
            plt.suptitle('Time points')
            plt.plot(d1.time(), label='Euler')
            plt.plot(d1.time(), label='CVODE')
            plt.legend()
            print(d1.time()[:7])
            print(d2.time()[:7])
            print(d1.time()[-7:])
            print(d2.time()[-7:])
            print(e0)

            plt.figure()
            plt.suptitle('Pacing signals')
            plt.subplot(2, 1, 1)
            plt.plot(d1.time(), d1['engine.pace'], label='Euler')
            plt.plot(d2.time(), d2['engine.pace'], label='CVODE')
            plt.legend()
            plt.subplot(2, 1, 2)
            plt.plot(d1.time(), r1)
            print(e1)

            plt.figure()
            plt.suptitle('Membrane potential')
            plt.subplot(2, 1, 1)
            plt.plot(d1.time(), d1['membrane.V', 0], label='Euler')
            plt.plot(d2.time(), d2['membrane.V'], label='CVODE')
            plt.legend()
            plt.subplot(2, 1, 2)
            plt.plot(d1.time(), r2)
            print(e2)

            plt.figure()
            plt.suptitle('Calcium current')
            plt.subplot(2, 1, 1)
            plt.plot(d1.time(), d1['ica.ICa', 0], label='Euler')
            plt.plot(d2.time(), d2['ica.ICa'], label='CVODE')
            plt.legend()
            plt.subplot(2, 1, 2)
            plt.plot(d1.time(), r2)
            print(e3)

            plt.show()

        self.assertLess(e0, 1e-14)
        self.assertLess(e1, 1e-14)
        self.assertLess(e2, 0.2)   # Note: The step size is really too big here
        self.assertLess(e3, 0.2)

        #
        # Test again, with event at step multiple, but now without Rush-Larsen
        #
        dt = 0.01   # Note: this is too big to be very accurate
        tmax = 200
        p = myokit.Protocol()
        p.schedule(
            level=e.level(),
            duration=e.duration(),
            period=600,
            start=10)

        logvars = ['engine.time', 'membrane.V', 'engine.pace', 'ica.ICa']
        s1 = myokit.Simulation1d(m, p, ncells=1, rl=False)
        s1.set_step_size(dt)
        d1 = s1.run(tmax, logvars, log_interval=dt).npview()
        s2.reset()
        s2.set_protocol(p)
        s2.set_tolerance(1e-8, 1e-8)
        d2 = s2.run(tmax, logvars, log_interval=dt).npview()

        # Check membrane potential (will have some error!)
        # Using MRMS from Marsh, Ziaratgahi, Spiteri 2012
        r2 = d1['membrane.V', 0] - d2['membrane.V']
        r2 /= (1 + np.abs(d2['membrane.V']))
        e2 = np.sqrt(np.sum(r2**2) / len(r2))
        self.assertLess(e2, 0.05)  # Note: The step size is really too big here

        # Check logging of intermediary variables
        r3 = d1['ica.ICa', 0] - d2['ica.ICa']
        r3 /= (1 + np.abs(d2['ica.ICa']))
        e3 = np.sqrt(np.sum(r3**2) / len(r3))
        self.assertLess(e3, 0.05)


if __name__ == '__main__':
    import sys
    if '-v' in sys.argv:
        print('Running in debug/verbose mode')
        debug = True
    else:
        print('Add -v for more debug output')
    unittest.main()
