#!/usr/bin/env python3
#
# Tests shared infrastructure in myokit.formats.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import unittest

import myokit
import myokit.formats

from myokit.tests import TemporaryDirectory

# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp


class FormatsTest(unittest.TestCase):
    """
    Test infrastructure from the formats module.
    """

    def test_register_external_importer(self):
        # Tests registering an external importer.

        class TestImporter(myokit.formats.Importer):
            pass

        self.assertRaisesRegex(
            KeyError, 'Importer not found',
            myokit.formats.importer, 'testo')

        myokit.formats.register_external_importer('testo', TestImporter)
        e = myokit.formats.importer('testo')
        self.assertIsInstance(e, TestImporter)
        e = myokit.formats.importer('testo')
        self.assertIsInstance(e, TestImporter)

        # Test overwriting
        myokit.formats.register_external_importer('testo', TestImporter)
        e = myokit.formats.importer('testo')
        self.assertIsInstance(e, TestImporter)

        # Test removing
        myokit.formats.register_external_importer('testo', None)
        self.assertRaisesRegex(
            KeyError, 'Importer not found',
            myokit.formats.importer, 'testo')

    def test_register_external_exporter(self):
        # Tests registering an external exporter.

        class TestExporter(myokit.formats.Exporter):
            pass

        self.assertRaisesRegex(
            KeyError, 'Exporter not found',
            myokit.formats.exporter, 'testo')

        myokit.formats.register_external_exporter('testo', TestExporter)
        e = myokit.formats.exporter('testo')
        self.assertIsInstance(e, TestExporter)
        e = myokit.formats.exporter('testo')
        self.assertIsInstance(e, TestExporter)

        # Test overwriting
        myokit.formats.register_external_exporter('testo', TestExporter)
        e = myokit.formats.exporter('testo')
        self.assertIsInstance(e, TestExporter)

        # Test removing
        myokit.formats.register_external_exporter('testo', None)
        self.assertRaisesRegex(
            KeyError, 'Exporter not found',
            myokit.formats.exporter, 'testo')

    def test_register_external_ewriter(self):
        # Tests registering an external expression writer.

        class TestExpressionWriter(myokit.formats.ExpressionWriter):
            pass

        self.assertRaisesRegex(
            KeyError, 'Expression writer not found',
            myokit.formats.ewriter, 'testo')

        myokit.formats.register_external_ewriter('testo', TestExpressionWriter)
        e = myokit.formats.ewriter('testo')
        self.assertIsInstance(e, TestExpressionWriter)
        e = myokit.formats.ewriter('testo')
        self.assertIsInstance(e, TestExpressionWriter)

        # Test overwriting
        myokit.formats.register_external_ewriter('testo', TestExpressionWriter)
        e = myokit.formats.ewriter('testo')
        self.assertIsInstance(e, TestExpressionWriter)

        # Test removing
        myokit.formats.register_external_ewriter('testo', None)
        self.assertRaisesRegex(
            KeyError, 'Expression writer not found',
            myokit.formats.ewriter, 'testo')


class ExporterTest(unittest.TestCase):
    """
    Tests some parts of :class:`Exporter` that are not tested when testing the
    various exporter implementations.
    """
    def test_writable_dir(self):
        # Test :meth:`_test_writable_dir` for existing paths.

        m, p, x = myokit.load('example')
        e = myokit.formats.exporter('ansic')
        with TemporaryDirectory() as d:

            # Create in new dir
            path = d.path('new-dir')
            e.runnable(path, m, p)

            # Create again, in same dir (should be ok)
            e.runnable(path, m, p)

            # Create at location of file: not allowed!
            path = d.path('file')
            with open(path, 'w') as f:
                f.write('Hello')
            self.assertRaisesRegex(
                myokit.ExportError, 'file exists', e.runnable, path, m, p)


if __name__ == '__main__':
    unittest.main()
