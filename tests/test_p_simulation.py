#!/usr/bin/env python
#
# Tests the PSimulation class.
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
import numpy as np

import myokit

from shared import DIR_DATA


class PSimulation(unittest.TestCase):
    """
    Tests the PSimulation.
    """
    def test_simple(self):

        # Load model
        m = os.path.join(DIR_DATA, 'lr-1991.mmt')
        m, p, x = myokit.load(m)

        # Run a tiny simulation
        s = myokit.PSimulation(
            m, p, variables=['membrane.V'], parameters=['ina.gNa', 'ica.gCa'])
        s.set_step_size(0.002)
        d, dp = s.run(10, log_interval=2)

        # Create without variables or parameters
        self.assertRaisesRegexp(
            ValueError, 'variables', myokit.PSimulation, m, p,
            parameters=['ina.gNa'])
        self.assertRaisesRegexp(
            ValueError, 'parameters', myokit.PSimulation, m, p,
            variables=['membrane.V'])

        # Run without validated model
        m2 = m.clone()
        m2.get('membrane.V').set_rhs(
            myokit.Multiply(m2.get('membrane.V').rhs(), myokit.Number(0.9)))
        s = myokit.PSimulation(
            m, p, variables=['membrane.V'], parameters=['ina.gNa', 'ica.gCa'])
        s.set_step_size(0.002)
        d, dp = s.run(10, log_interval=2)

        # Variable or parameter given twice
        self.assertRaisesRegexp(
            ValueError, 'Duplicate variable', myokit.PSimulation, m, p,
            variables=['membrane.V', 'membrane.V'], parameters=['ina.gNa'])
        self.assertRaisesRegexp(
            ValueError, 'Duplicate parameter', myokit.PSimulation, m, p,
            variables=['membrane.V'], parameters=['ina.gNa', 'ina.gNa'])

        # Bound variable or parameter
        self.assertRaisesRegexp(
            ValueError, 'bound', myokit.PSimulation, m, p,
            variables=['engine.pace'], parameters=['ina.gNa'])
        self.assertRaisesRegexp(
            ValueError, 'bound', myokit.PSimulation, m, p,
            variables=['membrane.V'], parameters=['engine.pace'])

        # Constant variable
        self.assertRaisesRegexp(
            ValueError, 'constant', myokit.PSimulation, m, p,
            variables=['ica.gCa'], parameters=['ina.gNa'])

        # Non-constant parameter
        self.assertRaisesRegexp(
            ValueError, 'literal constant', myokit.PSimulation, m, p,
            variables=['membrane.V'], parameters=['cell.RTF'])

        # Variables given as objects
        myokit.PSimulation(
            m, p, variables=[m.get('membrane.V')],
            parameters=[m.get('ina.gNa')])

    def test_block(self):
        """
        Tests :meth:`PSimulation.block()`.
        """
        m, p, x = myokit.load(os.path.join(DIR_DATA, 'lr-1991.mmt'))
        s = myokit.PSimulation(
            m, p, variables=['membrane.V'], parameters=['ina.gNa', 'ica.gCa'])
        s.set_step_size(0.002)
        d, dp = s.run(10, log_interval=2)

        b = s.block(d, dp)
        self.assertIsInstance(b, myokit.DataBlock2d)
        self.assertEqual(b.len0d(), len(d) - 1)
        self.assertTrue(np.all(b.time() == d.time()))

        # Log without time
        e = myokit.DataLog(d)
        del(e[e.time_key()])
        self.assertRaisesRegexp(ValueError, 'must contain', s.block, e, dp)

        # Wrong size derivatives array
        de = dp[:,:-1]
        self.assertRaisesRegexp(ValueError, 'shape', s.block, d, dp[:,:-1])


if __name__ == '__main__':
    unittest.main()
