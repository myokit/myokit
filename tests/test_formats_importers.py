#!/usr/bin/env python
#
# Tests the importers for various formats
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
import os
import unittest

import myokit
import myokit.formats as formats

from shared import DIR_DATA


class CellMLTest(unittest.TestCase):
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


class SBMLTest(unittest.TestCase):
    def test_model(self):
        i = formats.importer('sbml')
        self.assertTrue(i.supports_model())
        m = i.model(os.path.join(DIR_DATA, 'HodgkinHuxley.xml'))
        try:
            m.validate()
        except myokit.MissingTimeVariableError:
            # SBML models don't specify the time variable
            pass


class ChannelMLTest(unittest.TestCase):
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


class AxonTest(unittest.TestCase):
    def test_protocol(self):
        i = formats.importer('abf')
        self.assertTrue(i.supports_protocol())
        i.protocol(os.path.join(DIR_DATA, 'proto.abf'))


if __name__ == '__main__':
    unittest.main()
