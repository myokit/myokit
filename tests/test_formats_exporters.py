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
import myokit.formats

from shared import TemporaryDirectory


class ExportTest(unittest.TestCase):

    def _test(self, e):
        """
        Test a given exporter `e`.
        """
        # Test info method.
        self.assertIn(type(e.info()), [str, unicode])

        # Load model, protocol
        m, p, x = myokit.load('example')

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

    def test_ansic_exporter(self):
        self._test(myokit.formats.exporter('ansic'))

    def test_ansic_cable_exporter(self):
        self._test(myokit.formats.exporter('ansic-cable'))

    def test_ansic_euler_exporter(self):
        self._test(myokit.formats.exporter('ansic-euler'))

    def test_cellml_exporter(self):
        self._test(myokit.formats.exporter('cellml'))

    def test_cuda_kernel_exporter(self):
        self._test(myokit.formats.exporter('cuda-kernel'))

    def test_latex_article_exporter(self):
        self._test(myokit.formats.exporter('latex-article'))

    def test_latex_poster_exporter(self):
        self._test(myokit.formats.exporter('latex-poster'))

    def test_html_exporter(self):
        self._test(myokit.formats.exporter('html'))

    def test_xml_exporter(self):
        self._test(myokit.formats.exporter('xml'))

    def test_matlab_exporter(self):
        self._test(myokit.formats.exporter('matlab'))

    def test_opencl_exporter(self):
        self._test(myokit.formats.exporter('opencl'))

    def test_python_exporter(self):
        self._test(myokit.formats.exporter('python'))

    def test_stan_exporter(self):
        self._test(myokit.formats.exporter('stan'))

    def test_completeness(self):
        """
        Tests that all exporters have a test (so meta!).
        """
        methods = [x for x in dir(self) if x[:5] == 'test_']
        for name in myokit.formats.exporters():
            name = name.replace('-', '_')
            name = 'test_' + name + '_exporter'
            self.assertIn(name, methods)

    def test_unknown_exporter(self):
        """
        Tests the error handling for requesting an unknown exporter.
        """
        self.assertRaisesRegexp(
            KeyError, 'Exporter not found', myokit.formats.exporter, 'elvish')


if __name__ == '__main__':
    unittest.main()
