#
# Myokit symbolic expression classes. Defines different expressions, equations
# and the unit system.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
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

        # Store references
        self._references = set()
        for op in self._operands:
            self._references |= op._references

        # Contains partial derivatives or initial values?
        self._has_partials = False
        self._has_initials = False
        for op in self._operands:
            if op._has_partials:
                self._has_partials = True
            if op._has_initials:
                self._has_initials = True

        # Cached results:
        # Since expressions are immutable, the results of many methods can be
        # cached. These could be evaluated initially, but it's more efficient
        # to way until a first request.
        self._cached_hash = None
        self._cached_polish = None
        self._cached_validation = None
        self._cached_unit_tolerant = None
        self._cached_unit_strict = None

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

        When :class:`Name` objects are encountered, the fullly qualified name
        of the :class:`myokit.Variable` that they refer to is rendered, with
        the following exceptions:

        - if the variable's component matches the argument ``component`` or the
          variable is nested, then the local variable name is used
        - if the given ``component`` has an alias for the variable, this alias
          is used.
        """
        # Note: Because variable and component names can change, the output of
        # code can not be cached (for non-literal expressions).
        b = StringIO()
        self._code(b, component)
        return b.getvalue()

    def _code(self, b, c):
        """
        Internal version of ``code()``, should write the generated code to the
        stringbuffer ``b``, from the context of component ``c``.
        """
        raise NotImplementedError

    def __contains__(self, key):
        return key in self._operands

    def contains_type(self, kind):
        """
        Returns True if this expression tree contains an expression of the
        given type.
        """
        if isinstance(self, kind):
            return True
        if kind == PartialDerivative:
            return self._has_partials
        if kind == InitialValue:
            return self._has_initials
        for op in self:
            if op.contains_type(kind):
                return True
        return False

    def depends_on(self, lhs, deep=False):
        """
        Returns ``True`` if this :class:`Expression` depends on the given
        :class:`LhsExpresion`.

        With ``deep=False`` (default), only dependencies appearing directly in
        the expression are checked. With ``deep=True`` the method also checks
        the right-hand side equation defined in the model for any
        :class:`Name` or :class:`Derivative` it encounters.
        """
        # Shallow check
        if not deep:
            return lhs in self._references

        # Determine if this variable has a (deep) dependency on the given lhs
        done = set()
        if isinstance(self, myokit.LhsExpression):
            done.add(self)
        todo = set(self._references)
        while todo:
            ref = todo.pop()
            done.add(ref)
            if ref == lhs:
                return True
            elif ref._has_partials or ref._has_initials:
                # Partial derivatives and initial values have no rhs
                continue
            elif not ref._proper:
                # Values that are not variables count as independent
                continue

            var = ref.var()
            if ref.is_state_value() or var.is_bound():
                # State values and bound variables have no rhs
                continue
            else:
                todo.update(var.rhs()._references - done)
        return False

    def depends_on_state(self, deep=False):
        """
        Returns ``True`` if this :class:`Expression` depends on one or more
        state variables.

        With ``deep=False`` (default), only dependencies appearing directly in
        the expression are checked. With ``deep=True`` the method also checks
        the right-hand side equation defined in the model for any
        :class:`Name` or :class:`Derivative` it encounters.
        """
        # Shallow check
        if not deep:
            for lhs in self._references:
                if lhs.is_state_value():
                    return True
            return False

        # Determine if this variable has a (deep) dependency on a state
        todo = set(self._references)
        done = set()
        if isinstance(self, myokit.LhsExpression):
            done.add(self)
        while todo:
            ref = todo.pop()
            done.add(ref)
            if ref.is_state_value():
                return True
            elif ref._has_partials or ref._has_initials:
                # Partial derivatives and initial values have no rhs
                continue
            elif not ref._proper:
                # Values that are not variables count as independent
                continue
            var = ref.var()
            if not var.is_bound():
                todo.update(var.rhs()._references - done)
        return False

    def diff(self, lhs, independent_states=True):
        """
        Returns an expression representing the partial derivative of this
        expression with respect to the expression ``lhs``.

        The argument ``lhs`` must be a :class:`Name` or a
        :class:`InitialValue`, taking derivatives with respect to
        a class:`Derivative` or :class:`PartialDerivative` is not supported.

        **Expressions involving variables**

        Partial derivatives are determined recursively. If, at any point in
        this recursion, a :class:`Name` or :class:`Derivative` is encountered,
        this is handled in the following way:

        - The partial derivative of any :class:`Name` with respect to an
          identical ``Name`` is 1 (without units / dimensionless).
        - The partial derivative of a :class:`Name` referencing a state
          variable is zero if ``independent_states=True``, but will otherwise
          be represented as a :class:`PartialDerivative`.
        - The partial derivative of a :class:`Derivative` or of a :class:`Name`
          referencing a non-state variable, will both be determined based on
          the corresponding right-hand side expression. If this references the
          ``lhs``, then a ``PartialDerivative`` will be returned. If it does
          not reference the ``lhs`` and ``independent_states=True``, then zero
          will be returned. If it does not reference the ``lhs``, but
          ``independent_states=False`` and one or more states are referenced,
          then a :class:`PartialDerivative` will be returned.
        - The partial derivative of a :class:`Name` referencing a bound
          variable is zero.

        **Simplification**

        Some effort is made to eliminate expressions that evaluate to zero, but
        no further simplification is performed. Multiplications by 1 are
        preserved as these can provide valuable unit information.

        **Conditional expressions**

        When calculating derivatives, the following simplifying assumptions are
        made with respect to conditional expressions:

        - When evaluating conditional expressions (:class:`If` and
          :class:`Piecewise`), the discontinuities at the condition boundaries
          are ignored. Instead, the method simply returns a similar conditional
          expression with the original operands replaced by their derivatives,
          e.g. ``if(condition, a, b)`` becomes ``if(condition, a', b')``.

        **Discontinuous functions**

        Similarly, some functions are discontinuous so that their derivatives
        are undefined at certain points, but this method returns the
        right-derivative for those points. In particular:

        - The true derivative of ``floor(x)`` is zero when ``x`` is not an
          integer and undefined if it is, but this method always returns zero.
        - Similarly, the true derivative of ``ceil(x)`` is undefined when ``x``
          is an integer, but this method always returns zero.
        - The true derivative of an integer division ``a // b`` with respect to
          either ``a`` or ``b`` is zero when ``a`` is not an integer multiple
          of ``b``, and otherwise undefined; but this method always returns
          zero.
        - The true derivative of the remainder operation
          ``a(x) % b(x) = a - b * floor(a / b)`` is
          ``da/dx - db/dx * floor(a/b) - b * d/dx floor(a/b)``, but (as above)
          this method assumes the derivative of the floor function is zero, and
          so will always return ``da/dx - db/dx * floor(a/b)``.
        - The true derivative of ``abs(f(x))`` is f'(x) for ``x > 0``, -f'(x)
          for ``x < 0``, and undefined for ``x == 0``, but this method will
          return ``f'(x)`` for ``x >= 0`` and ``-f'(x)``s for ``x < 0``.

        **Non-integer powers**

        Since ``a(x)^b(x)`` is undefined for non-integer ``b(x)`` when
        `a(x) < 0``, the derivative of ``a(x)^b(x)`` is only defined if
        ``a(x) >= 0`` or ``b'(x) = 0``. No errors or warnings are given if the
        derivative is undefined, until the equations are evaluated (note that
        at this point evaluation of ``a(x)^b(x)`` will also fail).

        """
        # Check LHS
        if not isinstance(lhs, (Name, InitialValue)):
            raise ValueError(
                'Partial derivatives can only be taken with respect to a'
                ' myokit.Name or myokit.InitialValue.')

        # Get derivative or None for 0
        derivative = self._diff(lhs, bool(independent_states))

        # Result zero? Then ensure it has the right unit
        if derivative is None:
            derivative = Number(0, self._diff_unit(lhs))

        return derivative

    def _diff(self, lhs, idstates):
        """
        Internal version of ``diff()``.

        Assumes lhs is a Name; and will return None if this expression does not
        depend on ``lhs``.
        """
        raise NotImplementedError

    def _diff_unit(self, lhs):
        """
        Returns the unit that the derivative of this expression w.r.t. the
        given ``lhs`` _should_ be in.

        This is used by both :meth:`diff()` and several implementations of
        :meth:`_diff()`.
        """
        try:
            unit1 = self.eval_unit(myokit.UNIT_TOLERANT)
        except myokit.IncompatibleUnitError as e:
            unit1 = None
        unit2 = lhs.var().unit()

        if unit1 is None and unit2 is None:
            return None
        if unit1 is None:
            return 1 / unit2
        if unit2 is None:
            return unit1
        return unit1 / unit2

    def __eq__(self, other):
        # Equality checking method, used by all expressions.
        if self is other:
            return True
        elif type(self) != type(other):
            return False
        else:
            # Compare cached polish expression (which uses ids)
            # Note that the polish representation uses object ids instead of
            # qnames
            return self._polish() == other._polish()

    def eval(self, subst=None, precision=myokit.DOUBLE_PRECISION):
        """
        Evaluates this expression and returns the result.

        The optional argument ``subst`` can be used to pass a dictionary
        mapping :class:`LhsExpression` objects to expressions or numbers to
        substitute them with.

        For debugging purposes, the argument ``precision`` can be set to
        ``myokit.SINGLE_PRECISION`` to perform the evaluation with 32 bit
        floating point numbers.

        Note: This operation will fail if the expression contains :class:`Name`
        objects with a value other than an :class:`Expression` or (an object
        that can be cast to) a float.
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

        In strict mode, this method will always either return a
        :class:`myokit.Unit` or raise an :class:`myokit.IncompatibleUnitError`.
        In tolerant mode, ``None`` will be returned if the units are unknown.
        """
        # Get cached unit or error
        if mode == myokit.UNIT_STRICT:
            result = self._cached_unit_strict
        else:
            result = self._cached_unit_tolerant

        # Evaluate and cache
        if result is None:
            try:
                result = self._eval_unit(mode)
            except EvalUnitError as e:
                result = myokit.IncompatibleUnitError(
                    _expr_error_message(self, e),
                    e.expr._token
                )

            if mode == myokit.UNIT_STRICT:
                self._unit_strict = result
            else:
                self._unit_tolerant = result

        # Raise error or return
        if isinstance(result, myokit.IncompatibleUnitError):
            raise result
        return result

    def _eval_unit(self, mode):
        """ Internal version of eval_unit(). """
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

    def is_derivative(self, var=None):
        """
        Returns ``True`` only if this is a time-derivative, i.e. a
        :class:`myokit.Derivative` instance (and references the variable
        ``var``, if given).
        """
        return False

    def is_literal(self):
        """
        Returns ``True`` if this expression doesn't contain any references.
        """
        return len(self._references) == 0

    def is_name(self, var=None):
        """
        Returns ``True`` only if this expression is a :class:`myokit.Name`
        (and references the variable ``var``, if given).
        """
        return False

    def is_number(self, value=None):
        """
        Returns ``True`` only if this expression is a :class:`myokit.Number`
        (and has the value ``value``, if given).
        """
        return False

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

        Note that id's are immutable _during the Variable's lifetime_. Since a
        Name object stores a reference to the Variable, this means the
        variable id is immutable in the expression's lifetime.
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
            myokit._exec(c, {'numpy': numpy}, local)
        else:
            myokit._exec(c, {'math': math}, local)

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

    def __reduce__(self):
        """ Called when attempting to pickle an expression. """
        raise NotImplementedError(
            'Individual myokit Expressions can not be pickled. Please try e.g.'
            ' pickling a full model, or pickling the output of'
            ' `Expression.code()` and following unpickling with a call to'
            ' `myokit.parse_expression(unpickled_code, context=a_model)` to'
            ' recreate the Expression.')

    def references(self):
        """
        Returns a set containing all references to variables made in this
        expression.
        """
        return set(self._references)

    def __repr__(self):
        return 'myokit.Expression[' + self.code() + ']'

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
        if isinstance(value, myokit.Quantity):
            # Conversion from Quantity class
            if unit is not None:
                raise ValueError(
                    'myokit.Number created from a myokit.Quantity cannot'
                    ' specify an additional unit.')
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
        self._str = myokit.float.str(self._value)
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
        if self._unit and self._unit != myokit.units.dimensionless:
            self._str += ' ' + str(self._unit)

    def bracket(self, op=None):
        """See :meth:`Expression.bracket()`."""
        if op is not None:
            raise ValueError('Given operand is not used in this expression.')
        return False

    def clone(self, subst=None, expand=False, retain=None):
        """See :meth:`Expression.clone()`."""
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
        return Number(myokit.Unit.convert(self._value, self._unit, unit), unit)

    def _diff(self, lhs, idstates):
        return None

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
        """See :meth:`Expression.is_constant()`."""
        return True

    def is_literal(self):
        """See :meth:`Expression.is_literal()`."""
        return True

    def is_number(self, value=None):
        """See :meth:`Expression.is_number()`."""
        return (value is None) or (value == self._value)

    def _polishb(self, b):
        b.write(self._str)

    def _tree_str(self, b, n):
        b.write(' ' * n + self._str + '\n')

    def unit(self):
        """
        Returns the unit associated with this Number or ``None`` if no unit was
        specified.
        """
        return self._unit

    def value(self):
        """Returns the value of this number."""
        return self._value


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
        """See :meth:`Expression.is_constant()`."""
        return self.var().is_constant()

    def is_literal(self):
        """See :meth:`Expression.is_constant()`."""
        return False

    def rhs(self):
        """
        Returns the RHS expression equal to this LHS expression in the
        associated model.
        """
        raise NotImplementedError

    def var(self):
        """
        Returns the variable referenced by this `LhsExpression`.

        For :class:`Name` objects this will be equal to the left hand side of
        their defining equation, for :class:`Derivative` objects this will be
        the variable they represent the derivative of.
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
        self._value = value
        self._references = set([self])
        self._proper = isinstance(self._value, myokit.Variable)

    def bracket(self, op=None):
        """See :meth:`Expression.bracket()`."""
        if op is not None:
            raise ValueError('Given operand is not used in this expression.')
        return False

    def clone(self, subst=None, expand=False, retain=None):
        """See :meth:`Expression.clone()`."""
        if subst and self in subst:
            return subst[self]
        if expand and self._proper:
            if not self._value.is_state():
                if (retain is None) or (
                        self not in retain
                        and self._value not in retain
                        and self._value.qname() not in retain
                ):
                    return self._value.rhs().clone(subst, expand, retain)
        return Name(self._value)

    def _code(self, b, c):
        if self._proper:
            # Handle proper variable references
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
        elif isinstance(self._value, basestring):
            # Allow strings for debugging
            b.write('str:' + str(self._value))
        else:
            # Allow "misusing" the expression system by storing other types as
            # values.
            b.write(str(self._value))

    def _diff(self, lhs, idstates):

        # Derivative w.r.t. self is one
        if lhs == self:
            return Number(1)

        # Value isn't a variable? Then always return an object
        if not self._proper:
            return PartialDerivative(self, lhs)

        # If idstates=False, a state variable reference returns an object, and
        # any state-dependent variable is dependent on the lhs.
        if not idstates:
            if self._value.is_state():
                return PartialDerivative(self, lhs)
            elif self._value.is_intermediary():
                # Possible state dependency: check!
                if self.depends_on_state(deep=True):
                    return PartialDerivative(self, lhs)

        # Otherwise, check for dependency (includes checks on this variable!)
        if self.depends_on(lhs, deep=True):
            return PartialDerivative(self, lhs)
        return None

    def _eval_unit(self, mode):

        if self._proper:
            # Note: Don't get it from the variable's RHS!
            # If the variable unit isn't specified:
            #  1. In tolerant mode a None will propagate without errors
            #  2. In strict mode, it is dimensionless (and if the RHS thinks
            #     otherwise the RHS is wrong).
            # In addition, for e.g. derivatives this can lead to cycles.
            return self._value.unit(mode)

        # Improper name, return dimensionless or None
        elif mode == myokit.UNIT_STRICT:
            return myokit.units.dimensionless
        return None

    def __eq__(self, other):
        if type(other) != Name:
            return False
        if self._proper:
            # Value is name? Then just check with is
            return self._value is other._value
        else:
            # Debug thing? Then convert to string and see if the
            # representations match. (This is the same as what would happen if
            # __eq__ was called on an expression _containing_ a Name, e.g
            # myokit.PrefixPlus(myokit.Name(1.23)).
            return self.code() == other.code()

    def is_name(self, var=None):
        """See :meth:`Expression.is_name()`."""
        return (var is None) or (var == self._value)

    def is_state_value(self):
        """See: meth:`Expression.is_state_value()`."""
        return self._proper and self._value.is_state()

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
        """See :meth:`LhsExpression.rhs()`."""
        if self._proper:
            if self._value.is_state():
                return Number(self._value.state_value())
            elif self._value.lhs() == self:
                return self._value.rhs()
        return None

    def _tree_str(self, b, n):
        b.write(' ' * n + str(self._value) + '\n')

    def _validate(self, trail):
        super(Name, self)._validate(trail)
        # Check value: String is allowed at construction for debugging, but
        # not here!
        if not self._proper:
            raise IntegrityError(
                'Name value "' + repr(self._value) + '" is not an instance of'
                ' class myokit.Variable', self._token)

    def var(self):
        """See :meth:`LhsExpression.var()`."""
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
                'The dot() operator can only be used on variables.',
                self._token)
        self._op = op
        self._proper = self._op._proper
        self._references = set([self])

    def bracket(self, op):
        """See :meth:`Expression.bracket()`."""
        if op != self._op:
            raise ValueError('Given operand is not used in this expression.')
        return False

    def clone(self, subst=None, expand=False, retain=None):
        """See :meth:`Expression.clone()`."""
        if subst and self in subst:
            return subst[self]
        return Derivative(self._op.clone(subst, expand, retain))

    def _code(self, b, c):
        b.write('dot(')
        self._op._code(b, c)
        b.write(')')

    def _diff(self, lhs, idstates):
        # Value isn't a variable? Then always return an object
        if not self._proper:
            return PartialDerivative(self, lhs)

        # Get rhs
        rhs = self._op._value.rhs()

        # Not treating states as independent: then return object if any of the
        # RHS's references are to intermediary or state variables.
        # (Note that the fact that this is a dot(state) doesn't mean it depends
        # on that state: We should instead inspect the RHS.)
        if not idstates:
            for ref in rhs._references:
                var = ref.var()
                if ref == lhs or (not ref._proper) or var.is_state():
                    return PartialDerivative(self, lhs)
                if var.is_intermediary():
                    # Possible state dependency: check!
                    if ref.depends_on_state(deep=True):
                        return PartialDerivative(self, lhs)

        # Check for dependencies in RHS
        if rhs.depends_on(lhs, deep=True):
            return PartialDerivative(self, lhs)
        return None

    def _eval_unit(self, mode):
        # Get numerator (never None in strict mode)
        unit1 = self._op._eval_unit(mode)

        # Get denomenator
        unit2 = \
            myokit.units.dimensionless if mode == myokit.UNIT_STRICT else None
        if self._proper:
            model = self._op._value.model()
            if model is not None:
                unit2 = model.time_unit(mode)

        # Handle as division
        if unit2 is None:
            return unit1    # Can be None in tolerant mode!
        elif unit1 is None:
            return 1 / unit2
        return unit1 / unit2

    def is_derivative(self, var=None):
        """See :meth:`Expression.is_derivative()`."""
        return (var is None) or (var == self._op._value)

    def _polishb(self, b):
        b.write('dot ')
        self._op._polishb(b)

    def __repr__(self):
        return '<Derivative(' + repr(self._op) + ')>'

    def rhs(self):
        """See :meth:`LhsExpression.rhs()`."""
        if self._proper:
            return self._op._value.rhs()
        return None

    def _tree_str(self, b, n):
        b.write(' ' * n + 'dot(' + str(self._op._value) + ')\n')

    def var(self):
        """See :meth:`LhsExpression.var()`."""
        return self._op._value

    def _validate(self, trail):
        super(Derivative, self)._validate(trail)
        # Check that value is a variable has already been performed by name
        # Check if value is the name of a state variable
        if not self._op._value.is_state():
            raise IntegrityError(
                'Derivatives can only be defined for state variables.',
                self._token)


class PartialDerivative(LhsExpression):
    """
    Represents a reference to the partial derivative of one variable with
    respect to another.

    This class is used when writing out derivatives of equations, but may _not_
    appear in right-hand-side expressions for model variables!

    *Extends:* :class:`LhsExpression`
    """
    _rbp = FUNCTION_CALL
    _nargs = [2]    # Allows parsing as a function
    __hash__ = LhsExpression.__hash__   # For Python3, when __eq__ is present

    def __init__(self, var1, var2):
        if not isinstance(var1, (Name, Derivative)):
            raise IntegrityError(
                'The first argument to a partial derivative must be a'
                ' variable name or a dot() expression.')
        if not isinstance(var2, (Name, InitialValue)):
            raise IntegrityError(
                'The second argument to a partial derivative must be a'
                ' variable name or an initial value.')
        super(PartialDerivative, self).__init__((var1, var2))

        self._var1 = var1
        self._var2 = var2
        self._references = set([self])
        self._has_partials = True

    def bracket(self, op=None):
        """See :meth:`Expression.bracket()`."""
        if op not in self._operands:
            raise ValueError('Given operand is not used in this expression.')
        return False

    def clone(self, subst=None, expand=False, retain=None):
        """See :meth:`Expression.clone()`."""
        if subst and self in subst:
            return subst[self]
        return PartialDerivative(
            self._var1.clone(subst, expand, retain),
            self._var2.clone(subst, expand, retain),
        )

    def _code(self, b, c):
        b.write('diff(')
        self._var1._code(b, c)
        b.write(', ')
        self._var2._code(b, c)
        b.write(')')

    def dependent_expression(self):
        """
        Returns the expression that a derivative is taken of, i.e. "y" in
        "dy/dx".
        """
        return self._var1

    def _diff(self, lhs, idstates):
        raise NotImplementedError(
            'Partial derivatives of partial derivatives are not supported.')

    def _eval_unit(self, mode):
        unit1 = self._var1._eval_unit(mode)
        unit2 = self._var2._eval_unit(mode)
        if unit2 is None:
            return unit1    # Can be None in tolerant mode!
        elif unit1 is None:
            return 1 / unit2
        return unit1 / unit2

    def independent_expression(self):
        """
        Returns the expression that a derivative is taken with respect to, i.e.
        ``x`` in ``dy/dx``.
        """
        return self._var2

    def _polishb(self, b):
        b.write('diff ')
        self._var1._polishb(b)
        self._var2._polishb(b)

    def __repr__(self):
        return ('<PartialDerivative(' + repr(self._var1) + ', '
                + repr(self._var2) + ')>')

    def rhs(self):
        """
        See :meth:`LhsExpression.rhs()`.

        The RHS returned in this case will be ``None``, as there is no RHS
        associated with partial derivatives in the model.
        """
        return None

    def _tree_str(self, b, n):
        b.write(' ' * n + 'partial\n')
        self._var1._tree_str(b, n + self._treeDent)
        self._var2._tree_str(b, n + self._treeDent)

    def var(self):
        """
        See :meth:`LhsExpression.var()`.

        As with time-derivatives, this returns the variable of which a
        derivative is taken (i.e. the dependent variable "y" in "dy/dx").
        """
        return self._var1._value


class InitialValue(LhsExpression):
    """
    Represents a reference to the initial value of a state variable.

    This class is used when writing out derivatives of equations, but may _not_
    appear in right-hand-side expressions for model variables!

    *Extends:* :class:`LhsExpression`
    """
    _rbp = FUNCTION_CALL
    _nargs = [1]    # Allows parsing as a function
    __hash__ = LhsExpression.__hash__   # For Python3, when __eq__ is present

    def __init__(self, var):
        super(InitialValue, self).__init__((var, ))
        if not isinstance(var, Name):
            raise IntegrityError(
                'The first argument to an initial condition must be a variable'
                ' name.', self._token)

        self._var = var
        self._references = set([self])
        self._has_initials = True

    def bracket(self, op=None):
        """See :meth:`Expression.bracket()`."""
        if op not in self._operands:
            raise ValueError('Given operand is not used in this expression.')
        return False

    def clone(self, subst=None, expand=False, retain=None):
        """See :meth:`Expression.clone()`."""
        if subst and self in subst:
            return subst[self]
        return InitialValue(self._var.clone(subst, expand, retain))

    def _code(self, b, c):
        b.write('init(')
        self._var._code(b, c)
        b.write(')')

    def _diff(self, lhs, idstates):
        raise NotImplementedError(
            'Partial derivatives of initial conditions are not supported.')

    def _eval_unit(self, mode):
        return self._var._eval_unit(mode)

    def _polishb(self, b):
        b.write('init ')
        self._var._polishb(b)

    def __repr__(self):
        return '<InitialValue(' + repr(self._var) + ')>'

    def rhs(self):
        """
        See :meth:`LhsExpression.rhs()`.

        The RHS returned in this case will be ``None``, as there is no RHS
        associated with initial conditions in the model.
        """
        # Note: This _could_ return a Number(init, var unit) instead...
        return None

    def _tree_str(self, b, n):
        b.write(' ' * n + 'init(' + str(self._var._value) + ')\n')

    def var(self):
        """See :meth:`LhsExpression.var()`."""
        return self._var._value

    def _validate(self, trail):
        super(InitialValue, self)._validate(trail)
        # Check if value is the name of a state variable
        var = self._var._value
        if not (isinstance(var, myokit.Variable) and var.is_state()):
            raise IntegrityError(
                'Initial conditions can only be defined for state variables.',
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
        """See :meth:`Expression.bracket()`."""
        if op != self._op:
            raise ValueError('Given operand is not used in this expression.')
        return (self._op._rbp > LITERAL) and (self._op._rbp < self._rbp)

    def clone(self, subst=None, expand=False, retain=None):
        """See :meth:`Expression.clone()`."""
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

    def _diff(self, lhs, idstates):
        return self._op._diff(lhs, idstates)

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

    def _diff(self, lhs, idstates):
        op = self._op._diff(lhs, idstates)
        return None if op is None else PrefixMinus(op)

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
    _spaces_round_operator = True

    def __init__(self, left, right):
        super(InfixExpression, self).__init__((left, right))
        self._op1 = left
        self._op2 = right

    def bracket(self, op):
        """See :meth:`Expression.bracket()`."""
        if op == self._op1:
            return (op._rbp > LITERAL and (op._rbp < self._rbp))
        elif op == self._op2:
            return (op._rbp > LITERAL and (op._rbp <= self._rbp))
        raise ValueError('Given operand is not used in this expression.')

    def clone(self, subst=None, expand=False, retain=None):
        """See :meth:`Expression.clone()`."""
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
        if self._spaces_round_operator:
            b.write(' ')
        b.write(self._rep)
        if self._spaces_round_operator:
            b.write(' ')
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

    def _diff(self, lhs, idstates):
        op1 = self._op1._diff(lhs, idstates)
        op2 = self._op2._diff(lhs, idstates)
        if op1 is None:
            return op2  # Could be None
        if op2 is None:
            return op1  # Definitely not None
        return Plus(op1, op2)

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
            + unit1.clarify() + ' and ' + unit2.clarify() + '.')


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

    def _diff(self, lhs, idstates):
        op1 = self._op1._diff(lhs, idstates)
        op2 = self._op2._diff(lhs, idstates)
        if op2 is None:
            return op1  # Could be None
        if op1 is None:
            # Op2 is not None, so need to return -op2
            return PrefixMinus(op2)
        return Minus(op1, op2)

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
            self, 'Subtraction requires equal units, got '
            + unit1.clarify() + ' and ' + unit2.clarify() + '.')


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

    def _diff(self, lhs, idstates):
        op1 = self._op1._diff(lhs, idstates)
        op2 = self._op2._diff(lhs, idstates)
        if op1 is None and op2 is None:
            return None
        elif op2 is None:
            return Multiply(op1, self._op2)     # f' g
        elif op1 is None:
            return Multiply(self._op1, op2)     # f g'
        return Plus(Multiply(op1, self._op2), Multiply(self._op1, op2))

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

    def _diff(self, lhs, idstates):
        op1 = self._op1._diff(lhs, idstates)
        op2 = self._op2._diff(lhs, idstates)

        if op1 is None and op2 is None:
            return None
        elif op2 is None:
            # g f' / g^2 = f' / g
            return Divide(op1, self._op2)
        elif op1 is None:
            # -(f g') / g^2
            return Divide(
                Multiply(PrefixMinus(self._op1), op2),
                Power(self._op2, Number(2))
            )

        # (f' g - f g') / g^2
        return Divide(
            Minus(Multiply(op1, self._op2), Multiply(self._op1, op2)),
            Power(self._op2, Number(2))
        )

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
    Represents the quotient of a division ``left // right``, also known as
    integer division.

    >>> import myokit
    >>> x = myokit.parse_expression('7 // 3')
    >>> print(x.eval())
    2.0

    Note that, for negative numbers Myokit follows the convention of rounding
    towards negative infinity, rather than towards zero. Thus:

    >>> print(myokit.parse_expression('-7 // 3').eval())
    -3.0

    Similarly:

    >>> print(myokit.parse_expression('5 // -3').eval())
    -2.0

    Note that this differs from how integer division is implemented in C, which
    _truncates_ (round towards zero), but similar to how ``floor()`` is
    implemented in C, which rounds towards negative infinity.

    See: https://python-history.blogspot.co.uk/2010/08/
    And: https://en.wikipedia.org/wiki/Euclidean_division

    *Extends:* :class:`InfixExpression`
    """
    _rbp = PRODUCT
    _rep = '//'

    def _diff(self, lhs, idstates):
        # The result of a // b is always flat, with discontinuous jumps
        # whenever a = k*b (for an integer k). As a result, the derivatives
        # d/da(a//b) and d/db(a//b) are either zero (most of the time) or
        # undefined (at the jumps). Notably, outside of the jump points, the
        # line a//b is flat, so does not depend on a, b, a', or b'!
        #
        # Alternatively, a // b = floor(a / b).
        #
        # Here we ignore the discontinuities in favour of a left or right
        # derivative, and simply return zero for all points.
        return None

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

    See: https://en.wikipedia.org/wiki/Modulo_operation

    *Extends:* :class:`InfixExpression`
    """
    _rbp = PRODUCT
    _rep = '%'

    def _diff(self, lhs, idstates):
        # Since
        #   a(x) % b(x) is defined as a(x) - b(x) * floor(a(x) / b(x))
        # its derivative is
        #   a' - b' floor(a/b) - b * d/dx floor(a/b).
        # Using d/dx floor(a/b) = 0 (ignoring discontinuities, see Floor), that
        # simplifies to
        #   a' - b' floor(a/b)

        op1 = self._op1._diff(lhs, idstates)
        op2 = self._op2._diff(lhs, idstates)

        if op1 is None and op2 is None:
            return None
        elif op1 is None:
            # -b' floor(a/b)
            return Multiply(
                PrefixMinus(op2), Floor(Divide(self._op1, self._op2)))
        elif op2 is None:
            # a'
            return op1

        # a' - b' floor(a/b)
        return Minus(op1, Multiply(op2, Floor(Divide(self._op1, self._op2))))

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
    _spaces_round_operator = False

    def _diff(self, lhs, idstates):
        # The general rule is derived using a(x)^b(x) = e^(ln(a(x)) * b(x)).
        # This only works when ln(a(x)) is defined, so when a(x) >= 0. But this
        # is OK, as a(x)^b(x) is only defined for fractional b(x) if a(x) >= 0!
        #
        # Applying the chain and product rules:
        #  d/dx e^(ln(a) * b)
        #   = e^(ln(a) * b) * d/dx (ln(a) * b)
        #   = a^b * (ln(a) * b' + b / a * a')
        #
        # If b' is 0 this reduces to a^b * b/a * a' = b * a^(b-1) * a'
        # If a' is 0 this reduces to a^b * b' / ln(a) (for a >= 0)
        #
        # If b depends on the lhs, to have a derivative it _must_ be
        # fractional, and so a(x) _must_ be positive. We don't need to check
        # this; it will just fail along with normal evaluation.
        # If b does not depend on the lhs, we use the reduced form i.e. the
        # general power rule.
        #
        op1 = self._op1._diff(lhs, idstates)
        op2 = self._op2._diff(lhs, idstates)

        if op1 is None and op2 is None:
            return None

        if op2 is None:
            # Tweaks: x^number --> reduce number by 1; and x^2 becomes x
            if isinstance(self._op2, Number):
                if self._op2.value() == 2:
                    new_power = self._op1
                elif self._op2.value() == 1:
                    return op1
                else:
                    new_power = Number(self._op2.value() - 1, self._op2.unit())
                    new_power = Power(self._op1, new_power)
            else:
                new_power = Power(self._op1, Minus(self._op2, Number(1)))
            return Multiply(Multiply(self._op2, new_power), op1)

        if op1 is None:
            return Divide(Multiply(self, op2), Log(self._op1))

        return Multiply(self, Plus(
            Multiply(Log(self._op1), op2),
            Multiply(Divide(self._op2, self._op1), op1)
        ))

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
                self,
                'Exponent in Power must be dimensionless, got '
                + unit2.clarify() + '.')

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
        """See :meth:`Expression.bracket()`."""
        if op not in self._operands:
            raise ValueError('Given operand is not used in this expression.')
        return False

    def clone(self, subst=None, expand=False, retain=None):
        """See :meth:`Expression.clone()`."""
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
                ' dimensionless operand, got ' + unit.clarify() + '.')

        # Unary dimensionless functions are always dimensionless
        return myokit.units.dimensionless


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

    def _diff(self, lhs, idstates):
        op = self._operands[0]
        dop = op._diff(lhs, idstates)
        if dop is None:
            return None
        return Divide(dop, Multiply(Number(2), self))

    def _eval(self, subst, precision):
        try:
            return numpy.sqrt(self._operands[0]._eval(subst, precision))
        except (ArithmeticError, ValueError) as e:  # pragma: no cover
            raise EvalError(self, subst, e)

    def _eval_unit(self, mode):
        unit = self._operands[0]._eval_unit(mode)
        if unit is None:
            return None
        return unit ** 0.5


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

    def _diff(self, lhs, idstates):
        op = self._operands[0]
        dop = op._diff(lhs, idstates)
        if dop is None:
            return None
        return Multiply(Cos(op), dop)

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

    def _diff(self, lhs, idstates):
        op = self._operands[0]
        dop = op._diff(lhs, idstates)
        if dop is None:
            return None
        return Multiply(PrefixMinus(Sin(op)), dop)

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

    def _diff(self, lhs, idstates):
        op = self._operands[0]
        dop = op._diff(lhs, idstates)
        if dop is None:
            return None
        return Divide(dop, Power(Cos(op), Number(2)))

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

    def _diff(self, lhs, idstates):
        op = self._operands[0]
        dop = op._diff(lhs, idstates)
        if dop is None:
            return None
        return Divide(dop, Sqrt(Minus(Number(1), Power(op, Number(2)))))

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

    def _diff(self, lhs, idstates):
        op = self._operands[0]
        dop = op._diff(lhs, idstates)
        if dop is None:
            return None
        return Divide(
            PrefixMinus(dop),
            Sqrt(Minus(Number(1), Power(op, Number(2))))
        )

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

    def _diff(self, lhs, idstates):
        op = self._operands[0]
        dop = op._diff(lhs, idstates)
        if dop is None:
            return None
        return Divide(dop, Plus(Number(1), Power(op, Number(2))))

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

    def _diff(self, lhs, idstates):
        op = self._operands[0]
        dop = op._diff(lhs, idstates)
        if dop is None:
            return None
        return Multiply(self, dop)

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

    def _diff(self, lhs, idstates):

        if len(self._operands) == 1:
            # One operand: natural logarithm: a' / a
            op = self._operands[0]
            dop = op._diff(lhs, idstates)
            if dop is None:
                return None
            return Divide(dop, op)

        else:
            # Two operands: log_a(b) = Log(b, a)
            op1 = self._operands[0]     # b
            op2 = self._operands[1]     # a
            dop1 = op1._diff(lhs, idstates)     # b'
            dop2 = op2._diff(lhs, idstates)     # a'
            if dop1 is None and dop2 is None:
                return None
            elif dop2 is None:
                # a' = 0 --> b' / (b * ln(a))
                return Divide(dop1, Multiply(op1, Log(op2)))

            elif dop1 is None:
                # b' = 0 --> -a' ln(b) / (a ln(a)^2)
                return Divide(
                    Multiply(PrefixMinus(dop2), Log(op1)),
                    Multiply(op2, Power(Log(op2), Number(2))),
                )

            # Full form:
            #   b' / (b * ln(a)) - (a' ln(b)) / (a ln(a)^2)
            return Minus(
                Divide(dop1, Multiply(op1, Log(op2))),
                Divide(
                    Multiply(dop2, Log(op1)),
                    Multiply(op2, Power(Log(op2), Number(2))),
                )
            )

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

        # Check contents of single operand
        if len(self._operands) == 1:
            unit = self._operands[0]._eval_unit(mode)

            # Propagate None in tolerant mode
            if unit is None:
                return None

            # Check units in strict mode
            if mode == myokit.UNIT_STRICT:
                if unit != myokit.units.dimensionless:
                    raise EvalUnitError(
                        self,
                        'Log() requires a dimensionless operand, got '
                        + unit.clarify() + '.')

        # Two operands
        else:
            unit1 = self._operands[0]._eval_unit(mode)
            unit2 = self._operands[1]._eval_unit(mode)

            # Propagate None in tolerant mode
            if unit1 is None and unit2 is None:
                return None

            # Check units in strict mode
            if mode == myokit.UNIT_STRICT:
                if not unit1 == unit2 == myokit.units.dimensionless:
                    raise EvalUnitError(
                        self,
                        'Log() requires dimensionless operands, got '
                        + unit1.clarify() + ' and ' + unit2.clarify() + '.')

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

    def _diff(self, lhs, idstates):
        op = self._operands[0]
        dop = op._diff(lhs, idstates)
        if dop is None:
            return None
        return Divide(dop, Multiply(op, Log(Number(10))))

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

    def _diff(self, lhs, idstates):
        # Floor is stepwise constant, so it's derivative is zero except when
        # the value of its operand is an integer. Here we simplify and just say
        # the derivative is always zero.
        return None

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

    def _diff(self, lhs, idstates):
        # Ceil is stepwise constant, so it's derivative is zero except when
        # the value of its operand is an integer. Here we simplify and just say
        # the derivative is always zero.
        return None

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

    def _diff(self, lhs, idstates):
        # The derivative of abs(f(x)) is f'(x) for x > 0, -f'(x) for x < 0, and
        # undefined if x == 0. Here we simplify and say it's f'(x) if x >= 0.

        # Get derivative of operand
        op = self._operands[0]
        dop = op._diff(lhs, idstates)
        if dop is None:
            return None

        # Get operand unit (_not_ the unit of the returned derivative)
        try:
            unit = op.eval_unit(myokit.UNIT_TOLERANT)
        except myokit.IncompatibleUnitError:
            unit = None

        # Return if
        return If(MoreEqual(op, Number(0, unit)), dop, PrefixMinus(dop))

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

    def _diff(self, lhs, idstates):
        op1 = self._t._diff(lhs, idstates)
        op2 = self._e._diff(lhs, idstates)

        # Return None if both None, or if() if both expressions
        if op1 is None and op2 is None:
            return None
        elif op1 is not None and op2 is not None:
            return If(self._i, op1, op2)

        # If only one is None, create a zero with the correct units
        zero = Number(0, self._diff_unit(lhs))
        if op1 is None:
            return If(self._i, zero, op2)
        else:
            return If(self._i, op1, zero)

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

    def _diff(self, lhs, idstates):

        # Evaluate derivatives of the (m + 1) expressions
        ops = [op._diff(lhs, idstates) for op in self._e]

        # Count the number of Nones
        n_zeroes = sum([1 if op is None else 0 for op in ops])

        # Return None if all None
        if n_zeroes == len(ops):
            return None

        # Create zero to use if any of the expressions are None
        zero = None
        if n_zeroes > 0:
            zero = Number(0, self._diff_unit(lhs))

        # Create and return piecewise
        new_ops = [0] * (2 * len(self._i) + 1)
        for i, _if in enumerate(self._i):
            new_ops[2 * i] = _if
            new_ops[2 * i + 1] = zero if ops[i] is None else ops[i]
        new_ops[-1] = zero if ops[-1] is None else ops[-1]
        return Piecewise(*new_ops)

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

    def _diff(self, lhs, idstates):
        raise NotImplementedError(
            'Conditions do not have partial derivatives.')


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
            return not self._op._eval(subst, precision)
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
        self.line = self.char = None
        if expr._token is not None:
            self.line = expr._token[2]
            self.char = expr._token[3]


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
    if isinstance(e, EvalUnitError):
        msg = 'Incompatible units'
        if e.expr._token is not None:
            msg += ' on line ' + str(e.expr._token[2])
        msg += ': ' + str(e.err)
        out.append(msg)
    else:
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
