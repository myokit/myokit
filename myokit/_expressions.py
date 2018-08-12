#
# Myokit symbolic expression classes. Defines different expressions, equations
# and the unit system.
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import math
import numpy

import myokit
from myokit import IntegrityError

# StringIO in Python 2 and 3
try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO

# Strings in Python 2 and 3
try:
    basestring
except NameError:   # pragma: no python 2 cover
    basestring = str

# Expression precedence levels
FUNCTION_CALL = 70
POWER = 60
PREFIX = 50
PRODUCT = 40
SUM = 30
CONDITIONAL = 20
CONDITION_AND = 10
LITERAL = 0


class Expression(object):
    """
    Myokit's most generic interface for expressions. All expressions extend
    this class.

    Expressions are immutable objects.

    Expression objects have an ``_rbp`` property determining their *right
    binding power* (myokit uses a top-down operator precedence parsing scheme)
    and an optional ``_token`` property that may contain the text token this
    expression object was originally parsed from.

    *Abstract class*
    """
    _rbp = None     # Right-binding power (see parser).
    _rep = ''       # Mmt representation
    _treeDent = 2   # Tab size used when displaying as tree.

    def __init__(self, operands=None):
        self._token = None
        # Store operands
        self._operands = () if operands is None else operands
        # Cached values
        # These _could_ be calculated immediatly, since they won't change in
        # the object's lifetime. However, it turns out to be faster to only
        # evaluate them the first time they're requested.
        self._cached_hash = None
        self._cached_polish = None
        self._cached_validation = None
        # Store references
        self._references = set()
        for op in self._operands:
            self._references |= op._references

    def __bool__(self):     # pragma: no python 2 cover
        """ Python 3 method to determine the outcome of "if expression". """
        return True

    def bracket(self, op=None):
        """
        Checks if the given operand (which should be an operand of this
        expression) needs brackets around it when writing a mathematical
        expression.

        For example, ``5 + 3`` will require a bracket when used in a
        multiplication (e.g. ``2 * (5 + 3)``), so calling ``bracket(5 + 3)`` on
        a multiplication will return ``True``.

        Alternatively, when used in a function the expression will not require
        brackets, as the function (e.g. ``sin()``) already provides them, so
        calling ``bracket(5 + 3)`` on a function will return False.
        """
        raise NotImplementedError

    def clone(self, subst=None, expand=False, retain=None):
        """
        Clones this expression.

        The optional argument ``subst`` can be used to pass a dictionary
        mapping expressions to a substitute. Any expression that finds itself
        listed as a key in the dictionary will return this replacement value
        instead.

        The argument ``expand`` can be set to True to expand all variables
        other than states. For example, if ``x = 5 + 3 * y`` and
        ``y = z + sqrt(2)`` and ``dot(z) = ...``, cloning x while expanding
        will yield ``x = 5 + 3 * (z + sqrt(2))``. When expanding, all constants
        are converted to numerical values. To maintain some of the constants,
        pass in a list of variables or variable names as ``retain``.

        Substitution takes precedence over expansion: A call such as
        ``e.clone(subst={x:y}, expand=True) will replace ``x`` by ``y`` but not
        expand any names appearing in ``y``.
        """
        raise NotImplementedError

    def code(self, component=None):
        """
        Returns this expression formatted in ``mmt`` syntax.

        When :class:`LhsExpressions <LhsExpression>` are encountered, their
        full qname is rendered, except in two cases: (1) if the variable's
        component matches the argument ``component`` or (2) if the variable is
        nested. Aliases are used in place of qnames if found in the given
        component.
        """
        b = StringIO()
        self._code(b, component)
        return b.getvalue()

    def _code(self, b, c):
        """
        Internal version of ``code()``, should write the generated code to the
        stringbuffer ``b``, from the context of component ``c``.
        """
        raise NotImplementedError

    def contains_type(self, kind):
        """
        Returns True if this expression tree contains an expression of the
        given type.
        """
        if isinstance(self, kind):
            return True
        for op in self:
            if op.contains_type(kind):
                return True
        return False

    def depends_on(self, lhs):
        """
        Returns True if this :class:`Expression` depends on the given
        :class:`LhsExpresion`.
        """
        return lhs in self._references

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        # Get polish is fast because it uses caching
        return self._polish() == other._polish()

    def eval(self, subst=None, precision=myokit.DOUBLE_PRECISION):
        """
        Evaluates this expression and returns the result. This operation will
        fail if the expression contains any
        :class:`Names <Name>` that do not resolve to
        numerical values.

        The optional argument ``subst`` can be used to pass a dictionary
        mapping :class:`LhsExpression` objects to expressions or numbers to
        substitute them with.

        For debugging purposes, the argument ``precision`` can be set to
        ``myokit.SINGLE_PRECISION`` to perform the evaluation with 32 bit
        floating point numbers.
        """
        # Check subst dict
        if subst:
            try:
                subst = dict(subst)
            except TypeError:
                raise ValueError('Argument `subst` must be dict or None.')
            for k, v in subst.items():
                if not isinstance(k, myokit.LhsExpression):
                    raise ValueError(
                        'All keys in `subst` must LhsExpression objects.')
                if not isinstance(v, myokit.Expression):
                    try:
                        v = float(v)
                    except ValueError:
                        raise ValueError(
                            'All values in `subst` must be Expression objects'
                            ' or numbers.')
                    subst[k] = myokit.Number(v)

        # Evaluate
        try:
            return self._eval(subst, precision)
        except EvalError as e:

            # It went wrong! Create a nice error message.
            out = [_expr_error_message(self, e)]

            # Show values of operands
            ops = [op for op in e.expr]
            if ops:
                out.append('With the following operands:')
                for i, op in enumerate(ops):
                    pre = '  (' + str(1 + i) + ') '
                    try:
                        out.append(pre + str(op._eval(subst, precision)))
                    except EvalError:
                        out.append(pre + 'another error')

            # Show variables included in expression
            refs = e.expr.references()
            if refs:
                out.append('And the following variables:')
                for ref in refs:
                    name = str(ref)

                    # Perform substitution, or get expression from lhs
                    if subst and ref in subst:
                        rhs = subst[ref]
                    else:
                        rhs = ref.rhs()

                    if isinstance(rhs, Number):
                        # Show numbers on same line
                        pre = '  ' + name + ' = '
                    else:
                        # Show expressions + results on next line
                        out.append('  ' + name + ' = ' + rhs.code())
                        pre = '  ' + ' ' * len(name) + ' = '

                    try:
                        out.append(pre + str(rhs._eval(subst, precision)))
                    except EvalError:
                        out.append(pre + 'another error')

            # Raise new exception with better message
            out = '\n'.join(out)
            raise myokit.NumericalError(out)

    def _eval(self, subst, precision):
        """
        Internal, error-handling free version of eval.
        """
        raise NotImplementedError

    def eval_unit(self, mode=myokit.UNIT_TOLERANT):
        """
        Evaluates the unit this expression should have, based on the units of
        its variables and literals.

        Incompatible units may result in a
        :class:`myokit.IncompatibleUnitError` being raised. The method for
        dealing with unspecified units can be set using the ``mode`` argument.

        Using ``myokit.UNIT_STRICT`` any unspecified unit will be treated as
        dimensionless. For example adding ``None + [kg]`` will be treated as
        ``[1] + [kg]`` which will raise an error. Similarly, ``None * [m]``
        will be taken to mean ``[1] * [m]`` which is valid, and ``None * None``
        will return ``[1]``. In strict mode, functions such as ``exp()``, which
        expect dimensionless input will raise an error if given a
        non-dimensionless operator.

        Using ``myokit.UNIT_TOLERANT`` unspecified units will try to be ignored
        where possible. For example, the expression ``None + [kg]`` will be
        treated as ``[kg] + [kg]``, while ``None * [m]`` will be read as
        ``[1] * [m]`` and ``None * None`` will return ``None``. Functions such
        as ``exp()`` will not raise an error, but simply return a dimensionless
        value.

        The method is intended to be used to check the units in a model, so
        every branch of an expression is evaluated, even if it won't affect the
        final result.
        """
        try:
            return self._eval_unit(mode)
        except EvalUnitError as e:
            raise myokit.IncompatibleUnitError(_expr_error_message(self, e))

    def _eval_unit(self, mode):
        """
        Internal version of eval_unit()
        """
        raise NotImplementedError

    def __float__(self):
        # Cast to float is required in Python 3: numpy float etc. are ok, but
        # this is deprecated.
        return float(self.eval())

    def __getitem__(self, key):
        return self._operands[key]

    def __hash__(self):
        if self._cached_hash is None:
            self._cached_hash = hash(self._polish())
        return self._cached_hash
        # Note for Python3:
        #   In Python3, anything that has an __eq__ stops inheriting this hash
        #   method!
        # From: https://docs.python.org/3.1/reference/datamodel.html
        # > If a class that overrides __eq__() needs to retain the
        #   implementation of __hash__() from a parent class, the interpreter
        #   must be told this explicitly by setting
        #   __hash__ = <ParentClass>.__hash__. Otherwise the inheritance of
        #   __hash__() will be blocked, just as if __hash__ had been explicitly
        #   set to None.

    def __int__(self):
        return int(self.eval())

    def is_conditional(self):
        """
        Returns True if and only if this expression's tree contains a
        conditional statement.
        """
        for e in self:
            if e.is_conditional():
                return True
        return False

    def is_constant(self):
        """
        Returns true if this expression contains no references or only
        references to variables with a constant value.
        """
        for ref in self._references:
            if not ref.is_constant():
                return False
        return True

    def is_literal(self):
        """
        Returns ``True`` if this expression doesn't contain any references.
        """
        return len(self._references) == 0

    def is_state_value(self):
        """
        Returns ``True`` if this expression is a :class:`Name` pointing to the
        current value of a state variable.
        """
        return False

    def __iter__(self):
        return iter(self._operands)

    def __len__(self):
        return len(self._operands)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __nonzero__(self):  # pragma: no python 3 cover
        """ Python 2 method to determine the outcome of "if expression". """
        return True

    def operator_rep(self):
        """
        Returns a representation of this expression's type. (For example '+' or
        '*')
        """
        return self._rep

    def _polish(self):
        """
        Returns a reverse-polish notation version of this expression's code,
        using Variable id's instead of Variable name's to create immutable,
        unambiguous expressions.
        """
        if self._cached_polish is None:
            b = StringIO()
            self._polishb(b)
            self._cached_polish = b.getvalue()
        return self._cached_polish

    def _polishb(self, b):
        """
        Recursive part of _polish(). Should write the generated code to the
        stringbuffer b.

        Because hash() and others use _polish(), this function should never
        use eval() or other advanced functions.
        """
        raise NotImplementedError

    def pyfunc(self, use_numpy=True):
        """
        Converts this expression to python and returns the new function's
        handle.

        By default, when converting mathematical functions such as ``log``, the
        version from ``numpy`` (i.e. ``numpy.log``) is used. To use the
        built-in ``math`` module instead, set ``use_numpy=False``.
        """
        # Get expression writer
        if use_numpy:
            w = myokit.numpy_writer()
        else:
            w = myokit.python_writer()

        # Create function text
        args = [w.ex(x) for x in self._references]
        c = 'def ex_pyfunc_generated(' + ','.join(args) + '):\n    return ' \
            + w.ex(self)

        # Create function
        local = {}
        if use_numpy:
            exec(c, {'numpy': numpy}, local)
        else:
            exec(c, {'math': math}, local)

        # Return
        return local['ex_pyfunc_generated']

    def pystr(self, use_numpy=False):
        """
        Returns a string representing this expression in python syntax.

        By default, built-in functions such as 'exp' are converted to the
        python version 'math.exp'. To use the numpy versions, set
        ``numpy=True``.
        """
        # Get expression writer
        if use_numpy:
            w = myokit.numpy_writer()
        else:
            w = myokit.python_writer()

        # Return string
        return w.ex(self)

    def references(self):
        """
        Returns a set containing all references to variables made in this
        expression.
        """
        return set(self._references)

    def __str__(self):
        return self.code()

    def tree_str(self):
        """
        Returns a string representing the parse tree corresponding to this
        expression.
        """
        b = StringIO()
        self._tree_str(b, 0)
        return b.getvalue()

    def _tree_str(self, b, n):
        raise NotImplementedError

    def validate(self):
        """
        Validates operands, checks cycles without following references. Will
        raise exceptions if errors are found.
        """
        return self._validate([])

    def _validate(self, trail):
        """
        The argument ``trail`` is used to check for cyclical refererences.
        """
        if self._cached_validation:
            return
        # Check for cyclical dependency
        if id(self) in trail:
            raise IntegrityError('Cyclical expression found', self._token)
        trail2 = trail + [id(self)]
        # It's okay to do this check with id's. Even if there are multiple
        # objects that are equal, if they're cyclical you'll get back round to
        # the same ones eventually. Doing this with the value requires hash()
        # which requires code() which may not be safe to use before the
        # expressions have been validated.
        for op in self:
            if not isinstance(op, Expression):
                raise IntegrityError(
                    'Expression operands must be other Expression objects.'
                    ' Found: ' + str(type(op)) + '.', self._token)
            op._validate(trail2)
        # Cache validation status
        self._cached_validation = True

    def walk(self, allowed_types=None):
        """
        Returns an iterator over this expression tree (depth-first). This is a
        slow operation. Do _not_ use in performance sensitive code!

        Example::

            5 + (2 * sqrt(x))

            1) Plus
            2) Number(5)
            3) Multiply
            4) Number(2)
            5) Sqrt
            6) Name(x)

        To return only expressions of certain types, pass in a sequence
        ``allowed_typess``, containing all types desired in the output.
        """
        if allowed_types is None:

            def walker(op):
                yield op
                for kid in op:
                    for x in walker(kid):
                        yield x
            return walker(self)

        else:

            if type(allowed_types) == type:
                allowed_types = set([allowed_types])
            else:
                allowed_types = set(allowed_types)

            def walker(op):
                if type(op) in allowed_types:
                    yield op
                for kid in op:
                    for x in walker(kid):
                        yield x
            return walker(self)


