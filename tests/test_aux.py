#!/usr/bin/env python3
#
# Tests the myokit._aux module.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import io
import re
import unittest

from shared import DIR_DATA, WarningCollector

import myokit


class AuxTest(unittest.TestCase):
    """
    Test various methods from myokit._aux.
    """

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
        self.assertTrue(isinstance(script, str))
        self.assertIn('run(1000)', script)

        # Test adapting the time unit
        model = myokit.Model()
        t = model.add_component('c').add_variable('t')
        t.set_rhs(0)
        script = myokit.default_script(model)
        self.assertTrue(isinstance(script, str))
        self.assertIn('run(1000)', script)

        t.set_binding('time')
        script = myokit.default_script(model)
        self.assertTrue(isinstance(script, str))
        self.assertIn('run(1000)', script)

        t.set_unit('s')
        script = myokit.default_script(model)
        self.assertTrue(isinstance(script, str))
        self.assertIn('run(1.0)', script)

        t.set_unit('ms')
        script = myokit.default_script(model)
        self.assertTrue(isinstance(script, str))
        self.assertIn('run(1000)', script)

        # Test plotting membrane potential
        v = model.get('c').add_variable('v')
        v.set_label('membrane_potential')
        script = myokit.default_script(model)
        self.assertTrue(isinstance(script, str))
        self.assertIn("var = 'c.v'", script)

        # TODO: Run with tiny model?

    def test_model_comparison(self):
        # Test the model comparison class.

        m1 = myokit.load_model(DIR_DATA / 'beeler-1977.mmt')
        m2 = m1.clone()
        m2.set_name('beeler-1977-with-differences')
        m2.meta['desc'] = 'Hello'
        m2.meta['extra'] = 'This is so extra'
        del(m2.meta['mmt_authors'])
        with WarningCollector():
            m1.add_function('f', ('a'), '2 * a')
            m2.add_function('f', ('a'), '2 * a + 1')
            m2.add_function('g', ('a'), '2 * a')
        m2.get('engine.time').rename('toim')
        m2.get('ina.h').set_initial_value(myokit.Number(0))
        m1.get('ina.j').set_initial_value(myokit.Number(0))
        m2.get('ix1.x1').set_rhs(3)
        m2.get('ix1.x1').remove_variable(m2.get('ix1.x1.alpha'))
        m2.get('ix1.x1').remove_variable(m2.get('ix1.x1.beta'))
        m2.get('calcium.Cai').set_rhs(0)
        m2.get('calcium.Cai').demote()
        m2.get('membrane.V').set_unit('kV')
        c1 = m2.get('is')
        c2 = m2.add_component('ois')
        for var in list(c1):
            c1.move_variable(var, c2)
        m2.remove_component(c1)
        m2.get('ois').add_variable('X', rhs=1, initial_value=0)
        m2.get('ois').add_variable('Y', rhs=2, initial_value=0)

        with myokit.tools.capture() as capture:
            c = myokit.ModelComparison(m1, m2, live=True)
        differences = [
            '[x] Mismatched Meta property in model: "name"',
            '[x] Mismatched Meta property in model: "desc"',
            '[1] Missing Meta property in model: "extra"',
            '[2] Missing Meta property in model: "mmt_authors"',
            '[x] Mismatched User function "f(1)"',
            '[1] Missing User function "g(1)".',
            '[x] Mismatched Time variable: [1]"engine.time" [2]"engine.toim"',
            '[x] Mismatched Initial value for "ina.h"',
            '[x] Mismatched Initial value for "ina.j"',
            '[2] Missing Variable "engine.time"',
            '[1] Missing Variable "engine.toim"',
            '[x] Mismatched LHS "calcium.Cai"',
            '[x] Mismatched RHS "calcium.Cai"',
            '[x] Mismatched RHS "ix1.x1"',
            '[2] Missing Variable "ix1.x1.alpha"',
            '[2] Missing Variable "ix1.x1.beta"',
            '[x] Mismatched RHS "membrane.i_ion"',
            '[x] Mismatched unit "membrane.V"',
            '[x] Mismatched State at position 4: [1]"is.d" [2]"ois.d"',
            '[x] Mismatched State at position 5: [1]"is.f" [2]"ois.f"',
            '[1] Missing Component "ois"',
            '[2] Missing Component "is"',
            '[1] Missing state at position 9',
            '[x] Mismatched State at position 7: [1]"calcium.Cai" [2]"ois.X"'
        ]

        live = [
            'Comparing:',
            '  [1] beeler-1977',
            '  [2] beeler-1977-with-differences',
        ] + differences + [
            'Done',
            f'  {len(differences)} differences found',
        ]

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
            '[2] Missing User function "f(1)"\n'
            '[2] Missing Time variable "engine.time"')
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

        m, p, _ = myokit.load(DIR_DATA / 'beeler-1977.mmt')
        x = '\n'.join([
            'import myokit',
            'm = get_model()',  # Test magic methods
            'p = get_protocol()',
        ])
        with myokit.tools.capture():
            myokit.run(m, p, x)
        with myokit.tools.capture():
            myokit.run(m, p, f'[[script]]\n{x}')
        self.assertRaises(ZeroDivisionError, myokit.run, m, p, 'print(1 / 0)')

        # Test with stringio
        x = "print('Hi there')"
        s = io.StringIO()
        with myokit.tools.capture() as c:
            myokit.run(m, p, x, stderr=s, stdout=s)
        self.assertEqual(c.text(), '')
        self.assertEqual(s.getvalue(), 'Hi there\n')

        # Model expected but not provided
        x = '\n'.join([
            'import myokit',
            'm = get_model()',
            'p = get_protocol()',
        ])
        self.assertRaisesRegex(
            RuntimeError, 'Model not available', myokit.run, None, p, x)
        self.assertRaisesRegex(
            RuntimeError, 'Protocol not available', myokit.run, m, None, x)
        x = '\n'.join(['import myokit', 'p = get_model()'])
        self.assertRaisesRegex(
            RuntimeError, 'Model not available', myokit.run, None, None, x)
        x = '\n'.join(['import myokit', 'p = get_protocol()'])
        self.assertRaisesRegex(
            RuntimeError, 'Protocol not available', myokit.run, None, None, x)
        x = '\n'.join(['import myokit'])
        myokit.run(None, None, x)

    def test_step(self):
        # Test the step() method.
        m1 = myokit.load_model(DIR_DATA / 'beeler-1977.mmt')

        # For whatever reason, CI gives slightly different final digits some
        # times.
        r1 = re.compile(r'[a-zA-Z]\w*\.[a-zA-Z]\w*\s+([^\s]+)\s+([^\s]+)')
        r2 = re.compile(r'\s+([0-9e.+-]+)')
        r3 = re.compile(r'^[ ^]*$')
        r4 = re.compile(r'^Found \([0-9]+\) small mismatches.$')

        def almost_equal(x, y):
            # Easy checks
            if x == y:
                return True

            # Get numbers with regex and compare
            # First case: assume two numbers on each line. 2nd is tested
            g1, g2 = r1.match(x), r1.match(y)
            if g1 is not None and g2 is not None:
                x, y = float(g1.group(2)), float(g2.group(2))
                return myokit.float.close(x, y)

            # Second case: one number per line.
            g1, g2 = r2.match(x), r2.match(y)
            if g1 is not None and g2 is not None:
                x, y = float(g1.group(1)), float(g2.group(1))
                return myokit.float.close(x, y)

            # Third case: "   ^^^ "
            # These don't matter: we've already seen that the floats are close
            g1, g2 = r3.match(x), r3.match(y)
            if g1 is not None and g2 is not None:
                return True

            # Fourth case: Found (x) small differences
            # These don't matter: we've already seen that the floats are close
            g1, g2 = r4.match(x), r4.match(y)
            if g1 is not None and g2 is not None:
                return True

            return x == y

        # Test simple output
        x = myokit.step(m1).splitlines()
        y = [
            'Evaluating state vector derivatives...',
            '-' * 79,
            'Name         Initial value             Derivative at t=0       ',
            '-' * 79,
            'membrane.V   -8.43499999999999943e+01  -1.59225544529053437e-03',
            'ina.m         1.00000000000000002e-02   1.05572457615837556e-01',
            'ina.h         9.89999999999999991e-01  -2.57573692422314801e-03',
            'ina.j         9.69999999999999973e-01   2.27729027201508923e-04',
            'is.d          3.00000000000000006e-03   3.37267935768704313e-06',
            'is.f          1.00000000000000000e+00  -3.66608204332271936e-07',
            'ix1.x1        2.99999999999999989e-02  -1.06690490942922786e-04',
            'calcium.Cai   1.80000000000000011e-04  -8.14771094609788952e-08',
            '-' * 79,
        ]
        for a, b in zip(x, y):
            self.assertTrue(almost_equal(a, b))
        self.assertEqual(len(x), len(y))

        # Test with an initial state
        # For whatever reason, CI gives slightly different final 3 digits some
        # times.
        state = [-80, 1e-7, 0.1, 0.9, 0.9, 0.1, 0.9, 0.1]
        x = myokit.step(m1, state=state).splitlines()
        y = [
            'Evaluating state vector derivatives...',
            '-' * 79,
            'Name         Initial value             Derivative at t=0       ',
            '-' * 79,
            'membrane.V   -8.00000000000000000e+01   6.99933961152120032e-01',
            'ina.m         9.99999999999999955e-08   1.26374945544508321e+00',
            'ina.h         1.00000000000000006e-01   2.38558150922925788e-01',
            'ina.j         9.00000000000000022e-01   1.43519283896554857e-03',
            'is.d          9.00000000000000022e-01  -9.96503893516665490e-02',
            'is.f          1.00000000000000006e-01   1.63647819146313829e-02',
            'ix1.x1        9.00000000000000022e-01  -3.55793884094798146e-03',
            'calcium.Cai   1.00000000000000006e-01  -6.89766400310046473e-03',
            '-' * 79,
        ]
        for a, b in zip(x, y):
            self.assertTrue(almost_equal(a, b))
        self.assertEqual(len(x), len(y))

        # Test comparison against another model (with both models the same)
        m2 = m1.clone()
        x = myokit.step(m1, reference=m2).splitlines()
        y = [
            'Evaluating state vector derivatives...',
            '-' * 79,
            'Name         Initial value             Derivative at t=0       ',
            '-' * 79,
            'membrane.V   -8.43499999999999943e+01  -1.59225544529053437e-03',
            '                                       -1.59225544529053437e-03',
            '',
            'ina.m         1.00000000000000002e-02   1.05572457615837556e-01',
            '                                        1.05572457615837556e-01',
            '',
            'ina.h         9.89999999999999991e-01  -2.57573692422314801e-03',
            '                                       -2.57573692422314801e-03',
            '',
            'ina.j         9.69999999999999973e-01   2.27729027201508923e-04',
            '                                        2.27729027201508923e-04',
            '',
            'is.d          3.00000000000000006e-03   3.37267935768704313e-06',
            '                                        3.37267935768704313e-06',
            '',
            'is.f          1.00000000000000000e+00  -3.66608204332271936e-07',
            '                                       -3.66608204332271936e-07',
            '',
            'ix1.x1        2.99999999999999989e-02  -1.06690490942922786e-04',
            '                                       -1.06690490942922786e-04',
            '',
            'calcium.Cai   1.80000000000000011e-04  -8.14771094609788952e-08',
            '                                       -8.14771094609788952e-08',
            '',
            'Model check completed without errors.',
            '-' * 79,
        ]
        for a, b in zip(x, y):
            self.assertTrue(almost_equal(a, b))
        self.assertEqual(len(x), len(y))

        # Test comparison against another model, with an initial state
        x = myokit.step(m1, reference=m2, state=state).splitlines()
        y = [
            'Evaluating state vector derivatives...',
            '-' * 79,
            'Name         Initial value             Derivative at t=0       ',
            '-' * 79,
            'membrane.V   -8.00000000000000000e+01   6.99933961152120032e-01',
            '                                        6.99933961152120032e-01',
            '',
            'ina.m         9.99999999999999955e-08   1.26374945544508321e+00',
            '                                        1.26374945544508321e+00',
            '',
            'ina.h         1.00000000000000006e-01   2.38558150922925788e-01',
            '                                        2.38558150922925788e-01',
            '',
            'ina.j         9.00000000000000022e-01   1.43519283896554857e-03',
            '                                        1.43519283896554857e-03',
            '',
            'is.d          9.00000000000000022e-01  -9.96503893516665490e-02',
            '                                       -9.96503893516665490e-02',
            '',
            'is.f          1.00000000000000006e-01   1.63647819146313829e-02',
            '                                        1.63647819146313829e-02',
            '',
            'ix1.x1        9.00000000000000022e-01  -3.55793884094798146e-03',
            '                                       -3.55793884094798146e-03',
            '',
            'calcium.Cai   1.00000000000000006e-01  -6.89766400310046473e-03',
            '                                       -6.89766400310046473e-03',
            '',
            'Model check completed without errors.',
            '-' * 79,
        ]
        for a, b in zip(x, y):
            self.assertTrue(almost_equal(a, b))
        self.assertEqual(len(x), len(y))

        # Test comparison against stored data
        # And get all the different error outputs
        ref = m1.evaluate_derivatives()
        ref[0] += 3e-19  # < 1 eps
        ref[2] += 1e-16  # Tiny error
        ref[4] *= -1     # Sign error
        ref[6] -= 2e-4   # Big error
        ref[7] *= 100    # Exponent
        x = myokit.step(m1, reference=ref).splitlines()
        y = [
'Evaluating state vector derivatives...',
'-' * 79,
'Name         Initial value             Derivative at t=0       ',
'-' * 79,
'membrane.V   -8.43499999999999943e+01  -1.59225544529053437e-03',
'                                       -1.59225544529053415e-03 <= 1 eps',
'',
'ina.m         1.00000000000000002e-02   1.05572457615837556e-01',
'                                        1.05572457615837556e-01',
'',
'ina.h         9.89999999999999991e-01  -2.57573692422314801e-03',
'                                       -2.57573692422304783e-03 ~ 175.2 eps',
'                                                      ^^^^^^^^^',
'ina.j         9.69999999999999973e-01   2.27729027201508923e-04',
'                                        2.27729027201508923e-04',
'',
'is.d          3.00000000000000006e-03   3.37267935768704313e-06',
'                                       -3.37267935768704313e-06 sign',
'                                       ^^^^^^^^^^^^^^^^^^^^^^^^',
'is.f          1.00000000000000000e+00  -3.66608204332271936e-07',
'                                       -3.66608204332271936e-07',
'',
'ix1.x1        2.99999999999999989e-02  -1.06690490942922786e-04',
'                                        -3.06690490942922796e-04 X',
'                                       ^^^^^^^^^^^^^^^^^^^^^^^^',
'calcium.Cai   1.80000000000000011e-04  -8.14771094609788952e-08',
'                                       -8.14771094609788952e-06 exponent',
'                                                           ^^^^',
'Found (3) large mismatches between output and reference values.',
'Found (1) small mismatches.',
'-' * 79,
        ]
        for a, b in zip(x, y):
            self.assertTrue(almost_equal(a, b))
        self.assertEqual(len(x), len(y))

        # Test positive/negative zero comparison
        m1 = myokit.Model()
        c = m1.add_component('c')
        t = c.add_variable('t')
        t.set_binding('time')
        t.set_rhs(0)
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
        for a, b in zip(x, y):
            self.assertEqual(a, b)
        self.assertEqual(len(x), len(y))

        # Test setting inputs
        m1.get('c').add_variable('p', rhs=0, binding='pace')
        m1.get('c.x').set_rhs('3 * c.t')
        m1.get('c.y').set_rhs('c.p + c.t')
        x = myokit.step(m1).splitlines()
        y = [
            'Evaluating state vector derivatives...',
            '-' * 79,
            'Name  Initial value             Derivative at t=0       ',
            '-' * 79,
            'c.x    1.00000000000000000e+00   0.00000000000000000e+00',
            'c.y    1.00000000000000000e+00   0.00000000000000000e+00',
            '-' * 79,
        ]
        for a, b in zip(x, y):
            self.assertEqual(a, b)
        self.assertEqual(len(x), len(y))
        y[4:6] = ['c.x    1.00000000000000000e+00   6.00000000000000000e+00',
                  'c.y    1.00000000000000000e+00   2.50000000000000000e+00']
        x = myokit.step(m1, inputs={'time': 2, 'pace': 0.5}).splitlines()
        for a, b in zip(x, y):
            self.assertEqual(a, b)
        # Non-existent / unbound are ignored
        y[4:6] = ['c.x    1.00000000000000000e+00   6.00000000000000000e+00',
                  'c.y    1.00000000000000000e+00   2.00000000000000000e+00']
        x = myokit.step(m1, inputs={'time': 2, 'hello': 0.5}).splitlines()
        for a, b in zip(x, y):
            self.assertEqual(a, b)

        # No issues when passing initial state from a model
        # See https://github.com/myokit/myokit/pull/1083
        myokit.step(m1, reference=m2, state=m1.initial_values())

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
        self.assertIsInstance(raw, str)
        parts = raw.split('.')
        self.assertTrue(len(parts) in [3, 4])

        # Formatted version
        v = myokit.version()
        v = v.splitlines()
        self.assertEqual(len(v), 3)


if __name__ == '__main__':
    unittest.main()
