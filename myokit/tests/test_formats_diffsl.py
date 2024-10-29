#!/usr/bin/env python3
#
# Tests the DiffSL module.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import itertools
import unittest

import myokit
import myokit.formats
import myokit.formats.diffsl
import myokit.tests
from myokit import (Abs, ACos, And, ASin, ATan, Ceil, Cos, Divide, Equal, Exp,
                    Floor, If, Less, LessEqual, Log, Log10, Minus, More,
                    MoreEqual, Multiply, Not, NotEqual, Number, Or, Piecewise,
                    Plus, Power, PrefixMinus, PrefixPlus, Quotient, Remainder,
                    Sin, Sqrt, Tan)
from myokit.tests import TemporaryDirectory, WarningCollector

# Model that requires unit conversion
units_model = """
[[model]]
mb.V = -0.08
hh.x = 0.1
hh.y = 0.9
mm.C = 0.9

[engine]
pace = 0 bind pace
time = 0 [s]
    in [s]
    bind time

[ideal]
Vc = engine.pace * 1

[mb]
dot(V) = (hh.I1 + mm.I2 + tt.I3) / C
    in [V]
C = 20 [pF]
    in [pF]

[hh]
dot(x) = (inf - x) / tau
    inf = 0.8
    tau = 3 [s]
        in [s]
dot(y) = alpha * (1 - y) - beta * y
    alpha = 0.1 [1/s]
        in [1/s]
    beta = 0.2 [1/s]
        in [1/s]
I1 = 3 [pS] * x * y * (mb.V - 0.05 [V])
    in [pA]

[mm]
dot_C = beta * O - alpha * C
dot(C) = dot_C
alpha = 0.3 [1/s]
    in [1/s]
beta = 0.4 [1/s]
    in [1/s]
O = 1 - C
I2 = 2 [pS] * O * (mb.V + 0.02 [V])
    in [pA]

[tt]
I3 = 4 [pS] * mm.O * (mb.V + 0.02 [V])
tTest = 0
t_Test = 1
t_test = 2
I4 = if(hh.I1 < 0.1 [pA], 0 [pA], 1 [pA])
I5 = if(mm.I2 < 0.1 [pA], 1 [pA], 0 [pA])
"""

units_output = """
/*
This file was generated by Myokit.
*/

/* Input parameters */
/* E.g. in = [ varZero, varOne, varTwo ] */
in = [ ]

/* Engine: pace */
/* E.g.
  -80 * (1 - sigmoid((t-100)*5000))
  -120 * (sigmoid((t-100)*5000) - sigmoid((t-200)*5000))
*/
enginePace { 0.0 } /* engine.pace */

/* Constants: hh */
hhXInf { 0.8 } /* hh.x.inf */
hhXTau { 3.0 } /* hh.x.tau [s] */
hhYAlpha { 0.1 } /* hh.y.alpha [S/F] */
hhYBeta { 0.2 } /* hh.y.beta [S/F] */

/* Constants: mm */
mmAlpha { 0.3 } /* mm.alpha [S/F] */
mmBeta { 0.4 } /* mm.beta [S/F] */

/* Constants: tt */
ttTTest1 { 0.0 } /* tt.tTest */
ttTTest2 { 1.0 } /* tt.t_Test */
ttTTest3 { 2.0 } /* tt.t_test */

/* Constants: mb */
mbC { 20.0 } /* mb.C [pF] */

/* Initial conditions */
u_i {
  mbV = -0.08 * 1000 [1 (0.001)], /* mb.V [mV] */
  hhX = 0.1, /* hh.x */
  hhY = 0.9, /* hh.y */
  mmC = 0.9, /* mm.C */
}

dudt_i {
  diffMbV = 0,
  diffHhX = 0,
  diffHhY = 0,
  diffMmC = 0,
}

/* Variables: hh */
hhI1 { 3.0 * hhX * hhY * (mbV / 1000.0 - 0.05) * 0.05 } /* hh.I1 [A/F] */

/* Variables: mm */
mmO { 1.0 - mmC } /* mm.O */
mmI2 { 2.0 * mmO * (mbV / 1000.0 + 0.02) * 0.05 } /* mm.I2 [A/F] */
mmDotC { mmBeta * mmO - mmAlpha * mmC } /* mm.dot_C */

/* Variables: ideal */
idealVc { enginePace * 1.0 } /* ideal.Vc */

/* Variables: tt */
ttI3 { 4.0 * mmO * (mbV / 1000.0 + 0.02) } /* tt.I3 */
ttI4 { 1.0 * heaviside(hhI1 / 0.05 - 0.1) } /* tt.I4 */
ttI5 { 1.0 * (1 - heaviside(mmI2 / 0.05 - 0.1)) } /* tt.I5 */

/* Solve */
F_i {
  diffMbV,
  diffHhX,
  diffHhY,
  diffMmC,
}

G_i {
  (hhI1 / 0.05 + mmI2 / 0.05 + ttI3) / mbC * 1000.0 / 1000.0,
  (hhXInf - hhX) / hhXTau / 1000.0,
  (hhYAlpha * (1.0 - hhY) - hhYBeta * hhY) / 1000.0,
  mmDotC / 1000.0,
}

/* Output */
out_i {
  hhX,
  hhY,
  mbV,
  mmC,
}
"""


