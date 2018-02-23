.. _api/expressions:

***********
Expressions
***********

.. module:: myokit

Mathematical expressions in Myokit are represented as trees of
:class:`Expression` objects. For example the expression `5 + 2` is represented
as a :class:`Plus` expression with two operands of the type
:class:`Number`. All expressions extend the :class:`Expression` base
class described below.

Creating expression trees manually is a labour-intesive process. In most cases,
expressions will be created by the :ref:`parser <api/io>`.

.. _api/myokit.Expression:
.. autoclass:: Expression
   :members:

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
   :members:

.. _api/myokit.LhsExpression:
.. autoclass:: LhsExpression
   :members:

.. _api/myokit.Name:
.. autoclass:: Name
   :members:

.. _api/myokit.Derivative:
.. autoclass:: Derivative
   :members:

Operators
---------

.. _api/myokit.PrefixExpression:
.. autoclass:: PrefixExpression
   :members:

.. _api/myokit.InfixExpression:
.. autoclass:: InfixExpression
   :members:

Functions
---------

.. _api/myokit.Function:
.. autoclass:: Function
   :members:

Conditions
----------

.. _api/myokit.Condition:
.. autoclass:: Condition
    :members:

.. _api/myokit.PrefixCondition:
.. autoclass:: PrefixCondition
    :members:

.. _api/myokit.InfixCondition:
.. autoclass:: InfixCondition
    :members:

Unary plus and minus
--------------------

.. _api/myokit.PrefixPlus:
.. autoclass:: PrefixPlus
   :members:

.. _api/myokit.PrefixMinus:
.. autoclass:: PrefixMinus
   :members:

Addition and multiplication
----------------------------

.. _api/myokit.Plus:
.. autoclass:: Plus
   :members:

.. _api/myokit.Minus:
.. autoclass:: Minus
   :members:

.. _api/myokit.Multiply:
.. autoclass:: Multiply
   :members:

.. _api/myokit.Divide:
.. autoclass:: Divide
   :members:

Powers and roots
----------------

.. _api/myokit.Power:
.. autoclass:: Power
   :members:

.. _api/myokit.Sqrt:
.. autoclass:: Sqrt
   :members:

Logarithms and e
----------------

.. _api/myokit.Exp:
.. autoclass:: Exp
   :members:

.. _api/myokit.Log:
.. autoclass:: Log
   :members:

.. _api/myokit.Log10:
.. autoclass:: Log10
   :members:

.. _api/expressions/trig:

Trigonometric functions
-----------------------

All trigonometric functions use angles in radians.

.. _api/myokit.Sin:
.. autoclass:: Sin
   :members:

.. _api/myokit.Cos:
.. autoclass:: Cos
   :members:

.. _api/myokit.Tan:
.. autoclass:: Tan
   :members:

.. _api/myokit.ASin:
.. autoclass:: ASin
   :members:

.. _api/myokit.ACos:
.. autoclass:: ACos
   :members:

.. _api/myokit.ATan:
.. autoclass:: ATan
   :members:

.. _api/expressions/conditional:

Conditional operators
---------------------
.. _api/myokit.If:
.. autoclass:: If
   :members:

.. _api/myokit.Piecewise:
.. autoclass:: Piecewise
   :members:

.. _api/myokit.OrderedPiecewise:
.. autoclass:: OrderedPiecewise
   :members:

.. _api/myokit.Not:
.. autoclass:: Not
    :members:

.. _api/myokit.Equal:
.. autoclass:: Equal
    :members:

.. _api/myokit.NotEqual:
.. autoclass:: NotEqual
    :members:

.. _api/myokit.More:
.. autoclass:: More
    :members:

.. _api/myokit.Less:
.. autoclass:: Less
    :members:

.. _api/myokit.MoreEqual:
.. autoclass:: MoreEqual
    :members:

.. _api/myokit.LessEqual:
.. autoclass:: LessEqual
    :members:

.. _api/myokit.And:
.. autoclass:: And
    :members:

.. _api/myokit.Or:
.. autoclass:: Or
    :members:

.. _api/expressions/misc:

Miscellaneous
-------------
.. _api/myokit.Abs:
.. autoclass:: Abs
   :members:

.. _api/myokit.Floor:
.. autoclass:: Floor
   :members:

.. _api/myokit.Ceil:
.. autoclass:: Ceil
   :members:

.. _api/myokit.Quotient:
.. autoclass:: Quotient
   :members:

.. _api/myokit.Remainder:
.. autoclass:: Remainder
   :members:
   
.. _api/myokit.Polynomial:
.. autoclass:: Polynomial
   :members:
   
.. _api/myokit.Spline:
.. autoclass:: Spline
   :members:
   
.. _api/myokit.UnsupportedFunction:
.. autoclass:: UnsupportedFunction
    :members:
    
.. _api/myokit.UserFunction:
.. autoclass:: UserFunction
    :members:
