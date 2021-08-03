#
# Sundials information class
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import logging
import os

import myokit

# Path to C Source for Sundials info module
SOURCE_FILE = 'sundials.c'


class Sundials(myokit.CModule):
    """
    Tests for Sundials/Sundials support.
    """
    # Unique id for this object
    _index = 0

    # Cached back-end object if compiled, False if compilation failed
    _instance = None

    # Cached compilation error messages
    _message = None

    # Version of Sundials found
    _version = None

    def __init__(self):
        super(Sundials, self).__init__()
        # Create and cache back-end
        Sundials._index += 1

        # Define libraries
        libd = list(myokit.SUNDIALS_LIB)
        incd = list(myokit.SUNDIALS_INC)
        incd.append(myokit.DIR_CFUNC)
        libs = []

        # Create Sundials back-end
        mname = 'myokit_sundials_info_' + str(Sundials._index)
        mname += '_' + str(myokit.pid_hash())
        fname = os.path.join(myokit.DIR_CFUNC, SOURCE_FILE)
        args = {'module_name': mname}
        try:
            Sundials._instance = self._compile(
                mname, fname, args, libs, libd, incd)
        except myokit.CompilationError as e:  # pragma: no cover
            Sundials._instance = False
            Sundials._message = str(e)

    @staticmethod
    def _get_instance():
        """
        Returns a cached back-end, creates and returns a new back-end or raises
        a :class:`NoSundialsError`.
        """
        # No instance? Create it
        if Sundials._instance is None:
            Sundials()

        # Instance creation failed, raise exception
        if Sundials._instance is False:  # pragma: no cover
            raise NoSundialsError(
                'Sundials support not found.\n' + Sundials._message)
        # Return instance
        return Sundials._instance

    #@staticmethod
    #def supported():
    #    """
    #    Returns ``True`` if Sundials support has been detected on this system.
    #    """
    #    try:
    #        Sundials._get_instance()
    #        return True
    #    except NoSundialsError:
    #        return False

    @staticmethod
    def version():
        """
        Returns the detected Sundials version on this system, or None if no
        version of Sundials was found.
        """
        try:
            return Sundials._get_instance().sundials_version()
        except NoSundialsError:  # pragma: no cover
            return None
        except IOError:  # pragma: no cover
            # This is an annoying read-the-docs error. It seems to install
            # myokit, but then run a different version for the docs? As a
            # result, it can't find sundials.c and the build fails.
            return None

    @staticmethod
    def version_int():
        """
        Returns a sundials version number as an integer, or None if no version
        number could be detected.
        """
        # Get version from sundials header
        version = Sundials.version()
        if version is not None:
            try:
                # Version can be x.y.z-dev
                if '-' in version:  # pragma: no cover
                    version = version[:version.index('-')]
                version = [int(x) for x in version.split('.')]
                version = version[0] * 10000 + version[1] * 100 + version[2]
            except Exception:   # pragma: no cover
                log = logging.getLogger(__name__)
                log.warning(
                    'Unable to parse sundials version: ' + str(version))
                version = None
        return version


class NoSundialsError(myokit.MyokitError):
    """
    Raised when Sundials is required by no compatible Sundials installation can
    be found.
    """

