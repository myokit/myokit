#!/usr/bin/env python3
#
# Tests the classes in `myokit.lib.common`.
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

from myokit.tests import DIR_DATA, WarningCollector


class CommonTest(unittest.TestCase):
    """Tests lib.common"""

    def test_activation(self):
        # Test the activation experiment class.
        with WarningCollector():
            import myokit.lib.common as common

        # Load model
        m = os.path.join(DIR_DATA, 'lr-1991.mmt')
        m = myokit.load_model(m)
        # Create experiment
        c = m.get('ina')
        g = c.add_variable('g')
        g.set_rhs('m^3 * h * j')
        m.validate()
        a = common.Activation(m, 'ina.g')
        # Test
        a.times()
        a.traces()
        a.peaks(normalize=True)
        a.peaks(normalize=False)
        a.fit_boltzmann()
        a.convert_g2i()
        a.times()
        a.traces()
        a.peaks(normalize=True)
        a.peaks(normalize=False)
        a.fit_boltzmann()

    def test_inactivation(self):
        # Test the inactivation experiment class.
        with WarningCollector():
            import myokit.lib.common as common

        # Load model
        m = os.path.join(DIR_DATA, 'lr-1991.mmt')
        m = myokit.load_model(m)
        # Create experiment
        c = m.get('ina')
        g = c.add_variable('g')
        g.set_rhs('m^3 * h * j')
        m.validate()
        a = common.Inactivation(m, 'ina.g')
        # Test
        a.times()
        a.traces()
        a.peaks(normalize=True)
        a.peaks(normalize=False)
        a.fit_boltzmann()

    def test_recovery(self):
        # Test the recovery experiment class.
        with WarningCollector():
            import myokit.lib.common as common

        # Load model
        m = os.path.join(DIR_DATA, 'lr-1991.mmt')
        m = myokit.load_model(m)
        # Create experiment
        c = m.get('ina')
        g = c.add_variable('g')
        g.set_rhs('m^3 * h * j')
        m.validate()
        r = common.Recovery(m, 'ina.g')
        # Test
        n = 20
        r.set_pause_duration(0.1, 10, n)
        d = r.ratio()
        self.assertEqual(len(d), 2)
        self.assertIn('engine.time', d)
        self.assertIn('ina.g', d)
        self.assertEqual(n, len(d['engine.time']))
        self.assertEqual(n, len(d['ina.g']))
        x = d['engine.time']
        self.assertTrue(np.all(x[1:] > x[:-1]))
        x = d['ina.g']  # This is a monotonically increasing function
        self.assertTrue(np.all(x[1:] > x[:-1]))

    def test_restitution(self):
        # Test the restitution experiment class.
        with WarningCollector():
            import myokit.lib.common as common

        # Load model
        m = os.path.join(DIR_DATA, 'lr-1991.mmt')
        m = myokit.load_model(m)
        # Create experiment
        r = common.Restitution(m)
        # Test
        r.set_times(300, 800, 200)
        r.run()

    def test_strength_duration(self):
        # Test the strength-duration experiment class.
        with WarningCollector():
            import myokit.lib.common as common

        # Load model
        m = os.path.join(DIR_DATA, 'lr-1991.mmt')
        m = myokit.load_model(m)
        # Create experiment
        s = common.StrengthDuration(m, 'membrane.i_stim')
        # Test
        s.set_currents(-200, -10)
        s.set_times(0.5, 1.0, 0.2)
        s.run()


if __name__ == '__main__':
    unittest.main()
