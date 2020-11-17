#!/usr/bin/env python3
#
# Tests the OpenCL simulation classes
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

from shared import OpenCL_FOUND, DIR_DATA
from shared import WarningCollector

# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp


# Show simulation output
debug = False


@unittest.skipIf(not OpenCL_FOUND, 'OpenCL not found on this system.')
class SimulationOpenCL0dTest(unittest.TestCase):
    """
    Tests the OpenCL simulation against CVODE, in 0d mode.
    """
    def test_against_cvode(self):
        # Compare the SimulationOpenCL output with CVODE output

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

        s1 = myokit.SimulationOpenCL(
            m, p, ncells=1, rl=True, precision=myokit.DOUBLE_PRECISION)
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
            plt.plot(d1.time(), d1['engine.pace'], label='OpenCL')
            plt.plot(d2.time(), d2['engine.pace'], label='CVODE')
            plt.legend()
            plt.subplot(2, 1, 2)
            plt.plot(d1.time(), r1)
            print(e1)

            plt.figure()
            plt.suptitle('Membrane potential')
            plt.subplot(2, 1, 1)
            plt.plot(d1.time(), d1['membrane.V', 0], label='OpenCL')
            plt.plot(d2.time(), d2['membrane.V'], label='CVODE')
            plt.legend()
            plt.subplot(2, 1, 2)
            plt.plot(d1.time(), r2)
            print(e2)

            plt.figure()
            plt.suptitle('Calcium current')
            plt.subplot(2, 1, 1)
            plt.plot(d1.time(), d1['ica.ICa', 0], label='OpenCL')
            plt.plot(d2.time(), d2['ica.ICa'], label='CVODE')
            plt.legend()
            plt.subplot(2, 1, 2)
            plt.plot(d1.time(), r2)
            print(e3)

            plt.show()

        self.assertLess(e0, 1e-14)
        self.assertLess(e1, 1e-14)
        self.assertLess(e2, 0.1)   # Note: The step size is really too big here
        self.assertLess(e3, 0.05)

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
            plt.plot(d1.time(), label='OpenCL')
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
            plt.plot(d1.time(), d1['engine.pace'], label='OpenCL')
            plt.plot(d2.time(), d2['engine.pace'], label='CVODE')
            plt.legend()
            plt.subplot(2, 1, 2)
            plt.plot(d1.time(), r1)
            print(e1)

            plt.figure()
            plt.suptitle('Membrane potential')
            plt.subplot(2, 1, 1)
            plt.plot(d1.time(), d1['membrane.V', 0], label='OpenCL')
            plt.plot(d2.time(), d2['membrane.V'], label='CVODE')
            plt.legend()
            plt.subplot(2, 1, 2)
            plt.plot(d1.time(), r2)
            print(e2)

            plt.figure()
            plt.suptitle('Calcium current')
            plt.subplot(2, 1, 1)
            plt.plot(d1.time(), d1['ica.ICa', 0], label='OpenCL')
            plt.plot(d2.time(), d2['ica.ICa'], label='CVODE')
            plt.legend()
            plt.subplot(2, 1, 2)
            plt.plot(d1.time(), r2)
            print(e3)

            plt.show()

        self.assertLess(e0, 1e-14)
        self.assertLess(e1, 1e-14)
        self.assertLess(e2, 0.1)   # Note: The step size is really too big here
        self.assertLess(e3, 0.05)

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
            plt.plot(d1.time(), d1['ica.ICa', 0], label='OpenCL')
            plt.plot(d2.time(), d2['ica.ICa'], label='CVODE')
            plt.legend()
            plt.subplot(2, 1, 2)
            plt.plot(d1.time(), r2)
            print(e3)

            plt.show()

        self.assertLess(e0, 1e-14)
        self.assertLess(e1, 1e-14)
        self.assertLess(e2, 0.2)   # Note: The step size is really too big here
        self.assertLess(e3, 0.05)

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

        s1 = myokit.SimulationOpenCL(
            m, p, ncells=1, rl=False, precision=myokit.DOUBLE_PRECISION)
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
        self.assertLess(e3, 0.01)


