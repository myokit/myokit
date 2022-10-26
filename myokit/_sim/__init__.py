#
# This hidden module contains the core functions dealing with simulations and
# the data they generate.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

# Library imports
import os
import platform
import sys
import tempfile
import threading
import timeit
import traceback


# Windows fix: On win7 with MinGW, when running distutils from Qt the
# (deprecated) os.popen command fails. The docs suggest to replace calls to
# popen with subprocess.Popen. The following wrapper implements this
# dynamically.
if platform.system() == 'Windows':  # pragma: no linux cover
    import subprocess  # noqa

    def _ospop(command, mode='r', bufsize=0):
        if mode == 'r':
            return subprocess.Popen(
                command, shell=True, bufsize=bufsize, stdout=subprocess.PIPE
            ).stdout
        else:
            return subprocess.Popen(
                command, shell=True, bufsize=bufsize, stdin=subprocess.PIPE
            ).stdin
    os.popen = _ospop


# Setuptools imports
from setuptools import setup, Extension  # noqa


# Myokit imports
import myokit       # noqa
import myokit.pype  # noqa


# Dynamic module finding and loading in Python 3.5+ and younger
if sys.hexversion >= 0x03050000:
    import importlib.machinery
    import importlib

    def load_module(name, path):
        spec = importlib.machinery.PathFinder.find_spec(name, [path])
        module = importlib.util.module_from_spec(spec)
        return module

else:  # pragma: no python 3 cover
    import imp

    def load_module(name, path):
        (f, pathname, description) = imp.find_module(name, [path])
        f.close()
        return imp.load_dynamic(name, pathname)


