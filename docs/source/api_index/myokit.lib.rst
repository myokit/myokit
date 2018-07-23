.. _api/index/myokit/lib:

==========
myokit.lib
==========

myokit.lib.common
-----------------
- :class:`myokit.lib.common.Activation`
- :class:`myokit.lib.common.Inactivation`
- :class:`myokit.lib.common.Recovery`
- :class:`myokit.lib.common.Restitution`
- :class:`myokit.lib.common.StepProtocol`
- :class:`myokit.lib.common.StrengthDuration`

myokit.lib.deps
---------------
- :meth:`myokit.lib.deps.create_component_dependency_graph`
- :meth:`myokit.lib.deps.create_state_dependency_matrix`
- :meth:`myokit.lib.deps.create_variable_dependency_graph`
- :class:`myokit.lib.deps.DiGraph`
- :meth:`myokit.lib.deps.plot_component_dependency_graph`
- :meth:`myokit.lib.deps.plot_digraph`
- :meth:`myokit.lib.deps.plot_state_dependency_matrix`
- :meth:`myokit.lib.deps.plot_variable_dependency_graph`
- :class:`myokit.lib.deps.Node`

myokit.lib.fit
--------------
- :meth:`myokit.lib.fit.bfgs`
- :meth:`myokit.lib.fit.cmaes`
- :meth:`myokit.lib.fit.evaluate`
- :class:`myokit.lib.fit.Evaluator`
- :meth:`myokit.lib.fit.loss_surface_colors`
- :meth:`myokit.lib.fit.loss_surface_mesh`
- :meth:`myokit.lib.fit.map_grid`
- :meth:`myokit.lib.fit.nelder_mead`
- :class:`myokit.lib.fit.ParallelEvaluator`
- :meth:`myokit.lib.fit.powell`
- :meth:`myokit.lib.fit.pso`
- :class:`myokit.lib.fit.SequentialEvaluator`
- :meth:`myokit.lib.fit.snes`
- :meth:`myokit.lib.fit.voronoi_regions`
- :meth:`myokit.lib.fit.xnes`

myokit.lib.markov
-----------------
- :class:`myokit.lib.markov.AnalyticalSimulation`
- :class:`myokit.lib.markov.DiscreteSimulation`
- :class:`myokit.lib.markov.LinearModel`
- :class:`myokit.lib.markov.LinearModelError`
- :class:`myokit.lib.markov.MarkovModel` (Deprecated)

myokit.lib.multi
----------------
- :meth:`myokit.lib.multi.binding`
- :meth:`myokit.lib.multi.iterdir`
- :meth:`myokit.lib.multi.label`
- :meth:`myokit.lib.multi.scandir`
- :meth:`myokit.lib.multi.time`
- :meth:`myokit.lib.multi.unit`

myokit.lib.plot
---------------
- :meth:`myokit.lib.plots.cumulative_current`
- :meth:`myokit.lib.plots.current_arrows`
- :meth:`myokit.lib.plots.simulation_times`
