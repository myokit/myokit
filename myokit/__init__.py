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

This module provides a gateway to the main Myokit components. For example, to
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


#
# Configure logging
#
import logging  # noqa  (not at top of file)
logging.basicConfig()
del(logging)


#
# Check python version
#
import sys  # noqa
if sys.hexversion < 0x02070000:     # pragma: no python 3 cover
    print('-- ERROR --')
    print('Myokit requires Python version 2.7.0 or higher.')
    print('Detected Python version: ')
    print(sys.version)
    print()
    sys.exit(1)
elif sys.hexversion >= 0x03000000 and sys.hexversion < 0x03040000:
    print('-- ERROR --')
    print('Python 3.0 to 3.3 are not supported.')
    print()
    sys.exit(1)

# Exec() that works with Python 2 versions before 2.7.9
if sys.hexversion < 0x020709F0:
    from ._exec_old import _exec    # noqa
else:
    from ._exec_new import _exec    # noqa
del(sys)


#
# Version information
#
from ._myokit_version import (  # noqa
    __release__,
    __version__,
    __version_tuple__,
)


# Myokit version
def version(raw=False):
    """
    Returns the current Myokit version.
    """
    if raw:
        return __version__
    else:
        t1 = ' Myokit ' + __version__ + ' '
        t2 = '_' * len(t1)
        t1 += '|/\\'
        t2 += '|  |' + '_' * 5
        return '\n' + t1 + '\n' + t2


# Warn about development version
import logging  # noqa
log = logging.getLogger(__name__)
log.info('Loading Myokit version ' + __version__)
if not __release__:
    log.warning(
        'Using development version of Myokit. This may contain untested'
        ' features and bugs. Please see http://myokit.org for the latest'
        ' stable release.')
del(log, logging)


#
# Licensing
#

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
COPYRIGHT = '(C) 2011-2018, Maastricht University, University of Oxford'


#
# Paths
#

# Myokit root
import os, inspect  # noqa
try:
    frame = inspect.currentframe()
    DIR_MYOKIT = os.path.dirname(inspect.getfile(frame))
finally:
    # Always manually delete frame
    # https://docs.python.org/2/library/inspect.html#the-interpreter-stack
    del(frame)

# Binary data files
DIR_DATA = os.path.join(DIR_MYOKIT, '_bin')

# C header files
DIR_CFUNC = os.path.join(DIR_MYOKIT, '_sim')

# Location of myokit user config
DIR_USER = os.path.join(os.path.expanduser('~'), '.config', 'myokit')

# Old user config location: Move if possible
DIR_USER_OLD = os.path.join(os.path.expanduser('~'), '.myokit')

if os.path.exists(DIR_USER_OLD):    # pragma: no cover
    if not os.path.exists(DIR_USER):
        import shutil  # noqa
        shutil.move(DIR_USER_OLD, DIR_USER)
        del(shutil)

# Ensure the user config directory exists and is writable
if os.path.exists(DIR_USER):    # pragma: no cover
    if not os.path.isdir(DIR_USER):
        raise Exception(
            'File or link found in place of user directory: ' + str(DIR_USER))
else:
    os.makedirs(DIR_USER)

# Example mmt file
EXAMPLE = os.path.join(DIR_DATA, 'example.mmt')

# Don't expose standard libraries as part of Myokit
del(os, inspect)


#
# Debugging mode: Simulation code will be shown, not executed
#
DEBUG = False


#
# Data logging flags (bitmasks)
#
LOG_NONE = 0
LOG_STATE = 1
LOG_BOUND = 2
LOG_INTER = 4
LOG_DERIV = 8
LOG_ALL = LOG_STATE + LOG_INTER + LOG_BOUND + LOG_DERIV

#
# Floating point precision
#
SINGLE_PRECISION = 32
DOUBLE_PRECISION = 64

#
# Unit checking modes
#
UNIT_TOLERANT = 1
UNIT_STRICT = 2

#
# Maximum precision float output format strings
#
SFDOUBLE = '{:< 1.17e}'  # Exponent can have 3 digits for very small numbers
SFSINGLE = '{:< 1.9e}'

#
# Date and time formats to use throughout Myokit
#
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
TIME_FORMAT = '%H:%M:%S'

#
# Add line numbers to debug output of simulations
#
DEBUG_LINE_NUMBERS = True


#
# GUI: Favour PySide or PyQt
#
FORCE_PYQT5 = False
FORCE_PYQT4 = False
FORCE_PYSIDE = False


#
# Library paths and settings
#

# Location of the Sundials (CVODE) shared library objects (.dll or .so)
SUNDIALS_LIB = []

# Location of the Sundials (CVODE) header files (.h)
SUNDIALS_INC = []

# Sundials version number. Defaults to 0.
SUNDIALS_VERSION = 0

# Location of the OpenCL shared library objects (.dll or .so)
OPENCL_LIB = []

# Location of the OpenCL header files (.h)
OPENCL_INC = []


#
# Imports
#

# Exceptions
from ._err import (  # noqa
    CompilationError,
    CyclicalDependencyError,
    DataBlockReadError,
    DataLogReadError,
    DuplicateFunctionArgument,
    DuplicateFunctionName,
    DuplicateName,
    ExportError,
    FindNanError,
    GenerationError,
    IllegalAliasError,
    IllegalReferenceError,
    ImportError,
    IncompatibleModelError,
    IncompatibleUnitError,
    IntegrityError,
    InvalidBindingError,
    InvalidDataLogError,
    InvalidFunction,
    InvalidLabelError,
    InvalidMetaDataNameError,
    InvalidNameError,
    MissingRhsError,
    MissingTimeVariableError,
    MyokitError,
    NonLiteralValueError,
    NumericalError,
    ParseError,
    ProtocolEventError,
    ProtocolParseError,
    SectionNotFoundError,
    SimulationCancelledError,
    SimulationError,
    SimultaneousProtocolEventError,
    UnresolvedReferenceError,
    UnusedVariableError,
)

