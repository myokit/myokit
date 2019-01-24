#!/usr/bin/env python
#
# Tests the protocol output for step protocols where floating point accuracy
# matters.
#
# In particular, for a protocol like:
#
# level     start       duration
# -80       0           3.3333
# -70       3.3333      3.3331
# -60       6.6664      3.3336
#
# We can run into problems with doubles, as:
#
#   >>> 3.3333 + 3.3331
#   6.666399999999999
#   >>> 3.3333 + 3.3331 < 6.6664
#   True
#
# This can cause the 2nd even to end just before the 3d starts, leading to a
# quick jump to 0 in between -70 and -60.
#
# To avoid this, we should use slightly more careful ways of comparing floating
# point numbers if all protocol handling code.
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import unittest

import myokit
import myokit.pype

from shared import TemporaryDirectory

# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp


class ProtocolFloatingPointTest(unittest.TestCase):

    def test_cvode_floating_point_protocol(self):
        # Tests the protocol handling in a CVODE simulation, which uses the
        # pacing.h file shared by all C/C++ simulation code.

        m = myokit.Model()
        c = m.add_component('c')
        t = c.add_variable('t')
        t.set_rhs(0)
        t.set_binding('time')
        v = c.add_variable('v')
        v.set_rhs('0')
        v.set_binding('pace')

        p = myokit.Protocol()
        p.schedule(-80, 0, 3.3333)
        p.schedule(-70, 3.3333, 3.3331)
        p.schedule(-60, 6.6664, 3.3336)

        s = myokit.Simulation(m, p)
        d = s.run(p.characteristic_time())

        self.assertEqual(d['c.v'], [-80, -70, -60, 0])















if __name__ == '__main__':
    unittest.main()