@unittest.skipIf(not OpenCL_FOUND, 'OpenCL not found on this system.')
class SimulationOpenCLTest(unittest.TestCase):
    """
    Tests the OpenCL simulation in 1d and 2d mode.
    """

    def test_neighbours(self):
        # Test listing neighbours in a 1d or arbitrary geom simulation
        m, p, _ = myokit.load('example')

        # 0d
        s = myokit.SimulationOpenCL(m, p, 1)
        x = s.neighbours(0)
        self.assertEqual(len(x), 0)
        self.assertRaisesRegex(ValueError, 'out of range', s.neighbours, -1)
        self.assertRaisesRegex(ValueError, 'out of range', s.neighbours, 1)
        self.assertRaisesRegex(ValueError, '1-dimensional', s.neighbours, 0, 1)

        # 1d
        s = myokit.SimulationOpenCL(m, p, 5)
        # Left edge
        x = s.neighbours(0)
        self.assertEqual(len(x), 1)
        self.assertIn(1, x)
        # Middle
        x = s.neighbours(1)
        self.assertEqual(len(x), 2)
        self.assertIn(0, x)
        self.assertIn(2, x)
        # Right edge
        x = s.neighbours(4)
        self.assertEqual(len(x), 1)
        self.assertIn(3, x)
        # Out of range
        self.assertRaisesRegex(ValueError, 'out of range', s.neighbours, -1)
        self.assertRaisesRegex(ValueError, 'out of range', s.neighbours, 6)
        self.assertRaisesRegex(ValueError, '1-dimensional', s.neighbours, 0, 1)

        # Arbitrary geometry
        g = 1
        s.set_connections([(0, 1, g), (0, 2, g), (3, 0, g), (3, 2, g)])
        x = s.neighbours(0)
        self.assertEqual(len(x), 3)
        self.assertIn(1, x)
        self.assertIn(2, x)
        self.assertIn(3, x)
        x = s.neighbours(1)
        self.assertEqual(len(x), 1)
        self.assertIn(0, x)
        x = s.neighbours(2)
        self.assertEqual(len(x), 2)
        self.assertIn(0, x)
        self.assertIn(3, x)
        x = s.neighbours(3)
        self.assertEqual(len(x), 2)
        self.assertIn(0, x)
        self.assertIn(2, x)
        x = s.neighbours(4)
        self.assertEqual(len(x), 0)

        # Invalid connections
        self.assertRaisesRegex(
            ValueError, 'nvalid connection', s.set_connections, [(0, 0, g)])
        self.assertRaisesRegex(
            ValueError, 'nvalid connection', s.set_connections, [(-1, 0, g)])
        self.assertRaisesRegex(
            ValueError, 'nvalid connection', s.set_connections, [(0, -1, g)])
        self.assertRaisesRegex(
            ValueError, 'nvalid connection', s.set_connections, [(0, 5, g)])
        self.assertRaisesRegex(
            ValueError, 'nvalid connection', s.set_connections, [(5, 0, g)])

        # Duplicate connections
        self.assertRaisesRegex(
            ValueError, 'uplicate connection',
            s.set_connections, [(0, 1, g), (0, 1, g)])
        self.assertRaisesRegex(
            ValueError, 'uplicate connection',
            s.set_connections, [(0, 1, g), (1, 0, g)])

        # 2d
        s = myokit.SimulationOpenCL(m, p, (5, 4))
        # Corners
        x = s.neighbours(0, 0)
        self.assertEqual(len(x), 2)
        self.assertIn((1, 0), x)
        self.assertIn((0, 1), x)
        x = s.neighbours(4, 3)
        self.assertEqual(len(x), 2)
        self.assertIn((4, 2), x)
        self.assertIn((3, 3), x)
        # Edges
        x = s.neighbours(1, 0)
        self.assertEqual(len(x), 3)
        self.assertIn((0, 0), x)
        self.assertIn((2, 0), x)
        self.assertIn((1, 1), x)
        x = s.neighbours(4, 2)
        self.assertEqual(len(x), 3)
        self.assertIn((3, 2), x)
        self.assertIn((4, 1), x)
        self.assertIn((4, 3), x)
        # Middle
        x = s.neighbours(1, 1)
        self.assertEqual(len(x), 4)
        self.assertIn((0, 1), x)
        self.assertIn((2, 1), x)
        self.assertIn((1, 0), x)
        self.assertIn((1, 2), x)
        x = s.neighbours(3, 2)
        self.assertEqual(len(x), 4)
        self.assertIn((2, 2), x)
        self.assertIn((4, 2), x)
        self.assertIn((3, 1), x)
        self.assertIn((3, 3), x)
        # Out of range
        self.assertRaisesRegex(ValueError, 'out of range', s.neighbours, -1, 0)
        self.assertRaisesRegex(ValueError, 'out of range', s.neighbours, 0, -1)
        self.assertRaisesRegex(ValueError, 'out of range', s.neighbours, 5, 0)
        self.assertRaisesRegex(ValueError, '2-dimensional', s.neighbours, 0)

    def test_set_paced_interface_1d(self):
        # Test the set_paced and is_paced methods in 1d (interface only, does
        # not test running the simulation!

        m, p, _ = myokit.load('example')
        s = myokit.SimulationOpenCL(m, p, 5)

        # Set first few cells
        s.set_paced_cells(3)
        self.assertTrue(s.is_paced(0))
        self.assertTrue(s.is_paced(1))
        self.assertTrue(s.is_paced(2))
        self.assertFalse(s.is_paced(3))
        self.assertFalse(s.is_paced(4))

        # Set with an offset
        s.set_paced_cells(nx=2, x=2)
        self.assertFalse(s.is_paced(0))
        self.assertFalse(s.is_paced(1))
        self.assertTrue(s.is_paced(2))
        self.assertTrue(s.is_paced(3))
        self.assertFalse(s.is_paced(4))

        # Set final cells with negative number
        s.set_paced_cells(nx=-2)
        self.assertFalse(s.is_paced(0))
        self.assertFalse(s.is_paced(1))
        self.assertFalse(s.is_paced(2))
        self.assertTrue(s.is_paced(3))
        self.assertTrue(s.is_paced(4))

        # Set with an offset and a negative number
        s.set_paced_cells(nx=-2, x=4)
        self.assertFalse(s.is_paced(0))
        self.assertFalse(s.is_paced(1))
        self.assertTrue(s.is_paced(2))
        self.assertTrue(s.is_paced(3))
        self.assertFalse(s.is_paced(4))

        # Set with a negative offset and negative number
        s.set_paced_cells(nx=-2, x=-2)
        self.assertFalse(s.is_paced(0))
        self.assertTrue(s.is_paced(1))
        self.assertTrue(s.is_paced(2))
        self.assertFalse(s.is_paced(3))
        self.assertFalse(s.is_paced(4))

        # Set with a list
        s.set_paced_cell_list([0, 2, 3])
        self.assertTrue(s.is_paced(0))
        self.assertFalse(s.is_paced(1))
        self.assertTrue(s.is_paced(2))
        self.assertTrue(s.is_paced(3))
        self.assertFalse(s.is_paced(4))

        # Duplicate paced cells
        s.set_paced_cell_list([0, 0, 0, 0, 3, 3, 3])
        self.assertTrue(s.is_paced(0))
        self.assertFalse(s.is_paced(1))
        self.assertFalse(s.is_paced(2))
        self.assertTrue(s.is_paced(3))
        self.assertFalse(s.is_paced(4))

        # Just one cell
        s.set_paced_cell_list([2])
        self.assertFalse(s.is_paced(0))
        self.assertFalse(s.is_paced(1))
        self.assertTrue(s.is_paced(2))
        self.assertFalse(s.is_paced(3))
        self.assertFalse(s.is_paced(4))

        # Set paced cells out of bounds
        self.assertRaisesRegex(
            ValueError, 'out of range', s.set_paced_cell_list, [-1])
        self.assertRaisesRegex(
            ValueError, 'out of range', s.set_paced_cell_list, [5])

        # Is-paced called out of bounds
        self.assertRaisesRegex(
            ValueError, 'out of range', s.is_paced, -1)
        self.assertRaisesRegex(
            ValueError, 'out of range', s.is_paced, 5)
        self.assertRaisesRegex(
            ValueError, '1-dimensional', s.is_paced, 3, 3)

    def test_set_paced_interface_2d(self):
        # Test the set_paced and is_paced methods in 2d (interface only, does
        # not test running the simulation!

        m, p, _ = myokit.load('example')
        s = myokit.SimulationOpenCL(m, p, (2, 3))

        # Set first few cells
        s.set_paced_cells(1, 2)
        self.assertTrue(s.is_paced(0, 0))
        self.assertTrue(s.is_paced(0, 1))
        self.assertFalse(s.is_paced(0, 2))
        self.assertFalse(s.is_paced(1, 0))
        self.assertFalse(s.is_paced(1, 1))
        self.assertFalse(s.is_paced(1, 2))

        # Set with an offset
        s.set_paced_cells(x=1, y=1, nx=1, ny=2)
        self.assertFalse(s.is_paced(0, 0))
        self.assertFalse(s.is_paced(0, 1))
        self.assertFalse(s.is_paced(0, 2))
        self.assertFalse(s.is_paced(1, 0))
        self.assertTrue(s.is_paced(1, 1))
        self.assertTrue(s.is_paced(1, 2))

        # Set final cells with negative number
        s.set_paced_cells(nx=-1, ny=-1)
        self.assertFalse(s.is_paced(0, 0))
        self.assertFalse(s.is_paced(0, 1))
        self.assertFalse(s.is_paced(0, 2))
        self.assertFalse(s.is_paced(1, 0))
        self.assertFalse(s.is_paced(1, 1))
        self.assertTrue(s.is_paced(1, 2))

        # Set with an offset and a negative number
        s.set_paced_cells(x=1, y=2, nx=-1, ny=-2)
        self.assertTrue(s.is_paced(0, 0))
        self.assertTrue(s.is_paced(0, 1))
        self.assertFalse(s.is_paced(0, 2))
        self.assertFalse(s.is_paced(1, 0))
        self.assertFalse(s.is_paced(1, 1))
        self.assertFalse(s.is_paced(1, 2))

        # Set with a negative offset and negative number
        s.set_paced_cells(x=0, y=-1, nx=1, ny=-1)
        self.assertFalse(s.is_paced(0, 0))
        self.assertTrue(s.is_paced(0, 1))
        self.assertFalse(s.is_paced(0, 2))
        self.assertFalse(s.is_paced(1, 0))
        self.assertFalse(s.is_paced(1, 1))
        self.assertFalse(s.is_paced(1, 2))

        # Set with a list
        s.set_paced_cell_list([(0, 0), (0, 2), (1, 1)])
        self.assertTrue(s.is_paced(0, 0))
        self.assertFalse(s.is_paced(0, 1))
        self.assertTrue(s.is_paced(0, 2))
        self.assertFalse(s.is_paced(1, 0))
        self.assertTrue(s.is_paced(1, 1))
        self.assertFalse(s.is_paced(1, 2))

        # Duplicate paced cells
        s.set_paced_cell_list([(0, 0), (0, 0), (0, 0), (0, 2), (0, 2)])
        self.assertTrue(s.is_paced(0, 0))
        self.assertFalse(s.is_paced(0, 1))
        self.assertTrue(s.is_paced(0, 2))
        self.assertFalse(s.is_paced(1, 0))
        self.assertFalse(s.is_paced(1, 1))
        self.assertFalse(s.is_paced(1, 2))

        # Just one cell
        s.set_paced_cell_list([(1, 2)])
        self.assertFalse(s.is_paced(0, 0))
        self.assertFalse(s.is_paced(0, 1))
        self.assertFalse(s.is_paced(0, 2))
        self.assertFalse(s.is_paced(1, 0))
        self.assertFalse(s.is_paced(1, 1))
        self.assertTrue(s.is_paced(1, 2))

        # Set paced cells out of bounds
        self.assertRaisesRegex(
            ValueError, 'out of range', s.set_paced_cell_list, [(-1, 0)])
        self.assertRaisesRegex(
            ValueError, 'out of range', s.set_paced_cell_list, [(2, 0)])
        self.assertRaisesRegex(
            ValueError, 'out of range', s.set_paced_cell_list, [(0, -1)])
        self.assertRaisesRegex(
            ValueError, 'out of range', s.set_paced_cell_list, [(0, 3)])
        self.assertRaisesRegex(
            ValueError, 'out of range', s.set_paced_cell_list, [(-2, -2)])
        self.assertRaisesRegex(
            ValueError, 'out of range', s.set_paced_cell_list, [(5, 5)])

        # Is-paced called out of bounds
        self.assertRaisesRegex(
            ValueError, 'out of range', s.is_paced, -1, 0)
        self.assertRaisesRegex(
            ValueError, 'out of range', s.is_paced, 2, 0)
        self.assertRaisesRegex(
            ValueError, 'out of range', s.is_paced, 0, -1)
        self.assertRaisesRegex(
            ValueError, 'out of range', s.is_paced, 0, 3)
        self.assertRaisesRegex(
            ValueError, 'out of range', s.is_paced, -2, 2)
        self.assertRaisesRegex(
            ValueError, 'out of range', s.is_paced, 5, 5)
        self.assertRaisesRegex(
            ValueError, '2-dimensional', s.is_paced, 1)

    def test_set_state_1d(self):
        # Test the set_state method in 1d

        m, p, _ = myokit.load('example')
        n = 10
        s = myokit.SimulationOpenCL(m, p, n)
        sm = m.state()
        ss = [s.state(x) for x in range(n)]
        for si in ss:
            self.assertEqual(sm, si)

        # Test setting a single, global state
        sx = [0.0] * 8
        self.assertNotEqual(sm, sx)
        s.set_state(sx)
        for i in range(n):
            self.assertEqual(sx, s.state(i))
        self.assertEqual(sx * n, s.state())
        s.set_state(sm)
        self.assertEqual(sm * n, s.state())
        # Test setting a single state
        j = 1
        s.set_state(sx, j)
        for i in range(n):
            if i == j:
                self.assertEqual(s.state(i), sx)
            else:
                self.assertEqual(s.state(i), sm)

    #TODO Add test_set_state_2d

    def test_sim_1d(self):
        # Test running a short 1d simulation (doesn't inspect output)

        m, p, _ = myokit.load('example')
        s = myokit.SimulationOpenCL(m, p, 20)

        # Run, log state and intermediary variable (separate logging code!)
        d = s.run(1, log=['engine.time', 'membrane.V', 'ina.INa'])
        self.assertIn('engine.time', d)
        self.assertIn('0.membrane.V', d)
        self.assertIn('19.membrane.V', d)
        self.assertIn('0.ina.INa', d)
        self.assertIn('19.ina.INa', d)
        self.assertEqual(len(d), 41)

        # Test is_2d()
        self.assertFalse(s.is_2d())
        with WarningCollector() as wc:
            self.assertFalse(s.is2d())
        self.assertIn('deprecated', wc.text())

    def test_sim_2d(self):
        # Test running a short 2d simulation (doesn't inspect output)

        m, p, _ = myokit.load('example')
        n = (8, 8)
        s = myokit.SimulationOpenCL(m, p, n)
        s.set_paced_cells(4, 4)

        # Run, log state and intermediary variable (separate logging code!)
        d = s.run(1, log=['engine.time', 'membrane.V', 'ina.INa'])
        self.assertEqual(len(d), 129)
        self.assertIn('engine.time', d)
        self.assertIn('0.0.membrane.V', d)
        self.assertIn('7.7.membrane.V', d)
        self.assertIn('0.0.ina.INa', d)
        self.assertIn('7.7.ina.INa', d)

        # Test is_2d()
        self.assertTrue(s.is_2d())
        with WarningCollector() as wc:
            self.assertTrue(s.is2d())
        self.assertIn('deprecated', wc.text())


