.. _api/library/fit:

************************
Parameter identification
************************

.. module:: myokit.lib.fit

The module ``myokit.lib.fit`` provides tools to help with the process of
parameter identification: Finding the parameter values for (part of) a model
that produce the desired output.

Global optimization methods are provided that use heuristic search methods to
explore large search spaces and find reasonable results. Further refinement of
these solutions can then be done using a local optimization method. Some
information about the quality of the solution can be obtained by fitting a
second order polynomial to points near the solution: if it's a minimum this
should result in a hyper-parabola with a critical point at the solution.
Methods are provided to evaluate a large number of points in parallel or on a
single CPU. These can also be used to perform a brute-force mapping of the
parameter space. Finally, some methods are provided to visualize 2D parameter
spaces. Because points found using for example a particle search optimization
will not be regularly distributed in space, these visualization methods are
based on voronoi diagrams.


..  toctree

-------------------
Global optimization
-------------------

The methods listed below perform global optimization (pso) or global/local
optimization (cmaes, snes, xnes).
The cma-es method is an interface to the Python `cma` module.

.. autofunction:: cmaes

.. autofunction:: pso

.. autofunction:: snes

.. autofunction:: xnes

------------------
Local optimization
------------------

The local optimization methods presented here are interfaces to methods found
in SymPy (http://sympy.org).

.. autofunction:: bfgs

.. autofunction:: nelder_mead

.. autofunction:: powell

---------------
Checking minima
---------------

The following function can be used to investigate if points in the parameter
space are (local) minima.
Unfortunately, they often fail in complex search spaces.

.. autofunction:: quadfit

.. autofunction:: quadfit_count

.. autofunction:: quadfit_crit

.. autofunction:: quadfit_minimum

---------------------------
Parameter space exploration
---------------------------

The following methods can be used for (parallelised) exploration of the
parameter space.

.. autofunction:: map_grid

.. autofunction:: evaluate

.. autoclass:: Evaluator

.. autoclass:: SequentialEvaluator

.. autoclass:: ParallelEvaluator

-------------------------------
Loss surface visualisation (2d)
-------------------------------

The methods below can be used to visualise loss (score, penalty, fitness, etc.)
surfaces in two dimensions.
Because most search/exploration methods return unevenly spaced points, a
Voronoi diagram representation is used.

.. autofunction:: loss_surface_colors

.. autofunction:: loss_surface_mesh

.. autofunction:: voronoi_regions

