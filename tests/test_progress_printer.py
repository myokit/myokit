#!/usr/bin/env python
#
# Tests the PSimulation class.
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import unittest
import re
import time

import myokit


class ProgressPrinterTests(unittest.TestCase):
    """
    Tests the :class:`ProgressPrinter`.
    """
    def test_progress_printer(self):
        """ Test basic functionality. """

        # Zero call
        with myokit.PyCapture() as c:
            p = myokit.ProgressPrinter()
            self.assertTrue(p.update(0))
        pattern1 = re.compile(
            '\[[0-9]{1}\.[0-9]{1} minutes\] [0-9]+(.[0-9])? % done')
        lines = c.text().splitlines()
        self.assertTrue(len(lines) > 0)
        for line in lines:
            self.assertTrue(pattern1.match(line))

        # Normal call
        with myokit.PyCapture() as c:
            p = myokit.ProgressPrinter()
            self.assertTrue(p.update(0.49))
        pattern2 = re.compile(
            '\[[0-9]{1}\.[0-9]{1} minutes] [0-9]+(.[0-9])? % done,'
            ' estimated [0-9]{1} seconds remaining')
        lines = c.text().splitlines()
        self.assertTrue(len(lines) > 0)
        for line in lines:
            self.assertTrue(pattern2.match(line))

        # Call that will take minutes
        with myokit.PyCapture() as c:
            p = myokit.ProgressPrinter()
            time.sleep(0.1)
            self.assertTrue(p.update(1e-3))
        self.assertIn('minutes remaining', c.text())

        # Note: Printer must be created withing PyCapture, otherwise it will
        # print to stdout (which won't have been redirected yet).

        # Status every ten percent
        with myokit.PyCapture() as c:
            p = myokit.ProgressPrinter(digits=-1)
            self.assertTrue(p.update(0))
            self.assertTrue(p.update(0.08))
            self.assertTrue(p.update(0.18))
            self.assertTrue(p.update(0.19))
            self.assertTrue(p.update(0.199))
            self.assertTrue(p.update(1))
        lines = c.text().splitlines()
        self.assertTrue(len(lines), 3)
        self.assertTrue(pattern1.match(lines[0]))
        self.assertTrue(pattern2.match(lines[1]))
        self.assertTrue(pattern2.match(lines[2]))


if __name__ == '__main__':
    unittest.main()