class Number(Expression):
    """
    Represents a number with an optional unit for use in Myokit expressions.
    All numbers used in Myokit expressions are floating point.

    >>> import myokit
    >>> x = myokit.Number(10)
    >>> print(x)
    10

    >>> x = myokit.Number(5.00, myokit.units.V)
    >>> print(x)
    5 [V]

    Arguments:

    ``value``
        A numerical value (something that can be converted to a ``float``).
        Number objects are immutable so no clone constructor is provided.
    ``unit``
        A unit to associate with this number. If no unit is specified the
        number's unit will be left undefined.

    *Extends:* :class:`Expression`
    """
    _rbp = LITERAL

    def __init__(self, value, unit=None):
        super(Number, self).__init__()
        if isinstance(value, Quantity):
            # Conversion from Quantity class
            if unit is not None:
                raise ValueError(
                    'Myokit Number created from a Quantity cannot specify an'
                    ' additional unit.')
            self._value = value.value()
            self._unit = value.unit()
        else:
            # Basic creation with number and unit
            self._value = float(value) if value else 0.0
            if unit is None or isinstance(unit, myokit.Unit):
                self._unit = unit
            elif isinstance(unit, basestring):
                self._unit = myokit.parse_unit(unit)
            else:
                raise ValueError(
                    'Unit in myokit.Number should be a myokit.Unit or None.')
        # Create nice string representation
        self._str = myokit.strfloat(self._value)
        if self._str[-2:] == '.0':
            # Turn 5.0 into 5
            self._str = self._str[:-2]
        elif self._str[-4:-1] == 'e-0':
            # Turn 1e-05 into 1e-5
            self._str = self._str[:-2] + self._str[-1]
        elif self._str[-4:-2] == 'e+':
            if self._str[-2:] == '00':
                # Turn 1e+00 into 1
                self._str = self._str[:-4]
            elif self._str[-2:-1] == '0':
                # Turn e+05 into e5
                self._str = self._str[:-3] + self._str[-1:]
            else:
                # Turn e+15 into e15
                self._str = self._str[:-3] + self._str[-2:]
        if self._unit and self._unit != dimensionless:
            self._str += ' ' + str(self._unit)

    def bracket(self, op=None):
        if op is not None:
            raise ValueError('Given operand is not in this expression.')
        return False

    def clone(self, subst=None, expand=False, retain=None):
        if subst and self in subst:
            return subst[self]
        return Number(self._value, self._unit)

    def _code(self, b, c):
        b.write(self._str)

    def convert(self, unit):
        """
        Returns a copy of this number in a different unit. If the two units are
        not compatible a :class:`myokit.IncompatibleUnitError` is raised.
        """
        return Number(Unit.convert(self._value, self._unit, unit), unit)

    def _eval(self, subst, precision):
        if precision == myokit.SINGLE_PRECISION:
            return numpy.float32(self._value)
        else:
            return self._value

    def _eval_unit(self, mode):
        if mode == myokit.UNIT_STRICT and self._unit is None:
            return myokit.units.dimensionless
        return self._unit

    def is_constant(self):
        return True

    def is_literal(self):
        return True

    def _polishb(self, b):
        b.write(self._str)

    def _tree_str(self, b, n):
        b.write(' ' * n + self._str + '\n')

    def unit(self):
        """
        Returns the unit associated with this number/quantity or ``None`` if no
        unit was specified.
        """
        return self._unit


class LhsExpression(Expression):
    """
    An expression referring to the left-hand side of an equation.

    Running :func:`eval() <Expression.eval>` on an `LhsExpression` returns the
    evaluation of the associated right-hand side. This may result in errors if
    no right-hand side is defined. In other words, this will only work if the
    expression is embedded in a variable's defining equation.

    *Abstract class, extends:* :class:`Expression`
    """
    def _eval(self, subst, precision):
        if subst and self in subst:
            return subst[self].eval()
        try:
            return self.rhs()._eval(subst, precision)
        except (ArithmeticError, ValueError) as e:  # pragma: no cover
            raise EvalError(self, subst, e)

    def is_constant(self):
        return self.var().is_constant()

    def is_derivative(self):
        return False

    def is_literal(self):
        return False

    def rhs(self):
        """
        Returns the rhs expression equal to this lhs expression.
        """
        raise NotImplementedError

    def var(self):
        """
        Returns the variable referenced by this `LhsExpression`. For
        :class:`Name` objects this will be equal to the left hand
        side of their defining equation, for derivatives this will be the
        variable they represent the the derivative of.
        """
        raise NotImplementedError


class Name(LhsExpression):
    """
    Represents a reference to a variable.

    *Extends:* :class:`LhsExpression`
    """
    _rbp = LITERAL
    __hash__ = LhsExpression.__hash__   # For Python3, when __eq__ is present

    def __init__(self, value):
        super(Name, self).__init__()
        if not isinstance(value, myokit.Variable):
            if not isinstance(value, basestring):
                raise ValueError(
                    'myokit.Name objects must have a value that is a'
                    ' myokit.Variable (or, when debugging, a string).')
        self._value = value
        self._references = set([self])

    def bracket(self, op=None):
        if op is not None:
            raise ValueError('Given operand is not in this expression.')
        return False

    def clone(self, subst=None, expand=False, retain=None):
        if subst and self in subst:
            return subst[self]
        if expand and isinstance(self._value, myokit.Variable):
            if not self._value.is_state():
                if (retain is None) or (
                        self not in retain
                        and self._value not in retain
                        and self._value.qname() not in retain
                ):
                    return self._value.rhs().clone(subst, expand, retain)
        return Name(self._value)

    def _code(self, b, c):
        if isinstance(self._value, basestring):
            # Allow an exception for strings (used in function templates and
            # debugging).
            b.write('str:' + str(self._value))
        else:
            if self._value.is_nested():
                b.write(self._value.name())
            else:
                if c:
                    try:
                        b.write(c.alias_for(self._value))
                        return
                    except KeyError:
                        pass
                b.write(self._value.qname(c))

    def _eval_unit(self, mode):

        # Try getting unit from variable, if linked
        if isinstance(self._value, myokit.Variable):
            return self._value.unit(mode)

            # Note: Don't get it from the variable's RHS!
            # If the variable unit isn't specified:
            #  1. In tolerant mode a None will propagate without errors
            #  2. In strict mode, it is dimensionless (and if the RHS thinks
            #     otherwise the RHS is wrong).
            # In addition, for e.g. derivatives this can lead to cycles.

        # Unlinked name or no unit found, return dimensionless or None
        if mode == myokit.UNIT_STRICT:
            return myokit.units.dimensionless
        return None

    def __eq__(self, other):
        if type(other) != Name:
            return False
        return self._value == other._value

    def is_state_value(self):
        return self._value.is_state()

    def _polishb(self, b):
        if isinstance(self._value, basestring):
            # Allow an exception for strings
            b.write('str:')
            b.write(self._value)
        else:
            # Use object id here to make immutable references. This is fine
            # since references should always be to variable objects, and
            # variables are unique this way (one Variable('x') doesn't equal
            # another Variable('x')).
            b.write('var:')
            b.write(str(id(self._value)))

    def __repr__(self):
        return '<Name(' + repr(self._value) + ')>'

    def rhs(self):
        if self._value.is_state():
            return Number(self._value.state_value())
        elif self._value.lhs() == self:
            return self._value.rhs()

    def _tree_str(self, b, n):
        b.write(' ' * n + str(self._value) + '\n')

    def _validate(self, trail):
        super(Name, self)._validate(trail)
        # Check value: String is allowed at construction for debugging, but
        # not here!
        if not isinstance(self._value, myokit.Variable):
            raise IntegrityError(
                'Name value "' + repr(self._value) + '" is not an instance of'
                ' class myokit.Variable', self._token)

    def var(self):
        return self._value


