#!/usr/bin/env python3
#
# Tests if the myokit.lib.plots module runs without exceptions, doesn't inspect
# the output.
#
# This file is part of Myokit.
# See https://github.com/myokit/myokit for copyright, sharing, and licensing.
#
import unittest

from shared import DIR_DATA, WarningCollector

import myokit
import myokit.lib.plots as plots

debug = False


def close(fig):
    """ Show or close a figure """
    import matplotlib.pyplot as plt
    if debug:
        plt.show()
    else:
        plt.close(fig)


class LibPlotTest(unittest.TestCase):
    """
    Tests if the myokit.lib.plots module runs without exceptions, doesn't
    inspect the output.
    """

    def test_simulation_times(self):
        # Test the simulation times() plots (has several modes).

        # Select matplotlib backend that doesn't require a screen
        import matplotlib
        if not debug:
            matplotlib.use('template')
        import matplotlib.pyplot as plt

        # Run simulation, get benchmarks
        m, p, x = myokit.load(DIR_DATA / 'beeler-1977.mmt')
        e = m.get('engine')
        e.add_variable('realtime', rhs=0, binding='realtime')
        e.add_variable('evaluations', rhs=0, binding='evaluations')

        s = myokit.Simulation(m, p)
        d = s.run(1000, log=[
            'engine.time', 'engine.realtime', 'engine.evaluations'])
        st = d['engine.time']
        rt = d['engine.realtime']
        ev = d['engine.evaluations']

        # Stair
        fig = plt.figure()
        plots.simulation_times(st, rt, ev, 'stair')
        close(fig)

        # Inverse stair
        fig = plt.figure()
        plots.simulation_times(st, rt, ev, 'stair_inverse')
        close(fig)

        # Load
        fig = plt.figure()
        plots.simulation_times(st, rt, ev, 'load')
        close(fig)

        # Histogram
        fig = plt.figure()
        plots.simulation_times(st, rt, ev, 'histo')
        close(fig)

        # Time per step
        fig = plt.figure()
        plots.simulation_times(st, rt, ev, 'time_per_step')
        close(fig)

        # Evaluations per step
        fig = plt.figure()
        plots.simulation_times(st, rt, ev, 'eval_per_step')
        close(fig)

        # Not enough arguments
        self.assertRaises(ValueError, plots.simulation_times, mode='stair')
        self.assertRaises(
            ValueError, plots.simulation_times, mode='stair_inverse')
        self.assertRaises(ValueError, plots.simulation_times, mode='load')
        self.assertRaises(ValueError, plots.simulation_times, mode='histo')
        self.assertRaises(
            ValueError, plots.simulation_times, mode='time_per_step')
        self.assertRaises(
            ValueError, plots.simulation_times, mode='eval_per_step')

        # Non-existing model
        self.assertRaises(
            ValueError, plots.simulation_times, st, rt, ev, mode='xxx')
        plt.close('all')

    def test_current_arrows(self):
        # Test the current arrows plot.

        # Select matplotlib backend that doesn't require a screen
        import matplotlib
        if not debug:
            matplotlib.use('template')
        import matplotlib.pyplot as plt

        # Run simulation, get currents
        m, p, x = myokit.load(DIR_DATA / 'beeler-1977.mmt')

        # Add dummy current, that never carries much charge and should be
        # ignored
        c = m.add_component('dummy')
        x = c.add_variable('IDummy')
        x.set_rhs('0 * membrane.V')

        s = myokit.Simulation(m, p)
        currents = ['ina.INa', 'ik1.IK1', 'is.Is', 'dummy.IDummy']
        d = s.run(600, log=['engine.time', 'membrane.V'] + currents)

        fig = plt.figure()
        plots.current_arrows(d, 'membrane.V', currents)
        close(fig)

        # Massive peak at final point
        d = d.npview()
        d['dummy.IDummy'][-1] = 100
        fig = plt.figure()
        plots.current_arrows(d, 'membrane.V', currents)
        plt.close(fig)

    def test_cumulative_current(self):
        # Test the cumulative current plot.

        # Select matplotlib backend that doesn't require a screen
        import matplotlib
        if not debug:
            matplotlib.use('template')
        import matplotlib.pyplot as plt

        # Run simulation, get currents
        m, p, x = myokit.load(DIR_DATA / 'beeler-1977.mmt')
        s = myokit.Simulation(m, p)
        currents = ['ix1.Ix1', 'is.Is', 'ik1.IK1', 'ina.INa']
        d = s.run(600, log=['engine.time', 'membrane.V'] + currents)

        # No extra arguments
        fig = plt.figure()
        plots.cumulative_current(d, currents)
        plt.legend()
        close(fig)

        # Labels set
        labels = ['Ix1', 'Is', 'IK1', 'INa']
        fig = plt.figure()
        plots.cumulative_current(d, currents, labels=labels)
        plt.legend()
        close(fig)

        # Colors set
        colors = ['green', 'blue', 'yellow', 'brown']
        fig = plt.figure()
        plots.cumulative_current(d, currents, colors=colors)
        plt.legend()
        close(fig)

        # Not enough colors set (will repeat array)
        colors = ['green', 'blue']
        fig = plt.figure()
        plots.cumulative_current(d, currents, colors=colors)
        plt.legend()
        close(fig)

        # Integrate currents to charges
        fig = plt.figure()
        plots.cumulative_current(d, currents, integrate=True)
        plt.legend()
        close(fig)

        # Normalize currents
        fig = plt.figure()
        plots.cumulative_current(d, currents, normalize=True)
        plt.legend()
        close(fig)

        # Normalize currents and set maximum number of currents shown
        fig = plt.figure()
        plots.cumulative_current(d, currents, normalize=True, max_currents=2)
        plt.legend()
        close(fig)

        with WarningCollector() as w:
            fig = plt.figure()
            plots.cumulative_current(d, currents, normalise=True)
            plt.legend()
            plt.close(fig)
        self.assertIn('deprecated', w.text())


if __name__ == '__main__':

    import sys
    if '-v' in sys.argv:
        print('Running in debug/verbose mode')
        debug = True
    else:
        print('Add -v for more debug output')

    unittest.main()

