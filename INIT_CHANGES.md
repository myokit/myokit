Trying to write out the full scope of the changes below, with an eye to reuse in release notes

# Changes for users

In Myokit versions before 1.34.0, a model's initial values were represented internally as numbers (although it was allowed to specify them using a numbers-only expression like 'membrane.V = -80 + 1`).
This allowed you to specify systems of ODEs as:
```
dy/dt = f(y, t, p)
y(t=t0) = y0
```
where `y` is the state, `t` is the time variable, and `p` is the set of all time-invariant variables (i.e. everything that isn't a state, a bound variable, or something that depends on a state or bound variable).
The value `t0` is an unspecified time when the state equals the initial conditions.

Starting from version 1.34, a model's initial values are stored as expressions, which are allowed to refer to constant-valued variables:
```
dy/dt = f(y, t, p)
y(t=0) = g(p)
```

## Model API

- The `Model` methods `state()` and `set_state()` are deprecated in favour of `initial_values` and `set_initial_values` which handle both floats and expressions. Instead of `Model.inits()` you can now use `Model.initial_values(as_equations=True)`.
- The `Variable` methods `state_value()` and `set_state_value()` are now deprecated in favour of `initial_value()` and `set_initial_value()`, which can handle both floats and expressions.
- The method to create states, `Variable.promote()`, now handles expressions.

- TODO THINK ABOUT FORMAT STATE, LOAD_STATE, SAVE_STATE
- TODO THINK ABOUT MAP TO STATE 

A full overview is given in the [changelog](https://github.com/myokit/myokit/blob/main/CHANGELOG.md).

## Unit checking

Before version 1.34 initial values were never unit checked.
Starting from version 1.34, initial value expressions that reference variables will be unit checked.

```
component.a = 1                 # Not unit checked before or after 1.34
component.b = 1 + 1             # Not unit checked before or after 1.34
component.c = component.x       # Unit checked in 1.34, invalid before
component.d = 1 / component.x   # Unit checked in 1.34, invalid before
```

## Simulations

Starting from version 1.34, a simulation's _default state_ is the model's initial state, which may contain expressions:
```
# Create a model where the initial value of x depends on y

model = myokit.parse_model('''
[[model]]
c.x = 1 + c.y

[c]
dot(x) = 0.1
y = 2
''')

sim = myokit.Simulation(model)
for value in sim.default_state():
    print(value)
```
will result in `myokit.Expression[1 + c.y]`, while 
```
print('Original')
for value in sim.state():
    print(value)
    
print('Modified')
sim.set_constant('c.y', 10)
```
will show
```
What should this show? Should state=None initially, and then it gets evaluated
on-the-fly when we call state()?
```

If we run the simulation, its state will deviate from the default state:
```
sim.run(10)

print('New state:')
for value in sim.state():
    print(value)
    
print('The state no longer depends on c.y:')
sim.set_constant('c.y', 10)
```

Even if we change the time back to 0:
```
sim.set_time(0)

print('Still the same state:')
for value in sim.state():
    print(value)
    
print('And it does not depend on c.y:')
sim.set_constant('c.y', 20)
```
shows
```
```

Using `reset()` will reset a model to `t=0` and to its intial state:
```
sim.reset()

print('Back to the initial state:')
for value in sim.state():
    print(value)
    
print('Which depends on c.y:')
sim.set_constant('c.y', 30)
for value in sim.state():
    print(value)
```
shows
```
```

However, if we change the default state with `set_default_state` or by using `pre()`, the connection to the model's initial state will be lost:
```
sim.pre(10)

print('The default state no longer depends on c.y:')
for value in sim.default_state():
    print(value)
```
shows
```
```



### Simulation

The `Simulation` class has full support for variables in initial expressions.

#### Simulation with sensitivities

Sensitivities can only be calculated with respect to expressions that do not reference other variables (i.e. expressions for which `is_literal()` is True).
Before 1.34, all initial values were literal, by definition, but starting in 1.34 you might get an error when trying to calculate sensitivities for non-literal initial values:

```
model = myokit.parse_model('''
[[model]]
c.x = 3
c.y = c.p / 2

[c]
dot(x) = 1
dot(y) = -1
p = 32
''')

print('This is OK, because init(c.x) is literal:')
sim = myokit.Simulation(model, sensitivities=(['c.x'], ['init(c.x)']))

print('This is OK, because c.p is literal:')
sim = myokit.Simulation(model, sensitivities=(['c.y'], ['c.p']))

