*What follows below is very much a work in progress!*

*More examples can be found on:* http://myokit.org/examples/

# Using Myokit

These example notebooks showing how Myokit can be used in a variety of applications, ranging from cellular to sub-cellular to tissue simulations.
They accompany the detailed Myokit (API) documentation provided on [https://myokit.readthedocs.io](https://myokit.readthedocs.io).

## Running simulations

1. [Simulating an action potential](https://nbviewer.jupyter.org/github/MichaelClerx/myokit/blob/main/examples/1-1-simulating-an-action-potential.ipynb)
    - Loading a model, protocol, and script
    - Creating a simulation
    - Running a simulation
    - Plotting simulation results with matplotlib

2. [Logging simulation results](https://nbviewer.jupyter.org/github/MichaelClerx/myokit/blob/main/examples/1-2-logging-simulation-results.ipynb)
    - [ ] Selecting variable by name
    - [ ] Logging derivatives
    - [ ] Using logging flags
    - [ ] Continuing on from a previous simulation
    - [ ] Selecting which points to log
    - [ ] Storing results to disk

3. [Starting, stopping, pre-pacing, and loops](https://nbviewer.jupyter.org/github/MichaelClerx/myokit/blob/main/examples/1-3-starting-stopping.ipynb)
    - [ ] Starting and stoppping simulations
    - [ ] Pre-pacing to a "steady state"
    - [ ] Simulating the effects of parameter changes

4. Controlling the solver
    - [ ] Sim errors
    - [ ] Step tolerance
    - [ ] Set max time step

4. Using the IDE
    - [ ] Script in IDE vs script in Python
    - [ ] Run (w. F6)
    - [ ] Eval eq., var info
    - [ ] Graphing variables (Ctrl+G)
    - [ ] Graph component and variable dependencies
    - [ ] Graph "state dependency matrix"

6. Periodic pacing protocols
    - [ ] MMT syntax, link to full
    - [ ] API
    - [ ] pacing factories
    - [ ] AP clamp
    - [ ] Models without pacing (Purkinje)

## Single-cell simulations

0. Calculating APDs
    - [ ] APD calculation
    - [ ] Restitution
    - [ ] Alternans

0. Pre-pacing to steady state

0. Strenght-duration curves

0. Analysing currents
    - [ ] Cumulative current plots
    - [ ] More things from lib.plots ?

0. Sensitivities

## Ion current simulations

0. Voltage-step protocols
    - [ ] Creating a step protocol in mmt (``next``)
    - [ ] Plotting it (fitting tutorial!)
    - [ ] is_sequence etc,
    - [ ] with add_step
    - [ ] with pacing factory
    - Link to fitting tutorial. Or even move those bits here?

0. Running single current simulations
    - [ ] CVODES sim
    - [ ] HH
    - [ ] Converting HH model forms
    - [ ] Markov (analytical)
    - [ ] Markov (discrete)

0. Examples of fitting ionic currents and fitting conductances: [ion channel fitting tutorial](https://github.com/pints-team/myokit-pints-examples)

## Multi-cell simulations

0. Simulating strand and tissue
    - [ ] 1d, no OpenCL, binding
    - [ ] Step size!
    - [ ] 1d, OpenCL
    - [ ] OpenCL info & select
    - [ ] Setting step size (convergence)
    - [ ] 2d, OpenCL

0. Viewing multi-cell simulation results
    - [ ] Storing CSV log
    - [ ] Converting to block
    - [ ] Writing block (txt vs zip)
    - [ ] Displaying with block viewer
    - [ ] Movies

0. Running simulations
    - [ ] Setting step sizes again!
    - [ ] Using find_nan (automatically)
    - [ ] Using a progress reporter

0. Simulating with heterogeneity
    - [ ] Scalar field
    - [ ] With different cell types (field approach)
    - [ ] Conductance field

0. Simulating arbitrary networks
    - [ ] set_connections

## Working with models

0. Model syntax
    - [ ] Model, comp, var, nested var
    - [ ] Alias
    - [ ] Units (number vs in, checking)
    - [ ] Use func?
    - [ ] Binding & labels
    - [ ] Link to full

0. Implementing models
    - [ ] Comparing models with step
    - [ ] Unit checking
    - [ ] State dep matrix
    - [ ] Show variable info / evaluation
    - [ ] Show variable users and dependencies
    - [ ] Interconnected components?

0. Modifying models using the API
    - [ ] Adding variables
    - [ ] Getting functions with pyfunc
    - [ ] Manipulating models
    - [ ] Manipulating equations (variable, eq, lhs, rhs, derivatives, refs_by, refs_to)

0. Units
    - [ ] Unit objects
    - [ ] Predefined units
    - [ ] Quantities
    - [ ] Unit conversion

0. Working with multiple models
    - [ ] Labels (annotated variables)
    - [ ] lib.guess
    - [ ] Unit conversion (again)
    - [ ] freezing variables
    - [ ] importing components
    - [ ] Oxmeta/WL integration?

## Importing and exporting

0. Using CellML
    - [ ] Importing
    - [ ] Exporting
    - [ ] Auto stimulus, vs hardcoded ?
    - [ ] Using APIs ???

0. More model formats
    - [ ] SBML
    - [ ] ChannelML
    - [ ] easyml, stan

0. Exporting runnable code
    - [ ] matlab, C, C++, python
    - [ ] opencl, cuda
    - [ ] Import isn't possible

0. Exporting presentation formats
    - [ ] Exporting for presentations: latex / html

0. Data formats
    - [ ] Importing patch clamp data
    - [ ] DataLog viewer
    - [ ] Importing protocols from ABF
    - [ ] Exporting patch clamp protocols? (ATF)

## Appendix

0. DataLog viewer

0. DataBlock viewer

0. Graph Data Extractor

0. Matplotlib basics, see https://myokit.readthedocs.io/guide/matplotlib.html
    - [ ] Base on from https://myokit.readthedocs.io/guide/matplotlib.html
    - [ ] Show simple example, but with axes etc.
    - [ ] Then with subplots, and subplots_adjust
    - [ ] Then with gridspec
    - [ ] Then stop.

0. Using numpy
    - [ ] Discuss log.npview() ?
    - [ ] Just show an example
    - [ ] And link to https://docs.scipy.org/doc/numpy/user/numpy-for-matlab-users.html

0. Developing Myokit
    - [ ] Yes please!
    - [ ] Github issues
    - [ ] Contributing.md (includes code layout)
    - [ ] Technical notes

## Technical notes

This section contains notebooks that explain or define some of the trickier parts in Myokit.
They are used in Myokit development, and document tricky decisions made along the way.
These notebooks have not been reviewed or checked extensively, so some errors may be present.

1. [Pacing](https://nbviewer.jupyter.org/github/MichaelClerx/myokit/blob/main/examples/t1-pacing.ipynb)
2. [Logging](https://nbviewer.jupyter.org/github/MichaelClerx/myokit/blob/main/examples/t2-logging.ipynb)
3. [CVODE(s) single-cell simulations](https://nbviewer.jupyter.org/github/MichaelClerx/myokit/blob/main/examples/t3-cvodes-simulation.ipynb)
4. [OpenCL multi-cell simulations](https://nbviewer.jupyter.org/github/MichaelClerx/myokit/blob/main/examples/t4-opencl-simulation.ipynb)
5. [HH channel models](https://nbviewer.jupyter.org/github/MichaelClerx/myokit/blob/main/examples/t5-hh-channels.ipynb)
6. [Markov channel models](https://nbviewer.jupyter.org/github/MichaelClerx/myokit/blob/main/examples/t6-markov-channels.ipynb)
7. [Rush-Larsen updates](https://nbviewer.jupyter.org/github/MichaelClerx/myokit/blob/main/examples/t7-rush-larsen.ipynb)

- [Simulation test case: Simple model](https://nbviewer.jupyter.org/github/MichaelClerx/myokit/blob/main/examples/tA-test-case-simple.ipynb)
- Simulation test case: HH ion channel model
- [Simulation test case: PK model](https://nbviewer.jupyter.org/github/MichaelClerx/myokit/blob/main/examples/tC-test-case-pk-model.ipynb)
- [Autodiff simulations](https://nbviewer.jupyter.org/github/MichaelClerx/myokit/blob/main/examples/tZ-autodiff.ipynb)

