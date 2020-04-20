#!/usr/bin/env python3
#
# Runs tests for Myokit.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
# Parts of this test script are based on the test script for Pints
# See: https://github.com/pints-team/pints
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import argparse
import fnmatch
import gc
import importlib
import inspect
import os
import re
import subprocess
import sys
import traceback
import unittest


def coverage(args):
    """
    Runs the unit tests and prints a coverage report.
    """
    try:
        print('Gathering coverage data')
        p = subprocess.Popen([
            'python3',
            '-m',
            'coverage',
            'run',
            'run-tests.py',
            'unit',
        ])
        try:
            ret = p.wait()
        except KeyboardInterrupt:
            try:
                p.terminate()
            except OSError:
                pass
            p.wait()
            print('')
            sys.exit(1)
        if ret != 0:
            print('FAILED')
            sys.exit(ret)

        print('Generating coverage report.')
        p = subprocess.Popen([
            'python3',
            '-m',
            'coverage',
            'report',
            '-m',
            '--skip-covered',
        ])
        p.wait()

    finally:
        # Remove coverage file
        if os.path.isfile('.coverage'):
            os.remove('.coverage')


def _doc_coverage_check_completeness(classes, functions):
    """
    Check all classes and functions exposed by Myokit are included in the docs
    somewhere.

    This method is based on one made by Fergus Cooper for PINTS.
    See https://github.com/pints-team/pints
    """

    doc_files = []
    for root, dirs, files in os.walk(os.path.join('docs', 'source')):
        for file in files:
            if file.endswith('.rst'):
                doc_files.append(os.path.join(root, file))

    # Regular expression that would find either 'module' or 'currentmodule':
    # this needs to be prepended to the symbols as x.y.z != x.z
    regex_module = re.compile(r'\.\.\s*\S*module\:\:\s*(\S+)')

    # Regular expressions to find autoclass and autofunction specifiers
    regex_class = re.compile(r'\.\.\s*autoclass\:\:\s*(\S+)')
    regex_funct = re.compile(r'\.\.\s*autofunction\:\:\s*(\S+)')

    # Identify all instances of autoclass and autofunction in all rst files
    doc_classes = []
    doc_functions = []
    for doc_file in doc_files:
        with open(doc_file, 'r') as f:
            # We need to identify which module each class or function is in
            module = ''
            for line in f.readlines():
                m_match = re.search(regex_module, line)
                c_match = re.search(regex_class, line)
                f_match = re.search(regex_funct, line)
                if m_match:
                    module = m_match.group(1) + '.'
                elif c_match:
                    doc_classes.append(module + c_match.group(1))
                elif f_match:
                    doc_functions.append(module + f_match.group(1))

    # Check if documented symbols match known classes and functions
    classes = set(classes)
    functions = set(functions)
    doc_classes = set(doc_classes)
    doc_functions = set(doc_functions)

    undoc_classes = classes - doc_classes
    undoc_functions = functions - doc_functions
    extra_classes = doc_classes - classes
    extra_functions = doc_functions - functions

    # Compare the results
    if undoc_classes:
        n = len(undoc_classes)
        printline()
        print('Found (' + str(n) + ') classes without documentation:')
        print('\n'.join(
            '  ' + colored('warning', y) for y in sorted(undoc_classes)))
    if undoc_functions:
        n = len(undoc_functions)
        printline()
        print('Found (' + str(n) + ') functions without documentation:')
        print('\n'.join(
            '  ' + colored('warning', y) for y in sorted(undoc_functions)))
    if extra_classes:
        n = len(extra_classes)
        printline()
        print('Found (' + str(n) + ') documented but unknown classes:')
        print('\n'.join(
            '  ' + colored('warning', y) for y in sorted(extra_classes)))
    if extra_functions:
        n = len(extra_functions)
        printline()
        print('Found (' + str(n) + ') documented but unknown classes:')
        print('\n'.join(
            '  ' + colored('warning', y) for y in sorted(extra_functions)))
    n = (len(undoc_classes) + len(undoc_functions)
         + len(extra_classes) + len(extra_functions))
    printline()
    print('Found total of (' + str(n) + ') mismatches.')

    return n == 0