class Derivative(LhsExpression):
    """
    Represents a reference to the time-derivative of a variable.

    *Extends:* :class:`LhsExpression`
    """
    _rbp = FUNCTION_CALL
    _nargs = [1]    # Allows parsing as a function
    __hash__ = LhsExpression.__hash__   # For Python3, when __eq__ is present

    def __init__(self, op):
        super(Derivative, self).__init__((op,))
        if not isinstance(op, Name):
            raise IntegrityError(
                'The dot() operator can only be used on named variables.',
                self._token)
        self._op = op
        self._references = set([self])

    def bracket(self, op):
        if op != self._op:
            raise ValueError('Given operand is not in this expression.')
        return False

    def clone(self, subst=None, expand=False, retain=None):
        if subst and self in subst:
            return subst[self]
        return Derivative(self._op.clone(subst, expand, retain))

    def _code(self, b, c):
        b.write('dot(')
        self._op._code(b, c)
        b.write(')')

    def __eq__(self, other):
        if type(other) != Derivative:
            return False
        return self._op == other._op

    def _eval_unit(self, mode):
        # Get numerator (never None in strict mode)
        unit1 = self._op._eval_unit(mode)

        # Get denomenator
        unit2 = \
            myokit.units.dimensionless if mode == myokit.UNIT_STRICT else None
        if self._op._value is not None:
            model = self._op._value.model()
            if model is not None:
                unit2 = model.time_unit(mode)

        # Handle as division
        if unit2 is None:
            return unit1    # Can be None in tolerant mode!
        elif unit1 is None:
            return 1 / unit2
        return unit1 / unit2

    def is_derivative(self):
        return True

    def _polishb(self, b):
        b.write('dot ')
        self._op._polishb(b)

    def __repr__(self):
        return '<Derivative(' + repr(self._op) + ')>'

    def rhs(self):
        return self._op._value.rhs()

    def _tree_str(self, b, n):
        b.write(' ' * n + 'dot(' + str(self._op._value) + ')' + '\n')

    def var(self):
        return self._op._value

    def _validate(self, trail):
        super(Derivative, self)._validate(trail)
        # Check if value is the name of a state variable
        var = self._op.var()
        if not (isinstance(var, myokit.Variable) and var.is_state()):
            raise IntegrityError(
                'Derivatives can only be defined for state variables.',
                self._token)


class PrefixExpression(Expression):
    """
    Base class for prefix expressions: expressions with a single operand.

    *Abstract class, extends:* :class:`Expression`
    """
    _rbp = PREFIX
    _rep = None

    def __init__(self, op):
        super(PrefixExpression, self).__init__((op,))
        self._op = op

    def bracket(self, op):
        if op != self._op:
            raise ValueError('Given operand is not in this expression.')
        return (self._op._rbp > LITERAL) and (self._op._rbp < self._rbp)

    def clone(self, subst=None, expand=False, retain=None):
        if subst and self in subst:
            return subst[self]
        return type(self)(self._op.clone(subst, expand, retain))

    def _code(self, b, c):
        b.write(self._rep)
        brackets = self._op._rbp > LITERAL and self._op._rbp < self._rbp
        if brackets:
            b.write('(')
        self._op._code(b, c)
        if brackets:
            b.write(')')

    def _eval_unit(self, mode):
        return self._op._eval_unit(mode)

    def _tree_str(self, b, n):
        b.write(' ' * n + self._rep + '\n')
        self._op._tree_str(b, n + self._treeDent)


class PrefixPlus(PrefixExpression):
    """
    Prefixed plus. Indicates a positive number ``+op``.

    >>> from myokit import *
    >>> x = PrefixPlus(Number(10))
    >>> print(x.eval())
    10.0

    *Extends:* :class:`PrefixExpression`
    """
    _rep = '+'

    def _eval(self, subst, precision):
        try:
            return self._op._eval(subst, precision)
        except (ArithmeticError, ValueError) as e:  # pragma: no cover
            raise EvalError(self, subst, e)

    def _polishb(self, b):
        self._op._polishb(b)


class PrefixMinus(PrefixExpression):
    """
    Prefixed minus. Indicates a negative number ``-op``.

    >>> from myokit import *
    >>> x = PrefixMinus(Number(10))
    >>> print(x.eval())
    -10.0

    *Extends:* :class:`PrefixExpression`
    """
    _rep = '-'

    def _eval(self, subst, precision):
        try:
            return -self._op._eval(subst, precision)
        except (ArithmeticError, ValueError) as e:  # pragma: no cover
            raise EvalError(self, subst, e)

    def _polishb(self, b):
        b.write('~ ')
        self._op._polishb(b)


class InfixExpression(Expression):
    """
    Base class for for infix expressions: ``<left> operator <right>``.

    The order of the operands may matter, so that ``<left> operator <right>``
    is not always equal to ``<right> operator <left>``.

    *Abstract class, extends:* :class:`Expression`
    """
    _rep = None      # Operator representation (+, *, et)

    def __init__(self, left, right):
        super(InfixExpression, self).__init__((left, right))
        self._op1 = left
        self._op2 = right

    def bracket(self, op):
        if op == self._op1:
            return (op._rbp > LITERAL and (op._rbp < self._rbp))
        elif op == self._op2:
            return (op._rbp > LITERAL and (op._rbp <= self._rbp))
        raise ValueError('Given operand is not in this expression.')

    def clone(self, subst=None, expand=False, retain=None):
        if subst and self in subst:
            return subst[self]
        return type(self)(
            self._op1.clone(subst, expand, retain),
            self._op2.clone(subst, expand, retain))

    def _code(self, b, c):
        # Test bracket locally, avoid function call
        if self._op1._rbp > LITERAL and self._op1._rbp < self._rbp:
            b.write('(')
            self._op1._code(b, c)
            b.write(')')
        else:
            self._op1._code(b, c)
        b.write(' ')
        b.write(self._rep)
        b.write(' ')
        #if self.bracket(self._op2):
        if self._op2._rbp > LITERAL and self._op2._rbp <= self._rbp:
            b.write('(')
            self._op2._code(b, c)
            b.write(')')
        else:
            self._op2._code(b, c)

    def _polishb(self, b):
        b.write(self._rep)
        b.write(' ')
        self._op1._polishb(b)
        b.write(' ')
        self._op2._polishb(b)

    def _tree_str(self, b, n):
        b.write(' ' * n + self._rep + '\n')
        self._op1._tree_str(b, n + self._treeDent)
        self._op2._tree_str(b, n + self._treeDent)


class Plus(InfixExpression):
    """
    Represents the addition of two operands: ``left + right``.

    >>> from myokit import *
    >>> x = parse_expression('5 + 2')
    >>> print(x.eval())
    7.0

    *Extends:* :class:`InfixExpression`
    """
    _rbp = SUM
    _rep = '+'
    _description = 'Addition'

    def _eval(self, subst, precision):
        try:
            return (
                self._op1._eval(subst, precision)
                + self._op2._eval(subst, precision))
        except (ArithmeticError, ValueError) as e:  # pragma: no cover
            raise EvalError(self, subst, e)

    def _eval_unit(self, mode):
        unit1 = self._op1._eval_unit(mode)
        unit2 = self._op2._eval_unit(mode)

        if unit1 == unit2:
            return unit1
        if unit1 is None:
            return unit2
        if unit2 is None:
            return unit1

        raise EvalUnitError(
            self, 'Addition requires equal units, got '
            + str(unit1) + ' and ' + str(unit2) + '.')


class Minus(InfixExpression):
    """
    Represents subtraction: ``left - right``.

    >>> from myokit import *
    >>> x = parse_expression('5 - 2')
    >>> print(x.eval())
    3.0

    *Extends:* :class:`InfixExpression`
    """
    _rbp = SUM
    _rep = '-'
    _description = 'Subtraction'

    def _eval(self, subst, precision):
        try:
            return (
                self._op1._eval(subst, precision)
                - self._op2._eval(subst, precision))
        except (ArithmeticError, ValueError) as e:  # pragma: no cover
            raise EvalError(self, subst, e)

    def _eval_unit(self, mode):
        unit1 = self._op1._eval_unit(mode)
        unit2 = self._op2._eval_unit(mode)

        if unit1 == unit2:
            return unit1
        if unit1 is None:
            return unit2
        if unit2 is None:
            return unit1

        raise EvalUnitError(
            self, 'Subtraction requires equal units, got ' + str(unit1)
            + ' and ' + str(unit2) + '.')


class Multiply(InfixExpression):
    """
    Represents multiplication: ``left * right``.

    >>> from myokit import *
    >>> x = parse_expression('5 * 2')
    >>> print(x.eval())
    10.0

    *Extends:* :class:`InfixExpression`
    """
    _rbp = PRODUCT
    _rep = '*'

    def _eval(self, subst, precision):
        try:
            return (
                self._op1._eval(subst, precision)
                * self._op2._eval(subst, precision))
        except (ArithmeticError, ValueError) as e:  # pragma: no cover
            raise EvalError(self, subst, e)

    def _eval_unit(self, mode):
        unit1 = self._op1._eval_unit(mode)
        unit2 = self._op2._eval_unit(mode)

        if unit1 is None:
            return unit2
        if unit2 is None:
            return unit1

        return unit1 * unit2


