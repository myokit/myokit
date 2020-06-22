.. _guide/model:

***************
Model structure
***************

.. currentmodule:: myokit

The core of a myokit :class:`model <Model>` is a set of :class:`variables
<Variable>` and the equations that define them. For convenience, variables are
grouped together in :class:`components <Component>`. Variables, in turn, can
have nested variables of their own, hidden from the rest of the model to avoid
cluttering up the namespace.

Myokit was built to solve ODE systems: it assumes the current state of a model
can be accuratly described using a set of variables - the state - and a set of
equations describing the derivatives of these state variables.

As a result, a variable in myokit can have one of three characters:

1. A state variable. This variable is defined by the equation for its
   derivative and an initial (or current) value stored in the Model class
   itself. The value of a state variable is updated by the ODE solving routine
   at each iteration.

   A state variable may never be nested.

2. A (physical) constant or parameter. These are variables whose value does not
   change *during the course of a simulation*. Myokit determines these values
   implicitly, by inspecting the variables defining equations.

3. Values that aren't states or constants are called intermediate values. For
   example, in a typical cardiac cell model all currents are intermediate
   values. Myocyte models are slightly unusual in that most state variables are
   of little interest compared to the intermediate values.

To communicate with the outside world (e.g. the simulation engine), variables
can be bound to external inputs. For example, explicit time dependence can be
implemented by binding a variable to the value "time" This variable is then
updated by the simulation engine to have the correct value at every simulation
step.

Defining equations
------------------
A variable in myokit has one or more defining equations: State variables
define a time derivative and an initial value, all other variables define a
value.
::

    # State variable, two defining equations
    x = 1
    dot(x) = 0.5 * sqrt(x)

    # Ordinary variable, defined directly
    y = 4 * x

Names, qnames and unames
------------------------
Each component or variable has a name that should start with an ascii letter
(a-zA-Z) and contain only alphanumerical characters or underscores
(a-ZA-Z0-9\_).

A *fully qualified name* (or simply ``qname``) lists the name of a variable
including all its parents' names, until a component is reached. For example,
the variable ``V`` in the component ``membrane`` has qname ``membrane.V``.
Similarly, a nested variable ``alpha`` belonging to ``m`` in the component
``ina`` has qname ``ina.m.alpha``.

To facilitate the generation of source code in various languages, a ``uname``
is created for all variables whenever a model is generated. This name does not
contain any periods (.) and is guaranteed to be unique within the model.

To avoid conflicts between unames and language keywords a function
:func:`Model.reserve_unique_names` is defined. Any keywords reserved using this
function will not appear as unames.
