#!/usr/bin/env python
#
# Tests protocol creation and pacing
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


class PacingTest(unittest.TestCase):
    """
    Contains tests for the Protocol class, ProtocolEvent, PacingSystem and
    the C implementation of pacing.
    """
    def test_event_creation(self):
        """
        Tests the basics of creating events.
        """
        # Invalid event specifications
        def create(start, duration, period=0, multiplier=0):
            myokit.ProtocolEvent(1, start, duration, period, multiplier)
        create(0, 1)
        create(1, 0)
        create(1, 1)
        create(1, 1, 0, 0)
        create(1, 1, 1, 0)
        create(1, 1, 1, 1)
        self.assertRaises(myokit.ProtocolEventError, create, -1, 0)
        self.assertRaises(myokit.ProtocolEventError, create, 0, -1)
        self.assertRaises(myokit.ProtocolEventError, create, -1, 1)
        self.assertRaises(myokit.ProtocolEventError, create, 1, -1)
        self.assertRaises(myokit.ProtocolEventError, create, 0, 0, -1)
        self.assertRaises(myokit.ProtocolEventError, create, 0, 0, 0, 1)
        self.assertRaises(myokit.ProtocolEventError, create, 0, 0, 1, -1)
        self.assertRaises(myokit.ProtocolEventError, create, 0, 0, 1, 0.5)
        self.assertRaises(myokit.ProtocolEventError, create, 0, 2, 1)
        self.assertRaises(myokit.ProtocolEventError, create, 0, 2, 1, 1)

    def test_protocol_creation(self):
        """
        Tests the basics of creating a protocol
        """
        p = myokit.Protocol()
        self.assertIsNone(p.head())
        p.schedule(1, 10, 0.5, 0, 0)
        f = p.head()
        self.assertEqual(f.level(), 1)
        self.assertEqual(f.start(), 10)
        self.assertEqual(f.duration(), 0.5)
        self.assertEqual(f.period(), 0)
        self.assertEqual(f.multiplier(), 0)

        # Invalid event: period is zero but multiplier is not
        self.assertRaises(
            myokit.ProtocolEventError, p.schedule, 1, 10, 0.5, 0, 10)

        # Add second event
        p.schedule(2, 1, 0.5, 0, 0)
        e = p.head()
        self.assertNotEqual(e, f)
        self.assertEqual(e.level(), 2)
        self.assertEqual(e.start(), 1)
        self.assertEqual(e.duration(), 0.5)
        self.assertEqual(e.period(), 0)
        self.assertEqual(e.multiplier(), 0)

        # Add third event
        p.schedule(3, 100, 0.5, 100, 100)

        # Invalid event: starts simultaneously
        def sim(p, start, duration, period=0, multiplier=0, clash=0):
            self.assertRaises(
                myokit.SimultaneousProtocolEventError,
                p.schedule, 2, start, duration, period, multiplier)
            try:
                p.schedule(2, start, duration, period, multiplier)
            except myokit.SimultaneousProtocolEventError as e:
                m = e.message
                t = m[2 + m.index('t='):-1]
                self.assertEqual(float(t), clash)
        sim(p, 1, 0.5, clash=1)
        sim(p, 10, 0.5, clash=10)
        sim(p, 100, 0.5, clash=100)

    def test_characteristic_time(self):
        """
        Tests characteristic_time determination.
        """
        # Singular event
        e = myokit.ProtocolEvent(1, 100, 0.5, 0, 0)
        self.assertEqual(e.characteristic_time(), 100.5)
        # Finite event
        e = myokit.ProtocolEvent(1, 100, 0.5, 1000, 3)
        self.assertEqual(e.characteristic_time(), 3100)
        # Indefinite event
        e = myokit.ProtocolEvent(1, 100, 0.5, 1000, 0)
        self.assertEqual(e.characteristic_time(), 1000)
        # Delayed indefinite event
        e = myokit.ProtocolEvent(1, 900, 200, 1000, 0)
        self.assertEqual(e.characteristic_time(), 1900)
        # Test protocols
        # Singular event
        p = myokit.Protocol()
        p.schedule(1, 100, 0.5, 0, 0)
        self.assertEqual(p.characteristic_time(), 100.5)
        # Finite event
        p = myokit.Protocol()
        p.schedule(1, 100, 0.5, 1000, 3)
        self.assertEqual(p.characteristic_time(), 3100)
        # Indefinite event
        p = myokit.Protocol()
        p.schedule(1, 100, 0.5, 1000, 0)
        self.assertEqual(p.characteristic_time(), 1000)
        # Delayed indefinite event
        p = myokit.Protocol()
        p.schedule(1, 800, 250, 1000, 0)
        self.assertEqual(p.characteristic_time(), 1800)
        # Sequence of singular events
        p = myokit.Protocol()
        p.schedule(1, 0, 100)
        p.schedule(1, 100, 200)
        p.schedule(1, 300, 300)
        self.assertEqual(p.characteristic_time(), 600)

    def test_pacing_system(self):
        """
        Tests if the pacing systems works correctly.
        """
        # Test basics
        p = myokit.Protocol()
        p.schedule(2, 0, 1, 10, 0)
        s = myokit.PacingSystem(p)
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
        p = myokit.Protocol()
        p.schedule(2, 1, 1, 10, 0)
        s = myokit.PacingSystem(p)
        self.assertEqual(s.time(), 0)
        self.assertEqual(s.next_time(), 1)
        self.assertEqual(s.pace(), 0)
        p = myokit.Protocol()
        s = myokit.PacingSystem(p)
        self.assertEqual(s.time(), 0)
        self.assertEqual(s.next_time(), float('inf'))
        self.assertEqual(s.pace(), 0)

        # Test basic use + log creation methods
        p = myokit.Protocol()
        p.schedule(1, 10, 1, 1000, 0)
        d = p.create_log_for_interval(0, 3000)
        self.assertEqual(d.time(), [0, 10, 11, 1010, 1011, 2010, 2011, 3000])
        d = p.create_log_for_interval(0, 2000, for_drawing=True)
        self.assertEqual(d.time(), [
            0, 10, 10, 11, 11, 1010, 1010, 1011, 1011, 2000])
        p = myokit.Protocol()
        p.schedule(1, 0, 1, 1000, 0)
        d = p.create_log_for_interval(0, 3000)
        self.assertEqual(d.time(), [0, 1, 1000, 1001, 2000, 2001, 3000])
        d = p.create_log_for_interval(0, 2000, for_drawing=True)
        self.assertEqual(d.time(), [0, 1, 1, 1000, 1000, 1001, 1001, 2000])
        if False:
            import matplotlib.pyplot as pl
            pl.figure()
            pl.plot(d.time(), d['pace'])
            pl.show()

        # Test bad interval call
        self.assertRaises(ValueError, p.create_log_for_interval, 100, 0)

        # Test raising of errors on rescheduled events
        p = myokit.Protocol()
        p.schedule(1, 0, 1, 1000)
        p.schedule(1, 3000, 1)
        s = myokit.PacingSystem(p)
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
        try:
            s.advance(t)
        except myokit.SimultaneousProtocolEventError as e:
            m = e.message
            self.assertEqual(float(m[2 + m.index('t='):-1]), 3000)

    def test_create_log_for_times(self):
        """
        Tests the method Protocol.create_log_for_times()
        """
        p = myokit.Protocol()
        #          level, self.characteristic_time(), duration
        p.schedule(2, 10, 100, 1000, 2)

        t = [0, 9.999, 10, 10.001, 109.999, 110, 110.001, 1000, 1009.99, 1010,
             1110, 2000, 2020]
        v = [0, 0, 2, 2, 2, 0, 0, 0, 0, 2, 0, 0, 0]
        d = p.create_log_for_times(t)
        self.assertEqual(len(d), 2)
        self.assertIn('time', d)
        self.assertIn('pace', d)
        self.assertEqual(d.time(), t)
        self.assertEqual(d['pace'], v)

    def test_guess_duration(self):
        """
        Deprecated method.
        """
        p = myokit.Protocol()
        self.assertEqual(p.characteristic_time(), p.guess_duration())

    def test_event_based_pacing_ansic(self):
        """
        Tests the Ansi-C event-based pacing system.
        """
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
        # Test basic use + log creation methods
        p = myokit.Protocol()
        p.schedule(1, 10, 1, 1000, 0)
        d = AnsicEventBasedPacing.create_log_for_interval(p, 0, 3000)
        self.assertEqual(d.time(), [0, 10, 11, 1010, 1011, 2010, 2011, 3000])
        d = AnsicEventBasedPacing.create_log_for_interval(
            p, 0, 2000, for_drawing=True)
        self.assertEqual(d.time(), [
            0, 10, 10, 11, 11, 1010, 1010, 1011, 1011, 2000])
        p = myokit.Protocol()
        p.schedule(1, 0, 1, 1000, 0)
        d = AnsicEventBasedPacing.create_log_for_interval(p, 0, 3000)
        self.assertEqual(d.time(), [0, 1, 1000, 1001, 2000, 2001, 3000])
        d = AnsicEventBasedPacing.create_log_for_interval(
            p, 0, 2000, for_drawing=True)
        self.assertEqual(d.time(), [0, 1, 1, 1000, 1000, 1001, 1001, 2000])
        # Test raising of errors on rescheduled events
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

    def test_fixed_form_pacing_ansic(self):
        """
        Tests the Ansi-C fixed-form pacing system.
        """
        if False:
            # Graphical test, just for playing with the pacing system
            m, p, x = myokit.load('example')
            s = myokit.Simulation(m, p)
            d = s.run(500).npview()
            # Get time and voltage
            t = d.time()
            v = d['membrane.V']
            # Plot trace
            import matplotlib.pyplot as pl
            pl.figure()
            pl.plot(t, v, 'x')
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
            pl.plot(t2, v2, '.', color='green')
            pl.show()
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
        values = range(len(times))
        pacing = AnsicFixedFormPacing(times, values)

        def test(value, index):
            self.assertEquals(pacing.pace(value), index)

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
