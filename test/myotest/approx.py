#!/usr/bin/env python2
#
# Tests the parser
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
import unittest
import numpy as np
import myokit
import myokit.lib.approx as approx
import myotest


def suite():
    """
    Returns a test suite with all tests in this module
    """
    suite = unittest.TestSuite()
    # Polynomials
    suite.addTest(ApproxTest('test_polynomial'))
    suite.addTest(ApproxTest('test_piecewise_polynomial'))
    # Fitting
    suite.addTest(ApproxTest('test_lagrange_fit'))
    suite.addTest(ApproxTest('test_remez_fit'))
    suite.addTest(ApproxTest('test_cubic_spline_fit'))
    # Done!
    return suite


class ApproxTest(unittest.TestCase):
    """
    Test the module myokit.lib.approx
    """
    def test_polynomial(self):
        """
        Tests Polynomial()
        """
        # Set up test space
        c = [1.23, 4.567, -8.901, 0.000321, -.04367]
        x = np.linspace(-10, 10, 10000)
        F = c[0] + x * (c[1] + x * (c[2] + x * (c[3] + x * c[4])))
        # Test polynomial
        p = approx.Polynomial(c)
        self.assertTrue(np.all(np.abs(F - p(x)) < 1e-14))
        # Test myokit polynomial and myokit-to-numpy conversion
        g = p.myokit_form(myokit.Name('x')).pyfunc()
        self.assertTrue(np.all(np.abs(F - g(x)) < 1e-14))
        # Test len, iterator and item access
        self.assertEqual(len(c), len(p))
        for k, x in enumerate(p):
            self.assertEqual(x, c[k])
            self.assertEqual(x, p[k])

    def test_piecewise_polynomial(self):
        """
        Test piecewise polynomial
        """
        # Set up test space
        x = np.linspace(-10, 10, 10000)
        # Test number one
        knots = [1, 2]
        coeff = [
            [0.123, 0.456, 2.789, -0.123, -0.456],
            [5.4123, -0.1456, 7.789, -0.123, -0.456],
            [-40.6123, 0.2456, -0.86453, 0.23, -0.753],
        ]
        f = approx.PiecewisePolynomial(coeff, knots)
        g = f.myokit_form(myokit.Name('x')).pyfunc()
        if myotest.DEBUG:
            import matplotlib.pyplot as pl
            pl.figure()
            p0 = approx.Polynomial(coeff[0])
            p1 = approx.Polynomial(coeff[1])
            p2 = approx.Polynomial(coeff[2])
            pl.plot(x, p0(x), label='p0')
            pl.plot(x, p1(x), label='p1')
            pl.plot(x, p2(x), label='p2')
            pl.plot(x, f(x), label='f')
            pl.plot(x, g(x), label='g')
            pl.legend(loc='lower left')
            pl.show()
        self.assertTrue(np.all(np.abs(f(x) - g(x)) < 1e-15))
        # Test number two
        knots = [-5.0, 1.0, 3.123]
        coeff = [
            [0.123, 0.456, 2.789, -0.123, -0.456, 0.0035],
            [5.4123, -0.1456, 7.789, -0.123, -0.456, 0.023],
            [-40.6123, 0.2456, -0.86453, 0.23, -0.753, 0.4262],
            [-20.4123, -2.0156, 1.79, -0.00642, -0.2632, -1.098],
        ]
        f = approx.PiecewisePolynomial(coeff, knots)
        g = f.myokit_form(myokit.Name('x')).pyfunc()
        self.assertTrue(np.all(np.abs(f(x) - g(x)) < 1e-15))
        # Test cloning
        h = approx.PiecewisePolynomial(f)
        self.assertTrue(np.all(np.abs(f(x) - h(x)) < 1e-15))

    def test_lagrange_fit(self):
        """
        Test fit_lagrange_polynomial()
        """
        p = [-100, 50]

        def f(x):
            return 0.095 * np.exp(-0.01 * (x - 5)) / (
                1 + np.exp(-0.072 * (x - 5)))
        g = approx.fit_lagrange_polynomial(f, p, n=15)

        # No error? Then okay
        if myotest.DEBUG:
            import matplotlib.pyplot as pl
            pl.figure()
            pl.title('Lagrange polynomial')
            x = np.linspace(p[0], p[1], 1000)
            pl.plot(x, f(x))
            pl.plot(x, g(x))
            pl.show()

    def test_remez_fit(self):
        """
        Test fit_remez_polynomial()
        """
        p = [-100, 50]

        def f(x):
            return 0.095 * np.exp(-0.01 * (x - 5)) / (
                1 + np.exp(-0.072 * (x - 5)))
        g = approx.fit_remez_polynomial(f, p, n=15)

        # No error? Then okay
        if myotest.DEBUG:
            import matplotlib.pyplot as pl
            pl.figure()
            pl.title('Polynomial fitted with remez exchange algorithm')
            x = np.linspace(p[0], p[1], 1000)
            pl.plot(x, f(x))
            pl.plot(x, g(x))
            pl.show()

    def test_cubic_spline_fit(self):
        """
        Tests fit_cubic_spline() and solve_cubic_spline()
        """
        p = [-100, 100]

        def f(x):
            return 0.095 * np.exp(-0.01 * (x - 5)) / (
                1 + np.exp(-0.072 * (x - 5)))
        g = approx.fit_cubic_spline(f, p)
        self.assertEqual(type(g), approx.Spline)

        # No error? Then okay
        if myotest.DEBUG:
            import matplotlib.pyplot as pl
            pl.figure()
            pl.title('Cubic spline fit')
            x = np.linspace(p[0], p[1], 1000)
            pl.plot(x, f(x))
            pl.plot(x, g(x))
            k = np.array(g.knots())
            pl.plot(k, f(k), 'x')
            pl.show()
