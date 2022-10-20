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

from myokit.tests import TemporaryDirectory, WarningCollector


debug = True


# Simple test
config_basic = """
[myokit]
[time]
date_format = TEST_DATE_FORMAT
time_format = TEST_TIME_FORMAT
[gui]
[sundials]
lib = one;two
inc = three;four
[opencl]
lib = five;six
inc = three;eight
"""

# Config with extra bits
config_extra = """
[extra]
setting = 12
sotting=2
str=String value
"""

# Config with empty paths and spaces
config_paths_1 = """
[sundials]
lib = five
inc = three;four;
[opencl]
lib = one;;   two point five;three;
inc =
"""

# Config with empty paths and " ;", which in Python 2 is ignored
config_paths_2 = """
[sundials]
lib = five ; six
inc = three;four;
[opencl]
lib = one ;;   two point five ;three;
inc =
"""


class TestConfig(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        # Import hidden _config module
        path = sys.path
        try:
            sys.path.append(myokit.DIR_MYOKIT)
            import _config as config
        finally:
            sys.path = path

        # Back-up current settings
        cls._compat_no_capture = myokit.COMPAT_NO_CAPTURE
        cls._compat_no_fd_capture = myokit.COMPAT_NO_FD_CAPTURE
        cls._date_format = myokit.DATE_FORMAT
        cls._time_format = myokit.TIME_FORMAT
        cls._force_pyside = myokit.FORCE_PYSIDE
        cls._force_pyside2 = myokit.FORCE_PYSIDE2
        cls._force_pyqt4 = myokit.FORCE_PYQT4
        cls._force_pyqt5 = myokit.FORCE_PYQT5
        cls._sundials_lib = myokit.SUNDIALS_LIB
        cls._sundials_inc = myokit.SUNDIALS_INC
        cls._opencl_lib = myokit.OPENCL_LIB
        cls._opencl_inc = myokit.OPENCL_INC

        # Temporarily change myokit config dir
        cls._dir_user = myokit.DIR_USER
        cls._temp_dir = TemporaryDirectory()
        cls._temp_dir.__enter__()
        myokit.DIR_USER = cls._temp_dir.path()

        # Config module
        cls._config_module = config

        if debug:
            print('setUpClass completed')

    @classmethod
    def tearDownClass(cls):

        # Reset path
        myokit.DIR_USER = cls._dir_user

        # Reset data and time
        myokit.COMPAT_NO_CAPTURE = cls._compat_no_capture
        myokit.COMPAT_NO_FD_CAPTURE = cls._compat_no_fd_capture
        myokit.DATE_FORMAT = cls._date_format
        myokit.TIME_FORMAT = cls._time_format
        myokit.FORCE_PYSIDE = cls._force_pyside
        myokit.FORCE_PYSIDE2 = cls._force_pyside2
        myokit.FORCE_PYQT4 = cls._force_pyqt4
        myokit.FORCE_PYQT5 = cls._force_pyqt5
        myokit.SUNDIALS_LIB = cls._sundials_lib
        myokit.SUNDIALS_INC = cls._sundials_inc
        myokit.OPENCL_LIB = cls._opencl_lib
        myokit.OPENCL_INC = cls._opencl_inc

        # Reload local settings
        cls._config_module._load()

        # Sanity check
        assert myokit.COMPAT_NO_CAPTURE == cls._compat_no_capture
        assert myokit.COMPAT_NO_FD_CAPTURE == cls._compat_no_fd_capture
        assert myokit.DATE_FORMAT != 'TEST_DATE_FORMAT'
        assert myokit.TIME_FORMAT != 'TEST_TIME_FORMAT'
        assert myokit.FORCE_PYSIDE == cls._force_pyside
        assert myokit.FORCE_PYSIDE2 == cls._force_pyside2
        assert myokit.FORCE_PYQT4 == cls._force_pyqt4
        assert myokit.FORCE_PYQT5 == cls._force_pyqt5
        assert myokit.SUNDIALS_LIB != ['one', 'two']
        assert myokit.SUNDIALS_INC != ['three', 'four']
        assert myokit.OPENCL_LIB != ['five', 'six']
        assert myokit.OPENCL_INC != ['three', 'eight']

        if debug:
            print('tearDownClass completed')

    def test_create(self):
        # Test if the `_create` method works.

        # Test _create
        with TemporaryDirectory() as d:
            filename = d.path('test.ini')
            self._config_module._create(filename)
            self.assertTrue(os.path.isfile(filename))
        self.assertFalse(os.path.isfile(filename))

        # No ini file (calls _create())
        path = self._temp_dir.path('myokit.ini')
        if os.path.exists(path):
            os.remove(path)
        self._config_module._load()
        self.assertTrue(os.path.isfile(path))
        os.remove(path)
        self.assertFalse(os.path.isfile(path))

    def test_load_basic(self):
        # Tests basic entries are loaded.
        myokit.SUNDIALS_LIB = []
        myokit.SUNDIALS_INC = []
        myokit.OPENCL_LIB = []
        myokit.OPENCL_INC = []
        myokit.FORCE_PYSIDE = myokit.FORCE_PYSIDE2 = False
        myokit.FORCE_PYQT4 = myokit.FORCE_PYQT5 = False
        with open(self._temp_dir.path('myokit.ini'), 'w') as f:
            f.write(config_basic)
        self._config_module._load()
        self.assertEqual(myokit.DATE_FORMAT, 'TEST_DATE_FORMAT')
        self.assertEqual(myokit.TIME_FORMAT, 'TEST_TIME_FORMAT')
        self.assertFalse(myokit.FORCE_PYSIDE)
        self.assertFalse(myokit.FORCE_PYSIDE2)
        self.assertFalse(myokit.FORCE_PYQT4)
        self.assertFalse(myokit.FORCE_PYQT5)
        self.assertEqual(myokit.SUNDIALS_LIB, ['one', 'two'])
        self.assertEqual(myokit.SUNDIALS_INC, ['three', 'four'])
        self.assertEqual(myokit.OPENCL_LIB, ['five', 'six'])
        self.assertEqual(myokit.OPENCL_INC, ['three', 'eight'])

        # Unknown settings are ignored
        with open(self._temp_dir.path('myokit.ini'), 'w') as f:
            f.write(config_extra)
        self._config_module._load()

    def test_load_empty(self):
        # Test loading with an empty file.

        with open(self._temp_dir.path('myokit.ini'), 'w') as f:
            f.write('')
        self._config_module._load()

    def test_load_paths(self):
        # Test loading of sundials and opencl paths

        # Lists of paths should be filtered for empty values and trimmed
        myokit.SUNDIALS_LIB = []
        myokit.SUNDIALS_INC = []
        myokit.OPENCL_LIB = []
        myokit.OPENCL_INC = []
        with open(self._temp_dir.path('myokit.ini'), 'w') as f:
            f.write(config_paths_1)
        self._config_module._load()
        self.assertEqual(myokit.SUNDIALS_LIB, ['five'])
        self.assertEqual(myokit.SUNDIALS_INC, ['three', 'four'])
        self.assertEqual(
            myokit.OPENCL_LIB,
            ['one', 'two point five', 'three'])
        self.assertEqual(myokit.OPENCL_INC, [])

        # Even if the list contains " ;", which Python 2's config parser treats
        # as a comment
        myokit.SUNDIALS_LIB = []
        myokit.SUNDIALS_INC = []
        myokit.OPENCL_LIB = []
        myokit.OPENCL_INC = []
        with open(self._temp_dir.path('myokit.ini'), 'w') as f:
            f.write(config_paths_2)
        if sys.hexversion < 0x03020000:
            self.assertRaises(ImportError, self._config_module._load)
        else:
            self._config_module._load()
            self.assertEqual(myokit.SUNDIALS_LIB, ['five', 'six'])
            self.assertEqual(myokit.SUNDIALS_INC, ['three', 'four'])
            self.assertEqual(
                myokit.OPENCL_LIB,
                ['one', 'two point five', 'three'])
            self.assertEqual(myokit.OPENCL_INC, [])

    def test_load_gui_backend(self):
        # Tests setting the GUI back end

        # Qt gui options
        with open(self._temp_dir.path('myokit.ini'), 'w') as f:
            f.write('[gui]\nbackend=pyqt4\n')
        self._config_module._load()
        self.assertFalse(myokit.FORCE_PYSIDE)
        self.assertFalse(myokit.FORCE_PYSIDE2)
        self.assertTrue(myokit.FORCE_PYQT4)
        self.assertFalse(myokit.FORCE_PYQT5)

        with open(self._temp_dir.path('myokit.ini'), 'w') as f:
            f.write('[gui]\nbackend=pyqt5\n')
        self._config_module._load()
        self.assertFalse(myokit.FORCE_PYSIDE)
        self.assertFalse(myokit.FORCE_PYSIDE2)
        self.assertFalse(myokit.FORCE_PYQT4)
        self.assertTrue(myokit.FORCE_PYQT5)

        with open(self._temp_dir.path('myokit.ini'), 'w') as f:
            f.write('[gui]\nbackend=pyside\n')
        self._config_module._load()
        self.assertTrue(myokit.FORCE_PYSIDE)
        self.assertFalse(myokit.FORCE_PYSIDE2)
        self.assertFalse(myokit.FORCE_PYQT4)
        self.assertFalse(myokit.FORCE_PYQT5)

        with open(self._temp_dir.path('myokit.ini'), 'w') as f:
            f.write('[gui]\nbackend=pyside2\n')
        self._config_module._load()
        self.assertFalse(myokit.FORCE_PYSIDE)
        self.assertTrue(myokit.FORCE_PYSIDE2)
        self.assertFalse(myokit.FORCE_PYQT4)
        self.assertFalse(myokit.FORCE_PYQT5)

        # Empty has no effect
        with open(self._temp_dir.path('myokit.ini'), 'w') as f:
            f.write('[gui]\nbackend=\n')
        with WarningCollector() as c:
            self._config_module._load()
        self.assertEqual(c.text(), '')
        self.assertFalse(myokit.FORCE_PYSIDE)
        self.assertTrue(myokit.FORCE_PYSIDE2)
        self.assertFalse(myokit.FORCE_PYQT4)
        self.assertFalse(myokit.FORCE_PYQT5)

        # Invalid raises warning
        with open(self._temp_dir.path('myokit.ini'), 'w') as f:
            f.write('[gui]\nbackend=lalala\n')
        with WarningCollector() as c:
            self._config_module._load()
        self.assertIn('Expected values for backend are', c.text())
        self.assertTrue(myokit.FORCE_PYSIDE2)

    def test_load_compat_no_capture(self):
        # Tests loading compatibility option: no_capture

        myokit.COMPAT_NO_CAPTURE = False
        with open(self._temp_dir.path('myokit.ini'), 'w') as f:
            f.write('[compatibility]\nno_capture = True\n')
        self._config_module._load()
        self.assertTrue(myokit.COMPAT_NO_CAPTURE)

        with open(self._temp_dir.path('myokit.ini'), 'w') as f:
            f.write('[compatibility]\nno_capture = False\n')
        self._config_module._load()
        self.assertFalse(myokit.COMPAT_NO_CAPTURE)

        # Empty has no effect
        with open(self._temp_dir.path('myokit.ini'), 'w') as f:
            f.write('[compatibility]\nno_capture = \n')
        with WarningCollector() as c:
            self._config_module._load()
        self.assertEqual(c.text(), '')
        self.assertFalse(myokit.COMPAT_NO_CAPTURE)
        myokit.COMPAT_NO_CAPTURE = True
        with WarningCollector() as c:
            self._config_module._load()
        self.assertEqual(c.text(), '')
        self.assertTrue(myokit.COMPAT_NO_CAPTURE)

        # Invalid raises warning
        with open(self._temp_dir.path('myokit.ini'), 'w') as f:
            f.write('[compatibility]\nno_capture = hiya\n')
        with WarningCollector() as c:
            self._config_module._load()
        self.assertTrue(myokit.COMPAT_NO_CAPTURE)
        self.assertIn('Expected values for no_capture are', c.text())

    def test_load_compat_no_capture_fd(self):
        # Tests loading compatibility option: no_fd_capture

        myokit.COMPAT_NO_FD_CAPTURE = False
        with open(self._temp_dir.path('myokit.ini'), 'w') as f:
            f.write('[compatibility]\nno_fd_capture = True\n')
        self._config_module._load()
        self.assertTrue(myokit.COMPAT_NO_FD_CAPTURE)

        with open(self._temp_dir.path('myokit.ini'), 'w') as f:
            f.write('[compatibility]\nno_fd_capture = False\n')
        self._config_module._load()
        self.assertFalse(myokit.COMPAT_NO_FD_CAPTURE)

        # Empty has no effect
        with open(self._temp_dir.path('myokit.ini'), 'w') as f:
            f.write('[compatibility]\nno_fd_capture = \n')
        with WarningCollector() as c:
            self._config_module._load()
        self.assertEqual(c.text(), '')
        self.assertFalse(myokit.COMPAT_NO_FD_CAPTURE)
        myokit.COMPAT_NO_FD_CAPTURE = True
        with WarningCollector() as c:
            self._config_module._load()
        self.assertEqual(c.text(), '')
        self.assertTrue(myokit.COMPAT_NO_FD_CAPTURE)

        # Invalid raises warning
        with open(self._temp_dir.path('myokit.ini'), 'w') as f:
            f.write('[compatibility]\nno_fd_capture = hiya\n')
        with WarningCollector() as c:
            self._config_module._load()
        self.assertTrue(myokit.COMPAT_NO_FD_CAPTURE)
        self.assertIn('Expected values for no_fd_capture are', c.text())


if __name__ == '__main__':
    unittest.main(verbosity=2)
