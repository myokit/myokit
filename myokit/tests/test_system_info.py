#!/usr/bin/env python3
#
# Tests the system() method
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
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
        with myokit.tools.capture():
            myokit.system(live_printing=True)


if __name__ == '__main__':
    unittest.main()
