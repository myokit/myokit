#!/usr/bin/env python3
#
# Tests the lib.markov module.
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
import myokit.lib.markov as markov

from myokit.tests import DIR_DATA, WarningCollector

# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp


class LinearModelTest(unittest.TestCase):
    """
    Tests the linear model class.
    """

    def test_manual_creation(self):

        # Load model
        fname = os.path.join(DIR_DATA, 'clancy-1999-fitting.mmt')
        model = myokit.load_model(fname)

        # Select a number of states and parameters
        states = [
            'ina.C3',
            'ina.C2',
            'ina.C1',
            'ina.IF',
            'ina.IS',
            model.get('ina.O'),
        ]
        parameters = [
            'ina.p1',
            'ina.p2',
            'ina.p3',
            model.get('ina.p4'),
        ]
        current = 'ina.i'

        # Create a markov model
        m = markov.LinearModel(model, states, parameters, current)
        markov.LinearModel(model, states, parameters, model.get(current))

        # Check membrane potential
        self.assertEqual(m.membrane_potential(), 'membrane.V')

        # Check parameters
        parameters[3] = parameters[3].qname()
        for p in m.parameters():
            self.assertIn(p, parameters)

        # Test deprecated MarkovModel class
        with WarningCollector() as w:
            m2 = markov.MarkovModel(model, states, parameters, current)
        self.assertEqual(type(m2), markov.AnalyticalSimulation)
        self.assertIn('deprecated', w.text())

        # State doesn't exist
        self.assertRaisesRegex(
            markov.LinearModelError, 'Unknown state',
            markov.LinearModel, model, states + ['bert'], parameters, current)

        # State isn't a state
        self.assertRaisesRegex(
            markov.LinearModelError, 'not a state',
            markov.LinearModel, model, states + ['ina.i'], parameters, current)

        # State added twice
        self.assertRaisesRegex(
            markov.LinearModelError, 'twice',
            markov.LinearModel, model, states + ['ina.O'], parameters, current)

        # No parameters is allowed
        markov.LinearModel(model, states, None, current)

        # Non-literal parameter
        self.assertRaisesRegex(
            markov.LinearModelError, 'Unsuitable',
            markov.LinearModel, model, states, parameters + ['ina.i'], current)

        # Parameter added twice
        self.assertRaisesRegex(
            markov.LinearModelError, 'Parameter listed twice',
            markov.LinearModel,
            model, states, parameters + ['ina.p1'], current)

        # Unknown parameter
        self.assertRaisesRegex(
            markov.LinearModelError, 'Unknown parameter', markov.LinearModel,
            model, states, parameters + ['ina.p1000'], current)

        # Current is a state
        self.assertRaisesRegex(
            markov.LinearModelError, 'Current variable can not be a state',
            markov.LinearModel, model, states, parameters, 'ina.O')

        # Current is not a function of the states
        m2 = model.clone()
        markov.LinearModel(m2, states, parameters, current)
        m2.get(current).set_rhs(0)
        self.assertRaisesRegex(
            markov.LinearModelError, 'Current must be a function of',
            markov.LinearModel, m2, states, parameters, current)

        # Vm not given in model
        m2 = model.clone()
        markov.LinearModel(m2, states, parameters, current)
        m2.get('membrane.V').set_label(None)
        self.assertRaisesRegex(
            markov.LinearModelError, 'potential must be specified',
            markov.LinearModel, m2, states, parameters, current)
        markov.LinearModel(m2, states, parameters, current, vm='membrane.V')

        # Vm is a parameter
        self.assertRaisesRegex(
            markov.LinearModelError, 'list of parameters', markov.LinearModel,
            m2, states, parameters, current, vm=parameters[0])

        # Vm is a state
        self.assertRaisesRegex(
            markov.LinearModelError, 'list of states',
            markov.LinearModel, m2, states, parameters, current, vm=states[0])

        # Vm is the current
        self.assertRaisesRegex(
            markov.LinearModelError, 'be the current',
            markov.LinearModel, m2, states, parameters, current, vm=current)

        # States must have bidrectional dependencies
        m2 = model.clone()
        # Set bad config, but with columns still summing to zero
        m2.get('ina.C3').set_rhs('ina.C1')
        x = m2.get('ina.C2')
        x.set_rhs(str(x.rhs()) + '+ a12 * C2 + - b12 * C1')
        x = m2.get('ina.C1')
        x.set_rhs(str(x.rhs()) + ' - ina.C1')
        self.assertRaisesRegex(
            markov.LinearModelError, 'not vice versa',
            markov.LinearModel, m2, states, parameters, current)

        # States must sum to 1
        m2 = model.clone()
        m2.get(states[0]).set_state_value(0.6)
        m2.get(states[1]).set_state_value(0.6)
        self.assertRaisesRegex(
            markov.LinearModelError, 'sum of states',
            markov.LinearModel, m2, states, parameters, current)

        # Derivatives per column don't sum to zero
        m2 = model.clone()
        x = m2.get(states[0])
        x.set_rhs('2 * ' + str(x.rhs()))
        self.assertRaisesRegex(
            markov.LinearModelError, 'sum to non-zero',
            markov.LinearModel, m2, states, parameters, current)

        # Not a linear model
        m2 = model.clone()
        x = m2.get(states[0])
        y = m2.get(states[1])
        # Set rhs to something non-linear, make sure columns still sum to 0
        x.set_rhs(str(x.rhs()) + ' + C1^2')
        y.set_rhs(str(y.rhs()) + ' - C1^2')
        self.assertRaisesRegex(
            markov.LinearModelError, 'linear combination of states',
            markov.LinearModel, m2, states, parameters, current)

        # Current not a linear combination of states
        m2 = model.clone()
        m2.get(current).set_rhs('sqrt(ina.O)')
        self.assertRaisesRegex(
            markov.LinearModelError, 'linear combination of states',
            markov.LinearModel, m2, states, parameters, current)

    def test_linear_model_from_component(self):

        # Load model
        fname = os.path.join(DIR_DATA, 'clancy-1999-fitting.mmt')
        model = myokit.load_model(fname)

        # Create a markov model
        markov.LinearModel.from_component(model.get('ina'))

        # Test deprecated MarkovModel class
        with WarningCollector() as w:
            m = markov.MarkovModel.from_component(model.get('ina'))
        self.assertEqual(type(m), markov.AnalyticalSimulation)
        self.assertIn('deprecated', w.text())

        # Test partially automatic creation
        states = [
            'ina.C3',
            'ina.C2',
            'ina.C1',
            'ina.IF',
            'ina.IS',
            model.get('ina.O'),
        ]
        markov.LinearModel.from_component(model.get('ina'), states=states)

        parameters = [
            'ina.p1',
            'ina.p2',
            'ina.p3',
            model.get('ina.p4',)
        ]
        markov.LinearModel.from_component(
            model.get('ina'), parameters=parameters)

        current = 'ina.i'
        markov.LinearModel.from_component(model.get('ina'), current=current)

        markov.LinearModel.from_component(
            model.get('ina'), current=model.get(current))

        # No current --> This is allowed
        m2 = model.clone()
        m2.get('ina').remove_variable(m2.get('ina.i'))
        m = markov.LinearModel.from_component(m2.get('ina'))

        # Two currents
        m2 = model.clone()
        v = m2.get('ina').add_variable('i2')
        v.set_rhs(m2.get('ina.i').rhs().clone())
        self.assertRaisesRegex(
            markov.LinearModelError,
            'more than one variable that could be a current',
            markov.LinearModel.from_component, m2.get('ina'))

        # Explict vm
        m2 = model.clone()
        m2.get('membrane.V').set_label(None)
        markov.LinearModel.from_component(model.get('ina'), vm='membrane.V')
        self.assertRaisesRegex(
            markov.LinearModelError,
            'labeled as "membrane_potential"',
            markov.LinearModel.from_component, m2.get('ina'))

    def test_linear_model_matrices(self):

        # Create model
        fname = os.path.join(DIR_DATA, 'clancy-1999-fitting.mmt')
        model = myokit.load_model(fname)
        m = markov.LinearModel.from_component(model.get('ina'))

        # Test shape of output
        A, B = m.matrices(-20, range(21))
        self.assertEqual(A.shape, (6, 6))
        self.assertEqual(B.shape, (6, ))

        # Requires 21 parameters
        self.assertRaises(ValueError, m.matrices, -20, range(3))

    def test_linear_model_steady_state_1(self):
        # Test finding the steady-state of the Clancy model

        # Create model
        filename = os.path.join(DIR_DATA, 'clancy-1999-fitting.mmt')
        model = myokit.load_model(filename)
        m = markov.LinearModel.from_component(model.get('ina'))

        # Get steady state
        ss = np.array(m.steady_state())

        # Check that this is a valid steady state
        self.assertTrue(np.all(ss >= 0))
        self.assertTrue(np.all(ss <= 1))

        # Check that derivatives with ss are close to zero
        ss = list(ss)
        model.set_state(ss + ss)    # Model has 2 ina's
        derivs = model.evaluate_derivatives()
        for i in range(len(ss)):
            self.assertAlmostEqual(0, derivs[i])

        # Try with awful parameters
        self.assertRaisesRegex(
            markov.LinearModelError, 'positive eigenvalues',
            m.steady_state, parameters=[-1] * 21)

    def test_linear_model_steady_state_2(self):
        # Test finding the steady-state of one of Dominic's models, which
        # exposed a bug in the steady state code

        # Create model
        filename = os.path.join(DIR_DATA, 'dom-markov.mmt')
        model = myokit.load_model(filename)
        m = markov.LinearModel.from_component(model.get('ikr'))

        # Get steady state
        ss = np.array(m.steady_state())

        # Check that this is a valid steady state
        self.assertTrue(np.all(ss >= 0))
        self.assertTrue(np.all(ss <= 1))

        # Check that derivatives with ss are close to zero
        model.set_state(ss)
        derivs = model.evaluate_derivatives()
        for i in range(len(ss)):
            self.assertAlmostEqual(0, derivs[i])

    def test_rates(self):

        # Load model
        fname = os.path.join(DIR_DATA, 'clancy-1999-fitting.mmt')
        model = myokit.load_model(fname)

        # Create a markov model
        m = markov.LinearModel.from_component(model.get('ina'))

        # Test rates method runs
        self.assertEqual(len(m.rates()), 12)
        m.rates(parameters=[0.01] * 21)
        self.assertRaisesRegex(
            ValueError, 'Illegal parameter vector size',
            m.rates, parameters=[0.01] * 22)


