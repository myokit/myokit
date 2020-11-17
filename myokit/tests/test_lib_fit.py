#!/usr/bin/env python3
#
# Tests the classes in myokit.lib.fit
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import os
import unittest
import numpy as np

import myokit
import myokit.lib.markov as markov

from shared import DIR_DATA, WarningCollector

# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp


class EvaluatorTest(unittest.TestCase):
    """
    Tests the sequential and parallel evaluation classes.
    """

    def test_evaluators(self):

        with WarningCollector():
            import myokit.lib.fit as fit

        # Test basic sequential/parallel evaluation
        x = 1 + np.random.random(100)

        # Simple run: sequential and parallel
        fit.evaluate(f, x, parallel=False)

        # Note: the overhead is almost 100% of the run-time of this test
        fit.evaluate(f, x, parallel=True)

        e = fit.SequentialEvaluator(f_args, [10, 20])
        self.assertEqual(e.evaluate([1])[0], 1)

        # Argument must be callable
        self.assertRaises(ValueError, fit.SequentialEvaluator, 1)

        # Args must be a sequence
        self.assertRaises(ValueError, fit.SequentialEvaluator, f_args, 1)

    def test_parallel_evaluator(self):

        with WarningCollector():
            import myokit.lib.fit as fit

        # Test parallel execution
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

        e = fit.ParallelEvaluator(f_args, args=[10, 20])
        self.assertEqual(e.evaluate([1])[0], 1)

        # Argument must be callable
        self.assertRaises(ValueError, fit.ParallelEvaluator, 1)

        # Args must be a sequence
        self.assertRaises(ValueError, fit.ParallelEvaluator, f_args, args=1)

        # n-workers must be >0
        self.assertRaises(ValueError, fit.ParallelEvaluator, f, 0)

        # max tasks must be >0
        self.assertRaises(ValueError, fit.ParallelEvaluator, f, 1, 0)

        e = fit.ParallelEvaluator(ioerror_on_five)

        self.assertRaisesRegex(
            Exception, 'in subprocess', e.evaluate, range(10))

    def test_parallel_simulations(self):
        # Test running simulations in parallel

        with WarningCollector():
            import myokit.lib.fit as fit

        # Test running simulation defined in object
        s = Sim()
        e = fit.ParallelEvaluator(s.run, nworkers=4)
        e.evaluate([1, 2, 3, 4])

        # Test running simulation created inside of score function
        e = fit.ParallelEvaluator(run_sim, nworkers=4)
        e.evaluate([1, 2, 3, 4])

    def test_worker(self):
        # Manual test of worker, since cover doesn't pick up on its run method.

        with WarningCollector():
            from myokit.lib.fit import _Worker as Worker

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

        w = Worker(h, (), tasks, results, max_tasks, errors, error)
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

        w = Worker(h, (), tasks, results, max_tasks, errors, error)
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

        w = Worker(h, (), tasks, results, max_tasks, errors, error)
        w.run()

        self.assertEqual(results.get(timeout=0.01), (0, 2))
        self.assertTrue(results.empty())
        self.assertTrue(error.is_set())
        #self.assertFalse(errors.empty())
        self.assertIsNotNone(errors.get(timeout=0.01))


