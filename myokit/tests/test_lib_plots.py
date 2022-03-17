#!/usr/bin/env python3
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

from myokit.tests import DIR_DATA


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
        fig = plt.figure()
        plots.simulation_times(st, rt, ev, 'stair')
        plt.show()
        plt.close(fig)
        self.assertRaises(ValueError, plots.simulation_times, mode='stair')

        # Inverse stair
        fig = plt.figure()
        plots.simulation_times(st, rt, ev, 'stair_inverse')
        plt.show()
        plt.close(fig)
        self.assertRaises(
            ValueError, plots.simulation_times, mode='stair_inverse')

        # Load
        fig = plt.figure()
        plots.simulation_times(st, rt, ev, 'load')
        plt.show()
        plt.close(fig)
        self.assertRaises(ValueError, plots.simulation_times, mode='load')

        # Histogram
        fig = plt.figure()
        plots.simulation_times(st, rt, ev, 'histo')
        plt.show()
        plt.close(fig)
        self.assertRaises(ValueError, plots.simulation_times, mode='histo')

        # Time per step
        fig = plt.figure()
        plots.simulation_times(st, rt, ev, 'time_per_step')
        plt.show()
        plt.close(fig)
        self.assertRaises(
            ValueError, plots.simulation_times, mode='time_per_step')

        # Evaluations per step
        fig = plt.figure()
        plots.simulation_times(st, rt, ev, 'eval_per_step')
        plt.show()
        plt.close(fig)
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

        fig = plt.figure()
        plots.current_arrows(d, 'membrane.V', currents)
        plt.close(fig)
        plt.show()

        # Massive peak at final point
        d = d.npview()
        d['dummy.IDummy'][-1] = 100
        fig = plt.figure()
        plots.current_arrows(d, 'membrane.V', currents)
        plt.close(fig)
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
        fig = plt.figure()
        plots.cumulative_current(d, currents)
        plt.legend()
        plt.close(fig)
        plt.show()

        # Labels set
        labels = ['I_Ca', 'I_K', 'I_K1', 'I_Kp', 'I_b']
        fig = plt.figure()
        plots.cumulative_current(d, currents, labels=labels)
        plt.legend()
        plt.close(fig)
        plt.show()

        # Colors set
        colors = ['green', 'blue', 'yellow', 'brown', 'gray']
        fig = plt.figure()
        plots.cumulative_current(d, currents, colors=colors)
        plt.legend()
        plt.close(fig)
        plt.show()

        # Not enough colors set (will repeat array)
        colors = ['green', 'blue']
        fig = plt.figure()
        plots.cumulative_current(d, currents, colors=colors)
        plt.legend()
        plt.close(fig)
        plt.show()

        # Integrate currents to charges
        fig = plt.figure()
        plots.cumulative_current(d, currents, integrate=True)
        plt.legend()
        plt.close(fig)
        plt.show()

        # Normalise currents
        fig = plt.figure()
        plots.cumulative_current(d, currents, normalise=True)
        plt.legend()
        plt.close(fig)
        plt.show()

        # Normalise currents and set maximum number of currents shown
        fig = plt.figure()
        plots.cumulative_current(d, currents, normalise=True, max_currents=3)
        plt.legend()
        plt.close(fig)
        plt.show()


if __name__ == '__main__':
    unittest.main()
