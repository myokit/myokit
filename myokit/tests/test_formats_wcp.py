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

import myokit.formats.wcp as wcp

from myokit.tests import DIR_FORMATS, WarningCollector


class WcpTest(unittest.TestCase):
    """
    Tests the WCP format module.
    """

    def test_data_file(self):
        # Test basic wcp file reading.

        # Load old file from Maastricht
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

        # Test Sequence interface
        self.assertEqual(len(w), w.record_count())
        self.assertEqual(np.array(w[0]).shape, (2, 256))
        self.assertEqual(len([r for r in w]), w.record_count())

        # Test SweepSource interface
        self.assertEqual(w.channel_count(), 2)
        self.assertEqual(w.channel_names(), ['Im', 'Vm'])
        self.assertEqual(w.sweep_count(), w.record_count())

        # Test SweepSource.channel()
        # Without joining
        x = w.channel(0)
        y = w.channel(1)
        self.assertEqual(len(x), len(y), w.sweep_count())
        self.assertEqual(len(x[0]), w.sample_count())
        self.assertEqual(len(x[1]), w.sample_count())
        self.assertEqual(len(x[2]), w.sample_count())
        self.assertTrue(np.all(x[1] == w.channel('Im')[1]))
        self.assertTrue(np.all(x[1] != w.channel('Vm')[1]))
        self.assertTrue(np.all(y[1] == w.channel('Vm')[1]))

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
        self.assertTrue(np.all(d['time'] == w.channel(0)[0]))
        self.assertTrue(np.all(d['1.0.channel'] == w.channel(0)[2]))

        # Without joining, use names
        d = w.log(use_names=True)
        k = ['time']
        for c in w.channel_names():
            for r in range(w.record_count()):
                k.append(f'{r}.{c}')
        self.assertEqual(set(k), set(d.keys()))
        self.assertTrue(np.all(d['time'] == w.channel(0)[0]))
        self.assertTrue(np.all(d['1.Im'] == w.channel(0)[2]))

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

        # Selected channels
        d = w.log(join_sweeps=True, use_names=True, channels=['Im'])
        self.assertEqual(list(d.keys()), ['time', 'Im'])
        d = w.log(join_sweeps=True, use_names=True, channels=[1])
        self.assertEqual(list(d.keys()), ['time', 'Vm'])

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
