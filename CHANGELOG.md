# Changelog
                
This page lists the main changes made to Myokit in each release.

## Unreleased
- Added
  - [#1143](https://github.com/myokit/myokit/pull/1143) Added `convert_ramps` argument AbfFile which, if set, will allow reading ramps as steps (instead of refusing to import the protocol entirely).
- Changed
  - [#1147](https://github.com/myokit/myokit/pull/1147) CellML imported files now have an `mmt-author` in their description, rather than `author`, indicating the mmt file rather than the model author.
- Deprecated
- Removed
- Fixed

## [1.38.0] - 2025-08-14
- Added
  - [#1136](https://github.com/myokit/myokit/pull/1136) Added limited support for ABF reading in modes other than "episodic acquisition".
- Changed
  - [#1135](https://github.com/myokit/myokit/pull/1135) Updated documentation of "prediction" in PatchMasterFile.
  - [#1139](https://github.com/myokit/myokit/pull/1139) Protocol start times set using the ``next`` keyword are now rounded to 9 digits precision. This helps avoid unexpected results in very long protocols, where floating point errors can accumulate. Start times set explicitly are not rounded.
- Fixed
  - [#1135](https://github.com/myokit/myokit/pull/1135) Fixed bug in PatchMasterFile where data types other than int 16 were not detected.
  - [#1137](https://github.com/myokit/myokit/pull/1137) Fixed error in colormap attribution.
  - [#1138](https://github.com/myokit/myokit/pull/1138) Fixed bug in FiberTissueSimulation and Simulation1d that was causing compilation errors.

## [1.37.4] - 2025-06-30
- Added
  - [#1118](https://github.com/myokit/myokit/pull/1118) @kwabenantim Added a minimal `pyproject.toml` specifying the build system.
  - [#1120](https://github.com/myokit/myokit/pull/1120) Added "close" and "close all" menu items in the data log viewer.
  - [#1122](https://github.com/myokit/myokit/pull/1122) The Patchmaster file reader now documents the lack of "prediction" setting availability. Added detailed C-fast information to meta data exported to DataLog.
- Changed
  - [#1121](https://github.com/myokit/myokit/pull/1121) The filter 2 frequency in Patchmaster files is now returned in kHz instead of Hz. Added a method to get the filter 1 frequency. Both frequencies are added to the meta data when creating a DataLog.
- Fixed
  - [#1117](https://github.com/myokit/myokit/pull/1117) @martinjrobins Fixed a bug in SBML export of non-constant, non-state variables.
  - [#1134](https://github.com/myokit/myokit/pull/1134) Added missing `__len__` method to `PatchMasterFile`.

## [1.37.3] - 2025-01-09
- Changed
  - [#1116](https://github.com/myokit/myokit/pull/1116) Unit names passed to `Unit.register` are now validated using `myokit.check_name`, and the fourth argument to `Unit.register` is now called `preferred_representation`.
  - [#1116](https://github.com/myokit/myokit/pull/1116) The method `Unit.register_preferred_representation` now checks that the given representation parses to the given unit.
- Fixed
  - [#1116](https://github.com/myokit/myokit/pull/1116) Fixed issue where units were represented with double multipliers, e.g. ``[m (0.001) (1e-3)]``, causing unparseable code to be written.

## [1.37.2] - 2025-01-09
- Added
  - [#1098](https://github.com/myokit/myokit/pull/1098) @martinjrobins Added SBML export.
- Changed
  - [#1102](https://github.com/myokit/myokit/pull/1102) Replaced the HEKA method `c_fast_tau` with a method `c_fast_detailed`.
- Removed
  - [#1111](https://github.com/myokit/myokit/pull/1111) No longer testing on Python 3.7.
- Fixed
  - [#1100](https://github.com/myokit/myokit/pull/1100) Added missing PatchMaster classes to the API and docs.
  - [#1109](https://github.com/myokit/myokit/pull/1109) Fixed issue with meta data in Patchmaster class for files with alternative amplifier state storage.

## [1.37.1] - 2024-11-05
- Added
  - [#1073](https://github.com/myokit/myokit/pull/1073) Added export to [DiffSL](https://github.com/martinjrobins/diffeq-js/).
  - [#1088](https://github.com/myokit/myokit/pull/1088) The DataLogViewer now displays meta data for myokit DataLogs.
  - [#1088](https://github.com/myokit/myokit/pull/1088) The HEKA file format now supports more meta data, including filters.
  - [#1092](https://github.com/myokit/myokit/pull/1092) The method `DataLog.load_csv` can now read CSV files with duplicate column names.
  - [#1095](https://github.com/myokit/myokit/pull/1095) Myokit is now tested on Python 3.12 and 3.13.
- Fixed
  - [#1083](https://github.com/myokit/myokit/pull/1083) Fixed bug when passing initial state `Expression` objects to `myokit.step`.
  - [#1088](https://github.com/myokit/myokit/pull/1088) The HEKA file format meta data now shows the correct value for fast capacitance correction.
  - [#1088](https://github.com/myokit/myokit/pull/1088) The ABF reader no longer crashes if degrees Celsius are encountered.
  - [#1093](https://github.com/myokit/myokit/pull/1093) `DataLog.load_csv` will now ignore an initial byte order marker.

## [1.37.0] - 2024-06-17
- Added
  - [#1075](https://github.com/myokit/myokit/pull/1075) Add a `myokit.TypeError` exception, which inherits from `myokit.IntegrityError` but is used specifically if one type of expression was expected but another was found.
- Changed
  - [#1067](https://github.com/myokit/myokit/pull/1067) Improved the meta data loaded from HEKA files when creating a `myokit.DataLog`.
  - [#1074](https://github.com/myokit/myokit/pull/1074) Expressions will now raise a `myokit.IntegrityError` in the constructor if their operands are not expression objects: previously, this check was only performed by `Expression.validate()`.
  - [#1075](https://github.com/myokit/myokit/pull/1075) Expressions will now raise a `myokit.TypeError` in the constructor if their operands are unexpected expression types, e.g. if numbers and booleans are mixed.
- Removed
  - [#1075](https://github.com/myokit/myokit/pull/1075) Removed the `PrefixCondition` base class previously used in the expression system, as only `Not` inherited from it.
- Fixed
  - [#1071](https://github.com/myokit/myokit/pull/1071) When DataLog.split_periodic does not make a split, a length 1 list is returned instead of a `DataLog`.
  - [#1075](https://github.com/myokit/myokit/pull/1075) Added missing `Expression` base classes to public API.
  - [#1077](https://github.com/myokit/myokit/pull/1077) Fixed bug where data log viewer crashed when reading an empty WCP file.
  - [#1078](https://github.com/myokit/myokit/pull/1078) Added support for Numpy 2.

## [1.36.1] - 2024-05-10
- Added
  - [#1063](https://github.com/myokit/myokit/pull/1063) Added support for Sundials 7.0.0.
- Removed
  - [#1061](https://github.com/myokit/myokit/issues/1061) Currently unable to test OpenCL features on Mac OS.
- Fixed
  - [#1060](https://github.com/myokit/myokit/pull/1060) Fixed an issue with overflows in tau for HH analytical simulations leading to unnecessary NaNs in state and current simulation outputs.

## [1.36.0] - 2024-03-22
This release fixes a potential issue in simulation output, please see [#1055](https://github.com/myokit/myokit/pull/1055) for details.
- Added
  - [#1051](https://github.com/myokit/myokit/pull/1051) Added a method `Simulation.crash_inputs` that returns the inputs (binding values) if the last run raised a `SimulationError`.
  - [#1055](https://github.com/myokit/myokit/pull/1055) Added an abstract class `CBasedExpressionWriter` to use as base class for expression writers for C-like languages.
- Changed
  - [#1051](https://github.com/myokit/myokit/pull/1051) `Model.evaluate_derivatives` will now use `numpy.errstate(all='raise')` when `ignore_errors` is set to `False`, causing more numerical issues to be reported.
  - [#1055](https://github.com/myokit/myokit/pull/1055) `Expression.pyfunc` now sorts its arguments in alphabetical order.
- Deprecated
  - [#1051](https://github.com/myokit/myokit/pull/1051) `Simulation.eval_derivatives` is deprecated in favour of an `evaluate_derivatives` method that uses `default_state` instead of `state` when no state is given, and has better support and clearer rules for handling bindings.
  - [#1051](https://github.com/myokit/myokit/pull/1051) `Simulation.last_state` is deprecated in favour of `crash_state`.
- Fixed
  - [#1045](https://github.com/myokit/myokit/pull/1045) Fixed an issue where the cache used in MarkovModel was not invalidated if `set_constant()` changed simulation parameters.
  - [#1050](https://github.com/myokit/myokit/pull/1050) Fixed warnings about unknown escape sequences.
  - [#1051](https://github.com/myokit/myokit/pull/1051) Numerical simulation errors in `Simulation` now re-evaluate the state using the last inputs, as well as the last state.
  - [#1051](https://github.com/myokit/myokit/pull/1051) The `Simulation` class now provides error states and inputs for both cvode-detected crashes and too many zero-length step crashes.
  - [#1055](https://github.com/myokit/myokit/pull/1055) `ExpressionWriter` classes now always output a `PrefixPlus`, including brackets where necessary.
  - [#1055](https://github.com/myokit/myokit/pull/1055) The `AnsiCExpressionWriter` and related expression writers now wrap all conditions in brackets.
  - [#1055](https://github.com/myokit/myokit/pull/1055) The `PythonExpressionWriter`, `NumPyExpressionWriter`, `StanExpressionWriter`, and `LatexExpressionWriter` now output brackets around double `Power` operations, so that the Myokit expression `a**b**c` is interpreted as `(a**b)**c`.
  - [#1055](https://github.com/myokit/myokit/pull/1055) Fixed bracket adding for `PrefixPlus`, `PrefixMinus`, and `Not` in `LatexExpressionWriter`.
  - [#1055](https://github.com/myokit/myokit/pull/1055) Fixed bracket adding for `PrefixPlus` and `PrefixMinus` in Presentation MathML.

## [1.35.4] - 2023-10-12
- Added
  - [#1010](https://github.com/myokit/myokit/pull/1010) Added more information methods to `formats.heka.Segment`
  - [#1012](https://github.com/myokit/myokit/pull/1012) The method `Model.add_variable` now has keyword arguments `unit`, `rhs`, `label`, `binding`, and `initial_value` to allow one-line variable creation and initialisation.
  - [#1018](https://github.com/myokit/myokit/pull/1018) The PatchMaster file reading can now extract information for multiple amplifiers (if used), and more information methods were added.
- Fixed
  - [#1020](https://github.com/myokit/myokit/pull/1020) Fixed an issue where the explorer time fields had a white background in dark mode.
  - [#1021](https://github.com/myokit/myokit/pull/1021) Fixed a buggy deprecation warning in `lib.plots.cumulative_current`.
  
## [1.35.3] - 2023-07-26
- Added
  - [#1006](https://github.com/myokit/myokit/pull/1006) The `DataLog` class can now store global meta data in `.meta` and per-column meta data in `.cmeta`. Both must be string-string key-value pairs.
  - [#1006](https://github.com/myokit/myokit/pull/1006) Simulations now automatically add some meta data (units) to the data log.
  - [#1006](https://github.com/myokit/myokit/pull/1006) The `DataLog` class can now save meta data to disk using the [CSV-on-the-web](https://w3c.github.io/csvw/) format.
  - [#1006](https://github.com/myokit/myokit/pull/1006) Added a class `ColumnMetaData` to represent per-column meta data of a table or DataLog.
  - [#1006](https://github.com/myokit/myokit/pull/1006) ABF, WCP, and PatchMaster file classes now add meta data when creating a `DataLog`.
- Changed
  - [#1006](https://github.com/myokit/myokit/pull/1006) Made core classes `ObjectWithMetaData`, `MetaDataContainer`, `VarOwner`, and `VarProvider` part of the public API. Similarly the method `check_name`.
  - [#1008](https://github.com/myokit/myokit/pull/1008) The `PatchMasterFile` reader no longer performs "zero offset subtraction" (in which a recorded current trace is shifted until a user-specified segment has zero current) by default.
- Fixed
  - [#1006](https://github.com/myokit/myokit/pull/1006) `DataLog.clone()` no longer replaces `array.array` objects with lists.

## [1.35.2] - 2023-07-19
- Fixed
  - [#1005](https://github.com/myokit/myokit/pull/1005) DataBlock viewer now shows user-set values when exporting a colormap.

## [1.35.1] - 2023-07-19
- Added
  - [#955](https://github.com/myokit/myokit/pull/955) Added provisional HEKA PatchMaster file reading.
  - [#985](https://github.com/myokit/myokit/pull/985), [#998](https://github.com/myokit/myokit/pull/998) The `AbfFile` and `WcpFile` now implement a shared `SweepSource` interface.
  - [#985](https://github.com/myokit/myokit/pull/985) Added a method `AtfFile.path` that returns the full path.
  - [#985](https://github.com/myokit/myokit/pull/985) Added a method `WcpFile.info` that returns a string version of the file's meta data, and a method `WcpFile.sample_count` that returns the number of samples per channel.
  - [#1003](https://github.com/myokit/myokit/pull/1003) The DataBlock viewer now has fields to enter a lower and upper range for the colormap conversion.
  - [#1003](https://github.com/myokit/myokit/pull/1003) Added new color maps for `myokit.DataBlock` viewing.
- Changed
  - [#985](https://github.com/myokit/myokit/pull/985), [#998](https://github.com/myokit/myokit/pull/998)  The interface to the `AbfFile` class has changed significantly, and in a backwards incompatible ways. Please see the documentation for further details.
  - [#991](https://github.com/myokit/myokit/pull/991) Myokit no longer uses the `logging` module but makes calls to `warnings.warn` instead.
  - [#992](https://github.com/myokit/myokit/pull/992) If a `Simulation` is created with `protocol={}`, then `pace` will not be set as a binding label. To stay backwards compatible it _will_ be set if `protocol=None`.
  - [#994](https://github.com/myokit/myokit/pull/994) Simulations can now start at arbitrary times, including negative ones. Note that protocol events have a default offset of 0, so no events are usually expected at negative times.
- Deprecated
  - [#985](https://github.com/myokit/myokit/pull/985) The method `WcpFile.myokit_log` is deprecated in favor of `WcpFile.log`.
  - [#985](https://github.com/myokit/myokit/pull/985) The methods `WcpFile.channels` and `WcpFile.records` are deprecated in favor of `WcpFile.channel_count` and `WcpFile.record_count`.
  - [#985](https://github.com/myokit/myokit/pull/985) The method `WcpFile.plot` is deprecated in favor of `WcpFile.matplotlib_figure`.
  - [#985](https://github.com/myokit/myokit/pull/985) The method `WcpFile.records` is deprecated in favor of `WcpFile.record_count` or `WcpFile.sweep_count`.
  - [#985](https://github.com/myokit/myokit/pull/985) The method `AtfFile.myokit_log` is deprecated in favor of `AtfFile.log`.
  - [#998](https://github.com/myokit/myokit/pull/998) The method `WcpFile.info` is deprecated in favor of `WcpFile.meta_str`.
  - [#998](https://github.com/myokit/myokit/pull/998) The method `AtfFile.info` is deprecated in favor of `AtfFile.meta_str`.
- Fixed
  - [#985](https://github.com/myokit/myokit/pull/985) `AbfFile.filename` now returns the filename, not the full path.
  - [#985](https://github.com/myokit/myokit/pull/985) `AtfFile.filename` now returns the filename, not the full path.
  - [#992](https://github.com/myokit/myokit/pull/992) `Simulation` now sets any variable bound to a pacing label to 0 if no protocol for that label is set.
  - [#998](https://github.com/myokit/myokit/pull/998) Fixed a bug where channels in ABF v1 files were sometimes scaled using the wrong meta data.
  - [#1003](https://github.com/myokit/myokit/pull/1003) Fixed a bug in the DataBlockViewer introduced when adding Qt6 support.

## [1.35.0] - 2023-06-21
- Added
  - [#979](https://github.com/myokit/myokit/pull/979) Added support for PyQt6 and PySide6.
- Changed
  - [#980](https://github.com/myokit/myokit/pull/980) Python 2 is no longer supported. The minimum supported Python version is now 3.7.
- Removed
  - [#979](https://github.com/myokit/myokit/pull/979) Removed support for PyQt4 and PySide, which were deprecated since 2019.

## [1.34.0] - 2023-06-07
- Added
  - [#898](https://github.com/myokit/myokit/pull/899) @martinjrobins Initial conditions for state variables can now be (constant-valued) expressions. Previously, only literals were allowed.
  - [#918](https://github.com/myokit/myokit/pull/918) Added `Model.initial_values`, which returns the model's initial values as a list of expressions, floats, or equations.
  - [#918](https://github.com/myokit/myokit/pull/918) Added `Model.set_initial_values`, which sets the model's initial values using a list of expressions or anything accepted by `map_to_state`.
  - [#918](https://github.com/myokit/myokit/pull/918) Added `Variable.initial_value`, which returns a state variable's initial value as an expression or float.
  - [#918](https://github.com/myokit/myokit/pull/918) Added `Variable.set_initial_value`, which sets a state variable's initial value using an expression, string expression, or float.
  - [#918](https://github.com/myokit/myokit/pull/918) Added `IllegalReferenceInInitialValueError` for illegal references made in initial value expressions.
  - [#947](https://github.com/myokit/myokit/pull/947) @martinjrobins The `Simulation` class can now handle multiple protocols during a single simulation.
  - [#947](https://github.com/myokit/myokit/pull/947) Fixed-form protocols are now implemented in a `TimeSeriesProtocol`.
- Changed
  - [#898](https://github.com/myokit/myokit/pull/899) `Variable.promote` can now take an expression, a number, or a string (which will be parsed as an expression) for the argument `initial_value`.
  - [#909](https://github.com/myokit/myokit/pull/909) Myokit is now tested on Python 3.11.
  - [#909](https://github.com/myokit/myokit/pull/909) Myokit is no longer tested on Python 3.6.
  - [#918](https://github.com/myokit/myokit/pull/918) The only argument to `Variable.promote` has been renamed from `state_value` to `initial_value`.
  - [#918](https://github.com/myokit/myokit/pull/918) `Model.import_component` now preserves the ordering of the imported states.
  - [#953](https://github.com/myokit/myokit/pull/953) The DataLogViewer now overlaps traces with numbering (e.g. 0.membrane.V and 1.membrane.V), and toggles between files and variables with Page up and down Or Ctrl+Page up and down.
  - [#962](https://github.com/myokit/myokit/pull/962) Scipy is no longer a required dependency.
  - [#962](https://github.com/myokit/myokit/pull/962) The DataLogViewer only supports Matlab file loading if SciPy is installed.
  - [#975](https://github.com/myokit/myokit/pull/975) Global parameters in imported SBML documents are now placed in a component named `global` instead of `myokit`.
  - [#978](https://github.com/myokit/myokit/pull/978) The IDE now validates _either_ the model _or_ the protocol, depending on the current tab (previously both were validated).
- Deprecated
  - [#918](https://github.com/myokit/myokit/pull/918) `Model.state` is deprecated in favor of `Model.initial_values`.
  - [#918](https://github.com/myokit/myokit/pull/918) `Model.set_state` is deprecated in favor of `Model.set_initial_values`.
  - [#918](https://github.com/myokit/myokit/pull/918) `Model.inits` is deprecated.
  - [#918](https://github.com/myokit/myokit/pull/918) `Variable.state_value` is deprecated in favor of `Variable.initial_value`.
  - [#918](https://github.com/myokit/myokit/pull/918) `Variable.set_state_value` is deprecated in favor of `Variable.set_initial_value`.
  - [#918](https://github.com/myokit/myokit/pull/918) `Model.save_state` and `Model.load_state` are deprecated.
  - [#918](https://github.com/myokit/myokit/pull/918) The `Variable.promote` keyword argument `state_value` is deprecated in favor of `initial_value`.
  - [#947](https://github.com/myokit/myokit/pull/947) `Simulation.set_fixed_form_protocol` is deprecated in favor of using `Simulation.set_protocol` with a `TimeSeriesProtocol`
  - [#962](https://github.com/myokit/myokit/pull/962) The method `DataLog.regularize` is deprecated.
  - [#974](https://github.com/myokit/myokit/pull/974) `Variable.indice` is deprecated in favor of `Variable.index`.
  - [#976](https://github.com/myokit/myokit/pull/976) `SimulationOpenCL.neighbours` is deprecated in favor of `SimulationOpenCL.neighbors`.
- Removed
  - [#898](https://github.com/myokit/myokit/pull/899) `NonLiteralValueError` is now no longer raised by Myokit and so has been removed.
  - [#921](https://github.com/myokit/myokit/pull/921) Removed deprecated `LegacySimulation` class.
  - [#921](https://github.com/myokit/myokit/pull/921) Removed deprecated `PSimulation` class.
  - [#921](https://github.com/myokit/myokit/pull/921) Removed deprecated `ICSimulation` class.
  - [#957](https://github.com/myokit/myokit/pull/957) Removed the method `Model.prepare_bindings`.
  - [#961](https://github.com/myokit/myokit/pull/961) Removed the module `myokit.lib.common`, which had been deprecated since April 2018.
- Fixed
  - [#918](https://github.com/myokit/myokit/pull/918) Fixed error when `var()` was called on a `PartialDerivative` with a `Derivative` as first argument.
  - [#933](https://github.com/myokit/myokit/pull/933) Made `myokit.step` base its error classification (large/small/none) on numerics, not representation.
  - [#947](https://github.com/myokit/myokit/pull/947) Fixed minor memory leak (reference counting issue) when using fixed form protocols.
  - [#967](https://github.com/myokit/myokit/pull/967) Myokit no longer calls `logging.basicConfig()` when used as a library.
  - [#977](https://github.com/myokit/myokit/pull/977) `myokit.save()` now raises a `ValueError` if `model`, `protocol`, and `script` are all None.
  - [#978](https://github.com/myokit/myokit/pull/978) Clarified message shown in IDE after re-validation of valid model or protocol.

## [1.33.9] - 2022-11-08
- Fixed
  - [#908](https://github.com/myokit/myokit/pull/908) Added new homebrew location used on M1 apple devices, potentially solving [#861](https://github.com/myokit/myokit/issues/861).
  - [#912](https://github.com/myokit/myokit/pull/912) Reporting of numerical errors in `Simulation` now catches more exception types arising from `evaluate_derivatives`.
  - [#951](https://github.com/myokit/myokit/pull/951) Made syntax highlighting in IDE recognise units containing `-` and `*`.

## [1.33.8] - 2022-10-21
- Added
  - [#895](https://github.com/myokit/myokit/pull/895) Added method `Expression.depends_on_state()`.
  - [#901](https://github.com/myokit/myokit/pull/901) Added options `compatibility.no_capture` and `compatibility.no_fd_capture` to `myokit.ini` to allow users to tweak compiler output capturing.
  - [#903](https://github.com/myokit/myokit/pull/903) Fixed a bug in `SimulationOpenCL` that caused a `CL_INVALID_ARG_SIZE` error on strict systems.
- Changed
  - [#893](https://github.com/myokit/myokit/pull/893) `Variable.convert_unit` now returns `True` if a conversion was carried out or `False` if not.
- Fixed
  - [#888](https://github.com/myokit/myokit/pull/888) [#892](https://github.com/myokit/myokit/pull/892) Improved documentation for `Unit.conversion_factor` with help from @martinjrobins.
  - [#895](https://github.com/myokit/myokit/pull/895) Fixed the value returned by `Name.diff()` and `Expression.diff()` for the situation where the associated RHS depends on a bound variable.
  - [#895](https://github.com/myokit/myokit/pull/895) Fixed performance issue in `Expression.depends_on`.
  - [#896](https://github.com/myokit/myokit/pull/896) Small improvements to Model, Component, and Variable documentation. 

## [1.33.7] - 2022-07-27
- Fixed
  - [#883](https://github.com/myokit/myokit/pull/883) Fixed memory leak in `myokit.Simulation` when using the `log_times` argument.

## [1.33.6] - 2022-07-04
- Added
  - [#872](https://github.com/myokit/myokit/pull/872) The `myokit.Simulation` class can now be initialised using a precompiled backend (see the documentation for the ``path`` argument).
- Changed
  - [#872](https://github.com/myokit/myokit/pull/872) `Model.solvable_order` now returns consistently ordered equations, regardless of the order components and variables were created/parsed in.
  - [#872](https://github.com/myokit/myokit/pull/872) `myokit.tools.rmtree` now takes an optional argument `silent` that can be set to `True` to ignore any exceptions.
  - [#876](https://github.com/myokit/myokit/pull/876) `Model.import_component` can now take a list of possibly interdependent components.

## [1.33.5] - 2022-05-02
- Fixed
  - [#873](https://github.com/myokit/myokit/pull/873) Small bugfixes and improvements in numerical error reporting in `FiberTissueSimulation`.
  - [#873](https://github.com/myokit/myokit/pull/873) Fixed argument list in docstring of `FiberTissueSimulation`.

## [1.33.4] - 2022-04-22
- Added
  - [#869](https://github.com/myokit/myokit/pull/869) Added methods `myokit.FiberTissueSimulation.fiber_shape` and `.tissue_shape` (but see [https://github.com/myokit/myokit/issues/764] for an important open issue).
  - [#869](https://github.com/myokit/myokit/pull/869) Added a method `myokit.FiberTissueSimulation.step_size()`.
- Changed
  - [#865](https://github.com/myokit/myokit/pull/865) Added more platform information to `myokit system`.
  - [#866](https://github.com/myokit/myokit/pull/866) Slightly tweaked the plotting in `myokit.lib.plots.cumulative_current`, and added two arguments `line_args` and `fill_args` that can be used to customize the plotting style.
  - [#869](https://github.com/myokit/myokit/pull/869) The class `myokit.FiberTissueSimulation` now raises `ValueError` for various method-argument errors, instead of the more generic `Exception`.
  - [#869](https://github.com/myokit/myokit/pull/869) The class `myokit.FiberTissueSimulation` now raises `IndexError` for various index-related errors, instead of the less appropriate `KeyError`.
- Deprecated
  - [#869](https://github.com/myokit/myokit/pull/869) The class `myokit.FiberTissueSimulation` is no longer considered deprecated.
- Fixed
  - [#867](https://github.com/myokit/myokit/pull/867) @DavAug Fixed a memory leak in `myokit.Simulation`.
  - [#869](https://github.com/myokit/myokit/pull/869) Added a missing ``y`` argument to `FiberTissueSimulation.fiber_state()` and `FiberTissueSimulation.tissue_state()`.
  - [#869](https://github.com/myokit/myokit/pull/869) Fixed out-of-range checking in `FiberTissueSimulation` `state` and `set_state` methods.

## [1.33.3] - 2022-03-17
- Changed
  - [#860](https://github.com/myokit/myokit/pull/860) Made `myokit.tests` into a module. Made tests runnable via `setup.py`. Added more meta data to `setup.py`.

## [1.33.2] - 2022-03-17
- Changed
  - [#843](https://github.com/myokit/myokit/pull/843) Myokit is no longer tested on Python 3.5.
  - [#844](https://github.com/myokit/myokit/pull/844) Tweaked the CellML export's `initial_value` attribute to strip `e+00` if present.
  - [#845](https://github.com/myokit/myokit/pull/845) Improved syntax highlighting and automatic detection of "dark mode" themes.
  - [#849](https://github.com/myokit/myokit/pull/849) Trying to pickle a `myokit.Expression` now raises a more helpful error message.
  - [#849](https://github.com/myokit/myokit/pull/849) The method `myokit.parse_expression()` now accepts a `Model` as a context.
  - [#849](https://github.com/myokit/myokit/pull/849) Model comparison with `==` now only returns ``True`` if both operands are the same object. Comparison based on code can be performed with `Model.is_similar()`.
  - [#852](https://github.com/myokit/myokit/pull/852) Myokit is no longer tested on Python 3.6 for Windows (please use 3.7 and up).
- Fixed
  - [#841](https://github.com/myokit/myokit/pull/841) The MathMLExpressionWriter now uses `type="e-notation"` where necessary, instead of writing e.g. `1e-6`.
  - [#849](https://github.com/myokit/myokit/pull/849) If `Model.get()` and `Component.get()` now raise a `ValueError` if a component or variable from a different model is passed in.
  - [#849](https://github.com/myokit/myokit/pull/849) `Equation` objects are now immutable, and their `hash` is consistent during the object's lifetime.
  - [#849](https://github.com/myokit/myokit/pull/849) The `hash` of a `Quantity` object is now consistent during its lifetime, regardless of unit representations.
  - [#857](https://github.com/myokit/myokit/pull/857) Fixed a memory leak in Simulation.run().
  - [#858](https://github.com/myokit/myokit/pull/858) `OpenCL.info` no longer raises `CL_PLATFORM_NOT_FOUND_KHR` if drivers but no devices are found.

## [1.33.1] - 2022-01-24
- Added
  - [#799](https://github.com/myokit/myokit/pull/799) Added pL, MOhm, and GOhm as standard units.
  - [#811](https://github.com/myokit/myokit/pull/811) DatalogViewer now accepts `.zip` for binary data logs.
  - [#817](https://github.com/myokit/myokit/pull/816) Added support for Python 3.10.
  - [#821](https://github.com/myokit/myokit/pull/821) Sundials-based simulations now auto-detect the version number. The version indicated in myokit.ini is no longer used.
  - [#823](https://github.com/myokit/myokit/pull/823) Sundials 6.0.0 is now supported.
  - [#826](https://github.com/myokit/myokit/pull/826) Added a method `myokit.tools.Benchmarker.print` that prints elapsed time alongside a profiling message.
- Changed
  - Examples will be located in a separate repository, at https://github.com/myokit/myokit-examples
  - [#815](https://github.com/myokit/myokit/pull/815) Myokit will now warn when run on Python 2.7, as testing for 2.7 is being phased out.
  - [#816](https://github.com/myokit/myokit/pull/816) The method `myokit.tools.Benchmarker.format` can now be called without any arguments.
  - [#817](https://github.com/myokit/myokit/pull/816) The internal templating engine now uses `ast` instead of the deprecated (and removed in 3.10) `parser` module.
  - [#825](https://github.com/myokit/myokit/pull/825) The context manager `myokit.tools.capture` now takes an extra argument ``enabled`` which can be used to disabled output capturing.
  - [#825](https://github.com/myokit/myokit/pull/825), [#826](https://github.com/myokit/myokit/pull/826) The debugging arguments to ``myokit run`` have been split into five parts, see ``myokit run --help`` for details.
  - [#834](https://github.com/myokit/myokit/pull/834) The find/replace dialog in the IDE has been replaced with a toolbar.
  - [#836](https://github.com/myokit/myokit/pull/836) Colours in the IDE have been adapted to be clearer in "dark mode".
- Removed
  - [#796](https://github.com/myokit/myokit/pull/796) The Graph Data Extractor tool is now a separate project, hosted at https://github.com/myokit/gde.
  - [#804](https://github.com/myokit/myokit/pull/804) The command line utility `system` no longer reports on the `cma` module.
  - [#821](https://github.com/myokit/myokit/pull/821) Removed the method `myokit.Sundials.version_int`.
- Fixed
  - [#805](https://github.com/myokit/myokit/pull/805) Added missing command line utilities to the documentation, and re-organised the command-line tool docs.
  - [#831](https://github.com/myokit/myokit/pull/831) @DavAug Fixed bug in SBML parser that caused it to ignore terms in differential equations for products of reactions.

## [1.33.0] - 2021-08-04
- Added
  - [#581](https://github.com/myokit/myokit/pull/581) Myokit's expression system now includes a `PartialDerivative` and an `InitialValue` class. Both are for use in sensitivity calculations and may not appear in models.
  - [#581](https://github.com/myokit/myokit/pull/581) Expressions now have a method `diff(lhs)` that returns the (partial) derivative of an expression with respect to the given `LhsExpression`.
  - [#581](https://github.com/myokit/myokit/pull/581) Expressions now have methods `is_derivative`, `is_name`, and `is_number`.
  - [#581](https://github.com/myokit/myokit/pull/581) Added a method `Number.value()`.
  - [#581](https://github.com/myokit/myokit/pull/581) The method `Expression.depends_on` now has an argument `deep` that can be set to `True` to perform a recursive dependency check.
  - [#595](https://github.com/myokit/myokit/pull/595) A class `myokit.CModel` was added that can generate multi-purpose C code for use in simulations. This is mainly for internal use.
  - [#682](https://github.com/myokit/myokit/pull/682) OpenCL code now recognises error code -1001.
  - [#683](https://github.com/myokit/myokit/pull/683) Now testing OpenCL code in CI.
  - [#704](https://github.com/myokit/myokit/pull/704) Added first example notebook to the github repository.
  - [#728](https://github.com/myokit/myokit/pull/728) Added a context manager `myokit.tools.capture` that can redirect and capture output from Python `stdout` and `stderr` via a Python-only method or file-descriptor redirection and should be thread-safe.
  - [#735](https://github.com/myokit/myokit/pull/735) The new module `myokit.float` contains several functions related to floating point numbers that were previously in the main `myokit` namespace or not part of the public API.
  - [#735](https://github.com/myokit/myokit/pull/735) The new module `myokit.tools` contains several stand-alone tools that are used by Myokit and were previously in the main `myokit` namespace or not part of the public API.
  - [#735](https://github.com/myokit/myokit/pull/735) The method `pid_hash`, which is used by compiled code to generate (hopefully) unique ids is now part of the public API.
  - [#744](https://github.com/myokit/myokit/pull/744) Added a method `myokit.OpenCL.available` to check if OpenCL is supported and at least one OpenCL device is detected.
  - [#754](https://github.com/myokit/myokit/pull/754) Added a method `myokit.OpenCL.current_info(x)` that returns information about the currently selected platform and device; support of OpenCL extensions can then be checked with `OpenCLPlatformInfo.has_extension`.
  - [#754](https://github.com/myokit/myokit/pull/754) Improved error message when an `OpenCLSimulation` with double precision is run on a device that does not support it.
  - [#763](https://github.com/myokit/myokit/pull/763) Added a method `OpenCLSimulation.set_conductance_field` to apply heterogeneous conductance on a rectangular grid.
  - [#769](https://github.com/myokit/myokit/pull/769) @Rebecca-Rumney Added a method `myokit.Model.import_component` to import a component from one model to another.
  - [#769](https://github.com/myokit/myokit/pull/769) @Rebecca-Rumney Added an exception type `VariableMappingError` to be raised when there is an error in a variable mapping.
  - [#776](https://github.com/myokit/myokit/pull/776) Added a method `OpenCLSimulation.monodomain_conductance` to replace the deprecated method `calculate_conductance`.
  - [#780](https://github.com/myokit/myokit/pull/780) Alt-up and alt-down can now be used in the text editor to move selected lines up or down.
  - [#782](https://github.com/myokit/myokit/pull/782) The IDE can now import CellML files on opening, e.g. by typing `myokit ide example.cellml`.
  - [#786](https://github.com/myokit/myokit/pull/786) Added a method `myokit.Variable.clamp()` to fix any variable to a constant value.
  - [#786](https://github.com/myokit/myokit/pull/786) Added a method `myokit.Variable.remove_child_variables()` to remove all child (nested) variables from a given variable.
  - [#788](https://github.com/myokit/myokit/pull/788) The IDE will now suggest filenames for model exports.
  - [#792](https://github.com/myokit/myokit/pull/792) @DavAug SBML import now handles equations that explicitly use time.
- Changed
  - [#581](https://github.com/myokit/myokit/pull/581) Powers are now rendered without spaces in mmt code, e.g. `x^2` instead of `x ^ 2`.
  - [#595](https://github.com/myokit/myokit/pull/595) The `Simulation` class now uses CVODES instead of CVODE as backend, which may require changes to your installation.
  - [#595](https://github.com/myokit/myokit/pull/595) The `Simulation` can now calculate sensitivities of variables with respect to parameters and/or initial conditions (see docs for details).
  - [#595](https://github.com/myokit/myokit/pull/595) The `Simulation` class no longer has `apd_var` as a constructor argument. Instead, you can pass an argument `apd_variable` to its `run()` method.
  - [#595](https://github.com/myokit/myokit/pull/595) The `Simulation` class no longer suppresses CVODES warnings but passes them on to the `warnings` module.
  - [#595](https://github.com/myokit/myokit/pull/595) Fix to `Simulation` for Sundials 4.1.0.
  - [#687](https://github.com/myokit/myokit/pull/687) `Variable.set_rhs(None)` now removes an RHS, instead of setting it to `Number(0)`.
  - [#687](https://github.com/myokit/myokit/pull/687) Calling `SimulationOpenCL.set_conductance` will now override any conductances previously set with `set_connections`.
  - [#687](https://github.com/myokit/myokit/pull/687) `SimulationOpenCL.set_connections` no longer accepts `None` as a valid argument.
  - [#687](https://github.com/myokit/myokit/pull/687) The `SimulationOpenCL` methods `set_conductance`, `conductance`, `set_connections`, `neighbours`, `set_paced_cells`, `set_paced_cell_list`, and `is_paced`, will now raise a `RuntimeError` if diffusion was disabled at construction.
  - [#687](https://github.com/myokit/myokit/pull/687) The method `SimulationOpenCL.remove_field` now raises a `KeyError` if no field is set for the given variable.
  - [#689](https://github.com/myokit/myokit/pull/689) In Python 2, an `ImportError` is now raised if `myokit.ini` contains the sequence " ;" in any of its value (as this cannot be processed by Python 2's `ConfigParser`).
  - [#728](https://github.com/myokit/myokit/pull/728) The `LegacySimulation` class no longer suppresses CVODE warnings but passes them on to the `warnings` module (backported from new `Simulation` class).
  - [#789](https://github.com/myokit/myokit/pull/789) The method `myokit.DataLog.save_csv()` now stores the keys using natural sort order (time is still the first field, if present).
- Deprecated
  - [#595](https://github.com/myokit/myokit/pull/595) The classes `myokit.PSimulation` and `myokit.ICSimulation` have been deprecated in favor of the new `Simulation` class.
  - [#735](https://github.com/myokit/myokit/pull/735) The class `myokit.Benchmarker` is deprecated in favor of `myokit.tools.Benchmarker`.
  - [#735](https://github.com/myokit/myokit/pull/735) The method `myokit.format_float_dict` is deprecated and will be removed in future versions.
  - [#735](https://github.com/myokit/myokit/pull/735) The method `myokit.format_path` is deprecated in favor of `myokit.tools.format_path`.
  - [#735](https://github.com/myokit/myokit/pull/735) The method `myokit.strfloat` is deprecated in favor of `myokit.float.str`.
  - [#758](https://github.com/myokit/myokit/pull/758) The class `myokit.FiberTissueSimulation` is deprecated and will be removed in future versions.
  - [#776](https://github.com/myokit/myokit/pull/776) The method `OpenCLSimulation.calculate_conductance` is deprecated in favor of the new method `calculate_conductance`, which takes slightly different parameters.
  - [#787](https://github.com/myokit/myokit/pull/787) The method `myokit.Model.eval_state_derivatives` is deprecated in favor of `myokit.Model.evaluate_derivatives`.
- Removed
  - [#683](https://github.com/myokit/myokit/pull/683) No longer testing on Python 2.7.6 on linux (still testing latest 2.7). No longer testing any Python 2.7 on Windows.
  - [#728](https://github.com/myokit/myokit/pull/728) The classes `myokit.PyCapture` and `myokit.SubCapture` have been replaced by a single context manager `myokit.tools.capture`.
  - [#730](https://github.com/myokit/myokit/pull/730) Removed the method `myokit.pack_snapshot`.
  - [#737](https://github.com/myokit/myokit/pull/737) The method `Model.merge_interdependent_components` was removed. This method was deprecated since 2018-05-30.
  - [#737](https://github.com/myokit/myokit/pull/737) The method `Model.show_line` was removed. This method was deprecated since 2018-05-30.
  - [#737](https://github.com/myokit/myokit/pull/737) The method `Protocol.guess_duration` was removed. This method was deprecated since 2016-02-06.
- Fixed 
  - [#684](https://github.com/myokit/myokit/pull/684) @DavAug Fixed OpenCL loading issue on MacOS (with special thanks to Martin Aguilar).
  - [#686](https://github.com/myokit/myokit/pull/686) Fixed a (windows only) bug in `myokit.tools.format_path()`.
  - [#687](https://github.com/myokit/myokit/pull/687) `Simulation1d` now logs pacing as a global variable, and can log diffusion currents.
  - [#689](https://github.com/myokit/myokit/pull/689) Path lists read from `myokit.ini` are now filtered for empty entries and closing semicolons.
  - [#744](https://github.com/myokit/myokit/pull/744) Fixed a bug in `OpenCLSimulation.find_nan()`, that occurred for very small simulations (e.g. 2 cells).
  - [#744](https://github.com/myokit/myokit/pull/744) Fixed a bug in `OpenCLSimulation` that made it impossible to use `set_connections()` with double precision.
  - [#744](https://github.com/myokit/myokit/pull/744) Fixed a bug in `OpenCLSimulation` that made it impossible to use `set_connections()` on Python 2.
  - [#754](https://github.com/myokit/myokit/pull/754) Improved error message when an `OpenCLSimulation` with double precision is run on a device that does not support it.
  - [#766](https://github.com/myokit/myokit/pull/766) Improved error message when an empty MathML `<cn>` element is encountered.

## [1.32.0] - 2021-01-19
- Added
  - [#672](https://github.com/myokit/myokit/pull/672) Added more detailed error output to several CVODE errors related to RHS-related numerical issues.
  - [#672](https://github.com/myokit/myokit/pull/672) Now tested on Sundials 5 (locally).
  - [#672](https://github.com/myokit/myokit/pull/672) Now testing on Python 3.9 (Linux).
  - [#672](https://github.com/myokit/myokit/pull/672) `Simulation.run` documentation is now more clear on what happens for very short simulation durations (or zero).
  - [#674](https://github.com/myokit/myokit/pull/674) Added a method `Model.has_parse_info` that checks if the model contains information from parsing (i.e. line numbers).
  - [#674](https://github.com/myokit/myokit/pull/674) Added a parameter `raw` to `Model.show_line_of` that returns the line number as an integer
  - [#674](https://github.com/myokit/myokit/pull/674) Added a method to the IDE that lets you jump to the definition of a selected variable.
  - [#680](https://github.com/myokit/myokit/pull/680) Now testing on Python 3.9 and Miniconda 3.8 (Windows).
- Removed
  - [#681](https://github.com/myokit/myokit/pull/681) Removed the deprecated library `myokit.lib.fit`. For fitting see e.g. [PINTS](https://github.com/pints-team/pints) and this [tutorial on fitting ion channel data with Myokit & PINTS](https://github.com/CardiacModelling/fitting-notebooks).
- Fixed
  - [#672](https://github.com/myokit/myokit/pull/672) Fixed bug in `Variable.convert_unit()` that caused unexpected (and quite arbitrary) results.
  - [#672](https://github.com/myokit/myokit/pull/672) Fixed bug where calling `Simulation.run()` with a very short runtime caused a zero state to be returned.
  - [#676](https://github.com/myokit/myokit/pull/676) Fixed a bug in CellML (1 and 2) export when inferring units for a state variable.
  - [#679](https://github.com/myokit/myokit/pull/679) Fixed "DLL load failed while importing myokit" issue on Windows 10 with Python 3.8 (via miniconda).

## [1.31.1] - 2020-12-01
- Added
  - [#623](https://github.com/myokit/myokit/pull/623) The changes made with each release are now stored in CHANGELOG.md.
  - [#622](https://github.com/myokit/myokit/pull/622) `SimulationOpenCL` now includes a method `is_paced` and `neighbours` that provide information about the simulated cells.
  - [#622](https://github.com/myokit/myokit/pull/622) `SimulationOpenCL.find_nan` now has an option to return a `DataLog` with the final logged variables before the error occurred.
  - [#632](https://github.com/myokit/myokit/pull/632) Added methods `DataBlock1d.to_log` and `DataBlock2d.to_log`.
  - [#633](https://github.com/myokit/myokit/pull/633) DataBlockViewer now shows mouse coordinates in status bar for video and graph view.
  - [#652](https://github.com/myokit/myokit/pull/652) Added methods to remove 1d and 2d traces from `DataBlock1d` and `DataBlock2d`.
- Changed
  - [#610](https://github.com/myokit/myokit/pull/610) If numerical errors occur when evaluating an expression, the IDE now shows these in the console instead of in a pop-up.
  - [#622](https://github.com/myokit/myokit/pull/622) `myokit.strfloat` now takes a `precision` argument.
  - [#622](https://github.com/myokit/myokit/pull/622) `Model.format_state` and `Model.format_state_derivatives` now take a `precision` argument.
  - [#622](https://github.com/myokit/myokit/pull/622) If errors occur, the `SimulationOpenCL` now displays improved (and hopefully more informative) output.
  - [#623](https://github.com/myokit/myokit/pull/623) Updated licensing info.
  - [#653](https://github.com/myokit/myokit/pull/653) `Model.pyfunc()` now validates the model before running (and fails if the model does not validate).
  - [#661](https://github.com/myokit/myokit/pull/661) When importing MathML, the inverse hyperbolic trig functions are now rendered using slightly simpler equations.
  - [#664](https://github.com/myokit/myokit/pull/664) EasyML export now adds meta data, a group of CVODE-solved variables, a group of variables to trace, and a group of parameters (based on code contributed by Ed Vigmond).
  - [#664](https://github.com/myokit/myokit/pull/664) EasyML export now converts voltage, current, and time variables to the preferred units.
  - [#664](https://github.com/myokit/myokit/pull/664) EasyML export now has consistently ordered output when re-run.
  - [#664](https://github.com/myokit/myokit/pull/664) EasyML expression writer now uses `expm1` where possible.
- Deprecated
  - [#622](https://github.com/myokit/myokit/pull/622) `SimulationOpenCL.is2d()` was deprecated in favor of `SimulationOpenCL.is_2d()`.
  - [#632](https://github.com/myokit/myokit/pull/632) `DataBlock1d.from_DataLog` and `DataBlock2d.from_DataLog` have both been deprecated, in favor of new `from_log` methods.
- Fixed
  - [#650](https://github.com/myokit/myokit/pull/650) Fix to `myokit.lib.plots.cumulative_current` for normalisation in areas with zero current.
  - [#603](https://github.com/myokit/myokit/pull/603) Improved handling of types (ints resulting from logical operators) in `OpenCLSimulation`.
  - [#613](https://github.com/myokit/myokit/pull/613) `Model.map_component_io` now respects the `omit_constants` argument for Rush-Larsen variables.
  - [#622](https://github.com/myokit/myokit/pull/622) If `Model.format_state_derivatives` needs to evaluate the derivatives, it will now use the given `state` instead of the model state.
  - [#628](https://github.com/myokit/myokit/pull/628) The DataBlockViewer now shows a working colour bar for 1d simulations.
  - [#638](https://github.com/myokit/myokit/pull/638) The DataBlockViewer now handles blocks with `t[0] > 0` correctly.
  - [#655](https://github.com/myokit/myokit/pull/655) Fixed bug where wrong initial state was shown by `myokit.step()`.
  - [#663](https://github.com/myokit/myokit/pull/663) Fixed deprecation warning in `save_state_bin()`.

## [1.31.0] - 2020-08-26
- Added
  - [#548](https://github.com/myokit/myokit/pull/548) Models, protocols, and CVODE simulations can now be pickled, and tests have been added that check that simulations can be run in parallel (even on Windows). 
  - [#548](https://github.com/myokit/myokit/pull/548) Model and protocol now support comparison with `==`.
  - [#553](https://github.com/myokit/myokit/pull/553) The cumulative-current plot now has a maximum-number-of-currents option (all further currents will be bundled into one).
  - [#567](https://github.com/myokit/myokit/pull/567) Added support for Simulation building on Python 3.8 on Windows.
  - [#574](https://github.com/myokit/myokit/pull/574), [#599](https://github.com/myokit/myokit/pull/599), [#547](https://github.com/myokit/myokit/pull/547), [#528](https://github.com/myokit/myokit/pull/528) @DavAug A completely rewritten SBML API and parser that's capable of handling models that define species and reactions.
- Changed
  - [#536](https://github.com/myokit/myokit/issues/536) `Ohm` is now a quantifiable unit in the `mmt` syntax, i.e. `1 [MOhm]`. This replaces the non-standard `R` unit which has been removed.
  - [#556](https://github.com/myokit/myokit/pull/556) CellML imports now import models that contain unsupported units (but with warnings).
  - [#557](https://github.com/myokit/myokit/pull/557) Imports and exports now raise warnings instead of using the Myokit textlogger for this.
  - [#559](https://github.com/myokit/myokit/pull/559), [#541](https://github.com/myokit/myokit/pull/541) Unit tests are now included in the PyPI package.
  - [#560](https://github.com/myokit/myokit/pull/560) Sympy is no longer a required dependency (but still an optional one).
  - [#565](https://github.com/myokit/myokit/pull/565) Some slight changes to simulation building: Now uses `--inplace` instead of `--old-and-unmanageable` and should delete any temporary files created in the process.
  - [#566](https://github.com/myokit/myokit/pull/566) Simulations now include a time and process number dependent hash in their generated-module names.
  - [#569](https://github.com/myokit/myokit/pull/569) The CellML export now ensures there are no spaces in initial value or unit multiplier attributes.
  - [#576](https://github.com/myokit/myokit/pull/576) Non-integer exponents are now allowed in the unit system, which compares units with a `close()` method that expects a certain numerical tolerance, instead of using exact comparison.
  - [#576](https://github.com/myokit/myokit/pull/576) CellML imports now import models with non-integer unit exponents.
  - [#597](https://github.com/myokit/myokit/pull/597) The output of the `step()` method has been improved, and the method now only warns about relative differences bigger than 1 epsilon.
  - [commit](https://github.com/myokit/myokit/commit/fc08debb03bd0f2e2d93a52fc0dc9e907448d057) The method `show_evalution_of` now has consistently ordered output.
  - CellML imports treat new base units as dimensionless.
  - The IDE now checks the protocol even if the model is invalid or unchanged.
- Removed
  - [#563](https://github.com/myokit/myokit/pull/563), [#564](https://github.com/myokit/myokit/pull/564) The `myokit.mxml` module has been removed.
- Fixed
  - [#539](https://github.com/myokit/myokit/pull/539) Bugfix for simulations that ended at a time numerically indistinguishable from an event time.
  - [#570](https://github.com/myokit/myokit/pull/570) Bugfixes and fewer warnings for various matplotlib versions.
  - [#572](https://github.com/myokit/myokit/pull/572) Bugfix to `lib.common.StrenghtDuration`.
  - [#585](https://github.com/myokit/myokit/pull/585) A recently introduced bug in the `HHSimulation`'s `steady_state()` method was fixed.

## [1.30.6] - 2020-04-29
- Fixed
  - [#531](https://github.com/myokit/myokit/pull/531) Fixed bug where GUI CellML export didn't export stimulus current.

## [1.30.5] - 2020-04-20
- Added
  - [#525](https://github.com/myokit/myokit/pull/525) Added support for CellML 2.0.
- Changed
  - [#516](https://github.com/myokit/myokit/pull/516) Rewrote SBML import to use etree instead of DOM.
- Removed
  - [#522](https://github.com/myokit/myokit/pull/522) Removed `myokit.formats.mathml.parse_mathml_dom` function.
  - [#522](https://github.com/myokit/myokit/pull/522) Removed mxml `myokit.mxml.dom_child` and `myokit.mxml.dom_next` methods.
- Fixed
  - [#515](https://github.com/myokit/myokit/pull/515) Now setting OpenCL framework as linker flag on MacOS.

## [1.30.4] - 2020-03-27
- Added
  - [#503](https://github.com/myokit/myokit/pull/503) Added `clone()` and `__repr__()` methods to myokit.Equation.
  - [#507](https://github.com/myokit/myokit/pull/507) Fixed a bug with running simulations in Spyder on Windows.
- Fixed
  - [#496](https://github.com/myokit/myokit/pull/496) Some fixes and tweaks to CellML 1.0/1.1 API.

## [1.30.3] - 2020-03-02
- Small fixes to CellML validation.
- Fixed typo in units `becquerel`.
- Added `notanumber` and `infinity` to MathML parser.

## [1.30.2] - 2020-02-01
- Removed `myo` script.
- Fixed EasyML issue for inf/tau variables used by more than one state.

## [1.30.1] - 2020-01-03
- Added more import/export options to the IDE menu.
- Updated `component.code()` to always outout aliases in the same order.
- Added method to find Markov models in a Myokit model.
- Added method to convert Markov models to compact form.
- Added method to convert Markov models to full ODE form.
- LinearModel now converts to full ODE form.
- Added method `lib.guess.membrane_capacitance`.
- Added method `lib.guess.membrane_currents`.
- Added (experimental) EasyML export.
- Small bugfixes and documentation updates.
- Improved exception handling when evaluating a unit containing an invalid power.
- Made default script and protocol robust against incompatible units.
- Made CellML API `from_myokit_model` more robust against invalid units.

## [1.30.0] - 2019-12-30
- Rewrote CellML import and export, with improved error handling and validation.
- CellML import now converts hardcoded stimulus equation to Myokit protocol.
- CellML export now converts Myokit protocol to hardcoded stimulus equation.
- CellML import now generates more approprate default scripts.
- CellML import now supports unit conversion between components.
- CellML export now infers units from RHS if no unit set.
- CellML import and export can now both handle Web Lab `oxmeta` annotations.
- Various changes and improvements to MathML parsing.
- Added missing `__iter__` to Model and VarOwner.
- The myokit.Name expression can now wrap objects other than myokit.Variable, allowing Myokit's expression system to be re-used for non-myokit expressions.
- Removed myokit.UnsupportedFunction.

## [1.29.1] - 2019-11-24
- Added guessing module, with method to guess which variables (if any) represent the membrane potential and stimulus current.
- Fix for sundials development versions.
- Fixes for PySide2 support.

## [1.29.0] - 2019-10-11
- Myokit is now released under a BSD 3-clause license
- Bugfix to `myokit step` command line tool.

## [1.28.9] - 2019-09-11
- Added PySide2 support.
- Deprecated PyQt4 and PySide.
- Added a method `Model.remove_derivative_references()`.
- Bugfix to `Model.repr()` for models with no name.
- Added `Model.timex()`, `labelx()` and `bindingx()`, which work like `time()`, `label()` and `binding()` but raise an exception if no appropriate variable is found.
- Deprecated `lib.multi.time()`, `label()`, and `binding()`.

## [1.28.8] - 2019-09-03
- Added method `Variable.convert_unit()` that changes a variable's units and updates the model equations accordingly.
- `Unit.conversion_factor` now returns a `Quantity` instead of a float, and accepts helper `Quantity` objects for incompatible conversions.
- Added `Unit.clarify()` method that gives clear representation.
- Added `Unit.multiplier_log_10()` method.
- Added `rtruediv` and `pow` operators to `Quantity` class.
- Small bugfixes to `myokit.lib.hh`.
- Stopped requiring HH alphas/betas and taus/infs to depend on V (allows drug-binding work).
- Bugfix: Time variable in CellML export no longer has equation or initial value.
- CellML export: components now ordered alphabetically.
- Variables with an `oxmeta: time` meta annotation are now exported to CellML with an oxmeta RDF annotation.
- CellML import now allows `deca` prefix.
- Added CellML identifier checks to cellml import.
- Renamed `DataLog.find()` to `find_after()`.
- Added DataLog.interpolate_at(name, time) method.
- Improved colormap used in `plots.cumulative_current()`.
- Bugfix to 'myokit step' for models without a name meta property.
- Updated sign error handling in `myokit.step()`.
- Added IDE shortcuts for unit checking.
- IDE now jumps to unit errors, if found.
- Improved exception display in IDE.
- Var_info now includes unit.
- Fixed bug in `Unit.__repr__` for small multipliers.
- Improved notation of units when complaining about them.

## [1.28.7] - 2019-08-03
- Added option to register external formats.
- Added option to avoid certain prefixes when generating unique variable names.
- `Model.expressions_for()` now accepts more than 1 argument, and handles dependencies on derivatives correctly.
- Removed deprecated method `Model.solvable_subset()`.

## [1.28.6] - 2019-07-26
- Added debug option to `myokit compiler` command.

## [1.28.5] - 2019-07-16
- Bugfix: Removing variables now also removes their bindings and labels.
- Added unit tests.
- Improved performance in `lib.markov` analytical simulations.
- Updated the `myo` script to use the python3 executable.
- Fixed a bug in the default script used when creating or importing a model.
- Made GNOME/KDE icons install using sys.executable instead of a hardcoded python command.
- Fixed handling of string encoding in cellml import.

## [1.28.4] - 2019-05-28
- Myokit is now tested on Python 3.7, but no longer on 3.4.
- Updated default OpenCL paths for windows.
- GUI fixes for matplotlib 3.1.0+.
- Added `set_constant()` method to markov simulations.
- Added `log_times` option to `lib.markov.AnalyticalSimulation`, and started pre-allocating arrays.
- Added option to cumulative current plot to normalise currents.

## [1.28.3] - 2019-05-02
- Fixed some floating point issues with protocols and pacing.
- Updated OpenCL code to work with VS 9.
- Some small changes to the Protocol API.
- Added format protocol option to IDE.

## [1.28.2] - 2018-12-19
- Improved support for native OpenCL on MacOS.
- Native maths in OpenCL simulations is now configurable and disabled by default.

## [1.28.1] - 2018-12-19
- Added support for Sundials 4.0.0
- Made SymPy a dependency.
- Made current loggable in discrete markov simulations.
- Added `log_times` argument to analytical HH simulation.
- Improved performance of analytical HH simulation.
- Added `AbfFile.extract_channel` method that joins sweeps.
- Added `ATF` capability to datalog viewer.
- Added limited `.pro` support to `DataLogViewer`.
- Added `ProgressReporter` that cancels the operation after a time out.
- Added cut/copy/paste options to menu in IDE.
- Bugfix: `myokit.system` didn't check for SymPy version.
- Deprecated `myo` script.
- Changed myokit.VERSION to `myokit.__version__`.
- Various minor tweaks and fixes.

## [1.28.0] - 2018-11-22
- Added `myokit.lib.hh` module for recognising Hodgkin-Huxley style ion current models and using them in fast analytical simulations.
- Added Rush-Larsen (RL) option to OpenCLSimulation.
- Added CUDA kernel export with RL updates.
- Added `OpenCLRLExporter` for OpenCL kernel with Rush-Larsen.
- Improved logging of intermediary variables in OpenCL simulations.
- Improved logging in `Simulation1d`.
- Fix to ABF reader for (unsupported) userlists (abf v2).
- Fixes to Sundials configuration on Windows.
- Small bugfixes, documentation updates, etc.

## [1.27.7] - 2018-11-01
- Various fixes to make Myokit work with Python 2.7.6 (and later).

## [1.27.6] - 2018-09-27
- Now running sundials auto-detection with every `import myokit` if not set in config file.

## [1.27.5] - 2018-09-20
- Bugfix to `OpenCL.load_selection`.
- Added system info command.
- Added command option to show C Compiler support.
- Added command option to show Sundials support.
- Bugfix to `Unit.rdiv`.
- Small fixes to `lib.fit`.
- Documentation config update for `sphinx >=1.8`.
- Parsing now has full test cover.
- Removed special line feed code from parser, as in unicode they are treated as newlines (and stripped out by `splitlines()`).
- Removed obsolete `TEXT_OPS` code from parser.
- Removed redundant check from parser.
- Removed another redundant check from parser.
- Various small bugfixes and tweaks.

## [1.27.4] - 2018-08-12
- Added sundials version detection on first run.
- Moved myokit config files from `~/.myokit` to `~/.config/myokit`.
- Renamed `NumpyExpressionwriter` to `NumPyExpressionWriter`.
- Fixed test issues on MacOS.

## [1.27.3] - 2018-08-06
- Updated the way sundials library locations are stored on windows systems.

## [1.27.2] - 2018-08-04
- Added script that creates icons for windows.
- Updated script that creates icons for linux.

## [1.27.1] - 2018-08-03
- Placeholder release to fix Pypi issue.

## [1.27.0] - 2018-08-03
- Added support for Python 3.4, 3.5, and 3.6.
- Added support for Sundials 3 (by @teosbpl).
- Added support for various Visual C++ compilers.
- Made Myokit pip-installable, stopped providing windows installer.
- Replaced windows sundials binaries with Visual-Studio compiled ones.
- Added a system-wide `myokit` command (after pip install on unix systems).
- Moved development from private repo to GitHub.
- Set up automated testing with Travis (linux) and Appveyor (windows).
- Greatly increased unit-test coverage (and set up checking with codecov.io).
- Added contribution guidelines.
- Added style checking with `flake8`.
- Removed `OrderedPiecewise`, `Polynomial`, `Spline`, and `lib.approx`.
- Deprecated `lib.fit`. Please have a look at [PINTS](https://github.com/pints-team/pints) instead.
- Removed `quadfit()` methods from `lib.fit`.
- Deprecated `lib.common`
- Removed HTML page generating classes from mxml.
- Simplified some of the error classes.
- Simplified `Benchmarker`.
- `DataLog.apd()` now has same output as Simulation threshold crossing finder.
- On-the-fly compilation switched from distutils to setuptools.
- Tidied up.
- Lots of bugfixes.
- Made IDE show Python version in about screen.

## [1.26.3] - 2018-02-09
- Fixed critical bug introduced in version 1.26.2 that stopped Windows simulations from running.

## [1.26.2] - 2018-01-11
- Fixed a small bug in `Simulation`'s logging when using the new `log_times` argument.
- Added Matlab and text file tab to DataLog viewer.
- Removed ancient restriction on components not being called `external`.
- Refactored code to pass flake8 tests.
- Added `len()` method to Protocol.
- Now setting `runtime_libraries` parameter for all compiled classes (simulations), removing the need to set `LD_LIBRARY_PATH` on some systems.

## [1.26.1] - 2017-11-24
- Updated licensing info.

## [1.26.0] - 2017-11-24
- Myokit can now be installed as library using `python setup.py develop`.
- Fixed a bug in the gnome scripts that install icons.
- The `DataLog` `trim`, `itrim` and `extend` methods now return copies, instead of modifying the data 'in place'. 
  This makes the `DataLog`'s methods more consistent, and prevents accidental data loss.
  However, this change makes Myokit 1.26.0 slightly backwards incompatible.
- Added a `DataLog.keys_like` method to iterate over 1d or 2d logs.

## [1.25.3] - 2017-10-06
- Small tweaks to IDE
- Fix to `DataLog.fold()` to discard remainder if period doesn't exactly divide the log length.
- Various bugfixes.
- Improved cvode error catching.
- More control over `lib.fit` verbosity
- Added random starting point option to lib.fit methods.
- Added the option to explicitly specify log points in the single-cell `Simulation` class.
- CVODE sim now raises `SimulationError` if maximum number of repeated zero-steps is made, instead of plain `Exception`.
- Fix `fit.cmaes` to work with cma version 2.x

## [1.25.2] - 2017-08-03
- Small tweaks to IDE.
- Fixed bug with saving the time variable in `DataLog.save_csv()`.

## [1.25.1] - 2017-07-18
- Added xNES and SNES optimisation methods.
- Added interface to CMA-ES optimisation method.
- Replaced the 'tolerance' arguments `in myokit.lib.fit` with more accurate counterparts.
- Removed `ga()` optimisation method.

## [1.25.0] - 2017-07-10
- Added model export to Stan.
- Added data-clamp to CVODE simulation (works, but generally a bad idea).
- Added Protocol.add_step convenience method for building sequential step protocols.
- Added `log()` method to `ExportError`.
- Fixed bug in ABF reading (ABF channel index can be greater than number of channels in file).
- Small fixes to `DataLogViewer`.
- Fixed issue with PySide file open/save dialogs.
- Several small fixes to docs.

## [1.24.4] - 2017-05-04
- Bugfix in PyQt4 support.

## [1.24.3] - 2017-05-03
- Fixed PyQt4/5 and PySide compatibility issue that was causing errors in the DataBlock viewer's open function.

## [1.24.2] - 2017-03-28
- Added missing #pragma directive to enable double-precision simulations OpenCL.

## [1.24.1] - 2016-10-24
- Added support for PyQt5.

## [1.24.0] - 2016-10-14
- The IDE now has a model navigator, that displays the model components alphabetically and lets you navigate large models more easily.
- Fixed a bug in the implementation of `DataBlock1d.grid()`, and updated its documentation: this method returns coordinates for squares where each square represents a data point.
  See the [Stewart 2009 OpenCL example](http://myokit.org/examples/#stewart-2009) for an example of its use.
- Added a second method `DataBlock1d.image_grid()` that returns coordinates for points where each point in space represents a data point.
- Fixed bug with Ctrl+Shift+Home in IDE.
- Various small bugfixes in IDE.
- Updated installation instructions on website.

## [1.23.4] - 2016-09-04
- Fixed bug (with new numpy) in `DataLog.split_periodic`.
- Fixed warnings in GDE.
- Fixed issue with pyside/pyqt difference.

## [1.23.3] - 2016-07-21
- Updated documentation and examples.
- Added extra callback option to pso for detailed feedback.
- Updated default search paths for Sundials headers and libraries.

## [1.23.2] - 2016-06-16
- Small bugfix to IDE.
- Added `pre()` method to Markov simulations (`AnalyticalSimulation` and `DiscreteSimulation`).
- Fixed a bug in `lib.markov.AnalyticalSimulation.run` when `log_interval >= duration`.
- IDE now shows exact location of recent files in status bar.
- Fixed bug in `SymPyExpressionWriter.eq()` and renamed classes to use SymPy with capital P.

## [1.23.1] - 2016-06-05
- Updated documentation.
- Fixed opencl issue.

## [1.23.0] - 2016-05-30
- Added methods for easier symbolic addition of names/components for situations where exact names aren't important.
- Bugfix to datalog viewer.
- Bugfix to vargrapher.

## [1.22.7] - 2016-05-25
- Update to ide: Can now add/remove comments.
- Bugfixes to protocol reading in `AbfFile`.
- Bugfix in `AbfFile` string reading.
- DataLog viewer now opens multiple files if specified on the command line.
- Fix to OpenCL sim reserved names list.
- Various tweaks and fixes.

## [1.22.6] - 2016-03-11
- Fixed bug in IDE.
- Fix to windows start menu icons.

## [1.22.5] - 2016-02-25
- Updated online examples.
- Bugfix in deprecated method `Protocol.guess_duration()`.

## [1.22.4] - 2016-02-24
- Fixed bug with auto-indenting and smart up/down arrows in IDE.
- Fixed bug in parsing of indented multi-line meta-data properties.
- Fixed bug with `[[script]]` sections being added to files when saved.
- Slight update to `DataLog.apd()`.
- Updated the docs of both apd methods to make clear that they use fixed thresholds.

## [1.22.3] - 2016-02-19
- Added hybrid PSO option to `myokit.lib.fit`.
- Added option to return multiple particles' results to PSO.
- Bugfixes and updates to documentation.
- Added BFGS method (interface to scipy) to `myokit.lib.fit`.

## [1.22.2] - 2016-02-08
- Small bugfix in markov simulation class.

## [1.22.1] - 2016-02-08
- Updates to source highlighting in the IDE.
- Various small bugfixes.
- Protocols and events now define a 'characteristic time'.
- The protocol class is now slightly stricter than before, removed its `validate()` method.
- Both markov model simulation classes can now run simulations based on `myokit.Protocol` objects.

## [1.22.0] - 2016-01-28
- Rewrote the Markov model module.
- Added a method to perform stochastic simulations with Markov models.
- Various small bugfixes.

## [1.21.12] - 2016-01-20
- The CellML export now includes a simple periodic pacing protocol.
- Various small bugfixes.

## [1.21.11] - 2016-01-05
- Tidied up code.

## [1.21.10] - 2016-01-04
- Various small bugfixes.

## [1.21.9] - 2015-12-28
- Various small bugfixes.

## [1.21.8] - 2015-11-05
- Removed option to run `mmt` files in threads (was not used and caused issues with GUI).
- Giving up on multiprocessing on windows. Adding switches to disable it in the examples.
- Various bugfixes and improvements.

## [1.21.7] - 2015-10-27
- Improved logging in simulations, made it more consistent throughout Myokit.

## [1.21.6] - 2015-10-23
- Various small bugfixes, improvements and website updates.

## [1.21.5] - 2015-10-14
- Changed the way states are stored in the model (list instead of OrderedDict). Was causing funny bug. Now has less redundant info.
- Fixed bug in `remove_component()`.

## [1.21.4] - 2015-10-06
- Added debug options to openclsim.
- OpenCL sim can now pace based on rules again, which is far more efficient for large numbers of cells.

## [1.21.3] - 2015-10-06
- Various bugfixes.

## [1.21.2] - 2015-10-05
- Added OpenCL device selection.
- Updated cumulative current plot method.

## [1.21.1] - 2015-09-12
- Various small bugfixes and improvements.

## [1.21.0] - 2015-09-04
- Add Powell's method to fit library.
- Added model statistics screen to IDE.
- Presence of `<import>` tag in CellML now causes exception instead of warning.
- Improved CellML import error messages.
- There is no longer a restriction on the type of expression used as a first argument to piecewise and if.
- Fixes to MathML parser and CellML import.
- Added option to extract colormap to DataBlock viewer.
- Added section about uninstalling on windows and slight hints about filesizes to website.
- Introduced "evaluator" class used for parallelized optimization algorithms. Rewrote PSO to use it.
- Added a genetic algorithm optimization method (does not outperform PSO).
- Added reset script to myo that removes all user settings i.e. the entire `DIR_MYOKIT`.
- Added version check to avoid Python3.
- Myokit for WinPython now has an uninstaller that shows up in "Add/Remove programs".
- Various small bugfixes and improvements.

## [1.20.5] - 2015-06-01
- Added Python version check.
- Fitting library: Adding quadratic polynomial fit used to test local optima.
- Various small bugfixes.

## [1.20.4] - 2015-05-11
- Improved export of units to CellML.
- `DataLogViewer` can now open CSV.
- Fixed windows newline issue when writing `\r\n`.
- Small fix to OpenCL memory management.
- OpenCL sim now also cleans when cancelled with keyboard interrupt.
- Added a `finally: sim_clean()` to all simulations.
- Various small bugfixes and improvements.

## [1.20.1] - 2015-04-21
- Various bugs fixed in the IDE.

## [1.20.0] - 2015-04-08
- Added 'next' keyword to protocol syntax.

## [1.19.0] - 2015-04-07
- Explorer now shows output in IDE console.
- PSimulation now tracks arbitrary variables dz/dp, no longer only states dy/dp.
- Various small bugfixes.

## [1.18.6] - 2015-03-29
- Various small bugfixes in the GUI.

## [1.18.5] - 2015-03-24
- Even more improvements to the GUI.

## [1.18.4] - 2015-03-23
- Several improvements to the new GUI.

## [1.18.3] - 2015-03-18
- Added new icons for datablock viewer and gde.
- Update to `settings.py` for CUDA.
- Added string highlighting in script editor.
- `JacobianCalculator` bugfix due to Enno.
- Various small bugfixes and improvements.

## [1.18.2] - 2015-03-16
- Removed last traces of previous GUI.
- Fixes to output capturing so that it works on Windows.
- Various small bugfixes.

## [1.18.1] - 2015-03-15
- New IDE seems stable.
- Added monkey patch for `os.popen` issue on windows.

## [1.18.0] - 2015-03-14
- Completely new GUI in QT instead of WX, should solve mac problems, improve performance throughout.
- Integrated GDE with Myokit classes.
- Updated docs for command line tools.
- Dropping idea of supporting `msvc9` compiler on windows. Too many issues.
- Various small bugfixes.

## [1.17.4] - 2015-03-09
- Bugfix in settings.py

## [1.17.3] - 2015-03-09
- GDE is now a part of Myokit.
- Added "monkey patch" for old windows compilers.
- Some changes for C89 compatibility.

## [1.17.1] - 2015-03-05
- SI units named after people are now also accepted when capitalized.
  Never used for output in this fashion.

## [1.17.0] - 2015-03-05
- Now allowing (but not guaranteeing correctness of) arbitrary connections in OpenCL sim.
- Various improvements and bugfixes.

## [1.16.3] - 2015-02-25
- Added `Quantity` class for number-with-unit arithmetic.
- Fix to CellML export of dimensionless variables with a multiplier.
- Various small bugfixes and improvements.

## [1.16.2] - 2015-02-22
- Added current calculating method to Markov model class.
- Added on multi-model experiment convenience classes.

## [1.16.1] - 2015-02-19
- Binds and labels now share a namespace.

## [1.16.0] - 2015-02-19
- Added unit conversion method to unit class.
- Various small bugfixes and improvements.

## [1.15.0] - 2015-02-05
- Various small bugfixes and improvements.

## [1.14.2] - 2015-02-02
- Added NaN check to `PSimulation`.
- Added on model comparison method.
- Nicer output of numbers in expressions and unit quantifiers.
- Tiny fixes in Number representation and GUI.
- Imrpoved video generation script.
- Various small bugfixes and improvements.

## [1.14.1] - 2015-01-25
- Added partial validation to Markov model class.
- Moved `OpenCLInfo` into separate object.
- GUI now shows remaining time during experiment.
- Various small bugfixes and improvements.

## [1.14.0] - 2015-01-16
- Added Alt-1,2,3 tab switching to GUI.
- Updates to `DataLog`.
- Fixed opencl issue: constant memory is limited, using `__constant` for parameter fields can give a strange error (`invalid_kernel_args` instead of out of memory errors). 
  Fixed this by chaning `__constant` to `__global`.
- Various small bugfixes and improvements.

## [1.13.2] - 2014-12-05
- Various improvements and bugfixes.

## [1.13.1] - 2014-12-03
- Fixed a bug with fixed interval logging in CVODE sim.

## [1.13.0] - 2014-11-30
- Checked all load/save methods for `expanduser()` after issues during demo in Ghent.
- Changed `model.var_by_label()` to `model.label()`.
- Added option to show variables dependent on selected var.
- Added support for reading WinWCP files.
- Various improvements and bugfixes.

## [1.12.2] - 2014-11-19
- Added `parse_model()` etc methods to parser.
- Made sure protocol is cloned in all simulations.
  Protocols are not immutable and changes made after setting the protocol should not affect the simulation (or vice versa).
- Added a simulation that calculates the derivative of a state w.r.t. a parameter.
- Working on `MarkovModel` class.
- Added method to convert monodomain parameters to conductances to opencl simulation.
- Various small bugfixes.

## [1.12.1] - 2014-11-08
- Various small bugfixes.

## [1.12.0] - 2014-11-07
- Added `ATF` support.
- Added a Python-based `PacingSystem` to evaluate protocols over time in Python.
- Added `Protocol` to `SimulationLog` conversion.
- Improvements to GUI classes.
- Added protocol preview to GUI.
- Various small bugfixes.

## [1.11.13] - 2014-11-04
- Fixed memory use and halting issue in `lib.fit`.
- Fixed bug in `aux.run()`.
  APDs are now returned in SimulationLogs instead of plain dicts.
  This allows saving as csv and is more consistent with what users would expect the simulation to return.

## [1.11.12] - 2014-11-03
- Bugfix in PSO code: Initial positions weren't set properly, could end up out of bounds.

## [1.11.11] - 2014-10-30
- Made threaded `run()` an option in `settings.py`.

## [1.11.10] - 2014-10-30
- Added quick figure method to `abf`.
- Various small bugfixes.

## [1.11.9] - 2014-10-18
- Added PySilence context manager, made `CSilence` extend it.
- `myokit.run()` now runs the script inside a separate thread.
  This allows `sys.exit()` to be used in a script.
- `myokit.run()` now handles exceptions correctly.
- Various improvements and bugfixes.

## [1.11.8] - 2014-10-17
- Added rectangular grid mapping of parameter spaces.
- Removed custom open dialog from GUI.
- Various improvements and bugfixes.

## [1.11.7] - 2014-10-14
- Added jacobian examples.
- Various improvements and bugfixes.

## [1.11.6] - 2014-10-10
- Added parallelized particle search optimization method (PSO).
- Made linear system solving much faster.
- Looked at using matrix exponentials in markov model code, over 1000 times slower than eigenvalue method!
- Added method to draw colored Voronoi diagram.
- Further annotated the example files.
- Various small bugfixes.

## [1.11.5] - 2014-09-24
- Added note about csv import to `SimulationLog.save_csv`.
- Added publications to website. Uploaded hand-outs for workshop.
- Updated GDE version to 1.3.0.

## [1.11.4] - 2014-09-22
- Added hyperbolic functions to CellML import.
- Updated cellml import: Unused variables without an rhs are now removed, used variables without an rhs are given an automatic rhs of 0. 
  Both cases generate a warning.
- Update to cellml import: If a variable is mentioned but never declared (i.e. if it is an external input) a dummy variable is now created and a warning is  given.
- Added method to `myo` to get version number.
- Fixed string encoding issue in CellML import.
- Tweaks to the gui based on workshop feedback.
- Fixed windows issue: IE likes to download `.cellml` files as `.xml,` making them invisible to the gui. 
  Added a glob rule for `.xml` to the cellml import in the gui.

## [1.11.3] - 2014-09-19
- Moving to next version.
- Small bugfixes and a `variable.value()` method.

## [1.11.2] - 2014-09-18
- Various small bugfixes.

## [1.11.1] - 2014-09-18
- Added a formatting option to the `Benchmarker`.
- Fixed OS/X GUI issues with progress bar.

## [1.11.0] - 2014-09-15
- Adding Sympy to formats list.
- Added sympy exporter and importer.
- Added `LinearModel` class for working with markov models.

## [1.10.3] - 2014-09-11
- Now raising exception when user cancels simulation instead of silent exit.
- Added zero-step detection to cvode sim that now raises a `SimulationError` after too many consecutive zero steps.

## [1.10.2] - 2014-09-10
- Improvement debugging in the GUI: Now shows line numbers of error in script.

## [1.10.1] - 2014-09-08
- Fixed bug in error handling.

## [1.10.0] - 2014-08-30
- Added Windows installer.

## [1.9.11] - 2014-08-29
- Updates to Windows install script.

## [1.9.10] - 2014-08-27
- Added (valid) CellML export.
- Various small bugfixes.

## [1.9.9] - 2014-08-26
- Added update script.

## [1.9.8] - 2014-08-25
- Various improvements and bugfixes.

## [1.9.7] - 2014-08-21
- Fixed bug with dialogs on OS/X.
- Bundled all scripts into a single script `myo`.
- Updated installation script for Windows.

## [1.9.6] - 2014-08-19
- Fixed bug with dialogs on OS/X

## [1.9.5] - 2014-08-14
- Added device info to OpenCL debug output.
- Improved memory handling in OpenCL simulations.
- Various small bugfixes.

## [1.9.4] - 2014-08-13
- Added a script that installs a desktop icon for the gui under Windows.
- Added a global `readme.txt`.
- Various small bugfixes.

## [1.9.3] - 2014-08-08
- Various small bugfixes.

## [1.9.2] - 2014-08-01
- Improved ABF support.
- Various small bugfixes.

## [1.9.1] - 2014-07-31
- Bugfix in GUI for Windows.

## [1.9.0] - 2014-07-31
- Added stable point finding method.
- Added icons for windows version.
- Rebranding as 'Myokit' (with capital M, no more mention of the "Maastricht Myocyte Toolkit").
- Changed license to GPL.

## [1.8.1] - 2014-07-16
- Various improvements and bugfixes.

## [1.8.0] - 2014-07-16
- Updates to website
- Various small bugfixes.

## [1.7.5] - 2014-07-10
- Added method to fold log periodically (based on `split_periodic`).
- Various small bugfixes.

## [1.7.4] - 2014-07-08
- Various small bugfixes.

## [1.7.3] - 2014-07-07
- Reinstated logging of derivatives in CVODE simulation.
- Various small bugfixes.

## [1.7.2] - 2014-07-07
- Various small bugfixes.

## [1.7.1] - 2014-07-07
- Added load/save methods to DataBlock1d.
- Made ICSimulation work with DataBlock2d to calculate eigenvalues.
- Various small bugfixes.

## [1.7.0] - 2014-07-04
- Added a JacobianGenerator class.
- Added a simulation that integrates partial derivatives to find the derivatives of the state w.r.t. the initial conditions.
- Added latex export.
- Various small bugfixes.

## [1.6.2] - 2014-06-18
- Various small bugfixes.

## [1.6.1] - 2014-06-13
- Added IV curve experiment.
- Improved error detection in CVODE simulation.

## [1.6.0] - 2014-06-06
- Added a diffusion on/off switch to the OpenCL simulation.
- The OpenCL sim can now replace constants by scalar fields.
  This allows it to be used to test parameter influence or to simulate heterogeneity.

## [1.5.2] - 2014-06-04
- Better handling of unknown units.
- Added `eval_state_derivs` option to GUI.
- Added trim trailing whitespace method to gui.
- Gui and step script now show numerical errors if they occur.
- Added `trim()` and `itrim()` methods to simulation log.
- Added a 2-variable parameter range exploration class.
- DataBlock viewer now can export frames and graphs.
- Various improvements and bugfixes.

## [1.5.1] - 2014-05-08
- Added method `Model.set_name()`.
- Updated installer script for GNOME/KDE.
- Various small bugfixes.

## [1.5.0] - 2014-04-24
- Added on Strength-Duration experiment.
- Added method to create cumulative current/charge plots.

## [1.4.8] - 2014-04-22
- Changed `SimulationLog.integrate()` to use left-point rule instead of midpoint rule.
  This makes much more sense for the stimulus current when using CVODE.
- Various improvements and bugfixes.

## [1.4.7] - 2014-04-17
- Various small bugfixes.

## [1.4.6] - 2014-04-10
- Added RestitutionExperiment to `lib.common`.
- Various small bugfixes.

## [1.4.5] - 2014-04-07
- Re-organised code.
- Various small bugfixes.

## [1.4.4] - 2014-03-27
- Various improvements and bugfixes.

## [1.4.3] - 2014-03-17
- Various small bugfixes.

## [1.4.2] - 2014-03-11
- Added unit methods to IDE.
- Updated the installation guide.
- Added method to 'walk' over the operands in an expression, depth-first.
- Added a few default unit representations
- Various small bugfixes.

## [1.4.0] - 2014-02-18
- Added unit checking methods.
- Improved CellML unit reading from constants.
- Added `pack_snapshot()` method that creates a copy of the current Myokit version.
- Created `DataBlock` classes for alternative view of rectangular simulation data.
- Added GUI for viewing 1D and 2D simulation data.
- Various small bugfixes.

## [1.2.0] - 2014-01-27
- Changed `[[plot]]` to `[[script]]`.
- Various improvements and bugfixes.

## [1.1.0] - 2014-01-24
- Updated interface of opencl simulations.
- Added OpenCL-based parameter RangeTester class.
- Various small bugfixes.

## [1.0.2] - 2014-01-09
- Updates to documentation.

## [1.0.0] - 2013-12-24
- Improved documentation.
- Added a 'running simulations' guide.
- Added SymPy export.
- Added unit tests.
- Added binary format for simulation logs.
- Aliases are now retained in model export.
- Various small bugfixes.

## [0.17.2] - 2013-12-19
- Improved documentation.
- Various small bugfixes.

## [0.17.1] - 2013-12-19
- New model syntax, model stars with: `[[model]]`.
- Various small bugfixes.

## [0.17.0] - 2013-12-11
- Added binary version of `save_state` and `load_state`.
- Added ProgressPrinter to show progress during long simulations.
- Added precision switch to `prepare_log` and `load_csv`.
- Added method to find solvable equations dependent on one or more variables.
- Improved support for ABF protocol and data reading.
- Various small bugfixes.

## [0.16.3] - 2013-11-06
- Improved OpenCL simulation error output.
- Various improvements and bugfixes.

## [0.16.2] - 2013-11-01
- Improvements to GUI.
- Improved `find_nan` method in OpenCL sim.
- Added method to expression's `eval()` to evaluate with numpy.Float32 objects.
  This helps finding the source of OpenCL single-precision NaN errors.
- Various small bugfixes.

## [0.16.1] - 2013-10-31
- Refactored code, reduced size of giant modules.
- Various small bugfixes.

## [0.16.0] - 2013-10-31
- Added recovery-from-inactivation experiment.
- Updated `ActivationExperiment`, added boltzmann fit.
- Added boltzmann fit to `InactivationExperiment`.
- Added time constant of activation method to `ActivationExperiment`.
- Rewrote unit system.
- Various improvements and bugfixes.

## [0.15.9] - 2013-10-22
- Various small bugfixes.

## [0.15.8] - 2013-10-16
- Slight optimizations in OpenCL code.
- Various small bugfixes.

## [0.15.7] - 2013-10-15
- Various small bugfixes.

## [0.15.6] - 2013-10-15
- Updated step method to accept models as reference.
- Reinstated `Model.load_state()` method.
- Imrpoved find dialog.
- Various small bugfixes.

## [0.15.5] - 2013-10-14
- Added quick var info to gui.
- Renamed `current_diff` to `diffusion_current`.

## [0.15.4] - 2013-10-12
- Added on ChanneML import.
- FiberTissueSimulation now works with 2D fibers.

## [0.15.2] - 2013-10-10
- Added data extraction features to abf format.
- Added on Fiber-Tissue simulation class.
- Various improvements and bugfixes.

## [0.15.0] - 2013-09-18
- Number of cells to pace can now be set in `OpenCLCableSimulation`.
- Added function to find origin of NaN errors in an `OpenCLCableSimulation`.
- Updated SimulationLog to return mesh grid for pyplot.
- Added 1D CV calculation to `SimulationLog`.
- Renamed cable simulation classes.
- Made 1D OpenCL Simulation suitable for 2D use.
- Added method to list component cycles.
- Added a method that checks which variables cause mutually dependent components.
- Various small bugfixes.

## [0.14.1] - 2013-08-23
- Fixed direction convention for diffusion current.
- Simulation log now has local and global variables (for multi-cell simulations).
- Added OpenCL export.
- Added a C header file with pacing functions, shared by several simulations.
- Added a settings file `settings.py`.
- Added OpenCL simulation object.
- Various small bugfixes.

## [0.14.0] - 2013-07-19
- Various performance boosts.
- Rewrite of expression classes.
- Improved parser.
- Added options to move variables, delete variables.
- Improved `Model.clone()` method.
- Added strand simulations via Python interface.
- Various improvements and bugfixes.

## [0.13.9] - 2013-06-06
- Working CUDA kernel export.

## [0.13.8] - 2013-06-06
- Various small bugfixes.

## [0.13.7] - 2013-06-06
- Added simple Ansi-C forward euler export.
- Various small bugfixes.

## [0.13.6] - 2013-05-31
- Added progress bars to explorer in gui (F6).
- Worked on dependency graphs.
- Added meta data to components.
- Added option to `SimulationLog` to split into periodic pieces.
- Various improvements and bugfixes.

## [0.13.5] - 2013-05-23
- Various improvements and bugfixes.

## [0.13.4] - 2013-05-23
- Made `engine.realtime` contain the elapsed system time, not the absolute system time.
- Made `SimulationLog` suitable for multi-dimensional data.
- Added `StrandSimulation` object.
- Added Graph Data Extractor.
- Added `RhsBenchmarker`.
- Began work on CUDA export.
- Added Coffman-Graham algorithm for directed acyclic graph layer assignment.
- Added `get_last_number_of_evaluations()` method to `Simulation`.
- Various updates to the documentation.
- Various small bugfixes.

## [0.13.0] - 2013-03-28
- Added export to strand/fiber simulation in Ansi-C.
- Added syntax for binding to external values.
- Various small bugfixes.

## [0.12.7] - 2013-02-27
- Added plotting methods.
- Added benchmarking to simulation.
- Various improvements and bugfixes.

## [0.12.6] - 2013-02-26
- Refactored `myokit.lib`.
- Added APD calculating function.
- Added APD measurement to simulation using CVode's root finding.
- Added padding function to `save_csv`.
- Created `SimulationLog` class.
- Various small bugfixes.

## [0.12.4] - 2013-02-20
- Refactored import/export modules.
- Updated documentation.
- Added method to interpolate logged results.
- Improved performance in CVODE simulations.
- Added periodic logging option to simulation.
- Improved Explorer GUI.
- Added method to run euler/rk4 simulations.
- Added OrderedPiecewise class.
- Added progress bar to gui.
- Various small bugfixes.

## [0.10.8] - 2013-01-15
- Bugfix in metadata export.

## [0.10.7] - 2013-01-15
- Various improvements and bugfixes.

## [0.10.6] - 2013-01-15
- Rewrote cellml import.
- Worked on methods to fit simplify functions.
- Updates to `mmt` syntax
- Added multi-line comments to `mmt` syntax.
- Various small bugfixes.

## [0.10.5] - 2012-11-12
- Added tests.
- Added `piecewise()` expressions.
- Various improvements and bugfixes.

## [0.10.3] - 2012-10-30
- Improved import and export interfaces.
- Added `save_state()` method.
- Improved documentation
- Conversion of Myokit expressions to Python functions.
- Added benchmarking methods.
- Implemented unit parsing.
- Added SBML import.
- Added methods for function simplification (via approximations).
- Introduced website.
- Various small bugfixes.

## [0.9.17] - 2012-07-27
- Added local aliases to syntax.
- Simplified syntax.
- Simulation and gui now allow unlogged pacing.
- Added search function to GUI.
- Templating based exports, available from GUI.
- Import of CellML metadata.
- Added protocol wizard to GUI.
- Added simple component dependency graph to GUI.
- Added model debug options.
- Added matlab export.
- Introduced three-section `mmt` file.
- ABF protocol import.
- Added Sphinx-based documentation.
- Added routine that shows sizes of integrator steps.
- Various small bugfixes.

## [0.9.0] - 2012-03-12
- First `mmt` syntax, parser and model classes.
- Initial CellML import.
- C++ export.
- Ansi-C export, python export.
- Beat script that uses generated Ansi-C and CVODE, compiled on the fly.
- First working GUI.

## [0.0.0] - 2011-12-19
- Working on simple model syntax, parser and export to C++.

