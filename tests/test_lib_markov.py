#!/usr/bin/env python
#
# Tests the LinearModel class
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
import os
import unittest
import numpy as np

import myokit
import myokit.lib.markov as markov

from shared import DIR_DATA


class LinearModelTest(unittest.TestCase):
    def test_manual_creation(self):
        """
        Tests manual creation of a LinearModel
        """
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
        m = markov.LinearModel(model, states, parameters, current)
        # Create a simulation
        s = markov.AnalyticalSimulation(m)
        # Times to evaluate at
        times = np.linspace(0, 100, 5)
        # Voltages to test at
        voltages = np.arange(-70, 0, 30)
        # Generate traces
        for v in voltages:
            s.set_membrane_potential(v)
            x, i = s.solve(times)

    def test_automatic_creation(self):
        # Load model
        fname = os.path.join(DIR_DATA, 'clancy-1999-fitting.mmt')
        model = myokit.load_model(fname)
        # Create a markov model
        m = markov.LinearModel.from_component(model.get('ina'))
        # Create a simulation
        s = markov.AnalyticalSimulation(m)
        # Times to evaluate at
        times = np.linspace(0, 100, 5)
        # Voltages to test at
        voltages = np.arange(-70, 0, 30)
        # Generate traces
        for v in voltages:
            s.set_membrane_potential(v)
            x, i = s.solve(times)


if __name__ == '__main__':
    unittest.main()
