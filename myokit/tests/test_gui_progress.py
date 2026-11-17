#!/usr/bin/env python3
#
# Tests the myokit.gui.progress module.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import unittest
import unittest.mock

import myokit
from myokit.tests import qt_application


class GuiProgressTest(unittest.TestCase):
    """
    Tests the ``ProgressBar`` and ``ProgressBarReporter`` classes.
    """

    @classmethod
    def setUpClass(cls):
        cls.app = qt_application()
        import myokit.gui.progress
        cls.progress = myokit.gui.progress

    def setUp(self):
        self.bar = self.progress.ProgressBar(None, 'Working')

    def tearDown(self):
        self.bar.close()
        self.bar.deleteLater()

    def test_progress_bar(self):
        # Test the progress bar dialog
        bar = self.bar
        self.assertEqual(bar.labelText(), 'Working')
        self.assertEqual(bar.minimum(), 0)
        self.assertEqual(bar.maximum(), self.progress.N)
        self.assertFalse(bar.autoClose())
        self.assertFalse(bar.autoReset())
        self.assertFalse(bar.was_cancelled())
        bar.cancel()
        self.assertTrue(bar.was_cancelled())

        # Reporter is created once
        r = bar.reporter()
        self.assertIsInstance(r, self.progress.ProgressBarReporter)
        self.assertIsInstance(r, myokit.ProgressReporter)
        self.assertIs(bar.reporter(), r)

    def test_reporter(self):
        # Test the progress bar reporter
        bar = self.bar
        r = bar.reporter()

        # Enter with and without message
        r.enter('Running simulation')
        self.assertTrue(bar.isEnabled())
        self.assertEqual(bar.labelText(), 'Running simulation')
        self.assertEqual(bar.value(), 0)
        r.enter()
        self.assertEqual(bar.labelText(), 'Running simulation')

        # Update
        self.assertTrue(r.update(0.5))
        self.assertEqual(bar.value(), self.progress.N // 2)
        self.assertTrue(r.update(1))
        self.assertEqual(bar.value(), self.progress.N)

        # Exit
        r.exit()
        self.assertFalse(bar.isEnabled())

        # Cancelling
        with r.job('Again'):
            self.assertTrue(bar.isEnabled())
            self.assertTrue(r.update(0.1))
            bar.cancel()
            self.assertFalse(r.update(0.2))
        self.assertFalse(bar.isEnabled())

        # Re-entering resets the cancelled state
        r.enter()
        self.assertTrue(r.update(0.3))
        r.exit()

    def test_simulation(self):
        # Test using the reporter in a simulation
        m, p, _ = myokit.load('example')
        s = myokit.Simulation(m, p)
        r = self.bar.reporter()
        d = s.run(100, progress=r, log=['engine.time'])
        self.assertEqual(d['engine.time'][-1], 100)
        self.assertEqual(self.bar.value(), self.progress.N)
        self.assertEqual(self.bar.labelText(), 'Running simulation')
        self.assertFalse(self.bar.isEnabled())

        # Cancelling before a run has no effect, as enter() resets the bar
        s.reset()
        self.bar.cancel()
        s.run(10, progress=r)

        # Cancel during a simulation
        s.reset()
        with unittest.mock.patch.object(
                self.bar, 'wasCanceled', return_value=True):
            self.assertRaises(
                myokit.SimulationCancelledError, s.run, 100, progress=r)


if __name__ == '__main__':
    unittest.main()
