# Changelog
                
This page lists the main changes made to Myokit in each release.

<h3 id="v1.31.0" class="changelog-header">Version 1.31.0</h3>
<p class="changelog-date">Wed Aug 26 15:23:38 2020</p>
<ul class="changelog-list">
    <li>A completely rewritten SBML API and parser, by @DavAug, that's capable of handling models that define species and reactions.</li>
    <li><code>Ohm</code> is now a quantifiable unit in the mmt syntax, i.e. <code>1 [MOhm]</code>. This replaces the non-standard <code>R</code> unit which has been removed.</li>
    <li>Unit tests are now included in the pypi package.</li>
    <li>A recently introduced bug in the HHSimulation's <code>steady_state()</code> method was fixed.</li>
    <li>Sympy is no longer a required dependency (but still an optional one).</li>
    <li>Models, protocols, and CVODE simulations can now be pickled, and tests have been added that check that simulations can be run in parallel (even on Windows). To further aid in this, simulations now include a time and process number dependent hash in their generated-module names.</li>
    <li>Non-integer exponents are now allowed in the unit system, which compares units with a <code>close()</code> method that expects a certain numerical tolerance, instead of using exact comparison.</li>
    <li>The <code>myokit.mxml</code> module has been removed.</li>
    <li>The cumulative-current plot now has a maximum-number-of-currents option (all further currents will be bundled into one).</li>
    <li>Model and protocol now support comparison with <code>==</code>.</li>
    <li>Imports and exports now raise warnings instead of using the Myokit textlogger for this.</li>
    <li>The CellML export now ensures there are no spaces in initial value or unit multiplier attributes.</li>
    <li>CellML imports treat new base units as dimensionless.</li>
    <li>CellML imports now import models that contain unsupported units (but with warnings).</li>
    <li>CellML imports now import models with non-integer unit exponents.</li>
    <li>The method <code>show_evalution_of</code> now has consistently ordered output.</li>
    <li>The output of the <code>step()</code> method has been improved, and the method now only warns about relative differences bigger than 1 epsilon.</li>
    <li>Some slight changes to simulation building: Now uses <code>--inplace</code> instead of <code>--old-and-unmanageable</code> and should delete any temporary files created in the process.</li>
    <li>The IDE now checks the protocol even if the model is invalid or unchanged.</li>
    <li>Bugfix for simulations that ended at a time numerically indistinguishable from an event time.</li>
    <li>Bugfixes and fewer warnings for various matplotlib versions.</li>
    <li>Bugfix to lib.common.StrenghtDuration.</li>
</ul>

<h3 id="v1.30.6" class="changelog-header">Version 1.30.6</h3>
<p class="changelog-date">Wed Apr 29 11:26:16 2020</p>
<ul class="changelog-list">
    <li>Fixed bug where GUI CellML export didn't export stimulus current.</li>
</ul>

<h3 id="v1.30.5" class="changelog-header">Version 1.30.5</h3>
<p class="changelog-date">Mon Apr 20 12:51:58 2020</p>
<ul class="changelog-list">
    <li>Added support for CellML 2.0.</li>
    <li>Rewrote SBML import to use etree instead of DOM.</li>
    <li>Removed parse_mathml_dom function.</li>
    <li>Removed mxml dom_child and dom_next methods.</li>
    <li>Now setting OpenCL framework as linker flag on osx.</li>
</ul>

<h3 id="v1.30.4" class="changelog-header">Version 1.30.4</h3>
<p class="changelog-date">Fri Mar 27 12:13:35 2020</p>
<ul class="changelog-list">
    <li>Fixed a bug with running simulations in Spyder on Windows.</li>
    <li>Added clone() and __repr__() methods to myokit.Equation.</li>
    <li>Some fixes and tweaks to CellML 1.0/1.1 API</li>
</ul>

<h3 id="v1.30.3" class="changelog-header">Version 1.30.3</h3>
<p class="changelog-date">Mon Mar 2 11:03:38 2020</p>
<ul class="changelog-list">
    <li>Small fixes to CellML validation.</li>
    <li>Fixed typo in units becquerel.</li>
    <li>Added notanumber and infinity to MathML parser.</li>
</ul>

<h3 id="v1.30.2" class="changelog-header">Version 1.30.2</h3>
<p class="changelog-date">Sat Feb 1 19:43:40 2020</p>
<ul class="changelog-list">
    <li>Removed 'myo' script.</li>
    <li>Fixed EasyML issue for inf/tau variables used by more than one state.</li>
</ul>

<h3 id="v1.30.1" class="changelog-header">Version 1.30.1</h3>
<p class="changelog-date">Fri Jan 3 16:31:40 2020</p>
<ul class="changelog-list">
    <li>Added more import/export options to the IDE menu.</li>
    <li>Updated component.code() to always outout aliases in the same order.</li>
    <li>Added method to find Markov models in a Myokit model.</li>
    <li>Added method to convert Markov models to compact form.</li>
    <li>Added method to convert Markov models to full ODE form.</li>
    <li>LinearModel now converts to full ODE form.</li>
    <li>Added method lib.guess.membrane_capacitance.</li>
    <li>Added method lib.guess.membrane_currents.</li>
    <li>Added (experimental) EasyML export.</li>
    <li>Small bugfixes and documentation updates.</li>
    <li>Improved exception handling when evaluating a unit containing an invalid power.</li>
    <li>Made default script and protocol robust against incompatible units.</li>
    <li>Made CellML API from_myokit_model more robust against invalid units.</li>
</ul>

<h3 id="v1.30.0" class="changelog-header">Version 1.30.0</h3>
<p class="changelog-date">Mon Dec 30 12:08:56 2019</p>
<ul class="changelog-list">
    <li>Rewrote CellML import and export, with improved error handling and validation.</li>
    <li>CellML import now converts hardcoded stimulus equation to Myokit protocol.</li>
    <li>CellML export now converts Myokit protocol to hardcoded stimulus equation.</li>
    <li>CellML import now generates more approprate default scripts.</li>
    <li>CellML import now supports unit conversion between components.</li>
    <li>CellML export now infers units from RHS if no unit set.</li>
    <li>CellML import and export can now both handle Web Lab "oxmeta" annotations.</li>
    <li>Various changes and improvements to MathML parsing</li>
    <li>Added missing __iter__ to Model and VarOwner.</li>
    <li>The myokit.Name expression can now wrap objects other than myokit.Variable, allowing Myokit's expression system to be re-used for non-myokit expressions.</li>
    <li>Removed myokit.UnsupportedFunction.</li>
</ul>

<h3 id="v1.29.1" class="changelog-header">Version 1.29.1</h3>
<p class="changelog-date">Sun Nov 24 12:48:54 2019</p>
<ul class="changelog-list">
    <li>Added guessing module, with method to guess which variables (if any) represent the membrane potential and stimulus current.</li>
    <li>Fix for sundials development versions.</li>
    <li>Fixes for PySide2 support.</li>
</ul>

<h3 id="v1.29.0" class="changelog-header">Version 1.29.0</h3>
<p class="changelog-date">Fri Oct 11 16:21:01 2019</p>
<ul class="changelog-list">
    <li>Myokit is now released under a BSD 3-clause license</li>
    <li>Bugfix to <pre>myokit step</pre> command line tool.</li>
</ul>

<h3 id="v1.28.9" class="changelog-header">Version 1.28.9</h3>
<p class="changelog-date">Wed Sep 11 23:18:57 2019</p>
<ul class="changelog-list">
    <li>Added PySide2 support.</li>
    <li>Deprecated PyQt4 and PySide.</li>
    <li>Added a method Model.remove_derivative_references().</li>
    <li>Bugfix to repr(Model) for models with no name.</li>
    <li>Added Model.timex(), labelx() and binding(), which work
        like time(), label() and binding() but raise an exception
        if no appropriate variable is found.</li>
    <li>Deprecated lib.multi.time(), label(), and binding().</li>
</ul>

<h3 id="v1.28.8" class="changelog-header">Version 1.28.8</h3>
<p class="changelog-date">Tue Sep 3 18:09:01 2019</p>
<ul class="changelog-list">
    <li>Added method Variable.convert_unit() that changes a variable's units and updates the model equations accordingly.</li>
    <li>Unit.conversion_factor now returns a Quantity instead of a float, and accepts helper Quantities for incompatible conversions.</li>
    <li>Added Unit.clarify() method that gives clear representation.</li>
    <li>Added Unit.multiplier_log_10() method.</li>
    <li>Added rtruediv and pow operators to Quantity class.</li>
    <li>Small bugfixes to myokit.lib.hh.</li>
    <li>Stopped requiring HH alphas/betas and taus/infs to depend on V (allows drug-binding work).</li>
    <li>Bugfix: Time variable in CellML export no longer has equation or initial value.</li>
    <li>CellML export: components now ordered alphabetically.</li>
    <li>Variables with an 'oxmeta: time' meta annotation are now exported to CellML with an oxmeta RDF annotation.</li>
    <li>CellML import now allows 'deca' prefix.</li>
    <li>Added CellML identifier checks to cellml import.</li>
    <li>Renamed DataLog.find() to find_after().</li>
    <li>Added DataLog.interpolate_at(name, time) method.</li>
    <li>Improved colormap used in plots.cumulative_current().</li>
    <li>Bugfix to 'myokit step' for models without a name meta property.</li>
    <li>Updated sign error handling in myokit.step().</li>
    <li>Added IDE shortcuts for unit checking.</li>
    <li>IDE now jumps to unit errors, if found.</li>
    <li>Improved exception display in IDE.</li>
    <li>Var_info now includes unit.</li>
    <li>Fixed bug in Unit.__repr__ for small multipliers.</li>
    <li>Improved notation of units when complaining about them.</li>
