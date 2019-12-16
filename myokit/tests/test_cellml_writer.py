#!/usr/bin/env python
#
# Tests the CellML 1.0 writer
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import unittest

import myokit.formats.cellml.cellml_1 as cellml
import myokit.formats.cellml.writer_1 as writer
import myokit.formats.cellml.parser_1 as parser

# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp


class TestCellMLWriter(unittest.TestCase):
    """ Tests for cellml.Writer. """

    def test_groups(self):
        """ Tests if encapsulation relationships are written to disk. """

        # Create a model with
        #      d
        #   a     e
        #       f   c
        #             b
        #
        m1 = cellml.Model('m')
        a = m1.add_component('a')
        b = m1.add_component('b')
        c = m1.add_component('c')
        d = m1.add_component('d')
        e = m1.add_component('e')
        f = m1.add_component('f')
        a.set_parent(d)
        e.set_parent(d)
        f.set_parent(e)
        c.set_parent(e)
        b.set_parent(c)

        xml = writer.write_string(m1)
        m2 = parser.parse_string(xml)
        a, b, c, d, e, f = [m2.component(x) for x in 'abcdef']
        self.assertIs(a.parent(), d)
        self.assertIs(e.parent(), d)
        self.assertIs(f.parent(), e)
        self.assertIs(c.parent(), e)
        self.assertIs(b.parent(), c)


if __name__ == '__main__':
    unittest.main()
