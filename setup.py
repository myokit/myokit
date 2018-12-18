#
# SetupTools script for Myokit
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals
from setuptools import setup, find_packages


# Get version number
import os
import sys
sys.path.append(os.path.abspath('myokit'))
from _myokit_version import __version__ as version  # noqa
sys.path.pop()
del(os, sys)


# Load text for description and license
with open('README.md') as f:
    readme = f.read()


# Go!
setup(
    # Module name (lowercase)
    name='myokit',

    # Version
    version=version,

    description='A simple interface to cardiac cellular electrophysiology',

    long_description=readme,
    long_description_content_type='text/markdown',

    license='GNU General Public License version 3',

    author='Michael Clerx',

    author_email='michael@myokit.org',

    url='http://myokit.org',

    # Packages to include
    packages=find_packages(include=('myokit', 'myokit.*')),

    # Include non-python files (via MANIFEST.in)
    include_package_data=True,

    # Register myokit as a shell script
    entry_points={
        'console_scripts': ['myokit = myokit.__main__:main']
    },

    # List of dependencies
    install_requires=[
        'numpy',
        'scipy',
        'matplotlib>=1.5',
        'configparser',
        'setuptools',
        'sympy',            # Used in lib.markov
        # PyQT or PySide?
        # (PySide is pip installable, Travis can get PyQt from apt)
    ],

    # Optional extras
    extras_require={
        'docs': [
            'sphinx>=1.5, !=1.7.3',     # Doc generation
        ],
        'dev': [
            'flake8>=3',                # Style checking
        ],
        'optional': [
            'cma',                      # Used in lib.fit
        ],
        'gui': [
            'pyqt5',
            'sip',
        ],
    },
)
