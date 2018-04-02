#!/usr/bin/env python2
#
# Tests the DataLog class
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
import myokit
import myotest
import os
import unittest
import numpy as np


def suite():
    """
    Returns a test suite with all tests in this module.
    """
    suite = unittest.TestSuite()
    suite.addTest(DataLogTest('extend'))
    suite.addTest(DataLogTest('find_time'))
    suite.addTest(DataLogTest('indexing'))
    suite.addTest(DataLogTest('integrate'))
    suite.addTest(DataLogTest('itrim'))
    suite.addTest(DataLogTest('itrim_left'))
    suite.addTest(DataLogTest('itrim_right'))
    suite.addTest(DataLogTest('keys_like'))
    suite.addTest(DataLogTest('length'))
    suite.addTest(DataLogTest('prepare_single'))
    suite.addTest(DataLogTest('prepare_1d'))
    suite.addTest(DataLogTest('save'))
    suite.addTest(DataLogTest('save_csv'))
    suite.addTest(DataLogTest('split'))
    suite.addTest(DataLogTest('split_periodic'))
    suite.addTest(DataLogTest('trim'))
    suite.addTest(DataLogTest('trim_left'))
    suite.addTest(DataLogTest('trim_right'))
    suite.addTest(DataLogTest('validate'))
    return suite


