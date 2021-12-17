#!/usr/bin/env python3
#
# Tests the lib.deps dependency graphing module.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import random
import unittest

import myokit
import myokit.lib.deps as deps

# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp


class LibDepsTest(unittest.TestCase):

    def test_state_dependency_matrix(self):
        # Test create_ and plot_ state dependency matrix method, to create
        # matrix plot of state interdependencies.

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
        self.assertRaisesRegex(
            ValueError, 'must be states', deps.create_state_dependency_matrix,
            model, direct=True, knockout=['ina.INa'])

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
        matplotlib.use('template')

        # Create plot
        deps.plot_state_dependency_matrix(model)

    def test_component_dependency_graph(self):
        # Test create_ and plot_ component dependency graph method, to show
        # digraph plot of variable dependencies.

        # Nodes are placed at random, so seed the generator for consistent
        # output (otherwise we risk missing full cover on some runs).
        random.seed(1)

        # Load model
        model = myokit.load_model('example')

        # Select matplotlib backend that doesn't require a screen
        import matplotlib
        matplotlib.use('template')

        # Create plot
        self.assertFalse(model.has_interdependent_components())
        deps.plot_component_dependency_graph(model)

        # Add cyclical component dependencies, plot again
        # This time, the acylical plotting code can't be used.
        v = model.get('ina').add_variable('ion')
        v.set_rhs('membrane.i_ion')
        self.assertTrue(model.has_interdependent_components())
        deps.plot_component_dependency_graph(model)

    def test_variable_dependency_graph(self):
        # Test create_ and plot_ variable dependency graph method, to show
        # digraph plot of variable dependencies.

        # Nodes are placed at random, so seed the generator for consistent
        # output (otherwise we risk missing full cover on some runs).
        random.seed(1)

        # Load model
        model = myokit.load_model('example')

        # Select matplotlib backend that doesn't require a screen
        import matplotlib
        matplotlib.use('template')

        # Create plot
        deps.plot_variable_dependency_graph(model)


class DiGraphTest(unittest.TestCase):
    """
    Tests parts of :class:`myokit.lib.deps.DiGraph`.
    """

    def test_basic(self):
        # Test basic DiGraph functions.

        # Create empty graph
        d = deps.DiGraph()
        self.assertEqual(len(d), 0)
        self.assertEqual(d.text(), 'Empty graph')
        d.add_node(1)
        self.assertEqual(len(d), 1)
        d.add_node(2)
        self.assertEqual(len(d), 2)
        d.add_node(3)
        self.assertEqual(len(d), 3)
        d.add_edge(1, 2)
        self.assertEqual(len(d), 3)
        d.add_edge(2, 3)
        d.add_edge(3, 1)

        # Node errors
        self.assertRaisesRegex(ValueError, 'Duplicate', d.add_node, 3)
        dwrong = deps.DiGraph()
        xwrong = dwrong.add_node(99)
        self.assertRaisesRegex(ValueError, 'another graph', d.add_node, xwrong)
        self.assertRaisesRegex(
            ValueError, 'another graph', d.uid_or_node, xwrong)

        # Edge errors
        self.assertRaisesRegex(ValueError, 'Node not found', d.add_edge, 1, 4)

        # Test text
        self.assertEqual(
            d.text(), 'Node "1"\n  > Node "2"\nNode "2"\n  > Node "3"\n'
            'Node "3"\n  > Node "1"')
        self.assertEqual(
            d.text(True), '0, 1, 0\n0, 0, 1\n1, 0, 0')

        # Test cloning
        d2 = deps.DiGraph(d)
        self.assertEqual(len(d2), 3)
        self.assertEqual(d.text(), d2.text())

        # Test build from matrix: Doesn't copy labels
        matrix = d.matrix()
        d3 = deps.DiGraph(matrix)
        self.assertEqual(len(d3), 3)
        self.assertEqual(
            d3.text(), 'Node "0"\n  > Node "1"\nNode "1"\n  > Node "2"\n'
            'Node "2"\n  > Node "0"')
        d3.build_from_matrix(matrix)
        self.assertEqual(
            d3.text(), 'Node "0"\n  > Node "1"\nNode "1"\n  > Node "2"\n'
            'Node "2"\n  > Node "0"')
        d3.build_from_matrix(matrix, edges_only=True)
        self.assertRaises(ValueError, deps.DiGraph, matrix[:-1])
        self.assertEqual(
            d3.text(), 'Node "0"\n  > Node "1"\nNode "1"\n  > Node "2"\n'
            'Node "2"\n  > Node "0"')
        self.assertRaises(ValueError, d.build_from_matrix, matrix[:-1])
        matrix = [x[:-1] for x in matrix[:-1]]
        self.assertRaises(
            ValueError, d.build_from_matrix, matrix, edges_only=True)

        # Test that megs and layering fail on cyclical graph
        self.assertRaisesRegex(Exception, 'cyclical', d.cg_layers_dag)
        d.add_edge(1, 1)
        self.assertRaisesRegex(Exception, 'self-referencing', d.meg_dag)


if __name__ == '__main__':
    unittest.main()
