#!/usr/bin/env python3
#
# Tests the Fiber-tissue OpenCL simulation
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
class FiberTissueSimulationTest(unittest.TestCase):
    """
    Tests the fiber-tissue simulation.
    """

    @classmethod
    def setUpClass(cls):
        # Create objects for shared used in testing

        # Fiber model, tissue model, protocol
        cls.mf = myokit.load_model(
            os.path.join(DIR_DATA, 'dn-1985-normalised.mmt'))
        cls.mt = myokit.load_model(os.path.join(DIR_DATA, 'lr-1991.mmt'))
        cls.p = myokit.pacing.blocktrain(1000, 2.0, offset=.01)

        # Fiber/Tissue sizes (small sim)
        cls.nfx = 8
        cls.nfy = 4
        cls.ntx = 8
        cls.nty = 6

        # Shared simulations
        cls._s0 = cls._s1 = None

    @property
    def s0(self):
        # Shared 2x1 simulation
        if self._s0 is None:
            self._s0 = myokit.FiberTissueSimulation(
                self.mt,
                self.mt,
                self.p,
                ncells_fiber=(1, 1),
                ncells_tissue=(1, 1),
                nx_paced=1,
                g_fiber=(0, 0),
                g_tissue=(0, 0),
                g_fiber_tissue=0,
                precision=myokit.DOUBLE_PRECISION,
                dt=0.01,
            )
        return self._s0

    @property
    def s1(self):
        # Shared small simulation
        if self._s1 is None:
            self._s1 = myokit.FiberTissueSimulation(
                self.mf,
                self.mt,
                self.p,
                ncells_fiber=(self.nfx, self.nfy),
                ncells_tissue=(self.ntx, self.nty),
                nx_paced=4,
                g_fiber=(235, 100),
                g_tissue=(9, 5),
                g_fiber_tissue=9,
                dt=0.0012,
            )
        return self._s1

    def test_against_cvode(self):
        # Compare the fiber-tissue simulation output with CVODE output

        # Set up logging
        logvars = ['engine.time', 'engine.pace', 'membrane.V', 'ica.ICa']
        logt = myokit.LOG_NONE

        # Run simulation
        tmax = 100
        dlog = 0.1
        try:
            d1, logt = self.s0.run(
                tmax, logf=logvars, logt=logt, log_interval=dlog)
        finally:
            self.s0.reset()
        del logt
        d1 = d1.npview()

        # Run CVODE simulation
        s2 = myokit.Simulation(self.mt, self.p)
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
            plt.plot(d1.time(), d1['engine.pace'], '--', label='FiberTissue')
            plt.plot(d2.time(), d2['engine.pace'], '--', label='CVODE')
            plt.legend()
            plt.subplot(2, 1, 2)
            plt.plot(d1.time(), r1)
            print(e1)

            plt.figure()
            plt.suptitle('Membrane potential')
            plt.subplot(2, 1, 1)
            plt.plot(d1.time(), d1['membrane.V', 0, 0], label='FiberTissue')
            plt.plot(d2.time(), d2['membrane.V'], '--', label='CVODE')
            plt.legend()
            plt.subplot(2, 1, 2)
            plt.plot(d1.time(), r2)
            print(e2)

            plt.figure()
            plt.suptitle('Calcium current')
            plt.subplot(2, 1, 1)
            plt.plot(d1.time(), d1['ica.ICa', 0, 0], label='FiberTissue')
            plt.plot(d2.time(), d2['ica.ICa'], '--', label='CVODE')
            plt.legend()
            plt.subplot(2, 1, 2)
            plt.plot(d1.time(), r2)
            print(e3)

            plt.show()

        self.assertLess(e0, 1e-10)
        self.assertLess(e1, 1e-14)
        self.assertLess(e2, 0.05)
        self.assertLess(e3, 0.01)

    def test_basic(self):
        # Test basic functionality
        s = self.s1
        nfx, nfy, ntx, nty = self.nfx, self.nfy, self.ntx, self.nty

        # Run times
        run = .1

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
        try:
            logf, logt = s.run(run, logf=logf, logt=logt, log_interval=0.01)
        finally:
            s.reset()

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

    def test_creation(self):
        # Tests fiber tisue simulation creation
        mf, mt, p = self.mf, self.mt, self.p
        FT = myokit.FiberTissueSimulation

        # Models must be valid
        m2 = mf.clone()
        m2.label('membrane_potential').set_rhs(None)
        self.assertFalse(m2.is_valid())
        self.assertRaises(myokit.MissingRhsError, FT, m2, mt)
        self.assertFalse(m2.is_valid())
        self.assertRaises(myokit.MissingRhsError, FT, mf, m2)

        # Models must have interdependent components
        m2 = mf.clone()
        x = m2.get('ik').add_variable('xx')
        x.set_rhs('membrane.i_ion')
        self.assertTrue(m2.has_interdependent_components())
        self.assertRaisesRegex(ValueError, 'interdependent', FT, m2, mt)
        self.assertTrue(m2.has_interdependent_components())
        self.assertRaisesRegex(ValueError, 'interdependent', FT, mf, m2)

        # Dimensionalities must be 2d tuples
        s = FT(mf, mt, p, (5, 6), (7, 8))
        self.assertEqual(s.fiber_shape(), (6, 5))
        self.assertEqual(s.tissue_shape(), (8, 7))
        self.assertRaisesRegex(
            ValueError, r'fiber size must be a tuple \(nx, ny\)',
            FT, mf, mt, ncells_fiber=None)
        self.assertRaisesRegex(
            ValueError, r'fiber size must be a tuple \(nx, ny\)',
            FT, mf, mt, ncells_fiber=12)
        self.assertRaisesRegex(
            ValueError, r'fiber size must be a tuple \(nx, ny\)',
            FT, mf, mt, ncells_fiber=(12, ))
        self.assertRaisesRegex(
            ValueError, r'fiber size must be a tuple \(nx, ny\)',
            FT, mf, mt, ncells_fiber=(12, 12, 12))

        self.assertRaisesRegex(
            ValueError, r'tissue size must be a tuple \(nx, ny\)',
            FT, mf, mt, ncells_tissue=None)
        self.assertRaisesRegex(
            ValueError, r'tissue size must be a tuple \(nx, ny\)',
            FT, mf, mt, ncells_tissue=4)
        self.assertRaisesRegex(
            ValueError, r'tissue size must be a tuple \(nx, ny\)',
            FT, mf, mt, ncells_tissue=(3, ))
        self.assertRaisesRegex(
            ValueError, r'tissue size must be a tuple \(nx, ny\)',
            FT, mf, mt, ncells_tissue=(6, 6, 6))

        # Number of cells must be at least 1
        self.assertRaisesRegex(
            ValueError, r'fiber size must be at least \(1, 1\)',
            FT, mf, mt, ncells_fiber=(0, 10))
        self.assertRaisesRegex(
            ValueError, r'fiber size must be at least \(1, 1\)',
            FT, mf, mt, ncells_fiber=(10, 0))
        self.assertRaisesRegex(
            ValueError, r'fiber size must be at least \(1, 1\)',
            FT, mf, mt, ncells_fiber=(-1, -1))
        self.assertRaisesRegex(
            ValueError, r'tissue size must be at least \(1, 1\)',
            FT, mf, mt, ncells_tissue=(0, 10))
        self.assertRaisesRegex(
            ValueError, r'tissue size must be at least \(1, 1\)',
            FT, mf, mt, ncells_tissue=(10, 0))
        self.assertRaisesRegex(
            ValueError, r'tissue size must be at least \(1, 1\)',
            FT, mf, mt, ncells_tissue=(-1, -1))
        self.assertRaisesRegex(
            ValueError, 'exceed that of the tissue',
            FT, mf, mt, p, (5, 6), (5, 5))

        # Number of paced cells must be >= 0
        FT(mf, mt, p, nx_paced=0)
        self.assertRaisesRegex(
            ValueError, 'width of the stimulus pulse must be non-negative',
            FT, mf, mt, p, nx_paced=-1)

        # Check conductivities are tuples
        self.assertRaisesRegex(
            ValueError, r'fiber conductivity must be a tuple \(gx, gy\)',
            FT, mf, mt, p, g_fiber=1)
        self.assertRaisesRegex(
            ValueError, r'fiber conductivity must be a tuple \(gx, gy\)',
            FT, mf, mt, p, g_fiber=(1, ))
        self.assertRaisesRegex(
            ValueError, r'fiber conductivity must be a tuple \(gx, gy\)',
            FT, mf, mt, p, g_fiber=(1, 1, 1))
        self.assertRaisesRegex(
            ValueError, r'tissue conductivity must be a tuple \(gx, gy\)',
            FT, mf, mt, p, g_tissue=1)
        self.assertRaisesRegex(
            ValueError, r'tissue conductivity must be a tuple \(gx, gy\)',
            FT, mf, mt, p, g_tissue=(1, ))
        self.assertRaisesRegex(
            ValueError, r'tissue conductivity must be a tuple \(gx, gy\)',
            FT, mf, mt, p, g_tissue=(1, 1, 1))

        # Check step size is > 0
        self.assertRaisesRegex(
            ValueError, 'step size must be greater', FT, mf, mt, p, dt=0)
        self.assertRaisesRegex(
            ValueError, 'step size must be greater', FT, mf, mt, p, dt=-1)

        # Precision must be single or double
        self.assertRaisesRegex(
            ValueError, 'Only single and double',
            FT, mf, mt,
            precision=myokit.SINGLE_PRECISION + myokit.DOUBLE_PRECISION)

        # Membrane potentials must be given with labels
        m2 = mf.clone()
        m2.label('membrane_potential').set_label(None)
        self.assertRaisesRegex(
            ValueError, '"membrane_potential" in the fiber model',
            FT, m2, mt)
        self.assertRaisesRegex(
            ValueError, '"membrane_potential" in the tissue model',
            FT, mf, m2)

        # Membrane potential must be a state
        m2.get('ik.iK').set_label('membrane_potential')
        self.assertRaisesRegex(
            ValueError, 'fiber model must be a state variable',
            FT, m2, mt)
        self.assertRaisesRegex(
            ValueError, 'tissue model must be a state variable',
            FT, mf, m2)

        # Membrane potential vars must have same unit
        m2 = mf.clone()
        m2.label('membrane_potential').set_unit(None)
        self.assertRaisesRegex(
            ValueError, 'fiber model must specify a unit for the membrane',
            FT, m2, mt)
        self.assertRaisesRegex(
            ValueError, 'tissue model must specify a unit for the membrane',
            FT, mf, m2)
        m2.label('membrane_potential').set_unit(myokit.units.pF)
        self.assertRaisesRegex(
            ValueError, 'membrane potential must have the same unit',
            FT, mf, m2)

        # Diffusion currents must be given with labels
        m2 = mf.clone()
        m2.binding('diffusion_current').set_binding(None)
        self.assertRaisesRegex(
            ValueError, 'fiber model to be bound to "diffusion_current"',
            FT, m2, mt)
        self.assertRaisesRegex(
            ValueError, 'tissue model to be bound to "diffusion_current"',
            FT, mf, m2)

        # Diffusion vars must have same unit
        m2 = mf.clone()
        m2.binding('diffusion_current').set_unit(None)
        self.assertRaisesRegex(
            ValueError, 'fiber model must specify a unit for the diffusion',
            FT, m2, mt)
        self.assertRaisesRegex(
            ValueError, 'tissue model must specify a unit for the diffusion',
            FT, mf, m2)
        m2.binding('diffusion_current').set_unit(myokit.units.pF)
        self.assertRaisesRegex(
            ValueError, 'diffusion current must have the same unit',
            FT, mf, m2)

    def test_pre_reset(self):
        # Tests getting/setting of states and time, and use of pre() and run()
        try:
            # Check setting of time
            self.assertEqual(self.s1.time(), 0)
            self.s1.set_time(10)
            self.assertEqual(self.s1.time(), 10)
            self.s1.reset()     # Check that reset() resets time
            self.assertEqual(self.s1.time(), 0)

            # Check initial state equals default state
            sf, st = self.s1.fiber_state(), self.s1.tissue_state()
            self.assertEqual(sf, self.s1.default_fiber_state())
            self.assertEqual(st, self.s1.default_tissue_state())
        finally:
            self.s1.reset()

        # At this point, we have either quit or sf and st are set.
        # Use these to restore the original sim state at the end of the test.
        sf0, st0 = sf, st

        try:
            # Check running updates time and states, but not default states
            self.s1.run(5, logf=myokit.LOG_NONE, logt=myokit.LOG_NONE)
            self.assertEqual(self.s1.time(), 5)
            self.assertNotEqual(
                self.s1.fiber_state(), self.s1.default_fiber_state())
            self.assertNotEqual(
                self.s1.tissue_state(), self.s1.default_tissue_state())
            self.assertEqual(sf, self.s1.default_fiber_state())
            self.assertEqual(st, self.s1.default_tissue_state())

            # Setting time to 0 is different from reset()
            self.s1.set_time(0)
            self.assertEqual(self.s1.time(), 0)
            self.assertNotEqual(
                self.s1.fiber_state(), self.s1.default_fiber_state())
            self.assertNotEqual(
                self.s1.tissue_state(), self.s1.default_tissue_state())

            # Check reset() fixes everything
            self.s1.reset()
            self.assertEqual(sf, self.s1.fiber_state())
            self.assertEqual(st, self.s1.tissue_state())
            self.assertEqual(self.s1.time(), 0)

            # Check that pre() updates both states, but not time
            self.s1.pre(5)
            self.assertEqual(self.s1.time(), 0)
            self.assertNotEqual(sf, self.s1.fiber_state())
            self.assertNotEqual(st, self.s1.tissue_state())
            sf, st = self.s1.fiber_state(), self.s1.tissue_state()
            self.assertEqual(sf, self.s1.default_fiber_state())
            self.assertEqual(st, self.s1.default_tissue_state())
            self.assertEqual(self.s1.time(), 0)

            # Check that reset restores new default state
            self.s1.run(5, logf=myokit.LOG_NONE, logt=myokit.LOG_NONE)
            self.assertEqual(self.s1.time(), 5)
            self.assertNotEqual(
                self.s1.fiber_state(), self.s1.default_fiber_state())
            self.assertNotEqual(
                self.s1.tissue_state(), self.s1.default_tissue_state())
            self.assertEqual(sf, self.s1.default_fiber_state())
            self.assertEqual(st, self.s1.default_tissue_state())
            self.s1.reset()
            self.assertEqual(self.s1.time(), 0)
            self.assertEqual(sf, self.s1.fiber_state())
            self.assertEqual(st, self.s1.tissue_state())

        finally:
            self.s1.set_default_fiber_state(sf0)
            self.s1.set_default_tissue_state(st0)
            self.s1.reset()

    def test_protocol(self):
        # Test setting a protocol

        try:
            # Run, check Vm is raised
            df, dt = self.s0.run(
                5, logf=['membrane.V'], logt=myokit.LOG_NONE, log_interval=1)
            self.assertGreater(df['membrane.V', 0, 0][-1], 0)
            self.s0.reset()

            # Unset protocol, check Vm stays low
            self.s0.set_protocol(None)
            df, dt = self.s0.run(
                5, logf=['membrane.V'], logt=myokit.LOG_NONE, log_interval=1)
            self.assertLess(df['membrane.V', 0, 0][-1], 0)
            self.s0.reset()

            # Reset protocol, check Vm goes high
            self.s0.set_protocol(self.p)
            df, dt = self.s0.run(
                5, logf=['membrane.V'], logt=myokit.LOG_NONE, log_interval=1)
            self.assertGreater(df['membrane.V', 0, 0][-1], 0)
        finally:
            self.s0.reset()

    def test_run_errors(self):
        # Test invalid calls to run()

        try:
            # Run with negative sim time
            self.assertRaisesRegex(ValueError, 'can\'t be negative',
                                   self.s1.run, -1)

            # Run with negative or zero log interval: Just gets set to really
            # small value
            self.s1.run(1, log_interval=0)
            self.s1.run(1, log_interval=-1)
        finally:
            self.s1.reset()

    def test_run_progress(self):
        # Tests running with a progress reporter.
        pass

        # Run with a progress reporter
        with myokit.tools.capture() as c:
            self.s1.run(3, progress=myokit.ProgressPrinter())
        self.assertTrue(c.text() != '')

        # Cancel using a progress reporter
        self.assertRaises(
            myokit.SimulationCancelledError,
            self.s1.run, 20, progress=CancellingReporter(0))

        # Run with invalid progress reporter
        try:
            self.assertRaisesRegex(ValueError, 'subclass of myokit.ProgressR',
                                   self.s1.run, 1, progress=12)
        finally:
            self.s1.reset()

    def test_fiber_state(self):
        # Test the fiber_state related methods.

        # Check simulation state equals model state
        m = self.mf.count_states()
        nx, ny = self.nfx, self.nfy

        sm = self.mf.state()
        for i in range(nx):
            for j in range(ny):
                self.assertEqual(sm, self.s1.fiber_state(i, j))

        try:
            # Test setting a full-sized state
            sx = list(range(nx * ny * m))
            self.s1.set_fiber_state(sx)
            self.assertEqual(sx, self.s1.fiber_state())

            # Test setting a single, global state
            sx = [0.0] * m
            self.assertNotEqual(sm, sx)
            self.s1.set_fiber_state(sx)
            for i in range(nx):
                for j in range(ny):
                    self.assertEqual(sx, self.s1.fiber_state(i, j))
            self.assertEqual(sx * (nx * ny), self.s1.fiber_state())
            self.s1.set_fiber_state(sm)
            self.assertEqual(sm * (nx * ny), self.s1.fiber_state())

            # Test setting the state of a single cell
            x, y = 1, 2
            self.s1.set_fiber_state(sx, x, y)
            for i in range(nx):
                for j in range(ny):
                    if i == x and j == y:
                        self.assertEqual(self.s1.fiber_state(i, j), sx)
                    else:
                        self.assertEqual(self.s1.fiber_state(i, j), sm)

            # Test indexing in state vector is x first, then y
            self.s1.set_fiber_state(sx)
            self.s1.set_fiber_state(sm, x=1, y=2)
            s = self.s1.fiber_state()[::m]
            self.assertEqual(s[2 * nx + 1], sm[0])
            for i in range(nx * ny):
                if i != 2 * nx + 1:
                    self.assertEqual(s[i], 0)

            # Test getting specific states
            self.assertEqual(self.s1.fiber_state(0, 0), sx)
            self.assertEqual(self.s1.fiber_state(1, 2), sm)
            self.assertEqual(self.s1.default_fiber_state(0, 0),
                             self.s1.default_fiber_state(1, 1))

            # Check error messages for set_fiber_state() (shared)
            self.assertRaisesRegex(IndexError, 'x-index out of range',
                                   self.s1.set_fiber_state, sm, -1, 0)
            self.assertRaisesRegex(IndexError, 'x-index out of range',
                                   self.s1.set_fiber_state, sm, nx, 0)
            self.assertRaisesRegex(IndexError, 'y-index out of range',
                                   self.s1.set_fiber_state, sm, 0, -1)
            self.assertRaisesRegex(IndexError, 'y-index out of range',
                                   self.s1.set_fiber_state, sm, 0, ny)
            self.assertRaisesRegex(ValueError, 'both x and y',
                                   self.s1.set_fiber_state, sm, 0)
            self.assertRaisesRegex(ValueError, 'single fiber cell state or',
                                   self.s1.set_fiber_state, sm * 2)

            # Check error messages for fiber_state()
            self.assertRaisesRegex(IndexError, 'x-index out of range',
                                   self.s1.fiber_state, -1, 0)
            self.assertRaisesRegex(IndexError, 'x-index out of range',
                                   self.s1.fiber_state, nx, 0)
            self.assertRaisesRegex(IndexError, 'y-index out of range',
                                   self.s1.fiber_state, 0, -1)
            self.assertRaisesRegex(IndexError, 'y-index out of range',
                                   self.s1.fiber_state, 0, ny)
            self.assertRaisesRegex(ValueError, 'both an x and y',
                                   self.s1.fiber_state, 0)

            # Check error messages for default_fiber_state()
            self.assertRaisesRegex(IndexError, 'x-index out of range',
                                   self.s1.default_fiber_state, -1, 0)
            self.assertRaisesRegex(IndexError, 'x-index out of range',
                                   self.s1.default_fiber_state, nx, 0)
            self.assertRaisesRegex(IndexError, 'y-index out of range',
                                   self.s1.default_fiber_state, 0, -1)
            self.assertRaisesRegex(IndexError, 'y-index out of range',
                                   self.s1.default_fiber_state, 0, ny)
            self.assertRaisesRegex(ValueError, 'both an x and y',
                                   self.s1.default_fiber_state, 0)
        finally:
            self.s1.reset()

    def test_tissue_state(self):
        # Test the set_tissue_state and set_default_tissue_state methods

        # Check simulation state equals model state
        m = self.mt.count_states()
        nx, ny = self.ntx, self.nty

        sm = self.mt.state()
        for i in range(nx):
            for j in range(ny):
                self.assertEqual(sm, self.s1.tissue_state(i, j))

        try:
            # Test setting a full-sized state
            sx = list(range(nx * ny * m))
            self.s1.set_tissue_state(sx)
            self.assertEqual(sx, self.s1.tissue_state())

            # Test setting a single, global state
            sx = [0.0] * m
            self.assertNotEqual(sm, sx)
            self.s1.set_tissue_state(sx)
            for i in range(nx):
                for j in range(ny):
                    self.assertEqual(sx, self.s1.tissue_state(i, j))
            self.assertEqual(sx * (nx * ny), self.s1.tissue_state())
            self.s1.set_tissue_state(sm)
            self.assertEqual(sm * (nx * ny), self.s1.tissue_state())

            # Test setting the state of a single cell
            x, y = 1, 2
            self.s1.set_tissue_state(sx, x, y)
            for i in range(nx):
                for j in range(ny):
                    if i == x and j == y:
                        self.assertEqual(self.s1.tissue_state(i, j), sx)
                    else:
                        self.assertEqual(self.s1.tissue_state(i, j), sm)

            # Test indexing in state vector is x first, then y
            self.s1.set_tissue_state(sx)
            self.s1.set_tissue_state(sm, x=1, y=2)
            s = self.s1.tissue_state()[::m]
            self.assertEqual(s[2 * nx + 1], sm[0])
            for i in range(nx * ny):
                if i != 2 * nx + 1:
                    self.assertEqual(s[i], 0)

            # Test getting specific states
            self.assertEqual(self.s1.tissue_state(0, 0), sx)
            self.assertEqual(self.s1.tissue_state(1, 2), sm)
            self.assertEqual(self.s1.default_tissue_state(0, 0),
                             self.s1.default_tissue_state(1, 1))

            # Check error messages for set_tissue_state() (shared)
            self.assertRaisesRegex(IndexError, 'x-index out of range',
                                   self.s1.set_tissue_state, sm, -1, 0)
            self.assertRaisesRegex(IndexError, 'x-index out of range',
                                   self.s1.set_tissue_state, sm, nx, 0)
            self.assertRaisesRegex(IndexError, 'y-index out of range',
                                   self.s1.set_tissue_state, sm, 0, -1)
            self.assertRaisesRegex(IndexError, 'y-index out of range',
                                   self.s1.set_tissue_state, sm, 0, ny)
            self.assertRaisesRegex(ValueError, 'both x and y',
                                   self.s1.set_tissue_state, sm, 0)
            self.assertRaisesRegex(ValueError, 'single tissue cell state or',
                                   self.s1.set_tissue_state, sm * 2)

            # Check error messages for tissue_state()
            self.assertRaisesRegex(IndexError, 'x-index out of range',
                                   self.s1.tissue_state, -1, 0)
            self.assertRaisesRegex(IndexError, 'x-index out of range',
                                   self.s1.tissue_state, nx, 0)
            self.assertRaisesRegex(IndexError, 'y-index out of range',
                                   self.s1.tissue_state, 0, -1)
            self.assertRaisesRegex(IndexError, 'y-index out of range',
                                   self.s1.tissue_state, 0, ny)
            self.assertRaisesRegex(ValueError, 'both an x and y',
                                   self.s1.tissue_state, 0)

            # Check error messages for default_tissue_state()
            self.assertRaisesRegex(IndexError, 'x-index out of range',
                                   self.s1.default_tissue_state, -1, 0)
            self.assertRaisesRegex(IndexError, 'x-index out of range',
                                   self.s1.default_tissue_state, nx, 0)
            self.assertRaisesRegex(IndexError, 'y-index out of range',
                                   self.s1.default_tissue_state, 0, -1)
            self.assertRaisesRegex(IndexError, 'y-index out of range',
                                   self.s1.default_tissue_state, 0, ny)
            self.assertRaisesRegex(ValueError, 'both an x and y',
                                   self.s1.default_tissue_state, 0)
        finally:
            self.s1.reset()

    def test_step_size(self):
        # Tests setting/getting step size
        try:
            self.assertEqual(self.s1.step_size(), 0.0012)
            self.s1.set_step_size(0.0011)
            self.assertEqual(self.s1.step_size(), 0.0011)

            self.assertRaisesRegex(ValueError, 'greater than zero',
                                   self.s1.set_step_size, -1)
            self.assertRaisesRegex(ValueError, 'greater than zero',
                                   self.s1.set_step_size, 0)
        finally:
            self.s1.set_step_size(0.0012)


