#!/usr/bin/env python2
#
# Tests the Markov Model class
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
import myokit.lib.common as common
import myotest


def suite():
    """
    Returns a test suite with all tests in this module
    """
    suite = unittest.TestSuite()
    suite.addTest(CommonTest('activation'))
    suite.addTest(CommonTest('inactivation'))
    suite.addTest(CommonTest('recovery'))
    suite.addTest(CommonTest('restitution'))
    suite.addTest(CommonTest('strength_duration'))
    return suite


class CommonTest(unittest.TestCase):
    def activation(self):
        """
        Tests the activation experiment class.
        """
        # Load model
        m = os.path.join(myotest.DIR_DATA, 'lr-1991.mmt')
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

    def inactivation(self):
        """
        Tests the inactivation experiment class.
        """
        # Load model
        m = os.path.join(myotest.DIR_DATA, 'lr-1991.mmt')
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

    def recovery(self):
        """
        Tests the recovery experiment class.
        """
        # Load model
        m = os.path.join(myotest.DIR_DATA, 'lr-1991.mmt')
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

    def restitution(self):
        """
        Tests the restitution experiment class.
        """
        # Load model
        m = os.path.join(myotest.DIR_DATA, 'lr-1991.mmt')
        m = myokit.load_model(m)
        # Create experiment
        r = common.Restitution(m)
        # Test
        r.set_times(300, 800, 200)
        r.run()

    def strength_duration(self):
        """
        Tests the strength-duration experiment class.
        """
        # Load model
        m = os.path.join(myotest.DIR_DATA, 'lr-1991.mmt')
        m = myokit.load_model(m)
        # Create experiment
        s = common.StrengthDuration(m, 'membrane.i_stim')
        # Test
        s.set_currents(-200, -10)
        s.set_times(0.5, 1.0, 0.2)
        s.run()
