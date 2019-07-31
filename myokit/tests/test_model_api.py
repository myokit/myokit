#!/usr/bin/env python
#
# Tests the model API.
#
# Notes:
#  - Tests for dependency checking in models are in `test_dependency_checking`.
#
# This file is part of Myokit
#  Copyright 2011-2019 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import unittest
import numpy as np

import myokit

from shared import TemporaryDirectory

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
        """
        Test if an error is raised when a variable can't be resolved.
        """
        m = myokit.Model('Resolve')
        c = m.add_component('c')
        p = c.add_variable('p')
        q = c.add_variable('q')
        p.set_rhs('10 * q')
        self.assertRaises(myokit.ParseError, q.set_rhs, '10 * r')

    def test_scope(self):
        """
        Test if illegal references are detected.
        """
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
        """
        Test if invalid or duplicate names are detected.
        """
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
        """
        Test unused variable and cycle detection.
        """
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


class VarOwnerTest(unittest.TestCase):
    """
    Tests parts of :class:`myokit.VarOwner`.
    """
    def test_move_variable(self):
        """
        Test the method to move component variables to another component.
        """
        # Create a model
        m = myokit.Model('LotkaVolterra')
        X = m.add_component('X')
        a = X.add_variable('a')
        a.set_rhs(3)
        b = X.add_variable('b')
        b1 = b.add_variable('b1')
        b2 = b.add_variable('b2')
        b1.set_rhs(1)
        b2.set_rhs(
            myokit.Minus(
                myokit.Minus(myokit.Name(a), myokit.Name(b1)),
                myokit.Number(1)
            )
        )
        b.set_rhs(myokit.Plus(myokit.Name(b1), myokit.Name(b2)))
        x = X.add_variable('x')
        x.promote()
        Y = m.add_component('Y')
        c = Y.add_variable('c')
        c.set_rhs(myokit.Minus(myokit.Name(a), myokit.Number(1)))
        d = Y.add_variable('d')
        d.set_rhs(2)
        y = Y.add_variable('y')
        y.promote()
        x.set_rhs(myokit.Minus(
            myokit.Multiply(myokit.Name(a), myokit.Name(x)),
            myokit.Multiply(
                myokit.Multiply(myokit.Name(b), myokit.Name(x)),
                myokit.Name(y)
            )
        ))
        x.set_state_value(10)
        y.set_rhs(myokit.Plus(
            myokit.Multiply(
                myokit.PrefixMinus(myokit.Name(c)), myokit.Name(y)
            ),
            myokit.Multiply(
                myokit.Multiply(myokit.Name(d), myokit.Name(x)), myokit.Name(y)
            )
        ))
        y.set_state_value(5)
        Z = m.add_component('Z')
        t = Z.add_variable('total')
        t.set_rhs(myokit.Plus(myokit.Name(x), myokit.Name(y)))
        E = m.add_component('engine')
        time = E.add_variable('time')
        time.set_rhs(0)
        time.set_binding('time')

        # Move time variable into X
        m.validate()    # If not valid, this will raise an exception
        E.move_variable(time, Z)
        m.validate()

        # Can't do it a second time
        self.assertRaises(ValueError, E.move_variable, time, Z)

        # Move to self
        Z.move_variable(time, Z)
        m.validate()
        Z.move_variable(time, Z)
        m.validate()

        # Duplicate variable name
        E.add_variable('time')
        self.assertRaises(myokit.DuplicateName, Z.move_variable, time, E)

        # Create a nested variable by moving
        m = myokit.Model()
        c = m.add_component('c')
        v = c.add_variable('v')
        w = c.add_variable('w')
        self.assertFalse(w.is_nested())
        c.move_variable(w, v)
        self.assertTrue(w.is_nested())
        v.move_variable(w, c)
        self.assertFalse(w.is_nested())

        # State variables can't be made nested
        w.promote(0)
        self.assertRaisesRegex(
            Exception, 'State variables', c.move_variable, w, v)

    def test_remove_variable(self):
        """
        Test the removal of a variable.
        """
        # Create a model
        m = myokit.Model('LotkaVolterra')

        # Add a variable 'a'
        X = m.add_component('X')

        # Simplest case
        a = X.add_variable('a')
        self.assertEqual(X.count_variables(), 1)
        X.remove_variable(a)
        self.assertEqual(X.count_variables(), 0)
        self.assertRaises(Exception, X.remove_variable, a)

        # Test re-adding
        a = X.add_variable('a')
        a.set_rhs(myokit.Number(5))
        self.assertEqual(X.count_variables(), 1)

        # Test deleting dependent variables
        b = X.add_variable('b')
        self.assertEqual(X.count_variables(), 2)
        b.set_rhs(myokit.Plus(myokit.Number(3), myokit.Name(a)))

        # Test blocking of removal
        self.assertRaises(myokit.IntegrityError, X.remove_variable, a)
        self.assertEqual(X.count_variables(), 2)

        # Test removal in the right order
        X.remove_variable(b)
        self.assertEqual(X.count_variables(), 1)
        X.remove_variable(a)
        self.assertEqual(X.count_variables(), 0)

        # Test reference to current state variable values
        a = X.add_variable('a')
        a.set_rhs(myokit.Number(5))
        a.promote()
        b = X.add_variable('b')
        b.set_rhs(myokit.Plus(myokit.Number(3), myokit.Name(a)))
        self.assertRaises(myokit.IntegrityError, X.remove_variable, a)
        X.remove_variable(b)
        X.remove_variable(a)
        self.assertEqual(X.count_variables(), 0)

        # Test reference to current state variable values with "self"-ref
        a = X.add_variable('a')
        a.promote()
        a.set_rhs(myokit.Name(a))
        X.remove_variable(a)

        # Test it doesn't interfere with normal workings
        a = X.add_variable('a')
        a.promote()
        a.set_rhs(myokit.Name(a))
        b = X.add_variable('b')
        b.set_rhs(myokit.Name(a))
        self.assertRaises(myokit.IntegrityError, X.remove_variable, a)
        X.remove_variable(b)
        X.remove_variable(a)

        # Test reference to dot
        a = X.add_variable('a')
        a.set_rhs(myokit.Number(5))
        a.promote()
        b = X.add_variable('b')
        b.set_rhs(myokit.Derivative(myokit.Name(a)))
        self.assertRaises(myokit.IntegrityError, X.remove_variable, a)
        X.remove_variable(b)
        X.remove_variable(a)

        # Test if orphaned
        self.assertIsNone(b.parent())

        # Test deleting variable with nested variables
        a = X.add_variable('a')
        b = a.add_variable('b')
        b.set_rhs(myokit.Plus(myokit.Number(2), myokit.Number(2)))
        a.set_rhs(myokit.Multiply(myokit.Number(3), myokit.Name(b)))
        self.assertRaises(myokit.IntegrityError, X.remove_variable, a)
        self.assertEqual(a.count_variables(), 1)
        self.assertEqual(X.count_variables(), 1)

        # Test recursive deleting
        X.remove_variable(a, recursive=True)
        self.assertEqual(a.count_variables(), 0)
        self.assertEqual(X.count_variables(), 0)

        # Same with dot(a) = a, b = 3 * a
        a = X.add_variable('a')
        a.promote(0.123)
        b = a.add_variable('b')
        b.set_rhs(myokit.Multiply(myokit.Number(3), myokit.Name(a)))
        a.set_rhs(myokit.Name(b))
        self.assertRaises(myokit.IntegrityError, X.remove_variable, a)
        self.assertRaises(myokit.IntegrityError, a.remove_variable, b)
        self.assertRaises(myokit.IntegrityError, a.remove_variable, b, True)
        X.remove_variable(a, recursive=True)

        # Test if removed from model's label and binding lists
        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        y = c.add_variable('y')
        x.set_rhs(0)
        y.set_rhs(0)
        x.set_binding('time')
        y.set_label('membrane_potential')
        self.assertIs(m.binding('time'), x)
        self.assertIs(m.label('membrane_potential'), y)
        c.remove_variable(x)
        self.assertIs(m.binding('time'), None)
        self.assertIs(m.label('membrane_potential'), y)
        c.remove_variable(y)
        self.assertIs(m.binding('time'), None)
        self.assertIs(m.label('membrane_potential'), None)

    def test_varowner_get(self):
        """
        Test VarOwner.get().
        """
        # Test basics
        m = myokit.Model('test')
        c = m.add_component('c')
        x = c.add_variable('x')
        self.assertIs(m.get('c'), c)
        self.assertIs(m.get('c.x'), x)
        self.assertIs(c.get('x'), x)

        # Test asking for object
        self.assertIs(m.get(c), c)
        self.assertIs(m.get(x), x)
        self.assertIs(c.get(x), x)
        self.assertIs(x.get(c), c)

        # Test not founds
        self.assertRaises(KeyError, m.get, 'y')
        self.assertRaises(KeyError, m.get, 'c.y')
        self.assertRaises(KeyError, c.get, 'y')

        # Test class filter
        self.assertIs(m.get('c', myokit.Component), c)
        self.assertRaises(KeyError, m.get, 'c', myokit.Variable)
        self.assertIs(m.get('c.x', myokit.Variable), x)
        self.assertIs(c.get('x', myokit.Variable), x)
        self.assertRaises(KeyError, m.get, 'c.x', myokit.Component)
        self.assertRaises(KeyError, c.get, 'x', myokit.Component)

    def test_add_variable_allow_renaming(self):
        """
        Test the ``VarProvider.add_variable_allow_renaming`` method.
        """
        m = myokit.Model('test')
        c = m.add_component('c')
        x = c.add_variable('x')
        self.assertTrue(c.has_variable('x'))
        self.assertRaises(myokit.DuplicateName, c.add_variable, 'x')
        y = c.add_variable_allow_renaming('x')
        self.assertEqual(x.name(), 'x')
        self.assertEqual(y.name(), 'x_1')
        z = c.add_variable_allow_renaming('x')
        self.assertEqual(z.name(), 'x_2')

        # Test repeated calls
        r = c.add_variable('r')
        for i in range(10):
            r = c.add_variable_allow_renaming('r')
            self.assertEqual(r.name(), 'r_' + str(1 + i))


