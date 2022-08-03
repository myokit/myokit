#!/usr/bin/env python3
#
# Tests the Variable class.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import myokit
import numpy as np
import unittest


# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp


class VariableTest(unittest.TestCase):
    """
    Tests parts of :class:`myokit.Variable`.
    """
    def test_clamp(self):
        # Tests clamping a variable to a fixed value
        m = myokit.parse_model("""
            [[model]]
            z.g = 2
            z.h = 6.123
            z.p = 1.5

            [z]
            t = 0 [s]
                in [s]
                bind time
            a = 3 [ms]
                in [ms]
            b = 4 [mV]
            b2 = 3
                in [A]
            c = 4 [A] * 3 [A] / 2 [A] + 5 [A]
                in [A]
            d = e + f + t + 8 [m*s] / g
                e = 1 [s]
                    in [s]
                f = 2 [s]
                    in [s]
                in [s]
            dot(g) = 3 [m/s]
                in [m]
            dot(h) = h / 3 [s] + i + 2 [m] / d
                i = 4 [m/s] * j * m * n + h / 1 [s]
                    in [m/s]
                    j = 3 + 2 * k + n
                        k = 4
                    m = j - 1
                    n = 2
                in [m]
            dot(p) = 1
                in [mV]
            """)
        m.validate()
        m.check_units(myokit.UNIT_TOLERANT)
        m_org = m.clone()

        # Clamp literal constants
        m.get('z.a').clamp(5)
        self.assertEqual(m.get('z.a').rhs(), myokit.Number(5, myokit.units.ms))
        m.get('z.b').clamp()
        self.assertEqual(m.get('z.b').rhs(), myokit.Number(4))
        m.get('z.b2').clamp(1)
        self.assertEqual(m.get('z.b2').rhs(), myokit.Number(1, myokit.units.A))
        m.get('z.c').clamp()
        self.assertEqual(m.get('z.c').rhs(), myokit.Number(11, myokit.units.A))

        # Clamp variable with child and sibling dependencies
        d = m.get('z.d')
        self.assertEqual(len(d), 2)
        m.get('z.d.e')
        self.assertFalse(d.is_constant())
        d.clamp()
        self.assertEqual(d.rhs(), myokit.Number(7, myokit.units.s))
        self.assertTrue(d.is_constant())
        self.assertEqual(len(d), 0)
        self.assertRaises(KeyError, m.get, 'z.d.e')
        self.assertRaises(KeyError, m.get, 'z.d.f')
        del d

        # Clamp simple state
        g = m.get('z.g')
        self.assertTrue(g.is_state())
        self.assertTrue(g.state_value() != 10)
        self.assertEqual(g.unit(), myokit.units.m)
        self.assertEqual(g.rhs().unit(), myokit.units.m / myokit.units.s)
        self.assertEqual(m.count_states(), 3)
        g.clamp(10)
        self.assertTrue(g.is_literal())
        self.assertFalse(g.is_state())
        self.assertEqual(g.rhs(), myokit.Number(10, myokit.units.m))
        self.assertEqual(m.count_states(), 2)
        del g

        # Clamp simple state with missing units
        p = m.get('z.p')
        self.assertTrue(p.is_state())
        self.assertTrue(p.rhs().eval() != 1.5)
        self.assertEqual(m.count_states(), 2)
        p.clamp()
        self.assertTrue(p.is_literal())
        self.assertFalse(p.is_state())
        self.assertEqual(p.rhs(), myokit.Number(1.5, myokit.units.mV))
        self.assertEqual(m.count_states(), 1)
        del p

        # Clamp state with child and sibling dependencies
        h = m.get('z.h')
        self.assertEqual(len(h), 1)
        self.assertEqual(len(list(h.variables(deep=True))), 5)
        m.get('z.h.i.j.k')
        self.assertFalse(h.is_constant())
        self.assertEqual(m.count_states(), 1)
        h.clamp()
        self.assertEqual(h.rhs(), myokit.Number(6.123, myokit.units.m))
        self.assertTrue(h.is_constant())
        self.assertEqual(len(h), 0)
        self.assertRaises(KeyError, m.get, 'z.h.i.j.k')
        self.assertRaises(KeyError, m.get, 'z.h.i')
        self.assertRaises(KeyError, m.get, 'z.h.i.m')
        self.assertEqual(m.count_states(), 0)
        del h

        # Clamp nested variable
        m = m_org.clone()
        h = m.get('z.h')
        x = h.eval()
        self.assertEqual(len(list(h.variables(deep=True))), 5)
        self.assertEqual(len(h), 1)
        h.get('i.j.k')
        self.assertFalse(h.is_constant())
        i = h.get('i')
        self.assertEqual(len(list(i.variables(deep=True))), 4)
        self.assertFalse(i.is_literal())
        y = i.eval()
        i.clamp()
        self.assertTrue(i.is_literal())
        self.assertEqual(i.eval(), y)
        self.assertEqual(h.eval(), x)
        self.assertEqual(len(list(i.variables(deep=True))), 0)
        self.assertEqual(len(list(h.variables(deep=True))), 1)
        del h, i

    def test_convert_unit(self):
        # Test changing variable units

        m = myokit.parse_model("""
            [[model]]
            membrane.V = -83

            [env]
            t = 0 [ms] bind time
                in [ms]

            [membrane]
            dot(V) = - (ikr.i + ina.i * 1 [cm^2/uF])
                in [mV]
            dotv = 5 [mV/ms] + dot(V)
                in [mV/ms]

            [cell]
            Cm = 0.123 [uF]
                in [uF]

            [ina]
            i = 12 [uA/cm^2]
                in [uA/cm^2]

            [ikr]
            use membrane.V
            E = -81 [mV]
                in [mV]
            g = 23 [mS/uF]
                in [mS/uF]
            i = g * (V - E)
                in [uA/uF]
        """)
        m.check_units(myokit.UNIT_STRICT)

        # Convert to same
        code = m.code()
        v = m.get('membrane.V')
        v.convert_unit('mV')
        self.assertEqual(code, m.code())

        # Convert state
        vdot = v.rhs().eval()
        self.assertNotEqual(v.unit(), myokit.units.V)
        v.convert_unit('V')
        self.assertEqual(v.unit(), myokit.units.V)

        # Check dot(v) is the same, and all units are compatible
        vdot /= 1000
        self.assertEqual(vdot, v.rhs().eval())
        m.check_units(myokit.UNIT_STRICT)

        # Convert non-state
        i = m.get('ina.i')
        self.assertNotEqual(i.unit(), myokit.parse_unit('uA/uF'))
        i.convert_unit('uA/uF', ['1 [uF/cm^2]'])
        self.assertEqual(i.unit(), myokit.parse_unit('uA/uF'))

        # Check dot(v) is the same, and all units are compatible
        self.assertEqual(vdot, v.rhs().eval())
        m.check_units(myokit.UNIT_STRICT)

        # Convert time variable
        t = m.time()
        self.assertNotEqual(t.unit(), myokit.units.s)
        t.convert_unit('s')
        self.assertEqual(t.unit(), myokit.units.s)

        # Check dot(v) is the same, and all units are compatible
        vdot *= 1000
        self.assertEqual(vdot, v.rhs().eval())
        m.check_units(myokit.UNIT_STRICT)

    def test_is_referenced(self):
        # Test :meth:`Variable.is_referenced().

        m = myokit.Model()
        c = m.add_component('c')
        v = c.add_variable('v')
        v.set_rhs(3)
        w = c.add_variable('w')
        w.set_rhs(4)

        self.assertFalse(v.is_referenced())
        self.assertFalse(w.is_referenced())
        v.set_rhs('3 * w')
        self.assertFalse(v.is_referenced())
        self.assertTrue(w.is_referenced())
        w.set_rhs('2 * v')
        self.assertTrue(v.is_referenced())
        self.assertTrue(w.is_referenced())

        z = c.add_variable('z')
        z.set_rhs('3 * v')
        self.assertFalse(z.is_referenced())
        self.assertTrue(v.is_referenced())
        w.set_rhs(1)
        self.assertTrue(v.is_referenced())
        z.set_rhs(2)
        self.assertFalse(v.is_referenced())

    def test_labelling(self):
        # Test variable labelling.

        m = myokit.Model()
        c = m.add_component('c')
        v = c.add_variable('v')
        v.set_rhs(3)

        self.assertFalse(v.is_labelled())
        self.assertIsNone(v.label())
        v.set_label('membrane_potential')
        self.assertTrue(v.is_labelled())
        self.assertEqual(v.label(), 'membrane_potential')
        v.set_label(None)
        self.assertFalse(v.is_labelled())
        self.assertIsNone(v.label())

    def test_promote_demote(self):
        # Test variable promotion and demotion.

        m = myokit.Model()
        c = m.add_component('c')
        v = c.add_variable('v')
        v.set_rhs(3)

        self.assertTrue(v.is_literal())
        self.assertTrue(v.is_constant())
        self.assertFalse(v.is_intermediary())
        self.assertFalse(v.is_state())
        self.assertEqual(v.lhs(), myokit.Name(v))
        self.assertRaises(Exception, v.demote)
        self.assertRaises(Exception, v.indice)
        self.assertRaises(Exception, v.state_value)

        v.promote(3)
        self.assertFalse(v.is_literal())
        self.assertFalse(v.is_constant())
        self.assertFalse(v.is_intermediary())
        self.assertTrue(v.is_state())
        self.assertEqual(v.lhs(), myokit.Derivative(myokit.Name(v)))
        self.assertEqual(v.indice(), 0)
        self.assertEqual(v.state_value(), 3)

        v.demote()
        self.assertTrue(v.is_literal())
        self.assertTrue(v.is_constant())
        self.assertFalse(v.is_intermediary())
        self.assertFalse(v.is_state())
        self.assertEqual(v.lhs(), myokit.Name(v))
        self.assertRaises(Exception, v.demote)
        self.assertRaises(Exception, v.indice)
        self.assertRaises(Exception, v.state_value)

        # Test errors
        v.promote(3)
        self.assertRaisesRegex(Exception, 'already', v.promote, 4)
        v.demote()
        v.set_binding('time')
        self.assertRaisesRegex(Exception, 'cannot be bound', v.promote, 4)
        w = v.add_variable('w')
        self.assertRaisesRegex(
            Exception, 'only be added to Components', w.promote, 4)

        # Test we can't demote a variable with references to its derivative
        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        x.set_rhs(3)
        x.promote()
        y = c.add_variable('y')
        y.set_rhs('1 + dot(x)')
        self.assertRaisesRegex(
            Exception, 'references to its derivative', x.demote)
        y.set_rhs('1 + x')
        x.demote()

    def test_pyfunc(self):
        # Test :meth:`Variable.pyfunc().

        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        x.set_rhs(3)
        y = c.add_variable('y')
        y.set_rhs(4)
        z = c.add_variable('z')
        z.set_rhs('3 * x + y')

        # Invalid model: pyfunc fails
        self.assertRaises(myokit.IntegrityError, z.pyfunc)
        t = c.add_variable('time')
        t.set_rhs(0)
        t.set_binding('time')

        # No states --> No arguments
        f = z.pyfunc(use_numpy=False)
        self.assertEqual(f(), 13)
        f = z.pyfunc(use_numpy=True)
        self.assertEqual(f(), 13)
        f, args = z.pyfunc(use_numpy=False, arguments=True)
        self.assertEqual(args, [])
        f, args = z.pyfunc(use_numpy=True, arguments=True)
        self.assertEqual(args, [])

        # One state
        y.promote(3)
        f = z.pyfunc(use_numpy=False)
        self.assertEqual(f(1), 10)
        f = z.pyfunc(use_numpy=True)
        self.assertEqual(f(1), 10)
        self.assertTrue(
            np.all(f(np.array([1, 2, 4])) == np.array([10, 11, 13])))
        f, args = z.pyfunc(use_numpy=False, arguments=True)
        self.assertEqual(args, (myokit.Name(y), ))
        f, args = z.pyfunc(use_numpy=True, arguments=True)
        self.assertEqual(args, (myokit.Name(y), ))

        # Two states (alphabetically ordered)
        x.promote(2)
        f = z.pyfunc(use_numpy=False)
        self.assertEqual(f(1, 2), 5)
        f = z.pyfunc(use_numpy=True)
        self.assertEqual(f(1, 2), 5)
        self.assertTrue(
            np.all(f(
                np.array([1, 2, 4]), np.array([3, 2, 1])
            ) == np.array([6, 8, 13]))
        )
        f, args = z.pyfunc(use_numpy=False, arguments=True)
        self.assertEqual(args, (myokit.Name(x), myokit.Name(y)))
        f, args = z.pyfunc(use_numpy=True, arguments=True)
        self.assertEqual(args, (myokit.Name(x), myokit.Name(y)))

    def test_refs_by_and_to(self):
        # Test :meth:`Variable.is_referenced().

        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        x.set_rhs(3)
        y = c.add_variable('y')
        y.set_rhs(4)
        z = c.add_variable('z')
        z.set_rhs(0)

        self.assertEqual(list(x.refs_to()), [])
        self.assertEqual(list(y.refs_to()), [])
        self.assertEqual(list(z.refs_to()), [])
        self.assertEqual(list(x.refs_by()), [])
        self.assertEqual(list(y.refs_by()), [])
        self.assertEqual(list(z.refs_by()), [])

        z.set_rhs('3 * x')
        self.assertEqual(list(x.refs_to()), [])
        self.assertEqual(list(y.refs_to()), [])
        self.assertEqual(list(z.refs_to()), [x])
        self.assertEqual(list(x.refs_by()), [z])
        self.assertEqual(list(y.refs_by()), [])
        self.assertEqual(list(z.refs_by()), [])

        y.set_rhs('2 + x')
        self.assertEqual(list(x.refs_to()), [])
        self.assertEqual(list(y.refs_to()), [x])
        self.assertEqual(list(z.refs_to()), [x])
        self.assertEqual(set(x.refs_by()), set([y, z]))
        self.assertEqual(list(y.refs_by()), [])
        self.assertEqual(list(z.refs_by()), [])

        # Remove by removing RHS
        y.set_rhs(None)
        self.assertEqual(list(x.refs_to()), [])
        self.assertEqual(list(y.refs_to()), [])
        self.assertEqual(list(z.refs_to()), [x])
        self.assertEqual(set(x.refs_by()), set([z]))
        self.assertEqual(list(y.refs_by()), [])
        self.assertEqual(list(z.refs_by()), [])
        y.set_rhs('2 + x')

        # Remove by changing RHS
        z.set_rhs(2)
        self.assertEqual(list(x.refs_to()), [])
        self.assertEqual(list(y.refs_to()), [x])
        self.assertEqual(list(z.refs_to()), [])
        self.assertEqual(list(x.refs_by()), [y])
        self.assertEqual(list(y.refs_by()), [])
        self.assertEqual(list(z.refs_by()), [])

        # State refs
        self.assertRaises(Exception, x.refs_by, True)
        self.assertRaises(Exception, y.refs_by, True)
        self.assertRaises(Exception, z.refs_by, True)
        self.assertEqual(list(x.refs_to(True)), [])
        self.assertEqual(list(y.refs_to(True)), [])
        self.assertEqual(list(z.refs_to(True)), [])

        # After promoting x, its refs should become srefs
        x.promote(3)
        self.assertEqual(list(x.refs_to(False)), [])
        self.assertEqual(list(y.refs_to(False)), [])
        self.assertEqual(list(z.refs_to(False)), [])
        self.assertEqual(list(x.refs_by(False)), [])
        self.assertEqual(list(y.refs_by(False)), [])
        self.assertEqual(list(z.refs_by(False)), [])
        self.assertEqual(list(x.refs_to(True)), [])
        self.assertEqual(list(y.refs_to(True)), [x])
        self.assertEqual(list(z.refs_to(True)), [])
        self.assertEqual(list(x.refs_by(True)), [y])
        self.assertRaises(Exception, y.refs_by, True)
        self.assertRaises(Exception, z.refs_by, True)

        # Add another reference to x, should now appear in state refs
        z.set_rhs('3 + x')
        self.assertEqual(list(x.refs_to(False)), [])
        self.assertEqual(list(y.refs_to(False)), [])
        self.assertEqual(list(z.refs_to(False)), [])
        self.assertEqual(list(x.refs_by(False)), [])
        self.assertEqual(list(y.refs_by(False)), [])
        self.assertEqual(list(z.refs_by(False)), [])
        self.assertEqual(list(x.refs_to(True)), [])
        self.assertEqual(list(y.refs_to(True)), [x])
        self.assertEqual(list(z.refs_to(True)), [x])
        self.assertEqual(set(x.refs_by(True)), set([y, z]))
        self.assertRaises(Exception, y.refs_by, True)
        self.assertRaises(Exception, z.refs_by, True)
        self.assertEqual(list(y._srefs_by), [])
        self.assertEqual(list(z._srefs_by), [])

        # Demote x: Now its state refs should become ordinary refs again
        x.demote()
        self.assertEqual(list(x.refs_to(False)), [])
        self.assertEqual(list(y.refs_to(False)), [x])
        self.assertEqual(list(z.refs_to(False)), [x])
        self.assertEqual(set(x.refs_by(False)), set([y, z]))
        self.assertEqual(list(y.refs_by(False)), [])
        self.assertEqual(list(z.refs_by(False)), [])
        self.assertEqual(list(x.refs_to(True)), [])
        self.assertEqual(list(y.refs_to(True)), [])
        self.assertEqual(list(z.refs_to(True)), [])
        self.assertRaises(Exception, x.refs_by, True)
        self.assertRaises(Exception, y.refs_by, True)
        self.assertRaises(Exception, z.refs_by, True)
        self.assertEqual(list(x._srefs_by), [])
        self.assertEqual(list(y._srefs_by), [])
        self.assertEqual(list(z._srefs_by), [])
        x.validate()

        #
        # Another test, this time promoting first, then demoting later
        #
        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        x.promote(0)
        x.set_rhs(3)
        y = c.add_variable('y')
        y.set_rhs('3 + x')

        self.assertEqual(list(x.refs_to(False)), [])
        self.assertEqual(list(y.refs_to(False)), [])
        self.assertEqual(list(x.refs_by(False)), [])
        self.assertEqual(list(y.refs_by(False)), [])
        self.assertEqual(list(x.refs_to(True)), [])
        self.assertEqual(list(y.refs_to(True)), [x])
        self.assertEqual(list(x.refs_by(True)), [y])
        self.assertRaises(Exception, y.refs_by, True)

        # Demote x: Now its state refs should become ordinary refs again
        x.demote()
        self.assertEqual(list(x.refs_to(False)), [])
        self.assertEqual(list(y.refs_to(False)), [x])
        self.assertEqual(list(x.refs_by(False)), [y])
        self.assertEqual(list(y.refs_by(False)), [])
        self.assertEqual(list(x.refs_to(True)), [])
        self.assertEqual(list(y.refs_to(True)), [])
        self.assertRaises(Exception, x.refs_by, True)
        self.assertRaises(Exception, y.refs_by, True)
        x.validate()

        #
        # Another test, this time including self reference by a state
        #
        m = myokit.Model()
        c = m.add_component('c')
        t = c.add_variable('t')
        t.set_rhs(0)
        t.set_binding('time')
        x = c.add_variable('x')
        x.promote(0)
        x.set_rhs('3 - x')
        y = c.add_variable('y')
        y.set_rhs('3 + x')

        self.assertEqual(list(x.refs_to(False)), [])
        self.assertEqual(list(y.refs_to(False)), [])
        self.assertEqual(list(x.refs_by(False)), [])
        self.assertEqual(list(y.refs_by(False)), [])
        self.assertEqual(list(x.refs_to(True)), [x])
        self.assertEqual(list(y.refs_to(True)), [x])
        self.assertEqual(set(x.refs_by(True)), set([x, y]))
        self.assertRaises(Exception, y.refs_by, True)

        # Now demoting causes self-reference
        m.validate()
        x.demote()
        x.validate()
        self.assertRaises(myokit.CyclicalDependencyError, m.validate)

    def test_remove_child_variables(self):
        # Tests removing all child variables
        m = myokit.parse_model("""
            [[model]]

            [z]
            t = 0 [s]
                in [s]
                bind time
            a = 4 [A] * 3 [A] / 2 [A] + 5 [A]
                in [A]
            b = c + d + t + 8 [s]
                c = 1 [s]
                    in [s]
                d = 2 [s]
                    in [s]
                in [s]
            e = f
                f = g
                    g = h
                    h = i + j
                        i = 1 [m]
                        j = 2 [m]
                in [m]
            """)
        m.validate()
        m.check_units(myokit.UNIT_TOLERANT)
        m_org = m.clone()

        # Remove children on var without children
        m.get('z.a').remove_child_variables()
        self.assertTrue(m.is_similar(m_org, True))

        # Remove children on var with used children
        self.assertRaisesRegex(
            myokit.IntegrityError, 'the RHS still depends on <z.e.f>.',
            m.get('z.e').remove_child_variables)
        self.assertTrue(m.is_similar(m_org, True))

        # Remove children on nested var with used children
        self.assertRaisesRegex(
            myokit.IntegrityError,
            'depends on <z.e.f.h.[i|j]> and <z.e.f.h.[j|i]>.',
            m.get('z.e.f.h').remove_child_variables)
        self.assertTrue(m.is_similar(m_org, True))

        # Remove children on nested var with unused children
        e = m.get('z.e')
        h = e.get('f.h')
        self.assertEqual(len(list(h.variables())), 2)
        self.assertEqual(len(list(e.variables(deep=True))), 5)
        h.set_rhs('3 [m]')
        h.remove_child_variables()
        self.assertEqual(len(list(h.variables())), 0)
        self.assertEqual(len(list(e.variables(deep=True))), 3)
        m.validate()
        del h

        # Remove children on var with unused children
        e.set_rhs('1.234 [m]')
        self.assertEqual(len(list(e.variables(deep=True))), 3)
        e.remove_child_variables()
        self.assertEqual(len(list(e.variables(deep=True))), 0)
        m.validate()

    def test_rename(self):
        # Test :meth:`Variable.rename().

        # The functional part of this is done by Component.move_variable, so no
        # extensive testing is required
        m = myokit.Model()
        c = m.add_component('c')
        v = c.add_variable('v')
        v.rename('w')
        self.assertEqual(v.name(), 'w')
        self.assertEqual(v.qname(), 'c.w')

    def test_set_state_value(self):
        # Test :meth:`Variable.set_state_value()`.

        m = myokit.Model()
        c = m.add_component('c')
        v = c.add_variable('v')
        w = c.add_variable('w')

        # Test basic functionality
        v.promote(10)
        self.assertEqual(v.state_value(), 10)
        v.set_state_value(12)
        self.assertEqual(v.state_value(), 12)

        # Only states have this option
        v.demote()
        self.assertRaisesRegex(
            Exception, 'Only state variables', v.set_state_value, 3)
        self.assertRaisesRegex(
            Exception, 'Only state variables', w.set_state_value, 3)

        # State values must be literals
        v.promote(3)
        self.assertRaises(
            myokit.NonLiteralValueError, v.set_state_value, w.lhs())

    def test_set_unit(self):
        # Test :meth:`Variable.set_unit()`.
        m = myokit.Model()
        c = m.add_component('c')
        v = c.add_variable('v')

        # Test basic functionality
        s = myokit.UNIT_STRICT
        self.assertIsNone(v.unit())
        self.assertEqual(v.unit(s), myokit.units.dimensionless)
        v.set_unit(myokit.units.Newton)
        self.assertEqual(v.unit(), myokit.units.Newton)
        self.assertEqual(v.unit(s), myokit.units.Newton)

        # Set via unit parsing
        v.set_unit('kg/ms')
        self.assertEqual(v.unit(), myokit.parse_unit('kg/ms'))

        # Set to a non unit
        self.assertRaisesRegex(
            TypeError, 'expects a myokit.Unit', v.set_unit, 12)

    def test_unit(self):
        # Test :meth:`Variable.unit()`.
        m = myokit.Model()
        c = m.add_component('c')
        v = c.add_variable('v')
        d = myokit.units.dimensionless

        # Test no unit case
        self.assertIsNone(v.unit())
        self.assertEqual(v.unit(myokit.UNIT_STRICT), d)

        # RHS unit is not variable unit
        v.set_rhs('1 [ms]')
        self.assertIsNone(v.unit())
        self.assertEqual(v.unit(myokit.UNIT_STRICT), d)

        # Test unit-set case
        kg = myokit.units.kg
        v.set_unit(kg)
        self.assertEqual(v.unit(), kg)
        self.assertEqual(v.unit(myokit.UNIT_STRICT), kg)

    def test_validate(self):
        # Test some edge cases for validation.

        # Test scope rule:
        # Variables are allowed access all children of their ancestors
        m = myokit.Model()
        c = m.add_component('c')
        p = c.add_variable('p')
        p11 = p.add_variable('p11')
        p12 = p.add_variable('p12')
        p121 = p12.add_variable('p121')
        p121.set_rhs('p + p11 + p12')
        p121.validate()

        # But not children of children of ancestors
        p112 = p11.add_variable('p112')
        p121.set_rhs(p112.lhs())
        self.assertRaises(myokit.IllegalReferenceError, p121.validate)

        # RHS cannot be a partial, init, or condition
        m = myokit.Model()
        c = m.add_component('c')
        p = c.add_variable('p')
        p.set_rhs(3)
        q = c.add_variable('q')
        q.set_rhs(2)
        p.validate()
        p.set_rhs(myokit.PartialDerivative(p.lhs(), q.lhs()))
        self.assertRaisesRegex(
            myokit.IntegrityError, 'Partial derivatives', p.validate)
        p.promote(1)
        p.set_rhs(myokit.InitialValue(myokit.Name(p)))
        self.assertRaisesRegex(
            myokit.IntegrityError, 'Initial value', p.validate)
        p.set_rhs('q == 3')
        self.assertRaisesRegex(
            myokit.IntegrityError, 'can not be a condition', p.validate)

    def test_value(self):
        # Test :meth:`Variable.value()`.

        m = myokit.Model()
        c = m.add_component('c')
        v = c.add_variable('v')
        v.set_rhs('1 + 2 + 3 + 4')
        self.assertEqual(v.value(), 10)


if __name__ == '__main__':
    unittest.main()
