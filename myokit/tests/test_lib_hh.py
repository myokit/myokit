#!/usr/bin/env python3
#
# Tests the lib.hh module.
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
import myokit.lib.hh as hh

from myokit.tests import DIR_DATA

# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp


MODEL = """
[[model]]
membrane.V = -80
ikr.a = 4.5e-4
ikr.r = 0.15
ina.r = 0.15
binding.act = 1e-4
binding.rec = 0.56
binding.b = 1e-4

[engine]
time = 0 bind time
pace = 0 bind pace

[membrane]
dot(V) = 0
    label membrane_potential

[ikr]
use membrane.V
IKr = g * a * r^2 * (V - EK)
dot(a) = (inf - a) / tau
    inf = alpha * tau
    tau = 1 / (alpha + beta)
    alpha = 2e-4 * exp(+7e-2 * V)
    beta = 3e-5 * exp(-5e-2 * V)
dot(r) = alpha * (1 - r) - beta * r
    alpha = 8e-2 * exp(+3e-3 * V)
    beta = 5e-3 * exp(-1e-2 * V)
g = 3
EK = -85

[ina]
use membrane.V as V
dot(r) = alpha * (1 - r) - beta * r
    alpha = 8e-2 * exp(+3e-3 * V)
    beta = 5e-3 * exp(-1e-2 * V)

[binding]
use membrane.V
conc = 10 [nM]
dot(act) = k1 * (1 - act) - k2 * act
    k1 = 2e-4 * exp(7e-2 * V)
    k2 = 3e-5 * exp(-5e-2 * V)
dot(rec) = k4 * (1 - rec) - k3 * rec
    k3 = 9e-2 * exp(9e-3 * V)
    k4 = 5e-3 * exp(-3e-2 * V)
dot(b) = (inf - b) / tau
    inf = (kon * conc) * tau
    tau = 1 / (kon * conc + koff)
kon = 1e-4 [1/nM/ms]
koff = 1e-5 [1/ms]
g = 3
EK = -85
I = g * (1 - b) * act * rec * (V - EK)
"""


