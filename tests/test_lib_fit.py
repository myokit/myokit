#!/usr/bin/env python
#
# Tests the classes in myokit.lib.fit
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import os
import unittest
import numpy as np

import myokit
import myokit.lib.fit as fit
import myokit.lib.markov as markov

from shared import DIR_DATA

# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:  # pragma: no cover
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp


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

        # Test object with args
        def g(x, y, z):
            self.assertEqual(y, 10)
            self.assertEqual(z, 20)

        e = fit.SequentialEvaluator(g, [10, 20])
        e.evaluate([1])

        # Argument must be callable
        self.assertRaises(ValueError, fit.SequentialEvaluator, 1)

        # Args must be a sequence
        self.assertRaises(ValueError, fit.SequentialEvaluator, g, 1)

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

        # Test object with args
        def g(x, y, z):
            self.assertEqual(y, 10)
            self.assertEqual(z, 20)

        e = fit.ParallelEvaluator(g, args=[10, 20])
        e.evaluate([1])

        # Argument must be callable
        self.assertRaises(ValueError, fit.ParallelEvaluator, 1)

        # Args must be a sequence
        self.assertRaises(ValueError, fit.ParallelEvaluator, g, args=1)

        # n-workers must be >0
        self.assertRaises(ValueError, fit.ParallelEvaluator, f, 0)

        # max tasks must be >0
        self.assertRaises(ValueError, fit.ParallelEvaluator, f, 1, 0)

        # Exceptions in called method should trigger halt, cause new exception
        def ioerror_on_five(x):
            if x == 5:
                raise IOError
            return x

        e = fit.ParallelEvaluator(ioerror_on_five)

        self.assertRaisesRegex(
            Exception, 'in subprocess', e.evaluate, range(10))

    def test_worker(self):
        """
        Manual test of worker, since cover doesn't pick up on its run method.
        """
        from myokit.lib.fit import _Worker as Worker

        # Define function
        def f(x):
            if x == 30:
                raise KeyboardInterrupt
            return 2 * x

        # Create queues for worker
        import multiprocessing
        tasks = multiprocessing.Queue()
        results = multiprocessing.Queue()
        errors = multiprocessing.Queue()
        error = multiprocessing.Event()
        tasks.put((0, 1))
        tasks.put((1, 2))
        tasks.put((2, 3))
        max_tasks = 3

        w = Worker(f, (), tasks, results, max_tasks, errors, error)
        w.run()

        self.assertEqual(results.get(timeout=0.01), (0, 2))
        self.assertEqual(results.get(timeout=0.01), (1, 4))
        self.assertEqual(results.get(timeout=0.01), (2, 6))
        self.assertTrue(results.empty())

        # Test worker stops if error flag is set
        tasks = multiprocessing.Queue()
        results = multiprocessing.Queue()
        errors = multiprocessing.Queue()
        error = multiprocessing.Event()
        tasks.put((0, 1))
        tasks.put((1, 2))
        tasks.put((2, 3))
        error.set()

        w = Worker(f, (), tasks, results, max_tasks, errors, error)
        w.run()

        self.assertEqual(results.get(timeout=0.01), (0, 2))
        self.assertTrue(results.empty())

        # Tests worker catches, stores and halts on exception
        tasks = multiprocessing.Queue()
        results = multiprocessing.Queue()
        errors = multiprocessing.Queue()
        error = multiprocessing.Event()
        tasks.put((0, 1))
        tasks.put((1, 30))
        tasks.put((2, 3))

        w = Worker(f, (), tasks, results, max_tasks, errors, error)
        w.run()

        self.assertEqual(results.get(timeout=0.01), (0, 2))
        self.assertTrue(results.empty())
        self.assertTrue(error.is_set())
        #self.assertFalse(errors.empty())
        self.assertIsNotNone(errors.get(timeout=0.01))


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
        fname = os.path.join(DIR_DATA, 'clancy-1999-fitting.mmt')
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
        # p1 = 0.1027 / 3.802 ~ 0.0270
        # p2 = 0.20 / 3.802 ~ 0.0526
        self._hint = [0.0269, 0.052]

    def test_cmaes(self):
        """
        Tests if a CMA-ES routine runs without errors.
        """
        try:
            import cma
            del(cma)
        except ImportError:
            print('CMA module not found, skipping test.')
            return

        np.random.seed(1)
        with np.errstate(all='ignore'):  # Tell numpy not to issue warnings
            x, f = fit.cmaes(
                self._score, self._boundaries, hint=self._hint, parallel=False,
                target=1)

    def test_pso(self):
        """
        Tests if a PSO routine runs without errors.
        """
        np.random.seed(1)
        with np.errstate(all='ignore'):  # Tell numpy not to issue warnings
            x, f = fit.pso(
                self._score, self._boundaries, hints=[self._hint],
                parallel=False, max_iter=50)

    def test_snes(self):
        """
        Tests if a SNES routine runs without errors.
        """
        np.random.seed(1)
        with np.errstate(all='ignore'):  # Tell numpy not to issue warnings
            x, f = fit.snes(
                self._score, self._boundaries, hint=self._hint, parallel=False,
                max_iter=50)

    def test_xnes(self):
        """
        Tests if a xNES routine runs without errors.
        """
        np.random.seed(1)
        with np.errstate(all='ignore'):  # Tell numpy not to issue warnings
            x, f = fit.xnes(
                self._score, self._boundaries, hint=self._hint, parallel=False,
                max_iter=50)


if __name__ == '__main__':
    unittest.main()
