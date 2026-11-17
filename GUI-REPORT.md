# GUI and command-line unit tests: report

This report describes the new unit tests for `myokit.gui` and `myokit/__main__.py`, the bugs they uncovered, and how those bugs were fixed.

## Summary

- **New test files:** nine, one per module in `myokit.gui` plus one for `myokit/__main__.py`, adding 171 tests. Each file holds a single `unittest.TestCase` and uses only `unittest` and `unittest.mock`.
- **Bugs found and fixed:** about 45, across the GUI, the command-line tool, `myokit.lib.deps` and the ABF reader.
- **Current state:** the full suite (`python -m myokit test unit`) runs 1578 tests: all OK, 67 skipped. `ruff check` is clean.

## Test files

| Test file | Tests | Module under test |
|---|---|---|
| `test_gui.py` | 5 | `myokit/gui/__init__.py` |
| `test_gui_progress.py` | 3 | `myokit/gui/progress.py` |
| `test_gui_explorer.py` | 5 | `myokit/gui/explorer.py` |
| `test_gui_vargrapher.py` | 5 | `myokit/gui/vargrapher.py` |
| `test_gui_source.py` | 30 | `myokit/gui/source.py` |
| `test_gui_datalog_viewer.py` | 20 | `myokit/gui/datalog_viewer.py` |
| `test_gui_datablock_viewer.py` | 36 | `myokit/gui/datablock_viewer.py` |
| `test_gui_ide.py` | 35 | `myokit/gui/ide.py` |
| `test_main.py` | 32 | `myokit/__main__.py` |

Existing test files that gained tests for the fixes:

- `test_lib_deps.py`: path matrices and single-state models.
- `test_formats_axon.py`: the error message for an unknown ABF version.

## How the tests run

### Headless Qt

`myokit/tests/__init__.py` has a new helper, `qt_application()`.

- It imports `myokit.gui`. If no Qt binding is installed, it raises `unittest.SkipTest`, so the GUI tests are skipped rather than failing.
- Importing `myokit.gui` changes matplotlib's backend, so the helper puts the backend back.
- If no `QApplication` exists yet, it creates one on the `offscreen` platform, so the tests need no display.

Each GUI test case calls the helper in `setUpClass`.

### Isolation

- **No blocking:** modal dialogs, file pickers, message boxes and `input()` are mocked.
- **No side effects:** subprocesses, OpenCL device selection and moviepy are mocked.
- **No user files touched:**
  - Settings files (`SETTINGS_FILE`) and `myokit.DIR_USER` are pointed at temporary directories, so `~/.config/myokit` is never read or written.
  - The commands that run tests, coverage or icon installation are run in a temporary working directory or with a temporary home directory.

### Command-line tests

`test_main.py` calls `myokit.__main__.main()` with a patched `sys.argv`. It captures output with `contextlib.redirect_stdout` and `redirect_stderr`, and catches `SystemExit`. Every sub-command and its help text is covered.

## Bugs found and fixed

Some bugs only came to light while the tests were being written. At first these were recorded as `# Note:` comments in the tests rather than asserted. After the fixes, every note was replaced with an assertion of the correct behavior.

### `myokit/gui/datalog_viewer.py`

- **`.dat` files:** none could be opened, because `myokit.formats.heka` was never imported. The import is added.
- **Text files:** the transpose test was backwards, and every tab plotted all the data instead of its own column, so a simple two-column (time, value) file crashed the viewer. Both are fixed.
- **`.mat` files:** arrays with unsupported shapes (square, 3-D, empty or non-numeric) were still plotted. They are now skipped.
- **CSV files:** after the "no time key" error, loading carried on. It now stops.
- **Errors in general:** an empty tab was still added after a load error.
  - A new `GraphTabWidget._fail()` deletes the half-built tab and raises `ValueError`.
  - The loaders catch that error, show it, and add no tab.
- **ATF info tab:** it used the deprecated `AtfFile.info()`. It now uses `meta_str()`.
- **Menu:** the "Next file" action was added to the menu twice.

### `myokit/gui/explorer.py`