</ul>

<h3 id="v1.28.7" class="changelog-header">Version 1.28.7</h3>
<p class="changelog-date">Sat Aug 3 02:53:59 2019</p>
<ul class="changelog-list">
    <li>Added option to register external formats.</li>
    <li>Added option to avoid certain prefixes when generating unique variable names.</li>
    <li>Model.expressions_for() now accepts more than 1 argument, and handles
dependencies on derivatives correctly.</li>
    <li>Removed deprecated method Model.solvable_subset().</li>
</ul>

<h3 id="v1.28.6" class="changelog-header">Version 1.28.6</h3>
<p class="changelog-date">Fri Jul 26 14:20:17 2019</p>
<ul class="changelog-list">
    <li>Added debug option to 'myokit compiler' command.</li>
</ul>

<h3 id="v1.28.5" class="changelog-header">Version 1.28.5</h3>
<p class="changelog-date">Tue Jul 16 11:17:07 2019</p>
<ul class="changelog-list">
    <li>Bugfix: Removing variables now also removes their bindings and labels.</li>
    <li>Added unit tests.</li>
    <li>Improved performance in lib.markov analytical simulations.</li>
    <li>Updated the 'myo' script to use the python3 executable</li>
    <li>Fixed a bug in the default script used when creating or importing a model.</li>
    <li>Made GNOME/KDE icons install using sys.executable instead of a hardcoded python command.</li>
    <li>Fixed handling of string encoding in cellml import.</li>
</ul>

<h3 id="v1.28.4" class="changelog-header">Version 1.28.4</h3>
<p class="changelog-date">Tue May 28 21:47:10 2019</p>
<ul class="changelog-list">
    <li>Myokit is now tested on Python 3.7, but no longer on 3.4</li>
    <li>Updated default OpenCL paths for windows</li>
    <li>GUI fixes for matplotlib 3.1.0+</li>
    <li>Added set_constant() method to markov simulations.</li>
    <li>Added log_times option to lib.markov.AnalyticalSimulation, and started pre-
        allocating arrays.</li>
    <li>Added option to cumulative current plot to normalise currents.</li>
</ul>

<h3 id="v1.28.3" class="changelog-header">Version 1.28.3</h3>
<p class="changelog-date">Thu May 2 12:41:15 2019</p>
<ul class="changelog-list">
    <li>Fixed some floating point issues with protocols and pacing.</li>
    <li>Updated OpenCL code to work with VS 9.</li>
    <li>Some small changes to the Protocol API.</li>
    <li>Added format protocol option to IDE.</li>
</ul>

<h3 id="v1.28.2" class="changelog-header">Version 1.28.2</h3>
<p class="changelog-date">Wed Dec 19 19:43:19 2018</p>
<ul class="changelog-list">
    <li>Improved support for native OpenCL on OS/X.</li>
    <li>Native maths in OpenCL simulations is now configurable and disabled by default.</li>
</ul>

<h3 id="v1.28.1" class="changelog-header">Version 1.28.1</h3>
<p class="changelog-date">Wed Dec 19 00:50:04 2018</p>
<ul class="changelog-list">
    <li>Added support for Sundials 4.0.0</li>
    <li>Made SymPy a dependency.</li>
    <li>Made current loggable in discrete markov simulations.</li>
    <li>Added log_times argument to analytical HH simulation.</li>
    <li>Improved performance of analytical HH simulation.</li>
    <li>Added AbfFile.extract_channel method that joins sweeps.</li>
    <li>Added ATF capability to datalog viewer.</li>
    <li>Added limited .pro support to DataLogViewer.</li>
    <li>Added ProgressReporter that cancels the operation after a time out.</li>
    <li>Added cut/copy/paste options to menu in IDE.</li>
    <li>Bugfix: myokit.system didn't check for sympy version.</li>
    <li>Deprecated myo script.</li>
    <li>Changed myokit.VERSION to myokit.__version__.</li>
    <li>Various minor tweaks and fixes.</li>
</ul>

<h3 id="v1.28.0" class="changelog-header">Version 1.28.0</h3>
<p class="changelog-date">Thu Nov 22 22:49:55 2018</p>
<ul class="changelog-list">
    <li>Added myokit.lib.hh module for recognising Hodgkin-Huxley style ion current models and using them in fast analytical simulations.</li>
    <li>Added Rush-Larsen (RL) option to OpenCLSimulation.</li>
    <li>Added CUDA kernel export with RL updates.</li>
    <li>Added OpenCLRLExporter for OpenCL kernel with Rush-Larsen.</li>
    <li>Improved logging of intermediary variables in OpenCL simulations.</li>
    <li>Improved logging in Simulation1d.</li>
    <li>Fix to Abf reader for (unsupported) userlists (abf v2).</li>
    <li>Fixes to Sundials configuration on Windows</li>
    <li>Small bugfixes, documentation updates, etc..</li>
</ul>

<h3 id="v1.27.7" class="changelog-header">Version 1.27.7</h3>
<p class="changelog-date">Thu Nov 1 00:19:10 2018</p>
<ul class="changelog-list">
    <li>Various fixes to make Myokit work with Python 2.7.6 (and later).</li>
</ul>

<h3 id="v1.27.6" class="changelog-header">Version 1.27.6</h3>
<p class="changelog-date">Thu Sep 27 15:24:51 2018</p>
<ul class="changelog-list">
    <li>Now running sundials auto-detection with every 'import myokit' if not set in config file.</li>
</ul>

<h3 id="v1.27.5" class="changelog-header">Version 1.27.5</h3>
<p class="changelog-date">Thu Sep 20 12:18:33 2018</p>
<ul class="changelog-list">
    <li>Bugfix to OpenCL.load_selection.</li>
    <li>Added system info command</li>
    <li>Added command option to show C Compiler support.</li>
    <li>Added command option to show Sundials support.</li>
    <li>Bugfix to Unit.rdiv</li>
    <li>Small fixes to lib.fit</li>
    <li>Documentation config update for sphinx >=1.8.</li>
    <li>Parsing now has full test cover.</li>
    <li>Removed special line feed code from parser, as in unicode they are treated as newlines (and stripped out by splitlines())</li>
    <li>Removed obsolete TEXT_OPS code from parser.</li>
    <li>Removed redundant check from parser.</li>
    <li>Removed another redundant check from parser.</li>
    <li>Various small bugfixes and tweaks.</li>
</ul>

<h3 id="v1.27.4" class="changelog-header">Version 1.27.4</h3>
<p class="changelog-date">Sun Aug 12 22:34:40 2018</p>
<ul class="changelog-list">
    <li>Added sundials version detection on first run.</li>
    <li>Moved myokit config files from ~/.myokit to ~/.config/myokit</li>
    <li>Renamed NumpyExpressionwriter NumPyExpressionWriter.</li>
    <li>Fixed test issues on os/x.</li>
</ul>

<h3 id="v1.27.3" class="changelog-header">Version 1.27.3</h3>
<p class="changelog-date">Mon Aug 6 13:53:38 2018</p>
<ul class="changelog-list">
    <li>Updated the way sundials library locations are stored on windows systems.</li>
</ul>

<h3 id="v1.27.2" class="changelog-header">Version 1.27.2</h3>
<p class="changelog-date">Sat Aug 4 18:02:15 2018</p>
<ul class="changelog-list">
    <li>Added script that creates icons for windows.</li>
    <li>Updated script that creates icons for linux.</li>
</ul>

<h3 id="v1.27.1" class="changelog-header">Version 1.27.1</h3>
<p class="changelog-date">Fri Aug 3 18:00:00 2018</p>
<ul class="changelog-list">
    <li>Placeholder release to fix Pypi issue.</li>
</ul>

