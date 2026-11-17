#!/usr/bin/env python3
#
# Tests the myokit.gui.explorer module.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import io
import unittest
import unittest.mock

import myokit
from myokit.tests import qt_application


class GuiExplorerTest(unittest.TestCase):
    """
    Tests the ``Explorer`` dialog.
    """

    @classmethod
    def setUpClass(cls):
        cls.app = qt_application()
        import myokit.gui.explorer
        cls.Explorer = myokit.gui.explorer.Explorer
        cls.model, cls.protocol, _ = myokit.load('example')

    def setUp(self):
        self.calls = 0
        self.stream = io.StringIO()
        self.explorer = self.Explorer(
            None, self.sim_method, self.stream, duration=50)

    def tearDown(self):
        self.explorer.close()
        self.explorer.deleteLater()

    def sim_method(self):
        # Returns a model, protocol, and simulation
        self.calls += 1
        s = myokit.Simulation(self.model, self.protocol)
        return self.model, self.protocol, s

    def test_construction(self):
        # Test the initial state of the explorer
        e = self.explorer
        self.assertEqual(e.windowTitle(), 'Myokit Explorer')
        self.assertEqual(e._pre_field.text(), '0')
        self.assertEqual(e._run_field.text(), '50')
        self.assertIsNone(e._data)
        self.assertIsNone(e._keys)
        self.assertEqual(e._select_x.count(), 0)
        self.assertEqual(e._select_y.count(), 0)

        # Default duration
        e2 = self.Explorer(None, self.sim_method, self.stream)
        self.assertEqual(e2._run_field.text(), '1000')
        e2.close()
        e2.deleteLater()

        # Drawing without data clears the figure
        e.action_draw()
        self.assertEqual(len(e._figure.axes), 0)

    def test_run_and_clear(self):
        # Test running simulations and clearing the data
        e = self.explorer
        e.action_run()
        self.assertEqual(self.calls, 1)
        self.assertEqual(len(e._data), 1)
        self.assertIn('Final state:', self.stream.getvalue())
        self.assertIn('membrane.V', self.stream.getvalue())

        # Keys are set, and time and the first logged variable are selected
        keys = set(e._data[0].keys())
        self.assertEqual(e._keys, keys)
        self.assertEqual(e._select_x.count(), len(keys))
        self.assertEqual(
            [e._select_x.itemText(i) for i in range(e._select_x.count())],
            sorted(keys))
        self.assertEqual(e._select_x.currentText(), 'engine.time')
        self.assertIn(e._select_y.currentText(), keys)
        self.assertEqual(e._data[0]['engine.time'][-1], 50)

        # One line is drawn
        self.assertEqual(len(e._figure.axes), 1)
        self.assertEqual(len(e._axes.lines), 1)

        # Running again adds data, keeps the selection, and draws both lines
        e._select_y.setCurrentIndex(e._select_y.findText('membrane.V'))
        e._pre_field.setText('10')
        e._run_field.setText('20')
        e.action_run()
        self.assertEqual(self.calls, 2)
        self.assertEqual(len(e._data), 2)
        self.assertEqual(e._select_x.currentText(), 'engine.time')
        self.assertEqual(e._select_y.currentText(), 'membrane.V')
        self.assertEqual(len(e._axes.lines), 2)

        # Redrawing doesn't add any lines
        e.action_draw()
        self.assertEqual(len(e._axes.lines), 2)
        # Note: pre-pacing changes the state, but not the time
        self.assertEqual(e._data[1]['engine.time'][0], 0)
        self.assertEqual(e._data[1]['engine.time'][-1], 20)
        self.assertNotEqual(
            e._data[0]['membrane.V'][0], e._data[1]['membrane.V'][0])

        # Changing the selection redraws all data on new axes
        e._select_x.setCurrentIndex(e._select_x.findText('membrane.V'))
        self.assertEqual(len(e._figure.axes), 1)
        self.assertEqual(len(e._axes.lines), 2)

        # Clearing removes the data but keeps the keys
        e.action_clear()
        self.assertIsNone(e._data)
        self.assertEqual(e._keys, keys)
        self.assertEqual(len(e._figure.axes), 0)

        # Changing the selection without data does nothing
        e._select_x.setCurrentIndex(0)
        self.assertEqual(len(e._figure.axes), 0)

        # Running after clearing starts from scratch
        e.action_run()
        self.assertEqual(len(e._data), 1)
        self.assertEqual(len(e._axes.lines), 1)

    def test_changing_keys(self):
        # Test running a simulation that logs different variables

        model = myokit.parse_model('''
            [[model]]
            c.x = 0

            [engine]
            time = 0 bind time

            [c]
            dot(x) = 1
        ''')

        def sim_method():
            return model, self.protocol, myokit.Simulation(model)

        e = self.explorer
        e.action_run()
        self.assertIn('ina.m.alpha', e._keys)
        e._select_y.setCurrentIndex(e._select_y.findText('ina.m.alpha'))

        # New keys: data is replaced, selection is reset if needed
        e._sim_method = sim_method
        e.action_run()
        self.assertEqual(len(e._data), 1)
        self.assertEqual(e._keys, {'engine.time', 'c.x', 'dot(c.x)'})
        self.assertEqual(e._select_x.count(), 3)
        self.assertEqual(e._select_x.currentText(), 'engine.time')
        self.assertIn(e._select_y.currentText(), e._keys)
        self.assertNotEqual(e._select_y.currentText(), 'ina.m.alpha')
        self.assertEqual(len(e._axes.lines), 1)

    def test_errors(self):
        # Test handling of errors and cancellation
        e = self.explorer

        # Simulation method returns a message
        e._sim_method = lambda: 'Something is wrong'
        e.action_run()
        self.assertEqual(self.stream.getvalue(), 'Something is wrong')
        self.assertIsNone(e._data)

        # Simulation method raises a MyokitError
        def raise_myokit():
            raise myokit.IncompatibleModelError('m', 'Bad model')

        self.stream.seek(0)
        self.stream.truncate()
        e._sim_method = raise_myokit
        e.action_run()
        self.assertIn('Bad model', self.stream.getvalue())
        self.assertIsNone(e._data)

        # Simulation method raises another exception
        def raise_other():
            raise ValueError('Bad value')

        self.stream.seek(0)
        self.stream.truncate()
        e._sim_method = raise_other
        e.action_run()
        self.assertEqual(self.stream.getvalue(), 'Bad value')
        self.assertIsNone(e._data)

        # Simulation is cancelled
        self.stream.seek(0)
        self.stream.truncate()
        e._sim_method = self.sim_method
        with unittest.mock.patch(
                'myokit.gui.progress.ProgressBar.wasCanceled',
                return_value=True):
            e.action_run()
        self.assertEqual(self.stream.getvalue(), '')
        self.assertIsNone(e._data)

    def test_close(self):
        # Test closing the explorer
        e = self.explorer
        e.show()
        self.assertTrue(e.isVisible())
        e._close_button.click()
        self.assertFalse(e.isVisible())


if __name__ == '__main__':
    unittest.main()
