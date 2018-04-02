#!/usr/bin/env python
#
# Tests the main simulation classes.
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
from __future__ import print_function
import os
import unittest
import numpy as np

import myokit

from shared import DIR_DATA


class SimulationTest(unittest.TestCase):
    """
    Tests the CVode simulation class.
    """
    @classmethod
    def setUpClass(self):
        """
        Test simulation creation.
        """
        m, p, x = myokit.load(os.path.join(DIR_DATA, 'lr-1991.mmt'))
        self.model = m
        self.protocol = p
        self.sim = myokit.Simulation(self.model, self.protocol)

    def test_pre(self):
        """
        Test pre-pacing.
        """
        self.sim.reset()
        self.sim.pre(200)

    def test_simple(self):
        """
        Test simple run.
        """
        self.sim.reset()
        self.sim.pre(50)
        d = self.sim.run(50)
        self.assertEqual(type(d), myokit.DataLog)
        self.assertIn('engine.time', d)
        n = len(d['engine.time'])
        for k, v in d.items():
            self.assertEqual(n, len(v))

    def test_no_protocol(self):
        """
        Test running without a protocol.
        """
        self.sim.reset()
        self.sim.pre(50)
        self.sim.set_protocol(None)
        d = self.sim.run(50).npview()
        # Check if pace was set to zero (see prop 651 / technical docs).
        self.assertTrue(np.all(d['engine.pace'] == 0.0))

    def test_in_parts(self):
        """
        Test running the simulation in parts.
        """
        self.sim.reset()
        # New logs should start with first state, finish with final
        d = self.sim.run(150)
        self.assertEqual(d['engine.time'][0], 0.0)
        self.assertEqual(d['engine.time'][-1], 150.0)
        # Next part should continue at 150, leave where last left off
        e = self.sim.run(50)
        self.assertEqual(d['engine.time'][-1], e['engine.time'][0])
        self.assertEqual(d['membrane.V'][-1], e['membrane.V'][0])
        # Re-used logs shouldn't re-log their first state
        n = len(e['engine.time'])
        e = self.sim.run(50, log=e)
        self.assertNotEqual(e['engine.time'][n - 1], e['engine.time'][n])
        self.assertGreater(e['engine.time'][n], e['engine.time'][n - 1])


class RuntimeSimulationTest(unittest.TestCase):
    """
    Tests the obtaining of runtimes from the CVode simulation.
    """
    def test_short_runtimes(self):
        m, p, x = myokit.load(
            os.path.join(DIR_DATA, 'lr-1991-runtimes.mmt'))
        myokit.run(m, p, x)


class Simulation1d(unittest.TestCase):
    """
    Tests the non-parallel 1d simulation.
    """
    def test_set_state(self):
        m, p, x = myokit.load(os.path.join(DIR_DATA, 'lr-1991.mmt'))
        n = 4
        s = myokit.Simulation1d(m, p, n)
        sm = m.state()
        ss = [s.state(x) for x in range(n)]
        for si in ss:
            self.assertEqual(sm, si)
        # Test setting a single, global state
        sx = [0] * 8
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


class RhsBenchmarker(unittest.TestCase):
    """
    Tests the RhsBenchmarker class
    """
    def test_simple(self):
        # Create test model
        m = myokit.Model('test')
        c = m.add_component('c')
        t = c.add_variable('time')
        t.set_rhs('0')
        t.set_binding('time')
        v = c.add_variable('V')
        v.set_rhs('0')
        v.promote(-80.1)
        x = c.add_variable('x')
        x.set_rhs('exp(V)')
        m.validate()
        # Create simulation log
        log = myokit.DataLog()
        log['c.time'] = np.zeros(1000)
        log['c.V'] = np.linspace(-80.0, 50.0, 10)
        # Number of repeats
        repeats = 10
        # Run
        x.set_rhs('1 / (7 * exp((V + 12) / 35) + 9 * exp(-(V + 77) / 6))')
        b = myokit.RhsBenchmarker(m, [x])
        t = b.bench_full(log, repeats)
        t = b.bench_part(log, repeats)
        # No errors = pass


class ICSimulation(unittest.TestCase):
    """
    Tests the ICSimulation.
    """
    def test_simple(self):
        # Load model
        m = os.path.join(DIR_DATA, 'lr-1991.mmt')
        m, p, x = myokit.load(m)
        # Run a simulation
        s = myokit.ICSimulation(m, p)
        d, e = s.run(20, log_interval=5)
        # Create a datablock from the simulation log
        b = s.block(d, e)
        del(d, e)
        # Calculate eigenvalues
        b.eigenvalues('derivatives')


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


class JacobianTracer(unittest.TestCase):
    """
    Tests the JacobianTracer.
    """
    def test_simple(self):
        # Load model
        m = os.path.join(DIR_DATA, 'lr-1991.mmt')
        m, p, x = myokit.load(m)
        v = m.binding('diffusion_current')
        if v is not None:
            v.set_binding(None)
        # Run a simulation, save all states & bound values
        s = myokit.Simulation(m, p)
        s.pre(10)
        s.reset()
        d = s.run(20, log=myokit.LOG_STATE + myokit.LOG_BOUND)
        # Calculate the dominant eigenvalues for each log position
        g = myokit.JacobianTracer(m)
        b = g.jacobians(d)
        b.dominant_eigenvalues('jacobians')
        b.largest_eigenvalues('jacobians')


class JacobianCalculator(unittest.TestCase):
    """
    Tests the JacobianCalculator.
    """
    def test_simple(self):
        # Load model
        m = os.path.join(DIR_DATA, 'lr-1991.mmt')
        m, p, x = myokit.load(m)
        # Run a simple simulation
        c = myokit.JacobianCalculator(m)
        x, f, j, e = c.newton_root(damping=0.01, max_iter=50)


if __name__ == '__main__':
    unittest.main()
