#!/usr/bin/env python3
#
# Tests the C implementation of the Pacing System
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import unittest

import myokit
from myokit.tests.ansic_event_based_pacing import AnsicEventBasedPacing
from myokit.tests.ansic_time_series_pacing import AnsicTimeSeriesPacing


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
        self.assertTrue(s.next_time() > 1e123)
        self.assertEqual(s.pace(), 0)

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

    def test_negative_time(self):
        # Test starting from a negative time

        p = myokit.pacing.blocktrain(level=1, duration=1, period=2)
        s = AnsicEventBasedPacing(p, initial_time=-100)
        self.assertEqual(s.time(), -100)
        self.assertEqual(s.next_time(), 0)
        self.assertEqual(s.pace(), 0)

        p = myokit.pacing.blocktrain(level=1, duration=1, period=2, offset=1)
        s = AnsicEventBasedPacing(p, initial_time=-100)
        self.assertEqual(s.time(), -100)
        self.assertEqual(s.next_time(), 1)
        self.assertEqual(s.pace(), 0)
        s.advance(s.next_time())
        self.assertEqual(s.time(), 1)
        self.assertEqual(s.pace(), 1)


class TimeSeriesPacingAnsicTest(unittest.TestCase):
    """
    Test the Ansi-C time-series pacing system (aka point-list, aka data-clamp).
    """
    def test_time_series_pacing_ansic(self):
        # Tests if the basics work

        # Test with small lists
        times = [0, 0, 1, 1, 1, 2, 2, 2, 3, 4, 5, 7]
        values = list(range(len(times)))
        pacing = AnsicTimeSeriesPacing(
            myokit.TimeSeriesProtocol(times, values))

        self.assertEqual(pacing.pace(-1), 0)
        self.assertEqual(pacing.pace(0), 1)
        self.assertEqual(pacing.pace(1), 2)
        self.assertEqual(pacing.pace(2), 5)
        self.assertEqual(pacing.pace(3), 8)
        self.assertEqual(pacing.pace(4), 9)
        self.assertEqual(pacing.pace(5), 10)
        self.assertEqual(pacing.pace(7), 11)
        self.assertEqual(pacing.pace(8), 11)
        self.assertEqual(pacing.pace(1.5), 4.5)
        self.assertEqual(pacing.pace(1.75), 4.75)
        self.assertEqual(pacing.pace(6), 10.5)
        self.assertEqual(pacing.pace(5.5), 10.25)

        # Test not starting at 0
        times = [1, 2]
        values = [10, 20]
        pacing = AnsicTimeSeriesPacing(
            myokit.TimeSeriesProtocol(times, values))

        self.assertEqual(pacing.pace(-1), 10)
        self.assertEqual(pacing.pace(0), 10)
        self.assertEqual(pacing.pace(1), 10)
        self.assertEqual(pacing.pace(2), 20)
        self.assertEqual(pacing.pace(3), 20)
        self.assertEqual(pacing.pace(1.5), 15)


if __name__ == '__main__':
    unittest.main()
