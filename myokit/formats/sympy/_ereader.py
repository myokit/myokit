#
# Sympy expression reader
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import myokit
import myokit.formats


class SymPyExpressionReader:
    """
    Converts Sympy expressions to Myokit expressions.

    Any variable names will be resolved against the given model. If no model is
    given, string names will be used instead of myokit Variable objects.
    """
    def __init__(self, model=None):
        self._model = model
        self._op_map = self._build_op_map()

    def ex(self, e):
        """
        Converts the Sympy expression ``e`` to a :class:`myokit.Expression`.
        """
        from sympy.core.numbers import Number
        try:
            action = self._op_map[type(e)]
        except KeyError:
            if isinstance(e, Number):
                action = self._ex_number
            else:
                raise ValueError('Unsupported type: ' + str(type(e)))
        return action(e)

    def set_model(self, model=None):
        """
        Changes the model used by this reader to resolve variable names.
        """
        self._model = model

    def _build_op_map(self):
        """
        Creates and returns a mapping of sympy object types to handling
        methods.
        """
        from sympy.core.symbol import Symbol
        from sympy.core.add import Add
        from sympy.core.mul import Mul
        from sympy.core.mod import Mod
        from sympy.core.power import Pow
        from sympy.functions.elementary.trigonometric import (
            sin, cos, tan, asin, acos, atan)
        from sympy.functions.elementary.exponential import exp, log
        from sympy.functions.elementary.integers import floor, ceiling
        from sympy.functions.elementary.complexes import Abs
        from sympy.logic.boolalg import Not
        from sympy.core.relational import (
            Equality, Unequality, StrictGreaterThan, StrictLessThan,
            GreaterThan, LessThan)
        from sympy.logic.boolalg import And, Or
        from sympy.functions.elementary.piecewise import Piecewise

        return {
            Symbol: self._ex_name,
            Add: self._ex_plus,
            Mul: self._ex_multiply,
            Mod: self._ex_remainder,
            Pow: self._ex_power,
            sin: self._ex_sin,
            cos: self._ex_cos,
            tan: self._ex_tan,
            asin: self._ex_asin,
            acos: self._ex_acos,
            atan: self._ex_atan,
            exp: self._ex_exp,
            log: self._ex_log,
            floor: self._ex_floor,
            ceiling: self._ex_ceil,
            Abs: self._ex_abs,
            Not: self._ex_not,
            Equality: self._ex_equal,
            Unequality: self._ex_not_equal,
            StrictGreaterThan: self._ex_more,
            StrictLessThan: self._ex_less,
            GreaterThan: self._ex_more_equal,
            LessThan: self._ex_less_equal,
            And: self._ex_and,
            Or: self._ex_or,
            Piecewise: self._ex_piecewise,
        }

    def _ex_name(self, e):
        var = str(e)
        # Check if this is a derivative
        # See :meth:`SymPyExpressionWriter._ex_derivative()`.
        if self._model:
            if var[:4] == 'dot(' and var[-1:] == ')':
                var = self._model.get(var[4:-1], myokit.Variable)
                return myokit.Derivative(myokit.Name(var))
            var = self._model.get(var, myokit.Variable)
        return myokit.Name(var)

    def _ex_number(self, e):
        return myokit.Number(float(e))

    def _ex_plus(self, e):
        a, b = e.as_two_terms()
        return myokit.Plus(self.ex(a), self.ex(b))

    def _ex_multiply(self, e):
        from sympy.core.numbers import NegativeOne
        a, b = e.as_two_terms()
        if type(a) == NegativeOne:
            return myokit.PrefixMinus(self.ex(b))
        return myokit.Multiply(self.ex(a), self.ex(b))

    def _ex_remainder(self, e):
        a, b = e.args
        return myokit.Remainder(self.ex(a), self.ex(b))

    def _ex_power(self, e):
        a, b = e.args
        return myokit.Power(self.ex(a), self.ex(b))

    def _ex_sin(self, e):
        return myokit.Sin(self.ex(e.args[0]))

    def _ex_cos(self, e):
        return myokit.Cos(self.ex(e.args[0]))

    def _ex_tan(self, e):
        return myokit.Tan(self.ex(e.args[0]))

    def _ex_asin(self, e):
        return myokit.ASin(self.ex(e.args[0]))

    def _ex_acos(self, e):
        return myokit.ACos(self.ex(e.args[0]))

    def _ex_atan(self, e):
        return myokit.ATan(self.ex(e.args[0]))

    def _ex_exp(self, e):
        return myokit.Exp(self.ex(e.args[0]))

    def _ex_log(self, e):
        return myokit.Log(*[self.ex(x) for x in e.args])

    def _ex_floor(self, e):
        return myokit.Floor(self.ex(e.args[0]))

    def _ex_ceil(self, e):
        return myokit.Ceil(self.ex(e.args[0]))

    def _ex_abs(self, e):
        return myokit.Abs(self.ex(e.args[0]))

    def _ex_not(self, e):   # pragma: no cover
        # Sympy turns not(a == b) into a != b etc., so can't test!
        return myokit.Not(self.ex(e.args[0]))

    def _ex_equal(self, e):
        return myokit.Equal(*[self.ex(x) for x in e.args])

    def _ex_not_equal(self, e):
        return myokit.NotEqual(*[self.ex(x) for x in e.args])

    def _ex_more(self, e):
        return myokit.More(*[self.ex(x) for x in e.args])

    def _ex_less(self, e):
        return myokit.Less(*[self.ex(x) for x in e.args])

    def _ex_more_equal(self, e):
        return myokit.MoreEqual(*[self.ex(x) for x in e.args])

    def _ex_less_equal(self, e):
        return myokit.LessEqual(*[self.ex(x) for x in e.args])

    def _ex_and(self, e):
        return myokit.And(*[self.ex(x) for x in e.args])

    def _ex_or(self, e):
        return myokit.Or(*[self.ex(x) for x in e.args])

    def _ex_piecewise(self, e):
        from sympy.logic.boolalg import BooleanTrue, BooleanFalse

        args = []
        n = len(e.args) - 1
        for k, pair in enumerate(e.args):
            expr, cond = pair
            expr = self.ex(expr)
            cond_is_true = False
            if type(cond) == BooleanTrue:
                cond_is_true = True
                cond = myokit.Equal(myokit.Number(1), myokit.Number(1))
            elif type(cond) == BooleanFalse:    # pragma: no cover
                # Cover pragma: SymPy currently optimises out BooleanFalse
                cond = myokit.Equal(myokit.Number(0), myokit.Number(1))
            else:
                cond = self.ex(cond)
            if k < n:
                args.append(cond)
                args.append(expr)
        if cond_is_true:
            args.append(expr)
        else:
            args.append(cond)
            args.append(expr)
            args.append(myokit.Number(0))
        return myokit.Piecewise(*args)
