#!/usr/bin/env python
#
# Tests the lib.guess variable meaning guessing module
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import unittest

import myokit
import myokit.lib.guess as guess

# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp


class LibGuessTest(unittest.TestCase):
    """
    Tests for ``myokit.lib.guess``.
    """

    def test_compatible_units(self):
        # Tests the (hidden) method to check if a unit is compatible with one
        # of a list of types
        A = myokit.units.A
        pA = myokit.units.pA
        AF = A / myokit.units.F
        Am2 = A / myokit.units.m**2

        units = [pA, AF, Am2]
        self.assertTrue(guess._compatible_units(pA, units))
        self.assertTrue(guess._compatible_units(A, units))
        self.assertTrue(guess._compatible_units(AF, units))
        self.assertTrue(guess._compatible_units(Am2, units))
        self.assertTrue(guess._compatible_units(123 * Am2, units))
        self.assertFalse(guess._compatible_units(myokit.units.m, units))
        self.assertFalse(guess._compatible_units(myokit.units.V, units))
        self.assertFalse(guess._compatible_units(None, units))

    def test_distance_to_bound(self):
        # Tests the (hidden) method to calculate the distance to a bound
        # variable

        # Test case 1
        # Get distance to env.time, but only for variables that depend on
        # time but are otherwise constant
        m = myokit.parse_model("""
            [[model]]
            c.a = 1

            [env]
            time = 0 bind time

            [c]
            dot(a) = (b + 7) / a + c
            b = exp(a)
            c = 10 * b + d
            d = 1 + e
            e = 2 + f
            f = 3 / env.time
            g = 4 + e
            """)
        d = guess._distance_to_bound(m.get('env.time'))
        self.assertEqual(len(d), 4)
        self.assertEqual(d[m.get('c.d')], 3)
        self.assertEqual(d[m.get('c.e')], 2)
        self.assertEqual(d[m.get('c.f')], 1)
        self.assertEqual(d[m.get('c.g')], 3)
        self.assertEqual(m.get('env.time').binding(), 'time')

        # Test case 2
        m = myokit.parse_model("""
            [[model]]
            c.a = 1

            [env]
            time = 0 bind time

            [c]
            dot(a) = (b + 7) / a + c
            b = exp(a) + j
            c = 1 + env.time
            d = 2 / env.time
            e = 3 * env.time
            f = c + d
            g = j ^ d
            h = 1 - e
            i = cos(e)
            j = 2 * f
            """)
        d = guess._distance_to_bound(m.get('env.time'))
        self.assertEqual(len(d), 8)
        self.assertEqual(d[m.get('c.c')], 1)
        self.assertEqual(d[m.get('c.d')], 1)
        self.assertEqual(d[m.get('c.e')], 1)
        self.assertEqual(d[m.get('c.f')], 2)
        self.assertEqual(d[m.get('c.g')], 2)
        self.assertEqual(d[m.get('c.h')], 2)
        self.assertEqual(d[m.get('c.i')], 2)
        self.assertEqual(d[m.get('c.j')], 3)
        self.assertEqual(m.get('env.time').binding(), 'time')

        # Can only be called on bound variable
        self.assertRaisesRegex(
            ValueError, 'must be a bound variable',
            guess._distance_to_bound, m.get('c.a'))
        self.assertRaisesRegex(
            ValueError, 'must be a bound variable',
            guess._distance_to_bound, m.get('c.c'))

    def test_membrane_potential_1(self):
        # Test finding the membrane potential based on annotations

        m = myokit.parse_model('''
            [[model]]
            membrane.V = -80

            [membrane]
            time = 0 bind time
            dot(V) = 1 [mV/ms]
                in [mV]

            [c]
            x = 5 in [A]
            ''')

        # Annotated with membrane_potential: return regardless of other factors
        x = m.get('c.x')
        x.set_label('membrane_potential')
        self.assertEqual(guess.membrane_potential(m), x)
        x.set_label(None)
        x.set_label('membrane_potentials')
        self.assertNotEqual(guess.membrane_potential(m), x)

        # Alternatively, use oxmeta annotation
        x.meta['oxmeta'] = 'membrane_voltage'
        self.assertEqual(guess.membrane_potential(m), x)
        del(x.meta['oxmeta'])
        self.assertNotEqual(guess.membrane_potential(m), x)

    def test_membrane_potential_2(self):
        # Test finding the membrane potential based on a scoring system

        # Must be in volts or None
        m = myokit.parse_model('''
            [[model]]
            membrane.V = -80

            [membrane]
            time = 0 bind time
            dot(V) = 1
                in [A]
            ''')
        self.assertIsNone(guess.membrane_potential(m))
        v = m.get('membrane.V')
        v.set_unit('V')
        self.assertEqual(guess.membrane_potential(m), v)
        v.set_unit('MV')
        self.assertEqual(guess.membrane_potential(m), v)
        v.set_unit(None)
        self.assertEqual(guess.membrane_potential(m), v)

        # Prefer volts over none
        w = m.get('membrane').add_variable('Vm')
        w.set_rhs(1)
        w.promote(-80)
        w.set_unit('mV')
        self.assertEqual(guess.membrane_potential(m), w)
        w.set_unit(None)
        v.set_unit('kV')
        self.assertEqual(guess.membrane_potential(m), v)

        # Prefer common variable names
        m = myokit.parse_model('''
            [[model]]
            membrane.U = -80
            membrane.V = -80
            membrane.W = -80

            [membrane]
            time = 0 bind time
            dot(U) = 1
            dot(V) = 1
            dot(W) = 1
            ''')
        self.assertEqual(guess.membrane_potential(m), m.get('membrane.V'))

        # Prefer common component names
        m = myokit.parse_model('''
            [[model]]
            a.V = -80
            membrane.V = -80
            c.V = -80

            [a]
            time = 0 bind time
            dot(V) = 1

            [membrane]
            dot(V) = 1

            [c]
            dot(V) = 1
            ''')
        self.assertEqual(guess.membrane_potential(m), m.get('membrane.V'))
        # Synergy gives extra points
        m.get('a.V').set_unit('mV')
        self.assertEqual(guess.membrane_potential(m), m.get('membrane.V'))
        m.get('a.V').set_unit(None)
        # Component name works without variable name
        m.get('a.V').rename('W')
        m.get('membrane.V').rename('W')
        m.get('c.V').rename('W')
        self.assertEqual(guess.membrane_potential(m), m.get('membrane.W'))

        # Prefer states
        m = myokit.parse_model('''
            [[model]]
            b.V = -80

            [a]
            time = 0 bind time
            V = 1

            [b]
            dot(V) = 1

            [c]
            V = 1
            ''')
        self.assertEqual(guess.membrane_potential(m), m.get('b.V'))

        # Use number of references as tie breaker
        m = myokit.parse_model('''
            [[model]]

            [a]
            time = 0 bind time
            V = 1
            x = V + b.V

            [b]
            V = 1

            [c]
            V = 1
            x = V + b.V
            ''')
        self.assertEqual(guess.membrane_potential(m), m.get('b.V'))

        # Don't return really awful guesses
        m = myokit.parse_model('''
            [[model]]

            [a]
            time = 0 bind time
            x = 1
            y = 2
            z = 3
            ''')
        self.assertIsNone(guess.membrane_potential(m))

    def test_stimulus_current_1(self):
        # Test finding the stimulus current based on annotations

        m = myokit.parse_model('''
            [[model]]
            c.V = -80

            [c]
            time = 0 bind time
            pace = 0 bind pace
            dot(V) = 0.1
            i_stim = pace * 10 [pA]
                in [pA]
            d = 3 [m]
            ''')

        # Annotated with stimulus_current: return regardless of other factors
        x = m.get('c.d')
        x.set_label('stimulus_current')
        self.assertEqual(guess.stimulus_current(m), x)
        x.set_label(None)
        x.set_label('stimulus_currents')
        self.assertNotEqual(guess.stimulus_current(m), x)

        # Alternatively, use oxmeta annotation
        x.meta['oxmeta'] = 'membrane_stimulus_current'
        self.assertEqual(guess.stimulus_current(m), x)
        del(x.meta['oxmeta'])
        self.assertNotEqual(guess.stimulus_current(m), x)

    def test_stimulus_current_2(self):
        # Test finding the stimulus current using dependence on time or pace

        # Find variable furthest from time / pace (in A)
        m = myokit.parse_model('''
            [[model]]

            [t]
            pace = 0 bind pace
            time = 0 bind time
                in [s]
            a = time * 1 [A/s]
            b = 2 * a
            c = 3 * b
            d = 4 * c
            i_stim = 5 [A]
                in [A]
            ''')
        a, b, c, d = [m.get(var) for var in ['t.a', 't.b', 't.c', 't.d']]
        self.assertEqual(guess.stimulus_current(m), d)

        # Prefer explicitly correct unit
        c.set_unit('A')
        self.assertEqual(guess.stimulus_current(m), c)
        c.set_unit(None)
        self.assertEqual(guess.stimulus_current(m), d)
        b.set_unit('A/F')
        self.assertEqual(guess.stimulus_current(m), b)
        d.set_unit('A/cm^2')
        self.assertEqual(guess.stimulus_current(m), d)

        # Disallow incorrect unit
        d.set_unit('m')
        self.assertEqual(guess.stimulus_current(m), b)
        b.set_unit(None)
        self.assertEqual(guess.stimulus_current(m), c)
        d.set_unit(None)
        self.assertEqual(guess.stimulus_current(m), d)

        # Prefer variables with known names
        m2 = m.clone()
        x = m2.get('t').add_variable('test')
        x.set_rhs('1 * a')
        self.assertEqual(guess.stimulus_current(m2), m2.get('t.d'))
        x = m2.get('t.i_stim')
        x.set_rhs('1 * a')
        self.assertEqual(guess.stimulus_current(m2), x)
        # Even if others have better units
        x.set_unit(None)
        m2.get('t.d').set_unit('A')
        self.assertEqual(guess.stimulus_current(m2), x)
        # Allow other names
        x.rename('istim')
        self.assertEqual(guess.stimulus_current(m2), x)
        x.rename('ist')
        self.assertEqual(guess.stimulus_current(m2), x)
        x.rename('i_st')
        self.assertEqual(guess.stimulus_current(m2), x)

        # This still works if using pace instead of time
        m.get('t.pace').set_binding(None)
        m.get('t.time').set_binding(None)
        m.get('t.time').set_binding('pace')
        self.assertEqual(guess.stimulus_current(m), d)

        # But not with other bindings
        m.get('t.time').set_binding(None)
        m.get('t.time').set_binding('plaice')
        self.assertNotEqual(guess.stimulus_current(m), d)

    def test_stimulus_current_3(self):
        # Test finding the stimulus current if it's a constant

        # Find variable furthest from time / pace (in A)
        m = myokit.parse_model('''
            [[model]]

            [t]
            time = 0 bind time
                in [s]
            i_stim = 5 [A]
                in [A]
            i_steam = 4 [A]
                in [A]
            ''')

        # Correct name and unit
        i = m.get('t.i_stim')
        self.assertEqual(guess.stimulus_current(m), i)

        # Unit wrong or name wrong: don't return
        i.set_unit('m')
        self.assertIsNone(guess.stimulus_current(m))

        # Other allowed units
        i.set_unit('pA')
        self.assertEqual(guess.stimulus_current(m), i)
        i.set_unit('A/kF')
        self.assertEqual(guess.stimulus_current(m), i)
        i.set_unit('A/hm^2')
        self.assertEqual(guess.stimulus_current(m), i)
        i.set_unit(None)
        self.assertEqual(guess.stimulus_current(m), i)
        i.set_unit('mV')
        self.assertIsNone(guess.stimulus_current(m))

        # Other allowed names
        i.set_unit('pA')
        self.assertEqual(guess.stimulus_current(m), i)
        i.rename('istim')
        self.assertEqual(guess.stimulus_current(m), i)
        i.rename('ist')
        self.assertEqual(guess.stimulus_current(m), i)
        i.rename('i_st')
        self.assertEqual(guess.stimulus_current(m), i)
        i.rename('ii_st')
        self.assertIsNone(guess.stimulus_current(m))


if __name__ == '__main__':
    unittest.main()