def _doc_coverage_check_index(modules, classes, functions):
    """
    Checks the documentation index to see if everything is listed and to see if
    nothing is listed that shouldn't be listed.
    """

    def scan_docs(path):
        """ Scan api_index docs """
        r = re.compile('(class|meth):`([^`]*)`')

        def read_file(fpath, classes, functions):
            with open(fpath, 'r') as f:
                for m in r.finditer(f.read()):
                    xtype = m.string[m.start(1):m.end(1)]
                    xname = m.string[m.start(2):m.end(2)]
                    if xtype == 'class':
                        classes.add(xname)
                    else:
                        functions.add(xname)

        # Scan directory, read files
        files = set()
        classes = set()
        functions = set()
        for fname in os.listdir(path):
            fpath = os.path.join(path, fname)
            if not os.path.isfile(fpath):
                continue
            if fname[-4:] != '.rst':
                continue
            read_file(fpath, classes, functions)
            files.add(fpath)
        # Return results
        return files, classes, functions

    # Scan api/index files
    print('Reading doc files for api_index')
    docdir = os.path.join('docs', 'source', 'api_index')
    doc_files, doc_classes, doc_functions = scan_docs(docdir)
    print(
        'Found (' + str(len(doc_files)) + ') files, identified ('
        + str(len(doc_classes)) + ') classes and (' + str(len(doc_functions))
        + ') functions.')

    # Compare the results
    n = 0
    x = classes - doc_classes
    if x:
        n += len(x)
        printline()
        print('Found (' + str(len(x)) + ') classes not in doc index:')
        print('\n'.join('  ' + colored('warning', y) for y in sorted(x)))
    x = functions - doc_functions
    if x:
        n += len(x)
        printline()
        print('Found (' + str(len(x)) + ') functions not in doc index:')
        print('\n'.join('  ' + colored('warning', y) for y in sorted(x)))
    x = doc_classes - classes
    if x:
        n += len(x)
        printline()
        print('Found (' + str(len(x)) + ') indexed, unknown classes:')
        print('\n'.join('  ' + colored('warning', y) for y in sorted(x)))
    x = doc_functions - functions
    if x:
        n += len(x)
        printline()
        print('Found (' + str(len(x)) + ') indexed, unknown functions:')
        print('\n'.join('  ' + colored('warning', y) for y in sorted(x)))
    printline()
    print('Found total of (' + str(n) + ') mismatches.')

    return n == 0