<h3 id="v1.27.0" class="changelog-header">Version 1.27.0</h3>
<p class="changelog-date">Fri Aug 3 13:51:05 2018</p>
<ul class="changelog-list">
    <li>Added support for Python 3.4, 3.5, and 3.6.</li>
    <li>Added support for Sundials 3 (by <a href="https://github.com/teosbpl">teosbpl</a>).</li>
    <li>Added support for various Visual C++ compilers.</li>
    <li>Made Myokit pip-installable, stopped providing windows installer.</li>
    <li>Replaced windows sundials binaries with Visual-Studio compiled ones.</li>
    <li>Added a system-wide <code>myokit</code> command (after pip install on unix systems).</li>
    <li>Moved development from private repo to <a href="https://github.com/MichaelClerx/myokit/">GitHub</a></li>
    <li>Set up automated testing with Travis (linux) and Appveyor (windows)</li>
    <li>Greatly increased unit-test coverage (and set up checking with codecov.io)</li>
    <li>Added contribution guidelines</li>
    <li>Added style checking with Flake8</li>
    <li>Removed OrderedPiecewise, Polynomial, Spline, and lib.approx.</li>
    <li>Deprecated lib.fit. Please have a look at <a href="https://github.com/pints-team/pints">Pints</a> instead.</li>
    <li>Removed quadfit() methods from lib.fit.</li>
    <li>Deprecated lib.common</a>
    <li>Removed HTML page generating classes from mxml.</li>
    <li>Simplified some of the error classes.</li>
    <li>Simplified Benchmarker.</li>
    <li>DataLog.apd() now has same output as Simulation threshold crossing finder.</li>
    <li>On-the-fly compilation switched from distutils to setuptools.</li>
    <li>Tidied up.</li>
    <li>Lots of bugfixes.</li>
    <li>Made IDE show Python version in about screen.</li>
</ul>

<h3 id="v1.26.3" class="changelog-header">Version 1.26.3</h3>
<p class="changelog-date">Fri Feb 9 19:24:21 2018</p>
<ul class="changelog-list">
    <li>Fixed critical bug introduced in version 1.26.2 that
    stopped Windows simulations from running.</li>
</ul>

<h3 id="v1.26.2" class="changelog-header">Version 1.26.2</h3>
<p class="changelog-date">Thu Jan 11 23:49:06 2018</p>
<ul class="changelog-list">
    <li>Fixed a small bug in Simulation's logging when using
        the new <code>log_times</code> argument.</li>
    <li>Added Matlab and text file tab to DataLog viewer.</li>
    <li>Removed ancient restriction on components not being called <code>external</code>.</li>
    <li>Refactored code to pass flake8 tests.</li>
    <li>Added <code>len()</code> method to Protocol</li>
    <li>Now setting <code>runtime_libraries</code> parameter for
        all compiled classes (simulations), removing the need to
        set <code>LD_LIBRARY_PATH</code> on some systems.</li>
</ul>

<h3 id="v1.26.1" class="changelog-header">Version 1.26.1</h3>
<p class="changelog-date">Fri Nov 24 15:13:19 2017</p>
<ul class="changelog-list">
    <li>Updated licensing info</li>
</ul>

<h3 id="v1.26.0" class="changelog-header">Version 1.26.0</h3>
<p class="changelog-date">Fri Nov 24 12:22:57 2017</p>
<ul class="changelog-list">
    <li>Myokit can now be installed as library using 'python setup.py develop'</li>
    <li>Fixed a bug in the gnome scripts that install icons</li>
    <li>The DataLog trim, itrim and extend methods now return
        copies, instead of modifying the data 'in place'. This
        makes the DataLog's methods more consistent, and
        prevents accidental data loss. However, this change
        makes Myokit 1.26.0 slightly backwards incompatible.</li>
    <li>Added a DataLog.keys_like method to iterate over 1d or 2d logs</li>
</ul>

<h3 id="v1.25.3" class="changelog-header">Version 1.25.3</h3>
<p class="changelog-date">Fri Oct 6 20:41:10 2017</p>
<ul class="changelog-list">
    <li>Small tweaks to IDE</li>
    <li>Fix to DataLog.fold() to discard remainder if period doesn't exactly
        divide the log length.</li>
    <li>Various bugfixes.</li>
    <li>Improved cvode error catching.</li>
    <li>More control over lib.fit verbosity</li>
    <li>Added random starting point option to lib.fit methods.</li>
    <li>Added the option to explicitly specify log points in the single-cell Simulation
        class.</li>
    <li>CVODE sim now raises SimulationError if maximum number of repeated zero-steps
        is made, instead of plain Exception.</li>
    <li>Fix fit.cmaes to work with cma version 2.x</li>
</ul>

<h3 id="v1.25.2" class="changelog-header">Version 1.25.2</h3>
<p class="changelog-date">Thu Aug 3 22:24:31 2017</p>
<ul class="changelog-list">
    <li>Small tweaks to IDE.</li>
    <li>Fixed bug with saving the time variable in DataLog.save_csv().</li>
</ul>

<h3 id="v1.25.1" class="changelog-header">Version 1.25.1</h3>
<p class="changelog-date">Tue Jul 18 12:27:55 2017</p>
<ul class="changelog-list">
    <li>Added xNES and SNES optimisation methods.</li>
    <li>Added interface to CMA-ES optimisation method.</li>
    <li>Replaced the 'tolerance' arguments in myokit.lib.fit
        with more accurate counterparts.</li>
    <li>Removed ga() optimisation method.</li>
</ul>

<h3 id="v1.25.0" class="changelog-header">Version 1.25.0</h3>
<p class="changelog-date">Mon Jul 10 12:23:52 2017</p>
<ul class="changelog-list">
    <li>Added model export to 'stan'.</li>
    <li>Added data-clamp to CVODE simulation (works, but
        generally a bad idea).</li>
    <li>Added Protocol.add_step convenience method for building
        sequential step protocols.</li>
    <li>Added log() method to ExportError.</li>
    <li>Fixed bug in ABF reading (ABF channel index can be
        greater than number of channels in file).</li>
    <li>Small fixes to DataLogViewer.</li>
    <li>Fixed issue with PySide file open/save dialogs.</li>
    <li>Several small fixes to docs.</li>
</ul>

<h3 id="v1.24.4" class="changelog-header">Version 1.24.4</h3>
<p class="changelog-date">Thu May 4 15:25:38 2017</p>
<ul class="changelog-list">
    <li>Bugfix in PyQt4 support.</li>
</ul>

<h3 id="v1.24.3" class="changelog-header">Version 1.24.3</h3>
<p class="changelog-date">Wed May 3 22:48:21 2017</p>
<ul class="changelog-list">
    <li>Fixed PyQt4/5 and PySide compatibility issue that was
    causing errors in the DataBlock viewer's open function.</li>
</ul>

<h3 id="v1.24.2" class="changelog-header">Version 1.24.2</h3>
<p class="changelog-date">Tue Mar 28 11:10:53 2017</p>
<ul class="changelog-list">
    <li>Added missing #pragma directive to enable double-precision
    simulations OpenCL .</li>
</ul>

<h3 id="v1.24.1" class="changelog-header">Version 1.24.1</h3>
<p class="changelog-date">Mon Oct 24 16:57:01 2016</p>
<ul class="changelog-list">
    <li>Added support for PyQt5.</li>
</ul>

<h3 id="v1.24.0" class="changelog-header">Version 1.24.0</h3>
<p class="changelog-date">Fri Oct 14 11:13:26 2016</p>
<ul class="changelog-list">
    <li>The IDE now has a model navigator, that displays the
        model components alphabetically and lets you navigate large
        models more easily.</li>
    <li>Fixed a bug in the implementation of DataBlock1d.grid(),
        and updated its documentation: this method returns
        coordinates for squares where each square represents a
        data point.
        See the <a href="<?=root()?>examples/#stewart-2009">Stewart
        2009 OpenCL example</a> for an example of its use.
        </li>
    <li>Added a second method DataBlock1d.image_grid() that returns
        coordinates for points where each point in space
        represents a data point.</li>
    <li>Fixed bug with Ctrl+Shift+Home in IDE</li>
    <li>Various small bugfixes in IDE</li>
    <li>Updated installation instructions on website</li>
</ul>

<h3 id="v1.23.4" class="changelog-header">Version 1.23.4</h3>
<p class="changelog-date">Sun Sep 4 13:01:03 2016</p>
<ul class="changelog-list">
    <li>Fixed bug (with new numpy) in DataLog.split_periodic</li>
    <li>Fixed warnings in GDE</li>
    <li>Fixed issue with pyside/pyqt difference</li>
</ul>

<h3 id="v1.23.3" class="changelog-header">Version 1.23.3</h3>
<p class="changelog-date">Thu Jul 21 17:25:52 2016</p>
<ul class="changelog-list">
    <li>Updated documentation and examples</li>
    <li>Added extra callback option to pso for detailed feedback</li>
    <li>Updated default search paths for Sundials headers and libraries</li>
</ul>

<h3 id="v1.23.2" class="changelog-header">Version 1.23.2</h3>
<p class="changelog-date">Thu Jun 16 00:01:04 2016</p>
<ul class="changelog-list">
    <li>Small bugfix to IDE</li>
    <li>Added pre() method to Markov simulations (AnalyticalSimulation and
        DiscreteSimulation)</li>
    <li>Fixed a bug in lib.markov.AnalyticalSimulation(run) when
        log_interval >= duration</li>
    <li>IDE now shows exact location of recent files in status bar.</li>
    <li>Fixed bug in SymPyExpressionWriter.eq() and renamed classes
        to use SymPy with capital P</li>
</ul>

<h3 id="v1.23.1" class="changelog-header">Version 1.23.1</h3>
<p class="changelog-date">Sun Jun 5 22:38:15 2016</p>
<ul class="changelog-list">
    <li>Updated documentation</li>
    <li>Fixed opencl issue</li>
</ul>

