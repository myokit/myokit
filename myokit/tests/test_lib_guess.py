#!/usr/bin/env python3
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

    def test_add_embedded_protocol_pacing(self):
        # Tests the method to add protocols, to models without a stimulus
        # current

        # 1. Should work for variable bound to pace, and with protocol
        m = myokit.Model('m')
        c = m.add_component('c')
        t = c.add_variable('t')
        t.set_unit(myokit.units.second)
        t.set_binding('time')
        x = c.add_variable('x')
        xa = x.add_variable('a')
        xa.set_rhs(3)
        xb = x.add_variable('b')
        xb.set_rhs('3 * a')
        x.set_rhs('sqrt(b) * 3 [mV]')
        x.set_unit(myokit.units.ampere)
        x.set_binding('pace')

        protocol = myokit.pacing.blocktrain(
            duration=1e-3, offset=0.01, period=1, level=2)

        # Check adding works
        model = m.clone()
        self.assertTrue(guess.add_embedded_protocol(model, protocol))

        # Check generated rhs
        self.assertTrue(isinstance(model.get('c.x').rhs(), myokit.If))
        self.assertEqual(
            model.get('c.x').rhs().code(),
            'if((c.t - offset) % period < duration, 2 [A], 0 [A])')
        self.assertIsNone(model.get('c.x').binding())

        # Check units
        self.assertEqual(
            model.get('c.x').unit(), myokit.units.ampere)
        self.assertEqual(
            model.get('c.x.offset').unit(), myokit.units.second)
        self.assertEqual(
            model.get('c.x.duration').unit(), myokit.units.second)
        self.assertEqual(
            model.get('c.x.period').unit(), myokit.units.second)

        # Check values
        self.assertEqual(model.get('c.x.offset').rhs(),
                         myokit.Number(0.01, myokit.units.second))
        self.assertEqual(model.get('c.x.duration').rhs(),
                         myokit.Number(1e-3, myokit.units.second))
        self.assertEqual(model.get('c.x.period').rhs(),
                         myokit.Number(1, myokit.units.second))

        # 2. Should fail if nothing bound to pace
        x.set_binding(None)
        code = m.code()
        self.assertFalse(guess.add_embedded_protocol(m, protocol))
        self.assertEqual(code, m.code())
        x.set_binding('pace')
        model = m.clone()
        self.assertTrue(guess.add_embedded_protocol(model, protocol))
        self.assertTrue(isinstance(model.get('c.x').rhs(), myokit.If))

        # 3 .Should fail if there's no time variable
        t.set_binding(None)
        code = m.code()
        self.assertFalse(guess.add_embedded_protocol(m, protocol))
        self.assertEqual(code, m.code())
        t.set_binding('time')
        model = m.clone()
        self.assertTrue(guess.add_embedded_protocol(model, protocol))
        self.assertTrue(isinstance(model.get('c.x').rhs(), myokit.If))

        # 4. Should fail if we have a step protocol
        p = myokit.pacing.steptrain([1, 2, 3], -80, 0.01, 1)
        code = m.code()
        self.assertFalse(guess.add_embedded_protocol(m, p))
        self.assertEqual(code, m.code())
        model = m.clone()
        self.assertTrue(guess.add_embedded_protocol(model, protocol))
        self.assertTrue(isinstance(model.get('c.x').rhs(), myokit.If))

        # 5. Should fail if we have a non-zero multiplier
        protocol = myokit.Protocol()
        protocol.schedule(
            duration=1e-3, start=0.01, period=1, level=2, multiplier=10)
        code = m.code()
        self.assertFalse(guess.add_embedded_protocol(m, protocol))
        self.assertEqual(code, m.code())

    def test_add_embedded_protocol_stimulus(self):
        # Tests the method to add protocols to models with a stimulus current

        # 1. Should work for variable bound to pace, and with protocol
        m = myokit.parse_model("""
        [[model]]

        [engine]
        time = 0 [ms]
            in [ms]
            bind time
        pace = x
            x = 5 [1]
            bind pace
            in [1]

        [stimulus]
        i_stim = engine.pace * amplitude
            in [pA]
        amplitude = -80 [pA]
            in [pA]
        """)

        protocol = myokit.pacing.blocktrain(
            duration=0.5, offset=5, period=1000, level=2)

        # Check adding works
        model = m.clone()
        self.assertTrue(guess.add_embedded_protocol(model, protocol))

        # Check generated rhs
        rhs = model.get('stimulus.i_stim').rhs()
        self.assertTrue(isinstance(rhs, myokit.Multiply))
        self.assertTrue(isinstance(rhs[0], myokit.If))

        # Check pacing variable has disappeared
        self.assertNotIn('pace', model.get('engine'))
        self.assertIsNone(model.binding('pace'))

        # Check units
        self.assertEqual(
            model.get('stimulus.i_stim').unit(),
            myokit.units.pA)
        self.assertEqual(
            model.get('stimulus.i_stim.offset').unit(),
            myokit.units.ms)
        self.assertEqual(
            model.get('stimulus.i_stim.duration').unit(),
            myokit.units.ms)
        self.assertEqual(
            model.get('stimulus.i_stim.period').unit(),
            myokit.units.ms)

        # Check values
        self.assertEqual(model.get('stimulus.i_stim.offset').rhs(),
                         myokit.Number(5, myokit.units.ms))
        self.assertEqual(model.get('stimulus.i_stim.duration').rhs(),
                         myokit.Number(0.5, myokit.units.ms))
        self.assertEqual(model.get('stimulus.i_stim.period').rhs(),
                         myokit.Number(1000, myokit.units.ms))

        # 2. Should fail if stimulus variables are present
        model = m.clone()
        p = model.get('stimulus').add_variable('period')
        p.set_unit(myokit.units.ms)
        p.set_rhs(1000)
        p.meta['oxmeta'] = 'membrane_stimulus_current_period'
        guess.add_embedded_protocol(model, protocol)

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

    def test_deep_deps(self):
        # Tests the (hidden) method to find all dependencies of a particular
        # variable.

        m = myokit.parse_model("""
            [[model]]
            c.v = -80

            [c]
            time = 0 bind time
            dot(v) = -i_ion
            i_ion = i1 + i2
            i1 = 5 * v
            i2 = x * v
                x = 13 / time
            z = 2 + y
            y = 3
            """)

        # Simple cases
        y, z = m.get('c.y'), m.get('c.z')
        d = guess._deep_deps(y)
        self.assertEqual(len(d), 0)
        d = guess._deep_deps(z)
        self.assertEqual(d[y], 1)
        self.assertEqual(len(d), 1)

        # Harder cases
        v, time, i_ion = m.get('c.v'), m.get('c.time'), m.get('c.i_ion')
        i1, i2, i2x = m.get('c.i1'), m.get('c.i2'), m.get('c.i2.x')
        d = guess._deep_deps(i2)
        self.assertEqual(d[i2x], 1)
        self.assertEqual(d[time], 2)
        self.assertEqual(len(d), 2)

        d = guess._deep_deps(v)
        self.assertEqual(d[i_ion], 1)
        self.assertEqual(d[i1], 2)
        self.assertEqual(d[i2], 2)
        self.assertEqual(d[i2x], 3)
        self.assertEqual(d[time], 4)
        self.assertEqual(len(d), 5)

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

    def test_remove_nested(self):
        # Tests the method to remove nested variables

        m = myokit.parse_model("""
            [[model]]
            membrane.V = -80

            [membrane]
            t = 0 bind time
            dot(V) = 1 + x + y
                x = 1 + a + y + c
                    a = b
                        f = 9
                        b = 10 - f * g
                        g = 2
                    c = a + d
                    d = 4 * a
                y = 12
                in [mV]
                label membrane_potential
            """)
        m.validate()

        m2 = m.clone()
        v = m2.get('membrane.V')
        v.set_rhs(0)
        myokit.lib.guess._remove_nested(v)
        self.assertEqual(v.unit(), myokit.units.mV)
        self.assertEqual(len(v), 0)

    def test_membrane_capacitance(self):
        # Tests getting the membrane capacitance variable

        # Get by annotation
        m = myokit.parse_model("""
            [[model]]
            membrane.V = -80

            [membrane]
            t = 0 bind time
                oxmeta: it's me
            dot(V) = -1/Cm * i_ion
                oxmeta: membrane_capacitance
            i_ion = 4
            Cm = 1 [pF]
                in [pF]
            """)
        self.assertEqual(guess.membrane_capacitance(m).name(), 'V')

        # Get referenced in Vm
        m = myokit.parse_model("""
            [[model]]
            membrane.V = -80

            [membrane]
            t = 0 bind time
                oxmeta: it's me
            dot(V) = - i_ion
            i_ion = 4
            """)
        self.assertEqual(guess.membrane_capacitance(m).name(), 'i_ion')
        # Must be constant
        m.get('membrane.i_ion').set_rhs('4 * V')
        self.assertIsNone(guess.membrane_capacitance(m))

        # Get by name
        m = myokit.parse_model("""
            [[model]]
            membrane.V = -80

            [membrane]
            t = 0 bind time
            dot(V) = - i_ion
            i_ion = 4
            Cm = 3
                in [pF]
            """)
        c = m.get('membrane.Cm')
        self.assertEqual(guess.membrane_capacitance(m), c)
        c.rename('c')
        self.assertEqual(guess.membrane_capacitance(m), c)
        c.rename('c_m')
        self.assertEqual(guess.membrane_capacitance(m), c)
        c.rename('acap')
        self.assertEqual(guess.membrane_capacitance(m), c)
        c.rename('a_cap')
        self.assertEqual(guess.membrane_capacitance(m), c)
        c.rename('zzz')
        self.assertNotEqual(guess.membrane_capacitance(m), c)

        # Get by unit
        c.rename('Cm')
        self.assertEqual(guess.membrane_capacitance(m), c)
        c.set_unit(None)
        self.assertNotEqual(guess.membrane_capacitance(m), c)
        c.set_unit('pF/cm^2')
        self.assertEqual(guess.membrane_capacitance(m), c)
        c.set_unit('cm^2')
        self.assertEqual(guess.membrane_capacitance(m), c)

        # Bad unit cancels out point for name
        m = myokit.parse_model("""
            [[model]]

            [membrane]
            t = 0 bind time
            Cm = 3
                in [A]
            """)
        self.assertIsNone(guess.membrane_capacitance(m), c)

    def test_membrane_currents(self):
        # Tests getting a list of (outer) membrane currents

        # Test with annotated variable
        m = myokit.load_model('example')
        c = guess.membrane_currents(m)
        self.assertEqual(len(c), 6)
        c = [v.qname() for v in c]
        self.assertIn('ica.ICa', c)
        self.assertIn('ik.IK', c)
        self.assertIn('ik1.IK1', c)
        self.assertIn('ikp.IKp', c)
        self.assertIn('ina.INa', c)
        self.assertIn('ib.Ib', c)

        # Test with Vm
        i = m.label('cellular_current')
        i.set_label(None)
        c = guess.membrane_currents(m)
        self.assertEqual(len(c), 3)
        c = [v.qname() for v in c]
        self.assertIn('membrane.i_diff', c)
        self.assertIn('membrane.i_ion', c)
        self.assertIn('membrane.i_stim', c)

    def test_membrane_potential_1(self):
        # Test finding the membrane potential based on annotations

        m = myokit.parse_model("""
            [[model]]
            membrane.V = -80

            [membrane]
            time = 0 bind time
            dot(V) = 1 [mV/ms]
                in [mV]

            [c]
            x = 5 in [A]
            """)

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
        del x.meta['oxmeta']
        self.assertNotEqual(guess.membrane_potential(m), x)

    def test_membrane_potential_2(self):
        # Test finding the membrane potential based on a scoring system

        # Must be in volts or None
        m = myokit.parse_model("""
            [[model]]
            membrane.V = -80

            [membrane]
            time = 0 bind time
            dot(V) = 1
                in [A]
            """)
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
        m = myokit.parse_model("""
            [[model]]
            membrane.U = -80
            membrane.V = -80
            membrane.W = -80

            [membrane]
            time = 0 bind time
            dot(U) = 1
            dot(V) = 1
            dot(W) = 1
            """)
        self.assertEqual(guess.membrane_potential(m), m.get('membrane.V'))

        # Prefer common component names
        m = myokit.parse_model("""
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
            """)
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
        m = myokit.parse_model("""
            [[model]]
            b.V = -80

            [a]
            time = 0 bind time
            V = 1

            [b]
            dot(V) = 1

            [c]
            V = 1
            """)
        self.assertEqual(guess.membrane_potential(m), m.get('b.V'))

        # Use number of references as tie breaker
        m = myokit.parse_model("""
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
            """)
        self.assertEqual(guess.membrane_potential(m), m.get('b.V'))

        # Don't return really awful guesses
        m = myokit.parse_model("""
            [[model]]

            [a]
            time = 0 bind time
            x = 1
            y = 2
            z = 3
            """)
        self.assertIsNone(guess.membrane_potential(m))

    def test_remove_embedded_protocol(self):
        # Tests extracting an embedded protocol

        # Test without an offset
        model = myokit.parse_model("""
            [[model]]
            c.V = -80

            [c]
            time = 0 [ms]
                in [ms]
                bind time
            dot(V) = 0.1 * i_stim
            i_stim = if(time % period < duration, amplitude, 0)
                in [pA]
            duration = 0.3 [ms]
                in [ms]
            period = 500
            amplitude = -80 [pA]
            d = 3 [m]
            """)
        protocol = myokit.lib.guess.remove_embedded_protocol(model)
        self.assertIsInstance(protocol, myokit.Protocol)
        self.assertEqual(protocol.head().start(), 0)
        self.assertEqual(protocol.head().duration(), 0.3)
        self.assertEqual(protocol.head().period(), 500)

        # Test with an offset
        model = myokit.parse_model("""
            [[model]]
            c.V = -80

            [c]
            time = 0 [ms]
                in [ms]
                bind time
            dot(V) = 0.1 * i_stim
            i_stim = if((time - offset) % period < duration, amplitude, 0)
                in [pA]
            offset = 11 [ms]
                in [ms]
            duration = 0.3 [ms]
                in [ms]
            period = 500
            amplitude = -80 [pA]
            d = 3 [m]
            """)
        m2 = model.clone()
        protocol = myokit.lib.guess.remove_embedded_protocol(m2)
        self.assertIsInstance(protocol, myokit.Protocol)
        self.assertEqual(protocol.head().start(), 11)
        self.assertEqual(protocol.head().duration(), 0.3)
        self.assertEqual(protocol.head().period(), 500)

        # Test various ways it can fail

        # Stimulus current not found
        m2 = model.clone()
        m2.get('c.V').set_rhs(1)
        m2.get('c').remove_variable(m2.get('c.i_stim'))
        m2.get('c').remove_variable(m2.get('c.amplitude'))
        protocol = myokit.lib.guess.remove_embedded_protocol(m2)
        self.assertIsNone(protocol)

        # Duration not found
        m2 = model.clone()
        v = m2.get('c.i_stim')
        v.set_rhs('if((time - offset) % period < 0.4, 0, 0)')
        protocol = myokit.lib.guess.remove_embedded_protocol(m2)
        self.assertIsNone(protocol)

        # Negative duration
        m2 = model.clone()
        m2.get('c.duration').set_rhs(-5)
        protocol = myokit.lib.guess.remove_embedded_protocol(m2)
        self.assertIsNone(protocol)

        # Period not found
        m2 = model.clone()
        v = m2.get('c.i_stim')
        v.set_rhs('if((time - offset) < duration, 0, 0)')
        protocol = myokit.lib.guess.remove_embedded_protocol(m2)
        self.assertIsNone(protocol)

        # Negative period
        m2 = model.clone()
        m2.get('c.period').set_rhs(-5)
        protocol = myokit.lib.guess.remove_embedded_protocol(m2)
        self.assertIsNone(protocol)

        # Amplitude not found
        m2 = model.clone()
        v = m2.get('c.i_stim')
        v.set_rhs('if((time - offset) % period < duration, 0, 0)')
        protocol = myokit.lib.guess.remove_embedded_protocol(m2)
        self.assertIsNone(protocol)

        # Test recovering a protocol created by myokit
        m, p1, _ = myokit.load('example')
        myokit.lib.guess.add_embedded_protocol(m, p1)
        p2 = myokit.lib.guess.remove_embedded_protocol(m)
        self.assertIsInstance(p2, myokit.Protocol)
        self.assertEqual(p1.head().level(), p2.head().level())
        self.assertEqual(p1.head().start(), p2.head().start())
        self.assertEqual(p1.head().duration(), p2.head().duration())
        self.assertEqual(p1.head().period(), p2.head().period())
        self.assertEqual(p1.head().multiplier(), p2.head().multiplier())

    def test_stimulus_current_1(self):
        # Test finding the stimulus current based on annotations

        m = myokit.parse_model("""
            [[model]]
            c.V = -80

            [c]
            time = 0 bind time
            pace = 0 bind pace
            dot(V) = 0.1
            i_stim = pace * 10 [pA]
                in [pA]
            d = 3 [m]
            """)

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
        del x.meta['oxmeta']
        self.assertNotEqual(guess.stimulus_current(m), x)

    def test_stimulus_current_2(self):
        # Test finding the stimulus current using dependence on time or pace

        # Find variable furthest from time / pace (in A)
        m = myokit.parse_model("""
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
            """)
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
        m = myokit.parse_model("""
            [[model]]

            [t]
            time = 0 bind time
                in [s]
            i_stim = 5 [A]
                in [A]
            i_steam = 4 [A]
                in [A]
            """)

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

    def test_stimulus_current_info_1(self):
        # Tests guessing of stimulus info based on annotations

        # Guess all using oxmeta labels
        m = myokit.parse_model("""
            [[model]]
            c.v = -80

            [c]
            t = 18 / 2
                oxmeta: membrane_stimulus_current
            a = 0 bind time
                oxmeta: membrane_stimulus_current_period
            dot(v) = -a
                oxmeta: membrane_stimulus_current_amplitude
            b = a / v
                oxmeta: membrane_stimulus_current_offset
            c = t
                oxmeta: membrane_stimulus_current_duration
            """)
        i = guess.stimulus_current_info(m)
        self.assertEqual(i['current'], m.get('c.t'))
        self.assertEqual(i['amplitude'], m.get('c.v'))
        self.assertEqual(i['duration'], m.get('c.c'))
        self.assertEqual(i['period'], m.get('c.a'))
        self.assertEqual(i['offset'], m.get('c.b'))
        self.assertIsNone(i['amplitude_expression'])

        # Try one without a label
        m.get('c.v').meta['oxmeta'] = 'monkey'
        i = guess.stimulus_current_info(m)
        self.assertIsNone(i['amplitude'])
        self.assertIsNotNone(i['amplitude_expression'])

        # Stimulus current can have a myokit label
        m.get('c.v').meta['oxmeta'] = 'membrane_stimulus_current_amplitude'
        m.get('c.t').set_label('stimulus_current')
        i = guess.stimulus_current_info(m)
        self.assertEqual(i['current'], m.get('c.t'))
        self.assertEqual(i['amplitude'], m.get('c.v'))
        self.assertEqual(i['duration'], m.get('c.c'))
        self.assertEqual(i['period'], m.get('c.a'))
        self.assertEqual(i['offset'], m.get('c.b'))
        self.assertIsNone(i['amplitude_expression'])
        del m.get('c.t').meta['oxmeta']
        i = guess.stimulus_current_info(m)
        self.assertEqual(i['current'], m.get('c.t'))
        self.assertEqual(i['amplitude'], m.get('c.v'))
        self.assertEqual(i['duration'], m.get('c.c'))
        self.assertEqual(i['period'], m.get('c.a'))
        self.assertEqual(i['offset'], m.get('c.b'))
        self.assertIsNone(i['amplitude_expression'])

        # No current? no info
        m.get('c.t').set_label(None)
        i = guess.stimulus_current_info(m)
        self.assertIsNone(i['current'])
        self.assertIsNone(i['amplitude'])
        self.assertIsNone(i['duration'])
        self.assertIsNone(i['period'])
        self.assertIsNone(i['offset'])
        self.assertIsNone(i['amplitude_expression'])

    def test_stimulus_current_info_amplitude(self):
        # Tests guessing of stimulus amplitude

        m = myokit.parse_model("""
            [[model]]
            [c]
            t = 0 [s] bind time
                in [s]
            i_stim = 4 * if((t - s) % p < d, a, 0 [pA])
                in [pA]
            s = 10 [s] in [s]
            p = 1000 [s] in [s]
            d = 0.5 [s] in [s]
            a = 5 [pA] in [pA]
            """)
        i = guess.stimulus_current_info(m)
        self.assertEqual(i['current'], m.get('c.i_stim'))

        # Guess from correct unit or None
        a = m.get('c.a')
        self.assertEqual(i['amplitude'], a)
        a.set_unit(None)
        i = guess.stimulus_current_info(m)
        self.assertEqual(i['amplitude'], a)

        # Reject incompatible unit
        a.set_unit('pF')
        i = guess.stimulus_current_info(m)
        self.assertIsNone(i['amplitude'])
        a.set_unit(None)

        # Prefer explicit current over None
        m = myokit.parse_model("""
            [[model]]
            [c]
            t = 0 [s] bind time
                in [s]
            i_stim = if((t - s) % p < d, a, 0 [pA])
                in [pA]
            s = 10 [s] in [s]
            p = 1000 [s] in [s]
            d = 0.5 [s] in [s]
            a = b
            b = 5 in [pA]
            """)
        b = m.get('c.b')
        i = guess.stimulus_current_info(m)
        self.assertEqual(i['amplitude'], b)
        b.set_unit(None)
        i = guess.stimulus_current_info(m)
        self.assertNotEqual(i['amplitude'], b)

        # Guessing from name
        m = myokit.parse_model("""
            [[model]]
            [c]
            t = 0 [s] bind time
                in [s]
            i_stim = 2 + if((t - s) % p < d, a, 0 [pA])
                in [pA]
            s = 10 [s] in [s]
            p = 1000 [s] in [s]
            d = 0.5 [s] in [s]
            a = b in [pA]
            b = c in [pA]
            c = 7 [pA] in [pA]
            """)
        b = m.get('c.b')
        i = guess.stimulus_current_info(m)
        self.assertEqual(i['current'], m.get('c.i_stim'))
        self.assertNotEqual(i['amplitude'], b)
        b.rename('amplitude')
        i = guess.stimulus_current_info(m)
        self.assertEqual(i['amplitude'], b)
        b.rename('zamplitudez')
        i = guess.stimulus_current_info(m)
        self.assertEqual(i['amplitude'], b)
        b.rename('umplitudo')
        i = guess.stimulus_current_info(m)
        self.assertNotEqual(i['amplitude'], b)
        b.rename('current_zamplitudez')
        i = guess.stimulus_current_info(m)
        self.assertEqual(i['amplitude'], b)
        b.rename('current_zzz')
        i = guess.stimulus_current_info(m)
        self.assertEqual(i['amplitude'], b)
        b.rename('umplitudo')
        i = guess.stimulus_current_info(m)
        self.assertNotEqual(i['amplitude'], b)

        # Guessing from distance
        self.assertEqual(i['amplitude'], m.get('c.a'))

        # Can't already be used
        m.get('c.a').meta['oxmeta'] = 'membrane_stimulus_current_offset'
        i = guess.stimulus_current_info(m)
        self.assertNotEqual(i['amplitude'], m.get('c.a'))

    def test_stimulus_current_info_amplitude_expression(self):
        # Tests guessing of stimulus amplitude expression

        # Expression is not set if amplitude can be determined
        m = myokit.parse_model("""
            [[model]]
            [c]
            t = 0 [s] bind time
                in [s]
            i_stim = amplitude
                in [pA]
            amplitude = 1 [pA]
                in [pA]
            """)
        i = guess.stimulus_current_info(m)
        self.assertIsNotNone(i['amplitude'])
        self.assertIsNone(i['amplitude_expression'])

        # Simple constant (can be zero)
        m = myokit.parse_model("""
            [[model]]
            [c]
            t = 0 [s] bind time
                in [s]
            i_stim = 0 [pA]
                in [pA]
            """)
        i = guess.stimulus_current_info(m)
        self.assertIsNone(i['amplitude'])
        self.assertEqual(str(i['amplitude_expression']), '0 [pA]')

        # More complicated constant
        i_stim = m.get('c.i_stim')
        r = '1 + 2 + 3 / sqrt(4)'
        i_stim.set_rhs(r)
        i = guess.stimulus_current_info(m)
        self.assertEqual(str(i['amplitude_expression']), r)

        # Non-zero part of an if (and ignore time variable)
        m = myokit.parse_model("""
            [[model]]
            [c]
            t = 0 bind time
            i_stim = if(t < 5, 1, 0)
            """)
        i = guess.stimulus_current_info(m)
        self.assertEqual(str(i['amplitude_expression']), '1')

        # Non-zero part of an if
        i_stim = m.get('c.i_stim')
        i_stim.set_rhs('if(t < 5, 0, 2)')
        i = guess.stimulus_current_info(m)
        self.assertEqual(str(i['amplitude_expression']), '2')
        i_stim.set_rhs('1 - if(t < 5, 0, 0)')
        i = guess.stimulus_current_info(m)
        self.assertIsNone(i['amplitude_expression'])

        # Non-zero part of a piecewise
        i_stim.set_rhs('piecewise(t < 5, 0, t < 10, 0, 0)')
        i = guess.stimulus_current_info(m)
        self.assertIsNone(i['amplitude_expression'])
        i_stim.set_rhs('1 - piecewise(t < 5, 3, t < 10, 0, 0)')
        i = guess.stimulus_current_info(m)
        self.assertEqual(str(i['amplitude_expression']), '3')
        i_stim.set_rhs('2 + piecewise(t < 5, 0, t < 10, 2 / 4, 0)')
        i = guess.stimulus_current_info(m)
        self.assertEqual(str(i['amplitude_expression']), '2 / 4')
        i_stim.set_rhs('3 / piecewise(t < 5, 0, t < 10, 0, -18 / 2.4)')
        i = guess.stimulus_current_info(m)
        self.assertEqual(str(i['amplitude_expression']), '-18 / 2.4')

        # No suitable expression
        m = myokit.parse_model("""
            [[model]]
            [c]
            t = 0 bind time
            i_stim = t * 3
            """)
        i = guess.stimulus_current_info(m)
        self.assertIsNone(i['amplitude'])
        self.assertIsNone(i['amplitude_expression'])

    def test_stimulus_current_info_duration(self):
        # Tests guessing of stimulus duration

        m = myokit.parse_model("""
            [[model]]
            [c]
            t = 0 [s] bind time
                in [s]
            i_stim = if((t - s) % p < d, a, 0 [pA])
                in [pA]
            s = 10 [s] in [s]
                oxmeta: membrane_stimulus_current_offset
            p = 1000 [s] in [s]
                oxmeta: membrane_stimulus_current_period
            d = 0.5 [s] in [s]
            a = 5 [pA] in [pA]
                oxmeta: membrane_stimulus_current_amplitude
            """)
        i = guess.stimulus_current_info(m)
        self.assertEqual(i['current'], m.get('c.i_stim'))

        # Note: Having labels above allows the method to exit early. We can't
        # test this mini-optimisation, but it does show up in coverage

        # Guess from name + (correct unit or None)
        v = m.get('c.d')
        self.assertIsNone(i['duration'], v)
        v.rename('durandurations')
        i = guess.stimulus_current_info(m)
        self.assertEqual(i['duration'], v)
        v.set_unit(None)
        i = guess.stimulus_current_info(m)
        self.assertEqual(i['duration'], v)
        v.set_unit('s^2')
        i = guess.stimulus_current_info(m)
        self.assertIsNone(i['duration'], v)
        v.set_unit('1')
        i = guess.stimulus_current_info(m)
        self.assertIsNone(i['duration'], v)

        # Can't already be used
        v.set_unit(None)
        i = guess.stimulus_current_info(m)
        self.assertEqual(i['duration'], v)
        m.get('c.s').meta['oxmeta'] = 'hello'
        v.meta['oxmeta'] = 'membrane_stimulus_current_offset'
        i = guess.stimulus_current_info(m)
        self.assertNotEqual(i['duration'], v)

    def test_stimulus_current_info_offset(self):
        # Tests guessing of stimulus offset

        m = myokit.parse_model("""
            [[model]]
            [c]
            t = 0 [s] bind time
                in [s]
            i_stim = if((t - s) % p < d, a, 0 [pA])
                in [pA]
            s = 10 [s] in [s]
            p = 1000 [s] in [s]
            d = 0.5 [s] in [s]
            a = 5 [pA] in [pA]
            """)
        i = guess.stimulus_current_info(m)
        self.assertEqual(i['current'], m.get('c.i_stim'))

        # Guess from name + (correct unit or None)
        v = m.get('c.d')
        self.assertIsNone(i['offset'], v)
        v.rename('foffsetti')
        i = guess.stimulus_current_info(m)
        self.assertEqual(i['offset'], v)
        v.set_unit(None)
        i = guess.stimulus_current_info(m)
        self.assertEqual(i['offset'], v)
        v.set_unit('s^2')
        i = guess.stimulus_current_info(m)
        self.assertIsNone(i['offset'], v)
        v.set_unit('1')
        i = guess.stimulus_current_info(m)
        self.assertIsNone(i['offset'], v)

        # Can't already be used
        v.set_unit(None)
        i = guess.stimulus_current_info(m)
        self.assertEqual(i['offset'], v)
        v.meta['oxmeta'] = 'membrane_stimulus_current_period'
        i = guess.stimulus_current_info(m)
        self.assertNotEqual(i['offset'], v)

    def test_stimulus_current_info_period(self):
        # Tests guessing of stimulus period

        m = myokit.parse_model("""
            [[model]]
            [c]
            t = 0 [s] bind time
                in [s]
            i_stim = if((t - s) % p < d, a, 0 [pA])
                in [pA]
            s = 10 [s] in [s]
            p = 1000 [s] in [s]
            d = 0.5 [s] in [s]
            a = 5 [pA] in [pA]
            """)
        i = guess.stimulus_current_info(m)
        self.assertEqual(i['current'], m.get('c.i_stim'))

        # Guess from name + (correct unit or None)
        v = m.get('c.d')
        self.assertIsNone(i['period'], v)
        v.rename('stim_periodic')
        i = guess.stimulus_current_info(m)
        self.assertEqual(i['period'], v)
        v.set_unit(None)
        i = guess.stimulus_current_info(m)
        self.assertEqual(i['period'], v)
        v.set_unit('s^2')
        i = guess.stimulus_current_info(m)
        self.assertIsNone(i['period'], v)

        # Period can be dimensionless too
        v.set_unit('1')
        i = guess.stimulus_current_info(m)
        self.assertEqual(i['period'], v)

        # Can't already be used
        v.meta['oxmeta'] = 'membrane_stimulus_current_offset'
        i = guess.stimulus_current_info(m)
        self.assertNotEqual(i['duration'], v)

    def test_stimulus_current_info_period_duration_offset(self):
        # Tests what happens when a single variable matches multiple words

        # In this model, amplitude should be x, and at most 2 variables out of
        # duration, period, and offset can be set.
        m = myokit.parse_model("""
            [[model]]
            [c]
            t = 0 [s] bind time
                in [s]
            i_stim = if((t - x) % perioddurationoffset < x, 1, 0)
            x = 5
            perioddurationoffset = 2
                in [s]
            """)
        i = guess.stimulus_current_info(m)
        self.assertEqual(i['current'], m.get('c.i_stim'))
        self.assertEqual(i['amplitude'], m.get('c.x'))
        self.assertIsNone(i['amplitude_expression'])
        empties = [x for x in i.values() if x is None]
        self.assertEqual(len(empties), 3)

        # Don't match period
        x = m.get('c.perioddurationoffset')
        x.rename('durationoffset')
        i = guess.stimulus_current_info(m)
        empties = [k for k, v in i.items() if v is None]
        self.assertEqual(len(empties), 3)
        self.assertIn('period', empties)

        # Don't match duration
        x.rename('periodnoffset')
        i = guess.stimulus_current_info(m)
        empties = [k for k, v in i.items() if v is None]
        self.assertEqual(len(empties), 3)
        self.assertIn('duration', empties)

        # Don't match offset
        x.rename('durationperiod')
        i = guess.stimulus_current_info(m)
        empties = [k for k, v in i.items() if v is None]
        self.assertEqual(len(empties), 3)
        self.assertIn('offset', empties)


if __name__ == '__main__':
    unittest.main()
