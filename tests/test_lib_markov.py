#!/usr/bin/env python
#
# Tests the lib.makov module.
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
import myokit.lib.markov as markov

from shared import DIR_DATA

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
        """ Manually create a linear model """

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
        m2 = markov.MarkovModel(model, states, parameters, current)
        self.assertEqual(type(m2), markov.AnalyticalSimulation)

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
            markov.LinearModelError, 'not Multiply or Name',
            markov.LinearModel, m2, states, parameters, current)

        # Not a linear model
        m2 = model.clone()
        markov.LinearModel(m2, states, parameters, current)
        x = m2.get(states[0])
        y = m2.get(states[1])
        x.set_rhs('V')
        self.assertRaisesRegex(
            markov.LinearModelError, 'without state dependency',
            markov.LinearModel, m2, states, parameters, current)

        # Not a linear model
        m2 = model.clone()
        markov.LinearModel(m2, states, parameters, current)
        x = m2.get(states[0])
        y = m2.get(states[1])
        x.set_rhs(states[0] + ' * ' + states[1])
        self.assertRaisesRegex(
            markov.LinearModelError, 'multiple state dependencies',
            markov.LinearModel, m2, states, parameters, current)

        # Current not a linear combination of states
        m2 = model.clone()
        m2.get(current).set_rhs('sqrt(ina.O)')
        self.assertRaisesRegex(
            markov.LinearModelError, 'not Multiply or Name',
            markov.LinearModel, m2, states, parameters, current)

        # Current not a linear combination of states
        m2 = model.clone()
        x = m2.get(current)
        x.set_rhs(states[0] + ' * ' + states[1])
        self.assertRaisesRegex(
            markov.LinearModelError, 'multiple state dependencies',
            markov.LinearModel, m2, states, parameters, current)

        # Current not a linear combination of states
        m2 = model.clone()
        x = m2.get(current)
        x.set_rhs(str(x.rhs()) + ' + V')
        self.assertRaisesRegex(
            markov.LinearModelError, 'without state dependency',
            markov.LinearModel, m2, states, parameters, current)

    def test_automatic_creation(self):
        """ Create a linear model from a component. """

        # Load model
        fname = os.path.join(DIR_DATA, 'clancy-1999-fitting.mmt')
        model = myokit.load_model(fname)

        # Create a markov model
        markov.LinearModel.from_component(model.get('ina'))

        # Test deprecated MarkovModel class
        m = markov.MarkovModel.from_component(model.get('ina'))
        self.assertEqual(type(m), markov.AnalyticalSimulation)

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
        """
        Tests the LinearModel.matrices() method.
        """

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

    def test_linear_model_steady_state(self):
        """ Tests the method LinearModel.steady_state(). """

        # Create model
        fname = os.path.join(DIR_DATA, 'clancy-1999-fitting.mmt')
        model = myokit.load_model(fname)
        m = markov.LinearModel.from_component(model.get('ina'))

        ss = list(m.steady_state())
        model.set_state(ss + ss)    # Model has 2 ina's
        derivs = model.eval_state_derivatives()
        for i in range(len(ss)):
            self.assertAlmostEqual(0, derivs[i])

        # Try with awful parameters
        self.assertRaisesRegex(
            markov.LinearModelError, 'positive eigenvalues',
            m.steady_state, parameters=[-1] * 21)

    def test_rates(self):
        """ Create a linear model from a component. """

        # Load model
        fname = os.path.join(DIR_DATA, 'clancy-1999-fitting.mmt')
        model = myokit.load_model(fname)

        # Create a markov model
        m = markov.LinearModel.from_component(model.get('ina'))

        # Test rates method
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
        """ Test basics """

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
        del(model2, m2, s2)

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
        del(d['hello'])
        del(d[next(iter(d.keys()))])
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
        """
        Tests basic get/set methods of analytical simulation.
        """
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
        p = range(len(s.parameters()))
        self.assertNotEqual(p, s.parameters())
        s.set_parameters(p)
        self.assertEqual(p, s.parameters())

        # State
        state = np.zeros(len(s.state()))
        state[0] = 0.5
        state[1] = 0.5
        self.assertNotEqual(list(state), list(s.state()))
        s.set_state(state)
        self.assertEqual(list(state), list(s.state()))

        # Default state
        dstate = np.zeros(len(s.default_state()))
        dstate[0] = 0.5
        dstate[1] = 0.5
        self.assertNotEqual(list(dstate), list(s.default_state()))
        s.set_default_state(dstate)
        self.assertEqual(list(dstate), list(s.default_state()))


class DiscreteSimulationTest(unittest.TestCase):
    """
    Tests :class:`myokit.lib.markov.DiscreteSimulationTest`.
    """

    def test_basics(self):
        """ Tests the DiscreteSimulation class, running, resetting etc.. """

        # Create a simulation
        fname = os.path.join(DIR_DATA, 'clancy-1999-fitting.mmt')
        model = myokit.load_model(fname)
        m = markov.LinearModel.from_component(model.get('ina'))

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

        # Pre should change the state and default state
        state = s.state()
        dstate = s.default_state()
        s.pre(tprep + tstep)
        self.assertNotEqual(state, s.state())
        self.assertNotEqual(dstate, s.default_state())

        # Run should change the state, not the default state
        state = s.state()
        dstate = s.default_state()
        s.run(15)
        self.assertNotEqual(state, s.state())
        self.assertEqual(dstate, s.default_state())

        # Reset should reset the state
        s.reset()
        self.assertEqual(state, s.state())

        # Run can append to log
        d = s.run(10)
        n = len(d['engine.time'])
        e = s.run(1, log=d)
        self.assertIs(d, e)
        self.assertTrue(len(d['engine.time']) > n)

    def test_discrete_simulation_properties(self):
        """
        Tests basic get/set methods of discrete simulation.
        """
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
        p = range(len(s.parameters()))
        self.assertNotEqual(p, s.parameters())
        s.set_parameters(p)
        self.assertEqual(p, s.parameters())

        # State
        state = np.zeros(len(s.state()))
        state[0] = 25
        state[1] = 25
        self.assertNotEqual(list(state), list(s.state()))
        s.set_state(state)
        self.assertEqual(list(state), list(s.state()))

        # Default state
        dstate = np.zeros(len(s.default_state()))
        dstate[0] = 25
        dstate[1] = 25
        self.assertNotEqual(list(dstate), list(s.default_state()))
        s.set_default_state(dstate)
        self.assertEqual(list(dstate), list(s.default_state()))


if __name__ == '__main__':
    unittest.main()
