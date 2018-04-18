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
from myokit import VERSION as version


# Load text for description and license
with open('README.md') as f:
    readme = f.read()
with open('LICENSE') as f:
    license = f.read()


# Go!
setup(
    # Module name
    name='myokit',

    # Version
    version=version,

    description='A simple interface to cardiac cellular electrophysiology',

    long_description=readme,

    license=license,

    author='Michael Clerx',

    author_email='michael@myokit.org',

    url='http://myokit.org',

    # Packages to include
    packages=find_packages(include=('myokit', 'myokit.*')),

    # Also load non-python files (via MANIFEST.in)
    include_package_data=True,

    # List of dependencies
    install_requires=[
        'numpy',
        'scipy',
        'matplotlib>=1.5',       # Move to extras?
        # PyQT or PySide?
        # (PySide is pip installable, Travis can get PyQt from apt)
    ],
)
