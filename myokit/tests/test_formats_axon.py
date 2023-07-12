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
  Unit: [pA]
D/A Channel 0: "OUT 0"
  Unit: [mV]
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
  Unit: [mV]
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

V1_PROTOCOL_VS = '''
[[protocol]]
# Level  Start    Length   Period   Multiplier
-0.1     0.0      0.1      0.0      0
0.0      0.1      0.4      0.0      0
-0.08    0.5      0.1      0.0      0
0.0      0.6      0.4      0.0      0
-0.06    1.0      0.1      0.0      0
0.0      1.1      0.4      0.0      0
-0.04    1.5      0.1      0.0      0
0.0      1.6      0.4      0.0      0
-0.02    2.0      0.1      0.0      0
0.0      2.1      0.4      0.0      0
0.0      2.5      0.1      0.0      0
0.0      2.6      0.4      0.0      0
0.02     3.0      0.1      0.0      0
0.0      3.1      0.4      0.0      0
0.04     3.5      0.1      0.0      0
0.0      3.6      0.4      0.0      0
0.06     4.0      0.1      0.0      0
0.0      4.1      0.4      0.0      0
'''.strip()

V2_INFO = '''
Axon Binary File: abf-v2.abf
ABF Format version 2.0.0.0
Recorded on: 2016-01-07 10:51:55.345000
Acquisition mode: 5: Episodic stimulation mode
Protocol set for 1 trials, spaced 0.0s apart.
    with 1 runs per trial, spaced 0.0s apart.
     and 37 sweeps per run, spaced 5.0s apart.
Sampling rate: 20000.0 Hz
A/D Channel 0: "IN 0"
  Unit: [pA]
  Low-pass filter: 10000.0 Hz
  Cm (telegraphed): 11.083984375 pF
D/A Channel 0: "Cmd 0"
  Unit: [mV]

'''.strip()

