#!/usr/bin/env python3
#
# Tests protocol creation via myokit.pacing
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import unittest

import myokit


class PacingFactoryTest(unittest.TestCase):
    """
    Tests the pacing factory module `myokit.pacing`.
    """

    def test_blocktrain(self):
        # Test creation of a block train protocol.

        period, duration, offset, level, limit = 1000, 1, 0, 1, 0
        p = myokit.pacing.blocktrain(period, duration, offset, level, limit)
        e = p.events()
        self.assertEqual(len(e), 1)
        e = e[0]
        self.assertEqual(e.level(), level)
        self.assertEqual(e.start(), offset)
        self.assertEqual(e.duration(), duration)
        self.assertEqual(e.period(), period)
        self.assertEqual(e.multiplier(), limit)

        period, duration, offset, level, limit = 500, 0.5, 79, 2.1, 14
        p = myokit.pacing.blocktrain(period, duration, offset, level, limit)
        e = p.events()
        self.assertEqual(len(e), 1)
        e = e[0]
        self.assertEqual(e.level(), level)
        self.assertEqual(e.start(), offset)
        self.assertEqual(e.duration(), duration)
        self.assertEqual(e.period(), period)
        self.assertEqual(e.multiplier(), limit)

    def test_bpm2bcl(self):
        # Test conversion from beats-per-minute to cycle length.

        # Milliseconds
        self.assertEqual(myokit.pacing.bpm2bcl(60), 1000)
        self.assertEqual(myokit.pacing.bpm2bcl(30), 2000)
        self.assertEqual(myokit.pacing.bpm2bcl(120), 500)

        # Seconds
        self.assertEqual(myokit.pacing.bpm2bcl(60, 1), 1)
        self.assertEqual(myokit.pacing.bpm2bcl(30, 1), 2)
        self.assertEqual(myokit.pacing.bpm2bcl(120, 1), 0.5)

    def test_constant(self):
        # Test the creation of a constant protocol.

        level = 0.5
        p = myokit.pacing.constant(level)
        s = myokit.PacingSystem(p)
        self.assertEqual(len(p.events()), 1)
        self.assertEqual(s.pace(), level)
        s.advance(100)
        self.assertEqual(s.pace(), level)
        for i in range(10):
            s.advance(s.next_time())
            self.assertEqual(s.pace(), level)

    def test_steptrain(self):
        # Test the creation of a step protocol.

        vs = [-100, -80, 40, -20]
        vhold = -80
        tpre = 200
        tstep = 1000
        tpost = 800

        p = myokit.pacing.steptrain(vs, vhold, tpre, tstep, tpost)
        self.assertEqual(len(p.events()), 3 * len(vs))
        self.assertEqual(
            p.characteristic_time(), len(vs) * (tpre + tstep + tpost))
        p = iter(p)
        t = 0
        for v in vs:
            e = next(p)
            self.assertEqual(e.level(), vhold)
            self.assertEqual(e.start(), t)
            self.assertEqual(e.duration(), tpre)
            self.assertEqual(e.period(), 0)
            self.assertEqual(e.multiplier(), 0)
            t += tpre

            e = next(p)
            self.assertEqual(e.level(), v)
            self.assertEqual(e.start(), t)
            self.assertEqual(e.duration(), tstep)
            self.assertEqual(e.period(), 0)
            self.assertEqual(e.multiplier(), 0)
            t += tstep

            e = next(p)
            self.assertEqual(e.level(), vhold)
            self.assertEqual(e.start(), t)
            self.assertEqual(e.duration(), tpost)
            self.assertEqual(e.period(), 0)
            self.assertEqual(e.multiplier(), 0)
            t += tpost

    def test_steptrain_linear(self):
        # Test the creation of a step protocol with linear steps.

        # Incrementing steps
        vs = [-40, -20, 0, 20]
        vmin = -40
        vmax = 40
        dv = 20
        vhold = -80
        tpre = 200
        tstep = 1000
        tpost = 800

        p = myokit.pacing.steptrain_linear(
            vmin, vmax, dv, vhold, tpre, tstep, tpost)
        self.assertEqual(len(p.events()), 3 * len(vs))
        self.assertEqual(
            p.characteristic_time(), len(vs) * (tpre + tstep + tpost))
        p = iter(p)
        t = 0
        for v in vs:
            e = next(p)
            self.assertEqual(e.level(), vhold)
            self.assertEqual(e.start(), t)
            self.assertEqual(e.duration(), tpre)
            self.assertEqual(e.period(), 0)
            self.assertEqual(e.multiplier(), 0)
            t += tpre

            e = next(p)
            self.assertEqual(e.level(), v)
            self.assertEqual(e.start(), t)
            self.assertEqual(e.duration(), tstep)
            self.assertEqual(e.period(), 0)
            self.assertEqual(e.multiplier(), 0)
            t += tstep

            e = next(p)
            self.assertEqual(e.level(), vhold)
            self.assertEqual(e.start(), t)
            self.assertEqual(e.duration(), tpost)
            self.assertEqual(e.period(), 0)
            self.assertEqual(e.multiplier(), 0)
            t += tpost

        # Decrementing steps
        vs = [40, 20, 0, -20]
        vmin = 40
        vmax = -40
        dv = -20
        vhold = -80
        tpre = 200
        tstep = 1000
        tpost = 800

        p = myokit.pacing.steptrain_linear(
            vmin, vmax, dv, vhold, tpre, tstep, tpost)
        self.assertEqual(len(p.events()), 3 * len(vs))
        self.assertEqual(
            p.characteristic_time(), len(vs) * (tpre + tstep + tpost))
        p = iter(p)
        t = 0
        for v in vs:
            e = next(p)
            self.assertEqual(e.level(), vhold)
            self.assertEqual(e.start(), t)
            self.assertEqual(e.duration(), tpre)
            self.assertEqual(e.period(), 0)
            self.assertEqual(e.multiplier(), 0)
            t += tpre

            e = next(p)
            self.assertEqual(e.level(), v)
            self.assertEqual(e.start(), t)
            self.assertEqual(e.duration(), tstep)
            self.assertEqual(e.period(), 0)
            self.assertEqual(e.multiplier(), 0)
            t += tstep

            e = next(p)
            self.assertEqual(e.level(), vhold)
            self.assertEqual(e.start(), t)
            self.assertEqual(e.duration(), tpost)
            self.assertEqual(e.period(), 0)
            self.assertEqual(e.multiplier(), 0)
            t += tpost

    def test_steptrain_bad_values(self):
        # Test the creation of a step protocol with illegal times.

        vs = [-100, -80, 40, -20]
        vhold = -80
        tpre = 200
        tstep = 1000
        tpost = 800

        myokit.pacing.steptrain(vs, vhold, tpre, tstep, tpost)
        self.assertRaises(
            ValueError, myokit.pacing.steptrain, vs, vhold, -1, tstep, tpost)
        self.assertRaises(
            ValueError, myokit.pacing.steptrain, vs, vhold, tpre, -1, tpost)
        self.assertRaises(
            ValueError, myokit.pacing.steptrain, vs, vhold, tpre, tstep, -1)

    def test_steptrain_linear_bad_values(self):
        # Test the creation of a step protocol with linear steps and bad
        # values.

        # Incrementing steps
        vmin = -40
        vmax = 40
        dv = 20
        vhold = -80
        tpre = 200
        tstep = 1000
        tpost = 800

        # Wrong direction of dv
        myokit.pacing.steptrain_linear(
            vmin, vmax, dv, vhold, tpre, tstep, tpost)
        self.assertRaises(
            ValueError, myokit.pacing.steptrain_linear, vmin, vmax, -dv, vhold,
            tpre, tstep, tpost)
        myokit.pacing.steptrain_linear(
            vmax, vmin, -dv, vhold, tpre, tstep, tpost)
        self.assertRaises(
            ValueError, myokit.pacing.steptrain_linear, vmax, vmin, dv, vhold,
            tpre, tstep, tpost)

        # Bad times
        self.assertRaises(
            ValueError, myokit.pacing.steptrain_linear, vmin, vmax, dv, vhold,
            -1, tstep, tpost)
        self.assertRaises(
            ValueError, myokit.pacing.steptrain_linear, vmin, vmax, dv, vhold,
            tpre, -1, tpost)
        self.assertRaises(
            ValueError, myokit.pacing.steptrain_linear, vmin, vmax, dv, vhold,
            tpre, tstep, -1)


if __name__ == '__main__':
    unittest.main()