class HHDetectionTest(unittest.TestCase):
    """
    Tests methods to detect HH states.
    """

    def test_alpha_beta_form(self):
        # Test methods for working with alpha-beta form
        m = myokit.parse_model(MODEL)
        self.assertIsInstance(m, myokit.Model)
        v = m.get('membrane.V')
        a = m.get('ikr.a')
        r = m.get('ikr.r')

        # Test without v (detected from label)
        self.assertTrue(hh.has_alpha_beta_form(r))
        alph, beta = hh.get_alpha_and_beta(r)
        self.assertEqual(alph, m.get('ikr.r.alpha'))
        self.assertEqual(beta, m.get('ikr.r.beta'))
        self.assertFalse(hh.has_alpha_beta_form(a))
        self.assertIsNone(hh.get_alpha_and_beta(a))

        # Test with v as a state, without a label
        v.set_label(None)
        self.assertRaisesRegex(
            ValueError, 'Membrane potential must be given',
            hh.has_alpha_beta_form, r)
        self.assertTrue(hh.has_alpha_beta_form(r, v))
        alph, beta = hh.get_alpha_and_beta(r, v)
        self.assertEqual(alph, m.get('ikr.r.alpha'))
        self.assertEqual(beta, m.get('ikr.r.beta'))
        self.assertFalse(hh.has_alpha_beta_form(a, v))
        self.assertIsNone(hh.get_alpha_and_beta(a, v))

        # Test with v as a constant
        v.demote()
        v.set_rhs(-80)
        self.assertTrue(hh.has_alpha_beta_form(r, v))
        alph, beta = hh.get_alpha_and_beta(r, v)
        self.assertEqual(alph, m.get('ikr.r.alpha'))
        self.assertEqual(beta, m.get('ikr.r.beta'))
        self.assertFalse(hh.has_alpha_beta_form(a, v))
        self.assertIsNone(hh.get_alpha_and_beta(a, v))

        # Almost correct forms / different ways to fail
        def bad(e):
            r.set_rhs(e)
            self.assertFalse(hh.has_alpha_beta_form(r, v))
            r.set_rhs('alpha * (1 - r) - beta * r')
            self.assertTrue(hh.has_alpha_beta_form(r, v))

        def good(e):
            r.set_rhs(e)
            self.assertTrue(hh.has_alpha_beta_form(r, v))

        # r is not a state
        self.assertTrue(hh.has_alpha_beta_form(r, v))
        r.demote()
        self.assertFalse(hh.has_alpha_beta_form(r, v))
        r.promote(0)
        self.assertTrue(hh.has_alpha_beta_form(r, v))

        # Not a minus
        bad('alpha * (1 - r) + beta * r')

        # Minus, but terms aren't multiplies
        bad('alpha / (1 - r) - beta * r')
        bad('alpha * (1 - r) - beta / r')

        # Terms in multiplications can be switched
        good('(1 - r) * alpha - beta * r')
        good('(1 - r) * alpha - r * beta')
        good('alpha * (1 - r) - beta * r')

        # But the correct terms are required
        bad('alpha * (2 - r) - beta * r')
        bad('alpha^2 * (1 - r) - beta * r')
        bad('alpha * (1 - r) - beta * r^2')
        bad('alpha * (1 - r) - beta^2 * r')

        # Alpha and beta can't be states
        m2 = m.clone()
        m2.get('membrane.V').set_label('membrane_potential')
        m2.get('ikr.r').move_variable(
            m2.get('ikr.r.alpha'), m2.get('ikr'), 'ralpha')
        self.assertTrue(hh.has_alpha_beta_form(m2.get('ikr.r')))
        m2.get('ikr.ralpha').promote(1)
        self.assertFalse(hh.has_alpha_beta_form(m2.get('ikr.r')))
        m2.get('ikr.ralpha').demote()
        m2.get('ikr.r').move_variable(
            m2.get('ikr.r.beta'), m2.get('ikr'), 'rbeta')
        self.assertTrue(hh.has_alpha_beta_form(m2.get('ikr.r')))
        m2.get('ikr.rbeta').promote(1)

        # Alpha and beta can't depend on other states than v
        c = m.add_component('ccc')
        x = c.add_variable('vvv')
        x.set_rhs(1)
        x.promote(0)
        ralph = m.get('ikr.r.alpha').rhs()
        self.assertTrue(hh.has_alpha_beta_form(r, v))
        m.get('ikr.r.alpha').set_rhs('3 * ccc.vvv + V')
        self.assertFalse(hh.has_alpha_beta_form(r, v))
        m.get('ikr.r.alpha').set_rhs(ralph)
        self.assertTrue(hh.has_alpha_beta_form(r, v))
        ralph = m.get('ikr.r.beta').rhs()
        m.get('ikr.r.beta').set_rhs('2 + ccc.vvv - V')
        self.assertFalse(hh.has_alpha_beta_form(r, v))
        m.get('ikr.r.beta').set_rhs(ralph)
        self.assertTrue(hh.has_alpha_beta_form(r, v))

    def test_inf_tau_form(self):
        # Test methods for working with inf-tau form
        m = myokit.parse_model(MODEL)
        self.assertIsInstance(m, myokit.Model)
        v = m.get('membrane.V')
        a = m.get('ikr.a')
        r = m.get('ikr.r')

        # Test with v detected from label
        self.assertTrue(hh.has_inf_tau_form(a))
        inf, tau = hh.get_inf_and_tau(a)
        self.assertEqual(inf, m.get('ikr.a.inf'))
        self.assertEqual(tau, m.get('ikr.a.tau'))
        self.assertFalse(hh.has_inf_tau_form(r))
        self.assertIsNone(hh.get_inf_and_tau(r))

        # Test with v argument, no label
        v.set_label(None)
        self.assertRaisesRegex(
            ValueError, 'Membrane potential must be given',
            hh.has_inf_tau_form, a)
        self.assertTrue(hh.has_inf_tau_form(a, v))
        inf, tau = hh.get_inf_and_tau(a, v)
        self.assertEqual(inf, m.get('ikr.a.inf'))
        self.assertEqual(tau, m.get('ikr.a.tau'))
        self.assertFalse(hh.has_inf_tau_form(r, v))
        self.assertIsNone(hh.get_inf_and_tau(r, v))

        # Test with v as a constant
        v.demote()
        v.set_rhs(-80)
        self.assertTrue(hh.has_inf_tau_form(a, v))
        inf, tau = hh.get_inf_and_tau(a, v)
        self.assertEqual(inf, m.get('ikr.a.inf'))
        self.assertEqual(tau, m.get('ikr.a.tau'))
        self.assertFalse(hh.has_inf_tau_form(r, v))
        self.assertIsNone(hh.get_inf_and_tau(r, v))
        del r

        # a is not a state
        self.assertTrue(hh.has_inf_tau_form(a, v))
        a.demote()
        self.assertFalse(hh.has_inf_tau_form(a, v))
        a.promote(0)
        self.assertTrue(hh.has_inf_tau_form(a, v))

        # Almost correct forms / different ways to fail
        def bad(e):
            a.set_rhs(e)
            self.assertFalse(hh.has_inf_tau_form(a, v))
            a.set_rhs('(inf - a) / tau')
            self.assertTrue(hh.has_inf_tau_form(a, v))

        def good(e):
            a.set_rhs(e)
            self.assertTrue(hh.has_inf_tau_form(a, v))

        bad('(inf - a) / (1 + tau)')
        bad('(inf + a) / tau')
        bad('(inf - 1) / tau')
        bad('(1 - inf) / tau')
        bad('(inf - r) / tau')

        # Inf and tau can't be states
        m.get('ikr.a').move_variable(m.get('ikr.a.inf'), m.get('ikr'), 'ainf')
        m.get('ikr.a').move_variable(m.get('ikr.a.tau'), m.get('ikr'), 'atau')
        self.assertTrue(hh.has_inf_tau_form(a, v))
        m.get('ikr.ainf').promote(1)
        self.assertFalse(hh.has_inf_tau_form(a, v))
        m.get('ikr.ainf').demote()
        self.assertTrue(hh.has_inf_tau_form(a, v))
        m.get('ikr.atau').promote(1)
        self.assertFalse(hh.has_inf_tau_form(a, v))
        m.get('ikr.atau').demote()
        self.assertTrue(hh.has_inf_tau_form(a, v))

        # Inf and tau can't depend on other states than v
        c = m.add_component('ccc')
        x = c.add_variable('vvv')
        x.set_rhs(1)
        x.promote(0)
        ainf = m.get('ikr.ainf').rhs()
        m.get('ikr.ainf').set_rhs('2 + ccc.vvv * V')
        self.assertFalse(hh.has_inf_tau_form(a, v))
        m.get('ikr.ainf').set_rhs(ainf)
        self.assertTrue(hh.has_inf_tau_form(a, v))
        atau = m.get('ikr.atau').rhs()
        m.get('ikr.atau').set_rhs('3 * ccc.vvv * V')
        self.assertFalse(hh.has_inf_tau_form(a, v))
        m.get('ikr.atau').set_rhs(atau)
        self.assertTrue(hh.has_inf_tau_form(a, v))

    def test_convert_hh_states_to_inf_tau_form(self):
        # Tests conversion to inf-tau form
        m1 = myokit.parse_model(MODEL)
        self.assertTrue(hh.has_inf_tau_form(m1.get('ikr.a')))
        self.assertFalse(hh.has_inf_tau_form(m1.get('ikr.r')))

        # Rewrite model
        m2 = hh.convert_hh_states_to_inf_tau_form(m1)
        self.assertNotEqual(m1.code(), m2.code())
        self.assertTrue(hh.has_inf_tau_form(m1.get('ikr.a')))
        self.assertFalse(hh.has_inf_tau_form(m1.get('ikr.r')))
        self.assertTrue(hh.has_inf_tau_form(m2.get('ikr.a')))
        self.assertTrue(hh.has_inf_tau_form(m2.get('ikr.r')))

        # Test only r was affected
        self.assertEqual(m1.get('ikr.a').code(), m2.get('ikr.a').code())
        self.assertNotEqual(m1.get('ikr.r').code(), m2.get('ikr.r').code())

        # Test form
        self.assertEqual(m2.get('ikr.r').rhs().code(), '(inf - ikr.r) / tau')
        a = m2.get('ikr.r.alpha').eval()
        b = m2.get('ikr.r.beta').eval()
        inf = m2.get('ikr.r.inf').eval()
        tau = m2.get('ikr.r.tau').eval()
        self.assertAlmostEqual(inf, a / (a + b))
        self.assertAlmostEqual(tau, 1 / (a + b))

        # Test state values are similar
        self.assertAlmostEqual(
            m1.get('ikr.r').eval(),
            m2.get('ikr.r').eval()
        )

        # Second rewrite isn't necessary
        m3 = hh.convert_hh_states_to_inf_tau_form(m2)
        self.assertEqual(m2.code(), m3.code())

        # First argument must be a myokit model
        self.assertRaisesRegex(
            ValueError, 'must be a myokit.Model',
            hh.convert_hh_states_to_inf_tau_form, [])

        # Membrane potential given explicitly (not as label)
        m2 = m1.clone()
        v = m2.get('membrane.V')
        v.set_label(None)
        m3 = hh.convert_hh_states_to_inf_tau_form(m2, v)
        self.assertNotEqual(m2.code(), m3.code())
        # Note: the next methods are called with v from m2, not v from m3! But
        # this should still work as variables are .get() from the model.
        self.assertTrue(hh.has_inf_tau_form(m3.get('ikr.a'), v))
        self.assertTrue(hh.has_inf_tau_form(m3.get('ikr.r'), v))

        # Unknown membrane potential
        self.assertRaisesRegex(
            ValueError, 'Membrane potential must be given',
            hh.convert_hh_states_to_inf_tau_form, m2)

    def test_rush_larsen_conversion(self):
        # Tests methods for writing RL state updates
        m1 = myokit.parse_model(MODEL)
        m2 = hh.convert_hh_states_to_inf_tau_form(m1)

        # Test RL update method
        dt = myokit.Name('dt')
        rl = hh.get_rl_expression(m2.get('ikr.a'), dt)
        self.assertEqual(
            rl.code(), 'inf + (ikr.a - inf) * exp(-(str:dt / tau))')
        rl = hh.get_rl_expression(m2.get('ikr.r'), dt)
        self.assertEqual(
            rl.code(), 'inf + (ikr.r - inf) * exp(-(str:dt / tau))')

        # Test RL update is close to Euler for small dt
        m2.get('membrane.V').set_rhs(20)
        ikr = m2.get('ikr')
        dt = ikr.add_variable('dt')
        dt.set_rhs(1e-6)
        # Test for a
        a = m2.get('ikr.a')
        rl = hh.get_rl_expression(a, myokit.Name(dt))
        a1 = rl.eval()
        a2 = a.state_value() + dt.eval() * a.rhs().eval()
        self.assertAlmostEqual(a1, a2)
        # And for r
        r = m2.get('ikr.r')
        rl = hh.get_rl_expression(r, myokit.Name(dt))
        r1 = rl.eval()
        r2 = r.state_value() + dt.eval() * r.rhs().eval()
        self.assertAlmostEqual(r1, r2)

        # Dt must be an expression
        self.assertRaisesRegex(
            ValueError, 'must be a myokit.Expression',
            hh.get_rl_expression, a, 'dt')

        # Returns None if not in inf-tau form
        self.assertIsNone(hh.get_rl_expression(
            m1.get('ikr.r'), myokit.Name(dt)))


