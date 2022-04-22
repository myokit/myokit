#!/usr/bin/env python3
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
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import unittest

import myokit

from myokit.tests.ansic_event_based_pacing import AnsicEventBasedPacing

# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp


class ProtocolFloatingPointTest(unittest.TestCase):

    def test_is_sequence_and_length_floats_1(self):

        # Tests how float issues are handled in characteristic_time,
        # is_sequence, and is_unbroken_sequence

        # Example 1: Sum too high

        # Good arithmetic: 1.2345 + 2.3454 = 3.5799
        # With doubles   :                   3.5799000000000003
        # So that        : 1.2345 + 2.3454 > 3.5799

        # Absolute error :                   4.440892098500626e-16
        # Float epsilon  : sys.float_info    2.220446049250313e-16
        # Abs error / eps:                   2.0 = 2**1
        # 2-log of sum   :                   [1-2]
        # Relative error : abs error / sum   1.2405073042544837e-16

        p = myokit.Protocol()
        p.schedule(-80, 0, 1.2345)
        p.schedule(-70, 1.2345, 2.3454)
        p.schedule(-60, 3.5799, 1.4201)

        self.assertEqual(p.characteristic_time(), 5)
        self.assertTrue(p.is_sequence())
        self.assertTrue(p.is_unbroken_sequence())

    def test_is_sequence_and_length_floats_2(self):

        # Tests how float issues are handled in characteristic_time,
        # is_sequence, and is_unbroken_sequence

        # Example 2: Sum too low

        # Good arithmetic: 3.3333 + 3.3331 = 6.6664
        # With doubles   :                   6.666399999999999
        # So that        : 3.3333 + 3.3331 < 6.6664

        # Absolute error :                   -8.881784197001252e-16
        # Float epsilon  : sys.float_info     2.220446049250313e-16
        # Abs error / eps:                   -4.0 = 2**2
        # 2-log of sum   :                    [2-3]
        # Relative error : abs error / sum   -1.3323209223870833e-16

        p = myokit.Protocol()
        p.schedule(-80, 0, 3.3333)
        p.schedule(-70, 3.3333, 3.3331)
        p.schedule(-60, 6.6664, 3.3336)

        self.assertEqual(p.characteristic_time(), 10)
        self.assertTrue(p.is_sequence())
        self.assertTrue(p.is_unbroken_sequence())

    def test_is_sequence_and_length_floats_3(self):

        # Tests how float issues are handled in characteristic_time,
        # is_sequence, and is_unbroken_sequence

        # Example 3: The size of the numbers matters
        #
        # Good arithmetic: 1340.6 + 22159.6 = 23500.2
        # With doubles   :                    23500.199999999997
        # So that        : 1340.6 + 22159.6 < 23500.2

        # Error          :                   -3.637978807091713e-12
        # Float epsilon  : sys.float_info     2.220446049250313e-16
        # Abs error / eps:                   -16384.0 = 2**14
        # 2-log of sum   :                    [14-15]
        # Relative error : abs error / sum   -1.5480629131206173e-16

        p = myokit.Protocol()
        p.schedule(-80, 0, 22159.6)
        p.schedule(-70, 22159.6, 1340.6)
        p.schedule(-60, 23500.2, 6499.8)

        self.assertEqual(p.characteristic_time(), 30000)
        self.assertTrue(p.is_sequence())
        self.assertTrue(p.is_unbroken_sequence())


