.. _syntax/model:

***********************
Model definition syntax
***********************

Every line starting in ``#`` is taken to be a comment.

White lines are ignored.

Everything within a set of parentheses is read as one line. This can be used
to create multi-line statements. Alternatively, code may be split over
multiple lines by ending a line with \

The first non-comment in a file must be a model header. The exact syntax of
a model header is given below.

A model is divided into components. Components are declared by writing
``[component_name]`` on a new line (including the square brackets!). Each
component lasts until the next component declaration.

Within a component, a variable is defined by writing its name on a new,
unindented line. Variables can contain nested variables, not visible outside
the scope of their parent variable. Nesting is indicated using indenting.

Variable names
==============
Model, component and variable names follow standard programming conventions:
each name must start with a letter and the remainder of the name can contain
any 'word' character: lowercase letters, uppercase letters, numbers or an
underscore.

Within a component, variables can simply be referred to using their name.
To reference a variable from another component, its "fully qualified" name
must be used. This consists of the component name followed by a period
followed by the variable name: ``component_name.variable_name``.

Model header
============
Each model must begin with a model header ``[[model]]``.

Meta-data can be added to a model using the syntax ``field: value``

All state variables require an initial value to be specified in the model
header using the syntax ``component.variable = value``

Initial values can be numbers or expressions. Expressions can make reference 
to variables as long as they are constant in time. References must be made
using fully qualified names, for example using ``c.y`` to refer to variable
``y`` in component ``c``.

Example::

    [[model]]
    name: This model's name
    desc: Model description. Can be split over multiple lines using \
          backslash notation.
    author: Identifies the author of the model implementation
    membrane.V = -84
    na_fast.m  = 0
    na_fast.h  = 1.0
    na_fast.j  = 1.0

Component syntax
================
A component starts with its name in square brackets, followed by any number
of variables of meta-data properties
::

    [component_1]
    desc: This is the first component
    x = <expression>
    y = <expression>
    dot(z) = <expression>

All component names must be unique.

Defining variables
==================
Each variable must have a single defining equation of the form that describes
either its value or its derivative. In the following example x is defined
directly, whereas y is a state variable defined through its derivative::

    x = 12
    dot(y) = 10 * y

The ``dot()`` operator is the only operator that may appear on the left-hand
side of an equation.

Meta-data and descriptions
==========================
Meta data can be specified by adding ``field: value`` pairs on the lines
following a variable's definition. To indicate they belong to the previous
variable, these lines should be indented.
::

    E_Na = 12
        desc: The Nernst potential of sodium
        latex: E_{Na^+}

All text to the right of a ``:`` sign is treated as plain text. Meta properties
can be added at will.

The common meta property "desc" can be set using the following
shorthand syntax::

    x = 12 : A weight

This is equivalent to
::

    x = 12
        desc: A weight

A model part cannot specify the same meta-data property twice. For example, a
variable cannot have two properties 'name'.

Meta-data properties can be grouped into namespaces using the syntax::

    x = 123
        group1:property1: This is the first property in group 1
        group1:property2: This is the second property in group 1
        group2:property1: This is the first property in group 2


.. _syntax/model/units:

Units
=====
Myokit has support for units in two ways: units attached to a variable and
units attached to a literal value.

Variables can specify their units using the ``in`` keyword::

    x = 12 : A weight
        in [kg]

This specifies that the variable ``x`` is in the unit ``kg``, regardless of how
``x`` is defined: ``x = 12`` or ``x = exp(cos(4)+2)``, we know that it's in
``kg``.

The second way of using units is by attaching them to a literal value. For
example writing ``5 [kg]`` instead of ``5``. This double specification can be
used for unig checking, for example, if x is known to be invalid it makes no
sense to assign it a value ``7 [m/s]``.

For state variables, the ``in`` keyword refers to *the variable*, not its
derivative. Thus::

    dot(V) = 5
        in [mV]

