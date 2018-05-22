#!/usr/bin/env python
#
# Tests the RhsBenchmarker
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import unittest
import numpy as np

import myokit


class RhsBenchmarkerTest(unittest.TestCase):
    """
    Tests the RhsBenchmarker class.
    """
    def test_simple(self):

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
        log['c.time'] = np.zeros(1000)
        log['c.V'] = np.linspace(-80.0, 50.0, 10)

        # Number of repeats
        repeats = 10

        # Run
        x.set_rhs('1 / (7 * exp((V + 12) / 35) + 9 * exp(-(V + 77) / 6))')
        b = myokit.RhsBenchmarker(m, [x])
        t = b.bench_full(log, repeats)
        t = b.bench_part(log, repeats)
        # No errors = pass


if __name__ == '__main__':
    unittest.main()
