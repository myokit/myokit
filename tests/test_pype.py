#!/usr/bin/env python
#
# Tests the parser
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import os
import unittest

import myokit, myokit.pype

from shared import TemporaryDirectory, DIR_DATA


class PypeTest(unittest.TestCase):

    def test_process_errors(self):
        """
        Tests error handling in the ``process`` method.
        """

        # Process method takes a dict
        e = myokit.pype.TemplateEngine()
        self.assertRaisesRegexp(
            ValueError, 'dict', e.process, 'file.txt', [])

        self.error("""<?print(1/0) ?>""", {}, 'ZeroDivisionError')

    def error(self, template, args, message):
        """
        Runs a template, returns any error raised.
        """
        with TemporaryDirectory() as d:
            path = d.path('template')
            with open(path, 'w') as f:
                f.write(template)
            e = myokit.pype.TemplateEngine()
            try:
                e.process(path, args)
            except myokit.pype.PypeError:
                # Check expected message in error details
                self.assertIn(message, e.error_details())
                return
            raise RuntimeError('PypeError not raised.')


if __name__ == '__main__':
    unittest.main()
