#!/usr/bin/env python
#
# Tests the system() method
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import unittest

import myokit


# Strings in Python2 and Python3
try:
    basestring
except NameError:   # pragma: no cover
    basestring = str


class SystemInfoTest(unittest.TestCase):
    """
    Tests the system info method.
    """
    def test_system_info(self):
        import matplotlib
        matplotlib.use('template')

        self.assertIsInstance(myokit.system(), basestring)
        with myokit.PyCapture():
            myokit.system(live_printing=True)


if __name__ == '__main__':
    unittest.main()
