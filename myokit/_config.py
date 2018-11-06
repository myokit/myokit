#
# Loads settings from configuration file in user home directory or attempts to
# guess best settings.
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

# Load Myokit, at least, the bit that's been setup so far. This just means
# this method will add a link to the myokit module already being loaded
# into this method's namespace. This allows us to use the constants defined
# before this method was called.
import myokit

# Load libraries
import os
import logging
import platform

# ConfigParser in Python 2 and 3
try:
    from ConfigParser import ConfigParser
except ImportError:
    from configparser import RawConfigParser as ConfigParser


def _create(path):
    """
    Attempts to guess the best settings and stores them in a new configuration
    file.
    """
    # Get operating system
    system = platform.system()

    # Create config parser
    config = ConfigParser(allow_no_value=True)

    # Make the parser case sensitive (need for unix paths!)
    config.optionxform = str

    # General information
    config.add_section('myokit')
    config.set(
        'myokit',
        '# This file can be used to set global configuration options for'
        ' Myokit.')

    # Date format
    config.add_section('time')
    config.set('time', '# Date format used throughout Myokit')
    config.set('time', '# Format should be acceptable for time.strftime')
    config.set('time', 'date_format', myokit.DATE_FORMAT)
    config.set('time', '# Time format used throughout Myokit')
    config.set('time', '# Format should be acceptable for time.strftime')
    config.set('time', '# Format should be acceptable for time.strftime')
    config.set('time', 'time_format', myokit.TIME_FORMAT)

    # Add line numbers to debug output of simulations
    config.add_section('debug')
    config.set('debug', '# Add line numbers to debug output of simulations')
    config.set('debug', 'line_numbers', myokit.DEBUG_LINE_NUMBERS)

    # GUI Backend
    config.add_section('gui')
    config.set('gui', '# Backend to use for graphical user interface.')
    config.set('gui', '# Valid options are "pyqt5", "pyqt4" or "pyside".')
    config.set('gui', '# Leave unset for automatic selection.')
    config.set('gui', '#backend = pyqt5')
    config.set('gui', '#backend = pyqt4')
    config.set('gui', '#backend = pyside')

    # Locations of sundials library
    config.add_section('sundials')
    config.set(
        'sundials', '# Location of sundials shared libary files'
        ' (.so or .dll).')
    config.set('sundials', '# Multiple paths can be set using ; as separator.')

    if system == 'Windows':     # pragma: no linux cover
        # Windows: Don't set (see load())
        config.set('sundials', '#lib', ';'.join([
            'C:\\Program Files\\sundials\\lib',
            'C:\\Program Files (x86)\\sundials\\lib',
        ]))
    else:
        # Linux and OS/X
        # Standard linux and OS/X install: /usr/local/lib
        # Macports OS/X install: /opt/local/lib ??
        config.set('sundials', 'lib', ';'.join([
            '/usr/local/lib',
            '/opt/local/lib',
        ]))

    config.set('sundials', '# Location of sundials header files (.h).')
    config.set('sundials', '# Multiple paths can be set using ; as separator.')

    if system == 'Windows':     # pragma: no linux cover
        # Windows: Don't set (see load())
        config.set('sundials', '#inc', ';'.join([
            'C:\\Program Files\\sundials\\include',
            'C:\\Program Files (x86)\\sundials\\include',
        ]))
    else:
        # Linux and OS/X
        # Standard linux and OS/X install: /usr/local/include
        # Macports OS/X install: /opt/local/include
        config.set('sundials', 'inc', ';'.join([
            '/usr/local/include',
            '/opt/local/include',
        ]))

    # Set sundials version, try to auto-detect
    if platform.system() == 'Windows':  # pragma: no linux cover
        _dynamically_add_embedded_sundials_win()
    sundials = myokit.Sundials.version_int()
    if sundials is None:    # pragma: no cover
        log = logging.getLogger(__name__)
        log.warning('Unable to auto-detect Sundials version.')
        config.set('sundials', '#version', 30100)
    else:
        config.set('sundials', 'version', sundials)

    # Locations of OpenCL libraries
    config.add_section('opencl')
    config.set(
        'opencl', '# Location of opencl shared libary files (.so or .dll).')
    config.set('opencl', '# Multiple paths can be set using ; as separator.')

    if system == 'Windows':     # pragma: no linux cover
        # All windowses
        c32 = 'C:\\Program Files\\'
        c64 = 'C:\\Program Files (x86)\\'
        config.set('opencl', 'lib', ';'.join([
            c32 + 'Intel\\OpenCL SDK\\6.3\\lib\\x86',
            c64 + 'Intel\\OpenCL SDK\\6.3\\lib\\x86',
            c32 + 'AMD APP SDK\\2.9\\bin\\x86',
            c64 + 'AMD APP SDK\\2.9\\bin\\x86',
            c32 + 'NVIDIA GPU Computing Toolkit\\CUDA\\v7.0\\lib\\Win32',
            c64 + 'NVIDIA GPU Computing Toolkit\\CUDA\\v7.0\\lib\\Win32',
        ]))
    else:
        # Linux and mac
        config.set('opencl', 'lib', ';'.join([
            '/usr/lib64',
            '/usr/lib64/nvidia',
            '/usr/local/cuda/lib64',
        ]))

    config.set('opencl', '# Location of opencl header files (.h).')
    config.set('opencl', '# Multiple paths can be set using ; as separator.')

    if system == 'Windows':     # pragma: no linux cover
        # All windowses
        c32 = 'C:\\Program Files\\'
        c64 = 'C:\\Program Files (x86)\\'
        config.set('opencl', 'inc', ';'.join([
            # Enable for Intel OpenCL drivers
            c32 + 'Intel\\OpenCL SDK\\6.3\\include',
            c64 + 'Intel\\OpenCL SDK\\6.3\\include',
            c32 + 'AMD APP SDK\\2.9\\include',
            c64 + 'AMD APP SDK\\2.9\\include',
            c32 + 'NVIDIA GPU Computing Toolkit\\CUDA\\v7.0\\include',
            c64 + 'NVIDIA GPU Computing Toolkit\\CUDA\\v7.0\\include',
        ]))
    else:
        # Linux and mac
        config.set('opencl', 'inc', ';'.join([
            '/usr/include/CL',
            '/usr/local/cuda/include',
        ]))

    # Write ini file
    try:
        with open(path, 'w') as configfile:
            config.write(configfile)
    except IOError:     # pragma: no cover
        logger = logging.getLogger('myokit')
        logger.warning('Warning: Unable to write settings to ' + str(path))