specifies that ``V`` is in ``[mV]``. Using ``[ms]`` as time unit, the
expression ``dot(V)`` itself is expressed in ``[mV/ms]``.

Unit specifications use the following syntax:
    * A "simple unit" consists of a unit name (m, g, V etc) with an optional
      quantifier (mm, kg, etc). Not all unit names support quantifiers, a
      "centimile", for example, will not be recognized.
    * Simple units can be exponentiated using ``^``. For example ``m^3`` and
      ``s^-1``
    * (Exponentiated) simple units can be strung together using multiplication
      (``*``) or division (``/``). For example ``kg/cm^2``.
    * A full unit description is a string of (exponentiated) simple units
      wrapped in square brackets. For example ``[kg/cm^2]``.
    * An optional multiplication factor can be added. For example an inch can
      be written as ``[cm (2.54)]`` or ``[m (0.0254)]``.
    * Units with offsets (celsius and fahrenheit) are not supported.

Myokit supports at least the following units:
    * The seven base SI units ``kg``, ``m``, ``s``, ``A``, ``K``, ``cd`` and
      ``mol``
    * A number of derived SI units such as ``V``, ``C``, ``F`` and others
    * A number of non-si units such as ``M`` (molar) and ``L`` (liter)
    * Some alternative units such as ``lb``, ``mile``, ``day`` etc

A large number of predefined units are available in the module
``myokit.units``.

Quantifiers such as "k" for kilo, "m" for milli etc. can be added for all base
SI units, derived SI units and a couple of non-SI ones (notably mL and mM).
The available quantifiers are:

+---+-------+-------+
| y | yocto | 1e-24 |
+---+-------+-------+
| z | zepto | 1e-21 |
+---+-------+-------+
| a | atto  | 1e-18 |
+---+-------+-------+
| f | femto | 1e-15 |
+---+-------+-------+
| p | pico  | 1e-12 |
+---+-------+-------+
| n | nano  | 1e-9  |
+---+-------+-------+
| u | micro | 1e-6  |
+---+-------+-------+
| m | milli | 1e-3  |
+---+-------+-------+
| c | centi | 1e-2  |
+---+-------+-------+
| d | deci  | 1e-1  |
+---+-------+-------+
| h | hecto | 1e2   |
+---+-------+-------+
| k | kilo  | 1e3   |
+---+-------+-------+
| M | mega  | 1e6   |
+---+-------+-------+
| G | giga  | 1e9   |
+---+-------+-------+
| T | tera  | 1e12  |
+---+-------+-------+
| E | exa   | 1e15  |
+---+-------+-------+
| Z | zetta | 1e18  |
+---+-------+-------+
| Y | yotta | 1e21  |
+---+-------+-------+

Note the omission of "deca/deka" (da) and the use of "u" for micro.

Some examples of valid unit declarations are::

    F = [C/mol]
    R = 8314 [mJ/mol/K]
    T = 310 [K]

    length = 0.01 [cm]
    radius = 0.0011 [cm] : Cell radius
    volume = 3.14 * 1000 * radius * radius * length
        in [uL]
        desc: Cell volume
    v_cyt = volume * 0.678
        in [uL]

Foreign variables
=================
Variables from other components can be addressed using the syntax
``component_name.variable_name``.
::

    [membrane]
    dot(V) = expression

    [other]
    x = 5 * exp(membrane.V)

Local aliases
=============
Within a component, it is possible to define an alias for commonly used
variables from different components::

    [membrane]
    dot(V) = expression

    [other]
    use membrane.V as Vm
    x = 5 * exp(Vm)

If no name is specified with "as", the original variable name is used. In the
following example the ``[other]`` component is equivalent to the one given
above::

    [other]
    use membrane.V
    x = 5 * exp(V)

Alias definitions can be chained together with commas::

    [other]
    use membrane.V, comp.var1 as v1, comp.var2 as v2
    x = 5 * exp(V) + v1 * v2