class CModule(object):
    """
    Abstract base class for classes that dynamically create and compile a
    back-end C-module.
    """
    def __init__(self):
        self._debug_file_count = 0

    def _compile(self, name, template, variables, libs, libd=None, incd=None,
                 carg=None, larg=None, store_build=False,
                 continue_in_debug_mode=False):
        """
        Compiles a source ``template`` with the given ``variables`` into a
        module called ``name``, then imports it and returns a reference to the
        imported module.

        Arguments:

        ``name``
            The name of the generated module (used when importing)
        ``template``
            A template to evaluate
        ``variables``
            Variables to pass in to the template
        ``libs``
            A list of C libraries to link to, e.g.
            ``libs=['sundials_cvodes']``.
        ``libd``
            A list of directories to search for shared library objects, or
            ``None``.
        ``incd``
            A list of directories to search for header files, or ``None``.
        ``carg``
            A list of extra compiler arguments (e.g. ``carg=['-Wall']), or
            ``None``.
        ``larg``
            A list of extra linker arguments (e.g.
            ``larg=['-framework', 'OpenCL']``), or ``None``.
        ``store_build``
            If set to ``False`` (the default), the method will delete the
            temporary directory that the module was built in.
        ``continue_in_debug_mode``
            If ``myokit.DEBUG_SG`` or ``myokit.DEBUG_WG`` are set, the
            generated code will be printed to screen and/or written to disk,
            and ``sys.exit(1)`` will be called. Set ``continue_in_debug_mode``
            to ``True`` to skip the exitting and keep going instead.

        Returns a tuple ``(module, build_path)``, where ``module`` is the
        compiled and imported module, and ``build_path`` is either ``None``
        (the default) or the path to a temporary directory that the build files
        are stored in.

        """
        # Show and/or write code in debug mode
        if myokit.DEBUG_SG or myokit.DEBUG_WG:  # pragma: no cover
            if myokit.DEBUG_SG:
                self._debug_show(template, variables)
            else:
                self._debug_write(template, variables)
            if not continue_in_debug_mode:
                sys.exit(1)

        # Write to temp dir and compile
        src_file = self._source_file()
        working_dir = os.getcwd()
        d_cache = tempfile.mkdtemp('myokit')
        d_build = None
        try:
            # Create build directory
            if store_build:
                # Create separate build directory
                d_build = tempfile.mkdtemp('myokit_build')
            else:
                d_build = os.path.join(d_cache, 'build')
                os.makedirs(d_build)

            # Export c file
            src_file = os.path.join(d_cache, src_file)
            self._export_inner(template, variables, src_file)

            # Ensure headers can be read from myokit/_sim
            if incd is None:
                incd = []
            incd.append(myokit.DIR_CFUNC)

            # Inputs must all be strings
            name = str(name)
            src_file = str(src_file)
            incd = [str(x) for x in incd]
            libd = None if libd is None else [str(x) for x in libd]
            libs = None if libs is None else [str(x) for x in libs]
            carg = None if carg is None else [str(x) for x in carg]
            larg = None if larg is None else [str(x) for x in larg]

            # Show warnings
            if myokit.DEBUG_SC:
                if carg is None:
                    carg = []
                carg.append('-Wall')
                if platform.system() == 'Linux':
                    carg.extend([
                        '-Wextra',
                        '-Wstrict-prototypes',
                        '-Wold-style-definition',
                        #'-Wmissing-prototypes',
                        #'-Wmissing-declarations',
                        '-Wdeclaration-after-statement',
                        '-Wconversion',
                        '-Wno-unused-parameter',
                    ])

            # Add runtime_library_dirs to prevent LD_LIBRARY_PATH errors on
            # unconventional linux sundials installations, but not on windows
            # as this can lead to a weird error in setuptools
            runtime = libd
            if platform.system() == 'Windows':  # pragma: no linux cover
                if libd is not None:
                    runtime = None

                    # Make windows search the libd directories
                    path = os.environ.get('path', '')
                    if path is None:
                        path = ''
                    to_add = [x for x in libd if x not in path]
                    os.environ['path'] = os.pathsep.join([path] + to_add)

                    # In Python 3.8+, they need to be registered with
                    # add_dll_directory too. This does not seem to be 100%
                    # consistent. AppVeyor tests pass when using
                    # add_dll_directory *without* adding the directories to the
                    # path, while installations via miniconda seem to need the
                    # path method too.
                    try:
                        # Fail if add_dll_directory not present
                        os.add_dll_directory

                        # Add DLL paths
                        for path in libd:
                            if os.path.isdir(path):
                                os.add_dll_directory(path)
                    except AttributeError:
                        pass

            # Create extension
            ext = Extension(
                name,
                sources=[src_file],
                libraries=libs,
                library_dirs=libd,
                runtime_library_dirs=runtime,
                include_dirs=incd,
                extra_compile_args=carg,
                extra_link_args=larg,
            )

            # Compile in build directory, catch output
            capture = not (myokit.DEBUG_SC or myokit.COMPAT_NO_CAPTURE)
            fd = not myokit.COMPAT_NO_FD_CAPTURE
            error, trace = None, None
            with myokit.tools.capture(fd=fd, enabled=capture) as s:
                try:
                    os.chdir(d_build)
                    setup(
                        name=name,
                        description='Temporary module',
                        ext_modules=[ext],
                        script_args=[
                            str('build_ext'),
                            str('--inplace'),
                        ])
                except (Exception, SystemExit) as e:  # pragma: no cover
                    error = e
                    trace = traceback.format_exc()
            if error is not None:  # pragma: no cover
                t = ['Unable to compile.', 'Error message:']
                t.append(str(error))
                t.append(trace)
                t.append('Compiler output:')
                captured = s.text().strip()
                t.extend(['    ' + x for x in captured.splitlines()])
                raise myokit.CompilationError('\n'.join(t))

            # Import module
            module = load_module(name, d_build)
            if store_build:
                return module, d_build
            return module

        except Exception:   # pragma: no cover
            # Delete build dir, if created separately
            if store_build and d_build is not None:
                myokit.tools.rmtree(d_build, silent=True)
            raise

        finally:
            # Revert changes to working directory
            os.chdir(working_dir)

            # Delete cache dir (and build dir, if not stored separetely)
            myokit.tools.rmtree(d_cache, silent=True)

    def _debug_show(self, template, variables):  # pragma: no cover
        """ Processes ``template`` and prints the output to screen. """
        print('\n'.join([
            '{:4d}'.format(1 + i) + ' ' + line
            for i, line in enumerate(
                self._export_inner(template, variables).splitlines())
        ]))

    def _debug_write(self, template, variables):  # pragma: no cover
        """ Processes ``template`` and writes the output to file. """
        self._debug_file_count += 1
        fname = 'debug-' + str(self._debug_file_count) + '.c'
        print('DEBUG: Writing generated code to ' + fname)
        with open(fname, 'w') as f:
            f.write(self._export_inner(template, variables))

    def _export(self, template, variables, target=None,
                continue_in_debug_mode=False):
        """
        Exports a source ``template`` with the given ``variables`` and returns
        the result as a string or writes it to the file given by ``target``.

        If ``myokit.DEBUG_SG`` or ``myokit.DEBUG_WG`` are set, the method will
        print the generated code to screen and/or write it to disk. Following
        this, it will terminate with exit code 1 unless
        ``continue_in_debug_mode`` is changed to ``True``.
        """
        # Show and/or write code in debug mode
        if myokit.DEBUG_SG or myokit.DEBUG_WG:  # pragma: no cover
            if myokit.DEBUG_SG:
                self._debug_show(template, variables)
            else:
                self._debug_write(template, variables)
            if not continue_in_debug_mode:
                sys.exit(1)

        return self._export_inner(
            template, variables, target, continue_in_debug_mode)

    def _export_inner(self, template, variables, target=None,
                      continue_in_debug_mode=False):
        """ Internal version of :meth:`_export`. """

        # Test if given module path is writable
        if target is not None:
            if os.path.exists(target):  # pragma: no cover
                # This shouldn't really occur: Writing is always done in a
                # temporary directory
                if os.path.isdir(target):
                    line = 'Can\'t create output file. A directory exists at '
                    line += format_path(target)
                    raise IOError(line)
            # Open output file
            handle = open(target, 'w')

        # Create source
        p = myokit.pype.TemplateEngine()
        if target is not None:
            p.set_output_stream(handle)

        try:
            result = None
            result = p.process(template, variables)
        except myokit.pype.PypeError:  # pragma: no cover
            # Not included in cover, because this can only happen if the
            # template code is wrong, i.e. during development.
            msg = ['An error ocurred while processing the template']
            msg.append(traceback.format_exc())
            d = p.error_details()
            if d:
                msg.append(d)
            raise myokit.GenerationError('\n'.join(msg))
        finally:
            if target is not None:
                handle.close()

        return result

    def _source_file(self):
        """
        Returns a name for the source file created and compiled for this
        module.
        """
        return 'source.c'


class CppModule(CModule):
    """
    Extends the :class:`CModule` class and adds C++ support.
    """
    def _source_file(self):
        return 'source.cpp'


def pid_hash():
    """
    Returns a positive integer hash that depends on the current time as well as
    the process and thread id, so that it's likely to return a different number
    when called twice.
    """
    pid = 1 + os.getpid()                       # Range 0 to 99999
    tid = threading.current_thread().ident      # Non-zero integer
    x = pid * tid * timeit.default_timer()
    return abs(hash(str(x - int(x))))

