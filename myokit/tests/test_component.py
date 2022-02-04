#!/usr/bin/env python3
#
# Tests the Component and VarOwner classes.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import myokit
import unittest


# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp


class VarOwnerTest(unittest.TestCase):
    """
    Tests parts of :class:`myokit.VarOwner`.
    """
    def test_move_variable(self):
        # Test the method to move component variables to another component.

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
        # Test the removal of a variable.

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

        # Test deleting variable with nested variables that depend on each
        # other
        a = X.add_variable('a')
        b = a.add_variable('b')
        c = a.add_variable('c')
        d = a.add_variable('d')
        a.set_rhs('b + c - d')
        a.promote(0.1)
        b.set_rhs('2 * a - d')
        c.set_rhs('a + b + d')
        d.set_rhs('3 * a')
        self.assertRaises(myokit.IntegrityError, X.remove_variable, a)
        self.assertEqual(a.count_variables(), 3)
        self.assertEqual(X.count_variables(), 1)
        X.remove_variable(a, recursive=True)
        self.assertEqual(a.count_variables(), 0)
        self.assertEqual(X.count_variables(), 0)

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

    def test_sequence_interface(self):
        # Test the sequence interface implementation

        model = myokit.load_model('example')
        c = model['membrane']

        vs = [v for v in c]
        self.assertEqual(vs, list(c.variables()))
        self.assertEqual(len(vs), len(c))
        v = c['V']
        self.assertEqual(v.name(), 'V')

    def test_varowner_get(self):
        # Test VarOwner.get().

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

        # Test asking for object from another model
        c2 = m.clone().get('c')
        self.assertRaisesRegex(ValueError, 'different model', c2.get, x)

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
        # Test the ``VarProvider.add_variable_allow_renaming`` method.

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


class ComponentTest(unittest.TestCase):
    """
    Tests parts of :class:`myokit.Component`.
    """
    def test_alias_methods(self):
        # Test various methods to do with aliases.

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
        # Test error handling in :meth:`Component.add_alias()`.
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


if __name__ == '__main__':
    unittest.main()
