#!/usr/bin/env python3
#
# Tests the CVODE simulation class.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import os
import pickle
import platform
import re
import sys
import unittest

import numpy as np

import myokit

from myokit.tests import DIR_DATA, CancellingReporter, WarningCollector

# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp


@unittest.skipIf(platform.system() != 'Linux', 'Legacy CVODE tests')
class LegacySimulationTest(unittest.TestCase):
    """
    Tests the Legacy CVODE simulation class.
    """

    @classmethod
    def setUpClass(cls):
        # Test simulation creation.

        m, p, x = myokit.load(os.path.join(DIR_DATA, 'lr-1991.mmt'))
        cls.model = m
        cls.protocol = p
        cls.sim = myokit.LegacySimulation(cls.model, cls.protocol)

    def test_pre(self):
        # Test pre-pacing.

        self.sim.reset()
        self.sim.pre(200)

    def test_simple(self):
        # Test simple run.

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
        # Test running without a protocol.

        self.sim.reset()
        self.sim.pre(50)
        self.sim.set_protocol(None)
        d = self.sim.run(50).npview()

        # Check if pace was set to zero (see prop 651 / technical docs).
        self.assertTrue(np.all(d['engine.pace'] == 0.0))

    def test_fixed_form_protocol(self):
        # Test running with a fixed form protocol.

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
        # Test running the simulation in parts.

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

    def test_pacing_values_at_event_transitions(self):
        # Tests the value of the pacing signal at event transitions

        # Create a simple model
        m = myokit.Model()
        c = m.add_component('c')
        t = c.add_variable('t')
        t.set_rhs(0)
        t.set_binding('time')
        v = c.add_variable('v')
        v.set_rhs('0')
        v.set_binding('pace')
        x = c.add_variable('x')
        x.set_rhs(0.1)
        x.promote(0)

        # Create step protocol
        p = myokit.Protocol()
        p.schedule(0, 0, 2)
        p.schedule(1, 2, 2)
        p.schedule(2, 4, 4)
        p.schedule(3, 8, 2)

        # Simulate with dynamic logging
        s = myokit.LegacySimulation(m, p)
        d = s.run(p.characteristic_time())
        time = list(d.time())
        value = list(d['c.v'])

        if False:
            for i, t in enumerate(d.time()):
                t = str(np.round(t, 5))
                print(t + ' ' * (10 - len(t)) + str(d['c.v'][i]))

        # Values should be
        #   t   0   1   2   3   4   5   6   7   8   9   10
        #   p   0   0   1   1   2   2   2   2   3   3   0
        self.assertEqual(value[time.index(0.0)], 0)
        self.assertEqual(value[time.index(0.0) + 1], 0)
        self.assertEqual(value[time.index(2.0) - 1], 0)
        self.assertEqual(value[time.index(2.0)], 1)
        self.assertEqual(value[time.index(2.0) + 1], 1)
        self.assertEqual(value[time.index(4.0) - 1], 1)
        self.assertEqual(value[time.index(4.0)], 2)
        self.assertEqual(value[time.index(4.0) + 1], 2)
        self.assertEqual(value[time.index(8.0) - 1], 2)
        self.assertEqual(value[time.index(8.0)], 3)
        self.assertEqual(value[time.index(8.0) + 1], 3)
        self.assertEqual(value[time.index(10.0) - 1], 3)
        self.assertEqual(value[time.index(10.0)], 0)

        # Simulate with fixed logging
        s.reset()
        d = s.run(p.characteristic_time() + 1, log_times=d.time())
        time2 = list(d.time())
        value2 = list(d['c.v'])
        self.assertEqual(time, time2)
        self.assertEqual(value, value2)

    def test_progress_reporter(self):
        # Test running with a progress reporter.

        # Test if it works
        sim = myokit.LegacySimulation(self.model, self.protocol)
        with myokit.tools.capture() as c:
            sim.run(110, progress=myokit.ProgressPrinter())
        c = c.text().splitlines()
        self.assertEqual(len(c), 2)
        p = re.compile(re.escape('[0.0 minutes] 1.9 % done, estimated ') +
                       '[0-9]+' + re.escape(' seconds remaining'))
        self.assertIsNotNone(p.match(c[0]))
        p = re.compile(re.escape('[0.0 minutes] 100.0 % done, estimated ') +
                       '[0-9]+' + re.escape(' seconds remaining'))
        self.assertIsNotNone(p.match(c[1]))

        # Not a progress reporter
        self.assertRaisesRegex(
            ValueError, 'ProgressReporter', self.sim.run, 5, progress=12)

        # Cancel from reporter
        self.assertRaises(
            myokit.SimulationCancelledError, self.sim.run, 1,
            progress=CancellingReporter(0))

    def test_apd_tracking(self):
        # Test the APD calculation method.

        # More testing is done in test_datalog.py!

        # Apd var is not a state
        v = self.model.get('ina.INa')
        self.assertRaisesRegex(
            ValueError, 'must be a state', myokit.LegacySimulation, self.model,
            self.protocol, apd_var=v)

        # Set a valid apd variable
        v = self.model.get('ik.x')
        sim = myokit.LegacySimulation(
            self.model, self.protocol, apd_var=v)
        sim.run(1, apd_threshold=12)

        # No apd var given, but threshold provided
        self.assertRaisesRegex(
            ValueError, 'without apd_var', self.sim.run, 1, apd_threshold=12)

    def test_last_state(self):
        # Returns the last state before an error, or None.

        m = self.model.clone()
        istim = m.get('membrane.i_stim')
        istim.set_rhs('engine.pace / stim_amplitude')
        s = myokit.LegacySimulation(m, self.protocol)
        self.assertIsNone(s.last_state())
        s.run(1)
        self.assertIsNone(s.last_state())
        s.set_constant('membrane.i_stim.stim_amplitude', 0)
        s.reset()
        self.assertRaisesRegex(myokit.SimulationError, "at t = 0", s.run, 5)
        self.assertEqual(len(s.last_state()), len(s.state()))
        self.assertEqual(s.last_state(), s.state())

    def test_last_evaluations_and_steps(self):
        # Test :meth:`LegacySimulation.last_number_of_evaluations()` and
        # :meth:`LegacySimulation.last_number_of_steps()`

        s = myokit.LegacySimulation(self.model, self.protocol)
        self.assertEqual(s.last_number_of_evaluations(), 0)
        self.assertEqual(s.last_number_of_steps(), 0)
        s.run(1)
        self.assertTrue(s.last_number_of_evaluations() > 0)
        self.assertTrue(s.last_number_of_steps() > 0)
        self.assertNotEqual(
            s.last_number_of_evaluations(), s.last_number_of_steps())

    def test_eval_derivatives(self):
        # Test :meth:`LegacySimulation.eval_derivatives()`.

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
        # Test :meth:`LegacySimulation.set_tolerance()`.

        self.assertRaisesRegex(
            ValueError, 'Absolute', self.sim.set_tolerance, abs_tol=0)
        self.assertRaisesRegex(
            ValueError, 'Relative', self.sim.set_tolerance, rel_tol=0)
        self.sim.set_tolerance(1e-6, 1e-4)

    def test_set_step_size(self):
        # Test :meth:`LegacySimulation.set_min_step_size()` and
        # :meth:`LegacySimulation.set_max_step_size()`.

        # Minimum: set, unset, allow negative value to unset
        self.sim.set_min_step_size(0.1)
        self.sim.set_min_step_size(None)
        self.sim.set_min_step_size(-1)

        # Same for max
        self.sim.set_max_step_size(0.1)
        self.sim.set_max_step_size(None)
        self.sim.set_max_step_size(-1)

    def test_set_state(self):
        # Test :meth:`LegacySimulation.set_state()` and
        # :meth:`LegacySimulation.set_default_state()`.

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
        # Test :meth:`LegacySimulation.set_constant()`.

        # Literal
        v = self.model.get('cell.Na_i')
        self.sim.set_constant(v, 11)
        self.assertRaises(KeyError, self.sim.set_constant, 'cell.Bert', 11)

        # Calculated constant
        self.assertRaisesRegex(
            ValueError, 'not a literal', self.sim.set_constant, 'ina.ENa', 11)

    def test_short_runs(self):
        # Test for simulations run a very short time

        # Run for 1 unit (OK)
        self.sim.reset()
        self.sim.run(1)

        # Test running for 0 units doesn't affect state
        x0 = self.sim.state()
        self.sim.run(0)
        self.assertEqual(x0, self.sim.state())
        self.sim.run(0)
        self.assertEqual(x0, self.sim.state())

        # Test running between indistinguishable times doesn't affect state
        t = self.sim.time()
        d = 0.5 * sys.float_info.epsilon
        self.assertEqual(t, t + d)
        self.sim.run(d)

        # Test running between only just distinguishable times is fine
        self.sim.reset()
        self.sim.run(1)
        t = self.sim.time()
        d = 3 * sys.float_info.epsilon
        self.assertNotEqual(t, t + d)
        self.sim.run(d)

        # Test running between barely distinguishable times raises CVODE error.
        t = self.sim.time()
        d = 2 * sys.float_info.epsilon
        self.assertNotEqual(t, t + d)
        self.assertRaisesRegex(
            myokit.SimulationError, 'CV_TOO_CLOSE', self.sim.run, d)

        # Empty log times
        self.sim.reset()
        self.sim.run(1, log_times=[])

        # Non-monotonic times
        self.sim.reset()
        with self.assertRaisesRegex(ValueError, 'Values in log_times'):
            self.sim.run(1, log_times=[1, 2, 1])

        # Simultaneous use of log_times and log_interval
        self.sim.reset()
        with self.assertRaisesRegex(ValueError, 'The arguments log_times'):
            self.sim.run(1, log_times=[1, 2], log_interval=2)

    def test_simulation_error_1(self):
        # Test for simulation error detection: massive stimulus.

        # Silly protocol
        p = myokit.Protocol()
        p.schedule(level=1000, start=1, duration=1)
        self.sim.reset()
        self.sim.set_protocol(p)
        self.assertRaisesRegex(
            myokit.SimulationError, 'numerical error', self.sim.run, 10)
        self.sim.set_protocol(self.protocol)

    @unittest.skipIf(platform.system() != 'Linux', 'CVODE error tests')
    def test_simulation_error_2(self):
        # Test for simulation error detection: failure occurred too often.

        # Cvode error (test failure occurred too many times)
        m = self.model.clone()
        v = m.get('membrane.V')
        v.set_rhs(myokit.Multiply(v.rhs(), myokit.Number(1e18)))
        s = myokit.LegacySimulation(m, self.protocol)
        with WarningCollector():
            self.assertRaisesRegex(
                myokit.SimulationError, 'numerical error', s.run, 5000)

    def test_cvode_simulation_with_zero_states(self):
        # Tests running cvode simulations on models with no ODEs

        # Create a model without states
        m1 = myokit.Model()
        c = m1.add_component('c')
        t = c.add_variable('t')
        t.set_rhs(0)
        t.set_binding('time')
        v = c.add_variable('v')
        v.set_rhs('0')
        v.set_binding('pace')
        w = c.add_variable('w')
        w.set_rhs('2 * v')

        # Create a model with a state
        m2 = m1.clone()
        z = m2.get('c').add_variable('z')
        z.set_rhs(0.1)
        z.promote(0)

        # Test without protocol and dynamic logging
        s1 = myokit.LegacySimulation(m1)
        d1 = s1.run(5)
        self.assertEqual(len(d1.time()), 2)
        self.assertEqual(list(d1.time()), [0, 5])
        self.assertEqual(list(d1['c.w']), [0, 0])
        s2 = myokit.LegacySimulation(m2)
        d2 = s2.run(6, log_times=d1.time())
        self.assertEqual(d1.time(), d2.time())
        self.assertEqual(d1['c.w'], d2['c.w'])

        # Test with a protocol and dynamic logging
        p = myokit.Protocol()
        p.schedule(0, 0, 2)
        p.schedule(1, 2, 2)
        p.schedule(2, 4, 4)
        p.schedule(3, 8, 2)
        s1.reset()
        s1.set_protocol(p)
        d1 = s1.run(p.characteristic_time())
        self.assertEqual(len(d1.time()), 5)
        self.assertEqual(list(d1.time()), [0, 2, 4, 8, 10])
        self.assertEqual(list(d1['c.w']), [0, 2, 4, 6, 0])
        s2.reset()
        s2.set_protocol(p)
        d2 = s2.run(p.characteristic_time() + 1, log_times=d1.time())
        self.assertEqual(d1.time(), d2.time())
        self.assertEqual(d1['c.w'], d2['c.w'])

        # Test with fixed logging times
        s1.reset()
        d1 = s1.run(p.characteristic_time() + 1, log_times=d1['c.t'])
        self.assertEqual(list(d1.time()), [0, 2, 4, 8, 10])
        self.assertEqual(list(d1['c.w']), [0, 2, 4, 6, 0])
        s2.reset()
        d2 = s2.run(p.characteristic_time() + 1, log_times=d1.time())
        self.assertEqual(d1.time(), d2.time())
        self.assertEqual(d1['c.w'], d2['c.w'])

        # Test appending to log
        s1.reset()
        d1 = s1.run(5)
        d1 = s1.run(5, log=d1)
        self.assertEqual(list(d1.time()), [0, 2, 4, 5, 8, 10])
        self.assertEqual(list(d1['c.w']), [0, 2, 4, 4, 6, 0])

        # Test with a log interval
        s1.reset()
        d1 = s1.run(11, log_interval=1)
        self.assertEqual(list(d1.time()), [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        self.assertEqual(list(d1['c.w']), [0, 0, 2, 2, 4, 4, 4, 4, 6, 6, 0])

    def test_pickling(self):
        # Test pickling a simulation

        # Test with myokit.Protocol
        m, p, _ = myokit.load('example')
        s1 = myokit.LegacySimulation(m, p)
        s1.pre(123)
        s_bytes = pickle.dumps(s1)
        s2 = pickle.loads(s_bytes)
        self.assertEqual(s1.time(), s2.time())
        self.assertEqual(s1.state(), s2.state())
        self.assertEqual(s1.default_state(), s2.default_state())
        s1.run(123, log=myokit.LOG_NONE)
        s2.run(123, log=myokit.LOG_NONE)
        self.assertEqual(s1.time(), s2.time())
        self.assertEqual(s1.state(), s2.state())

        # Test simulation properties
        s1.set_tolerance(1e-8, 1e-8)
        s1.set_min_step_size(1e-2)
        s1.set_max_step_size(0.1)
        s2 = pickle.loads(pickle.dumps(s1))
        s1.run(23, log=myokit.LOG_NONE)
        s2.run(23, log=myokit.LOG_NONE)
        self.assertEqual(s1.time(), s2.time())
        self.assertEqual(s1.state(), s2.state())

        # Test changed constants
        s1.set_constant('membrane.C', 1.1)
        s2 = pickle.loads(pickle.dumps(s1))
        s1.run(17, log=myokit.LOG_NONE)
        s2.run(17, log=myokit.LOG_NONE)
        self.assertEqual(s1.time(), s2.time())
        self.assertEqual(s1.state(), s2.state())

    def test_sim_stats(self):
        # Test extraction of simulation statistics
        m, p, _ = myokit.load('example')
        rt = m['engine'].add_variable('realtime')
        rt.set_rhs(0)
        rt.set_binding('realtime')
        ev = m['engine'].add_variable('evaluations')
        ev.set_rhs(0)
        ev.set_binding('evaluations')
        s = myokit.LegacySimulation(m, p)
        d = s.run(100, log=myokit.LOG_BOUND).npview()

        self.assertIn('engine.realtime', d)
        self.assertIn('engine.evaluations', d)
        rt, ev = d['engine.realtime'], d['engine.evaluations']
        self.assertEqual(len(d.time()), len(rt))
        self.assertEqual(len(d.time()), len(ev))
        self.assertTrue(np.all(rt >= 0))
        self.assertTrue(np.all(ev >= 0))
        self.assertTrue(np.all(rt[1:] >= rt[:-1]))
        self.assertTrue(np.all(ev[1:] >= ev[:-1]))

    def test_apd(self):
        # Test the apd rootfinding routine

        s = myokit.LegacySimulation(
            self.model, self.protocol, apd_var='membrane.V')
        s.set_tolerance(1e-8, 1e-8)
        d, apds = s.run(1800, log=myokit.LOG_NONE, apd_threshold=-70)

        # Check with threshold equal to V
        self.assertEqual(len(apds['start']), 2)
        self.assertEqual(len(apds['duration']), 2)
        self.assertAlmostEqual(apds['start'][0], 1.19, places=1)
        self.assertAlmostEqual(apds['start'][1], 1001.19, places=1)
        self.assertAlmostEqual(apds['duration'][0], 383.88262, places=0)
        self.assertAlmostEqual(apds['duration'][1], 378.31448, places=0)

    def test_derivatives(self):
        # Tests logging of derivatives by comparing with a finite difference
        # approximation

        # Run past the upstroke, where finite diff approx is worst
        self.sim.reset()
        self.sim.run(52)

        # Now run logged part
        d = self.sim.run(600).npview()
        if False:
            import matplotlib.pyplot as plt
            plt.figure()
            ax = plt.subplot(3, 1, 1)
            ax.plot(d.time(), d['membrane.V'])
            ax = plt.subplot(3, 1, 2)
            ax.plot(d.time(), d['dot(membrane.V)'])

        # Get central difference approximation
        t = d.time()
        v = d['membrane.V']
        dv = (v[2:] - v[:-2]) / (t[2:] - t[:-2])
        e = d['dot(membrane.V)'][1:-1] - dv
        if False:
            t = t[1:-1]
            ax.plot(t, dv, '--')
            ax = plt.subplot(3, 1, 3)
            ax.plot(t, e)
            print(np.max(np.abs(e)))

        # Compare
        self.assertLess(np.max(np.abs(e)), 0.1)


if __name__ == '__main__':
    unittest.main()

