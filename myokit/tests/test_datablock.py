#!/usr/bin/env python3
#
# Tests the DataBlock1d and DataBlock2d classes
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import os
import unittest
import numpy as np

import myokit

from myokit.tests import (
    TemporaryDirectory,
    DIR_DATA,
    DIR_IO,
    TestReporter,
    CancellingReporter,
    WarningCollector,
)

# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp


class DataBlock1dTest(unittest.TestCase):
    """
    Tests the DataBlock1d
    """
    def test_combined(self):
        # Runs a combined test of:
        #
        # - DataLog to Block conversion
        # - Access to fields in block
        # - Saving block to binary file
        # - Loading block from binary file
        #

        # Create simulation log with 1d data
        log = myokit.DataLog()
        log.set_time_key('time')
        t = np.linspace(0, 1, 20)
        log['time'] = t
        log['0.x'] = np.sin(t)
        log['1.x'] = np.cos(t)
        log['2.x'] = np.tan(t)

        # Convert to datablock
        b = log.block1d()

        # Check block contents
        self.assertTrue(np.all(b.time() == t))
        self.assertFalse(b.time() is t)
        self.assertEqual(b.len0d(), 0)
        self.assertEqual(b.len1d(), 1)
        x = b.get1d('x')
        self.assertTrue(np.all(x[:, 0] == log['0.x']))
        self.assertTrue(np.all(x[:, 1] == log['1.x']))
        self.assertTrue(np.all(x[:, 2] == log['2.x']))

        # Make bigger log, try again
        log['pace'] = np.ones(t.shape) + t**2
        log['0.y'] = np.sqrt(t)
        log['1.y'] = 1 + np.sqrt(t)
        log['2.y'] = 2 + np.sqrt(t)

        # Convert to datablock
        b = log.block1d()

        # Check block contents
        self.assertTrue(np.all(b.time() == t))
        self.assertFalse(b.time() is t)
        self.assertEqual(b.len0d(), 1)
        self.assertEqual(b.len1d(), 2)
        self.assertTrue(np.all(b.get0d('pace') == log['pace']))
        self.assertFalse(b.get0d('pace') is log['pace'])
        x = b.get1d('x')
        self.assertTrue(np.all(x[:, 0] == log['0.x']))
        self.assertTrue(np.all(x[:, 1] == log['1.x']))
        self.assertTrue(np.all(x[:, 2] == log['2.x']))
        y = b.get1d('y')
        self.assertTrue(np.all(y[:, 0] == log['0.y']))
        self.assertTrue(np.all(y[:, 1] == log['1.y']))
        self.assertTrue(np.all(y[:, 2] == log['2.y']))

        # Test reading and writing
        with TemporaryDirectory() as d:
            fname = d.path('block1d.zip')
            b.save(fname)
            c = myokit.DataBlock1d.load(fname)
            # Test block contents
            self.assertTrue(np.all(b.time() == c.time()))
            self.assertFalse(b.time() is c.time())
            self.assertEqual(c.len0d(), 1)
            self.assertEqual(c.len1d(), 2)
            self.assertTrue(np.all(b.get0d('pace') == c.get0d('pace')))
            self.assertFalse(b.get0d('pace') is c.get0d('pace'))
            xb = b.get1d('x')
            xc = c.get1d('x')
            self.assertTrue(np.all(xb == xc))
            self.assertFalse(xb is xc)
            yb = b.get1d('y')
            yc = c.get1d('y')
            self.assertTrue(np.all(yb == yc))
            self.assertFalse(yb is yc)

    def test_bad_constructor(self):
        # Test bad arguments to a DataBlock1d raise ValueErrors.

        # Test valid constructor
        w = 2
        time = [1, 2, 3]
        myokit.DataBlock1d(w, time)

        # Test w < 1
        self.assertRaises(ValueError, myokit.DataBlock1d, 0, time)

        # Test time matrix
        self.assertRaises(ValueError, myokit.DataBlock1d, w, [[1, 2, 3]])

        # Decreasing times
        self.assertRaises(ValueError, myokit.DataBlock1d, w, [3, 2, 1])

    def test_block2d(self):
        # Test conversion to 2d.

        w = 2
        time = [1, 2, 3]
        pace = [0, 0, 2]
        x = np.array([[1, 1], [2, 2], [3, 3]])
        b1 = myokit.DataBlock1d(w, time)
        b1.set0d('pace', pace)
        b1.set1d('x', x)

        b2 = b1.block2d()
        self.assertTrue(np.all(b2.get0d('pace') == pace))
        self.assertTrue(np.all(b2.get2d('x') == x.reshape((3, 1, 2))))

    def test_cv(self):
        # Test the CV method.

        b = os.path.join(DIR_DATA, 'cv1d.zip')
        b = myokit.DataBlock1d.load(b)
        self.assertAlmostEqual(b.cv('membrane.V'), 5.95272837350686004e+01)

        # Invalid border argument
        # Negative
        self.assertRaises(ValueError, b.cv, 'membrane.V', border=-1)
        # Too large
        self.assertRaises(ValueError, b.cv, 'membrane.V', border=1000)

        # No upstroke
        time = np.linspace(0, 1, 100)
        down = np.zeros(100) - 85

        d = myokit.DataLog()
        d.set_time_key('time')
        d['time'] = time
        d['x', 0] = down
        d['x', 1] = down
        d['x', 2] = down
        d['x', 3] = down
        d['x', 4] = down
        b = myokit.DataBlock1d.from_log(d)
        self.assertEqual(b.cv('x'), 0)

        # No propagation: Single-cell stimulus
        d = myokit.DataLog()
        d.set_time_key('time')
        d['time'] = time
        d['x', 0] = np.array(down, copy=True)
        d['x', 1] = np.array(down, copy=True)
        d['x', 2] = np.array(down, copy=True)
        d['x', 3] = np.array(down, copy=True)
        d['x', 4] = np.array(down, copy=True)
        d['x', 1][10:] = 40
        b = myokit.DataBlock1d.from_log(d)
        self.assertEqual(b.cv('x'), 0)

        # No propagation: Multi-cell stimulus
        d = myokit.DataLog()
        d.set_time_key('time')
        d['time'] = time
        d['x', 0] = np.array(down, copy=True)
        d['x', 1] = np.array(down, copy=True)
        d['x', 2] = np.array(down, copy=True)
        d['x', 3] = np.array(down, copy=True)
        d['x', 4] = np.array(down, copy=True)
        d['x', 1][10:] = 40
        d['x', 2][10:] = 40
        d['x', 3][10:] = 40
        b = myokit.DataBlock1d.from_log(d)
        self.assertEqual(b.cv('x'), 0)

    def test_from_log(self):
        # Test some edge cases of `DataBlock1d.from_log`.

        # Test valid construction
        d = myokit.DataLog()
        d.set_time_key('time')
        d['time'] = [1, 2, 3]
        d['x', 0] = [0, 0, 0]
        d['x', 1] = [1, 1, 2]
        myokit.DataBlock1d.from_log(d)

        # Deprecated alias
        with WarningCollector() as wc:
            myokit.DataBlock1d.from_DataLog(d)
        self.assertIn('deprecated', wc.text())

        # No time key
        d = myokit.DataLog()
        d['time'] = [1, 2, 3]
        d['x', 0] = [0, 0, 0]
        d['x', 1] = [1, 1, 2]
        self.assertRaises(ValueError, myokit.DataBlock1d.from_log, d)

        # Multi-dimensional time key
        d.set_time_key('0.x')
        self.assertRaises(ValueError, myokit.DataBlock1d.from_log, d)

        # 2-dimensional stuff
        d.set_time_key('time')
        myokit.DataBlock1d.from_log(d)
        d['y', 0, 0] = [10, 10, 10]
        self.assertRaises(ValueError, myokit.DataBlock1d.from_log, d)

        # Mismatched dimensions
        d = myokit.DataLog()
        d.set_time_key('time')
        d['time'] = [1, 2, 3]
        d['x', 0] = [0, 0, 0]
        d['x', 1] = [1, 1, 2]
        d['y', 0] = [2, 0, 0]
        d['y', 1] = [3, 1, 2]
        d['y', 2] = [0, 4, 5]
        self.assertRaises(ValueError, myokit.DataBlock1d.from_log, d)

    def test_grids(self):
        # Test conversion of the DataBlock1d to a 2d grid.

        # Create simulation log with 1d data
        log = myokit.DataLog()
        log.set_time_key('time')
        n = 5   # Points in time
        w = 8   # Points in space
        t = np.arange(n)
        log['time'] = t
        for i in range(w):
            log['x', i] = i * t
            log['y', i] = i * t * 10

        # Create datablock
        b = log.block1d()

        # Check dimensions
        self.assertEqual(b.len0d(), 0)
        self.assertEqual(b.len1d(), 2)
        self.assertEqual(b.shape(), (n, w))
        self.assertEqual(n, len(b.time()))
        self.assertEqual(b.get1d('x').shape, (n, w))
        self.assertEqual(b.get1d('y').shape, (n, w))

        # Convert to grid for matplotlib plotting
        x, y, z = b.grid('x', transpose=True)
        self.assertEqual(x.shape, (w + 1, n + 1))
        self.assertEqual(y.shape, (w + 1, n + 1))
        self.assertEqual(z.shape, (w, n))
        xx, yy, zz = b.grid('x', transpose=False)
        self.assertEqual(xx.shape, (n + 1, w + 1))
        self.assertFalse(np.all(xx.transpose() == x))
        self.assertEqual(yy.shape, (n + 1, w + 1))
        self.assertFalse(np.all(yy.transpose() == y))
        self.assertEqual(zz.shape, (n, w))
        self.assertTrue(np.all(zz.transpose() == z))

        # Convert to grid for image-like plotting
        x, y, z = b.image_grid('x', transpose=True)
        self.assertEqual(x.shape, (w, n))
        self.assertEqual(y.shape, (w, n))
        self.assertEqual(z.shape, (w, n))
        self.assertTrue(
            np.all(x == np.array([
                [0, 1, 2, 3, 4],
                [0, 1, 2, 3, 4],
                [0, 1, 2, 3, 4],
                [0, 1, 2, 3, 4],
                [0, 1, 2, 3, 4],
                [0, 1, 2, 3, 4],
                [0, 1, 2, 3, 4],
                [0, 1, 2, 3, 4]])))
        self.assertTrue(
            np.all(y == np.array([
                [0, 0, 0, 0, 0],
                [1, 1, 1, 1, 1],
                [2, 2, 2, 2, 2],
                [3, 3, 3, 3, 3],
                [4, 4, 4, 4, 4],
                [5, 5, 5, 5, 5],
                [6, 6, 6, 6, 6],
                [7, 7, 7, 7, 7]])))
        self.assertTrue(
            np.all(z == np.array([
                [0, 0, 0, 0, 0],
                [0, 1, 2, 3, 4],
                [0, 2, 4, 6, 8],
                [0, 3, 6, 9, 12],
                [0, 4, 8, 12, 16],
                [0, 5, 10, 15, 20],
                [0, 6, 12, 18, 24],
                [0, 7, 14, 21, 28]])))
        xx, yy, zz = b.image_grid('x', transpose=False)
        self.assertEqual(xx.shape, (n, w))
        self.assertEqual(yy.shape, (n, w))
        self.assertEqual(zz.shape, (n, w))
        self.assertFalse(np.all(xx == x.transpose()))
        self.assertTrue(np.all(xx == np.array([
            [0, 1, 2, 3, 4, 5, 6, 7],
            [0, 1, 2, 3, 4, 5, 6, 7],
            [0, 1, 2, 3, 4, 5, 6, 7],
            [0, 1, 2, 3, 4, 5, 6, 7],
            [0, 1, 2, 3, 4, 5, 6, 7]])))
        self.assertFalse(np.all(yy == y.transpose()))
        self.assertTrue(np.all(yy == np.array([
            [0, 0, 0, 0, 0, 0, 0, 0],
            [1, 1, 1, 1, 1, 1, 1, 1],
            [2, 2, 2, 2, 2, 2, 2, 2],
            [3, 3, 3, 3, 3, 3, 3, 3],
            [4, 4, 4, 4, 4, 4, 4, 4]])))
        self.assertTrue(np.all(zz == z.transpose()))

        # Compare grid and image_grid
        x, y, z = b.grid('x', transpose=True)
        xx, yy, zz = b.image_grid('x', transpose=True)
        self.assertTrue(np.all(x[:-1, :-1] == xx))
        self.assertTrue(np.all(y[:-1, :-1] == yy))
        self.assertTrue(np.all(z == zz))

    def test_keys(self):
        # Test the keys0d() and keys1d() methods.

        w = 2
        time = [1, 2, 3]
        b1 = myokit.DataBlock1d(w, time)

        # Test keys0d
        self.assertEqual(len(list(b1.keys0d())), 0)
        pace = np.array([0, 0, 2])
        b1.set0d('pace', pace)
        self.assertEqual(len(list(b1.keys0d())), 1)
        self.assertIn('pace', b1.keys0d())
        b1.set0d('poos', pace)
        self.assertEqual(len(list(b1.keys0d())), 2)
        self.assertIn('poos', b1.keys0d())

        # Test keys1d
        self.assertEqual(len(list(b1.keys1d())), 0)
        x = np.array([[1, 1], [2, 2], [3, 3]])
        b1.set1d('x', x)
        self.assertEqual(len(list(b1.keys1d())), 1)
        y = np.array([[2, 1], [3, 2], [4, 3]])
        b1.set1d('y', y)
        self.assertEqual(len(list(b1.keys1d())), 2)

    def test_load_bad_file(self):
        # Test loading errors.

        # Not enough files
        path = os.path.join(DIR_IO, 'bad1d-1-not-enough-files.zip')
        self.assertRaisesRegex(
            myokit.DataBlockReadError, 'Not enough files',
            myokit.DataBlock1d.load, path)

        # No header file
        path = os.path.join(DIR_IO, 'bad1d-2-no-header.zip')
        self.assertRaisesRegex(
            myokit.DataBlockReadError, 'Header not found',
            myokit.DataBlock1d.load, path)

        # No data file
        path = os.path.join(DIR_IO, 'bad1d-3-no-data.zip')
        self.assertRaisesRegex(
            myokit.DataBlockReadError, 'Data not found',
            myokit.DataBlock1d.load, path)

        # Not a zip
        path = os.path.join(DIR_IO, 'bad1d-4-not-a-zip.zip')
        self.assertRaisesRegex(
            myokit.DataBlockReadError, 'Bad zip',
            myokit.DataBlock1d.load, path)

        # Unknown data type in data
        path = os.path.join(DIR_IO, 'bad1d-5-bad-data-type.zip')
        self.assertRaisesRegex(
            myokit.DataBlockReadError, 'Unrecognized data type',
            myokit.DataBlock1d.load, path)

        # Not enough data: detected at time level
        path = os.path.join(DIR_IO, 'bad1d-6-time-too-short.zip')
        self.assertRaisesRegex(
            myokit.DataBlockReadError, 'larger data',
            myokit.DataBlock1d.load, path)

        # Not enoug data: detected at 0d level
        path = os.path.join(DIR_IO, 'bad1d-7-0d-too-short.zip')
        self.assertRaisesRegex(
            myokit.DataBlockReadError, 'larger data',
            myokit.DataBlock1d.load, path)

        # Not enough data: detected at 1d level
        path = os.path.join(DIR_IO, 'bad1d-8-1d-too-short.zip')
        self.assertRaisesRegex(
            myokit.DataBlockReadError, 'larger data',
            myokit.DataBlock1d.load, path)

        # Test progress reporter
        path = os.path.join(DIR_DATA, 'cv1d.zip')
        p = TestReporter()
        self.assertFalse(p.entered)
        self.assertFalse(p.exited)
        self.assertFalse(p.updated)
        b = myokit.DataBlock1d.load(path, p)
        self.assertIsNotNone(b)
        self.assertTrue(p.entered)
        self.assertTrue(p.exited)
        self.assertTrue(p.updated)

        # Test cancelling in progress reporter
        p = CancellingReporter()
        b = myokit.DataBlock1d.load(path, p)
        self.assertIsNone(b)
        p = CancellingReporter(1)
        b = myokit.DataBlock1d.load(path, p)
        self.assertIsNone(b)
        p = CancellingReporter(2)
        b = myokit.DataBlock1d.load(path, p)
        self.assertIsNone(b)
        p = CancellingReporter(3)
        b = myokit.DataBlock1d.load(path, p)
        self.assertIsNone(b)

    def test_remove0d(self):
        # Test remove0d().

        # Add new 0d field and remove again
        b = myokit.DataBlock1d(2, [1, 2, 3])
        self.assertEqual(b.len0d(), 0)
        b.set0d('pace', np.array([0, 0, 2]))
        self.assertEqual(b.len0d(), 1)
        b.remove0d('pace')
        self.assertEqual(b.len0d(), 0)

        # Time can't be removed
        self.assertRaises(KeyError, b.remove0d, 'time')

    def test_remove1d(self):
        # Test remove1d().

        # Add new 0d field and remove again
        b = myokit.DataBlock1d(2, [1, 2, 3])
        self.assertEqual(b.len1d(), 0)
        b.set1d('z', np.array([[0, 0], [2, 3], [2, 1]]))
        self.assertEqual(b.len1d(), 1)
        b.remove1d('z')
        self.assertEqual(b.len1d(), 0)

    def test_set0d(self):
        # Test set0d().

        w = 2
        time = [1, 2, 3]
        b1 = myokit.DataBlock1d(w, time)

        # Test valid call
        pace = np.array([0, 0, 2])
        b1.set0d('pace', pace)
        self.assertTrue(np.all(b1.get0d('pace') == pace))

        # Test copying
        b1.set0d('pace', pace, copy=False)
        self.assertTrue(np.all(b1.get0d('pace') == pace))
        self.assertIs(b1.get0d('pace'), pace)
        b1.set0d('pace', pace, copy=True)
        self.assertTrue(np.all(b1.get0d('pace') == pace))
        self.assertIsNot(b1.get0d('pace'), pace)

        # Test bad calls
        self.assertRaises(ValueError, b1.set0d, '', pace)
        self.assertRaises(ValueError, b1.set0d, 'pace', [1, 2, 3, 4])
        self.assertRaises(ValueError, b1.set0d, 'pace', np.array([1, 2, 3, 4]))

    def test_set1d(self):
        # Test set1d().

        w = 2
        time = [1, 2, 3]
        b1 = myokit.DataBlock1d(w, time)

        # Test valid call
        x = np.array([[1, 1], [2, 2], [3, 3]])
        b1.set1d('x', x)
        self.assertTrue(np.all(b1.get1d('x') == x))

        # Test copying
        b1.set1d('x', x, copy=False)
        self.assertTrue(np.all(b1.get1d('x') == x))
        self.assertIs(b1.get1d('x'), x)
        b1.set1d('x', x, copy=True)
        self.assertTrue(np.all(b1.get1d('x') == x))
        self.assertIsNot(b1.get1d('x'), x)

        # Test bad calls
        self.assertRaises(ValueError, b1.set1d, '', x)
        x = np.array([[1, 1], [2, 2], [3, 3], [4, 4]])
        self.assertRaises(ValueError, b1.set1d, 'x', x)

    def test_to_log(self):
        # Test the `DataBlock1d.to_log()` method.

        # Create test block
        b = myokit.DataBlock1d(3, [1, 2, 3, 4])
        b.set0d('pace', [0, 1, 0, 0])
        b.set1d('voltage', [[2, 1, 0], [1, 2, 1], [0, 1, 2], [0, 0, 1]])

        # Convert and inspect
        d = b.to_log()
        self.assertIn('time', d)
        self.assertIn('pace', d)
        self.assertIn('0.voltage', d)
        self.assertIn('1.voltage', d)
        self.assertIn('2.voltage', d)
        self.assertEqual(len(d), 5)
        self.assertEqual(list(d.time()), [1, 2, 3, 4])
        self.assertEqual(list(d['pace']), [0, 1, 0, 0])
        self.assertEqual(list(d['0.voltage']), [2, 1, 0, 0])
        self.assertEqual(list(d['1.voltage']), [1, 2, 1, 0])
        self.assertEqual(list(d['2.voltage']), [0, 1, 2, 1])

    def test_trace(self):
        w = 2
        time = [1, 2, 3]
        b = myokit.DataBlock1d(w, time)
        x = np.array([[1, 4], [2, 5], [3, 6]])
        b.set1d('x', x)
        self.assertTrue(np.all(b.trace('x', 0) == [1, 2, 3]))
        self.assertTrue(np.all(b.trace('x', 1) == [4, 5, 6]))


