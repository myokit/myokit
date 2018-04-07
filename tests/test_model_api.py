#!/usr/bin/env python
#
# Tests the model API.
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
from myokit import (
    Model, Component, Variable, Derivative, Equation, Name, Number,
    Plus, Minus, Multiply, PrefixMinus,
    IntegrityError, MissingRhsError, MissingTimeVariableError,
    UnusedVariableError, CyclicalDependencyError,
    DuplicateName, InvalidNameError,
    ParseError, IllegalReferenceError,
)


class ModelBuildTest(unittest.TestCase):

    def test_model_creation(self):
        # Create a model
        m = Model('LotkaVolterra')

        # Add the first component
        X = m.add_component('X')
        self.assertEqual(X.qname(), 'X')
        self.assertEqual(X.parent(), m)
        self.assertIsInstance(X, Component)
        self.assertIn(X.qname(), m)
        self.assertEqual(len(m), 1)

        # Add variable a
        self.assertFalse(X.has_variable('a'))
        a = X.add_variable('a')
        self.assertTrue(X.has_variable('a'))
        self.assertEqual(a, a)
        self.assertIsInstance(a, Variable)
        self.assertEqual(len(X), 1)
        self.assertIn(a.name(), X)
        a.set_rhs(3)
        self.assertFalse(a.is_state())
        self.assertFalse(a.is_intermediary())
        self.assertTrue(a.is_constant())
        self.assertEqual(a.lhs(), Name(a))
        self.assertEqual(a.rhs(), Number(3))
        self.assertEqual(a.rhs().eval(), 3)
        self.assertEqual(a.code(), 'a = 3\n')
        self.assertEqual(a.eq().code(), 'X.a = 3')
        self.assertEqual(a.lhs().code(), 'X.a')
        self.assertEqual(a.rhs().code(), '3')
        self.assertEqual(a.eq(), Equation(Name(a), Number(3)))

        # Check lhs
        a_name1 = myokit.Name(a)
        a_name2 = myokit.Name(a)
        self.assertEqual(a_name1, a_name1)
        self.assertEqual(a_name2, a_name2)
        self.assertEqual(a_name1, a_name2)
        self.assertEqual(a_name2, a_name1)

        # Add variable b with two temporary variables
        b = X.add_variable('b')
        self.assertIsInstance(b, Variable)
        self.assertEqual(len(X), 2)
        self.assertIn(b.name(), X)
        self.assertFalse(b.has_variable('b1'))
        b1 = b.add_variable('b1')
        self.assertTrue(b.has_variable('b1'))
        self.assertEqual(len(b), 1)
        self.assertIn(b1.name(), b)
        self.assertIsInstance(b1, Variable)
        b2 = b.add_variable('b2')
        self.assertEqual(len(b), 2)
        self.assertIn(b2.name(), b)
        self.assertIsInstance(b2, Variable)
        b1.set_rhs(1)
        b2.set_rhs(Minus(Minus(Name(a), Name(b1)), Number(1)))
        b.set_rhs(Plus(Name(b1), Name(b2)))
        self.assertEqual(b.rhs().eval(), 2)
        self.assertFalse(b.is_state())
        self.assertFalse(b.is_intermediary())
        self.assertTrue(b.is_constant())
        self.assertEqual(b.lhs(), Name(b))

        # Add state variable x
        x = X.add_variable('x')
        x.set_rhs(10)
        x.promote()
        self.assertNotEqual(x, X)
        self.assertIsInstance(x, Variable)
        self.assertEqual(len(X), 3)
        self.assertIn(x.name(), X)
        self.assertTrue(x.is_state())
        self.assertFalse(x.is_intermediary())
        self.assertFalse(x.is_constant())
        self.assertEqual(x.lhs(), Derivative(Name(x)))

        # Test demoting, promoting
        x.demote()
        self.assertFalse(x.is_state())
        self.assertFalse(x.is_intermediary())
        self.assertTrue(x.is_constant())
        self.assertEqual(x.lhs(), Name(x))
        x.promote()
        self.assertTrue(x.is_state())
        self.assertFalse(x.is_intermediary())
        self.assertFalse(x.is_constant())
        self.assertEqual(x.lhs(), Derivative(Name(x)))
        x.demote()
        x.promote()
        x.demote()
        x.promote()
        self.assertTrue(x.is_state())
        self.assertFalse(x.is_intermediary())
        self.assertFalse(x.is_constant())
        self.assertEqual(x.lhs(), Derivative(Name(x)))

        # Add second component, variables
        Y = m.add_component('Y')
        self.assertNotEqual(X, Y)
        self.assertEqual(len(m), 2)
        c = Y.add_variable('c')
        c.set_rhs(Minus(Name(a), Number(1)))
        d = Y.add_variable('d')
        d.set_rhs(2)
        y = Y.add_variable('y')
        y.promote()

        # Set rhs for x and y
        x.set_rhs(Minus(
            Multiply(Name(a), Name(x)),
            Multiply(Multiply(Name(b), Name(x)), Name(y))))
        x.set_state_value(10)
        self.assertEqual(x.rhs().code(), 'X.a * X.x - X.b * X.x * Y.y')
        y.set_rhs(Plus(
            Multiply(PrefixMinus(Name(c)), Name(y)),
            Multiply(Multiply(Name(d), Name(x)), Name(y))))
        y.set_state_value(5)
        self.assertEqual(y.rhs().code(), '-Y.c * Y.y + Y.d * X.x * Y.y')

        # Add another component, variables
        Z = m.add_component('Z')
        self.assertNotEqual(X, Z)
        self.assertNotEqual(Y, Z)
        self.assertEqual(len(m), 3)
        t = Z.add_variable('total')
        self.assertEqual(t.name(), 'total')
        self.assertEqual(t.qname(), 'Z.total')
        self.assertEqual(t.qname(X), 'Z.total')
        self.assertEqual(t.qname(Z), 'total')
        t.set_rhs(Plus(Name(x), Name(y)))
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
            lst = vrs[m.get(var).lhs() if type(var) in [str, unicode] else var]
            self.assertEqual(len(lst), len(dps))
            for d in dps:
                d = m.get(d).lhs() if type(d) in [str, unicode] else d
                self.assertIn(d, lst)

        vrs = m.map_shallow_dependencies(omit_states=False)
        self.assertEqual(len(vrs), 12)
        has('X.a')
        has('X.b', 'X.b.b1', 'X.b.b2')
        has('X.b.b1')
        has('X.b.b2', 'X.a', 'X.b.b1')
        has('X.x', 'X.a', 'X.b', Name(x), Name(y))
        has(Name(x))
        has('Y.c', 'X.a')
        has('Y.d')
        has('Y.y', 'Y.c', 'Y.d', Name(x), Name(y))
        has(Name(y))
        has('Z.total', Name(x), Name(y))
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

    def test_move_variable(self):
        """
        Tests the method to move component variables to another component.
        """
        # Create a model
        m = Model('LotkaVolterra')
        X = m.add_component('X')
        a = X.add_variable('a')
        a.set_rhs(3)
        b = X.add_variable('b')
        b1 = b.add_variable('b1')
        b2 = b.add_variable('b2')
        b1.set_rhs(1)
        b2.set_rhs(Minus(Minus(Name(a), Name(b1)), Number(1)))
        b.set_rhs(Plus(Name(b1), Name(b2)))
        x = X.add_variable('x')
        x.promote()
        Y = m.add_component('Y')
        c = Y.add_variable('c')
        c.set_rhs(Minus(Name(a), Number(1)))
        d = Y.add_variable('d')
        d.set_rhs(2)
        y = Y.add_variable('y')
        y.promote()
        x.set_rhs(Minus(
            Multiply(Name(a), Name(x)),
            Multiply(Multiply(Name(b), Name(x)), Name(y))))
        x.set_state_value(10)
        y.set_rhs(Plus(
            Multiply(PrefixMinus(Name(c)), Name(y)),
            Multiply(Multiply(Name(d), Name(x)), Name(y))))
        y.set_state_value(5)
        Z = m.add_component('Z')
        t = Z.add_variable('total')
        t.set_rhs(Plus(Name(x), Name(y)))
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

    def test_remove_component(self):
        """
        Tests the removal of a component.
        """
        # Create model
        m = Model('LotkaVolterra')
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
        # With internal variables
        a = X.add_variable('a')
        a.set_rhs(Number(4))
        b = X.add_variable('b')
        b.set_rhs(Name(a))
        m.remove_component(X)
        self.assertEqual(m.count_components(), 0)
        # With dependencies from another component
        X = m.add_component('X')
        a = X.add_variable('a')
        a.set_rhs(Number(45))
        b = X.add_variable('b')
        b.set_rhs(Name(b))
        Y = m.add_component('Y')
        c = Y.add_variable('c')
        c.set_rhs(Name(a))
        d = Y.add_variable('d')
        d.set_rhs(Name(c))
        self.assertEqual(m.count_components(), 2)
        self.assertRaises(IntegrityError, m.remove_component, X)
        self.assertEqual(m.count_components(), 2)
        # In the right order...
        m.remove_component(Y)
        self.assertEqual(m.count_components(), 1)
        m.remove_component(X)
        self.assertEqual(m.count_components(), 0)

    def test_remove_variable(self):
        """
        Tests the removal of a variable.
        """
        # Create a model
        m = Model('LotkaVolterra')
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
        a.set_rhs(Number(5))
        self.assertEqual(X.count_variables(), 1)
        # Test deleting dependent variables
        b = X.add_variable('b')
        self.assertEqual(X.count_variables(), 2)
        b.set_rhs(Plus(Number(3), Name(a)))
        # Test blocking of removal
        self.assertRaises(IntegrityError, X.remove_variable, a)
        self.assertEqual(X.count_variables(), 2)
        # Test removal in the right order
        X.remove_variable(b)
        self.assertEqual(X.count_variables(), 1)
        X.remove_variable(a)
        self.assertEqual(X.count_variables(), 0)
        # Test reference to current state variable values
        a = X.add_variable('a')
        a.set_rhs(Number(5))
        a.promote()
        b = X.add_variable('b')
        b.set_rhs(Plus(Number(3), Name(a)))
        self.assertRaises(IntegrityError, X.remove_variable, a)
        X.remove_variable(b)
        X.remove_variable(a)
        self.assertEqual(X.count_variables(), 0)
        # Test reference to current state variable values with "self"-ref
        a = X.add_variable('a')
        a.promote()
        a.set_rhs(Name(a))
        X.remove_variable(a)
        # Test it doesn't interfere with normal workings
        a = X.add_variable('a')
        a.promote()
        a.set_rhs(Name(a))
        b = X.add_variable('b')
        b.set_rhs(Name(a))
        self.assertRaises(IntegrityError, X.remove_variable, a)
        X.remove_variable(b)
        X.remove_variable(a)
        # Test reference to dot
        a = X.add_variable('a')
        a.set_rhs(Number(5))
        a.promote()
        b = X.add_variable('b')
        b.set_rhs(Derivative(Name(a)))
        self.assertRaises(IntegrityError, X.remove_variable, a)
        X.remove_variable(b)
        X.remove_variable(a)
        # Test if orphaned
        self.assertIsNone(b.parent())
        # Test deleting variable with nested variables
        a = X.add_variable('a')
        b = a.add_variable('b')
        b.set_rhs(Plus(Number(2), Number(2)))
        a.set_rhs(Multiply(Number(3), Name(b)))
        self.assertRaises(IntegrityError, X.remove_variable, a)
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
        b.set_rhs(Multiply(Number(3), Name(a)))
        a.set_rhs(Name(b))
        self.assertRaises(IntegrityError, X.remove_variable, a)
        self.assertRaises(IntegrityError, a.remove_variable, b)
        self.assertRaises(IntegrityError, a.remove_variable, b, True)
        X.remove_variable(a, recursive=True)

    def test_remove_with_alias(self):
        """
        Tests cloning after an add / remove event.
        """
        m = Model('AddRemoveClone')
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

    def test_resolve(self):
        """
        Tests if an error is raised when a variable can't be resolved.
        """
        m = Model('Resolve')
        c = m.add_component('c')
        p = c.add_variable('p')
        q = c.add_variable('q')
        p.set_rhs('10 * q')
        self.assertRaises(ParseError, q.set_rhs, '10 * r')

    def test_scope(self):
        """
        Tests if illegal references are detected.
        """
        m = Model('Scope')
        c = m.add_component('c')
        p = c.add_variable('p')
        q = p.add_variable('q')
        p.set_rhs('10 + q')
        q.set_rhs('18 / 2.4')
        d = m.add_component('d')
        r = d.add_variable('r')
        r.set_rhs(Name(q))
        self.assertRaises(IllegalReferenceError, r.validate)

    def test_invalid_names(self):
        """
        Tests if invalid or duplicate names are detected.
        """
        m = Model('Duplicates')
        c0 = m.add_component('c0')
        t = c0.add_variable('time')
        t.set_rhs(Number(0))
        t.set_binding('time')

        # Test add component
        # Duplicates
        self.assertRaises(DuplicateName, m.add_component, 'c0')
        # Badly formed names
        self.assertRaises(InvalidNameError, m.add_component, '0')
        self.assertRaises(InvalidNameError, m.add_component, '_0')
        self.assertRaises(InvalidNameError, m.add_component, '123abvc')
        self.assertRaises(InvalidNameError, m.add_component, 'ab cd')
        self.assertRaises(InvalidNameError, m.add_component, 'ab.cd')
        self.assertRaises(InvalidNameError, m.add_component, 'ab!cd')
        self.assertRaises(InvalidNameError, m.add_component, '5*x')
        # Keywords
        self.assertRaises(InvalidNameError, m.add_component, 'and')
        self.assertRaises(InvalidNameError, m.add_component, 'bind')
        # Test adding variable to component
        c1 = m.add_component('c1')
        # Duplicate
        # Badly formed names
        self.assertRaises(InvalidNameError, c0.add_variable, '0')
        self.assertRaises(InvalidNameError, c0.add_variable, '_aap')
        self.assertRaises(InvalidNameError, c0.add_variable, '123abvc')
        self.assertRaises(InvalidNameError, c0.add_variable, 'ab cd')
        self.assertRaises(InvalidNameError, c0.add_variable, 'ab.cd')
        self.assertRaises(InvalidNameError, c0.add_variable, 'ab!cd')
        self.assertRaises(InvalidNameError, c0.add_variable, '5*x')
        # Keywords
        self.assertRaises(InvalidNameError, c0.add_variable, 'or')
        self.assertRaises(InvalidNameError, c0.add_variable, 'label')

        # Test adding variable to variable
        v1 = c0.add_variable('c0')
        # Duplicate
        v2 = c1.add_variable('c0')
        self.assertRaises(DuplicateName, c1.add_variable, 'c0')
        self.assertRaises(DuplicateName, v1.add_variable, 'c0')
        self.assertRaises(DuplicateName, v2.add_variable, 'c0')
        # Badly formed names
        self.assertRaises(InvalidNameError, v1.add_variable, '0')
        self.assertRaises(InvalidNameError, v1.add_variable, '_aap')
        self.assertRaises(InvalidNameError, v1.add_variable, '123abvc')
        self.assertRaises(InvalidNameError, v1.add_variable, 'ab cd')
        self.assertRaises(InvalidNameError, v1.add_variable, 'ab.cd')
        self.assertRaises(InvalidNameError, v1.add_variable, 'ab!cd')
        self.assertRaises(InvalidNameError, v1.add_variable, '5*x')
        # Keywords
        self.assertRaises(InvalidNameError, v1.add_variable, 'not')
        self.assertRaises(InvalidNameError, v1.add_variable, 'in')

    def test_unused_and_cycles(self):
        """
        Test unused variable and cycle detection.
        """
        m = Model('LotkaVolterra')
        c0 = m.add_component('c0')
        t = c0.add_variable('time')
        t.set_rhs(Number(0))
        t.set_binding('time')
        c1 = m.add_component('c1')
        m.add_component('c2')
        c1_a = c1.add_variable('a')
        c1_b = c1.add_variable('b')
        c1_a.promote(1.0)
        c1_a.set_rhs(Multiply(Name(c1_a), Number(0.5)))
        c1_b.set_rhs(Multiply(Name(c1_a), Number(1.0)))
        # b is unused, test if found
        m.validate()
        w = m.warnings()
        self.assertEqual(len(w), 1)
        self.assertEqual(type(w[0]), UnusedVariableError)
        # b is used by c, c is unused, test if found
        c1_c = c1.add_variable('c')
        c1_c.set_rhs(Name(c1_b))
        m.validate()
        w = m.warnings()
        self.assertEqual(len(w), 2)
        self.assertEqual(type(w[0]), UnusedVariableError)
        self.assertEqual(type(w[1]), UnusedVariableError)
        # Test 1:1 cycle
        c1_b.set_rhs(Name(c1_b))
        self.assertRaises(CyclicalDependencyError, m.validate)
        # Test longer cycles
        c1_b.set_rhs(Multiply(Number(10), Name(c1_c)))
        self.assertRaises(CyclicalDependencyError, m.validate)
        # Reset
        c1_b.set_rhs(Multiply(Name(c1_a), Number(1.0)))
        m.validate()
        # Test cycle involving state variable
        c1_a.set_rhs(Name(c1_b))
        m.validate()
        c1_b.set_rhs(Multiply(Name(c1_a), Name(c1_b)))
        self.assertRaises(CyclicalDependencyError, m.validate)
        c1_b.set_rhs(Multiply(Name(c1_a), Name(c1_c)))
        c1_c.set_rhs(Multiply(Name(c1_a), Number(3)))
        m.validate()
        w = m.warnings()
        self.assertEqual(len(w), 0)
        c1_c.set_rhs(Multiply(Name(c1_a), Name(c1_b)))
        self.assertRaises(CyclicalDependencyError, m.validate)

    def test_no_rhs_error(self):
        """
        Tests an exception is raised when a variable is missing an rhs.
        """
        m = Model('LotkaVolterra')
        c0 = m.add_component('c0')
        t = c0.add_variable('time')
        t.set_binding('time')
        self.assertRaises(MissingRhsError, m.validate)
        t.set_rhs(Number(0))
        m.validate()
        a = c0.add_variable('test')
        self.assertRaises(MissingRhsError, m.validate)
        a.set_rhs(Number(1))
        m.validate()
        b = c0.add_variable('derv')
        b.promote(10)
        self.assertRaises(MissingRhsError, m.validate)
        b.set_rhs(2)
        m.validate()

    def test_no_time_variable(self):
        """
        Tests an exception is raised if nothing is bound to time.
        """
        m = Model('LotkaVolterra')
        c0 = m.add_component('c0')
        t = c0.add_variable('time')
        t.set_rhs(Number(0))
        self.assertRaises(MissingTimeVariableError, m.validate)

    def test_expressions_between(self):
        """
        Tests the ``expressions_between`` method.
        """
        m = Model('test')
        x = m.add_component('membrane')
        t = x.add_variable('time')
        t.set_rhs(0)
        t.set_binding('time')
        a = x.add_variable('a')
        a.set_rhs(12)
        b = x.add_variable('b')
        b.set_rhs('3 * a')
        c = x.add_variable('c')
        c.set_rhs('a + b')
        d = x.add_variable('d')
        d.set_rhs('a * c')
        e = x.add_variable('e')
        e.set_rhs('sqrt(d) * b + 3*c')
        f = x.add_variable('f')
        f.set_rhs('exp(e - 10)')
        g = x.add_variable('g')
        g.set_rhs('3 * e + 4 * f')
        h = x.add_variable('h')
        h.set_rhs('f + cos(g)')
        i = x.add_variable('i')
        i.promote(0.43)
        i.set_rhs('1 + h')
        m.validate()
        eqs = m.expressions_between(a, i)
        self.assertEqual(len(eqs), 9)
        for k, v in enumerate([a, b, c, d, e, f, g, h, i]):
            self.assertEqual(v.lhs(), eqs[k].lhs)
            self.assertEqual(v.rhs(), eqs[k].rhs)

    def test_add_component_allow_renamining(self):
        """
        Tests the ``Model.add_component_allow_renaming`` method.
        """
        m = Model('test')
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

    def test_add_variable_allow_renaming(self):
        """
        Tests the ``VarProvider.add_variable_allow_renaming`` method.
        """
        m = Model('test')
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

    def test_get(self):
        """
        Tests the VarOwner.get() method.
        """
        # Test basics
        m = Model('test')
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

        # Test class filter
        self.assertIs(m.get('c', myokit.Component), c)
        self.assertRaises(KeyError, m.get, 'c', myokit.Variable)
        self.assertIs(m.get('c.x', myokit.Variable), x)
        self.assertRaises(KeyError, m.get, 'x', myokit.Component)

    def test_add_function(self):
        """
        Tests the ``Model.add_function`` method.
        """
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
        self.assertRaises(
            myokit.DuplicateFunctionName, m.add_function, 'f', ('a', 'b'),
            'a - b')

        # Test duplicate argument name
        self.assertRaises(
            myokit.DuplicateFunctionArgument, m.add_function, 'g', ('a', 'a'),
            'a + a')

        # Dot operator is not allowed
        self.assertRaises(
            myokit.InvalidFunction, m.add_function, 'fdot', ('a', ), 'dot(a)')

        # Unused argument
        self.assertRaises(
            myokit.InvalidFunction, m.add_function, 'fun', ('a', 'b'), 'a')

    def test_check_units(self):
        """
        Tests the ``model.check_units`` method.
        """
        model = myokit.Model('m')
        component = model.add_component('c')
        a = component.add_variable('a')
        a.set_rhs(1)
        b = component.add_variable('b')
        b.set_rhs(2)
        c = component.add_variable('c')
        c.set_rhs('a + b')
        model.check_units()


if __name__ == '__main__':
    unittest.main()