class AnalyticalSimulationTest(unittest.TestCase):
    """
    Tests :class:`myokit.lib.markov.AnalyticalSimulation`.
    """

    def test_create_and_run(self):
        # Test basics of analytical simulation

        # Create a simulation
        fname = os.path.join(DIR_DATA, 'clancy-1999-fitting.mmt')
        model = myokit.load_model(fname)
        m = markov.LinearModel.from_component(model.get('ina'))

        # Bad constructors
        self.assertRaisesRegex(
            ValueError, 'LinearModel', markov.AnalyticalSimulation, 1)
        self.assertRaisesRegex(
            ValueError, 'Protocol', markov.AnalyticalSimulation, m, 1)

        # Create properly
        s = markov.AnalyticalSimulation(m)

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

        # Calculate current for a particular state
        self.assertIsInstance(s.current(s.state()), float)

        # No current variable? Then current can't be calculated
        model2 = model.clone()
        model2.get('ina').remove_variable(model2.get('ina.i'))
        m2 = markov.LinearModel.from_component(model2.get('ina'))
        s2 = markov.AnalyticalSimulation(m2)
        self.assertRaisesRegex(
            Exception, 'did not specify a current', s2.current, s2.state())
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
        s = markov.AnalyticalSimulation(m, p)

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

    def test_analytical_simulation_properties(self):
        # Test basic get/set methods of analytical simulation.

        # Create a simulation
        fname = os.path.join(DIR_DATA, 'clancy-1999-fitting.mmt')
        model = myokit.load_model(fname)
        m = markov.LinearModel.from_component(model.get('ina'))
        s = markov.AnalyticalSimulation(m)

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
        state[0] = 0.5
        state[1] = 0.5
        self.assertNotEqual(list(state), list(s.state()))
        s.set_state(state)
        self.assertEqual(list(state), list(s.state()))
        self.assertRaisesRegex(
            ValueError, 'Wrong size', s.set_state, state[:-1])
        state[0] += 0.1
        self.assertRaisesRegex(
            ValueError, 'sum to 1', s.set_state, state)
        state[0] = -.1
        state[1] = 1.1
        self.assertRaisesRegex(
            ValueError, 'negative', s.set_state, state)

        # Default state
        dstate = np.zeros(len(s.default_state()))
        dstate[0] = 0.5
        dstate[1] = 0.5
        self.assertNotEqual(list(dstate), list(s.default_state()))
        s.set_default_state(dstate)
        self.assertEqual(list(dstate), list(s.default_state()))
        self.assertRaisesRegex(
            ValueError, 'Wrong size', s.set_default_state, dstate[:-1])
        dstate[0] += 0.1
        self.assertRaisesRegex(
            ValueError, 'sum to 1', s.set_default_state, dstate)
        dstate[0] = -.1
        dstate[1] = 1.1
        self.assertRaisesRegex(
            ValueError, 'negative', s.set_default_state, dstate)

    def test_against_cvode(self):
        # Validate against a cvode sim.

        # Get a model
        fname = os.path.join(DIR_DATA, 'clancy-1999-fitting.mmt')
        model = myokit.load_model(fname)

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
        m = markov.LinearModel.from_component(model.get('ina'))
        s1 = markov.AnalyticalSimulation(m, p)
        d1 = s1.run(t, log_interval=dt).npview()

        s2 = myokit.Simulation(model, p)
        s2.set_tolerance(1e-8, 1e-8)
        d2 = s2.run(t, log_interval=dt).npview()

        # Test protocol output is the same
        e = np.abs(d1['membrane.V'] - d2['membrane.V'])
        if False:
            import matplotlib.pyplot as plt
            plt.figure()
            plt.plot(d1['membrane.V'])
            plt.plot(d2['membrane.V'])
            plt.show()
        self.assertEqual(np.max(e), 0)

        # Test current output is very similar
        e = np.abs(d1['ina.i'] - d2['ina.i'])
        if False:
            import matplotlib.pyplot as plt
            plt.figure()
            plt.plot(d1['ina.i'])
            plt.plot(d2['ina.i'])
            plt.figure()
            plt.plot(d1['ina.i'] - d2['ina.i'])
            plt.show()
        self.assertLess(np.max(e), 2e-4)