Nested variables
================
Many electrophysiological equations contain repeated terms or terms with a
conceptual meaning that are not used by any other equations within the system.
To separate these "sub-equations", myokit allows nesting of variables.

Nested variables can be added to a variable definition by writing them indented
on the subsequent line::

    dot(m) = a * (1 - m) + b * m
        a = 5 * exp(3)
        b = 10 * 1 / exp(V + 40)

In this example, ``m`` is said to be the parent of ``a`` and ``b``. Variables
with the same parent are referred to as siblings.

Myokit allows multi-level nesting::

    dot(m) = a * (1 - m) + b * m
        a = 5 * exp(3)
        b = c + 14
            c = 5

Here, the set of ``m`` and ``b`` are refered to as ``c``'s ancestors.

Scope and naming
================
Using an unqualified name, a variable can always access its own child variables
or a child of any of its ancestors. Access to children of any other variables
is not allowed.

Using a qualified name (component.variable), a variable can access non-nested
variables in any component.

This is reflected in the naming scope rules: when adding a variable to a
component or another variable the naming rules are checked to ensure names are
unique with each variable's scope.

Multi-line expressions
======================
Variable expressions spanning multiple lines can be created by ending a line
in ``\`` or by wrapping the expression in parentheses::

    [membrane]
    dot(V) = 1 / C * ( I_one
                 + I_two
                 + I_three)
    I_one = g * (V - E)   \
          + a + b + c

Multi-line metadata
===================
Multi-line metadata values can be entered by wrapping them in triple quotes::

    R = 8314
        desc: """
              This is a very
              very
              long description
              """

The line breaks in multi-line values are maintained, all whitespace is
trimmed from the right-hand side. On the left, whitespace corresponding to
the lowest indentation level is trimmed.

Expression syntax
=================
The following operators are provided:

+---------+-----------------------------+-----------------+
|  ``+``  | Addition                    | ``1 + 1 = 2``   |
+---------+-----------------------------+-----------------+
|  ``-``  | Subtraction                 | ``2 - 1 = 1``   |
+---------+-----------------------------+-----------------+
|  ``*``  | Multiplication              | ``4 * 2 = 8``   |
+---------+-----------------------------+-----------------+
|  ``/``  | Division                    | ``8 / 4 = 2``   |
+---------+-----------------------------+-----------------+
|  ``//`` | Integer division / Quotient | ``11 // 3 = 3`` |
+---------+-----------------------------+-----------------+
|  ``%``  | Modulo / Remainder          | ``11 % 3  = 2`` |
+---------+-----------------------------+-----------------+
|  ``^``  | Exponentiation / Power      | ``3 ^ 2 = 9``   |
+---------+-----------------------------+-----------------+

In addition, + and - can be used to indicate signs: ``+5+-2=3``

Parts of expressions can be grouped using parentheses ``5 * (4 - 2) = 10``

The following conditional operators are defined:

+--------+-----------------------+
| ``==`` | Equality              |
+--------+-----------------------+
| ``!=`` | Inequality            |
+--------+-----------------------+
| ``>``  | Greater than          |
+--------+-----------------------+
| ``<``  | Less than             |
+--------+-----------------------+
| ``>=`` | Greater than or equal |
+--------+-----------------------+
| ``<=`` | Less than or equal    |
+--------+-----------------------+

Conditions can be strung together using ``and`` and ``or``, or negated with
``not``.

Pre-defined Functions
=====================
The following functions are defined:

