#
# Myokit's main module
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
"""
Myokit: The Maastricht Modeling Toolkit

This module provides a gateway to the main myokit components. For example, to
load a model use myokit.load_model('filename.mmt'), create a myokit.Protocol
and then a myokit.Simulation which you can .run() to obtain simulated results.
"""

#__all__ =
#
# __all__ should NOT be provided! Doing so removes all methods below from
# the content imported by "from myokit import *".
#
# Without an explicit __all__, importing * will result in importing all
# functions and classes described below. No submodules of myokit will be
# loaded!

#
# GUI and graphical modules should not be auto-included because they define a
# matplotlib backend to use. If the user requires a different backend, this
# will generate an error.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

# Check python version
import sys
if sys.hexversion < 0x02070000:
    print('-- ERROR --')
    print('Myokit requires Python version 2.7.0 or higher.')
    print('Detected Python version: ')
    print(sys.version)
    print()
    sys.exit(1)

# Constants

# Version information
VERSION_INT = 1, 26, 4
VERSION = '.'.join([str(x) for x in VERSION_INT])
if not sys.hexversion > 0x03000000:
    del(x)
del(sys)
RELEASE = ''

# Licensing

# Full license text
LICENSE = """
Myokit
Copyright 2011-2018 Maastricht University, University of Oxford
michael@myokit.org

Myokit is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your
option) any later version.

Myokit is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE.
See the GNU General Public License for more details.

For a copy of the GNU General Public License,
see http://www.gnu.org/licenses/.
""".strip()

# Full license text, html
LICENSE_HTML = """
<h1>Myokit</h1>
<p>
    Copyright 2011-2018 Maastricht University, University of Oxford
    <br /><a href="mailto:michael@myokit.org">michael@myokit.org</a>
</p>
<p>
    Myokit is free software: you can redistribute it and/or modify it under the
    terms of the GNU General Public License as published by the Free Software
    Foundation, either version 3 of the License, or (at your option) any later
    version.
</p>
<p>
    Myokit is distributed in the hope that it will be useful, but WITHOUT ANY
    WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
    FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
    details.
</p>
<p>
    For a copy of the GNU General Public License, see
    <a href="http://www.gnu.org/licenses/">http://www.gnu.org/licenses/</a>.
</p>
""".strip()

# Example license header that should appear in most files
LICENSE_HEADER = """
This file is part of Myokit
 Copyright 2011-2018 Maastricht University, University of Oxford
 Licensed under the GNU General Public License v3.0
 See: http://myokit.org
""".strip()

# Single-line copyright notice
COPYRIGHT = '(C) 2011-2017, Maastricht University, University of Oxford'

# Myokit paths
import os, inspect  # noqa
try:
    frame = inspect.currentframe()
    DIR_MYOKIT = os.path.dirname(inspect.getfile(frame))
finally:
    # Always manually delete frame
    # https://docs.python.org/2/library/inspect.html#the-interpreter-stack
    del(frame)

DIR_DATA = os.path.join(DIR_MYOKIT, '_bin')
DIR_CFUNC = os.path.join(DIR_MYOKIT, '_sim')

# Location of myokit user info
DIR_USER = os.path.join(os.path.expanduser('~'), '.myokit')

if os.path.exists(DIR_USER):
    if not os.path.isdir(DIR_USER):
        raise Exception(
            'File or link found in place of user directory: ' + str(DIR_USER))
else:
    os.makedirs(DIR_USER)

# Location of example mmt file
EXAMPLE = os.path.join(DIR_DATA, 'example.mmt')

# Prevent standard libraries being represented as part of Myokit
del(os, inspect)

# Debugging mode: Simulation code will be shown, not executed
DEBUG = False

# Data logging flags (bitmasks)
LOG_NONE = 0
LOG_STATE = 1
LOG_BOUND = 2
LOG_INTER = 4
LOG_DERIV = 8
LOG_ALL = LOG_STATE + LOG_INTER + LOG_BOUND + LOG_DERIV

# Floating point precision
SINGLE_PRECISION = 32
DOUBLE_PRECISION = 64

# Unit checking modes
UNIT_TOLERANT = 1
UNIT_STRICT = 2

# Maximum precision float output
SFDOUBLE = '{:< 1.17e}'
SFSINGLE = '{:< 1.9e}'

# Date and time formats to use throughout Myokit
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
TIME_FORMAT = '%H:%M:%S'

# Add line numbers to debug output of simulations
DEBUG_LINE_NUMBERS = True

# Favor PySide or PyQt
FORCE_PYQT5 = False
FORCE_PYQT4 = False
FORCE_PYSIDE = False

# Location of the Sundials (CVODE) shared library objects (.dll or .so)
SUNDIALS_LIB = []

# Location of the Sundials (CVODE) header files (.h)
SUNDIALS_INC = []

# Sundials major version number. Defaults to 26000.
SUNDIALS_VERSION = 26000

# Location of the OpenCL shared library objects (.dll or .so)
OPENCL_LIB = []

# Location of the OpenCL header files (.h)
OPENCL_INC = []


# Load settings
from . import _config   # noqa
del(_config)


# Myokit version
def version(raw=False):
    """
    Returns the current Myokit version.
    """
    if raw:
        return VERSION
    else:
        return '\n Myokit version ' + VERSION + ' ' * (15 - len(VERSION)) \
               + '|/\\\n_______________________________|  |______'