class ModelTest(unittest.TestCase):
    """
    Tests parts of :class:`myokit.Model`.
    """
    def test_remove_component(self):
        # Test the removal of a component.

        # Create model
        m = myokit.Model('LotkaVolterra')
        # Simplest case
        X = m.add_component('X')
        self.assertEqual(m.count_components(), 1)
        m.remove_component(X)
        self.assertEqual(m.count_components(), 0)
        self.assertRaises(KeyError, m.remove_component, X)

        # Test if orphaned
        self.assertIsNone(X.parent())

        # Re-adding
        self.assertEqual(m.count_components(), 0)
        X = m.add_component('X')
        self.assertEqual(m.count_components(), 1)

        # With internal variables and string name
        a = X.add_variable('a')
        a.set_rhs(myokit.Number(4))
        b = X.add_variable('b')
        b.set_rhs(myokit.Name(a))
        m.remove_component('X')
        self.assertEqual(m.count_components(), 0)

        # With dependencies from another component
        X = m.add_component('X')
        a = X.add_variable('a')
        a.set_rhs(myokit.Number(45))
        b = X.add_variable('b')
        b.set_rhs(myokit.Name(b))
        Y = m.add_component('Y')
        c = Y.add_variable('c')
        c.set_rhs(myokit.Name(a))
        d = Y.add_variable('d')
        d.set_rhs(myokit.Name(c))
        self.assertEqual(m.count_components(), 2)
        self.assertRaises(myokit.IntegrityError, m.remove_component, X)
        self.assertEqual(m.count_components(), 2)

        # In the right order...
        m.remove_component(Y)
        self.assertEqual(m.count_components(), 1)
        m.remove_component(X)
        self.assertEqual(m.count_components(), 0)

    def test_remove_with_alias(self):
        # Test cloning after an add / remove event.

        m = myokit.Model('AddRemoveClone')
        c = m.add_component('c')
        p = c.add_variable('p')
        p.set_binding('time')
        p.set_rhs(0)
        q = c.add_variable('q')
        q.set_rhs(12)
        m.validate()    # Raises error if not ok
        m.clone()       # Raises error if not ok
        d = m.add_component('d')
        d.add_alias('bert', p)
        e = d.add_variable('e')
        e.set_rhs('10 * bert')
        m.validate()
        m.clone()
        d.add_alias('ernie', q)
        m.validate()
        m.clone()
        c.remove_variable(q)
        m.validate()
        m.clone()   # Will raise error if alias isn't deleted

    def test_no_rhs_error(self):
        # Test an exception is raised when a variable is missing an rhs.

        m = myokit.Model('LotkaVolterra')
        c0 = m.add_component('c0')
        t = c0.add_variable('time')
        t.set_binding('time')
        self.assertRaises(myokit.MissingRhsError, m.validate)
        t.set_rhs(myokit.Number(0))
        m.validate()
        a = c0.add_variable('test')
        self.assertRaises(myokit.MissingRhsError, m.validate)
        a.set_rhs(myokit.Number(1))
        m.validate()
        b = c0.add_variable('derv')
        b.promote(10)
        self.assertRaises(myokit.MissingRhsError, m.validate)
        b.set_rhs(2)
        m.validate()

    def test_no_time_variable(self):
        # Test an exception is raised if nothing is bound to time.

        m = myokit.Model('LotkaVolterra')
        c0 = m.add_component('c0')
        t = c0.add_variable('time')
        t.set_rhs(myokit.Number(0))
        self.assertRaises(myokit.MissingTimeVariableError, m.validate)

    def test_add_component_allow_renamining(self):
        # Test the ``Model.add_component_allow_renaming`` method.

        m = myokit.Model('test')
        c = m.add_component('c')
        self.assertTrue(m.has_component('c'))
        self.assertRaises(myokit.DuplicateName, m.add_component, 'c')
        d = m.add_component_allow_renaming('c')
        self.assertEqual(c.name(), 'c')
        self.assertEqual(d.name(), 'c_1')
        e = m.add_component_allow_renaming('c')
        self.assertEqual(e.name(), 'c_2')

        # Test repeated calls
        r = m.add_component('r')
        for i in range(10):
            r = m.add_component_allow_renaming('r')
            self.assertEqual(r.name(), 'r_' + str(1 + i))

    def test_model_get(self):
        # Test Model.get().

        m = myokit.load_model('example')

        # Get by name
        v = m.get('membrane.V')
        self.assertEqual(v.qname(), 'membrane.V')
        self.assertIsInstance(v, myokit.Variable)

        # Get by variable ref (useful for handling unknown input type)
        w = m.get(v)
        self.assertIs(w, v)

        # Get nested
        a = m.get('ina.m.alpha')
        self.assertEqual(a.qname(), 'ina.m.alpha')
        self.assertIsInstance(a, myokit.Variable)

        # Get component
        c = m.get('membrane')
        self.assertEqual(c.qname(), 'membrane')
        self.assertIsInstance(c, myokit.Component)

        # Get with filter
        a = m.get('ina.m.alpha', myokit.Variable)
        self.assertEqual(a.qname(), 'ina.m.alpha')
        self.assertIsInstance(a, myokit.Variable)
        self.assertRaises(KeyError, m.get, 'ina.m.alpha', myokit.Component)
        self.assertRaises(KeyError, m.get, 'ina', myokit.Variable)
        m.get('ina', myokit.Component)

        # Get non-existent
        self.assertRaises(KeyError, m.get, 'membrane.bert')
        self.assertRaises(KeyError, m.get, 'bert.bert')

    def test_add_function(self):
        # Test the ``Model.add_function`` method.

        m = myokit.Model('m')
        c = m.add_component('c')
        x = c.add_variable('x')

        # Test basics
        m.add_function('f', ('a', 'b', 'c'), 'a + b + c')
        x.set_rhs('f(1, 2, 3)')
        self.assertEqual(x.eval(), 6)

        # Test duplicate name
        # Different number of arguments is allowed:
        m.add_function('f', ('a', 'b'), 'a + b')
        self.assertRaisesRegex(
            myokit.DuplicateFunctionName, 'already defined', m.add_function,
            'f', ('a', 'b'), 'a - b')

        # Test duplicate argument name
        self.assertRaisesRegex(
            myokit.DuplicateFunctionArgument, 'already in use',
            m.add_function, 'g', ('a', 'a'), 'a + a')

        # Dot operator is not allowed
        self.assertRaisesRegex(
            myokit.InvalidFunction, 'dot\(\) operator',
            m.add_function, 'fdot', ('a', ), 'dot(a)')

        # Unused argument
        self.assertRaisesRegex(
            myokit.InvalidFunction, 'never used', m.add_function, 'fun',
            ('a', 'b'), 'a')

        # Unspecified variable
        self.assertRaisesRegex(
            myokit.InvalidFunction, 'never declared',
            m.add_function, 'fun', ('a', ), 'a + b')

    def test_reorder_state(self):
        # Test :meth:`Model.reorder_state()`.

        m = myokit.Model()
        c = m.add_component('c')
        t = c.add_variable('time')
        t.set_binding('time')
        t.set_rhs(0)
        v = c.add_variable('v')
        v.set_rhs('3 - v')
        v.promote(0)
        w = c.add_variable('w')
        w.set_rhs(1)
        w.promote(0)
        self.assertEqual(list(m.states()), [v, w])
        m.reorder_state([w, v])
        self.assertEqual(list(m.states()), [w, v])
        m.reorder_state([w, v])
        self.assertEqual(list(m.states()), [w, v])
        m.reorder_state([v, w])
        self.assertEqual(list(m.states()), [v, w])

        # Wrong number of states
        self.assertRaisesRegex(
            ValueError, 'number of entries', m.reorder_state, [v])
        self.assertRaisesRegex(
            ValueError, 'number of entries', m.reorder_state, [v, w, v])

        # Duplicate entries
        self.assertRaisesRegex(
            ValueError, 'Duplicate', m.reorder_state, [v, v])

        # Not a state
        self.assertRaisesRegex(
            ValueError, 'must all be', m.reorder_state, [v, t])

    def test_name(self):
        # Test :meth:`Model.set_name(name)`.

        m = myokit.Model()
        self.assertIsNone(m.name())
        m.set_name('ernie')
        self.assertEqual(m.name(), 'ernie')
        m.set_name(None)
        self.assertIsNone(m.name())
        m.set_name(None)
        self.assertIsNone(m.name())

        m = myokit.Model(name='ernie')
        self.assertEqual(m.name(), 'ernie')
        m.set_name(None)
        self.assertIsNone(m.name())
        m.set_name('bert')
        self.assertEqual(m.name(), 'bert')

    def test_check_units(self):
        # Test the ``model.check_units`` method.

        model = myokit.Model('m')
        component = model.add_component('c')
        t = component.add_variable('time')
        t.set_binding('time')

        # Check units before any rhs or units set
        s = myokit.UNIT_STRICT
        self.assertRaisesRegex(
            myokit.IntegrityError, 'No RHS set', model.check_units)
        self.assertRaisesRegex(
            myokit.IntegrityError, 'No RHS set', model.check_units, s)

        # Check units before any rhs set
        t.set_unit('s')
        self.assertRaisesRegex(
            myokit.IntegrityError, 'No RHS set', model.check_units)
        self.assertRaisesRegex(
            myokit.IntegrityError, 'No RHS set', model.check_units, s)

        # Check mini model with rhs and units, no states
        t.set_rhs('0 [s]')
        a = component.add_variable('a')
        a.set_rhs(1)
        model.check_units()
        model.check_units(s)

        # Check mini model with a state
        # Strict check should fail: a's RHS should be in 1/s
        a.promote(0)
        model.check_units()
        self.assertRaises(myokit.IncompatibleUnitError, model.check_units, s)
        a.set_rhs('1 [1/s]')
        model.check_units(s)

        b = component.add_variable('b')
        b.set_rhs(2)
        c = component.add_variable('c')
        c.set_rhs('2 * b')
        model.check_units()
        model.check_units(s)

        a.set_rhs('1 [N/s]')
        b.set_rhs('2 [m]')
        c.set_rhs('a * b')

        # No variable units set
        model.check_units()
        self.assertRaises(myokit.IncompatibleUnitError, model.check_units, s)

        # Variable unit set for state
        a.set_unit('N')     # So rhs should be N/s
        b.set_unit('m')
        model.check_units()
        self.assertRaises(myokit.IncompatibleUnitError, model.check_units, s)

        # Bad derived unit
        c.set_unit('A')
        self.assertRaises(myokit.IncompatibleUnitError, model.check_units)
        self.assertRaises(myokit.IncompatibleUnitError, model.check_units, s)

        c.set_unit(myokit.parse_unit('N*m'))
        model.check_units()
        model.check_units(s)

        # References use variable unit, not RHS unit!
        model = myokit.Model('m')
        component = model.add_component('c')
        x = component.add_variable('x')
        y = component.add_variable('y')
        x.set_unit(None)
        y.set_unit(None)
        x.set_rhs('5 [mV]')
        y.set_rhs('3 [A] + x')  # x unit is unspecified, not mV!
        model.check_units()
        self.assertRaises(myokit.IncompatibleUnitError, model.check_units, s)

    def test_code(self):
        # Test :meth:`Model.code()`.
        model = myokit.Model('m')
        component = model.add_component('comp1')
        a = component.add_variable('a')
        b = component.add_variable('b')
        c = component.add_variable('c')
        a.set_rhs('1 [N]')
        a.set_label('aaa')
        b.set_rhs('2 [m]')
        b.set_binding('bbb')
        c.set_rhs('a * b')
        c.set_unit('N*m')
        component2 = model.add_component('comp2')
        d = component2.add_variable('d')
        d.set_rhs(myokit.Name(a))

        self.assertEqual(
            model.code(),
            '[[model]]\n'
            'name: m\n'
            '\n'
            '[comp1]\n'
            'a = 1 [N] label aaa\n'
            'b = 2 [m] bind bbb\n'
            'c = a * b\n'
            '    in [J]\n'
            '\n'
            '[comp2]\n'
            'd = comp1.a\n'
            '\n'
        )

        a.set_rhs('1 + 2 + 3 + 4 + 5 + 6 + 7 + 8 + 9 + 10 + 11')
        b.set_rhs('2 + 3 + 4 + 5 + 6 + 7 + 8 + 9 + 10 + 11 + 12')

        self.assertEqual(
            model.code(line_numbers=True),
            ' 1 [[model]]\n'
            ' 2 name: m\n'
            ' 3 \n'
            ' 4 [comp1]\n'
            ' 5 a = 1 + 2 + 3 + 4 + 5 + 6 + 7 + 8 + 9 + 10 + 11\n'
            ' 6     label aaa\n'
            ' 7 b = 2 + 3 + 4 + 5 + 6 + 7 + 8 + 9 + 10 + 11 + 12\n'
            ' 8     bind bbb\n'
            ' 9 c = a * b\n'
            '10     in [J]\n'
            '11 \n'
            '12 [comp2]\n'
            '13 d = comp1.a\n'
        )

    def test_model_eval_state_derivatives(self):
        # Test Model.eval_state_derivatives().
        model = myokit.Model('m')
        component = model.add_component('comp1')
        t = component.add_variable('time')
        t.set_binding('time')
        t.set_rhs(1)
        a = component.add_variable('a')
        b = component.add_variable('b')
        c = component.add_variable('c')
        a.promote(1)
        a.set_rhs('1')
        b.promote(2)
        b.set_rhs('2 * b')
        c.promote(3)
        c.set_rhs('b + c')
        model.validate()
        self.assertEqual(model.eval_state_derivatives(), [1, 4, 5])
        self.assertEqual(
            model.eval_state_derivatives(state=[1, 1, 2]), [1, 2, 3])
        c.set_rhs('b + c + time')
        self.assertEqual(model.eval_state_derivatives(), [1, 4, 6])
        self.assertEqual(
            model.eval_state_derivatives(state=[1, 1, 2], inputs={'time': 0}),
            [1, 2, 3])

        # Errors
        c.set_rhs('(b + c) / 0')
        self.assertRaises(myokit.NumericalError, model.eval_state_derivatives)
        nan = model.eval_state_derivatives(ignore_errors=True)[2]
        self.assertNotEqual(nan, nan)   # x != x is a nan test...

    def test_expressions_for(self):
        # Test Model.expressions_for().
        m = myokit.load_model('example')

        # Simple test
        eqs, vrs = m.expressions_for('ina.m')
        self.assertEqual(len(eqs), 3)
        self.assertEqual(len(vrs), 2)
        self.assertIn(myokit.Name(m.get('ina.m')), vrs)
        self.assertIn(myokit.Name(m.get('membrane.V')), vrs)

        # Massive test
        eqs, vrs = m.expressions_for('membrane.V')
        self.assertEqual(len(eqs), 37)

        # Bad system
        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        y = c.add_variable('y')
        x.set_rhs('y')
        y.set_rhs('x')
        self.assertRaisesRegex(
            Exception, 'Failed to solve', m.expressions_for, 'c.x')

    def test_format_state(self):
        # Test Model.format_state()
        m = myokit.load_model('example')

        # Test without state argument
        self.assertEqual(
            m.format_state(),
            'membrane.V = -84.5286\n'
            'ina.m      = 0.0017\n'
            'ina.h      = 0.9832\n'
            'ina.j      = 0.995484\n'
            'ica.d      = 3e-06\n'
            'ica.f      = 1.0\n'
            'ik.x       = 0.0057\n'
            'ica.Ca_i   = 0.0002'
        )

        # Test with state argument
        self.assertEqual(
            m.format_state([1, 2, 3, 4, 5, 6, 7, 8]),
            'membrane.V = 1\n'
            'ina.m      = 2\n'
            'ina.h      = 3\n'
            'ina.j      = 4\n'
            'ica.d      = 5\n'
            'ica.f      = 6\n'
            'ik.x       = 7\n'
            'ica.Ca_i   = 8'
        )

        # Test with invalid state argument
        self.assertRaisesRegex(
            ValueError, 'list of \(8\)', m.format_state, [1, 2, 3])

        # Test with second state argument
        self.assertEqual(
            m.format_state([1, 2, 3, 4, 5, 6, 7, 8], [8, 7, 6, 5, 4, 3, 2, 1]),
            'membrane.V = 1    8\n'
            'ina.m      = 2    7\n'
            'ina.h      = 3    6\n'
            'ina.j      = 4    5\n'
            'ica.d      = 5    4\n'
            'ica.f      = 6    3\n'
            'ik.x       = 7    2\n'
            'ica.Ca_i   = 8    1'
        )

        # Test with invalid second state argument
        self.assertRaisesRegex(
            ValueError, 'list of \(8\)', m.format_state,
            [1, 2, 3, 4, 5, 6, 7, 8], [1, 2, 3])

    def test_format_state_derivatives(self):
        # Test Model.format_state_derivatives().

        m = myokit.load_model('example')

        # Test without arguments
        self.assertEqual(
            m.format_state_derivatives(), # noqa
'membrane.V = -84.5286                   dot = -5.68008003798848027e-02\n'
'ina.m      = 0.0017                     dot = -4.94961486033834719e-03\n'
'ina.h      = 0.9832                     dot =  9.02025299127830887e-06\n'
'ina.j      = 0.995484                   dot = -3.70409866928434243e-04\n'
'ica.d      = 3e-06                      dot =  3.68067721821794798e-04\n'
'ica.f      = 1.0                        dot = -3.55010150519739432e-07\n'
'ik.x       = 0.0057                     dot = -2.04613933160084307e-07\n'
'ica.Ca_i   = 0.0002                     dot = -6.99430692442154227e-06'
        )

        # Test with state argument
        self.assertEqual(
            m.format_state_derivatives([1, 2, 3, 4, 5, 6, 7, 8]), # noqa
'membrane.V = 1                          dot = -5.68008003798848027e-02\n'
'ina.m      = 2                          dot = -4.94961486033834719e-03\n'
'ina.h      = 3                          dot =  9.02025299127830887e-06\n'
'ina.j      = 4                          dot = -3.70409866928434243e-04\n'
'ica.d      = 5                          dot =  3.68067721821794798e-04\n'
'ica.f      = 6                          dot = -3.55010150519739432e-07\n'
'ik.x       = 7                          dot = -2.04613933160084307e-07\n'
'ica.Ca_i   = 8                          dot = -6.99430692442154227e-06'
        )

        # Test with invalid state argument
        self.assertRaisesRegex(
            ValueError, 'list of \(8\)', m.format_state_derivatives, [1, 2, 3])

        # Test with derivs argument
        self.assertEqual(
            m.format_state_derivatives(
                [1, 2, 3, 4, 5, 6, 7, 8], [8, 7, 6, 5, 4, 3, 2, 1]),
            'membrane.V = 1                          dot = 8\n'
            'ina.m      = 2                          dot = 7\n'
            'ina.h      = 3                          dot = 6\n'
            'ina.j      = 4                          dot = 5\n'
            'ica.d      = 5                          dot = 4\n'
            'ica.f      = 6                          dot = 3\n'
            'ik.x       = 7                          dot = 2\n'
            'ica.Ca_i   = 8                          dot = 1'
        )

        # Test with invalid derivs argument
        self.assertRaisesRegex(
            ValueError, 'list of \(8\)', m.format_state_derivatives,
            [1, 2, 3, 4, 5, 6, 7, 8], [1, 2, 3])

    def test_unique_names_1(self):
        # Test Model.create_unique_names().

        # Heavily disputed variable names
        m = myokit.Model()
        a = m.add_component('a')
        ax = a.add_variable('x')
        b = m.add_component('b')
        bx = b.add_variable('x')
        x = m.add_component('x')
        xx = x.add_variable('x')
        m.create_unique_names()
        self.assertEqual(a.uname(), 'a')
        self.assertEqual(ax.uname(), 'a_x')
        self.assertEqual(b.uname(), 'b')
        self.assertEqual(bx.uname(), 'b_x')
        self.assertEqual(x.uname(), 'x_1')
        self.assertEqual(xx.uname(), 'x_x')

        # Disputed variable name --> Generated name already exists
        m = myokit.Model()
        a = m.add_component('a')
        ax = a.add_variable('x')
        abx = a.add_variable('b_x')
        aax = a.add_variable('a_x')
        ax11 = a.add_variable('x_1_1')
        b = m.add_component('b')
        bx = b.add_variable('x')
        bx11 = b.add_variable('x_1_1')
        m.create_unique_names()
        self.assertEqual(a.uname(), 'a')
        self.assertEqual(ax.uname(), 'a_x_1')
        self.assertEqual(abx.uname(), 'b_x')
        self.assertEqual(aax.uname(), 'a_x')
        self.assertEqual(ax11.uname(), 'a_x_1_1')
        self.assertEqual(b.uname(), 'b')
        self.assertEqual(bx.uname(), 'b_x_1')
        self.assertEqual(bx11.uname(), 'b_x_1_1')

        # Disputed component name
        m = myokit.Model()
        a = m.add_component('a')
        a.add_variable('x')
        m.add_component('x')
        m.create_unique_names()
        self.assertEqual(m.get('a').uname(), 'a')
        self.assertEqual(m.get('a.x').uname(), 'a_x')
        self.assertEqual(m.get('x').uname(), 'x_1')

        # Disputed component name --> Generated name already exists
        m = myokit.Model()
        a = m.add_component('a')
        a.add_variable('x')
        m.add_component('x')
        m.add_component('x_1')
        m.create_unique_names()
        self.assertEqual(m.get('a').uname(), 'a')
        self.assertEqual(m.get('a.x').uname(), 'a_x')
        self.assertEqual(m.get('x').uname(), 'x_2')
        self.assertEqual(m.get('x_1').uname(), 'x_1')

    def test_unique_names_2(self):
        # Test reserving of unique name prefixes

        m = myokit.Model()
        a = m.add_component('paddington')
        x = a.add_variable('v_x')
        y = a.add_variable('bear')
        b = m.add_component('yogi')
        z = b.add_variable('bear')

        m.create_unique_names()
        self.assertEqual(x.uname(), 'v_x')
        self.assertEqual(y.uname(), 'paddington_bear')
        self.assertEqual(z.uname(), 'yogi_bear')

        # Don't allow v_ prefix
        m.reserve_unique_name_prefix('v_', 'var_')
        m.create_unique_names()
        self.assertEqual(x.uname(), 'var_v_x')
        self.assertEqual(y.uname(), 'paddington_bear')
        self.assertEqual(z.uname(), 'yogi_bear')

        # Don't allow pad prefix
        m.reserve_unique_name_prefix('pad', 'marmelade_')
        m.create_unique_names()
        self.assertEqual(x.uname(), 'var_v_x')
        self.assertEqual(y.uname(), 'marmelade_paddington_bear')
        self.assertEqual(z.uname(), 'yogi_bear')
        self.assertEqual(a.uname(), 'marmelade_paddington')

        # Test bad calls
        self.assertRaisesRegex(
            ValueError, 'prefix cannot be empty',
            m.reserve_unique_name_prefix, '', 'x')
        self.assertRaisesRegex(
            ValueError, 'prepend cannot be empty',
            m.reserve_unique_name_prefix, 'x', '')
        self.assertRaisesRegex(
            ValueError, 'prepend cannot start with prefix',
            m.reserve_unique_name_prefix, 'x', 'x')

    def test_warnings(self):
        # Test Model.has_warnings(), model.warnings() and
        # Model.format_warnings().

        # Test model without warnings
        m = myokit.Model()
        c = m.add_component('c')
        t = c.add_variable('time')
        t.set_binding('time')
        t.set_rhs(0)
        v = c.add_variable('v')
        v.set_rhs('3 - v')
        v.promote(0.1)
        m.validate()

        self.assertFalse(m.has_warnings())
        self.assertIn('0 validation warning', m.format_warnings())
        self.assertEqual(m.warnings(), [])

        # Test model with warnings
        v.validate()
        v.demote()
        v.validate()
        v.set_rhs(3)
        m.validate()

        self.assertTrue(m.has_warnings())
        self.assertIn('1 validation warning', m.format_warnings())
        self.assertIn('Unused variable', str(m.warnings()[0]))

    def test_bindings(self):
        # Test setting bindings and :meth:`Model.bindings()`.

        # Test set_binding() and bindings()
        m = myokit.Model()
        c = m.add_component('c')
        t = c.add_variable('time')
        t.set_binding('time')
        t.set_rhs(0)
        v = c.add_variable('v')
        v.set_rhs('3 - v')
        w = c.add_variable('w')
        w.set_rhs(0)
        bindings = list(m.bindings())
        self.assertEqual(len(bindings), 1)
        self.assertEqual(bindings[0][0], 'time')
        self.assertEqual(bindings[0][1], t)

        # Can't have two labels
        self.assertRaisesRegex(
            myokit.InvalidBindingError, 'already bound to', t.set_binding,
            'bert')

        # No two variables can have the same label
        self.assertRaisesRegex(
            myokit.InvalidBindingError, 'Duplicate binding', v.set_binding,
            'time')

        # Binding can't overlap with label
        v.set_label('membrane_potential')
        self.assertRaisesRegex(
            myokit.InvalidBindingError, 'in use as a label', w.set_binding,
            'membrane_potential')

        # State variables can't be bound
        v.promote(0)
        self.assertRaisesRegex(
            myokit.InvalidBindingError, 'State variables', v.set_binding, 'x')

    def test_labels(self):
        # Test setting labels and :meth:`Model.labels()`.

        # Test set_label() and labels()
        m = myokit.Model()
        c = m.add_component('c')
        t = c.add_variable('time')
        t.set_binding('time')
        t.set_rhs(0)
        v = c.add_variable('v')
        v.set_rhs('3 - v')
        v.set_label('membrane_potential')
        w = c.add_variable('w')
        w.set_rhs(1)
        x = c.add_variable('x')
        x.set_rhs(1)
        labels = list(m.labels())
        self.assertEqual(len(labels), 1)
        self.assertEqual(labels[0][0], 'membrane_potential')
        self.assertEqual(labels[0][1], v)

        # Can't have two labels
        self.assertRaisesRegex(
            myokit.InvalidLabelError, 'already has a label', v.set_label,
            'bert')

        # No two variables can have the same label
        self.assertRaisesRegex(
            myokit.InvalidLabelError, 'already in use', w.set_label,
            'membrane_potential')

        # Labels can't overlap with bindings
        self.assertRaisesRegex(
            myokit.InvalidLabelError, 'in use as a binding', w.set_label,
            'time')

    def test_load_save_state(self):
        # Test :meth:`Model.save_state()` and :meth:`Model.load_state()`.

        m = myokit.load_model('example')
        s1 = m.state()
        with TemporaryDirectory() as d:
            path = d.path('state.csv')
            m.save_state(path)
            self.assertEqual(m.state(), s1)
            sx = list(s1)
            sx[0] = 10
            m.set_state(sx)
            self.assertNotEqual(m.state(), s1)
            m.load_state(path)
            self.assertEqual(m.state(), s1)

    def test_map_to_state(self):
        # Test :meth:`Model.map_to_state()`.

        # Create test model
        m = myokit.Model()
        c = m.add_component('c')
        t = c.add_variable('time')
        t.set_binding('time')
        t.set_rhs(0)
        v = c.add_variable('v')
        v.set_rhs('3 - v')
        v.promote(0)
        w = c.add_variable('w')
        w.set_rhs('1 - w')
        w.promote(0)

        # List of numbers
        x = m.map_to_state([1, 2])
        self.assertEqual(x, [1.0, 2.0])

        # Wrong size list
        self.assertRaisesRegex(
            ValueError, 'Wrong number', m.map_to_state, [1, 2, 3])

        # String not tested, handled by parse_state.

        # Dict of names
        x = m.map_to_state({'c.v': 2, 'c.w': 3})
        self.assertEqual(x, [2.0, 3.0])

        # Dict of Variables
        x = m.map_to_state({v: 2, 'c.w': 3})
        self.assertEqual(x, [2.0, 3.0])

        # Missing state
        self.assertRaisesRegex(
            ValueError, 'Missing state', m.map_to_state, {v: 2})

    def test_resolve_interdependent_components(self):
        # Test :meth:`Model.resolve_interdependent_components()`.

        # Create test model
        m = myokit.Model()
        c1 = m.add_component('c1')
        t = c1.add_variable('time')
        t.set_binding('time')
        t.set_rhs(0)
        c2 = m.add_component('c2')
        v = c2.add_variable('v')
        c3 = m.add_component('c3')
        w = c3.add_variable('w')
        x = c3.add_variable('x')
        v.set_rhs(3)
        w.set_rhs(2)
        x.set_rhs(1)

        # Test merge not required
        self.assertEqual(m.has_interdependent_components(), False)

        # Test merge doesn't change model
        self.assertEqual(m.count_components(), 3)
        m.resolve_interdependent_components()
        self.assertEqual(m.count_components(), 3)

        # Test deprecated name
        m.merge_interdependent_components()
        self.assertEqual(m.count_components(), 3)

        # Create interdependent components
        v.set_rhs('3 - c3.x')
        w.set_rhs('1 - c2.v')

        # Test merge is required
        self.assertTrue(m.has_interdependent_components())

        # Merge
        self.assertEqual(m.count_components(), 3)
        m.resolve_interdependent_components()
        self.assertEqual(m.count_components(), 4)
        m.get('remaining')

        # Test name clash detection
        m = myokit.Model()
        c1 = m.add_component('remaining')
        t = c1.add_variable('time')
        t.set_binding('time')
        t.set_rhs(0)
        c2 = m.add_component('remaining_1')
        v = c2.add_variable('v')
        c3 = m.add_component('c3')
        w = c3.add_variable('w')
        x = c3.add_variable('x')
        v.set_rhs('3 - c3.x')
        w.set_rhs('1 - remaining_1.v')
        x.set_rhs('12')

        self.assertEqual(m.count_components(), 3)
        m.resolve_interdependent_components()
        self.assertEqual(m.count_components(), 4)
        m.get('remaining_2')

    def test_show_evaluation_of(self):
        # Test :meth:`Model.show_evaluation_of(variable)`.
        # Depends mostly on `references()`, and `code()` methods.

        m = myokit.load_model('example')

        # Test for literal
        e = m.show_evaluation_of('cell.Na_o')
        self.assertIn('cell.Na_o = ', e)
        self.assertIn('Literal constant', e)
        self.assertEqual(len(e.splitlines()), 4)

        # Test for calculated constant
        e = m.show_evaluation_of('ina.ENa')
        self.assertIn('ina.ENa = ', e)
        self.assertIn('Calculated constant', e)
        self.assertEqual(len(e.splitlines()), 10)

        # Test for intermediary variable
        e = m.show_evaluation_of('ina.INa')
        self.assertIn('ina.INa = ', e)
        self.assertIn('Intermediary variable', e)
        self.assertEqual(len(e.splitlines()), 13)

        # Test for state variable (with nested variables)
        e = m.show_evaluation_of('ina.m')
        self.assertIn('ina.m = ', e)
        self.assertIn('State variable', e)
        self.assertEqual(len(e.splitlines()), 15)

        # Test with guessing of similar
        e = m.show_evaluation_of('ina.Na_o')
        self.assertIn('not found', e)
        self.assertIn('cell.Na_o = ', e)
        self.assertIn('Literal constant', e)
        self.assertEqual(len(e.splitlines()), 5)

        # Test with nothing similar
        m = myokit.Model()
        self.assertRaises(Exception, m.show_evaluation_of, 'Hello')

    def test_show_expressions_for(self):
        # Test :meth:`Model.show_expressions_for(variable)`.

        m = myokit.load_model('example')
        e = m.show_expressions_for(m.get('ina.INa'))
        self.assertIn('ina.INa is a function of', e)
        self.assertEqual(len(e.splitlines()), 20)

    def test_show_line_of(self):
        # Test :meth:`Model.show_line_of(variable)`.

        m = myokit.load_model('example')
        e = m.show_line_of(m.get('ina.INa'))
        self.assertIn('Defined on line 86', e)
        self.assertIn('Intermediary variable', e)
        self.assertEqual(len(e.splitlines()), 3)

        # Test deprecated alias
        m.show_line(m.get('ina.INa'))

    def test_suggest(self):
        # Test :meth:`Model.suggest(variable_name)`.

        m = myokit.Model()
        c1 = m.add_component('c1')
        t = c1.add_variable('time')
        t.set_binding('time')
        t.set_rhs(0)
        c2 = m.add_component('c2')
        v = c2.add_variable('v')
        v.set_rhs('3')

        # Test with correct name
        found, suggested, msg = m.suggest_variable('c1.time')
        self.assertEqual(found, t)
        self.assertIsNone(suggested)
        self.assertIsNone(msg)

        # Test with wrong name
        found, suggested, msg = m.suggest_variable('c1.tim')
        self.assertIsNone(found)
        self.assertEqual(suggested, t)
        self.assertIn('Unknown', msg)

        # Test with case mismatch
        found, suggested, msg = m.suggest_variable('c1.timE')
        self.assertIsNone(found)
        self.assertEqual(suggested, t)
        self.assertIn('Case mismatch', msg)

        # Test without component
        found, suggested, msg = m.suggest_variable('time')
        self.assertIsNone(found)
        self.assertEqual(suggested, t)
        self.assertIn('No component', msg)

    def test_validate_and_remove_unused_variables(self):
        # Test :class:`Model.validate` with ``remove_unused_variables=True``.

        m = myokit.Model()
        c = m.add_component('c')
        t = c.add_variable('time')
        t.set_binding('time')
        t.set_rhs(0)
        x = c.add_variable('x')
        y = c.add_variable('y')
        z = c.add_variable('z')
        z1 = z.add_variable('z1')
        x.set_rhs('(10 - x) / y')
        x.promote(0)
        y.set_rhs(1)
        z.set_rhs('2 + z1')
        z1.set_rhs(3)

        # Two unused variables: z and z1
        m.validate()
        self.assertEqual(len(m.warnings()), 2)

        # Remove unused variables
        m.validate(remove_unused_variables=True)
        self.assertEqual(len(m.warnings()), 2)  # 2 removal warnings
        m.validate()
        self.assertEqual(len(m.warnings()), 0)  # issue fixed!

    def test_value(self):
        # Test :meth:`Model.value()`.

        m = myokit.Model()
        c = m.add_component('c')
        t = c.add_variable('t')
        t.set_binding('time')
        t.set_rhs(1000)
        self.assertEqual(m.value('c.t'), 1000)

    def test_item_at_text_position(self):
        # Test :meth:`Model.item_at_text_position()`.

        text = [
            '[[model]]',        # 1
            'c.x = 0',          # 2
            '',                 # 3
            '[e]',              # 4
            't = 0 bind time',
            '',
            '[c]',
            'desc: This is a test component',
            'dot(x) = (10 - x) / y',
            'y = 5 + y1',
            '    y1 = 3',
            ''
        ]
        model = myokit.parse_model(text)
        e = model.get('e')
        t = model.get('e.t')
        c = model.get('c')
        x = model.get('c.x')
        y = model.get('c.y')
        y1 = model.get('c.y.y1')

        def check(line, char, var):
            tv = model.item_at_text_position(line, char)
            if var is None:
                self.assertIsNone(tv)
            else:
                token, var2 = tv
                self.assertIsNotNone(var2)
                self.assertEqual(var.qname(), var2.qname())

        # It doesn't work on initial conditions
        check(1, 0, None)
        check(1, 1, None)
        check(1, 2, None)

        # Find the component e and its variable
        check(4, 0, None)
        check(4, 1, e)
        check(4, 2, None)
        check(5, 0, t)
        check(5, 1, None)

        # Find the component c and its variables
        check(7, 1, c)
        check(9, 4, x)
        check(10, 0, y)
        check(11, 4, y1)


