#!/usr/bin/env python3
#
# Tests the PSimulation class.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import os
import unittest

import myokit
import numpy as np

from myokit.tests import DIR_DATA, CancellingReporter, WarningCollector

# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp


class PSimulationTest(unittest.TestCase):
    """
    Tests the PSimulation.
    """
    def test_simple(self):

        # Load model
        m = os.path.join(DIR_DATA, 'lr-1991.mmt')
        m, p, x = myokit.load(m)

        # Create simulation
        with WarningCollector() as c:
            s = myokit.PSimulation(
                m, p, variables=['membrane.V'],
                parameters=['ina.gNa', 'ica.gCa'])
        self.assertIn('`PSimulation` is deprecated', c.text())

        # Test state & default state
        self.assertEqual(s.state(), s.default_state())

        # Test derivatives method
        dp = s.derivatives()
        self.assertEqual(dp.shape, (8, 2))
        self.assertTrue(np.all(dp == 0))

        # Run a tiny simulation
        self.assertEqual(s.time(), 0)
        s.set_step_size(0.002)
        d, dp = s.run(10, log_interval=2)
        self.assertEqual(s.time(), 10)

        # Test derivatives method
        dp = s.derivatives()
        self.assertEqual(dp.shape, (8, 2))
        self.assertFalse(np.all(dp == 0))

        # Test state & default state before & after reset
        self.assertNotEqual(s.state(), s.default_state())
        s.reset()
        self.assertEqual(s.state(), s.default_state())
        self.assertEqual(s.time(), 0)

        # Test derivatives method after reset
        dp = s.derivatives()
        self.assertEqual(dp.shape, (8, 2))
        self.assertTrue(np.all(dp == 0))

        # Test pre-pacing --> Not implemented!
        #s.pre(2)
        #self.assertEqual(s.state(), s.default_state())

        # Create without variables or parameters
        with WarningCollector() as c:
            self.assertRaisesRegex(
                ValueError, 'variables', myokit.PSimulation, m, p,
                parameters=['ina.gNa'])
            self.assertRaisesRegex(
                ValueError, 'parameters', myokit.PSimulation, m, p,
                variables=['membrane.V'])

        # Run without validated model
        m2 = m.clone()
        m2.add_component('bert')
        with WarningCollector() as c:
            s = myokit.PSimulation(
                m2, p, variables=['membrane.V'],
                parameters=['ina.gNa', 'ica.gCa'])
        s.set_step_size(0.002)
        d, dp = s.run(10, log_interval=2)

        # Variable or parameter given twice
        with WarningCollector() as c:
            self.assertRaisesRegex(
                ValueError, 'Duplicate variable', myokit.PSimulation, m, p,
                variables=['membrane.V', 'membrane.V'], parameters=['ina.gNa'])
            self.assertRaisesRegex(
                ValueError, 'Duplicate parameter', myokit.PSimulation, m, p,
                variables=['membrane.V'], parameters=['ina.gNa', 'ina.gNa'])

            # Bound variable or parameter
            self.assertRaisesRegex(
                ValueError, 'bound', myokit.PSimulation, m, p,
                variables=['engine.pace'], parameters=['ina.gNa'])
            self.assertRaisesRegex(
                ValueError, 'bound', myokit.PSimulation, m, p,
                variables=['membrane.V'], parameters=['engine.pace'])

            # Constant variable
            self.assertRaisesRegex(
                ValueError, 'constant', myokit.PSimulation, m, p,
                variables=['ica.gCa'], parameters=['ina.gNa'])

            # Non-constant parameter
            self.assertRaisesRegex(
                ValueError, 'literal constant', myokit.PSimulation, m, p,
                variables=['membrane.V'], parameters=['cell.RTF'])

            # Variables given as objects
            myokit.PSimulation(
                m, p, variables=[m.get('membrane.V')],
                parameters=[m.get('ina.gNa')])

        # Negative times
        self.assertRaisesRegex(
            ValueError, 'negative', s.run, -1)

        # Negative or zero step size
        self.assertRaisesRegex(
            ValueError, 'zero', s.set_step_size, 0)
        self.assertRaisesRegex(
            ValueError, 'zero', s.set_step_size, -1)

        # Set unset protocol
        s.set_protocol(None)
        s.set_protocol(p)

    def test_block(self):
        # Test :meth:`PSimulation.block()`.

        m, p, x = myokit.load(os.path.join(DIR_DATA, 'lr-1991.mmt'))
        with WarningCollector() as c:
            s = myokit.PSimulation(
                m, p, variables=['membrane.V'],
                parameters=['ina.gNa', 'ica.gCa'])
        s.set_step_size(0.002)
        d, dp = s.run(10, log_interval=2)

        b = s.block(d, dp)
        self.assertIsInstance(b, myokit.DataBlock2d)
        self.assertEqual(b.len0d(), len(d) - 1)
        self.assertTrue(np.all(b.time() == d.time()))

        # Log without time
        e = myokit.DataLog(d)
        del e[e.time_key()]
        self.assertRaisesRegex(ValueError, 'must contain', s.block, e, dp)

        # Wrong size derivatives array
        self.assertRaisesRegex(ValueError, 'shape', s.block, d, dp[:, :-1])

    def test_set_constant(self):
        # Test :meth:`PSimulation.set_constant()` and
        # :meth:`PSimulation.set_parameters()`

        m, p, x = myokit.load(os.path.join(DIR_DATA, 'lr-1991.mmt'))
        with WarningCollector() as c:
            s = myokit.PSimulation(
                m, p, variables=['membrane.V'], parameters=['ina.gNa'])
        s.set_constant('ica.gCa', 1)
        s.set_constant(m.get('ica.gCa'), 1)

        # Variable is not a literal
        self.assertRaisesRegex(
            ValueError, 'literal', s.set_constant, 'membrane.V', 1)

        # Variable is in parameters list
        self.assertRaisesRegex(
            ValueError, 'parameter', s.set_constant, 'ina.gNa', 1)

        # Set parameter values
        s.set_parameters([1])
        self.assertRaisesRegex(
            ValueError, '1 values', s.set_parameters, [1, 2])
        s.set_parameters({'ina.gNa': 1})
        s.set_parameters({m.get('ina.gNa'): 1})
        self.assertRaisesRegex(
            ValueError, 'Unknown', s.set_parameters, {'bert': 2})
        self.assertRaisesRegex(
            ValueError, 'parameter', s.set_parameters, {'ica.gCa': 2})

    def test_progress_reporter(self):
        # Test running with a progress reporter.

        m, p, x = myokit.load(os.path.join(DIR_DATA, 'lr-1991.mmt'))
        with WarningCollector() as c:
            s = myokit.PSimulation(
                m, p, variables=['membrane.V'], parameters=['ina.gNa'])
        with myokit.tools.capture() as c:
            s.run(2, progress=myokit.ProgressPrinter())
        c = c.text().splitlines()
        self.assertEqual(len(c), 2)
        self.assertEqual(
            c[0], '[0.0 minutes] 50.0 % done, estimated 0 seconds remaining')
        self.assertEqual(
            c[1], '[0.0 minutes] 100.0 % done, estimated 0 seconds remaining')

        # Not a progress reporter
        self.assertRaisesRegex(
            ValueError, 'ProgressReporter', s.run, 1, progress=12)

        # Cancel from reporter
        self.assertRaises(
            myokit.SimulationCancelledError, s.run, 1,
            progress=CancellingReporter(0))


if __name__ == '__main__':
    unittest.main()
