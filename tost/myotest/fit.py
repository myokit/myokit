#!/usr/bin/env python2
#
# Tests the fitting module from the library
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
import os
import unittest
import numpy as np
import myokit
import myokit.lib.fit as fit
import myokit.lib.markov as markov
import myotest


def suite():
    """
    Returns a test suite with all tests in this module
    """
    suite = unittest.TestSuite()
    # Quadratic polynomial through a series of points
    suite.addTest(QuadFitTest('test_quadfit'))
    # Parallel and sequential evaluation of user functions
    suite.addTest(EvaluatorTest('test_evaluators'))
    suite.addTest(EvaluatorTest('test_parallel_evaluator'))
    # Short fitting method tests
    #suite.addTest(FittingTest('test_cmaes'))
    suite.addTest(FittingTest('test_pso'))
    suite.addTest(FittingTest('test_snes'))
    suite.addTest(FittingTest('test_xnes'))
    # Done!
    return suite


class EvaluatorTest(unittest.TestCase):
    """
    Tests the sequential and parallel evaluation classes.
    """
    def test_evaluators(self):
        # Test basic sequential/parallel evaluation
        # Create test data
        def f(x):
            if x == 0:
                raise Exception('Everything is terrible')
            return 1 / 1 / 1 / 1 / 1 / 1 / 1 / 1 / 1 / 1 / 1 / 1 / 1 / 1 / x
        x = 1 + np.random.random(100)
        # Simple run: sequential and parallel
        fit.evaluate(f, x, parallel=False)
        # Note: the overhead is almost 100% of the run-time of this test
        fit.evaluate(f, x, parallel=True)

    def test_parallel_evaluator(self):
        # Test parallel execution
        # Create test data
        def f(x):
            if x == 0:
                raise Exception('Everything is terrible')
            return 1 / 1 / 1 / 1 / 1 / 1 / 1 / 1 / 1 / 1 / 1 / 1 / 1 / 1 / x
        e = fit.ParallelEvaluator(f, max_tasks_per_worker=9)
        # Test 1
        x = 1 + np.random.random(30)
        e.evaluate(x)
        # Test 2
        x = 2 + np.random.random(15)
        e.evaluate(x)
        # Test 3 (with exception)
        x[13] = 0
        self.assertRaises(Exception, e.evaluate, x)
        # Repeat run with exception
        x[11] = 0
        self.assertRaises(Exception, e.evaluate, x)
        # Repeat run
        x = 1 + np.random.random(16)
        e.evaluate(x)


class QuadFitTest(unittest.TestCase):
    """
    Tests the quadratic polynomial fitting in myokit.lib.fit.
    """
    def test_quadfit(self):
        """
        Tests quadfit(x, y)
        """
        e = 1e-13

        # 1D
        AA = 7
        BB = np.array([-3])
        CC = np.array([[-2]])

        def f(x):
            x = np.array(x)
            return AA + BB.dot(x) + 0.5 * x.transpose() * CC * x

        x = [-2, 1, 6]
        y = [f(i) for i in x]
        A, B, C = fit.quadfit(x, y)
        self.assertTrue(np.all(np.abs(A - AA) < e))
        self.assertTrue(np.all(np.abs(B - BB) < e))
        self.assertTrue(np.all(np.abs(C - CC) < e))

        # 2D
        a = 5, 4, 3, 1, -2, -4

        def f(x, y):
            return (
                a[0] +
                a[1] * x +
                a[2] * y +
                a[3] * x**2 +
                a[4] * x * y +
                a[5] * y**2)
        x = [[-2, -1], [-1, 3], [0, -1], [1, 2], [2, 2], [3, -4]]
        y = [f(*i) for i in x]
        A, B, C = fit.quadfit(x, y)
        AA = np.array([a[0]])
        BB = np.array([a[1], a[2]])
        CC = np.array([[a[3] * 2, a[4]], [a[4], a[5] * 2]])
        self.assertTrue(np.all(np.abs(A - AA) < e))
        self.assertTrue(np.all(np.abs(B - BB) < e))
        self.assertTrue(np.all(np.abs(C - CC) < e))

        # 3D
        a = 3, 2, 1, -1, -6, 5, 4, 3, 2, 1

        def f(x, y, z):
            return (
                a[0] + a[1] * x + a[2] * y + a[3] * z +
                a[4] * x**2 + a[5] * x * y + a[6] * x * z +
                a[7] * y**2 + a[8] * y * z +
                a[9] * z**2)
        x = [
            [-2, -1, 0], [-1, 2, 3], [0, 2, -1], [1, 1, 2], [2, 2, 2],
            [-1, 3, -4], [4, 2, -1], [4, 1, 2], [4, 2, 2], [1, 2, 3]
        ]
        y = [f(*i) for i in x]
        A, B, C = fit.quadfit(x, y)
        AA = np.array([a[0]])
        BB = np.array([a[1], a[2], a[3]])
        CC = np.array([
            [a[4] * 2, a[5] * 1, a[6] * 1],
            [a[5] * 1, a[7] * 2, a[8] * 1],
            [a[6] * 1, a[8] * 1, a[9] * 2],
        ])
        self.assertTrue(np.all(np.abs(A - AA) < e))
        self.assertTrue(np.all(np.abs(B - BB) < e))
        self.assertTrue(np.all(np.abs(C - CC) < e))