<h3 id="v1.23.0" class="changelog-header">Version 1.23.0</h3>
<p class="changelog-date">Mon May 30 17:13:52 2016</p>
<ul class="changelog-list">
    <li>Added methods for easier symbolic addition of names/components for situations
        where exact names aren't important.</li>
    <li>Bugfix to datalog viewer</li>
    <li>Bugfix to vargrapher</li>
</ul>

<h3 id="v1.22.7" class="changelog-header">Version 1.22.7</h3>
<p class="changelog-date">Wed May 25 23:02:44 2016</p>
<ul class="changelog-list">
    <li>Update to ide: Can now add/remove comments</li>
    <li>Bugfixes to protocol reading in AbfFile</li>
    <li>Bugfix in AbfFile string reading</li>
    <li>DataLog viewer now opens multiple files if specified on the command line</li>
    <li>Fix to OpenCL sim reserved names list</li>
    <li>Various tweaks and fixes</li>
</ul>

<h3 id="v1.22.6" class="changelog-header">Version 1.22.6</h3>
<p class="changelog-date">Fri Mar 11 16:07:23 2016</p>
<ul class="changelog-list">
    <li>Fixed bug in IDE</li>
    <li>Fix to windows start menu icons</li>
</ul>

<h3 id="v1.22.5" class="changelog-header">Version 1.22.5</h3>
<p class="changelog-date">Thu Feb 25 18:14:43 2016</p>
<ul class="changelog-list">
    <li>Updated online examples.</li>
    <li>Bugfix in deprecated method Protocol.guess_duration()</li>
</ul>

<h3 id="v1.22.4" class="changelog-header">Version 1.22.4</h3>
<p class="changelog-date">Wed Feb 24 12:40:16 2016</p>
<ul class="changelog-list">
    <li>Fixed bug with auto-indenting and smart up/down arrows in IDE.</li>
    <li>Fixed bug in parsing of indented multi-line meta-data properties.</li>
    <li>Fixed bug with [[script]] sections being added to files when saved.</li>
    <li>Slight update to DataLog.apd().</li>
    <li>Updated the docs of both apd methods to make clear that they use fixed thresholds.</li>
</ul>

<h3 id="v1.22.3" class="changelog-header">Version 1.22.3</h3>
<p class="changelog-date">Fri Feb 19 16:02:51 2016</p>
<ul class="changelog-list">
    <li>Added hybrid PSO option to myokit.lib.fit.</li>
    <li>Added option to return multiple particles' results to PSO.</li>
    <li>Bugfixes and updates to documentation.</li>
    <li>Added BFGS method (interface to scipy) to myokit.lib.fit.</li>
</ul>

<h3 id="v1.22.2" class="changelog-header">Version 1.22.2</h3>
<p class="changelog-date">Mon Feb 8 21:11:59 2016</p>
<ul class="changelog-list">
    <li>Small bugfix in markov simulation class.</li>
</ul>

<h3 id="v1.22.1" class="changelog-header">Version 1.22.1</h3>
<p class="changelog-date">Mon Feb 8 15:51:42 2016</p>
<ul class="changelog-list">
    <li>Updates to source highlighting in the IDE.</li>
    <li>Various small bugfixes.</li>
    <li>Protocols and events now define a 'characteristic time'.</li>
    <li>The protocol class is now slightly stricter than before, removed its
        validate() method.</li>
    <li>Both markov model simulation classes can now run simulations based on
        myokit.Protocol objects.</li>
</ul>

<h3 id="v1.22.0" class="changelog-header">Version 1.22.0</h3>
<p class="changelog-date">Thu Jan 28 20:16:15 2016</p>
<ul class="changelog-list">
    <li>Rewrote the Markov model module.</li>
    <li>Added a method to perform stochastic simulations with Markov
     models.</li>
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 1.21.12</h3>
<p class="changelog-date">Wed Jan 20 00:36:14 2016</p>
<ul class="changelog-list">
    <li>The CellML export now includes a simple periodic pacing protocol.</li>
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 1.21.11</h3>
<p class="changelog-date">Tue Jan 5 00:33:47 2016</p>
<ul class="changelog-list">
    <li>Tidied up code.</li>
</ul>

<h3 class="changelog-header">Version 1.21.10</h3>
<p class="changelog-date">Mon Jan 4 22:53:56 2016</p>
<ul class="changelog-list">
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 1.21.9</h3>
<p class="changelog-date">Mon Dec 28 13:15:45 2015</p>
<ul class="changelog-list">
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 1.21.8</h3>
<p class="changelog-date">Thu Nov 5 14:21:49 2015</p>
<ul class="changelog-list">
    <li>Removed option to run mmt files in threads (was not used and caused
     issues with GUI).</li>
    <li>Giving up on multiprocessing on windows. Adding switches to disable it
     in the examples.</li>
    <li>Various bugfixes and improvements</li>
</ul>

<h3 class="changelog-header">Version 1.21.7</h3>
<p class="changelog-date">Tue Oct 27 12:11:18 2015</p>
<ul class="changelog-list">
    <li>Improved logging in simulations, made it more consistent throughout
     Myokit</li>
</ul>

<h3 class="changelog-header">Version 1.21.6</h3>
<p class="changelog-date">Fri Oct 23 12:13:32 2015</p>
<ul class="changelog-list">
    <li>Various small bugfixes, improvements and website updates</li>
</ul>

<h3 class="changelog-header">Version 1.21.5</h3>
<p class="changelog-date">Wed Oct 14 14:31:28 2015</p>
<ul class="changelog-list">
    <li>Changed the way states are stored in the model (list instead of
     OrderedDict). Was causing funny bug. Now has less redundant info.</li>
    <li>Fixed bug in remove_component()</li>
</ul>

<h3 class="changelog-header">Version 1.21.4</h3>
<p class="changelog-date">Tue Oct 6 17:22:08 2015</p>
<ul class="changelog-list">
<li>Moving to next version</li>
    <li>Added debug options to openclsim</li>
    <li>OpenCL sim can now pace based on rules again, which is far more
     efficient for large numbers of cells.</li>
</ul>

<h3 class="changelog-header">Version 1.21.3</h3>
<p class="changelog-date">Tue Oct 6 09:44:02 2015</p>
<ul class="changelog-list">
    <li>Various bugfixes</li>
</ul>

<h3 class="changelog-header">Version 1.21.2</h3>
<p class="changelog-date">Mon Oct 5 22:16:48 2015</p>
<ul class="changelog-list">
    <li>Added OpenCL device selection</li>
    <li>Updated cumulative current plot method</li>
</ul>

<h3 class="changelog-header">Version 1.21.1</h3>
<p class="changelog-date">Sat Sep 12 20:55:48 2015</p>
<ul class="changelog-list">
    <li>Various small bugfixes and improvements</li>
</ul>

<h3 class="changelog-header">Version 1.21.0</h3>
<p class="changelog-date">Fri Sep 4 00:55:24 2015</p>
<ul class="changelog-list">
    <li>Add Powell's method to fit library</li>
    <li>Added model statistics screen to IDE</li>
    <li>Presence of <import> tag in CellML now causes exception instead of
     warning.</li>
    <li>Improved CellML import error messages</li>
    <li>There is no longer a restriction on the type of expression used as a
     first argument to piecewise and if</li>
    <li>Fixes to MathML parser and CellML import</li>
    <li>Added option to extract colormap to DataBlock viewer</li>
    <li>Added section about uninstalling on windows and slight hints about
     filesizes to website</li>
    <li>Introduced "evaluator" class used for parallelized optimization
     algorithms. Rewrote PSO to use it.</li>
    <li>Added a genetic algorithm optimization method (does not outperform
     PSO)</li>
    <li>Added reset script to myo that removes all user settings i.e. the
     entire DIR_MYOKIT.</li>
    <li>Added version check to avoid Python3</li>
    <li>Myokit for WinPython now has an uninstaller that shows up in Add/Remove
    programs.</li>
    <li>Various small bugfixes and improvements</li>
</ul>

<h3 class="changelog-header">Version 1.20.5</h3>
<p class="changelog-date">Mon Jun 1 16:21:41 2015</p>
<ul class="changelog-list">
    <li>Added Python version check.</li>
    <li>Fitting library: Adding quadratic polynomial fit used to test local
     optima</li>
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 1.20.4</h3>
<p class="changelog-date">Mon May 11 14:52:12 2015</p>
<ul class="changelog-list">
    <li>Improved export of units to CellML</li>
    <li>DataLogViewer can now open CSV</li>
    <li>Fixed windows newline issue when writing \r\n.</li>
    <li>Small fix to OpenCL memory management</li>
    <li>OpenCL sim now also cleans when cancelled with keyboard interrupt</li>
    <li>Added a finally: sim_clean() to all simulations.</li>
    <li>Various small bugfixes and improvements</li>
</ul>

<h3 class="changelog-header">Version 1.20.1</h3>
<p class="changelog-date">Tue Apr 21 16:15:03 2015</p>
<ul class="changelog-list">
    <li>Various bugs fixed in the IDE</li>
</ul>

<h3 class="changelog-header">Version 1.20.0</h3>
<p class="changelog-date">Wed Apr 8 15:57:41 2015</p>
<ul class="changelog-list">
    <li>Added 'next' keyword to protocol syntax.</li>
