#!/usr/bin/env python
#
# Tests the exporters from the format module.
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
import myokit.formats as formats

from shared import TemporaryDirectory, DIR_DATA


class ExportTest(unittest.TestCase):

    def go(self, exporter):
        """
        Test the export functions for a given exporter type.
        """
        # Load model, protocol
        m, p, x = myokit.load('example')

        # Get exporter
        e = formats.exporter(exporter)

        # Create empty output directory as subdirectory of DIR_OUT
        with TemporaryDirectory() as d:
            path = d.path()

            # Try exports
            exports = 0

            # Try model export
            if e.supports_model():
                exports += 1
                fpath = os.path.join(path, 'model.txt')
                ret = e.model(fpath, m)
                self.assertIsNone(ret)
                self.assertTrue(os.path.isfile(fpath))
            else:
                self.assertRaises(NotImplementedError, e.model, path, m)

            # Try runnable export
            if e.supports_runnable():
                exports += 1
                # Check without protocol
                dpath = os.path.join(path, 'runnable1')
                ret = e.runnable(dpath, m)
                self.assertIsNone(ret)
                self.assertTrue(os.path.isdir(dpath))
                self.assertTrue(len(os.listdir(dpath)) > 0)
                # Check with protocol
                dpath = os.path.join(path, 'runnable2')
                ret = e.runnable(dpath, m, p)
                self.assertIsNone(ret)
                self.assertTrue(os.path.isdir(dpath))
                self.assertTrue(len(os.listdir(dpath)) > 0)
            else:
                self.assertRaises(NotImplementedError, e.runnable, path, m, p)

            # Test if any exports were available
            if exports == 0:
                raise Exception(
                    'No types of export supported by: ' + exporter)

    def test_exporters(self):
        for name in myokit.formats.exporters():
            try:
                self.go(name)
            except myokit.ExportError as e:
                raise Exception(
                    'Exporter error for ' + name + ': ' + e.message)


class SympyTest(unittest.TestCase):
    def test_expression(self):
        from myokit.formats import sympy
        m = myokit.load_model(
            os.path.join(DIR_DATA, 'heijman-2011.mmt'))
        for v in m.variables(deep=True):
            e = v.rhs()
            e = sympy.write(e)
            e = sympy.read(e)


if __name__ == '__main__':
    unittest.main()
