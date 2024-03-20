#!/usr/bin/env python3
#
# Tests shared infrastructure in myokit.formats.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import os
import unittest

import myokit
import myokit.formats

from myokit.tests import TemporaryDirectory


class FormatsTest(unittest.TestCase):
    """ Test shared formats functionality. """

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
    """ Tests shared :class:`Exporter` functionality. """

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

    def test_runnable_exporter(self):
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


class ImporterTest(unittest.TestCase):
    """ Test shared importer functionality. """

    def test_importer_interface(self):
        # Test listing and creating importers.
        ims = myokit.formats.importers()
        self.assertTrue(len(ims) > 0)
        for i in ims:
            self.assertIsInstance(i, str)
            i = myokit.formats.importer(i)
            self.assertTrue(isinstance(i, myokit.formats.Importer))

    def test_unknown(self):
        # Test requesting an unknown importer.
        # Test fetching using importer method
        self.assertRaisesRegex(
            KeyError, 'Importer not found', myokit.formats.importer, 'blip')


class EWriterTest(unittest.TestCase):
    """ Test shared ewriter functionality. """

    def test_ewriter_interface(self):
        # Test listing and creating expression writers.

        # Test listing
        es = myokit.formats.ewriters()
        self.assertTrue(len(es) > 0)

        # Create one of each
        for e in es:
            self.assertIsInstance(e, str)
            e = myokit.formats.ewriter(e)
            self.assertTrue(isinstance(e, myokit.formats.ExpressionWriter))

    def test_unknown(self):
        # Test requesting an unknown expression writer.
        # Test fetching using ewriter method
        self.assertRaisesRegex(
            KeyError, 'Expression writer not found', myokit.formats.ewriter,
            'dada')


if __name__ == '__main__':
    unittest.main()
