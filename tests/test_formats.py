#!/usr/bin/env python
#
# Tests infrastructure (e.g. the text logger) from the formats module.
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
import myokit.formats


class FormatsTest(unittest.TestCase):
    """
    Tests infrastructure (e.g. the text logger) from the formats module.
    """

    def test_text_logger(self):
        """
        Tests myokit.formats.TextLogger().
        """

        # Test basic methods
        with myokit.PyCapture() as c:
            x = myokit.formats.TextLogger()
            self.assertFalse(x.is_live())
            x.log_flair('Hello there this is a line')
            x.log('Text')
            x.log_line()
            x.log('More text')
            self.assertFalse(x.has_warnings())
            x.warn('Everything is awful.')
            self.assertTrue(x.has_warnings())
            x.clear_warnings()
            self.assertFalse(x.has_warnings())
            x.warn('Things are not good.')
            self.assertTrue(x.has_warnings())
            x = x.text().splitlines()
        self.assertEqual(c.text(), '')
        y = [
            '-' * 79,
            ' ' * 26 + 'Hello there this is a line',
            '-' * 79,
            'Text',
            '-' * 79,
            'More text',
        ]
        for i, line in enumerate(x):
            self.assertEqual(line, y[i])
        self.assertEqual(len(x), len(y))

        # Test live writing
        with myokit.PyCapture() as c:
            x = myokit.formats.TextLogger()
            self.assertFalse(x.is_live())
            x.set_live(True)
            self.assertTrue(x.is_live())
            x.log_flair('Hello there this is a line')
            x.log('Text')
            x.log_line()
            x.log('More text')
            x.warn('Everything is awful.')
            x.clear_warnings()
            x.warn('Things are not good.')
            x = x.text().splitlines()
        for i, line in enumerate(x):
            self.assertEqual(line, y[i])
        self.assertEqual(len(x), len(y))
        z = c.text().splitlines()
        for i, line in enumerate(z):
            self.assertEqual(line, y[i])
        self.assertEqual(len(z), len(y))

        # Test warning logging
        with myokit.PyCapture() as c:
            x = myokit.formats.TextLogger()
            self.assertFalse(x.is_live())
            x.log_flair('Hello there this is a line')
            x.log('Text')
            x.log_line()
            x.log('More text')
            x.warn('Everything is awful.')
            x.clear_warnings()
            x.warn('Things are not good.')
            self.assertTrue(x.has_warnings())
            x.log_warnings()
            self.assertFalse(x.has_warnings())
            x.warn('It is not going very well.')
            self.assertTrue(x.has_warnings())
            x.log_warnings()
            self.assertFalse(x.has_warnings())
            x.warn('Aaaaaah.')
            x.warn('Oh no.')
            self.assertTrue(x.has_warnings())
            x.log_warnings()
            self.assertFalse(x.has_warnings())
            x = x.text().splitlines()
        self.assertEqual(c.text(), '')
        y = [
            '-' * 79,
            ' ' * 26 + 'Hello there this is a line',
            '-' * 79,
            'Text',
            '-' * 79,
            'More text',
            '-' * 79,
            ' ' * 29 + 'One warning generated',
            '-' * 79,
            '(1) Things are not good.',
            '-' * 79,
            '-' * 79,
            ' ' * 29 + 'One warning generated',
            '-' * 79,
            '(1) It is not going very well.',
            '-' * 79,
            '-' * 79,
            ' ' * 29 + '2 Warnings generated',
            '-' * 79,
            '(1) Aaaaaah.',
            '(2) Oh no.',
            '-' * 79,
        ]
        for i, line in enumerate(x):
            self.assertEqual(line, y[i])
        self.assertEqual(len(x), len(y))


if __name__ == '__main__':
    unittest.main()