class DataBlock2dTest(unittest.TestCase):
    """
    Tests `DataBlock2d`.
    """

    def test_bad_constructor(self):
        # Test bad arguments to a DataBlock2d raise ValueErrors.

        # Test valid constructor
        w = 2
        h = 3
        time = [1, 2, 3]
        myokit.DataBlock2d(w, h, time)

        # Test w < 1, h < 1
        self.assertRaises(ValueError, myokit.DataBlock2d, 0, h, time)
        self.assertRaises(ValueError, myokit.DataBlock2d, w, 0, time)

        # Test time matrix
        self.assertRaises(ValueError, myokit.DataBlock2d, w, h, [[1, 2, 3]])

        # Decreasing times
        self.assertRaises(ValueError, myokit.DataBlock2d, w, h, [3, 2, 1])

    def test_colors(self):
        # Test conversion to colors using different color maps.

        w, h = 2, 3
        time = [1, 2, 3]
        b = myokit.DataBlock2d(w, h, time)
        x = np.array([  # Each 3 by 2 array is a point in time
            [[0, 1],
             [2, 3],
             [4, 5]],

            [[5, 4],
             [3, 2],
             [1, 0]],

            [[0, 0],
             [0, 0],
             [0, 0]],
        ])
        b.set2d('x', x)

        # Red colormap
        t0 = np.array([  # Deepest array is a pixel
            [[255, 255, 255], [255, 204, 204]],
            [[255, 153, 153], [255, 102, 102]],
            [[255, 50, 50], [255, 0, 0]],
        ])
        t1 = np.array([
            [[255, 0, 0], [255, 50, 50]],
            [[255, 102, 102], [255, 153, 153]],
            [[255, 204, 204], [255, 255, 255]],
        ])
        t2 = np.array([
            [[255, 255, 255], [255, 255, 255]],
            [[255, 255, 255], [255, 255, 255]],
            [[255, 255, 255], [255, 255, 255]],
        ])
        c = b.colors('x', colormap='red')
        self.assertTrue(np.all(c == np.array([t0, t1, t2])))

        # Red with normalization
        t0 = np.array([
            [[255, 255, 255], [255, 255, 255]],
            [[255, 255, 255], [255, 127, 127]],
            [[255, 0, 0], [255, 0, 0]],
        ])
        t1 = np.array([
            [[255, 0, 0], [255, 0, 0]],
            [[255, 127, 127], [255, 255, 255]],
            [[255, 255, 255], [255, 255, 255]],
        ])
        t2 = np.array([
            [[255, 255, 255], [255, 255, 255]],
            [[255, 255, 255], [255, 255, 255]],
            [[255, 255, 255], [255, 255, 255]],
        ])
        c = b.colors('x', colormap='red', lower=2, upper=4)
        self.assertTrue(np.all(c[0] == t0))
        self.assertTrue(np.all(c[1] == t1))
        self.assertTrue(np.all(c[2] == t2))

        # Red with extreme normalization
        t2 = np.array([
            [[255, 255, 255], [255, 255, 255]],
            [[255, 255, 255], [255, 255, 255]],
            [[255, 255, 255], [255, 255, 255]],
        ])
        c = b.colors('x', colormap='red', lower=4, upper=4)
        self.assertTrue(np.all(c[0] == t2))
        self.assertTrue(np.all(c[1] == t2))
        self.assertTrue(np.all(c[2] == t2))

        # Green
        t0 = np.array([
            [[255, 255, 255], [204, 255, 204]],
            [[153, 255, 153], [102, 255, 102]],
            [[50, 255, 50], [0, 255, 0]],
        ])
        t1 = np.array([
            [[0, 255, 0], [50, 255, 50]],
            [[102, 255, 102], [153, 255, 153]],
            [[204, 255, 204], [255, 255, 255]],
        ])
        t2 = np.array([
            [[255, 255, 255], [255, 255, 255]],
            [[255, 255, 255], [255, 255, 255]],
            [[255, 255, 255], [255, 255, 255]],
        ])
        c = b.colors('x', colormap='green')
        self.assertTrue(np.all(c == np.array([t0, t1, t2])))

        # Blue colormap
        t0 = np.array([  # Deepest array is a pixel
            [[255, 255, 255], [204, 204, 255]],
            [[153, 153, 255], [102, 102, 255]],
            [[50, 50, 255], [0, 0, 255]],
        ])
        t1 = np.array([
            [[0, 0, 255], [50, 50, 255]],
            [[102, 102, 255], [153, 153, 255]],
            [[204, 204, 255], [255, 255, 255]],
        ])
        t2 = np.array([
            [[255, 255, 255], [255, 255, 255]],
            [[255, 255, 255], [255, 255, 255]],
            [[255, 255, 255], [255, 255, 255]],
        ])
        c = b.colors('x', colormap='blue')
        self.assertTrue(np.all(c == np.array([t0, t1, t2])))

        # Rainbow/traditional colormap
        t0 = np.array([  # Deepest array is a pixel
            [[153, 61, 143], [49, 35, 212]],
            [[4, 235, 249], [4, 250, 14]],
            [[209, 213, 35], [153, 61, 61]],
        ])
        t1 = np.array([
            [[153, 61, 61], [209, 213, 35]],
            [[4, 250, 14], [4, 235, 249]],
            [[49, 35, 212], [153, 61, 143]],
        ])
        t2 = np.array([
            [[153, 61, 143], [153, 61, 143]],
            [[153, 61, 143], [153, 61, 143]],
            [[153, 61, 143], [153, 61, 143]],
        ])
        c = b.colors('x', colormap='traditional')
        self.assertTrue(np.all(c[0] == t0))
        self.assertTrue(np.all(c[1] == t1))
        self.assertTrue(np.all(c[2] == t2))

    def test_colors_multiplier(self):
        # Test using the multiplier argument in colors

        w, h = 2, 3
        time = [1, 2, 3]
        b = myokit.DataBlock2d(w, h, time)
        x = np.array([  # Each 3 by 2 array is a point in time
            [[0, 1],
             [2, 3],
             [4, 5]],

            [[5, 4],
             [3, 2],
             [1, 0]],

            [[0, 0],
             [0, 0],
             [0, 0]],
        ])
        b.set2d('x', x)

        # Test with multiplier of 1 or less
        p = [255, 255, 255]
        q = [255, 204, 204]
        r = [255, 153, 153]
        s = [255, 102, 102]
        t = [255, 50, 50]
        u = [255, 0, 0]
        t0 = np.array([  # Deepest array is a pixel
            [p, q],
            [r, s],
            [t, u],
        ])
        t1 = np.array([
            [u, t],
            [s, r],
            [q, p],
        ])
        t2 = np.array([
            [p, p],
            [p, p],
            [p, p],
        ])
        c = b.colors('x', colormap='red', multiplier=1)
        self.assertTrue(np.all(c == np.array([t0, t1, t2])))
        c = b.colors('x', colormap='red', multiplier=1.5)
        self.assertTrue(np.all(c == np.array([t0, t1, t2])))
        c = b.colors('x', colormap='red', multiplier=0.5)
        self.assertTrue(np.all(c == np.array([t0, t1, t2])))

        t0 = np.array([
            [p, p, q, q],
            [p, p, q, q],
            [r, r, s, s],
            [r, r, s, s],
            [t, t, u, u],
            [t, t, u, u],
        ])
        t1 = np.array([
            [u, u, t, t],
            [u, u, t, t],
            [s, s, r, r],
            [s, s, r, r],
            [q, q, p, p],
            [q, q, p, p],
        ])
        t2 = np.array([
            [p, p, p, p],
            [p, p, p, p],
            [p, p, p, p],
            [p, p, p, p],
            [p, p, p, p],
            [p, p, p, p],
        ])
        c = b.colors('x', colormap='red', multiplier=2)
        self.assertTrue(np.all(c == np.array([t0, t1, t2])))

        t0 = np.array([
            [p, p, p, q, q, q],
            [p, p, p, q, q, q],
            [p, p, p, q, q, q],
            [r, r, r, s, s, s],
            [r, r, r, s, s, s],
            [r, r, r, s, s, s],
            [t, t, t, u, u, u],
            [t, t, t, u, u, u],
            [t, t, t, u, u, u],
        ])
        t1 = np.array([
            [u, u, u, t, t, t],
            [u, u, u, t, t, t],
            [u, u, u, t, t, t],
            [s, s, s, r, r, r],
            [s, s, s, r, r, r],
            [s, s, s, r, r, r],
            [q, q, q, p, p, p],
            [q, q, q, p, p, p],
            [q, q, q, p, p, p],
        ])
        t2 = np.array([
            [p, p, p, p, p, p],
            [p, p, p, p, p, p],
            [p, p, p, p, p, p],
            [p, p, p, p, p, p],
            [p, p, p, p, p, p],
            [p, p, p, p, p, p],
            [p, p, p, p, p, p],
            [p, p, p, p, p, p],
            [p, p, p, p, p, p],
        ])
        c = b.colors('x', colormap='red', multiplier=3)
        self.assertTrue(np.all(c == np.array([t0, t1, t2])))

    def test_combined(self):
        # Test loading, saving, conversion from data log.

        # Create simulation log with 1d data
        log = myokit.DataLog()
        log.set_time_key('time')
        t = np.linspace(0, 1, 20)
        log['time'] = t
        log['0.0.x'] = np.sin(t)
        log['0.1.x'] = np.cos(t)
        log['0.2.x'] = np.tan(t)
        log['1.0.x'] = np.sin(2 * t)
        log['1.1.x'] = np.cos(2 * t)
        log['1.2.x'] = np.tan(2 * t)

        # Convert to datablock
        b = log.block2d()

        # Check block contents
        self.assertTrue(np.all(b.time() == t))
        self.assertFalse(b.time() is t)
        self.assertEqual(b.len0d(), 0)
        self.assertEqual(b.len2d(), 1)
        x = b.get2d('x')
        for xx in range(2):
            for yy in range(3):
                self.assertTrue(np.all(x[:, yy, xx] == log['x', xx, yy]))

        # Make bigger log, try again
        log['pace'] = np.ones(t.shape) + t**2
        log['0.0.y'] = np.sqrt(t)
        log['0.1.y'] = 1 + np.sqrt(t)
        log['0.2.y'] = 2 + np.sqrt(t)
        log['1.0.y'] = np.sqrt(t * 2)
        log['1.1.y'] = 1 + np.sqrt(t * 2)
        log['1.2.y'] = 2 + np.sqrt(t * 3)

        # Convert to datablock
        b = log.block2d()

        # Check block contents
        self.assertTrue(np.all(b.time() == t))
        self.assertFalse(b.time() is t)
        self.assertEqual(b.len0d(), 1)
        self.assertEqual(b.len2d(), 2)
        self.assertTrue(np.all(b.get0d('pace') == log['pace']))
        self.assertFalse(b.get0d('pace') is log['pace'])
        x = b.get2d('x')
        y = b.get2d('y')
        for xx in range(2):
            for yy in range(3):
                self.assertTrue(np.all(x[:, yy, xx] == log['x', xx, yy]))
                self.assertTrue(np.all(y[:, yy, xx] == log['y', xx, yy]))

        # Test reading and writing
        with TemporaryDirectory() as td:
            fname = td.path('block2d.zip')
            b.save(fname)
            c = myokit.DataBlock2d.load(fname)

            # Test block contents
            self.assertTrue(np.all(b.time() == c.time()))
            self.assertFalse(b.time() is c.time())
            self.assertEqual(c.len0d(), 1)
            self.assertEqual(c.len2d(), 2)
            self.assertTrue(np.all(b.get0d('pace') == c.get0d('pace')))
            self.assertFalse(b.get0d('pace') is c.get0d('pace'))
            xb = b.get2d('x')
            xc = c.get2d('x')
            self.assertTrue(np.all(xb == xc))
            self.assertFalse(xb is xc)
            yb = b.get2d('y')
            yc = c.get2d('y')
            self.assertTrue(np.all(yb == yc))
            self.assertFalse(yb is yc)

    def test_combine(self):
        # Test the combine() method.

        # Create first data block
        w1, h1 = 2, 3
        t1 = [1, 2, 3]
        b1 = myokit.DataBlock2d(w1, h1, t1)
        x1 = np.array([  # Each 3 by 2 array is a point in time
            [[0, 1],
             [2, 3],
             [4, 5]],
            [[5, 4],
             [3, 2],
             [1, 0]],
            [[0, 0],
             [0, 0],
             [0, 0]],
        ])
        b1.set2d('x', x1)

        # Create first data block
        w2, h2 = 1, 2
        t2 = [1, 2, 3]
        b2 = myokit.DataBlock2d(w2, h2, t2)
        x2 = np.array([  # Each 2 by 1 array is a point in time
            [[0],
             [1]],
            [[2],
             [3]],
            [[4],
             [5]],
        ])
        b2.set2d('x', x2)

        # Basic combine
        m12 = {'x': ('x', 'x', -1)}
        b = myokit.DataBlock2d.combine(b1, b2, m12)
        c0 = [[0, 1, 0],
              [2, 3, 1],
              [4, 5, -1]]
        c1 = [[5, 4, 2],
              [3, 2, 3],
              [1, 0, -1]]
        c2 = [[0, 0, 4],
              [0, 0, 5],
              [0, 0, -1]]
        x = b.get2d('x')
        self.assertTrue(np.all(x[0] == c0))
        self.assertTrue(np.all(x[1] == c1))
        self.assertTrue(np.all(x[2] == c2))

        # Combine with automatic padding value
        mx = {'x': ('x', 'x')}
        b = myokit.DataBlock2d.combine(b1, b2, mx)
        c0 = [[0, 1, 0],
              [2, 3, 1],
              [4, 5, 0]]
        c1 = [[5, 4, 2],
              [3, 2, 3],
              [1, 0, 0]]
        c2 = [[0, 0, 4],
              [0, 0, 5],
              [0, 0, 0]]
        x = b.get2d('x')
        self.assertTrue(np.all(x[0] == c0))
        self.assertTrue(np.all(x[1] == c1))
        self.assertTrue(np.all(x[2] == c2))

        # Combine with pos1 and pos2 set
        m12 = {'x': ('x', 'x', -1)}
        b = myokit.DataBlock2d.combine(b1, b2, m12, pos1=(1, 0), pos2=(0, 1))
        c0 = [[-1, 0, 1],
              [0, 2, 3],
              [1, 4, 5]]
        c1 = [[-1, 5, 4],
              [2, 3, 2],
              [3, 1, 0]]
        c2 = [[-1, 0, 0],
              [4, 0, 0],
              [5, 0, 0]]
        x = b.get2d('x')
        self.assertTrue(np.all(x[0] == c0))
        self.assertTrue(np.all(x[1] == c1))
        self.assertTrue(np.all(x[2] == c2))

        # Combine with 0d information
        b1.set0d('y', [0, 10, 20])
        b2.set0d('y', [20, 30, 40])
        b = myokit.DataBlock2d.combine(b1, b2, m12, {'y': ('y', None)})
        self.assertTrue(np.all(b.get0d('y') == [0, 10, 20]))
        b = myokit.DataBlock2d.combine(b1, b2, m12, {'y': (None, 'y')})
        self.assertTrue(np.all(b.get0d('y') == [20, 30, 40]))
        self.assertRaises(
            ValueError, myokit.DataBlock2d.combine, b1, b2, m12,
            {'y': ('y', 'y')})

        # Test bad time points
        b1 = myokit.DataBlock2d(w1, h1, t1)
        b2 = myokit.DataBlock2d(w2, h2, [4, 5, 6])
        self.assertRaises(ValueError, myokit.DataBlock2d.combine, b1, b2, m12)

        # Test negative pos1, bad pos2
        b1 = myokit.DataBlock2d(w1, h1, t1)
        b2 = myokit.DataBlock2d(w2, h2, t2)
        self.assertRaises(
            ValueError, myokit.DataBlock2d.combine, b1, b2, m12, pos1=(0, -1))
        self.assertRaises(
            ValueError, myokit.DataBlock2d.combine, b1, b2, m12, pos2=(0, -1))

        # Test overlapping pos1, bad pos2
        b1 = myokit.DataBlock2d(w1, h1, t1)
        b2 = myokit.DataBlock2d(w2, h2, t2)
        self.assertRaises(
            ValueError, myokit.DataBlock2d.combine, b1, b2, m12, pos1=(0, 0),
            pos2=(1, 1))

    def test_from_data_log(self):
        # Test some edge cases of `DataBlock2d.from_log`.

        # Test valid construction
        d = myokit.DataLog()
        d.set_time_key('time')
        d['time'] = [1, 2, 3]
        d['x', 0, 0] = [0, 0, 0]
        d['x', 1, 0] = [1, 1, 2]
        d['x', 0, 1] = [1, 2, 2]
        d['x', 1, 1] = [3, 4, 5]
        d['x', 0, 2] = [6, 6, 6]
        d['x', 1, 2] = [7, 7, 2]
        myokit.DataBlock2d.from_log(d)

        # Deprecated alias
        with WarningCollector() as wc:
            myokit.DataBlock2d.from_DataLog(d)
        self.assertIn('deprecated', wc.text())

        # No time key
        d.set_time_key(None)
        self.assertRaises(ValueError, myokit.DataBlock2d.from_log, d)

        # Bad time key
        d.set_time_key('z')

        # Multi-dimensional time key
        d.set_time_key('0.0.x')
        self.assertRaises(ValueError, myokit.DataBlock2d.from_log, d)

        # 1-dimensional stuff
        d.set_time_key('time')
        myokit.DataBlock2d.from_log(d)
        d['y', 0] = [10, 10, 10]
        d['y', 1] = [20, 20, 20]
        self.assertRaises(ValueError, myokit.DataBlock2d.from_log, d)

        # Mismatched dimensions
        d = myokit.DataLog()
        d.set_time_key('time')
        d['time'] = [1, 2, 3]
        d['x', 0, 0] = [0, 0, 0]
        d['x', 1, 0] = [1, 1, 2]
        d['x', 0, 1] = [1, 2, 2]
        d['x', 1, 1] = [3, 4, 5]
        d['x', 0, 2] = [6, 6, 6]
        d['x', 1, 2] = [7, 7, 2]
        d['y', 0, 0] = [0, 0, 0]
        d['y', 1, 0] = [1, 1, 2]
        d['y', 0, 1] = [1, 2, 2]
        d['y', 1, 1] = [3, 4, 5]
        d['y', 0, 2] = [6, 6, 6]
        d['y', 1, 2] = [7, 7, 2]
        myokit.DataBlock2d.from_log(d)
        del d['0.2.y']
        del d['1.2.y']
        self.assertRaises(ValueError, myokit.DataBlock2d.from_log, d)

    def test_images(self):
        # Test the images() method.

        w, h = 2, 2
        time = [1, 2]
        b = myokit.DataBlock2d(w, h, time)
        x = np.array([  # Each 2 by 2 array is a point in time
            [[0, 1],
             [2, 3]],
            [[3, 4],
             [4, 5]],
        ])
        b.set2d('x', x)

        # Red colormap
        t0 = np.array([  # Like colors, but strided together (ARGB32)
            255, 255, 255, 255, 204, 204, 255, 255,
            153, 153, 255, 255, 102, 102, 255, 255
        ])
        t1 = np.array([
            102, 102, 255, 255, 50, 50, 255, 255,
            50, 50, 255, 255, 0, 0, 255, 255,
        ])

        c = b.images('x', colormap='red')
        self.assertTrue(np.all(c[0] == t0))
        self.assertTrue(np.all(c[1] == t1))

    def test_is_square(self):
        # Test the is_square method.

        b = myokit.DataBlock2d(1, 1, [1, 2, 3])
        self.assertTrue(b.is_square())
        b = myokit.DataBlock2d(1, 2, [1, 2, 3])
        self.assertFalse(b.is_square())
        b = myokit.DataBlock2d(10, 10, [1, 2, 3])
        self.assertTrue(b.is_square())

    def test_keys_and_items(self):
        # Test the keys0d and keys2d methods, plus the items methods.

        w = 2
        h = 3
        time = [1, 2, 3]
        b = myokit.DataBlock2d(w, h, time)

        # Test keys0d
        self.assertEqual(len(list(b.keys0d())), 0)
        pace = np.array([0, 0, 2])
        b.set0d('pace', pace)
        self.assertEqual(len(list(b.keys0d())), 1)
        self.assertEqual(len(dict(b.items0d())), 1)
        self.assertIn('pace', b.keys0d())
        b.set0d('poos', pace)
        self.assertEqual(len(list(b.keys0d())), 2)
        self.assertEqual(len(dict(b.items0d())), 2)
        self.assertIn('poos', b.keys0d())
        self.assertIn('poos', dict(b.items0d()).keys())

        # Test keys2d
        self.assertEqual(len(list(b.keys2d())), 0)
        self.assertEqual(len(dict(b.items2d())), 0)
        x = np.array([
            [[1, 2], [3, 4], [5, 6]],
            [[3, 4], [5, 6], [7, 8]],
            [[1, 1], [2, 2], [3, 3]]
        ])
        b.set2d('x', x)
        self.assertEqual(len(list(b.keys2d())), 1)
        self.assertEqual(len(dict(b.items2d())), 1)
        y = 3 * x + 1
        b.set2d('y', y)
        self.assertEqual(len(list(b.keys2d())), 2)
        self.assertEqual(len(dict(b.items2d())), 2)

    def test_dominant_eigenvalues(self):
        # Test the dominant_eigenvalues method.

        # Won't work on non-square matrix
        b = myokit.DataBlock2d(1, 2, [1])
        self.assertRaises(Exception, b.dominant_eigenvalues, 'x')

        # Proper test
        b = myokit.DataBlock2d(3, 3, [1])
        x = [[2, 0, 0], [0, 3, 4], [0, 4, 9]]
        b.set2d('x', [x])
        self.assertEqual(b.dominant_eigenvalues('x')[0], 11)

        # Complex values
        # Note: This example has complex eigenvalues, but they're not the
        # dominant ones. If they were, they'd have the same magnitude so the
        # dominant one would be undefined (and so implementation dependent,
        # which causes issues for this test. See #230).
        b = myokit.DataBlock2d(3, 3, [1])
        x = [[0.8, -0.6, 0], [0.6, 0.8, 0], [1, 2, 2]]
        b.set2d('x', [x])
        self.assertAlmostEqual(
            b.dominant_eigenvalues('x')[0], 2 + 0j)

    def test_eigenvalues(self):
        # Test the eigenvalues method.

        # Won't work on non-square matrix
        b = myokit.DataBlock2d(1, 2, [1])
        self.assertRaises(Exception, b.eigenvalues, 'x')

        # Proper test
        b = myokit.DataBlock2d(3, 3, [1])
        x = [[2, 0, 0], [0, 3, 4], [0, 4, 9]]
        b.set2d('x', [x])
        self.assertTrue(np.all(b.eigenvalues('x') == [[11, 1, 2]]))

        # Complex values
        b = myokit.DataBlock2d(3, 3, [1])
        x = [[0, 1, 0], [0, 0, 1], [1, 0, 0]]
        b.set2d('x', [x])
        e = b.eigenvalues('x')[0]
        self.assertAlmostEqual(e[0], -0.5 - np.sqrt(3) / 2j)
        self.assertAlmostEqual(e[1], -0.5 + np.sqrt(3) / 2j)
        self.assertAlmostEqual(e[2], 1)

    def test_largest_eigenvalues(self):
        # Test the largest_eigenvalues method.

        # Won't work on non-square matrix
        b = myokit.DataBlock2d(1, 2, [1])
        self.assertRaises(Exception, b.largest_eigenvalues, 'x')

        # Proper test
        b = myokit.DataBlock2d(3, 3, [1])
        x = [[2, 0, 0], [0, 3, 4], [0, 4, 9]]
        b.set2d('x', [x])
        self.assertEqual(b.largest_eigenvalues('x')[0], 11)

        # Complex values
        b = myokit.DataBlock2d(3, 3, [1])
        x = [[0, 1, 0], [0, 0, 1], [1, 0, 0]]
        b.set2d('x', [x])
        self.assertAlmostEqual(b.largest_eigenvalues('x')[0], 1)

    def test_load_bad_file(self):
        # Test loading errors.

        # Not enough files
        path = os.path.join(DIR_IO, 'bad2d-1-not-enough-files.zip')
        self.assertRaisesRegex(
            myokit.DataBlockReadError, 'Not enough files',
            myokit.DataBlock2d.load, path)

        # No header file
        path = os.path.join(DIR_IO, 'bad2d-2-no-header.zip')
        self.assertRaisesRegex(
            myokit.DataBlockReadError, 'Header not found',
            myokit.DataBlock2d.load, path)

        # No data file
        path = os.path.join(DIR_IO, 'bad2d-3-no-data.zip')
        self.assertRaisesRegex(
            myokit.DataBlockReadError, 'Data not found',
            myokit.DataBlock2d.load, path)

        # Not a zip
        path = os.path.join(DIR_IO, 'bad2d-4-not-a-zip.zip')
        self.assertRaisesRegex(
            myokit.DataBlockReadError, 'Bad zip',
            myokit.DataBlock2d.load, path)

        # Unknown data type in data
        path = os.path.join(DIR_IO, 'bad2d-5-bad-data-type.zip')
        self.assertRaisesRegex(
            myokit.DataBlockReadError, 'Unrecognized data type',
            myokit.DataBlock2d.load, path)

        # Unknown data type in data
        path = os.path.join(DIR_IO, 'bad2d-6-time-too-short.zip')
        self.assertRaisesRegex(
            myokit.DataBlockReadError, 'larger data',
            myokit.DataBlock2d.load, path)

        # Unknown data type in data
        path = os.path.join(DIR_IO, 'bad2d-7-0d-too-short.zip')
        self.assertRaisesRegex(
            myokit.DataBlockReadError, 'larger data',
            myokit.DataBlock2d.load, path)

        # Unknown data type in data
        path = os.path.join(DIR_IO, 'bad2d-8-2d-too-short.zip')
        self.assertRaisesRegex(
            myokit.DataBlockReadError, 'larger data',
            myokit.DataBlock2d.load, path)

        # Test progress reporter
        path = os.path.join(DIR_IO, 'block2d.zip')
        p = TestReporter()
        self.assertFalse(p.entered)
        self.assertFalse(p.exited)
        self.assertFalse(p.updated)
        b = myokit.DataBlock2d.load(path, p)
        self.assertIsNotNone(b)
        self.assertTrue(p.entered)
        self.assertTrue(p.exited)
        self.assertTrue(p.updated)

        # Test cancelling in progress reporter
        p = CancellingReporter()
        b = myokit.DataBlock2d.load(path, p)
        self.assertIsNone(b)
        p = CancellingReporter(1)
        b = myokit.DataBlock2d.load(path, p)
        self.assertIsNone(b)
        p = CancellingReporter(2)
        b = myokit.DataBlock2d.load(path, p)
        self.assertIsNone(b)
        p = CancellingReporter(3)
        b = myokit.DataBlock2d.load(path, p)
        self.assertIsNone(b)

        # Test loading 1d block with 2d method
        path = os.path.join(DIR_DATA, 'cv1d.zip')
        b = myokit.DataBlock2d.load(path)
        self.assertIsInstance(b, myokit.DataBlock2d)
        # Test if None is passed through
        p = CancellingReporter()
        b = myokit.DataBlock2d.load(path, p)
        self.assertIsNone(b)

    def test_save_frame_csv(self):
        # Test the save_frame_csv() method.

        w, h = 2, 3
        time = [1, 2, 3]
        b = myokit.DataBlock2d(w, h, time)
        x = np.array([  # Each 3 by 2 array is a point in time
            [[0, 1],
             [2, 3],
             [4, 5]],

            [[5, 4],
             [3, 2],
             [1, 0]],

            [[0, 0],
             [0, 0],
             [0, 0]],
        ])
        b.set2d('x', x)

        with TemporaryDirectory() as d:
            path = d.path('test.csv')
            b.save_frame_csv(path, 'x', 0)
            with open(path, 'r') as f:
                lines = [str(x) for x in f.readlines()]
            self.assertEqual(lines[0], '"x","y","value"\n')
            self.assertEqual(lines[1], '0,0,0\n')
            self.assertEqual(lines[2], '1,0,1\n')
            self.assertEqual(lines[3], '0,1,2\n')
            self.assertEqual(lines[4], '1,1,3\n')
            self.assertEqual(lines[5], '0,2,4\n')
            self.assertEqual(lines[6], '1,2,5')

    def test_save_frame_grid(self):
        # Test the save_frame_grid() method.

        w, h = 2, 3
        time = [1, 2, 3]
        b = myokit.DataBlock2d(w, h, time)
        x = np.array([  # Each 3 by 2 array is a point in time
            [[0, 1],
             [2, 3],
             [4, 5]],

            [[5, 4],
             [3, 2],
             [1, 0]],

            [[0, 0],
             [0, 0],
             [0, 0]],
        ])
        b.set2d('x', x)

        with TemporaryDirectory() as d:
            path = d.path('test.csv')
            b.save_frame_grid(path, 'x', 0)
            with open(path, 'r') as f:
                lines = [str(x) for x in f.readlines()]
            self.assertEqual(lines[0], '0 1\n')
            self.assertEqual(lines[1], '2 3\n')
            self.assertEqual(lines[2], '4 5')

    def test_remove0d(self):
        # Test remove0d().

        # Add new 0d field and remove again
        b = myokit.DataBlock2d(2, 3, [1, 2, 3])
        self.assertEqual(b.len0d(), 0)
        b.set0d('pace', np.array([0, 0, 2]))
        self.assertEqual(b.len0d(), 1)
        b.remove0d('pace')
        self.assertEqual(b.len0d(), 0)

        # Time can't be removed
        self.assertRaises(KeyError, b.remove0d, 'time')

    def test_remove2d(self):
        # Test remove2d().

        # Add new 0d field and remove again
        b = myokit.DataBlock2d(2, 3, [1, 2, 3])
        x = np.array([
            [[1, 2], [3, 4], [5, 6]],
            [[3, 4], [5, 6], [7, 8]],
            [[1, 1], [2, 2], [3, 3]]
        ])
        self.assertEqual(b.len2d(), 0)
        b.set2d('x', np.array(x))
        self.assertEqual(b.len2d(), 1)
        b.remove2d('x')
        self.assertEqual(b.len2d(), 0)

    def test_set0d(self):
        # Test set0d().

        w = 2
        h = 3
        time = [1, 2, 3]
        b1 = myokit.DataBlock2d(w, h, time)

        # Test valid call
        pace = np.array([0, 0, 2])
        b1.set0d('pace', pace)
        self.assertTrue(np.all(b1.get0d('pace') == pace))

        # Test copying
        b1.set0d('pace', pace, copy=False)
        self.assertTrue(np.all(b1.get0d('pace') == pace))
        self.assertIs(b1.get0d('pace'), pace)
        b1.set0d('pace', pace, copy=True)
        self.assertTrue(np.all(b1.get0d('pace') == pace))
        self.assertIsNot(b1.get0d('pace'), pace)

        # Test bad calls
        self.assertRaises(ValueError, b1.set0d, '', pace)
        self.assertRaises(ValueError, b1.set0d, 'pace', [1, 2, 3, 4])
        self.assertRaises(ValueError, b1.set0d, 'pace', np.array([1, 2, 3, 4]))

    def test_set2d(self):
        # Test set2d().

        w = 2
        h = 3
        time = [1, 2, 3]
        b1 = myokit.DataBlock2d(w, h, time)

        # Test valid call
        x = np.array([
            [[1, 2], [3, 4], [5, 6]],
            [[3, 4], [5, 6], [7, 8]],
            [[1, 1], [2, 2], [3, 3]]
        ])

        b1.set2d('x', x)
        self.assertTrue(np.all(b1.get2d('x') == x))

        # Test copying
        b1.set2d('x', x, copy=False)
        self.assertTrue(np.all(b1.get2d('x') == x))
        self.assertIs(b1.get2d('x'), x)
        b1.set2d('x', x, copy=True)
        self.assertTrue(np.all(b1.get2d('x') == x))
        self.assertIsNot(b1.get2d('x'), x)

        # Test bad calls
        self.assertRaises(ValueError, b1.set2d, '', x)
        x = np.array([
            [[1, 2], [3, 4]],
            [[3, 4], [5, 6]],
            [[1, 1], [2, 2]],
        ])
        self.assertRaises(ValueError, b1.set2d, 'x', x)

    def test_to_log(self):
        # Test the `DataBlock2d.to_log()` method.

        # Create test block
        b = myokit.DataBlock2d(3, 2, [1, 2, 3, 4])
        b.set0d('pace', [0, 1, 0, 0])
        b.set2d(
            'voltage',
            [[[2, 1, 0],
              [1, 0, 0]],
             [[1, 2, 1],
              [2, 1, 0]],
             [[0, 1, 2],
              [1, 2, 1]],
             [[0, 0, 1],
              [0, 1, 2]]]
        )

        # Convert and inspect
        d = b.to_log()
        self.assertIn('time', d)
        self.assertIn('pace', d)
        self.assertIn('0.0.voltage', d)
        self.assertIn('1.0.voltage', d)
        self.assertIn('2.0.voltage', d)
        self.assertIn('0.1.voltage', d)
        self.assertIn('1.1.voltage', d)
        self.assertIn('2.1.voltage', d)
        self.assertEqual(len(d), 8)
        self.assertEqual(list(d.time()), [1, 2, 3, 4])
        self.assertEqual(list(d['pace']), [0, 1, 0, 0])
        self.assertEqual(list(d['0.0.voltage']), [2, 1, 0, 0])
        self.assertEqual(list(d['1.0.voltage']), [1, 2, 1, 0])
        self.assertEqual(list(d['2.0.voltage']), [0, 1, 2, 1])
        self.assertEqual(list(d['0.1.voltage']), [1, 2, 1, 0])
        self.assertEqual(list(d['1.1.voltage']), [0, 1, 2, 1])
        self.assertEqual(list(d['2.1.voltage']), [0, 0, 1, 2])

    def test_trace(self):
        # Tests the trace() method

        w = 2
        h = 3
        time = [1, 2, 3]
        b1 = myokit.DataBlock2d(w, h, time)
        x = np.array([
            [[1, 2], [3, 4], [5, 6]],
            [[3, 4], [5, 6], [7, 8]],
            [[1, 1], [2, 2], [3, 3]]
        ])
        b1.set2d('x', x)
        self.assertTrue(np.all(b1.trace('x', 1, 1) == [4, 6, 2]))


class ColorMapTest(unittest.TestCase):
    """
    Tests extra methods from ColorMap class.
    """
    def test_exists(self):
        self.assertFalse(myokit.ColorMap.exists('michael'))
        self.assertTrue(myokit.ColorMap.exists('red'))

    def test_get(self):
        self.assertIsInstance(myokit.ColorMap.get('red'), myokit.ColorMap)
        self.assertRaises(KeyError, myokit.ColorMap.get, 'michael')

    def test_names(self):
        names = list(myokit.ColorMap.names())
        self.assertIn('red', names)

    def test_image(self):
        # Test the image() method, that returns a colormap representation

        # Red colormap
        m = np.array([  # Like colors, but strided together (ARGB32)
            0, 0, 255, 255,
            50, 50, 255, 255,
            102, 102, 255, 255,
            153, 153, 255, 255,
            204, 204, 255, 255,
            255, 255, 255, 255,
        ])

        c = myokit.ColorMap.image('red', 1, 6)
        self.assertTrue(np.all(c == m))


if __name__ == '__main__':
    unittest.main()
