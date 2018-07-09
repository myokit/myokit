#!/usr/bin/env python
#
# Tests the importers for various formats
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

from shared import DIR_DATA


class ImporterTest(unittest.TestCase):
    """ Tests shared importer functionality. """

    def test_importer_interface(self):
        """ Tests listing and creating importers. """
        ims = myokit.formats.importers()
        self.assertTrue(len(ims) > 0)
        for i in ims:
            self.assertIn(type(i), [str, unicode])
            i = myokit.formats.importer(i)
            self.assertTrue(isinstance(i, myokit.formats.Importer))

    def test_unknown(self):
        """ Tests requesting an unknown importer. """
        # Test fetching using importer method
        self.assertRaisesRegexp(
            KeyError, 'Importer not found', myokit.formats.importer, 'blip')


class CellMLTest(unittest.TestCase):
    """ Tests the CellML importer. """

    def test_capability_reporting(self):
        """ Tests if the right capabilities are reported. """
        i = formats.importer('cellml')
        self.assertFalse(i.supports_component())
        self.assertTrue(i.supports_model())
        self.assertFalse(i.supports_protocol())

    def test_model_simple(self):
        # Beeler-Reuter is a simple model
        i = formats.importer('cellml')
        self.assertTrue(i.supports_model())
        m = i.model(os.path.join(DIR_DATA, 'br-1977.cellml'))
        m.validate()

    def test_model_dot(self):
        # This is beeler-reuter but with a dot() in an expression
        i = formats.importer('cellml')
        self.assertTrue(i.supports_model())
        m = i.model(os.path.join(DIR_DATA, 'br-1977-dot.cellml'))
        m.validate()

    def test_model_nesting(self):
        # The corrias model has multiple levels of nesting (encapsulation)
        i = formats.importer('cellml')
        self.assertTrue(i.supports_model())
        m = i.model(os.path.join(DIR_DATA, 'corrias.cellml'))
        m.validate()

    def test_info(self):
        i = formats.importer('cellml')
        self.assertIn(type(i.info()), [str, unicode])


class SBMLTest(unittest.TestCase):
    """ Tests SBML import. """

    def test_capability_reporting(self):
        """ Tests if the right capabilities are reported. """
        i = formats.importer('sbml')
        self.assertFalse(i.supports_component())
        self.assertTrue(i.supports_model())
        self.assertFalse(i.supports_protocol())

    def test_model(self):
        i = formats.importer('sbml')
        self.assertTrue(i.supports_model())
        m = i.model(os.path.join(DIR_DATA, 'HodgkinHuxley.xml'))
        try:
            m.validate()
        except myokit.MissingTimeVariableError:
            # SBML models don't specify the time variable
            pass

    def test_info(self):
        i = formats.importer('sbml')
        self.assertIn(type(i.info()), [str, unicode])


class ChannelMLTest(unittest.TestCase):
    """ Tests ChannelML importing. """

    def test_capability_reporting(self):
        """ Tests if the right capabilities are reported. """
        i = formats.importer('channelml')
        self.assertTrue(i.supports_component())
        self.assertTrue(i.supports_model())
        self.assertFalse(i.supports_protocol())

    def test_model(self):
        i = formats.importer('channelml')
        self.assertTrue(i.supports_model())
        m = i.model(os.path.join(DIR_DATA, '43.channelml'))
        m.validate()

    def test_component(self):
        path = os.path.join(DIR_DATA, '43.channelml')
        i = formats.importer('channelml')
        self.assertTrue(i.supports_component())
        m = myokit.Model()
        c = m.add_component('membrane')
        v = c.add_variable('V')
        self.assertRaises(myokit.ImportError, i.component, path, m)
        v.set_label('membrane_potential')
        i.component(path, m)
        cs = [c for c in m.components()]
        self.assertEqual(len(cs), 2)

    def test_info(self):
        i = formats.importer('channelml')
        self.assertIn(type(i.info()), [str, unicode])


class AxonTest(unittest.TestCase):
    """ Partially tests Axon formats importing. """

    def test_capability_reporting(self):
        """ Tests if the right capabilities are reported. """
        i = formats.importer('abf')
        self.assertFalse(i.supports_component())
        self.assertFalse(i.supports_model())
        self.assertTrue(i.supports_protocol())

    def test_protocol(self):
        i = formats.importer('abf')
        self.assertTrue(i.supports_protocol())
        i.protocol(os.path.join(DIR_DATA, 'abf-v1.abf'))

    def test_info(self):
        i = formats.importer('abf')
        self.assertIn(type(i.info()), [str, unicode])


if __name__ == '__main__':
    unittest.main()
