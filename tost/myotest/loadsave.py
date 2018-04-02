#!/usr/bin/env python2
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
import myotest


def suite():
    """
    Returns a test suite with all tests in this module
    """
    suite = unittest.TestSuite()
    suite.addTest(LoadSaveTest('multiline_string_indent'))
    suite.addTest(LoadSaveTest('save_model'))
    suite.addTest(LoadSaveTest('save_protocol'))
    suite.addTest(LoadSaveTest('save_script'))
    suite.addTest(LoadSaveTest('save'))
    return suite


class LoadSaveTest(unittest.TestCase):
    """
    Tests various parts of load/save behavior for model/protocol/script.
    """
    def multiline_string_indent(self):
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
        opath = os.path.join(myotest.DIR_OUT, 'multiline.mmt')
        if os.path.exists(opath):
            os.remove(opath)
        try:
            myokit.save_model(opath, m1)
            # Load and compare the meta-data string
            m2 = myokit.load_model(opath)
            d2 = m2.meta['desc']
            self.assertEqual(d1, d2)
        finally:
            # Tidy up
            if os.path.exists(opath):
                os.remove(opath)
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
        opath = os.path.join(myotest.DIR_OUT, 'multiline.mmt')
        if os.path.exists(opath):
            os.remove(opath)
        try:
            myokit.save_model(opath, m1)
            # Load and compare the meta-data string
            m2 = myokit.load_model(opath)
            d2 = m2.meta['desc']
            self.assertEqual(d2, dr)
        finally:
            # Tidy up
            if os.path.exists(opath):
                os.remove(opath)
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
        opath = os.path.join(myotest.DIR_OUT, 'multiline.mmt')
        if os.path.exists(opath):
            os.remove(opath)
        try:
            myokit.save_model(opath, m1)
            # Load and compare the meta-data string
            m2 = myokit.load_model(opath)
            d2 = m2.meta['desc']
            self.assertEqual(d2, dr)
        finally:
            # Tidy up
            if os.path.exists(opath):
                os.remove(opath)

    def save_model(self):
        """
        Tests if the correct parts are saved/loaded from disk using the
        ``save_model()`` method.
        """
        ipath = os.path.join(myotest.DIR_DATA, 'lr-1991.mmt')
        opath = os.path.join(myotest.DIR_OUT, 'loadsavetest.mmt')
        if os.path.exists(opath):
            os.remove(opath)
        # Test example loading
        m = myokit.load_model('example')
        self.assertIsInstance(m, myokit.Model)
        # Test file loading
        m = myokit.load_model(ipath)
        self.assertIsInstance(m, myokit.Model)
        if os.path.exists(opath):
            os.remove(opath)
        try:
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
        finally:
            os.remove(opath)

    def save_protocol(self):
        """
        Tests if the correct parts are saved/loaded from disk using the
        ``save_protocol()`` method.
        """
        ipath = os.path.join(myotest.DIR_DATA, 'lr-1991.mmt')
        opath = os.path.join(myotest.DIR_OUT, 'loadsavetest.mmt')
        if os.path.exists(opath):
            os.remove(opath)
        # Test example loading
        p = myokit.load_protocol('example')
        self.assertIsInstance(p, myokit.Protocol)
        # Test file loading
        p = myokit.load_protocol(ipath)
        self.assertIsInstance(p, myokit.Protocol)
        if os.path.exists(opath):
            os.remove(opath)
        try:
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
        finally:
            os.remove(opath)

    def save_script(self):
        """
        Tests if the correct parts are saved/loaded from disk using the
        ``save_script()`` method.
        """
        ipath = os.path.join(myotest.DIR_DATA, 'lr-1991.mmt')
        opath = os.path.join(myotest.DIR_OUT, 'loadsavetest.mmt')
        if os.path.exists(opath):
            os.remove(opath)
        # Test example loading
        x = myokit.load_script('example')
        self.assertIsInstance(x, str)
        # Test file loading
        x = myokit.load_script(ipath)
        self.assertIsInstance(x, str)
        if os.path.exists(opath):
            os.remove(opath)
        try:
            myokit.save_script(opath, x)
            # Test no other parts were written
            with open(opath, 'r') as f:
                text = f.read()
            self.assertFalse('[[model]]' in text)
            self.assertFalse('[[protocol]]' in text)
            self.assertTrue('[[script]]' in text)
            # Test reloading
            xx = myokit.load_script(opath)
            self.assertIsInstance(xx, str)
            self.assertEqual(x, xx)
        finally:
            os.remove(opath)

    def save(self):
        """
        Tests if the correct parts are saved/loaded from disk using the
        ``save()`` method.
        """
        opath = os.path.join(myotest.DIR_OUT, 'loadsavetest.mmt')
        if os.path.exists(opath):
            os.remove(opath)
        # Test example loading
        m, p, x = myokit.load('example')
        self.assertIsInstance(m, myokit.Model)
        self.assertIsInstance(p, myokit.Protocol)
        self.assertIsInstance(x, str)
        # Save all three and reload
        try:
            myokit.save(opath, m, p, x)
            mm, pp, xx = myokit.load(opath)
            self.assertEqual(m.code(), mm.code())
            self.assertEqual(p.code(), pp.code())
            self.assertEqual(x, xx)
        finally:
            if os.path.exists(opath):
                os.remove(opath)
        # Save only model
        try:
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
        finally:
            if os.path.exists(opath):
                os.remove(opath)
        # Save only protocol
        try:
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
        finally:
            if os.path.exists(opath):
                os.remove(opath)
        # Save only script
        try:
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
        finally:
            if os.path.exists(opath):
                os.remove(opath)
        # Save all but model
        try:
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
        finally:
            if os.path.exists(opath):
                os.remove(opath)
        # Save all but protocol
        try:
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
        finally:
            if os.path.exists(opath):
                os.remove(opath)
        # Save all but script
        try:
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
        finally:
            if os.path.exists(opath):
                os.remove(opath)
