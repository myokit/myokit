#!/usr/bin/env python3
#
# Tests the CVODES simulation class, when using a precompiled simulation.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import os
import unittest

import numpy as np

import myokit

from myokit.tests import (
    DIR_DATA,
)


class PrecompiledSimulationTest(unittest.TestCase):
    """
    Tests the CVODES simulation class, when using a precompiled simulation.
    """

    def test(self):
        # Create and run two simulations and compare the output

        # Load model and protocol
        model, protocol, _ = myokit.load(os.path.join(DIR_DATA, 'lr-1991.mmt'))

        # Select sensitivities to calculate
        sens = (
            ('membrane.V', 'ica.Ca_i', 'ina.INa', 'ik.x', 'dot(ina.m)'),
            ('init(ik.x)', 'init(ica.Ca_i)', 'ina.gNa', 'ik.PNa_K')
        )

        # Create both simulation
        path = 'precompiled-test.zip'
        assert not os.path.exists(path), 'Path used in test already exists'
        try:
            sim1 = myokit.Simulation(model, protocol, sens, path=path)
            sim2 = myokit.Simulation.from_path(path)
        finally:
            if os.path.exists(path):
                os.remove(path)
        assert not os.path.exists(path), 'Test leaked file: ' + path

        sim1.pre(10)
        sim1.run(10)
        d1, s1 = sim1.run(1000)
        d1, s1 = d1.npview(), np.array(s1)

        sim2.pre(10)
        sim2.run(10)
        d2, s2 = sim2.run(1000)
        d2, s2 = d2.npview(), np.array(s2)

        for k, v in d1.items():
            if k == 'engine.realtime':
                continue
            if np.max(np.abs(v - d2[k])) > 0:
                print(k)
            self.assertTrue(np.all(v == d2[k]))

        self.assertTrue(np.all(s1 == s2))


if __name__ == '__main__':
    unittest.main()
