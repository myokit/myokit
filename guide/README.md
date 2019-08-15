# Using Myokit

This page, lists _guide notebooks_ showing how Myokit can be used in a variety of applications, ranging from cellular to sub-cellular to tissue simulations.

Please note this is very much a work in progress, and many of the items on the list are yet to be filled in.


# IDEA: The RST docs describe everything bottom-up, from a Myokit perspective.
# These guides describe everything from an application point of view
# Guides should link to the docs wherever needed

# Guides are NOT BOTTOM-UP, can use things NOT YET EXPLAINED IN GUIDES

**Important: Do simulation first, model syntax later (it's pretty self-explanatory, and most people don't write models!)**

1. Running a single cell simulation
    - Starting/stopping
    - Pre-pacing and resetting
    - Different log options (names, existing log, constants, derivatives)
    - Different timing options (free, dt, explicit times)

X. Using the model API
    - Adding variables
    - Plotting with pyfunc
    - Manipulating models
    - Manipulating equations (variable, eq, lhs, rhs, derivatives, refs_by, refs_to)

X. Importing from CellML

X. Using the IDE
    - Graphing variables
    - Show variable info / evaluation
    - Show variable users and dependencies
    - Graph component dependencies
    - Graph "state dependency matrix"


X. Simulating a 1d strand
    - No OpenCL
    - With OpenCL
    - With different cell types
    - With heterogeneity
X. Simulating 2d tissue
    - Displaying with block
X. Simulating arbitrary shapes
    - Connections

X. Running single current simulations
    - CVODE sim
    - HH
    - Markov
    - Protocol options
    - Data clamp


- Creating pacing protocols
    - MMT syntax
    - API
    - Factory
    - Data clamp
    
- Formats
    - Importing models
    - Exporting models and simulations
    - Importing/exporting patch clamp data
























### Getting started

- Model, protocol, and script (link to syntax document)
- Using the explorer

### Using the IDE

### Using scripts
- running a simulation without pre-pacing (using the IDE)
- logging and plotting (link to numpy/matplotlib bits)
- pre-pacing, resetting
- partial runs, stopping and restarting a simulation
- creating pacing protocols (pacing factory, bmp2bcl)
- calculating apds
- creating apd vs pcl diagrams
- Accessing and changing model variables
- Graphing variables using pyfunc

### Converting formats
- Exporting for presentations: latex / html
- Exporting runnables: matlab, C, cuda
- Importing from CellML (and converting protocols)
- Importing protocols from ABF

### Separating script and models
- Writing scripts without a model in the IDE
- Writing scripts without a model in Python

### Ion channels
- Creating a step protocol (pacing factory)
- Markov models (including single-channel sim)
- Estimating ion channel parameters

### Multi-cellular simulation
- Cable sim
- OpenCL simulation
- FiberTissue simulation

### Advanced simulation types
- PSim
- ICSim etc.


### Appendix B: Working with external packages
- Matplotlib basics (see current docs)
- NumPy basics (and log.npview())

