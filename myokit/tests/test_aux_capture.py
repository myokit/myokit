#!/usr/bin/env python3
#
# Tests the capture methods in myokit._aux
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import sys
import threading
import time
import unittest

# Strings in Python2 and Python3
try:
    basestring
except NameError:   # pragma: no cover
    basestring = str

import myokit


class AuxCaptureTest(unittest.TestCase):
    """
    Test the capture methods in myokit.aux
    """

    def test_capture_nested(self):
        """Tests capturing in a nested pattern."""
        r = myokit.capture(False)
        q = myokit.capture(True)
        self.assertEqual(r.out(), '')
        self.assertEqual(r.err(), '')
        with myokit.capture(False) as p:
            self.assertEqual(p.out(), '')
            self.assertEqual(p.err(), '')
            print('1', end='')
            print('a', end='', file=sys.stderr)
            with q:
                print('2', end='')
                print('b', end='', file=sys.stderr)
                with r:
                    print('3', end='')
                    print('c', end='', file=sys.stderr)
                    with myokit.capture(True) as s:
                        print('4', end='')
                        print('d', end='', file=sys.stderr)
                    print('5', end='')
                    print('e', end='', file=sys.stderr)
                print('6', end='')
                print('f', end='', file=sys.stderr)
            print('7', end='')
            print('g', end='', file=sys.stderr)

        # Check captured text
        self.assertEqual(p.out(), '17')
        self.assertEqual(p.err(), 'ag')
        self.assertEqual(p.text(), '17ag')

        self.assertEqual(q.out(), '26')
        self.assertEqual(q.err(), 'bf')
        self.assertEqual(q.text(), '26bf')

        self.assertEqual(r.out(), '35')
        self.assertEqual(r.err(), 'ce')
        self.assertEqual(r.text(), '35ce')

        self.assertEqual(s.out(), '4')
        self.assertEqual(s.err(), 'd')
        self.assertEqual(s.text(), '4d')

    def test_capture_repeated_use(self):
        """Tests capturing in a nested pattern with repeated enters/exits."""
        x = myokit.capture()
        y = myokit.capture(True)
        self.assertEqual(x.out(), '')
        with x:
            print('1', end='')
            print('a', end='', file=sys.stderr)
            self.assertEqual(x.out(), '')
            with y:
                print('2', end='')
                print('b', end='', file=sys.stderr)
                with x:
                    print('3', end='')
                    print('c', end='', file=sys.stderr)
                    with y:
                        print('4', end='')
                        print('d', end='', file=sys.stderr)
                    print('5', end='')
                    print('e', end='', file=sys.stderr)
                print('6', end='')
                print('f', end='', file=sys.stderr)
            print('7', end='')
            print('g', end='', file=sys.stderr)

        # Check captured text
        self.assertEqual(x.out(), '17')
        self.assertEqual(x.err(), 'ag')
        self.assertEqual(x.text(), '17ag')

        self.assertEqual(y.out(), '23456')
        self.assertEqual(y.err(), 'bcdef')
        self.assertEqual(y.text(), '23456bcdef')

        with x:
            print('hey')
            print('ya', file=sys.stderr)
        self.assertEqual(x.out(), 'hey\n')
        self.assertEqual(x.err(), 'ya\n')

        with y:
            print('foo')
            print('bar', file=sys.stderr)
        self.assertEqual(y.out(), 'foo\n')
        self.assertEqual(y.err(), 'bar\n')

    def test_capture_with_threads(self):
        """Tests capturing with threading."""

        # Sleep times for each thread. Duration doesn't matter much, as will be
        # executed sequentially. But choose so that interlacing would occur if
        # not.
        times = [0.2, 0.01, 0.05]
        captured = [None, None, None]

        # Function to call inside threads
        def f(i):
            with myokit.capture() as c:
                print(str(i) + 'a ', end='')
                time.sleep(times[i])
                print(str(i) + 'b ', end='')
                print(str(i) + 'e ', end='', file=sys.stderr)
            captured[i] = c.text().strip()

        # Call function from threads
        ps = []
        for i in range(len(times)):
            p = threading.Thread(target=f, args=(i,))
            ps.append(p)
        for p in ps:
            p.start()
            time.sleep(0.01)
        for p in ps:
            if p.is_alive():
                p.join()

        # Check captured output
        self.assertEqual(len(captured), 3)
        self.assertEqual(captured[0], '0a 0b 0e')
        self.assertEqual(captured[1], '1a 1b 1e')
        self.assertEqual(captured[2], '2a 2b 2e')


if __name__ == '__main__':
    unittest.main()
