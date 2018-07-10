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
import myokit.formats
import myokit.formats.channelml

from shared import DIR_FORMATS


class ChannelMLTest(unittest.TestCase):
    """ Tests ChannelML importing. """

    def test_capability_reporting(self):
        """ Tests if the right capabilities are reported. """
        i = myokit.formats.importer('channelml')
        self.assertTrue(i.supports_component())
        self.assertTrue(i.supports_model())
        self.assertFalse(i.supports_protocol())

    def test_model(self):
        """ Tests :meth:`ChannelMLImporter.model()`. """
        i = myokit.formats.importer('channelml')
        self.assertTrue(i.supports_model())
        m = i.model(os.path.join(DIR_FORMATS, 'ch-00-valid-file.channelml'))
        m.validate()

    def test_component(self):
        """ Tests :meth:`ChannelMLImporter.component()`. """
        path = os.path.join(DIR_FORMATS, 'ch-00-valid-file.channelml')
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

    def test_info(self):
        """ Tests :meth:`ChannelMLImporter.info()`. """
        i = myokit.formats.importer('channelml')
        self.assertIn(type(i.info()), [str, unicode])

    def test_error_handling(self):
        """
        Tests various errors when loading ChannelML files.
        """
        i = myokit.formats.importer('channelml')
        ce = myokit.formats.channelml.ChannelMLError

        # Wrong XML root element
        self.assertRaisesRegexp(
            ce, 'Unknown root', i.model,
            os.path.join(DIR_FORMATS, 'ch-01-wrong-root.channelml'))

        # No channel_type element
        self.assertRaisesRegexp(
            ce, 'No <channel_type>', i.model,
            os.path.join(DIR_FORMATS, 'ch-02-no-channel-type.channelml'))

        # Test name adaptation when it overlaps with names already in the model
        m = i.model(
            os.path.join(DIR_FORMATS, 'ch-03-overlapping-name.channelml'))
        m.validate()
        self.assertIn('membrane_2', m)  # Renamed channel membrane > membrane_2

        # No current_voltage_relation element
        self.assertRaisesRegexp(
            ce, 'current voltage relation', i.model,
            os.path.join(DIR_FORMATS, 'ch-04-no-cvr.channelml'))

        # Multiple current_voltage_relation elements
        i.logger().clear_warnings()
        self.assertEqual(len(list(i.logger().warnings())), 0)
        m = i.model(os.path.join(DIR_FORMATS, 'ch-05-two-cvrs.channelml'))
        m.validate()
        warnings = list(i.logger().warnings())
        self.assertEqual(len(warnings), 1)
        self.assertIn('Multiple current voltage relations', warnings[0])

        # No q10 information
        m = i.model(os.path.join(DIR_FORMATS, 'ch-06-no-q10.channelml'))
        m.validate()

        # Not exactly 2 transitions
        self.assertRaisesRegexp(
            ce, 'exactly 2 transitions', i.model,
            os.path.join(DIR_FORMATS, 'ch-07-three-transitions.channelml'))

        # Not closed-to-open transition
        self.assertRaisesRegexp(
            ce, 'closed-to-open', i.model,
            os.path.join(DIR_FORMATS, 'ch-08-no-closed-to-open.channelml'))

        # Not open-to-closed transition
        self.assertRaisesRegexp(
            ce, 'open-to-closed', i.model,
            os.path.join(DIR_FORMATS, 'ch-09-no-open-to-closed.channelml'))

        # Unreadable closed-to-open expression
        i.logger().clear_warnings()
        self.assertEqual(len(list(i.logger().warnings())), 0)
        m = i.model(
            os.path.join(DIR_FORMATS, 'ch-10-tco-bad-expression.channelml'))

        # > RHS Should not be set
        self.assertRaises(myokit.MissingRhsError, m.validate)

        # > Warning should be generated
        warnings = list(i.logger().warnings())
        self.assertEqual(len(warnings), 1)
        self.assertIn('expression for closed-to-open', warnings[0])

        # > Unparsed expression should be in meta-data
        self.assertEquals('bort', m.get('Nav1_3.m.alpha').meta['expression'])

        # Unreadable open-to-closed expression
        i.logger().clear_warnings()
        self.assertEqual(len(list(i.logger().warnings())), 0)
        m = i.model(
            os.path.join(DIR_FORMATS, 'ch-11-toc-bad-expression.channelml'))
        self.assertRaises(myokit.MissingRhsError, m.validate)
        warnings = list(i.logger().warnings())
        self.assertEqual(len(warnings), 1)
        self.assertIn('expression for open-to-closed', warnings[0])
        self.assertEquals('bort', m.get('Nav1_3.m.beta').meta['expression'])

        # No transitions or steady-state/time-course for a gate
        self.assertRaisesRegexp(
            ce, 'steady state', i.model,
            os.path.join(DIR_FORMATS, 'ch-12-no-steady-state.channelml'))
        self.assertRaisesRegexp(
            ce, 'time course', i.model,
            os.path.join(DIR_FORMATS, 'ch-13-no-time-course.channelml'))

        # Unreadable steady-state expression
        i.logger().clear_warnings()
        self.assertEqual(len(list(i.logger().warnings())), 0)
        m = i.model(
            os.path.join(DIR_FORMATS, 'ch-14-inf-bad-expression.channelml'))
        self.assertRaises(myokit.MissingRhsError, m.validate)
        warnings = list(i.logger().warnings())
        self.assertEqual(len(warnings), 1)
        self.assertIn('expression for steady state', warnings[0])
        self.assertEquals('mill', m.get('Nav1_3.h.inf').meta['expression'])

        # Unreadable time-constant expression
        i.logger().clear_warnings()
        self.assertEqual(len(list(i.logger().warnings())), 0)
        m = i.model(
            os.path.join(DIR_FORMATS, 'ch-15-tau-bad-expression.channelml'))
        self.assertRaises(myokit.MissingRhsError, m.validate)
        warnings = list(i.logger().warnings())
        self.assertEqual(len(warnings), 1)
        self.assertIn('expression for time course', warnings[0])
        self.assertEquals('house', m.get('Nav1_3.h.tau').meta['expression'])

        # No gates
        self.assertRaisesRegexp(
            ce, 'at least one gate', i.model,
            os.path.join(DIR_FORMATS, 'ch-16-no-gates.channelml'))

        # Invalid name
        i.logger().clear_warnings()
        self.assertEqual(len(list(i.logger().warnings())), 0)
        m = i.model(
            os.path.join(DIR_FORMATS, 'ch-17-invalid-name.channelml'))
        m.validate()
        warnings = list(i.logger().warnings())
        self.assertEqual(len(warnings), 1)
        self.assertIn('Invalid name', warnings[0])

    def test_c_style_if(self):
        """ Tests parsing of a c-style cond?then:else expression. """
        # If-then-else
        i = myokit.formats.importer('channelml')
        m = i.model(
            os.path.join(DIR_FORMATS, 'ch-18-c-style-if.channelml'))
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