class DataLogTest(unittest.TestCase):
    """
    Tests the DataLog's functions.
    """
    show_plots = False

    def extend(self):
        """
        Tests the extend function.
        """
        d1 = myokit.DataLog()
        d1.set_time_key('time')
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

    def find_time(self):
        """
        Tests the find function.
        """
        x = myokit.DataLog({
            'engine.time': [0, 5, 10, 15, 20],
            'membrane.V': [0, 50, 100, 150, 200]})
        x.set_time_key('engine.time')
        self.assertEqual(x.find(-5), 0)
        self.assertEqual(x.find(0), 0)
        self.assertEqual(x.find(2), 1)
        self.assertEqual(x.find(5), 1)
        self.assertEqual(x.find(8), 2)
        self.assertEqual(x.find(10), 2)
        self.assertEqual(x.find(13), 3)
        self.assertEqual(x.find(15), 3)
        self.assertEqual(x.find(19), 4)
        self.assertEqual(x.find(20), 4)
        self.assertEqual(x.find(21), 5)

        # Now with a numpy log
        x = x.npview()
        self.assertEqual(x.find(-5), 0)
        self.assertEqual(x.find(0), 0)
        self.assertEqual(x.find(2), 1)
        self.assertEqual(x.find(5), 1)
        self.assertEqual(x.find(8), 2)
        self.assertEqual(x.find(10), 2)
        self.assertEqual(x.find(13), 3)
        self.assertEqual(x.find(15), 3)
        self.assertEqual(x.find(19), 4)
        self.assertEqual(x.find(20), 4)
        self.assertEqual(x.find(21), 5)

    def indexing(self):
        """
        Tests the indexing overrides in the simulation log.
        """
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
        del(d['a', (5, 6)])
        self.assertFalse(('a', (5, 6)) in d)

    def integrate(self):
        """
        Tests the integrate method.
        """
        # Create an irregular time array
        from random import random
        t = []
        for i in xrange(0, 100):
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
        if myotest.DEBUG:
            print(e)
        self.assertLess(e, 0.1)
        if self.show_plots:
            import matplotlib.pyplot as pl
            pl.figure()
            pl.plot(t, q, label='original')
            pl.plot(t, x, label='mid sum')
            pl.legend(loc='upper left')
            pl.figure()
            pl.plot(t, np.abs(x - q) / q, label='mid sum error')
            pl.legend(loc='upper left')
            pl.show()

    def itrim(self):
        """
        Tests the itrim() method.
        """
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

    def itrim_left(self):
        """
        Tests the itrim_left() method.
        """
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

    def itrim_right(self):
        """
        Tests the itrim_right() method.
        """
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

    def length(self):
        """
        Tests the length() method.
        """
        d = myokit.DataLog()
        d.set_time_key('t')
        d['t'] = [10, 20, 30, 40]
        d['v'] = [50, 60, 70, 80]
        self.assertEqual(d.length(), 4)

    def keys_like(self):
        """
        Tests the keys_like(query) method.
        """
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

    def prepare_1d(self):
        """
        Test the prepare_log function that handles the ``log`` argument passed
        into simulations. This function can handle different types of input.
        From its doc:

        An existing simulation log
            In this case, the log is tested for compatibility with the given
            model and simulation dimensions. For multi-cellular simulations
            this means all keys in the log must have the form
            "x.component.variable" where "x" is the cell index (for example "1"
            or "2.3").
        A list (or other sequence) of variable names to log.
            In this case, the list is converted to a DataLog object. All
            arguments in the list must be either strings corresponding to the
            variables' qnames (so "membrane.V") or variable objects from the
            given model.
            For multi-cell models, _only_ the qnames should be given (so
            "membrane.V" is valid, while "1.2.membrane.V" is not.
        An integer flag
            For example ``myokit.LOG_NONE``, ``myokit.LOG_STATE`` or
            ``myokit.LOG_STATE + myokit.LOG_BOUND``.
        None
            In this case the value from ``if_empty`` will be copied into log
            before the function proceeds to build a log.
        """
        # Test multi-cell log preparing
        from myokit import prepare_log
        m = myokit.load_model(
            os.path.join(myotest.DIR_DATA, 'lr-1991-testing.mmt'))

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
        # b = ['time', 'pace', 'diffusion_current']
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

        def err():
            prepare_log(('engine.time', 'membrane.dudez'), m, (2, 1))

        self.assertRaises(Exception, err)
        self.assertRaises(Exception, prepare_log, 'engine.time', m)
        self.assertRaises(Exception, prepare_log, {'map_to': 'rubbish'}, m)

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
        self.assertRaises(
            Exception, prepare_log,
            ('engine.time', '2.2.membrane.V'),
            m, (2, 1), global_vars=g)
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
        self.assertRaises(
            Exception, prepare_log,
            ('1.0.engine.time', '0.0.membrane.V'), m, (2, 1), global_vars=g)
        self.assertRaises(
            Exception, prepare_log,
            ('1.0.engine.time', 'membrane.V'), m, (2, 1), global_vars=g)

        #
        # 4. Existing log
        #
        self.assertRaises(
            Exception, prepare_log, {'engine.time': 'rubbish'}, m)
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
        self.assertRaises(
            Exception, prepare_log,
            {'2.0.engine.time': [1, 2, 3], '1.0.membrane.V': [1, 2, 3]},
            m, (2, 1))
        self.assertIsInstance(d, myokit.DataLog)
        self.assertEqual(len(d), 2)
        #self.assertRaises(Exception, prepare_log, {'engine.time': [1, 2, 3],
        #    'membrane.V': [1,2]}, m)
        # Different lengths is weird, but doesn't hurt...
        self.assertRaises(
            Exception, prepare_log, {'1.0.engine.toom': [1, 2, 3]}, m, (2, 1))
        d = prepare_log(d, m, (2, 1))
        self.assertIsInstance(d, myokit.DataLog)
        d = prepare_log(d, m, (2, 1))
        self.assertIsInstance(d, myokit.DataLog)
        #
        # 4B. Existing log, globals and local
        #
        self.assertRaises(
            Exception, prepare_log, {'1.0.engine.time': []}, m,
            (2, 1), global_vars=g)
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
        self.assertRaises(
            Exception, prepare_log,
            {'engine.time': [1, 2, 3], '0.0.membrane.V': [1, 2, 3]},
            m, (2, 1))
        self.assertRaises(
            Exception, prepare_log,
            {'engine.time': [1, 2, 3], '5.0.membrane.V': [1, 2, 3]},
            m, (2, 1), global_vars=g)
        d = prepare_log(d, m, (2, 1), global_vars=g)
        self.assertIsInstance(d, myokit.DataLog)
        d = prepare_log(d, m, (2, 1), global_vars=g)
        self.assertIsInstance(d, myokit.DataLog)

    def prepare_single(self):
        """
        Test the prepare_log function that handles the ``log`` argument passed
        into simulations. This function can handle different types of input.
        From its doc:

        An existing simulation log
            In this case, the log is tested for compatibility with the given
            model and simulation dimensions. For multi-cellular simulations
            this means all keys in the log must have the form
            "x.component.variable" where "x" is the cell index (for example "1"
            or "2.3").
        A list (or other sequence) of variable names to log.
            In this case, the list is converted to a DataLog object. All
            arguments in the list must be either strings corresponding to the
            variables' qnames (so "membrane.V") or variable objects from the
            given model.
            For multi-cell models, _only_ the qnames should be given (so
            "membrane.V" is valid, while "1.2.membrane.V" is not.
        An integer flag
            For example ``myokit.LOG_NONE``, ``myokit.LOG_STATE`` or
            ``myokit.LOG_STATE + myokit.LOG_BOUND``.
        None
            In this case the value from ``if_empty`` will be copied into log
            before the function proceeds to build a log.
        """
        # Test multi-cell log preparing
        from myokit import prepare_log
        m = myokit.load_model(
            os.path.join(myotest.DIR_DATA, 'lr-1991-testing.mmt'))

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

        def err():
            prepare_log(('engine.time', 'membrane.dudez'), m)
        self.assertRaises(Exception, err)
        self.assertRaises(Exception, prepare_log, 'engine.time', m)
        self.assertRaises(Exception, prepare_log, {'map_to': 'rubbish'}, m)

        #
        # 4. Existing log
        #
        self.assertRaises(
            Exception, prepare_log, {'engine.time': 'rubbish'}, m)
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
        # self.assertRaises(Exception, prepare_log, {'engine.time': [1, 2, 3],
        #    'membrane.V': [1,2]}, m)
        # Different lengths is weird, but doesn't hurt...
        self.assertRaises(
            Exception, prepare_log, {'engine.toom': [1, 2, 3]}, m)
        d = prepare_log(d, m)
        self.assertIsInstance(d, myokit.DataLog)
        d = prepare_log(d, m)
        self.assertIsInstance(d, myokit.DataLog)

    def save(self):
        """
        Tests saving in binary format.
        """
        fname = os.path.join(myotest.DIR_OUT, 'test.bin')
        d = myokit.DataLog()
        d['a.b'] = np.arange(0, 100, dtype=np.float32)
        d['c.d'] = np.sqrt(np.arange(0, 100) * 1.2)

        # Test saving with double precision
        d.save(fname)
        e = myokit.DataLog.load(fname)
        self.assertFalse(d is e)
        if not myotest.DEBUG:
            os.remove(fname)
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
        d.save(fname, precision=myokit.SINGLE_PRECISION)
        e = myokit.DataLog.load(fname)
        self.assertFalse(d is e)
        if not myotest.DEBUG:
            os.remove(fname)
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

    def save_csv(self):
        """
        Tests saving as csv.
        """
        fname = os.path.join(myotest.DIR_OUT, 'test.csv')
        d = myokit.DataLog()

        # Note: a.b and e.f are both non-decreaing, could be taken for time!
        d['a.b'] = np.arange(0, 100)
        d['c.d'] = np.sqrt(np.arange(0, 100) * 1.2)
        d['e.f'] = np.arange(0, 100) + 1
        d.save_csv(fname)
        e = myokit.DataLog.load_csv(fname)
        if not myotest.DEBUG:
            os.remove(fname)
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
        d.save_csv(fname)
        e = myokit.DataLog.load_csv(fname)
        if not myotest.DEBUG:
            os.remove(fname)
        self.assertEqual(e.time()[0], d['a.b'][0])

        # Now set time key
        d.set_time_key('e.f')
        d.save_csv(fname)
        e = myokit.DataLog.load_csv(fname)
        if not myotest.DEBUG:
            os.remove(fname)
        self.assertEqual(e.time()[0], d['e.f'][0])

    def split(self):
        """
        Tests the split function.
        """
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

        for i in xrange(2):
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

    def split_periodic(self):
        """
        Tests the split_periodic() function.
        """
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

    def trim(self):
        """
        Tests the trim() method.
        """
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

    def trim_left(self):
        """
        Tests the trim_left function.
        """
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

    def trim_right(self):
        """
        Tests the cut_right function.
        """
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

    def validate(self):
        """
        Tests the validate() method.
        """
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
