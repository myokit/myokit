#!/usr/bin/env python
#
# Tests the C implementation of the Pacing System
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import unittest
import numpy as np

import myokit

from ansic_event_based_pacing import AnsicEventBasedPacing
from ansic_fixed_form_pacing import AnsicFixedFormPacing

# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp


class EventBasedPacingAnsicTest(unittest.TestCase):
    """
    Tests the C implementation of event based pacing.
    """
    def test_with_event_at_t_0(self):
        # Test with event starting at t=0

        # Test basics
        p = myokit.Protocol()
        p.schedule(2, 0, 1, 10, 0)
        s = AnsicEventBasedPacing(p)
        self.assertEqual(s.time(), 0)
        self.assertEqual(s.next_time(), 1)
        self.assertEqual(s.pace(), 2)
        s.advance(0)
        self.assertEqual(s.time(), 0)
        self.assertEqual(s.next_time(), 1)
        self.assertEqual(s.pace(), 2)
        s.advance(0)
        s.advance(0)
        s.advance(0)
        self.assertEqual(s.time(), 0)
        self.assertEqual(s.next_time(), 1)
        self.assertEqual(s.pace(), 2)
        s.advance(0.5)
        self.assertEqual(s.time(), 0.5)
        self.assertEqual(s.next_time(), 1)
        self.assertEqual(s.pace(), 2)
        s.advance(1)
        self.assertEqual(s.time(), 1)
        self.assertEqual(s.next_time(), 10)
        self.assertEqual(s.pace(), 0)
        s.advance(2)
        self.assertEqual(s.time(), 2)
        self.assertEqual(s.next_time(), 10)
        self.assertEqual(s.pace(), 0)
        s.advance(10)
        self.assertEqual(s.time(), 10)
        self.assertEqual(s.next_time(), 11)
        self.assertEqual(s.pace(), 2)

    def test_with_event_at_t_1(self):
        p = myokit.Protocol()
        p.schedule(2, 1, 1, 10, 0)
        s = AnsicEventBasedPacing(p)
        self.assertEqual(s.time(), 0)
        self.assertEqual(s.next_time(), 1)
        self.assertEqual(s.pace(), 0)
        p = myokit.Protocol()
        s = AnsicEventBasedPacing(p)
        self.assertEqual(s.time(), 0)
        self.assertEqual(s.next_time(), float('inf'))
        self.assertEqual(s.pace(), 0)

    def test_max_time(self):
        # Test max time
        p = myokit.Protocol()
        s = AnsicEventBasedPacing(p)
        s.advance(20, max_time=13)
        self.assertEqual(s.time(), 13)
        #self.assertEqual(s.next_time(), 13)
        #self.assertEqual(s.pace(), 0)

        # Test basic use + log creation methods
        '''
        p = myokit.Protocol()
        p.schedule(1, 10, 1, 1000, 0)
        d = AnsicEventBasedPacing.log_for_interval(p, 0, 3000)
        self.assertEqual(d.time(), [0, 10, 11, 1010, 1011, 2010, 2011, 3000])
        d = AnsicEventBasedPacing.log_for_interval(
            p, 0, 2000, for_drawing=True)
        self.assertEqual(d.time(), [
            0, 10, 10, 11, 11, 1010, 1010, 1011, 1011, 2000])
        p = myokit.Protocol()
        p.schedule(1, 0, 1, 1000, 0)
        d = AnsicEventBasedPacing.log_for_interval(p, 0, 3000)
        self.assertEqual(d.time(), [0, 1, 1000, 1001, 2000, 2001, 3000])
        d = AnsicEventBasedPacing.log_for_interval(
            p, 0, 2000, for_drawing=True)
        self.assertEqual(d.time(), [0, 1, 1, 1000, 1000, 1001, 1001, 2000])
        '''

    def test_simultaneous_event_error(self):
        # Test raising of errors on rescheduled periodic events

        p = myokit.Protocol()
        p.schedule(1, 0, 1, 1000)
        p.schedule(1, 3000, 1)
        s = AnsicEventBasedPacing(p)
        t = s.next_time()
        self.assertEqual(t, 1)
        s.advance(t)
        t = s.next_time()
        self.assertEqual(t, 1000)
        s.advance(t)
        t = s.next_time()
        self.assertEqual(t, 1001)
        s.advance(t)
        t = s.next_time()
        self.assertEqual(t, 2000)
        self.assertRaises(myokit.SimultaneousProtocolEventError, s.advance, t)

        # Test raising of errors in simulation
        p = myokit.Protocol()
        p.schedule(1, 0, 1, 10)
        p.schedule(1, 30, 1)
        m = myokit.load_model('example')
        s = myokit.Simulation(m, p)
        self.assertRaises(myokit.SimultaneousProtocolEventError, s.run, 40)


class FixedFormPacingAnsicTest(unittest.TestCase):
    """
    Test the Ansi-C fixed-form pacing system (aka point-list, aka data-clamp).
    """
    def test_fixed_form_pacing_ansic(self):
        # Tests if the basics work

        if False:
            # Graphical test, just for playing with the pacing system
            m, p, x = myokit.load('example')
            s = myokit.Simulation(m, p)
            d = s.run(500).npview()
            # Get time and voltage
            t = d.time()
            v = d['membrane.V']
            # Plot trace
            import matplotlib.pyplot as plt
            plt.figure()
            plt.plot(t, v, 'x')
            # Get some points halfway, 1/4 of the way, and 3/4 of the way
            # between the known points
            t2 = t[:-1] + 0.25 * (t[1:] - t[:-1])
            t3 = t[:-1] + 0.5 * (t[1:] - t[:-1])
            t4 = t[:-1] + 0.75 * (t[1:] - t[:-1])
            t2 = np.concatenate((t2, t3, t4))
            del(t3, t4)
            # Get the pacing value at the points, measure how long it takes
            pacing = AnsicFixedFormPacing(list(t), list(v))
            b = myokit.Benchmarker()
            v2 = [pacing.pace(x) for x in t2]
            print(b.time())
            # Plot the new points
            plt.plot(t2, v2, '.', color='green')
            plt.show()
            # Quite
            import sys
            sys.exit(1)

        # Test input checking
        times = 1
        values = [1, 2]
        self.assertRaises(Exception, AnsicFixedFormPacing)
        self.assertRaises(Exception, AnsicFixedFormPacing, 1)
        self.assertRaises(Exception, AnsicFixedFormPacing, 1, 2)
        self.assertRaises(Exception, AnsicFixedFormPacing, [1], [2])
        self.assertRaises(
            Exception, AnsicFixedFormPacing, [1, 2], [2])
        self.assertRaises(
            Exception, AnsicFixedFormPacing, [2, 1], [2, 2])
        AnsicFixedFormPacing([1, 2], [1, 2])

        # Test with small lists
        values = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        times = [0, 0, 1, 1, 1, 2, 2, 2, 3, 4, 5, 7]
        values = list(range(len(times)))
        pacing = AnsicFixedFormPacing(times, values)

        def test(value, index):
            self.assertEqual(pacing.pace(value), index)

        test(-1, 0)
        test(0, 1)
        test(1, 2)
        test(2, 5)
        test(3, 8)
        test(4, 9)
        test(5, 10)
        test(7, 11)
        test(8, 11)
        test(1.5, 4.5)
        test(1.75, 4.75)
        test(6, 10.5)
        test(5.5, 10.25)


if __name__ == '__main__':
    unittest.main()