</ul>

<h3 class="changelog-header">Version 1.19.0</h3>
<p class="changelog-date">Tue Apr 7 01:51:31 2015</p>
<ul class="changelog-list">
    <li>Explorer now shows output in IDE console</li>
    <li>PSimulation now tracks arbitrary variables dy/dp, no longer only states
     dy/dp</li>
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 1.18.6</h3>
<p class="changelog-date">Sun Mar 29 15:57:38 2015</p>
<ul class="changelog-list">
    <li>Various small bugfixes in the GUI</li>
</ul>

<h3 class="changelog-header">Version 1.18.5</h3>
<p class="changelog-date">Tue Mar 24 15:46:01 2015</p>
<ul class="changelog-list">
    <li>Even more improvements to the GUI</li>
</ul>

<h3 class="changelog-header">Version 1.18.4</h3>
<p class="changelog-date">Mon Mar 23 13:05:39 2015</p>
<ul class="changelog-list">
    <li>Several improvements to the new GUI</li>
</ul>

<h3 class="changelog-header">Version 1.18.3</h3>
<p class="changelog-date">Wed Mar 18 13:01:02 2015</p>
<ul class="changelog-list">
    <li>Added new icons for datablock viewer and gde</li>
    <li>Update to settings.py for CUDA</li>
    <li>Added string highlighting in script editor</li>
    <li>JacobianCalculator bugfix due to Enno</li>
    <li>Various small bugfixes and improvements</li>
</ul>

<h3 class="changelog-header">Version 1.18.2</h3>
<p class="changelog-date">Mon Mar 16 11:50:41 2015</p>
<ul class="changelog-list">
    <li>Removed last traces of previous GUI</li>
    <li>Fixes to output capturing so that it works on windows</li>
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 1.18.1</h3>
<p class="changelog-date">Sun Mar 15 11:44:36 2015</p>
<ul class="changelog-list">
    <li>New IDE seems stable</li>
    <li>Added monkey patch for os.popen issue on windows</li>
</ul>

<h3 class="changelog-header">Version 1.18.0</h3>
<p class="changelog-date">Sat Mar 14 02:23:33 2015</p>
<ul class="changelog-list">
    <li>Completely new GUI in QT instead of WX, should solve mac problems,
     improve performance throughout</li>
    <li>Integrated GDE with Myokit classes</li>
    <li>Updated docs for command line tools</li>
    <li>Dropping idea of supporting msvc9 compiler on windows. Too many
     issues.</li>
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 1.17.4</h3>
<p class="changelog-date">Mon Mar 9 15:26:30 2015</p>
<ul class="changelog-list">
    <li>Bugfix in settings.py</li>
</ul>

<h3 class="changelog-header">Version 1.17.3</h3>
<p class="changelog-date">Mon Mar 9 15:16:15 2015</p>
<ul class="changelog-list">
    <li>GDE is now a part of Myokit</li>
    <li>Added "monkey patch" for old windows compilers</li>
    <li>Some changes for C89 compatibility</li>
</ul>

<h3 class="changelog-header">Version 1.17.1</h3>
<p class="changelog-date">Thu Mar 5 23:00:33 2015</p>
<ul class="changelog-list">
    <li>SI units named after people are now also accepted when capitalized.
    Never used for output in this fashion.</li>
</ul>

<h3 class="changelog-header">Version 1.17.0</h3>
<p class="changelog-date">Thu Mar 5 18:35:19 2015</p>
<ul class="changelog-list">
    <li>Now allowing (but not guaranteeing correctness of) arbitrary
     connections in OpenCL sim</li>
    <li>Various improvements and bugfixes</li>
</ul>

<h3 class="changelog-header">Version 1.16.3</h3>
<p class="changelog-date">Wed Feb 25 17:43:48 2015</p>
<ul class="changelog-list">
    <li>Added Quantity class for number-with-unit arithmetic</li>
    <li>Fix to cellml export of dimensionless variables with a multiplier</li>
    <li>Various small bugfixes and improvements</li>
</ul>

<h3 class="changelog-header">Version 1.16.2</h3>
<p class="changelog-date">Sun Feb 22 20:47:28 2015</p>
<ul class="changelog-list">
    <li>Added current calculating method to Markov model class</li>
    <li>Added on multi-model experiment convenience classes</li>
</ul>

<h3 class="changelog-header">Version 1.16.1</h3>
<p class="changelog-date">Thu Feb 19 18:48:08 2015</p>
<ul class="changelog-list">
    <li>Binds and labels now share a namespace</li>
</ul>

<h3 class="changelog-header">Version 1.16.0</h3>
<p class="changelog-date">Thu Feb 19 18:11:48 2015</p>
<ul class="changelog-list">
    <li>Added unit conversion method to unit class</li>
    <li>Various small bugfixes and improvements</li>
</ul>

<h3 class="changelog-header">Version 1.15.0</h3>
<p class="changelog-date">Thu Feb 5 21:33:58 2015</p>
<ul class="changelog-list">
<li>Releasing 1.15.0</li>
    <li>Various small bugfixes and improvements</li>
</ul>

<h3 class="changelog-header">Version 1.14.2</h3>
<p class="changelog-date">Mon Feb 2 13:19:20 2015</p>
<ul class="changelog-list">
    <li>Added NaN check to PSimulation</li>
    <li>Added on model comparison method</li>
    <li>Nicer output of numbers in expressions and unit quantifiers</li>
    <li>Tiny fixes in Number representation and GUI</li>
    <li>Imrpoved video generation script</li>
    <li>Various small bugfixes and improvements</li>
</ul>

<h3 class="changelog-header">Version 1.14.1</h3>
<p class="changelog-date">Sun Jan 25 23:18:57 2015</p>
<ul class="changelog-list">
    <li>Added partial validation to Markov model class</li>
    <li>Moved OpenCLInfo into separate object</li>
    <li>GUI now shows remaining time during experiment.</li>
    <li>Various small bugfixes and improvements</li>
</ul>

<h3 class="changelog-header">Version 1.14.0</h3>
<p class="changelog-date">Fri Jan 16 15:25:38 2015</p>
<ul class="changelog-list">
    <li>Added Alt-1,2,3 tab switching to GUI</li>
    <li>Updates to DataLog</li>
    <li>Fixed opencl issue: constant memory is limited, using __constant for parameter
    fields can give a strange error (invalid_kernel_args instead of out of memory
    errors). Fixed this by chaning __constant to __global.</li>
    <li>Various small bugfixes and improvements</li>
</ul>

<h3 class="changelog-header">Version 1.13.2</h3>
<p class="changelog-date">Fri Dec 5 17:58:47 2014</p>
<ul class="changelog-list">
    <li>Various improvements and bugfixes</li>
</ul>

<h3 class="changelog-header">Version 1.13.1</h3>
<p class="changelog-date">Wed Dec 3 12:03:22 2014</p>
<ul class="changelog-list">
    <li>Fixed a bug with fixed interval logging in CVODE sim</li>
</ul>

<h3 class="changelog-header">Version 1.13.0</h3>
<p class="changelog-date">Sun Nov 30 14:59:20 2014</p>
<ul class="changelog-list">
    <li>Checked all load/save methods for expanduser() after issues during demo in Gent</li>
    <li>Changed model.var_by_label() to model.label()</li>
    <li>Added option to show variables dependent on selected var</li>
    <li>Added support for reading WinWCP files</li>
    <li>Various improvements and bugfixes</li>
</ul>

<h3 class="changelog-header">Version 1.12.2</h3>
<p class="changelog-date">Wed Nov 19 09:04:00 2014</p>
<ul class="changelog-list">
    <li>Added parse_model() etc methods to parser</li>
    <li>Made sure protocol is cloned in all simulations. Protocols are not immutable
    and changes made after setting the protocol should not affect the simulation
    (or vice versa).</li>
    <li>Added a simulation that calculates the derivative of a state
    w.r.t. a parameter</li>
    <li>Working on MarkovModel class</li>
    <li>Added method to convert monodomain parameters to conductances to opencl
    simulation</li>
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 1.12.1</h3>
<p class="changelog-date">Sat Nov 8 12:59:03 2014</p>
<ul class="changelog-list">
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 1.12.0</h3>
<p class="changelog-date">Fri Nov 7 18:21:21 2014</p>
<ul class="changelog-list">
    <li>Added ATF support</li>
    <li>Added a Python-based PacingSystem to evaluate protocols over time in
    Python</li>
    <li>Added Protocol to SimulationLog conversion</li>
    <li>Improvements to GUI classes</li>
    <li>Added protocol preview to GUI</li>
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 1.11.13</h3>
<p class="changelog-date">Tue Nov 4 17:15:59 2014</p>
<ul class="changelog-list">
    <li>Fixed memory use and halting issue in lib.fit</li>
    <li>Fixed bug in aux.run(). APDs are now returned in SimulationLogs instead of
    plain dicts. This allows saving as csv and is more consistent with what users
    would expect the simulation to return.</li>
</ul>

