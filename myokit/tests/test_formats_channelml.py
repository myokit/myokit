#!/usr/bin/env python3
#
# Tests the importers for various formats
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
import myokit.formats.channelml

from myokit.tests import DIR_FORMATS, WarningCollector

# ChannelML dir
DIR = os.path.join(DIR_FORMATS, 'channelml')

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


class ChannelMLTest(unittest.TestCase):
    """ Test ChannelML importing. """

    def test_capability_reporting(self):
        # Test if the right capabilities are reported.
        i = myokit.formats.importer('channelml')
        self.assertTrue(i.supports_component())
        self.assertTrue(i.supports_model())
        self.assertFalse(i.supports_protocol())

    def test_model(self):
        # Test :meth:`ChannelMLImporter.model()`.
        i = myokit.formats.importer('channelml')
        self.assertTrue(i.supports_model())
        m = i.model(os.path.join(DIR, 'ch-00-valid-file.channelml'))
        m.validate()

    def test_component(self):
        # Test :meth:`ChannelMLImporter.component()`.
        path = os.path.join(DIR, 'ch-00-valid-file.channelml')
        i = myokit.formats.importer('channelml')
        self.assertTrue(i.supports_component())
        m = myokit.Model()
        c = m.add_component('membrane')
        v = c.add_variable('V')
        self.assertRaises(myokit.ImportError, i.component, path, m)
        v.set_label('membrane_potential')
        i.component(path, m)
        cs = [c for c in m.components()]
        self.assertEqual(len(cs), 2)

    def test_error_handling(self):
        # Test various errors when loading ChannelML files.

        i = myokit.formats.importer('channelml')
        ce = myokit.formats.channelml.ChannelMLError

        # Wrong XML root element
        self.assertRaisesRegex(
            ce, 'Unknown root', i.model,
            os.path.join(DIR, 'ch-01-wrong-root.channelml'))

        # No channel_type element
        self.assertRaisesRegex(
            ce, 'No <channel_type>', i.model,
            os.path.join(DIR, 'ch-02-no-channel-type.channelml'))

        # Test name adaptation when it overlaps with names already in the model
        m = i.model(
            os.path.join(DIR, 'ch-03-overlapping-name.channelml'))
        m.validate()
        self.assertIn('membrane_2', m)  # Renamed channel membrane > membrane_2

        # No current_voltage_relation element
        self.assertRaisesRegex(
            ce, 'current voltage relation', i.model,
            os.path.join(DIR, 'ch-04-no-cvr.channelml'))

        # Multiple current_voltage_relation elements
        with WarningCollector() as w:
            m = i.model(os.path.join(DIR, 'ch-05-two-cvrs.channelml'))
        m.validate()
        self.assertEqual(w.count(), 1)
        self.assertIn('Multiple current voltage relations', w.text())

        # No q10 information
        m = i.model(os.path.join(DIR, 'ch-06-no-q10.channelml'))
        m.validate()

        # Not exactly 2 transitions
        self.assertRaisesRegex(
            ce, 'exactly 2 transitions', i.model,
            os.path.join(DIR, 'ch-07-three-transitions.channelml'))

        # Not closed-to-open transition
        self.assertRaisesRegex(
            ce, 'closed-to-open', i.model,
            os.path.join(DIR, 'ch-08-no-closed-to-open.channelml'))

        # Not open-to-closed transition
        self.assertRaisesRegex(
            ce, 'open-to-closed', i.model,
            os.path.join(DIR, 'ch-09-no-open-to-closed.channelml'))

        # Unreadable closed-to-open expression
        with WarningCollector() as w:
            m = i.model(
                os.path.join(DIR, 'ch-10-tco-bad-expression.channelml'))

        # > RHS Should not be set
        self.assertRaises(myokit.MissingRhsError, m.validate)

        # > Warning should be generated
        self.assertEqual(w.count(), 1)
        self.assertIn('expression for closed-to-open', w.text())

        # > Unparsed expression should be in meta-data
        self.assertEqual('bort', m.get('Nav1_3.m.alpha').meta['expression'])

        # Unreadable open-to-closed expression
        with WarningCollector() as w:
            m = i.model(
                os.path.join(DIR, 'ch-11-toc-bad-expression.channelml'))
        self.assertRaises(myokit.MissingRhsError, m.validate)
        self.assertEqual(w.count(), 1)
        self.assertIn('expression for open-to-closed', w.text())
        self.assertEqual('bort', m.get('Nav1_3.m.beta').meta['expression'])

        # No transitions or steady-state/time-course for a gate
        self.assertRaisesRegex(
            ce, 'steady state', i.model,
            os.path.join(DIR, 'ch-12-no-steady-state.channelml'))
        self.assertRaisesRegex(
            ce, 'time course', i.model,
            os.path.join(DIR, 'ch-13-no-time-course.channelml'))

        # Unreadable steady-state expression
        with WarningCollector() as w:
            m = i.model(
                os.path.join(DIR, 'ch-14-inf-bad-expression.channelml'))
        self.assertRaises(myokit.MissingRhsError, m.validate)
        self.assertEqual(w.count(), 1)
        self.assertIn('expression for steady state', w.text())
        self.assertEqual('mill', m.get('Nav1_3.h.inf').meta['expression'])

        # Unreadable time-constant expression
        with WarningCollector() as w:
            m = i.model(
                os.path.join(DIR, 'ch-15-tau-bad-expression.channelml'))
        self.assertRaises(myokit.MissingRhsError, m.validate)
        self.assertEqual(w.count(), 1)
        self.assertIn('expression for time course', w.text())
        self.assertEqual('house', m.get('Nav1_3.h.tau').meta['expression'])

        # No gates
        self.assertRaisesRegex(
            ce, 'at least one gate', i.model,
            os.path.join(DIR, 'ch-16-no-gates.channelml'))

        # Invalid name
        with WarningCollector() as w:
            m = i.model(
                os.path.join(DIR, 'ch-17-invalid-name.channelml'))
        m.validate()
        self.assertEqual(w.count(), 1)
        self.assertIn('Invalid name', w.text())

    def test_c_style_if(self):
        # Test parsing of a c-style cond?then:else expression.

        # If-then-else
        i = myokit.formats.importer('channelml')
        m = i.model(
            os.path.join(DIR, 'ch-18-c-style-if.channelml'))
        self.assertEqual(
            str(m.get('Nav1_3.m.alpha').rhs()),
            'if(membrane.v != -26, 12, 13)'
        )

        # If-then
        self.assertEqual(
            str(m.get('Nav1_3.m.beta').rhs()),
            'if(membrane.v != -26, 100, 0)'
        )


if __name__ == '__main__':
    unittest.main()
