#!/usr/bin/env python3
#
# Tests the WCP format module.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import os
import unittest

import numpy as np

import myokit
import myokit.formats.wcp as wcp

from myokit.tests import DIR_FORMATS, WarningCollector


INFO = '''
WinWCP file: wcp-file.wcp
WinWCP Format version 9
Recorded on: 21/11/2014 14:18:28
  Number of records: 11
  Channels per record: 2
  Samples per channel: 256
  Sampling interval: 0.001 s
A/D channel: Im
  Unit: pA
A/D channel: Vm
  Unit: mV
Records: Type, Status, Sampling Interval, Start, Marker
Record 0: TEST, ACCEPTED, 0.0, ""
Record 1: TEST, ACCEPTED, 0.5, ""
Record 2: TEST, ACCEPTED, 1.0, ""
Record 3: TEST, ACCEPTED, 1.5, ""
Record 4: TEST, ACCEPTED, 2.0615234375, ""
Record 5: TEST, ACCEPTED, 3.0615234375, ""
Record 6: TEST, ACCEPTED, 3.5615234375, ""
Record 7: TEST, ACCEPTED, 4.0615234375, ""
Record 8: TEST, ACCEPTED, 4.5615234375, ""
Record 9: TEST, ACCEPTED, 5.125, ""
Record 10: TEST, ACCEPTED, 5.625, ""
'''.strip()


INFO_LONG = INFO + '''
----------------------------------- header -----------------------------------
ver: 9
ctime: 21/11/2014 12:43:08
rtime: 21/11/2014 14:18:28
nbh: 1024
adcmax: 32677
nc: 2
nba: 2
nbd: 2
ad: 10.0
nr: 11
dt: 0.001
nz: 20
id: ''' + '''
--------------------------------- raw header ---------------------------------
rtimesecs: 9062.11
yo0: 0
yu0: pA
yn0: Im
yg0: 0.0005
yz0: 0
yr0: 0
yo1: 1
yu1: mV
yn1: Vm
yg1: 0.01
yz1: 0
yr1: 0
txperc: 0
pkpavg: 1
nsvchan: 0
nsvalign: 0
nsvtypr: 0
nsvs2p: F
nsvcur0: 0
nsvcur1: 0
'''.rstrip()


