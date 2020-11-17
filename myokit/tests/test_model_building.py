#!/usr/bin/env python3
#
# Tests the model building API.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import myokit
import unittest

# Strings in Python 2 and 3
try:
    basestring
except NameError:
    basestring = str

# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp

# Further model API tests are found in:
#  - test_dependency_checking.py


class ModelBuildTest(unittest.TestCase):

    def test_model_creation(self):
        # Create a model
        m = myokit.Model('LotkaVolterra')

        # Add the first component
        X = m.add_component('X')
        self.assertEqual(X.qname(), 'X')
        self.assertEqual(X.parent(), m)
        self.assertIsInstance(X, myokit.Component)
        self.assertIn(X.qname(), m)
        self.assertEqual(len(m), 1)

        # Add variable a
        self.assertFalse(X.has_variable('a'))
        a = X.add_variable('a')
        self.assertTrue(X.has_variable('a'))
        self.assertEqual(a, a)
        self.assertIsInstance(a, myokit.Variable)
        self.assertEqual(len(X), 1)
        self.assertIn(a.name(), X)
        a.set_rhs(3)
        self.assertFalse(a.is_state())
        self.assertFalse(a.is_intermediary())
        self.assertTrue(a.is_constant())
        self.assertEqual(a.lhs(), myokit.Name(a))
        self.assertEqual(a.rhs(), myokit.Number(3))
        self.assertEqual(a.rhs().eval(), 3)
        self.assertEqual(a.code(), 'a = 3\n')
        self.assertEqual(a.eq().code(), 'X.a = 3')
        self.assertEqual(a.lhs().code(), 'X.a')
        self.assertEqual(a.rhs().code(), '3')
        self.assertEqual(
            a.eq(), myokit.Equation(myokit.Name(a), myokit.Number(3)))

        # Check lhs
        a_name1 = myokit.Name(a)
        a_name2 = myokit.Name(a)
        self.assertEqual(a_name1, a_name1)
        self.assertEqual(a_name2, a_name2)
        self.assertEqual(a_name1, a_name2)
        self.assertEqual(a_name2, a_name1)

        # Add variable b with two temporary variables
        b = X.add_variable('b')
        self.assertIsInstance(b, myokit.Variable)
        self.assertEqual(len(X), 2)
        self.assertIn(b.name(), X)
        self.assertFalse(b.has_variable('b1'))
        b1 = b.add_variable('b1')
        self.assertTrue(b.has_variable('b1'))
        self.assertEqual(len(b), 1)
        self.assertIn(b1.name(), b)
        self.assertIsInstance(b1, myokit.Variable)
        b2 = b.add_variable('b2')
        self.assertEqual(len(b), 2)
        self.assertIn(b2.name(), b)
        self.assertIsInstance(b2, myokit.Variable)
        b1.set_rhs(1)
        b2.set_rhs(
            myokit.Minus(
                myokit.Minus(myokit.Name(a), myokit.Name(b1)),
                myokit.Number(1))
        )
        b.set_rhs(myokit.Plus(myokit.Name(b1), myokit.Name(b2)))
        self.assertEqual(b.rhs().eval(), 2)
        self.assertFalse(b.is_state())
        self.assertFalse(b.is_intermediary())
        self.assertTrue(b.is_constant())
        self.assertEqual(b.lhs(), myokit.Name(b))

        # Add state variable x
        x = X.add_variable('x')
        x.set_rhs(10)
        x.promote()
        self.assertNotEqual(x, X)
        self.assertIsInstance(x, myokit.Variable)
        self.assertEqual(len(X), 3)
        self.assertIn(x.name(), X)
        self.assertTrue(x.is_state())
        self.assertFalse(x.is_intermediary())
        self.assertFalse(x.is_constant())
        self.assertEqual(x.lhs(), myokit.Derivative(myokit.Name(x)))
        self.assertEqual(x.indice(), 0)

        # Test demoting, promoting
        x.demote()
        self.assertFalse(x.is_state())
        self.assertFalse(x.is_intermediary())
        self.assertTrue(x.is_constant())
        self.assertEqual(x.lhs(), myokit.Name(x))
        x.promote()
        self.assertTrue(x.is_state())
        self.assertFalse(x.is_intermediary())
        self.assertFalse(x.is_constant())
        self.assertEqual(x.lhs(), myokit.Derivative(myokit.Name(x)))
        x.demote()
        x.promote()
        x.demote()
        x.promote()
        self.assertTrue(x.is_state())
        self.assertFalse(x.is_intermediary())
        self.assertFalse(x.is_constant())
        self.assertEqual(x.lhs(), myokit.Derivative(myokit.Name(x)))

        # Add second component, variables
        Y = m.add_component('Y')
        self.assertNotEqual(X, Y)
        self.assertEqual(len(m), 2)
        c = Y.add_variable('c')
        c.set_rhs(myokit.Minus(myokit.Name(a), myokit.Number(1)))
        d = Y.add_variable('d')
        d.set_rhs(2)
        y = Y.add_variable('y')
        y.promote()

        # Set rhs for x and y
        x.set_rhs(myokit.Minus(
            myokit.Multiply(myokit.Name(a), myokit.Name(x)),
            myokit.Multiply(
                myokit.Multiply(myokit.Name(b), myokit.Name(x)),
                myokit.Name(y)
            )
        ))
        x.set_state_value(10)
        self.assertEqual(x.rhs().code(), 'X.a * X.x - X.b * X.x * Y.y')
        y.set_rhs(myokit.Plus(
            myokit.Multiply(
                myokit.PrefixMinus(myokit.Name(c)), myokit.Name(y)
            ),
            myokit.Multiply(
                myokit.Multiply(myokit.Name(d), myokit.Name(x)),
                myokit.Name(y)
            )
        ))
        y.set_state_value(5)
        self.assertEqual(y.rhs().code(), '-Y.c * Y.y + Y.d * X.x * Y.y')

        # Add ano component, variables
        Z = m.add_component('Z')
        self.assertNotEqual(X, Z)
        self.assertNotEqual(Y, Z)
        self.assertEqual(len(m), 3)
        t = Z.add_variable('total')
        self.assertEqual(t.name(), 'total')
        self.assertEqual(t.qname(), 'Z.total')
        self.assertEqual(t.qname(X), 'Z.total')
        self.assertEqual(t.qname(Z), 'total')
        t.set_rhs(myokit.Plus(myokit.Name(x), myokit.Name(y)))
        self.assertFalse(t.is_state())
        self.assertFalse(t.is_constant())
        self.assertTrue(t.is_intermediary())
        self.assertEqual(t.rhs().code(), 'X.x + Y.y')
        self.assertEqual(t.rhs().code(X), 'x + Y.y')
        self.assertEqual(t.rhs().code(Y), 'X.x + y')
        self.assertEqual(t.rhs().code(Z), 'X.x + Y.y')

        # Add engine component
        E = m.add_component('engine')
        self.assertNotEqual(X, E)
        self.assertNotEqual(Y, E)
        self.assertNotEqual(Z, E)
        self.assertEqual(len(m), 4)
        time = E.add_variable('time')
        time.set_rhs(0)
        self.assertIsNone(time.binding())
        time.set_binding('time')
        self.assertIsNotNone(time.binding())

        # Check state
        state = [i for i in m.states()]
        self.assertEqual(len(state), 2)
        self.assertIn(x, state)
        self.assertIn(y, state)

        # Test variable iterators
        def has(*v):
            for var in v:
                self.assertIn(var, vrs)
            self.assertEqual(len(vrs), len(v))
        vrs = [i for i in m.variables()]
        has(a, b, c, d, x, y, t, time)
        vrs = [i for i in m.variables(deep=True)]
        has(a, b, c, d, x, y, t, b1, b2, time)
        vrs = [i for i in m.variables(const=True)]
        has(a, b, c, d)
        vrs = [i for i in m.variables(const=True, deep=True)]
        has(a, b, c, d, b1, b2)
        vrs = [i for i in m.variables(const=False)]
        has(x, y, t, time)
        vrs = [i for i in m.variables(const=False, deep=True)]
        has(x, y, t, time)
        vrs = [i for i in m.variables(state=True)]
        has(x, y)
        vrs = [i for i in m.variables(state=True, deep=True)]
        has(x, y)
        vrs = [i for i in m.variables(state=False)]
        has(a, b, c, d, t, time)
        vrs = [i for i in m.variables(state=False, deep=True)]
        has(a, b, c, d, t, b1, b2, time)
        vrs = [i for i in m.variables(inter=True)]
        has(t)
        vrs = [i for i in m.variables(inter=True, deep=True)]
        has(t)
        vrs = [i for i in m.variables(inter=False)]
        has(a, b, c, d, x, y, time)
        vrs = [i for i in m.variables(inter=False, deep=True)]
        has(a, b, c, d, x, y, b1, b2, time)
        vrs = list(m.variables(const=True, state=True))
        has()
        vrs = list(m.variables(const=True, state=False))
        has(a, b, c, d)

        # Test sorted variable iteration
        names = [v.name() for v in m.variables(deep=True, sort=True)]
        self.assertEqual(names, [
            'a', 'b', 'b1', 'b2', 'x', 'c', 'd', 'y', 'total', 'time'])

        # Test equation iteration
        # Deeper testing is done when testing the ``variables`` method.
        eq = [eq for eq in X.equations(deep=False)]
        self.assertEqual(len(eq), 3)
        self.assertEqual(len(eq), X.count_equations(deep=False))
        eq = [eq for eq in X.equations(deep=True)]
        self.assertEqual(len(eq), 5)
        self.assertEqual(len(eq), X.count_equations(deep=True))
        eq = [eq for eq in Y.equations(deep=False)]
        self.assertEqual(len(eq), 3)
        self.assertEqual(len(eq), Y.count_equations(deep=False))
        eq = [eq for eq in Y.equations(deep=True)]
        self.assertEqual(len(eq), 3)
        self.assertEqual(len(eq), Y.count_equations(deep=True))
        eq = [eq for eq in Z.equations(deep=False)]
        self.assertEqual(len(eq), 1)
        self.assertEqual(len(eq), Z.count_equations(deep=False))
        eq = [eq for eq in Z.equations(deep=True)]
        self.assertEqual(len(eq), 1)
        self.assertEqual(len(eq), Z.count_equations(deep=True))
        eq = [eq for eq in E.equations(deep=False)]
        self.assertEqual(len(eq), 1)
        eq = [eq for eq in E.equations(deep=True)]
        self.assertEqual(len(eq), 1)
        eq = [eq for eq in m.equations(deep=False)]
        self.assertEqual(len(eq), 8)
        eq = [eq for eq in m.equations(deep=True)]
        self.assertEqual(len(eq), 10)

        # Test dependency mapping
        def has(var, *dps):
            lst = vrs[m.get(var).lhs() if isinstance(var, basestring) else var]
            self.assertEqual(len(lst), len(dps))
            for d in dps:
                d = m.get(d).lhs() if isinstance(d, basestring) else d
                self.assertIn(d, lst)

        vrs = m.map_shallow_dependencies(omit_states=False)
        self.assertEqual(len(vrs), 12)
        has('X.a')
        has('X.b', 'X.b.b1', 'X.b.b2')
        has('X.b.b1')
        has('X.b.b2', 'X.a', 'X.b.b1')
        has('X.x', 'X.a', 'X.b', myokit.Name(x), myokit.Name(y))
        has(myokit.Name(x))
        has('Y.c', 'X.a')
        has('Y.d')
        has('Y.y', 'Y.c', 'Y.d', myokit.Name(x), myokit.Name(y))
        has(myokit.Name(y))
        has('Z.total', myokit.Name(x), myokit.Name(y))
        vrs = m.map_shallow_dependencies()
        self.assertEqual(len(vrs), 10)
        has('X.a')
        has('X.b', 'X.b.b1', 'X.b.b2')
        has('X.b.b1')
        has('X.b.b2', 'X.a', 'X.b.b1')
        has('X.x', 'X.a', 'X.b')
        has('Y.c', 'X.a')
        has('Y.d')
        has('Y.y', 'Y.c', 'Y.d')
        has('Z.total')
        vrs = m.map_shallow_dependencies(collapse=True)
        self.assertEqual(len(vrs), 8)
        has('X.a')
        has('X.b', 'X.a')
        has('X.x', 'X.a', 'X.b')
        has('Y.c', 'X.a')
        has('Y.d')
        has('Y.y', 'Y.c', 'Y.d')
        has('Z.total')

        # Validate
        m.validate()

        # Get solvable order
        order = m.solvable_order()
        self.assertEqual(len(order), 5)
        self.assertIn('*remaining*', order)
        self.assertIn('X', order)
        self.assertIn('Y', order)
        self.assertIn('Z', order)

        # Check that X comes before Y
        pos = dict([(name, k) for k, name in enumerate(order)])
        self.assertLess(pos['X'], pos['Y'])
        self.assertEqual(pos['*remaining*'], 4)

        # Check component equation lists
        eqs = order['*remaining*']
        self.assertEqual(len(eqs), 0)
        eqs = order['Z']
        self.assertEqual(len(eqs), 1)
        self.assertEqual(eqs[0].code(), 'Z.total = X.x + Y.y')
        eqs = order['Y']
        self.assertEqual(len(eqs), 3)
        self.assertEqual(
            eqs[2].code(), 'dot(Y.y) = -Y.c * Y.y + Y.d * X.x * Y.y')
        eqs = order['X']
        self.assertEqual(len(eqs), 5)
        self.assertEqual(eqs[0].code(), 'X.a = 3')
        self.assertEqual(eqs[1].code(), 'b1 = 1')
        self.assertEqual(eqs[2].code(), 'b2 = X.a - b1 - 1')
        self.assertEqual(eqs[3].code(), 'X.b = b1 + b2')

        # Test model export and cloning
        code1 = m.code()
        code2 = m.clone().code()
        self.assertEqual(code1, code2)

    def test_resolve(self):
        # Test if an error is raised when a variable can't be resolved.

        m = myokit.Model('Resolve')
        c = m.add_component('c')
        p = c.add_variable('p')
        q = c.add_variable('q')
        p.set_rhs('10 * q')
        self.assertRaises(myokit.ParseError, q.set_rhs, '10 * r')

    def test_scope(self):
        # Test if illegal references are detected.

        m = myokit.Model('Scope')
        c = m.add_component('c')
        p = c.add_variable('p')
        q = p.add_variable('q')
        p.set_rhs('10 + q')
        q.set_rhs('18 / 2.4')
        d = m.add_component('d')
        r = d.add_variable('r')
        r.set_rhs(myokit.Name(q))
        self.assertRaises(myokit.IllegalReferenceError, r.validate)

    def test_invalid_names(self):
        # Test if invalid or duplicate names are detected.

        m = myokit.Model('Duplicates')
        c0 = m.add_component('c0')
        t = c0.add_variable('time')
        t.set_rhs(myokit.Number(0))
        t.set_binding('time')

        # Test add component
        # Duplicates
        self.assertRaises(myokit.DuplicateName, m.add_component, 'c0')
        # Badly formed names
        self.assertRaises(myokit.InvalidNameError, m.add_component, '0')
        self.assertRaises(myokit.InvalidNameError, m.add_component, '_0')
        self.assertRaises(myokit.InvalidNameError, m.add_component, '123abvc')
        self.assertRaises(myokit.InvalidNameError, m.add_component, 'ab cd')
        self.assertRaises(myokit.InvalidNameError, m.add_component, 'ab.cd')
        self.assertRaises(myokit.InvalidNameError, m.add_component, 'ab!cd')
        self.assertRaises(myokit.InvalidNameError, m.add_component, '5*x')
        # Keywords
        self.assertRaises(myokit.InvalidNameError, m.add_component, 'and')
        self.assertRaises(myokit.InvalidNameError, m.add_component, 'bind')
        # Test adding variable to component
        c1 = m.add_component('c1')
        # Duplicate
        # Badly formed names
        self.assertRaises(myokit.InvalidNameError, c0.add_variable, '0')
        self.assertRaises(myokit.InvalidNameError, c0.add_variable, '_aap')
        self.assertRaises(myokit.InvalidNameError, c0.add_variable, '123abvc')
        self.assertRaises(myokit.InvalidNameError, c0.add_variable, 'ab cd')
        self.assertRaises(myokit.InvalidNameError, c0.add_variable, 'ab.cd')
        self.assertRaises(myokit.InvalidNameError, c0.add_variable, 'ab!cd')
        self.assertRaises(myokit.InvalidNameError, c0.add_variable, '5*x')
        # Keywords
        self.assertRaises(myokit.InvalidNameError, c0.add_variable, 'or')
        self.assertRaises(myokit.InvalidNameError, c0.add_variable, 'label')

        # Test adding variable to variable
        v1 = c0.add_variable('c0')
        # Duplicate
        v2 = c1.add_variable('c0')
        self.assertRaises(myokit.DuplicateName, c1.add_variable, 'c0')
        self.assertRaises(myokit.DuplicateName, v1.add_variable, 'c0')
        self.assertRaises(myokit.DuplicateName, v2.add_variable, 'c0')
        # Badly formed names
        self.assertRaises(myokit.InvalidNameError, v1.add_variable, '0')
        self.assertRaises(myokit.InvalidNameError, v1.add_variable, '_aap')
        self.assertRaises(myokit.InvalidNameError, v1.add_variable, '123abvc')
        self.assertRaises(myokit.InvalidNameError, v1.add_variable, 'ab cd')
        self.assertRaises(myokit.InvalidNameError, v1.add_variable, 'ab.cd')
        self.assertRaises(myokit.InvalidNameError, v1.add_variable, 'ab!cd')
        self.assertRaises(myokit.InvalidNameError, v1.add_variable, '5*x')
        # Keywords
        self.assertRaises(myokit.InvalidNameError, v1.add_variable, 'not')
        self.assertRaises(myokit.InvalidNameError, v1.add_variable, 'in')

    def test_unused_and_cycles(self):
        # Test unused variable and cycle detection.

        m = myokit.Model('LotkaVolterra')
        c0 = m.add_component('c0')
        t = c0.add_variable('time')
        t.set_rhs(myokit.Number(0))
        t.set_binding('time')
        c1 = m.add_component('c1')
        m.add_component('c2')
        c1_a = c1.add_variable('a')
        c1_b = c1.add_variable('b')
        c1_a.promote(1.0)
        c1_a.set_rhs(myokit.Multiply(myokit.Name(c1_a), myokit.Number(0.5)))
        c1_b.set_rhs(myokit.Multiply(myokit.Name(c1_a), myokit.Number(1.0)))
        # b is unused, test if found
        m.validate()
        w = m.warnings()
        self.assertEqual(len(w), 1)
        self.assertEqual(type(w[0]), myokit.UnusedVariableError)
        # b is used by c, c is unused, test if found
        c1_c = c1.add_variable('c')
        c1_c.set_rhs(myokit.Name(c1_b))
        m.validate()
        w = m.warnings()
        self.assertEqual(len(w), 2)
        self.assertEqual(type(w[0]), myokit.UnusedVariableError)
        self.assertEqual(type(w[1]), myokit.UnusedVariableError)
        # Test 1:1 cycle
        c1_b.set_rhs(myokit.Name(c1_b))
        self.assertRaises(myokit.CyclicalDependencyError, m.validate)
        # Test longer cycles
        c1_b.set_rhs(myokit.Multiply(myokit.Number(10), myokit.Name(c1_c)))
        self.assertRaises(myokit.CyclicalDependencyError, m.validate)
        # Reset
        c1_b.set_rhs(myokit.Multiply(myokit.Name(c1_a), myokit.Number(1.0)))
        m.validate()
        # Test cycle involving state variable
        c1_a.set_rhs(myokit.Name(c1_b))
        m.validate()
        c1_b.set_rhs(myokit.Multiply(myokit.Name(c1_a), myokit.Name(c1_b)))
        self.assertRaises(myokit.CyclicalDependencyError, m.validate)
        c1_b.set_rhs(myokit.Multiply(myokit.Name(c1_a), myokit.Name(c1_c)))
        c1_c.set_rhs(myokit.Multiply(myokit.Name(c1_a), myokit.Number(3)))
        m.validate()
        w = m.warnings()
        self.assertEqual(len(w), 0)
        c1_c.set_rhs(myokit.Multiply(myokit.Name(c1_a), myokit.Name(c1_b)))
        self.assertRaises(myokit.CyclicalDependencyError, m.validate)


if __name__ == '__main__':
    unittest.main()
