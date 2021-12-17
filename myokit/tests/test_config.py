#!/usr/bin/env python3
#
# Tests the exporters from the format module.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import os
import sys
import unittest

import myokit

from shared import TemporaryDirectory


# Empty config
config1 = """
"""

# Config with lots of settings
config2 = """
[myokit]
[time]
date_format = TEST_DATE_FORMAT
time_format = TEST_TIME_FORMAT
[debug]
line_numbers=True
[gui]
[sundials]
lib = one;two
inc = three;four
[opencl]
lib = five;six
inc = three;eight
"""

# Config with empty paths and spaces
config_empties_1 = """
[sundials]
lib = five
inc = three;four;
[opencl]
lib = one;;   two point five;three;
inc =
"""

# Config with empty paths and " ;", which in Python 2 is ignored
config_empties_2 = """
[sundials]
lib = five ; six
inc = three;four;
[opencl]
lib = one ;;   two point five ;three;
inc =
"""

# Qt options
config_pyside = """
[gui]
backend=pyside
"""

config_pyside2 = """
[gui]
backend=pyside2
"""

config_pyqt4 = """
[gui]
backend=pyqt4
"""

config_pyqt5 = """
[gui]
backend=pyqt5
"""

# Config with extra bits
config3 = """
[extra]
setting = 12
sotting=2
str=String value
"""


