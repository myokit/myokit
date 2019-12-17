#!/usr/bin/env python
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


class VersionTest(unittest.TestCase):
    """
    Tests the version() method.
    """
    def test_version(self):

        # Raw version
        raw = myokit.version(raw=True)
        self.assertIsInstance(raw, basestring)
        parts = raw.split('.')
        self.assertTrue(len(parts) in [3, 4])

        # Formatted version
        v = myokit.version()
        v = v.splitlines()
        self.assertEqual(len(v), 3)


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