class WcpTest(unittest.TestCase):
    """
    Tests the WCP format module.
    """

    def test_data_file(self):
        # Test basic wcp file reading.

        # Load test file
        fname = 'wcp-file.wcp'
        path = os.path.join(DIR_FORMATS, fname)
        w = wcp.WcpFile(path)
        self.assertEqual(w.version(), '9')

        self.assertEqual(w.filename(), fname)
        self.assertEqual(w.path(), path)
        self.assertEqual(w.record_count(), 11)
        self.assertEqual(w.sample_count(), 256)
        self.assertEqual(len(w.times()), 256)
        self.assertEqual(len(w.values(0, 0)), 256)

        # Test meta data
        self.maxDiff = None
        self.assertEqual(w.meta_str(), INFO)
        self.assertEqual(w.meta_str(True), INFO_LONG)
        with WarningCollector() as c:
            self.assertEqual(w.info(), INFO)
        self.assertIn('deprecated', c.text())

        # Test Sequence interface
        self.assertEqual(len(w), w.record_count())
        self.assertEqual(np.array(w[0]).shape, (2, 256))
        self.assertEqual(len([r for r in w]), w.record_count())

        # Test SweepSource interface
        self.assertEqual(w.channel_count(), 2)
        self.assertEqual(w.channel_names(), ['Im', 'Vm'])
        self.assertEqual(w.channel_units(), [myokit.units.pA, myokit.units.mV])
        self.assertEqual(w.channel_names(0), 'Im')
        self.assertEqual(w.channel_names(1), 'Vm')
        self.assertEqual(w.channel_units(0), myokit.units.pA)
        self.assertEqual(w.channel_units(1), myokit.units.mV)
        self.assertEqual(w.sweep_count(), w.record_count())
        self.assertTrue(w.equal_length_sweeps())
        self.assertEqual(w.time_unit(), myokit.units.s)

        # Test SweepSource.channel()
        # Without joining
        t0, v0 = w.channel(0)
        t1, v1 = w.channel(1)
        self.assertEqual(len(t0), len(t1), w.sweep_count())
        self.assertEqual(len(v0), len(v1), w.sweep_count())
        self.assertEqual(len(t0[0]), w.sample_count())
        self.assertEqual(len(t1[1]), w.sample_count())
        self.assertEqual(len(v0[2]), w.sample_count())
        self.assertEqual(len(v1[3]), w.sample_count())
        self.assertTrue(np.all(v0[0] == w.channel('Im')[1][0]))
        self.assertTrue(np.all(v0[0] != w.channel('Vm')[1][0]))
        self.assertTrue(np.all(v1[1] == w.channel('Vm')[1][1]))

        # With joining
        x = w.channel(0, join_sweeps=True)
        y = w.channel(1, join_sweeps=True)
        self.assertEqual(len(x), len(y), 2)
        self.assertEqual(len(x[0]), w.sample_count() * w.sweep_count())
        self.assertEqual(len(x[0]), len(x[1]))
        self.assertEqual(len(x[0]), len(y[0]), len(y[1]))
        self.assertTrue(np.all(x[1] == w.channel('Im', True)[1]))
        self.assertTrue(np.all(x[1] != w.channel('Vm', True)[1]))
        self.assertTrue(np.all(y[1] == w.channel('Vm', True)[1]))

        # Channel doesn't exist
        self.assertRaises(IndexError, w.channel, -1)
        self.assertRaises(IndexError, w.channel, 2)
        self.assertRaises(KeyError, w.channel, 'Tom')

        # Conversion to log
        # Without joining
        d = w.log()
        k = ['time']
        for r in range(w.record_count()):
            for c in range(w.channel_count()):
                k.append(f'{r}.{c}.channel')
        self.assertEqual(set(k), set(d.keys()))
        self.assertTrue(np.all(d['time'] == w.channel(0)[0][0]))
        self.assertTrue(np.all(d['1.0.channel'] == w.channel(0)[1][1]))

        # Without joining, use names
        d = w.log(use_names=True)
        k = ['time']
        for c in w.channel_names():
            for r in range(w.record_count()):
                k.append(f'{r}.{c}')
        self.assertEqual(set(k), set(d.keys()))
        self.assertTrue(np.all(d['time'] == w.channel(0)[0][0]))
        self.assertTrue(np.all(d['1.Im'] == w.channel(0)[1][1]))

        # With joining
        d = w.log(join_sweeps=True)
        self.assertEqual(list(d.keys()), ['time', '0.channel', '1.channel'])
        self.assertTrue(np.all(d['time'] == w.channel(0, True)[0]))
        self.assertTrue(np.all(d['0.channel'] == w.channel(0, True)[1]))

        # With joining, use names
        d = w.log(join_sweeps=True, use_names=True)
        self.assertEqual(list(d.keys()), ['time', 'Im', 'Vm'])
        self.assertTrue(np.all(d['time'] == w.channel(0, True)[0]))
        self.assertTrue(np.all(d['Vm'] == w.channel(1, True)[1]))

        # Deprecated methods
        with WarningCollector() as c:
            self.assertEqual(w.records(), w.record_count())
        self.assertIn('deprecated', c.text())
        with WarningCollector() as c:
            self.assertEqual(w.channels(), w.channel_count())
        self.assertIn('deprecated', c.text())
        with WarningCollector() as c:
            e = w.myokit_log()
        self.assertIn('deprecated', c.text())

        # Unsupported da methods
        self.assertEqual(w.da_count(), 0)
        self.assertRaises(NotImplementedError, w.da, 0)
        self.assertRaises(NotImplementedError, w.da_names)
        self.assertRaises(NotImplementedError, w.da_units)
        self.assertRaises(NotImplementedError, w.da_protocol)

    def test_figure_method(self):
        # Tests matplotlib_figure
        # Select matplotlib backend that doesn't require a screen
        import matplotlib
        matplotlib.use('template')
        w = wcp.WcpFile(os.path.join(DIR_FORMATS, 'wcp-file.wcp'))
        f = w.matplotlib_figure()
        self.assertIsInstance(f, matplotlib.figure.Figure)

    def test_figure_method_deprecated(self):
        # Tests matplotlib_figure
        # Select matplotlib backend that doesn't require a screen
        import matplotlib
        matplotlib.use('template')
        w = wcp.WcpFile(os.path.join(DIR_FORMATS, 'wcp-file.wcp'))
        with WarningCollector() as c:
            f = w.plot()
        self.assertIn('deprecated', c.text())
        self.assertIsNone(f, matplotlib.figure.Figure)


if __name__ == '__main__':
    unittest.main()
