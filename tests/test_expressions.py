#!/usr/bin/env python
#
# Tests the expression classes.
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


#TODO Add tests for all operators


class NumberTest(unittest.TestCase):
    def test_basics(self):
        """
        Test the basics of the Number class.
        """
        # Test myokit.Number creation and representation
        x = myokit.Number(-4.0)
        self.assertEqual(str(x), '-4')
        x = myokit.Number(4.0)
        self.assertEqual(str(x), '4')
        y = myokit.Number(4)
        self.assertEqual(str(y), '4')
        self.assertEqual(x, y)
        self.assertFalse(x is y)
        x = myokit.Number(4.01)
        self.assertEqual(str(x), '4.01')
        x = myokit.Number(-4.01)
        self.assertEqual(str(x), '-4.01')
        x = myokit.Number('-4e9')
        self.assertEqual(str(x), '-4.00000000000000000e9')
        x = myokit.Number('4e+09')
        self.assertEqual(str(x), ' 4.00000000000000000e9')
        x = myokit.Number('-4e+00')
        self.assertEqual(str(x), '-4')
        x = myokit.Number('4e-05')
        self.assertEqual(str(x), '4e-5')
        x = myokit.Number(4, myokit.Unit.parse_simple('pF'))
        self.assertEqual(str(x), '4 [pF]')
        x = myokit.Number(-3, myokit.Unit.parse_simple('pF'))
        self.assertEqual(str(x), '-3 [pF]')
        # Test unit conversion
        x = myokit.Number('2000', myokit.units.pF)
        y = x.convert('nF')
        self.assertEqual(y.eval(), 2)
        self.assertEqual(str(y), '2 [nF]')
        self.assertEqual(y.unit(), myokit.Unit.parse_simple('nF'))
        a = y.convert('uF')
        b = x.convert('uF')
        self.assertEqual(a, b)
        self.assertRaises(myokit.IncompatibleUnitError, x.convert, 'A')


class ExpressionTest(unittest.TestCase):
    def test_equal(self):
        """
        Tests __eq__ operators
        """
        a1 = myokit.Number(4)
        a2 = myokit.Number(5)
        self.assertEqual(a1, a1)
        self.assertEqual(a1, myokit.Number(4))
        self.assertEqual(a1, myokit.Number(4.0))
        self.assertNotEqual(a1, a2)
        b1 = myokit.Name('test')
        b2 = myokit.Name('tost')
        self.assertEqual(b1, b1)
        self.assertNotEqual(b1, b2)
        c1 = myokit.PrefixPlus(a1)
        c2 = myokit.PrefixPlus(a1)
        self.assertEqual(c1, c1)
        self.assertEqual(c1, c2)
        c2 = myokit.PrefixPlus(a2)
        self.assertNotEqual(c1, c2)
        d1 = myokit.Plus(a1, a2)
        d2 = myokit.Plus(a1, a2)
        self.assertEqual(d1, d1)
        self.assertEqual(d1, d2)
        d2 = myokit.Plus(a2, a1)
        self.assertNotEqual(d2, d1)
        e1 = myokit.Sqrt(a1)
        e2 = myokit.Sqrt(a1)
        self.assertEqual(e1, e1)
        self.assertEqual(e1, e2)
        e2 = myokit.Sqrt(a2)
        self.assertNotEqual(e1, e2)

    def test_if(self):
        """
        Tests If
        """
        true = myokit.Number(1)
        false = myokit.Number(0)
        two = myokit.Number(2)
        three = myokit.Number(3)
        x = myokit.If(true, two, three)
        self.assertEqual(x.eval(), 2)
        self.assertEqual(x.condition(), true)
        x = myokit.If(true, three, two)
        self.assertEqual(x.eval(), 3)
        x = myokit.If(false, two, three)
        self.assertEqual(x.eval(), 3)
        self.assertEqual(x.condition(), false)
        x = myokit.If(false, three, two)
        self.assertEqual(x.eval(), 2)

        # Conversion to piecewise
        x = myokit.If(true, two, three).piecewise()
        self.assertIsInstance(x, myokit.Piecewise)
        self.assertEqual(x.eval(), 2)
        x = myokit.If(true, three, two).piecewise()
        self.assertIsInstance(x, myokit.Piecewise)
        self.assertEqual(x.eval(), 3)
        x = myokit.If(false, two, three).piecewise()
        self.assertIsInstance(x, myokit.Piecewise)
        self.assertEqual(x.eval(), 3)
        x = myokit.If(false, three, two).piecewise()
        self.assertIsInstance(x, myokit.Piecewise)
        self.assertEqual(x.eval(), 2)

    def test_opiecewise(self):
        """
        Tests OrderedPiecewise
        """
        x = myokit.Name('x')
        p = myokit.OrderedPiecewise(
            x,
            myokit.parse_expression('1 * 10'), myokit.Number(1),
            myokit.parse_expression('2 * 10'), myokit.Number(2),
            myokit.parse_expression('3 * 10'), myokit.Number(3),
            myokit.parse_expression('4 * 10')
        )

        def test(p, x):
            self.assertEqual(p.eval(subst={x: 0}), 10)
            self.assertEqual(p.eval(subst={x: 0.99}), 10)
            self.assertEqual(p.eval(subst={x: 1}), 20)
            self.assertEqual(p.eval(subst={x: 1.99}), 20)
            self.assertEqual(p.eval(subst={x: 2}), 30)
            self.assertEqual(p.eval(subst={x: 2.99}), 30)
            self.assertEqual(p.eval(subst={x: 3}), 40)
            self.assertEqual(p.eval(subst={x: 4}), 40)
        test(p, x)

        # Conversion to piecewise
        w = myokit.Piecewise(
            myokit.Less(x, myokit.Number(1)), myokit.parse_expression('1* 10'),
            myokit.Less(x, myokit.Number(2)), myokit.parse_expression('2 *10'),
            myokit.Less(
                x, myokit.Number(3)), myokit.parse_expression('3 * 10'),
            myokit.parse_expression('4 * 10'))
        test(w, x)
        q = p.piecewise()
        self.assertEqual(q, w)
        test(p, x)

        # Test conversion to binary tree
        r = p.if_tree()
        test(r, x)

    def test_polynomial(self):
        """
        Tests Polynomial.
        """
        x = myokit.Name('x')
        c = [
            myokit.Number(5),
            myokit.Number(4),
            myokit.Number(3),
            myokit.Number(2)
        ]
        p = myokit.Polynomial(x, *c)
        self.assertEqual(p.eval(subst={x: 0}), 5)
        self.assertEqual(p.eval(subst={x: 1}), 14)
        self.assertEqual(p.eval(subst={x: 2}), 41)
        self.assertEqual(p.eval(subst={x: -1}), 2)
        self.assertEqual(p.eval(subst={x: 0.5}), 8)
        q = p.tree()
        self.assertNotEqual(p, q)
        for i in [-1, 0, 0.5, 1, 2]:
            s = {x: i}
            self.assertEqual(p.eval(subst=s), q.eval(subst=s))
        q = p.tree(horner=False)
        self.assertNotEqual(p, q)
        for i in [-1, 0, 0.5, 1, 2]:
            s = {x: i}
            self.assertEqual(p.eval(subst=s), q.eval(subst=s))


if __name__ == '__main__':
    unittest.main()
