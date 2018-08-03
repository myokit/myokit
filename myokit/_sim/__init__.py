#
# This hidden module contains the core functions dealing with simulations and
# the data they generate.
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

# Library imports
import os
import sys
import shutil
import platform
import tempfile
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
import myokit  # noqa
import myokit.pype as pype  # noqa


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
    def _code(self, tpl, tpl_vars, line_numbers=False):  # pragma: no cover
        """
        Returns the code that would be created by the equivalent call to
        :meth:`_compile()`.
        """
        # This is a debugging/development method, so not hit in cover checking
        if line_numbers:
            lines = []
            i = 1
            for line in self._export(tpl, tpl_vars).split('\n'):
                lines.append('{:4d}'.format(i) + ' ' + line)
                i += 1
            return '\n'.join(lines)
        else:
            return self._export(tpl, tpl_vars)

    def _compile(
            self, name, tpl, tpl_vars, libs, libd=None, incd=None, flags=None):
        """
        Compiles a source template into a module and returns it.

        The module's name is specified by ``name``.

        The template to compile is given by ``tpl``, while any variables
        required to process the template should be given as the dict
        ``tpl_vars``.

        Any C libraries needed for compilation should be given in the sequence
        type ``libs``. Library dirs and include dirs can be passed in using
        ``libd`` and ``incd``. Extra compiler arguments can be given in the
        list ``flags``.
        """
        src_file = self._source_file()
        d_cache = tempfile.mkdtemp('myokit')
        try:
            # Create output directories
            d_build = os.path.join(d_cache, 'build')
            d_modul = os.path.join(d_cache, 'module')
            os.makedirs(d_build)
            os.makedirs(d_modul)

            # Export c file
            src_file = os.path.join(d_cache, src_file)
            self._export(tpl, tpl_vars, src_file)

            # Inputs must all be strings
            name = str(name)
            src_file = str(src_file)
            flags = None if flags is None else [str(x) for x in flags]
            libd = None if libd is None else [str(x) for x in libd]
            incd = None if incd is None else [str(x) for x in incd]
            libs = None if libs is None else [str(x) for x in libs]

            # Add runtime_library_dirs (to prevent LD_LIBRARY_PATH) errors on
            # unconventional linux sundials installations, but not on windows
            # as this can lead to a weird error in setuptools
            runtime = libd
            if (platform.system() == 'Windows'
                    and libd is not None):          # pragma: no linux cover
                runtime = None

                # Instead, add libd to path on windows
                try:
                    path = os.environ['path']
                except KeyError:
                    path = ''
                to_add = [x for x in libd if x not in path]
                if to_add:
                    os.environ['path'] = os.pathsep.join([path] + to_add)

            # Create extension
            ext = Extension(
                name,
                sources=[src_file],
                libraries=libs,
                library_dirs=libd,
                runtime_library_dirs=runtime,
                include_dirs=incd,
                extra_compile_args=flags,
            )

            # Compile, catch output
            with myokit.SubCapture() as s:
                try:
                    setup(
                        name=name,
                        description='Temporary module',
                        ext_modules=[ext],
                        script_args=[
                            str('build'),
                            str('--build-base=' + d_build),
                            str('install'),
                            str('--install-lib=' + d_modul),
                            str('--old-and-unmanageable'),
                        ])
                except (Exception, SystemExit) as e:
                    s.disable()
                    t = ['Unable to compile.', 'Error message:']
                    t.append(str(e))
                    t.append('Error traceback')
                    t.append(traceback.format_exc())
                    t.append('Compiler output:')
                    captured = s.text().strip()
                    t.extend(['    ' + x for x in captured.splitlines()])
                    raise myokit.CompilationError('\n'.join(t))
                finally:
                    egg = name + '.egg-info'
                    if os.path.exists(egg):
                        shutil.rmtree(egg)

            # Include module (and refresh in case 2nd model is loaded)
            return load_module(name, d_modul)

        finally:
            try:
                shutil.rmtree(d_cache)
            except Exception:   # pragma: no cover
                pass

    def _export(self, source, varmap, target=None):
        """
        Exports the given ``source`` to the file ``target`` using the variable
        mapping ``varmap``. If no target is given, the result is returned as a
        string.
        """
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
        p = pype.TemplateEngine()
        if target is not None:
            p.set_output_stream(handle)

        try:
            result = None
            result = p.process(source, varmap)
        except pype.PypeError:  # pragma: no cover
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

