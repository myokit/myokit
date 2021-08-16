*What follows below is very much a work in progress!*

*More examples can be found on:* http://myokit.org/examples/

# Using Myokit

These example notebooks showing how Myokit can be used in a variety of applications, ranging from cellular to sub-cellular to tissue simulations.
They accompany the detailed Myokit (API) documentation provided on [https://myokit.readthedocs.io](https://myokit.readthedocs.io).

## Running simulations

1. Demo

2. Model syntax
    - [ ] Model, comp, var, nested var
    - [ ] Alias
    - [ ] Units (number vs in, checking)
    - [ ] Use func?
    - [ ] Binding & labels
    - [ ] Link to full

4. Using the IDE
    - [ ] Script in IDE vs script in Python
    - [ ] Run (w. F6)
    - [ ] Component explorer
    - [ ] Graphing variables (Ctrl+G)
    - [ ] Graph component and variable dependencies
    - [ ] Graph "state dependency matrix"


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


5. Solver
    - [ ] Sim errors
    - [ ] Step tolerance
    - [ ] Set max time step

6. Protocols and syntax
    - [ ] MMT syntax, link to full
    - [ ] API
    - [ ] pacing factories
    - [ ] AP clamp
    - [ ] Models without pacing (Purkinje)

7. Post-processing single-cell results
    - [ ] APD calculation
    - [ ] Restitution
    - [ ] Alternans
    - [ ] Cumulative current plots
    - [ ] More things from lib.plots ?

## Ion current simulations

0. Pacing protocols for
    - [ ] Creating a step protocol in mmt (``next``)
    - [ ] Plotting it
    - [ ] is_sequence etc,
    - [ ] with add_step
    - [ ] with pacing factory
    - [ ] With fancy bits
    - [ ] Data clamp

0. Running single current simulations
    - [ ] CVODES sim
    - [ ] HH
    - [ ] Markov

0. Examples of fitting ionic currents and fitting conductances: [ion channel fitting tutorial](https://github.com/pints-team/myokit-pints-examples)

## Multi-cell simulations

0. Simulating a 1d strand
    - [ ] No OpenCL
    - [ ] With OpenCL
    - [ ] With different cell types (field approach)
    - [ ] With heterogeneity

0. Simulating 2d tissue
    - [ ] with heterogeneity (field approach)
    - [ ] Displaying with block viewer
    - [ ] With different cell types (FiberTissue)

0. Simulating arbitrary shapes
    - [ ] Connections

## Working with models

0. Implementing models
    - [ ] Comparing models with step
    - [ ] Unit checking
    - [ ] State dep matrix
    - [ ] Show variable info / evaluation
    - [ ] Show variable users and dependencies
    - [ ] Interconnected components?

0. Modifying models using the API
    - [ ] Adding variables
    - [ ] Plotting with pyfunc
    - [ ] Manipulating models
    - [ ] Manipulating equations (variable, eq, lhs, rhs, derivatives, refs_by, refs_to)

0. Working with multiple models
    - [ ] Make changes to model dynamically
    - [ ] Unit conversion
    - [ ] Annotated variables? and lib.guess
    - [ ] Oxmeta/WL integration?
    - [ ] lib.multi?

## Importing and exporting

0. Using CellML
    - [ ] Importing
    - [ ] Exporting
    - [ ] Auto stimulus, vs hardcoded ?
    - [ ] Using APIs ???

0. Importing models from other formats
    - [ ] SBML
    - [ ] ChannelML
    - Not really enough to talk about?

0. Exporting runnable code
    - [ ] matlab, C, cuda
    - [ ] Import isn't possible

0. Exporting presentation formats
    - [ ] Exporting for presentations: latex / html

0. Importing data
    - [ ] Importing patch clamp data
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

The "technical notes" are a series of notebooks that explain or define some of the trickier parts in Myokit.
They are used in developing Myokit, and to document decisions made along the way.
They have not been reviewed or checked extensively, so some errors may be present.

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

