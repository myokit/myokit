#
# System information class.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import os
import sys
import platform
import importlib

import myokit


def system(live_printing=False):
    """
    Returns a (long) string with system information.

    If ``live_printing`` is set to ``True``, no string is returned but the
    results are printed to screen as they come in.
    """

    # Print directly to screen or store in array
    if not live_printing:
        out = []
    else:
        # Create fake list interface that just prints
        class Out(object):
            def append(self, x):
                print(x)

            def extend(self, xs):
                print('\n'.join(xs))

        out = Out()

    # Basic system information
    out.append('== System information ==')
    out.append('Myokit: ' + myokit.version(raw=True))
    ver = iter(sys.version.splitlines())
    out.append('Python: ' + next(ver))
    out.extend([' ' * 8 + v for v in ver])
    out.append(
        'OS: ' + platform.system()
        + ' (' + sys.platform + ', ' + os.name + ')')
    out.append('    ' + platform.platform())
    out.append('')

    # Python requirements
    out.append('== Python requirements ==')
    out.append('NumPy: ' + _module_version('numpy'))
    out.append('SciPy: ' + _module_version('scipy'))
    out.append('Matplotlib: ' + _module_version('matplotlib'))
    out.append('ConfigParser: ' + _module_version('configparser'))
    out.append('Setuptools: ' + _module_version('setuptools'))
    out.append('')

    # Python extras
    out.append('== Python extras ==')
    out.append('SymPy: ' + _module_version('sympy'))
    out.append('MoviePy: ' + _module_version('moviepy'))
    out.append('')

    # GUI toolkits
    out.append('== GUI ==')

    try:    # pragma: no cover
        from PyQt5.QtCore import QT_VERSION_STR
        out.append('PyQt5: ' + QT_VERSION_STR)
        out.append('  Sip: ' + _module_version('sip'))
        del QT_VERSION_STR
    except ImportError:
        out.append('PyQt5: Not found')

    try:    # pragma: no cover
        from PyQt4.QtCore import QT_VERSION_STR
        out.append('PyQt4: ' + QT_VERSION_STR)
        out.append('  Sip: ' + _module_version('sip'))
        del QT_VERSION_STR
    except ImportError:
        out.append('PyQt4: Not found')
    except RuntimeError:    # pragma: no cover
        # Happens if PyQt5 was also found
        out.append('PyQt4: OK')

    out.append('PySide: ' + _module_version('PySide'))
    out.append('PySide2: ' + _module_version('PySide2'))
    out.append('')

    # Development tools
    out.append('== Development tools ==')
    out.append('Sphinx: ' + _module_version('sphinx'))
    out.append('Flake8: ' + _module_version('flake8'))
    out.append('')

    # Simulation tools / compilation
    out.append('== Simulation tools ==')
    compiler = myokit.Compiler.info()
    if compiler is None:    # pragma: no cover
        out.append('Compiler: NOT FOUND')
        out.append('Sundials: Compiler not found')
        out.append('OpenCL: Compiler not found')
    else:
        out.append('Compiler: ' + compiler)
        out.append('Sundials: ' + (myokit.Sundials.version() or 'Not found'))

        opencl = myokit.OpenCL()
        if not opencl.supported():  # pragma: no cover
            out.append('OpenCL: No OpenCL support detected.')
        else:   # pragma: no cover
            devices = []
            for p in opencl.info().platforms:
                for d in p.devices:
                    devices.append(d.name + ' on ' + p.name)
            out.append('OpenCL: ' + str(len(devices)) + ' device(s) found')
            for d in devices:
                out.append('  ' + d)
            out.append('  Use `python -m myokit opencl` for more information.')

    if not live_printing:
        return '\n'.join(out)


def _module_version(module):
    """
    Checks if the given ``module`` is present, and attempts to return a string
    containing its version. If the module can't be found 'Not found' is
    returned. If the module is found, but the  version can't be detected, 'OK'
    is returned.
    """
    try:
        m = importlib.import_module(module)
    except ImportError:     # pragma: no cover
        return 'Not found'

    # NumPy, SciPy, SymPy
    try:
        return str(m.version.version)
    except AttributeError:  # pragma: no cover
        pass

    # Matplotlib & others
    try:
        return str(m.__version__)
    except AttributeError:  # pragma: no cover
        pass

    # Setuptools
    try:
        return str(m.version.__version__)
    except AttributeError:  # pragma: no cover
        pass

    # Not found
    return 'OK'
