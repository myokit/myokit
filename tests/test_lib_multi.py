#!/usr/bin/env python
#
# Tests the myokit.lib.multi module.
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

import myokit
import myokit.lib.multi as multi

from shared import DIR_DATA

DIR_MULTI = os.path.join(DIR_DATA, 'multi')


class LibMultiTest(unittest.TestCase):
    """
    Tests the myokit.lib.multi module.
    """

    def test_iterdir(self):
        """
        Tests the iterdir() method that iterators over model, protocol tuples.
        """

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
        self.assertRaises(ValueError, next, i)
        try:
            next(multi.iterdir(path))
        except ValueError as e:
            self.assertIn('not a directory', str(e))

    def test_scandir(self):
        """
        Tests the scandir() method that returns a models list and a protocols
        list.
        """

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
        """
        Tests the time() method that returns the time variable.
        """
        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        x.set_rhs(0)

        self.assertRaises(myokit.IncompatibleModelError, multi.time, m)
        x.set_binding('time')
        self.assertEqual(x, multi.time(m))

    def test_label(self):
        """
        Tests the label() method that returns a labelled variable.
        """
        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        x.set_rhs(0)

        self.assertRaises(myokit.IncompatibleModelError, multi.label, m, 'x')
        x.set_label('x')
        self.assertEqual(x, multi.label(m, 'x'))

    def test_binding(self):
        """
        Tests the binding() method that returns a bound variable.
        """
        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        x.set_rhs(0)

        self.assertRaises(myokit.IncompatibleModelError, multi.binding, m, 'x')
        x.set_binding('x')
        self.assertEqual(x, multi.binding(m, 'x'))

    def test_unit(self):
        """
        Tests the unit() method that returns a unit conversion factor.
        """
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