<h3 class="changelog-header">Version 1.11.12</h3>
<p class="changelog-date">Mon Nov 3 13:20:48 2014</p>
<ul class="changelog-list">
    <li>Bugfix in PSO code: Initial positions weren't set properly, could end up
    out of bounds</li>
</ul>

<h3 class="changelog-header">Version 1.11.11</h3>
<p class="changelog-date">Thu Oct 30 16:53:53 2014</p>
<ul class="changelog-list">
    <li>Made threaded run() an option in settings.py</li>
</ul>

<h3 class="changelog-header">Version 1.11.10</h3>
<p class="changelog-date">Thu Oct 30 14:36:32 2014</p>
<ul class="changelog-list">
    <li>Added quick figure method to abf</li>
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 1.11.9</h3>
<p class="changelog-date">Sat Oct 18 14:57:55 2014</p>
<ul class="changelog-list">
    <li>Added PySilence context manager, made CSilence extend it</li>
    <li>Myokit.run() now runs the script inside a separate thread. This allows
    sys.exit() to be used in a script</li>
    <li>myokit.run() now handles exceptions correctly</li>
    <li>Various improvements and bugfixes</li>
</ul>

<h3 class="changelog-header">Version 1.11.8</h3>
<p class="changelog-date">Fri Oct 17 13:00:04 2014</p>
<ul class="changelog-list">
    <li>Added rectangular grid mapping of parameter spaces</li>
    <li>Removed custom open dialog from GUI</li>
    <li>Various improvements and bugfixes</li>
</ul>

<h3 class="changelog-header">Version 1.11.7</h3>
<p class="changelog-date">Tue Oct 14 16:00:18 2014</p>
<ul class="changelog-list">
    <li>Added jacobian examples. Fixed bug with class_exist() in php (argument
     should be string).</li>
    <li>Various improvements and bugfixes</li>
</ul>

<h3 class="changelog-header">Version 1.11.6</h3>
<p class="changelog-date">Fri Oct 10 18:38:28 2014</p>
<ul class="changelog-list">
    <li>Added parallelized particle search optimization method (PSO)</li>
    <li>Made linear system solving much faster</li>
    <li>Looked at using matrix exponentials in markov model code, over 1000
    times slower than eigenvalue method!</li>
    <li>Added method to draw colored Voronoi diagram</li>
    <li>Further annotated the example files</li>
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 1.11.5</h3>
<p class="changelog-date">Wed Sep 24 15:52:50 2014</p>
<ul class="changelog-list">
    <li>Added note about csv import to SimulationLog.save_csv</li>
    <li>Added publications to website. Uploaded hand-outs for workshop</li>
    <li>Updated gde version to 1.3.0</li>
</ul>

<h3 class="changelog-header">Version 1.11.4</h3>
<p class="changelog-date">Mon Sep 22 22:03:55 2014</p>
<ul class="changelog-list">
    <li>Added hyperbolic functions to cellml import</li>
    <li>Updated cellml import: Unused variables without an rhs are now removed, used
    variables without an rhs are given an automatic rhs of 0. Both cases generate a
    warning.</li>
    <li>Update to cellml import: If a variable is mentioned but never declared (i.e. if
    it is an external input) a dummy variable is now created and a warning is
    given.</li>
    <li>Added method to myo to get version number</li>
    <li>Fixed string encoding issue in CellML import</li>
    <li>Tweaks to the gui based on workshop feedback</li>
    <li>Fixed windows issue: IE likes to download .cellml files as .xml, making them
    invisible to the gui. Added a glob rule for .xml to the cellml import in the
    gui.</li>
</ul>

<h3 class="changelog-header">Version 1.11.3</h3>
<p class="changelog-date">Fri Sep 19 12:50:35 2014</p>
<ul class="changelog-list">
<li>Moving to next version</li>
<li>Small bugfixes and a variable.value() method.</li>
<li>Releasing version 1.11.3</li>
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 1.11.2</h3>
<p class="changelog-date">Thu Sep 18 02:37:34 2014</p>
<ul class="changelog-list">
<li>Releasing version 1.11.2</li>
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 1.11.1</h3>
<p class="changelog-date">Thu Sep 18 02:10:28 2014</p>
<ul class="changelog-list">
    <li>Added a formatting option to the Benchmarker</li>
    <li>Fixed OS/X GUI issues with progress bar</li>
</ul>

<h3 class="changelog-header">Version 1.11.0</h3>
<p class="changelog-date">Mon Sep 15 19:50:09 2014</p>
<ul class="changelog-list">
    <li>Adding Sympy to formats list</li>
    <li>Added sympy exporter and importer</li>
    <li>Added LinearModel class for working with markov models</li>
</ul>

<h3 class="changelog-header">Version 1.10.3</h3>
<p class="changelog-date">Thu Sep 11 17:17:33 2014</p>
<ul class="changelog-list">
    <li>Now raising exception when user cancels simulation instead of silent exit</li>
    <li>Added zero-step detection to cvode sim that now raises a SimulationError after
    too many consecutive zero steps.</li>
</ul>

<h3 class="changelog-header">Version 1.10.2</h3>
<p class="changelog-date">Wed Sep 10 05:13:29 2014</p>
<ul class="changelog-list">
    <li>Improvement debugging in the GUI: Now shows line numbers of error in script</li>
</ul>

<h3 class="changelog-header">Version 1.10.1</h3>
<p class="changelog-date">Mon Sep 8 18:55:43 2014</p>
<ul class="changelog-list">
    <li>Fixed bug in error handling</li>
</ul>

<h3 class="changelog-header">Version 1.10.0</h3>
<p class="changelog-date">Sat Aug 30 01:33:52 2014</p>
<ul class="changelog-list">
    <li>Added Windows installer</li>
</ul>

<h3 class="changelog-header">Version 1.9.11</h3>
<p class="changelog-date">Fri Aug 29 14:21:37 2014</p>
<ul class="changelog-list">
    <li>Updates to Windows install script</li>
</ul>

<h3 class="changelog-header">Version 1.9.10</h3>
<p class="changelog-date">Wed Aug 27 01:23:41 2014</p>
<ul class="changelog-list">
    <li>Added (valid) CellML export</li>
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 1.9.9</h3>
<p class="changelog-date">Tue Aug 26 00:54:45 2014</p>
<ul class="changelog-list">
    <li>Added update script</li>
</ul>

<h3 class="changelog-header">Version 1.9.8</h3>
<p class="changelog-date">Mon Aug 25 01:35:05 2014</p>
<ul class="changelog-list">
    <li>Various improvements and bugfixes</li>
</ul>

<h3 class="changelog-header">Version 1.9.7</h3>
<p class="changelog-date">Thu Aug 21 12:59:45 2014</p>
<ul class="changelog-list">
    <li>Fixed bug with dialogs on OS/X</li>
    <li>Bundled all scripts into a single script "myo"</li>
    <li>Updated installation script for Windows</li>
</ul>

<h3 class="changelog-header">Version 1.9.6</h3>
<p class="changelog-date">Tue Aug 19 13:51:14 2014</p>
<ul class="changelog-list">
    <li>Fixed bug with dialogs on OS/X</li>
</ul>

<h3 class="changelog-header">Version 1.9.5</h3>
<p class="changelog-date">Thu Aug 14 17:30:05 2014</p>
<ul class="changelog-list">
    <li>Added device info to OpenCL debug output</li>
    <li>Improved memory handling in OpenCL simulations</li>
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 1.9.4</h3>
<p class="changelog-date">Wed Aug 13 09:11:36 2014</p>
<ul class="changelog-list">
    <li>Added a script that installs a desktop icon for the gui under Windows</li>
    <li>Added a global readme.txt</li>
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 1.9.3</h3>
<p class="changelog-date">Fri Aug 8 18:27:19 2014</p>
<ul class="changelog-list">
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 1.9.2</h3>
<p class="changelog-date">Fri Aug 1 15:10:05 2014</p>
<ul class="changelog-list">
    <li>Improved ABF support</li>
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 1.9.1</h3>
<p class="changelog-date">Thu Jul 31 13:11:48 2014</p>
<ul class="changelog-list">
    <li>Bugfix in GUI for Windows</li>
</ul>

<h3 class="changelog-header">Version 1.9.0</h3>
<p class="changelog-date">Thu Jul 31 01:43:53 2014</p>
<ul class="changelog-list">
    <li>Added stable point finding method</li>
    <li>Added icons for windows version</li>
    <li>Rebranding as 'Myokit' (with capital M, no more mention
    of the "Maastricht Myocyte Toolkit")</li>
    <li>Changed license to GPL</li>
</ul>

<h3 class="changelog-header">Version 1.8.1</h3>
<p class="changelog-date">Wed Jul 16 09:45:46 2014</p>
<ul class="changelog-list">
    <li>Various improvements and bugfixes</li>
</ul>

