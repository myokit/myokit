#!/usr/bin/env python2
#
# Runs all unit tests for Myokit.
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
import sys
import myotest
result = myotest.cmd()
sys.exit(0 if result else 1)
