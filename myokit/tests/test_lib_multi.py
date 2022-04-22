#!/usr/bin/env python3
#
# Tests the myokit.lib.multi module.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import os
import unittest

import myokit

from myokit.tests import DIR_DATA, WarningCollector

# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp

# Path to multi-model testing files
DIR_MULTI = os.path.join(DIR_DATA, 'multi')


class LibMultiTest(unittest.TestCase):
    """
    Tests the myokit.lib.multi module.
    """

    def test_iterdir(self):
        # Test the iterdir() method that iterators over model, protocol tuples.

        with WarningCollector():
            import myokit.lib.multi as multi

        # Get all found tuples (model, protocol)
        tuples = [x for x in multi.iterdir(DIR_MULTI)]
        self.assertEqual(len(tuples), 2)

        # Should contain (ordered by filename)
        #  (Beeler (no name), None)
        #  (Lr1991, protocol)
        #
        self.assertEqual(type(tuples[0][0]), myokit.Model)
        self.assertEqual(tuples[0][0].name(), 'beeler-no-name')
        self.assertIsNone(tuples[0][1], None)
        self.assertEqual(type(tuples[1][0]), myokit.Model)
        self.assertEqual(tuples[1][0].name(), 'Luo-Rudy model (1991)')
        self.assertEqual(type(tuples[1][1]), myokit.Protocol)

        # Test without name setting
        tuples = [x for x in multi.iterdir(DIR_MULTI, False)]
        self.assertEqual(len(tuples), 2)
        self.assertEqual(type(tuples[0][0]), myokit.Model)
        self.assertIsNone(tuples[0][0].name())
        self.assertIsNone(tuples[0][1], None)
        self.assertEqual(type(tuples[1][0]), myokit.Model)
        self.assertEqual(tuples[1][0].name(), 'Luo-Rudy model (1991)')
        self.assertEqual(type(tuples[1][1]), myokit.Protocol)

        # Path must be a directory
        path = os.path.join(DIR_MULTI, 'lr-1991.mmt')
        i = multi.iterdir(path)
        self.assertRaisesRegex(ValueError, 'not a directory', next, i)

    def test_scandir(self):
        # Test the scandir() method that returns a models list and a protocols
        # list.

        with WarningCollector():
            import myokit.lib.multi as multi

        # Get list of models and protocols
        models, protocols = multi.scandir(DIR_MULTI)
        self.assertEqual(len(models), len(protocols), 2)

        # Should contain (ordered by model name)
        #  (Lr1991, protocol) --> Upper case goes first
        #  (Beeler (no name), None)
        #
        self.assertEqual(type(models[0]), myokit.Model)
        self.assertEqual(type(models[1]), myokit.Model)
        self.assertEqual(models[0].name(), 'Luo-Rudy model (1991)')
        self.assertEqual(models[1].name(), 'beeler-no-name')
        self.assertEqual(type(protocols[0]), myokit.Protocol)
        self.assertIsNone(protocols[1])

    def test_time(self):
        # Test the time() method that returns the time variable.

        with WarningCollector():
            import myokit.lib.multi as multi

        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        x.set_rhs(0)

        with WarningCollector() as w:
            self.assertRaises(myokit.IncompatibleModelError, multi.time, m)
            x.set_binding('time')
            self.assertEqual(x, multi.time(m))
        self.assertIn('deprecated', w.text())

    def test_label(self):
        # Test the label() method that returns a labelled variable.

        with WarningCollector():
            import myokit.lib.multi as multi

        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        x.set_rhs(0)

        with WarningCollector() as w:
            self.assertRaises(
                myokit.IncompatibleModelError, multi.label, m, 'x')
            x.set_label('x')
            self.assertEqual(x, multi.label(m, 'x'))
        self.assertIn('deprecated', w.text())

    def test_binding(self):
        # Test the binding() method that returns a bound variable.

        with WarningCollector():
            import myokit.lib.multi as multi

        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        x.set_rhs(0)

        with WarningCollector() as w:
            self.assertRaises(
                myokit.IncompatibleModelError, multi.binding, m, 'x')
            x.set_binding('x')
            self.assertEqual(x, multi.binding(m, 'x'))
        self.assertIn('deprecated', w.text())

    def test_unit(self):
        # Test the unit() method that returns a unit conversion factor.

        with WarningCollector():
            import myokit.lib.multi as multi

        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        x.set_rhs(0)
        x.set_unit(myokit.parse_unit('mV'))

        self.assertRaises(
            myokit.IncompatibleModelError, multi.unit, x,
            myokit.parse_unit('kg'))
        self.assertEqual(multi.unit(x, myokit.parse_unit('V')), 0.001)
        self.assertEqual(multi.unit(x, myokit.parse_unit('mV')), 1)
        self.assertEqual(multi.unit(x, myokit.parse_unit('uV')), 1000)


if __name__ == '__main__':
    unittest.main()
