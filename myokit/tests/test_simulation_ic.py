#!/usr/bin/env python3
#
# Tests the ICSimulation class.
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

from myokit.tests import DIR_DATA, CancellingReporter, WarningCollector

# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp


class ICSimulationTest(unittest.TestCase):
    """
    Tests the :class:`ICSimulation`.
    """
    def test_basic(self):
        # Test basic usage.
        # Load model
        m, p, _ = myokit.load(os.path.join(DIR_DATA, 'lr-1991.mmt'))
        n = m.count_states()

        # Run a simulation
        with WarningCollector() as c:
            s = myokit.ICSimulation(m, p)
        self.assertIn('`ICSimulation` is deprecated', c.text())

        self.assertEqual(s.time(), 0)
        self.assertEqual(s.state(), m.state())
        self.assertEqual(s.default_state(), m.state())
        self.assertTrue(np.all(s.derivatives() == np.eye(n)))
        d, e = s.run(20, log_interval=5)
        self.assertEqual(s.time(), 20)
        self.assertNotEqual(s.state(), m.state())
        self.assertEqual(s.default_state(), m.state())
        self.assertFalse(np.all(s.derivatives() == np.eye(n)))

        # Create a datablock from the simulation log
        b = s.block(d, e)

        # Calculate eigenvalues
        b.eigenvalues('derivatives')

        # Log with missing time value
        d2 = d.clone()
        del d2['engine.time']
        self.assertRaisesRegex(ValueError, 'time', s.block, d2, e)

        # Wrong size derivatives array
        self.assertRaisesRegex(ValueError, 'shape', s.block, d, e[:-1])

        # Time can't be negative
        self.assertRaises(ValueError, s.run, -1)

        # Test running without a protocol
        s.set_protocol(None)
        s.run(1)

        # Test step size is > 0
        self.assertRaises(ValueError, s.set_step_size, 0)

        # Test negative log interval is ignored
        s.run(1, log_interval=-1)

    def test_progress_reporter(self):
        # Test running with a progress reporter.
        m, p, x = myokit.load(os.path.join(DIR_DATA, 'lr-1991.mmt'))

        # Test using a progress reporter
        with WarningCollector() as c:
            s = myokit.ICSimulation(m, p)
        with myokit.tools.capture() as c:
            s.run(110, progress=myokit.ProgressPrinter())
        c = c.text().splitlines()
        self.assertTrue(len(c) > 0)

        # Not a progress reporter
        self.assertRaisesRegex(
            ValueError, 'ProgressReporter', s.run, 5, progress=12)

        # Cancel from reporter
        self.assertRaises(
            myokit.SimulationCancelledError, s.run, 1,
            progress=CancellingReporter(0))

    def test_invalid_model(self):
        # Test running with an invalid model.
        m = myokit.Model()
        with WarningCollector() as c:
            self.assertRaises(
                myokit.MissingTimeVariableError, myokit.ICSimulation, m)


if __name__ == '__main__':
    unittest.main()
