#!/usr/bin/env python3
#
# Tests protocol creation and pacing
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import pickle
import unittest

import myokit

from myokit.tests import WarningCollector

# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp


class ProtocolTest(unittest.TestCase):
    """
    Tests the Protocol class.
    """

    def test_characteristic_time(self):
        # Test characteristic_time determination.

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

    def test_clone(self):
        # Test cloning

        p1 = myokit.Protocol()
        p1.schedule(1, 0, 100)
        p1.schedule(1, 100, 200, 1000, 10)
        p1.schedule(1, 300, 300, 2000)
        p2 = p1.clone()
        self.assertEqual(p1, p2)

    def test_equals(self):
        # Test protocol equality checking

        p1 = myokit.Protocol()
        p2 = myokit.Protocol()
        self.assertEqual(p1, p2)

        p1.schedule(1, 0, 100)
        self.assertNotEqual(p1, p2)
        p2.schedule(1, 0, 100)
        self.assertEqual(p1, p2)

        p1.schedule(1, 100, 200, 1000, 10)
        p1.schedule(1, 300, 300, 2000)
        self.assertNotEqual(p1, p2)
        p2.schedule(1, 100, 200, 1000, 10)
        p2.schedule(1, 300, 300, 2000)
        self.assertEqual(p1, p2)

        self.assertNotEqual(p1, None)
        self.assertNotEqual(p1, 17)
        self.assertNotEqual(p1, p1.code())
        self.assertEqual(p1, p1)

    def test_event_creation(self):
        # Test creating events.

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

    def test_in_words(self):
        # Test :meth:`Protocol.in_words()`.

        p = myokit.Protocol()
        self.assertEqual(p.in_words(), 'Empty protocol.')

        p = myokit.Protocol()
        p.schedule(2, 10, 100, 1000, 2)
        self.assertEqual(
            p.in_words(),
            'Stimulus of 2.0 times the normal level applied at t=10.0, '
            'lasting 100.0 and occurring 2 times with a period of 1000.0.')

        p = myokit.Protocol()
        p.schedule(2, 10, 100, 1000, 0)
        self.assertEqual(
            p.in_words(),
            'Stimulus of 2.0 times the normal level applied at t=10.0,'
            ' lasting 100.0 and recurring indefinitely'
            ' with a period of 1000.0.')
        self.assertEqual(p.in_words(), str(p.tail()))

        p = myokit.Protocol()
        p.schedule(2, 10, 100, 1000, 0)
        p.schedule(2, 300, 100, 1000, 0)
        self.assertEqual(
            p.in_words(),
            'Stimulus of 2.0 times the normal level applied at t=10.0,'
            ' lasting 100.0 and recurring indefinitely'
            ' with a period of 1000.0.\n'
            'Stimulus of 2.0 times the normal level applied at t=300.0,'
            ' lasting 100.0 and recurring indefinitely'
            ' with a period of 1000.0.')

    def test_is_infinite(self):
        # Tests :meth:`Protocol.is_infinite()

        p = myokit.Protocol()
        self.assertFalse(p.is_infinite())

        p = myokit.Protocol()
        p.schedule(2, 10, 100, 1000, 2)
        self.assertFalse(p.is_infinite())

        p = myokit.Protocol()
        p.schedule(2, 10, 100, 1000, 2)
        p.schedule(2, 1, 1, 1000, 0)
        self.assertTrue(p.is_infinite())

    def test_is_sequence(self):
        # Tests :meth:`Protocol.is_sequence()

        p = myokit.Protocol()
        self.assertTrue(p.is_sequence())
        self.assertTrue(p.is_sequence_exception())
        self.assertTrue(p.is_unbroken_sequence())
        self.assertTrue(p.is_unbroken_sequence_exception())

        # First event is periodic
        p = myokit.Protocol()
        p.schedule(2, 10, 100, 1000, 2)
        self.assertFalse(p.is_sequence())
        self.assertRaisesRegex(
            Exception, 'contains periodic', p.is_sequence_exception)
        self.assertFalse(p.is_unbroken_sequence())
        self.assertRaisesRegex(
            Exception, 'contains periodic', p.is_unbroken_sequence_exception)

        # Second event is periodic
        p = myokit.Protocol()
        p.schedule(2, 10, 100, 0, 0)
        p.schedule(20, 100, 100, 1000, 1000)
        self.assertFalse(p.is_sequence())
        self.assertRaisesRegex(
            Exception, 'contains periodic', p.is_sequence_exception)
        self.assertFalse(p.is_unbroken_sequence())
        self.assertRaisesRegex(
            Exception, 'contains periodic', p.is_unbroken_sequence_exception)

        # Multiple periodic events
        p = myokit.Protocol()
        p.schedule(2, 10, 100, 1000, 2)
        p.schedule(2, 1, 1, 1000, 0)
        self.assertFalse(p.is_sequence())
        self.assertRaisesRegex(
            Exception, 'contains periodic', p.is_sequence_exception)
        self.assertFalse(p.is_unbroken_sequence())
        self.assertRaisesRegex(
            Exception, 'contains periodic', p.is_unbroken_sequence_exception)

        # Overlapping events
        p = myokit.Protocol()
        p.schedule(2, 10, 100, 0, 0)
        p.schedule(2, 12, 1, 0, 0)
        p.schedule(2, 420, 1, 0, 0)
        self.assertFalse(p.is_sequence())
        self.assertRaisesRegex(
            Exception, 'overlap', p.is_sequence_exception)
        self.assertFalse(p.is_unbroken_sequence())
        self.assertRaisesRegex(
            Exception, 'overlap', p.is_unbroken_sequence_exception)

        # Non-overlapping events
        p = myokit.Protocol()
        p.schedule(2, 10, 100, 0, 0)
        p.schedule(2, 120, 1, 0, 0)
        p.schedule(2, 420, 1, 0, 0)
        self.assertTrue(p.is_sequence())
        self.assertTrue(p.is_sequence_exception())
        self.assertFalse(p.is_unbroken_sequence())
        self.assertRaisesRegex(
            Exception, 'start directly afte', p.is_unbroken_sequence_exception)

        # Unbroken sequence
        p = myokit.Protocol()
        p.schedule(2, 10, 100, 0, 0)
        p.schedule(2, 110, 310, 0, 0)
        p.schedule(2, 420, 1, 0, 0)
        self.assertTrue(p.is_sequence())
        self.assertTrue(p.is_sequence_exception())
        self.assertTrue(p.is_unbroken_sequence())
        self.assertTrue(p.is_unbroken_sequence_exception())

    def test_levels(self):
        # Tests :meth:`Protocol.levels()

        p = myokit.Protocol()
        p.schedule(2, 10, 100, 0, 0)
        p.schedule(3, 110, 310, 0, 0)
        p.schedule(1, 420, 1, 0, 0)
        self.assertTrue(p.is_unbroken_sequence())
        self.assertEqual(p.levels(), [2, 3, 1])

    def test_log_for_interval(self):
        # Tests the method Protocol.log_for_interval()
        # Relies on PacingSystem

        debug = False

        # Test basic use + log creation methods
        p = myokit.Protocol()
        p.schedule(1, 10, 1, 1000, 0)
        d = p.log_for_interval(0, 3000)
        self.assertEqual(d.time(), [0, 10, 11, 1010, 1011, 2010, 2011, 3000])
        d = p.log_for_interval(0, 2000, for_drawing=True)
        if debug:
            import matplotlib.pyplot as plt
            plt.figure()
            plt.plot(d.time(), d['pace'])
            plt.show()
        self.assertEqual(d.time(), [
            0, 10, 10, 11, 11, 1010, 1010, 1011, 1011, 2000])
        p = myokit.Protocol()
        p.schedule(1, 0, 1, 1000, 0)
        d = p.log_for_interval(0, 3000)
        self.assertEqual(d.time(), [0, 1, 1000, 1001, 2000, 2001, 3000])
        d = p.log_for_interval(0, 2000, for_drawing=True)
        if debug:
            import matplotlib.pyplot as plt
            plt.figure()
            plt.plot(d.time(), d['pace'])
            plt.show()
        self.assertEqual(
            d.time(), [0, 1, 1, 1000, 1000, 1001, 1001, 2000, 2000])

        # Test bad interval call
        self.assertRaises(ValueError, p.log_for_interval, 100, 0)

        # Test deprecated alias
        with WarningCollector() as w:
            p.create_log_for_interval(0, 2000, for_drawing=True)
        self.assertIn('deprecated', w.text())

    def test_log_for_times(self):
        # Test the method Protocol.log_for_times()
        # Relies on PacingSystem

        p = myokit.Protocol()
        p.schedule(2, 10, 100, 1000, 2)

        t = [0, 9.999, 10, 10.001, 109.999, 110, 110.001, 1000, 1009.99, 1010,
             1110, 2000, 2020]
        v = [0, 0, 2, 2, 2, 0, 0, 0, 0, 2, 0, 0, 0]
        d = p.log_for_times(t)
        self.assertEqual(len(d), 2)
        self.assertIn('time', d)
        self.assertIn('pace', d)
        self.assertEqual(d.time(), t)
        self.assertEqual(d['pace'], v)

        # Empty times
        d = p.log_for_times([])
        self.assertEqual(len(d.time()), 0)
        self.assertEqual(len(d['pace']), 0)

        # Deprecated alias
        with WarningCollector() as w:
            p.create_log_for_times([])
        self.assertIn('deprecated', w.text())

    def test_pickling(self):
        # Test protocol pickling

        p1 = myokit.Protocol()
        p1.schedule(1, 0, 100)
        p1.schedule(1, 100, 200, 1000, 10)
        p1.schedule(1, 300, 300, 2000)

        p_bytes = pickle.dumps(p1)
        p2 = pickle.loads(p_bytes)
        self.assertEqual(p1, p2)

    def test_protocol_creation(self):
        # Test the basics of creating a protocol
        p = myokit.Protocol()
        self.assertIsNone(p.head())
        p.schedule(1, 10, 0.5, 0, 0)
        f = p.head()
        self.assertEqual(f.level(), 1)
        self.assertEqual(f.start(), 10)
        self.assertEqual(f.duration(), 0.5)
        self.assertEqual(f.period(), 0)
        self.assertEqual(f.multiplier(), 0)
        self.assertEqual(f.stop(), 10.5)

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
            with self.assertRaises(myokit.SimultaneousProtocolEventError) as e:
                p.schedule(2, start, duration, period, multiplier)
            m = str(e.exception)
            t = m[2 + m.index('t='):-1]
            self.assertEqual(float(t), clash)
        sim(p, 1, 0.5, clash=1)
        sim(p, 10, 0.5, clash=10)
        sim(p, 100, 0.5, clash=100)

    def test_protocol_to_string(self):
        # Tests str(protocol)
        p = myokit.Protocol()
        p.schedule(2, 10, 100, 0, 0)
        p.schedule(3, 110, 310, 0, 0)
        p.schedule(1, 420, 1, 0, 0)
        self.assertEqual(p.code(), str(p))

    def test_range(self):
        # Tests :meth:`Protocol.range()
        p = myokit.Protocol()
        self.assertEqual(p.range(), (0, 0))

        p = myokit.Protocol()
        p.schedule(2, 10, 100, 0, 0)
        p.schedule(3, 110, 310, 0, 0)
        p.schedule(1, 420, 1, 0, 0)
        self.assertTrue(p.is_unbroken_sequence())
        self.assertEqual(p.range(), (0, 3))

        p = myokit.Protocol()
        p.schedule(2, 0, 110, 0, 0)
        p.schedule(3, 110, 310, 0, 0)
        p.schedule(1, 420, 1, 0, 0)
        self.assertTrue(p.is_unbroken_sequence())
        self.assertEqual(p.range(), (1, 3))

    def test_tail(self):
        # Tests Protocol.tail() which returns the final protocol event

        p = myokit.Protocol()
        p.schedule(2, 10, 100, 0, 0)
        p.schedule(3, 110, 310, 0, 0)
        p.schedule(1, 420, 1, 0, 0)
        self.assertEqual(p.tail().start(), 420)

        p = myokit.Protocol()
        p.schedule(1, 420, 1, 0, 0)
        p.schedule(2, 10, 100, 0, 0)
        p.schedule(3, 110, 310, 0, 0)
        self.assertEqual(p.tail().start(), 420)

    def test_value_at_times(self):
        # Test the method Protocol.value_at_times()
        # Relies on PacingSystem

        p = myokit.Protocol()
        p.schedule(2, 10, 100, 1000, 2)
        t = [0, 9.999, 10, 10.001, 109.999, 110, 110.001, 1000, 1009.99, 1010,
             1110, 2000, 2020]
        v = [0, 0, 2, 2, 2, 0, 0, 0, 0, 2, 0, 0, 0]
        self.assertEqual(v, p.value_at_times(t))

        # Empty times
        d = p.log_for_times([])
        self.assertEqual(len(p.value_at_times([])), 0)

        # Decreasing times
        self.assertRaisesRegex(
            ValueError, 'non-decreasing', p.value_at_times, [1, 0])

        # Negative times
        self.assertRaisesRegex(
            ValueError, 'negative', p.value_at_times, [-1, 0])


if __name__ == '__main__':
    import warnings
    warnings.simplefilter('always')
    unittest.main()
