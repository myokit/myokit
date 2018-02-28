#!/usr/bin/env python
#
# Runs the unit tests / developer tests for myokit
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
import sys
import myotest
exclude = [
    'simulation_opencl.py',
]
result = myotest.run_all(exclude)
sys.exit(0 if result else 1)