+----------------+------------------------------------------------------------+
| ``sqrt(x)``    | Square root                                                |
+----------------+------------------------------------------------------------+
| ``sin(x)``     | Sine (all trigonomic functions work with radians)          |
+----------------+------------------------------------------------------------+
| ``cos(x)``     | Cosine                                                     |
+----------------+------------------------------------------------------------+
| ``tan(x)``     | Tangent                                                    |
+----------------+------------------------------------------------------------+
| ``asin(x)``    | Inverse sine                                               |
+----------------+------------------------------------------------------------+
| ``acos(x)``    | Inverse cosine                                             |
+----------------+------------------------------------------------------------+
| ``atan(x)``    | Inverse tangent                                            |
+----------------+------------------------------------------------------------+
| ``exp(x)``     | Returns e to the power of x                                |
+----------------+------------------------------------------------------------+
| ``log(x)``     | Returns the natural logarithm (also known as ln) of x      |
+----------------+------------------------------------------------------------+
| ``log(x, b)``  | Returns the base-b logarithm of x                          |
+----------------+------------------------------------------------------------+
| ``log10(x)``   | Returns the base-10 logarithm of x                         |
+----------------+------------------------------------------------------------+
| ``floor(x)``   | Returns the largest integer less than or equal to x        |
+----------------+------------------------------------------------------------+
| ``ceil(x)``    | Returns the smallest integer greater than or equal to x    |
+----------------+------------------------------------------------------------+
| ``abs(x)``     | Returns the absolute value of x                            |
+----------------+------------------------------------------------------------+

In addition, the expression ``dot(x)`` can be used to reference the time
derivative of state variable ``x``.

Conditional statements (if)
===========================
Simple conditional statements can be made using the ``if`` function::

    x = if(V < -50,
        0.2 * exp((V - 12) / 4.7),
        0.5 * exp((V + 19) / 1.2))

Which should be read as::

    if V < -50 then
        x = 0.2 * exp((V - 12) / 4.7)
    else
        x = 0.5 * exp((V + 19) / 1.2)


Piecewise conditional statements
===============================
Conditional statements with more than 1 branch can be made using the
``piecewise`` construct::

    x = piecewise(
        V < -50, 0.2 * exp((V - 12) / 4.7),
        V <   0, 0.5 * exp((V + 19) / 1.2),
        0)

Which should be read as::

    if V < -50 then
        x = 0.2 * exp((V - 12) / 4.7)
    else if V < 0 then
        x = 0.5 * exp((V + 19) / 1.2)
    else
        x = 0

The final "else" part is not optional. If conditions overlap, only the first
condition that evaluates to true will be used.

.. _syntax/template_functions:

User defined functions
======================
A user may define template functions by adding them to the header. User
functions may reference each other but not themselves. The syntax is shown
in the following example::

    [[model]]
    sigmoid(V, Vh, s, lo, hi) = lo + (hi - lo) / (1 + exp((Vh - V) / s))

Interfacing with the outside world
==================================
In many cases, not all variables of interest are contained within the model.
For example if a simulation engine is used to drive the model this engine may
provide a variable ``time``. Other examples of external variables include a
pacing or driving variable or an input current derived from neighbouring cells.

The ``mmt`` syntax allows variables to be *bound* to an external value using
the ``bind`` keyword::

    [environment]
    t = 5 bind time

In this example, the variable ``t`` is defined and given the value 5. However,
when the model is passed to a simulation or export routine that provides the
external source "time", it will know to replace t's value with the appropriate
value (in this case the simulation time) on every iteration. If the routine
doesn't provide a suitable "time" it can simply revert to the default value
``5``. This way, a model can be made suitable for use with different simulation
routines.

Bindings are unique: two variables in the same model cannot be bound to the
same input.

The external sources provided by each simulation engine or export are listed in
their documentation.

Time dependence and pacing
--------------------------
Explicit time dependence is discouraged, but possible in many simulations using
the external source ``time``.

In principle, this variable can be used to pace the model, but there are a
number of problems with this:

1. Conceptually, it makes sense to apply different protocols to the same cell
   model.
2. Pacing tends to be applied in block pulses. Because these are discontinuous,
   there is nothing in their derivatives that indicates to an ODE solver that
   something interesting is about to happen. As a result, the solver may skip
   over the - typically very short - stimuli.

To remedy this, the standard myokit simulation engine has an event-driven
pacing mechanism that can be accessed through the variable ``pace``::

    [stimulus]
    level = 0 bind pace
    amplitude = -25
    istim = level * amplitude

