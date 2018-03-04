#!/usr/bin/env python2
#
# Runs all example scripts included with Myokit publications.
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
import os
from runner import run

# Get file directory
path = os.path.abspath(os.path.dirname(__file__))

# Get publications directory
path_pub = os.path.join(path, 'publications')


# Run all
# PBMB 2016. Myokit: A simple interface to cardiac cellular electrophysiology
run(os.path.join(path_pub, 'pbmb-2016'))
