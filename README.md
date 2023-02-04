[![Ubuntu unit tests](https://github.com/myokit/myokit/actions/workflows/unit-tests-ubuntu.yml/badge.svg)](https://github.com/myokit/myokit/actions/workflows/unit-tests-ubuntu.yml)
[![MacOS unit tests](https://github.com/myokit/myokit/actions/workflows/unit-tests-macos.yml/badge.svg)](https://github.com/myokit/myokit/actions/workflows/unit-tests-macos.yml)
[![Windows unit tests](https://github.com/myokit/myokit/actions/workflows/unit-tests-windows.yml/badge.svg)](https://github.com/myokit/myokit/actions/workflows/unit-tests-windows.yml)
[![Windows Miniconda test](https://github.com/myokit/myokit/actions/workflows/unit-tests-windows-miniconda.yml/badge.svg)](https://github.com/myokit/myokit/actions/workflows/unit-tests-windows-miniconda.yml)
[![codecov](https://codecov.io/gh/myokit/myokit/branch/main/graph/badge.svg)](https://codecov.io/gh/myokit/myokit)
[![Documentation Status](https://readthedocs.org/projects/myokit/badge/?version=latest)](https://myokit.readthedocs.io/?badge=latest)

![Myokit](http://myokit.org/static/img/logo.png)

[Myokit](http://myokit.org) is an [open-source](https://github.com/MichaelClerx/myokit/blob/main/LICENSE.txt) Python-based toolkit that facilitates modeling and simulation of cardiac cellular electrophysiology.
It's hosted on [GitHub](https://github.com/MichaelClerx/myokit/) and available on [PyPi](https://pypi.org/project/myokit/).
For the latest documentation, see [myokit.readthedocs.io](https://myokit.readthedocs.io/).

More information, including examples and an installation guide, is available on [myokit.org](http://myokit.org).
A list of changes introduced in each Myokit release is provided in the [Changelog](https://github.com/MichaelClerx/myokit/blob/main/CHANGELOG.md).


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

You can contribute to Myokit by [reporting issues](https://github.com/MichaelClerx/myokit/issues), but code contributions (bugfixes, new formats, new features etc.) are also very welcome!
New features are best discussed in an issue before starting any implementation work, and guidelines for code style (and more) can be found in [CONTRIBUTING.md](https://github.com/MichaelClerx/myokit/blob/main/CONTRIBUTING.md).


## Citing Myokit

If you use Myokit in your research, please cite it using the information in our [CITATION file](https://github.com/MichaelClerx/myokit/blob/main/CITATION).

I like to [keep track of who's using Myokit](http://myokit.org/publications/) (for my CV!). If you are using Myokit for teaching, I'd love to hear about it. You can drop me a line at michael[at]myokit.org.
