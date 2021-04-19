.. _api/units:

*****
Units
*****

.. currentmodule:: myokit

Model variables can declare their units using the syntax explained in
:ref:`syntax/model/units`. Internally, units are represented as
:class:`Unit` objects.

A large number of units can be accessed through ``myokit.units``, this module
is imported automatically when ``import myokit`` is run::

    >>> import myokit
    >>> print myokit.units.m
    [m]
    >>> print myokit.units.mol / myokit.units.L
    [M]
    >>> print myokit.units.gallons / myokit.units.furlongs
    [m^2 (2.25984749065e-07)]

A class :class:`myokit.Quantity` is provided that can perform unit-safe
arithmetic.

Quantifiers
===========
Basic units (indicated by a shorthand such as ``m``, ``s`` or ``mol`` are
*quantifiable*. Standard SI quantifiers are used (with the exception of the
quantifier Deca/da for 10^1, which is omitted).

+--------+------------+-------+
| Prefix | Multiplier | Name  |
+--------+------------+-------+
| y      | 10^-24     | yocto |
+--------+------------+-------+
| z      | 10^-21     | zepto |
+--------+------------+-------+
| a      | 10^-18     | atto  |
+--------+------------+-------+
| f      | 10^-15     | femto |
+--------+------------+-------+
| p      | 10^-12     | pico  |
+--------+------------+-------+
| n      | 10^-9      | nano  |
+--------+------------+-------+
| u      | 10^-6      | micro |
+--------+------------+-------+
| m      | 10^-3      | milli |
+--------+------------+-------+
| c      | 10^-2      | centi |
+--------+------------+-------+
| d      | 10^-1      | deci  |
+--------+------------+-------+
| h      | 10^2       | hecto |
+--------+------------+-------+
| k      | 10^3       | kilo  |
+--------+------------+-------+
| M      | 10^6       | mega  |
+--------+------------+-------+
| G      | 10^9       | giga  |
+--------+------------+-------+
| T      | 10^12      | tera  |
+--------+------------+-------+
| P      | 10^15      | peta  |
+--------+------------+-------+
| E      | 10^18      | exa   |
+--------+------------+-------+
| Z      | 10^21      | zetta |
+--------+------------+-------+
| Y      | 10^24      | yotta |
+--------+------------+-------+

Quantifiers can be used in ``mmt`` syntax to quantify the abbreviated unit
names. For example the unit ``[ms]`` will be recognized as a millisecond. Full
unit names are not quantifiable: ``[msecond]`` will not be recognized.

Unit class
===========

.. autoclass:: Unit

Known units
===========

.. _api/known_units:

A list of common units recognized by Myokit is given below. For each unit, the
appropriate ``mmt`` syntax is given as well as the unit's object's name in the
``myokit.units`` module.

+----------+-----------------------------------+-----------------+
| SI units                                                       |
+==========+===================================+=================+
| Kilogram | ``[kg]``, ``[kilogram]``          | kg, kilogram    |
+----------+-----------------------------------+-----------------+
| Meter    | ``[m]``, ``[metre]``, ``[meter``] | m, metre, meter |
+----------+-----------------------------------+-----------------+
| Second   | ``[s]``, ``[second]``             | s, second       |
+----------+-----------------------------------+-----------------+
| Ampere   | ``[A]``, ``[ampere]``             | A, ampere       |
+----------+-----------------------------------+-----------------+
| Kelvin   | ``[K]``, ``[kelvin]``             | K, kelvin       |
+----------+-----------------------------------+-----------------+
| Candela  | ``[cd]``, ``[candela]``           | cd, candela     |
+----------+-----------------------------------+-----------------+
| Mole     | ``[mol]``, ``[mole]]``            | mol, mole       |
+----------+-----------------------------------+-----------------+

The short form of the SI units is quantifiable in ``mmt`` syntax: ``[ms]``,
``[kmol]``, etc. The exception is ``[kg]``, which in Myokit is implemented as
the quantified form of ``[g]``: ``[mg]``, ``[kg]`` etc.

