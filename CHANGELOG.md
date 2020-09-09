# Changelog
                
This page lists the main changes made to Myokit in each release.

## Unreleased
Unreleased

### Added
### Changed
### Deprecated
### Removed
### Fixed


## Version 1.31.0
Released Wed Aug 26 15:23:38 2020.

- A completely rewritten SBML API and parser, by @DavAug, that's capable of handling models that define species and reactions.
- `Ohm` is now a quantifiable unit in the `mmt` syntax, i.e. `1 [MOhm]`. 
  This replaces the non-standard `R` unit which has been removed.
- Unit tests are now included in the PyPI package.
- A recently introduced bug in the `HHSimulation`'s `steady_state()` method was fixed.
- Sympy is no longer a required dependency (but still an optional one).
- Models, protocols, and CVODE simulations can now be pickled, and tests have been added that check that simulations can be run in parallel (even on Windows). 
  To further aid in this, simulations now include a time and process number dependent hash in their generated-module names.
- Non-integer exponents are now allowed in the unit system, which compares units with a `close()` method that expects a certain numerical tolerance, instead of using exact comparison.
- The `myokit.mxml` module has been removed.
- The cumulative-current plot now has a maximum-number-of-currents option (all further currents will be bundled into one).
- Model and protocol now support comparison with `==`.
- Imports and exports now raise warnings instead of using the Myokit textlogger for this.
- The CellML export now ensures there are no spaces in initial value or unit multiplier attributes.
- CellML imports treat new base units as dimensionless.
- CellML imports now import models that contain unsupported units (but with warnings).
- CellML imports now import models with non-integer unit exponents.
- The method `show_evalution_of` now has consistently ordered output.
- The output of the `step()` method has been improved, and the method now only warns about relative differences bigger than 1 epsilon.
- Some slight changes to simulation building: Now uses `--inplace` instead of `--old-and-unmanageable` and should delete any temporary files created in the process.
- The IDE now checks the protocol even if the model is invalid or unchanged.
- Bugfix for simulations that ended at a time numerically indistinguishable from an event time.
- Bugfixes and fewer warnings for various matplotlib versions.
- Bugfix to `lib.common.StrenghtDuration`.


## Version 1.30.6
Released Wed Apr 29 11:26:16 2020.

- Fixed bug where GUI CellML export didn't export stimulus current.


## Version 1.30.5
Released Mon Apr 20 12:51:58 2020.

- Added support for CellML 2.0.
- Rewrote SBML import to use etree instead of DOM.
- Removed `parse_mathml_dom` function.
- Removed mxml `dom_child` and `dom_next` methods.
- Now setting OpenCL framework as linker flag on osx.


## Version 1.30.4
Released Fri Mar 27 12:13:35 2020.

- Fixed a bug with running simulations in Spyder on Windows.
- Added `clone()` and `__repr__()` methods to myokit.Equation.
- Some fixes and tweaks to CellML 1.0/1.1 API.


## Version 1.30.3
Released Mon Mar 2 11:03:38 2020.

- Small fixes to CellML validation.
- Fixed typo in units `becquerel`.
- Added `notanumber` and `infinity` to MathML parser.


## Version 1.30.2
Released Sat Feb 1 19:43:40 2020.

- Removed `myo` script.
- Fixed EasyML issue for inf/tau variables used by more than one state.


## Version 1.30.1
Released Fri Jan 3 16:31:40 2020.

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


## Version 1.30.0
Released Mon Dec 30 12:08:56 2019.

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


## Version 1.29.1
Released Sun Nov 24 12:48:54 2019.

- Added guessing module, with method to guess which variables (if any) represent the membrane potential and stimulus current.
- Fix for sundials development versions.
- Fixes for PySide2 support.


## Version 1.29.0
Released Fri Oct 11 16:21:01 2019.

- Myokit is now released under a BSD 3-clause license
- Bugfix to `myokit step` command line tool.


## Version 1.28.9
Released Wed Sep 11 23:18:57 2019.

- Added PySide2 support.
- Deprecated PyQt4 and PySide.
- Added a method `Model.remove_derivative_references()`.
- Bugfix to `Model.repr()` for models with no name.
- Added `Model.timex()`, `labelx()` and `bindingx()`, which work like `time()`, `label()` and `binding()` but raise an exception if no appropriate variable is found.
- Deprecated `lib.multi.time()`, `label()`, and `binding()`.


## Version 1.28.8
Released Tue Sep 3 18:09:01 2019.

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


## Version 1.28.7
Released Sat Aug 3 02:53:59 2019.

- Added option to register external formats.
- Added option to avoid certain prefixes when generating unique variable names.
- `Model.expressions_for()` now accepts more than 1 argument, and handles dependencies on derivatives correctly.
- Removed deprecated method `Model.solvable_subset()`.


## Version 1.28.6
Released Fri Jul 26 14:20:17 2019.

- Added debug option to `myokit compiler` command.


## Version 1.28.5
Released Tue Jul 16 11:17:07 2019.

