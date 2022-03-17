#!/usr/bin/env python3
#
# Tests the RhsBenchmarker
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import unittest
import numpy as np

import myokit

# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp


class RhsBenchmarkerTest(unittest.TestCase):
    """
    Tests :class:`RhsBenchmarker`.
    """
    def test_simple(self):
        # Test basic functionality.

        # Create test model
        m = myokit.Model('test')
        c = m.add_component('c')
        t = c.add_variable('time')
        t.set_rhs('0')
        t.set_binding('time')
        v = c.add_variable('V')
        v.set_rhs('0')
        v.promote(-80.1)
        x = c.add_variable('x')
        x.set_rhs('exp(V)')
        m.validate()

        # Create simulation log
        log = myokit.DataLog()
        log['c.time'] = np.zeros(10)
        log['c.V'] = np.linspace(-80.0, 50.0, 10)

        # Number of repeats
        repeats = 10

        # Run
        x.set_rhs('1 / (7 * exp((V + 12) / 35) + 9 * exp(-(V + 77) / 6))')
        b = myokit.RhsBenchmarker(m, [x])
        t = b.bench_full(log, repeats)
        t = b.bench_part(log, repeats)
        # No errors = pass

        # Get mean and std after outlier removal
        mean = b.mean(t)
        mean, std = b.mean_std(t)

    def test_bad_log(self):
        # Test error handling when unsuitable log is used.

        # Create test model
        m = myokit.Model('test')
        c = m.add_component('c')
        t = c.add_variable('time')
        t.set_rhs('0')
        t.set_binding('time')
        v = c.add_variable('V')
        v.set_rhs('0')
        v.promote(-80.1)
        w = c.add_variable('W')
        w.set_rhs(0)
        w.promote(10)
        x = c.add_variable('x')
        x.set_rhs('exp(V) + W')
        m.validate()

        # Create benchmarker
        b = myokit.RhsBenchmarker(m, [x])

        # Missing state variable
        d = myokit.DataLog()
        d['c.time'] = np.zeros(10)
        #d['c.V'] = np.linspace(-80.0, 50.0, 10)
        d['c.W'] = np.linspace(0.0, 10.0, 10)
        self.assertRaisesRegex(
            ValueError, 'State variable <c.V> not found', b.bench_full, d, 1)

        # Different size log entries
        d = myokit.DataLog()
        d['c.time'] = np.zeros(1000)
        d['c.V'] = np.linspace(-80.0, 50.0, 10)
        d['c.W'] = np.linspace(0.0, 10.0, 11)
        self.assertRaisesRegex(
            ValueError, 'same length', b.bench_full, d, 1)

    def test_creation(self):
        # Test Benchmarker creation.
        # Create test model
        m = myokit.Model('test')
        c = m.add_component('c')
        t = c.add_variable('time')
        t.set_rhs('0')
        t.set_binding('time')
        v = c.add_variable('V')
        v.set_rhs('0')
        v.promote(-80.1)
        x = c.add_variable('x')
        x.set_rhs('exp(V)')
        y = c.add_variable('y')
        y.set_rhs(3)
        m.validate()

        # Create benchmarker without variables
        myokit.RhsBenchmarker(m)

        # Create with objects
        myokit.RhsBenchmarker(m, [x])

        # Create with strings
        myokit.RhsBenchmarker(m, ['c.x'])

        # Cannot create with constants
        self.assertRaisesRegex(
            ValueError, 'constant', myokit.RhsBenchmarker, m, [y])

        # Cannot create with bound variables
        self.assertRaisesRegex(
            ValueError, 'bound', myokit.RhsBenchmarker, m, [t])


if __name__ == '__main__':
    unittest.main()