@unittest.skipIf(not OpenCL_FOUND, 'OpenCL not found on this system.')
class FiberTissueSimulationFindNanTest(unittest.TestCase):
    """ Tests the FiberTissue simulation's find_nan method. """

    @classmethod
    def setUpClass(cls):
        # Load models and protocols for use in testing

        # Fiber model, tissue model, protocol
        cls.mf = myokit.load_model(
            os.path.join(DIR_DATA, 'dn-1985-normalised.mmt'))
        cls.mt = myokit.load_model(os.path.join(DIR_DATA, 'lr-1991.mmt'))

        # Fiber/Tissue sizes (small sim)
        cls.nfx = 8
        cls.nfy = 4
        cls.ntx = 8
        cls.nty = 6

        # Standard protocols
        cls.p1 = myokit.pacing.blocktrain(1000, 2, offset=.01)

        # Protocol with error at t = 2
        cls.p2 = myokit.Protocol()
        cls.p2.schedule(period=0, duration=5, level=5e3, start=2)

        # Protocol with error at t = 1.234 (in tissue?)
        cls.p3 = myokit.Protocol()
        cls.p3.schedule(period=0, duration=5, level=-1, start=1.234)
        v = cls.mt.get('ina.m')
        v.set_rhs('if(membrane.V < -100, 1e4, ' + v.rhs().code() + ')')

        # Shared simulations
        cls._s1 = None

    @property
    def s1(self):
        if self._s1 is None:
            self._s1 = myokit.FiberTissueSimulation(
                self.mf,
                self.mt,
                self.p1,
                ncells_fiber=(self.nfx, self.nfy),
                ncells_tissue=(self.ntx, self.nty),
                nx_paced=10,
                g_fiber=(235, 100),
                g_tissue=(9, 5),
                g_fiber_tissue=9,
                dt=0.0012,
            )
        return self._s1

    def test_big_stimulus(self):
        # Tests if NaNs are detected after a massive stimulus

        try:
            self.s1.set_protocol(self.p2)

            # Automatic detection
            with WarningCollector():
                self.assertRaisesRegex(
                    myokit.SimulationError,
                    'numerical error in fiber simulation at t = 2.0',
                    self.s1.run, 10, log_interval=1)

            # Automatic detection, but not enough information
            self.s1.reset()
            with WarningCollector():
                self.assertRaisesRegex(
                    myokit.SimulationError, 'Unable to pinpoint',
                    self.s1.run, 5, logf=['membrane.V'], logt=myokit.LOG_NONE,
                    log_interval=0.1)

            # Offline detection
            # res = part, time, icell, var, value, states, bound
            self.s1.reset()
            df, dt = self.s1.run(5, log_interval=0.1, report_nan=False)
            res = self.s1.find_nan(df, dt)
            self.assertEqual(round(res[1], 1), 2.0)

            # Missing state and bound var in fiber log
            d2 = df.clone()
            del d2['membrane.V', 0, 0]
            self.assertRaisesRegex(
                myokit.FindNanError, 'fiber(.+)membrane.V',
                self.s1.find_nan, d2, dt)
            d2 = df.clone()
            del d2['engine.time']
            self.assertRaisesRegex(
                myokit.FindNanError, 'fiber(.+)engine.time',
                self.s1.find_nan, d2, dt)

            # Missing state and bound var in tissue log
            d2 = dt.clone()
            del d2['membrane.V', 0, 0]
            self.assertRaisesRegex(
                myokit.FindNanError, 'tissue(.+)membrane.V',
                self.s1.find_nan, df, d2)
            d2 = dt.clone()
            del d2['engine.time']
            self.assertRaisesRegex(
                myokit.FindNanError, 'tissue(.+)engine.time',
                self.s1.find_nan, df, d2)

            # NaN at first data point
            d2 = df.clone()
            d2['membrane.V', 0, 0][0] = float('nan')
            self.assertRaisesRegex(
                myokit.FindNanError, 'first data point',
                self.s1.find_nan, d2, dt)

            # No NaN
            d2 = df.trim_right(1.9)
            d3 = dt.trim_right(1.9)
            self.assertRaisesRegex(
                myokit.FindNanError, 'Error condition not found',
                self.s1.find_nan, d2, d3)

        finally:
            self.s1.set_protocol(self.p1)
            self.s1.reset()

    def test_neg_stimulus(self):
        # Tests if NaNs are detected in the tissue, after a negative stimulus

        try:
            self.s1.set_protocol(self.p3)
            with WarningCollector():
                self.assertRaisesRegex(
                    myokit.SimulationError, 'in tissue simulation at t = 1.7',
                    self.s1.run, 5)
        finally:
            self.s1.set_protocol(self.p1)
            self.s1.reset()

    def test_big_step(self):
        # Tests if NaNs are detected in the diffusion current

        dt = self.s1.step_size()
        try:
            self.s1.set_step_size(0.01)
            with WarningCollector():
                self.assertRaisesRegex(
                    myokit.SimulationError, 'when membrane.i_diff',
                    self.s1.run, 5)
        finally:
            self.s1.set_step_size(dt)
            self.s1.reset()


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