class DiscreteSimulationTest(unittest.TestCase):
    """
    Tests :class:`myokit.lib.markov.DiscreteSimulationTest`.
    """

    def test_basics(self):
        # Test the DiscreteSimulation class, running, resetting etc..

        # Create a simulation
        fname = os.path.join(DIR_DATA, 'clancy-1999-fitting.mmt')
        model = myokit.load_model(fname)
        m = markov.LinearModel.from_component(model.get('ina'))

        # Bad constructors
        self.assertRaisesRegex(
            ValueError, 'LinearModel', markov.DiscreteSimulation, 1)
        self.assertRaisesRegex(
            ValueError, 'Protocol', markov.DiscreteSimulation, m, 1)
        self.assertRaisesRegex(
            ValueError, 'at least 1',
            markov.DiscreteSimulation, m, nchannels=0)

        # Test running without a protocol
        s = markov.DiscreteSimulation(m)
        s.run(1)

        # Rest running for a very short time doesn't cause crash
        s.run(0)

        # Create protocol

        # Protocol times: prep, step, post, full
        tprep = 10
        tstep = 150
        tpost = 0

        # Step voltages
        vhold = -80
        vlo = -140
        vhi = 100
        res = 50
        v = np.arange(vlo, vhi + res, res)
        p = myokit.pacing.steptrain(v, vhold, tprep, tstep, tpost)

        # Create simulation with protocol (set_protocol is not supported)
        np.random.seed(1)
        s = markov.DiscreteSimulation(m, p)

        # Membrane potential and protocol can't be used simultaneously
        self.assertRaisesRegex(
            Exception, 'cannot be set if', s.set_membrane_potential, -80)

        # Pre should change the state and default state
        state = s.state()
        dstate = s.default_state()
        s.pre(tprep + tstep)
        self.assertNotEqual(state, s.state())
        self.assertNotEqual(dstate, s.default_state())
        self.assertRaisesRegex(ValueError, 'negative', s.pre, -1)

        # Run should change the state, not the default state
        state = s.state()
        dstate = s.default_state()
        d = s.run(15)
        self.assertNotEqual(state, s.state())
        self.assertEqual(dstate, s.default_state())
        self.assertRaisesRegex(ValueError, 'negative', s.run, -1)

        # Reset should reset the state
        s.reset()
        self.assertEqual(state, s.state())

        # Run can append to log
        n = len(d['engine.time'])
        e = s.run(1, log=d)
        self.assertIs(d, e)
        self.assertTrue(len(d['engine.time']) > n)
        self.assertEqual(len(d['engine.time']), len(d['membrane.V']))
        self.assertEqual(len(d['engine.time']), len(d['ina.i']))
        self.assertEqual(len(d['engine.time']), len(d['ina.O']))
        d2 = d.clone()
        del d2[next(iter(d2.keys()))]
        self.assertRaisesRegex(ValueError, 'missing', s.run, 1, log=d2)
        d2 = d.clone()
        d2['hello'] = [1, 2, 3]
        self.assertRaisesRegex(ValueError, 'extra', s.run, 1, log=d2)

        #
        # Test without current variable
        #
        model.get('ina').remove_variable(model.get('ina.i'))
        m = markov.LinearModel.from_component(model.get('ina'))

        # Create simulation with protocol (set_protocol is not supported)
        np.random.seed(1)
        s = markov.DiscreteSimulation(m, p)
        d = s.run(10)
        n = len(d['engine.time'])
        e = s.run(1, log=d)
        self.assertIs(d, e)
        self.assertTrue(len(d['engine.time']) > n)
        self.assertEqual(len(d['engine.time']), len(d['membrane.V']))
        self.assertEqual(len(d['engine.time']), len(d['ina.O']))
        self.assertNotIn('ina.i', d)
        d2 = d.clone()
        del d2[next(iter(d2.keys()))]
        self.assertRaisesRegex(ValueError, 'missing', s.run, 1, log=d2)
        d2 = d.clone()
        d2['hello'] = [1, 2, 3]
        self.assertRaisesRegex(ValueError, 'extra', s.run, 1, log=d2)

    def test_discrete_simulation_properties(self):
        # Test basic get/set methods of discrete simulation.

        # Create a simulation
        fname = os.path.join(DIR_DATA, 'clancy-1999-fitting.mmt')
        model = myokit.load_model(fname)
        m = markov.LinearModel.from_component(model.get('ina'))
        s = markov.DiscreteSimulation(m, nchannels=50)

        # membrane potential
        self.assertEqual(
            s.membrane_potential(), model.get('membrane.V').eval())
        s.set_membrane_potential(10)
        self.assertEqual(s.membrane_potential(), 10)

        # Number of channels
        self.assertEqual(s.number_of_channels(), 50)

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
        state[0] = 25
        state[1] = 25
        self.assertNotEqual(list(state), list(s.state()))
        s.set_state(state)
        self.assertEqual(list(state), list(s.state()))
        self.assertRaisesRegex(
            ValueError, 'Wrong size', s.set_state, state[:-1])
        state[0] += 1
        self.assertRaisesRegex(
            ValueError, 'must equal', s.set_state, state)
        state[0] = -1
        state[1] = 51
        self.assertRaisesRegex(
            ValueError, 'negative', s.set_state, state)

        # Default state
        dstate = np.zeros(len(s.default_state()))
        dstate[0] = 25
        dstate[1] = 25
        self.assertNotEqual(list(dstate), list(s.default_state()))
        s.set_default_state(dstate)
        self.assertEqual(list(dstate), list(s.default_state()))
        self.assertRaisesRegex(
            ValueError, 'Wrong size', s.set_default_state, dstate[:-1])
        dstate[0] += 1
        self.assertRaisesRegex(
            ValueError, 'must equal', s.set_default_state, dstate)
        dstate[0] = -1
        dstate[1] = 51
        self.assertRaisesRegex(
            ValueError, 'negative', s.set_default_state, dstate)

        # Discretize state
        self.assertEqual(s.discretize_state([0.4, 0.6]), [20, 30])
        self.assertRaisesRegex(
            ValueError, 'must equal 1', s.discretize_state, [0.5, 0.6])