def _load():
    """
    Reads the configuration file and attempts to set the library paths.
    """
    # Location of configuration file
    path = os.path.join(myokit.DIR_USER, 'myokit.ini')

    # No file present? Create one and return
    if not os.path.isfile(path):
        _create(path)

    # Create the config parser (no value allows comments)
    config = ConfigParser(allow_no_value=True)

    # Make the parser case sensitive (need for unix paths!)
    config.optionxform = str

    # Parse the config file
    config.read(path)

    # Date format
    if config.has_option('time', 'date_format'):
        x = config.get('time', 'date_format')
        if x:
            myokit.DATE_FORMAT = str(x)

    # Time format
    if config.has_option('time', 'time_format'):
        x = config.get('time', 'time_format')
        if x:
            myokit.TIME_FORMAT = str(x)

    # Add line numbers to debug output of simulations
    if config.has_option('debug', 'line_numbers'):
        try:
            myokit.DEBUG_LINE_NUMBERS = config.getboolean(
                'debug', 'line_numbers')
        except ValueError:  # pragma: no cover
            pass

    # GUI Backend
    if config.has_option('gui', 'backend'):
        x = config.get('gui', 'backend').strip().lower()
        if x == 'pyside':
            myokit.FORCE_PYSIDE = True
            myokit.FORCE_PYQT4 = False
            myokit.FORCE_PYQT5 = False
        elif x == 'pyqt' or x == 'pyqt4':
            myokit.FORCE_PYSIDE = False
            myokit.FORCE_PYQT4 = True
            myokit.FORCE_PYQT5 = False
        elif x == 'pyqt5':
            myokit.FORCE_PYSIDE = False
            myokit.FORCE_PYQT4 = False
            myokit.FORCE_PYQT5 = True
        #else:
        # If empty or invalid, don't adjust the settings!

    # Sundials libraries, header files, and version
    if config.has_option('sundials', 'lib'):
        for x in config.get('sundials', 'lib').split(';'):
            myokit.SUNDIALS_LIB.append(x.strip())
    if config.has_option('sundials', 'inc'):
        for x in config.get('sundials', 'inc').split(';'):
            myokit.SUNDIALS_INC.append(x.strip())
    if config.has_option('sundials', 'version'):
        try:
            myokit.SUNDIALS_VERSION = int(config.get('sundials', 'version'))
        except ValueError:  # pragma: no cover
            pass

    # Dynamically add embedded sundials paths for windows
    if platform.system() == 'Windows':  # pragma: no linux cover
        _dynamically_add_embedded_sundials_win()

    # If needed, attempt auto-detection of Sundials version
    if myokit.SUNDIALS_VERSION == 0:    # pragma: no cover
        sundials = myokit.Sundials.version_int()
        log = logging.getLogger(__name__)
        if sundials is None:
            log.warning(
                'Sundials version not set in myokit.ini and version'
                ' auto-detection failed.'
            )
        else:
            myokit.SUNDIALS_VERSION = sundials
            log.warning(
                'Sundials version not set in myokit.ini. Continuing with'
                ' detected version (' + str(sundials) + '). For a tiny'
                ' performance boost, please set this version in ' + path)

    # OpenCL libraries and header files
    if config.has_option('opencl', 'lib'):
        for x in config.get('opencl', 'lib').split(';'):
            myokit.OPENCL_LIB.append(x.strip())
    if config.has_option('opencl', 'inc'):
        for x in config.get('opencl', 'inc').split(';'):
            myokit.OPENCL_INC.append(x.strip())


def _dynamically_add_embedded_sundials_win():   # pragma: no linux cover
    """
    On windows, sundials binaries are packaged with Myokit. Storing this
    location in the config file could cause issues, for example if a user moves
    a Myokit installation, reinstalls e.g. Anaconda to a different path, uses
    multiple Myokits or Python distros etc. So instead of storing this location
    in the config file, it is added dynamically.
    This is only done _if_ the user doesn't set an explicit path (i.e. we allow
    user overrides).
    """
    sundials_win = os.path.abspath(
        os.path.join(myokit.DIR_DATA, 'sundials-win-vs'))
    if len(myokit.SUNDIALS_LIB) == 0:
        myokit.SUNDIALS_LIB.append(os.path.join(sundials_win, 'lib'))
    if len(myokit.SUNDIALS_INC) == 0:
        myokit.SUNDIALS_INC.append(os.path.join(sundials_win, 'include'))


# Load settings
_load()
