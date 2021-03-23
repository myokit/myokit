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

    def test_streamcapture_interlaced(self):
        """
        Tests using multiple StreamCapture objects, starting and stopping in an
        interlaced pattern.
        """
        x = myokit.StreamCapture()
        y = myokit.StreamCapture()
        z = myokit.StreamCapture()

        # Enable x
        x.start()
        print('1', end='', file=sys.stdout)
        print('a', end='', file=sys.stderr)
        # Enable y
        y.start()
        print('b', end='', file=sys.stderr)
        print('2', end='', file=sys.stdout)
        # Enable z
        z.start()
        print('3', end='', file=sys.stdout)
        print('c', end='', file=sys.stderr)
        # Disable y
        y.stop()
        print('d', end='', file=sys.stderr)
        print('4', end='', file=sys.stdout)
        # Disable x
        x.stop()
        print('5', end='', file=sys.stdout)
        print('e', end='', file=sys.stderr)
        # Disable z
        z.stop()

        # Check captured text
        self.assertEqual(x.out(), '1234')
        self.assertEqual(x.err(), 'abcd')
        self.assertEqual(y.out(), '23')
        self.assertEqual(y.err(), 'bc')
        self.assertEqual(z.out(), '345')
        self.assertEqual(z.err(), 'cde')
        self.assertEqual(z.text(), '345cde')

        # Check type in Python 2
        self.assertIsInstance(z.text(), basestring)

    def test_streamcapture_nested(self):
        """
        Tests using multiple StreamCapture objects, starting and stopping in a
        nested pattern.
        """
        x = myokit.StreamCapture()
        y = myokit.StreamCapture()
        z = myokit.StreamCapture()

        # Enable x
        self.assertEqual(x.out(), '')
        self.assertEqual(x.err(), '')
        x.start()
        print('1', end='', file=sys.stdout)
        print('a', end='', file=sys.stderr)
        self.assertEqual(x.out(), '1')
        self.assertEqual(x.err(), 'a')
        # Enable y
        y.start()
        print('b', end='', file=sys.stderr)
        print('2', end='', file=sys.stdout)
        # Enable z
        z.start()
        print('3', end='', file=sys.stdout)
        print('c', end='', file=sys.stderr)
        # Disable z
        z.stop()
        print('d', end='', file=sys.stderr)
        print('4', end='', file=sys.stdout)
        # Disable y
        y.stop()
        print('5', end='', file=sys.stdout)
        print('e', end='', file=sys.stderr)
        # Disable z
        x.stop()

        # Check captured text
        self.assertEqual(x.out(), '12345')
        self.assertEqual(x.err(), 'abcde')
        self.assertEqual(y.out(), '234')
        self.assertEqual(y.err(), 'bcd')
        self.assertEqual(z.out(), '3')
        self.assertEqual(z.err(), 'c')
        self.assertEqual(z.text(), '3c')

    def test_stream_capture_repeated_start_stop(self):
        """Tests repeated start-stop commands in the StreamCapture"""
        with myokit.StreamCapture() as x:

            y = myokit.StreamCapture()
            self.assertEqual(y.out(), '')
            self.assertEqual(y.err(), '')

            print('1', end='', file=sys.stdout)
            print('a', end='', file=sys.stderr)
            y.start()
            print('2', end='', file=sys.stdout)
            print('b', end='', file=sys.stderr)
            y.start()
            print('3', end='', file=sys.stdout)
            print('c', end='', file=sys.stderr)
            y.stop()
            print('4', end='', file=sys.stdout)
            print('d', end='', file=sys.stderr)
            y.stop()
            print('5', end='', file=sys.stdout)
            print('e', end='', file=sys.stderr)
            y.stop()
            y.stop()
            y.stop()
            self.assertEqual(y.out(), '23')
            self.assertEqual(y.err(), 'bc')

            y.start()
            print('6', end='', file=sys.stdout)
            y.stop()
            self.assertEqual(y.out(), '6')
            self.assertEqual(y.err(), '')

        self.assertEqual(x.out(), '123456')
        self.assertEqual(x.err(), 'abcde')

    def test_stream_capture_threads(self):
        """Tests StreamCapture with threading."""

        # Sleep times for each thread. Must be long enough to get predictable
        # test output, even on slow CI systems.
        times = [0.25, 0.05, 0.5]
        captured = [None, None, None]

        # Function to call inside threads
        def f(i):
            with myokit.StreamCapture() as c:
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
        self.assertEqual(captured[0], '0a 1a 2a 1b 0b 1e 0e')
        self.assertEqual(captured[1], '1a 2a 1b 1e')
        self.assertEqual(captured[2], '2a 1b 0b 2b 1e 0e 2e')

    def test_stream_capture_silly_context(self):
        """
        Tests StreamCapture when used in odd combinations of context manager
        and object.
        """
        with myokit.StreamCapture() as x:
            print(1)
            y = myokit.StreamCapture()
            with y:
                print(2)
                with y:
                    print(3)
                    y.stop()
                print(4)
            print(5)
        self.assertEqual(x.text(), '1\n2\n3\n4\n5\n')
        self.assertEqual(y.text(), '2\n3\n')

    def test_process_output_capture_nested(self):
        """
        Tests using the ProcessOutputCapture class in a nested pattern.
        """
        z = myokit.ProcessOutputCapture()
        with myokit.ProcessOutputCapture() as x:
            print('1', end='')
            print('a', end='', file=sys.stderr)
            with myokit.ProcessOutputCapture() as y:
                print('2', end='')
                print('b', end='', file=sys.stderr)
                with z:
                    print('3', end='')
                    print('c', end='', file=sys.stderr)
                print('4', end='')
                print('d', end='', file=sys.stderr)
            print('5', end='')
            print('e', end='', file=sys.stderr)

        # Check captured text
        self.assertEqual(x.out(), '15')
        self.assertEqual(x.err(), 'ae')
        self.assertEqual(x.text(), '15ae')
        self.assertEqual(y.out(), '24')
        self.assertEqual(y.err(), 'bd')
        self.assertEqual(y.text(), '24bd')
        self.assertEqual(z.out(), '3')
        self.assertEqual(z.err(), 'c')
        self.assertEqual(z.text(), '3c')

    def test_process_output_capture_repeated_use(self):
        """
        Tests using the ProcessOutputCapture class in a nested pattern with
        repeated enters/exits.
        """
        x = myokit.ProcessOutputCapture()
        y = myokit.ProcessOutputCapture()
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
                print('4', end='')
                print('d', end='', file=sys.stderr)
            print('5', end='')
            print('e', end='', file=sys.stderr)

        # Check captured text
        self.assertEqual(x.out(), '15')
        self.assertEqual(x.err(), 'ae')
        self.assertEqual(x.text(), '15ae')
        self.assertEqual(y.out(), '234')
        self.assertEqual(y.err(), 'bcd')
        self.assertEqual(y.text(), '234bcd')

        with x:
            print('hiya')
        self.assertEqual(x.out(), 'hiya\n')

    def test_process_output_capture_threads(self):
        """Tests ProcessOutputCapture with threading."""

        # Sleep times for each thread. Duration doesn't matter much, as will be
        # executed sequentially. But choose so that interlacing would occur if
        # not.
        times = [0.2, 0.01, 0.05]
        captured = [None, None, None]

        # Function to call inside threads
        def f(i):
            with myokit.ProcessOutputCapture() as c:
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
