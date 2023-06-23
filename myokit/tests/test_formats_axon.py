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
'''.strip()

V1_PROTO_INFO = '''
Axon Protocol File: abf-protocol.pro
ABF Format version 1.65
Recorded on: 2005-06-17 14:33:02.160000
Acquisition mode: 5: Episodic stimulation mode
Protocol set for 1 trials, spaced 0.0s apart.
    with 1 runs per trial, spaced 0.0s apart.
     and 30 sweeps per run, spaced 5.0s apart.
Sampling rate: 20000.0 Hz
D/A Channel 0: "Cmd 0"
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

V2_INFO = '''
Axon Binary File: abf-v2.abf
ABF Format version 2.0.0.0
Recorded on: 2014-10-01 14:03:55.980999
Acquisition mode: 5: Episodic stimulation mode
Protocol set for 1 trials, spaced 0.0s apart.
    with 1 runs per trial, spaced 0.0s apart.
     and 1 sweeps per run, spaced 5.0s apart.
Sampling rate: 10000.0 Hz
A/D Channel 0: "IN 0"
  Unit: pA
  Low-pass filter: 10000.0 Hz
  Cm (telegraphed): 6.34765625 pF
D/A Channel 0: "Cmd 0"
  Unit: mV
'''.strip()

V2_PROTOCOL = '''
[[protocol]]
# Level  Start    Length   Period   Multiplier
12.0     0.0      1000.0   0.0      0
-120.0   1000.0   4000.0   0.0      0
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
        self.assertIsInstance(abf, myokit.formats.SweepSource)

        # Check getting info
        self.assertIn('version 1.65', abf.info())
        self.maxDiff = None
        self.assertEqual(abf.info(), V1_INFO)

        # Test getting full header runs without crashing
        abf.info(True)

        # Get version
        self.assertEqual(abf.version(), '1.65')

        # Test len returns number of sweeps
        self.assertEqual(len(abf), 9)

        # Test access to A/D channels via native API
        self.assertEqual(abf.ad_channel_count(), 1)    # 1 data channel
        self.assertIsInstance(abf[0], axon.Sweep)
        self.assertIsInstance(abf[0][0], axon.Channel)
        self.assertEqual(abf.da_channel_count(), 1)    # 1 D/A channel
        self.assertIsInstance(abf[0][1], axon.Channel)
        self.assertEqual(len([s for s in abf]), 9)
        self.assertEqual(len(abf[0]), abf.channel_count())

        # Test conversion to Myokit protocol
        p = abf.protocol(1)
        self.assertEqual(len(p), 18)
        self.assertEqual(p.code(), V1_PROTOCOL)

        # Test other D/A channel methods
        self.assertEqual(abf.da_holding_level(1), 0)
        self.assertEqual(len(abf.da_steps(1)[0]), 9)
        self.assertEqual(
            list(abf.da_steps(1)[0]),
            [-100, -80, -60, -40, -20, 0, 20, 40, 60])

        # Test Channel methods
        channel = abf[0][0]
        self.assertIsInstance(channel.number(), int)
        self.assertEqual(channel.name(), 'IN 0')
        self.assertEqual(str(channel),
                         'Channel(0 "IN 0"); 5000 points sampled at 10000.0Hz,'
                         ' starts at t=0.0.')
        self.assertEqual(len(channel.times()), len(channel.values()))
        self.assertFalse(np.all(channel.times() == channel.values()))

        # Test SweepSource interface
        self.assertEqual(abf.sweep_count(), 9)
        self.assertEqual(abf.channel_count(), 2)
        self.assertEqual(abf.channel_names(), ['IN 0', 'OUT 0'])

        # Channel without joining
        x = abf.channel(0)
        self.assertEqual(len(x), 1 + len(abf))
        self.assertEqual(len(x[0]), len(x[1]))
        self.assertEqual(len(x[0]), len(x[2]))
        self.assertEqual(len(x[0]), len(x[3]))
        self.assertEqual(len(x[0]), len(x[4]))
        self.assertEqual(len(x[0]), len(x[5]))
        self.assertEqual(len(x[0]), len(x[6]))
        self.assertEqual(len(x[0]), len(x[7]))
        self.assertEqual(len(x[0]), len(x[8]))
        self.assertEqual(len(x[0]), len(x[9]))

        # Channel with joining
        y = abf.channel(0, join_sweeps=True)
        self.assertEqual(len(y), 2)
        self.assertEqual(len(y[0]), 9 * len(x[0]))
        self.assertEqual(len(y[0]), len(y[1]))

        # Channel doesn't exist
        self.assertRaises(IndexError, abf.channel, -1)
        self.assertRaises(IndexError, abf.channel, 2)
        self.assertRaises(KeyError, abf.channel, 'Tom')

        # Conversion to data log without joining
        x = abf.log()
        k = list(x.keys())
        self.assertEqual(len(x), 1 + 2 * 9)
        self.assertIn('time', x)
        self.assertIn('0.0.channel', k)
        self.assertIn('1.0.channel', k)
        self.assertIn('2.0.channel', k)
        self.assertIn('3.0.channel', k)
        self.assertIn('4.0.channel', k)
        self.assertIn('5.0.channel', k)
        self.assertIn('6.0.channel', k)
        self.assertIn('7.0.channel', k)
        self.assertIn('8.0.channel', k)
        self.assertIn('0.1.channel', k)
        self.assertIn('1.1.channel', k)
        self.assertIn('2.1.channel', k)
        self.assertIn('3.1.channel', k)
        self.assertIn('4.1.channel', k)
        self.assertIn('5.1.channel', k)
        self.assertIn('6.1.channel', k)
        self.assertIn('7.1.channel', k)
        self.assertIn('8.1.channel', k)
        self.assertEqual(len(x['time']), len(x['5.0.channel']))
        self.assertEqual(len(x['7.1.channel']), len(x['5.0.channel']))

        x = abf.log(use_names=True)
        k = list(x.keys())
        self.assertEqual(len(x), 1 + 2 * 9)
        self.assertIn('time', k)
        self.assertIn('0.IN 0', k)
        self.assertIn('1.IN 0', k)
        self.assertIn('2.IN 0', k)
        self.assertIn('3.IN 0', k)
        self.assertIn('4.IN 0', k)
        self.assertIn('5.IN 0', k)
        self.assertIn('6.IN 0', k)
        self.assertIn('7.IN 0', k)
        self.assertIn('8.IN 0', k)
        self.assertIn('0.OUT 0', k)
        self.assertIn('1.OUT 0', k)
        self.assertIn('2.OUT 0', k)
        self.assertIn('3.OUT 0', k)
        self.assertIn('4.OUT 0', k)
        self.assertIn('5.OUT 0', k)
        self.assertIn('6.OUT 0', k)
        self.assertIn('7.OUT 0', k)
        self.assertIn('8.OUT 0', k)

        y = abf.log(use_names=True, channels=[1])
        k = list(y.keys())
        self.assertEqual(len(y), 1 + 9)
        self.assertIn('time', y)
        self.assertIn('0.OUT 0', y)
        x = abf.log(use_names=True, channels=['OUT 0'])
        y = list(x.keys())
        self.assertEqual(len(y), 1 + 9)
        self.assertIn('time', y)
        self.assertIn('8.OUT 0', y)
        x = abf.log(use_names=True, channels=['IN 0', 'OUT 0'])
        y = list(x.keys())
        self.assertEqual(len(y), 1 + 2 * 9)
        self.assertIn('time', y)
        self.assertIn('0.OUT 0', y)
        self.assertIn('2.IN 0', y)
        self.assertEqual(len(x['time']), len(x['2.IN 0']))

        # Conversion to data log with joining
        y = abf.log(join_sweeps=True)
        self.assertEqual(len(y), 3)
        self.assertIn('time', y.keys())
        self.assertIn('0.channel', y.keys())
        self.assertIn('1.channel', y.keys())
        self.assertEqual(len(y['time']), 9 * len(x['time']))
        self.assertEqual(len(y['time']), len(y['0.channel']))
        self.assertEqual(len(y['time']), len(y['1.channel']))

        y = abf.log(join_sweeps=True, use_names=True)
        self.assertEqual(len(y), 3)
        self.assertIn('time', y.keys())
        self.assertIn('IN 0', y.keys())
        self.assertIn('OUT 0', y.keys())
        self.assertEqual(len(y['time']), 9 * len(x['time']))
        self.assertEqual(len(y['time']), len(y['IN 0']))
        self.assertEqual(len(y['time']), len(y['OUT 0']))

        y = abf.log(join_sweeps=True, use_names=True, channels=['IN 0'])
        self.assertEqual(len(y), 2)
        self.assertIn('time', y.keys())
        self.assertIn('IN 0', y.keys())

    def test_read_protocol_v1(self):
        # Test reading a v1 protocol file.

        # Load file
        path = os.path.join(DIR_FORMATS, 'abf-protocol.pro')
        abf = axon.AbfFile(path)

        # Check version info
        self.assertIn('version 1.65', abf.info())
        self.assertEqual(abf.info(), V1_PROTO_INFO)
        abf.info(True)  # Test getting full header runs without crashing
        self.assertEqual(abf.channel_count(), 1)
        self.assertEqual(abf.ad_channel_count(), 0)
        self.assertEqual(abf.da_channel_count(), 1)
        self.assertEqual(abf.channel_names(), ['Cmd 0'])
        #self.assertEqual(len(abf.log(join_sweeps=True)), 2)

        # Load, force as protocol
        path = os.path.join(DIR_FORMATS, 'abf-protocol.pro')
        abf = axon.AbfFile(path, is_protocol_file=True)
        self.assertEqual(abf.channel_count(), 1)
        self.assertEqual(abf.ad_channel_count(), 0)
        self.assertEqual(abf.da_channel_count(), 1)

        # Check version info
        self.assertIn('version 1.65', abf.info())
        self.assertIn('Axon Protocol File', abf.info())

        # Test protocol extraction
        p = abf.protocol()
        self.assertEqual(len(p), 60)

    def test_read_v2(self):
        # Test reading a version 2 file.

        # Load file
        path = os.path.join(DIR_FORMATS, 'abf-v2.abf')
        abf = axon.AbfFile(path)
        self.assertEqual(abf.path(), path)
        self.assertEqual(abf.filename(), 'abf-v2.abf')

        # Check getting info
        self.assertIn('version 2.0', abf.info())
        self.maxDiff = None
        self.assertEqual(abf.info(), V2_INFO)

        # Test getting full header runs without crashing
        abf.info(True)

        # Get version
        self.assertEqual(abf.version(), '2.0.0.0')

        # Test len returns number of sweeps
        self.assertEqual(len(abf), 1)

        # Test access to A/D channels via native API
        self.assertEqual(abf.ad_channel_count(), 1)    # 1 data channel
        self.assertIsInstance(abf[0], axon.Sweep)
        self.assertIsInstance(abf[0][0], axon.Channel)
        self.assertEqual(abf.da_channel_count(), 1)    # 1 D/A channel
        self.assertIsInstance(abf[0][1], axon.Channel)
        self.assertEqual(len([s for s in abf]), 1)
        self.assertEqual(len(abf[0]), abf.channel_count())

        # Test conversion to Myokit protocol
        p = abf.protocol(1)
        self.assertEqual(len(p), 2)
        self.assertEqual(p.code(), V2_PROTOCOL)
        self.assertRaises(ValueError, abf.protocol, 0)  # Not a D/A channel

        # Test other D/A channel methods
        self.assertEqual(abf.da_holding_level(1), -120)
        self.assertEqual(len(abf.da_steps(1)[0]), 1)
        self.assertEqual(abf.da_steps(1)[0], [12])

        # Test Channel methods
        channel = abf[0][0]
        self.assertIsInstance(channel.number(), int)
        self.assertEqual(channel.name(), 'IN 0')
        self.assertEqual(str(channel),
                         'Channel(0 "IN 0"); 3100 points sampled at 10000.0Hz,'
                         ' starts at t=76.5501.')
        self.assertEqual(len(channel.times()), len(channel.values()))
        self.assertFalse(np.all(channel.times() == channel.values()))

        # Test SweepSource interface
        self.assertEqual(abf.sweep_count(), 1)
        self.assertEqual(abf.channel_count(), 2)
        self.assertEqual(abf.channel_names(), ['IN 0', 'Cmd 0'])

        # Channel without joining
        x = abf.channel(0)
        self.assertEqual(len(x), 1 + len(abf))
        self.assertEqual(len(x[0]), len(x[1]))

        # Channel with joining
        y = abf.channel(0, join_sweeps=True)
        self.assertEqual(len(y), 2)
        self.assertEqual(len(y[0]), len(x[0]))
        self.assertEqual(len(y[0]), len(y[1]))

        # Conversion to data log without joining
        x = abf.log()
        k = list(x.keys())
        self.assertEqual(len(x), 3)
        self.assertIn('time', x)
        self.assertIn('0.0.channel', k)
        self.assertIn('0.1.channel', k)
        self.assertEqual(len(x['time']), len(x['0.0.channel']))
        self.assertEqual(len(x['time']), len(x['0.1.channel']))
        self.assertTrue(np.all(x['time'] == abf.channel(0)[0]))
        self.assertTrue(np.all(x['0.0.channel'] == abf.channel(0)[1]))

        x = abf.log(use_names=True)
        k = list(x.keys())
        self.assertEqual(len(x), 3)
        self.assertIn('time', k)
        self.assertIn('0.IN 0', k)
        self.assertIn('0.Cmd 0', k)

        y = abf.log(use_names=True, channels=[1])
        k = list(y.keys())
        self.assertEqual(len(y), 2)
        self.assertIn('time', y)
        self.assertIn('0.Cmd 0', y)
        x = abf.log(use_names=True, channels=['Cmd 0'])
        y = list(x.keys())
        self.assertEqual(len(y), 2)
        self.assertIn('time', y)
        self.assertIn('0.Cmd 0', y)
        x = abf.log(use_names=True, channels=[0, 'Cmd 0'])
        y = list(x.keys())
        self.assertEqual(len(y), 3)
        self.assertIn('time', y)
        self.assertIn('0.Cmd 0', y)
        self.assertIn('0.IN 0', y)
        self.assertEqual(len(x['time']), len(x['0.IN 0']))

        # Conversion to data log with joining
        y = abf.log(join_sweeps=True)
        self.assertEqual(len(y), 3)
        self.assertIn('time', y.keys())
        self.assertIn('0.channel', y.keys())
        self.assertIn('1.channel', y.keys())
        self.assertEqual(len(y['time']), 1 * len(x['time']))
        self.assertEqual(len(y['time']), len(y['0.channel']))
        self.assertEqual(len(y['time']), len(y['1.channel']))
        self.assertTrue(np.all(y['time'] == abf.channel(0, True)[0]))
        self.assertTrue(np.all(y['0.channel'] == abf.channel(0, True)[1]))

        y = abf.log(join_sweeps=True, use_names=True)
        self.assertEqual(len(y), 3)
        self.assertIn('time', y.keys())
        self.assertIn('IN 0', y.keys())
        self.assertIn('Cmd 0', y.keys())
        self.assertEqual(len(y['time']), 1 * len(x['time']))
        self.assertEqual(len(y['time']), len(y['IN 0']))
        self.assertEqual(len(y['time']), len(y['Cmd 0']))

        y = abf.log(join_sweeps=True, use_names=True, channels=['IN 0'])
        self.assertEqual(len(y), 2)
        self.assertIn('time', y.keys())
        self.assertIn('IN 0', y.keys())

    def test_matplotlib_figure(self):
        # Test figure drawing method (doesn't inspect output).
        # Select matplotlib backend that doesn't require a screen
        import matplotlib
        matplotlib.use('template')
        path = os.path.join(DIR_FORMATS, 'abf-v1.abf')
        abf = axon.AbfFile(path)
        f = abf.matplotlib_figure()
        self.assertIsInstance(f, matplotlib.figure.Figure)


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

            # Deprecated method
            with WarningCollector() as w:
                log3 = axon.AtfFile(path).myokit_log()
            self.assertIn('deprecated', w.text())
            self.assertEqual(len(log), len(log3))
            self.assertEqual(set(log.keys()), set(log3.keys()))
            for k, v in log.items():
                self.assertTrue(np.all(v == log3[k]))

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
                Exception, 'double quotes', axon.load_atf, path)

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

            # Test filename() and path()
            self.assertEqual(atf.path(), path)
            self.assertEqual(atf.filename(), 'test.atf')

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
