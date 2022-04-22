#!/usr/bin/env python3
#
# Tests the exporters from the format module.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import os
import unittest

import myokit
import myokit.formats

from myokit.tests import TemporaryDirectory

# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:  # pragma: no python 3 cover
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp

# Strings in Python 2 and 3
try:
    basestring
except NameError:   # pragma: no python 2 cover
    basestring = str


class ExportTest(unittest.TestCase):
    """
    Tests various exporters.
    """

    def _test(self, e, model=None, protocol=None):
        """ Test a given exporter `e`. """

        # Test info method.
        self.assertIsInstance(e.post_export_info(), basestring)

        # Load model, protocol
        m, p = model, protocol
        if m is None:
            m = myokit.load_model('example')
        if p is None:
            p = myokit.load_protocol('example')

        with TemporaryDirectory() as d:
            path = d.path()

            # Try exports
            exports = 0

            # Try model export
            if e.supports_model():
                exports += 1

                # Basic export
                fpath = os.path.join(path, 'model.txt')
                ret = e.model(fpath, m)
                self.assertIsNone(ret)
                self.assertTrue(os.path.isfile(fpath))

                # Unnamed model
                name = m.name()
                try:
                    m.set_name(None)
                    ret = e.model(fpath, m)
                    self.assertIsNone(ret)
                    self.assertTrue(os.path.isfile(fpath))
                finally:
                    m.set_name(name)

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

                # Write to complex path
                dpath = os.path.join(path, 'runnable3', 'nest', 'test')
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

    def test_runnable_exporter_shared(self):
        # Test shared functionality of the TemplatedRunnableExporters.

        e = myokit.formats.exporter('ansic')

        # Load model, protocol
        m, p, x = myokit.load('example')

        # Create empty output directory as subdirectory of DIR_OUT
        with TemporaryDirectory() as d:
            path = d.path()

            # Simple export
            dpath = os.path.join(path, 'runnable1')
            ret = e.runnable(dpath, m)
            self.assertIsNone(ret)
            self.assertTrue(os.path.isdir(dpath))
            self.assertTrue(len(os.listdir(dpath)) > 0)

            # Write to complex path
            dpath = os.path.join(path, 'runnable2', 'nest', 'test')
            ret = e.runnable(dpath, m, p)
            self.assertIsNone(ret)
            self.assertTrue(os.path.isdir(dpath))
            self.assertTrue(len(os.listdir(dpath)) > 0)

            # Overwrite existing path
            ret = e.runnable(dpath, m, p)
            self.assertIsNone(ret)
            self.assertTrue(os.path.isdir(dpath))
            self.assertTrue(len(os.listdir(dpath)) > 0)

            # Path pointing to file
            dpath = os.path.join(path, 'file')
            with open(dpath, 'w') as f:
                f.write('contents\n')
            self.assertRaisesRegex(
                myokit.ExportError, 'file exists', e.runnable, dpath, m, p)

            # Directory exists where we're trying to write a file
            dpath = os.path.join(path, 'runnable3')
            fname = os.path.join(dpath, 'sim.c')
            os.makedirs(fname)
            self.assertRaisesRegex(
                myokit.ExportError, 'Directory exists',
                e.runnable, dpath, m, p)

            # Directory embedded in the output file path
            def embedded():
                return {'sim.c': 'nested/sim.c'}

            # 1. Normal operation
            e._dict = embedded
            dpath = os.path.join(path, 'runnable4')
            ret = e.runnable(dpath, m, p)
            self.assertIsNone(ret)
            self.assertTrue(os.path.isdir(dpath))
            self.assertTrue(len(os.listdir(dpath)) > 0)

            # 2. Try to create directory where file exists
            def embedded():
                return {'sim.c': 'nested/sim.c/som.c'}

            e._dict = embedded
            dpath = os.path.join(path, 'runnable4')
            self.assertRaisesRegex(
                myokit.ExportError, 'file or link', e.runnable, dpath, m, p)

    def test_completeness(self):
        # Test that all exporters have a test (so meta!).

        methods = [x for x in dir(self) if x[:5] == 'test_']
        for name in myokit.formats.exporters():
            name = name.replace('-', '_')
            name = 'test_' + name + '_exporter'
            self.assertIn(name, methods)

    def test_ansic_exporter(self):
        self._test(myokit.formats.exporter('ansic'))

    def test_ansic_cable_exporter(self):
        self._test(myokit.formats.exporter('ansic-cable'))

    def test_ansic_euler_exporter(self):
        self._test(myokit.formats.exporter('ansic-euler'))

    def test_cellml_exporter(self):
        self._test(myokit.formats.exporter('cellml'))

    def test_cellml1_exporter(self):
        self._test(myokit.formats.exporter('cellml1'))

    def test_cellml2_exporter(self):
        self._test(myokit.formats.exporter('cellml2'))

    def test_cuda_kernel_exporter(self):
        self._test(myokit.formats.exporter('cuda-kernel'))

    def test_cuda_kernel_rl_exporter(self):
        self._test(myokit.formats.exporter('cuda-kernel-rl'))

    def test_easyml_exporter(self):
        self._test(myokit.formats.exporter('easyml'))

    def test_html_exporter(self):
        self._test(myokit.formats.exporter('html'))

    def test_latex_article_exporter(self):
        self._test(myokit.formats.exporter('latex-article'))

    def test_latex_poster_exporter(self):
        self._test(myokit.formats.exporter('latex-poster'))

    def test_matlab_exporter(self):
        self._test(myokit.formats.exporter('matlab'))

    def test_opencl_exporter(self):
        self._test(myokit.formats.exporter('opencl'))

    def test_opencl_rl_exporter(self):
        self._test(myokit.formats.exporter('opencl-rl'))

    def test_opencl_exporter_errors(self):
        # Checks the errors raised by the OpenCL exporter.
        e = myokit.formats.exporter('opencl')

        # Label membrane_potential must be set
        m = myokit.load_model('example')
        m.label('membrane_potential').set_label(None)
        self.assertRaisesRegex(
            ValueError, 'membrane_potential', self._test, e, m)

        # Binding diffusion_current must be set
        m = myokit.load_model('example')
        m.binding('diffusion_current').set_binding(None)
        self.assertRaisesRegex(
            ValueError, 'diffusion_current', self._test, e, m)

    def test_python_exporter(self):
        self._test(myokit.formats.exporter('python'))

    def test_stan_exporter(self):
        # Basic test
        self._test(myokit.formats.exporter('stan'))

        # Test with parameters and output variable specified

        # Load model
        m = myokit.load_model('example')

        # Guess parameters
        parameters = []
        for v in m.get('ina').variables(const=True):
            if v.name()[:1] == 'p':
                parameters.append(v)
        parameters.sort(key=lambda v: myokit.tools.natural_sort_key(v.name()))

        # Set output
        output = 'ina.INa'

        # Export to stan
        e = myokit.formats.stan.StanExporter()
        with TemporaryDirectory() as d:
            dpath = d.path('out')
            ret = e.runnable(dpath, m, parameters=parameters, output=output)
            self.assertIsNone(ret)
            self.assertTrue(os.path.isdir(dpath))
            self.assertTrue(len(os.listdir(dpath)) > 0)

    def test_unknown_exporter(self):
        # Test the error handling for requesting an unknown exporter.
        self.assertRaisesRegex(
            KeyError, 'Exporter not found', myokit.formats.exporter, 'elvish')

    def test_xml_exporter(self):
        self._test(myokit.formats.exporter('xml'))


if __name__ == '__main__':
    unittest.main()