class ComponentTest(unittest.TestCase):
    """
    Tests parts of :class:`myokit.Component`.
    """
    def test_alias_methods(self):
        """ Test various methods to do with aliases. """

        # Proper use of add_alias
        m = myokit.Model()
        c1 = m.add_component('c1')
        a = c1.add_variable('a')
        a.set_rhs(2)
        c2 = m.add_component('c2')
        c2.add_alias('bert', a)
        b = c2.add_variable('b')
        b.set_rhs('3 * bert')
        self.assertEqual(b.eval(), 6)

        # Test alias() and alias_for(), remove_alias()
        self.assertTrue(c2.has_alias('bert'))
        self.assertTrue(c2.has_alias_for(a))
        self.assertEqual(c2.alias('bert'), a)
        self.assertEqual(c2.alias_for(a), 'bert')
        c2.remove_alias('bert')
        self.assertFalse(c2.has_alias('bert'))
        self.assertFalse(c2.has_alias_for(a))
        self.assertRaises(KeyError, c2.alias, 'bert')
        self.assertRaises(KeyError, c2.alias_for, a)
        c2.add_alias('bert', a)
        c2.add_alias('ernie', a)
        c2.add_alias('hello', a)
        self.assertTrue(c2.has_alias_for(a))
        c2.remove_alias('bert')
        self.assertTrue(c2.has_alias_for(a))
        c2.remove_aliases_for(a)
        self.assertFalse(c2.has_alias_for(a))

    def test_add_alias_errors(self):
        """ Test error handling in :meth:`Component.add_alias()`. """
        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        d = m.add_component('d')
        y = d.add_variable('y')
        z = y.add_variable('z')

        # Duplicate name
        d.add_alias('great_name', x)
        self.assertRaises(myokit.DuplicateName, d.add_alias, 'y', x)

        # Alias for a nested variable
        c.add_alias('not_a_problem', y)
        self.assertRaisesRegex(
            myokit.IllegalAliasError, 'whose parent', c.add_alias, 'xyz', z)

        # Alias for a variable in the same component
        self.assertRaisesRegex(
            myokit.IllegalAliasError, 'same component', c.add_alias, 'zz', x)

        # Alias for a component
        self.assertRaisesRegex(
            myokit.IllegalAliasError, 'for variables', c.add_alias, 'zz', c)


