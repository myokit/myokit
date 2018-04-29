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
            'ina.O',
        ]
        parameters = [
            'ina.p1',
            'ina.p2',
            'ina.p3',
            'ina.p4',
        ]
        current = 'ina.i'

        # Create a markov model
        markov.LinearModel(model, states, parameters, current)

        # Test deprecated MarkovModel class
        m2 = markov.MarkovModel(model, states, parameters, current)
        self.assertEqual(type(m2), markov.AnalyticalSimulation)

        # State doesn't exist
        self.assertRaises(
            ValueError, markov.LinearModel, model, states + ['bert'],
            parameters, current)

        # State isn't a state
        self.assertRaises(
            ValueError, markov.LinearModel, model, states + ['ina.i'],
            parameters, current)

        # State added twice
        self.assertRaises(
            ValueError, markov.LinearModel, model, states + ['ina.O'],
            parameters, current)

        # No parameters is allowed
        markov.LinearModel(model, states, None, current)

        # Non-literal parameter
        self.assertRaises(
            ValueError, markov.LinearModel, model, states,
            parameters + ['ina.i'], current)

        # Parameter added twice
        self.assertRaises(
            ValueError, markov.LinearModel, model, states,
            parameters + ['ina.p1'], current)

        # Unknown parameter
        self.assertRaises(
            ValueError, markov.LinearModel, model, states,
            parameters + ['ina.p1000'], current)

        # Current is a state
        self.assertRaises(
            ValueError, markov.LinearModel, model, states, parameters, 'ina.O')

        # Current is not a function of the states
        m2 = model.clone()
        markov.LinearModel(m2, states, parameters, current)
        m2.get(current).set_rhs(0)
        self.assertRaises(
            ValueError, markov.LinearModel, m2, states, parameters, current)

        # Vm not given in model
        m2 = model.clone()
        markov.LinearModel(m2, states, parameters, current)
        m2.get('membrane.V').set_label(None)
        self.assertRaises(
            ValueError, markov.LinearModel, m2, states, parameters, current)
        markov.LinearModel(m2, states, parameters, current, vm='membrane.V')

        # Vm is a parameter
        self.assertRaises(
            ValueError, markov.LinearModel, m2, states, parameters, current,
            vm=parameters[0])

        # Vm is a state
        self.assertRaises(
            ValueError, markov.LinearModel, m2, states, parameters, current,
            vm=states[0])

        # Vm is the current
        self.assertRaises(
            ValueError, markov.LinearModel, m2, states, parameters, current,
            vm=current)

        # States must have bidrectional dependencies
        m2 = model.clone()
        markov.LinearModel(m2, states, parameters, current)
        m2.get('ina.C3').set_rhs('0')
        # Set bad config, but with columns still summing to zero
        x = m2.get('ina.C2')
        m2.get('ina.C2').set_rhs(str(x.rhs()) + '+ a12 * C2 + - b12 * C1')
        self.assertRaises(
            ValueError, markov.LinearModel, m2, states, parameters, current)

        # States must sum to 1
        m2 = model.clone()
        markov.LinearModel(m2, states, parameters, current)
        m2.get(states[0]).set_state_value(0.6)
        m2.get(states[1]).set_state_value(0.6)
        self.assertRaises(
            Exception, markov.LinearModel, m2, states, parameters, current)

        # Derivatives per column don't sum to zero
        m2 = model.clone()
        markov.LinearModel(m2, states, parameters, current)
        x = m2.get(states[0])
        x.set_rhs('2 * ' + str(x.rhs()))
        self.assertRaises(
            Exception, markov.LinearModel, m2, states, parameters, current)

        # Not a linear model
        m2 = model.clone()
        markov.LinearModel(m2, states, parameters, current)
        x = m2.get(states[0])
        y = m2.get(states[1])
        # Set rhs to something non-linear, make sure columns still sum to 0
        x.set_rhs(str(x.rhs()) + ' + C1^2')
        y.set_rhs(str(y.rhs()) + ' - C1^2')
        self.assertRaises(
            Exception, markov.LinearModel, m2, states, parameters, current)

    def test_automatic_creation(self):
        """ Create a linear model from a component. """

        # Load model
        fname = os.path.join(DIR_DATA, 'clancy-1999-fitting.mmt')
        model = myokit.load_model(fname)

        # Create a markov model
        markov.LinearModel.from_component(model.get('ina'))

        # Test deprecated MarkovModel class
        m2 = markov.MarkovModel.from_component(model.get('ina'))
        self.assertEqual(type(m2), markov.AnalyticalSimulation)

        # Test partially automatic creation
        states = [
            'ina.C3',
            'ina.C2',
            'ina.C1',
            'ina.IF',
            'ina.IS',
            'ina.O',
        ]
        markov.LinearModel.from_component(model.get('ina'), states=states)

        parameters = [
            'ina.p1',
            'ina.p2',
            'ina.p3',
            'ina.p4',
        ]
        markov.LinearModel.from_component(
            model.get('ina'), parameters=parameters)

        current = 'ina.i'
        markov.LinearModel.from_component(model.get('ina'), current=current)

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

    def test_analytical_simulation(self):
        """ Tests the AnalyticalSimulation class. """

        # Create a simulation
        fname = os.path.join(DIR_DATA, 'clancy-1999-fitting.mmt')
        model = myokit.load_model(fname)
        m = markov.LinearModel.from_component(model.get('ina'))
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

        # Run should change the state, not the default state
        state = s.state()
        dstate = s.default_state()
        s.run(t)
        self.assertNotEqual(state, s.state())
        self.assertEqual(dstate, s.default_state())

        # Reset should reset the state
        s.reset()
        self.assertEqual(state, s.state())

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

    def test_discrete_simulation(self):
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


if __name__ == '__main__':
    unittest.main()