class Divide(InfixExpression):
    """
    Represents division: ``left / right``.

    >>> from myokit import *
    >>> x = parse_expression('5 / 2')
    >>> print(x.eval())
    2.5

    *Extends:* :class:`InfixExpression`
    """
    _rbp = PRODUCT
    _rep = '/'

    def _eval(self, subst, precision):
        try:
            b = self._op2._eval(subst, precision)
            if b == 0:
                raise ZeroDivisionError()
            return self._op1._eval(subst, precision) / b
        except (ArithmeticError, ValueError) as e:  # pragma: no cover
            raise EvalError(self, subst, e)

    def _eval_unit(self, mode):
        unit1 = self._op1._eval_unit(mode)
        unit2 = self._op2._eval_unit(mode)

        if unit2 is None:
            return unit1    # None propagation in tolerant mode
        elif unit1 is None:
            return 1 / unit2

        return unit1 / unit2


class Quotient(InfixExpression):
    """
    Represents the quotient (integer division) of a division ``left // right``.

    >>> import myokit
    >>> x = myokit.parse_expression('7 // 3')
    >>> print(x.eval())
    2.0

    Note that, for negative numbers Myokit follows the convention of Python
    (and some other languages, but not e.g. C) of rounding towards negative
    infinity, rather than towards zero. Thus:

    >>> print(myokit.parse_expression('-7 // 3').eval())
    -3.0

    Similarly:

    >>> print(myokit.parse_expression('5 // -3').eval())
    -2.0

    See: https://python-history.blogspot.co.uk/2010/08/
    And: https://en.wikipedia.org/wiki/Modulo_operation

    *Extends:* :class:`InfixExpression`
    """
    _rbp = PRODUCT
    _rep = '//'

    def _eval(self, subst, precision):
        try:
            return (
                self._op1._eval(subst, precision)
                // self._op2._eval(subst, precision))
        except (ArithmeticError, ValueError) as e:  # pragma: no cover
            raise EvalError(self, subst, e)

    def _eval_unit(self, mode):
        unit1 = self._op1._eval_unit(mode)
        unit2 = self._op2._eval_unit(mode)

        if unit2 is None:
            return unit1    # None propagation in tolerant mode
        elif unit1 is None:
            return 1 / unit2

        return unit1 / unit2


class Remainder(InfixExpression):
    """
    Represents the remainder of a division (the "modulo"), expressed in ``mmt``
    syntax as ``left % right``.

    >>> import myokit
    >>> x = myokit.parse_expression('7 % 3')
    >>> print(x.eval())
    1.0

    Note that, for negative numbers Myokit follows the convention of Python
    that the quotient is rounded to negative infinity. Thus:

    >>> print(myokit.parse_expression('-7 // 3').eval())
    -3.0

    and therefore:

    >>> print(myokit.parse_expression('-7 % 3').eval())
    2.0

    Similarly:

    >>> print(myokit.parse_expression('5 // -3').eval())
    -2.0

    so that:

    >>> print(myokit.parse_expression('5 % -3').eval())
    -1.0

    *Extends:* :class:`InfixExpression`
    """
    _rbp = PRODUCT
    _rep = '%'

    def _eval(self, subst, precision):
        try:
            return (
                self._op1._eval(subst, precision)
                % self._op2._eval(subst, precision))
        except (ArithmeticError, ValueError) as e:  # pragma: no cover
            raise EvalError(self, subst, e)

    def _eval_unit(self, mode):
        # 14 pizzas / 5 kids = 2 pizzas / kid + 4 pizzas
        unit1 = self._op1._eval_unit(mode)
        self._op2._eval_unit(mode)  # Also check op2!
        return unit1


class Power(InfixExpression):
    """
    Represents exponentiation: ``left ^ right``.

    >>> import myokit
    >>> x = myokit.parse_expression('5 ^ 2')
    >>> print(x.eval())
    25.0

    *Extends:* :class:`InfixExpression`
    """
    _rbp = POWER
    _rep = '^'

    def _eval(self, subst, precision):
        try:
            return (
                self._op1._eval(subst, precision)
                ** self._op2._eval(subst, precision))
        except (ArithmeticError, ValueError) as e:  # pragma: no cover
            raise EvalError(self, subst, e)

    def _eval_unit(self, mode):
        unit1 = self._op1._eval_unit(mode)
        unit2 = self._op2._eval_unit(mode)

        # In strict mode, check 2nd unit is dimensionless
        if unit2 != myokit.units.dimensionless and mode == myokit.UNIT_STRICT:
            raise EvalUnitError(
                self, 'Exponent in Power must be dimensionless.')

        if unit1 is None:
            return None
        return unit1 ** self._op2.eval()


class Function(Expression):
    """
    Base class for built-in functions.

    Functions have a ``name``, which must be set to a human readable function
    name (usually just the function's ``.mmt`` equivalent) and a list of
    integers called ``_nargs``. Each entry in ``_nargs`` specifies a number of
    arguments for which the function is implemented. For example :class:`Sin`
    has ``_nargs=[1]`` while :class:`Log` has ``_nargs=[1,2]``, showing that
    ``Log`` can be called with either ``1`` or ``2`` arguments.

    If errors occur when creating a function, an IntegrityError may be thrown.

    *Abstract class, extends:* :class:`Expression`
    """
    _nargs = [1]
    _fname = None
    _rbp = FUNCTION_CALL

    def __init__(self, *ops):
        super(Function, self).__init__(ops)
        if self._nargs is not None:
            if not len(ops) in self._nargs:
                raise IntegrityError(
                    'Function (' + str(self._fname) + ') created with wrong'
                    ' number of arguments (' + str(len(ops)) + ', expecting '
                    + ' or '.join([str(x) for x in self._nargs]) + ').',
                    self._token)

    def bracket(self, op=None):
        if op not in self._operands:
            raise ValueError('Given operand is not in this expression.')
        return False

    def clone(self, subst=None, expand=False, retain=None):
        if subst and self in subst:
            return subst[self]
        return type(self)(
            *[x.clone(subst, expand, retain) for x in self._operands])

    def _code(self, b, c):
        b.write(self._fname)
        b.write('(')
        if len(self._operands) > 0:
            self._operands[0]._code(b, c)
            for i in range(1, len(self._operands)):
                b.write(', ')
                self._operands[i]._code(b, c)
        b.write(')')

    def _polishb(self, b):
        # Function name | Number of operands | operands
        # This is sufficient for what we're doing here :)
        b.write(self._fname)
        b.write(' ')
        b.write(str(len(self._operands)))
        for op in self._operands:
            b.write(' ')
            op._polishb(b)

    def _tree_str(self, b, n):
        b.write(' ' * n + self._fname + '\n')
        for op in self._operands:
            op._tree_str(b, n + self._treeDent)


class UnaryDimensionlessFunction(Function):
    """
    Function with a single operand that has dimensionless input and output.

    *Abstract class, extends:* :class:`Function`
    """
    def _eval_unit(self, mode):
        unit = self._operands[0]._eval_unit(mode)

        # Propagate None in tolerant mode
        if unit is None:
            return None

        # Check unit in strict mode
        if mode == myokit.UNIT_STRICT and unit != myokit.units.dimensionless:
            raise EvalUnitError(
                self, 'Function ' + self._fname + '() requires a'
                ' dimensionless operand.')

        # Unary dimensionless functions are always dimensionless
        return myokit.units.dimensionless


class UnsupportedFunction(Function):
    """
    Unsupported functions in other formats than myokit can be imported as an
    ``UnsupportedFunction``. This preserves the meaning of the original
    document. UnsupportedFunction objects should never occur in valid models.
    """
    def __init__(self, name, ops):
        self._nargs = [len(ops)]
        self._fname = 'UNSUPPORTED::' + str(name).strip()
        super(UnsupportedFunction, self).__init__(*ops)

    def _validate(self, trail):
        raise IntegrityError('UnsupportedFunction in expression.', self._token)


class Sqrt(Function):
    """
    Represents the square root ``sqrt(x)``.

    >>> import myokit
    >>> x = myokit.parse_expression('sqrt(25)')
    >>> print(x.eval())
    5.0

    *Extends:* :class:`Function`
    """
    _fname = 'sqrt'

    def _eval(self, subst, precision):
        try:
            return numpy.sqrt(self._operands[0]._eval(subst, precision))
        except (ArithmeticError, ValueError) as e:  # pragma: no cover
            raise EvalError(self, subst, e)

    def _eval_unit(self, mode):
        unit = self._operands[0]._eval_unit(mode)
        if unit is None:
            return None
        try:
            return unit ** 0.5
        except ValueError as e:
            raise EvalUnitError(self, e)


class Sin(UnaryDimensionlessFunction):
    """
    Represents the sine function ``sin(x)``.

    >>> from myokit import *
    >>> x = parse_expression('sin(0)')
    >>> print(round(x.eval(), 1))
    0.0
    >>> x = Sin(Number(3.1415 / 2.0))
    >>> print(round(x.eval(), 1))
    1.0

    *Extends:* :class:`UnaryDimensionlessFunction`
    """
    _fname = 'sin'

    def _eval(self, subst, precision):
        try:
            return numpy.sin(self._operands[0]._eval(subst, precision))
        except (ArithmeticError, ValueError) as e:  # pragma: no cover
            raise EvalError(self, subst, e)


class Cos(UnaryDimensionlessFunction):
    """
    Represents the cosine function ``cos(x)``.

    >>> from myokit import *
    >>> x = Cos(Number(0))
    >>> print(round(x.eval(), 1))
    1.0
    >>> x = Cos(Number(3.1415 / 2.0))
    >>> print(round(x.eval(), 1))
    0.0

    *Extends:* :class:`UnaryDimensionlessFunction`
    """
    _fname = 'cos'

    def _eval(self, subst, precision):
        try:
            return numpy.cos(self._operands[0]._eval(subst, precision))
        except (ArithmeticError, ValueError) as e:  # pragma: no cover
            raise EvalError(self, subst, e)


class Tan(UnaryDimensionlessFunction):
    """
    Represents the tangent function ``tan(x)``.

    >>> from myokit import *
    >>> x = Tan(Number(3.1415 / 4.0))
    >>> print(round(x.eval(), 1))
    1.0

    *Extends:* :class:`UnaryDimensionlessFunction`
    """
    _fname = 'tan'

    def _eval(self, subst, precision):
        try:
            return numpy.tan(self._operands[0]._eval(subst, precision))
        except (ArithmeticError, ValueError) as e:  # pragma: no cover
            raise EvalError(self, subst, e)


class ASin(UnaryDimensionlessFunction):
    """
    Represents the inverse sine function ``asin(x)``.

    >>> from myokit import *
    >>> x = ASin(Sin(Number(1)))
    >>> print(round(x.eval(), 1))
    1.0

    *Extends:* :class:`UnaryDimensionlessFunction`
    """
    _fname = 'asin'

    def _eval(self, subst, precision):
        try:
            return numpy.arcsin(self._operands[0]._eval(subst, precision))
        except (ArithmeticError, ValueError) as e:  # pragma: no cover
            raise EvalError(self, subst, e)


class ACos(UnaryDimensionlessFunction):
    """
    Represents the inverse cosine ``acos(x)``.

    >>> from myokit import *
    >>> x = ACos(Cos(Number(3)))
    >>> print(round(x.eval(), 1))
    3.0

    *Extends:* :class:`UnaryDimensionlessFunction`
    """
    _fname = 'acos'

    def _eval(self, subst, precision):
        try:
            return numpy.arccos(self._operands[0]._eval(subst, precision))
        except (ArithmeticError, ValueError) as e:  # pragma: no cover
            raise EvalError(self, subst, e)


class ATan(UnaryDimensionlessFunction):
    """
    Represents the inverse tangent function ``atan(x)``.

    >>> from myokit import *
    >>> x = ATan(Tan(Number(1)))
    >>> print(round(x.eval(), 1))
    1.0

    If two arguments are given they are interpreted as the coordinates of a
    point (x, y) and the function returns this point's angle with the
    (positive) x-axis. In this case, the returned value will be in the range
    (-pi, pi].

    *Extends:* :class:`UnaryDimensionlessFunction`
    """
    _fname = 'atan'

    def _eval(self, subst, precision):
        try:
            return numpy.arctan(self._operands[0]._eval(subst, precision))
        except (ArithmeticError, ValueError) as e:  # pragma: no cover
            raise EvalError(self, subst, e)


class Exp(UnaryDimensionlessFunction):
    """
    Represents a power of *e*. Written ``exp(x)`` in ``.mmt`` syntax.

    >>> from myokit import *
    >>> x = Exp(Number(1))
    >>> print(round(x.eval(), 4))
    2.7183

    *Extends:* :class:`UnaryDimensionlessFunction`
    """
    _fname = 'exp'

    def _eval(self, subst, precision):
        try:
            return numpy.exp(self._operands[0]._eval(subst, precision))
        except (ArithmeticError, ValueError) as e:  # pragma: no cover
            raise EvalError(self, subst, e)


class Log(Function):
    """
    With one argument ``log(x)`` represents the natural logarithm.
    With two arguments ``log(x, k)`` is taken to be the base ``k`` logarithm of
    ``x``.

    >>> from myokit import *
    >>> x = Log(Number(10))
    >>> print(round(x.eval(), 4))
    2.3026
    >>> x = Log(Exp(Number(10)))
    >>> print(round(x.eval(), 1))
    10.0
    >>> x = Log(Number(256), Number(2))
    >>> print(round(x.eval(), 1))
    8.0

    *Extends:* :class:`Function`
    """
    _fname = 'log'
    _nargs = [1, 2]

    def _eval(self, subst, precision):
        try:
            if len(self._operands) == 1:
                return numpy.log(self._operands[0]._eval(subst, precision))
            return (
                numpy.log(self._operands[0]._eval(subst, precision)) /
                numpy.log(self._operands[1]._eval(subst, precision)))
        except (ArithmeticError, ValueError) as e:  # pragma: no cover
            raise EvalError(self, subst, e)

    def _eval_unit(self, mode):
        if len(self._operands) == 1:

            # One operand
            unit = self._operands[0]._eval_unit(mode)
            if unit is None:
                return None
            if mode == myokit.UNIT_STRICT:
                if unit != myokit.units.dimensionless:
                    raise EvalUnitError(
                        self, 'Log() requires a dimensionless operand.')
            return myokit.units.dimensionless

        else:

            # Two operands
            unit1 = self._operands[0]._eval_unit(mode)
            unit2 = self._operands[1]._eval_unit(mode)

            # Propagate None in tolerant mode
            if unit1 is None and unit2 is None:
                return None

            # Check units in strict mode
            if mode == myokit.UNIT_STRICT:
                if not unit1 == unit2 == myokit.units.dimensionless:
                    raise EvalUnitError(
                        self, 'Log() requires dimensionless operands.')

            return myokit.units.dimensionless


class Log10(UnaryDimensionlessFunction):
    """
    Represents the base-10 logarithm ``log10(x)``.

    >>> from myokit import *
    >>> x = Log10(Number(100))
    >>> print(round(x.eval(), 1))
    2.0

    *Extends:* :class:`UnaryDimensionlessFunction`
    """
    _fname = 'log10'

    def _eval(self, subst, precision):
        try:
            return numpy.log10(self._operands[0]._eval(subst, precision))
        except (ArithmeticError, ValueError) as e:  # pragma: no cover
            raise EvalError(self, subst, e)


class Floor(Function):
    """
    Represents a rounding towards minus infinity ``floor(x)``.

    >>> from myokit import *
    >>> x = Floor(Number(5.2))
    >>> print(x.eval())
    5.0
    >>> x = Floor(Number(-5.2))
    >>> print(x.eval())
    -6.0

    *Extends:* :class:`Function`
    """
    _fname = 'floor'

    def _eval(self, subst, precision):
        try:
            return numpy.floor(self._operands[0]._eval(subst, precision))
        except (ArithmeticError, ValueError) as e:  # pragma: no cover
            raise EvalError(self, subst, e)

    def _eval_unit(self, mode):
        return self._operands[0]._eval_unit(mode)


class Ceil(Function):
    """
    Represents a rounding towards positve infinity ``ceil(x)``.

    >>> from myokit import *
    >>> x = Ceil(Number(5.2))
    >>> print(x.eval())
    6.0
    >>> x = Ceil(Number(-5.2))
    >>> print(x.eval())
    -5.0

    *Extends:* :class:`Function`
    """
    _fname = 'ceil'

    def _eval(self, subst, precision):
        try:
            return numpy.ceil(self._operands[0]._eval(subst, precision))
        except (ArithmeticError, ValueError) as e:  # pragma: no cover
            raise EvalError(self, subst, e)

    def _eval_unit(self, mode):
        return self._operands[0]._eval_unit(mode)


class Abs(Function):
    """
    Returns the absolute value of a number ``abs(x)``.

    >>> from myokit import *
    >>> x = parse_expression('abs(5)')
    >>> print(x.eval())
    5.0
    >>> x = parse_expression('abs(-5)')
    >>> print(x.eval())
    5.0

    *Extends:* :class:`Function`
    """
    _fname = 'abs'

    def _eval(self, subst, precision):
        try:
            return numpy.abs(self._operands[0]._eval(subst, precision))
        except (ArithmeticError, ValueError) as e:  # pragma: no cover
            raise EvalError(self, subst, e)

    def _eval_unit(self, mode):
        return self._operands[0]._eval_unit(mode)


class If(Function):
    """
    Allows conditional functions to be defined using an if-then-else structure.

    The first argument to an ``If`` function must be a condition, followed
    directly by an expression to use to calculate the function's return value
    if this condition is ``True``. The third and final argument specifies the
    expression's value if the condition is ``False``.

    A simple example in ``.mmt`` syntax::

        x = if(V < 10, 5 * V + 100, 6 * V)

    *Extends:* :class:`Function`
    """
    _nargs = [3]
    _fname = 'if'

    def __init__(self, i, t, e):
        super(If, self).__init__(i, t, e)
        self._i = i     # if
        self._t = t     # then
        self._e = e     # else

    def condition(self):
        """
        Returns this if-function's condition.
        """
        return self._i

    def _eval(self, subst, precision):
        if self._i._eval(subst, precision):
            return self._t._eval(subst, precision)
        return self._e._eval(subst, precision)

    def _eval_unit(self, mode):

        # Check the condition and all options
        self._i._eval_unit(mode)
        unit2 = self._t._eval_unit(mode)
        unit3 = self._e._eval_unit(mode)

        # Check if the options have the same unit (or None in tolerant mode)
        if unit2 == unit3:
            return unit2

        # Allow 1 None in tolerant mode
        if unit2 is None:
            return unit3
        elif unit3 is None:
            return unit2

        # Mismatching units
        raise EvalUnitError(
            self, 'Units of `then` and `else` part of an `if`'
            ' must match. Got ' + str(unit2) + ' and ' + str(unit3) + '.')

    def is_conditional(self):
        return True

    def piecewise(self):
        """
        Returns an equivalent ``Piecewise`` object.
        """
        return Piecewise(self._i, self._t, self._e)

    def value(self, which):
        """
        Returns the expression used when this if's condition is ``True`` when
        called with ``which=True``. Otherwise return the expression used when
        this if's condition is ``False``.
        """
        return self._t if which else self._e


class Piecewise(Function):
    """
    Allows piecewise functions to be defined.

    The first argument to a ``Piecewise`` function must be a condition,
    followed directly by an expression to use to calculate the function's
    return value if this condition is true.

    Any number of condition-expression pairs can be added. If multiple
    conditions evaluate as true, only the first one will be used to set the
    return value.

    The final argument should be a default expression to use if none of the
    conditions evaluate to True. This means the ``piecewise()`` function can
    have any odd number of arguments greater than 2.

    A simple example in ``mmt`` syntax::

        x = piecewise(
            V < 10, 5 * V + 100
            V < 20, 6 * V,
            7 * V)

    This will return ``5 * V + 100`` for any value smaller than 10, ``6 * V``
    for any value greater or equal to 10 but smaller than 20, and ``7 * V`` for
    any values greather than or equal to 20.

    *Extends:* :class:`Function`
    """
    _nargs = None
    _fname = 'piecewise'

    def __init__(self, *ops):
        super(Piecewise, self).__init__(*ops)

        # Check number of arguments
        n = len(self._operands)
        if n % 2 == 0:
            raise IntegrityError(
                'Piecewise function must have odd number of arguments:'
                ' ([condition, value]+, else_value).', self._token)
        if n < 3:
            raise IntegrityError(
                'Piecewise function must have 3 or more arguments.',
                self._token)

        # Check arguments
        m = n // 2
        self._i = [0] * m           # Conditions
        self._e = [0] * (m + 1)     # Expressions
        oper = iter(ops)
        for i in range(0, m):
            self._i[i] = next(oper)
            self._e[i] = next(oper)
        self._e[m] = next(oper)

    def conditions(self):
        """
        Returns an iterator over the conditions used by this Piecewise.
        """
        return iter(self._i)

    def _eval(self, subst, precision):
        for k, cond in enumerate(self._i):
            if cond._eval(subst, precision):
                return self._e[k]._eval(subst, precision)
        return self._e[-1]._eval(subst, precision)

    def _eval_unit(self, mode):

        # Check the conditions and all options
        units = [x._eval_unit(mode) for x in self._i]   # And discard :)
        units = [x._eval_unit(mode) for x in self._e]

        # Check if the options have the same unit
        units = set(units)
        # Nones are allowed in tolerant mode, can't occur in strict mode
        if None in units:
            units.remove(None)
            if len(units) == 0:
                return None
        if len(units) == 1:
            return units.pop()
        raise EvalUnitError(
            self, 'All branches of a piecewise() must have the same unit.')

    def is_conditional(self):
        return True

    def pieces(self):
        """
        Returns an iterator over the pieces in this Piecewise.
        """
        return iter(self._e)


class Condition(object):
    """
    *Abstract class*

    Interface for conditional expressions that can be evaluated to True or
    False. Doesn't add any methods but simply indicates that this is a
    condition.
    """
    pass


class PrefixCondition(Condition, PrefixExpression):
    """
    Interface for prefix conditions.

    *Abstract class, extends:* :class:`Condition`, :class:`PrefixExpression`
    """


class Not(PrefixCondition):
    """
    Negates a condition. Written as ``not x``.

    >>> from myokit import *
    >>> x = parse_expression('1 == 1')
    >>> print(x.eval())
    True
    >>> y = Not(x)
    >>> print(y.eval())
    False
    >>> x = parse_expression('(2 == 2) and not (1 > 2)')
    >>> print(x.eval())
    True

    *Extends:* :class:`PrefixCondition`
    """
    _rep = 'not'

    def _code(self, b, c):
        b.write('not ')
        brackets = self._op._rbp > LITERAL and self._op._rbp < self._rbp
        if brackets:
            b.write('(')
        self._op._code(b, c)
        if brackets:
            b.write(')')

    def _eval(self, subst, precision):
        try:
            return not(self._op._eval(subst, precision))
        except (ArithmeticError, ValueError) as e:  # pragma: no cover
            raise EvalError(self, subst, e)

    def _eval_unit(self, mode):
        unit = self._op._eval_unit(mode)
        if unit not in (None, myokit.units.dimensionless):
            raise EvalUnitError(
                self, 'Operator `not` expects a dimensionless operand.')
        return unit

    def _polishb(self, b):
        b.write('not ')
        self._op._polishb(b)


class InfixCondition(Condition, InfixExpression):
    """
    Base class for infix expressions.

    *Abstract class, extends:* :class:`Condition`, :class:`InfixExpression`
    """
    _rbp = CONDITIONAL


class BinaryComparison(InfixCondition):
    """
    Base class for infix comparisons of two entities.

    *Abstract class, extends:* :class:`InfixCondition`
    """
    def _eval_unit(self, mode):
        unit1 = self._op1._eval_unit(mode)
        unit2 = self._op2._eval_unit(mode)

        # Equal (including both None) is always ok
        if unit1 == unit2:
            return None if unit1 is None else myokit.units.dimensionless

        # In tolerant mode, a single None is OK
        if unit1 is None or unit2 is None:
            return myokit.units.dimensionless

        # Otherwise must match
        raise EvalUnitError(
            self, 'Condition ' + self._rep + ' requires equal units on both'
            ' sides, got ' + str(unit1) + ' and ' + str(unit2) + '.')


class Equal(BinaryComparison):
    """
    Represents an equality check ``x == y``.

    >>> from myokit import *
    >>> print(parse_expression('1 == 0').eval())
    False
    >>> print(parse_expression('1 == 1').eval())
    True

    *Extends:* :class:`InfixCondition`
    """
    _rep = '=='

    def _eval(self, subst, precision):
        try:
            return (
                self._op1._eval(subst, precision)
                == self._op2._eval(subst, precision))
        except (ArithmeticError, ValueError) as e:  # pragma: no cover
            raise EvalError(self, subst, e)


class NotEqual(BinaryComparison):
    """
    Represents an inequality check ``x != y``.

    >>> from myokit import *
    >>> print(parse_expression('1 != 0').eval())
    True
    >>> print(parse_expression('1 != 1').eval())
    False

    *Extends:* :class:`InfixCondition`
    """
    _rep = '!='

    def _eval(self, subst, precision):
        try:
            return (
                self._op1._eval(subst, precision)
                != self._op2._eval(subst, precision))
        except (ArithmeticError, ValueError) as e:  # pragma: no cover
            raise EvalError(self, subst, e)


class More(BinaryComparison):
    """
    Represents an is-more-than check ``x > y``.

    >>> from myokit import *
    >>> print(parse_expression('5 > 2').eval())
    True

    *Extends:* :class:`InfixCondition`
    """
    _rep = '>'

    def _eval(self, subst, precision):
        try:
            return (
                self._op1._eval(subst, precision)
                > self._op2._eval(subst, precision))
        except (ArithmeticError, ValueError) as e:  # pragma: no cover
            raise EvalError(self, subst, e)


class Less(BinaryComparison):
    """
    Represents an is-less-than check ``x < y``.

    >>> from myokit import *
    >>> print(parse_expression('5 < 2').eval())
    False

    *Extends:* :class:`InfixCondition`
    """
    _rep = '<'

    def _eval(self, subst, precision):
        try:
            return (
                self._op1._eval(subst, precision)
                < self._op2._eval(subst, precision))
        except (ArithmeticError, ValueError) as e:  # pragma: no cover
            raise EvalError(self, subst, e)


class MoreEqual(BinaryComparison):
    """
    Represents an is-more-than-or-equal check ``x > y``.

    >>> from myokit import *
    >>> print(parse_expression('2 >= 2').eval())
    True

    *Extends:* :class:`InfixCondition`
    """
    _rep = '>='

    def _eval(self, subst, precision):
        try:
            return (
                self._op1._eval(subst, precision)
                >= self._op2._eval(subst, precision))
        except (ArithmeticError, ValueError) as e:  # pragma: no cover
            raise EvalError(self, subst, e)


class LessEqual(BinaryComparison):
    """
    Represents an is-less-than-or-equal check ``x <= y``.

    >>> from myokit import *
    >>> print(parse_expression('2 <= 2').eval())
    True

    *Extends:* :class:`InfixCondition`
    """
    _rep = '<='

    def _eval(self, subst, precision):
        try:
            return (
                self._op1._eval(subst, precision)
                <= self._op2._eval(subst, precision))
        except (ArithmeticError, ValueError) as e:  # pragma: no cover
            raise EvalError(self, subst, e)


class And(InfixCondition):
    """
    True if two conditions are true: ``x and y``.

    >>> from myokit import *
    >>> print(parse_expression('1 == 1 and 2 == 4').eval())
    False
    >>> print(parse_expression('1 == 1 and 4 == 4').eval())
    True

    *Extends:* :class:`InfixCondition`
    """
    _rbp = CONDITION_AND
    _rep = 'and'

    def _eval(self, subst, precision):
        try:
            return (
                self._op1._eval(subst, precision)
                and self._op2._eval(subst, precision))
        except (ArithmeticError, ValueError) as e:  # pragma: no cover
            raise EvalError(self, subst, e)

    def _eval_unit(self, mode):
        unit1 = self._op1._eval_unit(mode)
        unit2 = self._op2._eval_unit(mode)

        # Propagate both None in tolerant mode
        if unit1 is None and unit2 is None:
            return None

        # Ideal: both dimensionless
        unit1 = myokit.units.dimensionless if unit1 is None else unit1
        unit2 = myokit.units.dimensionless if unit2 is None else unit2
        if unit1 == unit2 == myokit.units.dimensionless:
            return unit1

        raise EvalUnitError(
            self, 'Operator `and` expects dimensionless operands.')


class Or(InfixCondition):
    """
    True if at least one of two conditions is true: ``x or y``.

    >>> from myokit import *
    >>> print(parse_expression('1 == 1 or 2 == 4').eval())
    True

    *Extends:* :class:`InfixCondition`
    """
    _rbp = CONDITION_AND
    _rep = 'or'

    def _eval(self, subst, precision):
        try:
            return (
                self._op1._eval(subst, precision)
                or self._op2._eval(subst, precision))
        except (ArithmeticError, ValueError) as e:  # pragma: no cover
            raise EvalError(self, subst, e)

    def _eval_unit(self, mode):
        unit1 = self._op1._eval_unit(mode)
        unit2 = self._op2._eval_unit(mode)

        # Propagate both None in tolerant mode
        if unit1 is None and unit2 is None:
            return None

        # Ideal: both dimensionless
        unit1 = myokit.units.dimensionless if unit1 is None else unit1
        unit2 = myokit.units.dimensionless if unit2 is None else unit2
        if unit1 == unit2 == myokit.units.dimensionless:
            return unit1

        raise EvalUnitError(
            self, 'Operator `or` expects dimensionless operands.')


class EvalError(Exception):
    """
    Used internally when an error is encountered during an ``eval()``
    operation. Is replaced by a ``myokit.NumericalError`` which is then sent
    to the caller.

    Attributes:

    ``expr``
        The expression that generated the error
    ``subst``
        Any substitutions given to the eval function
    ``err``
        The exception that triggered the error or an error message

    *Extends:* ``Exception``
    """
    def __init__(self, expr, subst, err):
        self.expr = expr
        self.err = err


class EvalUnitError(Exception):
    """
    Used internally when an error is encountered during an ``eval_unit()``
    operation. Is replaced by a :class:`myokit.IncompatibleUnitError` which is
    then sent to the caller.

    ``expr``
        The expression that generated the error
    ``err``
        The exception that triggered the error or an error message

    *Extends:* ``Exception``
    """
    def __init__(self, expr, err):
        self.expr = expr
        self.err = err


def _expr_error_message(owner, e):
    """
    Takes an ``EvalError`` or an ``EvalUnitError`` and traces the origins of
    the error in the expression. Returns an error message.

    Arguments:

    ``owner``
        The expression on which eval() or eval_unit() was called.
    ``e``
        The exception that occurred. The method expects the error to have the
        property ``expr`` containing an expression object that triggered the
        error and a property ``err`` that can be converted to a string
        explaining the error.

    """
    def path(root, target, trail=None):
        # Find all name expressions leading up to e.expr
        if trail is None:
            trail = []
        if root == target:
            return trail
        if isinstance(root, Name):
            return path(root.rhs(), target, trail + [root])
        else:
            for child in root:
                r = path(child, target, trail)
                if r is not None:
                    return r
            return None

    # Show there was an error
    out = []
    out.append(str(e.err))
    out.append('Encountered when evaluating')
    par_str = '  ' + owner.code()
    err_str = e.expr.code()

    # Attempt to locate Name containing error
    # Append list of Names up to that one
    out.append(par_str)
    trail = path(owner, e.expr)
    if trail:
        out.append('Error located at:')
        for i, var in enumerate(trail):
            out.append('  ' * (1 + i) + str(var))
        par_str = str(trail[-1]) + ' = ' + trail[-1].rhs().code()
        out.append(par_str)

    # Indicate location of error
    start = par_str.find(err_str)
    if start >= 0:
        out.append(' ' * start + '~' * len(err_str))

    # Raise new error with added info
    return '\n'.join(out)


class Unit(object):
    """
    Defines a unit.

    Each unit consists of

      * A list of seven integers: these are the exponents for the basic SI
        units: ``[g, m, s, A, K, cd, mol]``. Gram is used instead of the SI
        defined kilogram to create a more coherent syntax.
      * A multiplier. This includes both quantifiers (such as milli, kilo, Mega
        etc) and conversion factors (for example 1inch = 2.54cm). Multipliers
        are specified in powers of 10.

    There are two ways to create a unit:

        >>> # 1. By explicitly setting the exponent and multiplier
        >>> import myokit
        >>> km_per_s = myokit.Unit([0, 1, -1, 0, 0, 0, 0], 3)
        >>> print(km_per_s) # Here
        [m/s (1000)]

        >>> # 2. Creating a blank unit
        >>> dimless = myokit.Unit()
        >>> print(dimless)
        [1]

    Units can be manipulated using ``*`` and ``/`` and ``**``. A clear
    representation can be obtained using str().

        >>> s = myokit.Unit([0, 0, 1, 0, 0, 0, 0])
        >>> km = myokit.Unit([0, 1, 0, 0, 0, 0, 0], 3)
        >>> m_per_s = (km / 1000) / s
        >>> print(m_per_s)
        [m/s]

    Units that require offsets (aka celsius and fahrenheit) are not supported.
    """
    # Mapping of names to unit objects
    # These units will all be recognized by the parser
    _units = {}

    # Mapping of unit objects to preferred names
    _preferred_representations = {}

    # Set of recognized unit names that may be quantified with si quantifiers
    _quantifiable = set()

    # Mapping of SI exponent values to their symbols
    _si_exponents = {
        -24: 'y',   # yocto
        -21: 'z',   # zepto
        -18: 'a',   # atto
        -15: 'f',   # femto
        -12: 'p',   # pico
        -9: 'n',    # nano
        -6: 'u',    # micro
        -3: 'm',    # milli
        -2: 'c',    # centi
        -1: 'd',    # deci
        # 1: 'da',  # Deca
        2: 'h',
        3: 'k',
        6: 'M',
        9: 'G',
        12: 'T',
        15: 'P',
        18: 'E',
        21: 'Z',
        24: 'Y',
    }

    # Mapping of SI quantifier symbols to their values
    _si_quantifiers = dict((v, k) for k, v in _si_exponents.items())

    def __init__(self, exponents=None, multiplier=0):
        if exponents is None:
            self._x = [0] * 7
            self._m = float(multiplier)
        elif type(exponents) == Unit:
            # Clone
            self._x = list(exponents._x)
            self._m = exponents._m
        else:
            if not len(exponents) == 7:
                raise ValueError(
                    'Unit must have exactly seven exponents set:'
                    ' [g, m, s, A, K, cd, mol].')
            self._x = [int(x) for x in exponents]
            self._m = float(multiplier)
        self._hash = None
        self._repr = None

    @staticmethod
    def can_convert(unit1, unit2):
        """
        Returns true if the given units differ only by a multiplication. For
        example, ``[m/s]`` can be converted to ``[miles/hour]`` but not to
        ``[kg]``.
        """
        return unit1._x == unit2._x

    @staticmethod
    def conversion_factor(unit1, unit2):
        """
        Returns the number ``c`` such that ``1 [unit1] = c [unit2]``.

            >>> import myokit
            >>> myokit.Unit.conversion_factor('m', 'km')
            0.001

        """
        if not isinstance(unit1, myokit.Unit):
            if unit1 is None:
                unit1 = myokit.units.dimensionless
            else:
                try:
                    unit1 = myokit.parse_unit(unit1)
                except Exception:
                    raise myokit.IncompatibleUnitError(
                        'Cannot convert given object ' + repr(unit1)
                        + ' to unit.')

        if not isinstance(unit2, myokit.Unit):
            if unit2 is None:
                unit2 = myokit.units.dimensionless
            else:
                try:
                    unit2 = myokit.parse_unit(unit2)
                except Exception:
                    raise myokit.IncompatibleUnitError(
                        'Cannot convert given object ' + repr(unit2)
                        + ' to unit.')

        if unit1._x != unit2._x:
            raise myokit.IncompatibleUnitError(
                'Cannot convert from ' + str(unit1) + ' to ' + str(unit2)
                + '.')

        return 1 if unit1._m == unit2._m else 10**(unit1._m - unit2._m)

    @staticmethod
    def convert(amount, unit1, unit2):
        """
        Converts a number ``amount`` in units ``unit1`` to a new amount in
        units ``unit2``.

            >>> import myokit
            >>> myokit.Unit.convert(3000, 'm', 'km')
            3.0

        """
        return amount * Unit.conversion_factor(unit1, unit2)

    def __div__(self, other):
        """
        Evaluates ``self / other``
        """
        if not isinstance(other, Unit):
            return Unit(list(self._x), self._m - math.log10(float(other)))
        return Unit(
            [a - b for a, b in zip(self._x, other._x)],
            self._m - other._m)

    def __eq__(self, other):
        if not isinstance(other, Unit):
            return False
        return self._x == other._x and self._m == other._m

    def exponents(self):
        """
        Returns the list of this unit's exponents.
        """
        return list(self._x)

    def __float__(self):
        """
        Attempts to convert this unit to a float.
        """
        for x in self._x:
            if x != 0:
                raise TypeError(
                    'Unable to convert unit ' + str(self) + ' to float.')
        return self.multiplier()

    def __hash__(self):
        """
        Creates a hash for this unit
        """
        if not self._hash:
            self._hash = hash(
                ','.join([str(x) for x in self._x]) + 'e' + str(self._m))
        return self._hash

    @staticmethod
    def list_exponents():
        """
        Returns a list of seven units, corresponding to the exponents used when
        defining a new Unit.
        """
        e = []
        for i in range(0, 7):
            u = Unit()
            u._x[i] = 1
            e.append(u)
        return e

    def multiplier(self):
        """
        Returns this unit's multiplier (as an ordinary number, not as its base
        10 logarithm).
        """
        return 10 ** self._m

    def __mul__(self, other):
        """
        Evaluates ``self * other``
        """
        if not isinstance(other, Unit):
            return Unit(list(self._x), self._m + math.log10(float(other)))
        return Unit(
            [a + b for a, b in zip(self._x, other._x)],
            self._m + other._m)

    def __ne__(self, other):
        return not self.__eq__(other)

    @staticmethod
    def parse_simple(name):
        """
        Converts a single unit name (+ optional quantifier) to a Unit object.

        For example ``m`` and ``km`` will be accepted, while ``m/s`` or ``m^2``
        will not.

        >>> from myokit import Unit
        >>> print(Unit.parse_simple('km'))
        [km]
        >>> N = Unit.parse_simple('N')
        >>> print(repr(N))
        [g*m/s^2 (1000)]
        >>> print(str(N))
        [N]
        >>> print(Unit.parse_simple(''))       # Dimensionless
        [1]
        >>> print(Unit.parse_simple('mm'))     # millimeters
        [mm]
        >>> print(Unit.parse_simple('mM'))     # milli-mole per liter
        [mM]
        """
        name = name.strip()
        if name in ['1', '']:
            # Return empty unit
            return Unit()

        try:
            # Return clone of named unit
            return Unit(Unit._units[name])

        except KeyError:
            p1 = name[0]
            p2 = name[1:]
            if p2 in Unit._quantifiable:
                # Quantified unit
                try:
                    q = Unit._si_quantifiers[p1]
                except KeyError:

                    if p1 not in Unit._si_quantifiers:
                        raise KeyError(
                            'Unknown quantifier: "' + str(p1) + '".')
                    else:   # pragma: no cover
                        raise Exception(
                            'Unit "' + str(p1) + '" listed as quantifiable'
                            ' does not appear in unit list.')

                # Return new unit with updated exponent
                u = Unit._units[p2]
                return Unit(u._x, u._m + q)

            elif p1 in Unit._si_quantifiers and p2 in Unit._units:
                # Attempt to quantify non-quantifiable unit
                raise KeyError(
                    'Unit "' + str(p2) + '" cannot have quantifier "' + str(p1)
                    + '".')

            else:
                # Just plain wrong
                raise KeyError('Unknown unit: "' + str(name) + '".')

    def __pow__(self, f):
        """
        Evaluates ``self ^ other``
        """
        f = float(f)
        e = [f * x for x in self._x]
        for x in e:
            if abs(float(x) - int(x)) > 1e-15:
                raise ValueError(
                    'Unit exponentiation (' + repr(self) + ') ^ '
                    + str(f) + ' failed: would result in non-integer'
                    + ' exponents, which is not supported.')
        return Unit([int(x) for x in e], self._m * f)

    def __rdiv__(self, other):  # pragma: no cover    rtruediv used instead
        """
        Evaluates ``other / self``, where other is not a unit
        """
        return self.__rtruediv__(self, other)

    @staticmethod
    def register(name, unit, quantifiable=False, output=False):
        """
        Registers a unit name with the Unit class. Registered units will be
        recognised by the parse() method.

        Arguments:

        ``name``
            The unit name. A variable will be created using this name.
        ``unit``
            A valid unit object
        ``quantifiable``
            ``True`` if this unit should be registered with the unit class as a
            quantifiable unit. Typically this should only be done for the
            unquantified symbol notation of SI or SI derived units. For example
            m, g, Hz, N but not meter, kg, hertz or forthnight.
        ``output``
            ``True`` if this units name should be used to display this unit in.
            This should be set for all common units (m, kg, nm, Hz) but not for
            more obscure units (furlong, parsec). Having ``output`` set to
            ``False`` will cause one-way behaviour: Myokit will recognise the
            unit name but never use it in output.
            Setting this to ``True`` will also register the given name as a
            preferred representation format.

        """
        if not isinstance(name, basestring):
            raise TypeError('Given name must be a string.')
        if not isinstance(unit, Unit):
            raise TypeError('Given unit must be myokit.Unit')
        Unit._units[name] = unit
        if quantifiable:
            # Overwrite existing entries without warning
            Unit._quantifiable.add(name)
        if output:
            # Overwrite existing entries without warning
            Unit._preferred_representations[unit] = name

    @staticmethod
    def register_preferred_representation(rep, unit):
        """
        Registers a preferred representation for the given unit without
        registering it as a new type. This method can be used to register
        common representations such as "umol/L" and "km/h".

        Arguments:

        ``rep``
            A string, containing the preferred name for this unit. This should
            be something that Myokit can parse.
        ``unit``
            The unit to register a notation for.

        Existing entries are overwritten without warning.
        """
        # Overwrite existing entries without warning
        Unit._preferred_representations[unit] = rep

    def __repr__(self):
        """
        Returns this unit formatted in the base SI units.
        """
        if not self._repr:
            # SI unit names
            si = ['g', 'm', 's', 'A', 'K', 'cd', 'mol']
            # Get unit parts
            pos = []
            neg = []
            for k, x in enumerate(self._x):
                if x != 0:
                    y = si[k]
                    xabs = abs(x)
                    if xabs > 1:
                        y += '^' + str(xabs)
                    if x > 0:
                        pos.append(y)
                    else:
                        neg.append(y)
            u = '*'.join(pos) if pos else '1'
            for x in neg:
                u += '/' + str(x)
            # Add conversion factor
            if self._m != 0:
                m = 10**self._m
                if abs(m - int(m)) < 1e-15:
                    m = int(m)
                u += ' (' + str(m) + ')'
            self._repr = '[' + u + ']'
        return self._repr

    def __rmul__(self, other):
        """
        Evaluates ``other * self``, where other is not a Unit
        """
        return Unit(list(self._x), self._m + math.log10(other))

    def __rtruediv__(self, other):
        """
        Evaluates ``other / self``, where other is not a unit when future
        division is active.
        """
        return Unit([-a for a in self._x], math.log10(other) - self._m)

    def __str__(self):
        try:
            return '[' + Unit._preferred_representations[self] + ']'
        except KeyError:
            try:
                # Find representation without multiplier, add multiplier and
                # store as preferred representation.
                # "Without multiplier" here means times 1000^kilo_exponent,
                # because kilos are defined with a multiplier of 1000
                m = 3 * self._x[0]
                u = Unit(list(self._x), m)
                rep = Unit._preferred_representations[u]
                m = 10**(self._m - m)
                if abs(m - int(m)) < 1e-15:
                    m = int(m)
                rep = '[' + rep + ' (' + str(m) + ')]'
                Unit._preferred_representations[self] = rep[1:-1]
                return rep
            except KeyError:
                # Get plain representation, store as preferred
                rep = self.__repr__()
                Unit._preferred_representations[self] = rep[1:-1]
                return rep

    def __truediv__(self, other):
        """
        Evaluates self / other if future division is active.
        """
        # Only truediv is supported, so methods are equal
        return self.__div__(other)


# Dimensionless unit, used to compare against
dimensionless = Unit()


# Quantities with units


class Quantity(object):
    """
    Represents a quantity with a :class:`unit <myokit.Unit>`. Can be used to
    perform unit-safe arithmetic with Myokit.

    Example::

        >>> from myokit import Quantity as Q
        >>> a = Q('10 [pA]')
        >>> b = Q('5 [mV]')
        >>> c = a / b
        >>> print(c)
        2 [uS]

        >>> from myokit import Number as N
        >>> d = myokit.Number(4)
        >>> print(d.unit())
        None
        >>> e = myokit.Quantity(d)
        >>> print(e.unit())
        [1]

    Arguments:

    ``value``
        Either a numerical value (something that can be converted to ``float``)
        or a string representation of a number in ``mmt`` syntax such as ``4``
        or ``2 [mV]``. Quantities are immutable so no clone constructor is
        provided.
        If a :class:`myokit.Expression` is provided its value and unit will be
        converted. In this case, the unit argument should be ``None``. Myokit
        expressions with an undefined unit will be treated as dimensionless.
    ``unit``
        An optional unit. Only used if the given ``value`` did not specify a
        unit.  If no unit is given the quantity will be dimensionless.

    Quantities support basic arithmetic, provided they have compatible units.
    Quantity arithmetic uses the following rules

    1. Quantities with any units can be multiplied or divided by each other
    2. Quantities with exactly equal units can be added and subtracted.
    3. Quantities with units that can be converted to each other (such as mV
       and V) can  **not** be added or subtracted, as the output unit would be
       undefined.
    4. Quantities with the same value and exactly the same unit are equal.
    5. Quantities that would be equal after conversion are **not** seen as
       equal.

    Examples::

        >>> a = Q('10 [mV]')
        >>> b = Q('0.01 [V]')
        >>> print(a == b)
        False
        >>> print(a.convert('V') == b)
        True

    """
    def __init__(self, value, unit=None):

        if isinstance(value, myokit.Expression):
            # Convert myokit.Expression
            if unit is not None:
                raise ValueError(
                    'Cannot specify a unit when creating a'
                    ' myokit.Quantity from a myokit.Number.')
            self._value = value.eval()
            unit = value.unit()
            self._unit = unit if unit is not None else dimensionless

        else:
            # Convert other types
            self._unit = None
            try:
                # Convert value to float
                self._value = float(value)

            except (ValueError, TypeError):

                # Try parsing string
                try:
                    self._value = str(value)
                    parts = value.split('[', 1)
                except Exception:
                    raise ValueError(
                        'Value of type ' + str(type(value))
                        + ' could not be converted to myokit.Quantity.')

                # Very simple number-with-unit parsing
                try:
                    self._value = float(parts[0])
                except ValueError:
                    raise ValueError(
                        'Failed to parse string "' + str(value)
                        + '" as myokit.Quantity.')
                self._unit = myokit.parse_unit(parts[1].strip()[:-1])

            # No unit set yet? Then check unit argument
            if self._unit is None:
                if unit is None:
                    self._unit = dimensionless
                elif isinstance(unit, myokit.Unit):
                    self._unit = unit
                else:
                    self._unit = myokit.parse_unit(unit)
            elif unit is not None:
                raise ValueError('Two units specified for myokit.Quantity.')

        # Create string representation
        self._str = str(self._value) + ' ' + str(self._unit)

    def convert(self, unit):
        """
        Returns a copy of this :class:`Quantity`, converted to another
        :class:`myokit.Unit`.
        """
        return Quantity(Unit.convert(self._value, self._unit, unit), unit)

    def __add__(self, other):
        if not isinstance(other, Quantity):
            other = Quantity(other)
        if self._unit != other._unit:
            raise myokit.IncompatibleUnitError(
                'Cannot add quantities with units ' + str(self._unit)
                + ' and ' + str(other._unit) + '.')
        return Quantity(self._value + other._value, self._unit)

    def cast(self, unit):
        """
        Returns a new Quantity with this quantity's value and a different,
        possibly incompatible, unit.

        Example:

            >>> from myokit import Quantity as Q
            >>> a = Q('10 [A/F]')
            >>> b = a.cast('uA/cm^2')
            >>> print(str(b))
            10.0 [uA/cm^2]

        """
        if not isinstance(unit, myokit.Unit):
            unit = myokit.parse_unit(unit)
        return Quantity(self._value, unit)

    def __div__(self, other):
        if not isinstance(other, Quantity):
            other = Quantity(other)
        return Quantity(self._value / other._value, self._unit / other._unit)

    def __eq__(self, other):
        if not isinstance(other, Quantity):
            return False
        return self._value == other._value and self._unit == other._unit

    def __float__(self):
        return self._value

    def __hash__(self):
        return self._str

    def __mul__(self, other):
        if not isinstance(other, Quantity):
            other = Quantity(other)
        return Quantity(self._value * other._value, self._unit * other._unit)

    def __radd__(self, other):
        return self + other

    def __rdiv__(self, other):  # pragma: no cover    rtruediv used instead
        return Quanity(other) / self

    def __rmul__(self, other):
        return self * other

    def __rsub__(self, other):
        return Quantity(other) - self

    def __str__(self):
        return self._str

    def __sub__(self, other):
        if not isinstance(other, Quantity):
            other = Quantity(other)
        if self._unit != other._unit:
            raise myokit.IncompatibleUnitError(
                'Cannot subtract quantities with units ' + str(self._unit)
                + ' and ' + str(other._unit) + '.')
        return Quantity(self._value - other._value, self._unit)

    def __truediv__(self, other):
        # Only truediv is supported, so behaviour is identical to div
        return self.__div__(other)

    def unit(self):
        """
        Returns this Quantity's unit.
        """
        return self._unit

    def value(self):
        """
        Returns this Quantity's unitless value.
        """
        return self._value