class VariableTest(unittest.TestCase):
    """
    Tests parts of :class:`myokit.Variable`.
    """
    def test_unit(self):
        """ Test :meth:`Variable.unit()`. """
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

    def test_promote_demote(self):
        """
        Test variable promotion and demotion.
        """
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

    def test_labelling(self):
        """
        Test variable labelling.
        """
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

    def test_is_referenced(self):
        """ Test :meth:`Variable.is_referenced(). """
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

    def test_refs_by_and_to(self):
        """ Test :meth:`Variable.is_referenced(). """
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

    def test_pyfunc(self):
        """ Test :meth:`Variable.pyfunc(). """
        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        x.set_rhs(3)
        y = c.add_variable('y')
        y.set_rhs(4)
        z = c.add_variable('z')
        z.set_rhs('3 * x + y')

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

    def test_rename(self):
        """ Test :meth:`Variable.rename(). """
        # The functional part of this is done by Component.move_variable, so no
        # extensive testing is required
        m = myokit.Model()
        c = m.add_component('c')
        v = c.add_variable('v')
        v.rename('w')
        self.assertEqual(v.name(), 'w')
        self.assertEqual(v.qname(), 'c.w')

    def test_set_state_value(self):
        """ Test :meth:`Variable.set_state_value()`. """
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
        """ Test :meth:`Variable.set_unit()`. """
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

    def test_validate(self):
        """ Test some edge cases for validation. """

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

    def test_value(self):
        """ Test :meth:`Variable.value()`. """
        m = myokit.Model()
        c = m.add_component('c')
        v = c.add_variable('v')
        v.set_rhs('1 + 2 + 3 + 4')
        self.assertEqual(v.value(), 10)