For information on defining a pacing protocol, see the section
:ref:`syntax/protocol`.

Labelling special variables
---------------------------
Some variables in a model have a special meaning that may be relevant to
simulation engines. These can be marked using the ``label`` keyword. For
example, a multi-cell simulation might need to know the membrane potential to
determine the appropriate input current from one cell to the next or a single
cell simulation may wish to calculate the maximum dV/dt.

A typical label is "membrane_potential"::

    [membrane]
    dot(V) = -(I_K + I_Na + I_Ca + I_stim)
        label membrane_potential

A quick syntax for the label construct is provided::

    [membrane]
    dot(V) = -(I_K + I_Na + I_Ca + I_stim) label membrane_potential

Like bindings, label names are unique: a label can only be applied to one
variable per model. In addition, bindings and labels share the same namespace:
the names of labels and bindings cannot overlap.

The labels and bindings supported by simulation engines or exports are listed
in their documentation.

Namespaces and ontologies
-------------------------
At the time of writing, Myokit does not define any ontology providing the names
of labels and bindings. Instead, each simulation engine or experiment specifies
the labels and binds it uses in its documentation.

However, the following two constraints are imposed:

    1. Names of bindings and labels follow the same naming rules as
       unqualified variable names in Myokit.
    2. Labels and bindings share a namespace: The names of external inputs
       (bindings) and labels can not overlap.

References, solvability
=======================
The order in which variables are specified doesn't matter. However, cycles
in the variables' dependencies are not allowed. For the sake of modelling, it
is often nice to have a non-cyclical graph of *component* dependencies, but no
such requirements are made by myokit.

Shorthand syntax
================
Variable units, bindings, labels and descriptions can be written in a shorthand
syntax on the same line as the variable definition. If multiple shorthands are
used, their order is important. The correct order is::

    x = 15 in [ms] bind time label special : comment