- **Duplicate lines:** `action_draw` plotted all earlier runs again without removing the old lines, so lines piled up. Old lines are now removed first.

### `myokit/gui/ide.py`

- **Opening a `.cellml` file** given on the command line imported the model, then replaced it with an empty one.
- **Save-as to a folder that doesn't exist** raised an uncaught `FileNotFoundError`, because `os.chdir` was outside the `try`. It now shows an error and returns `False`.
- **Export** always printed "Export successful.", because the caught exception was never stored.
- **`action_model_stats`** showed the wrong failure message in the status bar.
- **`action_variable_graph`** carried on after showing its error, because of a missing `return`.
- **`protocol()`** checked its cache by truthiness, so a protocol with no events was parsed again every time. It now uses `is not None`.
- **`Console.write(None)`** crashed.

### `myokit/gui/source.py`

- **Ctrl+Shift+Home:** the check used `&` where it needed `|`.
- **Up/Down:** the remembered column went stale after other cursor moves, such as clicks, find or `jump_to`. Any move other than Up or Down now resets it.
- **Search settings:** `save_config` stored booleans rather than strings, which fails with a plain `ConfigParser`.
- **Bracket matching:** a bracket just behind the cursor was only matched at the end of the document. It now matches anywhere.
- **Highlighter colors:** the highlighter styles were only set once an `Editor` had been created. Each highlighter now sets them itself.
- **PageUp/PageDown:** on a small window they could move a negative distance. They now move at least one line.

### `myokit/gui/datablock_viewer.py`

- **Ctrl+C during a cancelled load:** a `return` inside a `finally` block swallowed the `KeyboardInterrupt`.
- **"No graphs to export":** this warning could never be shown, because the log always contains time.
- **Fit to view:** `fitInView` did not keep the aspect ratio, because `yr` was never set.
- **Frame slider:** its maximum was one frame too high.
- **`sizePolicy()`:** it referred to `QtCore.QSizePolicy`, which doesn't exist. It now uses `QtWidgets.QSizePolicy`.
- **Mouse-position label:** a `)` was missing.
- **Settings:** a non-integer value in the settings file crashed the viewer on start-up. Such values now fall back to the defaults.

### `myokit/__main__.py`

- **`read_model(silent=True)`** printed the "Reading" line, because the check was inverted.
- **`myokit step model.mmt -ref X --raw`** crashed, although the help text says `-ref` is ignored when `--raw` is used. It is now ignored.
- **`myokit icons` on Windows:** the `menu.json` template called `.replace()` on a `pathlib.Path`.
- **Documentation coverage:** the message for unknown functions said "classes".
- **`myokit video`:** the "key not found" message used `<key>` instead of quotes.
- **`myokit test mmt`** ignored files that failed to load. These now count as errors.
- **`myokit eval`** printed `str:x` for expressions that refer to variables. It now explains that this isn't possible.
- **Documentation scan:** it included `myokit.tests` if that package had been imported.

### `myokit/lib/deps.py`

- **`path_matrix`** had its `return` inside the loop, so it gave wrong results for any graph with more than one node, and returned `None` for an empty graph. This caused a crash on single-state models. **Results for graphs with more than one node change as a result.**
- **`meg_dag`'s cycle check** depended on the old behavior. It was updated to report nodes that refer to themselves separately from other cycles.
- **Empty graphs:** `cg_layers_dag` and `layout_layered` now handle them.
- **`plot_state_dependency_matrix`:**
  - It divided by zero on a single-state model.
  - It worked out the maximum weight from one row only, instead of the whole matrix.

### `myokit/formats/axon/_abf.py`

- **Line 375:** the "Unknown ABF Format" error message was missing its `f` prefix.

## Known remaining issues

- **Open file after a parse error:** `myokit.formats.heka.PatchMasterFile` leaves its file open when parsing fails. The test for loading a bad `.dat` file shows this as a `ResourceWarning`. It has not been fixed.
- **Tests that need warnings:** `test_main.test_export` and `test_main.test_import` check for printed warnings, so they fail if the suite is run with `-W ignore`.
