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

myokit.lib.guess
----------------
- :meth:`myokit.lib.guess.add_embedded_protocol`
- :meth:`myokit.lib.guess.membrane_capacitance`
- :meth:`myokit.lib.guess.membrane_currents`
- :meth:`myokit.lib.guess.membrane_potential`
- :meth:`myokit.lib.guess.remove_embedded_protocol`
- :meth:`myokit.lib.guess.stimulus_current`
- :meth:`myokit.lib.guess.stimulus_current_info`

myokit.lib.hh
-------------
- :class:`myokit.lib.hh.AnalyticalSimulation`
- :class:`myokit.lib.hh.HHModel`
- :class:`myokit.lib.hh.HHModelError`
- :meth:`myokit.lib.hh.convert_hh_states_to_inf_tau_form`
- :meth:`myokit.lib.hh.has_alpha_beta_form`
- :meth:`myokit.lib.hh.has_inf_tau_form`
- :meth:`myokit.lib.hh.get_alpha_and_beta`
- :meth:`myokit.lib.hh.get_inf_and_tau`
- :meth:`myokit.lib.hh.get_rl_expression`

myokit.lib.markov
-----------------
- :class:`myokit.lib.markov.AnalyticalSimulation`
- :class:`myokit.lib.markov.DiscreteSimulation`
- :meth:`myokit.lib.markov.convert_markov_models_to_compact_form`
- :meth:`myokit.lib.markov.convert_markov_models_to_full_ode_form`
- :meth:`myokit.lib.markov.find_markov_models`
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
