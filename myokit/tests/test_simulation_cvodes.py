#!/usr/bin/env python3
#
# Tests the CVODES simulation class.
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

from myokit.tests import (
    CancellingReporter,
    DIR_DATA,
    test_case_pk_model,
    WarningCollector,
)

# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp


class SimulationTest(unittest.TestCase):
    """
    Tests the CVODES simulation class.
    """

    @classmethod
    def setUpClass(cls):
        # Test simulation creation.

        m, p, x = myokit.load(os.path.join(DIR_DATA, 'lr-1991.mmt'))
        cls.model = m
        cls.protocol = p
        cls.sim = myokit.Simulation(cls.model, cls.protocol)

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
        s = myokit.Simulation(m, p)
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
        sim = myokit.Simulation(self.model, self.protocol)
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
        self.assertRaisesRegex(
            ValueError, 'must be a state',
            self.sim.run, 1000, apd_variable='ina.INa')

        # No apd var given, but threshold provided
        self.assertRaisesRegex(
            ValueError, 'no `apd_variable` specified',
            self.sim.run, 1, apd_threshold=12)

    def test_last_state(self):
        # Returns the last state before an error, or None.

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
        # Test :meth:`Simulation.last_number_of_evaluations()` and
        # :meth:`Simulation.last_number_of_steps()`

        s = myokit.Simulation(self.model, self.protocol)
        self.assertEqual(s.last_number_of_evaluations(), 0)
        self.assertEqual(s.last_number_of_steps(), 0)
        s.run(1)
        self.assertTrue(s.last_number_of_evaluations() > 0)
        self.assertTrue(s.last_number_of_steps() > 0)
        self.assertNotEqual(
            s.last_number_of_evaluations(), s.last_number_of_steps())

    def test_default_state_sensitivites(self):
        # Test :meth:`Simulation.default_state_sensitivies`

        # Create bolus infusion model with linear clearance
        model = myokit.Model()
        comp = model.add_component('myokit')

        amount = comp.add_variable('amount')
        time = comp.add_variable('time')
        dose_rate = comp.add_variable('dose_rate')
        elimination_rate = comp.add_variable('elimination_rate')

        time.set_binding('time')
        dose_rate.set_binding('pace')

        amount.promote(10)
        amount.set_rhs(
            myokit.Minus(
                myokit.Name(dose_rate),
                myokit.Multiply(
                    myokit.Name(elimination_rate),
                    myokit.Name(amount))))
        elimination_rate.set_rhs(myokit.Number(1))
        time.set_rhs(myokit.Number(0))
        dose_rate.set_rhs(myokit.Number(0))

        # Check no sensitivities set
        sim = myokit.Simulation(model)
        self.assertIsNone(sim.default_state_sensitivities())

        # Check for set sensitvities
        sensitivities = (
            ['myokit.amount'],
            ['init(myokit.amount)', 'myokit.elimination_rate'])
        sim = myokit.Simulation(model, sensitivities=sensitivities)
        s = sim.default_state_sensitivities()
        self.assertEqual(len(s), 2)
        self.assertEqual(s[0][0], 1)
        self.assertEqual(s[1][0], 0)

    def test_eval_derivatives(self):
        # Test :meth:`Simulation.eval_derivatives()`.

        self.sim.reset()
        s1 = self.sim.state()
        d1 = self.sim.eval_derivatives()
        self.sim.run(1)
        d2 = self.sim.eval_derivatives()
        self.assertNotEqual(d1, d2)
        self.assertEqual(d1, self.sim.eval_derivatives(s1))
        self.sim.set_state(s1)
        self.assertEqual(d1, self.sim.eval_derivatives())

    def test_sensitivites_initial(self):
        # Test setting initial sensitivity values.

        m = myokit.parse_model('''
            [[model]]
            e.y = 2.3

            [e]
            t = 0 bind time
            p = 1 / 100
            dot(y) = 2 * p - y
            ''')
        m.validate()

        #TODO: Test results
        s = myokit.Simulation(m, sensitivities=(['e.y'], ['e.p', 'init(e.y)']))

        # Test bad initial matrix
        self.assertRaisesRegex(
            ValueError, 'None or a list',
            s.run, 10, sensitivities='hello')

    def test_sensitivity_ordering(self):
        # Tests that sensitivities are returned in the correct order

        # Define model
        model = myokit.parse_model(
            """
            [[model]]
            name: one_compartment_pk_model
            # Initial values
            central.drug_amount = 0.1
            dose.drug_amount    = 0.1

            [central]
            dose_rate = 0 bind pace
                in [g/s (1.1574074074074077e-08)]
            dot(drug_amount) = -(
                    size * e.elimination_rate * drug_concentration) + (
                    dose.absorption_rate * dose.drug_amount)
                in [kg (1e-06)]
            drug_concentration = drug_amount / size
                in [g/m^3]
            size = 0.1
                in [L]

            [dose]
            absorption_rate = 0.1
                in [S/F (1.1574074074074077e-05)]
            dot(drug_amount) = (-absorption_rate * drug_amount
                                + central.dose_rate)
                in [kg (1e-06)]

            [e]
            elimination_rate = 0.1
                in [S/F (1.1574074074074077e-05)]
            time = 0 bind time
                in [s (86400)]
            """
        )

        # Select all states and possible independents
        var = ['central.drug_amount', 'dose.drug_amount']
        par = [
            'central.size',
            'init(central.drug_amount)',
            'dose.absorption_rate',
            'init(dose.drug_amount)',
            'e.elimination_rate',
        ]

        # Run and store
        sim = myokit.Simulation(model, sensitivities=(var, par))
        _, s1 = sim.run(6, log=myokit.LOG_NONE, log_interval=2)
        s1 = np.array(s1)

        # Now use reverse order
        var.reverse()
        par.reverse()

        # Run and store
        sim = myokit.Simulation(model, sensitivities=(var, par))
        _, s2 = sim.run(6, log=myokit.LOG_NONE, log_interval=2)
        s2 = np.array(s2)

        # Reverse results, to get back original order
        s2 = s2[:, ::-1, ::-1]
        self.assertTrue(np.all(s1 == s2))

    def test_sensitivities_bolus_infusion(self):
        # Test :meth:`Simulation.run()` accuracy by comparing to
        # analytic solution in a PKPD bolus infusion model.

        # Create bolus infusion model with linear clearance
        model = myokit.Model()
        comp = model.add_component('myokit')

        amount = comp.add_variable('amount')
        time = comp.add_variable('time')
        dose_rate = comp.add_variable('dose_rate')
        elimination_rate = comp.add_variable('elimination_rate')

        time.set_binding('time')
        dose_rate.set_binding('pace')

        amount.promote(10)
        amount.set_rhs(
            myokit.Minus(
                myokit.Name(dose_rate),
                myokit.Multiply(
                    myokit.Name(elimination_rate),
                    myokit.Name(amount))))
        elimination_rate.set_rhs(myokit.Number(1))
        time.set_rhs(myokit.Number(0))
        dose_rate.set_rhs(myokit.Number(0))

        # Create protocol
        amount = 5
        duration = 0.001
        protocol = myokit.pacing.blocktrain(
            1, duration, offset=0, level=amount / duration, limit=0)

        # Set sensitivies
        sensitivities = (
            ['myokit.amount'],
            ['init(myokit.amount)', 'myokit.elimination_rate'])

        sim = myokit.Simulation(model, protocol, sensitivities)

        # Set tolerance to be controlled by abs_tolerance for
        # easier comparison
        #TODO This rel_tol is insanely high
        sim.set_tolerance(abs_tol=1e-8, rel_tol=1e-30)

        # Solve problem analytically
        parameters = [10, 1, amount / duration, duration]
        times = np.linspace(0.1, 10, 13)
        ref_sol, ref_partials = test_case_pk_model(parameters, times)

        # Solve problem with simulator
        sol, partials = sim.run(
            11, log_times=times, log=['myokit.amount'])
        sol = np.array(sol['myokit.amount'])
        partials = np.array(partials).squeeze()

        # Check state
        self.assertAlmostEqual(sol[0], ref_sol[0], 6)
        self.assertAlmostEqual(sol[1], ref_sol[1], 6)
        self.assertAlmostEqual(sol[2], ref_sol[2], 6)
        self.assertAlmostEqual(sol[3], ref_sol[3], 6)
        self.assertAlmostEqual(sol[4], ref_sol[4], 6)
        self.assertAlmostEqual(sol[5], ref_sol[5], 6)
        self.assertAlmostEqual(sol[6], ref_sol[6], 6)
        self.assertAlmostEqual(sol[7], ref_sol[7], 6)
        self.assertAlmostEqual(sol[8], ref_sol[8], 6)
        self.assertAlmostEqual(sol[9], ref_sol[9], 6)
        self.assertAlmostEqual(sol[10], ref_sol[10], 6)
        self.assertAlmostEqual(sol[11], ref_sol[11], 6)
        self.assertAlmostEqual(sol[12], ref_sol[12], 6)

        # Check partials
        self.assertAlmostEqual(partials[0, 0], ref_partials[0, 0], 6)
        self.assertAlmostEqual(partials[1, 0], ref_partials[0, 1], 6)
        self.assertAlmostEqual(partials[2, 0], ref_partials[0, 2], 6)
        self.assertAlmostEqual(partials[3, 0], ref_partials[0, 3], 6)
        self.assertAlmostEqual(partials[4, 0], ref_partials[0, 4], 6)
        self.assertAlmostEqual(partials[5, 0], ref_partials[0, 5], 6)
        self.assertAlmostEqual(partials[6, 0], ref_partials[0, 6], 6)
        self.assertAlmostEqual(partials[7, 0], ref_partials[0, 7], 6)
        self.assertAlmostEqual(partials[8, 0], ref_partials[0, 8], 6)
        self.assertAlmostEqual(partials[9, 0], ref_partials[0, 9], 6)
        self.assertAlmostEqual(partials[10, 0], ref_partials[0, 10], 6)
        self.assertAlmostEqual(partials[11, 0], ref_partials[0, 11], 6)
        self.assertAlmostEqual(partials[12, 0], ref_partials[0, 12], 6)

        # Return apds
        result = sim.run(1, apd_variable='myokit.amount', apd_threshold=0.3)
        self.assertEqual(len(result), 3)

    def test_sensitivities_with_derivatives(self):
        # Test various inputs to the `sensitivities` argument are handled
        # correctly, including sensitivites of derivatives and intermediary
        # variables depending on derivatives.

        # Note: passing the wrong values into the sensitivities constructor arg
        # is tested in the CModel tests.

        m = myokit.parse_model('''
            [[model]]
            e.x = 1.2
            e.y = 2.3

            [e]
            t = 0 bind time
            p = 1 / 100
            q = 2
            r = 3
            dot(x) = p * q
            dot(y) = 2 * p - y
            fx = x^2
            fy = r + p^2 + dot(y)
            ''')
        m.validate()

        x0 = m.get('e.x').state_value()
        y0 = m.get('e.y').state_value()
        p = m.get('e.p').eval()
        q = m.get('e.q').eval()
        r = m.get('e.r').eval()

        # Dependents is a list of y in dy/dx.
        # Must refer to state, derivative, or intermediary, given as:
        #  - Variable
        #  - Name
        #  - Derivative
        #  - "qname"
        #  - "dot(qname)"
        dependents = [
            'e.x',                  # qname
            'e.y',                  # qname
            'dot(e.x)',             # dot(qname)
            m.get('e.y').lhs(),     # Derivative
            m.get('e.fx'),          # Variable
            m.get('e.fy').lhs(),    # Name
        ]

        # Independents is a list of x in dy/dx
        # Must refer to literals or initial values, given as:
        #  - Variable
        #  - Name
        #  - InitialValue
        #  - "qname"
        #  - "init(qname)"
        independents = [
            'e.p',                  # qname
            m.get('e.q'),           # qname
            m.get('e.r').lhs(),     # Name
            'init(e.x)',            # init(qname)
            myokit.InitialValue(myokit.Name(m.get('e.y'))),  # InitialValue
        ]

        # Run, get output
        s = myokit.Simulation(m, sensitivities=(dependents, independents))
        s.set_tolerance(1e-9, 1e-9)
        d, e = s.run(8)
        d, e = d.npview(), np.array(e)
        t = d.time()

        # Check solution
        self.assertTrue(
            np.allclose(d['e.x'], x0 + p * q * t))
        self.assertTrue(np.allclose(
            d['e.y'], 2 * p + (y0 - 2 * p) * np.exp(-t)))
        self.assertTrue(np.allclose(
            d['e.fx'], (p * q * t)**2 + 2 * p * q * t * x0 + x0**2))
        self.assertTrue(np.allclose(
            d['e.fy'], r + p**2 + (2 * p - y0) * np.exp(-t)))
        self.assertTrue(np.allclose(
            d['dot(e.x)'], p * q))
        self.assertTrue(np.allclose(
            d['dot(e.y)'], (2 * p - y0) * np.exp(-t)))

        # Sensitivities of  x  to (p, q, r, x0, y0)
        self.assertTrue(np.allclose(e[:, 0, 0], q * t))
        self.assertTrue(np.allclose(e[:, 0, 1], p * t))
        self.assertTrue(np.allclose(e[:, 0, 2], 0))
        self.assertTrue(np.allclose(e[:, 0, 3], 1))
        self.assertTrue(np.allclose(e[:, 0, 4], 0))

        # Sensitivities of  y  to (p, q, r, x0, y0)
        self.assertTrue(np.allclose(e[:, 1, 0], 2 - 2 * np.exp(-t)))
        self.assertTrue(np.allclose(e[:, 1, 1], 0))
        self.assertTrue(np.allclose(e[:, 1, 2], 0))
        self.assertTrue(np.allclose(e[:, 1, 3], 0))
        self.assertTrue(np.allclose(e[:, 1, 4], np.exp(-t)))

        # Sensitivities of  dot(x)  to (p, q, r, x0, y0)
        self.assertTrue(np.allclose(e[:, 2, 0], q))
        self.assertTrue(np.allclose(e[:, 2, 1], p))
        self.assertTrue(np.allclose(e[:, 2, 2], 0))
        self.assertTrue(np.allclose(e[:, 2, 3], 0))
        self.assertTrue(np.allclose(e[:, 2, 4], 0))

        # Sensitivities of  dot(y)  to (p, q, r, x0, y0)
        self.assertTrue(np.allclose(e[:, 3, 0], 2 * np.exp(-t)))
        self.assertTrue(np.allclose(e[:, 3, 1], 0))
        self.assertTrue(np.allclose(e[:, 3, 2], 0))
        self.assertTrue(np.allclose(e[:, 3, 3], 0))
        self.assertTrue(np.allclose(e[:, 3, 4], -np.exp(-t)))

        # Sensitivities of  fx  to (p, q, r, x0, y0)
        self.assertTrue(np.allclose(
            e[:, 4, 0], 2 * p * (q * t)**2 + 2 * q * t * x0))
        self.assertTrue(np.allclose(
            e[:, 4, 1], 2 * q * (p * t)**2 + 2 * p * t * x0))
        self.assertTrue(np.allclose(
            e[:, 4, 2], 0))
        self.assertTrue(np.allclose(
            e[:, 4, 3], 2 * p * q * t + 2 * x0))
        self.assertTrue(np.allclose(
            e[:, 4, 4], 0))

        # Sensitivities of  fy  to (p, q, r, x0, y0)
        self.assertTrue(np.allclose(e[:, 5, 0], 2 * p + 2 * np.exp(-t)))
        self.assertTrue(np.allclose(e[:, 5, 1], 0))
        self.assertTrue(np.allclose(e[:, 5, 2], 1))
        self.assertTrue(np.allclose(e[:, 5, 3], 0))
        self.assertTrue(np.allclose(e[:, 5, 4], -np.exp(-t)))

    def test_set_tolerance(self):
        # Test :meth:`Simulation.set_tolerance()`.

        self.assertRaisesRegex(
            ValueError, 'Absolute', self.sim.set_tolerance, abs_tol=0)
        self.assertRaisesRegex(
            ValueError, 'Relative', self.sim.set_tolerance, rel_tol=0)
        self.sim.set_tolerance(1e-6, 1e-4)

    def test_set_step_size(self):
        # Test :meth:`Simulation.set_min_step_size()` and
        # :meth:`Simulation.set_max_step_size()`.

        # Minimum: set, unset, allow negative value to unset
        self.sim.set_min_step_size(0.1)
        self.sim.set_min_step_size(None)
        self.sim.set_min_step_size(-1)

        # Same for max
        self.sim.set_max_step_size(0.1)
        self.sim.set_max_step_size(None)
        self.sim.set_max_step_size(-1)

    def test_set_state(self):
        # Test :meth:`Simulation.set_state()` and
        # :meth:`Simulation.set_default_state()`.

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
        # Test :meth:`Simulation.set_constant()`.

        # Literal
        self.sim.set_constant('cell.Na_i', 11)
        self.assertRaises(KeyError, self.sim.set_constant, 'cell.Bert', 11)

        # Parameter (needs sensitivies set)
        m, p, x = myokit.load(os.path.join(DIR_DATA, 'lr-1991.mmt'))
        sim = myokit.Simulation(m, p, (['ib.Ib'], ['ib.gb']))
        sim.set_constant('ib.gb', 20)

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

    @unittest.skipIf(platform.system() != 'Linux', 'Cvode error tests')
    def test_simulation_error_2(self):
        # Test for simulation error detection: failure occurred too often.

        # Cvode error (test failure occurred too many times)
        m = self.model.clone()
        v = m.get('membrane.V')
        v.set_rhs(myokit.Multiply(v.rhs(), myokit.Number(1e18)))
        s = myokit.Simulation(m, self.protocol)
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
        s1 = myokit.Simulation(m1)
        d1 = s1.run(5)
        self.assertEqual(len(d1.time()), 2)
        self.assertEqual(list(d1.time()), [0, 5])
        self.assertEqual(list(d1['c.w']), [0, 0])
        s2 = myokit.Simulation(m2)
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

        # Test with myokit.Protocol and sensitivities
        m, p, _ = myokit.load('example')
        s1 = myokit.Simulation(m, p, [
            ['ina.INa', 'ica.ICa', 'membrane.V'],
            ['ina.gNa', 'init(membrane.V)']
        ])
        s1.pre(123)
        # ...and with simulation properties
        s1.set_tolerance(1e-8, 1e-8)
        s1.set_min_step_size(1e-4)
        s1.set_max_step_size(0.1)
        # ...and changed properties
        s1.set_constant('membrane.C', 1.1)
        s_bytes = pickle.dumps(s1)
        s2 = pickle.loads(s_bytes)
        self.assertEqual(s1.time(), s2.time())
        self.assertEqual(s1.state(), s2.state())
        self.assertEqual(s1.default_state(), s2.default_state())
        d1, e1 = s1.run(123, log=myokit.LOG_NONE)
        d2, e2 = s2.run(123, log=myokit.LOG_NONE)
        self.assertEqual(s1.time(), s2.time())
        self.assertEqual(s1.state(), s2.state())
        self.assertTrue(np.all(e1 == e2))

    def test_sim_stats(self):
        # Test extraction of simulation statistics
        m, p, _ = myokit.load('example')
        rt = m['engine'].add_variable('realtime')
        rt.set_rhs(0)
        rt.set_binding('realtime')
        ev = m['engine'].add_variable('evaluations')
        ev.set_rhs(0)
        ev.set_binding('evaluations')
        s = myokit.Simulation(m, p)
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

        s = myokit.Simulation(self.model, self.protocol)
        s.set_tolerance(1e-8, 1e-8)
        d, apds = s.run(
            1800, log=myokit.LOG_NONE,
            apd_variable='membrane.V', apd_threshold=-70)

        # Check with threshold equal to V
        self.assertEqual(len(apds['start']), 2)
        self.assertEqual(len(apds['duration']), 2)
        self.assertAlmostEqual(apds['start'][0], 1.19, places=1)
        self.assertAlmostEqual(apds['start'][1], 1001.19, places=1)
        self.assertAlmostEqual(apds['duration'][0], 383.88262, places=1)
        self.assertAlmostEqual(apds['duration'][1], 378.31448, places=1)

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