class HHModelTest(unittest.TestCase):
    """
    Tests the HHModel class.
    """

    def test_manual_creation(self):
        # Test manual creation of a HHModel.

        # Load model
        fname = os.path.join(DIR_DATA, 'lr-1991-fitting.mmt')
        model = myokit.load_model(fname)

        # Select a number of states and parameters
        states = [
            'ina.m',
            model.get('ina.h'),
            'ina.j',
        ]
        parameters = [
            'ina.p1',
            model.get('ina.p10'),
            model.get('ina.p20'),
            'ina.p30',
        ]
        current = 'ina.INa'

        # Create a current model
        m = hh.HHModel(model, states, parameters, current)
        hh.HHModel(model, states, parameters, model.get(current))

        # Check membrane potential
        self.assertEqual(m.membrane_potential(), 'membrane.V')

        # Check parameters
        parameters[1] = parameters[1].qname()
        parameters[2] = parameters[2].qname()
        for p in m.parameters():
            self.assertIn(p, parameters)

        # First argument not a model
        self.assertRaisesRegex(
            ValueError, 'must be a myokit.Model', hh.HHModel, 1, states)

        # State doesn't exist
        self.assertRaisesRegex(
            hh.HHModelError, 'Unknown state',
            hh.HHModel, model, states + ['bert'], parameters, current)

        # Variable isn't a state
        self.assertRaisesRegex(
            hh.HHModelError, 'not a state',
            hh.HHModel, model, states + ['ina.INa'], parameters, current)

        # State added twice
        self.assertRaisesRegex(
            hh.HHModelError, 'twice',
            hh.HHModel, model, states + ['ina.h'], parameters, current)

        # No parameters is allowed
        hh.HHModel(model, states, None, current)

        # Non-literal parameter
        self.assertRaisesRegex(
            hh.HHModelError, 'Unsuitable',
            hh.HHModel, model, states, parameters + ['ina.INa'], current)

        # Parameter added twice
        self.assertRaisesRegex(
            hh.HHModelError, 'Parameter listed twice',
            hh.HHModel,
            model, states, parameters + ['ina.p1'], current)

        # Unknown parameter
        self.assertRaisesRegex(
            hh.HHModelError, 'Unknown parameter', hh.HHModel,
            model, states, parameters + ['ina.p1000'], current)

        # Current is a state
        self.assertRaisesRegex(
            hh.HHModelError, 'Current variable can not be a state',
            hh.HHModel, model, states, parameters, 'ina.m')

        # Current is not a function of the states
        m2 = model.clone()
        hh.HHModel(m2, states, parameters, current)
        m2.get(current).set_rhs(0)
        self.assertRaisesRegex(
            hh.HHModelError, 'Current must be a function of',
            hh.HHModel, m2, states, parameters, current)

        # Vm not given in model
        m2 = model.clone()
        hh.HHModel(m2, states, parameters, current)
        m2.get('membrane.V').set_label(None)
        self.assertRaisesRegex(
            hh.HHModelError, 'potential must be specified',
            hh.HHModel, m2, states, parameters, current)
        hh.HHModel(m2, states, parameters, current, vm='membrane.V')

        # Vm can't be a parameter
        self.assertRaisesRegex(
            hh.HHModelError, 'list of parameters', hh.HHModel,
            m2, states, parameters, current, vm=parameters[0])

        # Vm can't be a state
        self.assertRaisesRegex(
            hh.HHModelError, 'list of states',
            hh.HHModel, m2, states, parameters, current, vm=states[0])

        # Vm can't be the current
        self.assertRaisesRegex(
            hh.HHModelError, 'be the current',
            hh.HHModel, m2, states, parameters, current, vm=current)

        # States must have inf-tau form or alpha-beta form
        m2 = model.clone()
        m2.get('ina.m').set_rhs('alpha * (1 - m) - beta * m + 2')
        self.assertRaisesRegex(
            hh.HHModelError, 'must have "inf-tau form" or "alpha-beta form"',
            hh.HHModel, m2, states, parameters, current)

        # Current doesn't depend on states
        m2 = model.clone()
        m2.get(current).set_rhs('p1 + 12')
        self.assertRaisesRegex(
            hh.HHModelError, 'urrent must be a function of',
            hh.HHModel, m2, states, parameters, current)

        # Check states corresponds to input
        states[1] = states[1].qname()
        for s in m.states():
            self.assertIn(s, states)

        # Unlisted states are clamped
        v = model.get('ina').add_variable('xyz')
        v.promote(1.23)
        v.set_rhs(10)
        m = hh.HHModel(model, states, parameters, current)
        for s in m.states():
            self.assertIn(s, states)

        # All bindings other than time are removed
        # (e.g. this works without errors)
        i = model.get(current)
        i.set_binding('hello')
        m = hh.HHModel(model, states, parameters, current)

        # Returned reduced model is shorter than input model
        model2 = m.reduced_model()
        self.assertIsInstance(model2, myokit.Model)
        self.assertTrue(len(model2.code()) < len(model.code()))

    def test_automatic_creation(self):
        # Create a HH model from a component.

        # Load model
        fname = os.path.join(DIR_DATA, 'lr-1991-fitting.mmt')
        model = myokit.load_model(fname)

        # Create a current model
        hh.HHModel.from_component(model.get('ina'))

        # Test partially automatic creation
        states = [
            'ina.m',
            model.get('ina.h'),
            'ina.j',
        ]
        hh.HHModel.from_component(model.get('ina'), states=states)

        parameters = [
            'ina.p1',
            model.get('ina.p10'),
            model.get('ina.p20'),
            'ina.p30',
        ]
        hh.HHModel.from_component(
            model.get('ina'), parameters=parameters)

        current = 'ina.INa'
        hh.HHModel.from_component(model.get('ina'), current=current)
        hh.HHModel.from_component(model.get('ina'), current=model.get(current))

        # No current --> This is allowed
        m2 = model.clone()
        m2.get('ina').remove_variable(m2.get('ina.INa'))
        hh.HHModel.from_component(m2.get('ina'))

        # Two currents
        m2 = model.clone()
        v = m2.get('ina').add_variable('INa2')
        v.set_rhs(m2.get('ina.INa').rhs().clone())
        self.assertRaisesRegex(
            hh.HHModelError,
            'more than one variable that could be a current',
            hh.HHModel.from_component, m2.get('ina'))

        # Explict vm
        m2 = model.clone()
        m2.get('membrane.V').set_label(None)
        hh.HHModel.from_component(model.get('ina'), vm='membrane.V')
        self.assertRaisesRegex(
            hh.HHModelError,
            'labeled as "membrane_potential"',
            hh.HHModel.from_component, m2.get('ina'))

    def test_hh_model_steady_state(self):
        # Test the method HHModel.steady_state().

        # Create model
        fname = os.path.join(DIR_DATA, 'lr-1991-fitting.mmt')
        model = myokit.load_model(fname)
        m = hh.HHModel.from_component(model.get('ina'))

        # Get steady state
        ss = np.array(m.steady_state())

        # Check that this is a valid steady state
        self.assertTrue(np.all(ss >= 0))
        self.assertTrue(np.all(ss <= 1))

        # Test if derivatives are zero
        for k, x in enumerate(['ina.m', 'ina.h', 'ina.j']):
            x = model.get(x)
            x.set_state_value(ss[k])
            self.assertAlmostEqual(x.eval(), 0)

        # Test arguments
        m.steady_state(-20, m.default_parameters())
        self.assertRaisesRegex(
            ValueError, 'parameter vector size',
            m.steady_state, -20, [1])

    def test_manual_creation_with_v_independence(self):
        # Test with the v-independent states

        # Load model
        model = myokit.parse_model(MODEL)

        # Select a number of states and parameters
        states = ['binding.act', 'binding.rec', 'binding.b']
        parameters = ['binding.kon', 'binding.koff']

        # Create a HH model
        m = hh.HHModel(model, states, parameters)

        # Also select a current
        current = 'binding.I'
        m = hh.HHModel(model, states, parameters, current)

        # Test steady-state calculation doesn't fail
        m.steady_state(-80)

    def test_automatic_creation_with_v_independence(self):
        # Test with the v-independent states

        model = myokit.parse_model(MODEL)
        m = hh.HHModel.from_component(model.get('binding'))

        self.assertEqual(len(m.states()), 3)


