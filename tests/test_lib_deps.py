#!/usr/bin/env python
#
# Tests the lib.deps dependency graphing module.
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import unittest

import myokit
import myokit.lib.deps as deps


class LibDepsTest(unittest.TestCase):

    def test_state_dependency_matrix(self):
        """
        Tests create_ and plot_ state dependency matrix method, to create
        matrix plot of state interdependencies.
        """
        # Load model
        model = myokit.load_model('example')

        # Test direct version (simplest matrix)
        matrix = deps.create_state_dependency_matrix(model, direct=True)
        self.assertEqual(matrix, [
            # V m  h  j  d  f  x Cai
            [1, 1, 1, 1, 1, 1, 1, 1],  # V
            [1, 1, 0, 0, 0, 0, 0, 0],  # m
            [1, 0, 1, 0, 0, 0, 0, 0],  # h
            [1, 0, 0, 1, 0, 0, 0, 0],  # j
            [1, 0, 0, 0, 1, 0, 0, 0],  # d
            [1, 0, 0, 0, 0, 1, 0, 0],  # f
            [1, 0, 0, 0, 0, 0, 1, 0],  # x
            [1, 0, 0, 0, 1, 1, 0, 1],  # Cai depends on d and f
        ])

        # Test direct version without V
        matrix = deps.create_state_dependency_matrix(
            model, direct=True, knockout=['membrane.V'])
        self.assertEqual(matrix, [
            # V m  h  j  d  f  x Cai
            [0, 0, 0, 0, 0, 0, 0, 0],  # V
            [0, 1, 0, 0, 0, 0, 0, 0],  # m
            [0, 0, 1, 0, 0, 0, 0, 0],  # h
            [0, 0, 0, 1, 0, 0, 0, 0],  # j
            [0, 0, 0, 0, 1, 0, 0, 0],  # d
            [0, 0, 0, 0, 0, 1, 0, 0],  # f
            [0, 0, 0, 0, 0, 0, 1, 0],  # x
            [0, 0, 0, 0, 1, 1, 0, 1],  # Cai depends on d and f
        ])

        # Test indirect version
        matrix = deps.create_state_dependency_matrix(model, direct=False)
        self.assertEqual(matrix, [
            # V m  h  j  d  f  x Cai
            [1, 1, 1, 1, 1, 1, 1, 1],  # V
            [1, 1, 2, 2, 2, 2, 2, 2],  # m
            [1, 2, 1, 2, 2, 2, 2, 2],  # h
            [1, 2, 2, 1, 2, 2, 2, 2],  # j
            [1, 2, 2, 2, 1, 2, 2, 2],  # d
            [1, 2, 2, 2, 2, 1, 2, 2],  # f
            [1, 2, 2, 2, 2, 2, 1, 2],  # x
            [1, 2, 2, 2, 1, 1, 2, 1],  # Cai depends on d and f
        ])

        # Test indirect version, without V
        matrix = deps.create_state_dependency_matrix(
            model, direct=False, knockout=['membrane.V'])
        self.assertEqual(matrix, [
            # V m  h  j  d  f  x Ca_i
            [0, 0, 0, 0, 0, 0, 0, 0],  # V
            [0, 1, 0, 0, 0, 0, 0, 0],  # m
            [0, 0, 1, 0, 0, 0, 0, 0],  # h
            [0, 0, 0, 1, 0, 0, 0, 0],  # j
            [0, 0, 0, 0, 1, 0, 0, 0],  # d
            [0, 0, 0, 0, 0, 1, 0, 0],  # f
            [0, 0, 0, 0, 0, 0, 1, 0],  # x
            [0, 0, 0, 0, 1, 1, 0, 1],  # Cai depends on d and f

        ])

        # Select matplotlib backend that doesn't require a screen
        import matplotlib
        matplotlib.use('Agg')

        # Create plot
        deps.plot_state_dependency_matrix(model)

    def test_component_dependency_graph(self):
        """
        Tests create_ and plot_ component dependency graph method, to show
        digraph plot of variable dependencies.
        """
        # Load model
        model = myokit.load_model('example')

        # Select matplotlib backend that doesn't require a screen
        import matplotlib
        matplotlib.use('Agg')

        # Create plot
        deps.plot_component_dependency_graph(model)


    def test_component_dependency_graph(self):
        """
        Tests create_ and plot_ variable dependency graph method, to show
        digraph plot of variable dependencies.
        """
        # Load model
        model = myokit.load_model('example')

        # Select matplotlib backend that doesn't require a screen
        import matplotlib
        matplotlib.use('Agg')

        # Create plot
        deps.plot_variable_dependency_graph(model)



if __name__ == '__main__':
    unittest.main()
