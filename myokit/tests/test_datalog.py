#!/usr/bin/env python3
#
# Tests the DataLog class
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
    DIR_DATA,
    DIR_IO,
    TemporaryDirectory,
    TestReporter,
    CancellingReporter,
    WarningCollector,
)

# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp


# Universal newline mode in Python 2 and 3
def uopen(filename):
    try:
        return open(filename, 'r', newline=None)
    except TypeError:
        return open(filename, 'U')


# Extra output
debug = False


class DataLogTest(unittest.TestCase):
    """
    Tests the DataLog's functions.
    """

    def test_extend(self):
        # Test the extend function.

        d1 = myokit.DataLog(time='time')
        v1 = [10, 9, 10, -1, -1, -1]
        v2 = [12, 2, 43, 31, 2, 7]
        d1['time'] = [1, 2, 3]
        d1['v1'] = v1[:3]
        d1['v2'] = v2[:3]
        d2 = myokit.DataLog()
        d2.set_time_key('time')
        d2['time'] = [4, 5, 6]
        d2['v1'] = v1[3:]
        d2['v2'] = v2[3:]

        # No errors, method should work
        d3 = d1.extend(d2)
        self.assertEqual(d3.time(), [1, 2, 3, 4, 5, 6])
        self.assertEqual(d3['v1'], v1)
        self.assertEqual(d3['v2'], v2)

        # Both logs must have the same time key
        d2.set_time_key(None)
        self.assertRaises(ValueError, d1.extend, d2)
        d2.set_time_key('time')
        d1.extend(d2)
        d2.set_time_key('v1')
        self.assertRaises(ValueError, d1.extend, d2)
        d2.set_time_key('time')

        # Both logs must have the same keys
        d2['v3'] = v1
        self.assertRaises(ValueError, d1.extend, d2)
        del d2['v3']

        # Times can overlap
        d2['time'] = [3, 4, 5]
        d1.extend(d2)
        # But times in d2 must be >= than times in d1
        d2['time'] = [2, 3, 4]
        self.assertRaises(ValueError, d1.extend, d2)
        d2['time'] = [4, 5, 6]

        # Should work with two numpy arrays
        d3 = d1.npview().extend(d2.npview())
        self.assertEqual(list(d3.time()), [1, 2, 3, 4, 5, 6])
        self.assertEqual(list(d3['v1']), v1)
        self.assertEqual(list(d3['v2']), v2)

        # Should work with one numpy array
        d3 = d1.extend(d2.npview())
        self.assertEqual(list(d3.time()), [1, 2, 3, 4, 5, 6])
        self.assertEqual(list(d3['v1']), v1)
        self.assertEqual(list(d3['v2']), v2)

        # Should work with partial numpy arrays
        d1['v1'] = np.array(v1[:3])
        d2['v2'] = np.array(v2[3:])
        self.assertIsInstance(d1.time(), list)
        self.assertIsInstance(d1['v1'], np.ndarray)
        self.assertIsInstance(d1['v2'], list)
        self.assertIsInstance(d2.time(), list)
        self.assertIsInstance(d2['v1'], list)
        self.assertIsInstance(d2['v2'], np.ndarray)
        d3 = d1.extend(d2)
        self.assertIsInstance(d3.time(), list)
        self.assertIsInstance(d3['v1'], np.ndarray)
        self.assertIsInstance(d3['v2'], np.ndarray)
        self.assertEqual(list(d3.time()), [1, 2, 3, 4, 5, 6])
        self.assertEqual(list(d3['v1']), v1)
        self.assertEqual(list(d3['v2']), v2)

    def test_find(self):
        # Tests the deprecated find() function

        d = myokit.DataLog({
            'engine.time': [0, 5, 10, 15, 20],
            'membrane.V': [0, 50, 100, 150, 200]})
        d.set_time_key('engine.time')
        with WarningCollector():
            self.assertEqual(d.find(-5), d.find_after(-5))
            self.assertEqual(d.find(0), d.find_after(0))
            self.assertEqual(d.find(2), d.find_after(2))
            self.assertEqual(d.find(5), d.find_after(5))
            self.assertEqual(d.find(7), d.find_after(7))
            self.assertEqual(d.find(20), d.find_after(20))
            self.assertEqual(d.find(22), d.find_after(22))

    def test_find_after(self):
        # Test the find_after() function.

        x = myokit.DataLog({
            'engine.time': [0, 5, 10, 15, 20],
            'membrane.V': [0, 50, 100, 150, 200]})
        x.set_time_key('engine.time')
        self.assertEqual(x.find_after(-5), 0)
        self.assertEqual(x.find_after(0), 0)
        self.assertEqual(x.find_after(2), 1)
        self.assertEqual(x.find_after(5), 1)
        self.assertEqual(x.find_after(8), 2)
        self.assertEqual(x.find_after(10), 2)
        self.assertEqual(x.find_after(13), 3)
        self.assertEqual(x.find_after(15), 3)
        self.assertEqual(x.find_after(19), 4)
        self.assertEqual(x.find_after(20), 4)
        self.assertEqual(x.find_after(21), 5)

        # Now with a numpy log
        x = x.npview()
        self.assertEqual(x.find_after(-5), 0)
        self.assertEqual(x.find_after(0), 0)
        self.assertEqual(x.find_after(2), 1)
        self.assertEqual(x.find_after(5), 1)
        self.assertEqual(x.find_after(8), 2)
        self.assertEqual(x.find_after(10), 2)
        self.assertEqual(x.find_after(13), 3)
        self.assertEqual(x.find_after(15), 3)
        self.assertEqual(x.find_after(19), 4)
        self.assertEqual(x.find_after(20), 4)
        self.assertEqual(x.find_after(21), 5)

    def test_indexing(self):
        # Test the indexing overrides in the simulation log.

        d = myokit.DataLog()
        d['x'] = 'y'
        self.assertEqual(d['x'], 'y')
        d['1.2.membrane.V'] = 'a bear'
        x = d['1.2.membrane.V']
        y = d['membrane.V', 1, 2]
        z = d['membrane.V', (1, 2)]
        self.assertEqual(x, y, z)
        d['4.a'] = 5
        self.assertEqual(d['4.a'], 5)
        d['a', 4] = 6
        self.assertEqual(d['a', 4], 6)
        d['a', 4, 5] = 7
        self.assertEqual(d['a', 4, 5], 7)
        d['a', (5, 6)] = 8
        self.assertEqual(d['a', 5, 6], 8)
        self.assertTrue('4.a' in d)
        self.assertTrue(('a', 4) in d)
        self.assertFalse('5.a' in d)
        self.assertFalse(('a', 5) in d)
        self.assertTrue(('a', (5, 6)) in d)
        del d['a', (5, 6)]
        self.assertFalse(('a', (5, 6)) in d)

    def test_integrate(self):
        # Test the integrate method.

        # Create an irregular time array
        from random import random
        t = []
        for i in range(0, 100):
            t.append(5 * random())
        t.sort()
        t = np.array(t)

        # Create a signal and its derivative
        i = 15 * t**2 + 4 * t + 2
        q = 5 * t**3 + 2 * t**2 + 2 * t

        # Since q already has a value for q[0], remove it to look at the
        # error in integrating...
        q -= q[0]

        # Get estimated value from log
        d = myokit.DataLog({'engine.time': t, 'ina.INa': i})
        d.set_time_key('engine.time')
        x = d.integrate('ina.INa')

        # Get relative error
        e = np.abs(x[1:] - q[1:]) / q[1:]

        # Get mean
        e = np.mean(e)
        if debug:
            print(e)
        self.assertLess(e, 0.1)
        if debug:
            import matplotlib.pyplot as plt
            plt.figure()
            plt.plot(t, q, label='original')
            plt.plot(t, x, label='mid sum')
            plt.legend(loc='upper left')
            plt.figure()
            plt.plot(t, np.abs(x - q) / q, label='mid sum error')
            plt.legend(loc='upper left')
            plt.show()

    def test_interpolate_at(self):
        # Test the interpolate_at method.

        d = myokit.DataLog(time='t')
        d['t'] = [0, 1, 2, 3]
        d['v'] = [0, 10, 30, 60]
        self.assertEqual(d.interpolate_at('v', 0), 0)
        self.assertEqual(d.interpolate_at('v', 0.5), 5)
        self.assertEqual(d.interpolate_at('v', 1), 10)
        self.assertEqual(d.interpolate_at('v', 1.5), 20)
        self.assertEqual(d.interpolate_at('v', 2), 30)
        self.assertEqual(d.interpolate_at('v', 2.5), 45)
        self.assertEqual(d.interpolate_at('v', 3), 60)

        self.assertRaises(ValueError, d.interpolate_at, 'v', -0.5)
        self.assertRaises(ValueError, d.interpolate_at, 'v', 3 + 1e-9)

        d = myokit.DataLog(time='t')
        d['t'] = [2, 4]
        d['v'] = [200, 400]
        self.assertEqual(d.interpolate_at('v', 2), 200)
        self.assertEqual(d.interpolate_at('v', 2.4), 240)
        self.assertEqual(d.interpolate_at('v', 4), 400)

        self.assertRaises(ValueError, d.interpolate_at, 'v', 1)
        self.assertRaises(ValueError, d.interpolate_at, 'v', 5)

    def test_itrim(self):
        # Test the itrim() method.

        d = myokit.DataLog()
        d.set_time_key('t')
        d['t'] = t = [0, 0.1, 0.2, 0.3, 0.4]
        d['a'] = a = [1, 2, 3, 4, 5]
        d['b'] = b = [10, 20, 30, 40, 50]

        # Test function
        def tr(i, j):
            e = d.itrim(i, j)
            self.assertEqual(len(d['t']), 5)
            self.assertEqual(d['t'], t)
            self.assertEqual(d['a'], a)
            self.assertEqual(list(d['b']), list(b))
            self.assertEqual(e['t'], t[i:j])
            self.assertEqual(e['a'], a[i:j])
            self.assertEqual(list(e['b']), list(b[i:j]))

        # Normal operation
        tr(1, 3)
        tr(-5, 3)
        tr(1, 30)
        tr(-10, 40)

        # Partial numpy
        d['b'] = b = np.array(b)
        tr(1, 3)
        tr(-5, 3)
        tr(1, 30)
        tr(-10, 40)

    def test_itrim_left(self):
        # Test the itrim_left() method.

        d = myokit.DataLog()
        d.set_time_key('t')
        d['t'] = t = [0, 0.1, 0.2, 0.3, 0.4]
        d['a'] = a = [1, 2, 3, 4, 5]
        d['b'] = b = [10, 20, 30, 40, 50]

        # Test function
        def tr(i):
            e = d.itrim_left(i)
            self.assertEqual(len(d['t']), 5)
            self.assertEqual(d['t'], t)
            self.assertEqual(d['a'], a)
            self.assertEqual(list(d['b']), list(b))
            self.assertEqual(e['t'], t[i:])
            self.assertEqual(e['a'], a[i:])
            self.assertEqual(list(e['b']), list(b[i:]))

        # Normal operation
        tr(2)
        tr(-5)
        tr(30)

        # Partial numpy
        d['b'] = b = np.array(b)
        tr(2)
        tr(-5)
        tr(30)

    def test_itrim_right(self):
        # Test the itrim_right() method.

        d = myokit.DataLog()
        d.set_time_key('t')
        d['t'] = t = [0, 0.1, 0.2, 0.3, 0.4]
        d['a'] = a = [1, 2, 3, 4, 5]
        d['b'] = b = [10, 20, 30, 40, 50]

        # Test function
        def tr(i):
            e = d.itrim_right(i)
            self.assertEqual(len(d['t']), 5)
            self.assertEqual(d['t'], t)
            self.assertEqual(d['a'], a)
            self.assertEqual(list(d['b']), list(b))
            self.assertEqual(e['t'], t[:i])
            self.assertEqual(e['a'], a[:i])
            self.assertEqual(list(e['b']), list(b[:i]))

        # Normal operation
        tr(2)
        tr(-5)
        tr(30)

        # Partial numpy
        d['b'] = b = np.array(b)
        tr(2)
        tr(-5)
        tr(30)

    def test_keys_like(self):
        # Test the keys_like(query) method.

        d = myokit.DataLog()
        d.set_time_key('t')
        d['t'] = [1, 2, 3, 4]
        v = [0, 0, 0, 0]

        # Zero dimensional variable
        e = d.clone()
        e['v'] = v
        self.assertEqual(e.keys_like('v'), [])

        # Non-existant variable
        self.assertEqual(e.keys_like('w'), [])

        # 1-d
        e = d.clone()
        e['0.v'] = e['1.v'] = e['2.v'] = v
        self.assertEqual(e.keys_like('v'), ['0.v', '1.v', '2.v'])
        e['0.m.v'] = e['1.m.v'] = e['2.m.v'] = v
        self.assertEqual(e.keys_like('m.v'), ['0.m.v', '1.m.v', '2.m.v'])
        e['2.w'] = e['1.w'] = e['0.w'] = v
        self.assertEqual(e.keys_like('w'), ['0.w', '1.w', '2.w'])
        e['20.x'] = e['10.x'] = e['0.x'] = v
        self.assertEqual(e.keys_like('x'), ['0.x', '10.x', '20.x'])

        # 2-d
        e = d.clone()
        e['0.0.m.v'] = e['1.0.m.v'] = e['0.1.m.v'] = e['1.1.m.v'] = v
        self.assertEqual(
            e.keys_like('m.v'),
            ['0.0.m.v', '0.1.m.v', '1.0.m.v', '1.1.m.v'])

    def test_prepare_log_0d(self):
        # Test the `prepare_log` method for single-cell simulations.

        # Test multi-cell log preparing
        from myokit import prepare_log
        m = myokit.load_model(
            os.path.join(DIR_DATA, 'lr-1991-testing.mmt'))

        #
        # 1. Integer flags
        #

        # No variables
        d = prepare_log(myokit.LOG_NONE, m)
        self.assertIsInstance(d, myokit.DataLog)
        self.assertEqual(len(d), 0)

        # States
        d = prepare_log(myokit.LOG_STATE, m)
        self.assertIsInstance(d, myokit.DataLog)
        self.assertEqual(len(d), 8)
        self.assertIn('membrane.V', d)
        self.assertIn('ina.m', d)
        self.assertIn('ina.h', d)
        self.assertIn('ina.j', d)
        self.assertIn('ica.d', d)
        self.assertIn('ica.f', d)
        self.assertIn('ik.x', d)
        self.assertIn('ica.Ca_i', d)
        self.assertNotIn('garbage', d)
        self.assertNotIn('engine.time', d)

        # Internal variables
        d = prepare_log(myokit.LOG_INTER, m)
        self.assertIsInstance(d, myokit.DataLog)
        self.assertIn('membrane.i_stim', d)
        self.assertIn('membrane.i_ion', d)
        self.assertIn('ina.a', d)
        self.assertIn('ina.m.alpha', d)
        self.assertIn('ina.m.beta', d)
        self.assertIn('ina.h.alpha', d)
        self.assertIn('ina.h.beta', d)
        self.assertIn('ina.j.alpha', d)
        self.assertIn('ina.j.beta', d)
        self.assertIn('ina.INa', d)
        self.assertIn('ik.xi', d)
        self.assertIn('ik.x.alpha', d)
        self.assertIn('ik.x.beta', d)
        self.assertIn('ik.IK', d)
        self.assertIn('ikp.IKp', d)
        self.assertIn('ica.E', d)
        self.assertIn('ica.d.alpha', d)
        self.assertIn('ica.d.beta', d)
        self.assertIn('ica.d.beta.va', d)
        self.assertIn('ica.d.beta.vb', d)
        self.assertIn('ica.d.beta.vc', d)
        self.assertIn('ica.d.beta.vc.vd', d)
        self.assertIn('ica.f.alpha', d)
        self.assertIn('ica.f.beta', d)
        self.assertIn('ica.ICa', d)
        self.assertIn('ica.ICa.nest1', d)
        self.assertIn('ica.ICa.nest2', d)
        self.assertIn('ik1.gK1', d)
        self.assertIn('ik1.gK1.alpha', d)
        self.assertIn('ik1.gK1.beta', d)
        self.assertIn('ik1.IK1', d)
        self.assertIn('ib.Ib', d)
        self.assertEqual(len(d), 32)

        # Bound variables
        d = prepare_log(myokit.LOG_BOUND, m)
        self.assertIn('engine.time', d)
        self.assertIn('engine.pace', d)
        self.assertIn('membrane.i_diff', d)
        self.assertEqual(len(d), 3)

        # Combinations
        self.assertEqual(
            len(prepare_log(myokit.LOG_NONE + myokit.LOG_BOUND, m)), 3)
        self.assertEqual(
            len(prepare_log(myokit.LOG_NONE + myokit.LOG_INTER, m)), 32)
        self.assertEqual(
            len(prepare_log(myokit.LOG_BOUND + myokit.LOG_STATE, m)), 11)
        self.assertEqual(
            len(prepare_log(myokit.LOG_STATE + myokit.LOG_INTER, m)), 40)

        #
        # 2. None
        #

        d = prepare_log(None, m, if_empty=myokit.LOG_NONE)
        self.assertIsInstance(d, myokit.DataLog)
        self.assertEqual(len(d), 0)
        d = prepare_log(None, m, if_empty=myokit.LOG_STATE)
        self.assertIsInstance(d, myokit.DataLog)
        self.assertEqual(len(d), 8)

        #
        # 3. List of names
        #

        d = prepare_log(('engine.time', 'membrane.V'), m)
        self.assertEqual(len(d), 2)
        d = prepare_log((
            'engine.time',
            'engine.pace',
            'membrane.V',
            'ina.m',
            'ina.h',
            'ina.j',
            'ica.d',
            'ica.f',
            'ik.x',
            'ica.Ca_i',
            'membrane.i_stim',
            'membrane.i_ion',
            'membrane.i_diff',
            'ina.a',
            'ina.m.alpha',
            'ina.m.beta',
            'ina.h.alpha',
            'ina.h.beta',
            'ina.j.alpha',
            'ina.j.beta',
            'ina.INa',
            'ik.xi',
            'ik.x.alpha',
            'ik.x.beta',
            'ik.IK',
            'ikp.IKp',
            'ica.E',
            'ica.d.alpha',
            'ica.d.beta',
            'ica.d.beta.va',
            'ica.d.beta.vb',
            'ica.d.beta.vc',
            'ica.d.beta.vc.vd',
            'ica.f.alpha',
            'ica.f.beta',
            'ica.ICa',
            'ica.ICa.nest1',
            'ica.ICa.nest2',
            'ik1.gK1',
            'ik1.gK1.alpha',
            'ik1.gK1.beta',
            'ik1.IK1',
            'ib.Ib',), m)
        self.assertIsInstance(d, myokit.DataLog)
        self.assertEqual(len(d), 32 + 8 + 3)
        self.assertIn('engine.time', d)
        self.assertIn('engine.pace', d)
        self.assertIn('membrane.V', d)
        self.assertIn('ina.m', d)
        self.assertIn('ina.h', d)
        self.assertIn('ina.j', d)
        self.assertIn('ica.d', d)
        self.assertIn('ica.f', d)
        self.assertIn('ik.x', d)
        self.assertIn('ica.Ca_i', d)
        self.assertIn('membrane.i_stim', d)
        self.assertIn('ina.a', d)
        self.assertIn('ina.m.alpha', d)
        self.assertIn('ina.m.beta', d)
        self.assertIn('ina.h.alpha', d)
        self.assertIn('ina.h.beta', d)
        self.assertIn('ina.j.alpha', d)
        self.assertIn('ina.j.beta', d)
        self.assertIn('ina.INa', d)
        self.assertIn('ik.xi', d)
        self.assertIn('ik.x.alpha', d)
        self.assertIn('ik.x.beta', d)
        self.assertIn('ik.IK', d)
        self.assertIn('ikp.IKp', d)
        self.assertIn('ica.E', d)
        self.assertIn('ica.d.alpha', d)
        self.assertIn('ica.d.beta', d)
        self.assertIn('ica.d.beta.va', d)
        self.assertIn('ica.d.beta.vb', d)
        self.assertIn('ica.d.beta.vc', d)
        self.assertIn('ica.d.beta.vc.vd', d)
        self.assertIn('ica.f.alpha', d)
        self.assertIn('ica.f.beta', d)
        self.assertIn('ica.ICa', d)
        self.assertIn('ica.ICa.nest1', d)
        self.assertIn('ica.ICa.nest2', d)
        self.assertIn('ik1.gK1', d)
        self.assertIn('ik1.gK1.alpha', d)
        self.assertIn('ik1.gK1.beta', d)
        self.assertIn('ik1.IK1', d)
        self.assertIn('ib.Ib', d)

        # Variables or LhsExpressions in list
        d = prepare_log([m.get('membrane.V')], m)
        self.assertIn('membrane.V', d)
        d = prepare_log([m.get('membrane.V').lhs()], m)
        self.assertIn('dot(membrane.V)', d)

        #
        # 4. Existing log
        #
        # Empty log
        d = prepare_log({}, m)
        self.assertEqual(len(d), 0)
        #
        d = prepare_log({'engine.time': []}, m)
        self.assertIsInstance(d, myokit.DataLog)
        self.assertEqual(len(d), 1)
        self.assertIn('engine.time', d)
        self.assertNotIn('membrane.V', d)
        d = prepare_log({'engine.time': [1, 2, 3]}, m)
        self.assertIsInstance(d, myokit.DataLog)
        self.assertEqual(len(d), 1)
        self.assertIn('engine.time', d)
        self.assertNotIn('membrane.V', d)
        self.assertEqual(len(d['engine.time']), 3)
        d = prepare_log({'engine.time': [1, 2, 3], 'membrane.V': [1, 2, 3]}, m)
        self.assertIsInstance(d, myokit.DataLog)
        self.assertEqual(len(d), 2)
        d = prepare_log(d, m)
        self.assertIsInstance(d, myokit.DataLog)
        d = prepare_log(d, m)
        self.assertIsInstance(d, myokit.DataLog)

        #
        # 5. Errors
        #

        # Disallowed variable types, and explicitly specified variables
        self.assertRaisesRegex(
            ValueError, 'support constants', prepare_log, ['cell.Na_o'], m)
        self.assertRaisesRegex(
            ValueError, 'support state', prepare_log, ['membrane.V'], m,
            allowed_classes=myokit.LOG_BOUND)
        self.assertRaisesRegex(
            ValueError, 'support bound', prepare_log, ['engine.pace'], m,
            allowed_classes=myokit.LOG_STATE)
        self.assertRaisesRegex(
            ValueError, 'support intermediary', prepare_log, ['ina.INa'], m,
            allowed_classes=myokit.LOG_STATE)

        # Empty log argument, but bad `if-empty` argument
        self.assertRaisesRegex(
            ValueError, 'if_empty', prepare_log, None, m,
            if_empty=myokit.LOG_STATE, allowed_classes=myokit.LOG_BOUND)

        # Disallowed variable types, and integer flags for variables
        self.assertRaisesRegex(
            ValueError, 'support state', prepare_log, myokit.LOG_STATE, m,
            allowed_classes=myokit.LOG_BOUND)
        self.assertRaisesRegex(
            ValueError, 'support bound', prepare_log, myokit.LOG_BOUND, m,
            allowed_classes=myokit.LOG_STATE)
        self.assertRaisesRegex(
            ValueError, 'support intermediary', prepare_log, myokit.LOG_INTER,
            m, allowed_classes=myokit.LOG_STATE)
        self.assertRaisesRegex(
            ValueError, 'support time-derivatives', prepare_log,
            myokit.LOG_DERIV, m, allowed_classes=myokit.LOG_STATE)

        # Unknown integer flags
        self.assertRaisesRegex(ValueError, 'unknown flag', prepare_log, -1, m)

        # Unknown variable in log/dict
        d = myokit.DataLog()
        d['bert.bert'] = []
        self.assertRaisesRegex(
            ValueError, 'Unknown variable', prepare_log, d, m)

        # Unsupported time-derivative in log/dict
        d = myokit.DataLog()
        d['dot(membrane.V)'] = []
        self.assertRaisesRegex(
            ValueError, 'derivatives', prepare_log, d, m,
            allowed_classes=myokit.LOG_STATE)

        # Time-derivative of non-state in log/dict
        d = myokit.DataLog()
        d['dot(ina.INa)'] = []
        self.assertRaisesRegex(
            ValueError, 'derivative of non-state', prepare_log, d, m)

        # Log given with objects that we can't append to
        self.assertRaisesRegex(
            ValueError, 'support the append', prepare_log,
            {'membrane.V': 'hi'}, m)

        # Argument `log` doesn't match any of the options
        self.assertRaisesRegex(
            ValueError, 'unexpected type', prepare_log, IOError, m)
        self.assertRaisesRegex(
            ValueError, 'String passed', prepare_log, 'membrane.V', m)

        # Unknown variable in list
        self.assertRaisesRegex(
            ValueError, 'Unknown variable', prepare_log, ['bert.bert'], m)

        # Unsupported time-derivative in list
        self.assertRaisesRegex(
            ValueError, 'derivatives', prepare_log, ['dot(membrane.V)'], m,
            allowed_classes=myokit.LOG_STATE)

        # Time-derivative of non-state in list
        self.assertRaisesRegex(
            ValueError, 'derivative of non-state', prepare_log,
            ['dot(ina.INa)'], m)

    def test_prepare_log_2d(self):
        # Test the `prepare_log` method for 2-dimensional logs.

        # Test multi-cell log preparing
        from myokit import prepare_log
        m = myokit.load_model(
            os.path.join(DIR_DATA, 'lr-1991-testing.mmt'))

        #
        # 1. Integer flags
        #

        # No variables
        d = prepare_log(myokit.LOG_NONE, m, (2, 1))
        self.assertIsInstance(d, myokit.DataLog)
        self.assertEqual(len(d), 0)

        # States
        d = prepare_log(myokit.LOG_STATE, m, (2, 1))
        self.assertIsInstance(d, myokit.DataLog)
        self.assertEqual(len(d), 16)
        self.assertIn('0.0.membrane.V', d)
        self.assertIn('0.0.ina.m', d)
        self.assertIn('0.0.ina.h', d)
        self.assertIn('0.0.ina.j', d)
        self.assertIn('0.0.ica.d', d)
        self.assertIn('0.0.ica.f', d)
        self.assertIn('0.0.ik.x', d)
        self.assertIn('0.0.ica.Ca_i', d)
        self.assertIn('1.0.membrane.V', d)
        self.assertIn('1.0.ina.m', d)
        self.assertIn('1.0.ina.h', d)
        self.assertIn('1.0.ina.j', d)
        self.assertIn('1.0.ica.d', d)
        self.assertIn('1.0.ica.f', d)
        self.assertIn('1.0.ik.x', d)
        self.assertIn('1.0.ica.Ca_i', d)
        self.assertNotIn('membrane.V', d)
        self.assertNotIn('ina.m', d)
        self.assertNotIn('ina.h', d)
        self.assertNotIn('ina.j', d)
        self.assertNotIn('ica.d', d)
        self.assertNotIn('ica.f', d)
        self.assertNotIn('ik.x', d)
        self.assertNotIn('ica.Ca_i', d)
        self.assertNotIn('garbage', d)
        self.assertNotIn('engine.time', d)
        d = prepare_log(myokit.LOG_STATE, m, (2, 2))
        self.assertIsInstance(d, myokit.DataLog)
        self.assertEqual(len(d), 32)
        d = prepare_log(myokit.LOG_STATE, m, (4, 2))
        self.assertIsInstance(d, myokit.DataLog)
        self.assertEqual(len(d), 64)

        # Internal variables
        d = prepare_log(myokit.LOG_INTER, m, (2, 1))
        self.assertIsInstance(d, myokit.DataLog)

        #self.assertEqual(len(d), 64)
        self.assertIn('0.0.membrane.i_stim', d)
        self.assertIn('0.0.membrane.i_ion', d)
        self.assertIn('0.0.ina.a', d)
        self.assertIn('0.0.ina.m.alpha', d)
        self.assertIn('0.0.ina.m.beta', d)
        self.assertIn('0.0.ina.h.alpha', d)
        self.assertIn('0.0.ina.h.beta', d)
        self.assertIn('0.0.ina.j.alpha', d)
        self.assertIn('0.0.ina.j.beta', d)
        self.assertIn('0.0.ina.INa', d)
        self.assertIn('0.0.ik.xi', d)
        self.assertIn('0.0.ik.x.alpha', d)
        self.assertIn('0.0.ik.x.beta', d)
        self.assertIn('0.0.ik.IK', d)
        self.assertIn('0.0.ikp.IKp', d)
        self.assertIn('0.0.ica.E', d)
        self.assertIn('0.0.ica.d.alpha', d)
        self.assertIn('0.0.ica.d.beta', d)
        self.assertIn('0.0.ica.d.beta.va', d)
        self.assertIn('0.0.ica.d.beta.vb', d)
        self.assertIn('0.0.ica.d.beta.vc', d)
        self.assertIn('0.0.ica.d.beta.vc.vd', d)
        self.assertIn('0.0.ica.f.alpha', d)
        self.assertIn('0.0.ica.f.beta', d)
        self.assertIn('0.0.ica.ICa', d)
        self.assertIn('0.0.ica.ICa.nest1', d)
        self.assertIn('0.0.ica.ICa.nest2', d)
        self.assertIn('0.0.ik1.gK1', d)
        self.assertIn('0.0.ik1.gK1.alpha', d)
        self.assertIn('0.0.ik1.gK1.beta', d)
        self.assertIn('0.0.ik1.IK1', d)
        self.assertIn('0.0.ib.Ib', d)
        self.assertIn('1.0.membrane.i_stim', d)
        self.assertIn('1.0.membrane.i_ion', d)
        self.assertIn('1.0.ina.a', d)
        self.assertIn('1.0.ina.m.alpha', d)
        self.assertIn('1.0.ina.m.beta', d)
        self.assertIn('1.0.ina.h.alpha', d)
        self.assertIn('1.0.ina.h.beta', d)
        self.assertIn('1.0.ina.j.alpha', d)
        self.assertIn('1.0.ina.j.beta', d)
        self.assertIn('1.0.ina.INa', d)
        self.assertIn('1.0.ik.xi', d)
        self.assertIn('1.0.ik.x.alpha', d)
        self.assertIn('1.0.ik.x.beta', d)
        self.assertIn('1.0.ik.IK', d)
        self.assertIn('1.0.ikp.IKp', d)
        self.assertIn('1.0.ica.E', d)
        self.assertIn('1.0.ica.d.alpha', d)
        self.assertIn('1.0.ica.d.beta', d)
        self.assertIn('1.0.ica.d.beta.va', d)
        self.assertIn('1.0.ica.d.beta.vb', d)
        self.assertIn('1.0.ica.d.beta.vc', d)
        self.assertIn('1.0.ica.d.beta.vc.vd', d)
        self.assertIn('1.0.ica.f.alpha', d)
        self.assertIn('1.0.ica.f.beta', d)
        self.assertIn('1.0.ica.ICa', d)
        self.assertIn('1.0.ica.ICa.nest1', d)
        self.assertIn('1.0.ica.ICa.nest2', d)
        self.assertIn('1.0.ik1.gK1', d)
        self.assertIn('1.0.ik1.gK1.alpha', d)
        self.assertIn('1.0.ik1.gK1.beta', d)
        self.assertIn('1.0.ik1.IK1', d)
        self.assertIn('1.0.ib.Ib', d)

        # Bound variables
        d = prepare_log(myokit.LOG_BOUND, m, (2, 1))
        self.assertEqual(len(d), 6)
        self.assertIn('0.0.engine.time', d)
        self.assertIn('1.0.engine.time', d)
        self.assertIn('0.0.engine.pace', d)
        self.assertIn('1.0.engine.pace', d)
        self.assertIn('0.0.membrane.i_diff', d)
        self.assertIn('1.0.membrane.i_diff', d)

        # Combinations
        self.assertEqual(
            len(prepare_log(myokit.LOG_NONE + myokit.LOG_BOUND,
                m, (2, 1))), 6)
        self.assertEqual(
            len(prepare_log(myokit.LOG_NONE + myokit.LOG_INTER,
                m, (2, 1))), 64)
        self.assertEqual(
            len(prepare_log(myokit.LOG_BOUND + myokit.LOG_STATE,
                m, (2, 1))), 22)
        self.assertEqual(
            len(prepare_log(myokit.LOG_STATE + myokit.LOG_INTER,
                m, (2, 1))), 80)

        #
        # 1A. Globals and locals
        #
        g = ['engine.time']
        d = prepare_log(myokit.LOG_NONE, m, (2, 1), global_vars=g)
        self.assertIsInstance(d, myokit.DataLog)
        self.assertEqual(len(d), 0)

        # States
        d = prepare_log(myokit.LOG_STATE, m, (2, 1), global_vars=g)
        self.assertIsInstance(d, myokit.DataLog)
        self.assertEqual(len(d), 16)
        self.assertNotIn('engine.time', d)
        d = prepare_log(myokit.LOG_STATE, m, (2, 2), global_vars=g)
        self.assertIsInstance(d, myokit.DataLog)
        self.assertEqual(len(d), 32)
        d = prepare_log(myokit.LOG_STATE, m, (4, 2), global_vars=g)
        self.assertIsInstance(d, myokit.DataLog)
        self.assertEqual(len(d), 64)

        # Internal variables
        d = prepare_log(myokit.LOG_INTER, m, (2, 1), global_vars=g)
        self.assertIsInstance(d, myokit.DataLog)
        self.assertEqual(len(d), 64)

        # Bound variables
        d = prepare_log(myokit.LOG_BOUND, m, (2, 1), global_vars=g)
        self.assertEqual(len(d), 5)
        self.assertIn('engine.time', d)
        self.assertIn('0.0.engine.pace', d)
        self.assertIn('1.0.engine.pace', d)
        self.assertIn('0.0.membrane.i_diff', d)
        self.assertIn('1.0.membrane.i_diff', d)

        # Combinations
        self.assertEqual(
            len(prepare_log(myokit.LOG_NONE + myokit.LOG_BOUND, m, (2, 1),
                global_vars=g)), 5)
        self.assertEqual(
            len(prepare_log(myokit.LOG_NONE + myokit.LOG_INTER, m, (2, 1),
                global_vars=g)), 64)
        self.assertEqual(
            len(prepare_log(myokit.LOG_BOUND + myokit.LOG_STATE, m, (2, 1),
                global_vars=g)), 21)
        self.assertEqual(
            len(prepare_log(myokit.LOG_STATE + myokit.LOG_INTER, m, (2, 1),
                global_vars=g)), 80)

        # Global intermediary variable
        m2 = m.clone()
        x = m2.get('engine').add_variable('x')
        x.set_rhs('5 * pace')
        d = prepare_log(
            myokit.LOG_INTER, m2, (2, 1), global_vars=g + ['engine.x'])
        self.assertIn('engine.x', d)

        #
        # 2. None
        #
        d = prepare_log(None, m, (2, 1), if_empty=myokit.LOG_NONE)
        self.assertIsInstance(d, myokit.DataLog)
        self.assertEqual(len(d), 0)
        d = prepare_log(None, m, (2, 1), if_empty=myokit.LOG_STATE)
        self.assertIsInstance(d, myokit.DataLog)
        self.assertEqual(len(d), 16)

        #
        # 2B. Globals and locals
        #
        d = prepare_log(
            None, m, (2, 1), if_empty=myokit.LOG_NONE, global_vars=g)
        self.assertIsInstance(d, myokit.DataLog)
        self.assertEqual(len(d), 0)
        d = prepare_log(
            None, m, (2, 1), if_empty=myokit.LOG_STATE, global_vars=g)
        self.assertIsInstance(d, myokit.DataLog)
        self.assertEqual(len(d), 16)

        #
        # 3. List of names
        #
        d = prepare_log(('engine.time', 'membrane.V'), m, (2, 1))
        self.assertIsInstance(d, myokit.DataLog)
        self.assertEqual(len(d), 4)
        d = prepare_log((
            'engine.time',
            'engine.pace',
            'membrane.V',
            'ina.m',
            'ina.h',
            'ina.j',
            'ica.d',
            'ica.f',
            'ik.x',
            'ica.Ca_i',
            'membrane.i_stim',
            'ina.a',
            'ina.m.alpha',
            'ina.m.beta',
            'ina.h.alpha',
            'ina.h.beta',
            'ina.j.alpha',
            'ina.j.beta',
            'ina.INa',
            'ik.xi',
            'ik.x.alpha',
            'ik.x.beta',
            'ik.IK',
            'ikp.IKp',
            'ica.E',
            'ica.d.alpha',
            'ica.d.beta',
            'ica.d.beta.va',
            'ica.d.beta.vb',
            'ica.d.beta.vc',
            'ica.d.beta.vc.vd',
            'ica.f.alpha',
            'ica.f.beta',
            'ica.ICa',
            'ica.ICa.nest1',
            'ica.ICa.nest2',
            'ik1.gK1',
            'ik1.gK1.alpha',
            'ik1.gK1.beta',
            'ik1.IK1',
            'ib.Ib',
        ), m, (2, 1))
        self.assertIsInstance(d, myokit.DataLog)
        self.assertEqual(len(d), 2 * (31 + 8 + 2))
        self.assertIn('0.0.engine.time', d)
        self.assertIn('0.0.engine.pace', d)
        self.assertIn('0.0.membrane.V', d)
        self.assertIn('0.0.ina.m', d)
        self.assertIn('0.0.ina.h', d)
        self.assertIn('0.0.ina.j', d)
        self.assertIn('0.0.ica.d', d)
        self.assertIn('0.0.ica.f', d)
        self.assertIn('0.0.ik.x', d)
        self.assertIn('0.0.ica.Ca_i', d)
        self.assertIn('0.0.membrane.i_stim', d)
        self.assertIn('0.0.ina.a', d)
        self.assertIn('0.0.ina.m.alpha', d)
        self.assertIn('0.0.ina.m.beta', d)
        self.assertIn('0.0.ina.h.alpha', d)
        self.assertIn('0.0.ina.h.beta', d)
        self.assertIn('0.0.ina.j.alpha', d)
        self.assertIn('0.0.ina.j.beta', d)
        self.assertIn('0.0.ina.INa', d)
        self.assertIn('0.0.ik.xi', d)
        self.assertIn('0.0.ik.x.alpha', d)
        self.assertIn('0.0.ik.x.beta', d)
        self.assertIn('0.0.ik.IK', d)
        self.assertIn('0.0.ikp.IKp', d)
        self.assertIn('0.0.ica.E', d)
        self.assertIn('0.0.ica.d.alpha', d)
        self.assertIn('0.0.ica.d.beta', d)
        self.assertIn('0.0.ica.d.beta.va', d)
        self.assertIn('0.0.ica.d.beta.vb', d)
        self.assertIn('0.0.ica.d.beta.vc', d)
        self.assertIn('0.0.ica.d.beta.vc.vd', d)
        self.assertIn('0.0.ica.f.alpha', d)
        self.assertIn('0.0.ica.f.beta', d)
        self.assertIn('0.0.ica.ICa', d)
        self.assertIn('0.0.ica.ICa.nest1', d)
        self.assertIn('0.0.ica.ICa.nest2', d)
        self.assertIn('0.0.ik1.gK1', d)
        self.assertIn('0.0.ik1.gK1.alpha', d)
        self.assertIn('0.0.ik1.gK1.beta', d)
        self.assertIn('0.0.ik1.IK1', d)
        self.assertIn('0.0.ib.Ib', d)
        self.assertIn('1.0.engine.time', d)
        self.assertIn('1.0.engine.pace', d)
        self.assertIn('1.0.membrane.V', d)
        self.assertIn('1.0.ina.m', d)
        self.assertIn('1.0.ina.h', d)
        self.assertIn('1.0.ina.j', d)
        self.assertIn('1.0.ica.d', d)
        self.assertIn('1.0.ica.f', d)
        self.assertIn('1.0.ik.x', d)
        self.assertIn('1.0.ica.Ca_i', d)
        self.assertIn('1.0.membrane.i_stim', d)
        self.assertIn('1.0.ina.a', d)
        self.assertIn('1.0.ina.m.alpha', d)
        self.assertIn('1.0.ina.m.beta', d)
        self.assertIn('1.0.ina.h.alpha', d)
        self.assertIn('1.0.ina.h.beta', d)
        self.assertIn('1.0.ina.j.alpha', d)
        self.assertIn('1.0.ina.j.beta', d)
        self.assertIn('1.0.ina.INa', d)
        self.assertIn('1.0.ik.xi', d)
        self.assertIn('1.0.ik.x.alpha', d)
        self.assertIn('1.0.ik.x.beta', d)
        self.assertIn('1.0.ik.IK', d)
        self.assertIn('1.0.ikp.IKp', d)
        self.assertIn('1.0.ica.E', d)
        self.assertIn('1.0.ica.d.alpha', d)
        self.assertIn('1.0.ica.d.beta', d)
        self.assertIn('1.0.ica.d.beta.va', d)
        self.assertIn('1.0.ica.d.beta.vb', d)
        self.assertIn('1.0.ica.d.beta.vc', d)
        self.assertIn('1.0.ica.d.beta.vc.vd', d)
        self.assertIn('1.0.ica.f.alpha', d)
        self.assertIn('1.0.ica.f.beta', d)
        self.assertIn('1.0.ica.ICa', d)
        self.assertIn('1.0.ica.ICa.nest1', d)
        self.assertIn('1.0.ica.ICa.nest2', d)
        self.assertIn('1.0.ik1.gK1', d)
        self.assertIn('1.0.ik1.gK1.alpha', d)
        self.assertIn('1.0.ik1.gK1.beta', d)
        self.assertIn('1.0.ik1.IK1', d)
        self.assertIn('1.0.ib.Ib', d)

        #
        # 3B. Globals and local
        #
        d = prepare_log(
            ('engine.time', 'membrane.V'), m, (2, 1), global_vars=g)
        self.assertIsInstance(d, myokit.DataLog)
        self.assertEqual(len(d), 3)
        self.assertIn('engine.time', d)
        self.assertIn('0.0.membrane.V', d)
        self.assertIn('1.0.membrane.V', d)
        d = prepare_log(
            ('engine.time', '0.0.membrane.V'),
            m, (2, 1), global_vars=g)
        self.assertIsInstance(d, myokit.DataLog)
        self.assertEqual(len(d), 2)
        self.assertIn('engine.time', d)
        self.assertIn('0.0.membrane.V', d)
        d = prepare_log(
            ('engine.time', '0.0.membrane.V', '1.0.membrane.V'),
            m, (2, 1), global_vars=g)
        self.assertEqual(len(d), 3)
        self.assertIn('engine.time', d)
        self.assertIn('0.0.membrane.V', d)
        self.assertIn('1.0.membrane.V', d)
        d = prepare_log(
            ('engine.time', '0.0.membrane.V', 'membrane.V'),
            m, (2, 1), global_vars=g)
        self.assertEqual(len(d), 3)
        self.assertIn('engine.time', d)
        self.assertIn('0.0.membrane.V', d)
        self.assertIn('1.0.membrane.V', d)
        d = prepare_log(
            ('engine.time', 'membrane.V', '0.0.membrane.V'),
            m, (2, 1), global_vars=g)
        self.assertEqual(len(d), 3)
        self.assertIn('engine.time', d)
        self.assertIn('0.0.membrane.V', d)
        self.assertIn('1.0.membrane.V', d)

        #
        # 4. Existing log
        #
        # Empty log
        d = prepare_log({}, m)
        self.assertEqual(len(d), 0)
        #
        d = prepare_log({'1.0.engine.time': []}, m, (2, 1))
        self.assertIsInstance(d, myokit.DataLog)
        self.assertEqual(len(d), 1)
        self.assertIn('1.0.engine.time', d)
        self.assertNotIn('membrane.V', d)
        d = prepare_log({'0.0.engine.time': [1, 2, 3]}, m, (2, 1))
        self.assertIsInstance(d, myokit.DataLog)
        self.assertEqual(len(d), 1)
        self.assertIn('0.0.engine.time', d)
        self.assertNotIn('0.0.membrane.V', d)
        self.assertNotIn('engine.time', d)
        self.assertEqual(len(d['0.0.engine.time']), 3)
        d = prepare_log(
            {'0.0.engine.time': [1, 2, 3], '1.0.membrane.V': [1, 2, 3]},
            m, (2, 1))
        self.assertIsInstance(d, myokit.DataLog)
        self.assertEqual(len(d), 2)
        d = prepare_log(d, m, (2, 1))
        self.assertIsInstance(d, myokit.DataLog)
        d = prepare_log(d, m, (2, 1))
        self.assertIsInstance(d, myokit.DataLog)

        #
        # 4B. Existing log, globals and local
        #
        d = prepare_log({'engine.time': [1, 2, 3]}, m, (2, 1), global_vars=g)
        self.assertIsInstance(d, myokit.DataLog)
        self.assertEqual(len(d), 1)
        self.assertIn('engine.time', d)
        self.assertEqual(len(d['engine.time']), 3)
        d = prepare_log(
            {'engine.time': [1, 2, 3], '1.0.membrane.V': [1, 2, 3]},
            m, (2, 1), global_vars=g)
        self.assertIsInstance(d, myokit.DataLog)
        self.assertEqual(len(d), 2)
        d = prepare_log(d, m, (2, 1), global_vars=g)
        self.assertIsInstance(d, myokit.DataLog)
        d = prepare_log(d, m, (2, 1), global_vars=g)
        self.assertIsInstance(d, myokit.DataLog)

        #
        # 5. Errors
        #

        # Unknown global variable
        self.assertRaisesRegex(
            ValueError, 'Unknown variable specified in global', prepare_log,
            myokit.LOG_NONE, m, (2, 1), global_vars=['michael'])

        # State passed as global variable
        self.assertRaisesRegex(
            ValueError, 'State cannot be global', prepare_log, myokit.LOG_NONE,
            m, (2, 1), global_vars=['membrane.V'])

        # Index specified for global variable in log/dict
        self.assertRaisesRegex(
            ValueError, 'index for global', prepare_log,
            {'0.0.engine.time': []}, m, (2, 1), global_vars=['engine.time'])

        # Invalid index for variable in log/dict
        self.assertRaisesRegex(
            ValueError, 'Invalid index', prepare_log, {'3.3.membrane.V': []},
            m, (2, 1))

        # No index for variable that needs it, in log/dict
        self.assertRaisesRegex(
            ValueError, 'non-indexed entry', prepare_log, {'membrane.V': []},
            m, (2, 1))

        # Index specified for global variable in list
        self.assertRaisesRegex(
            ValueError, 'index for global', prepare_log,
            ['0.0.engine.time'], m, (2, 1), global_vars=['engine.time'])

        # Invalid index for variable in list
        self.assertRaisesRegex(
            ValueError, 'Invalid index', prepare_log, ['3.3.membrane.V'], m,
            (2, 1))

    def test_save(self):
        # Test saving in binary format.

        d = myokit.DataLog()
        d['a.b'] = np.arange(0, 100, dtype=np.float32)
        d['c.d'] = np.sqrt(np.arange(0, 100) * 1.2)

        # Test saving with double precision
        with TemporaryDirectory() as td:
            fname = td.path('test.bin')
            d.save(fname)
            e = myokit.DataLog.load(fname)
            self.assertFalse(d is e)
            self.assertEqual(len(d), len(e))
            self.assertIn('a.b', e)
            self.assertIn('c.d', e)
            self.assertNotIn('a.d', e)
            self.assertEqual(len(d['a.b']), len(e['a.b']))
            self.assertEqual(len(d['c.d']), len(e['c.d']))
            self.assertEqual(list(d['a.b']), list(e['a.b']))
            self.assertEqual(list(d['c.d']), list(e['c.d']))
            self.assertTrue(isinstance(d['a.b'][0], np.float32))
            self.assertTrue(isinstance(d['c.d'][0], float))
            self.assertTrue(isinstance(e['a.b'][0], float))
            self.assertTrue(isinstance(e['c.d'][0], float))
            self.assertEqual(e['a.b'].typecode, 'd')
            self.assertEqual(e['c.d'].typecode, 'd')

        # Test saving with single precision
        d = myokit.DataLog()
        d.set_time_key('c.d')
        d['a.b'] = np.arange(0, 100, dtype=np.float32)
        d['c.d'] = np.sqrt(np.arange(0, 100, dtype=np.float32) * 1.2)
        with TemporaryDirectory() as td:
            fname = td.path('test.bin')
            d.save(fname, precision=myokit.SINGLE_PRECISION)
            e = myokit.DataLog.load(fname)
            self.assertFalse(d is e)
            self.assertEqual(len(d), len(e))
            self.assertIn('a.b', e)
            self.assertIn('c.d', e)
            self.assertNotIn('a.d', e)
            self.assertEqual(len(d['a.b']), len(e['a.b']))
            self.assertEqual(len(d['c.d']), len(e['c.d']))
            self.assertEqual(list(d['a.b']), list(e['a.b']))
            self.assertEqual(list(d['c.d']), list(e['c.d']))
            self.assertTrue(isinstance(d['a.b'][0], np.float32))
            self.assertTrue(isinstance(d['c.d'][0], np.float32))
            self.assertTrue(isinstance(e['a.b'][0], float))
            self.assertTrue(isinstance(e['c.d'][0], float))
            self.assertEqual(e['a.b'].typecode, 'f')
            self.assertEqual(e['c.d'].typecode, 'f')
            self.assertEqual(e.time_key(), 'c.d')
            self.assertTrue(np.all(e.time() == d.time()))
            self.assertTrue(np.all(e.time() == d['c.d']))

    def test_load_errors(self):
        # Test if the correct load errors are raised.

        # Missing data file
        path = os.path.join(DIR_IO, 'badlog-1-no-data.zip')
        self.assertRaisesRegex(
            myokit.DataLogReadError, 'log file format', myokit.DataLog.load,
            path)

        # Missing structure file
        path = os.path.join(DIR_IO, 'badlog-2-no-structure.zip')
        self.assertRaisesRegex(
            myokit.DataLogReadError, 'log file format', myokit.DataLog.load,
            path)

        # Not a zip
        path = os.path.join(DIR_IO, 'badlog-3-not-a-zip.zip')
        self.assertRaisesRegex(
            myokit.DataLogReadError, 'bad zip file', myokit.DataLog.load, path)

        # Wrong number of fields
        path = os.path.join(DIR_IO, 'badlog-4-invalid-n-fields.zip')
        self.assertRaisesRegex(
            myokit.DataLogReadError, 'number of fields', myokit.DataLog.load,
            path)

        # Negative data size
        path = os.path.join(DIR_IO, 'badlog-5-invalid-data-size.zip')
        self.assertRaisesRegex(
            myokit.DataLogReadError, 'Invalid data size', myokit.DataLog.load,
            path)

        # Unknown data type
        path = os.path.join(DIR_IO, 'badlog-6-bad-data-type.zip')
        self.assertRaisesRegex(
            myokit.DataLogReadError, 'Invalid data type', myokit.DataLog.load,
            path)

        # Not enough data
        path = os.path.join(DIR_IO, 'badlog-7-not-enough-data.zip')
        self.assertRaisesRegex(
            myokit.DataLogReadError, 'larger data', myokit.DataLog.load, path)

    def test_load_with_progress(self):
        # Test loading with a progress reporter.

        p = TestReporter()
        path = os.path.join(DIR_IO, 'goodlog.zip')
        self.assertFalse(p.entered)
        self.assertFalse(p.exited)
        self.assertFalse(p.updated)
        d = myokit.DataLog.load(path, progress=p)
        self.assertTrue(p.entered)
        self.assertTrue(p.exited)
        self.assertTrue(p.updated)
        self.assertEqual(type(d), myokit.DataLog)

        p = CancellingReporter(1)
        d = myokit.DataLog.load(path, progress=p)
        self.assertIsNone(d)

    def test_save_csv(self):
        # Test saving as csv.

        d = myokit.DataLog()

        # Note: a.b and e.f are both non-decreaing, could be taken for time!
        d['a.b'] = np.arange(0, 100)
        d['c.d'] = np.sqrt(np.arange(0, 100) * 1.2)
        d['e.f'] = np.arange(0, 100) + 1
        with TemporaryDirectory() as td:
            fname = td.path('test.csv')
            d.save_csv(fname)
            e = myokit.DataLog.load_csv(fname)
            self.assertEqual(len(d), len(e))
            self.assertIn('a.b', e)
            self.assertIn('c.d', e)
            self.assertNotIn('a.d', e)
            self.assertEqual(len(d['a.b']), len(e['a.b']))
            self.assertEqual(len(d['c.d']), len(e['c.d']))
            self.assertEqual(list(d['a.b']), list(e['a.b']))
            self.assertEqual(list(d['c.d']), list(e['c.d']))

        # No time key set, will think a.b is time
        self.assertEqual(e.time()[0], d['a.b'][0])

        # Now set time key
        d.set_time_key('a.b')
        with TemporaryDirectory() as td:
            fname = td.path('test.csv')
            d.save_csv(fname)
            e = myokit.DataLog.load_csv(fname)
            self.assertEqual(e.time()[0], d['a.b'][0])

        # Now set time key
        d.set_time_key('e.f')
        with TemporaryDirectory() as td:
            fname = td.path('test.csv')
            d.save_csv(fname)
            e = myokit.DataLog.load_csv(fname)
            self.assertEqual(e.time()[0], d['e.f'][0])

        # Test saving with single precision
        d = myokit.DataLog(time='a.b')
        d['a.b'] = np.arange(0, 100)
        d['c.d'] = np.sqrt(np.arange(0, 100) * 1.2)
        d['e.f'] = np.arange(0, 100) + 1
        d = d.npview()
        with TemporaryDirectory() as td:
            fname = td.path('test.csv')
            d.save_csv(fname, precision=myokit.SINGLE_PRECISION)
            e = myokit.DataLog.load_csv(fname).npview()
            self.assertEqual(len(d), len(e))
            self.assertIn('a.b', e)
            self.assertIn('c.d', e)
            self.assertNotIn('a.d', e)
            self.assertEqual(len(d['a.b']), len(e['a.b']))
            self.assertEqual(len(d['c.d']), len(e['c.d']))
            self.assertTrue(np.all(np.abs(d['a.b'] - e['a.b']) < 1e-6))
            self.assertTrue(np.all(np.abs(d['c.d'] - e['c.d']) < 1e-6))

        # Test saving with python string formats
        d = myokit.DataLog(time='a.b')
        d['a.b'] = np.arange(0, 100)
        d['c.d'] = np.sqrt(np.arange(0, 100) * 1.2)
        d['e.f'] = np.arange(0, 100) + 1
        with TemporaryDirectory() as td:
            fname = td.path('test.csv')
            d.save_csv(fname, precision=None)
            e = myokit.DataLog.load_csv(fname)
            self.assertEqual(len(d), len(e))
            self.assertIn('a.b', e)
            self.assertIn('c.d', e)
            self.assertNotIn('a.d', e)
            self.assertEqual(len(d['a.b']), len(e['a.b']))
            self.assertEqual(len(d['c.d']), len(e['c.d']))
            self.assertTrue(np.all(np.abs(d['a.b'] - e['a.b']) < 1e-6))
            self.assertTrue(np.all(np.abs(d['c.d'] - e['c.d']) < 1e-6))

        # Test invalid precision arguments
        with TemporaryDirectory() as td:
            fname = td.path('test.csv')
            self.assertRaises(ValueError, d.save_csv, fname, 'ernie')

        # Test saving with a fixed order
        d = myokit.DataLog(time='a.b')
        d['a.b'] = np.arange(0, 100)
        d['c.d'] = np.sqrt(np.arange(0, 100) * 1.2)
        d['e.f'] = np.arange(0, 100) + 1
        with TemporaryDirectory() as td:
            fname = td.path('test.csv')
            d.save_csv(fname, order=['a.b', 'c.d', 'e.f'])
            with uopen(fname) as f:
                header = f.readline()
            self.assertEqual(header, '"a.b","c.d","e.f"\n')

            d.save_csv(fname, order=['e.f', 'a.b', 'c.d'])
            with uopen(fname) as f:
                header = f.readline()
            self.assertEqual(header, '"e.f","a.b","c.d"\n')

            # Test invalid order
            self.assertRaises(
                ValueError, d.save_csv, fname, order=['e.f', 'a.b', 'c.e'])

        # Test saving with a natural sort order
        d = myokit.DataLog(time='e.t')
        d['e.t'] = np.arange(10)
        d['1.z.a'] = np.arange(10) * 1
        d['0.z.a'] = np.arange(10) * 0
        d['20.z.a'] = np.arange(10) * 20
        d['101.z.a'] = np.arange(10) * 101
        d['100.z.a'] = np.arange(10) * 100
        d['2.z.a'] = np.arange(10) * 2
        d['11.z.a'] = np.arange(10) * 11
        d['14.z.a'] = np.arange(10) * 10
        with TemporaryDirectory() as td:
            fname = td.path('test.csv')
            d.save_csv(fname)
            with uopen(fname) as f:
                order = [x[1:-1] for x in f.readline().strip().split(',')]
            self.assertEqual(len(order), 9)
            self.assertEqual(order[0], 'e.t')
            self.assertEqual(order[1], '0.z.a')
            self.assertEqual(order[2], '1.z.a')
            self.assertEqual(order[3], '2.z.a')
            self.assertEqual(order[4], '11.z.a')
            self.assertEqual(order[5], '14.z.a')
            self.assertEqual(order[6], '20.z.a')
            self.assertEqual(order[7], '100.z.a')
            self.assertEqual(order[8], '101.z.a')

        # Test saving and loading empty log
        d = myokit.DataLog()
        with TemporaryDirectory() as td:
            fname = td.path('test.csv')
            d.save_csv(fname)
            e = myokit.DataLog.load_csv(fname)
            self.assertEqual(len(e.keys()), 0)

    def test_load_csv_errors(self):
        # Test for errors during csv loading.

        # Test errory file, with comments etc., should work fine!
        path = os.path.join(DIR_IO, 'datalog.csv')
        d = myokit.DataLog.load_csv(path).npview()
        self.assertEqual(set(d.keys()), set(['time', 'v']))
        self.assertTrue(np.all(d['time'] == (1 + np.arange(6))))
        self.assertTrue(np.all(d['v'] == 10 * (1 + np.arange(6))))

        # Empty file
        path = os.path.join(DIR_IO, 'datalog-1-empty.csv')
        d = myokit.DataLog.load_csv(path)
        self.assertEqual(set(d.keys()), set())

        # Test windows line endings
        path = os.path.join(DIR_IO, 'datalog-2-windows.csv')
        d = myokit.DataLog.load_csv(path).npview()
        self.assertEqual(set(d.keys()), set(['time', 'v']))
        self.assertTrue(np.all(d['time'] == (1 + np.arange(6))))
        self.assertTrue(np.all(d['v'] == 10 * (1 + np.arange(6))))

        # Test old mac line endings
        path = os.path.join(DIR_IO, 'datalog-3-old-mac.csv')
        d = myokit.DataLog.load_csv(path).npview()
        self.assertEqual(set(d.keys()), set(['time', 'v']))
        self.assertTrue(np.all(d['time'] == (1 + np.arange(6))))
        self.assertTrue(np.all(d['v'] == 10 * (1 + np.arange(6))))

        # Test empty lines at end
        path = os.path.join(DIR_IO, 'datalog-4-empty-lines.csv')
        d = myokit.DataLog.load_csv(path).npview()
        self.assertEqual(set(d.keys()), set(['time', 'v']))
        self.assertTrue(np.all(d['time'] == (1 + np.arange(6))))
        self.assertTrue(np.all(d['v'] == 10 * (1 + np.arange(6))))

        # Test semicolons at end of each line
        path = os.path.join(DIR_IO, 'datalog-5-semicolons.csv')
        d = myokit.DataLog.load_csv(path).npview()
        self.assertEqual(set(d.keys()), set(['time', 'v']))
        self.assertTrue(np.all(d['time'] == (1 + np.arange(6))))
        self.assertTrue(np.all(d['v'] == 10 * (1 + np.arange(6))))

        # Test unterminated string
        path = os.path.join(DIR_IO, 'datalog-6-open-string.csv')
        self.assertRaisesRegex(
            myokit.DataLogReadError, 'inside quoted', myokit.DataLog.load_csv,
            path)

        # Test empty lines between data
        path = os.path.join(DIR_IO, 'datalog-7-empty-lines-2.csv')
        d = myokit.DataLog.load_csv(path)
        self.assertEqual(set(d.keys()), set(['time', 'v']))
        self.assertTrue(np.all(d['time'] == np.arange(1, 7)))
        self.assertTrue(np.all(d['v'] == 10 * (np.arange(1, 7))))

        # Test unquoted field names
        path = os.path.join(DIR_IO, 'datalog-8-unquoted-header.csv')
        d = myokit.DataLog.load_csv(path).npview()
        self.assertEqual(set(d.keys()), set(['time', 'v']))
        self.assertTrue(np.all(d['time'] == (1 + np.arange(6))))
        self.assertTrue(np.all(d['v'] == 10 * (1 + np.arange(6))))

        # Test double-quoted field names
        path = os.path.join(DIR_IO, 'datalog-9-double-quoted-header.csv')
        d = myokit.DataLog.load_csv(path).npview()
        self.assertEqual(set(d.keys()), set(['time', 'v"quote"']))
        self.assertTrue(np.all(d['time'] == (1 + np.arange(6))))
        self.assertTrue(np.all(d['v"quote"'] == 10 * (1 + np.arange(6))))

        # Test file with just some spaces (one line)
        path = os.path.join(DIR_IO, 'datalog-10-just-spaces.csv')
        d = myokit.DataLog.load_csv(path).npview()
        self.assertEqual(set(d.keys()), set())

        # Test file with just some spaces (one line)
        path = os.path.join(DIR_IO, 'datalog-11-just-a-semicolon.csv')
        d = myokit.DataLog.load_csv(path).npview()
        self.assertEqual(set(d.keys()), set())

        # Test header "abc"x"adc"
        path = os.path.join(DIR_IO, 'datalog-12-bad-header.csv')
        self.assertRaisesRegex(
            myokit.DataLogReadError, 'Expecting double quote',
            myokit.DataLog.load_csv, path)

        # Test empty field "" in header
        path = os.path.join(DIR_IO, 'datalog-13-header-with-empty-1.csv')
        self.assertRaisesRegex(
            myokit.DataLogReadError, 'Empty field', myokit.DataLog.load_csv,
            path)

        # Test empty field "x",,"y" in header
        path = os.path.join(DIR_IO, 'datalog-14-header-with-empty-2.csv')
        self.assertRaisesRegex(
            myokit.DataLogReadError, 'Empty field', myokit.DataLog.load_csv,
            path)

        # Test empty field "time","v", in header
        path = os.path.join(DIR_IO, 'datalog-15-header-with-empty-3.csv')
        self.assertRaisesRegex(
            myokit.DataLogReadError, 'Empty field', myokit.DataLog.load_csv,
            path)

        # Test wrong field count in data
        path = os.path.join(DIR_IO, 'datalog-16-wrong-columns-in-data.csv')
        self.assertRaisesRegex(
            myokit.DataLogReadError, 'Wrong number of columns',
            myokit.DataLog.load_csv, path)

        # Test non-float data
        path = os.path.join(DIR_IO, 'datalog-17-non-float-data.csv')
        self.assertRaisesRegex(
            myokit.DataLogReadError, 'Unable to convert',
            myokit.DataLog.load_csv, path)

    def test_split(self):
        # Test the split function.

        var1 = 'engine.toom'
        var2 = 'membrane.V'
        x = myokit.DataLog({
            var1: [0, 5, 10, 15, 20],
            var2: [1, 2, 3, 4, 5],
        })
        x.set_time_key(var1)

        def split(value):
            s1, s2 = x.split(value)
            return (
                list(s1[var1]),
                list(s2[var1]),
                list(s1[var2]),
                list(s2[var2])
            )

        for i in range(2):
            # First without, then with numpy
            t1, t2, v1, v2 = split(-5)
            self.assertEqual(t1, [])
            self.assertEqual(t2, [0, 5, 10, 15, 20])
            self.assertEqual(v1, [])
            self.assertEqual(v2, [1, 2, 3, 4, 5])
            t1, t2, v1, v2 = split(0)
            self.assertEqual(t1, [])
            self.assertEqual(t2, [0, 5, 10, 15, 20])
            self.assertEqual(v1, [])
            self.assertEqual(v2, [1, 2, 3, 4, 5])
            t1, t2, v1, v2 = split(2)
            self.assertEqual(t1, [0])
            self.assertEqual(t2, [5, 10, 15, 20])
            self.assertEqual(v1, [1])
            self.assertEqual(v2, [2, 3, 4, 5])
            t1, t2, v1, v2 = split(5)
            self.assertEqual(t1, [0])
            self.assertEqual(t2, [5, 10, 15, 20])
            self.assertEqual(v1, [1])
            self.assertEqual(v2, [2, 3, 4, 5])
            t1, t2, v1, v2 = split(7)
            self.assertEqual(t1, [0, 5])
            self.assertEqual(t2, [10, 15, 20])
            self.assertEqual(v1, [1, 2])
            self.assertEqual(v2, [3, 4, 5])
            t1, t2, v1, v2 = split(10)
            self.assertEqual(t1, [0, 5])
            self.assertEqual(t2, [10, 15, 20])
            self.assertEqual(v1, [1, 2])
            self.assertEqual(v2, [3, 4, 5])
            t1, t2, v1, v2 = split(13)
            self.assertEqual(t1, [0, 5, 10])
            self.assertEqual(t2, [15, 20])
            self.assertEqual(v1, [1, 2, 3])
            self.assertEqual(v2, [4, 5])
            t1, t2, v1, v2 = split(15)
            self.assertEqual(t1, [0, 5, 10])
            self.assertEqual(t2, [15, 20])
            self.assertEqual(v1, [1, 2, 3])
            self.assertEqual(v2, [4, 5])
            t1, t2, v1, v2 = split(17)
            self.assertEqual(t1, [0, 5, 10, 15])
            self.assertEqual(t2, [20])
            self.assertEqual(v1, [1, 2, 3, 4])
            self.assertEqual(v2, [5])
            t1, t2, v1, v2 = split(20)
            self.assertEqual(t1, [0, 5, 10, 15])
            self.assertEqual(t2, [20])
            self.assertEqual(v1, [1, 2, 3, 4])
            self.assertEqual(v2, [5])
            t1, t2, v1, v2 = split(22)
            self.assertEqual(t1, [0, 5, 10, 15, 20])
            self.assertEqual(t2, [])
            self.assertEqual(v1, [1, 2, 3, 4, 5])
            self.assertEqual(v2, [])
            x = x.npview()

    def test_split_periodic(self):
        # Test the split_periodic() function.

        tvar = 'engine.toime'
        vvar = 'membrane.V'
        s1 = myokit.DataLog({
            tvar: [0, 500, 999, 1500, 1600, 1700, 2000],
            vvar: [0, 5, 9.99, 15, 16, 17, 20]})
        s1.set_time_key(tvar)
        s2 = myokit.DataLog({
            tvar: [0, 500, 999, 1500, 1600, 1700, 2000, 2001],
            vvar: [0, 5, 9.99, 15, 16, 17, 20, 20.01]})
        s2.set_time_key(tvar)
        n1 = s1.npview()
        n2 = s2.npview()

        # Test default parameters
        #   - endpoint in data
        #   - no split point in data
        logs = s1.split_periodic(1000)
        nlogs = len(logs)
        self.assertEqual(nlogs, 2)
        for var in [tvar, vvar]:
            for log in logs:
                self.assertTrue(var in log)
        self.assertTrue(logs[0][tvar] == [0, 500, 999])
        self.assertTrue(logs[1][tvar] == [1500, 1600, 1700, 2000])

        # Same but now with numpy logs
        logs = n1.split_periodic(1000)
        nlogs = len(logs)
        self.assertEqual(nlogs, 2)
        for var in [tvar, vvar]:
            for log in logs:
                self.assertTrue(var in log)
        self.assertTrue(np.array_equal(logs[0][tvar], np.array([0, 500, 999])))
        self.assertTrue(
            np.array_equal(logs[1][tvar], np.array([1500, 1600, 1700, 2000])))

        # Test default parameters
        #   - no endpoint in data
        #   - split point in data
        logs = s2.split_periodic(1000)
        nlogs = len(logs)
        self.assertEqual(nlogs, 3)
        for var in [tvar, vvar]:
            for log in logs:
                self.assertTrue(var in log)
        self.assertTrue(logs[0][tvar] == [0, 500, 999])
        self.assertTrue(logs[1][tvar] == [1500, 1600, 1700, 2000])
        self.assertTrue(logs[2][tvar] == [2000, 2001])

        # Same but now with numpy logs
        logs = n2.split_periodic(1000)
        nlogs = len(logs)
        self.assertEqual(nlogs, 3)
        for var in [tvar, vvar]:
            for log in logs:
                self.assertTrue(var in log)
        self.assertTrue(np.array_equal(logs[0][tvar], np.array([0, 500, 999])))
        self.assertTrue(np.array_equal(
            logs[1][tvar], np.array([1500, 1600, 1700, 2000])))
        self.assertTrue(np.array_equal(logs[2][tvar], np.array([2000, 2001])))

        # Test with half-closed intervals
        #   - endpoint in data
        #   - no split point in data
        logs = s1.split_periodic(1000, closed_intervals=False)
        nlogs = len(logs)
        self.assertEqual(nlogs, 2)
        for var in [tvar, vvar]:
            for log in logs:
                self.assertTrue(var in log)
        self.assertTrue(logs[0][tvar] == [0, 500, 999])
        self.assertTrue(logs[1][tvar] == [1500, 1600, 1700])

        # Same but now with numpy logs
        logs = n1.split_periodic(1000, closed_intervals=False)
        nlogs = len(logs)
        self.assertEqual(nlogs, 2)
        for var in [tvar, vvar]:
            for log in logs:
                self.assertTrue(var in log)
        self.assertTrue(np.array_equal(logs[0][tvar], np.array([0, 500, 999])))
        self.assertTrue(
            np.array_equal(logs[1][tvar], np.array([1500, 1600, 1700])))

        # Test with half-closed intervals
        #   - no endpoint in data
        #   - split point in data
        logs = s2.split_periodic(1000, closed_intervals=False)
        nlogs = len(logs)
        self.assertEqual(nlogs, 3)
        for var in [tvar, vvar]:
            for log in logs:
                self.assertTrue(var in log)
        self.assertTrue(logs[0][tvar] == [0, 500, 999])
        self.assertTrue(logs[1][tvar] == [1500, 1600, 1700])
        self.assertTrue(logs[2][tvar] == [2000, 2001])

        # Same but now with numpy logs
        logs = n2.split_periodic(1000, closed_intervals=False)
        nlogs = len(logs)
        self.assertEqual(nlogs, 3)
        for var in [tvar, vvar]:
            for log in logs:
                self.assertTrue(var in log)
        self.assertTrue(np.array_equal(logs[0][tvar], np.array([0, 500, 999])))
        self.assertTrue(
            np.array_equal(logs[1][tvar], np.array([1500, 1600, 1700])))
        self.assertTrue(np.array_equal(logs[2][tvar], np.array([2000, 2001])))

        # Test with normalized time
        logs = s2.split_periodic(1000, adjust=True)
        nlogs = len(logs)
        self.assertEqual(nlogs, 3)
        for var in [tvar, vvar]:
            for log in logs:
                self.assertTrue(var in log)
        self.assertTrue(logs[0][tvar] == [0, 500, 999])
        self.assertTrue(logs[1][tvar] == [500, 600, 700, 1000])
        self.assertTrue(logs[2][tvar] == [0, 1])

        # Same but now with numpy logs
        logs = n2.split_periodic(1000, adjust=True)
        nlogs = len(logs)
        self.assertEqual(nlogs, 3)
        for var in [tvar, vvar]:
            for log in logs:
                self.assertTrue(var in log)
        self.assertTrue(np.array_equal(logs[0][tvar], np.array([0, 500, 999])))
        self.assertTrue(
            np.array_equal(logs[1][tvar], np.array([500, 600, 700, 1000])))
        self.assertTrue(np.array_equal(logs[2][tvar], np.array([0, 1])))

        # Test on empty log
        d = myokit.DataLog(time='t')
        self.assertRaises(myokit.InvalidDataLogError, d.split_periodic, 100)
        d['t'] = []
        self.assertRaises(RuntimeError, d.split_periodic, 10)

        # Test negative period
        d['t'] = [1, 2, 3, 4]
        self.assertRaises(ValueError, d.split_periodic, 0)
        self.assertRaises(ValueError, d.split_periodic, -1)

        # Test larger period than log data
        d['x'] = [4, 5, 6, 7]
        e = d.split_periodic(100)
        self.assertEqual(set(d.keys()), set(e.keys()))
        self.assertFalse(d is e)

    def test_trim(self):
        # Test the trim() method.

        d = myokit.DataLog()
        d.set_time_key('t')
        d['t'] = t = [0, 0.1, 0.2, 0.3, 0.4]
        d['a'] = a = [1, 2, 3, 4, 5]
        d['b'] = b = [10, 20, 30, 40, 50]

        # Test function
        def tr(i, j, m, n):
            e = d.trim(i, j)
            self.assertEqual(len(d['t']), 5)
            self.assertEqual(d['t'], t)
            self.assertEqual(d['a'], a)
            self.assertEqual(list(d['b']), list(b))
            self.assertEqual(e['t'], t[m:n])
            self.assertEqual(e['a'], a[m:n])
            self.assertEqual(list(e['b']), list(b[m:n]))

        # Normal operation
        tr(0.1, 0.3, 1, 3)
        tr(-5, 0.3, -5, 3)
        tr(0.2, 30, 2, 30)
        tr(-10, 40, -10, 40)

        # Partial numpy
        d['b'] = b = np.array(b)
        tr(0.1, 0.3, 1, 3)
        tr(-5, 0.3, -5, 3)
        tr(0.2, 30, 2, 30)
        tr(-10, 40, -10, 40)

        # Without adjustment
        d = myokit.DataLog(time='t')
        d['t'] = [1, 2, 3, 4, 5]
        d['v'] = [10, 20, 30, 40, 50]
        e = d.trim(2, 5, adjust=False)
        self.assertEqual(len(e['t']), 3)
        self.assertEqual(len(e['v']), 3)
        self.assertEqual(e['t'], [2, 3, 4])
        self.assertEqual(e['v'], [20, 30, 40])

        # With adjustment
        d = myokit.DataLog(time='t')
        d['t'] = [1, 2, 3, 4, 5]
        d['v'] = [10, 20, 30, 40, 50]
        e = d.trim(2, 5, adjust=True)
        self.assertEqual(len(e['t']), 3)
        self.assertEqual(len(e['v']), 3)
        self.assertEqual(e['t'], [0, 1, 2])
        self.assertEqual(e['v'], [20, 30, 40])

        # Without adjustment, numpy
        d = myokit.DataLog(time='t')
        d['t'] = [1, 2, 3, 4, 5]
        d['v'] = [10, 20, 30, 40, 50]
        d = d.npview()
        e = d.trim(2, 5, adjust=True)
        self.assertEqual(len(e['t']), 3)
        self.assertEqual(len(e['v']), 3)
        self.assertTrue(np.all(e['t'] == [0, 1, 2]))
        self.assertTrue(np.all(e['v'] == [20, 30, 40]))

    def test_trim_left(self):
        # Test the trim_left function.

        var1 = 'engine.toom'
        var2 = 'membrane.V'
        adjust = False
        wnumpy = False

        def trim(value):
            x = myokit.DataLog({
                var1: [0, 5, 10, 15, 20],
                var2: [1, 2, 3, 4, 5],
            })
            x.set_time_key(var1)
            if wnumpy:
                x = x.npview()
            y = x.trim_left(value, adjust=adjust)
            self.assertEqual(len(x[var1]), 5)
            self.assertEqual(len(x[var2]), 5)
            return list(y[var1]), list(y[var2])

        t, v = trim(-5)
        self.assertEqual(t, [0, 5, 10, 15, 20])
        self.assertEqual(v, [1, 2, 3, 4, 5])
        t, v = trim(0)
        self.assertEqual(t, [0, 5, 10, 15, 20])
        self.assertEqual(v, [1, 2, 3, 4, 5])
        t, v = trim(2)
        self.assertEqual(t, [5, 10, 15, 20])
        self.assertEqual(v, [2, 3, 4, 5])
        t, v = trim(5)
        self.assertEqual(t, [5, 10, 15, 20])
        self.assertEqual(v, [2, 3, 4, 5])
        t, v = trim(7)
        self.assertEqual(t, [10, 15, 20])
        self.assertEqual(v, [3, 4, 5])
        t, v = trim(10)
        self.assertEqual(t, [10, 15, 20])
        self.assertEqual(v, [3, 4, 5])
        t, v = trim(13)
        self.assertEqual(t, [15, 20])
        self.assertEqual(v, [4, 5])
        t, v = trim(15)
        self.assertEqual(t, [15, 20])
        self.assertEqual(v, [4, 5])
        t, v = trim(17)
        self.assertEqual(t, [20])
        self.assertEqual(v, [5])
        t, v = trim(20)
        self.assertEqual(t, [20])
        self.assertEqual(v, [5])
        t, v = trim(22)
        self.assertEqual(t, [])
        self.assertEqual(v, [])

        # Now repeat but with adjustments
        adjust = True
        t, v = trim(-5)
        self.assertEqual(t, [5, 10, 15, 20, 25])
        self.assertEqual(v, [1, 2, 3, 4, 5])
        t, v = trim(0)
        self.assertEqual(t, [0, 5, 10, 15, 20])
        self.assertEqual(v, [1, 2, 3, 4, 5])
        t, v = trim(2)
        self.assertEqual(t, [3, 8, 13, 18])
        self.assertEqual(v, [2, 3, 4, 5])
        t, v = trim(5)
        self.assertEqual(t, [0, 5, 10, 15])
        self.assertEqual(v, [2, 3, 4, 5])
        t, v = trim(7)
        self.assertEqual(t, [3, 8, 13])
        self.assertEqual(v, [3, 4, 5])
        t, v = trim(10)
        self.assertEqual(t, [0, 5, 10])
        self.assertEqual(v, [3, 4, 5])
        t, v = trim(13)
        self.assertEqual(t, [2, 7])
        self.assertEqual(v, [4, 5])
        t, v = trim(15)
        self.assertEqual(t, [0, 5])
        self.assertEqual(v, [4, 5])
        t, v = trim(17)
        self.assertEqual(t, [3])
        self.assertEqual(v, [5])
        t, v = trim(20)
        self.assertEqual(t, [0])
        self.assertEqual(v, [5])
        t, v = trim(22)
        self.assertEqual(t, [])
        self.assertEqual(v, [])

        # Now repeat but with numpy and adjustments
        adjust = True
        wnumpy = True
        t, v = trim(-5)
        self.assertEqual(t, [5, 10, 15, 20, 25])
        self.assertEqual(v, [1, 2, 3, 4, 5])
        t, v = trim(0)
        self.assertEqual(t, [0, 5, 10, 15, 20])
        self.assertEqual(v, [1, 2, 3, 4, 5])
        t, v = trim(2)
        self.assertEqual(t, [3, 8, 13, 18])
        self.assertEqual(v, [2, 3, 4, 5])
        t, v = trim(5)
        self.assertEqual(t, [0, 5, 10, 15])
        self.assertEqual(v, [2, 3, 4, 5])
        t, v = trim(7)
        self.assertEqual(t, [3, 8, 13])
        self.assertEqual(v, [3, 4, 5])
        t, v = trim(10)
        self.assertEqual(t, [0, 5, 10])
        self.assertEqual(v, [3, 4, 5])
        t, v = trim(13)
        self.assertEqual(t, [2, 7])
        self.assertEqual(v, [4, 5])
        t, v = trim(15)
        self.assertEqual(t, [0, 5])
        self.assertEqual(v, [4, 5])
        t, v = trim(17)
        self.assertEqual(t, [3])
        self.assertEqual(v, [5])
        t, v = trim(20)
        self.assertEqual(t, [0])
        self.assertEqual(v, [5])
        t, v = trim(22)
        self.assertEqual(t, [])
        self.assertEqual(v, [])

    def test_trim_right(self):
        # Test the trim_right function.

        var1 = 'engine.toom'
        var2 = 'membrane.V'

        def trim(value):
            x = myokit.DataLog({
                var1: [0, 5, 10, 15, 20],
                var2: [1, 2, 3, 4, 5],
            })
            x.set_time_key(var1)
            y = x.trim_right(value)
            self.assertEqual(len(x[var1]), 5)
            self.assertEqual(len(x[var2]), 5)
            return y[var1], y[var2]

        t, v = trim(-5)
        self.assertEqual(t, [])
        self.assertEqual(v, [])
        t, v = trim(0)
        self.assertEqual(t, [])
        self.assertEqual(v, [])
        t, v = trim(2)
        self.assertEqual(t, [0])
        self.assertEqual(v, [1])
        t, v = trim(5)
        self.assertEqual(t, [0])
        self.assertEqual(v, [1])
        t, v = trim(7)
        self.assertEqual(t, [0, 5])
        self.assertEqual(v, [1, 2])
        t, v = trim(10)
        self.assertEqual(t, [0, 5])
        self.assertEqual(v, [1, 2])
        t, v = trim(13)
        self.assertEqual(t, [0, 5, 10])
        self.assertEqual(v, [1, 2, 3])
        t, v = trim(15)
        self.assertEqual(t, [0, 5, 10])
        self.assertEqual(v, [1, 2, 3])
        t, v = trim(17)
        self.assertEqual(t, [0, 5, 10, 15])
        self.assertEqual(v, [1, 2, 3, 4])
        t, v = trim(20)
        self.assertEqual(t, [0, 5, 10, 15])
        self.assertEqual(v, [1, 2, 3, 4])
        t, v = trim(22)
        self.assertEqual(t, [0, 5, 10, 15, 20])
        self.assertEqual(v, [1, 2, 3, 4, 5])

    def test_validate(self):
        # Test the validate() method.

        d = myokit.DataLog()
        d.validate()
        d['time'] = [1, 2, 3]
        d.validate()
        d['time'] = [3, 2, 1]
        d.validate()
        d.set_time_key('time')
        self.assertRaises(myokit.InvalidDataLogError, d.validate)
        d = myokit.DataLog()
        d.set_time_key('time')
        self.assertRaises(myokit.InvalidDataLogError, d.validate)
        d['time'] = [0, 0, 1]
        d.validate()
        d['x'] = [3, 2, 1]
        d.validate()
        self.assertEqual(d.time_key(), 'time')
        self.assertEqual(d.time(), d['time'])
        self.assertEqual(d.time(), [0, 0, 1])
        d['y'] = [4, 5, 6]
        d.validate()
        d['z'] = [7, 8, 9]
        d.validate()
        d['x'].append(1)
        self.assertRaises(myokit.InvalidDataLogError, d.validate)

    def test_apd(self):
        # Test the apd method.

        # Very coarse check
        d = myokit.DataLog(time='time')
        d['time'] = np.linspace(0, 10, 11)
        d['v'] = np.ones(10) * -85
        d['v'][1:3] = 40
        d['v'][6:9] = 40
        apds = d.apd(v='v')
        self.assertEqual(len(apds), 2)
        self.assertTrue(apds['start'][0] > 0)
        self.assertTrue(apds['start'][0] < 1)
        self.assertTrue(apds['duration'][0] > 2.5)
        self.assertTrue(apds['duration'][0] < 3.0)
        self.assertTrue(apds['start'][1] > 5)
        self.assertTrue(apds['start'][1] < 6)
        self.assertTrue(apds['duration'][1] > 3.5)
        self.assertTrue(apds['duration'][1] < 4.0)

        # Check with threshold equal to V
        apds = d.apd(v='v', threshold=-85)
        self.assertEqual(len(apds['start']), 1)
        self.assertEqual(apds['start'][0], 5)
        self.assertEqual(apds['duration'][0], 4)

        # Check against example model
        m, p, x = myokit.load(os.path.join(DIR_DATA, 'lr-1991.mmt'))
        s = myokit.Simulation(m, p)
        s.set_tolerance(1e-8, 1e-8)
        d, apds1 = s.run(
            2000, log=['engine.time', 'membrane.V'],
            log_interval=0.005,
            apd_variable='membrane.V', apd_threshold=-70)
        apds2 = d.apd(threshold=-70)
        self.assertEqual(len(apds1['start']), 2)
        self.assertEqual(len(apds2['start']), 2)
        self.assertAlmostEqual(1, apds1['start'][0] / apds2['start'][0])
        self.assertAlmostEqual(1, apds1['start'][1] / apds2['start'][1])
        self.assertAlmostEqual(1, apds1['duration'][0] / apds2['duration'][0])
        self.assertAlmostEqual(1, apds1['duration'][1] / apds2['duration'][1])

    def test_clone(self):
        # Test data log cloning.

        m, p, x = myokit.load(os.path.join(DIR_DATA, 'lr-1991.mmt'))
        s = myokit.Simulation(m, p)
        d1 = s.run(100, log=myokit.LOG_BOUND + myokit.LOG_STATE).npview()
        d2 = d1.clone()

        # Check keys are the same
        self.assertEqual(d1.keys(), d2.keys())

        # Check the values are the same, but not the same objects
        for k, v in d1.items():
            self.assertTrue(np.all(v == d2[k]))
            self.assertFalse(v is d2[k])
            self.assertTrue(type(d2[k]) == list)

        # Check cloning as numpy arrays
        d2 = d1.clone(numpy=True)
        self.assertEqual(d1.keys(), d2.keys())
        for k, v in d1.items():
            self.assertTrue(np.all(v == d2[k]))
            self.assertFalse(v is d2[k])
            self.assertTrue(type(d2[k]) == np.ndarray)

    def test_fold(self):
        # Test the fold() method.

        d = myokit.DataLog(time='time')
        d['time'] = list(range(100))
        d['x'] = list(np.arange(100) * 3)

        # Test without discarding remainder
        d2 = d.fold(30, discard_remainder=False)
        self.assertEqual(set(d2.keys()), set([
            'time', '0.x', '1.x', '2.x', '3.x']))

        # Test with discarding remainder
        d = d.npview()
        d2 = d.fold(30)
        self.assertEqual(set(d2.keys()), set([
            'time', '0.x', '1.x', '2.x']))
        self.assertEqual(len(d2['time']), 30)
        self.assertEqual(len(d2['0.x']), 30)
        self.assertEqual(len(d2['1.x']), 30)
        self.assertEqual(len(d2['2.x']), 30)
        self.assertTrue(np.all(d2['time'] == d['time'][:30]))
        self.assertTrue(np.all(d2['0.x'] == d['x'][:30]))
        self.assertTrue(np.all(d2['1.x'] == d['x'][30:60]))
        self.assertTrue(np.all(d2['2.x'] == d['x'][60:90]))

    def test_has_nan(self):
        # Test the has_nan() method, which checks if the _final_ value in any
        # field is NaN.

        d = myokit.DataLog(time='time')
        d['time'] = list(range(100))
        d['x'] = list(np.arange(100) * 3)
        d['y'] = list(np.arange(100) * 3)
        d['z'] = list(np.arange(100) * 3)
        self.assertFalse(d.has_nan())
        d['x'][-3] = float('nan')
        self.assertFalse(d.has_nan())
        d['x'][-1] = float('inf')
        self.assertFalse(d.has_nan())
        d['x'][-1] = float('nan')
        self.assertTrue(d.has_nan())

    def test_length(self):
        # Test the length() method, that counts the length of the log's
        # entries.

        d = myokit.DataLog(time='time')
        self.assertEqual(d.length(), 0)
        d['time'] = list(np.arange(100) * 3)
        self.assertEqual(d.length(), 100)
        d['x'] = list(np.arange(100) * 3)
        self.assertEqual(d.length(), 100)

    def test_regularize(self):
        # Test the regularize() method.

        d = myokit.DataLog(time='time')
        d['time'] = np.log(np.linspace(1, 25, 100))
        d['values'] = np.linspace(1, 25, 100)
        e = d.regularize(dt=0.5)
        self.assertEqual(len(e['time']), 7)
        x = np.array([0, 0.5, 1, 1.5, 2, 2.5, 3])
        self.assertTrue(np.all(e['time'] == x))
        for i, y in enumerate(x):
            self.assertTrue(np.abs(np.exp(y) - e['values'][i]) < 0.02)

        # test setting tmin and tmax
        e = d.regularize(dt=0.5, tmin=0.4, tmax=2.6)
        self.assertEqual(len(e['time']), 5)
        x = np.array([0.4, 0.9, 1.4, 1.9, 2.4])
        self.assertTrue(np.all(e['time'] == x))
        for i, y in enumerate(x):
            self.assertTrue(np.abs(np.exp(y) - e['values'][i]) < 0.02)

    def test_time(self):
        # Test the time() method.

        d = myokit.DataLog(time='t')
        t = [1, 2, 3]
        d['t'] = t
        self.assertIs(d['t'], t)

        # Test non-existing time key
        d = myokit.DataLog(time='t')
        self.assertRaisesRegex(
            myokit.InvalidDataLogError, 'Invalid key', d.time)

        # Test no time key
        d = myokit.DataLog()
        self.assertRaisesRegex(
            myokit.InvalidDataLogError, 'No time', d.time)

    def test_variable_info_errors(self):
        # Test errors raised during variable info checking.

        # Test mismatched dimensions (1d versus 2d)
        d = myokit.DataLog(time='t')
        d['t'] = [1, 2, 3, 4]
        d['0.v'] = [1, 2, 3, 4]
        d['1.1.v'] = [1, 2, 3, 4]
        self.assertRaisesRegex(
            RuntimeError, 'Different dimensions', d.variable_info)
        # Note: Valid log, so not an InvalidDataLogError

        # Test "irregular data": can't be arranged in a rectangular grid
        d = myokit.DataLog(time='t')
        d['t'] = [1, 2, 3, 4]
        d['0.0.v'] = [1, 2, 3, 4]
        d['0.2.v'] = [1, 2, 3, 4]
        d['1.0.v'] = [1, 2, 3, 4]
        d['1.1.v'] = [1, 2, 3, 4]
        self.assertRaisesRegex(RuntimeError, 'Irregular', d.variable_info)
        # Note: Valid log, so not an InvalidDataLogError

    def test_variable_info(self):
        # Test if correct variable info is returned.

        d = myokit.DataLog(time='t')
        # Odd grid
        d['0.0.v'] = [0, 1, 2, 3]
        d['0.2.v'] = [1, 2, 3, 4]
        d['1.0.v'] = [2, 3, 4, 5]
        d['1.2.v'] = [3, 4, 5, 6]
        d['3.0.v'] = [4, 5, 6, 7]
        d['3.2.v'] = [5, 6, 7, 8]
        # Nice grid
        d['0.0.w'] = [0, 1, 2, 3]
        d['0.1.w'] = [1, 2, 3, 4]
        d['1.0.w'] = [2, 3, 4, 5]
        d['1.1.w'] = [3, 4, 5, 6]
        d['2.0.w'] = [4, 5, 6, 7]
        d['2.1.w'] = [5, 6, 7, 8]
        i = d.variable_info()

        # Check found variables
        self.assertEqual(set(i.keys()), set(['v', 'w']))

        # Check if data is in a regular grid
        v = i['v']
        w = i['w']
        self.assertFalse(v.is_regular_grid())
        self.assertTrue(w.is_regular_grid())

        # Check ids
        vids = [(0, 0), (0, 2), (1, 0), (1, 2), (3, 0), (3, 2)]
        self.assertEqual(list(v.ids()), vids)
        wids = [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)]
        self.assertEqual(list(w.ids()), wids)

        # Check keys
        viter = v.keys()
        for vid in vids:
            self.assertEqual(
                str(vid[0]) + '.' + str(vid[1]) + '.' + 'v', next(viter))
        witer = w.keys()
        for wid in wids:
            self.assertEqual(
                str(wid[0]) + '.' + str(wid[1]) + '.' + 'w', next(witer))

        # Check size
        self.assertEqual(v.size(), (3, 2))
        self.assertEqual(w.size(), (3, 2))

        # Check name
        self.assertEqual(v.name(), 'v')
        self.assertEqual(w.name(), 'w')


if __name__ == '__main__':
    print('Add -v for more debug output')
    import sys
    if '-v' in sys.argv:
        debug = True
    unittest.main()