<h3 class="changelog-header">Version 1.8.0</h3>
<p class="changelog-date">Wed Jul 16 01:28:36 2014</p>
<ul class="changelog-list">
    <li>Updates to website</li>
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 1.7.5</h3>
<p class="changelog-date">Thu Jul 10 23:44:44 2014</p>
<ul class="changelog-list">
    <li>Added method to fold log periodically (based on split_periodic)</li>
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 1.7.4</h3>
<p class="changelog-date">Tue Jul 8 17:30:13 2014</p>
<ul class="changelog-list">
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 1.7.3</h3>
<p class="changelog-date">Mon Jul 7 18:14:49 2014</p>
<ul class="changelog-list">
    <li>Reinstated logging of derivatives in CVODE simulation</li>
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 1.7.2</h3>
<p class="changelog-date">Mon Jul 7 04:01:56 2014</p>
<ul class="changelog-list">
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 1.7.1</h3>
<p class="changelog-date">Mon Jul 7 03:32:53 2014</p>
<ul class="changelog-list">
    <li>Added load/save methods to DataBlock1d</li>
    <li>Made ICSimulation work with DataBlock2d to calculate eigenvalues</li>
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 1.7.0</h3>
<p class="changelog-date">Fri Jul 4 23:43:33 2014</p>
<ul class="changelog-list">
    <li>Added a JacobianGenerator class</li>
    <li>Added a simulation that integrates partial derivatives to find the
    derivatives of the state w.r.t. the initial conditions</li>
    <li>Added latex export</li>
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 1.6.2</h3>
<p class="changelog-date">Wed Jun 18 02:07:47 2014</p>
<ul class="changelog-list">
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 1.6.1</h3>
<p class="changelog-date">Fri Jun 13 16:57:02 2014</p>
<ul class="changelog-list">
    <li>Added IV curve experiment</li>
    <li>Improved error detection in CVODE simulation.</li>
</ul>

<h3 class="changelog-header">Version 1.6.0</h3>
<p class="changelog-date">Fri Jun 6 21:03:26 2014</p>
<ul class="changelog-list">
    <li>Added a diffusion on/off switch to the OpenCL simulation</li>
    <li>The OpenCL sim can now replace constants by scalar fields. This allows
     it to be used to test parameter influence or to simulate
     heterogeneity.</li>
</ul>

<h3 class="changelog-header">Version 1.5.2</h3>
<p class="changelog-date">Wed Jun 4 17:59:58 2014</p>
<ul class="changelog-list">
    <li>Better handling of unknown units</li>
    <li>Added eval_state_derivs option to GUI</li>
    <li>Added trim trailing whitespace method to gui</li>
    <li>Gui and step script now show numerical errors if they occur</li>
    <li>Added trim() and itrim() methods to simulation log</li>
    <li>Added a 2-variable parameter range exploration class</li>
    <li>DataBlock viewer now can export frames and graphs</li>
    <li>Various improvements and bugfixes</li>
</ul>

<h3 class="changelog-header">Version 1.5.1</h3>
<p class="changelog-date">Thu May 8 16:27:25 2014</p>
<ul class="changelog-list">
    <li>Added method model.set_name()</li>
    <li>Updated installer script for GNOME/KDE.</li>
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 1.5.0</h3>
<p class="changelog-date">Thu Apr 24 12:42:08 2014</p>
<ul class="changelog-list">
    <li>Added on Strength-Duration experiment</li>
    <li>Added method to create cumulative current/charge plots</li>
</ul>

<h3 class="changelog-header">Version 1.4.8</h3>
<p class="changelog-date">Tue Apr 22 17:50:48 2014</p>
<ul class="changelog-list">
    <li>Changed SimulationLog.integrate() to use left-point rule instead of
    midpoint rule. This makes much more sense for the stimulus current when
    using CVODE.</li>
    <li>Various improvements and bugfixes</li>
</ul>

<h3 class="changelog-header">Version 1.4.7</h3>
<p class="changelog-date">Thu Apr 17 13:14:09 2014</p>
<ul class="changelog-list">
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 1.4.6</h3>
<p class="changelog-date">Thu Apr 10 18:17:35 2014</p>
<ul class="changelog-list">
    <li>Added RestitutionExperiment to lib.common</li>
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 1.4.5</h3>
<p class="changelog-date">Mon Apr 7 18:51:25 2014</p>
<ul class="changelog-list">
    <li>Re-organised code</li>
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 1.4.4</h3>
<p class="changelog-date">Thu Mar 27 22:08:43 2014</p>
<ul class="changelog-list">
    <li>Various improvements and bugfixes</li>
</ul>

<h3 class="changelog-header">Version 1.4.3</h3>
<p class="changelog-date">Mon Mar 17 20:58:48 2014</p>
<ul class="changelog-list">
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 1.4.2</h3>
<p class="changelog-date">Tue Mar 11 11:34:50 2014</p>
<ul class="changelog-list">
    <li>Added unit methods to Gui.</li>
    <li>Updated the installation guide.</li>
    <li>Added method to 'walk' over the operands in an expression, depth-first</li>
    <li>Added a few default unit representations</li>
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 1.4.0</h3>
<p class="changelog-date">Tue Feb 18 17:33:44 2014</p>
<ul class="changelog-list">
    <li>Added unit checking methods</li>
    <li>Improved CellML unit reading from constants</li>
    <li>Added pack_snapshot() method that creates a copy of the current Myokit version</li>
    <li>Created DataBlock classes for alternative view of rectangular simulation data</li>
    <li>Added GUI for viewing 1D and 2D simulation data</li>
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 1.2.0</h3>
<p class="changelog-date">Mon Jan 27 14:35:57 2014</p>
<ul class="changelog-list">
    <li>Changed [[plot]] to [[script]]</li>
    <li>Various improvements and bugfixes</li>
</ul>

<h3 class="changelog-header">Version 1.1.0</h3>
<p class="changelog-date">Fri Jan 24 16:49:08 2014</p>
<ul class="changelog-list">
    <li>Updated interface of opencl simulations</li>
    <li>Added OpenCL-based parameter RangeTester class</li>
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 1.0.2</h3>
<p class="changelog-date">Thu Jan 9 15:31:48 2014</p>
<ul class="changelog-list">
    <li>Updates to documentation</li>
</ul>

<h3 class="changelog-header">Version 1.0.0</h3>
<p class="changelog-date">Tue Dec 24 20:53:55 2013</p>
<ul class="changelog-list">
    <li>Improved documentation</li>
    <li>Added a 'running simulations' guide.</li>
    <li>Added SymPy export</li>
    <li>Added unit tests</li>
    <li>Added binary format for simulation logs</li>
    <li>Aliases are now retained in model export</li>
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 0.17.2</h3>
<p class="changelog-date">Thu Dec 19 11:52:00 2013</p>
<ul class="changelog-list">
    <li>Improved documentation</li>
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 0.17.1</h3>
<p class="changelog-date">Thu Dec 19 11:47:13 2013</p>
<ul class="changelog-list">
    <li>New model syntax, model stars with: [[model]]</li>
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 0.17.0</h3>
<p class="changelog-date">Wed Dec 11 23:44:17 2013</p>
<ul class="changelog-list">
    <li>Added binary version of save_state and load_state</li>
    <li>Added ProgressPrinter to show progress during long simulations</li>
    <li>Added precision switch to prepare_log and load_csv</li>
    <li>Added method to find solvable equations dependent on one or more variables.</li>
    <li>Improved support for ABF protocol and data reading</li>
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 0.16.3</h3>
<p class="changelog-date">Wed Nov 6 12:23:19 2013</p>
<ul class="changelog-list">
    <li>Improved OpenCL simulation error output</li>
    <li>Various improvements and bugfixes</li>
</ul>

<h3 class="changelog-header">Version 0.16.2</h3>
<p class="changelog-date">Fri Nov 1 22:00:13 2013</p>
<ul class="changelog-list">
    <li>Improvements to GUI</li>
    <li>Improved find_nan method in OpenCL sim</li>
    <li>Added method to expression's eval() to evaluate with numpy.Float32
        objects. This helps finding the source of OpenCL single-precision
        NaN errors.</li>
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 0.16.1</h3>
<p class="changelog-date">Thu Oct 31 18:10:26 2013</p>
<ul class="changelog-list">
    <li>Refactored code, reduced size of giant modules.</li>
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 0.16.0</h3>
<p class="changelog-date">Thu Oct 31 01:52:44 2013</p>
<ul class="changelog-list">
    <li>Added recovery-from-inactivation experiment</li>
    <li>Updated ActivationExperiment, added boltzmann fit</li>
    <li>Added boltzmann fit to InactivationExperiment</li>
    <li>Added time constant of activation method to ActivationExperiment.</li>
    <li>Rewrote unit system</li>
    <li>Various improvements and bugfixes</li>
</ul>

<h3 class="changelog-header">Version 0.15.9</h3>
<p class="changelog-date">Tue Oct 22 11:40:13 2013</p>
<ul class="changelog-list">
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 0.15.8</h3>
<p class="changelog-date">Wed Oct 16 16:48:04 2013</p>
<ul class="changelog-list">
    <li>Slight optimizations in OpenCL code</li>
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 0.15.7</h3>
<p class="changelog-date">Tue Oct 15 18:22:07 2013</p>
<ul class="changelog-list">
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 0.15.6</h3>
<p class="changelog-date">Tue Oct 15 15:36:34 2013</p>
<ul class="changelog-list">
    <li>Updated step method to accept models as reference</li>
    <li>Reinstated model.load_state() method</li>
    <li>Imrpoved find dialog</li>
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 0.15.5</h3>
<p class="changelog-date">Mon Oct 14 21:14:14 2013</p>
<ul class="changelog-list">
    <li>Added quick var info to gui</li>
    <li>Renamed 'current_diff' to 'diffusion_current'</li>
