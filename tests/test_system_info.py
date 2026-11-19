#!/usr/bin/env python3
#
# Tests the system() method
#
# This file is part of Myokit.
# See https://github.com/myokit/myokit for copyright, sharing, and licensing.
#
import unittest

import myokit


class SystemInfoTest(unittest.TestCase):
    """
    Tests the system info method.
    """

    def test_system_info(self):
        import matplotlib
        matplotlib.use('template')

        self.assertIsInstance(myokit.system(), str)
        with myokit.tools.capture():
            myokit.system(live_printing=True)


if __name__ == '__main__':
    unittest.main()
