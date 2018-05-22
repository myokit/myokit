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
import time

import myokit


class ProgressPrinterTests(unittest.TestCase):
    """
    Tests the :class:`ProgressPrinter`.
    """
    def test_progress_printer(self):

        # Zero call
        with myokit.PyCapture() as c:
            p = myokit.ProgressPrinter()
            self.assertTrue(p.update(0))
        self.assertEqual(c.text(), '[0.0 minutes] 0.0 % done\n')

        # Normal call
        with myokit.PyCapture() as c:
            p = myokit.ProgressPrinter()
            self.assertTrue(p.update(0.49))
        self.assertEqual(
            c.text(),
            '[0.0 minutes] 49.0 % done, estimated 0 seconds remaining\n')

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
            self.assertIn('0.0 %', c.text())
            c.clear()
            self.assertTrue(p.update(0.08))
            self.assertEqual(c.text(), '')
            self.assertTrue(p.update(0.18))
            self.assertIn(c.text(), '10.0 %')


if __name__ == '__main__':
    unittest.main()
