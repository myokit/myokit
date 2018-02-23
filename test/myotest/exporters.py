#!/usr/bin/env python2
#
# Tests the i/o facilities
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
import os
import shutil
import unittest
import myokit
import myokit.formats as formats
import myotest


def suite():
    """
    Returns a test suite with all tests in this module
    """
    suite = unittest.TestSuite()
    suite.addTest(SympyTest('expression'))
    for name in myokit.formats.exporters():
        class C(ExportTest):
            pass
        C._exporter = name
        suite.addTest(C('test'))
    return suite


class ExportTest(unittest.TestCase):
    _exporter = ''

    def __init__(self, name):
        super(ExportTest, self).__init__(name)

    def test(self):
        """
        Test the export functions for this exporter type.
        """
        # Load model, protocol
        m, p, x = myokit.load('example')
        # Get exporter
        e = formats.exporter(self._exporter)
        # Ok? Then update class name for nice error message (!)
        self.__class__.__name__ = 'ExportTest' + e.__class__.__name__
        # Create empty output directory as subdirectory of DIR_OUT
        path = os.path.join(myotest.DIR_OUT, self._exporter)
        if os.path.exists(path):
            shutil.rmtree(path)
        os.makedirs(path)
        try:
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
                    'No types of export supported by: ' + self._exporter)
        finally:
            if os.path.exists(path) and os.path.isdir(path):
                if not myotest.DEBUG:
                    shutil.rmtree(path)


class SympyTest(unittest.TestCase):
    def expression(self):
        from myokit.formats import sympy
        m = myokit.load_model(
            os.path.join(myotest.DIR_DATA, 'heijman-2011.mmt'))
        for v in m.variables(deep=True):
            e = v.rhs()
            e = sympy.write(e)
            e = sympy.read(e)
