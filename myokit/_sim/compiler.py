#
# C Compiler information class
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import os

import myokit

# Path to C Source for Compiler info module
SOURCE_FILE = 'compiler.c'


class Compiler(myokit.CModule):
    """
    Tests for distutils C-compilation support.
    """
    # Unique id for this object
    _index = 0

    # Cached back-end object if compiled, False if compilation failed
    _instance = None

    # Cached compilation error messages
    _message = None

    # Guess at compiler
    _compiler = None

    def __init__(self):
        super(Compiler, self).__init__()
        # Create and cache back-end
        Compiler._index += 1

        # Define libraries
        libd = list()
        incd = list()
        incd.append(myokit.DIR_CFUNC)
        libs = []

        # Create back-end
        mname = 'myokit_compiler_info_' + str(Compiler._index)
        mname += '_' + str(myokit.pid_hash())
        fname = os.path.join(myokit.DIR_CFUNC, SOURCE_FILE)
        args = {'module_name': mname}
        try:
            Compiler._instance = self._compile(
                mname, fname, args, libs, libd, incd)
        except myokit.CompilationError as e:  # pragma: no cover
            Compiler._instance = False
            Compiler._message = str(e)

    @staticmethod
    def _get_instance():
        """
        Returns a cached back-end, creates and returns a new back-end or raises
        a :class:`NoCompilerError`.
        """
        # No instance? Create it
        if Compiler._instance is None:
            Compiler()

        # Instance creation failed, raise exception
        if Compiler._instance is False:  # pragma: no cover
            raise NoCompilerError(
                'Could not detect C compiler.\n' + Compiler._message)

        # Return instance
        return Compiler._instance

    @staticmethod
    def info(debug=False):
        """
        Returns a string with information about the compiler found on this
        system, or ``None`` if no compiler could be found.

        If ``debug`` is set to ``True``, compilation errors will be printed to
        stdout.
        """
        try:
            return Compiler._get_instance().compiler()
        except NoCompilerError as e:  # pragma: no cover
            if debug:
                print(e)
                if Compiler._message is None:
                    print('No further error message available.')
                else:
                    print(Compiler._message)
            return None


class NoCompilerError(myokit.MyokitError):
    """
    Raised when a compiler is required but not found.
    """

