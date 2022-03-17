#!/usr/bin/env python3
#
# Tests the OpenCL info class.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import unittest

import myokit

from myokit.tests import TemporaryDirectory, OpenCL_FOUND

# Strings in Python2 and Python3
try:
    basestring
except NameError:
    basestring = str


@unittest.skipIf(not OpenCL_FOUND, 'OpenCL not found on this system.')
class OpenCLTest(unittest.TestCase):
    """
    Tests the OpenCL info class.
    """

    def test_available(self):
        # Tested as condition to get in, so must be true
        self.assertTrue(myokit.OpenCL.available())

    def test_current_info(self):
        # Tests the method to query the current device
        self.assertIsInstance(
            myokit.OpenCL.current_info(), myokit.OpenCLPlatformInfo)
        self.assertIsInstance(myokit.OpenCL.current_info(True), basestring)

    def test_info(self):
        # Tests the method to query the current device
        self.assertIsInstance(myokit.OpenCL.info(), myokit.OpenCLInfo)
        self.assertIsInstance(myokit.OpenCL.info(True), basestring)

    def test_load_save_selection(self):
        # Tests the load_selection method
        import myokit._sim.opencl
        org_name = myokit._sim.opencl.SETTINGS_FILE
        try:
            with TemporaryDirectory() as d:
                fname = d.path('opencl-temp.ini')
                myokit._sim.opencl.SETTINGS_FILE = fname

                # Save None and None
                myokit.OpenCL.save_selection(None, None)
                platform, device = myokit.OpenCL.load_selection()
                self.assertIsNone(platform)
                self.assertIsNone(device)

                myokit.OpenCL.save_selection(None, 'bert')
                platform, device = myokit.OpenCL.load_selection()
                self.assertIsNone(platform)
                self.assertEqual(device, 'bert')

                myokit.OpenCL.save_selection('ernie', None)
                platform, device = myokit.OpenCL.load_selection()
                self.assertEqual(platform, 'ernie')
                self.assertIsNone(device)

                myokit.OpenCL.save_selection('ernie', 'bert')
                platform, device = myokit.OpenCL.load_selection()
                self.assertEqual(platform, 'ernie')
                self.assertEqual(device, 'bert')

        finally:
            myokit._sim.opencl.SETTINGS_FILE = org_name

    def test_selection_info(self):
        # Tests getting info about devices, specifically for device selection
        info = myokit.OpenCL.selection_info()
        self.assertIsInstance(info, list)
        self.assertGreater(len(info), 0)
        item = info[0]
        self.assertEqual(len(item), 3)
        platform, device, specs = item
        self.assertIsInstance(platform, basestring)
        self.assertIsInstance(device, basestring)
        self.assertIsInstance(specs, basestring)

    def test_supported(self):
        # Tested as condition to get in, so must be true
        self.assertTrue(myokit.OpenCL.supported())

    def test_hidden(self):
        # Tests some private methods of the opencl module
        import myokit._sim.opencl as o

        # Test bytesize
        self.assertEqual(o.bytesize(3), '3 B')
        self.assertEqual(o.bytesize(1023), '1023 B')
        self.assertEqual(o.bytesize(1024), '1 KB')
        self.assertEqual(o.bytesize(2048), '2 KB')
        self.assertEqual(o.bytesize(1048575)[-2:], 'KB')
        self.assertEqual(o.bytesize(1048576), '1 MB')
        self.assertEqual(o.bytesize(1073741823)[-2:], 'MB')
        self.assertEqual(o.bytesize(1073741824), '1 GB')

        # Test clockspeed
        self.assertEqual(o.clockspeed(100), '100 MHz')
        self.assertEqual(o.clockspeed(999), '999 MHz')
        self.assertEqual(o.clockspeed(1000), '1 GHz')
        self.assertEqual(o.clockspeed(1200), '1.2 GHz')


if __name__ == '__main__':
    unittest.main()
