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

from shared import DIR_DATA, WarningCollector


class AuxTest(unittest.TestCase):
    """
    Test various methods from myokit._aux.
    """

    def test_benchmarker(self):
        # Deprecated alias of myokit.tools.Benchmarker
        with WarningCollector() as c:
            b = myokit.Benchmarker()
        self.assertIn('`myokit.Benchmarker` is deprecated', c.text())
        self.assertIsInstance(b, myokit.tools.Benchmarker)

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

    def test_format_float_dict(self):
        # Test myokit.format_float_dict, which is deprecated
        d = {'one': 1, 'Definitely two': 2, 'Three-ish': 3.1234567}
        with WarningCollector() as c:
            x = myokit.format_float_dict(d).splitlines()
        self.assertIn('`myokit.format_float_dict` is deprecated', c.text())
        self.assertEqual(len(x), 3)
        self.assertEqual(x[0], 'Definitely two = 2')
        self.assertEqual(x[1], 'Three-ish      = 3.1234567')
        self.assertEqual(x[2], 'one            = 1')

    def test_format_path(self):
        # Deprecated alias of myokit.tools.format_path
        root = os.path.join(os.path.abspath('.'), 'a')
        a = os.path.join(root, 'b', 'c')
        b = os.path.join(os.path.abspath('.'), 'a')
        with WarningCollector() as c:
            x = myokit.format_path(a, b)
        self.assertIn('`myokit.format_path` is deprecated', c.text())
        self.assertEqual(x, myokit.tools.format_path(a, b))

    def test_model_comparison(self):
        # Test the model comparison class.

        m1 = os.path.join(DIR_DATA, 'beeler-1977-model.mmt')
        m2 = os.path.join(DIR_DATA, 'beeler-1977-model-different.mmt')
        m1 = myokit.load_model(m1)
        m2 = myokit.load_model(m2)

        with myokit.tools.capture() as capture:
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
        with myokit.tools.capture():
            myokit.run(m, p, x)
        with myokit.tools.capture():
            myokit.run(m, p, '[[script]]\n' + x)
        self.assertRaises(ZeroDivisionError, myokit.run, m, p, 'print(1 / 0)')

        # Test with stringio
        x = "print('Hi there')"
        s = StringIO()
        with myokit.tools.capture() as c:
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

        # Test with an initial state
        state = [-80, 1e-7, 0.1, 0.9, 0.9, 0.1, 0.9, 0.1]
        x = myokit.step(m1, initial=state).splitlines()
        y = [
            'Evaluating state vector derivatives...',
            '-' * 79,
            'Name         Initial value             Derivative at t=0       ',
            '-' * 79,
            'membrane.V   -8.00000000000000000e+01   1.41230788219242243e+00',
            'calcium.Cai   9.99999999999999955e-08   1.68235244574188927e-07',
            'ina.m         1.00000000000000006e-01  -5.12333452433218284e+00',
            'ina.h         9.00000000000000022e-01   1.30873415607557463e-02',
            'ina.j         9.00000000000000022e-01   1.43519283896554857e-03',
            'isi.d         1.00000000000000006e-01  -1.06388689494351027e-02',
            'isi.f         9.00000000000000022e-01   1.81759609957233962e-03',
            'ix1.x1        1.00000000000000006e-01  -4.72598388279933061e-03',
            '-' * 79,
        ]
        #for i, line in enumerate(y):
        #    print(line)
        #    print(x[i])
        for i, line in enumerate(y):
            self.assertEqual(line, x[i])
        self.assertEqual(len(x), len(y))

        # Test comparison against another model (with both models the same)
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

        # Test comparison against another model, with an initial state
        x = myokit.step(m1, reference=m2, initial=state).splitlines()
        y = [
            'Evaluating state vector derivatives...',
            '-' * 79,
            'Name         Initial value             Derivative at t=0       ',
            '-' * 79,
            'membrane.V   -8.00000000000000000e+01   1.41230788219242243e+00',
            '                                        1.41230788219242243e+00',
            '',
            'calcium.Cai   9.99999999999999955e-08   1.68235244574188927e-07',
            '                                        1.68235244574188927e-07',
            '',
            'ina.m         1.00000000000000006e-01  -5.12333452433218284e+00',
            '                                       -5.12333452433218284e+00',
            '',
            'ina.h         9.00000000000000022e-01   1.30873415607557463e-02',
            '                                        1.30873415607557463e-02',
            '',
            'ina.j         9.00000000000000022e-01   1.43519283896554857e-03',
            '                                        1.43519283896554857e-03',
            '',
            'isi.d         1.00000000000000006e-01  -1.06388689494351027e-02',
            '                                       -1.06388689494351027e-02',
            '',
            'isi.f         9.00000000000000022e-01   1.81759609957233962e-03',
            '                                        1.81759609957233962e-03',
            '',
            'ix1.x1        1.00000000000000006e-01  -4.72598388279933061e-03',
            '                                       -4.72598388279933061e-03',
            '',
            'Model check completed without errors.',
            '-' * 79,
        ]
        #for i, line in enumerate(y):
        #    print(line)
        #    print(x[i])
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

    def test_strfloat(self):
        # Deprecated alias of myokit.float.str
        args = ['-1.234', True, myokit.SINGLE_PRECISION]
        with WarningCollector() as c:
            x = myokit.strfloat(*args)
        self.assertIn('`myokit.strfloat` is deprecated', c.text())
        self.assertEqual(x, myokit.float.str(*args))

    def test_time(self):
        # Test time formatting method.
        import time
        for i in range(6):
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
