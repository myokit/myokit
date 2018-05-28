#!/usr/bin/env python
#
# Tests the Axon format module.
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import unittest
import numpy as np

import myokit
import myokit.formats.axon as axon

from shared import TemporaryDirectory


class AtfTest(unittest.TestCase):
    """
    Tests the ATF format support.
    """

    def test_write_read(self):
        """
        Tests writing and reading an ATF file.
        """
        with TemporaryDirectory() as d:
            # Create data log
            log = myokit.DataLog()
            log.set_time_key('time')
            log['time'] = np.arange(100)
            log['sint'] = np.sin(log['time'])
            log['cost'] = np.cos(log['time'])

            # Write atf file
            path = d.path('test.atf')
            axon.save_atf(log, path)

            # Read atf file
            log2 = axon.load_atf(path)
            self.assertEqual(len(log), len(log2))
            self.assertEqual(set(log.keys()), set(log2.keys()))
            for k, v in log.iteritems():
                self.assertTrue(np.all(v == log2[k]))

            # Write selected fields
            axon.save_atf(log, path, fields=['time', 'sint'])
            log2 = axon.load_atf(path)
            self.assertEqual(set(log2.keys()), set(['time', 'sint']))

            # Time must be regularly spaced
            log['time'][-1] *= 2
            self.assertRaisesRegexp(
                ValueError, 'regularly spaced', axon.save_atf, log, path)

            # Field names can't contain quotes
            log['time'] = np.arange(100)
            log['si"nt'] = log['sint']
            self.assertRaisesRegexp(
                ValueError, 'double quotes', axon.save_atf, log, path)

            # Field names can't have newlines
            del(log['si"nt'])
            log['si\nnt'] = log['sint']
            self.assertRaisesRegexp(
                ValueError, 'newlines', axon.save_atf, log, path)

            # Fields in `fields` must exist
            del(log['si\nnt'])
            self.assertRaisesRegexp(
                ValueError, 'not found', axon.save_atf, log, path,
                fields=['time', 'sint', 'hi'])


if __name__ == '__main__':
    unittest.main()