+---------------+------------------+----------------+
| Dimensionless units                               |
+===============+==================+================+
| Dimensionless | ``[1]``          | dimensionless  |
+---------------+------------------+----------------+
| Radian        | ``[rad]``        | rad            |
+---------------+------------------+----------------+
|               | ``[radian]``     | radian         |
+---------------+------------------+----------------+
| Steradian     | ``[sr]``         | sr             |
+---------------+------------------+----------------+
|               | ``[sterradian]`` | sterradian     |
+---------------+------------------+----------------+

+----------+--------------------------+--------------+------------------------+
| Derived SI units                                                            |
+==========+==========================+==============+========================+
| Hertz    | ``[Hz]``, ``[hertz]``    | Hz, hertz    | Frequency              |
+----------+--------------------------+--------------+------------------------+
| Newton   | ``[N]``, ``[newton]``    | N, newton    | Force                  |
+----------+--------------------------+--------------+------------------------+
| Pascal   | ``[Pa]``, ``[pascal]``   | Pa, pascal   | Pressue                |
+----------+--------------------------+--------------+------------------------+
| Joule    | ``[J]``, ``[joule]``     | J, joule     | Energy                 |
+----------+--------------------------+--------------+------------------------+
| Watt     | ``[W]``, ``[watt]``      | W, watt      | Power                  |
+----------+--------------------------+--------------+------------------------+
| Coulomb  | ``[C]``, ``[coulomb]``   | C, coulomb   | Charge                 |
+----------+--------------------------+--------------+------------------------+
| Volt     | ``[V]``, ``[volt]``      | V, volt      | Electrical potential   |
+----------+--------------------------+--------------+------------------------+
| Farad    | ``[F]``, ``[farad]``     | F, farad     | Electrical capacitance |
+----------+--------------------------+--------------+------------------------+
| Ohm      | ``[R]``, ``[ohm]``       | R, ohm       | Electrical resistance  |
+----------+--------------------------+--------------+------------------------+
| Siemens  | ``[S]``, ``[siemens]``   | S, siemens   | Electrical conductance |
+----------+--------------------------+--------------+------------------------+
| Weber    | ``[Wb]``, ``[weber]``    | Wb, weber    | Magnetic flux          |
+----------+--------------------------+--------------+------------------------+
| Tesla    | ``[T]``, ``[tesla]``     | T, tesla     | Magnetic flux density  |
+----------+--------------------------+--------------+------------------------+
| Henry    | ``[H]``, ``[henry]``     | H, henry     | Magnetic field strength|
+----------+--------------------------+--------------+------------------------+
| Lumen    | ``[lm]``, ``[lumen]``    | lm, lumen    | Luminous flux          |
+----------+--------------------------+--------------+------------------------+
| Lux      | ``[lx]``, ``[lux]``      | lx, lux      | Illuminance            |
+----------+--------------------------+--------------+------------------------+
| Bequerel | ``[Bq]``, ``[bequerel]`` | Bq, bequerel | Radiocative decay      |
+----------+--------------------------+--------------+------------------------+
| Gray     | ``[Gy]``, ``[gray]``     | Gy, gray     | Absorbed ion. rad.     |
+----------+--------------------------+--------------+------------------------+
| Sievert  | ``[Sv]``, ``[sievert]``  | Sv, sievert  | Equivalent rad. dose   |
+----------+--------------------------+--------------+------------------------+
| Katal    | ``[kat]``, ``[katal]``   | kat, katal   | Catalytic activity     |
+----------+--------------------------+--------------+------------------------+

The short version of each dervied SI unit is quantifiable in ``mmt`` syntax,
allowing constructs like ``[mS/uF]``.

In addition, Myokit recognises a host of other units such as ``[L]`` for liter,
``[M]`` for mole/liter (quantifiable), ``bar`` and ``atm``, ``[minute]`` and
``[year]`` and even ``[parsec]``, ``[angstrom]``, ``[gallons]`` and
``[dog_year]``.


Unit arithmetic
===============

.. autoclass:: Quantity

For people who don't like units
===============================

.. autofunction:: strip_expression_units

