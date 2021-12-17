.. _api/expressions:

***********
Expressions
***********

.. currentmodule:: myokit

Mathematical expressions in Myokit are represented as trees of
:class:`Expression` objects. For example the expression `5 + 2` is represented
as a :class:`Plus` expression with two operands of the type
:class:`Number`. All expressions extend the :class:`Expression` base
class described below.

Creating expression trees manually is a labour-intesive process. In most cases,
expressions will be created by the :ref:`parser <api/io>`.

.. _api/myokit.Expression:
.. autoclass:: Expression

Names and numbers
-----------------

The simplest types of expression are atomic expressions, which have either a
definite, numerical value (:class:`Number`) or point to a variable
(:class:`Name`).

For equations a distinction is made between what may appear on the left-hand
side (lhs) and right-hand side (rhs). To indicate this difference in code, all
left-hand side equations must extend the class :class:`LhsExpression`.


.. _api/myokit.Number:
.. autoclass:: Number

.. _api/myokit.LhsExpression:
.. autoclass:: LhsExpression

.. _api/myokit.Name:
.. autoclass:: Name

.. _api/myokit.Derivative:
.. autoclass:: Derivative

Operators
---------

.. _api/myokit.PrefixExpression:
.. autoclass:: PrefixExpression

.. _api/myokit.InfixExpression:
.. autoclass:: InfixExpression

Functions
---------

.. _api/myokit.Function:
.. autoclass:: Function

Conditions
----------

.. _api/myokit.Condition:
.. autoclass:: Condition

.. _api/myokit.PrefixCondition:
.. autoclass:: PrefixCondition

.. _api/myokit.InfixCondition:
.. autoclass:: InfixCondition

Unary plus and minus
--------------------

.. _api/myokit.PrefixPlus:
.. autoclass:: PrefixPlus

.. _api/myokit.PrefixMinus:
.. autoclass:: PrefixMinus

Addition and multiplication
----------------------------

.. _api/myokit.Plus:
.. autoclass:: Plus

.. _api/myokit.Minus:
.. autoclass:: Minus

.. _api/myokit.Multiply:
.. autoclass:: Multiply

.. _api/myokit.Divide:
.. autoclass:: Divide

Powers and roots
----------------

.. _api/myokit.Power:
.. autoclass:: Power

.. _api/myokit.Sqrt:
.. autoclass:: Sqrt

Logarithms and e
----------------

.. _api/myokit.Exp:
.. autoclass:: Exp

.. _api/myokit.Log:
.. autoclass:: Log

.. _api/myokit.Log10:
.. autoclass:: Log10

.. _api/expressions/trig:

Trigonometric functions
-----------------------

All trigonometric functions use angles in radians.

.. _api/myokit.Sin:
.. autoclass:: Sin

.. _api/myokit.Cos:
.. autoclass:: Cos

.. _api/myokit.Tan:
.. autoclass:: Tan

.. _api/myokit.ASin:
.. autoclass:: ASin

.. _api/myokit.ACos:
.. autoclass:: ACos

.. _api/myokit.ATan:
.. autoclass:: ATan

.. _api/expressions/conditional:

Conditional operators
---------------------
.. _api/myokit.If:
.. autoclass:: If

.. _api/myokit.Piecewise:
.. autoclass:: Piecewise

.. _api/myokit.Not:
.. autoclass:: Not

.. _api/myokit.Equal:
.. autoclass:: Equal

.. _api/myokit.NotEqual:
.. autoclass:: NotEqual

.. _api/myokit.More:
.. autoclass:: More

.. _api/myokit.Less:
.. autoclass:: Less

.. _api/myokit.MoreEqual:
.. autoclass:: MoreEqual

.. _api/myokit.LessEqual:
.. autoclass:: LessEqual

.. _api/myokit.And:
.. autoclass:: And

.. _api/myokit.Or:
.. autoclass:: Or

.. _api/expressions/misc:

Discontinuous functions
-----------------------
.. _api/myokit.Abs:
.. autoclass:: Abs

.. _api/myokit.Floor:
.. autoclass:: Floor

.. _api/myokit.Ceil:
.. autoclass:: Ceil

.. _api/myokit.Quotient:
.. autoclass:: Quotient

.. _api/myokit.Remainder:
.. autoclass:: Remainder

Partial derivatives
--------------------
.. _api/myokit.PartialDerivative:
.. autoclass:: PartialDerivative

.. _api/myokit.InitialValue:
.. autoclass:: InitialValue

User-defined functions
----------------------
.. _api/myokit.UserFunction:
.. autoclass:: UserFunction

