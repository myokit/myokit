#!/usr/bin/env python3
#
# Tests the Axon format module.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import os
import unittest

import numpy as np

import myokit
import myokit.formats.axon as axon

from myokit.tests import TemporaryDirectory, DIR_FORMATS, WarningCollector


V1_INFO = '''
Axon Binary File: abf-v1.abf
ABF Format version 1.65
Recorded on: 2014-11-14 12:52:29.389999
Acquisition mode: 5: Episodic stimulation mode
Protocol set for 1 trials, spaced 0.0s apart.
    with 1 runs per trial, spaced 0.0s apart.
     and 9 sweeps per run, spaced 0.5s apart.
Sampling rate: 10000.0 Hz
A/D Channel 0: "IN 0"
  Unit: pA
D/A Channel 0: "OUT 0"
  Unit: mV
D/A Channel 1: "OUT 1"
  Unit: V
D/A Channel 2: "AO #2"
  Unit: mV
D/A Channel 3: "AO #3"
  Unit: mV
'''.strip()

V1_PROTOCOL = '''
[[protocol]]
# Level  Start    Length   Period   Multiplier
-100.0   0.0      100.0    0.0      0
0.0      100.0    400.0    0.0      0
-80.0    500.0    100.0    0.0      0
0.0      600.0    400.0    0.0      0
-60.0    1000.0   100.0    0.0      0
0.0      1100.0   400.0    0.0      0
-40.0    1500.0   100.0    0.0      0
0.0      1600.0   400.0    0.0      0
-20.0    2000.0   100.0    0.0      0
0.0      2100.0   400.0    0.0      0
0.0      2500.0   100.0    0.0      0
0.0      2600.0   400.0    0.0      0
20.0     3000.0   100.0    0.0      0
0.0      3100.0   400.0    0.0      0
40.0     3500.0   100.0    0.0      0
0.0      3600.0   400.0    0.0      0
60.0     4000.0   100.0    0.0      0
0.0      4100.0   400.0    0.0      0
'''.strip()


