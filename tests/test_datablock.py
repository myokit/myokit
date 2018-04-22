#!/usr/bin/env python
#
# Tests the DataBlock1d and DataBlock2d classes
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import os
import unittest
import numpy as np

import myokit

from shared import TemporaryDirectory, DIR_DATA


class Progress(myokit.ProgressReporter):
    """
    Progress reporter just for debugging.
    """
    def __init__(self):
        self.entered = False
        self.exited = False
        self.updated = False

    def enter(self, msg=None):
        self.entered = True

    def exit(self):
        self.exited = True

    def update(self, f):
        self.updated = True
        return True


class CancellingProgress(myokit.ProgressReporter):
    """
    Progress reporter just for debugging.
    """
    def __init__(self, okays=0):
        self.okays = int(okays)

    def enter(self, msg=None):
        pass

    def exit(self):
        pass

    def update(self, f):
        self.okays -= 1
        return self.okays >= 0


class DataBlock1dTest(unittest.TestCase):
    """
    Tests the DataBlock1d
    """
    def test_combined(self):
        """
        Runs a combined test of:

         - DataLog to Block conversion
         - Access to fields in block
         - Saving block to binary file
         - Loading block from binary file

        """
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
        """
        Tests bad arguments to a DataBlock1d raise ValueErrors.
        """
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
        """
        Tests conversion to 2d.
        """
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
        """
        Tests the CV method.
        """
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
        b = myokit.DataBlock1d.from_DataLog(d)
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
        b = myokit.DataBlock1d.from_DataLog(d)
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
        b = myokit.DataBlock1d.from_DataLog(d)
        self.assertEqual(b.cv('x'), 0)

    def test_from_data_log(self):
        """
        Tests some edge cases of `DataBlock1d.from_DataLog`.
        """
        # Test valid construction
        d = myokit.DataLog()
        d.set_time_key('time')
        d['time'] = [1, 2, 3]
        d['x', 0] = [0, 0, 0]
        d['x', 1] = [1, 1, 2]
        myokit.DataBlock1d.from_DataLog(d)

        # No time key
        d = myokit.DataLog()
        d['time'] = [1, 2, 3]
        d['x', 0] = [0, 0, 0]
        d['x', 1] = [1, 1, 2]
        self.assertRaises(ValueError, myokit.DataBlock1d.from_DataLog, d)

        # Multi-dimensional time key
        d.set_time_key('0.x')
        self.assertRaises(ValueError, myokit.DataBlock1d.from_DataLog, d)

        # 2-dimensional stuff
        d.set_time_key('time')
        myokit.DataBlock1d.from_DataLog(d)
        d['y', 0, 0] = [10, 10, 10]
        self.assertRaises(ValueError, myokit.DataBlock1d.from_DataLog, d)

        # Mismatched dimensions
        d = myokit.DataLog()
        d.set_time_key('time')
        d['time'] = [1, 2, 3]
        d['x', 0] = [0, 0, 0]
        d['x', 1] = [1, 1, 2]
        d['y', 0] = [2, 0, 0]
        d['y', 1] = [3, 1, 2]
        d['y', 2] = [0, 4, 5]
        self.assertRaises(ValueError, myokit.DataBlock1d.from_DataLog, d)

    def test_grids(self):
        """
        Tests conversion of the DataBlock1d to a 2d grid.
        """
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

    def test_load_bad_file(self):
        """
        Tests loading errors.
        """
        # Not enough files
        path = os.path.join(DIR_DATA, 'bad1d-1-not-enough-files.zip')
        self.assertRaises(
            myokit.DataBlockReadError, myokit.DataBlock1d.load, path)
        message = ''
        try:
            myokit.DataBlock1d.load(path)
        except myokit.DataBlockReadError as e:
            message = e.message
        self.assertIn('Not enough files', message)

        # No header file
        path = os.path.join(DIR_DATA, 'bad1d-2-no-header.zip')
        self.assertRaises(
            myokit.DataBlockReadError, myokit.DataBlock1d.load, path)
        message = ''
        try:
            myokit.DataBlock1d.load(path)
        except myokit.DataBlockReadError as e:
            message = e.message
        self.assertIn('Header not found', message)

        # No data file
        path = os.path.join(DIR_DATA, 'bad1d-3-no-data.zip')
        self.assertRaises(
            myokit.DataBlockReadError, myokit.DataBlock1d.load, path)
        message = ''
        try:
            myokit.DataBlock1d.load(path)
        except myokit.DataBlockReadError as e:
            message = e.message
        self.assertIn('Data not found', message)

        # Not a zip
        path = os.path.join(DIR_DATA, 'bad1d-4-not-a-zip.zip')
        self.assertRaises(
            myokit.DataBlockReadError, myokit.DataBlock1d.load, path)
        message = ''
        try:
            myokit.DataBlock1d.load(path)
        except myokit.DataBlockReadError as e:
            message = e.message
        self.assertIn('Bad zip', message)

        # Unknown data type in data
        path = os.path.join(DIR_DATA, 'bad1d-5-bad-data-type.zip')
        self.assertRaises(
            myokit.DataBlockReadError, myokit.DataBlock1d.load, path)
        message = ''
        try:
            myokit.DataBlock1d.load(path)
        except myokit.DataBlockReadError as e:
            message = e.message
        self.assertIn('Unrecognized data type', message)

        # Not enough data: detected at time level
        path = os.path.join(DIR_DATA, 'bad1d-6-time-too-short.zip')
        self.assertRaises(
            myokit.DataBlockReadError, myokit.DataBlock1d.load, path)
        message = ''
        try:
            myokit.DataBlock1d.load(path)
        except myokit.DataBlockReadError as e:
            message = e.message
        self.assertIn('larger data', message)

        # Not enoug data: detected at 0d level
        path = os.path.join(DIR_DATA, 'bad1d-7-0d-too-short.zip')
        self.assertRaises(
            myokit.DataBlockReadError, myokit.DataBlock1d.load, path)
        message = ''
        try:
            myokit.DataBlock1d.load(path)
        except myokit.DataBlockReadError as e:
            message = e.message
        self.assertIn('larger data', message)

        # Not enough data: detected at 1d level
        path = os.path.join(DIR_DATA, 'bad1d-8-1d-too-short.zip')
        self.assertRaises(
            myokit.DataBlockReadError, myokit.DataBlock1d.load, path)
        message = ''
        try:
            myokit.DataBlock1d.load(path)
        except myokit.DataBlockReadError as e:
            message = e.message
        self.assertIn('larger data', message)

        # Test progress reporter
        path = os.path.join(DIR_DATA, 'cv1d.zip')
        p = Progress()
        self.assertFalse(p.entered)
        self.assertFalse(p.exited)
        self.assertFalse(p.updated)
        b = myokit.DataBlock1d.load(path, p)
        self.assertIsNotNone(b)
        self.assertTrue(p.entered)
        self.assertTrue(p.exited)
        self.assertTrue(p.updated)

        # Test cancelling in progress reporter
        p = CancellingProgress()
        b = myokit.DataBlock1d.load(path, p)
        self.assertIsNone(b)
        p = CancellingProgress(1)
        b = myokit.DataBlock1d.load(path, p)
        self.assertIsNone(b)
        p = CancellingProgress(2)
        b = myokit.DataBlock1d.load(path, p)
        self.assertIsNone(b)
        p = CancellingProgress(3)
        b = myokit.DataBlock1d.load(path, p)
        self.assertIsNone(b)

    def test_set0d(self):
        """
        Tests set0d().
        """
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
        """
        Tests set1d().
        """
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

    def test_keys(self):
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
        """
        Tests bad arguments to a DataBlock2d raise ValueErrors.
        """
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

    def test_combined(self):
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

    def test_from_data_log(self):
        """
        Tests some edge cases of `DataBlock1d.from_DataLog`.
        """
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
        myokit.DataBlock2d.from_DataLog(d)

        # No time key
        d.set_time_key(None)
        self.assertRaises(ValueError, myokit.DataBlock2d.from_DataLog, d)

        # Bad time key
        d.set_time_key('z')

        # Multi-dimensional time key
        d.set_time_key('0.0.x')
        self.assertRaises(ValueError, myokit.DataBlock2d.from_DataLog, d)

        # 1-dimensional stuff
        d.set_time_key('time')
        myokit.DataBlock2d.from_DataLog(d)
        d['y', 0] = [10, 10, 10]
        d['y', 1] = [20, 20, 20]
        self.assertRaises(ValueError, myokit.DataBlock2d.from_DataLog, d)

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
        myokit.DataBlock2d.from_DataLog(d)
        del(d['0.2.y'])
        del(d['1.2.y'])
        self.assertRaises(ValueError, myokit.DataBlock2d.from_DataLog, d)

    def test_keys(self):
        w = 2
        h = 3
        time = [1, 2, 3]
        b = myokit.DataBlock2d(w, h, time)

        # Test keys0d
        self.assertEqual(len(list(b.keys0d())), 0)
        pace = np.array([0, 0, 2])
        b.set0d('pace', pace)
        self.assertEqual(len(list(b.keys0d())), 1)
        self.assertIn('pace', b.keys0d())
        b.set0d('poos', pace)
        self.assertEqual(len(list(b.keys0d())), 2)
        self.assertIn('poos', b.keys0d())

        # Test keys2d
        self.assertEqual(len(list(b.keys2d())), 0)
        x = np.array([
            [[1, 2], [3, 4], [5, 6]],
            [[3, 4], [5, 6], [7, 8]],
            [[1, 1], [2, 2], [3, 3]]
        ])
        b.set2d('x', x)
        self.assertEqual(len(list(b.keys2d())), 1)
        y = 3 * x + 1
        b.set2d('y', y)
        self.assertEqual(len(list(b.keys2d())), 2)

    def test_load_bad_file(self):
        """
        Tests loading errors.
        """
        # Not enough files
        path = os.path.join(DIR_DATA, 'bad2d-1-not-enough-files.zip')
        self.assertRaises(
            myokit.DataBlockReadError, myokit.DataBlock2d.load, path)
        message = ''
        try:
            myokit.DataBlock2d.load(path)
        except myokit.DataBlockReadError as e:
            message = e.message
        self.assertIn('Not enough files', message)

        # No header file
        path = os.path.join(DIR_DATA, 'bad2d-2-no-header.zip')
        self.assertRaises(
            myokit.DataBlockReadError, myokit.DataBlock2d.load, path)
        message = ''
        try:
            myokit.DataBlock2d.load(path)
        except myokit.DataBlockReadError as e:
            message = e.message
        self.assertIn('Header not found', message)

        # No data file
        path = os.path.join(DIR_DATA, 'bad2d-3-no-data.zip')
        self.assertRaises(
            myokit.DataBlockReadError, myokit.DataBlock2d.load, path)
        message = ''
        try:
            myokit.DataBlock2d.load(path)
        except myokit.DataBlockReadError as e:
            message = e.message
        self.assertIn('Data not found', message)

        # Not a zip
        path = os.path.join(DIR_DATA, 'bad2d-4-not-a-zip.zip')
        self.assertRaises(
            myokit.DataBlockReadError, myokit.DataBlock2d.load, path)
        message = ''
        try:
            myokit.DataBlock2d.load(path)
        except myokit.DataBlockReadError as e:
            message = e.message
        self.assertIn('Bad zip', message)

        # Unknown data type in data
        path = os.path.join(DIR_DATA, 'bad2d-5-bad-data-type.zip')
        self.assertRaises(
            myokit.DataBlockReadError, myokit.DataBlock2d.load, path)
        message = ''
        try:
            myokit.DataBlock2d.load(path)
        except myokit.DataBlockReadError as e:
            message = e.message
        self.assertIn('Unrecognized data type', message)

        # Unknown data type in data
        path = os.path.join(DIR_DATA, 'bad2d-6-time-too-short.zip')
        self.assertRaises(
            myokit.DataBlockReadError, myokit.DataBlock2d.load, path)
        message = ''
        try:
            myokit.DataBlock2d.load(path)
        except myokit.DataBlockReadError as e:
            message = e.message
        self.assertIn('larger data', message)

        # Unknown data type in data
        path = os.path.join(DIR_DATA, 'bad2d-7-0d-too-short.zip')
        self.assertRaises(
            myokit.DataBlockReadError, myokit.DataBlock2d.load, path)
        message = ''
        try:
            myokit.DataBlock2d.load(path)
        except myokit.DataBlockReadError as e:
            message = e.message
        self.assertIn('larger data', message)

        # Unknown data type in data
        path = os.path.join(DIR_DATA, 'bad2d-8-2d-too-short.zip')
        self.assertRaises(
            myokit.DataBlockReadError, myokit.DataBlock2d.load, path)
        message = ''
        try:
            myokit.DataBlock2d.load(path)
        except myokit.DataBlockReadError as e:
            message = e.message
        self.assertIn('larger data', message)

        # Test progress reporter
        path = os.path.join(DIR_DATA, 'block2d.zip')
        p = Progress()
        self.assertFalse(p.entered)
        self.assertFalse(p.exited)
        self.assertFalse(p.updated)
        b = myokit.DataBlock2d.load(path, p)
        self.assertIsNotNone(b)
        self.assertTrue(p.entered)
        self.assertTrue(p.exited)
        self.assertTrue(p.updated)

        # Test cancelling in progress reporter
        p = CancellingProgress()
        b = myokit.DataBlock2d.load(path, p)
        self.assertIsNone(b)
        p = CancellingProgress(1)
        b = myokit.DataBlock2d.load(path, p)
        self.assertIsNone(b)
        p = CancellingProgress(2)
        b = myokit.DataBlock2d.load(path, p)
        self.assertIsNone(b)
        p = CancellingProgress(3)
        b = myokit.DataBlock2d.load(path, p)
        self.assertIsNone(b)

        # Test loading 1d block with 2d method
        path = os.path.join(DIR_DATA, 'cv1d.zip')
        b = myokit.DataBlock2d.load(path)
        self.assertIsInstance(b, myokit.DataBlock2d)
        # Test if None is passed through
        p = CancellingProgress()
        b = myokit.DataBlock2d.load(path, p)
        self.assertIsNone(b)

    def test_set0d(self):
        """
        Tests set0d().
        """
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
        """
        Tests set2d().
        """
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

    def test_trace(self):
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


if __name__ == '__main__':
    unittest.main()