class TestConfig(unittest.TestCase):

    def test_create(self):
        # Test if the `_create` method works.

        # Import hidden _config module
        path = sys.path
        try:
            sys.path.append(myokit.DIR_MYOKIT)
            import _config as config
        finally:
            sys.path = path

        # Test _create
        with TemporaryDirectory() as d:
            filename = d.path('test.ini')
            config._create(filename)
            self.assertTrue(os.path.isfile(filename))
        self.assertFalse(os.path.isfile(filename))

    def test_load_read(self):
        # Test if the `_load` method works, when a config file exists.

        # Import hidden _config module
        path = sys.path
        try:
            sys.path.append(myokit.DIR_MYOKIT)
            import _config as config
        finally:
            sys.path = path

        # Back-up current settings
        date_format = myokit.DATE_FORMAT
        time_format = myokit.TIME_FORMAT
        debug_numbers = myokit.DEBUG_LINE_NUMBERS
        force_pyside = myokit.FORCE_PYSIDE
        force_pyside2 = myokit.FORCE_PYSIDE2
        force_pyqt4 = myokit.FORCE_PYQT4
        force_pyqt5 = myokit.FORCE_PYQT5
        sundials_lib = myokit.SUNDIALS_LIB
        sundials_inc = myokit.SUNDIALS_INC
        opencl_lib = myokit.OPENCL_LIB
        opencl_inc = myokit.OPENCL_INC

        # Change myokit config dir temporarily
        path = myokit.DIR_USER
        try:
            with TemporaryDirectory() as d:
                myokit.DIR_USER = d.path()

                # Simple test
                with open(d.path('myokit.ini'), 'w') as f:
                    f.write(config1)
                config._load()

                # Full values, PySide gui
                myokit.SUNDIALS_LIB = []
                myokit.SUNDIALS_INC = []
                myokit.OPENCL_LIB = []
                myokit.OPENCL_INC = []
                myokit.FORCE_PYSIDE = myokit.FORCE_PYSIDE2 = False
                myokit.FORCE_PYQT4 = myokit.FORCE_PYQT5 = False
                with open(d.path('myokit.ini'), 'w') as f:
                    f.write(config2)
                config._load()
                self.assertEqual(myokit.DATE_FORMAT, 'TEST_DATE_FORMAT')
                self.assertEqual(myokit.TIME_FORMAT, 'TEST_TIME_FORMAT')
                self.assertTrue(myokit.DEBUG_LINE_NUMBERS)
                self.assertFalse(myokit.FORCE_PYSIDE)
                self.assertFalse(myokit.FORCE_PYSIDE2)
                self.assertFalse(myokit.FORCE_PYQT4)
                self.assertFalse(myokit.FORCE_PYQT5)
                self.assertEqual(myokit.SUNDIALS_LIB, ['one', 'two'])
                self.assertEqual(myokit.SUNDIALS_INC, ['three', 'four'])
                self.assertEqual(myokit.OPENCL_LIB, ['five', 'six'])
                self.assertEqual(myokit.OPENCL_INC, ['three', 'eight'])

                # Lists of paths should be filtered for empty values and
                # trimmed
                myokit.SUNDIALS_LIB = []
                myokit.SUNDIALS_INC = []
                myokit.OPENCL_LIB = []
                myokit.OPENCL_INC = []
                with open(d.path('myokit.ini'), 'w') as f:
                    f.write(config_empties_1)
                config._load()
                self.assertEqual(myokit.SUNDIALS_LIB, ['five'])
                self.assertEqual(myokit.SUNDIALS_INC, ['three', 'four'])
                self.assertEqual(
                    myokit.OPENCL_LIB,
                    ['one', 'two point five', 'three'])
                self.assertEqual(myokit.OPENCL_INC, [])

                # Even if the list contains " ;", which Python 2's config
                # parser treats as a comment
                myokit.SUNDIALS_LIB = []
                myokit.SUNDIALS_INC = []
                myokit.OPENCL_LIB = []
                myokit.OPENCL_INC = []
                with open(d.path('myokit.ini'), 'w') as f:
                    f.write(config_empties_2)
                if sys.hexversion < 0x03020000:
                    self.assertRaises(ImportError, config._load)
                else:
                    config._load()
                    self.assertEqual(myokit.SUNDIALS_LIB, ['five', 'six'])
                    self.assertEqual(myokit.SUNDIALS_INC, ['three', 'four'])
                    self.assertEqual(
                        myokit.OPENCL_LIB,
                        ['one', 'two point five', 'three'])
                    self.assertEqual(myokit.OPENCL_INC, [])

                # Qt gui options
                with open(d.path('myokit.ini'), 'w') as f:
                    f.write(config_pyqt4)
                config._load()
                self.assertFalse(myokit.FORCE_PYSIDE)
                self.assertFalse(myokit.FORCE_PYSIDE2)
                self.assertTrue(myokit.FORCE_PYQT4)
                self.assertFalse(myokit.FORCE_PYQT5)

                with open(d.path('myokit.ini'), 'w') as f:
                    f.write(config_pyqt5)
                config._load()
                self.assertFalse(myokit.FORCE_PYSIDE)
                self.assertFalse(myokit.FORCE_PYSIDE2)
                self.assertFalse(myokit.FORCE_PYQT4)
                self.assertTrue(myokit.FORCE_PYQT5)

                with open(d.path('myokit.ini'), 'w') as f:
                    f.write(config_pyside)
                config._load()
                self.assertTrue(myokit.FORCE_PYSIDE)
                self.assertFalse(myokit.FORCE_PYSIDE2)
                self.assertFalse(myokit.FORCE_PYQT4)
                self.assertFalse(myokit.FORCE_PYQT5)

                with open(d.path('myokit.ini'), 'w') as f:
                    f.write(config_pyside2)
                config._load()
                self.assertFalse(myokit.FORCE_PYSIDE)
                self.assertTrue(myokit.FORCE_PYSIDE2)
                self.assertFalse(myokit.FORCE_PYQT4)
                self.assertFalse(myokit.FORCE_PYQT5)

                # Odd ini file
                with open(d.path('myokit.ini'), 'w') as f:
                    f.write(config3)
                config._load()

                # No ini file (calls _create())
                os.remove(d.path('myokit.ini'))
                config._load()

        finally:
            # Reset path
            myokit.DIR_USER = path

            # Reset data and time
            myokit.DATE_FORMAT = date_format
            myokit.TIME_FORMAT = time_format
            myokit.DEBUG_LINE_NUMBERS = debug_numbers
            myokit.FORCE_PYSIDE = force_pyside
            myokit.FORCE_PYQT4 = force_pyqt4
            myokit.FORCE_PYQT5 = force_pyqt5
            myokit.SUNDIALS_LIB = sundials_lib
            myokit.SUNDIALS_INC = sundials_inc
            myokit.OPENCL_LIB = opencl_lib
            myokit.OPENCL_INC = opencl_inc

            # Reload local settings
            config._load()

            # Sanity check
            self.assertNotEqual(myokit.DATE_FORMAT, 'TEST_DATE_FORMAT')
            self.assertNotEqual(myokit.TIME_FORMAT, 'TEST_TIME_FORMAT')
            self.assertEqual(myokit.DEBUG_LINE_NUMBERS, debug_numbers)
            self.assertEqual(myokit.FORCE_PYSIDE, force_pyside)
            self.assertEqual(myokit.FORCE_PYQT4, force_pyqt4)
            self.assertEqual(myokit.FORCE_PYQT5, force_pyqt5)
            self.assertNotEqual(myokit.SUNDIALS_LIB, ['one', 'two'])
            self.assertNotEqual(myokit.SUNDIALS_INC, ['three', 'four'])
            self.assertNotEqual(myokit.OPENCL_LIB, ['five', 'six'])
            self.assertNotEqual(myokit.OPENCL_INC, ['three', 'eight'])


if __name__ == '__main__':
    unittest.main()
