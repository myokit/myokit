#!/usr/bin/env python3
#
# Tests the OpenCL simulation classes.
#
# Comparisons against CVODE and Simulation1d (with various options e.g. rush
# larsen and native maths) are given in other files.
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

from myokit.tests import (
    CancellingReporter,
    DIR_DATA,
    OpenCL_FOUND,
    OpenCL_DOUBLE_PRECISION_CONNECTIONS,
    WarningCollector,
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
        cls._s0 = cls._s1 = cls._s2 = None

    @property
    def s0(self):
        if self._s0 is None:
            self._s0 = myokit.SimulationOpenCL(self.m, self.p, ncells=1)
        return self._s0

    @property
    def s1(self):
        if self._s1 is None:
            self._s1 = myokit.SimulationOpenCL(self.m, self.p, ncells=10)
        return self._s1

    @property
    def s2(self):
        if self._s2 is None:
            self._s2 = myokit.SimulationOpenCL(self.m, self.p, ncells=(4, 3))
        return self._s2

    def test_monodomain_conductance(self):
        # Test the method to calculate g from monodomain parameters
        k, D, chi, dx, A = 2, 3.4, 5.6, 7.8, 3
        g = D * k / ((k + 1) * chi * dx * dx)
        # Arguments: chi, k, D, dx, A
        self.assertEqual(
            self.s0.monodomain_conductance(chi, k, D, dx, A), g * A)

        # Test the deprecated calculate_conductance() method.
        with WarningCollector() as c:
            # Arguments: r, sx, one_over_chi, dx
            self.assertEqual(
                self.s0.calculate_conductance(k, D, 1 / chi, dx), g)
        self.assertIn('deprecated', c.text())

    def test_conductance(self):
        # Tests setting and getting conductance.

        # 1-dimensional
        try:
            # Test setting and getting
            gx = self.s1.conductance()
            self.assertIsInstance(gx, float)
            self.s1.set_conductance(gx + 1)
            self.assertEqual(self.s1.conductance(), gx + 1)

            # Test conductance changes have an effect
            self.s1.reset()
            self.s1.set_paced_cells(5)
            self.s1.set_conductance()
            d = self.s1.run(10, log=['membrane.V']).npview()
            self.assertGreater(np.max(d['membrane.V', 9]), 0)

            self.s1.reset()
            self.s1.set_conductance(0)
            d = self.s1.run(10, log=['membrane.V']).npview()
            self.assertLess(np.max(d['membrane.V', 9]), 0)
        finally:
            # Restore default values
            self.s1.set_conductance()

        # 2-dimensional
        try:
            # Test setting and getting
            gx, gy = self.s2.conductance()
            self.assertIsInstance(gx, float)
            self.assertIsInstance(gy, float)
            self.s2.set_conductance(gx + 1)
            self.assertEqual(self.s2.conductance(), (gx + 1, gy))
            self.s2.set_conductance(gx + 1, gx + 2)
            self.assertEqual(self.s2.conductance(), (gx + 1, gx + 2))
            self.s2.set_conductance(gy=gx + 3)
            self.assertEqual(self.s2.conductance()[1], gx + 3)

            # Test conductance changes have an effect
            self.s2.reset()
            self.s2.set_paced_cells(2, 2)
            self.s2.set_conductance(10, 10)
            d = self.s2.run(5, log=['membrane.V']).npview()
            self.assertGreater(np.max(d['membrane.V', 3, 0]), -80)
            self.assertGreater(np.max(d['membrane.V', 0, 2]), -80)
            self.assertGreater(np.max(d['membrane.V', 3, 2]), -80)

            self.s2.reset()
            self.s2.set_conductance(10, 0)
            d = self.s2.run(5, log=['membrane.V']).npview()
            self.assertGreater(np.max(d['membrane.V', 3, 0]), -80)
            self.assertLess(np.max(d['membrane.V', 0, 2]), -80)
            self.assertLess(np.max(d['membrane.V', 3, 2]), -80)

            self.s2.reset()
            self.s2.set_conductance(0, 10)
            d = self.s2.run(5, log=['membrane.V']).npview()
            self.assertLess(np.max(d['membrane.V', 3, 0]), -80)
            self.assertGreater(np.max(d['membrane.V', 0, 2]), -80)
            self.assertLess(np.max(d['membrane.V', 3, 2]), -80)

            self.s2.reset()
            self.s2.set_conductance(0, 0)
            d = self.s2.run(5, log=['membrane.V']).npview()
            self.assertLess(np.max(d['membrane.V', 3, 0]), 0)
            self.assertLess(np.max(d['membrane.V', 0, 2]), 0)
            self.assertLess(np.max(d['membrane.V', 3, 2]), 0)

            # Bad values
            self.assertRaisesRegex(
                ValueError, 'Invalid conductance gx',
                self.s2.set_conductance, -1, 10)
            self.assertRaisesRegex(
                ValueError, 'Invalid conductance gy',
                self.s2.set_conductance, 10, -1)

        finally:
            # Restore default values
            self.s2.set_paced_cells()
            self.s2.set_conductance()

    def test_conductance_field_set(self):
        # Tests setting conductance fields.

        # 1d
        try:
            # Fields unset scalar conductances
            self.assertIsNotNone(self.s1.conductance())
            self.s1.set_conductance_field(list(range(9)))
            self.assertIsNone(self.s1.conductance())

            # Set wrong length
            self.assertRaisesRegex(
                ValueError, 'must have length',
                self.s1.set_conductance_field, list(range(8)))
            self.assertRaisesRegex(
                ValueError, 'must have length',
                self.s1.set_conductance_field, list(range(10)))

            # Set negative values
            x = np.arange(9)
            x[3] = -1
            self.assertRaisesRegex(
                ValueError, 'negative', self.s1.set_conductance_field, x)

            # Set gy
            x = y = np.arange(9)
            self.assertRaisesRegex(
                ValueError, 'must be None',
                self.s1.set_conductance_field, x, y)
        finally:
            self.s1.set_conductance()

        # 2d
        try:
            # Fields unset scalar conductances
            # Shape is (3, 4)
            x = np.ones((3, 3))
            y = np.ones((2, 4))
            self.assertIsNotNone(self.s2.conductance())
            self.s2.set_conductance_field(x, y)
            self.assertIsNone(self.s2.conductance())

            # Set wrong shapes
            self.assertRaisesRegex(
                ValueError, r'dimensions \(3, 3\)',
                self.s2.set_conductance_field, y, y)
            self.assertRaisesRegex(
                ValueError, r'dimensions \(2, 4\)',
                self.s2.set_conductance_field, x, x)

            # Set negative values
            x[2, 2] = -1
            self.assertRaisesRegex(
                ValueError, 'negative', self.s2.set_conductance_field, x, y)
            x[2, 2] = 1
            y[1, 0] = -1
            self.assertRaisesRegex(
                ValueError, 'negative', self.s2.set_conductance_field, x, y)

            # Don't set gy
            self.assertRaisesRegex(
                ValueError, 'must be set', self.s2.set_conductance_field, x)
        finally:
            self.s2.set_conductance()

    def test_conductance_field_run_1d(self):
        # Tests running with conductance fields, in 1d.

        try:
            # Set, test all depol
            self.s1.reset()
            self.s1.set_paced_cells(3)
            x = np.ones(9)
            self.s1.set_conductance_field(x)

            d = self.s1.run(
                15, log=['engine.time', 'membrane.V'], log_interval=0.1)
            if debug:
                import matplotlib.pyplot as plt
                f = plt.figure(figsize=(10, 10))
                f.subplots_adjust(0.08, 0.07, 0.98, 0.95, 0.2, 0.4)
                ax = f.add_subplot(1, 1, 1)
                for i in range(10):
                    ax.plot(d.time(), d['membrane.V', i])
                plt.show()
            self.assertGreater(np.max(d['membrane.V', 0]), 0)
            self.assertGreater(np.max(d['membrane.V', 4]), 0)
            self.assertGreater(np.max(d['membrane.V', 7]), 0)
            self.assertGreater(np.max(d['membrane.V', 9]), 0)

            # Set, test some depol
            self.s1.reset()
            self.s1.set_paced_cells(x=3, nx=3)
            x = np.ones(9)
            x[0] = 0
            x[-2:] = 0
            self.s1.set_conductance_field(x)
            d = self.s1.run(
                15, log=['engine.time', 'membrane.V'], log_interval=0.1)
            if debug:
                import matplotlib.pyplot as plt
                f = plt.figure(figsize=(10, 10))
                f.subplots_adjust(0.08, 0.07, 0.98, 0.95, 0.2, 0.4)
                ax = f.add_subplot(1, 1, 1)
                for i in range(10):
                    ax.plot(d.time(), d['membrane.V', i])
                plt.show()
            self.assertLess(np.max(d['membrane.V', 0]), 0)
            self.assertGreater(np.max(d['membrane.V', 1]), 0)
            self.assertGreater(np.max(d['membrane.V', 2]), 0)
            self.assertGreater(np.max(d['membrane.V', 3]), 0)
            self.assertGreater(np.max(d['membrane.V', 4]), 0)  # Paced
            self.assertGreater(np.max(d['membrane.V', 5]), 0)  # Paced
            self.assertGreater(np.max(d['membrane.V', 6]), 0)  # Paced
            self.assertGreater(np.max(d['membrane.V', 7]), 0)
            self.assertLess(np.max(d['membrane.V', 8]), 0)
            self.assertLess(np.max(d['membrane.V', 9]), 0)

        finally:
            self.s1.set_paced_cells()
            self.s1.set_conductance()

    def test_conductance_field_run_2d(self):
        # Tests running with conductance fields, in 2d.

        # Set, test some depol
        try:
            # Shape is (y=3, x=4)
            x = np.ones((3, 3))
            y = np.ones((2, 4))
            # Don't stimulate cell x=2, y=1
            x[1, 1:3] = 0
            y[0:2, 2] = 0
            self.s2.reset()
            self.s2.set_paced_cells(2, 2)
            self.s2.set_conductance_field(x, y)
            d = self.s2.run(
                15, log=['engine.time', 'membrane.V'], log_interval=0.1)
            if debug:
                import matplotlib.pyplot as plt
                f = plt.figure(figsize=(10, 10))
                f.subplots_adjust(0.08, 0.07, 0.98, 0.95, 0.2, 0.4)
                k = 0
                for i in range(3):
                    for j in range(4):
                        k += 1
                        ax = f.add_subplot(3, 4, k)
                        ax.plot(d.time(), d['membrane.V', j, i])
                plt.show()
            self.assertGreater(np.max(d['membrane.V', 0, 0]), 0)
            self.assertGreater(np.max(d['membrane.V', 1, 0]), 0)
            self.assertGreater(np.max(d['membrane.V', 2, 0]), 0)
            self.assertGreater(np.max(d['membrane.V', 3, 0]), 0)
            self.assertGreater(np.max(d['membrane.V', 0, 1]), 0)
            self.assertGreater(np.max(d['membrane.V', 1, 1]), 0)
            self.assertLess(np.max(d['membrane.V', 2, 1]), 0)
            self.assertGreater(np.max(d['membrane.V', 3, 1]), 0)
            self.assertGreater(np.max(d['membrane.V', 0, 2]), 0)
            self.assertGreater(np.max(d['membrane.V', 1, 2]), 0)
            self.assertGreater(np.max(d['membrane.V', 2, 2]), 0)
            self.assertGreater(np.max(d['membrane.V', 3, 2]), 0)
        finally:
            self.s2.set_paced_cells()
            self.s2.set_conductance()

    def test_connections_set(self):
        # Tests setting connections.

        # Connections unsets conductance
        try:
            self.s1.set_connections([[0, 1, 1]])
            self.assertIsNone(self.s1.conductance())
        finally:
            self.s1.set_conductance()

        # Connections cannot be set on 2d sim
        try:
            self.assertRaisesRegex(
                RuntimeError, 'in 1d mode',
                self.s2.set_connections, [[0, 1, 1]])
        finally:
            self.s2.set_conductance()

        # Test list is checked
        try:
            self.s1.set_connections(((0, 1, 1),))
            self.s1.set_connections(([0, 1, 1], (0, 2, 1)))
            self.assertRaisesRegex(
                ValueError, 'Connection list cannot be None',
                self.s1.set_connections, None)

            # Wrong list contents
            self.assertRaisesRegex(
                ValueError, 'list of 3-tuples',
                self.s1.set_connections, [[1, 1]])
            self.assertRaisesRegex(
                ValueError, 'list of 3-tuples',
                self.s1.set_connections, [1, 1, 1])
            self.assertRaisesRegex(
                ValueError, 'list of 3-tuples',
                self.s1.set_connections, 'hello')

            # Invalid indices
            self.assertRaisesRegex(
                ValueError, 'Invalid connection',
                self.s1.set_connections, [[-1, 0, 1]])
            self.assertRaisesRegex(
                ValueError, 'Invalid connection',
                self.s1.set_connections, [[0, -2, 1]])
            self.assertRaisesRegex(
                ValueError, 'Invalid connection',
                self.s1.set_connections, [[10, 0, 1]])
            self.assertRaisesRegex(
                ValueError, 'Invalid connection',
                self.s1.set_connections, [[0, 10, 1]])

            # Duplicates
            self.assertRaisesRegex(
                ValueError, 'Duplicate connection',
                self.s1.set_connections, [[1, 0, 1], [1, 0, 1]])
            self.assertRaisesRegex(
                ValueError, 'Duplicate connection',
                self.s1.set_connections, [[1, 0, 1], [1, 0, 2]])
            self.assertRaisesRegex(
                ValueError, 'Duplicate connection',
                self.s1.set_connections, [[1, 0, 1], [0, 1, 1]])

            # Negative conductances
            self.assertRaisesRegex(
                ValueError, 'Invalid conductance',
                self.s1.set_connections, [[1, 0, 1], [0, 2, -1]])

        finally:
            self.s1.set_conductance()

    def test_connections_run(self):
        # Tests whether a simple simulation with connections gives the same
        # results as a simulation with set_conductance

        # Make protocol
        bcl = 1000
        duration = 10
        p = myokit.pacing.blocktrain(bcl, duration, level=1)

        # Run simulations
        try:
            self.s1.reset()
            self.s1.set_paced_cells(3)
            g = 5
            t = 10
            dt = 0.1
            log = ['engine.time', 'membrane.V', 'membrane.i_diff']
            self.s1.set_conductance(g, 0)
            d1a = self.s1.run(t, log=log, log_interval=dt).npview()
            self.s1.reset()
            self.s1.set_connections([(i, i + 1, g) for i in range(9)])
            d1b = self.s1.run(t, log=log, log_interval=dt).npview()
        finally:
            self.s1.set_conductance()

        if debug:
            # Display the result
            import matplotlib.pyplot as plt
            f = plt.figure(figsize=(10, 10))
            f.subplots_adjust(0.08, 0.07, 0.98, 0.95, 0.2, 0.4)

            x = f.add_subplot(2, 2, 1)
            x.set_ylabel('Vm')
            for i in range(10):
                x.plot(d1a['engine.time'], d1a['membrane.V', i], lw=2,
                       alpha=0.5)
            for i in range(10):
                x.plot(d1b['engine.time'], d1b['membrane.V', i], '--')

            x = f.add_subplot(2, 2, 2)
            x.set_ylabel('Vm')
            for i in range(10):
                x.plot(d1a['engine.time'],
                       d1a['membrane.V', i] - d1b['membrane.V', i])

            x = f.add_subplot(2, 2, 3)
            x.set_ylabel('I_diff')
            for i in range(10):
                #x.plot(d1a['engine.time'], d1a['membrane.i_diff', i], lw=2,
                #       alpha=0.5)
                x.plot(d1b['engine.time'], d1b['membrane.i_diff', i], '--')

            x = f.add_subplot(2, 2, 4)
            x.set_ylabel('I_diff')
            for i in range(10):
                x.plot(d1a['engine.time'],
                       d1a['membrane.i_diff', i] - d1b['membrane.i_diff', i])

            plt.show()

        # Check results are the same
        e0 = np.abs(d1a['membrane.V', 0] - d1b['membrane.V', 0])
        e1 = np.abs(d1a['membrane.V', 9] - d1b['membrane.V', 9])
        self.assertLess(np.max(e0), 1e-4)
        self.assertLess(np.max(e1), 1e-4)

    @unittest.skipIf(
        not OpenCL_DOUBLE_PRECISION_CONNECTIONS,
        'Required OpenCL extension cl_khr_int64_base_atomics not available.')
    def test_connections_run_double_precision(self):
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

    def test_creation(self):
        # Tests opencl simulation creation tasks

        # Model must be valid
        m2 = self.m.clone()
        m2.label('membrane_potential').set_rhs(None)
        self.assertFalse(m2.is_valid())
        self.assertRaises(
            myokit.MissingRhsError, myokit.SimulationOpenCL, m2)

        # Model must have interdependent components
        m2 = self.m.clone()
        x = m2.get('ix1').add_variable('xx')
        x.set_rhs('membrane.i_ion')
        self.assertTrue(m2.has_interdependent_components())
        self.assertRaisesRegex(
            ValueError, 'interdependent', myokit.SimulationOpenCL, m2)

        # Dimensionality must be scalar or 2d tuple
        # (Correct usage is tested later)
        s = myokit.SimulationOpenCL(self.m, ncells=1)
        self.assertEqual(s.shape(), 1)
        s = myokit.SimulationOpenCL(self.m, ncells=50)
        self.assertEqual(s.shape(), 50)
        s = myokit.SimulationOpenCL(self.m, ncells=(2, 1))
        self.assertEqual(s.shape(), (1, 2))
        self.assertRaisesRegex(
            ValueError, r'scalar or a tuple \(nx, ny\)',
            myokit.SimulationOpenCL, self.m, ncells=None)
        self.assertRaisesRegex(
            ValueError, r'scalar or a tuple \(nx, ny\)',
            myokit.SimulationOpenCL, self.m, ncells=(1,))
        self.assertRaisesRegex(
            ValueError, r'scalar or a tuple \(nx, ny\)',
            myokit.SimulationOpenCL, self.m, ncells=(1, 1, 1))

        # Number of cells must be at least 1
        self.assertRaisesRegex(
            ValueError, 'at least 1',
            myokit.SimulationOpenCL, self.m, ncells=-1)
        self.assertRaisesRegex(
            ValueError, 'at least 1',
            myokit.SimulationOpenCL, self.m, ncells=0)
        self.assertRaisesRegex(
            ValueError, 'at least 1',
            myokit.SimulationOpenCL, self.m, ncells=(0, 10))
        self.assertRaisesRegex(
            ValueError, 'at least 1',
            myokit.SimulationOpenCL, self.m, ncells=(10, 0))
        self.assertRaisesRegex(
            ValueError, 'at least 1',
            myokit.SimulationOpenCL, self.m, ncells=(-1, -1))

        # Precision must be single or double
        self.assertRaisesRegex(
            ValueError, 'Only single and double',
            myokit.SimulationOpenCL, self.m,
            precision=myokit.SINGLE_PRECISION + myokit.DOUBLE_PRECISION)

        # Membrane potential must be given with label
        m2 = self.m.clone()
        m2.label('membrane_potential').set_label(None)
        self.assertRaisesRegex(
            ValueError, 'requires the membrane potential',
            myokit.SimulationOpenCL, m2)

        # Membrane potential must be a state
        m2.get('ina.INa').set_label('membrane_potential')
        self.assertRaisesRegex(
            ValueError, 'must be a state variable',
            myokit.SimulationOpenCL, m2)

    def test_diffusion_free(self):
        # Tests creating a simulation without diffusion

        # Create without diffusion, 1d
        s = myokit.SimulationOpenCL(
            self.m, self.p, ncells=3, diffusion=False)

        # Check that various methods are now unavailable
        self.assertRaisesRegex(
            RuntimeError, 'method is unavailable', s.conductance)
        self.assertRaisesRegex(
            RuntimeError, 'method is unavailable', s.is_paced, 0)
        self.assertRaisesRegex(
            RuntimeError, 'method is unavailable', s.neighbours, 0)
        self.assertRaisesRegex(
            RuntimeError, 'method is unavailable', s.set_conductance)
        self.assertRaisesRegex(
            RuntimeError, 'method is unavailable', s.set_connections, [])
        self.assertRaisesRegex(
            RuntimeError, 'method is unavailable', s.set_paced_cells)
        self.assertRaisesRegex(
            RuntimeError, 'method is unavailable', s.set_paced_cell_list, [])
        self.assertRaisesRegex(
            RuntimeError, 'method is unavailable',
            s.set_conductance_field, [1, 1])

        # Test that all cells depolarise and are the same
        d = s.run(10, log=['membrane.V']).npview()
        self.assertGreater(np.max(d['membrane.V', 0]), 0)
        self.assertGreater(np.max(d['membrane.V', 1]), 0)
        self.assertGreater(np.max(d['membrane.V', 2]), 0)
        self.assertTrue(np.all(d['membrane.V', 0] == d['membrane.V', 1]))
        self.assertTrue(np.all(d['membrane.V', 0] == d['membrane.V', 2]))

        # Apply a field and try again (this is its intended use)
        s.reset()
        s.set_field('isi.gsBar', [0.05, 0.09, 0.14])
        d = s.run(10, log=['membrane.V']).npview()
        self.assertGreater(np.max(d['membrane.V', 0]), 0)
        self.assertGreater(np.max(d['membrane.V', 1]), 0)
        self.assertGreater(np.max(d['membrane.V', 2]), 0)
        self.assertFalse(np.all(d['membrane.V', 0] == d['membrane.V', 1]))
        self.assertFalse(np.all(d['membrane.V', 0] == d['membrane.V', 2]))
        self.assertFalse(np.all(d['membrane.V', 1] == d['membrane.V', 2]))

        # Create without diffusion, 1d, no membrane_potential label
        m = self.m.clone()
        m.label('membrane_potential').set_label(None)
        s = myokit.SimulationOpenCL(m, self.p, ncells=3, diffusion=False)

        # Test that all cells depolarise and are the same
        d = s.run(10, log=['membrane.V']).npview()
        self.assertGreater(np.max(d['membrane.V', 0]), 0)
        self.assertGreater(np.max(d['membrane.V', 1]), 0)
        self.assertGreater(np.max(d['membrane.V', 2]), 0)
        self.assertTrue(np.all(d['membrane.V', 0] == d['membrane.V', 1]))
        self.assertTrue(np.all(d['membrane.V', 0] == d['membrane.V', 2]))

    def test_neighbours_0d(self):
        # Test listing neighbours in a 0d simulation

        x = self.s0.neighbours(0)
        self.assertEqual(len(x), 0)
        self.assertRaisesRegex(
            IndexError, 'out of range', self.s0.neighbours, -1)
        self.assertRaisesRegex(
            IndexError, 'out of range', self.s0.neighbours, 1)
        self.assertRaisesRegex(
            ValueError, '1-dimensional', self.s0.neighbours, 0, 1)

    def test_neighbours_1d(self):
        # Test listing neighbours in a 1d simulation

        # Left edge
        x = self.s1.neighbours(0)
        self.assertEqual(len(x), 1)
        self.assertIn(1, x)
        # Middle
        x = self.s1.neighbours(1)
        self.assertEqual(len(x), 2)
        self.assertIn(0, x)
        self.assertIn(2, x)
        # Right edge
        x = self.s1.neighbours(9)
        self.assertEqual(len(x), 1)
        self.assertIn(8, x)

        # Out of range
        self.assertRaisesRegex(
            IndexError, 'out of range', self.s1.neighbours, -1)
        self.assertRaisesRegex(
            IndexError, 'out of range', self.s1.neighbours, 10)
        self.assertRaisesRegex(
            ValueError, '1-dimensional', self.s1.neighbours, 0, 1)

    def test_neighbours_1d_connections(self):
        # Test listing neighbours in a 1d simulation with arbitrary geometry

        try:
            g = 1
            self.s1.set_connections(
                [(0, 1, g), (0, 2, g), (3, 0, g), (3, 2, g)])
            x = self.s1.neighbours(0)
            self.assertEqual(len(x), 3)
            self.assertIn(1, x)
            self.assertIn(2, x)
            self.assertIn(3, x)
            x = self.s1.neighbours(1)
            self.assertEqual(len(x), 1)
            self.assertIn(0, x)
            x = self.s1.neighbours(2)
            self.assertEqual(len(x), 2)
            self.assertIn(0, x)
            self.assertIn(3, x)
            x = self.s1.neighbours(3)
            self.assertEqual(len(x), 2)
            self.assertIn(0, x)
            self.assertIn(2, x)
            x = self.s1.neighbours(4)
            self.assertEqual(len(x), 0)
        finally:
            # Restore defaults
            self.s1.set_conductance()

    def test_neighbours_2d(self):
        # Test listing neighbours in a 2d simulation

        # Corners
        x = self.s2.neighbours(0, 0)
        self.assertEqual(len(x), 2)
        self.assertIn((1, 0), x)
        self.assertIn((0, 1), x)
        x = self.s2.neighbours(3, 2)
        self.assertEqual(len(x), 2)
        self.assertIn((3, 1), x)
        self.assertIn((2, 2), x)

        # Edges
        x = self.s2.neighbours(1, 0)
        self.assertEqual(len(x), 3)
        self.assertIn((0, 0), x)
        self.assertIn((2, 0), x)
        self.assertIn((1, 1), x)
        x = self.s2.neighbours(3, 1)
        self.assertEqual(len(x), 3)
        self.assertIn((2, 1), x)
        self.assertIn((3, 0), x)
        self.assertIn((3, 2), x)

        # Middle
        x = self.s2.neighbours(1, 1)
        self.assertEqual(len(x), 4)
        self.assertIn((0, 1), x)
        self.assertIn((2, 1), x)
        self.assertIn((1, 0), x)
        self.assertIn((1, 2), x)
        x = self.s2.neighbours(2, 1)
        self.assertEqual(len(x), 4)
        self.assertIn((1, 1), x)
        self.assertIn((3, 1), x)
        self.assertIn((2, 0), x)
        self.assertIn((2, 2), x)

        # Out of range
        self.assertRaisesRegex(
            IndexError, 'out of range', self.s2.neighbours, -1, 0)
        self.assertRaisesRegex(
            IndexError, 'out of range', self.s2.neighbours, 0, -1)
        self.assertRaisesRegex(
            IndexError, 'out of range', self.s2.neighbours, 4, 0)
        self.assertRaisesRegex(
            IndexError, 'out of range', self.s2.neighbours, 0, 3)
        self.assertRaisesRegex(
            ValueError, '2-dimensional', self.s2.neighbours, 0)

    def test_protocol(self):
        # Tests changing the protocol

        # Run with protocol, check for depolarisation
        self.s0.reset()
        d0 = self.s0.run(3, log=['engine.pace']).npview()
        self.assertEqual(np.max(d0['engine.pace']), 1)

        try:
            # Unset protocol
            self.s0.reset()
            self.s0.set_protocol(None)
            d0 = self.s0.run(3, log=['engine.pace']).npview()
            self.assertEqual(np.max(d0['engine.pace']), 0)

            # Add new protocol
            p = myokit.pacing.blocktrain(period=1000, duration=2, offset=3)
            self.s0.reset()
            self.s0.set_protocol(p)
            d0 = self.s0.run(3, log=['engine.pace']).npview()
            self.assertEqual(np.max(d0['engine.pace']), 0)
            d0 = self.s0.run(3, log=['engine.pace']).npview()
            self.assertEqual(np.max(d0['engine.pace']), 1)

        finally:
            # Restore protocol
            self.s0.set_protocol(self.p)

    def test_run(self):
        # Test running, with pre, state, default state, etc.

        # Test initial state
        self.s0.reset()
        x0 = self.s0.default_state()
        self.assertEqual(x0, self.s0.state())
        self.assertEqual(0, self.s0.time())

        # Test running, then resetting to default state
        self.s0.run(1)
        x1 = self.s0.state()
        self.assertEqual(x0, self.s0.default_state())
        self.assertNotEqual(x0, x1)
        self.assertEqual(1, self.s0.time())
        self.s0.reset()
        self.assertEqual(x0, self.s0.default_state())
        self.assertEqual(x0, self.s0.state())
        self.assertEqual(0, self.s0.time())

        try:
            # Test pre()
            self.s0.pre(1)
            self.assertEqual(x1, self.s0.default_state())
            self.assertEqual(x1, self.s0.state())
            self.assertEqual(0, self.s0.time())

            # Test running and resetting to new default
            self.s0.run(1)
            self.assertEqual(x1, self.s0.default_state())
            self.assertNotEqual(x1, self.s0.state())
            self.assertEqual(1, self.s0.time())
            self.s0.reset()
            self.assertEqual(x1, self.s0.default_state())
            self.assertEqual(x1, self.s0.state())
            self.assertEqual(0, self.s0.time())

            # Test setting time
            self.s0.set_time(10)
            self.assertEqual(self.s0.time(), 10)
            self.s0.run(1)
            self.assertEqual(self.s0.time(), 11)
            self.assertRaisesRegex(
                ValueError, 'negative', self.s0.set_time, -1)

            # Test running for a negative amount of time
            self.assertRaisesRegex(
                ValueError, 'negative', self.s0.run, -1)

        finally:
            self.s0.set_default_state(x0)

    def test_run_progress_reporter(self):
        # Test running with a progress reporter

        with myokit.tools.capture() as c:
            self.s0.run(3, progress=myokit.ProgressPrinter())
        self.assertTrue(c.text() != '')

        # Not a progress reporter
        self.assertRaisesRegex(
            ValueError, 'progress', self.s0.run, 1, progress=True)

        # User cancel
        self.assertRaises(
            myokit.SimulationCancelledError,
            self.s0.run, 20, progress=CancellingReporter(0))

    def test_set_constant(self):
        # Test set_constant (interface only, rest is in cvode comparison)

        m2 = self.m.clone()
        v = m2['membrane'].add_variable('calculated_constant')
        v.set_rhs('3 * C')
        C = m2.get('membrane.C')
        s = myokit.SimulationOpenCL(m2)

        # Call with name
        s.set_constant('membrane.C', 3)
        # Call with variable
        s.set_constant(C, 2)

        # Not allowed on a non-literal (even a constant)
        self.assertRaisesRegex(
            ValueError, 'not a literal', s.set_constant, 'membrane.V', 1)
        self.assertRaisesRegex(
            ValueError, 'not a literal', s.set_constant, 'ina.INa', 3)
        self.assertRaisesRegex(
            ValueError, 'not a literal', s.set_constant, 'engine.time', 2)
        self.assertRaisesRegex(
            ValueError, 'not a literal', s.set_constant, v, 2)

    def test_set_field(self):
        # Test set_field (interface only, rest is in cvode comparison)

        # 1-dimensional
        try:
            x = list(range(10))
            self.s1.set_field('membrane.C', x)
            self.s1.set_field('membrane.C', x)  # overwriting is fine
            self.s1.remove_field('membrane.C')
            self.s1.set_field(self.m.get('membrane.C'), x)
            self.s1.remove_field(self.m.get('membrane.C'))
            self.assertRaises(KeyError, self.s1.remove_field, 'membrane.C')
            self.assertRaises(KeyError, self.s1.remove_field, 'membrane.C')
            self.assertRaises(KeyError, self.s1.remove_field, 'membrane.V')
            self.assertRaisesRegex(
                ValueError, 'constant',
                self.s1.set_field, 'membrane.V', x)
            self.assertRaisesRegex(
                ValueError, 'Bound',
                self.s1.set_field, 'engine.time', x)
            self.assertRaisesRegex(
                ValueError, 'length',
                self.s1.set_field, 'membrane.C', list(range(9)))
            self.assertRaisesRegex(
                ValueError, 'length',
                self.s1.set_field, 'membrane.C', list(range(11)))
        finally:
            try:
                self.s1.remove_field('membrane.C')
            except Exception:
                pass

        # 2-dimensional
        try:
            x = np.zeros(self.s2.shape())
            self.s2.set_field('membrane.C', x)
            self.assertRaisesRegex(
                ValueError, 'dimensions',
                self.s2.set_field, 'membrane.C', list(range(4)))
            self.assertRaisesRegex(
                ValueError, 'dimensions',
                self.s2.set_field, 'membrane.C', np.zeros((4, 4)))
            self.assertRaisesRegex(
                ValueError, 'dimensions',
                self.s2.set_field, 'membrane.C', np.zeros((1, 3)))
        finally:
            try:
                self.s2.remove_field('membrane.C')
            except Exception:
                pass

    def test_set_paced_cells_1d(self):
        # Test the set_paced_cells and is_paced methods in 1d (interface only,
        # does not test running the simulation)

        try:
            self.s1.set_paced_cells(3)
            self.assertTrue(self.s1.is_paced(0))
            self.assertTrue(self.s1.is_paced(1))
            self.assertTrue(self.s1.is_paced(2))
            self.assertFalse(self.s1.is_paced(3))
            self.assertFalse(self.s1.is_paced(4))

            # Set with an offset
            self.s1.set_paced_cells(nx=2, x=2)
            self.assertFalse(self.s1.is_paced(0))
            self.assertFalse(self.s1.is_paced(1))
            self.assertTrue(self.s1.is_paced(2))
            self.assertTrue(self.s1.is_paced(3))
            self.assertFalse(self.s1.is_paced(4))

            # Set final cells with negative number
            self.s1.set_paced_cells(nx=-2)
            self.assertFalse(self.s1.is_paced(0))
            self.assertFalse(self.s1.is_paced(1))
            self.assertFalse(self.s1.is_paced(2))
            self.assertTrue(self.s1.is_paced(8))
            self.assertTrue(self.s1.is_paced(9))

            # Set with an offset and a negative number
            self.s1.set_paced_cells(nx=-2, x=4)
            self.assertFalse(self.s1.is_paced(0))
            self.assertFalse(self.s1.is_paced(1))
            self.assertTrue(self.s1.is_paced(2))
            self.assertTrue(self.s1.is_paced(3))
            self.assertFalse(self.s1.is_paced(4))

            # Set with a negative offset and negative number
            self.s1.set_paced_cells(nx=-2, x=-2)
            self.assertFalse(self.s1.is_paced(5))
            self.assertTrue(self.s1.is_paced(6))
            self.assertTrue(self.s1.is_paced(7))
            self.assertFalse(self.s1.is_paced(8))
            self.assertFalse(self.s1.is_paced(9))

        finally:
            # Restore defaults
            self.s1.set_paced_cells()

    def test_set_paced_cell_list_1d(self):
        # Test the set_paced_cell_list and is_paced methods in 1d (interface
        # only, does not test running the simulation)

        try:
            self.s1.set_paced_cell_list([0, 2, 3])
            self.assertTrue(self.s1.is_paced(0))
            self.assertFalse(self.s1.is_paced(1))
            self.assertTrue(self.s1.is_paced(2))
            self.assertTrue(self.s1.is_paced(3))
            self.assertFalse(self.s1.is_paced(4))

            # Duplicate paced cells
            self.s1.set_paced_cell_list([0, 0, 0, 0, 3, 3, 3])
            self.assertTrue(self.s1.is_paced(0))
            self.assertFalse(self.s1.is_paced(1))
            self.assertFalse(self.s1.is_paced(2))
            self.assertTrue(self.s1.is_paced(3))
            self.assertFalse(self.s1.is_paced(4))

            # Just one cell
            self.s1.set_paced_cell_list([2])
            self.assertFalse(self.s1.is_paced(0))
            self.assertFalse(self.s1.is_paced(1))
            self.assertTrue(self.s1.is_paced(2))
            self.assertFalse(self.s1.is_paced(3))
            self.assertFalse(self.s1.is_paced(4))

            # Set paced cells out of bounds
            self.assertRaisesRegex(
                IndexError, 'out of range', self.s1.set_paced_cell_list, [-1])
            self.assertRaisesRegex(
                IndexError, 'out of range', self.s1.set_paced_cell_list, [10])

            # Is-paced called out of bounds
            self.assertRaisesRegex(
                IndexError, 'out of range', self.s1.is_paced, -1)
            self.assertRaisesRegex(
                IndexError, 'out of range', self.s1.is_paced, 10)
            self.assertRaisesRegex(
                ValueError, '1-dimensional', self.s1.is_paced, 3, 3)

        finally:
            # Restore defaults
            self.s1.set_paced_cells()

    def test_set_paced_cells_2d(self):
        # Test the set_paced_cells and is_paced methods in 2d (interface only,
        # does not test running the simulation)

        try:
            self.s2.set_paced_cells(1, 2)
            self.assertTrue(self.s2.is_paced(0, 0))
            self.assertTrue(self.s2.is_paced(0, 1))
            self.assertFalse(self.s2.is_paced(0, 2))
            self.assertFalse(self.s2.is_paced(1, 0))
            self.assertFalse(self.s2.is_paced(1, 1))
            self.assertFalse(self.s2.is_paced(1, 2))

            # Set with an offset
            self.s2.set_paced_cells(x=1, y=1, nx=1, ny=2)
            self.assertFalse(self.s2.is_paced(0, 0))
            self.assertFalse(self.s2.is_paced(0, 1))
            self.assertFalse(self.s2.is_paced(0, 2))
            self.assertFalse(self.s2.is_paced(1, 0))
            self.assertTrue(self.s2.is_paced(1, 1))
            self.assertTrue(self.s2.is_paced(1, 2))
            self.assertFalse(self.s2.is_paced(2, 1))

            # Set final cells with negative number
            self.s2.set_paced_cells(nx=-1, ny=-1)
            self.assertFalse(self.s2.is_paced(0, 0))
            self.assertFalse(self.s2.is_paced(0, 1))
            self.assertFalse(self.s2.is_paced(0, 2))
            self.assertFalse(self.s2.is_paced(2, 2))
            self.assertTrue(self.s2.is_paced(3, 2))

            # Set with an offset and a negative number
            self.s2.set_paced_cells(x=1, y=2, nx=-1, ny=-2)
            self.assertTrue(self.s2.is_paced(0, 0))
            self.assertTrue(self.s2.is_paced(0, 1))
            self.assertFalse(self.s2.is_paced(0, 2))
            self.assertFalse(self.s2.is_paced(1, 0))
            self.assertFalse(self.s2.is_paced(1, 1))
            self.assertFalse(self.s2.is_paced(1, 2))

            # Set with a negative offset and negative number
            self.s2.set_paced_cells(x=0, y=-1, nx=1, ny=-1)
            self.assertFalse(self.s2.is_paced(0, 0))
            self.assertTrue(self.s2.is_paced(0, 1))
            self.assertFalse(self.s2.is_paced(0, 2))
            self.assertFalse(self.s2.is_paced(1, 1))
            self.assertFalse(self.s2.is_paced(1, 2))

        finally:
            # Restore defaults
            self.s1.set_paced_cells()

    def test_set_paced_cell_list_2d(self):
        # Test the set_paced_cell_list and is_paced methods in 1d (interface
        # only, does not test running the simulation)

        try:
            # Set with a list
            self.s2.set_paced_cell_list([(0, 0), (0, 2), (1, 1)])
            self.assertTrue(self.s2.is_paced(0, 0))
            self.assertFalse(self.s2.is_paced(0, 1))
            self.assertTrue(self.s2.is_paced(0, 2))
            self.assertFalse(self.s2.is_paced(1, 0))
            self.assertTrue(self.s2.is_paced(1, 1))
            self.assertFalse(self.s2.is_paced(1, 2))

            # Duplicate paced cells
            self.s2.set_paced_cell_list(
                [(0, 0), (0, 0), (0, 0), (0, 2), (0, 2)])
            self.assertTrue(self.s2.is_paced(0, 0))
            self.assertFalse(self.s2.is_paced(0, 1))
            self.assertTrue(self.s2.is_paced(0, 2))
            self.assertFalse(self.s2.is_paced(1, 0))
            self.assertFalse(self.s2.is_paced(1, 1))
            self.assertFalse(self.s2.is_paced(1, 2))

            # Just one cell
            self.s2.set_paced_cell_list([(1, 2)])
            self.assertFalse(self.s2.is_paced(0, 0))
            self.assertFalse(self.s2.is_paced(0, 1))
            self.assertFalse(self.s2.is_paced(0, 2))
            self.assertFalse(self.s2.is_paced(1, 0))
            self.assertFalse(self.s2.is_paced(1, 1))
            self.assertTrue(self.s2.is_paced(1, 2))

            # Set paced cells out of bounds
            self.assertRaisesRegex(
                IndexError, 'out of range',
                self.s2.set_paced_cell_list, [(-1, 0)])
            self.assertRaisesRegex(
                IndexError, 'out of range',
                self.s2.set_paced_cell_list, [(4, 0)])
            self.assertRaisesRegex(
                IndexError, 'out of range',
                self.s2.set_paced_cell_list, [(0, -1)])
            self.assertRaisesRegex(
                IndexError, 'out of range',
                self.s2.set_paced_cell_list, [(0, 4)])
            self.assertRaisesRegex(
                IndexError, 'out of range',
                self.s2.set_paced_cell_list, [(-2, -2)])
            self.assertRaisesRegex(
                IndexError, 'out of range',
                self.s2.set_paced_cell_list, [(5, 5)])

            # Is-paced called out of bounds
            self.assertRaisesRegex(
                IndexError, 'out of range', self.s2.is_paced, -1, 0)
            self.assertRaisesRegex(
                IndexError, 'out of range', self.s2.is_paced, 4, 0)
            self.assertRaisesRegex(
                IndexError, 'out of range', self.s2.is_paced, 0, -1)
            self.assertRaisesRegex(
                IndexError, 'out of range', self.s2.is_paced, 0, 4)
            self.assertRaisesRegex(
                IndexError, 'out of range', self.s2.is_paced, -2, 2)
            self.assertRaisesRegex(
                IndexError, 'out of range', self.s2.is_paced, 5, 5)
            self.assertRaisesRegex(
                ValueError, '2-dimensional', self.s2.is_paced, 1)

        finally:
            # Restore defaults
            self.s1.set_paced_cells()

    def test_set_state_1d(self):
        # Test the set_state methods on a 1d simulation (interface only)

        # Check simulation state equals model state
        m = 8
        n = 10
        self.s1.reset()
        sm = self.m.state()
        ss = [self.s1.state(x) for x in range(n)]
        for si in ss:
            self.assertEqual(sm, si)

        # Test setting a full-sized state
        sx = list(range(n * m))
        self.s1.set_state(sx)
        self.assertEqual(sx, self.s1.state())

        # Test setting a single, global state
        sx = [0.0] * m
        self.assertNotEqual(sm, sx)
        self.s1.set_state(sx)
        for i in range(n):
            self.assertEqual(sx, self.s1.state(i))
        self.assertEqual(sx * n, self.s1.state())
        self.s1.set_state(sm)
        self.assertEqual(sm * n, self.s1.state())

        # Test setting the state of a single cell
        j = 3
        self.s1.set_state(sx, j)
        for i in range(n):
            if i == j:
                self.assertEqual(self.s1.state(i), sx)
            else:
                self.assertEqual(self.s1.state(i), sm)

        # Check error messages for set_state
        self.assertRaisesRegex(
            ValueError, 'x was not None',
            self.s1.set_state, [0] * m * n, 3)
        self.assertRaisesRegex(
            ValueError, 'y was not None',
            self.s1.set_state, [0] * m * n, y=2)
        self.assertRaisesRegex(
            ValueError, 'must have the same size as',
            self.s1.set_state, [0] * (m * n + 1))
        self.assertRaisesRegex(
            ValueError, 'must have the same size as',
            self.s1.set_state, [0] * 3, y=2)
        self.assertRaisesRegex(
            IndexError, 'x-index out of range',
            self.s1.set_state, sm, -1)
        self.assertRaisesRegex(
            IndexError, 'x-index out of range',
            self.s1.set_state, sm, n)
        self.assertRaisesRegex(
            ValueError, '1-dimensional',
            self.s1.set_state, sm, 0, 1)

        # Check error messages for state
        self.assertRaisesRegex(
            IndexError, 'x-index out of range',
            self.s1.state, -1)
        self.assertRaisesRegex(
            IndexError, 'x-index out of range',
            self.s1.state, n)
        self.assertRaisesRegex(
            ValueError, '1-dimensional',
            self.s1.state, 0, 1)

        # Test set_default_state
        try:
            sx = list(range(m))
            self.s1.set_state([0] * m)
            self.s1.set_default_state(sx, j)
            for i in range(n):
                if i == j:
                    self.assertEqual(self.s1.default_state(i), sx)
                else:
                    self.assertEqual(self.s1.default_state(i), sm)
            sx = list(range(m * n))
            self.s1.set_default_state(sx)
            self.assertEqual(sx, self.s1.default_state())
        finally:
            self.s1.set_default_state(sm)

        # Check error messages for default_state
        self.assertRaisesRegex(
            IndexError, 'x-index out of range',
            self.s1.default_state, -1)
        self.assertRaisesRegex(
            IndexError, 'x-index out of range',
            self.s1.default_state, n)
        self.assertRaisesRegex(
            ValueError, '1-dimensional',
            self.s1.default_state, 0, 1)

    def test_set_state_2d(self):
        # Test the set_state methods on a 2d simulation (interface only)

        # Check simulation state equals model state
        m = 8
        nx, ny = 4, 3
        self.s2.reset()
        sm = self.m.state()
        for i in range(nx):
            for j in range(ny):
                self.assertEqual(sm, self.s2.state(i, j))

        # Test setting a full-sized state
        sx = list(range(nx * ny * m))
        self.s2.set_state(sx)
        self.assertEqual(sx, self.s2.state())

        # Test setting a single, global state
        sx = [0.0] * m
        self.assertNotEqual(sm, sx)
        self.s2.set_state(sx)
        for i in range(nx):
            for j in range(ny):
                self.assertEqual(sx, self.s2.state(i, j))
        self.assertEqual(sx * (nx * ny), self.s2.state())
        self.s2.set_state(sm)
        self.assertEqual(sm * (nx * ny), self.s2.state())

        # Test setting the state of a single cell
        x, y = 1, 2
        self.s2.set_state(sx, x, y)
        for i in range(nx):
            for j in range(ny):
                if i == x and j == y:
                    self.assertEqual(self.s2.state(i, j), sx)
                else:
                    self.assertEqual(self.s2.state(i, j), sm)

        # Test indexing in state vector is x first, then y
        self.s2.set_state(sx)
        self.s2.set_state(sm, x=1, y=2)
        s = self.s2.state()[::8]
        self.assertEqual(s[0], 0)   # 0, 0
        self.assertEqual(s[1], 0)   # 1, 0
        self.assertEqual(s[2], 0)   # 2, 0
        self.assertEqual(s[3], 0)   # 3, 0
        self.assertEqual(s[4], 0)   # 0, 1
        self.assertEqual(s[5], 0)   # 1, 1
        self.assertEqual(s[6], 0)   # 2, 1
        self.assertEqual(s[7], 0)   # 3, 1
        self.assertEqual(s[8], 0)   # 0, 2
        self.assertEqual(s[9], sm[0])   # 1, 2
        self.assertEqual(s[10], 0)   # 2, 2
        self.assertEqual(s[11], 0)   # 3, 2

        # Check error messages for set_state
        self.assertRaisesRegex(
            IndexError, 'y-index out of range',
            self.s2.set_state, sm, 0, -1)
        self.assertRaisesRegex(
            IndexError, 'y-index out of range',
            self.s2.set_state, sm, 0, ny)

        # Check error messages for state
        self.assertRaisesRegex(
            IndexError, 'y-index out of range',
            self.s2.state, 0, -1)
        self.assertRaisesRegex(
            IndexError, 'y-index out of range',
            self.s2.state, 1, ny)

        # Test set_default_state
        try:
            x, y = 2, 1
            sx = list(range(m))
            self.s2.set_state([0] * m)
            self.s2.set_default_state(sx, x, y)
            for i in range(nx):
                for j in range(ny):
                    if i == x and j == y:
                        self.assertEqual(self.s2.default_state(i, j), sx)
                    else:
                        self.assertEqual(self.s2.default_state(i, j), sm)
        finally:
            self.s2.set_default_state(sm)

        # Check error messages for default_state
        self.assertRaisesRegex(
            IndexError, 'y-index out of range',
            self.s2.default_state, 0, -1)
        self.assertRaisesRegex(
            IndexError, 'y-index out of range',
            self.s2.default_state, 1, ny)

    def test_shape(self):
        # Tests shape() and is_2d()

        # Test shape
        self.assertEqual(self.s1.shape(), 10)
        self.assertEqual(self.s2.shape(), (3, 4))

        # Test is_2d
        self.assertTrue(self.s2.is_2d())
        self.assertFalse(self.s1.is_2d())

        # Deprecated alias
        with WarningCollector() as c:
            self.assertTrue(self.s2.is2d())
        self.assertIn('deprecated', c.text())
        with WarningCollector() as c:
            self.assertFalse(self.s1.is2d())
        self.assertIn('deprecated', c.text())

    def test_step_size(self):
        # Tests setting the step size (interface only)

        try:
            dt = self.s0.step_size() * 2 + 0.001
            self.s0.set_step_size(dt)
            self.assertEqual(self.s0.step_size(), dt)
        finally:
            self.s0.set_step_size()

        self.assertRaisesRegex(
            ValueError, 'greater than zero', self.s0.set_step_size, 0)
        self.assertRaisesRegex(
            ValueError, 'greater than zero', self.s0.set_step_size, -1)


@unittest.skipIf(not OpenCL_FOUND, 'OpenCL not found on this system.')
class SimulationOpenCLFindNanTest(unittest.TestCase):
    """
    Tests the OpenCL simulation's find_nan method.
    """

    @classmethod
    def setUpClass(cls):
        # Create simulations for later use in testing
        cls.m1 = myokit.load_model('example')
        cls.p1 = myokit.pacing.blocktrain(period=1000, duration=2)

        # Voltage-clamped LR1 model with interdependent components
        cls.m2 = myokit.load_model('example')
        p = cls.m2.binding('pace')
        p.set_binding(None)
        v = cls.m2.get('membrane.V')
        v.set_rhs(-80)
        v.demote()
        v.set_label(None)
        v.set_binding('pace')
        cls.m2.get('ica.Ca_i').set_label('membrane_potential')
        cls.m2.get('membrane').move_variable(v, cls.m2.get('engine'))

        # Create protocol causing error at t=1.234ms
        t = 1.234
        cls.p2 = myokit.Protocol()
        cls.p2.schedule(start=0, level=-80, duration=t)
        cls.p2.schedule(start=t, level=-47.13, duration=1000)

        # Simulations
        cls._s1 = cls._s2 = None

    @property
    def s1(self):
        if self._s1 is None:
            self._s1 = myokit.SimulationOpenCL(self.m1, self.p1, ncells=10)
        return self._s1

    @property
    def s2(self):
        if self._s2 is None:
            self._s2 = myokit.SimulationOpenCL(self.m2, self.p2, ncells=(3, 3))
            self._s2.set_paced_cell_list([[1, 1]])
        return self._s2

    def test_big_steps(self):
        # Test if an error is raised when step size is huge.

        self.s1.reset()
        self.s1.set_step_size(1)
        self.assertRaises(
            myokit.SimulationError, self.s1.run, 10)

        # Test running with too little info
        self.assertRaisesRegex(
            myokit.SimulationError, 'Unable to pinpoint',
            self.s1.run, 10, log=['membrane.V'])
        self.assertRaisesRegex(
            myokit.SimulationError, 'Unable to pinpoint',
            self.s1.run, 10, log=myokit.LOG_STATE)
        self.assertRaisesRegex(
            myokit.SimulationError, 'Unable to pinpoint',
            self.s1.run, 10, log=myokit.LOG_BOUND)

    def test_one_over_zero(self):
        # Test creating a 1/0 error after a few seconds

        self.s2.reset()
        self.assertRaisesRegex(
            myokit.SimulationError, 'Time:  1.23', self.s2.run, 5)

    def test_first_point(self):
        # Try with error at first logged point

        self.s2.reset()
        x = self.s2.state(0, 0)
        x[3] = float('nan')
        self.s2.set_state(x, 2, 2)
        self.assertRaisesRegex(
            myokit.SimulationError, 'met in the very first', self.s2.run, 2)

    def test_without_error(self):
        # Try without error

        try:
            self.s2.set_protocol(None)
            self.s2.reset()
            d = self.s2.run(10)
            self.assertRaisesRegex(
                myokit.FindNanError, 'not found in log', self.s2.find_nan, d)
        finally:
            self.s2.set_protocol(self.p2)

    def test_manual_call(self):
        # Try manual call

        p = myokit.Protocol()
        p.schedule(start=0, level=-90, duration=4)
        p.schedule(start=4, level=-47.13, duration=1000)
        try:
            self.s2.set_protocol(p)
            self.s2.reset()
            x = self.s2.state(0, 0)
            x[2] = 0.9  # Lower j, for later (makes bisecting algo branch)
            self.s2.set_state(x, 2, 2)
            d = self.s2.run(10, report_nan=False)
            time, icell, variable, value, states, bounds = self.s2.find_nan(d)
            self.assertAlmostEqual(time, 4.005, 5)
            self.assertEqual(icell, [1, 1])
            self.assertEqual(variable, 'ina.m')

            # Test watch var, bad arguments
            self.assertRaisesRegex(
                myokit.FindNanError, 'not found',
                self.s2.find_nan, d, 'x.y', [0, 1])
            self.assertRaisesRegex(
                myokit.FindNanError, 'state',
                self.s2.find_nan, d, 'engine.time', [0, 1])
            self.assertRaisesRegex(
                myokit.FindNanError, 'safe range',
                self.s2.find_nan, d, 'ina.m')
            self.assertRaisesRegex(
                myokit.FindNanError, 'lower than',
                self.s2.find_nan, d, 'ina.m', [1, 0])

            # Call with a watch var (and right arguments)
            # Most cells are unpaced, so get V=0, so ina quickly inactivates
            time, icell, variable, value, states, bounds = self.s2.find_nan(
                d, 'ina.j', [0.5, 1])
            self.assertGreater(time, 2)
            self.assertLess(time, 3)
            self.assertEqual(icell, [2, 2])  # lowered, see above
            self.assertEqual(variable, 'ina.j')
            time, icell, variable, value, states, bounds = self.s2.find_nan(
                d, 'ina.j', [0.2, 1])
            self.assertGreater(time, 5)
            self.assertLess(time, 6)
            self.assertEqual(icell, [2, 2])  # lowered, see above
            self.assertEqual(variable, 'ina.j')

        finally:
            self.s2.set_protocol(self.p2)


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
