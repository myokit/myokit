#!/usr/bin/env python
#
# Tests the Chaste module.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import unittest

import myokit
import myokit.formats
import myokit.formats.chaste

from shared import TemporaryDirectory

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


class ChasteExporterTest(unittest.TestCase):
    """ Tests Chaste export. """

    def test_chaste_exporter(self):
        # Tests exporting a model

        m, p, _ = myokit.load('example')
        e = myokit.formats.chaste.ChasteExporter()

        with TemporaryDirectory() as d:
            path = d.path('chaste')

            # Test with simple model
            e.runnable(path, m, p)

            # Test with invalid model
            v = m.get('membrane.V')
            v.demote()
            v.set_rhs('2 * V')
            self.assertRaisesRegex(
                myokit.ExportError, 'valid model', e.runnable, path, m, p)

    def test_chaste_exporter_fetching(self):
        # Tests getting an Chaste exporter via the 'exporter' interface

        e = myokit.formats.exporter('chaste')
        self.assertIsInstance(e, myokit.formats.chaste.ChasteExporter)

    def test_chaste_exporter_info(self):
        # Tests the info() method returns a string

        e = myokit.formats.chaste.ChasteExporter()
        self.assertIsInstance(e.info(), basestring)

        # Test support
        self.assertFalse(e.supports_model())
        self.assertTrue(e.supports_runnable())


class ChasteExpressionWriterTest(unittest.TestCase):
    """ Tests Chaste expression writer functionality. """

    def test_chaste_ewriter_fetching(self):

        # Test fetching using ewriter method
        w = myokit.formats.ewriter('chaste')
        self.assertIsInstance(w, myokit.formats.chaste.ChasteExpressionWriter)


if __name__ == '__main__':
    unittest.main()
