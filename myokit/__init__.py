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
# Hexversion guide:
#  0x   Hex
#  02   PY_MAJOR_VERSION
#  07   PY_MINOR_VERSION
#  0F   PY_MICRO_VERSION, in hex, so 0F is 15, 10 is 16, etc.
#  F    PY_RELEASE_LEVEL, A for alpha, B for beta, C for candidate, F for final
#  0    PY_RELEASE_SERIAL, increments with every release
#
import sys  # noqa
if sys.hexversion < 0x02070F00:     # pragma: no python 3 cover
    import logging  # noqa
    log = logging.getLogger(__name__)
    log.warning(
        'Myokit is not tested on Python 2 versions older than 2.7.15')
    log.warning('Detected Python version: ' + sys.version)
    del(logging, log)
elif (sys.hexversion >= 0x03000000 and
      sys.hexversion < 0x03050000):  # pragma: no cover
    import logging  # noqa
    log = logging.getLogger(__name__)
    log.warning(
        'Myokit is not tested on Python 3 versions older than 3.5.0')
    log.warning('Detected Python version: ' + sys.version)
    del(logging, log)


# Exec() that works with Python 2 versions before 2.7.9
if sys.hexversion < 0x020709F0:     # pragma: no python 3 cover
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


# Warn about development version
import logging  # noqa
log = logging.getLogger(__name__)
log.info('Loading Myokit version ' + __version__)
if not __release__:     # pragma: no cover
    log.warning('Using development version of Myokit (' + __version__ + ').')
del(log, logging)


#
# Licensing
#

# Full license text
LICENSE = """
BSD 3-Clause License

Copyright (c) 2011-2017 Maastricht University. All rights reserved.
Copyright (c) 2017-2020 University of Oxford. All rights reserved.
 (University of Oxford means the Chancellor, Masters and Scholars of the
  University of Oxford, having an administrative office at Wellington Square,
  Oxford OX1 2JD, UK).
Copyright (c) 2020-2021 University of Nottingham. All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
""".strip()

# Full license text, html
LICENSE_HTML = """
<h1>Myokit</h1>
<p>
    BSD 3-Clause License
    <br />
    <br />Copyright (c) 2011-2017 Maastricht University. All rights reserved.
    <br />Copyright (c) 2017-2019 University of Oxford. All rights reserved.
    <br />(University of Oxford means the Chancellor, Masters and Scholars of
    the University of Oxford, having an administrative office at Wellington
    Square, Oxford OX1 2JD, UK).
</p>
<p>
    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions are met:
</p>
<ul>
    <li>
        <p>
            Redistributions of source code must retain the above copyright
            notice, this list of conditions and the following disclaimer.
        </p>
    </li>
    <li>
        <p>
            Redistributions in binary form must reproduce the above copyright
            notice, this list of conditions and the following disclaimer in the
            documentation and/or other materials provided with the
            distribution.
        </p>
    </li>
    <li>
        <p>
            Neither the name of the copyright holder nor the names of its
            contributors may be used to endorse or promote products derived
            from this software without specific prior written permission.
        </p>
    </li>
</ul>
<p>
    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
    AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
    IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
    ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
    LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
    CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
    SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
    INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
    CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
    ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
    POSSIBILITY OF SUCH DAMAGE.
</p>
""".strip()


#
# Paths
#

# Myokit root
import os, inspect  # noqa
try:
    frame = inspect.currentframe()
    DIR_MYOKIT = os.path.abspath(os.path.dirname(inspect.getfile(frame)))
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
else:                           # pragma: no cover
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
FORCE_PYSIDE2 = False


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
        if name not in _globals:    # pragma: no cover
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
    # Version info
    version,

    # Global date and time formats
    date,
    time,

    # Default mmt parts
    default_protocol,
    default_script,

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

    # Output capturing
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

    # Floating point
    _close,
    _cround,
    _feq,
    _fgeq,
    _fround,
    format_float_dict,
    strfloat,

    # Misc
    format_path,
    _lvsd,
    _pid_hash,
    _rmtree,

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

