#!/usr/bin/env python3
#
# Tests the WCP format module.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import os
import unittest
import numpy as np

import myokit.formats.wcp as wcp

from myokit.tests import DIR_FORMATS


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

        self.assertEqual(w.channels(), 2)
        self.assertEqual(w.channel_names(), ['Im', 'Vm'])
        self.assertEqual(w.filename(), fname)
        self.assertEqual(w.path(), path)
        self.assertEqual(w.records(), 11)
        #print(w.sampling_interval())
        self.assertEqual(len(w.times()), 256)
        self.assertEqual(len(w.values(0, 0)), 256)

    def test_data_log_conversion(self):
        # Test conversion to a data log.

        w = wcp.WcpFile(os.path.join(DIR_FORMATS, 'wcp-file.wcp'))
        d = w.myokit_log()
        keys = ['time']
        for cn in w.channel_names():
            for i in range(w.records()):
                keys.append(str(i) + '.' + cn)
        self.assertEqual(set(d.keys()), set(keys))
        self.assertEqual(len(d.time()), 256)
        self.assertTrue(np.all(d.time() == w.times()))

    def test_plot_method(self):
        # Test the plot method.

        # Select matplotlib backend that doesn't require a screen
        import matplotlib
        matplotlib.use('template')

        # Load and create plots
        w = wcp.WcpFile(os.path.join(DIR_FORMATS, 'wcp-file.wcp'))
        w.plot()


if __name__ == '__main__':
    unittest.main()
