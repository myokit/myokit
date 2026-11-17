#!/usr/bin/env python3
#
# Tests the myokit.gui.vargrapher module.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import unittest

import numpy as np

import myokit
from myokit.tests import qt_application


class GuiVarGrapherTest(unittest.TestCase):
    """
    Tests the ``VarGrapher`` dialog.
    """

    @classmethod
    def setUpClass(cls):
        cls.app = qt_application()
        import myokit.gui.vargrapher
        cls.VarGrapher = myokit.gui.vargrapher.VarGrapher
        cls.model, _, _ = myokit.load('example')

    def setUp(self):
        self.graphers = []

    def tearDown(self):
        for g in self.graphers:
            g.close()
            g.deleteLater()

    def grapher(self, var):
        # Creates a grapher for the given variable
        var = self.model.get(var) if isinstance(var, str) else var
        f, a = var.pyfunc(arguments=True)
        g = self.VarGrapher(None, 'Graph', var, f, a)
        self.graphers.append(g)
        return g

    def bounds(self, g):
        # Returns the bounds as a dict of tuples of strings
        return {
            str(k): (v[0].text(), v[1].text()) for k, v in g._bounds.items()}

    def test_one_argument(self):
        # Test graphing a function of one variable
        g = self.grapher('ik1.IK1')
        self.assertEqual(g.windowTitle(), 'Graph')

        # Bounds guessed for membrane potential
        self.assertEqual(
            self.bounds(g), {'membrane.V': ('-100.0', '100.0')})

        # A 2d plot is created
        self.assertEqual(len(g._figure.axes), 1)
        ax = g._figure.axes[0]
        self.assertEqual(ax.name, 'rectilinear')
        self.assertEqual(len(ax.lines), 1)
        x, y = ax.lines[0].get_data()
        self.assertEqual(len(x), 10000)
        self.assertEqual(x[0], -100)
        self.assertEqual(x[-1], 100)
        self.assertEqual(ax.get_xlabel(), 'membrane.V [mV]')
        self.assertEqual(ax.get_ylabel(), 'ik1.IK1 [uA/cm^2]')

        # Values are calculated with the variable's function
        f = self.model.get('ik1.IK1').pyfunc()
        self.assertTrue(np.allclose(y, f(x), equal_nan=True))

        # Change and swap the bounds and redraw
        lo, hi = g._bounds[next(iter(g._bounds))]
        lo.setText('20')
        hi.setText('-10')
        g.action_draw()
        self.assertEqual(len(g._figure.axes), 1)
        x, y = g._figure.axes[0].lines[0].get_data()
        self.assertEqual(x[0], -10)
        self.assertEqual(x[-1], 20)

        # Equal bounds: graph of a single point
        lo.setText('5')
        hi.setText('5')
        g.action_draw()
        x, y = g._figure.axes[0].lines[0].get_data()
        self.assertEqual(list(x), [5])

    def test_bounds(self):
        # Test guessing of bounds

        # Value between 0 and 1, unitless
        g = self.grapher('ica.E')
        self.assertEqual(self.bounds(g), {'ica.Ca_i': ('0.0', '1.0')})
        self.assertEqual(
            g._figure.axes[0].get_xlabel(), 'ica.Ca_i [mM]')

        # No units
        g = self.grapher('membrane.i_stim')
        self.assertEqual(self.bounds(g), {'engine.pace': ('0.0', '1.0')})
        self.assertEqual(g._figure.axes[0].get_xlabel(), 'engine.pace')

        # Voltage in V, negative values, values greater than 1
        m = myokit.parse_model('''
            [[model]]
            c.V = -0.08
            c.a = -3
            c.b = 5
            c.c = 2

            [engine]
            time = 0 bind time

            [c]
            dot(V) = 0
                in [V]
            dot(a) = 0
            dot(b) = 0
            dot(c) = 0
            y = V + a + b + c
            z = b
        ''')
        g = self.grapher(m.get('c.y'))
        self.assertEqual(self.bounds(g), {
            'c.V': ('-0.1', '0.1'),
            'c.a': ('-50', '50'),
            'c.b': ('50.0', '50.0'),
            'c.c': ('50.0', '50.0'),
        })
        g = self.grapher(m.get('c.z'))
        self.assertEqual(self.bounds(g), {'c.b': ('0', '100')})

    def test_more_arguments(self):
        # Test graphing a function of more than one variable

        # Two variables: both have editable bounds
        g = self.grapher('ik.IK')
        b = self.bounds(g)
        self.assertEqual(b['membrane.V'], ('-100.0', '100.0'))
        self.assertEqual(b['ik.x'], ('0.0', '1.0'))
        for lo, hi in g._bounds.values():
            self.assertFalse(lo.isReadOnly())
            self.assertFalse(hi.isReadOnly())

        # A 3d plot is created
        self.assertEqual(len(g._figure.axes), 1)
        ax = g._figure.axes[0]
        self.assertEqual(ax.name, '3d')
        self.assertEqual(ax.get_xlabel(), 'membrane.V [mV]')
        self.assertEqual(ax.get_ylabel(), 'ik.x')
        self.assertEqual(ax.get_zlabel(), 'ik.IK [uA/cm^2]')

        # Four variables: last two are fixed
        g = self.grapher('ina.INa')
        b = self.bounds(g)
        self.assertEqual(len(b), 4)
        fixed = [
            v for v in g._bounds.values() if v[0] is v[1]]
        self.assertEqual(len(fixed), 2)
        for edit, _ in fixed:
            self.assertTrue(edit.isReadOnly())
            self.assertEqual(edit.text(), '0.5')
        self.assertEqual(g._figure.axes[0].name, '3d')

        # Redraw
        g.action_draw()
        self.assertEqual(len(g._figure.axes), 1)

    def test_constant(self):
        # Constants cannot be graphed
        self.assertRaisesRegex(
            Exception, 'Cannot graph constant', self.grapher, 'ina.gNa')

    def test_close(self):
        # Test closing with the close button
        g = self.grapher('ik1.IK1')
        g.show()
        self.assertTrue(g.isVisible())
        from myokit.gui import QtWidgets
        buttons = g._button_widget.findChildren(QtWidgets.QPushButton)
        self.assertEqual(
            [b.text() for b in buttons], ['Refresh', 'Close'])
        close = [b for b in buttons if b.text() == 'Close']
        self.assertEqual(len(close), 1)
        close[0].click()
        self.assertFalse(g.isVisible())


if __name__ == '__main__':
    unittest.main()
