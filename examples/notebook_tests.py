#!/usr/bin/env python3
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
# Some of the scripts in this file were adapted from PINTS, which is shared
# under a BSD 3-Clause License. See https://github.com/pints-team/pints
#
import myokit
import nbconvert
import os
import subprocess
import sys


def check_index(books):
    """ Check that every notebook is included in the index. """
    print('Checking index...')

    # Index file is in ./examples/README.md
    index_file = 'README.md'
    with open(index_file, 'r') as f:
        index_contents = f.read()

    # Find which are not indexed
    not_indexed = [book for book in books if book not in index_contents]

    # Report any failures
    if len(not_indexed) > 0:
        print('FAIL: Unindexed notebooks')
        for book in sorted(not_indexed):
            print('  ' + str(book))
        sys.exit(1)
    else:
        print('ok: All (' + str(len(books)) + ') notebooks are indexed.')


def check_running(books):
    """ Runs all notebooks, and exits if one fails. """

    # Ignore books with deliberate errors, but check they still exist
    ignore_list = [
    ]

    books = set(books) - set(ignore_list)

    # Scan and run
    print('Testing notebooks')
    failed = []
    for book in books:
        if not test_notebook(book):
            failed.append(book)
    if failed:
        print('FAIL: Errors encountered in notebooks')
        for book in failed:
            print('  ' + str(book))
        sys.exit(1)
    else:
        print('ok: Successfully ran all (' + str(len(books)) + ') notebooks.')


def list_notebooks(root='.', recursive=True, notebooks=None):
    """ Returns a list of all notebooks in a directory. """
    if notebooks is None:
        notebooks = []
    for filename in os.listdir(root):
        path = os.path.join(root, filename)

        # Add notebook
        if os.path.splitext(path)[1] == '.ipynb':
            notebooks.append(path)

        # Recurse into subdirectories
        elif recursive and os.path.isdir(path):
            # Ignore hidden directories
            if filename[:1] == '.':
                continue
            list_notebooks(path, recursive, notebooks)

    return notebooks


def test_notebook(path):
    """ Tests a notebook in a subprocess, exists if it doesn't finish. """
    b = myokit.Benchmarker()
    print('Running ' + path + ' ... ', end='')
    sys.stdout.flush()

    # Load notebook, convert to python
    e = nbconvert.exporters.PythonExporter()
    code, _ = e.from_filename(path)

    # Remove coding statement, if present
    code = '\n'.join([x for x in code.splitlines() if x[:9] != '# coding'])

    # Tell matplotlib not to produce any figures
    env = os.environ.copy()
    env['MPLBACKEND'] = 'Template'

    # Run in subprocess
    cmd = [sys.executable, '-c', code]
    try:
        p = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env
        )
        stdout, stderr = p.communicate()
        # TODO: Use p.communicate(timeout=3600) if Python3 only
        if p.returncode != 0:
            # Show failing code, output and errors before returning
            print('ERROR')
            print('-- script ' + '-' * (79 - 10))
            for i, line in enumerate(code.splitlines()):
                j = str(1 + i)
                print(j + ' ' * (5 - len(j)) + line)
            print('-- stdout ' + '-' * (79 - 10))
            print(stdout)
            print('-- stderr ' + '-' * (79 - 10))
            print(stderr)
            print('-' * 79)
            return False
    except KeyboardInterrupt:
        p.terminate()
        print('ABORTED')
        sys.exit(1)

    # Successfully run
    print('ok (' + b.format(b.time()) + ')')
    return True


if __name__ == '__main__':
    books = list_notebooks()
    print('Found ' + str(len(books)) + ' notebook(s).')
    check_index(books)
    check_running(books)