class FittingTest(unittest.TestCase):
    """
    Performs very basic tests of fitting methods (e.g., do they run).
    """
    def __init__(self, name):
        super(FittingTest, self).__init__(name)
        # Load model, simulation etc. only once
        fname = os.path.join(myotest.DIR_DATA, 'clancy-1999-fitting.mmt')
        model = myokit.load_model(fname)

        # Extract the Markov model of INa
        parameters = ['ina.p1', 'ina.p2']
        self._boundaries = [[1e-3, 10], [1e-3, 10]]
        markov_model = markov.LinearModel.from_component(
            model.get('ina'),
            parameters=parameters,
            current='ina.i',
        )

        # Create an analytical markov model simulation
        self._sim = markov.AnalyticalSimulation(markov_model)

        # Voltages to test at
        r = 10
        self._voltages = np.arange(-70, -10 + r, r)

        # Times to evaluate at
        times = np.concatenate((np.linspace(0, 4, 100), np.linspace(4, 8, 20)))

        # Generate reference traces
        self._references = []
        for v in self._voltages:
            self._sim.set_membrane_potential(v)
            x, i = self._sim.solve(times)
            self._references.append(i)

        # Define function to optimize
        def score(guess):
            try:
                error = 0
                self._sim.set_parameters(guess)
                for k, v in enumerate(self._voltages):
                    self._sim.set_membrane_potential(v)
                    x, i = self._sim.solve(times)
                    r = self._references[k]
                    rmax = np.max(np.abs(r))
                    error += np.sqrt(np.sum(((i - r) / rmax) ** 2))
                return error / len(self._voltages)
            except Exception:
                return float('inf')
        self._score = score

        # Give a hint
        self._hint = [0.03, 0.05]

    def test_cmaes(self):
        """
        Tests if a CMA-ES routine runs without errors.
        """
        # NOT RUN AT THE MOMENT
        # CMA-ES changes matplotlib behaviour (not super important here),
        # produces a bunch or warnings, and takes too long
        try:
            import cma
            del(cma)
        except ImportError:
            raise ImportError('Unable to load cma module for cma-es test.')
        with np.errstate(all='ignore'):  # Tell numpy not to issue warnings
            x, f = fit.cmaes(
                self._score, self._boundaries, hint=self._hint, parallel=False,
                target=0.5)

    def test_pso(self):
        """
        Tests if a PSO routine runs without errors.
        """
        with np.errstate(all='ignore'):  # Tell numpy not to issue warnings
            x, f = fit.pso(
                self._score, self._boundaries, hints=[self._hint],
                parallel=False, max_iter=50)

    def test_snes(self):
        """
        Tests if a SNES routine runs without errors.
        """
        with np.errstate(all='ignore'):  # Tell numpy not to issue warnings
            x, f = fit.snes(
                self._score, self._boundaries, hint=self._hint, parallel=False,
                max_iter=50)

    def test_xnes(self):
        """
        Tests if a xNES routine runs without errors.
        """
        with np.errstate(all='ignore'):  # Tell numpy not to issue warnings
            x, f = fit.xnes(
                self._score, self._boundaries, hint=self._hint, parallel=False,
                max_iter=50)