class PacingSystemFloatingPointTest(unittest.TestCase):
    """
    Test float behaviour in the Python PacingSystem implementation, using the
    log_for_interval method.
    """

    def test_python_pacing_floats_1(self):

        # Test fixes for event start/end touching
        p = myokit.Protocol()
        p.schedule(-80, 0, 1.2345)
        p.schedule(-70, 1.2345, 2.3454)
        p.schedule(-60, 3.5799, 1.4201)

        # Call log_for_interval, which uses the PacingSystem
        d = p.log_for_interval(0, 10)

        # Check if the correct values are recorded
        self.assertEqual(d['time'], [0, 1.2345, 3.5799, 5, 10])
        self.assertEqual(d['pace'], [-80, -70, -60, 0, 0])

        # Test fixes for start/end of interval touching events
        p = myokit.Protocol()
        p.schedule(-80, 0, 1.2345)
        p.schedule(-70, 1.2345, 2.3454)

        # Interval end
        d = p.log_for_interval(0, 3.5799)
        self.assertEqual(d['time'], [0, 1.2345, 3.5799])
        self.assertEqual(d['pace'], [-80, -70, 0])

        # Interval start
        d = p.log_for_interval(3.5799, 10)
        self.assertEqual(d['time'], [3.5799, 10])
        self.assertEqual(d['pace'], [0, 0])

    def test_python_pacing_floats_2(self):

        p = myokit.Protocol()
        p.schedule(-80, 0, 3.3333)
        p.schedule(-70, 3.3333, 3.3331)
        p.schedule(-60, 6.6664, 3.3336)

        # Call log_for_interval, which uses the PacingSystem
        d = p.log_for_interval(0, 20)

        # Check if the correct values are recorded
        self.assertEqual(d['time'], [0, 3.3333, 6.6664, 10, 20])
        self.assertEqual(d['pace'], [-80, -70, -60, 0, 0])

    def test_python_pacing_floats_3(self):

        p = myokit.Protocol()
        p.schedule(-80, 0, 22159.6)
        p.schedule(-70, 22159.6, 1340.6)
        p.schedule(-60, 23500.2, 6499.8)

        # Call log_for_interval, which uses the PacingSystem
        d = p.log_for_interval(0, 40000)

        # Check if the correct values are recorded
        self.assertEqual(d['time'], [0, 22159.6, 23500.2, 30000, 40000])
        self.assertEqual(d['pace'], [-80, -70, -60, 0, 0])


class AnsicPacingSystemFloatingPointTest(unittest.TestCase):
    """
    Test floating point behavior of C-pacing, using the Python wrapper and the
    method log_for_interval.
    """

    def test_C_pacing_floats_1(self):

        p = myokit.Protocol()
        p.schedule(-80, 0, 1.2345)
        p.schedule(-70, 1.2345, 2.3454)
        p.schedule(-60, 3.5799, 1.4201)

        # Call log_for_interval, which uses the PacingSystem
        d = AnsicEventBasedPacing.log_for_interval(p, 0, 10)

        # Check if the correct values are recorded
        self.assertEqual(d['time'], [0, 1.2345, 3.5799, 5, 10])
        self.assertEqual(d['pace'], [-80, -70, -60, 0, 0])

        # Test fixes for start/end of interval touching events
        p = myokit.Protocol()
        p.schedule(-80, 0, 1.2345)
        p.schedule(-70, 1.2345, 2.3454)

        # Interval end
        d = p.log_for_interval(0, 3.5799)
        self.assertEqual(d['time'], [0, 1.2345, 3.5799])
        self.assertEqual(d['pace'], [-80, -70, 0])

        # Interval start
        d = p.log_for_interval(3.5799, 10)
        self.assertEqual(d['time'], [3.5799, 10])
        self.assertEqual(d['pace'], [0, 0])

    def test_C_pacing_floats_2(self):

        p = myokit.Protocol()
        p.schedule(-80, 0, 3.3333)
        p.schedule(-70, 3.3333, 3.3331)
        p.schedule(-60, 6.6664, 3.3336)

        # Call log_for_interval, which uses the PacingSystem
        d = AnsicEventBasedPacing.log_for_interval(p, 0, 20)

        # Check if the correct values are recorded
        self.assertEqual(d['time'], [0, 3.3333, 6.6664, 10, 20])
        self.assertEqual(d['pace'], [-80, -70, -60, 0, 0])

    def test_C_pacing_floats_3(self):

        p = myokit.Protocol()
        p.schedule(-80, 0, 22159.6)
        p.schedule(-70, 22159.6, 1340.6)
        p.schedule(-60, 23500.2, 6499.8)

        # Call log_for_interval, which uses the PacingSystem
        d = AnsicEventBasedPacing.log_for_interval(p, 0, 40000)

        # Check if the correct values are recorded
        self.assertEqual(d['time'], [0, 22159.6, 23500.2, 30000, 40000])
        self.assertEqual(d['pace'], [-80, -70, -60, 0, 0])


