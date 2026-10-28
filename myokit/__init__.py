#
# Myokit's main module
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
"""
Myokit

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

#
# Check python version
#
# Hexversion guide:
#  0x   Hex
#  02   PY_MAJOR_VERSION
#  07   PY_MINOR_VERSION
#  0F   PY_MICRO_VERSION, in hex, so 0F is 15, 10 is 16, etc.
#  F    PY_RELEASE_LEVEL, A for alpha, B for beta, C for candidate, F for final
#  0    PY_RELEASE_SERIAL, increments with every release
#
import sys

if sys.hexversion < 0x03000000:  # pragma: no cover
    raise Exception('This version of Myokit does not support Python 2.')
elif sys.hexversion < 0x03070000:  # pragma: no cover
    import warnings
    warnings.warn(
        'Myokit is not tested on Python versions before 3.7. Detected'
        f' version {sys.version}.')
    del warnings
del sys


#
# Version information and licensing
#
import importlib.metadata

__version__ = importlib.metadata.version('myokit')
__release__ = len(__version__.split('.')) == 3
del importlib  # Do _not_ `del importlib.metadata`, that modifies importlib!

# Warn about development version
if not __release__:     # pragma: no cover
    import warnings
    warnings.warn(f'Using development version of Myokit ({__version__}).')
    del warnings

# Full license text
# dist = importlib.metadata.distribution('myokit')
# LICENSE = dist.read_text('licenses/LICENSE.txt').strip()

#
# Paths
#

# Myokit root
import inspect
import os

try:
    frame = inspect.currentframe()
    DIR_MYOKIT = os.path.abspath(os.path.dirname(inspect.getfile(frame)))
finally:
    # Always manually delete frame
    # https://docs.python.org/2/library/inspect.html#the-interpreter-stack
    del frame

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
        import shutil
        shutil.move(DIR_USER_OLD, DIR_USER)
        del shutil

# Ensure the user config directory exists and is writable
if os.path.exists(DIR_USER):    # pragma: no cover
    if not os.path.isdir(DIR_USER):
        raise Exception(
            f'File or link found in place of user directory: {DIR_USER}')
else:                           # pragma: no cover
    os.makedirs(DIR_USER)

# Example mmt file
EXAMPLE = os.path.join(DIR_DATA, 'example.mmt')

# Don't expose standard libraries as part of Myokit
del os, inspect


#
# Debugging modes
#
# Show Generated code, or Write Generated code to file(s):
DEBUG_SG = False
DEBUG_WG = False
# Show compiler output, with lots of warnings enabled:
DEBUG_SC = False
# Show C debug Messages when running compiled code:
DEBUG_SM = False
# Show C profiling information when running compiled code:
DEBUG_SP = False
# Show C detailed simulator stats when running simulations
DEBUG_SS = False

#
# Compatibility settings: Some users report problems with output capturing.
#
# Disable capturing (but don't add extra warning flags)
COMPAT_NO_CAPTURE = False
# Disable file-descriptor mode capturing
COMPAT_NO_FD_CAPTURE = False

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
# Shared real regex. Unsigned, and without "anchors" for string start and end
#
_RE_UNSIGNED_REAL = r'(([0-9]*\.[0-9]+)|([0-9]+\.?[0-9]*))([eE][+-]?[0-9]+)?'

#
# Date and time formats to use throughout Myokit
#
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
TIME_FORMAT = '%H:%M:%S'

#
# GUI: Favor PySide or PyQt
#
FORCE_PYQT6 = False
FORCE_PYQT5 = False
FORCE_PYSIDE6 = False
FORCE_PYSIDE2 = False


#
# Library paths and settings
#

# Location of the Sundials (CVODES) shared library objects (.dll or .so)
SUNDIALS_LIB = []

# Location of the Sundials (CVODES) header files (.h)
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
    IllegalReferenceInInitialValueError,
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
    NumericalError,
    ParseError,
    ProtocolEventError,
    ProtocolParseError,
    SectionNotFoundError,
    SimulationCancelledError,
    SimulationError,
    SimultaneousProtocolEventError,
    TypeError,
    UnresolvedReferenceError,
    UnusedVariableError,
    VariableMappingError,
)

# Tools
from . import float  # noqa
from . import tools  # noqa

# Model api
from ._model_api import ( # noqa
    check_name,
    Component,
    Equation,
    EquationList,
    MetaDataContainer,
    Model,
    ModelPart,
    ObjectWithMetaData,
    UserFunction,
    Variable,
    VarOwner,
    VarProvider,
)

# Expressions
from ._expressions import (  # noqa
    Abs,
    ACos,
    And,
    ASin,
    ATan,
    BinaryComparison,
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
    InitialValue,
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
    NumericalInfixExpression,
    NumericalPrefixExpression,
    Not,
    NotEqual,
    Or,
    PartialDerivative,
    Piecewise,
    Plus,
    Power,
    PrefixExpression,
    PrefixMinus,
    PrefixPlus,
    Quotient,
    Remainder,
    Sin,
    Sqrt,
    Tan,
    UnaryNumericalFunction,
    UnaryNumericalDimensionlessFunction,
)

# Unit and quantity
from ._unit import (  # noqa
    Quantity,
    Unit,
)

# Pacing protocol
from ._protocol import (  # noqa
    PacingSystem,
    Protocol,
    ProtocolEvent,
    TimeSeriesProtocol,
)
from . import pacing  # noqa

# Parser functions
from ._parsing import (  # noqa
    format_parse_error,
    KEYWORDS,
    parse,
    parse_expression_string as parse_expression,
    parse_model,
    parse_protocol,
    parse_state,
    parse_unit_string as parse_unit,
    split,
    strip_expression_units,
)

# Load/save functions
from ._io import (  # noqa
    # Reading, writing
    load,
    load_model,
    load_protocol,
    load_script,
    load_state,
    load_state_bin,
    save,
    save_model,
    save_protocol,
    save_script,
    save_state,
    save_state_bin,
)

# Common units (registers all unit names)
from . import units  # noqa

# Auxillary functions
from ._aux import (  # noqa
    default_protocol,
    default_script,
    ModelComparison,
    numpy_writer,
    _prepare_bindings,
    python_writer,
    run,
    step,
    version,
    # Deprecated and/or moved to myokit.tools
    Benchmarker,
    date,
    format_float_dict,
    format_path,
    strfloat,
    time,
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
    ColumnMetaData,
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
    pid_hash,
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
from ._sim.cmodel import CModel             # noqa
from ._sim.cvodessim import Simulation      # noqa
from ._sim.cable import Simulation1d        # noqa
from ._sim.rhs import RhsBenchmarker        # noqa
from ._sim.openclsim import SimulationOpenCL                    # noqa
from ._sim.fiber_tissue import FiberTissueSimulation            # noqa


#
# Globally shared progress reporter
#
_simulation_progress = None


#
# Load settings
#
from . import _config

del _config

