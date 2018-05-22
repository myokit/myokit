#!/usr/bin/env python
#
# Tests the Jacobian tracer.
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import os
import unittest

import myokit

from shared import DIR_DATA


class JacobianTracerTest(unittest.TestCase):
    """
    Tests the JacobianTracer.
    """
    def test_simple(self):
        # Load model
        m = os.path.join(DIR_DATA, 'lr-1991.mmt')
        m, p, x = myokit.load(m)
        v = m.binding('diffusion_current')
        if v is not None:
            v.set_binding(None)

        # Run a simulation, save all states & bound values
        s = myokit.Simulation(m, p)
        s.pre(10)
        s.reset()
        d = s.run(20, log=myokit.LOG_STATE + myokit.LOG_BOUND)

        # Calculate the dominant eigenvalues for each log position
        g = myokit.JacobianTracer(m)
        b = g.jacobians(d)
        b.dominant_eigenvalues('jacobians')
        b.largest_eigenvalues('jacobians')


if __name__ == '__main__':
    unittest.main()