class MarkovFunctionsTest(unittest.TestCase):
    """
    Test cases for finding Markov models.
    """

    def test_convert_markov_models_to_compact_form(self):
        # Tests convert_markov_models_to_compact_form()

        # Load clancy model, has two versions of same markov model in it
        fname = os.path.join(DIR_DATA, 'clancy-1999-fitting.mmt')
        model1 = myokit.load_model(fname)

        models = markov.find_markov_models(model1)
        self.assertEqual(len(models), 2)
        m1, m2 = models

        # Check both models are full ODE form
        n1 = sum([1 for x in m1 if x.is_state()])
        self.assertEqual(n1, len(m1))
        n2 = sum([1 for x in m2 if x.is_state()])
        self.assertEqual(n2, len(m2))

        # Convert both compact form
        model2 = markov.convert_markov_models_to_compact_form(model1)
        models = markov.find_markov_models(model2)
        self.assertEqual(len(models), 2)
        m1, m2 = models
        n1 = sum([1 for x in m1 if x.is_state()])
        self.assertEqual(n1, len(m1) - 1)
        n2 = sum([1 for x in m2 if x.is_state()])
        self.assertEqual(n2, len(m2) - 1)

        # Check states evaluate to the same value
        self.assertEqual(
            model1.get('ina.C1').eval(), model2.get('ina.C1').eval())
        self.assertEqual(
            model1.get('ina.C2').eval(), model2.get('ina.C2').eval())
        self.assertEqual(
            model1.get('ina.C3').eval(), model2.get('ina.C3').eval())
        self.assertEqual(
            model1.get('ina.IF').eval(), model2.get('ina.IF').eval())
        self.assertEqual(
            model1.get('ina.IS').eval(), model2.get('ina.IS').eval())
        self.assertEqual(
            model1.get('ina.O').eval(), model2.get('ina.O').eval())

        # Doing it twice should have no effect
        model3 = markov.convert_markov_models_to_compact_form(model2)
        self.assertEqual(model2.code(), model3.code())

    def test_convert_markov_models_to_full_ode_form(self):
        # Tests convert_markov_models_to_compact_form()

        # Load clancy model, has two versions of same markov model in it
        fname = os.path.join(DIR_DATA, 'clancy-1999-fitting.mmt')
        model1 = myokit.load_model(fname)

        # Convert to compact form, and check that it worked
        model1 = markov.convert_markov_models_to_compact_form(model1)
        m1, m2 = markov.find_markov_models(model1)
        n1 = sum([1 for x in m1 if x.is_state()])
        self.assertEqual(n1, len(m1) - 1)
        n2 = sum([1 for x in m2 if x.is_state()])
        self.assertEqual(n2, len(m2) - 1)

        # Now convert to full form
        model2 = markov.convert_markov_models_to_full_ode_form(model1)
        m1, m2 = markov.find_markov_models(model2)
        n1 = sum([1 for x in m1 if x.is_state()])
        self.assertEqual(n1, len(m1))
        n2 = sum([1 for x in m2 if x.is_state()])
        self.assertEqual(n2, len(m2))

        # Check states evaluate to the same value
        self.assertEqual(
            model1.get('ina.C1').eval(), model2.get('ina.C1').eval())
        self.assertEqual(
            model1.get('ina.C2').eval(), model2.get('ina.C2').eval())
        self.assertEqual(
            model1.get('ina.C3').eval(), model2.get('ina.C3').eval())
        self.assertEqual(
            model1.get('ina.IF').eval(), model2.get('ina.IF').eval())
        self.assertEqual(
            model1.get('ina.IS').eval(), model2.get('ina.IS').eval())
        self.assertEqual(
            model1.get('ina.O').eval(), model2.get('ina.O').eval())

        # Doing it twice should have no effect
        model3 = markov.convert_markov_models_to_full_ode_form(model2)
        self.assertEqual(model2.code(), model3.code())

    def test_find_markov_models(self):
        # Tests find_markov_models()

        # Load clancy model, has two versions of same markov model in it
        fname = os.path.join(DIR_DATA, 'clancy-1999-fitting.mmt')
        model = myokit.load_model(fname)

        models = markov.find_markov_models(model)
        self.assertEqual(len(models), 2)

        # Check states and ordering
        m1, m2 = models
        self.assertEqual([v.qname() for v in m1], [
            'ina.C1', 'ina.C2', 'ina.C3', 'ina.IF', 'ina.IS', 'ina.O'])
        self.assertEqual([v.qname() for v in m2], [
            'ina_ref.C1', 'ina_ref.C2', 'ina_ref.C3', 'ina_ref.IF',
            'ina_ref.IS', 'ina_ref.O'])
        del models, m1, m2

        # Try with `1 - sum(xi)` state
        c = model.get('ina_ref')
        v = c.get('C3')
        v.demote()
        v.set_rhs('1 - C1 - C2 - IF - IS - O')
        models = markov.find_markov_models(model)
        self.assertEqual(len(models), 2)
        m1, m2 = models
        self.assertEqual([v.qname() for v in m2], [
            'ina_ref.C1', 'ina_ref.C2', 'ina_ref.C3', 'ina_ref.IF',
            'ina_ref.IS', 'ina_ref.O'])
        del models, m1, m2

        # Try with `1 - sum(xi)` state, with a funny RHS
        c = model.get('ina_ref')
        v = c.get('C3')
        v.set_rhs('-(+IF + C1 -(-IS - C2)) + 1 - O')
        models = markov.find_markov_models(model)
        self.assertEqual(len(models), 2)
        m1, m2 = models
        self.assertEqual([v.qname() for v in m2], [
            'ina_ref.C1', 'ina_ref.C2', 'ina_ref.C3', 'ina_ref.IF',
            'ina_ref.IS', 'ina_ref.O'])

    def test_find_markov_models_bad(self):
        # Tests find_markov_models() for non-markov models

        # Load clancy model, has two versions of same markov model in it
        fname = os.path.join(DIR_DATA, 'clancy-1999-fitting.mmt')
        moodel = myokit.load_model(fname)

        # Remove ina_ref component
        c = moodel.get('ina_ref')
        for v in c.variables(deep=True):
            v.set_rhs(0)
        for v in list(c.variables(deep=True)):
            c.remove_variable(v, recursive=True)

        # Only one markov model left at this point
        self.assertEqual(len(markov.find_markov_models(moodel)), 1)

        # Check searching states that no-one refers to
        # (And for cases where not each state is a linear combo)
        m = moodel.clone()
        for v in list(m.get('ina.C1').refs_by(True)):
            v.set_rhs(3)
        self.assertEqual(len(markov.find_markov_models(m)), 0)

        # Test with one 1-minus state
        m = moodel.clone()
        v = m.get('ina.C3')
        v.demote()
        v.set_rhs('1 - C1 - C2 - IF - IS - O')
        self.assertEqual(len(markov.find_markov_models(m)), 1)

        # Test without a 1
        v.set_rhs('2 - C1 - C2 - IF - IS - O')
        self.assertEqual(len(markov.find_markov_models(m)), 0)
        v.set_rhs('-C1 - C2 - IF - IS - O')
        self.assertEqual(len(markov.find_markov_models(m)), 0)

        # Test 1-... contains non-linear terms
        v.set_rhs('1 - C1 - C2 - IF - IS - O - O^2')
        self.assertEqual(len(markov.find_markov_models(m)), 0)

        # Test 1-... contains terms with a factor other than -1
        v.set_rhs('1 - C1 - C2 - IF - IS - O - O')
        self.assertEqual(len(markov.find_markov_models(m)), 0)

        # Test if there's multiple variables with a 1-... RHS
        m = moodel.clone()
        v = m.get('ina.C3')
        v.demote()
        v.set_rhs('1 - C1 - C2 - IF - IS - O')
        self.assertEqual(len(markov.find_markov_models(m)), 1)
        v = m.get('ina').add_variable('C4')
        v.set_rhs('1 - C1 - C2 - IF - IS - O')
        self.assertEqual(len(markov.find_markov_models(m)), 0)

        # But having an extra variable is fine, if the rest checks out!
        m = moodel.clone()
        v = m.get('ina').add_variable('C4')
        v.set_rhs('1 - C1 - C2 - C3 - IF - IS - O')
        self.assertEqual(len(markov.find_markov_models(m)), 1)

        # Must have at least two states
        m = myokit.Model()
        c = m.add_component('c')
        t = c.add_variable('time')
        t.set_binding('time')
        v = c.add_variable('v')
        v.promote(0.1)
        self.assertEqual(len(markov.find_markov_models(m)), 0)

    def test_linear_combination(self):
        # Tests _linear_combination()

        # Load model, to create interesting RHS
        fname = os.path.join(DIR_DATA, 'clancy-1999-fitting.mmt')
        model = myokit.load_model(fname)
        v1 = model.get('ina.C1')
        v2 = model.get('ina.C2')
        v3 = model.get('ina.C3')
        v4 = model.get('ina.IF')
        v5 = model.get('ina.IS')
        v6 = model.get('ina.O')

        # Test C1 rhs
        f = markov._linear_combination(v1.rhs(), [v1, v2, v3, v4, v5, v6])
        self.assertEqual(f[0].code(), '-(ina.a13 + ina.b12 + ina.b3)')
        self.assertEqual(f[1].code(), 'ina.a12')
        self.assertIsNone(f[2])
        self.assertEqual(f[3].code(), 'ina.a3')
        self.assertIsNone(f[4])
        self.assertEqual(f[5].code(), 'ina.b13')

        # Test double appearances
        v1.set_rhs('2 * C1 - 3 * C1 + C1 * sqrt(O) + C2 * IF')
        f = markov._linear_combination(v1.rhs(), [v1, v2, v3])
        self.assertEqual(f[0].code(), '2 + -3 + sqrt(ina.O)')
        self.assertEqual(f[1].code(), 'ina.IF')
        self.assertIsNone(f[2])

    def test_split_factor(self):
        # Tests _split_factor

        # Load model, to create interesting RHS
        fname = os.path.join(DIR_DATA, 'clancy-1999-fitting.mmt')
        model = myokit.load_model(fname)
        v1 = model.get('ina.C1')
        v2 = model.get('ina.C2')
        v3 = model.get('ina.C3')
        v4 = model.get('ina.IF')

        # Test simplest cases
        v4.set_rhs('C1')
        self.assertEqual(
            markov._split_factor(v4.rhs(), [v1]),
            (myokit.Name(v1), myokit.Number(1)))
        v4.set_rhs('+++C1')
        self.assertEqual(
            markov._split_factor(v4.rhs(), [v1]),
            (myokit.Name(v1), myokit.Number(1)))
        v4.set_rhs('--C1')
        self.assertEqual(
            markov._split_factor(v4.rhs(), [v1]),
            (myokit.Name(v1), myokit.Number(1)))
        v4.set_rhs('---C1')
        self.assertEqual(
            markov._split_factor(v4.rhs(), [v1]),
            (myokit.Name(v1), myokit.PrefixMinus(myokit.Number(1))))

        # Test multiplication
        v4.set_rhs('C1 * 3')
        self.assertEqual(
            markov._split_factor(v4.rhs(), [v1]),
            (myokit.Name(v1), myokit.Number(3)))
        v4.set_rhs('C1 * (sqrt(C2) + C3)')
        self.assertEqual(
            markov._split_factor(v4.rhs(), [v1]),
            (myokit.Name(v1),
             myokit.Plus(myokit.Sqrt(myokit.Name(v2)), myokit.Name(v3))))

        # Test division
        v4.set_rhs('C1 / (sqrt(C2) + C3)')
        self.assertEqual(
            markov._split_factor(v4.rhs(), [v1]),
            (myokit.Name(v1),
             myokit.Divide(
                myokit.Number(1),
                myokit.Plus(myokit.Sqrt(myokit.Name(v2)), myokit.Name(v3)))))

        # Test division that's not allowed
        v4.set_rhs('(sqrt(C2) + C3) / C1')
        self.assertRaisesRegex(
            ValueError, r'Non-linear function \(division\)',
            markov._split_factor, v4.rhs(), [v1])

        # Test with list of variables
        v4.set_rhs('C2 * 3')
        self.assertEqual(
            markov._split_factor(v4.rhs(), [v1, v2, v3]),
            (myokit.Name(v2), myokit.Number(3)))

        # Multiple variables is not allowed
        v4.set_rhs('C2 * C1')
        self.assertRaisesRegex(
            ValueError, 'must reference exactly one variable',
            markov._split_factor, v4.rhs(), [v1, v2, v3])

        # Zero variables is not allowed
        v4.set_rhs('C3')
        self.assertRaisesRegex(
            ValueError, 'must reference exactly one variable',
            markov._split_factor, v4.rhs(), [v1, v2])

        # Non-linear term is not allowed
        v4.set_rhs('sqrt(C1)')
        self.assertRaisesRegex(
            ValueError, 'Non-linear function',
            markov._split_factor, v4.rhs(), [v1, v2])

        # Multiple terms is not allowed
        v4.set_rhs('C2 - C2')
        self.assertRaisesRegex(
            ValueError, 'must be a single term',
            markov._split_factor, v4.rhs(), [v1, v2, v3])

    def test_split_terms(self):
        # Tests _split_terms

        # Load model, get rhs with lots of terms
        fname = os.path.join(DIR_DATA, 'clancy-1999-fitting.mmt')
        model = myokit.load_model(fname)

        # Simple case
        v1 = model.get('ina.C1')
        v2 = model.get('ina.C2')
        v3 = model.get('ina.C3')
        v4 = model.get('ina.IF')
        v5 = model.get('ina.IS')
        v6 = model.get('ina.O')
        v3.set_rhs('1 - C1 - C2 - IF - IS - O')
        terms = markov._split_terms(v3.rhs())
        self.assertEqual(terms[0], myokit.Number(1))
        self.assertEqual(terms[1], myokit.PrefixMinus(myokit.Name(v1)))
        self.assertEqual(terms[2], myokit.PrefixMinus(myokit.Name(v2)))
        self.assertEqual(terms[3], myokit.PrefixMinus(myokit.Name(v4)))
        self.assertEqual(terms[4], myokit.PrefixMinus(myokit.Name(v5)))
        self.assertEqual(terms[5], myokit.PrefixMinus(myokit.Name(v6)))
        del terms

        # Case with brackets
        v3.set_rhs('-(+(IF) + C1 -(-IS - C2)) + 1 - O')
        terms = markov._split_terms(v3.rhs())
        self.assertEqual(terms[0], myokit.PrefixMinus(myokit.Name(v4)))
        self.assertEqual(terms[1], myokit.PrefixMinus(myokit.Name(v1)))
        self.assertEqual(terms[2], myokit.PrefixMinus(myokit.Name(v5)))
        self.assertEqual(terms[3], myokit.PrefixMinus(myokit.Name(v2)))
        self.assertEqual(terms[4], myokit.Number(1))
        self.assertEqual(terms[5], myokit.PrefixMinus(myokit.Name(v6)))

        # Empty case
        v3.set_rhs('1 * C1 * C2')
        terms = markov._split_terms(v3.rhs())
        self.assertEqual(len(terms), 1)
        self.assertEqual(terms[0], v3.rhs())


if __name__ == '__main__':
    unittest.main()
