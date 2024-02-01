#!/usr/bin/env python3
#
# Tests the CVODES simulation class.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
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


class SimulationTest(unittest.TestCase):
    """
    Tests the CVODES simulation class.
    """


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

    def test_sensitivities_initial(self):
        # Test setting initial sensitivity values.

        m = myokit.parse_model('''
            [[model]]
            e.y = 1 + 1.3

            [e]
            t = 0 bind time
            p = 1 / 100
            dot(y) = 2 * p - y
            ''')
        m.validate()

        #TODO: Test results
        s = myokit.Simulation(m, sensitivities=(['e.y'], ['e.p', 'init(e.y)']))

        # Warn if a parameter sensitivity won't be picked up.
        m = myokit.parse_model('''
            [[model]]
            c.x = 1 / c.p

            [c]
            t = 0 bind time
            p = 1 / q
            q = 5
            r = 3
            dot(x) = 2 + r
            ''')
        m.validate()
        s = (['c.x'], ['c.q'])
        self.assertRaisesRegex(
            NotImplementedError, 'respect to parameters used in initial',
            myokit.Simulation, m, sensitivities=s)
        s = (['c.x'], ['c.r'])
        s = myokit.Simulation(m, sensitivities=s)

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

        x0 = m.get('e.x').initial_value(True)
        y0 = m.get('e.y').initial_value(True)
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


if __name__ == '__main__':
    unittest.main()
