#!/usr/bin/env python
#
# Tests the CVODE simulation class.
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

        # Can't do negative times
        self.assertRaisesRegexp(ValueError, 'negative', self.sim.run, -1)

        # Negative log interval is set to zero
        self.sim.reset()
        d1 = self.sim.run(5)
        self.sim.reset()
        d2 = self.sim.run(5, log_interval=-5)
        self.assertEqual(d1.time(), d2.time())

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

    def test_progress_writer(self):
        """
        Test running with a progress writer.
        """
        sim = myokit.Simulation(self.model, self.protocol)
        with myokit.PyCapture() as c:
            sim.run(110, progress=myokit.ProgressPrinter())
        c = c.text().splitlines()
        self.assertEqual(len(c), 2)
        self.assertEqual(
            c[0], '[0.0 minutes] 1.9 % done, estimated 0 seconds remaining')
        self.assertEqual(
            c[1], '[0.0 minutes] 100.0 % done, estimated 0 seconds remaining')

    def test_apd_tracking(self):
        """
        Tests the APD calculation method.
        """
        # More testing is done in test_datalog.py!

        self.assertRaisesRegexp(
            ValueError, 'must be a state', myokit.Simulation, self.model,
            self.protocol, apd_var='ina.INa')

    def test_last_state(self):
        """
        Returns the last state before an error, or None.
        """
        m = self.model.clone()
        istim = m.get('membrane.i_stim')
        istim.set_rhs('engine.pace / stim_amplitude')
        s = myokit.Simulation(m, self.protocol)
        self.assertIsNone(s.last_state())
        s.run(1)
        self.assertIsNone(s.last_state())
        s.set_constant('membrane.i_stim.stim_amplitude', 0)
        s.reset()
        self.assertRaisesRegexp(myokit.SimulationError, "at t = 0", s.run, 5)
        self.assertEqual(len(s.last_state()), len(s.state()))
        self.assertEqual(s.last_state(), s.state())

    def test_last_evaluations_and_steps(self):
        """
        Tests :meth:`Simulation.last_number_of_evaluations()` and
        :meth:`Simulation.last_number_of_steps()`
        """
        s = myokit.Simulation(self.model, self.protocol)
        self.assertEqual(s.last_number_of_evaluations(), 0)
        self.assertEqual(s.last_number_of_steps(), 0)
        s.run(1)
        self.assertTrue(s.last_number_of_evaluations() > 0)
        self.assertTrue(s.last_number_of_steps() > 0)
        self.assertNotEqual(
            s.last_number_of_evaluations(), s.last_number_of_steps())

    def test_eval_derivatives(self):
        """
        Tests :meth:`Simulation.eval_derivatives()`.
        """
        self.sim.reset()
        s1 = self.sim.state()
        d1 = self.sim.eval_derivatives()
        self.sim.run(1)
        d2 = self.sim.eval_derivatives()
        self.assertNotEqual(d1, d2)
        self.assertEqual(d1, self.sim.eval_derivatives(s1))


class RuntimeSimulationTest(unittest.TestCase):
    """
    Tests the obtaining of runtimes from the CVode simulation.
    """
    def test_short_runtimes(self):
        m, p, x = myokit.load(
            os.path.join(DIR_DATA, 'lr-1991-runtimes.mmt'))
        myokit.run(m, p, x)


if __name__ == '__main__':
    unittest.main()
