# Using Myokit

This page lists example notebooks showing how Myokit can be used in a variety of applications, ranging from cellular to sub-cellular to tissue simulations.
They accompany the full Myokit documentation provided on [https://myokit.readthedocs.io](https://myokit.readthedocs.io).



Please note this page is still a work in progress, and many more examples are yet to be added



## Running single cell simulations

1. [Simulating an action potential](./1-1-simulating-an-action-potential.ipynb)
    - Loading a model, protocol, and script
    - Creating a simulation
    - Running a simulation
    - Plotting simulation results

2. [Logging simulation results](1-2-logging-simulation-results.ipynb)
    - Selecting variable by name
    - Logging derivatives
    - Using logging flags
    - Continuing on from a previous simulation
    - Storing results to disk

3. [Starting, stopping, pre-pacing, and loops](1-3-starting-stopping.ipynb)
    - Starting and stoppping simulations
    - Pre-pacing to a "steady state"
    - Exploring the effects of parameter changing
    
4. Exploring AP models
    - MMT syntax (link to ref)
    - Graphing variables and other MMT tricks
    - Modifying models using the API

5. Pacing protocols for AP models
    - MMT syntax
    - AP clamp

5. Post-processing and 
    - APD calculation
    - Restitution
    - Alternans









## Somewhere down the line

Examples of fitting ionic currents and fitting conductances: https://github.com/pints-team/myokit-pints-examples