</ul>

<h3 class="changelog-header">Version 0.15.4</h3>
<p class="changelog-date">Sat Oct 12 17:36:27 2013</p>
<ul class="changelog-list">
    <li>Added on ChanneML import</li>
    <li>FiberTissueSimulation now works with 2D fibers</li>
</ul>

<h3 class="changelog-header">Version 0.15.2</h3>
<p class="changelog-date">Thu Oct 10 21:40:07 2013</p>
<ul class="changelog-list">
    <li>Added data extraction features to abf format</li>
    <li>Added on Fiber-Tissue simulation class</li>
    <li>Various improvements and bugfixes</li>

</ul>
<h3 class="changelog-header">Version 0.15.0</h3>
<p class="changelog-date">Wed Sep 18 14:58:30 2013</p>
<ul class="changelog-list">
    <li>Number of cells to pace can now be set in OpenCLCableSimulation</li>
    <li>Added function to find origin of NaN errors in an
     OpenCLCableSimulation</li>
    <li>Updated SimulationLog to return mesh grid for pyplot</li>
    <li>Added 1D CV calculation to SimulationLog</li>
    <li>Renamed cable simulation classes.</li>
    <li>Made 1D OpenCL Simulation suitable for 2D use</li>
    <li>Added method to list component cycles</li>
    <li>Added a method that checks which variables cause mutually dependent
     components</li>
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 0.14.1</h3>
<p class="changelog-date">Fri Aug 23 17:01:35 2013</p>
<ul class="changelog-list">
    <li>Fixed direction convention for diffusion current</li>
    <li>Simulation log now has local and global variables (for multi-cell
     simulations)</li>
    <li>Added OpenCL export</li>
    <li>Added a C header file with pacing functions, shared by several
     simulations</li>
    <li>Added a settings file settings.py</li>
    <li>Added OpenCL simulation object</li>
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 0.14.0</h3>
<p class="changelog-date">Fri Jul 19 18:34:28 2013</p>
<ul class="changelog-list">
    <li>Various performance boosts</li>
    <li>Rewrite of expression classes</li>
    <li>Improved parser</li>
    <li>Added options to move variables, delete variables</li>
    <li>Improved model.clone() method</li>
    <li>Added strand simulations via Python interface</li>
    <li>Various improvements and bugfixes</li>
</ul>

<h3 class="changelog-header">Version 0.13.9</h3>
<p class="changelog-date">Thu Jun 6 15:42:11 2013</p>
<ul class="changelog-list">
    <li>Working CUDA kernel export</li>
</ul>

<h3 class="changelog-header">Version 0.13.8</h3>
<p class="changelog-date">Thu Jun 6 15:38:24 2013</p>
<ul class="changelog-list">
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 0.13.7</h3>
<p class="changelog-date">Thu Jun 6 13:23:03 2013</p>
<ul class="changelog-list">
    <li>Added simple ansi-c forward euler export.</li>
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 0.13.6</h3>
<p class="changelog-date">Fri May 31 18:20:00 2013</p>
<ul class="changelog-list">
    <li>Added progress bars to explorer in gui (F6)</li>
    <li>Worked on dependency graphs</li>
    <li>Added meta data to components</li>
    <li>Added option to simulationlog to split into periodic pieces</li>
    <li>Various improvements and bugfixes</li>
</ul>

<h3 class="changelog-header">Version 0.13.5</h3>
<p class="changelog-date">Thu May 23 20:53:10 2013</p>
<ul class="changelog-list">
    <li>Various improvements and bugfixes</li>
</ul>

<h3 class="changelog-header">Version 0.13.4</h3>
<p class="changelog-date">Thu May 23 00:06:55 2013</p>
<ul class="changelog-list">
    <li>Made engine.realtime contain the elapsed system time, not the absolute
     system time.</li>
    <li>Made SimulationLog suitable for multi-dimensional data.</li>
    <li>Added StrandSimulation object</li>
    <li>Added Graph Data Extractor</li>
    <li>Added RhsBenchmarker</li>
    <li>Began work on CUDA export</li>
    <li>Added Coffman-Graham algorithm for directed acyclic graph layer
     assignment.</li>
    <li>Added get_last_number_of_evaluations() method to Simulation</li>
    <li>Various updates to the documentation</li>
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 0.13.0</h3>
<p class="changelog-date">Thu Mar 28 02:21:09 2013</p>
<ul class="changelog-list">
    <li>Added export to strand/fiber simulation in ansi-c</li>
    <li>Added syntax for binding to external values</li>
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 0.12.7</h3>
<p class="changelog-date">Wed Feb 27 18:18:26 2013</p>
<ul class="changelog-list">
    <li>Added plotting methods.</li>
    <li>Added benchmarking to simulation.</li>
    <li>Various improvements and bugfixes</li>
</ul>

<h3 class="changelog-header">Version 0.12.6</h3>
<p class="changelog-date">Tue Feb 26 14:37:23 2013</p>
<ul class="changelog-list">
    <li>Refactored myokit.lib</li>
    <li>Added APD calculating function</li>
    <li>Added APD measurement to simulation using cvode's root finding</li>
    <li>Added padding function to save_csv</li>
    <li>Created SimulationLog class</li>
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 0.12.4</h3>
<p class="changelog-date">Wed Feb 20 16:01:55 2013</p>
<ul class="changelog-list">
    <li>Refactored import/export modules</li>
    <li>Updated documentation</li>
    <li>Added method to interpolate logged results</li>
    <li>Improved performance in CVODE simulations</li>
    <li>Added periodic logging option to simulation</li>
    <li>Improved Explorer GUI</li>
    <li>Added method to run euler/rk4 simulations</li>
    <li>Added OrderedPiecewise class</li>
    <li>Added progress bar to gui</li>
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 0.10.8</h3>
<p class="changelog-date">Tue Jan 15 14:55:31 2013</p>
<ul class="changelog-list">
    <li>Bugfix in metadata export</li>
</ul>

<h3 class="changelog-header">Version 0.10.7</h3>
<p class="changelog-date">Tue Jan 15 14:45:32 2013</p>
<ul class="changelog-list">
    <li>Various improvements and bugfixes</li>
</ul>

<h3 class="changelog-header">Version 0.10.6</h3>
<p class="changelog-date">Tue Jan 15 00:31:58 2013</p>
<ul class="changelog-list">
    <li>Rewrote cellml import</li>
    <li>Worked on methods to fit simplify functions</li>
    <li>Updates to mmt syntax</li>
    <li>Added multi-line comments to mmt syntax</li>
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 0.10.5</h3>
<p class="changelog-date">Mon Nov 12 14:56:57 2012</p>
<ul class="changelog-list">
    <li>Added tests</li>
    <li>Added piecewise() expressions</li>
    <li>Various improvements and bugfixes</li>
</ul>

<h3 class="changelog-header">Version 0.10.3</h3>
<p class="changelog-date">Tue Oct 30 12:04:10 2012</p>
<ul class="changelog-list">
    <li>Improved import and export interfaces</li>
    <li>Added save_state() method</li>
    <li>Improved documentation</li>
    <li>Conversion of Myokit expressions to Python functions</li>
    <li>Added benchmarking methods</li>
    <li>Implemented unit parsing</li>
    <li>Added SBML import</li>
    <li>Added methods for function simplification (via approximations)</li>
    <li>Introduced website</li>
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 0.9.17</h3>
<p class="changelog-date">Fri Jul 27 18:19:05 2012</p>
<ul class="changelog-list">
    <li>Added local aliases to syntax</li>
    <li>Simplified syntax</li>
    <li>Simulation and gui now allow unlogged pacing</li>
    <li>Added search function to GUI</li>
    <li>Templating based exports, available from GUI</li>
    <li>Import of CellML metadata</li>
    <li>Added protocol wizard to GUI</li>
    <li>Added simple component dependency graph to GUI</li>
    <li>Added model debug options</li>
    <li>Added matlab export</li>
    <li>Three-section mmt file introduced</li>
    <li>ABF protocol import</li>
    <li>Added Sphinx-based documentation</li>
    <li>Added routine that shows sizes of integrator steps</li>
    <li>Various small bugfixes</li>
</ul>

<h3 class="changelog-header">Version 0.9.0</h3>
<p class="changelog-date">Mon Mar 12 17:46:45 2012</p>
<ul class="changelog-list">
    <li>First mmt syntax, parser and model classes</li>
    <li>Initial CellML import</li>
    <li>C++ export</li>
    <li>Ansi-C export, python export</li>
    <li>Beat script that uses generated ansi-c and CVODE, compiled on the
     fly</li>
    <li>First working GUI</li>
</ul>

<h3 class="changelog-header">Version 0.0.0</h3>
<p class="changelog-date">Mon Dec 19 11:08:50 2011</p>
<ul>
    <li>Working on simple model syntax, parser and export to C++</li>
</ul>

