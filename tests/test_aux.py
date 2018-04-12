#!/usr/bin/env python
#
# Tests the myokit._aux module.
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import os
import sys
import unittest

import myokit

from shared import DIR_DATA, TemporaryDirectory


class AuxText(unittest.TestCase):
    """
    Tests various methods from myokit._aux.
    """
    def test_date(self):
        """ Test date formatting method. """
        import time
        for i in range(3):
            a = time.strftime(myokit.DATE_FORMAT)
            b = myokit._aux.date()
            if a == b:
                break
        self.assertEqual(a, b)

    def test_time(self):
        """ Test time formatting method. """
        import time
        for i in range(3):
            a = time.strftime(myokit.TIME_FORMAT)
            b = myokit._aux.time()
            if a == b:
                break
        self.assertEqual(a, b)

    def test_natural_sort(self):
        """ Test natural sort key method. """
        a = ['a12', 'a3', 'a11', 'a2', 'a10', 'a1']
        b = ['a1', 'a2', 'a3', 'a10', 'a11', 'a12']
        self.assertNotEqual(a, b)
        a.sort()
        self.assertNotEqual(a, b)
        a.sort(key=lambda x: myokit.natural_sort_key(x))
        self.assertEqual(a, b)

    def test_benchmarker(self):
        """ Tests the benchmarker. """
        b = myokit.Benchmarker()
        t0 = b.time()
        self.assertTrue(t0 >= 0)
        t1 = b.time()
        self.assertTrue(t1 >= t0)
        t2 = b.time()
        self.assertTrue(t2 >= t1)
        t3 = b.time()
        self.assertTrue(t3 >= t2)
        b.reset()
        t4 = b.time()
        self.assertTrue(t4 < t3)

        self.assertEqual(b.format(1), '1 second')
        self.assertEqual(b.format(61), '1 minute, 1 second')
        self.assertEqual(b.format(60), '1 minute, 0 seconds')
        self.assertEqual(b.format(180), '3 minutes, 0 seconds')
        self.assertEqual(b.format(3600), '1 hour, 0 minutes, 0 seconds')
        self.assertEqual(b.format(3661), '1 hour, 1 minute, 1 second')
        self.assertEqual(
            b.format(3600 * 24), '1 day, 0 hours, 0 minutes, 0 seconds')
        self.assertEqual(
            b.format(3600 * 24 * 7),
            '1 week, 0 days, 0 hours, 0 minutes, 0 seconds')

    def test_py_capture(self):
        """ Tests the PyCapture method. """
        # Test basic use
        with myokit.PyCapture() as c:
            print('Hello')
            self.assertEqual(c.text(), 'Hello\n')
            sys.stdout.write('Test')
        self.assertEqual(c.text(), 'Hello\nTest')

        # Test wrapping
        with myokit.PyCapture() as c:
            print('Hello')
            self.assertEqual(c.text(), 'Hello\n')
            with myokit.PyCapture() as d:
                print('Yes')
            self.assertEqual(d.text(), 'Yes\n')
            sys.stdout.write('Test')
        self.assertEqual(c.text(), 'Hello\nTest')

        # Test disabling / enabling
        with myokit.PyCapture() as c:
            print('Hello')
            self.assertEqual(c.text(), 'Hello\n')
            with myokit.PyCapture() as d:
                sys.stdout.write('Yes')
                d.disable()
                print('Hmmm')
                d.enable()
                print('No')
            self.assertEqual(d.text(), 'YesNo\n')
            sys.stdout.write('Test')
        self.assertEqual(c.text(), 'Hello\nHmmm\nTest')

    def test_examplify(self):
        """ Test examplify. """
        self.assertEqual(myokit._aux._examplify('test.txt'), 'test.txt')
        self.assertEqual(myokit._aux._examplify('example'), myokit.EXAMPLE)

    def test_format_float_dict(self):
        """ Tests myokit.format_float_dict. """
        d = {'one': 1, 'Definitely two': 2, 'Three-ish': 3.1234567}
        x = myokit.format_float_dict(d).splitlines()
        self.assertEqual(len(x), 3)
        self.assertEqual(x[0], 'Definitely two = 2')
        self.assertEqual(x[1], 'Three-ish      = 3.1234567')
        self.assertEqual(x[2], 'one            = 1')

    def test_format_path(self):
        """ Tests format_path(). """
        # Normal use
        self.assertEqual(
            myokit.format_path(os.path.join('a', 'b', 'c')), 'a/b/c')
        # No trailing slash
        self.assertEqual(
            myokit.format_path('a/'), 'a')
        self.assertEqual(
            myokit.format_path('a/b/'), 'a/b')
        # Use with custom root
        root = os.path.join(os.path.abspath('.'), 'a')
        self.assertEqual(
            myokit.format_path(os.path.join(root, 'b', 'c'), root), 'b/c')
        # Empty path
        self.assertEqual(
            myokit.format_path(''), './')
        self.assertEqual(
            myokit.format_path('.'), './')
        # Filesystem root
        self.assertEqual(
            myokit.format_path('/', root='/'), './')
        # Path outside of root
        self.assertEqual(
            myokit.format_path(
                os.path.abspath('/test'),
                os.path.abspath('/test/tost')),
            '/test')

    def test_pack_snapshot(self):
        """ Tests if the pack_snapshot method runs without exceptions. """
        with TemporaryDirectory() as d:
            # Run!
            path = d.path('pack.zip')
            new_path = myokit.pack_snapshot(path)
            self.assertTrue(os.path.isfile(new_path))
            self.assertTrue(os.path.getsize(new_path) > 500000)

            # Run with same location --> error
            self.assertRaises(
                IOError, myokit.pack_snapshot, path, overwrite=False)

            # Run with overwrite switch is ok
            myokit.pack_snapshot(path, overwrite=True)

            # Write to directory: finds own filename
            path = d.path('')
            new_path = myokit.pack_snapshot(path)
            self.assertEqual(new_path[:len(path)], path)
            self.assertTrue(len(new_path) - len(path) > 5)

            # Write to directory again without overwrite --> error
            self.assertRaises(
                IOError, myokit.pack_snapshot, path, overwrite=False)

            # Run with overwrite switch is ok
            myokit.pack_snapshot(path, overwrite=True)

    def test_levenshtein_distance(self):
        """ Tests the levenshtein distance method. """
        self.assertEqual(myokit.lvsd('kitten', 'sitting'), 3)
        self.assertEqual(myokit.lvsd('sitting', 'kitten'), 3)
        self.assertEqual(myokit.lvsd('saturday', 'sunday'), 3)
        self.assertEqual(myokit.lvsd('sunday', 'saturday'), 3)
        self.assertEqual(myokit.lvsd('michael', 'jennifer'), 7)
        self.assertEqual(myokit.lvsd('jennifer', 'michael'), 7)
        self.assertEqual(myokit.lvsd('jennifer', ''), 8)
        self.assertEqual(myokit.lvsd('', 'jennifer'), 8)

    def test_model_comparison(self):
        """ Tests the model comparison class. """

        m1 = os.path.join(DIR_DATA, 'beeler-1977-model.mmt')
        m2 = os.path.join(DIR_DATA, 'beeler-1977-model-different.mmt')
        m1 = myokit.load_model(m1)
        m2 = myokit.load_model(m2)

        with myokit.PyCapture() as capture:
            c = myokit.ModelComparison(m1, m2, live=True)
        self.assertEqual(capture.text(), """
Comparing:
  [1] beeler-1977
  [2] beeler-1977-with-differences
[x] Mismatched Meta property in model: "desc"
[x] Mismatched Meta property in model: "name"
[x] Mismatched Initial value for <ina.h>
[x] Mismatched State at position 5: [1]<isi.d> [2]<isiz.d>
[x] Mismatched State at position 6: [1]<isi.f> [2]<isiz.f>
[x] Mismatched RHS <calcium.Cai>
[x] Mismatched RHS <ina.h.alpha>
[x] Mismatched RHS <ina.j>
[2] Missing Variable <ina.j.beta>
[1] Missing Variable <ina.j.jeta>
[2] Missing Component <isi>
[x] Mismatched RHS <membrane.C>
[x] Mismatched RHS <membrane.i_ion>
[1] Missing Component <isiz>
Done
  14 differences found""".strip() + '\n')

        # Test equality method
        self.assertFalse(c.equal())
        self.assertTrue(myokit.ModelComparison(m1, m1).equal())
        self.assertTrue(myokit.ModelComparison(m2, m2).equal())

        # Test len and iterator interface
        self.assertEqual(len(c), 14)
        self.assertEqual(len([x for x in c]), 14)


if __name__ == '__main__':
    unittest.main()