- Bugfix: Removing variables now also removes their bindings and labels.
- Added unit tests.
- Improved performance in `lib.markov` analytical simulations.
- Updated the `myo` script to use the python3 executable.
- Fixed a bug in the default script used when creating or importing a model.
- Made GNOME/KDE icons install using sys.executable instead of a hardcoded python command.
- Fixed handling of string encoding in cellml import.


## Version 1.28.4
Released Tue May 28 21:47:10 2019.

- Myokit is now tested on Python 3.7, but no longer on 3.4.
- Updated default OpenCL paths for windows.
- GUI fixes for matplotlib 3.1.0+.
- Added `set_constant()` method to markov simulations.
- Added `log_times` option to `lib.markov.AnalyticalSimulation`, and started pre-allocating arrays.
- Added option to cumulative current plot to normalise currents.


## Version 1.28.3
Released Thu May 2 12:41:15 2019.

- Fixed some floating point issues with protocols and pacing.
- Updated OpenCL code to work with VS 9.
- Some small changes to the Protocol API.
- Added format protocol option to IDE.


## Version 1.28.2
Released Wed Dec 19 19:43:19 2018.

- Improved support for native OpenCL on OS/X.
- Native maths in OpenCL simulations is now configurable and disabled by default.


## Version 1.28.1
Released Wed Dec 19 00:50:04 2018.

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


## Version 1.28.0
Released Thu Nov 22 22:49:55 2018.

- Added `myokit.lib.hh` module for recognising Hodgkin-Huxley style ion current models and using them in fast analytical simulations.
- Added Rush-Larsen (RL) option to OpenCLSimulation.
- Added CUDA kernel export with RL updates.
- Added `OpenCLRLExporter` for OpenCL kernel with Rush-Larsen.
- Improved logging of intermediary variables in OpenCL simulations.
- Improved logging in `Simulation1d`.
- Fix to ABF reader for (unsupported) userlists (abf v2).
- Fixes to Sundials configuration on Windows.
- Small bugfixes, documentation updates, etc.


## Version 1.27.7
Released Thu Nov 1 00:19:10 2018.

- Various fixes to make Myokit work with Python 2.7.6 (and later).


## Version 1.27.6
Released Thu Sep 27 15:24:51 2018.

- Now running sundials auto-detection with every `import myokit` if not set in config file.


## Version 1.27.5
Released Thu Sep 20 12:18:33 2018.

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


## Version 1.27.4
Released Sun Aug 12 22:34:40 2018.

- Added sundials version detection on first run.
- Moved myokit config files from `~/.myokit` to `~/.config/myokit`.
- Renamed `NumpyExpressionwriter` to `NumPyExpressionWriter`.
- Fixed test issues on os/x.


## Version 1.27.3
Released Mon Aug 6 13:53:38 2018.

- Updated the way sundials library locations are stored on windows systems.


## Version 1.27.2
Released Sat Aug 4 18:02:15 2018.

- Added script that creates icons for windows.
- Updated script that creates icons for linux.


## Version 1.27.1
Released Fri Aug 3 18:00:00 2018.

- Placeholder release to fix Pypi issue.


## Version 1.27.0
Released Fri Aug 3 13:51:05 2018.

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


## Version 1.26.3
Released Fri Feb 9 19:24:21 2018.

- Fixed critical bug introduced in version 1.26.2 that stopped Windows simulations from running.


## Version 1.26.2
Released Thu Jan 11 23:49:06 2018.

- Fixed a small bug in `Simulation`'s logging when using the new `log_times` argument.
- Added Matlab and text file tab to DataLog viewer.
- Removed ancient restriction on components not being called `external`.
- Refactored code to pass flake8 tests.
- Added `len()` method to Protocol.
- Now setting `runtime_libraries` parameter for all compiled classes (simulations), removing the need to set `LD_LIBRARY_PATH` on some systems.


## Version 1.26.1
Released Fri Nov 24 15:13:19 2017.

- Updated licensing info.


## Version 1.26.0
Released Fri Nov 24 12:22:57 2017.

- Myokit can now be installed as library using `python setup.py develop`.
- Fixed a bug in the gnome scripts that install icons.
- The `DataLog` `trim`, `itrim` and `extend` methods now return copies, instead of modifying the data 'in place'. 
  This makes the `DataLog`'s methods more consistent, and prevents accidental data loss.
  However, this change makes Myokit 1.26.0 slightly backwards incompatible.
- Added a `DataLog.keys_like` method to iterate over 1d or 2d logs.


## Version 1.25.3
Released Fri Oct 6 20:41:10 2017.

- Small tweaks to IDE
- Fix to `DataLog.fold()` to discard remainder if period doesn't exactly divide the log length.
- Various bugfixes.
- Improved cvode error catching.
- More control over `lib.fit` verbosity
- Added random starting point option to lib.fit methods.
- Added the option to explicitly specify log points in the single-cell `Simulation` class.
- CVODE sim now raises `SimulationError` if maximum number of repeated zero-steps is made, instead of plain `Exception`.
- Fix `fit.cmaes` to work with cma version 2.x


## Version 1.25.2
Released Thu Aug 3 22:24:31 2017.

- Small tweaks to IDE.
- Fixed bug with saving the time variable in `DataLog.save_csv()`.


## Version 1.25.1
Released Tue Jul 18 12:27:55 2017.