# Check if all errors imported
# Dynamically importing them doesn't seem to be possible, and forgetting to
#  import an error creates a hard to debug bug (something needs to go wrong
#  before the interpreter reaches the code raising the error and notices it's
#  not there).
from . import _err  # noqa
import inspect  # noqa
_globals = globals()
ex, name, clas = None, None, None
for ex in inspect.getmembers(_err):
    name, clas = ex
    if type(clas) == type(MyokitError) and issubclass(clas, MyokitError):
        if name not in _globals:
            raise Exception('Failed to import exception: ' + name)
del(ex, name, clas, _globals, inspect)  # Prevent public visibility
del(_err)

# Model api
from ._model_api import ( # noqa
    check_name,
    Component,
    Equation,
    EquationList,
    Model,
    ModelPart,
    UserFunction,
    Variable,
)

# Expressions and units
from ._expressions import (  # noqa
    Abs,
    ACos,
    And,
    ASin,
    ATan,
    Ceil,
    Condition,
    Cos,
    Derivative,
    Divide,
    Equal,
    Exp,
    Expression,
    Floor,
    Function,
    If,
    InfixCondition,
    InfixExpression,
    Less,
    LessEqual,
    LhsExpression,
    Log,
    Log10,
    Minus,
    More,
    MoreEqual,
    Multiply,
    Name,
    Number,
    Not,
    NotEqual,
    Or,
    Piecewise,
    Plus,
    Power,
    PrefixCondition,
    PrefixExpression,
    PrefixMinus,
    PrefixPlus,
    Quantity,
    Quotient,
    Remainder,
    Sin,
    Sqrt,
    Tan,
    UnsupportedFunction,
    Unit,

)

# Pacing protocol
from ._protocol import (  # noqa
    PacingSystem,
    Protocol,
    ProtocolEvent,
)

# Parser functions
from ._parsing import (  # noqa
    format_parse_error,
    KEYWORDS,
    parse,
    parse_expression_string as parse_expression,
    parse_model,
    #parse_number_string as parse_number,
    parse_protocol,
    parse_state,
    parse_unit_string as parse_unit,
    split,
    strip_expression_units,
)

# Auxillary functions
from ._aux import (  # noqa
    # Global date and time formats
    date,
    time,

    # Reading, writing
    load,
    load_model,
    load_protocol,
    load_script,
    save,
    save_model,
    save_protocol,
    save_script,
    load_state,
    save_state,
    load_state_bin,
    save_state_bin,

    # Running scripts
    run,

    # Test step
    step,

    # Output masking
    PyCapture,
    SubCapture,

    # Sorting
    _natural_sort_key,

    # Dyanmic generation of Python/NumPy expressions
    python_writer,
    numpy_writer,

    # Model comparison
    ModelComparison,

    # Benchmarking
    Benchmarker,

    # Misc
    _lvsd,
    format_path,
    strfloat,
    format_float_dict,

    # Snapshot creation for replicability
    pack_snapshot,
)

# System information
from ._system import (      # noqa
    system,
)

# Progress reporting
from ._progress import (    # noqa
    ProgressPrinter,
    ProgressReporter,
    Timeout,
)

# Data logging
from ._datalog import (     # noqa
    DataLog,
    _dimco,
    LoggedVariableInfo,
    prepare_log,
    split_key,
)
from ._datablock import (   # noqa
    ColorMap,
    DataBlock1d,
    DataBlock2d,
)


# Simulations
from ._sim import (  # noqa
    CModule,
    CppModule,
)
from ._sim.compiler import (  # noqa
    Compiler,
)
from ._sim.sundials import (  # noqa
    Sundials,
)
from ._sim.opencl import (  # noqa
    OpenCL,
    OpenCLDeviceInfo,
    OpenCLInfo,
    OpenCLPlatformInfo,
)
from ._sim.cvodesim import Simulation       # noqa
from ._sim.cable import Simulation1d        # noqa
from ._sim.rhs import RhsBenchmarker        # noqa
from ._sim.icsim import ICSimulation        # noqa
from ._sim.psim import PSimulation          # noqa
from ._sim.jacobian import JacobianTracer, JacobianCalculator   # noqa
#from ._sim.openmp import SimulationOpenMP                       # noqa
from ._sim.openclsim import SimulationOpenCL                    # noqa
from ._sim.fiber_tissue import FiberTissueSimulation            # noqa

# Import whole modules
# This allows these modules to be used after myokit was imported, without
# importing the modules specifically (like os and os.path).
# All modules imported here must report so in their docs
from . import ( # noqa
    mxml,
    pacing,
    units,  # Also loads all common unit names
)


#
# Globally shared progress reporter
#
_Simulation_progress = None


#
# Load settings
#
from . import _config   # noqa
del(_config)


#
# Default mmt file parts
#
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
    return '\n'.join((
        "[[script]]",
        "import matplotlib.pyplot as plt",
        "import myokit",
        "",
        "# Get model and protocol, create simulation",
        "m = get_model()",
        "p = get_protocol()",
        "s = myokit.Simulation(m, p)",
        "",
        "# Run simulation",
        "d = s.run(1000)",
        "",
        "# Get the first state variable's name",
        "first_state = next(m.states)",
        "var = first_state.qname()",
        "",
        "# Display the results",
        "plt.figure()",
        "plt.plot(d.time(), d[var])",
        "plt.title(var)",
        "plt.show()",
    ))