Example: Luo-Rudy 1991
======================
What follows is an adaptation of the 1991 Luo-Rudy model for the ventricular
myocyte::

    [[model]]
    name: Luo-Rudy model 1991 (LR91)
    desc: """
          Test implementation of the Luo-Rudy model for the ventricular
          myocyte.
          The original model can be downloaded from http://rudylab.wustl.edu
          """
    # Template functions
    sig(V, Vstar, a, b) = exp(a * (Vstar - V)) / (1 + exp(b * (Vstar - V)))
    # Initial conditions
    membrane.V         = -84.4
    na_fast.m          = 0.0017
    na_fast.h          = 0.98
    na_fast.j          = 0.99
    ca_slow_inward.d   = 0.003
    ca_slow_inward.f   = 0.999
    k_time_dependent.x = 0.042
    ca_slow_inward.Cai = 0.00018

    [engine]
    time = 0 bind time
    pace = 0 bind pace

    [phys]
    R = 8314 [J/kmol/K] : Gas constant
    T = 310 [K] : The cell temperature
    F = 96484.6 [C/mol] : Faraday's constant
    RTF = R * T / F

    [membrane]
    C = 1 [uF/cm^2]
    stim_amplitude = -25.5 [uA/cm^2]
    I_stim = engine.pace * stim_amplitude
    dot(V) = (-1 / C) * (
             I_stim +
             na_fast.i_Na +
             ca_slow_inward.i_si +
             k_time_dependent.i_K +
             k_time_independent.i_K1 +
             k_plateau.i_Kp +
             background_current.i_b )
        label membrane_potential
        desc: The membrane potential
        in [mV]

    [ions]
    Nao = 140 [mmol/L] : External Na+ concentration
    Nai = 18  [mmol/L] : Internal Na+ concentration
    Ki  = 145 [mmol/L] : Internal K+ concentration
    Ko  = 5.4 [mmol/L] : External K+ concentration

    [na_fast]
    use membrane.V
    g_Na = 23 [mS/cm^2]
    E_Na = phys.RTF * log(ions.Nao / ions.Nai)
        desc: Na+ Nernst potential
        in [uF/cm^2]
    i_Na = g_Na * m^3 * h * j * (V - E_Na)
    dot(m) = alpha * (1 - m) - beta * m : m-gate of the fast sodium channel
        alpha = 0.32 * (V + 47.13) / (1 - exp(-0.1 * (V + 47.13)))
        beta = 0.08 * exp(-V / 11)
    dot(h) = alpha * (1 - h) - beta * h : h-gate of the fast sodium channel
        alpha = piecewise(V < -40,
            0.135 * exp((80 + V) / -6.8),
            0
            )
        beta = piecewise(
            V < -40,
            3.56 * exp(0.079 * V) + 310000 * exp(0.35 * V),
            1 / (0.13 * (1 + exp((V + 10.66) / -11.1)))
            )
    dot(j) = alpha * (1 - j) - beta * j : j-gate of the fast sodium channel
        alpha = piecewise(V < -40,
            (-127140 * exp(0.2444 * V) - 0.00003474 * exp(-0.04391 * V))
             * (V + 37.78) / (1 + exp(0.311 * (V + 79.23))),
            0
            )
        beta = piecewise(V < -40,
            0.1212 * exp(-0.01052 * V) / (1 + exp(-0.1378 * (V + 40.14))),
            0.3 * exp(-0.0000002535 * V) / (1 + exp(-0.1 * (V + 32)))
            )

    [ca_slow_inward]
    use membrane.V
    E_si = 7.7 - 13.0287 * log(Cai)
    i_si = 0.09 * d * f * (V - E_si)
    dot(d) = alpha * (1 - d) - beta * d
        alpha = 0.095 * sig(V, 5, 0.01, 0.072)
        beta  = 0.07 * sig(V, -44, 0.017, -0.05)
    dot(f) = alpha * (1 - f) - beta * f
        alpha = 0.012 * sig(V, -28, 0.008, -0.15)
        beta = 0.0065 * sig(V, -30, 0.02, 0.2)
    dot(Cai) = -0.0001 * i_si + 0.07 * (0.0001 - Cai)

    [k_time_dependent]
    use membrane.V
    use ions.Ko, ions.Nao, ions.Ki, ions.Nai
    PR_NaK = 0.01833
    g_K = 0.282 * sqrt(ions.Ko / 5.4)
    E_K = phys.RTF * log((Ko + PR_NaK * Nao) / (Ki + PR_NaK * Nai))
    xi = piecewise(V > -100,
            2.837 * (exp(0.04*(V + 77)) - 1) / ((V + 77)*exp(0.04 * (V + 35))),
            1)
    i_K = g_K * x * xi * (V - E_K)
    dot(x) = alpha * (1 - x) - beta * x
        alpha = 0.0005 * sig(V, -50, -0.083, -0.057)
        beta  = 0.0013 * sig(V, -20, 0.06,  0.04)

    [k_time_independent]
    use membrane.V
    E_K1 = phys.RTF * log(ions.Ko / ions.Ki)
    g_K1 = 0.6047 * sqrt(ions.Ko / 5.4)
    i_K1 = g_K1 * (alpha / (alpha + beta)) * (V - E_K1)
        alpha = 1.02 / (1 + exp(0.2385 * (V - E_K1 - 59.215)))
        beta = (0.49124 * exp(0.08032 * (V - E_K1 + 5.476))
                + exp(0.06175 * (V - E_K1 - 594.31))
               ) / (1 + exp(-0.5143 * (V - E_K1 + 4.753)))

    [k_plateau]
    g_Kp = 0.0183 [mS/cm^2]
    E_Kp = k_time_independent.E_K1
    i_Kp = g_Kp * Kp * (membrane.V - E_Kp)
        Kp = 1 / (1 + exp((7.488 - membrane.V) / 5.98))

    [background_current]
    E_b = -59.87 [mV]
    g_b = 0.03921 [mS/cm^2]
    i_b = g_b * (membrane.V - E_b)
