*What follows below is very much a work in progress!*

*More examples can be found on:* http://myokit.org/examples/

# Using Myokit

These example notebooks showing how Myokit can be used in a variety of applications, ranging from cellular to sub-cellular to tissue simulations.
They accompany the detailed Myokit (API) documentation provided on [https://myokit.readthedocs.io](https://myokit.readthedocs.io).

## Running single cell simulations

1. [Simulating an action potential](./1-1-simulating-an-action-potential.ipynb)
    - Loading a model, protocol, and script
    - Creating a simulation
    - Running a simulation
    - Plotting simulation results with matplotlib

## To-do

2. [Logging simulation results](1-2-logging-simulation-results.ipynb)
    - [ ] Selecting variable by name
    - [ ] Logging derivatives
    - [ ] Using logging flags
    - [ ] Continuing on from a previous simulation
    - [ ] Storing results to disk
    - [ ] Selecting which points to log

3. [Starting, stopping, pre-pacing, and loops](1-3-starting-stopping.ipynb)
    - [ ] Starting and stoppping simulations
    - [ ] Pre-pacing to a "steady state"
    - [ ] Simulating the effects of parameter changes

4. Exploring models in the IDE
    - [ ] Script in IDE vs script in Python
    - [ ] MMT syntax (link to ref)
    - [ ] Run (w. F6)
    - [ ] Component explorer
    - [ ] Graphing variables (Ctrl+G)
    - [ ] Show variable info / evaluation
    - [ ] Show variable users and dependencies
    - [ ] Graph component dependencies
    - [ ] Graph "state dependency matrix"

5. [Simulating a pharmacokinetic model with sensitivities](./repeated_bolus_infusion.ipynb)
    - Defining a model with Myokit's model building API
    - Define dosing schedule
    - Define sensitivities
    - Compare simulation results to analytic solution

0. Implementing models
    - [ ] Comparing models with step
    - [ ] Unit checking
    - [ ] State dep matrix
    - [ ] IDE shortcuts, variable graphing
    - [ ] Interconnected components?
0. Analysing model structure: see above
0. Analysing model output: common plots
    - [ ] Cumulative current plots
    - [ ] More things from lib.plots ?

0. Modifying models using the API
    - [ ] Adding variables
    - [ ] Plotting with pyfunc
    - [ ] Manipulating models
    - [ ] Manipulating equations (variable, eq, lhs, rhs, derivatives, refs_by, refs_to)

0. Pacing protocols for AP models
    - [ ] MMT syntax
    - [ ] API
    - [ ] pacing factories
    - [ ] AP clamp
    - [ ] Models without pacing (Purkinje)

0. Post-processing single-cell results: APD calculations
    - [ ] APD calculation
    - [ ] Restitution
    - [ ] Alternans

0. Advanced simulation types
    - [ ] PSim
    - [ ] ICSim etc.

0. Writing reproducible code
    - [ ] Make changes to model dynamically
    - [ ] Unit conversion
    - [ ] Annotated variables? and lib.guess
    - [ ] Oxmeta/WL integration?
    - [ ] lib.multi?

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

## Ion current simulations

0. Running single current simulations
    - [ ] Creating a step protocol (pacing factory)
    - [ ] CVODES sim
    - [ ] HH
    - [ ] Markov
    - [ ] Protocol options
    - [ ] Data clamp

0. Examples of fitting ionic currents and fitting conductances: https://github.com/pints-team/myokit-pints-examples

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

## Technical notes

1. Pacing
2. Logging in simulations
3. Multi-cell simulations
4. Ion channel simulations
X. Autodiff simulations

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
    - [ ] Contributing.md

