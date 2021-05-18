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

from shared import (
    DIR_DATA,
    OpenCL_FOUND,
    #OpenCL_DOUBLE_PRECISION,
    OpenCL_DOUBLE_PRECISION_CONNECTIONS,
    #WarningCollector,
)

# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp


# Show simulation output
debug = False


@unittest.skipIf(not OpenCL_FOUND, 'OpenCL not found on this system.')
class SimulationOpenCLTest(unittest.TestCase):
    """
    Tests the OpenCL simulation class.
    """

    @classmethod
    def setUpClass(cls):
        # Create simulations for later use in testing
        cls.m = myokit.load_model(
            os.path.join(DIR_DATA, 'beeler-1977-model.mmt'))
        cls.p = myokit.pacing.blocktrain(duration=2, offset=1, period=1000)
        cls.s1 = myokit.SimulationOpenCL(cls.m, cls.p, ncells=10)
        cls.s2 = myokit.SimulationOpenCL(cls.m, cls.p, ncells=(4, 4))

    def test_creation(self):
        # Tests opencl simulation creation tasks

        # Model must be valid
        m = myokit.load_model('example')
        m2 = m.clone()
        m2.label('membrane_potential').set_rhs(None)
        self.assertFalse(m2.is_valid())
        self.assertRaises(
            myokit.MissingRhsError, myokit.SimulationOpenCL, m2)

        # Model must have interdependent components
        m2 = m.clone()
        x = m2.get('ik').add_variable('xx')
        x.set_rhs('membrane.i_ion')
        self.assertTrue(m2.has_interdependent_components())
        self.assertRaisesRegex(
            ValueError, 'interdependent', myokit.SimulationOpenCL, m2)

        # Dimensionality must be scalar or 2d tuple
        # (Correct usage is tested later)
        #s = myokit.SimulationOpenCL(m, ncells=1)
        #self.assertEqual(s.shape(), 1)
        #s = myokit.SimulationOpenCL(m, ncells=50)
        #self.assertEqual(s.shape(), 50)
        #s = myokit.SimulationOpenCL(m, ncells=(1,1))
        #self.assertEqual(s.shape(), (1, 1))
        self.assertRaisesRegex(
            ValueError, r'scalar or a tuple \(nx, ny\)',
            myokit.SimulationOpenCL, m, ncells=None)
        self.assertRaisesRegex(
            ValueError, r'scalar or a tuple \(nx, ny\)',
            myokit.SimulationOpenCL, m, ncells=(1,))
        self.assertRaisesRegex(
            ValueError, r'scalar or a tuple \(nx, ny\)',
            myokit.SimulationOpenCL, m, ncells=(1, 1, 1))

        # Number of cells must be at least 1
        self.assertRaisesRegex(
            ValueError, 'at least 1',
            myokit.SimulationOpenCL, m, ncells=-1)
        self.assertRaisesRegex(
            ValueError, 'at least 1',
            myokit.SimulationOpenCL, m, ncells=0)
        self.assertRaisesRegex(
            ValueError, 'at least 1',
            myokit.SimulationOpenCL, m, ncells=(0, 10))
        self.assertRaisesRegex(
            ValueError, 'at least 1',
            myokit.SimulationOpenCL, m, ncells=(10, 0))
        self.assertRaisesRegex(
            ValueError, 'at least 1',
            myokit.SimulationOpenCL, m, ncells=(-1, -1))

        # Precision must be single or double
        self.assertRaisesRegex(
            ValueError, 'Only single and double',
            myokit.SimulationOpenCL, m,
            precision=myokit.SINGLE_PRECISION + myokit.DOUBLE_PRECISION)

        # Membrane potential must be given with label
        m2 = m.clone()
        m2.label('membrane_potential').set_label(None)
        self.assertRaisesRegex(
            ValueError, 'requires the membrane potential',
            myokit.SimulationOpenCL, m2)

        # Membrane potential must be a state
        m2.get('ina.INa').set_label('membrane_potential')
        self.assertRaisesRegex(
            ValueError, 'must be a state variable',
            myokit.SimulationOpenCL, m2)

    def test_calculate_conductance(self):
        # Test the calculate_conductance() method.
        r, sx, chi, dx = 2, 3.4, 5.6, 7.8
        self.assertEqual(
            self.s1.calculate_conductance(r, sx, chi, dx),
            r * sx * chi / ((1 + r) * dx * dx)
        )

    def test_diffusion_free(self):
        # Tests creating a simulation without diffusion

        # Create without diffusion, 1d
        s1 = myokit.SimulationOpenCL(
            self.m, self.p, ncells=3, diffusion=False)

        # Check that various methods are now unavailable
        self.assertRaisesRegex(
            RuntimeError, 'method is unavailable', s1.conductance)
        self.assertRaisesRegex(
            RuntimeError, 'method is unavailable', s1.is_paced, 0)
        self.assertRaisesRegex(
            RuntimeError, 'method is unavailable', s1.neighbours, 0)
        self.assertRaisesRegex(
            RuntimeError, 'method is unavailable', s1.set_conductance)
        self.assertRaisesRegex(
            RuntimeError, 'method is unavailable', s1.set_connections, [])
        self.assertRaisesRegex(
            RuntimeError, 'method is unavailable', s1.set_paced_cells)
        self.assertRaisesRegex(
            RuntimeError, 'method is unavailable', s1.set_paced_cell_list, [])

        # Test that all cells depolarise and are the same
        d = s1.run(10, log=['membrane.V']).npview()
        self.assertGreater(np.max(d['membrane.V', 0]), 0)
        self.assertGreater(np.max(d['membrane.V', 1]), 0)
        self.assertGreater(np.max(d['membrane.V', 2]), 0)
        self.assertTrue(np.all(d['membrane.V', 0] == d['membrane.V', 1]))
        self.assertTrue(np.all(d['membrane.V', 0] == d['membrane.V', 2]))

        # Apply a field and try again (this is its intended use)
        s1.reset()
        s1.set_field('isi.gsBar', [0.05, 0.09, 0.14])
        d = s1.run(10, log=['membrane.V']).npview()
        self.assertGreater(np.max(d['membrane.V', 0]), 0)
        self.assertGreater(np.max(d['membrane.V', 1]), 0)
        self.assertGreater(np.max(d['membrane.V', 2]), 0)
        self.assertFalse(np.all(d['membrane.V', 0] == d['membrane.V', 1]))
        self.assertFalse(np.all(d['membrane.V', 0] == d['membrane.V', 2]))
        self.assertFalse(np.all(d['membrane.V', 1] == d['membrane.V', 2]))

    def test_native_maths(self):
        # Tests running with native maths
        pass

        # Create, run, compare with sim1d

    def test_protocol(self):
        # Tests creating without protocol, and setting one later
        pass

        # Create, run, no stimulus
        # Call set_protocol, reset, run, has stimulus

    def test_rush_larsen(self):
        # Tests running with and without rush-larsen
        pass

        # Create, run, compare with sim1d

    # conductance() -> 1d, 2d
    # is2d(), is_2d() -> 1d, 2d
    # neighbours() -> 1d, 2d, arbitrary
    # set_conductance() -> 1d, 2d
    # set_connections() -> 1d
    # set_field() -> 1d, 2d
    # shape() -> 1d, 2d

    # set_paced_cells() -> 1d, 2d
    # set_paced_cell_list() -> 1d, 2d
    # is_paced() -> 1d, 2d, rectangle, explicit selection

    # run, pre, reset, time, set_time, state, set_state -> 1d, 2d
    # reset, pre, set_default_state

    # set_constant() -> 0d
    # set_step_size(), step_size -> 0d

    def test_connections_simple(self):
        # Tests whether a simple simulation with connections gives the same
        # results as a simulation with set_conductance

        # Make protocol
        bcl = 1000
        duration = 10
        p = myokit.pacing.blocktrain(bcl, duration, level=1)

        # Run simulations
        s1 = myokit.SimulationOpenCL(self.m, p, ncells=2)
        s1.set_paced_cells(1)
        g = 1
        t = 5
        log = ['engine.time', 'membrane.V', 'membrane.i_diff']
        s1.set_conductance(g)
        d1a = s1.run(t, log=log, log_interval=0.1).npview()
        s1.reset()
        s1.set_connections([(0, 1, g)])
        d1b = s1.run(t, log=log, log_interval=0.1).npview()

        if debug:
            # Display the result
            import matplotlib.pyplot as plt
            f = plt.figure(figsize=(10, 10))
            f.subplots_adjust(0.08, 0.07, 0.98, 0.95, 0.2, 0.4)

            x = f.add_subplot(2, 3, 1)
            x.set_title('set_conductance, sp')
            x.set_ylabel('Vm')
            x.plot(d1a['engine.time'], d1a['membrane.V', 0])
            x.plot(d1a['engine.time'], d1a['membrane.V', 1])
            x = f.add_subplot(2, 3, 2)
            x.set_title('set_connections, sp')
            x.set_ylabel('Vm')
            x.plot(d1b['engine.time'], d1b['membrane.V', 0])
            x.plot(d1b['engine.time'], d1b['membrane.V', 1])
            x = f.add_subplot(2, 3, 3)
            x.set_ylabel('Vm')
            x.plot(d1a['engine.time'],
                   d1a['membrane.V', 0] - d1b['membrane.V', 0])
            x.plot(d1a['engine.time'],
                   d1a['membrane.V', 1] - d1b['membrane.V', 1])

            x = f.add_subplot(2, 3, 4)
            x.set_ylabel('I_diff')
            x.plot(d1a['engine.time'], d1a['membrane.i_diff', 0])
            x.plot(d1a['engine.time'], d1a['membrane.i_diff', 1])
            x = f.add_subplot(2, 3, 5)
            x.set_ylabel('I_diff')
            x.plot(d1b['engine.time'], d1b['membrane.i_diff', 0])
            x.plot(d1b['engine.time'], d1b['membrane.i_diff', 1])
            x = f.add_subplot(2, 3, 6)
            x.set_ylabel('I_diff')
            x.plot(d1a['engine.time'],
                   d1a['membrane.i_diff', 0] - d1b['membrane.i_diff', 0])
            x.plot(d1a['engine.time'],
                   d1a['membrane.i_diff', 1] - d1b['membrane.i_diff', 1])

            plt.show()

        # Check results are the same
        e0 = np.abs(d1a['membrane.V', 0] - d1b['membrane.V', 0])
        e1 = np.abs(d1a['membrane.V', 1] - d1b['membrane.V', 1])
        self.assertLess(np.max(e0), 1e-9)
        self.assertLess(np.max(e1), 1e-9)

    @unittest.skipIf(
        not OpenCL_DOUBLE_PRECISION_CONNECTIONS,
        'Required OpenCL extension cl_khr_int64_base_atomics not available.')
    def test_connections_simple_double_precision(self):
        # Repeats test_connections_simple, but with double precision

        # Make protocol
        bcl = 1000
        duration = 10
        p = myokit.pacing.blocktrain(bcl, duration, level=1)

        # Run simulations
        s1 = myokit.SimulationOpenCL(
            self.m, p, ncells=2, precision=myokit.DOUBLE_PRECISION)
        s1.set_paced_cells(1)
        g = 1
        t = 5
        log = ['engine.time', 'membrane.V', 'membrane.i_diff']
        s1.set_conductance(g)
        d1a = s1.run(t, log=log, log_interval=0.1).npview()
        s1.reset()
        s1.set_connections([(0, 1, g)])
        d1b = s1.run(t, log=log, log_interval=0.1).npview()

        if debug:
            # Display the result
            import matplotlib.pyplot as plt
            f = plt.figure(figsize=(10, 10))
            f.subplots_adjust(0.08, 0.07, 0.98, 0.95, 0.2, 0.4)

            x = f.add_subplot(2, 3, 1)
            x.set_title('set_conductance, sp')
            x.set_ylabel('Vm')
            x.plot(d1a['engine.time'], d1a['membrane.V', 0])
            x.plot(d1a['engine.time'], d1a['membrane.V', 1])
            x = f.add_subplot(2, 3, 2)
            x.set_title('set_connections, sp')
            x.set_ylabel('Vm')
            x.plot(d1b['engine.time'], d1b['membrane.V', 0])
            x.plot(d1b['engine.time'], d1b['membrane.V', 1])
            x = f.add_subplot(2, 3, 3)
            x.set_ylabel('Vm')
            x.plot(d1a['engine.time'],
                   d1a['membrane.V', 0] - d1b['membrane.V', 0])
            x.plot(d1a['engine.time'],
                   d1a['membrane.V', 1] - d1b['membrane.V', 1])

            x = f.add_subplot(2, 3, 4)
            x.set_ylabel('I_diff')
            x.plot(d1a['engine.time'], d1a['membrane.i_diff', 0])
            x.plot(d1a['engine.time'], d1a['membrane.i_diff', 1])
            x = f.add_subplot(2, 3, 5)
            x.set_ylabel('I_diff')
            x.plot(d1b['engine.time'], d1b['membrane.i_diff', 0])
            x.plot(d1b['engine.time'], d1b['membrane.i_diff', 1])
            x = f.add_subplot(2, 3, 6)
            x.set_ylabel('I_diff')
            x.plot(d1a['engine.time'],
                   d1a['membrane.i_diff', 0] - d1b['membrane.i_diff', 0])
            x.plot(d1a['engine.time'],
                   d1a['membrane.i_diff', 1] - d1b['membrane.i_diff', 1])

            plt.show()

        # Check results are the same
        e0 = np.abs(d1a['membrane.V', 0] - d1b['membrane.V', 0])
        e1 = np.abs(d1a['membrane.V', 1] - d1b['membrane.V', 1])
        self.assertLess(np.max(e0), 1e-9)
        self.assertLess(np.max(e1), 1e-9)


class SimulationOpenCLFindNanTest(unittest.TestCase):
    """
    Tests the find_nan() method of `SimulationOpenCL`.
    """


'''
class TodoTest(unittest.TestCase):
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
'''


if __name__ == '__main__':

    import sys
    if '-v' in sys.argv:
        print('Running in debug/verbose mode')
        debug = True
    else:
        print('Add -v for more debug output')

    import warnings
    warnings.simplefilter('always')

    unittest.main()
