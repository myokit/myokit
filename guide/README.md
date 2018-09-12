# Using Myokit

There are several ways to use Myokit.
On this page, you'll find links to "guides" covering a variety of topics, ranging from cellular to sub-cellular to tissue simulations.

Please note this is very much a work in progress, and many of the items on the list are yet to be filled in.

### Getting started
- Installation (covers: installation basics, details in appendix)
- Running an example from the website
- Model, protocol, and script (link to syntax document)
- Using the explorer

### Using the IDE
- Graphing variables
- Show variable info / evaluation
- Show variable users and dependencies
- Graph component dependencies
- Graph "state dependency matrix"

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

### Appendix A: Installation guides
- Easy Linux installation
- Easy Windows installation
- Easy OX/S installation
- Installation on any platform
- Configuration files (covers: location of config files, changing them manually, `myokit reset`)
- Installing CVODE (covers: CVODE install, testing for CVODE support)
- Installing OpenCL (covers: OpenCL, testing for OpenCL support, selecting OpenCL device)

### Appendix B: Working with external packages
- Matplotlib basics (see current docs)
- NumPy basics (and log.npview())

