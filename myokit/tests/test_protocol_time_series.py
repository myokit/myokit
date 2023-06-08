#!/usr/bin/env python3
#
# Tests the time series protocol class
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import unittest
import pickle

import myokit


class TimeSeriesProtocolTest(unittest.TestCase):
    """
    Tests the TimeSeriesProtocol class.
    """

    def test_eq(self):
        # Equality testing
        p1 = myokit.TimeSeriesProtocol([1, 2], [2, 4])
        p2 = myokit.TimeSeriesProtocol([1, 2], [2, 4])
        self.assertEqual(p1, p2)
        self.assertNotEqual(p1, 1)
        self.assertEqual(p1, p1)

    def test_pickle(self):
        # Pickling and unpickling
        p1 = myokit.TimeSeriesProtocol([1, 2], [2, 4])
        p2 = pickle.loads(pickle.dumps(p1))
        self.assertEqual(p1, p2)

    def test_constructor(self):
        p = myokit.TimeSeriesProtocol([1], [2])
        self.assertEqual(p.times(), [1])
        self.assertEqual(p.values(), [2])

        p = myokit.TimeSeriesProtocol([1, 2], [1, 2])
        self.assertEqual(p.times(), [1, 2])
        self.assertEqual(p.values(), [1, 2])

        p = myokit.TimeSeriesProtocol([2, 1], [2, 1])
        self.assertEqual(p.times(), [1, 2])
        self.assertEqual(p.values(), [1, 2])

        self.assertRaises(  # No specific error from class!!
            TypeError, myokit.TimeSeriesProtocol, 1, 2)
        self.assertRaisesRegex(
            ValueError, 'same size', myokit.TimeSeriesProtocol, [1, 2], [2])
        self.assertRaisesRegex(
            ValueError, 'nknown interpolation', myokit.TimeSeriesProtocol,
            [1, 2], [2, 4], method='cubic'
        )

    def test_values(self):
        values = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        times = [0, 0, 1, 1, 1, 2, 2, 2, 3, 4, 5, 7]
        values = list(range(len(times)))
        pacing = myokit.TimeSeriesProtocol(times, values)

        def test(value, index):
            self.assertEqual(pacing.pace(value), index)

        test(-1, 0)
        test(0, 1)
        test(1, 4)
        test(2, 7)
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
    import warnings
    warnings.simplefilter('always')
    unittest.main()