class AnalyticalSimulationTest(unittest.TestCase):
    """
    Tests :class:`myokit.lib.hh.AnalyticalSimulation`.
    """

    def test_create_and_run(self):
        # Test creating and running a simulation

        # Create a simulation
        fname = os.path.join(DIR_DATA, 'lr-1991-fitting.mmt')
        model = myokit.load_model(fname)
        m = hh.HHModel.from_component(model.get('ina'))

        # Bad constructors
        self.assertRaisesRegex(
            ValueError, 'HHModel', hh.AnalyticalSimulation, 1)
        self.assertRaisesRegex(
            ValueError, 'Protocol', hh.AnalyticalSimulation, m, 1)

        # Create properly
        s = hh.AnalyticalSimulation(m)

        # Times to evaluate at
        times = np.linspace(0, 100, 5)

        # Voltages to test at
        voltages = np.arange(-70, 0, 30)

        # Generate traces with "solve" method
        state = s.state()
        dstate = s.default_state()
        for v in voltages:
            s.set_membrane_potential(v)
            x, i = s.solve(times)

        # Solve shouldn't change the state
        self.assertEqual(state, s.state())
        self.assertEqual(dstate, s.default_state())

        # Run for a bit
        self.assertIsInstance(s.run(10), myokit.DataLog)

        # Run can append to log
        d = s.run(10)
        n = len(d['engine.time'])
        e = s.run(1, log=d)
        self.assertIs(d, e)
        self.assertTrue(len(d['engine.time']) > n)

        # Run for zero duration
        d = s.run(0)
        self.assertEqual(len(d.time()), 0)
        d = s.run(0)
        self.assertEqual(len(d.time()), 0)

        # No current variable? Then current can't be calculated
        model2 = model.clone()
        model2.get('ina').remove_variable(model2.get('ina.INa'))
        m2 = hh.HHModel.from_component(model2.get('ina'))
        s2 = hh.AnalyticalSimulation(m2)
        # But simulation still works
        self.assertIsInstance(s2.run(10), myokit.DataLog)
        del model2, m2, s2

        # Create protocol

        # Protocol times: prep, step, post, full
        tprep = 2800
        tstep = 15
        tpost = 0

        # Step voltages
        vhold = -80
        vlo = -140
        vhi = 100
        res = 50
        v = np.arange(vlo, vhi + res, res)
        p = myokit.pacing.steptrain(v, vhold, tprep, tstep, tpost)
        t = p.characteristic_time()

        # Create simulation with protocol (set_protocol is not supported)
        s = hh.AnalyticalSimulation(m, p)

        # Membrane potential and protocol can't be used simultaneously
        self.assertRaisesRegex(
            Exception, 'cannot be set if', s.set_membrane_potential, -80)

        # Pre should change the state and default state
        state = s.state()
        dstate = s.default_state()
        s.pre(tprep + tstep)
        self.assertNotEqual(state, s.state())
        self.assertNotEqual(dstate, s.default_state())
        self.assertRaises(ValueError, s.pre, -1)

        # Run should change the state, not the default state
        state = s.state()
        dstate = s.default_state()
        d = s.run(t)
        self.assertNotEqual(state, s.state())
        self.assertEqual(dstate, s.default_state())
        self.assertRaisesRegex(ValueError, 'Duration', s.run, -1)
        self.assertRaisesRegex(
            ValueError, 'Log interval', s.run, 1, log_interval=-1)
        d['hello'] = [1, 2, 3]
        self.assertRaisesRegex(ValueError, 'extra keys', s.run, 1, log=d)
        del d['hello']
        del d[next(iter(d.keys()))]
        self.assertRaisesRegex(ValueError, 'missing', s.run, 1, log=d)

        # Reset should reset the state
        s.reset()
        self.assertEqual(state, s.state())

        # Run can append to log
        d = s.run(10)
        n = len(d['engine.time'])
        e = s.run(1, log=d)
        self.assertIs(d, e)
        self.assertTrue(len(d['engine.time']) > n)

        # Run for zero duration
        d = s.run(0)
        self.assertEqual(len(d.time()), 0)
        d = s.run(0)
        self.assertEqual(len(d.time()), 0)

    def test_analytical_simulation_properties(self):
        # Test basic get/set methods of analytical simulation.

        # Create a simulation
        fname = os.path.join(DIR_DATA, 'lr-1991-fitting.mmt')
        model = myokit.load_model(fname)
        m = hh.HHModel.from_component(model.get('ina'))
        s = hh.AnalyticalSimulation(m)

        # membrane potential
        self.assertEqual(
            s.membrane_potential(), model.get('membrane.V').eval())
        s.set_membrane_potential(10)
        self.assertEqual(s.membrane_potential(), 10)

        # Parameter values
        p = list(range(len(s.parameters())))
        self.assertNotEqual(p, s.parameters())
        s.set_parameters(p)
        self.assertEqual(p, s.parameters())
        self.assertRaises(ValueError, s.set_parameters, p[:-1])

        # Change parameter with set_constant
        p[3] += 1
        self.assertNotEqual(p, s.parameters())
        s.set_constant(m.parameters()[3], p[3])
        self.assertEqual(p, s.parameters())

        # State
        state = np.zeros(len(s.state()))
        state[0] = 0.3
        state[1] = 0.5
        self.assertNotEqual(list(state), list(s.state()))
        s.set_state(state)
        self.assertEqual(list(state), list(s.state()))
        self.assertRaisesRegex(
            ValueError, 'Wrong size', s.set_state, state[:-1])
        state[0] = -.1
        self.assertRaisesRegex(
            ValueError, 'must be in the range', s.set_state, state)
        state[0] = 0
        state[1] = 1.1
        self.assertRaisesRegex(
            ValueError, 'must be in the range', s.set_state, state)

        # Default state
        dstate = np.zeros(len(s.default_state()))
        dstate[0] = 0.3
        dstate[1] = 0.5
        self.assertNotEqual(list(dstate), list(s.default_state()))
        s.set_default_state(dstate)
        self.assertEqual(list(dstate), list(s.default_state()))
        self.assertRaisesRegex(
            ValueError, 'Wrong size', s.set_default_state, dstate[:-1])
        dstate[0] = -.1
        self.assertRaisesRegex(
            ValueError, 'must be in the range', s.set_default_state, dstate)
        state[0] = 0
        state[1] = 1.1
        self.assertRaisesRegex(
            ValueError, 'must be in the range', s.set_default_state, dstate)

    def test_against_cvode(self):
        # Validate against a cvode sim.

        # Get a model
        fname = os.path.join(DIR_DATA, 'lr-1991-fitting.mmt')
        model = myokit.load_model(fname)
        model.get('membrane.V').set_binding('pace')

        # Create a protocol
        vs = [-30, -20, -10]
        p = myokit.pacing.steptrain(
            vsteps=vs,
            vhold=-120,
            tpre=8,
            tstep=2,
            tpost=0)
        t = p.characteristic_time()

        # Run an analytical simulation
        dt = 0.01
        m = hh.HHModel.from_component(model.get('ina'))
        s1 = hh.AnalyticalSimulation(m, p)
        d1 = s1.run(t, log_interval=dt).npview()

        s2 = myokit.Simulation(model, p)
        s2.set_tolerance(1e-8, 1e-8)
        d2 = s2.run(t, log_interval=dt).npview()

        # Test protocol output is the same
        e = np.abs(d1['membrane.V'] - d2['membrane.V'])
        self.assertEqual(np.max(e), 0)

        # Test current output is very similar
        e = np.abs(d1['ina.INa'] - d2['ina.INa'])
        self.assertLess(np.max(e), 2e-4)

    def test_against_cvode_v_independent(self):

        # Test with v-independent states
        model = myokit.parse_model(MODEL)
        model.get('membrane.V').set_rhs(-80)
        model.get('membrane.V').demote()
        model.binding('pace').set_binding(None)
        model.get('membrane.V').set_binding('pace')

        # Create a protocol
        vs = [-30, -20, -10]
        p = myokit.pacing.steptrain(
            vsteps=vs,
            vhold=-120,
            tpre=8,
            tstep=2,
            tpost=0)
        t = p.characteristic_time()

        # Run an analytical simulation
        dt = 0.01
        m = hh.HHModel.from_component(model.get('binding'))
        s1 = hh.AnalyticalSimulation(m, p)
        d1 = s1.run(t, log_interval=dt).npview()

        s2 = myokit.Simulation(model, p)
        s2.set_tolerance(1e-8, 1e-8)
        d2 = s2.run(t, log_interval=dt).npview()

        # Test protocol output is the same
        e = np.abs(d1['membrane.V'] - d2['membrane.V'])
        self.assertEqual(np.max(e), 0)

        # Test current output is very similar
        e = np.abs(d1['binding.I'] - d2['binding.I'])
        self.assertLess(np.max(e), 2e-4)


if __name__ == '__main__':
    unittest.main()
