#!/usr/bin/env python3
#
# Tests the DiffSL module.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import os
import unittest

import myokit
import myokit.formats
import myokit.formats.diffsl
import myokit.tests

from myokit import (
    Number, PrefixPlus, PrefixMinus, Plus, Minus,
    Multiply, Divide, Quotient, Remainder, Power, Sqrt,
    Exp, Log, Log10, Sin, Cos, Tan, ASin, ACos, ATan, Floor, Ceil, Abs,
    Not, And, Or, Equal, NotEqual, More, Less, MoreEqual, LessEqual,
    If, Piecewise,
)

from myokit.tests import TemporaryDirectory, WarningCollector, DIR_DATA


class DiffSLExpressionWriterTest(myokit.tests.ExpressionWriterTestCase):
    """ Test conversion to DiffSL syntax. """
    _name = 'diffsl'
    _target = myokit.formats.diffsl.DiffSLExpressionWriter

    def test_functions(self):
        a, b = self.ab

        self.eq(Abs(a), 'abs(a)')
        self.eq(Cos(a), 'cos(a)')
        self.eq(Exp(a), 'exp(a)')
        self.eq(Log(a), 'log(a)')
        self.eq(Sin(a), 'sin(a)')
        self.eq(Sqrt(a), 'sqrt(a)')
        self.eq(Power(a, b), 'pow(a, b)')
        self.eq(Tan(a), 'tan(a)')

        with WarningCollector() as c:
            self.eq(ACos(a), 'acos(a)')
        self.assertIn('Unsupported', c.text())

        with WarningCollector() as c:
            self.eq(ASin(a), 'asin(a)')
        self.assertIn('Unsupported', c.text())

        with WarningCollector() as c:
            self.eq(ATan(a), 'atan(a)')
        self.assertIn('Unsupported', c.text())

        with WarningCollector() as c:
            self.eq(Ceil(a), 'ceil(a)')
        self.assertIn('Unsupported', c.text())

        with WarningCollector() as c:
            self.eq(Floor(a), 'floor(a)')
        self.assertIn('Unsupported', c.text())

if __name__ == '__main__':
    unittest.main()
