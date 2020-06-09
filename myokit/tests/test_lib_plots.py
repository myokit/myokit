#!/usr/bin/env python
#
# Tests if the myokit.lib.plots module runs without exceptions, doesn't inspect
# the output.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import os
import unittest

import myokit
import myokit.lib.plots as plots

from shared import DIR_DATA


class LibPlotTest(unittest.TestCase):
    """
    Tests if the myokit.lib.plots module runs without exceptions, doesn't
    inspect the output.
    """

    def test_simulation_times(self):
        # Test the simulation times() plots (has several modes).

        # Select matplotlib backend that doesn't require a screen
        import matplotlib
        matplotlib.use('template')
        import matplotlib.pyplot as plt

        # Run simulation, get benchmarks
        m, p, x = myokit.load(os.path.join(DIR_DATA, 'lr-1991.mmt'))
        s = myokit.Simulation(m, p)
        d = s.run(1000, log=[
            'engine.time', 'engine.realtime', 'engine.evaluations'])
        st = d['engine.time']
        rt = d['engine.realtime']
        ev = d['engine.evaluations']

        # Stair
        plt.figure()
        plots.simulation_times(st, rt, ev, 'stair')
        plt.show()
        self.assertRaises(ValueError, plots.simulation_times, mode='stair')

        # Inverse stair
        plt.figure()
        plots.simulation_times(st, rt, ev, 'stair_inverse')
        plt.show()
        self.assertRaises(
            ValueError, plots.simulation_times, mode='stair_inverse')

        # Load
        plt.figure()
        plots.simulation_times(st, rt, ev, 'load')
        plt.show()
        self.assertRaises(ValueError, plots.simulation_times, mode='load')

        # Histogram
        plt.figure()
        plots.simulation_times(st, rt, ev, 'histo')
        plt.show()
        self.assertRaises(ValueError, plots.simulation_times, mode='histo')

        # Time per step
        plt.figure()
        plots.simulation_times(st, rt, ev, 'time_per_step')
        plt.show()
        self.assertRaises(
            ValueError, plots.simulation_times, mode='time_per_step')

        # Evaluations per step
        plt.figure()
        plots.simulation_times(st, rt, ev, 'eval_per_step')
        plt.show()
        self.assertRaises(
            ValueError, plots.simulation_times, mode='eval_per_step')

        # Non-existing model
        self.assertRaises(
            ValueError, plots.simulation_times, st, rt, ev, mode='xxx')

    def test_current_arrows(self):
        # Test the current arrows plot.

        # Select matplotlib backend that doesn't require a screen
        import matplotlib
        matplotlib.use('template')
        import matplotlib.pyplot as plt

        # Run simulation, get currents
        m, p, x = myokit.load(os.path.join(DIR_DATA, 'lr-1991.mmt'))

        # Add dummy current, that never carries much charge and should be
        # ignored
        c = m.add_component('dummy')
        x = c.add_variable('IDummy')
        x.set_rhs('0 * membrane.V')

        s = myokit.Simulation(m, p)
        currents = ['ina.INa', 'ik1.IK1', 'ica.ICa', 'dummy.IDummy']
        d = s.run(600, log=['engine.time', 'membrane.V'] + currents)

        plt.figure()
        plots.current_arrows(d, 'membrane.V', currents)
        plt.show()

        # Massive peak at final point
        d = d.npview()
        d['dummy.IDummy'][-1] = 100
        plt.figure()
        plots.current_arrows(d, 'membrane.V', currents)
        plt.show()

    def test_cumulative_current(self):
        # Test the cumulative current plot.

        # Select matplotlib backend that doesn't require a screen
        import matplotlib
        matplotlib.use('template')
        import matplotlib.pyplot as plt

        # Run simulation, get currents
        m, p, x = myokit.load(os.path.join(DIR_DATA, 'lr-1991.mmt'))
        s = myokit.Simulation(m, p)
        currents = ['ica.ICa', 'ik.IK', 'ik1.IK1', 'ikp.IKp', 'ib.Ib']
        d = s.run(600, log=['engine.time', 'membrane.V'] + currents)

        # No extra arguments
        plt.figure()
        plots.cumulative_current(d, currents)
        plt.legend()
        plt.show()

        # Labels set
        labels = ['I_Ca', 'I_K', 'I_K1', 'I_Kp', 'I_b']
        plt.figure()
        plots.cumulative_current(d, currents, labels=labels)
        plt.legend()
        plt.show()

        # Colors set
        colors = ['green', 'blue', 'yellow', 'brown', 'gray']
        plt.figure()
        plots.cumulative_current(d, currents, colors=colors)
        plt.legend()
        plt.show()

        # Not enough colors set (will repeat array)
        colors = ['green', 'blue']
        plt.figure()
        plots.cumulative_current(d, currents, colors=colors)
        plt.legend()
        plt.show()

        # Integrate currents to charges
        plt.figure()
        plots.cumulative_current(d, currents, integrate=True)
        plt.legend()
        plt.show()

        # Normalise currents
        plt.figure()
        plots.cumulative_current(d, currents, normalise=True)
        plt.legend()
        plt.show()

        # Normalise currents and set maximum number of currents shown
        plt.figure()
        plots.cumulative_current(d, currents, normalise=True, max_currents=3)
        plt.legend()
        plt.show()


if __name__ == '__main__':
    unittest.main()
