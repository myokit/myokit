#!/usr/bin/env python
#
# Tests the OpenCL simulation classes
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

import myokit

from shared import OpenCL_FOUND, DIR_DATA


class SimulationOpenCL1dTest(unittest.TestCase):
    """
    Tests the OpenCL simulation in 1d mode.
    """
    def test_set_state(self):
        if not OpenCL_FOUND:
            print('OpenCL support not found, skipping test.')
            return

        m, p, x = myokit.load('example')
        n = 10
        s = myokit.SimulationOpenCL(m, p, n)
        sm = m.state()
        ss = [s.state(x) for x in range(n)]
        for si in ss:
            self.assertEqual(sm, si)

        # Test setting a single, global state
        sx = [0.0] * 8
        self.assertNotEqual(sm, sx)
        s.set_state(sx)
        for i in range(n):
            self.assertEqual(sx, s.state(i))
        self.assertEqual(sx * n, s.state())
        s.set_state(sm)
        self.assertEqual(sm * n, s.state())
        # Test setting a single state
        j = 1
        s.set_state(sx, j)
        for i in range(n):
            if i == j:
                self.assertEqual(s.state(i), sx)
            else:
                self.assertEqual(s.state(i), sm)

    def test_sim(self):
        if not OpenCL_FOUND:
            print('OpenCL support not found, skipping test.')
            return

        m, p, x = myokit.load('example')
        s = myokit.SimulationOpenCL(m, p, 20)

        # Run, log state and intermediary variable (separate logging code!)
        d = s.run(1, log=['engine.time', 'membrane.V', 'ina.INa'])
        self.assertIn('engine.time', d)
        self.assertIn('0.membrane.V', d)
        self.assertIn('19.membrane.V', d)
        self.assertIn('0.ina.INa', d)
        self.assertIn('19.ina.INa', d)
        self.assertEqual(len(d), 41)


@unittest.skipIf(not OpenCL_FOUND, 'OpenCL not found on this system.')
class SimulationOpenCL2dTest(unittest.TestCase):
    """
    Tests the OpenCL simulation in 2d mode.
    """
    def test_sim(self):
        m, p, x = myokit.load('example')
        n = (8, 8)
        s = myokit.SimulationOpenCL(m, p, n)
        s.set_paced_cells(4, 4)

        # Run, log state and intermediary variable (separate logging code!)
        d = s.run(1, log=['engine.time', 'membrane.V', 'ina.INa'])
        self.assertEqual(len(d), 129)
        self.assertIn('engine.time', d)
        self.assertIn('0.0.membrane.V', d)
        self.assertIn('7.7.membrane.V', d)
        self.assertIn('0.0.ina.INa', d)
        self.assertIn('7.7.ina.INa', d)


@unittest.skipIf(not OpenCL_FOUND, 'OpenCL not found on this system.')
class FiberTissueSimulationTest(unittest.TestCase):
    """
    Tests the fiber-tissue simulation.
    """
    def test_simple(self):
        # Load models
        mf = os.path.join(DIR_DATA, 'dn-1985-normalised.mmt')
        mt = os.path.join(DIR_DATA, 'lr-1991.mmt')
        mf = myokit.load_model(mf)
        mt = myokit.load_model(mt)

        # Run times
        run = .1

        # Create pacing protocol
        p = myokit.pacing.blocktrain(1000, 2.0, offset=.01)

        # Fiber/Tissue sizes
        nfx = 8
        nfy = 4
        ntx = 8
        nty = 6

        # Create simulation
        s = myokit.FiberTissueSimulation(
            mf,
            mt,
            p,
            ncells_fiber=(nfx, nfy),
            ncells_tissue=(ntx, nty),
            nx_paced=10,
            g_fiber=(235, 100),
            g_tissue=(9, 5),
            g_fiber_tissue=9
        )
        s.set_step_size(0.0012)
        # Set up logging
        logf = [
            'engine.time',
            'membrane.V',
            'isi.isiCa',
        ]
        logt = [
            'membrane.V',
            'ica.Ca_i',
            'ica.ICa',
        ]
        # Run simulation
        with myokit.PyCapture():
            logf, logt = s.run(run, logf=logf, logt=logt, log_interval=0.01)

        self.assertEqual(len(logf), 1 + 2 * nfx * nfy)
        self.assertIn('engine.time', logf)
        self.assertIn('0.0.membrane.V', logf)
        self.assertIn(str(nfx - 1) + '.' + str(nfy - 1) + '.membrane.V', logf)
        self.assertIn('0.0.isi.isiCa', logf)
        self.assertIn(str(nfx - 1) + '.' + str(nfy - 1) + '.isi.isiCa', logf)

        self.assertEqual(len(logt), 3 * ntx * nty)
        self.assertIn('0.0.membrane.V', logt)
        self.assertIn(str(ntx - 1) + '.' + str(nty - 1) + '.membrane.V', logt)
        self.assertIn('0.0.ica.Ca_i', logt)
        self.assertIn(str(ntx - 1) + '.' + str(nty - 1) + '.ica.Ca_i', logt)
        self.assertIn('0.0.ica.ICa', logt)
        self.assertIn(str(ntx - 1) + '.' + str(nty - 1) + '.ica.ICa', logt)


if __name__ == '__main__':
    unittest.main()
