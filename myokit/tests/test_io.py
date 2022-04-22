#!/usr/bin/env python3
#
# Tests the loading/saveing mmt files and states.
# See also test_parsing.py
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import os
import unittest
import numpy as np

import myokit

from myokit.tests import DIR_DATA, TemporaryDirectory

# Strings in Python 2 and 3
try:
    basestring
except NameError:
    basestring = str


class LoadSaveMmtTest(unittest.TestCase):
    """Tests load/save functions for mmt files."""

    def test_examplify(self):
        # Test _examplify.
        self.assertEqual(myokit._io._examplify('test.txt'), 'test.txt')
        self.assertEqual(myokit._io._examplify('example'), myokit.EXAMPLE)

    def test_load_multiline_string_indent(self):
        # Test what happens when you load save a string that gets auto-indented

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

    def test_load_partial(self):
        # Test loading of partial files.
        mpath = os.path.join(DIR_DATA, 'beeler-1977-model.mmt')
        ppath = os.path.join(DIR_DATA, 'beeler-1977-protocol.mmt')
        spath = os.path.join(DIR_DATA, 'beeler-1977-script.mmt')

        m, p, x = myokit.load(mpath)
        self.assertIsInstance(m, myokit.Model)
        self.assertIsNone(p)
        self.assertIsNone(x)

        m, p, x = myokit.load(ppath)
        self.assertIsNone(m)
        self.assertIsInstance(p, myokit.Protocol)
        self.assertIsNone(x)

        m, p, x = myokit.load(spath)
        self.assertIsNone(m)
        self.assertIsNone(p)
        self.assertTrue(isinstance(x, basestring))

        self.assertRaises(
            myokit.SectionNotFoundError, myokit.load_model, ppath)
        self.assertRaises(
            myokit.SectionNotFoundError, myokit.load_model, spath)
        self.assertRaises(
            myokit.SectionNotFoundError, myokit.load_protocol, mpath)
        self.assertRaises(
            myokit.SectionNotFoundError, myokit.load_protocol, spath)
        self.assertRaises(
            myokit.SectionNotFoundError, myokit.load_script, mpath)
        self.assertRaises(
            myokit.SectionNotFoundError, myokit.load_script, ppath)

    def test_save(self):
        # Test if the correct parts are saved/loaded from disk using the
        # ``save()`` method.

        # Test example loading
        m, p, x = myokit.load('example')
        self.assertIsInstance(m, myokit.Model)
        self.assertIsInstance(p, myokit.Protocol)
        self.assertTrue(isinstance(x, basestring))

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

        # Save all as strings
        with TemporaryDirectory() as d:
            opath = d.path('test.mmt')
            myokit.save(opath, m, p, x)
            with open(opath, 'r') as f:
                text1 = f.read()
            myokit.save(opath, m.code(), p.code(), x)
            with open(opath, 'r') as f:
                text2 = f.read()
            self.assertEqual(text1, text2)

        # Save all as strings without [[model]] or [[protocol]] tage
        with TemporaryDirectory() as d:
            opath = d.path('test.mmt')
            myokit.save(opath, m, p, x)
            with open(opath, 'r') as f:
                text1 = f.read()
            mcode = '\n'.join(m.code().splitlines()[1:])
            pcode = '\n'.join(p.code().splitlines()[1:])
            myokit.save(opath, mcode, pcode, x)
            with open(opath, 'r') as f:
                text2 = f.read()
            self.assertEqual(text1, text2)

        # Save all, compare with string generated version
        with TemporaryDirectory() as d:
            opath = d.path('test.mmt')
            myokit.save(opath, model=m, protocol=p, script=x)
            with open(opath, 'r') as f:
                text = f.read()
            self.assertEqual(text, myokit.save(model=m, protocol=p, script=x))

    def test_save_model(self):
        # Test if the correct parts are saved/loaded from disk using the
        # ``save_model()`` method.

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
        # Test if the correct parts are saved/loaded from disk using the
        # ``save_protocol()`` method.

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
        # Test if the correct parts are saved/loaded from disk using the
        # ``save_script()`` method.

        ipath = os.path.join(DIR_DATA, 'lr-1991.mmt')
        # Test example loading
        x = myokit.load_script('example')
        self.assertTrue(isinstance(x, basestring))
        # Test file loading
        x = myokit.load_script(ipath)
        self.assertTrue(isinstance(x, basestring))
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
            self.assertTrue(isinstance(xx, basestring))
            self.assertEqual(x, xx)


class LoadSaveStateTest(unittest.TestCase):
    """Tests loading and saving states."""

    def test_load_save_state(self):
        # Test loading/saving state.
        m, p, x = myokit.load('example')
        with TemporaryDirectory() as d:
            # Test save and load without model
            f = d.path('state.txt')
            myokit.save_state(f, m.state())
            self.assertEqual(myokit.load_state(f), m.state())

            # Test save and load with model argument
            myokit.save_state(f, m.state(), m)
            self.assertEqual(myokit.load_state(f, m), m.state())

            # Save without, load with model
            myokit.save_state(f, m.state())
            self.assertEqual(myokit.load_state(f, m), m.state())

            # Save with model, load without
            # Loaded version is dict!
            myokit.save_state(f, m.state(), m)
            dct = dict(zip([v.qname() for v in m.states()], m.state()))
            self.assertEqual(myokit.load_state(f), dct)

    def test_load_save_state_bin(self):
        # Test loading/saving state in binary format.
        m, p, x = myokit.load('example')
        with TemporaryDirectory() as d:

            # Test save and load with double precision
            f = d.path('state.bin')
            myokit.save_state_bin(f, m.state())
            self.assertEqual(myokit.load_state_bin(f), m.state())

            # Test save and load with single precision
            f = d.path('state.bin')
            myokit.save_state_bin(f, m.state(), myokit.SINGLE_PRECISION)
            d = np.array(myokit.load_state_bin(f)) - np.array(m.state())
            self.assertTrue(np.all(np.abs(d) < 1e-5))   # Not very precise!


if __name__ == '__main__':
    unittest.main()
