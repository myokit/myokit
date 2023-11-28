[![Ubuntu unit tests](https://github.com/myokit/myokit/actions/workflows/unit-tests-ubuntu.yml/badge.svg)](https://github.com/myokit/myokit/actions/workflows/unit-tests-ubuntu.yml)
[![MacOS unit tests](https://github.com/myokit/myokit/actions/workflows/unit-tests-macos.yml/badge.svg)](https://github.com/myokit/myokit/actions/workflows/unit-tests-macos.yml)
[![Windows unit tests](https://github.com/myokit/myokit/actions/workflows/unit-tests-windows.yml/badge.svg)](https://github.com/myokit/myokit/actions/workflows/unit-tests-windows.yml)
[![Windows Miniconda test](https://github.com/myokit/myokit/actions/workflows/unit-tests-windows-miniconda.yml/badge.svg)](https://github.com/myokit/myokit/actions/workflows/unit-tests-windows-miniconda.yml)
[![codecov](https://codecov.io/gh/myokit/myokit/branch/main/graph/badge.svg)](https://codecov.io/gh/myokit/myokit)
[![Documentation Status](https://readthedocs.org/projects/myokit/badge/?version=latest)](https://myokit.readthedocs.io/?badge=latest)

![Myokit](http://myokit.org/static/img/logo.png)

[Myokit](http://myokit.org) is a tool for modeling and simulation of cardiac cellular electrophysiology.
It's [open-source](https://github.com/myokit/myokit/blob/main/LICENSE.txt), written in Python, hosted on [GitHub](https://github.com/myokit/myokit/) and available on [PyPi](https://pypi.org/project/myokit/).
For the latest documentation, see [myokit.readthedocs.io](https://myokit.readthedocs.io/).

More information, including examples and an installation guide, is available on [myokit.org](http://myokit.org).
A list of changes introduced in each Myokit release is provided in the [Changelog](https://github.com/myokit/myokit/blob/main/CHANGELOG.md).


## Install

For full installation details (on linux, mac, or windows), please see [http://myokit.org/install](http://myokit.org/install).
A shorter installation guide for experienced users is given below.

To install Myokit, using PyQt5 for Myokit's GUI components, run:

    pip install myokit[pyqt]
    
to use PySide2 instead, run:
    
    pip install myokit[pyside]
    
If you're not planning to use the GUI components (for example to run simulations on a server), you can simply install with

    pip install myokit

On Linux and Windows, start menu icons can be added by running

    python -m myokit icons

To run single-cell simulations, [CVODES](https://computation.llnl.gov/projects/sundials/sundials-software) must be installed (but Windows users can skip this step, as binaries are included in the pip install).
In addition, Myokit needs a working C/C++ compiler to be present on the system.

Existing Myokit installations can be upgraded using

    pip install --upgrade myokit


## Quick-start guide

After installation, to quickly test if Myokit works, type

    python -m myokit run example
    
or simply

    myokit run example
    
To open an IDE window, type

    myokit ide

To see what else Myokit can do, type

    myokit -h
    

## Contributing to Myokit

You can contribute to Myokit by [asking questions](https://github.com/myokit/myokit/discussions), [reporting issues](https://github.com/myokit/myokit/issues), or contributing  code!
Detailed instructions on writing code for Myokit are found in [CONTRIBUTING.md](./CONTRIBUTING.md), but before doing anything, open [an issue](https://github.com/myokit/myokit/issues) where we can discuss what can and should be done.

A high-level plan for Myokit's future is provided in the [roadmap](./ROADMAP.md).

### Meet the team!

Myokit developed is driven by a [team](https://github.com/orgs/myokit/people) at the Universities of Nottingham, Oxford, and Macao, led by Michael Clerx (michael[at]myokit.org).
It has an external advisory board composed of Jordi Heijman (Maastricht University), Trine Krogh-Madsen (Weill Cornell Medicine), and David Gavaghan (Oxford).


## Citing Myokit

If you use Myokit in your research, please cite it using the information in our [CITATION file](https://github.com/myokit/myokit/blob/main/CITATION).

We like to [keep track of who's using Myokit](http://myokit.org/publications/) for research (based on publications) and teaching (based on peronsal correspondence).
If you've used Myokit in teaching, we're always happy to hear about it so please get in touch with michael[at]myokit.org.

