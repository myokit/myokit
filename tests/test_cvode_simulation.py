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

from shared import DIR_DATA, CancellingReporter

# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp


class SimulationTest(unittest.TestCase):
    """
    Tests the CVode simulation class.
    """
    @classmethod
    def setUpClass(cls):
        """
        Test simulation creation.
        """
        m, p, x = myokit.load(os.path.join(DIR_DATA, 'lr-1991.mmt'))
        cls.model = m
        cls.protocol = p
        cls.sim = myokit.Simulation(cls.model, cls.protocol)

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
        self.assertEqual(self.sim.time(), 0)
        self.sim.pre(5)
        self.assertEqual(self.sim.time(), 0)
        d = self.sim.run(5)
        self.assertEqual(self.sim.time(), 5)
        self.sim.set_time(0)
        self.assertEqual(self.sim.time(), 0)
        self.assertEqual(type(d), myokit.DataLog)
        self.assertIn('engine.time', d)
        n = len(d['engine.time'])
        for k, v in d.items():
            self.assertEqual(n, len(v))

        # Can't do negative times
        self.assertRaisesRegex(ValueError, 'negative', self.sim.run, -1)

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

    def test_fixed_form_protocol(self):
        """
        Tests running with a fixed form protocol.
        """
        n = 10
        time = list(range(n))
        pace = [0] * n
        pace[2:4] = [0.5, 0.5]

        self.sim.set_fixed_form_protocol(time, pace)
        self.sim.reset()
        d = self.sim.run(n, log_interval=1)
        self.assertEqual(list(d.time()), time)
        self.assertEqual(list(d['engine.pace']), pace)

        # Unset
        self.sim.set_fixed_form_protocol(None)
        self.sim.reset()
        d = self.sim.run(n, log_interval=1)
        self.assertEqual(list(d['engine.pace']), [0] * n)

        # Reset
        self.sim.set_fixed_form_protocol(time, pace)
        self.sim.reset()
        d = self.sim.run(n, log_interval=1)
        self.assertEqual(list(d.time()), time)
        self.assertEqual(list(d['engine.pace']), pace)

        # Unset, replace with original protocol
        self.sim.set_protocol(self.protocol)
        self.sim.reset()
        d = self.sim.run(n, log_interval=1)
        self.assertNotEqual(list(d['engine.pace']), pace)
        self.assertNotEqual(list(d['engine.pace']), [0] * n)

        # Invalid protocols
        self.assertRaisesRegex(
            ValueError, 'no times', self.sim.set_fixed_form_protocol,
            values=pace)
        self.assertRaisesRegex(
            ValueError, 'no values', self.sim.set_fixed_form_protocol,
            times=time)
        self.assertRaisesRegex(
            ValueError, 'same size', self.sim.set_fixed_form_protocol,
            time, pace[:-1])

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

    def test_progress_reporter(self):
        """
        Test running with a progress reporter.
        """
        # Test if it works
        sim = myokit.Simulation(self.model, self.protocol)
        with myokit.PyCapture() as c:
            sim.run(110, progress=myokit.ProgressPrinter())
        c = c.text().splitlines()
        self.assertEqual(len(c), 2)
        self.assertEqual(
            c[0], '[0.0 minutes] 1.9 % done, estimated 0 seconds remaining')
        self.assertEqual(
            c[1], '[0.0 minutes] 100.0 % done, estimated 0 seconds remaining')

        # Not a progress reporter
        self.assertRaisesRegex(
            ValueError, 'ProgressReporter', self.sim.run, 5, progress=12)

        # Cancel from reporter
        self.assertRaises(
            myokit.SimulationCancelledError, self.sim.run, 1,
            progress=CancellingReporter(0))

    def test_apd_tracking(self):
        """
        Tests the APD calculation method.
        """
        # More testing is done in test_datalog.py!

        # Apd var is not a state
        self.assertRaisesRegex(
            ValueError, 'must be a state', myokit.Simulation, self.model,
            self.protocol, apd_var='ina.INa')

        # No apd var given, but threshold provided
        self.assertRaisesRegex(
            ValueError, 'without apd_var', self.sim.run, 1, apd_threshold=12)

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
        self.assertRaisesRegex(myokit.SimulationError, "at t = 0", s.run, 5)
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
        self.sim.set_state(s1)
        self.assertEqual(d1, self.sim.eval_derivatives())

    def test_set_tolerance(self):
        """
        Tests :meth:`Simulation.set_tolerance()`.
        """
        self.assertRaisesRegex(
            ValueError, 'Absolute', self.sim.set_tolerance, abs_tol=0)
        self.assertRaisesRegex(
            ValueError, 'Relative', self.sim.set_tolerance, rel_tol=0)
        self.sim.set_tolerance(1e-6, 1e-4)

    def test_set_step_size(self):
        """
        Tests :meth:`Simulation.set_min_step_size()` and
        :meth:`Simulation.set_max_step_size()`.
        """
        # Minimum: set, unset, allow negative value to unset
        self.sim.set_min_step_size(0.1)
        self.sim.set_min_step_size(None)
        self.sim.set_min_step_size(-1)

        # Same for max
        self.sim.set_max_step_size(0.1)
        self.sim.set_max_step_size(None)
        self.sim.set_max_step_size(-1)

    def test_set_state(self):
        """
        Tests :meth:`Simulation.set_state()` and
        :meth:`Simulation.set_default_state()`.
        """
        # Get state and default state, both different from current
        state = self.sim.state()
        state[0] += 1
        default_state = self.sim.default_state()
        default_state[1] += 1
        if state == default_state:
            default_state[0] += 2

        self.assertNotEqual(self.sim.state(), state)
        self.assertNotEqual(self.sim.default_state(), default_state)

        self.sim.set_state(state)
        self.sim.set_default_state(default_state)

        self.assertEqual(self.sim.state(), state)
        self.assertEqual(self.sim.default_state(), default_state)

    def test_set_constant(self):
        """
        Tests :meth:`Simulation.set_constant()`.
        """
        # Literal
        self.sim.set_constant('cell.Na_i', 11)
        self.assertRaises(KeyError, self.sim.set_constant, 'cell.Bert', 11)

        # Calculated constant
        self.assertRaisesRegex(
            ValueError, 'not a literal', self.sim.set_constant, 'ina.ENa', 11)

    def test_simulation_error(self):
        """
        Tests for simulation error detection.
        """
        # Silly protocol
        p = myokit.Protocol()
        p.schedule(level=1000, start=1, duration=1)
        self.sim.reset()
        self.sim.set_protocol(p)
        self.assertRaises(myokit.SimulationError, self.sim.run, 10)
        self.sim.set_protocol(self.protocol)

        # Cvode error (test failure occurred too many times)
        m = self.model.clone()
        v = m.get('membrane.V')
        v.set_rhs(myokit.Multiply(v.rhs(), myokit.Number(1e12)))
        s = myokit.Simulation(m, self.protocol)
        with self.assertRaises(myokit.SimulationError) as e:
            s.run(5000)
        self.assertIn('CV_ERR_FAILURE', str(e.exception))


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