class UserFunctionTest(unittest.TestCase):
    """
    Tests :class:`UserFunction`.
    """
    def test_user_function(self):
        """ Test :class:`UserFunction` creation and methods. """

        # Create without arguments
        f = myokit.UserFunction('bert', [], myokit.Number(12))
        args = list(f.arguments())
        self.assertEqual(len(args), 0)
        self.assertEqual(f.convert([]), myokit.Number(12))

        # Create with one argument
        f = myokit.UserFunction(
            'x', [myokit.Name('a')], myokit.parse_expression('1 + a'))
        self.assertEqual(len(list(f.arguments())), 1)
        args = {myokit.Name('a'): myokit.Number(3)}
        self.assertEqual(f.convert(args).eval(), 4)

        # Create with two argument
        f = myokit.UserFunction(
            'x', [myokit.Name('a'), myokit.Name('b')],
            myokit.parse_expression('a + b'))
        self.assertEqual(len(list(f.arguments())), 2)
        args = {
            myokit.Name('a'): myokit.Number(3),
            myokit.Name('b'): myokit.Number(4)
        }
        self.assertEqual(f.convert(args), myokit.parse_expression('3 + 4'))

        # Call with wrong arguments
        del(args[myokit.Name('a')])
        self.assertRaisesRegex(
            ValueError, 'Wrong number', f.convert, args)
        args[myokit.Name('c')] = myokit.Number(100)
        self.assertRaisesRegex(
            ValueError, 'Missing input argument', f.convert, args)