def _doc_coverage_get_modules_classes_functions():
    """
    Scans Myokit and returns a list of modules, a list of classes, and a
    list of functions.
    """
    print('Finding Myokit modules...')

    def find_modules(root, modules=[]):
        """ Find all modules in the given directory. """

        # Get root as module
        module_root = root.replace('/', '.')

        # Check if this is a module
        if os.path.isfile(os.path.join(root, '__init__.py')):
            modules.append(module_root)
        else:
            return modules

        # Look for submodules
        for name in os.listdir(root):
            if name[:1] == '_' or name[:1] == '.':
                continue
            path = os.path.join(root, name)
            if os.path.isdir(path):
                find_modules(path, modules)
            else:
                base, ext = os.path.splitext(name)
                if ext == '.py':
                    modules.append(module_root + '.' + base)

        # Return found
        return modules

    # Get modules
    import myokit
    modules = find_modules('myokit')

    # Import all modules
    for module in modules:
        importlib.import_module(module)

    # Find modules, classes, and functions
    def scan(module, root, pref, modules, classes, functions):
        nroot = len(root)
        for name, member in inspect.getmembers(module):
            if name[0] == '_':
                # Don't include private members
                continue

            # Get full name
            full_name = pref + name

            # Module
            if inspect.ismodule(member):
                try:
                    # Don't scan external modules
                    if member.__file__[0:nroot] != root:
                        continue
                except AttributeError:
                    # Built-ins have no __file__ and should not be included
                    continue
                if full_name in modules:
                    continue
                modules.add(full_name)
                mpref = full_name + '.'
                mroot = os.path.join(root, name)
                scan(member, mroot, mpref, modules, classes, functions)

            # Class
            elif inspect.isclass(member):
                if member.__module__.startswith('myokit.'):
                    classes.add(full_name)

            # Function
            elif inspect.isfunction(member):
                if member.__module__.startswith('myokit.'):
                    functions.add(full_name)

        return

    # Scan and return
    print('Scanning Myokit modules...')
    module = myokit
    modules = set()
    classes = set()
    functions = set()
    root = os.path.dirname(module.__file__)
    pre = module.__name__ + '.'
    scan(module, root, pre, modules, classes, functions)

    print(
        'Found (' + str(len(modules)) + ') modules, identified ('
        + str(len(classes)) + ') classes and (' + str(len(functions))
        + ') functions.')

    return modules, classes, functions


def doc_tests(args):
    """
    Checks if the documentation can be built, runs all doc tests, exits if
    anything fails.
    """
    print('Checking documentation coverage.')
    # Scan Myokit modules for classes and functions
    modules, classes, functions = _doc_coverage_get_modules_classes_functions()

    # Check if they're all in the index
    ok = _doc_coverage_check_index(modules, classes, functions)

    # Check if they're all shown somewhere
    ok = ok and _doc_coverage_check_completeness(classes, functions)

    # Terminate if failed
    if not ok:
        sys.exit(1)


    print('Building docs and running doctests.')
    p = subprocess.Popen([
        'sphinx-build',
        '-b',
        'doctest',
        'docs/source',
        'docs/build/html',
        '-W',
    ])
    try:
        ret = p.wait()
    except KeyboardInterrupt:
        try:
            p.terminate()
        except OSError:
            pass
        p.wait()
        print('')
        sys.exit(1)
    if ret != 0:
        print('FAILED')
        sys.exit(ret)


def examples_pub(args):
    """
    Runs all publication examples, exits if one of them fails.
    """
    # Get publications directory
    path = os.path.join('myokit', 'tests', 'publications')

    # PBMB 2016. Myokit: A simple interface to cardiac cellular
    # electrophysiology
    if test_mmt_files(os.path.join(path, 'pbmb-2016')):
        sys.exit(1)


def examples_web(args):
    """
    Runs all web examples, exits if one of them fails.
    """
    # Get web directory
    path = os.path.join(
        'dev',
        'web',
        'html',
        'static',
        'download',
        'examples',
    )
    if not os.path.isdir(path):
        print('Web examples not found. Skipping.')
        return

    # Run, exit on error
    if test_mmt_files(path):
        sys.exit(1)


def flake8():
    """
    Runs flake8 in a subprocess, exits if it doesn't finish.
    """
    print('Running flake8 ... ')
    sys.stdout.flush()
    p = subprocess.Popen(['flake8', '-j4'], stderr=subprocess.PIPE)
    try:
        ret = p.wait()
    except KeyboardInterrupt:
        try:
            p.terminate()
        except OSError:
            pass
        p.wait()
        print('')
        sys.exit(1)
    if ret == 0:
        print('ok')
    else:
        print('FAILED')
        sys.exit(ret)


def printline():
    """ Utility method for printing horizontal lines. """
    print('-' * 60)


def colored(color, text):
    """ Utility method for printing colored text. """
    colors = {
        'normal': '\033[0m',
        'warning': '\033[93m',
        'fail': '\033[91m',
        'bold': '\033[1m',
        'underline': '\033[4m',
    }
    return colors[color] + str(text) + colors['normal']


