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

from shared import TemporaryDirectory

# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp


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
            self.assertEqual(len(list(x.warnings())), 0)
            x.warn('Everything is awful.')
            self.assertTrue(x.has_warnings())
            self.assertEqual(len(list(x.warnings())), 1)
            self.assertEqual(list(x.warnings()), ['Everything is awful.'])
            x.clear_warnings()
            self.assertFalse(x.has_warnings())
            self.assertEqual(len(list(x.warnings())), 0)
            x.warn('Things are not good.')
            self.assertTrue(x.has_warnings())
            self.assertEqual(len(list(x.warnings())), 1)
            self.assertEqual(list(x.warnings()), ['Things are not good.'])
            z = x.text().splitlines()

        self.assertEqual(c.text(), '')
        y = [
            '-' * 79,
            ' ' * 26 + 'Hello there this is a line',
            '-' * 79,
            'Text',
            '-' * 79,
            'More text',
        ]
        for i, line in enumerate(z):
            self.assertEqual(line, y[i])
        self.assertEqual(len(z), len(y))

        # Test clearing
        x.clear()
        self.assertEqual(x.text(), '')

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


class ExporterTest(unittest.TestCase):
    """
    Tests some parts of :class:`Exporter` that are not tested when testing the
    various exporter implementations.
    """
    def test_writable_dir(self):
        """
        Tests :meth:`_test_writable_dir` for existing paths.
        """
        m, p, x = myokit.load('example')
        e = myokit.formats.exporter('ansic')
        with TemporaryDirectory() as d:

            # Create in new dir
            path = d.path('new-dir')
            e.runnable(path, m, p)
            self.assertNotIn('Using existing', e.logger().text())

            # Create again, in same dir (should be ok)
            e._logger.clear()
            e.runnable(path, m, p)
            self.assertIn('Using existing', e.logger().text())

            # Create at location of file: not allowed!
            path = d.path('file')
            with open(path, 'w') as f:
                f.write('Hello')
            self.assertRaisesRegex(
                myokit.ExportError, 'file exists', e.runnable, path, m, p)


if __name__ == '__main__':
    unittest.main()