class FittingTest(unittest.TestCase):
    """
    Performs very basic tests of fitting methods (e.g., do they run).
    """
    @classmethod
    def setUpClass(cls):
        # Load model, simulation etc. only once
        fname = os.path.join(DIR_DATA, 'clancy-1999-fitting.mmt')
        model = myokit.load_model(fname)

        # Extract the Markov model of INa
        parameters = ['ina.p1', 'ina.p2']
        cls._boundaries = [[1e-3, 10], [1e-3, 10]]
        markov_model = markov.LinearModel.from_component(
            model.get('ina'),
            parameters=parameters,
            current='ina.i',
        )

        # Create an analytical markov model simulation
        cls._sim = markov.AnalyticalSimulation(markov_model)

        # Voltages to test at
        r = 10
        cls._voltages = np.arange(-70, -10 + r, r)

        # Times to evaluate at
        times = np.concatenate((np.linspace(0, 4, 100), np.linspace(4, 8, 20)))

        # Generate reference traces
        cls._references = []
        for v in cls._voltages:
            cls._sim.set_membrane_potential(v)
            x, i = cls._sim.solve(times)
            cls._references.append(i)

        # Give a hint
        # p1 = 0.1027 / 3.802 ~ 0.0270
        # p2 = 0.20 / 3.802 ~ 0.0526
        cls._hint = [0.0269, 0.052]

    @staticmethod
    def _score(guess):
        try:
            error = 0
            cls._sim.set_parameters(guess)
            for k, v in enumerate(cls._voltages):
                cls._sim.set_membrane_potential(v)
                x, i = cls._sim.solve(times)
                r = cls._references[k]
                rmax = np.max(np.abs(r))
                error += np.sqrt(np.sum(((i - r) / rmax) ** 2))
            return error / len(cls._voltages)
        except Exception:
            return float('inf')

    def test_cmaes(self):
        # Test if a CMA-ES routine runs without errors.

        with WarningCollector():
            import myokit.lib.fit as fit

        # Some CMAES versions import matplotlib...
        import matplotlib
        matplotlib.use('template')

        try:
            import cma
            del(cma)
        except ImportError:
            print('CMA module not found, skipping test.')
            return

        np.random.seed(1)
        with np.errstate(all='ignore'):  # Tell numpy not to issue warnings
            x, f = fit.cmaes(
                FittingTest._score, self._boundaries, hint=self._hint,
                parallel=False, target=1)

    def test_pso(self):
        # Test if a PSO routine runs without errors.
        with WarningCollector():
            import myokit.lib.fit as fit

        np.random.seed(1)
        with np.errstate(all='ignore'):  # Tell numpy not to issue warnings
            x, f = fit.pso(
                FittingTest._score, self._boundaries, hints=[self._hint],
                parallel=False, max_iter=50)

    def test_snes(self):
        # Test if a SNES routine runs without errors.
        with WarningCollector():
            import myokit.lib.fit as fit

        np.random.seed(1)
        with np.errstate(all='ignore'):  # Tell numpy not to issue warnings
            x, f = fit.snes(
                FittingTest._score, self._boundaries, hint=self._hint,
                parallel=False, max_iter=50)

    def test_xnes(self):
        # Test if a xNES routine runs without errors.
        with WarningCollector():
            import myokit.lib.fit as fit

        np.random.seed(1)
        with np.errstate(all='ignore'):  # Tell numpy not to issue warnings
            x, f = fit.xnes(
                FittingTest._score, self._boundaries, hint=self._hint,
                parallel=False, max_iter=50)


# Globally defined test functions (for windows)
def f(x):
    if x == 0:
        raise Exception('Everything is terrible')
    return 1 / 1 / 1 / 1 / 1 / 1 / 1 / 1 / 1 / 1 / 1 / 1 / 1 / 1 / x


# Test function with args
def f_args(x, y, z):
    return 1 if (y == 10 and z == 20) else 0


# Exceptions in called method should trigger halt, cause new exception
def ioerror_on_five(x):
    if x == 5:
        raise IOError
    return x


# Test handling of keyboard interrupts
def h(x):
    if x == 30:
        raise KeyboardInterrupt
    return 2 * x


# Run a simulation, created outside of the called method
class Sim(object):
    def __init__(self):
        m, p, _ = myokit.load('example')
        self.s = myokit.Simulation(m, p)

    def run(self, x):
        self.s.run(10)
        return x


# Run a simulation, created inside the called method
def run_sim(x):
    m, p, _ = myokit.load('example')
    s = myokit.Simulation(m, p)
    s.run(10)
    return x


if __name__ == '__main__':
    unittest.main()
