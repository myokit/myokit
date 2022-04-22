#!/usr/bin/env python3
#
# Tests the parser
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import unittest

import myokit
import myokit.pype

from myokit.tests import TemporaryDirectory

# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp


class PypeTest(unittest.TestCase):

    def test_process_errors(self):
        # Test error handling in the ``process`` method.

        # Process method takes a dict
        e = myokit.pype.TemplateEngine()
        self.assertRaisesRegex(
            ValueError, 'dict', e.process, 'file.txt', [])

        with myokit.tools.capture():

            # Test not-a-file
            self.assertRaises(IOError, e.process, 'file.txt', {})

            # Test simple error
            self.e("""<?print(1/0) ?>""", {}, 'ZeroDivisionError')

            # Test closing without opening
            self.e("""Hello ?>""", {}, 'without opening tag')

            # Opening without closing is allowed
            self.e("""<?print('hi')""", {})

            # Nested opening
            self.e(
                """<?print('hi')<?print('hello')?>""",
                {},
                'Nested opening tag',
            )

            # Too much inside <?=?>
            self.e("""<?=if 1 > 2: print('hi')?>""", {}, 'contain a single')
            self.e("""<?=print(1); print('hi')?>""", {}, 'contain a single')

            # Triple quote should be allowed
            self.e('''Hello"""string"""yes''', {})

            # OSError from inside pype
            self.e("""Hello<?open('file.txt', 'r')?>yes""", {}, 'No such file')

    def e(self, template, args, expected_error=None):
        """
        Runs a template, if an error is expected it checks if it's the right
        one.
        """
        with TemporaryDirectory() as d:
            path = d.path('template')
            with open(path, 'w') as f:
                f.write(template)
            e = myokit.pype.TemplateEngine()
            if expected_error is None:
                e.process(path, args)
            else:
                try:
                    e.process(path, args)
                except myokit.pype.PypeError:
                    # Check expected message in error details
                    self.assertIn(expected_error, e.error_details())
                    return
                raise RuntimeError('PypeError not raised.')


if __name__ == '__main__':
    unittest.main()
