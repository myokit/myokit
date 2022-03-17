#!/usr/bin/env python3
#
# Tests the OpenCL simulation classes
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

from myokit.tests import OpenCL_DOUBLE_PRECISION, DIR_DATA

# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp


# Show simulation output
debug = False


@unittest.skipIf(
    not OpenCL_DOUBLE_PRECISION,
    'OpenCL double precision extension not supported on selected device.')
class SimulationOpenCL1dTest(unittest.TestCase):
    """
    Tests the OpenCL simulation against Sim1d.
    """
    def test_simple_run(self):
        # Compare the SimulationOpenCL output with Simulation1d output

        # Set up simulations
        m = myokit.load_model(os.path.join(DIR_DATA, 'beeler-1977-model.mmt'))
        m.get('membrane.i_stim.amplitude').set_rhs(-80)
        p = myokit.pacing.blocktrain(period=1000, duration=2, offset=3)
        n = 10
        sa = myokit.Simulation1d(m, p, ncells=n)
        sb = myokit.SimulationOpenCL(
            m, p, ncells=n, precision=myokit.DOUBLE_PRECISION)

        dt = 0.005
        sa.set_step_size(dt)
        sb.set_step_size(dt)
        sa.set_paced_cells(2)
        sb.set_paced_cells(2)

        tmax = 15
        logvars = [
            'engine.time',
            'membrane.V',
            'engine.pace',
            'isi.Isi',
            'membrane.i_diff',
        ]
        da = sa.run(tmax, log=logvars, log_interval=0.5).npview()
        db = sb.run(tmax, log=logvars, log_interval=0.5).npview()

        # Show results
        if debug:
            import matplotlib.pyplot as plt
            fig = plt.figure(figsize=(12, 9))
            fig.subplots_adjust(0.08, 0.08, 0.98, 0.98, 0.5, 0.3)
            ax = fig.add_subplot(2, 4, 1)
            ax.set_xlabel('Time (ms)')
            ax.set_ylabel('V')
            ax.plot(da.time(), da['membrane.V', 0], '-', lw=2, alpha=0.5)
            ax.plot(da.time(), da['membrane.V', 9], '-', lw=2, alpha=0.5)
            ax.plot(db.time(), db['membrane.V', 0], '--')
            ax.plot(db.time(), db['membrane.V', 9], '--')

            ax = fig.add_subplot(2, 4, 2)
            ax.set_xlabel('Time (ms)')
            ax.set_ylabel('Idiff')
            ax.plot(da.time(), da['membrane.i_diff', 0], '-', lw=2, alpha=0.5)
            ax.plot(da.time(), da['membrane.i_diff', 9], '-', lw=2, alpha=0.5)
            ax.plot(db.time(), db['membrane.i_diff', 0], '--')
            ax.plot(db.time(), db['membrane.i_diff', 9], '--')

            ax = fig.add_subplot(2, 4, 3)
            ax.set_xlabel('Time (ms)')
            ax.set_ylabel('Isi')
            ax.plot(da.time(), da['isi.Isi', 0], '-', lw=2, alpha=0.5)
            ax.plot(da.time(), da['isi.Isi', 9], '-', lw=2, alpha=0.5)
            ax.plot(db.time(), db['isi.Isi', 0], '--')
            ax.plot(db.time(), db['isi.Isi', 9], '--')

            ax = fig.add_subplot(2, 4, 4)
            ax.set_xlabel('Time (ms)')
            ax.set_ylabel('pace')
            ax.plot(da.time(), da['engine.pace'], '-', lw=2, alpha=0.5)
            ax.plot(db.time(), db['engine.pace'], '--')

            ax = fig.add_subplot(2, 4, 5)
            ax.set_xlabel('Time (ms)')
            ax.set_ylabel('V error')
            ax.plot(da.time(), da['membrane.V', 0] - db['membrane.V', 0])
            ax.plot(da.time(), da['membrane.V', 9] - db['membrane.V', 9])

            ax = fig.add_subplot(2, 4, 6)
            ax.set_xlabel('Time (ms)')
            ax.set_ylabel('Idiff error')
            ax.plot(da.time(),
                    da['membrane.i_diff', 0] - db['membrane.i_diff', 0])
            ax.plot(da.time(),
                    da['membrane.i_diff', 9] - db['membrane.i_diff', 9])

            ax = fig.add_subplot(2, 4, 7)
            ax.set_xlabel('Time (ms)')
            ax.set_ylabel('Isi error')
            ax.plot(da.time(), da['isi.Isi', 0] - db['isi.Isi', 0])
            ax.plot(da.time(), da['isi.Isi', 9] - db['isi.Isi', 9])

            ax = fig.add_subplot(2, 4, 8)
            ax.set_xlabel('Time (ms)')
            ax.set_ylabel('pace error')
            ax.plot(da.time(), da['engine.pace'] - db['engine.pace'])
            plt.show()

        e = np.abs(da.time() - db.time())
        self.assertLess(np.max(e), 1e-17)
        e = np.abs(da['engine.pace'] - db['engine.pace'])
        self.assertLess(np.max(e), 1e-17)

        e = np.abs(da['membrane.V', 0] - db['membrane.V', 0])
        self.assertLess(np.max(e), 1e-13)
        e = np.abs(da['membrane.V', 9] - db['membrane.V', 9])
        self.assertLess(np.max(e), 1e-13)

        e = np.abs(da['membrane.i_diff', 0] - db['membrane.i_diff', 0])
        self.assertLess(np.max(e), 1e-13)
        e = np.abs(da['membrane.i_diff', 9] - db['membrane.i_diff', 9])
        self.assertLess(np.max(e), 1e-13)

        e = np.abs(da['isi.Isi', 0] - db['isi.Isi', 0])
        self.assertLess(np.max(e), 1e-13)
        e = np.abs(da['isi.Isi', 9] - db['isi.Isi', 9])
        self.assertLess(np.max(e), 1e-13)


if __name__ == '__main__':
    import sys
    if '-v' in sys.argv:
        print('Running in debug/verbose mode')
        debug = True
    else:
        print('Add -v for more debug output')
    unittest.main()
