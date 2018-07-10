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

        # Calculate jacobians from log
        g = myokit.JacobianTracer(m)
        b = g.jacobians(d)

        # Calculate the dominant eigenvalues
        g.dominant_eigenvalues(log=d)
        g.dominant_eigenvalues(block=b)
        self.assertRaises(ValueError, g.dominant_eigenvalues)

        # Calculate the largest eigenvalues
        g.largest_eigenvalues(log=d)
        g.largest_eigenvalues(block=b)
        self.assertRaises(ValueError, g.largest_eigenvalues)

        # Log missing a state
        d2 = d.clone()
        del(d2['membrane.V'])
        self.assertRaisesRegexp(ValueError, 'all state', g.jacobians, d2)

        # Log entries differ in length
        d2['membrane.V'] = d['membrane.V'][:-1]
        self.assertRaisesRegexp(ValueError, 'same length', g.jacobians, d2)

        # Log missing time
        d2['membrane.V'] = d['engine.time']
        del(d2['engine.time'])
        self.assertRaisesRegexp(ValueError, 'bound', g.jacobians, d2)


if __name__ == '__main__':
    unittest.main()
