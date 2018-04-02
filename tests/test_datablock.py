#!/usr/bin/env python
#
# Tests the DataBlock1d and DataBlock2d classes
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
import unittest
import numpy as np

import myokit

from shared import TemporaryDirectory


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
        for i in xrange(w):
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


class DataBlock2dTest(unittest.TestCase):
    """
    Tests the DataBlock2d
    """
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
        for xx in xrange(2):
            for yy in xrange(3):
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
        for xx in xrange(2):
            for yy in xrange(3):
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


if __name__ == '__main__':
    unittest.main()
