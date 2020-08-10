#!/usr/bin/env python3
#
# Tests the myokit._aux module.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import os
import sys
import unittest

# StringIO in Python 2 and 3
try:
    from cStringIO import StringIO
except ImportError:  # pragma: no python 2 cover
    from io import StringIO

# Strings in Python2 and Python3
try:
    basestring
except NameError:   # pragma: no cover
    basestring = str

import myokit

from shared import DIR_DATA, TemporaryDirectory


class AuxTest(unittest.TestCase):
    """
    Test various methods from myokit._aux.
    """

    def test_benchmarker(self):
        # Test the benchmarker.

        b = myokit.Benchmarker()
        x = [0] * 1000
        t0 = b.time()
        self.assertTrue(t0 >= 0)
        x = [0] * 1000
        t1 = b.time()
        self.assertTrue(t1 >= t0)
        x = [0] * 1000
        t2 = b.time()
        self.assertTrue(t2 >= t1)
        for i in range(1000):
            x = [0] * 1000
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

    def test_date(self):
        # Test date formatting method.

        import time
        for i in range(3):
            a = time.strftime(myokit.DATE_FORMAT)
            b = myokit.date()
            if a == b:
                break
        self.assertEqual(a, b)

    def test_default_protocol(self):
        # Test default_protocol()

        # Test default version
        protocol = myokit.default_protocol()
        self.assertTrue(isinstance(protocol, myokit.Protocol))
        self.assertEqual(protocol.head().period(), 1000)

        # Test adapting the time unit
        model = myokit.Model()
        t = model.add_component('c').add_variable('t')
        t.set_rhs(0)
        protocol = myokit.default_protocol(model)
        self.assertTrue(isinstance(protocol, myokit.Protocol))
        self.assertEqual(protocol.head().period(), 1000)

        t.set_binding('time')
        protocol = myokit.default_protocol(model)
        self.assertTrue(isinstance(protocol, myokit.Protocol))
        self.assertEqual(protocol.head().period(), 1000)

        t.set_unit('s')
        protocol = myokit.default_protocol(model)
        self.assertTrue(isinstance(protocol, myokit.Protocol))
        self.assertEqual(protocol.head().period(), 1)

        t.set_unit('ms')
        protocol = myokit.default_protocol(model)
        self.assertTrue(isinstance(protocol, myokit.Protocol))
        self.assertEqual(protocol.head().period(), 1000)

    def test_default_script(self):
        # Test default script

        # Test without a model
        script = myokit.default_script()
        self.assertTrue(isinstance(script, basestring))
        self.assertIn('run(1000)', script)

        # Test adapting the time unit
        model = myokit.Model()
        t = model.add_component('c').add_variable('t')
        t.set_rhs(0)
        script = myokit.default_script(model)
        self.assertTrue(isinstance(script, basestring))
        self.assertIn('run(1000)', script)

        t.set_binding('time')
        script = myokit.default_script(model)
        self.assertTrue(isinstance(script, basestring))
        self.assertIn('run(1000)', script)

        t.set_unit('s')
        script = myokit.default_script(model)
        self.assertTrue(isinstance(script, basestring))
        self.assertIn('run(1.0)', script)

        t.set_unit('ms')
        script = myokit.default_script(model)
        self.assertTrue(isinstance(script, basestring))
        self.assertIn('run(1000)', script)

        # Test plotting membrane potential
        v = model.get('c').add_variable('v')
        v.set_label('membrane_potential')
        script = myokit.default_script(model)
        self.assertTrue(isinstance(script, basestring))
        self.assertIn("var = 'c.v'", script)

        # TODO: Run with tiny model?

    def test_examplify(self):
        # Test examplify.

        self.assertEqual(myokit._aux._examplify('test.txt'), 'test.txt')
        self.assertEqual(myokit._aux._examplify('example'), myokit.EXAMPLE)

    def test_float_functions(self):
        # Test the floating point comparison methods

        # Test that test is going to work
        x = 49
        y = 1 / (1 / x)
        self.assertNotEqual(x, y)

        # Test if feq allows 1 floating point error
        # Test if
        self.assertTrue(myokit._feq(x, y))
        self.assertTrue(myokit._fgeq(x, y))
        self.assertTrue(myokit._fgeq(y, x))
        x += x * sys.float_info.epsilon
        self.assertTrue(myokit._feq(x, y))
        self.assertTrue(myokit._fgeq(x, y))
        self.assertTrue(myokit._fgeq(y, x))
        x += x * sys.float_info.epsilon
        self.assertFalse(myokit._feq(x, y))
        self.assertTrue(myokit._fgeq(x, y))
        self.assertFalse(myokit._fgeq(y, x))

        # Test rounding
        self.assertNotEqual(49, y)
        self.assertEqual(49, myokit._fround(y))
        self.assertNotEqual(49, myokit._fround(x))
        self.assertEqual(0.5, myokit._fround(0.5))
        self.assertIsInstance(myokit._fround(y), int)

        # Try with negative numbers
        self.assertNotEqual(-49, -y)
        self.assertEqual(-49, myokit._fround(-y))
        self.assertNotEqual(-49, myokit._fround(-x))
        self.assertEqual(-0.5, myokit._fround(-0.5))

        # Test that _close allows bigger errors
        x = 49
        y = x * (1 + 1e-11)
        self.assertNotEqual(x, y)
        self.assertFalse(myokit._feq(x, y))
        self.assertTrue(myokit._close(x, y))

        # And that close thinks everything small is equal
        x = 1e-16
        y = 1e-12
        self.assertNotEqual(x, y)
        self.assertFalse(myokit._feq(x, y))
        self.assertTrue(myokit._close(x, y))

        # Test rounding based on closeness
        x = 49
        y = x * (1 + 1e-11)
        self.assertNotEqual(x, y)
        self.assertEqual(x, myokit._cround(y))
        self.assertIsInstance(myokit._cround(y), int)
        self.assertNotEqual(x, myokit._cround(49.001))

    def test_format_float_dict(self):
        # Test myokit.format_float_dict.

        d = {'one': 1, 'Definitely two': 2, 'Three-ish': 3.1234567}
        x = myokit.format_float_dict(d).splitlines()
        self.assertEqual(len(x), 3)
        self.assertEqual(x[0], 'Definitely two = 2')
        self.assertEqual(x[1], 'Three-ish      = 3.1234567')
        self.assertEqual(x[2], 'one            = 1')

    def test_format_path(self):
        # Test format_path().

        # Normal use
        self.assertEqual(
            myokit.format_path(os.path.join('a', 'b', 'c')),
            os.path.join('a', 'b', 'c'))

        # No trailing slash
        self.assertEqual(
            myokit.format_path('a'), 'a')
        self.assertEqual(
            myokit.format_path('a/b/'), os.path.join('a', 'b'))

        # Use with custom root
        root = os.path.join(os.path.abspath('.'), 'a')
        self.assertEqual(
            myokit.format_path(os.path.join(root, 'b', 'c'), root),
            os.path.join('b', 'c'))

        # Empty path
        self.assertEqual(
            myokit.format_path(''), '.')
        self.assertEqual(
            myokit.format_path('.'), '.')

        # Filesystem root
        self.assertEqual(
            myokit.format_path('/'), os.path.abspath('/'))
        self.assertEqual(
            myokit.format_path('/', root='/'), '.')

        # Path outside of root
        self.assertEqual(
            myokit.format_path(
                os.path.abspath('test'),
                os.path.abspath('test/tost')),
            os.path.abspath('test'))

    def test_levenshtein_distance(self):
        # Test the levenshtein distance method.

        self.assertEqual(myokit._lvsd('kitten', 'sitting'), 3)
        self.assertEqual(myokit._lvsd('sitting', 'kitten'), 3)
        self.assertEqual(myokit._lvsd('saturday', 'sunday'), 3)
        self.assertEqual(myokit._lvsd('sunday', 'saturday'), 3)
        self.assertEqual(myokit._lvsd('michael', 'jennifer'), 7)
        self.assertEqual(myokit._lvsd('jennifer', 'michael'), 7)
        self.assertEqual(myokit._lvsd('jennifer', ''), 8)
        self.assertEqual(myokit._lvsd('', 'jennifer'), 8)
        self.assertEqual(myokit._lvsd('', ''), 0)

    def test_model_comparison(self):
        # Test the model comparison class.

        m1 = os.path.join(DIR_DATA, 'beeler-1977-model.mmt')
        m2 = os.path.join(DIR_DATA, 'beeler-1977-model-different.mmt')
        m1 = myokit.load_model(m1)
        m2 = myokit.load_model(m2)

        with myokit.PyCapture() as capture:
            c = myokit.ModelComparison(m1, m2, live=True)

        differences = [
            '[x] Mismatched Meta property in model: "desc"',
            '[x] Mismatched Meta property in model: "name"',
            '[2] Missing Meta property in model: "author"',
            '[1] Missing Meta property in model: "extra"',
            '[x] Mismatched User function <f(1)>',
            '[1] Missing User function <g(1)>.',
            '[x] Mismatched Time variable: [1]<engine.time> [2]<engine.toim>',
            '[x] Mismatched Initial value for <ina.h>',
            '[x] Mismatched State at position 5: [1]<isi.d> [2]<isiz.d>',
            '[x] Mismatched State at position 6: [1]<isi.f> [2]<isiz.f>',
            '[2] Missing state at position 7',
            '[x] Mismatched RHS <calcium.Cai>',
            '[2] Missing Variable <engine.time>',
            '[1] Missing Variable <engine.toim>',
            '[x] Mismatched RHS <ina.h.alpha>',
            '[x] Mismatched RHS <ina.j>',
            '[2] Missing Variable <ina.j.beta>',
            '[1] Missing Variable <ina.j.jeta>',
            '[2] Missing Component <isi>',
            '[x] Mismatched LHS <ix1.x1>',
            '[x] Mismatched RHS <ix1.x1>',
            '[2] Missing Variable <ix1.x1.alpha>',
            '[2] Missing Variable <ix1.x1.beta>',
            '[x] Mismatched RHS <membrane.C>',
            '[x] Mismatched RHS <membrane.i_ion>',
            '[x] Mismatched unit <membrane.V>',
            '[1] Missing Component <isiz>',
        ]

        live = [
            'Comparing:',
            '  [1] beeler-1977',
            '  [2] beeler-1977-with-differences',
        ] + differences + [
            'Done',
            '  ' + str(len(differences)) + ' differences found',
        ]

        # Show massive diff messages
        self.maxDiff = None

        caught_differences = set(capture.text().splitlines())
        live = set(live)
        self.assertEqual(live, caught_differences)
        differences = set(differences)
        caught_differences = set(c.text().splitlines())
        self.assertEqual(differences, caught_differences)

        # Test equality method
        self.assertFalse(c.equal())
        self.assertTrue(myokit.ModelComparison(m1, m1).equal())
        self.assertTrue(myokit.ModelComparison(m2, m2).equal())

        # Test len and iterator interface
        self.assertEqual(len(c), len(differences))
        self.assertEqual(len([x for x in c]), len(differences))

        # Test reverse is similar
        d = myokit.ModelComparison(m2, m1)
        self.assertEqual(len(c), len(d))

        # Test detection of missing time variable
        # Note: user function disappears when cloning
        m3 = m1.clone()
        m3.binding('time').set_binding(None)
        c = myokit.ModelComparison(m1, m3)
        self.assertEqual(
            c.text(),
            '[2] Missing User function <f(1)>\n'
            '[2] Missing Time variable <engine.time>')
        self.assertEqual(len(c), 2)
        self.assertEqual(len(c), len(myokit.ModelComparison(m3, m1)))

    def test_natural_sort_key(self):
        # Test natural sort key method.

        a = ['a12', 'a3', 'a11', 'a2', 'a10', 'a1']
        b = ['a1', 'a2', 'a3', 'a10', 'a11', 'a12']
        self.assertNotEqual(a, b)
        a.sort()
        self.assertNotEqual(a, b)
        a.sort(key=lambda x: myokit._natural_sort_key(x))
        self.assertEqual(a, b)

    def test_numpy_writer(self):
        # Test NumPy expression writer obtaining method.

        import myokit
        w = myokit.numpy_writer()
        import myokit.formats
        import myokit.formats.python
        self.assertIsInstance(w, myokit.formats.python.NumPyExpressionWriter)

        # Test custom name method for this writer
        e = myokit.parse_expression('5 + 3 * x')
        self.assertEqual(w.ex(e), '5.0 + 3.0 * x')

        # Test with unvalidated model (no unames set)
        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        x.set_rhs('5 + x')
        self.assertEqual(w.ex(x.rhs()), '5.0 + c_x')

    def test_pack_snapshot(self):
        # Test if the pack_snapshot method runs without exceptions.

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

    def test_python_writer(self):
        # Test Python expression writer obtaining method.

        import myokit
        w = myokit.python_writer()
        import myokit.formats
        import myokit.formats.python
        self.assertIsInstance(w, myokit.formats.python.PythonExpressionWriter)

        # Test custom name method for this writer
        e = myokit.parse_expression('5 + 3 * x')
        self.assertEqual(w.ex(e), '5.0 + 3.0 * x')

        # Test with unvalidated model (no unames set)
        m = myokit.Model()
        c = m.add_component('c')
        x = c.add_variable('x')
        x.set_rhs('5 + x')
        self.assertEqual(w.ex(x.rhs()), '5.0 + c_x')

    def test_py_capture(self):
        # Test the PyCapture method.

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

        # Test clear() method
        with myokit.PyCapture() as c:
            print('Hi')
            self.assertEqual(c.text(), 'Hi\n')
            print('Ho')
            self.assertEqual(c.text(), 'Hi\nHo\n')
            c.clear()
            print('Ha')
            self.assertEqual(c.text(), 'Ha\n')

        # Bug: Test clear method _without_ calling text() before clear()
        with myokit.PyCapture() as c:
            print('Hi')
            print('Ho')
            c.clear()
            print('Ha')
            self.assertEqual(c.text(), 'Ha\n')

    def test_run(self):
        # Test run() method.

        m, p, _ = myokit.load('example')
        x = '\n'.join([
            'import myokit',
            'm = get_model()',  # Test magic methods
            'p = get_protocol()',
            's = myokit.Simulation(m, p)',
            's.run(200)',
        ])
        with myokit.PyCapture():
            myokit.run(m, p, x)
        with myokit.PyCapture():
            myokit.run(m, p, '[[script]]\n' + x)
        self.assertRaises(ZeroDivisionError, myokit.run, m, p, 'print(1 / 0)')

        # Test with stringio
        x = "print('Hi there')"
        s = StringIO()
        with myokit.PyCapture() as c:
            myokit.run(m, p, x, stderr=s, stdout=s)
        self.assertEqual(c.text(), '')
        self.assertEqual(s.getvalue(), 'Hi there\n')

    def test_step(self):
        # Test the step() method.
        m1 = myokit.load_model(os.path.join(DIR_DATA, 'beeler-1977-model.mmt'))

        # Test simple output
        x = myokit.step(m1).splitlines()
        y = [
            'Evaluating state vector derivatives...',
            '-' * 79,
            'Name         Initial value             Derivative at t=0       ',
            '-' * 79,
            'membrane.V   -8.46219999999999999e+01  -3.97224086575331814e-04',
            'calcium.Cai   1.99999999999999991e-07  -1.56608433137725457e-09',
            'ina.m         1.00000000000000002e-02   7.48738392280519083e-02',
            'ina.h         9.89999999999999991e-01  -1.78891889478854579e-03',
            'ina.j         9.79999999999999982e-01  -3.06255006833574140e-04',
            'isi.d         3.00000000000000006e-03  -5.11993904291850035e-06',
            'isi.f         9.89999999999999991e-01   1.88374114688215870e-04',
            'ix1.x1        4.00000000000000019e-04  -3.21682814207918156e-07',
            '-' * 79,
        ]
        #for i, line in enumerate(y):
        #    print(line)
        #    print(x[i])
        for i, line in enumerate(y):
            self.assertEqual(line, x[i])
        self.assertEqual(len(x), len(y))

        # Test comparison against another model
        m2 = m1.clone()
        x = myokit.step(m1, reference=m2).splitlines()
        y = [
            'Evaluating state vector derivatives...',
            '-' * 79,
            'Name         Initial value             Derivative at t=0       ',
            '-' * 79,
            'membrane.V   -8.46219999999999999e+01  -3.97224086575331814e-04',
            '                                       -3.97224086575331814e-04',
            '',
            'calcium.Cai   1.99999999999999991e-07  -1.56608433137725457e-09',
            '                                       -1.56608433137725457e-09',
            '',
            'ina.m         1.00000000000000002e-02   7.48738392280519083e-02',
            '                                        7.48738392280519083e-02',
            '',
            'ina.h         9.89999999999999991e-01  -1.78891889478854579e-03',
            '                                       -1.78891889478854579e-03',
            '',
            'ina.j         9.79999999999999982e-01  -3.06255006833574140e-04',
            '                                       -3.06255006833574140e-04',
            '',
            'isi.d         3.00000000000000006e-03  -5.11993904291850035e-06',
            '                                       -5.11993904291850035e-06',
            '',
            'isi.f         9.89999999999999991e-01   1.88374114688215870e-04',
            '                                        1.88374114688215870e-04',
            '',
            'ix1.x1        4.00000000000000019e-04  -3.21682814207918156e-07',
            '                                       -3.21682814207918156e-07',
            '',
            'Model check completed without errors.',
            '-' * 79,
        ]

        for i, line in enumerate(y):
            self.assertEqual(line, x[i])
        self.assertEqual(len(x), len(y))

        # Test comparison against stored data
        ref = [
            -3.97224086575331868e-04,       # Numerically indistinguishable
            -1.56608433137725457e-09,
            7.48738392280519777e-02,        # Tiny error
            -1.78891889478854579e-03,
            3.06255006833574140e-04,        # Sign error
            -5.11993904291850035e-06,
            3.76748229376431740e-04,        # Large error
            -3.21682814207918156e-05,       # Exponent
        ]
        x = myokit.step(m1, reference=ref).splitlines()
        y = [
            'Evaluating state vector derivatives...',
            '-' * 79,
            'Name         Initial value             Derivative at t=0       ',
            '-' * 79,
            'membrane.V   -8.46219999999999999e+01  -3.97224086575331814e-04',
            '                                       -3.97224086575331868e-04'
            ' <= 1 eps',
            '',
            'calcium.Cai   1.99999999999999991e-07  -1.56608433137725457e-09',
            '                                       -1.56608433137725457e-09',
            '',
            'ina.m         1.00000000000000002e-02   7.48738392280519083e-02',
            '                                        7.48738392280519777e-02'
            ' ~ 4.2 eps',
            '                                                        ^^^^^^^',
            'ina.h         9.89999999999999991e-01  -1.78891889478854579e-03',
            '                                       -1.78891889478854579e-03',
            '',
            'ina.j         9.79999999999999982e-01  -3.06255006833574140e-04',
            '                                        3.06255006833574140e-04'
            ' sign',
            '                                       ^^^^^^^^^^^^^^^^^^^^^^^^',
            'isi.d         3.00000000000000006e-03  -5.11993904291850035e-06',
            '                                       -5.11993904291850035e-06',
            '',
            'isi.f         9.89999999999999991e-01   1.88374114688215870e-04',
            '                                        3.76748229376431740e-04'
            ' X',
            '                                        ^^^^^^^^^^^^^^^^^^^^^^^',
            'ix1.x1        4.00000000000000019e-04  -3.21682814207918156e-07',
            '                                       -3.21682814207918156e-05'
            ' exponent',
            '                                                           ^^^^',
            'Found (3) large mismatches between output and reference values.',
            'Found (1) small mismatches.',
            '-' * 79,
        ]

        for i, line in enumerate(y):
            self.assertEqual(line, x[i])
        self.assertEqual(len(x), len(y))

        # Test positive/negative zero comparison
        m1 = myokit.Model()
        c = m1.add_component('c')
        x = c.add_variable('x')
        x.promote(1)
        x.set_rhs('-0.0')
        y = c.add_variable('y')
        y.promote(1)
        y.set_rhs('0.0')
        m2 = m1.clone()
        m2.get('c.x').set_rhs(0.0)

        x = myokit.step(m1, reference=m2).splitlines()
        y = [
            'Evaluating state vector derivatives...',
            '-' * 79,
            'Name  Initial value             Derivative at t=0       ',
            '-' * 79,
            'c.x    1.00000000000000000e+00  -0.00000000000000000e+00',
            '                                 0.00000000000000000e+00',
            '',
            'c.y    1.00000000000000000e+00   0.00000000000000000e+00',
            '                                 0.00000000000000000e+00',
            '',
            'Model check completed without errors.',
            '-' * 79,
        ]

        #for i, line in enumerate(y):
        #    print(line + '<')
        #    print(x[i] + '<')
        for i, line in enumerate(y):
            self.assertEqual(line, x[i])
        self.assertEqual(len(x), len(y))

    def test_myokit_strfloat(self):
        # Test float to string conversion.

        # String should be passed through
        # Note: convert to str() to test in python 2 and 3.
        self.assertEqual(myokit.strfloat(str('123')), '123')

        # Simple numbers
        self.assertEqual(myokit.strfloat(0), '0')
        self.assertEqual(myokit.strfloat(0.0000), '0.0')
        self.assertEqual(myokit.strfloat(1.234), '1.234')
        self.assertEqual(
            myokit.strfloat(0.12432656245e12), ' 1.24326562450000000e+11')
        self.assertEqual(myokit.strfloat(-0), '0')
        self.assertEqual(myokit.strfloat(-0.0000), '-0.0')
        self.assertEqual(myokit.strfloat(-1.234), '-1.234')
        self.assertEqual(
            myokit.strfloat(-0.12432656245e12), '-1.24326562450000000e+11')

        # Strings are not converted
        x = '1.234'
        self.assertEqual(x, myokit.strfloat(x))

        # Myokit Numbers are converted
        x = myokit.Number(1.23)
        self.assertEqual(myokit.strfloat(x), '1.23')

        # Full precision override
        self.assertEqual(
            myokit.strfloat(1.23, True), ' 1.22999999999999998e+00')

    def test_time(self):
        # Test time formatting method.

        import time
        for i in range(3):
            a = time.strftime(myokit.TIME_FORMAT)
            b = myokit.time()
            if a == b:
                break
        self.assertEqual(a, b)

    def test_version(self):
        # Test the version() method.

        # Raw version
        raw = myokit.version(raw=True)
        self.assertIsInstance(raw, basestring)
        parts = raw.split('.')
        self.assertTrue(len(parts) in [3, 4])

        # Formatted version
        v = myokit.version()
        v = v.splitlines()
        self.assertEqual(len(v), 3)


if __name__ == '__main__':
    unittest.main()
