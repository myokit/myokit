#!/usr/bin/env python
#
# Tests the mmt file load/save functionality
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
import os
import unittest

import myokit

from shared import DIR_DATA, TemporaryDirectory


class LoadSaveTest(unittest.TestCase):
    """
    Tests various parts of load/save behavior for model/protocol/script.
    """
    def test_multiline_string_indent(self):
        """
        Tests what happens when you load save a string that gets auto-indented.
        """
        # Create model with multi-line meta-data property
        d1 = 'First line\n\nSecond line'
        m1 = myokit.Model()
        m1.meta['desc'] = d1
        e = m1.add_component('engine')
        v = e.add_variable('time')
        v.set_binding('time')
        v.set_rhs(0)
        # Store to disk
        with TemporaryDirectory() as d:
            opath = d.path('multiline.mmt')
            myokit.save_model(opath, m1)
            # Load and compare the meta-data string
            m2 = myokit.load_model(opath)
            d2 = m2.meta['desc']
            self.assertEqual(d1, d2)
        # Create model with indented multi-line meta-data property
        d1 = '  First line\n\n  Second line'
        dr = 'First line\n\nSecond line'
        m1 = myokit.Model()
        m1.meta['desc'] = d1
        e = m1.add_component('engine')
        v = e.add_variable('time')
        v.set_binding('time')
        v.set_rhs(0)
        # Store to disk
        with TemporaryDirectory() as d:
            opath = d.path('multiline.mmt')
            myokit.save_model(opath, m1)
            # Load and compare the meta-data string
            m2 = myokit.load_model(opath)
            d2 = m2.meta['desc']
            self.assertEqual(d2, dr)
        # Create model with strangely indented multi-line meta-data property
        d1 = '  First line\n\n   Second line'
        dr = 'First line\n\n Second line'
        m1 = myokit.Model()
        m1.meta['desc'] = d1
        e = m1.add_component('engine')
        v = e.add_variable('time')
        v.set_binding('time')
        v.set_rhs(0)
        # Store to disk
        with TemporaryDirectory() as d:
            opath = d.path('multiline.mmt')
            myokit.save_model(opath, m1)
            # Load and compare the meta-data string
            m2 = myokit.load_model(opath)
            d2 = m2.meta['desc']
            self.assertEqual(d2, dr)

    def test_save_model(self):
        """
        Tests if the correct parts are saved/loaded from disk using the
        ``save_model()`` method.
        """
        ipath = os.path.join(DIR_DATA, 'lr-1991.mmt')
        # Test example loading
        m = myokit.load_model('example')
        self.assertIsInstance(m, myokit.Model)
        # Test file loading
        m = myokit.load_model(ipath)
        self.assertIsInstance(m, myokit.Model)
        with TemporaryDirectory() as d:
            opath = d.path('loadsave.mmt')
            myokit.save_model(opath, m)
            # Test no other parts were written
            with open(opath, 'r') as f:
                text = f.read()
            self.assertTrue('[[model]]' in text)
            self.assertFalse('[[protocol]]' in text)
            self.assertFalse('[[script]]' in text)
            # Test reloading
            mm = myokit.load_model(opath)
            self.assertIsInstance(mm, myokit.Model)
            self.assertEqual(mm.code(), m.code())

    def test_save_protocol(self):
        """
        Tests if the correct parts are saved/loaded from disk using the
        ``save_protocol()`` method.
        """
        ipath = os.path.join(DIR_DATA, 'lr-1991.mmt')
        # Test example loading
        p = myokit.load_protocol('example')
        self.assertIsInstance(p, myokit.Protocol)
        # Test file loading
        p = myokit.load_protocol(ipath)
        self.assertIsInstance(p, myokit.Protocol)
        with TemporaryDirectory() as d:
            opath = d.path('test.mmt')
            myokit.save_protocol(opath, p)
            # Test no other parts were written
            with open(opath, 'r') as f:
                text = f.read()
            self.assertFalse('[[model]]' in text)
            self.assertTrue('[[protocol]]' in text)
            self.assertFalse('[[script]]' in text)
            # Test reloading
            pp = myokit.load_protocol(opath)
            self.assertIsInstance(pp, myokit.Protocol)
            self.assertEqual(pp.code(), p.code())

    def test_save_script(self):
        """
        Tests if the correct parts are saved/loaded from disk using the
        ``save_script()`` method.
        """
        ipath = os.path.join(DIR_DATA, 'lr-1991.mmt')
        # Test example loading
        x = myokit.load_script('example')
        self.assertTrue(isinstance(x, unicode) or isinstance(x, str))
        # Test file loading
        x = myokit.load_script(ipath)
        self.assertTrue(isinstance(x, unicode) or isinstance(x, str))
        with TemporaryDirectory() as d:
            opath = d.path('test.mmt')
            myokit.save_script(opath, x)
            # Test no other parts were written
            with open(opath, 'r') as f:
                text = f.read()
            self.assertFalse('[[model]]' in text)
            self.assertFalse('[[protocol]]' in text)
            self.assertTrue('[[script]]' in text)
            # Test reloading
            xx = myokit.load_script(opath)
            self.assertTrue(isinstance(xx, unicode) or isinstance(xx, str))
            self.assertEqual(x, xx)

    def test_save(self):
        """
        Tests if the correct parts are saved/loaded from disk using the
        ``save()`` method.
        """
        # Test example loading
        m, p, x = myokit.load('example')
        self.assertIsInstance(m, myokit.Model)
        self.assertIsInstance(p, myokit.Protocol)
        self.assertTrue(isinstance(x, unicode) or isinstance(x, str))

        # Save all three and reload
        with TemporaryDirectory() as d:
            opath = d.path('test.mmt')
            myokit.save(opath, m, p, x)
            mm, pp, xx = myokit.load(opath)
            self.assertEqual(m.code(), mm.code())
            self.assertEqual(p.code(), pp.code())
            self.assertEqual(x, xx)

        # Save only model
        with TemporaryDirectory() as d:
            opath = d.path('test.mmt')
            myokit.save(opath, model=m)
            with open(opath, 'r') as f:
                text = f.read()
            self.assertTrue('[[model]]' in text)
            self.assertFalse('[[protocol]]' in text)
            self.assertFalse('[[script]]' in text)
            mm, pp, xx = myokit.load(opath)
            self.assertEqual(mm.code(), m.code())
            self.assertEqual(pp, None)
            self.assertEqual(xx, None)

        # Save only protocol
        with TemporaryDirectory() as d:
            opath = d.path('test.mmt')
            myokit.save(opath, protocol=p)
            with open(opath, 'r') as f:
                text = f.read()
            self.assertFalse('[[model]]' in text)
            self.assertTrue('[[protocol]]' in text)
            self.assertFalse('[[script]]' in text)
            mm, pp, xx = myokit.load(opath)
            self.assertEqual(mm, None)
            self.assertEqual(pp.code(), p.code())
            self.assertEqual(xx, None)

        # Save only script
        with TemporaryDirectory() as d:
            opath = d.path('test.mmt')
            myokit.save(opath, script=x)
            with open(opath, 'r') as f:
                text = f.read()
            self.assertFalse('[[model]]' in text)
            self.assertFalse('[[protocol]]' in text)
            self.assertTrue('[[script]]' in text)
            mm, pp, xx = myokit.load(opath)
            self.assertEqual(mm, None)
            self.assertEqual(pp, None)
            self.assertEqual(xx, x)

        # Save all but model
        with TemporaryDirectory() as d:
            opath = d.path('test.mmt')
            myokit.save(opath, protocol=p, script=x)
            with open(opath, 'r') as f:
                text = f.read()
            self.assertFalse('[[model]]' in text)
            self.assertTrue('[[protocol]]' in text)
            self.assertTrue('[[script]]' in text)
            mm, pp, xx = myokit.load(opath)
            self.assertEqual(mm, None)
            self.assertEqual(pp.code(), p.code())
            self.assertEqual(xx, x)

        # Save all but protocol
        with TemporaryDirectory() as d:
            opath = d.path('test.mmt')
            myokit.save(opath, model=m, script=x)
            with open(opath, 'r') as f:
                text = f.read()
            self.assertTrue('[[model]]' in text)
            self.assertFalse('[[protocol]]' in text)
            self.assertTrue('[[script]]' in text)
            mm, pp, xx = myokit.load(opath)
            self.assertEqual(mm.code(), m.code())
            self.assertEqual(pp, None)
            self.assertEqual(xx, x)

        # Save all but script
        with TemporaryDirectory() as d:
            opath = d.path('test.mmt')
            myokit.save(opath, model=m, protocol=p)
            with open(opath, 'r') as f:
                text = f.read()
            self.assertTrue('[[model]]' in text)
            self.assertTrue('[[protocol]]' in text)
            self.assertFalse('[[script]]' in text)
            mm, pp, xx = myokit.load(opath)
            self.assertEqual(mm.code(), m.code())
            self.assertEqual(pp.code(), p.code())
            self.assertEqual(xx, None)


if __name__ == '__main__':
    unittest.main()