class EquationTest(unittest.TestCase):
    """
    Tests :class:`myokit.Equation`.
    """
    def test_creation(self):
        """ Test creation of equations. """
        lhs = myokit.Name('x')
        rhs = myokit.Number('3')
        myokit.Equation(lhs, rhs)

    def test_eq(self):
        """ Test equality checking. """
        eq1 = myokit.Equation(myokit.Name('x'), myokit.Number('3'))
        eq2 = myokit.Equation(myokit.Name('x'), myokit.Number('3'))
        self.assertEqual(eq1, eq2)
        self.assertEqual(eq2, eq1)
        self.assertFalse(eq1 != eq2)

        eq2 = myokit.Equation(myokit.Name('x'), myokit.Number('4'))
        self.assertNotEqual(eq1, eq2)
        self.assertNotEqual(eq2, eq1)
        self.assertTrue(eq1 != eq2)

        eq2 = myokit.Equation(myokit.Name('y'), myokit.Number('3'))
        self.assertNotEqual(eq1, eq2)
        self.assertNotEqual(eq2, eq1)

        eq2 = myokit.Equal(myokit.Name('x'), myokit.Number('3'))
        self.assertNotEqual(eq1, eq2)
        self.assertNotEqual(eq2, eq1)

        eq2 = 'hi'
        self.assertNotEqual(eq1, eq2)
        self.assertNotEqual(eq2, eq1)

    def test_code(self):
        """ Test :meth:`Equation.code()`. """
        eq = myokit.Equation(myokit.Name('x'), myokit.Number('3'))
        self.assertEqual(eq.code(), 'str:x = 3')
        self.assertEqual(eq.code(), str(eq))

    def test_hash(self):
        """ Test that equations can be hashed. """
        # No exception = pass
        hash(myokit.Equation(myokit.Name('x'), myokit.Number('3')))

    def test_iter(self):
        """ Test iteration over an equation. """
        lhs = myokit.Name('x')
        rhs = myokit.Number('3')
        eq = myokit.Equation(lhs, rhs)
        i = iter(eq)
        self.assertEqual(next(i), lhs)
        self.assertEqual(next(i), rhs)
        self.assertEqual(len(list(eq)), 2)


if __name__ == '__main__':
    unittest.main()
