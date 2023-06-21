#
# SetupTools script for Myokit
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from setuptools import setup, find_packages


# Get version number
import os
import sys
sys.path.append(os.path.abspath('myokit'))
from _myokit_version import __version__ as version  # noqa
sys.path.pop()
del os, sys


# Load text for description and license
with open('README.md') as f:
    readme = f.read()


# Go!
setup(
    # See https://python-packaging.readthedocs.io/en/latest/index.html
    # for details of what goes in here.

    # Module name (lowercase)
    name='myokit',

    # Version
    version=version,

    # Description
    description='A simple interface to cardiac cellular electrophysiology',
    long_description=readme,
    long_description_content_type='text/markdown',

    # Author and license
    license='BSD 3-clause license',
    author='Michael Clerx',
    author_email='michael@myokit.org',

    # URLs
    url='http://myokit.org',
    project_urls={
        'Bug Tracker': 'https://github.com/MichaelClerx/myokit/issues',
        'Documentation': 'http://docs.myokit.org',
        'Source Code': 'https://github.com/MichaelClerx/myokit',
    },

    # Classifiers for pypi
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'Topic :: Scientific/Engineering :: Chemistry',
        'Topic :: Scientific/Engineering :: Mathematics',
        'Topic :: Scientific/Engineering :: Medical Science Apps.',
        'Topic :: Scientific/Engineering :: Physics',
    ],

    # Packages to include
    packages=find_packages(include=('myokit', 'myokit.*')),

    # Include non-python files (via MANIFEST.in)
    include_package_data=True,

    # Register myokit as a shell script
    entry_points={
        'console_scripts': ['myokit = myokit.__main__:main']
    },

    # Python version
    python_requires='>=3.7',

    # List of dependencies
    install_requires=[
        'configparser',
        'lxml',
        'matplotlib>=2.2',
        'numpy',
        'setuptools',
        # PyQT or PySide?
        # (PySide is pip installable, Actions can get PyQt from apt)
    ],

    # Optional extras
    extras_require={
        'docs': [
            'sphinx>=1.7.4',        # Doc generation
        ],
        'dev': [
            'coverage',             # Coverage checking
            'flake8>=3',            # Style checking
        ],
        'optional': [
            'scipy',            # Used in data log, and data log viewer
            'sympy',            # Used in formats.sympy
        ],
        'gui': ['pyqt6', 'sip'],
        'pyqt': ['pyqt6', 'sip'],
        'pyside': ['pyside6'],
    },

    # Unit tests
    test_suite='myokit.tests',

    # See: https://setuptools.pypa.io/en/latest/userguide/miscellaneous.html
    #      #setting-the-zip-safe-flag
    zip_safe=False,
)