@unittest.skipIf(not OpenCL_FOUND, 'OpenCL not found on this system.')
class FiberTissueSimulationTest(unittest.TestCase):
    """
    Tests the fiber-tissue simulation.
    """
    def test_basic(self):
        # Load models
        mf = os.path.join(DIR_DATA, 'dn-1985-normalised.mmt')
        mt = os.path.join(DIR_DATA, 'lr-1991.mmt')
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
        nty = 6

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

        self.assertEqual(len(logf), 1 + 2 * nfx * nfy)
        self.assertIn('engine.time', logf)
        self.assertIn('0.0.membrane.V', logf)
        self.assertIn(str(nfx - 1) + '.' + str(nfy - 1) + '.membrane.V', logf)
        self.assertIn('0.0.isi.isiCa', logf)
        self.assertIn(str(nfx - 1) + '.' + str(nfy - 1) + '.isi.isiCa', logf)

        self.assertEqual(len(logt), 3 * ntx * nty)
        self.assertIn('0.0.membrane.V', logt)
        self.assertIn(str(ntx - 1) + '.' + str(nty - 1) + '.membrane.V', logt)
        self.assertIn('0.0.ica.Ca_i', logt)
        self.assertIn(str(ntx - 1) + '.' + str(nty - 1) + '.ica.Ca_i', logt)
        self.assertIn('0.0.ica.ICa', logt)
        self.assertIn(str(ntx - 1) + '.' + str(nty - 1) + '.ica.ICa', logt)

    def test_against_cvode(self):
        # Compare the fiber-tissue simulation output with CVODE output

        # Load model
        m = myokit.load_model(os.path.join(DIR_DATA, 'lr-1991.mmt'))

        # Create pacing protocol
        p = myokit.pacing.blocktrain(1000, 2.0, offset=0)

        # Create simulation
        s1 = myokit.FiberTissueSimulation(
            m,
            m,
            p,
            ncells_fiber=(1, 1),
            ncells_tissue=(1, 1),
            nx_paced=1,
            g_fiber=(0, 0),
            g_tissue=(0, 0),
            g_fiber_tissue=0,
            precision=myokit.DOUBLE_PRECISION,
        )
        s1.set_step_size(0.01)

        # Set up logging
        logvars = ['engine.time', 'engine.pace', 'membrane.V', 'ica.ICa']
        logt = myokit.LOG_NONE

        # Run simulation
        tmax = 100
        dlog = 0.1
        with myokit.PyCapture():
            d1, logt = s1.run(tmax, logf=logvars, logt=logt, log_interval=dlog)
        del(logt)
        d1 = d1.npview()

        # Run CVODE simulation
        s2 = myokit.Simulation(m, p)
        s2.set_tolerance(1e-8, 1e-8)
        d2 = s2.run(tmax, logvars, log_interval=dlog).npview()

        # Check implementation of logging point selection
        e0 = np.max(np.abs(d1.time() - d2.time()))

        # Check implementation of pacing
        r1 = d1['engine.pace'] - d2['engine.pace']
        e1 = np.sum(r1**2)

        # Check membrane potential (will have some error!)
        # Using MRMS from Marsh, Ziaratgahi, Spiteri 2012
        r2 = d1['membrane.V', 0, 0] - d2['membrane.V']
        r2 /= (1 + np.abs(d2['membrane.V']))
        e2 = np.sqrt(np.sum(r2**2) / len(r2))

        # Check logging of intermediary variables
        r3 = d1['ica.ICa', 0, 0] - d2['ica.ICa']
        r3 /= (1 + np.abs(d2['ica.ICa']))
        e3 = np.sqrt(np.sum(r3**2) / len(r3))

        if debug:
            import matplotlib.pyplot as plt
            print('Event at t=0')

            print(d1.time()[:7])
            print(d2.time()[:7])
            print(d1.time()[-7:])
            print(d2.time()[-7:])
            print(e0)

            plt.figure()
            plt.suptitle('Pacing signals')
            plt.subplot(2, 1, 1)
            plt.plot(d1.time(), d1['engine.pace'], label='FiberTissue')
            plt.plot(d2.time(), d2['engine.pace'], label='CVODE')
            plt.legend()
            plt.subplot(2, 1, 2)
            plt.plot(d1.time(), r1)
            print(e1)

            plt.figure()
            plt.suptitle('Membrane potential')
            plt.subplot(2, 1, 1)
            plt.plot(d1.time(), d1['membrane.V', 0, 0], label='FiberTissue')
            plt.plot(d2.time(), d2['membrane.V'], label='CVODE')
            plt.legend()
            plt.subplot(2, 1, 2)
            plt.plot(d1.time(), r2)
            print(e2)

            plt.figure()
            plt.suptitle('Calcium current')
            plt.subplot(2, 1, 1)
            plt.plot(d1.time(), d1['ica.ICa', 0, 0], label='FiberTissue')
            plt.plot(d2.time(), d2['ica.ICa'], label='CVODE')
            plt.legend()
            plt.subplot(2, 1, 2)
            plt.plot(d1.time(), r2)
            print(e3)

            plt.show()

        self.assertLess(e0, 1e-10)
        self.assertLess(e1, 1e-14)
        self.assertLess(e2, 0.05)
        self.assertLess(e3, 0.01)


if __name__ == '__main__':
    import sys
    if '-v' in sys.argv:
        print('Running in debug/verbose mode')
        debug = True
    else:
        print('Add -v for more debug output')
    unittest.main()
