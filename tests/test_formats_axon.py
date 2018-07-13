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

import os
import unittest
import numpy as np

import myokit
import myokit.formats.axon as axon

from shared import TemporaryDirectory, DIR_FORMATS

# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp


class AbfTest(unittest.TestCase):
    """
    Tests the ABF format support.
    """

    def test_read_v1(self):
        """
        Tests reading a version 1 file.
        """
        # Load file
        path = os.path.join(DIR_FORMATS, 'abf-v1.abf')
        abf = axon.AbfFile(path)
        self.assertEqual(abf.filename(), path)

        # Check version info
        self.assertIn('version 1.65', abf.info())
        self.assertEqual(abf.info(),    # noqa
'''Axon Binary File: abf-v1.abf
ABF Format version 1.65
Recorded on: 2014-11-14 12:52:29.389999
Acquisition mode: 5: Episodic stimulation mode
Protocol set for 1 trials, measuring 0.0s start-to-start.
    with 1 runs per trial, measuring 0.0s start-to-start.
     and 9 sweeps per run, measuring 0.5 s start-to-start
Sampling rate: 10000.0 Hz
Channel 0: "IN 0      "
  Unit: pA''')

        # Test data access
        self.assertEqual(abf.data_channels(), 1)    # 1 data channel
        x = abf.extract_channel(0)
        self.assertEqual(len(x), 1 + len(abf))      # sweeps + time
        y = abf.extract_channel_as_myokit_log(0)
        self.assertEqual(len(y), 1 + len(abf))      # sweeps + time
        z = abf.myokit_log()
        self.assertEqual(len(z), 6)     # time + channel + 4 protocol channels

        # Test protocol extraction
        self.assertEqual(abf.protocol_channels(), 4)    # 4 protocol channels
        p = abf.myokit_protocol()
        self.assertEqual(len(p), 18)    # 18 steps in this protocol
        self.assertEqual(abf.protocol_holding_level(0), 0)
        p = abf.myokit_protocol(0)
        self.assertEqual(len(p), 18)

    def test_read_v2(self):
        """
        Tests reading a version 2 file.
        """
        # Load file
        path = os.path.join(DIR_FORMATS, 'abf-v2.abf')
        abf = axon.AbfFile(path)

        # Check version info
        self.assertIn('version 2.0', abf.info())
        self.assertEqual(abf.info(),    # noqa
'''Axon Binary File: abf-v2.abf
ABF Format version 2.0
Recorded on: 2014-10-01 14:03:55.980999
Acquisition mode: 5: Episodic stimulation mode
Protocol set for 1 trials, measuring 0.0s start-to-start.
    with 1 runs per trial, measuring 0.0s start-to-start.
     and 1 sweeps per run, measuring 5.0 s start-to-start
Sampling rate: 10000.0 Hz
Channel 0: "IN 0"
  Unit: pA
  Low-pass filter: 10000.0 Hz
  Cm (telegraphed): 6.34765625 pF''')

        # Test data access
        self.assertEqual(abf.data_channels(), 1)    # 1 data channel
        x = abf.extract_channel(0)
        self.assertEqual(len(x), 1 + len(abf))      # sweeps + time
        y = abf.extract_channel_as_myokit_log(0)
        self.assertEqual(len(y), 1 + len(abf))      # sweeps + time
        z = abf.myokit_log()
        self.assertEqual(len(z), 6)     # time + channel + 4 protocol channels

        # Test protocol extraction
        self.assertEqual(abf.protocol_channels(), 4)    # 4 protocol channels
        p = abf.myokit_protocol()
        self.assertEqual(len(p), 2)     # 2 steps in this protocol
        self.assertEqual(abf.protocol_holding_level(0), -120)
        p = abf.myokit_protocol(0)
        self.assertEqual(len(p), 2)

    def test_read_protocol_v1(self):
        """
        Tests reading a v1 protocol file.
        """
        # Load file
        path = os.path.join(DIR_FORMATS, 'abf-protocol.pro')
        abf = axon.AbfFile(path)

        # Check version info
        self.assertIn('version 1.65', abf.info())
        self.assertEqual(abf.info(),    # noqa
'''Axon Protocol File: abf-protocol.pro
ABF Format version 1.65
Recorded on: 2005-06-17 14:33:02.160000
Acquisition mode: 5: Episodic stimulation mode
Protocol set for 1 trials, measuring 0.0s start-to-start.
    with 1 runs per trial, measuring 0.0s start-to-start.
     and 30 sweeps per run, measuring 5.0 s start-to-start
Sampling rate: 20000.0 Hz''')

        # Load, force as protocol
        path = os.path.join(DIR_FORMATS, 'abf-protocol.pro')
        abf = axon.AbfFile(path, is_protocol_file=True)

        # Check version info
        self.assertIn('version 1.65', abf.info())
        self.assertIn('Axon Protocol File', abf.info())

        # Test protocol extraction
        p = abf.myokit_protocol()
        self.assertEqual(len(p), 60)


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
            self.assertRaisesRegex(
                ValueError, 'regularly spaced', axon.save_atf, log, path)

            # Field names can't contain quotes
            log['time'] = np.arange(100)
            log['si"nt'] = log['sint']
            self.assertRaisesRegex(
                ValueError, 'double quotes', axon.save_atf, log, path)

            # Field names can't have newlines
            del(log['si"nt'])
            log['si\nnt'] = log['sint']
            self.assertRaisesRegex(
                ValueError, 'newlines', axon.save_atf, log, path)

            # Fields in `fields` must exist
            del(log['si\nnt'])
            self.assertRaisesRegex(
                ValueError, 'not found', axon.save_atf, log, path,
                fields=['time', 'sint', 'hi'])

            # Try using on other formats
            log.save_csv(path)
            self.assertRaisesRegex(Exception, 'file type', axon.load_atf, path)

            # Try reading raw meta data (no key-value pairs)
            with open(path, 'w') as f:
                f.write('ATF\t1.0\n')
                f.write('1\t3\n')
                f.write('"Hello! This is raw meta data"\n')
                f.write('"time"\t"sint"\t"cost"\n')
                f.write('0\t0.0\t1.0\n')
                f.write('1\t10\t20\n')
                f.write('2\t30\t40\n')
            log2 = axon.load_atf(path)

            # Test invalid header detection
            with open(path, 'w') as f:
                f.write('ATF\t1.0\n')
                f.write('1\t3\n')
                f.write('Hello! This is raw meta data\n')
                f.write('"time"\t"sint"\t"cost"\n')
                f.write('0\t0.0\t1.0\n')
                f.write('1\t10\t20\n')
                f.write('2\t30\t40\n')
            self.assertRaisesRegex(
                Exception, 'double quotation', axon.load_atf, path)

            # Bad column headers
            with open(path, 'w') as f:
                f.write('ATF\t1.0\n')
                f.write('1\t3\n')
                f.write('"Hello! This is raw meta data"\n')
                f.write('Bonjou\t"time"\t"sint"\t"cost"\n')
                f.write('0\t0.0\t1.0\n')
                f.write('1\t10\t20\n')
                f.write('2\t30\t40\n')
            self.assertRaisesRegex(
                Exception, 'column headers', axon.load_atf, path)

            # Bad column headers
            with open(path, 'w') as f:
                f.write('ATF\t1.0\n')
                f.write('1\t3\n')
                f.write('"Hello! This is raw meta data"\n')
                f.write('time"\t"sint"\t"cost"\n')
                f.write('0\t0.0\t1.0\n')
                f.write('1\t10\t20\n')
                f.write('2\t30\t40\n')
            self.assertRaisesRegex(
                Exception, 'column headers', axon.load_atf, path)

            # Too many headers
            with open(path, 'w') as f:
                f.write('ATF\t1.0\n')
                f.write('1\t3\n')
                f.write('"Hello! This is raw meta data"\n')
                f.write('"Bonjour"\t"time"\t"sint"\t"cost"\n')
                f.write('0\t0.0\t1.0\n')
                f.write('1\t10\t20\n')
                f.write('2\t30\t40\n')
            self.assertRaisesRegex(
                Exception, 'found 4', axon.load_atf, path)

            # Commas as delimiter are ok
            with open(path, 'w') as f:
                f.write('ATF\t1.0\n')
                f.write('1\t3\n')
                f.write('"Hello! This is raw meta data"\n')
                f.write('"time","sint","cost"\n')
                f.write('0,0.0,1.0\n')
                f.write('1,10,20\n')
                f.write('2,30,40\n')
            axon.load_atf(path)

            # But can't mix them
            with open(path, 'w') as f:
                f.write('ATF\t1.0\n')
                f.write('1\t3\n')
                f.write('"Hello! This is raw meta data"\n')
                f.write('"time"\t"sint","cost"\n')
                f.write('0,0.0,1.0\n')
                f.write('1,10,20\n')
                f.write('2,30,40\n')
            self.assertRaisesRegex(
                Exception, 'Mixed delimiters', axon.load_atf, path)

            # Too many columns
            with open(path, 'w') as f:
                f.write('ATF\t1.0\n')
                f.write('1\t3\n')
                f.write('"Hello! This is raw meta data"\n')
                f.write('"time"\t"sint"\t"cost"\n')
                f.write('0\t0.0\t1.0\n')
                f.write('1\t10\t20\t100\n')
                f.write('2\t30\t40\n')
            self.assertRaisesRegex(
                Exception, 'Invalid data', axon.load_atf, path)

    def test_accessors(self):
        """ Tests various accessor methods of :class:`AtfFile`. """
        with TemporaryDirectory() as d:
            # Create data log
            log = myokit.DataLog()
            log.set_time_key('time')
            log['time'] = np.arange(10)
            log['sint'] = np.sin(log['time'])
            log['cost'] = np.cos(log['time'])

            # Write atf file
            path = d.path('test.atf')
            axon.save_atf(log, path)

            # Read atf file
            atf = myokit.formats.axon.AtfFile(path)

            # Test filename()
            self.assertEqual(atf.filename(), path)

            # Test iter and getitem
            self.assertEqual(len(list(iter(atf))), 3)
            self.assertTrue(np.all(atf['time'] == log['time']))
            self.assertTrue(np.all(atf['sint'] == log['sint']))
            self.assertTrue(np.all(atf['cost'] == log['cost']))

            # Test items()
            items = list(atf.items())
            self.assertEqual(items[0][0], 'time')
            self.assertEqual(items[1][0], 'sint')
            self.assertEqual(items[2][0], 'cost')
            self.assertTrue(np.all(items[0][1] == log['time']))
            self.assertTrue(np.all(items[1][1] == log['sint']))
            self.assertTrue(np.all(items[2][1] == log['cost']))

            # Test keys()
            self.assertEqual(list(atf.keys()), ['time', 'sint', 'cost'])

            # Test values()
            values = list(atf.values())
            self.assertTrue(np.all(values[0] == log['time']))
            self.assertTrue(np.all(values[1] == log['sint']))
            self.assertTrue(np.all(values[2] == log['cost']))

            # Test len
            self.assertEqual(len(atf), 3)

            # Test info
            self.assertIn('myokit', atf.info())

            # Test version
            self.assertEqual(atf.version(), '1.0')


if __name__ == '__main__':
    unittest.main()