class AbfTest(unittest.TestCase):
    """
    Tests the ABF format support.
    """

    def test_read_v1(self):
        # Test reading a version 1 file.

        # Load file
        path = os.path.join(DIR_FORMATS, 'abf-v1.abf')
        abf = axon.AbfFile(path)
        self.assertEqual(abf.path(), path)
        self.assertEqual(abf.filename(), 'abf-v1.abf')

        print()
        print()
        print(abf.info())
        print()
        print()

        # Check getting info
        self.assertIn('version 1.65', abf.info())
        self.maxDiff = None
        self.assertEqual(abf.info(), V1_INFO)

        # Test getting full header runs without crashing
        abf.info(True)

        # Test len returns number of sweeps
        self.assertEqual(len(abf), 9)

        # Test access to A/D channels via native API
        self.assertEqual(abf.ad_channel_count(), 1)    # 1 data channel
        self.assertIsInstance(abf[0], axon.Sweep)
        self.assertIsInstance(abf[0][0], axon.Channel)
        self.assertEqual(abf.da_channel_count(), 4)    # 4 D/A channels
        self.assertIsInstance(abf[1], axon.Sweep)
        self.assertIsInstance(abf[2], axon.Sweep)
        self.assertIsInstance(abf[3], axon.Sweep)
        self.assertIsInstance(abf[4], axon.Sweep)
        self.assertIsInstance(abf[1][0], axon.Channel)
        self.assertEqual(len([s for s in abf]), 9)

        # Test conversion to Myokit protocol
        p = abf.protocol(1)
        self.assertEqual(len(p), 18)
        self.assertEqual(p.code(), V1_PROTOCOL)

        # Test other D/A channel methods
        self.assertEqual(abf.da_holding_level(1), 0)
        print(abf.da_steps(1)[0])
        self.assertEqual(len(abf.da_steps(1)[0]), 9)
        self.assertEqual(
            list(abf.da_steps(1)[0]),
            [-100, -80, -60, -40, -20, 0, 20, 40, 60])

        # Test Channel methods
        channel = abf[0][0]
        self.assertIsInstance(channel.number(), int)
        self.assertEqual(channel.name(), 'IN 0')
        self.assertEqual(str(channel), 'Channel(0 "IN 0"); 5000 points sampled'
            ' at 10000.0Hz, starts at t=0.0')
        self.assertEqual(len(channel.times()), len(channel.values()))
        self.assertFalse(np.all(channel.times() == channel.values()))







        # Test SweepSource interface
        self.assertEqual(abf.sweep_count(), 9)
        self.assertEqual(abf.channel_count(), 5)

        x = abf.channel(0)
        self.assertEqual(len(x), 1 + len(abf))      # sweeps + time
        self.assertEqual(len(x[0]), len(x[1]))
        self.assertEqual(len(x[0]), len(x[2]))
        self.assertEqual(len(x[0]), len(x[3]))
        self.assertEqual(len(x[0]), len(x[4]))
        self.assertEqual(len(x[0]), len(x[5]))
        self.assertEqual(len(x[0]), len(x[6]))
        self.assertEqual(len(x[0]), len(x[7]))
        self.assertEqual(len(x[0]), len(x[8]))
        self.assertEqual(len(x[0]), len(x[9]))

        y = abf.channel(0, join_sweeps=True)
        self.assertEqual(len(y), 2)
        self.assertEqual(len(y[0]), 9 * len(x[0]))
        self.assertEqual(len(y[0]), len(y[1]))






        # Test conversion to data log
        z = abf.log(True, False)

        self.assertEqual(len(z), 6)     # time + channel + 4 protocol channels
        sweep = abf[0]
        self.assertEqual(len(sweep), 1)     # 1 channel in sweep
        channel = sweep[0]
        self.assertIsInstance(channel.number(), int)
        self.assertIn('Channel', str(channel))
        self.assertEqual(len(abf) * len(channel.times()), len(z.time()))
        self.assertEqual(len(abf) * len(channel.values()), len(z.time()))




    def test_read_protocol_v1(self):
        # Test reading a v1 protocol file.

        # Load file
        path = os.path.join(DIR_FORMATS, 'abf-protocol.pro')
        abf = axon.AbfFile(path)

        # Check version info
        self.assertIn('version 1.65', abf.info())
        self.assertEqual(
            abf.info(),
            'Axon Protocol File: abf-protocol.pro\n'
            'ABF Format version 1.65\n'
            'Recorded on: 2005-06-17 14:33:02.160000\n'
            'Acquisition mode: 5: Episodic stimulation mode\n'
            'Protocol set for 1 trials, spaced 0.0s apart.\n'
            '    with 1 runs per trial, spaced 0.0s apart.\n'
            '     and 30 sweeps per run, spaced 5.0s apart.\n'
            'Sampling rate: 20000.0 Hz'
        )
        # Test getting full header runs without crashing
        abf.info(True)

        # Load, force as protocol
        path = os.path.join(DIR_FORMATS, 'abf-protocol.pro')
        abf = axon.AbfFile(path, is_protocol_file=True)

        # Check version info
        self.assertIn('version 1.65', abf.info())
        self.assertIn('Axon Protocol File', abf.info())

        # Test protocol extraction
        p = abf.myokit_protocol()
        self.assertEqual(len(p), 60)

        # Test step extraction
        p = abf.protocol_steps()
        self.assertEqual(len(p), 1)
        self.assertEqual(len(p[0]), 30)

    def test_read_v2(self):
        # Test reading a version 2 file.

        # Load file
        path = os.path.join(DIR_FORMATS, 'abf-v2.abf')
        abf = axon.AbfFile(path)

        # Check version info
        self.assertIn('version 2.0', abf.info())
        self.assertEqual(
            abf.info(),
            'Axon Binary File: abf-v2.abf\n'
            'ABF Format version 2.0\n'
            'Recorded on: 2014-10-01 14:03:55.980999\n'
            'Acquisition mode: 5: Episodic stimulation mode\n'
            'Protocol set for 1 trials, spaced 0.0s apart.\n'
            '    with 1 runs per trial, spaced 0.0s apart.\n'
            '     and 1 sweeps per run, spaced 5.0s apart.\n'
            'Sampling rate: 10000.0 Hz\n'
            'Channel 0: "IN 0"\n'
            '  Unit: pA\n'
            '  Low-pass filter: 10000.0 Hz\n'
            '  Cm (telegraphed): 6.34765625 pF')
        # Test getting full header runs without crashing
        abf.info(True)

        # Test len returns number of sweeps
        self.assertEqual(len(abf), 1)

        # Test data access
        self.assertEqual(abf.data_channels(), 1)    # 1 data channel
        x = abf.extract_channel(0)
        self.assertEqual(len(x), 1 + len(abf))      # sweeps + time
        self.assertEqual(len(x[0]), len(x[1]))
        y = abf.extract_channel_as_myokit_log(0)
        self.assertEqual(len(y), 1 + len(abf))      # sweeps + time
        z = abf.myokit_log()
        self.assertEqual(len(z), 6)     # time + channel + 4 protocol channels
        sweep = abf[0]
        self.assertEqual(len(sweep), 1)     # 1 channel in sweep
        channel = sweep[0]
        self.assertEqual(len(abf) * len(channel.times()), len(z.time()))
        self.assertEqual(len(abf) * len(channel.values()), len(z.time()))

        # Test protocol extraction
        self.assertEqual(abf.protocol_channels(), 4)    # 4 protocol channels
        p = abf.myokit_protocol()
        self.assertEqual(len(p), 2)     # 2 steps in this protocol
        self.assertEqual(abf.protocol_holding_level(0), -120)
        p = abf.myokit_protocol(0)
        self.assertEqual(len(p), 2)


    def test_matplotlib_figure(self):
        # Test figure drawing method (doesn't inspect output).
        # Select matplotlib backend that doesn't require a screen
        import matplotlib
        matplotlib.use('template')
        path = os.path.join(DIR_FORMATS, 'abf-v1.abf')
        abf = axon.AbfFile(path)
        abf.matplotlib_figure()


class AtfTest(unittest.TestCase):
    """
    Tests the ATF format support.
    """

    def test_write_read(self):
        # Test writing and reading an ATF file.

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
            for k, v in log.items():
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
            del log['si"nt']
            log['si\nnt'] = log['sint']
            self.assertRaisesRegex(
                ValueError, 'newlines', axon.save_atf, log, path)

            # Fields in `fields` must exist
            del log['si\nnt']
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
        # Test various accessor methods of :class:`AtfFile`.

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
