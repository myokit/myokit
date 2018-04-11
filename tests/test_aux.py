#!/usr/bin/env python
#
# Tests the myokit._aux module.
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import sys
import unittest

import myokit

#from shared import TemporaryDirectory


class AuxText(unittest.TestCase):
    """
    Tests various methods from myokit._aux.
    """
    def test_date(self):
        """ Test date formatting method. """
        import time
        for i in range(3):
            a = time.strftime(myokit.DATE_FORMAT)
            b = myokit._aux.date()
            if a == b:
                break
        self.assertEqual(a, b)

    def test_time(self):
        """ Test time formatting method. """
        import time
        for i in range(3):
            a = time.strftime(myokit.TIME_FORMAT)
            b = myokit._aux.time()
            if a == b:
                break
        self.assertEqual(a, b)

    def test_natural_sort(self):
        """ Test natural sort key method. """
        a = ['a12', 'a3', 'a11', 'a2', 'a10', 'a1']
        b = ['a1', 'a2', 'a3', 'a10', 'a11', 'a12']
        self.assertNotEqual(a, b)
        a.sort()
        self.assertNotEqual(a, b)
        a.sort(key=lambda x: myokit.natural_sort_key(x))
        self.assertEqual(a, b)

    def test_benchmarker(self):
        """ Tests the benchmarker. """
        b = myokit.Benchmarker()
        t0 = b.time()
        self.assertTrue(t0 >= 0)
        t1 = b.time()
        self.assertTrue(t1 >= t0)
        t2 = b.time()
        self.assertTrue(t2 >= t1)
        t3 = b.time()
        self.assertTrue(t3 >= t2)
        b.reset()
        t4 = b.time()
        self.assertTrue(t4 < t3)

        self.assertEqual(b.format(1), '1 second')
        self.assertEqual(b.format(61), '1 minute, 1 second')
        self.assertEqual(b.format(60), '1 minute, 0 seconds')
        self.assertEqual(b.format(180), '3 minutes, 0 seconds')
        self.assertEqual(b.format(3600), '1 hour, 0 minutes, 0 seconds')
        self.assertEqual(b.format(3661), '1 hour, 1 minute, 1 second')
        self.assertEqual(
            b.format(3600 * 24), '1 day, 0 hours, 0 minutes, 0 seconds')
        self.assertEqual(
            b.format(3600 * 24 * 7),
            '1 week, 0 days, 0 hours, 0 minutes, 0 seconds')

    def test_py_capture(self):
        """ Tests the PyCapture method. """
        # Test basic use
        with myokit.PyCapture() as c:
            print('Hello')
            self.assertEqual(c.text(), 'Hello\n')
            sys.stdout.write('Test')
        self.assertEqual(c.text(), 'Hello\nTest')

        # Test wrapping
        with myokit.PyCapture() as c:
            print('Hello')
            self.assertEqual(c.text(), 'Hello\n')
            with myokit.PyCapture() as d:
                print('Yes')
            self.assertEqual(d.text(), 'Yes\n')
            sys.stdout.write('Test')
        self.assertEqual(c.text(), 'Hello\nTest')

        # Test disabling / enabling
        with myokit.PyCapture() as c:
            print('Hello')
            self.assertEqual(c.text(), 'Hello\n')
            with myokit.PyCapture() as d:
                sys.stdout.write('Yes')
                d.disable()
                print('Hmmm')
                d.enable()
                print('No')
            self.assertEqual(d.text(), 'YesNo\n')
            sys.stdout.write('Test')
        self.assertEqual(c.text(), 'Hello\nHmmm\nTest')


if __name__ == '__main__':
    unittest.main()