V2_PROTOCOL = '''
[[protocol]]
# Level  Start    Length   Period   Multiplier
-100.0   0.0      25.0     0.0      0
-120.0   25.0     4975.0   0.0      0
-95.0    5000.0   25.0     0.0      0
-120.0   5025.0   4975.0   0.0      0
-90.0    10000.0  25.0     0.0      0
-120.0   10025.0  4975.0   0.0      0
-85.0    15000.0  25.0     0.0      0
-120.0   15025.0  4975.0   0.0      0
-80.0    20000.0  25.0     0.0      0
-120.0   20025.0  4975.0   0.0      0
-75.0    25000.0  25.0     0.0      0
-120.0   25025.0  4975.0   0.0      0
-70.0    30000.0  25.0     0.0      0
-120.0   30025.0  4975.0   0.0      0
-65.0    35000.0  25.0     0.0      0
-120.0   35025.0  4975.0   0.0      0
-60.0    40000.0  25.0     0.0      0
-120.0   40025.0  4975.0   0.0      0
-55.0    45000.0  25.0     0.0      0
-120.0   45025.0  4975.0   0.0      0
-50.0    50000.0  25.0     0.0      0
-120.0   50025.0  4975.0   0.0      0
-45.0    55000.0  25.0     0.0      0
-120.0   55025.0  4975.0   0.0      0
-40.0    60000.0  25.0     0.0      0
-120.0   60025.0  4975.0   0.0      0
-35.0    65000.0  25.0     0.0      0
-120.0   65025.0  4975.0   0.0      0
-30.0    70000.0  25.0     0.0      0
-120.0   70025.0  4975.0   0.0      0
-25.0    75000.0  25.0     0.0      0
-120.0   75025.0  4975.0   0.0      0
-20.0    80000.0  25.0     0.0      0
-120.0   80025.0  4975.0   0.0      0
-15.0    85000.0  25.0     0.0      0
-120.0   85025.0  4975.0   0.0      0
-10.0    90000.0  25.0     0.0      0
-120.0   90025.0  4975.0   0.0      0
-5.0     95000.0  25.0     0.0      0
-120.0   95025.0  4975.0   0.0      0
0.0      100000.0 25.0     0.0      0
-120.0   100025.0 4975.0   0.0      0
5.0      105000.0 25.0     0.0      0
-120.0   105025.0 4975.0   0.0      0
10.0     110000.0 25.0     0.0      0
-120.0   110025.0 4975.0   0.0      0
15.0     115000.0 25.0     0.0      0
-120.0   115025.0 4975.0   0.0      0
20.0     120000.0 25.0     0.0      0
-120.0   120025.0 4975.0   0.0      0
25.0     125000.0 25.0     0.0      0
-120.0   125025.0 4975.0   0.0      0
30.0     130000.0 25.0     0.0      0
-120.0   130025.0 4975.0   0.0      0
35.0     135000.0 25.0     0.0      0
-120.0   135025.0 4975.0   0.0      0
40.0     140000.0 25.0     0.0      0
-120.0   140025.0 4975.0   0.0      0
45.0     145000.0 25.0     0.0      0
-120.0   145025.0 4975.0   0.0      0
50.0     150000.0 25.0     0.0      0
-120.0   150025.0 4975.0   0.0      0
55.0     155000.0 25.0     0.0      0
-120.0   155025.0 4975.0   0.0      0
60.0     160000.0 25.0     0.0      0
-120.0   160025.0 4975.0   0.0      0
65.0     165000.0 25.0     0.0      0
-120.0   165025.0 4975.0   0.0      0
70.0     170000.0 25.0     0.0      0
-120.0   170025.0 4975.0   0.0      0
75.0     175000.0 25.0     0.0      0
-120.0   175025.0 4975.0   0.0      0
80.0     180000.0 25.0     0.0      0
-120.0   180025.0 4975.0   0.0      0
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
        self.assertIn('version 1.65', abf.meta_str())
        self.maxDiff = None
        self.assertEqual(abf.meta_str(), V1_INFO)

        # Test getting full header runs without crashing
        abf.meta_str(True)

        # Get version
        self.assertEqual(abf.version(), '1.65')

        # Sweep count
        self.assertEqual(len(abf), 9)
        self.assertEqual(abf.sweep_count(), 9)
        self.assertEqual(len([s for s in abf]), 9)

        # Test access to A/D and D/A channels via sequence interface
        self.assertIsInstance(abf[0], axon.Sweep)
        self.assertIsInstance(abf[8], axon.Sweep)
        self.assertFalse(abf[0] is abf[1])
        self.assertEqual(len(abf[0]), 2)
        self.assertEqual(len(abf[8]), 2)
        self.assertIsInstance(abf[0][0], axon.Channel)
        self.assertIsInstance(abf[0][1], axon.Channel)

        # Test abf.Channel methods
        channel = abf[0][0]
        self.assertEqual(channel.index(), 0)
        self.assertEqual(channel.name(), 'IN 0')
        self.assertIsInstance(channel.unit(), myokit.Unit)
        self.assertEqual(channel.unit(), myokit.units.pA)
        self.assertEqual(str(channel),
                         'Channel(0 "IN 0"); 5000 points sampled at 10000.0Hz,'
                         ' starts at t=0.0.')
        self.assertEqual(len(channel.times()), len(channel.values()))
        self.assertFalse(np.all(channel.times() == channel.values()))

        # Test SweepSource info
        self.assertTrue(abf.equal_length_sweeps())
        self.assertEqual(abf.time_unit(), myokit.units.s)

        # Test A/D channel access via SweepSource interface
        self.assertEqual(abf.channel_count(), 1)
        self.assertEqual(abf.channel_names(), ['IN 0'])
        self.assertEqual(abf.channel_names(0), 'IN 0')
        self.assertEqual(abf.channel_units(), [myokit.units.pA])
        self.assertEqual(abf.channel_units(0), myokit.units.pA)

        times, values = abf.channel(0)
        self.assertEqual(9, len(times), len(values))
        self.assertEqual(len(times[0]), len(values[0]))
        self.assertEqual(len(times[0]), len(times[1]), len(values[1]))
        self.assertEqual(len(times[0]), len(times[2]), len(values[2]))
        self.assertEqual(len(times[0]), len(times[3]), len(values[3]))
        self.assertEqual(len(times[0]), len(times[4]), len(values[4]))
        self.assertEqual(len(times[0]), len(times[5]), len(values[5]))
        self.assertEqual(len(times[0]), len(times[6]), len(values[6]))
        self.assertEqual(len(times[0]), len(times[7]), len(values[7]))
        self.assertEqual(len(times[0]), len(times[8]), len(values[8]))

        tj, vj = abf.channel(0, join_sweeps=True)
        self.assertTrue(np.all(tj == np.concatenate(times)))
        self.assertTrue(np.all(vj == np.concatenate(values)))

        # Channel doesn't exist
        self.assertRaises(IndexError, abf.channel, -1)
        self.assertRaises(IndexError, abf.channel, 1)
        self.assertRaises(KeyError, abf.channel, 'OUT 0')

        # Test D/A output access via SweepSource interface
        self.assertEqual(abf.da_count(), 1)
        self.assertEqual(abf.da_names(), ['OUT 0'])
        self.assertEqual(abf.da_names(0), 'OUT 0')
        self.assertEqual(abf.da_units(), [myokit.units.mV])
        self.assertEqual(abf.da_units(0), myokit.units.mV)

        da_times, da_values = abf.da(0)
        self.assertEqual(9, len(da_times), len(da_values))
        self.assertEqual(len(da_times[0]), len(da_values[0]))
        self.assertEqual(len(da_times[0]), len(da_times[1]), len(da_values[1]))
        self.assertEqual(len(da_times[0]), len(da_times[8]), len(da_values[8]))
        self.assertEqual(len(da_times[0]), len(times[0]))
        self.assertTrue(np.all(times[0] == da_times[0]))
        self.assertFalse(np.all(values[0] == da_values[0]))
        self.assertTrue(np.all(da_values[3] == abf.da('OUT 0')[1][3]))
        self.assertRaises(IndexError, abf.da, -1)
        self.assertRaises(IndexError, abf.da, 1)
        self.assertRaises(KeyError, abf.da, 'hiya')

        tj, vj = abf.da(0, join_sweeps=True)
        self.assertTrue(np.all(tj == np.concatenate(da_times)))
        self.assertTrue(np.all(vj == np.concatenate(da_values)))

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
        self.assertIn('0.0.da', k)
        self.assertIn('1.0.da', k)
        self.assertIn('2.0.da', k)
        self.assertIn('3.0.da', k)
        self.assertIn('4.0.da', k)
        self.assertIn('5.0.da', k)
        self.assertIn('6.0.da', k)
        self.assertIn('7.0.da', k)
        self.assertIn('8.0.da', k)
        self.assertEqual(len(x['time']), len(x['5.0.channel']))
        self.assertEqual(len(x['7.0.da']), len(x['5.0.channel']))

        x = abf.log(include_da=False)
        k = list(x.keys())
        self.assertEqual(len(x), 1 + 1 * 9)
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
        self.assertEqual(len(x['time']), len(x['5.0.channel']))

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

        # Conversion to data log with joining
        y = abf.log(join_sweeps=True)
        self.assertEqual(len(y), 3)
        self.assertIn('time', y.keys())
        self.assertIn('0.channel', y.keys())
        self.assertIn('0.da', y.keys())
        self.assertEqual(len(y['time']), 9 * len(x['time']))
        self.assertEqual(len(y['time']), len(y['0.channel']))
        self.assertEqual(len(y['time']), len(y['0.da']))

        y = abf.log(join_sweeps=True, use_names=True)
        self.assertEqual(len(y), 3)
        self.assertIn('time', y.keys())
        self.assertIn('IN 0', y.keys())
        self.assertIn('OUT 0', y.keys())
        self.assertEqual(len(y['time']), 9 * len(x['time']))
        self.assertEqual(len(y['time']), len(y['IN 0']))
        self.assertEqual(len(y['time']), len(y['OUT 0']))

        y = abf.log(join_sweeps=True, use_names=True, include_da=False)
        self.assertEqual(len(y), 2)
        self.assertIn('time', y.keys())
        self.assertIn('IN 0', y.keys())
        self.assertEqual(len(y['time']), 9 * len(x['time']))
        self.assertEqual(len(y['time']), len(y['IN 0']))

        # Test conversion to Myokit protocol
        p = abf.da_protocol(0)
        self.assertEqual(len(p), 18)
        self.assertEqual(p.code(), V1_PROTOCOL)

        p = abf.da_protocol(0, vu=myokit.units.V, tu='s')
        self.assertEqual(len(p), 18)
        self.assertEqual(p.code(), V1_PROTOCOL_VS)

    def test_read_protocol_file_v1(self):
        # Test reading a v1 protocol file.

        # Load file
        path = os.path.join(DIR_FORMATS, 'abf-protocol.pro')
        abf = axon.AbfFile(path)

        # Check version info
        self.assertIn('version 1.65', abf.meta_str())
        self.assertEqual(abf.meta_str(), V1_PROTO_INFO)
        abf.meta_str(True)  # Test getting full header runs without crashing
        self.assertEqual(abf.channel_count(), 0)
        self.assertEqual(abf.channel_names(), [])
        self.assertEqual(abf.channel_units(), [])
        self.assertEqual(abf.da_count(), 1)
        self.assertEqual(abf.da_names(), ['Cmd 0'])
        self.assertEqual(abf.da_names(0), 'Cmd 0')
        self.assertEqual(abf.da_units(), [myokit.units.mV])
        self.assertEqual(abf.da_units(0), myokit.units.mV)
        #self.assertEqual(len(abf.log(join_sweeps=True)), 2)

        # Load, force as protocol
        path = os.path.join(DIR_FORMATS, 'abf-protocol.pro')
        abf = axon.AbfFile(path, is_protocol_file=True)
        self.assertEqual(abf.channel_count(), 0)
        self.assertEqual(abf.channel_count(), 0)
        self.assertEqual(abf.da_count(), 1)

        # Check version info
        self.assertIn('version 1.65', abf.meta_str())
        self.assertIn('Axon Protocol File', abf.meta_str())

        # Test protocol extraction
        p = abf.da_protocol()
        self.assertEqual(len(p), 60)

    def test_read_v2(self):
        # Test reading a version 2 file.

        # Load file
        path = os.path.join(DIR_FORMATS, 'abf-v2.abf')
        abf = axon.AbfFile(path)
        self.assertEqual(abf.path(), path)
        self.assertEqual(abf.filename(), 'abf-v2.abf')

        # Check getting info
        self.assertIn('version 2.0', abf.meta_str())
        self.maxDiff = None
        self.assertEqual(abf.meta_str(), V2_INFO)

        # Test getting full header runs without crashing
        abf.meta_str(True)

        # Get version
        self.assertEqual(abf.version(), '2.0.0.0')

        # Sweep count
        self.assertEqual(len(abf), 37)
        self.assertEqual(abf.sweep_count(), 37)

        # Test access to A/D channels via native API
        self.assertIsInstance(abf[0], axon.Sweep)
        self.assertIsInstance(abf[1], axon.Sweep)
        self.assertIsInstance(abf[36], axon.Sweep)
        self.assertFalse(abf[0] is abf[1])
        self.assertEqual(len(abf[0]), 2)
        self.assertEqual(len(abf[36]), 2)
        self.assertIsInstance(abf[0][0], axon.Channel)
        self.assertIsInstance(abf[0][1], axon.Channel)
        self.assertFalse(abf[0][0] is abf[0][1])

        # Test abf.Channel methods
        channel = abf[0][0]
        self.assertEqual(channel.index(), 0)
        self.assertEqual(channel.name(), 'IN 0')
        self.assertIsInstance(channel.unit(), myokit.Unit)
        self.assertEqual(channel.unit(), myokit.units.pA)
        self.assertEqual(str(channel),
                         'Channel(0 "IN 0"); 516 points sampled at 20000.0Hz,'
                         ' starts at t=0.0.')
        self.assertEqual(len(channel.times()), len(channel.values()))
        self.assertFalse(np.all(channel.times() == channel.values()))

        # Test SweepSource info
        self.assertTrue(abf.equal_length_sweeps())
        self.assertEqual(abf.time_unit(), myokit.units.s)

        # Test A/D channel access via SweepSource interface
        self.assertEqual(abf.channel_count(), 1)
        self.assertEqual(abf.channel_names(), ['IN 0'])
        self.assertEqual(abf.channel_names(0), 'IN 0')
        self.assertEqual(abf.channel_units(), [myokit.units.pA])
        self.assertEqual(abf.channel_units(0), myokit.units.pA)

        times, values = abf.channel(0)
        self.assertEqual(37, len(times), len(values))
        self.assertEqual(len(times[0]), len(values[0]))
        self.assertEqual(len(times[0]), len(times[1]), len(values[1]))
        self.assertEqual(len(times[0]), len(times[2]), len(values[2]))
        self.assertEqual(len(times[0]), len(times[17]), len(values[13]))
        self.assertEqual(len(times[0]), len(times[36]), len(values[36]))

        tj, vj = abf.channel(0, join_sweeps=True)
        self.assertTrue(np.all(tj == np.concatenate(times)))
        self.assertTrue(np.all(vj == np.concatenate(values)))

        # Channel doesn't exist
        self.assertRaises(IndexError, abf.channel, -1)
        self.assertRaises(IndexError, abf.channel, 1)
        self.assertRaises(KeyError, abf.channel, 'OUT 0')

        # Test D/A output access via SweepSource interface
        self.assertEqual(abf.da_count(), 1)
        self.assertEqual(abf.da_names(), ['Cmd 0'])
        self.assertEqual(abf.da_names(0), 'Cmd 0')
        self.assertEqual(abf.da_units(), [myokit.units.mV])
        self.assertEqual(abf.da_units(0), myokit.units.mV)

        da_times, da_values = abf.da(0)
        self.assertEqual(37, len(da_times), len(da_values))
        self.assertEqual(len(da_times[0]), len(da_values[0]))
        self.assertEqual(len(da_times[0]), len(da_times[1]), len(da_values[1]))
        self.assertEqual(len(da_times[0]), len(da_times[4]), len(da_values[9]))
        self.assertEqual(len(da_times[0]), len(times[0]))
        self.assertTrue(np.all(times[0] == da_times[0]))
        self.assertFalse(np.all(values[0] == da_values[0]))

        tj, vj = abf.da(0, join_sweeps=True)
        self.assertTrue(np.all(tj == np.concatenate(da_times)))
        self.assertTrue(np.all(vj == np.concatenate(da_values)))

        # Conversion to data log without joining
        x = abf.log()
        k = list(x.keys())
        self.assertEqual(len(x), 1 + 2 * 37)
        self.assertIn('time', x)
        self.assertIn('0.0.channel', k)
        self.assertIn('1.0.channel', k)
        self.assertIn('2.0.channel', k)
        self.assertIn('3.0.channel', k)
        self.assertIn('36.0.channel', k)
        self.assertIn('0.0.da', k)
        self.assertIn('5.0.da', k)
        self.assertIn('16.0.da', k)
        self.assertIn('36.0.da', k)
        self.assertEqual(len(x['time']), len(x['5.0.channel']))
        self.assertEqual(len(x['7.0.da']), len(x['5.0.channel']))

        x = abf.log(include_da=False)
        k = list(x.keys())
        self.assertEqual(len(x), 1 + 1 * 37)
        self.assertIn('time', x)
        self.assertIn('0.0.channel', k)
        self.assertIn('1.0.channel', k)
        self.assertIn('2.0.channel', k)
        self.assertIn('3.0.channel', k)
        self.assertIn('36.0.channel', k)
        self.assertNotIn('0.0.da', k)
        self.assertNotIn('7.0.da', k)
        self.assertNotIn('36.0.da', k)
        self.assertEqual(len(x['time']), len(x['6.0.channel']))

        x = abf.log(use_names=True)
        k = list(x.keys())
        self.assertEqual(len(x), 1 + 2 * 37)
        self.assertIn('time', x)
        self.assertIn('0.IN 0', k)
        self.assertIn('1.IN 0', k)
        self.assertIn('2.IN 0', k)
        self.assertIn('36.IN 0', k)
        self.assertIn('0.Cmd 0', k)
        self.assertIn('5.Cmd 0', k)
        self.assertIn('16.Cmd 0', k)
        self.assertIn('36.Cmd 0', k)
        self.assertEqual(len(x['time']), len(x['5.IN 0']))
        self.assertEqual(len(x['7.Cmd 0']), len(x['5.IN 0']))

        # Conversion to data log with joining
        y = abf.log(join_sweeps=True)
        self.assertEqual(len(y), 3)
        self.assertIn('time', y.keys())
        self.assertIn('0.channel', y.keys())
        self.assertIn('0.da', y.keys())
        self.assertEqual(len(y['time']), 37 * len(x['time']))
        self.assertEqual(len(y['time']), len(y['0.channel']))
        self.assertEqual(len(y['time']), len(y['0.da']))

        y = abf.log(join_sweeps=True, use_names=True)
        self.assertEqual(len(y), 3)
        self.assertIn('time', y.keys())
        self.assertIn('IN 0', y.keys())
        self.assertIn('Cmd 0', y.keys())
        self.assertEqual(len(y['time']), 37 * len(x['time']))
        self.assertEqual(len(y['time']), len(y['IN 0']))
        self.assertEqual(len(y['time']), len(y['Cmd 0']))

        y = abf.log(join_sweeps=True, use_names=True, include_da=False)
        self.assertEqual(len(y), 2)
        self.assertIn('time', y.keys())
        self.assertIn('IN 0', y.keys())
        self.assertEqual(len(y['time']), 37 * len(x['time']))
        self.assertEqual(len(y['time']), len(y['IN 0']))

        # Test conversion to Myokit protocol
        p = abf.da_protocol(0)
        self.assertEqual(len(p), 37 * 2)
        self.assertEqual(p.code(), V2_PROTOCOL)

        # Test conversion with initial holding as in the real experiment
        p = abf.da_protocol(0, include_initial_holding=True)
        e = p.events()
        self.assertEqual(e[0].level(), -120)    # Pre step
        self.assertEqual(e[0].start(), 0)
        self.assertEqual(e[0].duration(), 0.4)
        self.assertEqual(e[1].level(), -100)    # Real step
        self.assertEqual(e[1].start(), 0.4)
        self.assertEqual(e[1].duration(), 25)
        self.assertEqual(e[2].level(), -120)    # Shortened post-step
        self.assertEqual(e[2].start(), 25.4)
        self.assertEqual(e[2].duration(), 4974.6)
        self.assertEqual(e[3].level(), -120)    # Next pre step
        self.assertEqual(e[3].start(), 5000)
        self.assertEqual(e[3].duration(), 0.4)
        self.assertEqual(len(e), 37 * 3)

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
            meta = atf.meta_str()
            self.assertIn('myokit', meta)
            with WarningCollector() as w:
                self.assertEqual(meta, atf.info())
            self.assertIn('deprecated', w.text())

            # Test version
            self.assertEqual(atf.version(), '1.0')


if __name__ == '__main__':
    unittest.main()
