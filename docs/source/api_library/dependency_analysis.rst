.. _api/myokit/library/deps:

*******************
Dependency analysis
*******************

.. module:: myokit.lib.deps

Using these functions from ``myokit.lib`` you can perform simple dependency
analysis algorithms on Myokit models.

This module uses ``matplotlib`` for visualisation.

.. autofunction:: plot_state_dependency_matrix

.. autofunction:: create_state_dependency_matrix

.. autofunction:: plot_component_dependency_graph

.. autofunction:: create_component_dependency_graph

.. autofunction:: plot_variable_dependency_graph

.. autofunction:: create_variable_dependency_graph

Internally, these functions make use of a tiny DiGraph class.

.. autoclass:: DiGraph

.. autoclass:: Node

.. autofunction:: plot_digraph