- Added xNES and SNES optimisation methods.
- Added interface to CMA-ES optimisation method.
- Replaced the 'tolerance' arguments `in myokit.lib.fit` with more accurate counterparts.
- Removed `ga()` optimisation method.


## Version 1.25.0
Released Mon Jul 10 12:23:52 2017.

- Added model export to Stan.
- Added data-clamp to CVODE simulation (works, but generally a bad idea).
- Added Protocol.add_step convenience method for building sequential step protocols.
- Added `log()` method to `ExportError`.
- Fixed bug in ABF reading (ABF channel index can be greater than number of channels in file).
- Small fixes to `DataLogViewer`.
- Fixed issue with PySide file open/save dialogs.
- Several small fixes to docs.


## Version 1.24.4
Released Thu May 4 15:25:38 2017.

- Bugfix in PyQt4 support.


## Version 1.24.3
Released Wed May 3 22:48:21 2017.

- Fixed PyQt4/5 and PySide compatibility issue that was causing errors in the DataBlock viewer's open function.


## Version 1.24.2
Released Tue Mar 28 11:10:53 2017.

- Added missing #pragma directive to enable double-precision simulations OpenCL.


## Version 1.24.1
Released Mon Oct 24 16:57:01 2016.

- Added support for PyQt5.


## Version 1.24.0
Released Fri Oct 14 11:13:26 2016.

