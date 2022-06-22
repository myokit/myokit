#!/usr/bin/env python3
#
# Tests the methods and classes in myokit.tools
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import os
import re
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

from myokit.tests import TemporaryDirectory


class BenchmarkerTest(unittest.TestCase):
    """Tests the ``Benchmarker``."""

    def test_time(self):
        # Test benchmarker.time()

        b = myokit.tools.Benchmarker()
        x = [0] * 1000
        t0 = b.time()
        self.assertTrue(t0 >= 0)
        x = [0] * 1000
        t1 = b.time()
        self.assertTrue(t1 >= t0)
        x = [0] * 1000
        t2 = b.time()
        self.assertTrue(t2 >= t1)
        for i in range(1000):
            x = [0] * 1000
        t3 = b.time()
        self.assertTrue(t3 >= t2)
        b.reset()
        t4 = b.time()
        self.assertTrue(t4 < t3)

    def test_format(self):
        # Test benchmarker.format()

        b = myokit.tools.Benchmarker()
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
        self.assertEqual(b.format()[-8:], ' seconds')

    def test_print(self):
        # Test benchmarker.print

        messages = [
            'Hello',
            'Yes yes',
            'Line 3',
        ]
        with myokit.tools.capture() as c:
            b = myokit.tools.Benchmarker()
            self.assertEqual(c.out(), '')
            self.assertEqual(c.err(), '')
            for m in messages:
                b.print(m)
        self.assertEqual(c.err(), '')
        lines = c.out().splitlines()
        self.assertEqual(len(lines), 3)

        r = re.compile(r'\[[ 0-9]+ us \([ 0-9]+ us\)\] ([ a-zA-Z0-9]+)')
        for line, msg in zip(lines, messages):
            m = r.match(line)
            self.assertIsNotNone(m)
            self.assertEqual(m.group(1), msg)


class CaptureTest(unittest.TestCase):
    """Test the ``capture`` context manager."""

    def test_capture_disabled(self):
        # Tests creating a capture manager that doesn't capture.

        with myokit.tools.capture(enabled=True) as p:
            with myokit.tools.capture(enabled=False) as q:
                print('2', end='')
                print('b', end='', file=sys.stderr)
                print('f', end='', file=sys.stderr)
            print('7', end='')
            print('g', end='', file=sys.stderr)

        self.assertEqual(p.out(), '27')
        self.assertEqual(p.err(), 'bfg')
        self.assertEqual(q.out(), '')
        self.assertEqual(q.err(), '')

    def test_capture_nested(self):
        # Tests capturing in a nested pattern.
        r = myokit.tools.capture(False)
        q = myokit.tools.capture(True)
        self.assertEqual(r.out(), '')
        self.assertEqual(r.err(), '')
        with myokit.tools.capture(False) as p:
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
                    with myokit.tools.capture(True) as s:
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
        # Tests capturing in a nested pattern with repeated enters/exits.
        x = myokit.tools.capture()
        y = myokit.tools.capture(True)
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
        # Tests capturing with threading.

        # Sleep times for each thread. Duration doesn't matter much, as will be
        # executed sequentially. But choose so that interlacing would occur if
        # not.
        times = [0.2, 0.01, 0.05]
        captured = [None, None, None]

        # Function to call inside threads
        def f(i):
            with myokit.tools.capture() as c:
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


class ToolsTest(unittest.TestCase):
    """Tests various tools in myokit.tools"""

    def test_format_path(self):
        # Test format_path().
        fp = myokit.tools.format_path

        # Normal use
        self.assertEqual(
            fp(os.path.join('a', 'b', 'c')), os.path.join('a', 'b', 'c'))

        # No trailing slash
        self.assertEqual(fp('a'), 'a')
        self.assertEqual(fp('a/b/'), os.path.join('a', 'b'))

        # Use with custom root
        root = os.path.join(os.path.abspath('.'), 'a')
        self.assertEqual(
            fp(os.path.join(root, 'b', 'c'), root), os.path.join('b', 'c'))

        # Empty path
        self.assertEqual(fp(''), '.')
        self.assertEqual(fp('.'), '.')

        # Filesystem root
        self.assertEqual(fp('/'), os.path.abspath('/'))
        self.assertEqual(fp('/', root='/'), '.')

        # Path outside of root
        self.assertEqual(
            fp(os.path.abspath('test'), os.path.abspath('test/tost')),
            os.path.abspath('test'))

    def test_levenshtein_distance(self):
        # Test the levenshtein distance method.
        self.assertEqual(myokit.tools.lvsd('kitten', 'sitting'), 3)
        self.assertEqual(myokit.tools.lvsd('sitting', 'kitten'), 3)
        self.assertEqual(myokit.tools.lvsd('saturday', 'sunday'), 3)
        self.assertEqual(myokit.tools.lvsd('sunday', 'saturday'), 3)
        self.assertEqual(myokit.tools.lvsd('michael', 'jennifer'), 7)
        self.assertEqual(myokit.tools.lvsd('jennifer', 'michael'), 7)
        self.assertEqual(myokit.tools.lvsd('jennifer', ''), 8)
        self.assertEqual(myokit.tools.lvsd('', 'jennifer'), 8)
        self.assertEqual(myokit.tools.lvsd('', ''), 0)

    def test_natural_sort_key(self):
        # Test natural sort key method.

        a = ['a12', 'a3', 'a11', 'a2', 'a10', 'a1']
        b = ['a1', 'a2', 'a3', 'a10', 'a11', 'a12']
        self.assertNotEqual(a, b)
        a.sort()
        self.assertNotEqual(a, b)
        a.sort(key=myokit.tools.natural_sort_key)
        self.assertEqual(a, b)

    def test_rmtree(self):
        # Test rmtree

        with TemporaryDirectory() as d:

            # Create dir with subdir
            path = d.path('a')
            os.mkdir(path)
            os.mkdir(os.path.join(path, 'b'))

            # This can't be deleted with rmdir
            self.assertRaises(OSError, os.rmdir, path)
            self.assertTrue(os.path.exists(path))

            # But rmtree works
            myokit.tools.rmtree(path)
            self.assertFalse(os.path.exists(path))

            # It doesn't work twice in a row:
            self.assertRaises(OSError, myokit.tools.rmtree, path)

            # But we can ignore the exception
            myokit.tools.rmtree(path, silent=True)


if __name__ == '__main__':
    unittest.main()