def suite_full(args):
    """
    Runs the full test suite, exits if anything fails.
    """
    # Set arguments for unit()
    flake8()
    doc_coverage(args)
    doc_tests(args)
    coverage(args)
    examples_web(args)
    examples_pub(args)


def suite_minimal(args):
    """
    Runs a minimal set of tests, exits if anything fails.
    """
    flake8()
    doc_coverage(args)
    doc_tests(args)
    coverage(args)


def test_mmt_files(path):
    """
    Run all the `mmt` files in a given directory `path`, returns 0 iff nothing
    goes wrong.
    """
    import myokit

    # Get absolute path
    path = os.path.abspath(path)

    # Show what we're running
    print('Running mmt files for:')
    print('  ' + path)

    # Get current dir
    current_dir = os.path.abspath(os.path.dirname(__file__))

    # Error states
    error = 0

    # Change dir, make sure to change back again
    try:
        # Change to dir
        os.chdir(path)

        # Run all
        glob = '*.mmt'
        for fn in fnmatch.filter(os.listdir(path), glob):
            # Load and run
            try:
                print('Loading ' + fn)
                m, p, x = myokit.load(os.path.join(path, fn))
                try:
                    print('Running...')
                    myokit.run(m, p, x)
                except Exception:
                    error = 1
                    print(traceback.format_exc())
                del(m, p, x)
            except Exception:
                print('Unable to load.')
                print(traceback.format_exc())

            # Tidy up
            gc.collect()
            print('-' * 70)

            # Quit on error
            if error:
                return error
    finally:
        # Change back
        os.chdir(current_dir)

    # Return error status 0
    return error


def unit(args):
    """
    Runs unit tests, exits if anything fails.
    """
    print('Running tests with ' + sys.executable)

    suite = unittest.defaultTestLoader.discover(
        os.path.join('myokit', 'tests'), pattern='test*.py')
    res = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if res.wasSuccessful() else 1)


if __name__ == '__main__':

    # Set up argument parsing
    parser = argparse.ArgumentParser(
        description='Run unit tests for Myokit.',
        epilog='To run individual unit tests, use e.g.'
               ' $ tests/test_parser.py',
    )
    subparsers = parser.add_subparsers(help='commands')

    # Disable matplotlib output
    parser.add_argument(
        '--nompl',
        action='store_true',
        help='Disable matplotlib output.',
    )

    # Coverage
    coverage_parser = subparsers.add_parser(
        'coverage', help='Run unit tests and print a coverage report.')
    coverage_parser.set_defaults(func=coverage)

    # Doctests
    doc_parser = subparsers.add_parser(
        'doc',
        help='Test documentation cover, building, and doc tests.')
    doc_parser.set_defaults(func=doc_tests)

    # Full test suite
    full_parser = subparsers.add_parser(
        'full', help='Run all tests (including graphical ones)')
    full_parser.set_defaults(func=suite_full)

    # Minimal test suite
    minimal_parser = subparsers.add_parser(
        'minimal', help='Run minimal checks (unit tests, flake8, docs)')
    minimal_parser.set_defaults(func=suite_minimal)

    # Publication examples
    pub_parser = subparsers.add_parser(
        'pub', help='Run publication examples.')
    pub_parser.set_defaults(func=examples_pub)

    # Unit tests
    unit_parser = subparsers.add_parser('unit', help='Run unit tests')
    unit_parser.set_defaults(func=unit)

    # Web examples
    web_parser = subparsers.add_parser(
        'web', help='Run web examples.')
    web_parser.set_defaults(func=examples_web)

    # Parse!
    args = parser.parse_args()
    if args.nompl:
        print('Disabling matplotlib output')
        import matplotlib
        matplotlib.use('template')
    if 'func' in args:
        args.func(args)
    else:
        parser.print_help()