- The IDE now has a model navigator, that displays the model components alphabetically and lets you navigate large models more easily.
- Fixed a bug in the implementation of `DataBlock1d.grid()`, and updated its documentation: this method returns coordinates for squares where each square represents a data point.
  See the [Stewart 2009 OpenCL example](http://myokit.org/examples/#stewart-2009) for an example of its use.
- Added a second method `DataBlock1d.image_grid()` that returns coordinates for points where each point in space represents a data point.
- Fixed bug with Ctrl+Shift+Home in IDE.
- Various small bugfixes in IDE.
- Updated installation instructions on website.


## Version 1.23.4
Released Sun Sep 4 13:01:03 2016.

- Fixed bug (with new numpy) in `DataLog.split_periodic`.
- Fixed warnings in GDE.
- Fixed issue with pyside/pyqt difference.


## Version 1.23.3
Released Thu Jul 21 17:25:52 2016.

- Updated documentation and examples.
- Added extra callback option to pso for detailed feedback.
- Updated default search paths for Sundials headers and libraries.


## Version 1.23.2
Released Thu Jun 16 00:01:04 2016.

- Small bugfix to IDE.
- Added `pre()` method to Markov simulations (`AnalyticalSimulation` and `DiscreteSimulation`).
- Fixed a bug in `lib.markov.AnalyticalSimulation.run` when `log_interval >= duration`.
- IDE now shows exact location of recent files in status bar.
- Fixed bug in `SymPyExpressionWriter.eq()` and renamed classes to use SymPy with capital P.


## Version 1.23.1
Released Sun Jun 5 22:38:15 2016.

- Updated documentation.
- Fixed opencl issue.


## Version 1.23.0
Released Mon May 30 17:13:52 2016.

- Added methods for easier symbolic addition of names/components for situations where exact names aren't important.
- Bugfix to datalog viewer.
- Bugfix to vargrapher.


## Version 1.22.7
Released Wed May 25 23:02:44 2016.

- Update to ide: Can now add/remove comments.
- Bugfixes to protocol reading in `AbfFile`.
- Bugfix in `AbfFile` string reading.
- DataLog viewer now opens multiple files if specified on the command line.
- Fix to OpenCL sim reserved names list.
- Various tweaks and fixes.


## Version 1.22.6
Released Fri Mar 11 16:07:23 2016.

- Fixed bug in IDE.
- Fix to windows start menu icons.


## Version 1.22.5
Released Thu Feb 25 18:14:43 2016.

- Updated online examples.
- Bugfix in deprecated method `Protocol.guess_duration()`.


## Version 1.22.4
Released Wed Feb 24 12:40:16 2016.

- Fixed bug with auto-indenting and smart up/down arrows in IDE.
- Fixed bug in parsing of indented multi-line meta-data properties.
- Fixed bug with `[[script]]` sections being added to files when saved.
- Slight update to `DataLog.apd()`.
- Updated the docs of both apd methods to make clear that they use fixed thresholds.


## Version 1.22.3
Released Fri Feb 19 16:02:51 2016.

- Added hybrid PSO option to `myokit.lib.fit`.
- Added option to return multiple particles' results to PSO.
- Bugfixes and updates to documentation.
- Added BFGS method (interface to scipy) to `myokit.lib.fit`.


## Version 1.22.2
Released Mon Feb 8 21:11:59 2016.

- Small bugfix in markov simulation class.


## Version 1.22.1
Released Mon Feb 8 15:51:42 2016.

- Updates to source highlighting in the IDE.
- Various small bugfixes.
- Protocols and events now define a 'characteristic time'.
- The protocol class is now slightly stricter than before, removed its `validate()` method.
- Both markov model simulation classes can now run simulations based on `myokit.Protocol` objects.


## Version 1.22.0
Released Thu Jan 28 20:16:15 2016.

- Rewrote the Markov model module.
- Added a method to perform stochastic simulations with Markov models.
- Various small bugfixes.


## Version 1.21.12
Released Wed Jan 20 00:36:14 2016.

- The CellML export now includes a simple periodic pacing protocol.
- Various small bugfixes.


## Version 1.21.11
Released Tue Jan 5 00:33:47 2016.

- Tidied up code.


## Version 1.21.10
Released Mon Jan 4 22:53:56 2016.

- Various small bugfixes.


## Version 1.21.9
Released Mon Dec 28 13:15:45 2015.

- Various small bugfixes.


## Version 1.21.8
Released Thu Nov 5 14:21:49 2015.

- Removed option to run `mmt` files in threads (was not used and caused issues with GUI).
- Giving up on multiprocessing on windows. Adding switches to disable it in the examples.
- Various bugfixes and improvements.


## Version 1.21.7
Released Tue Oct 27 12:11:18 2015.

- Improved logging in simulations, made it more consistent throughout Myokit.


## Version 1.21.6
Released Fri Oct 23 12:13:32 2015.

- Various small bugfixes, improvements and website updates.


## Version 1.21.5
Released Wed Oct 14 14:31:28 2015.

- Changed the way states are stored in the model (list instead of OrderedDict). Was causing funny bug. Now has less redundant info.
- Fixed bug in `remove_component()`.


## Version 1.21.4
Released Tue Oct 6 17:22:08 2015.

- Added debug options to openclsim.
- OpenCL sim can now pace based on rules again, which is far more efficient for large numbers of cells.


## Version 1.21.3
Released Tue Oct 6 09:44:02 2015.

- Various bugfixes.


## Version 1.21.2
Released Mon Oct 5 22:16:48 2015.

- Added OpenCL device selection.
- Updated cumulative current plot method.


## Version 1.21.1
Released Sat Sep 12 20:55:48 2015.

- Various small bugfixes and improvements.


## Version 1.21.0
Released Fri Sep 4 00:55:24 2015.

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


## Version 1.20.5
Released Mon Jun 1 16:21:41 2015.

- Added Python version check.
- Fitting library: Adding quadratic polynomial fit used to test local optima.
- Various small bugfixes.


## Version 1.20.4
Released Mon May 11 14:52:12 2015.

- Improved export of units to CellML.
- `DataLogViewer` can now open CSV.
- Fixed windows newline issue when writing `\r\n`.
- Small fix to OpenCL memory management.
- OpenCL sim now also cleans when cancelled with keyboard interrupt.
- Added a `finally: sim_clean()` to all simulations.
- Various small bugfixes and improvements.


## Version 1.20.1
Released Tue Apr 21 16:15:03 2015.

- Various bugs fixed in the IDE.


## Version 1.20.0
Released Wed Apr 8 15:57:41 2015.

- Added 'next' keyword to protocol syntax.


## Version 1.19.0
Released Tue Apr 7 01:51:31 2015.

- Explorer now shows output in IDE console.
- PSimulation now tracks arbitrary variables dz/dp, no longer only states dy/dp.
- Various small bugfixes.


## Version 1.18.6
Released Sun Mar 29 15:57:38 2015.

- Various small bugfixes in the GUI.


## Version 1.18.5
Released Tue Mar 24 15:46:01 2015.

- Even more improvements to the GUI.


## Version 1.18.4
Released Mon Mar 23 13:05:39 2015.

- Several improvements to the new GUI.


## Version 1.18.3
Released Wed Mar 18 13:01:02 2015.

- Added new icons for datablock viewer and gde.
- Update to `settings.py` for CUDA.
- Added string highlighting in script editor.
- `JacobianCalculator` bugfix due to Enno.
- Various small bugfixes and improvements.


## Version 1.18.2
Released Mon Mar 16 11:50:41 2015.

- Removed last traces of previous GUI.
- Fixes to output capturing so that it works on Windows.
- Various small bugfixes.


## Version 1.18.1
Released Sun Mar 15 11:44:36 2015.

- New IDE seems stable.
- Added monkey patch for `os.popen` issue on windows.


## Version 1.18.0
Released Sat Mar 14 02:23:33 2015.

- Completely new GUI in QT instead of WX, should solve mac problems, improve performance throughout.
- Integrated GDE with Myokit classes.
- Updated docs for command line tools.
- Dropping idea of supporting `msvc9` compiler on windows. Too many issues.
- Various small bugfixes.


## Version 1.17.4
Released Mon Mar 9 15:26:30 2015.

- Bugfix in settings.py


## Version 1.17.3
Released Mon Mar 9 15:16:15 2015.

- GDE is now a part of Myokit.
- Added "monkey patch" for old windows compilers.
- Some changes for C89 compatibility.


## Version 1.17.1
Released Thu Mar 5 23:00:33 2015.

- SI units named after people are now also accepted when capitalized.
  Never used for output in this fashion.


## Version 1.17.0
Released Thu Mar 5 18:35:19 2015.

- Now allowing (but not guaranteeing correctness of) arbitrary connections in OpenCL sim.
- Various improvements and bugfixes.


## Version 1.16.3
Released Wed Feb 25 17:43:48 2015.

- Added `Quantity` class for number-with-unit arithmetic.
- Fix to CellML export of dimensionless variables with a multiplier.
- Various small bugfixes and improvements.


## Version 1.16.2
Released Sun Feb 22 20:47:28 2015.

- Added current calculating method to Markov model class.
- Added on multi-model experiment convenience classes.


## Version 1.16.1
Released Thu Feb 19 18:48:08 2015.

- Binds and labels now share a namespace.


## Version 1.16.0
Released Thu Feb 19 18:11:48 2015.

- Added unit conversion method to unit class.
- Various small bugfixes and improvements.


## Version 1.15.0
Released Thu Feb 5 21:33:58 2015.

- Various small bugfixes and improvements.


## Version 1.14.2
Released Mon Feb 2 13:19:20 2015.

- Added NaN check to `PSimulation`.
- Added on model comparison method.
- Nicer output of numbers in expressions and unit quantifiers.
- Tiny fixes in Number representation and GUI.
- Imrpoved video generation script.
- Various small bugfixes and improvements.


## Version 1.14.1
Released Sun Jan 25 23:18:57 2015.

- Added partial validation to Markov model class.
- Moved `OpenCLInfo` into separate object.
- GUI now shows remaining time during experiment.
- Various small bugfixes and improvements.


## Version 1.14.0
Released Fri Jan 16 15:25:38 2015.

- Added Alt-1,2,3 tab switching to GUI.
- Updates to `DataLog`.
- Fixed opencl issue: constant memory is limited, using `__constant` for parameter fields can give a strange error (`invalid_kernel_args` instead of out of memory errors). 
  Fixed this by chaning `__constant` to `__global`.
- Various small bugfixes and improvements.


## Version 1.13.2
Released Fri Dec 5 17:58:47 2014.

- Various improvements and bugfixes.


## Version 1.13.1
Released Wed Dec 3 12:03:22 2014.

- Fixed a bug with fixed interval logging in CVODE sim.


## Version 1.13.0
Released Sun Nov 30 14:59:20 2014.

- Checked all load/save methods for `expanduser()` after issues during demo in Ghent.
- Changed `model.var_by_label()` to `model.label()`.
- Added option to show variables dependent on selected var.
- Added support for reading WinWCP files.
- Various improvements and bugfixes.


## Version 1.12.2
Released Wed Nov 19 09:04:00 2014.

- Added `parse_model()` etc methods to parser.
- Made sure protocol is cloned in all simulations.
  Protocols are not immutable and changes made after setting the protocol should not affect the simulation (or vice versa).
- Added a simulation that calculates the derivative of a state w.r.t. a parameter.
- Working on `MarkovModel` class.
- Added method to convert monodomain parameters to conductances to opencl simulation.
- Various small bugfixes.


## Version 1.12.1
Released Sat Nov 8 12:59:03 2014.

- Various small bugfixes.


## Version 1.12.0
Released Fri Nov 7 18:21:21 2014.

- Added `ATF` support.
- Added a Python-based `PacingSystem` to evaluate protocols over time in Python.
- Added `Protocol` to `SimulationLog` conversion.
- Improvements to GUI classes.
- Added protocol preview to GUI.
- Various small bugfixes.


## Version 1.11.13
Released Tue Nov 4 17:15:59 2014.

- Fixed memory use and halting issue in `lib.fit`.
- Fixed bug in `aux.run()`.
  APDs are now returned in SimulationLogs instead of plain dicts.
  This allows saving as csv and is more consistent with what users would expect the simulation to return.


## Version 1.11.12
Released Mon Nov 3 13:20:48 2014.

- Bugfix in PSO code: Initial positions weren't set properly, could end up out of bounds.


## Version 1.11.11
Released Thu Oct 30 16:53:53 2014.

- Made threaded `run()` an option in `settings.py`.


## Version 1.11.10
Released Thu Oct 30 14:36:32 2014.

- Added quick figure method to `abf`.
- Various small bugfixes.


## Version 1.11.9
Released Sat Oct 18 14:57:55 2014.

- Added PySilence context manager, made `CSilence` extend it.
- `myokit.run()` now runs the script inside a separate thread.
  This allows `sys.exit()` to be used in a script.
- `myokit.run()` now handles exceptions correctly.
- Various improvements and bugfixes.


## Version 1.11.8
Released Fri Oct 17 13:00:04 2014.

- Added rectangular grid mapping of parameter spaces.
- Removed custom open dialog from GUI.
- Various improvements and bugfixes.


## Version 1.11.7
Released Tue Oct 14 16:00:18 2014.

- Added jacobian examples.
- Various improvements and bugfixes.


## Version 1.11.6
Released Fri Oct 10 18:38:28 2014.

- Added parallelized particle search optimization method (PSO).
- Made linear system solving much faster.
- Looked at using matrix exponentials in markov model code, over 1000 times slower than eigenvalue method!
- Added method to draw colored Voronoi diagram.
- Further annotated the example files.
- Various small bugfixes.


## Version 1.11.5
Released Wed Sep 24 15:52:50 2014.

- Added note about csv import to `SimulationLog.save_csv`.
- Added publications to website. Uploaded hand-outs for workshop.
- Updated GDE version to 1.3.0.


## Version 1.11.4
Released Mon Sep 22 22:03:55 2014.

- Added hyperbolic functions to CellML import.
- Updated cellml import: Unused variables without an rhs are now removed, used variables without an rhs are given an automatic rhs of 0. 
  Both cases generate a warning.
- Update to cellml import: If a variable is mentioned but never declared (i.e. if it is an external input) a dummy variable is now created and a warning is  given.
- Added method to `myo` to get version number.
- Fixed string encoding issue in CellML import.
- Tweaks to the gui based on workshop feedback.
- Fixed windows issue: IE likes to download `.cellml` files as `.xml,` making them invisible to the gui. 
  Added a glob rule for `.xml` to the cellml import in the gui.


## Version 1.11.3
Released Fri Sep 19 12:50:35 2014.

- Moving to next version.
- Small bugfixes and a `variable.value()` method.


## Version 1.11.2
Released Thu Sep 18 02:37:34 2014.

- Various small bugfixes.


## Version 1.11.1
Released Thu Sep 18 02:10:28 2014.

- Added a formatting option to the `Benchmarker`.
- Fixed OS/X GUI issues with progress bar.


## Version 1.11.0
Released Mon Sep 15 19:50:09 2014.

- Adding Sympy to formats list.
- Added sympy exporter and importer.
- Added `LinearModel` class for working with markov models.


## Version 1.10.3
Released Thu Sep 11 17:17:33 2014.

- Now raising exception when user cancels simulation instead of silent exit.
- Added zero-step detection to cvode sim that now raises a `SimulationError` after too many consecutive zero steps.


## Version 1.10.2
Released Wed Sep 10 05:13:29 2014.

- Improvement debugging in the GUI: Now shows line numbers of error in script.


## Version 1.10.1
Released Mon Sep 8 18:55:43 2014.

- Fixed bug in error handling.


## Version 1.10.0
Released Sat Aug 30 01:33:52 2014.

- Added Windows installer.


## Version 1.9.11
Released Fri Aug 29 14:21:37 2014.

- Updates to Windows install script.


## Version 1.9.10
Released Wed Aug 27 01:23:41 2014.

- Added (valid) CellML export.
- Various small bugfixes.


## Version 1.9.9
Released Tue Aug 26 00:54:45 2014.

- Added update script.


## Version 1.9.8
Released Mon Aug 25 01:35:05 2014.

- Various improvements and bugfixes.


## Version 1.9.7
Released Thu Aug 21 12:59:45 2014.

- Fixed bug with dialogs on OS/X.
- Bundled all scripts into a single script `myo`.
- Updated installation script for Windows.


## Version 1.9.6
Released Tue Aug 19 13:51:14 2014.

- Fixed bug with dialogs on OS/X


## Version 1.9.5
Released Thu Aug 14 17:30:05 2014.

- Added device info to OpenCL debug output.
- Improved memory handling in OpenCL simulations.
- Various small bugfixes.


## Version 1.9.4
Released Wed Aug 13 09:11:36 2014.

- Added a script that installs a desktop icon for the gui under Windows.
- Added a global `readme.txt`.
- Various small bugfixes.


## Version 1.9.3
Released Fri Aug 8 18:27:19 2014.

- Various small bugfixes.


## Version 1.9.2
Released Fri Aug 1 15:10:05 2014.

- Improved ABF support.
- Various small bugfixes.


## Version 1.9.1
Released Thu Jul 31 13:11:48 2014.

- Bugfix in GUI for Windows.


## Version 1.9.0
Released Thu Jul 31 01:43:53 2014.

- Added stable point finding method.
- Added icons for windows version.
- Rebranding as 'Myokit' (with capital M, no more mention of the "Maastricht Myocyte Toolkit").
- Changed license to GPL.


## Version 1.8.1
Released Wed Jul 16 09:45:46 2014.

- Various improvements and bugfixes.


## Version 1.8.0
Released Wed Jul 16 01:28:36 2014.

- Updates to website
- Various small bugfixes.


## Version 1.7.5
Released Thu Jul 10 23:44:44 2014.

- Added method to fold log periodically (based on `split_periodic`).
- Various small bugfixes.


## Version 1.7.4
Released Tue Jul 8 17:30:13 2014.

- Various small bugfixes.


## Version 1.7.3
Released Mon Jul 7 18:14:49 2014.

- Reinstated logging of derivatives in CVODE simulation.
- Various small bugfixes.


## Version 1.7.2
Released Mon Jul 7 04:01:56 2014.

- Various small bugfixes.


## Version 1.7.1
Released Mon Jul 7 03:32:53 2014.

- Added load/save methods to DataBlock1d.
- Made ICSimulation work with DataBlock2d to calculate eigenvalues.
- Various small bugfixes.


## Version 1.7.0
Released Fri Jul 4 23:43:33 2014.

- Added a JacobianGenerator class.
- Added a simulation that integrates partial derivatives to find the derivatives of the state w.r.t. the initial conditions.
- Added latex export.
- Various small bugfixes.


## Version 1.6.2
Released Wed Jun 18 02:07:47 2014.

- Various small bugfixes.


## Version 1.6.1
Released Fri Jun 13 16:57:02 2014.

- Added IV curve experiment.
- Improved error detection in CVODE simulation.


## Version 1.6.0
Released Fri Jun 6 21:03:26 2014.

- Added a diffusion on/off switch to the OpenCL simulation.
- The OpenCL sim can now replace constants by scalar fields.
  This allows it to be used to test parameter influence or to simulate heterogeneity.


## Version 1.5.2
Released Wed Jun 4 17:59:58 2014.

- Better handling of unknown units.
- Added `eval_state_derivs` option to GUI.
- Added trim trailing whitespace method to gui.
- Gui and step script now show numerical errors if they occur.
- Added `trim()` and `itrim()` methods to simulation log.
- Added a 2-variable parameter range exploration class.
- DataBlock viewer now can export frames and graphs.
- Various improvements and bugfixes.


## Version 1.5.1
Released Thu May 8 16:27:25 2014.

- Added method `Model.set_name()`.
- Updated installer script for GNOME/KDE.
- Various small bugfixes.


## Version 1.5.0
Released Thu Apr 24 12:42:08 2014.

- Added on Strength-Duration experiment.
- Added method to create cumulative current/charge plots.


## Version 1.4.8
Released Tue Apr 22 17:50:48 2014.

- Changed `SimulationLog.integrate()` to use left-point rule instead of midpoint rule.
  This makes much more sense for the stimulus current when using CVODE.
- Various improvements and bugfixes.


## Version 1.4.7
Released Thu Apr 17 13:14:09 2014.

- Various small bugfixes.


## Version 1.4.6
Released Thu Apr 10 18:17:35 2014.

- Added RestitutionExperiment to `lib.common`.
- Various small bugfixes.


## Version 1.4.5
Released Mon Apr 7 18:51:25 2014.

- Re-organised code.
- Various small bugfixes.


## Version 1.4.4
Released Thu Mar 27 22:08:43 2014.

- Various improvements and bugfixes.


## Version 1.4.3
Released Mon Mar 17 20:58:48 2014.

- Various small bugfixes.


## Version 1.4.2
Released Tue Mar 11 11:34:50 2014.

- Added unit methods to IDE.
- Updated the installation guide.
- Added method to 'walk' over the operands in an expression, depth-first.
- Added a few default unit representations
- Various small bugfixes.


## Version 1.4.0
Released Tue Feb 18 17:33:44 2014.

- Added unit checking methods.
- Improved CellML unit reading from constants.
- Added `pack_snapshot()` method that creates a copy of the current Myokit version.
- Created `DataBlock` classes for alternative view of rectangular simulation data.
- Added GUI for viewing 1D and 2D simulation data.
- Various small bugfixes.


## Version 1.2.0
Released Mon Jan 27 14:35:57 2014.

- Changed `[[plot]]` to `[[script]]`.
- Various improvements and bugfixes.


## Version 1.1.0
Released Fri Jan 24 16:49:08 2014.

- Updated interface of opencl simulations.
- Added OpenCL-based parameter RangeTester class.
- Various small bugfixes.


## Version 1.0.2
Released Thu Jan 9 15:31:48 2014.

- Updates to documentation.


## Version 1.0.0
Released Tue Dec 24 20:53:55 2013.

- Improved documentation.
- Added a 'running simulations' guide.
- Added SymPy export.
- Added unit tests.
- Added binary format for simulation logs.
- Aliases are now retained in model export.
- Various small bugfixes.


## Version 0.17.2
Released Thu Dec 19 11:52:00 2013.

- Improved documentation.
- Various small bugfixes.


## Version 0.17.1
Released Thu Dec 19 11:47:13 2013.

- New model syntax, model stars with: `[[model]]`.
- Various small bugfixes.


## Version 0.17.0
Released Wed Dec 11 23:44:17 2013.

- Added binary version of `save_state` and `load_state`.
- Added ProgressPrinter to show progress during long simulations.
- Added precision switch to `prepare_log` and `load_csv`.
- Added method to find solvable equations dependent on one or more variables.
- Improved support for ABF protocol and data reading.
- Various small bugfixes.


## Version 0.16.3
Released Wed Nov 6 12:23:19 2013.

- Improved OpenCL simulation error output.
- Various improvements and bugfixes.


## Version 0.16.2
Released Fri Nov 1 22:00:13 2013.

- Improvements to GUI.
- Improved `find_nan` method in OpenCL sim.
- Added method to expression's `eval()` to evaluate with numpy.Float32 objects.
  This helps finding the source of OpenCL single-precision NaN errors.
- Various small bugfixes.


## Version 0.16.1
Released Thu Oct 31 18:10:26 2013.

- Refactored code, reduced size of giant modules.
- Various small bugfixes.


## Version 0.16.0
Released Thu Oct 31 01:52:44 2013.

- Added recovery-from-inactivation experiment.
- Updated `ActivationExperiment`, added boltzmann fit.
- Added boltzmann fit to `InactivationExperiment`.
- Added time constant of activation method to `ActivationExperiment`.
- Rewrote unit system.
- Various improvements and bugfixes.


## Version 0.15.9
Released Tue Oct 22 11:40:13 2013.

- Various small bugfixes.


## Version 0.15.8
Released Wed Oct 16 16:48:04 2013.

- Slight optimizations in OpenCL code.
- Various small bugfixes.


## Version 0.15.7
Released Tue Oct 15 18:22:07 2013.

- Various small bugfixes.


## Version 0.15.6
Released Tue Oct 15 15:36:34 2013.

- Updated step method to accept models as reference.
- Reinstated `Model.load_state()` method.
- Imrpoved find dialog.
- Various small bugfixes.


## Version 0.15.5
Released Mon Oct 14 21:14:14 2013.

- Added quick var info to gui.
- Renamed `current_diff` to `diffusion_current`.


## Version 0.15.4
Released Sat Oct 12 17:36:27 2013.

- Added on ChanneML import.
- FiberTissueSimulation now works with 2D fibers.


## Version 0.15.2
Released Thu Oct 10 21:40:07 2013.

- Added data extraction features to abf format.
- Added on Fiber-Tissue simulation class.
- Various improvements and bugfixes.


## Version 0.15.0
Released Wed Sep 18 14:58:30 2013.

- Number of cells to pace can now be set in `OpenCLCableSimulation`.
- Added function to find origin of NaN errors in an `OpenCLCableSimulation`.
- Updated SimulationLog to return mesh grid for pyplot.
- Added 1D CV calculation to `SimulationLog`.
- Renamed cable simulation classes.
- Made 1D OpenCL Simulation suitable for 2D use.
- Added method to list component cycles.
- Added a method that checks which variables cause mutually dependent components.
- Various small bugfixes.


## Version 0.14.1
Released Fri Aug 23 17:01:35 2013.

- Fixed direction convention for diffusion current.
- Simulation log now has local and global variables (for multi-cell simulations).
- Added OpenCL export.
- Added a C header file with pacing functions, shared by several simulations.
- Added a settings file `settings.py`.
- Added OpenCL simulation object.
- Various small bugfixes.


## Version 0.14.0
Released Fri Jul 19 18:34:28 2013.

- Various performance boosts.
- Rewrite of expression classes.
- Improved parser.
- Added options to move variables, delete variables.
- Improved `Model.clone()` method.
- Added strand simulations via Python interface.
- Various improvements and bugfixes.


## Version 0.13.9
Released Thu Jun 6 15:42:11 2013.

- Working CUDA kernel export.


## Version 0.13.8
Released Thu Jun 6 15:38:24 2013.

- Various small bugfixes.


## Version 0.13.7
Released Thu Jun 6 13:23:03 2013.

- Added simple Ansi-C forward euler export.
- Various small bugfixes.


## Version 0.13.6
Released Fri May 31 18:20:00 2013.

- Added progress bars to explorer in gui (F6).
- Worked on dependency graphs.
- Added meta data to components.
- Added option to `SimulationLog` to split into periodic pieces.
- Various improvements and bugfixes.


## Version 0.13.5
Released Thu May 23 20:53:10 2013.

- Various improvements and bugfixes.


## Version 0.13.4
Released Thu May 23 00:06:55 2013.

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


## Version 0.13.0
Released Thu Mar 28 02:21:09 2013.

- Added export to strand/fiber simulation in Ansi-C.
- Added syntax for binding to external values.
- Various small bugfixes.


## Version 0.12.7
Released Wed Feb 27 18:18:26 2013.

- Added plotting methods.
- Added benchmarking to simulation.
- Various improvements and bugfixes.


## Version 0.12.6
Released Tue Feb 26 14:37:23 2013.

- Refactored `myokit.lib`.
- Added APD calculating function.
- Added APD measurement to simulation using CVode's root finding.
- Added padding function to `save_csv`.
- Created `SimulationLog` class.
- Various small bugfixes.


## Version 0.12.4
Released Wed Feb 20 16:01:55 2013.

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


## Version 0.10.8
Released Tue Jan 15 14:55:31 2013.

- Bugfix in metadata export.


## Version 0.10.7
Released Tue Jan 15 14:45:32 2013.

- Various improvements and bugfixes.


## Version 0.10.6
Released Tue Jan 15 00:31:58 2013.

- Rewrote cellml import.
- Worked on methods to fit simplify functions.
- Updates to `mmt` syntax
- Added multi-line comments to `mmt` syntax.
- Various small bugfixes.


## Version 0.10.5
Released Mon Nov 12 14:56:57 2012.

- Added tests.
- Added `piecewise()` expressions.
- Various improvements and bugfixes.


## Version 0.10.3
Released Tue Oct 30 12:04:10 2012.

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


## Version 0.9.17
Released Fri Jul 27 18:19:05 2012.

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


## Version 0.9.0
Released Mon Mar 12 17:46:45 2012.

- First `mmt` syntax, parser and model classes.
- Initial CellML import.
- C++ export.
- Ansi-C export, python export.
- Beat script that uses generated Ansi-C and CVODE, compiled on the fly.
- First working GUI.


## Version 0.0.0
Released Mon Dec 19 11:08:50 2011.

- Working on simple model syntax, parser and export to C++.