class CVodeSimulationFloatingPointTest(unittest.TestCase):
    """
    Test floating point behavior of C-pacing, using the myokit Simulation class
    with a model without protocol (cvode-free mode).
    """

    def test_cvode_floating_point_protocol_1(self):

        # Tests the protocol handling in a CVODE simulation, which uses the
        # pacing.h file shared by all C/C++ simulation code.

        # Create model without states
        m = myokit.Model()
        c = m.add_component('c')
        t = c.add_variable('t')
        t.set_rhs(0)
        t.set_binding('time')
        v = c.add_variable('v')
        v.set_rhs('0')
        v.set_binding('pace')

        # Create tricky protocol
        p = myokit.Protocol()
        p.schedule(-80, 0, 1.2345)
        p.schedule(-70, 1.2345, 2.3454)
        p.schedule(-60, 3.5799, 1.4201)

        # Run & test
        s = myokit.Simulation(m, p)
        d = s.run(p.characteristic_time())
        self.assertEqual(list(d['c.v']), [-80, -70, -60, 0])

        # Test starting/stopping at difficult points
        p = myokit.Protocol()
        p.schedule(-80, 0, 1.2345)
        p.schedule(-70, 1.2345, 2.3454)

        # Interval end
        s = myokit.Simulation(m, p)
        d = s.run(3.5799)
        self.assertEqual(list(d['c.t']), [0, 1.2345, 3.5799])
        self.assertEqual(list(d['c.v']), [-80, -70, 0])

        # Interval start
        d = s.run(6.4201)
        self.assertEqual(list(d['c.t']), [3.5799, 10])
        self.assertEqual(list(d['c.v']), [0, 0])

    def test_cvode_floating_point_protocol_2(self):

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
        d = s.run(10)

        self.assertEqual(list(d['c.t']), [0, 3.3333, 6.6664, 10])
        self.assertEqual(list(d['c.v']), [-80, -70, -60, 0])

    def test_cvode_floating_point_protocol_3(self):

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
        p.schedule(-80, 0, 22159.6)
        p.schedule(-70, 22159.6, 1340.6)
        p.schedule(-60, 23500.2, 6499.8)

        # Test without state variables, dynamic logging
        s = myokit.Simulation(m, p)
        d = s.run(40000)
        self.assertEqual(list(d['c.t']), [0, 22159.6, 23500.2, 30000, 40000])
        self.assertEqual(list(d['c.v']), [-80, -70, -60, 0, 0])

        # Test without state variables, fixed log times
        s.reset()
        d = s.run(40001, log_times=d['c.t'])
        self.assertEqual(list(d['c.t']), [0, 22159.6, 23500.2, 30000, 40000])
        self.assertEqual(list(d['c.v']), [-80, -70, -60, 0, 0])

        x = c.add_variable('x')
        x.set_rhs('cos(t)')
        x.promote(0)

        # Test with state variables, fixed log times
        s = myokit.Simulation(m, p)
        d = s.run(40001, log_times=d['c.t'])
        self.assertEqual(list(d['c.t']), [0, 22159.6, 23500.2, 30000, 40000])
        self.assertEqual(list(d['c.v']), [-80, -70, -60, 0, 0])

    def test_ending_near_protocol_end(self):
        # Tests ending a CVODE simulation at a point almost equal to (i.e.
        # indistinguishable from) an event point

        m = myokit.load_model('example')
        m.binding('pace').set_binding(None)
        v = m.label('membrane_potential')
        v.set_rhs(0)
        v.demote()
        v.set_binding('pace')

        p = myokit.Protocol()
        p.schedule(-80, 0, 15400)

        # This will cause an error unles handled explicitly
        s = myokit.Simulation(m, p)
        s.run(15400.000000000002)


if __name__ == '__main__':
    unittest.main()