print('This is not OK, because init(c.y) is not literal:')
sim = myokit.Simulation(model, sensitivities=(['c.y'], ['init(c.y)']))
```

### SimulationOpenCL and FiberTissueSimulation

Not sure!

### Simulation1d

Not sure!

### Ion channel simulations

Not sure!

- `lib.hh.AnalyticalSimulation`
- `lib.markov.AnalyticalSimulation`
- `lib.markov.DiscreteSimulation`

### Compiled, model-dependent, but not simulations

Not sure!

- `JacobianTracer`
- `JacobianCalculator`
- `RhsBenchmarker`

### Legacy sims

Should probably just remove these now!

- `LegacySimulation`
- `PSimulation`
- `ICSimulation`

## Exports

### Ansi C

- Euler sim: not sure!
- CVODE sim: not sure!
- Cable sim: not sure!

### CellML

Reduce to numbers for now: do in separate ticket (import too!)

### HTML, XML, Latex

Should be very easy to output the expressions!

### CUDA and OpenCL

Not sure!

### EasyML

Don't think it supports it?
https://opencarp.org/documentation/examples/01_ep_single_cell/05_easyml

### Matlab

Not sure! Best look at code.

### Python

Not sure! Best look at code.

### Stan

Not sure if it supports it!
Think not: https://mc-stan.org/docs/2_19/stan-users-guide/solving-a-system-of-linear-odes-using-a-matrix-exponential.html

## Imports

### CellML

Seperate ticket!

### SBML

Probably supports it? Ask David?
We only import, so if it's supported it can be a separate ticket.

### ChannelML

Probably doesn't support it? Ignore!

# Internal stuff

## Cycle checking

Initial values can now depend on variables, but variables cannot depend on initial values.
- This means that cycle checking does not need to be updated.
- However, operations that work with initial values may now need to check model validity before starting.

## Used-variable checking

It should now be an error to delete a variable that is referenced in an initial value.
This means that the variable dependency counting system will need updating.

## CModel

Will probably find what needs to change when working on cvodessim...

At least:
- Needs to check that sensitivities wrt inits are literal (just like wrt variables)

# To-do

## Tests for model API

- [ ] Model parsing with expressions (always in global context)
- [ ] Model parsing can raise `NonConstantValueError`
- [ ] `Model.initial_values` (floats, expr, or eqs)
- [ ] `Model.set_initial_values` (takes lots of input args, if string then parsed w global context, can raise `NonConstantValueError`)
- [ ] Work out what to do with `map_to_state` (again)
- [ ] `Variable.initial_value` (float or expr)
- [ ] `Variable.set_initial_value` (takes lots of input args, if string then parsed w global context, can raise `NonConstantValueError`)
- [ ] `Variable.promote` with new possible input args (via `set_initial_value`?).
- [ ] Deprecation warning from `Model.state` and date in comment in the code
- [ ] Deprecation warning from `Model.set_state` and date in comment in the code
- [ ] Deprecation warning from `Model.inits` and date in comment in the code
- [ ] Deprecation warning from `Variable.state_value` and date in comment in the code
- [ ] Deprecation warning from `Variable.set_state_value` and date in comment in the code
- [ ] Deprecation warning from `Model.state` and date in comment in the code
- [ ] Work out which methods can raise cyclical errors (e.g. converting initial_values to floats) and add tests to check that they detect them.
- [ ] Add tests to check that a variable can't be deleted if it's used in an initial value
- [ ] Add tests for self-ref in initial values (`c.x = c.x`, `c.x = 1 + c.x`).

## Tests for unit checking

- [ ] `component.a = 1` Not unit checked before or after 1.34
- [ ] `component.b = 1 + 1`  Not unit checked before or after 1.34
- [ ] `component.c = component.x` Unit checked in 1.34, invalid before
- [ ] `component.d = 1 / component.x` Unit checked in 1.34, invalid before

## Tests for cvodes sim

See situations above. Add trickier if we can think of them?

Add checks for refs to non-literal inits in CModel and test them.

## Tests for other sims

- [ ] `SimulationOpenCL` Decide on support. Copy cvodessim tests or test that warning is raised when non-literal is "downgraded".
- [ ] `FiberTissueSimulation` Decide on support. Copy cvodessim tests or test that warning is raised when non-literal is "downgraded".
- [ ] `Simulation1d` Decide on support. Copy cvodessim tests or test that warning is raised when non-literal is "downgraded".
- [ ] `lib.hh.AnalyticalSimulation` Decide on support. Copy cvodessim tests or test that warning is raised when non-literal is "downgraded".
- [ ] `lib.markov.AnalyticalSimulation` Decide on support. Copy cvodessim tests or test that warning is raised when non-literal is "downgraded".
- [ ] `lib.markov.DiscreteSimulation` Decide on support. Copy cvodessim tests or test that warning is raised when non-literal is "downgraded".
- [ ] `JacobianTracer` Check if inits are used, then as above.
- [ ] `JacobianCalculator` Check if inits are used, then as above.
- [ ] `RhsBenchmarker` Check if inits are used, then as above.
- [ ] `LegacySimulation` Remove in separate PR.
- [ ] `PSimulation` Remove in separate PR.
- [ ] `ICSimulation` Remove in separate PR.

## Exports with proper testing

- [ ] CellML 1: Test that they are reduced to numbers for now.
- [ ] CellML 2: Test that they are reduced to numbers for now.
- [x] SBML: No export!

Not sure if these have it yet, but is easy to add:

- [ ] Add test to check that HTML export works and shows expressions.
- [ ] Add test to check that XML export works and shows expressions.
- [ ] Add test to check that LATEX export works and shows expressions.

## Exports with shallow testing

- [ ] Ansi C Euler sim. Implement if easy else convert to floats.
- [ ] Ansi CVODE sim. Implement if easy else convert to floats.
- [ ] Ansi cable sim. Implement if easy else convert to floats.
- [ ] CUDA. Convert to floats without warning. (OR WITH WARNING?)
- [ ] OpenCL. Convert to floats without warning. (OR WITH WARNING?)
- [ ] EasyML. Convert to floats without warning. (OR WITH WARNING?)
- [ ] Matlab. Convert to floats without warning. (OR WITH WARNING?)
- [ ] Python. Convert to floats without warning. (OR WITH WARNING?)
- [ ] Stan. Convert to floats without warning. (OR WITH WARNING?)

## Imports

Nothing to do!
