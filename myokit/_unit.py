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

import myokit

# Strings in Python 2 and 3
try:
    basestring
except NameError:   # pragma: no python 2 cover
    basestring = str


class Unit(object):
    """
    Represents a unit.

    Most users won't want to create units, but instead use e.g.
    ``myokit.parse_unit('kg/mV')`` or ``myokit.units.mV``.

    Each Unit consists of

      * A list of seven floats: these are the exponents for the basic SI
        units: ``[g, m, s, A, K, cd, mol]``. Gram is used instead of the SI
        defined kilogram to create a more coherent syntax.
      * A multiplier. This includes both quantifiers (such as milli, kilo, Mega
        etc) and conversion factors (for example 1inch = 2.54cm). Multipliers
        are specified in powers of 10, e.g. to create an inch use the
        multiplier log10(2.54).

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
            self._x = [float(x) for x in exponents]
            self._m = float(multiplier)

        self._hash = None
        self._repr = None

    @staticmethod
    def can_convert(unit1, unit2):
        """
        Returns ``True`` if the given units differ only by a multiplication.

        For example, ``[m/s]`` can be converted to ``[miles/hour]`` but not to
        ``[kg]``. This method is an alias of :meth:`close_exponent`.
        """
        return Unit.close_exponent(unit1, unit2)

    def clarify(self):
        """
        Returns a string showing this unit's representation using both the
        short syntax of ``str(unit)``, and the long syntax of ``repr(unit)``.

        For example::

            >>> from myokit import Unit
            >>> print(str(myokit.units.katal))
            [kat]
            >>> print(repr(myokit.units.katal))
            [mol/s]
            >>> print(myokit.units.katal.clarify())
            [kat] (or [mol/s])

        If both representations are equal, the second part is omitted""

            >>> print(myokit.units.m.clarify())
            [m]

        """
        r1 = str(self)
        r2 = repr(self)
        if r1 == r2:
            return r1
        return r1 + ' (or ' + r2 + ')'

    @staticmethod
    def close(unit1, unit2, reltol=1e-9, abstol=1e-9):
        """
        Checks whether the given units are close enough to be considered equal.

        Note that this differs from ``unit1 is unit2`` (which checks if they
        are the same object) and ``unit1 == unit2`` (which will check if they
        are the same unit to machine precision).

        The check for closeness is made with a relative tolerance of ``reltol``
        and absolute tolerance of ``abstol``, using::

            abs(a - b) < max(reltol * max(abs(a), abs(b)), abstol)

        Unit exponents are stored as floating point numbers and compared
        directly. Unit multipliers are stored as ``log10(multiplier)``, and
        compared without transforming back. As a result, units such as
        ``[nF]^2`` won't be considered close to ``[pF]^2``, but units such as
        ``[F]`` will be considered close to ``[F] * (1 + 1e-12)``.
        """
        if unit1 is unit2:
            return True

        # Compare exponents using normal representation, and with absolute
        # tolerance so that tiny differences from 0 are also picked up. Note
        # that this means we can't tell the difference between e.g. m^(1e-10)
        # and m^(1e-11), but that is fine.
        if not Unit.close_exponent(unit1, unit2, reltol, abstol):
            return False

        # Compare multipliers in log10 space. This means we can still easily
        # distinguish between e.g. pF and nF, but we lose the ability to tell
        # the difference between e.g. [F (1)] and [F (1.00000000000001)]
        return myokit.float.close(unit1._m, unit2._m, reltol, abstol)

    @staticmethod
    def close_exponent(unit1, unit2, reltol=1e-9, abstol=1e-9):
        """
        Returns ``True`` if the exponent of ``unit1`` is close to that of
        ``unit2``.

        Exponents are stored internally as floating point numbers, and the
        check for closeness if made with a relative tolerance of ``reltol`` and
        absolute tolerance of ``abstol``, using::

            abs(a - b) < max(reltol * max(abs(a), abs(b)), abstol)

        """
        for i, a in enumerate(unit1._x):
            if not myokit.float.close(a, unit2._x[i], reltol, abstol):
                return False
        return True

    @staticmethod
    def conversion_factor(unit1, unit2, helpers=None):
        """
        Returns a :class:`myokit.Quantity` ``c`` to convert from ``unit1`` to
        ``unit2``, such that ``1 [unit1] * c = 1 [unit2]``.

        For example::

            >>> import myokit
            >>> myokit.Unit.conversion_factor('m', 'km')
            0.001 [1 (1000)]

        Where::

            1 [m] = 0.001 [km/m] * 1 [km]

        so that ``c = 0.001 [km/m]``, and the unit ``[km/m]`` can be written as
        ``[km/m] = [ kilo ] = [1 (1000)]``.

        Note that this method uses the :meth:`close()` and
        :meth:`close_exponent` comparisons to see if units are equal.

        Conversions between *incompatible* units can be performed if one or
        multiple helper :class:`Quantity` objects are passed in. For example,
        to convert from ``g`` to ``mol`` a helper with units ``g/mol`` could
        be passed in. Conversion will be attempted with the helper and the
        inverse of the helper, and with any (dimensionless) scaling. For
        example, a ``g`` to ``mol`` conversion can also be facilitated by a
        helper in ``mol/g`` or ``mol/kg``. If multiple helpers are given each
        will be tried individually: helpers are not combined. If used, a helper
        (possibly scaled and/or inverted) will be included in the returned
        conversion factor ``c``.

        A common example in cell electrophysiology is::

            >>> import myokit
            >>> myokit.Unit.conversion_factor(
            ...     'uA/cm^2', 'uA/uF', ['1 [uF/cm^2]'])
            1.0 [cm^2/uF]

        Where::

            1 [uA/cm^2] = 1 [cm^2/uF] * 1 [uA/uF]

        Arguments:

        ``unit1``
            The new unit to convert from, given as a :class:`myokit.Unit` or as
            a string that can be converted to a unit with
            :meth:`myokit.parse_unit()`.
        ``unit2``
            The new unit to convert to.
        ``helpers=None``
            An optional list of conversion factors, which the method will
            attempt to use if the new and old units are incompatible. Each
            factor should be specified as a :class:`myokit.Quantity` or
            something that can be converted to a Quantity e.g. a string
            ``1 [uF/cm^2]``.

        Returns a :class:`myokit.Quantity`.

        Raises a :class:`myokit.IncompatibleUnitError` if the units cannot be
        converted.'
        """
        # Check unit1
        if not isinstance(unit1, myokit.Unit):
            if unit1 is None:
                unit1 = myokit.units.dimensionless
            else:
                unit1 = myokit.parse_unit(unit1)

        # Check unit2
        if not isinstance(unit2, myokit.Unit):
            if unit2 is None:
                unit2 = myokit.units.dimensionless
            else:
                unit2 = myokit.parse_unit(unit2)

        # Check helper units
        factors = []
        if helpers is not None:
            for factor in helpers:
                if not isinstance(factor, myokit.Quantity):
                    factor = myokit.Quantity(factor)
                factors.append(factor)
        del helpers

        # Simplest case: units are (almost) equal
        if Unit.close(unit1, unit2):
            return Quantity(1)

        # Get conversion factor
        fw = None
        if Unit.close_exponent(unit1, unit2):

            # Directly convertible
            fw = 10**(unit1._m - unit2._m)

        else:
            # Try conversion via one of the helpers
            for factor in factors:

                unit1a = unit1 * factor.unit()
                if Unit.close_exponent(unit1a, unit2):
                    fw = 10**(unit1a._m - unit2._m) * factor.value()
                    break

                unit1a = unit1 / factor.unit()
                if Unit.close_exponent(unit1a, unit2):
                    fw = 10**(unit1a._m - unit2._m) / factor.value()
                    break

        # Unable to convert?
        if fw is None:
            msg = 'Unable to convert from ' + unit1.clarify()
            msg += ' to ' + unit2.clarify()
            if factors:
                msg += ' (even with help of conversion factors).'
            raise myokit.IncompatibleUnitError(msg + '.')

        # Create Quantity and return
        fw = myokit.float.round(fw)
        return Quantity(fw, unit2 / unit1)

    @staticmethod
    def convert(amount, unit1, unit2):
        """
        Converts a number ``amount`` in units ``unit1`` to a new amount in
        units ``unit2``.

            >>> import myokit
            >>> myokit.Unit.convert(3000, 'm', 'km')
            3.0

        """
        factor = Unit.conversion_factor(unit1, unit2)
        if isinstance(amount, myokit.Quantity):
            return factor * amount
        return factor.value() * amount

    def __div__(self, other):   # pragma: no cover      truediv used instead
        return self.__truediv__(other)

    def __eq__(self, other):
        if not isinstance(other, Unit):
            return False

        for i, x in enumerate(self._x):
            if not myokit.float.eq(x, other._x[i]):
                return False
        return myokit.float.eq(self._m, other._m)

    def exponents(self):
        """
        Returns a list containing this unit's exponents.
        """
        return list(self._x)

    def __float__(self):
        # Attempts to convert this unit to a float.

        for x in self._x:
            if x != 0:
                raise TypeError(
                    'Unable to convert unit ' + str(self) + ' to float.')
        return self.multiplier()

    def __hash__(self):
        # Creates a hash for this Unit

        # This uses self._str with rounding, to get hashes that are the same
        # for units that are close (but note that the __eq__ check will still
        # tell them apart). It cannot use str(self) because that can involve
        # hashing to look up a preferred representation.

        if self._hash is None:
            self._hash = hash(self._str(True))
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

    def multiplier_log_10(self):
        """
        Returns the base 10 logarithm of this unit's multiplier.
        """
        return self._m

    def __mul__(self, other):
        # Evaluates ``self * other``

        if not isinstance(other, Unit):
            return Unit(list(self._x), self._m + math.log10(float(other)))
        return Unit(
            [a + b for a, b in zip(self._x, other._x)], self._m + other._m)

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
        # Evaluates ``self ^ other``

        f = float(f)
        e = [myokit.float.round(f * x) for x in self._x]
        return Unit(e, self._m * f)

    def __rdiv__(self, other):  # pragma: no cover    rtruediv used instead
        return self.__rtruediv__(other)

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
        if not isinstance(unit, myokit.Unit):
            raise ValueError(
                'Second argument to register_preferred_representation must be'
                ' a myokit.Unit')
        Unit._preferred_representations[unit] = str(rep)

    def __repr__(self):
        """
        Returns this unit formatted in the base SI units.
        """
        if self._repr is None:
            self._repr = self._str(False)
        return self._repr

    def __rmul__(self, other):
        # Evaluates ``other * self``, where other is not a Unit

        return Unit(list(self._x), self._m + math.log10(other))

    def __rtruediv__(self, other):
        # Evaluates ``other / self``, where other is not a unit, in Python 3
        # or when future division is active.

        return Unit([-a for a in self._x], math.log10(other) - self._m)

    def _str(self, use_close_for_rounding):
        """
        String representation without preferred representations, that will
        round to nearby integers if ``use_close_for_rounding=True``.
        """
        # Rounding
        if use_close_for_rounding:
            rnd = myokit.float.cround
        else:
            rnd = myokit.float.round

        # SI unit names
        si = ['g', 'm', 's', 'A', 'K', 'cd', 'mol']

        # Get unit parts
        pos = []
        neg = []
        for k, x in enumerate(self._x):
            x = rnd(x)
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
        m = self._m
        if m != 0:
            m = rnd(m)
            m = 10**m
            if m >= 1:
                m = rnd(m)
            if m < 1e6:
                m = str(m)
            else:
                m = '{:<1.0e}'.format(m)
            u += ' (' + m + ')'
        return '[' + u + ']'

    def __str__(self):

        # Strategy 1: Try simple look-up (using float.eq comparison)
        try:
            return '[' + Unit._preferred_representations[self] + ']'
        except KeyError:
            pass

        # Strategy 2: Find a representation for a unit that's close to this one
        rep = None
        for unit, test in Unit._preferred_representations.items():
            if Unit.close(self, unit):
                rep = '[' + test + ']'
                break

        # Strategy 3: Try finding a representation for the exponent and adding
        # a multiplier to that.
        if rep is None:

            # Because kilos are defined with a multiplier of 1000, the
            # "multiplier free" value is actually given by
            # 10**(3 * gram exponent)
            m = 3 * self._x[0]
            u = Unit(list(self._x), m)
            rep = Unit._preferred_representations.get(u, None)

            # Add multiplier part
            if rep is not None:
                m = myokit.float.cround(self._m - m)
                m = 10**m
                if m >= 1:
                    m = myokit.float.cround(m)
                if m < 1e6:
                    m = str(m)
                else:
                    m = '{:<1.0e}'.format(m)
                rep = '[' + rep + ' (' + m + ')]'

        # Strategy 4: Build a new representation
        if rep is None:
            rep = self._str(True)

        # Store new representation and return
        Unit._preferred_representations[self] = rep[1:-1]
        return rep

    def __truediv__(self, other):
        # Evaluates self / other if future division is active.

        if not isinstance(other, Unit):
            return Unit(list(self._x), self._m - math.log10(float(other)))
        return Unit(
            [a - b for a, b in zip(self._x, other._x)],
            self._m - other._m)


class Quantity(object):
    """
    Represents a quantity with a :class:`unit <myokit.Unit>`. Can be used to
    perform unit-safe arithmetic.

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
            self._unit = \
                unit if unit is not None else myokit.units.dimensionless

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
                    self._unit = myokit.units.dimensionless
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
                'Cannot add quantities with units ' + self._unit.clarify()
                + ' and ' + other._unit.clarify() + '.')
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

    def __div__(self, other):   # pragma: no cover      truediv used instead
        return self.__truediv__(other)

    def __eq__(self, other):
        if not isinstance(other, Quantity):
            return False
        return self._value == other._value and self._unit == other._unit

    def __float__(self):
        return self._value

    def __hash__(self):
        return hash(self._value) + hash(self._unit)

    def __mul__(self, other):
        if not isinstance(other, Quantity):
            other = Quantity(other)
        return Quantity(self._value * other._value, self._unit * other._unit)

    def __pow__(self, f):
        if isinstance(f, Quantity):
            if f.unit() != myokit.units.dimensionless:
                raise myokit.IncompatibleUnitError(
                    'Exponent of power must be dimensionless')
            f = f.value()
        return Quantity(self._value ** f, self._unit ** f)

    def __radd__(self, other):
        return self + other

    def __repr__(self):
        return self._str

    def __rdiv__(self, other):  # pragma: no cover    rtruediv used instead
        return Quantity(other) / self

    def __rmul__(self, other):
        return self * other

    def __rsub__(self, other):
        return Quantity(other) - self

    def __rtruediv__(self, other):
        return Quantity(other) / self

    def __str__(self):
        return self._str

    def __sub__(self, other):
        if not isinstance(other, Quantity):
            other = Quantity(other)
        if self._unit != other._unit:
            raise myokit.IncompatibleUnitError(
                'Cannot subtract quantities with units ' + self._unit.clarify()
                + ' and ' + other._unit.clarify() + '.')
        return Quantity(self._value - other._value, self._unit)

    def __truediv__(self, other):
        # Evaluates self / other

        if not isinstance(other, Quantity):
            other = Quantity(other)
        return Quantity(self._value / other._value, self._unit / other._unit)

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