class DiffSLExporterTest(unittest.TestCase):
    """Tests DiffSL export."""

    def test_diffsl_exporter(self):
        # Tests exporting a model

        model = myokit.load_model('example')
        with TemporaryDirectory() as d:
            path = d.path('diffsl.model')

            e = myokit.formats.diffsl.DiffSLExporter()

            # Test with simple model
            e.model(path, model)

            # Test with protocol set
            with self.assertRaisesRegex(ValueError, 'input protocol'):
                e.model(path, model, protocol='-80 + 120*heaviside(t-10)')

            # Test with extra bound variables
            model.get('membrane.C').set_binding('hello')
            e.model(path, model)

            # Test without V being a state variable
            v = model.get('membrane.V')
            v.demote()
            v.set_rhs(3)
            e.model(path, model)

            # Test with explicit time dependence
            t0 = model.get('membrane').add_variable('t0')
            t0.set_rhs('0 + engine.time')
            with self.assertRaisesRegex(myokit.ExportError, 'time dependence'):
                e.model(path, model)

            # Test with invalid model
            v.set_rhs('2 * V')
            with self.assertRaisesRegex(myokit.ExportError, 'valid model'):
                e.model(path, model)

    def test_unit_conversion(self):
        # Tests exporting a model that requires unit conversion

        # Export model
        m = myokit.parse_model(units_model)
        e = myokit.formats.diffsl.DiffSLExporter()
        with TemporaryDirectory() as d:
            path = d.path('diffsl.model')
            e.model(path, m)
            with open(path, 'r') as f:
                observed = f.read().strip().splitlines()

        # Get expected output
        expected = units_output.strip().splitlines()

        # Compare (line by line, for readable output)
        for ob, ex in zip(observed, expected):
            self.assertEqual(ob, ex)
        self.assertEqual(len(observed), len(expected))

        # Test warnings are raised if conversion fails
        m.get('mb.V').set_rhs('hh.I1 + mm.I2')
        m.get('mb').remove_variable(m.get('mb.C'))
        with TemporaryDirectory() as d:
            path = d.path('diffsl.model')
            with WarningCollector() as c:
                e.model(path, m)
            self.assertIn('Unable to convert hh.I1', c.text())
            self.assertIn('Unable to convert mm.I2', c.text())

        m.get('engine.time').set_unit(myokit.units.cm)
        with TemporaryDirectory() as d:
            path = d.path('diffsl.model')
            with WarningCollector() as c:
                e.model(path, m)
            self.assertIn('Unable to convert engine.time', c.text())

    def test_diffsl_exporter_fetching(self):
        # Tests getting an DiffSL exporter via the 'exporter' interface

        e = myokit.formats.exporter('diffsl')
        self.assertIsInstance(e, myokit.formats.diffsl.DiffSLExporter)

    def test_capability_reporting(self):
        # Tests if the correct capabilities are reported
        e = myokit.formats.diffsl.DiffSLExporter()
        self.assertTrue(e.supports_model())


