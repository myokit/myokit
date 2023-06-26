#!/usr/bin/env python3
#
# Tests the pure Python implementation of the Pacing System
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import unittest

import myokit


class EventBasedPacingPythonTest(unittest.TestCase):
    """
    Tests the pure python PacingSystem class.
    """
    def test_with_event_at_t_0(self):
        # Test with event starting at t=0

        p = myokit.Protocol()
        # schedule(level, start, duration, period, multiplier)
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
        self.assertRaisesRegex(ValueError, 'cannot be before', s.advance, 0)

    def test_with_event_at_t_1(self):
        # Test with event starting at t=1
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

    def test_simultaneous_event_error(self):
        # Test raising of errors on rescheduled periodic events

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
        with self.assertRaises(myokit.SimultaneousProtocolEventError) as e:
            s.advance(t)
        m = str(e.exception)
        self.assertEqual(float(m[2 + m.index('t='):-1]), 3000)

    def test_negative_time(self):
        # Test starting from a negative time

        p = myokit.pacing.blocktrain(level=1, duration=1, period=2)
        s = myokit.PacingSystem(p, initial_time=-100)
        self.assertEqual(s.time(), -100)
        self.assertEqual(s.next_time(), 0)
        self.assertEqual(s.pace(), 0)

        p = myokit.pacing.blocktrain(level=1, duration=1, period=2, offset=1)
        s = myokit.PacingSystem(p, initial_time=-100)
        self.assertEqual(s.time(), -100)
        self.assertEqual(s.next_time(), 1)
        self.assertEqual(s.pace(), 0)
        s.advance(s.next_time())
        self.assertEqual(s.time(), 1)
        self.assertEqual(s.pace(), 1)


if __name__ == '__main__':
    unittest.main()
