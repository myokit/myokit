#!/usr/bin/env python
#
# Tests meta data functions
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
import unittest

import myokit


class MetaTest(unittest.TestCase):

    def test_basic(self):
        """
        Tests the basic meta-data functionality
        """
        # Test assignment with simple and namespaced names
        m = myokit.Model()
        m.meta['bert'] = 'ernie'
        m.meta['bert:ernie'] = 'banaan'

        def f():
            m.meta['bert.ernie'] = 'banaan'
        self.assertRaises(myokit.InvalidMetaDataNameError, f)

        def f():
            m.meta['bert '] = 'banaan'
        self.assertRaises(myokit.InvalidMetaDataNameError, f)

        # Test retrieval
        self.assertEqual(m.meta['bert'], 'ernie')
        self.assertEqual(m.meta['bert:ernie'], 'banaan')

        def f():
            return m.meta['bert.ernie']
        self.assertRaises(myokit.InvalidMetaDataNameError, f)

        # Test overwriting
        m.meta['bert'] = 'verrekijker'
        self.assertEqual(m.meta['bert'], 'verrekijker')

        # Test deletion
        del(m.meta['bert'])
        self.assertRaises(KeyError, lambda: m.meta['bert'])

    def test_parser(self):
        """
        Tests basic meta-data parsing
        """
        # Parse simple model without meta data
        lines = [
            '[[model]]',
            'a.x = 0',
            '[a]',
            't = 0 bind time',
            'dot(x) = 4',
        ]
        m = myokit.parse_model('\n'.join(lines))
        self.assertTrue(m.is_valid())

        # Test simple meta data
        def model(key, value):
            x = list(lines)
            x.insert(1, key + ':' + value)
            m = myokit.parse_model('\n'.join(x))
            self.assertTrue(m.is_valid())
            self.assertEqual(m.meta[key], value)

        def component(key, value):
            m = myokit.parse_model('\n'.join(
                lines + [key + ':' + value]))
            self.assertTrue(m.is_valid())
            self.assertEqual(m.get('a').meta[key], value)

        def variable(key, value):
            m = myokit.parse_model('\n'.join(
                lines + ['    ' + key + ':' + value]))
            self.assertTrue(m.is_valid())
            self.assertEqual(m.get('a.x').meta[key], value)

        def test(key, value):
            model(key, value)
            component(key, value)
            variable(key, value)

        test('vic', 'bob')
        # Test empty property
        test('vic', '')
        # Test namespaced keys
        test('vic:bob', 'uvavu')
        test('vic:bob:eranu', 'uvavu')
        # Test invalid keys
        self.assertRaises(myokit.ParseError, test, 'vic.bob', 'uvavu')


if __name__ == '__main__':
    unittest.main()
