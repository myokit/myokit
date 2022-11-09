#
# Loads settings from configuration file in user home directory or attempts to
# guess best settings.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

# Load Myokit, at least, the bit that's been setup so far. This just means
# this method will add a link to the myokit module already being loaded
# into this method's namespace. This allows us to use the constants defined
# before this method was called.
import myokit

# Load standard library modules
import logging
import os
import platform
import sys
import warnings

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

    # Compatibility settings
    config.add_section('compatibility')
    config.set(
        'compatibility',
        '# Optional settings to make Myokit work on tricky systems.')
    config.set('compatibility', '# Don\'t capture compiler output.')
    config.set('compatibility', '#no_capture = True')
    config.set('compatibility', '# Don\'t use the file-descriptor method.')
    config.set('compatibility', '#no_fd_capture = True')

    # Date format
    config.add_section('time')
    config.set('time', '# Date format used throughout Myokit')
    config.set('time', '# The format should be acceptable for time.strftime')
    config.set('time', 'date_format', myokit.DATE_FORMAT)
    config.set('time', '# Time format used throughout Myokit')
    config.set('time', '# The format should be acceptable for time.strftime')
    config.set('time', 'time_format', myokit.TIME_FORMAT)

    # GUI Backend
    config.add_section('gui')
    config.set('gui', '# Backend to use for graphical user interface.')
    config.set('gui', '# Valid options are pyqt5, pyqt4, pyside2 and pyside.')
    config.set('gui', '# Leave unset for automatic selection.')
    config.set('gui', '#backend = pyqt5')
    config.set('gui', '#backend = pyqt4')
    config.set('gui', '#backend = pyside2')
    config.set('gui', '#backend = pyside')

    # Locations of sundials library
    config.add_section('sundials')
    config.set(
        'sundials', '# Location of sundials shared libary files'
        ' (.so, .dll, or .dylib).')
    config.set('sundials', '# Multiple paths can be set using ; as separator.')

    if system == 'Windows':     # pragma: no linux cover
        # Windows: Don't set (see load())
        config.set('sundials', '#lib', ';'.join([
            'C:\\Program Files\\sundials\\lib',
            'C:\\Program Files (x86)\\sundials\\lib',
        ]))
    elif system == 'Darwin':    # pragma: no linux cover
        # Apple
        # Standard: /usr/local/lib
        # Macports: /opt/local/lib
        # Homebrew: /opt/homebrew
        config.set('sundials', 'lib', ';'.join([
            '/usr/local/lib',
            '/usr/local/lib64',
            '/opt/local/lib',
            '/opt/local/lib64',
            '/opt/homebrew/lib',
            '/opt/homebrew/lib64',
        ]))
    else:
        # Linux
        config.set('sundials', 'lib', ';'.join([
            '/usr/local/lib',
            '/usr/local/lib64',
        ]))

    config.set('sundials',
               '# Location of sundials header files (.h).')
    config.set('sundials', '# Multiple paths can be set using ; as separator.')

    if system == 'Windows':     # pragma: no linux cover
        # Windows: Don't set (see load())
        config.set('sundials', '#inc', ';'.join([
            'C:\\Program Files\\sundials\\include',
            'C:\\Program Files (x86)\\sundials\\include',
        ]))
    elif system == 'Darwin':    # pragma: no linux cover
        # Apple
        # Standard: /usr/local/include
        # Macports: /opt/local/include
        # Homebrew: /opt/homebrew/include
        config.set('sundials', 'inc', ';'.join([
            '/usr/local/include',
            '/opt/local/include',
            '/opt/homebrew/include',
        ]))
    else:
        # Linux
        config.set('sundials', 'inc', ';'.join([
            '/usr/local/include',
        ]))

    # Locations of OpenCL libraries
    config.add_section('opencl')
    config.set('opencl',
               '# Location of opencl shared libary files (.so, .dll, .dylib).')
    config.set('opencl', '# Multiple paths can be set using ; as separator.')

    if system == 'Windows':     # pragma: no linux cover
        # All windowses
        c64 = 'C:\\Program Files\\'
        config.set('opencl', 'lib', ';'.join([
            c64 + 'Intel\\OpenCL SDK\\6.3\\lib\\x64',
            c64 + 'AMD APP SDK\\2.9\\bin\\x64',
            c64 + 'NVIDIA GPU Computing Toolkit\CUDA\\v11.8\\lib\\x64',
        ]))
    else:
        # Linux and mac
        paths = [
            '/usr/lib64',
            '/usr/lib64/nvidia',
            '/usr/local/cuda/lib64',
        ]
        if system == 'Darwin':  # pragma: no linux cover
            paths.append('/System/Library/Frameworks')
        config.set('opencl', 'lib', ';'.join(paths))

    config.set('opencl', '# Location of opencl header files (.h).')
    config.set('opencl', '# Multiple paths can be set using ; as separator.')

    if system == 'Windows':     # pragma: no linux cover
        # All windowses
        c64 = 'C:\\Program Files\\'
        config.set('opencl', 'inc', ';'.join([
            c64 + 'Intel\\OpenCL SDK\\6.3\\include',
            c64 + 'AMD APP SDK\\2.9\\include',
            c64 + 'NVIDIA GPU Computing Toolkit\\CUDA\\v11.8\\include',
        ]))
    else:
        # Linux and mac
        paths = [
            '/usr/include/CL',
            '/usr/local/cuda/include',
        ]
        if system == 'Darwin':  # pragma: no linux cover
            paths.append('/System/Library/Frameworks')
        config.set('opencl', 'inc', ';'.join(paths))

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

    # In Python <3.2, strings like "x ; y" are treated as "x" followed by a
    # comment. These shouldn't appear in myokit ini files!
    if sys.hexversion < 0x03020000:     # pragma: no cover
        with open(path, 'r') as f:
            lines = f.readlines()

        import re
        inline_comment = re.compile('[\w]+[\s]*=[\s]*.+?\s+(;)')
        for i, line in enumerate(lines):
            m = inline_comment.match(line)
            if m is not None:
                x = m.start(1) - 1
                raise ImportError(
                    'Unsupported syntax found in ' + str(path) + ' on line '
                    + str(1 + i) + ', character ' + str(x) + ', semicolons (;)'
                    + ' must not be preceded by whitespace: ```'
                    + line.strip() + '```.')
        del lines, inline_comment

    # Create the config parser (no value allows comments)
    config = ConfigParser(allow_no_value=True)

    # Make the parser case sensitive (need for unix paths!)
    config.optionxform = str

    # Parse the config file
    config.read(path)

    # Compatibility options
    if config.has_option('compatibility', 'no_capture'):
        x = config.get('compatibility', 'no_capture').strip().lower()
        if x == 'true':
            myokit.COMPAT_NO_CAPTURE = True
        elif x == 'false':
            myokit.COMPAT_NO_CAPTURE = False
        elif x != '':
            warnings.warn(
                'Invalid setting in myokit.ini. Expected values for no_capture'
                ' are true, false, or not set (empty), but got: ' + x)

    if config.has_option('compatibility', 'no_fd_capture'):
        x = config.get('compatibility', 'no_fd_capture').strip().lower()
        if x == 'true':
            myokit.COMPAT_NO_FD_CAPTURE = True
        elif x == 'false':
            myokit.COMPAT_NO_FD_CAPTURE = False
        elif x != '':
            warnings.warn(
                'Invalid setting in myokit.ini. Expected values for'
                ' no_fd_capture are true, false, or not set (empty), but got: '
                + x)

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

    # GUI Backend
    if config.has_option('gui', 'backend'):
        x = config.get('gui', 'backend').strip().lower()
        if x == 'pyqt' or x == 'pyqt4':
            myokit.FORCE_PYQT4 = True
            myokit.FORCE_PYQT5 = False
            myokit.FORCE_PYSIDE = False
            myokit.FORCE_PYSIDE2 = False
        elif x == 'pyqt5':
            myokit.FORCE_PYQT4 = False
            myokit.FORCE_PYQT5 = True
            myokit.FORCE_PYSIDE = False
            myokit.FORCE_PYSIDE2 = False
        elif x == 'pyside':
            myokit.FORCE_PYQT4 = False
            myokit.FORCE_PYQT5 = False
            myokit.FORCE_PYSIDE = True
            myokit.FORCE_PYSIDE2 = False
        elif x == 'pyside2':
            myokit.FORCE_PYQT4 = False
            myokit.FORCE_PYQT5 = False
            myokit.FORCE_PYSIDE = False
            myokit.FORCE_PYSIDE2 = True
        elif x != '':
            warnings.warn(
                'Invalid setting in myokit.ini. Expected values for backend'
                ' are pyqt, pyqt4, pyqt5, pyside, or pyside2. Got: ' + x)

    # Sundials libraries, header files, and version
    if config.has_option('sundials', 'lib'):
        myokit.SUNDIALS_LIB.extend(_path_list(config.get('sundials', 'lib')))
    if config.has_option('sundials', 'inc'):
        myokit.SUNDIALS_INC.extend(_path_list(config.get('sundials', 'inc')))

    # Dynamically add embedded sundials paths for windows
    if platform.system() == 'Windows':  # pragma: no linux cover
        _dynamically_add_embedded_sundials_win()

    # OpenCL libraries and header files
    if config.has_option('opencl', 'lib'):
        myokit.OPENCL_LIB.extend(_path_list(config.get('opencl', 'lib')))
    if config.has_option('opencl', 'inc'):
        myokit.OPENCL_INC.extend(_path_list(config.get('opencl', 'inc')))


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


def _path_list(text):
    return [
        os.path.expandvars(os.path.expanduser(x))
        for x in [x.strip() for x in text.split(';')] if x != '']


# Load settings
_load()