# Exceptions
from ._err import (
    MyokitError,
    IntegrityError, InvalidBindingError, InvalidLabelError,
    DuplicateName, InvalidNameError, IllegalAliasError,
    UnresolvedReferenceError, IllegalReferenceError,
    UnusedVariableError, CyclicalDependencyError,
    MissingRhsError, MissingTimeVariableError,
    NonLiteralValueError, NumericalError,
    IncompatibleUnitError, InvalidMetaDataNameError,
    DuplicateFunctionName, DuplicateFunctionArgument,
    InvalidFunction,
    ParseError, SectionNotFoundError,
    ProtocolParseError, ProtocolEventError,
    SimultaneousProtocolEventError,
    SimulationError, FindNanError, SimulationCancelledError,
    InvalidDataLogError, DataLogReadError, DataBlockReadError,
    GenerationError, CompilationError,
    ImportError, ExportError,
    IncompatibleModelError,
) # noqa


# Check if all errors imported
# Dynamically importing them doesn't seem to be possible, and forgetting to
#  import an error creates a hard to debug bug (something needs to go wrong
#  before the interpreter reaches the code raising the error and notices it's
#  not there).
import inspect  # noqa
_globals = globals()
ex, name, clas = None, None, None
for ex in inspect.getmembers(_err):
    name, clas = ex
    if type(clas) == type(MyokitError) and issubclass(clas, MyokitError):
        if name not in _globals:
            raise Exception('Failed to import exception: ' + name)
del(ex, name, clas, _globals, inspect)  # Prevent public visibility


# Model structure
from ._core import (
    ModelPart, Model, Component, Variable, check_name,
    Equation, EquationList, UserFunction,
) # noqa


# Expressions and units
from ._expr import (
    Expression, LhsExpression, Derivative, Name, Number,
    PrefixExpression, PrefixPlus, PrefixMinus,
    InfixExpression, Plus, Minus, Multiply, Divide,
    Quotient, Remainder, Power,
    Function, Sqrt, Sin, Cos, Tan, ASin, ACos, ATan, Exp, Log, Log10, Floor,
    Ceil, Abs,
    If, Condition, PrefixCondition, Not, And, Or, InfixCondition,
    Equal, NotEqual, More, Less, MoreEqual, LessEqual,
    Piecewise, OrderedPiecewise, Polynomial, Spline,
    UnsupportedFunction,
    Unit, Quantity,
) # noqa


# Pacing protocol
from ._protocol import (
    Protocol, ProtocolEvent, PacingSystem,
) # noqa


# Parser functions
from ._parser import (
    KEYWORDS,
    parse, split, format_parse_error,
    parse_model, parse_protocol, parse_state,
    parse_unit_string as parse_unit,
    parse_number_string as parse_number,
    parse_expression_string as parse_expression,
    strip_expression_units,
) # noqa


# Auxillary functions
from ._aux import (
    # Global date and time formats
    date, time,

    # Reading, writing
    load, load_model, load_protocol, load_script,
    save, save_model, save_protocol, save_script,
    load_state, save_state, load_state_bin, save_state_bin,

    # Running scripts
    run,

    # Test step
    step,

    # Output masking
    PyCapture, SubCapture,

    # Sorting
    natural_sort_key,

    # Dyanmic generation of Python/Numpy expressions
    pywriter, numpywriter,

    # Model comparison
    ModelComparison,

    # Benchmarking
    Benchmarker,

    # Logging
    TextLogger,

    # Misc
    lvsd, format_path, strfloat, format_float_dict,

    # Snapshot creation for replicability
    pack_snapshot,
) # noqa


# Data logging
from ._datalog import (
    DataLog, LoggedVariableInfo, dimco, split_key, prepare_log
) # noqa
from ._datablock import (
    DataBlock1d, DataBlock2d, ColorMap,
) # noqa


# Simulations
from ._sim import (
    ProgressReporter, ProgressPrinter,
    CModule, CppModule,
) # noqa
from ._sim.cvode import Simulation              # noqa
from ._sim.cable import Simulation1d            # noqa
from ._sim.opencl import OpenCL                 # noqa
from ._sim.opencl import OpenCLInfo, OpenCLPlatformInfo, OpenCLDeviceInfo  # noqa
from ._sim.openclsim import SimulationOpenCL    # noqa
# from ._sim.openmp import SimulationOpenMP
from ._sim.fiber_tissue import FiberTissueSimulation    # noqa
from ._sim.rhs import RhsBenchmarker            # noqa
from ._sim.jacobian import JacobianTracer, JacobianCalculator   # noqa
from ._sim.icsim import ICSimulation            # noqa
from ._sim.psim import PSimulation              # noqa


# Import whole modules
# This allows these modules to be used after myokit was imported, without
# importing the modules specifically (like os and os.path).
# All modules imported here must report so in their docs
from . import (
    mxml,
    pacing,
    units,  # Also loads all common unit names
) # noqa

# Globally shared progress reporter
_Simulation_progress = None


# Default mmt file parts
def default_protocol():
    """
    Provides a default protocol to use when no embedded one is available.
    """
    p = Protocol()
    p.schedule(1, 100, 0.5, 1000, 0)
    return p


def default_script():
    """
    Provides a default script to use when no embedded script is available.
    """
    return """[[script]]
import matplotlib.pyplot as pl
import myokit

# Get model and protocol, create simulation
m = get_model()
p = get_protocol()
s = myokit.Simulation(m, p)

# Run simulation
d = s.run(1000)

# Get the first state variable's name
first_state = m.states().next()
var = first_state.qname()

# Display the results
pl.figure()
pl.plot(d.time(), d[var])
pl.title(var)
pl.show()
"""