class DiffSLExpressionWriterTest(myokit.tests.ExpressionWriterTestCase):
    """Test conversion to DiffSL syntax."""

    _name = 'diffsl'
    _target = myokit.formats.diffsl.DiffSLExpressionWriter

    def test_number(self):
        self.eq(Number(1), '1.0')
        self.eq(Number(-2), '-2.0')
        self.eq(Number(13, 'mV'), '13.0')

    def test_name(self):
        # Inherited from CBasedExpressionWriter
        self.eq(self.a, 'a')
        w = self._target()
        w.set_lhs_function(lambda v: v.var().qname().upper())
        self.assertEqual(w.ex(self.a), 'COMP.A')

    def test_derivative(self):
        # Inherited from CBasedExpressionWriter
        self.eq(myokit.Derivative(self.a), 'dot(a)')

    def test_partial_derivative(self):
        e = myokit.PartialDerivative(self.a, self.b)
        self.assertRaisesRegex(NotImplementedError, 'Partial', self.w.ex, e)

    def test_initial_value(self):
        e = myokit.InitialValue(self.a)
        self.assertRaisesRegex(NotImplementedError, 'Initial', self.w.ex, e)

    def test_prefix_plus_minus(self):
        # Inherited from CBasedExpressionWriter
        p = Number(11, 'kV')
        a, b, c = self.abc
        self.eq(PrefixPlus(p), '+11.0')
        self.eq(PrefixPlus(PrefixPlus(PrefixPlus(p))), '+(+(+11.0))')
        self.eq(Divide(PrefixPlus(Plus(a, b)), c), '+(a + b) / c')
        self.eq(PrefixMinus(p), '-11.0')
        self.eq(PrefixMinus(PrefixMinus(p)), '-(-11.0)')
        self.eq(PrefixMinus(Number(-1)), '-(-1.0)')
        self.eq(PrefixMinus(Minus(a, b)), '-(a - b)')
        self.eq(Multiply(PrefixMinus(Plus(b, a)), c), '-(b + a) * c')
        self.eq(PrefixMinus(Divide(b, a)), '-(b / a)')

    def test_plus_minus(self):
        a, b, c = self.abc
        self.eq(Plus(a, b), 'a + b')
        self.eq(Plus(Plus(a, b), c), 'a + b + c')
        self.eq(Plus(a, Plus(b, c)), 'a + (b + c)')

        self.eq(Minus(a, b), 'a - b')
        self.eq(Minus(Minus(a, b), c), 'a - b - c')
        self.eq(Minus(a, Minus(b, c)), 'a - (b - c)')

        self.eq(Minus(a, b), 'a - b')
        self.eq(Plus(Minus(a, b), c), 'a - b + c')
        self.eq(Minus(a, Plus(b, c)), 'a - (b + c)')
        self.eq(Minus(Plus(a, b), c), 'a + b - c')
        self.eq(Minus(a, Plus(b, c)), 'a - (b + c)')

        # No expm in DiffSL
        self.eq(Minus(Exp(Number(2)), Number(1)), 'exp(2.0) - 1.0')
        self.eq(Minus(Number(1), Exp(Number(3))), '1.0 - exp(3.0)')

    def test_multiply_divide(self):
        # Inherited from CBasedExpressionWriter
        a, b, c = self.abc
        self.eq(Multiply(a, b), 'a * b')
        self.eq(Multiply(Multiply(a, b), c), 'a * b * c')
        self.eq(Multiply(a, Multiply(b, c)), 'a * (b * c)')
        self.eq(Divide(a, b), 'a / b')
        self.eq(Divide(Divide(a, b), c), 'a / b / c')
        self.eq(Divide(a, Divide(b, c)), 'a / (b / c)')

    def test_quotient(self):
        # Inherited from CBasedExpressionWriter
        a, b, c = self.abc
        with WarningCollector():
            self.eq(Quotient(a, b), 'floor(a / b)')
            self.eq(Quotient(Plus(a, c), b), 'floor((a + c) / b)')
            self.eq(Quotient(Divide(a, c), b), 'floor(a / c / b)')
            self.eq(Quotient(a, Divide(b, c)), 'floor(a / (b / c))')
            self.eq(Multiply(Quotient(a, b), c), 'floor(a / b) * c')
            self.eq(Multiply(c, Quotient(a, b)), 'c * (floor(a / b))')

    def test_remainder(self):
        # Inherited from CBasedExpressionWriter
        a, b, c = self.abc
        with WarningCollector():
            self.eq(Remainder(a, b), '(a - b * floor(a / b))')
            self.eq(
                Remainder(Plus(a, c), b), '(a + c - b * floor((a + c) / b))'
            )
            self.eq(Multiply(Remainder(a, b), c), '(a - b * floor(a / b)) * c')
            self.eq(Divide(c, Remainder(b, a)), 'c / ((b - a * floor(b / a)))')

    def test_power(self):
        # Inherited from CBasedExpressionWriter
        a, b, c = self.abc
        self.eq(Power(a, b), 'pow(a, b)')
        self.eq(Power(Power(a, b), c), 'pow(pow(a, b), c)')
        self.eq(Power(a, Power(b, c)), 'pow(a, pow(b, c))')

    def test_log(self):
        # Inherited from CBasedExpressionWriter
        a, b = self.ab
        self.eq(Log(a), 'log(a)')
        self.eq(Log10(a), '(log(a) / log(10.0))')
        self.eq(Log(a, b), '(log(a) / log(b))')

    def test_supported_functions(self):
        a = self.a

        self.eq(Abs(a), 'abs(a)')
        self.eq(Cos(a), 'cos(a)')
        self.eq(Exp(a), 'exp(a)')
        self.eq(Log(a), 'log(a)')
        self.eq(Sin(a), 'sin(a)')
        self.eq(Sqrt(a), 'sqrt(a)')
        self.eq(Tan(a), 'tan(a)')

    def test_unsupported_functions(self):
        a = self.a

        with WarningCollector() as wc:
            self.eq(ACos(a), 'acos(a)')
        self.assertIn('Unsupported', wc.text())

        with WarningCollector() as wc:
            self.eq(ASin(a), 'asin(a)')
        self.assertIn('Unsupported', wc.text())

        with WarningCollector() as wc:
            self.eq(ATan(a), 'atan(a)')
        self.assertIn('Unsupported', wc.text())

        with WarningCollector() as wc:
            self.eq(Ceil(a), 'ceil(a)')
        self.assertIn('Unsupported', wc.text())

        with WarningCollector() as wc:
            self.eq(Floor(a), 'floor(a)')
        self.assertIn('Unsupported', wc.text())

    def test_conditional_operators(self):
        a, b, c, d = self.abcd

        self.eq(Equal(a, b), 'heaviside(a - b) * heaviside(b - a)')

        self.eq(Less(a, b), '(1 - heaviside(a - b))')

        self.eq(LessEqual(a, b), 'heaviside(b - a)')

        self.eq(More(a, b), '(1 - heaviside(b - a))')

        self.eq(MoreEqual(a, b), 'heaviside(a - b)')

        self.eq(NotEqual(a, b), '(1 - heaviside(a - b) * heaviside(b - a))')

        self.eq(Not(NotEqual(a, b)), 'heaviside(a - b) * heaviside(b - a)')

        self.eq(Not(Not(Equal(a, b))), 'heaviside(a - b) * heaviside(b - a)')

        self.eq(
            And(Equal(a, b), NotEqual(c, d)),
            'heaviside(a - b) * heaviside(b - a)'
            ' * (1 - heaviside(c - d) * heaviside(d - c))',
        )

        self.eq(
            Or(More(d, c), MoreEqual(b, a)),
            '(1 - heaviside(c - d) * (1 - heaviside(b - a)))',
        )

        self.eq(
            Or(Less(d, c), LessEqual(b, a)),
            '(1 - heaviside(d - c) * (1 - heaviside(a - b)))',
        )

        self.eq(
            Not(Or(Equal(Number(1), Number(2)), Equal(Number(3), Number(4)))),
            '(1 - heaviside(1.0 - 2.0) * heaviside(2.0 - 1.0))'
            ' * (1 - heaviside(3.0 - 4.0) * heaviside(4.0 - 3.0))',
        )

        self.eq(Not(Less(Number(1), Number(2))), 'heaviside(1.0 - 2.0)')

    def test_if_expressions(self):
        a, b, c, d = self.abcd

        self.eq(
            If(Equal(a, b), c, d),
            '(c * heaviside(a - b) * heaviside(b - a)'
            ' + d * (1 - heaviside(a - b) * heaviside(b - a)))',
        )

        self.eq(
            If(Equal(a, b), c, Number(0)),
            'c * heaviside(a - b) * heaviside(b - a)',
        )

        self.eq(
            If(Equal(a, b), Number(0), d),
            'd * (1 - heaviside(a - b) * heaviside(b - a))',
        )

        self.eq(
            If(Equal(a, b), c, Number(1)),
            '(c * heaviside(a - b) * heaviside(b - a)'
            ' + (1 - heaviside(a - b) * heaviside(b - a)))',
        )

        self.eq(
            If(Equal(a, b), Number(1), d),
            '(heaviside(a - b) * heaviside(b - a)'
            ' + d * (1 - heaviside(a - b) * heaviside(b - a)))',
        )

        self.eq(
            If(NotEqual(a, b), c, d),
            '(c * (1 - heaviside(a - b) * heaviside(b - a))'
            ' + d * heaviside(a - b) * heaviside(b - a))',
        )

        self.eq(
            If(More(a, b), c, d),
            '(c * (1 - heaviside(b - a)) + d * heaviside(b - a))',
        )

        self.eq(
            If(MoreEqual(a, b), c, d),
            '(c * heaviside(a - b) + d * (1 - heaviside(a - b)))',
        )

        self.eq(
            If(Less(a, b), c, d),
            '(c * (1 - heaviside(a - b)) + d * heaviside(a - b))',
        )

        self.eq(
            If(LessEqual(a, b), c, d),
            '(c * heaviside(b - a) + d * (1 - heaviside(b - a)))',
        )

    def test_piecewise_expressions(self):
        a, b, c, d = self.abcd

        self.eq(Piecewise(Equal(a, b), c, d), self.w.ex(If(Equal(a, b), c, d)))

        self.eq(
            Piecewise(NotEqual(a, b), c, d),
            self.w.ex(
                If(NotEqual(a, b), c, d),
            ),
        )

        self.eq(
            Piecewise(More(a, b), c, d),
            self.w.ex(
                If(More(a, b), c, d),
            ),
        )

        self.eq(
            Piecewise(MoreEqual(a, b), c, d),
            self.w.ex(If(MoreEqual(a, b), c, d)),
        )

        self.eq(Piecewise(Less(a, b), c, d), self.w.ex(If(Less(a, b), c, d)))

        self.eq(
            Piecewise(LessEqual(a, b), c, d),
            self.w.ex(
                If(LessEqual(a, b), c, d),
            ),
        )

        self.eq(
            Piecewise(Equal(a, b), c, Equal(a, d), Number(3), Number(4)),
            self.w.ex(
                If(Equal(a, b), c, If(Equal(a, d), Number(3), Number(4)))
            ),
        )

        self.eq(
            Piecewise(Less(a, b), Number(0), Less(c, d), Number(0), Number(5)),
            '5.0 * heaviside(c - d) * heaviside(a - b)',
        )

    def test_heaviside_numerical(self):
        """Test generated heaviside expressions with numerical values"""

        def heaviside(x):
            return 1 if x >= 0 else 0

        values = itertools.product(
            [-10e9, -1, -1e-9, 0, 1e-9, 1, 10e9], repeat=4
        )

        for a, b, c, d in values:
            # a == b
            result = int(a == b)
            expr = self.w.ex(Equal(Number(a), Number(b)))
            self.assertEqual(eval(expr), result)

            # a < b
            result = int(a < b)
            expr = self.w.ex(Less(Number(a), Number(b)))
            self.assertEqual(eval(expr), result)

            # a <= b
            result = int(a <= b)
            expr = self.w.ex(LessEqual(Number(a), Number(b)))
            self.assertEqual(eval(expr), result)

            # a > b
            result = int(a > b)
            expr = self.w.ex(More(Number(a), Number(b)))
            self.assertEqual(eval(expr), result)

            # a >= b
            result = int(a >= b)
            expr = self.w.ex(MoreEqual(Number(a), Number(b)))
            self.assertEqual(eval(expr), result)

            # a != b
            result = int(a != b)
            expr = self.w.ex(NotEqual(Number(a), Number(b)))
            self.assertEqual(eval(expr), result)

            # not(a != b)
            result = int(not (a != b))
            expr = self.w.ex(Not(NotEqual(Number(a), Number(b))))
            self.assertEqual(eval(expr), result)

            # not(not(a == b))
            result = int(not (not (a == b)))
            expr = self.w.ex(Not(Not(Equal(Number(a), Number(b)))))
            self.assertEqual(eval(expr), result)

            # (a == b) and (c != d)
            result = int((a == b) and (c != d))
            expr = self.w.ex(
                And(
                    Equal(Number(a), Number(b)), NotEqual(Number(c), Number(d))
                )
            )
            self.assertEqual(eval(expr), result)

            # (d > c) or (b >= a)
            result = int((d > c) or (b >= a))
            expr = self.w.ex(
                Or(More(Number(d), Number(c)), MoreEqual(Number(b), Number(a)))
            )
            self.assertEqual(eval(expr), result)

            # (d < c) or (b <= a)
            result = int((d < c) or (b <= a))
            expr = self.w.ex(
                Or(Less(Number(d), Number(c)), LessEqual(Number(b), Number(a)))
            )
            self.assertEqual(eval(expr), result)

            # (a == b) or (c == d)
            result = int((a == b) or (c == d))
            expr = self.w.ex(
                Or(Equal(Number(a), Number(b)), Equal(Number(c), Number(d)))
            )
            self.assertEqual(eval(expr), result)

            # not(a < b)
            result = int(not (a < b))
            expr = self.w.ex(Not(Less(Number(a), Number(b))))
            self.assertEqual(eval(expr), result)

            # if(a > b, c, d)
            result = c if (a > b) else d
            expr = self.w.ex(
                If(More(Number(a), Number(b)), Number(c), Number(d))
            )
            self.assertEqual(eval(expr), result)

            # if(a >= b, c, d)
            result = c if (a >= b) else d
            expr = self.w.ex(
                If(MoreEqual(Number(a), Number(b)), Number(c), Number(d))
            )
            self.assertEqual(eval(expr), result)

            # if(a < b, c, d)
            result = c if (a < b) else d
            expr = self.w.ex(
                If(Less(Number(a), Number(b)), Number(c), Number(d))
            )
            self.assertEqual(eval(expr), result)

            # if(a <= b, c, d)
            result = c if (a <= b) else d
            expr = self.w.ex(
                If(LessEqual(Number(a), Number(b)), Number(c), Number(d))
            )
            self.assertEqual(eval(expr), result)

            # piecewise(a > b, c, d)
            result = c if (a > b) else d
            expr = self.w.ex(
                Piecewise(More(Number(a), Number(b)), Number(c), Number(d))
            )
            self.assertEqual(eval(expr), result)

            # piecewise(a >= b, c, d)
            result = c if (a >= b) else d
            expr = self.w.ex(
                Piecewise(
                    MoreEqual(Number(a), Number(b)), Number(c), Number(d)
                )
            )
            self.assertEqual(eval(expr), result)

            # piecewise(a < b, c, d)
            result = c if (a < b) else d
            expr = self.w.ex(
                Piecewise(Less(Number(a), Number(b)), Number(c), Number(d))
            )
            self.assertEqual(eval(expr), result)

            # piecewise(a <= b, c, d)
            result = c if (a <= b) else d
            expr = self.w.ex(
                Piecewise(
                    LessEqual(Number(a), Number(b)), Number(c), Number(d)
                )
            )
            self.assertEqual(eval(expr), result)

            # piecewise(a == b, c, a == d, 3, 4)
            result = c if (a == b) else (3 if (a == d) else 4)
            expr = self.w.ex(
                Piecewise(
                    Equal(Number(a), Number(b)),
                    Number(c),
                    Equal(Number(a), Number(d)),
                    Number(3),
                    Number(4),
                )
            )
            self.assertEqual(eval(expr), result)

            # piecewise(a < b, 0, c < d, 0, 5)
            result = 0 if (a < b) else (0 if (c < d) else 5)
            expr = self.w.ex(
                Piecewise(
                    Less(Number(a), Number(b)),
                    Number(0),
                    Less(Number(c), Number(d)),
                    Number(0),
                    Number(5),
                ),
            )
            self.assertEqual(eval(expr), result)


if __name__ == '__main__':
    unittest.main()
