[![travis](https://travis-ci.org/MichaelClerx/myokit.svg?branch=master)](https://travis-ci.org/MichaelClerx/myokit)
[![appveyor](https://ci.appveyor.com/api/projects/status/u2e6bc6tklgxyyra?svg=true)](https://ci.appveyor.com/project/MichaelClerx/myokit)
[![codecov](https://codecov.io/gh/MichaelClerx/myokit/branch/master/graph/badge.svg)](https://codecov.io/gh/MichaelClerx/myokit)
[![Documentation Status](https://readthedocs.org/projects/myokit/badge/?version=latest)](https://myokit.readthedocs.io/?badge=latest)

![Myokit](http://myokit.org/static/img/logo.png)

[Myokit](http://myokit.org) is an [open-source](https://github.com/MichaelClerx/myokit/blob/master/LICENSE.txt) Python-based toolkit that facilitates modeling and simulation of cardiac cellular electrophysiology.
It's hosted on [GitHub](https://github.com/MichaelClerx/myokit/) and available on [PyPi](https://pypi.org/project/myokit/).
For the latest documentation, see [myokit.readthedocs.io](https://myokit.readthedocs.io/).

More information, including examples and an installation guide, is available on [myokit.org](http://myokit.org).


## Install

To install Myokit, run

    pip install myokit

On linux and windows, start menu icons can then be added by running

    python -m myokit icons

To run single-cell simulations, [CVODE](https://computation.llnl.gov/projects/sundials/sundials-software) must be installed (windows binaries are included in the pip install).
In addition, Myokit needs a working C/C++ compiler to be present on the system.

For full details, see [http://myokit.org/install](http://myokit.org/install).

## Quick-start guide

After installation, to quickly test if Myokit works, type

    python -m myokit run example
    
or simply

    myokit run example
    
To open an IDE window, type

    myokit ide
    
To see what else Myokit can do, type

    myokit -h

