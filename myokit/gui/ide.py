#
# Graphical interface to myokit. Allows mmt files to be created, modified and
# run.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import configparser
import gc
import os
import sys
import textwrap
import traceback
import warnings

import myokit
import myokit.formats
import myokit.gui
import myokit.lib.deps
import myokit.lib.guess

from myokit.gui import QtWidgets, QtGui, QtCore, Qt

from . import source
from . import explorer
from . import progress
from . import vargrapher

# Matplotlib imports
# Matplotlib.pyplot must be imported _after_ myokit.gui has set the backend
import matplotlib
matplotlib.interactive(True)        # Allows plt.show()


# Application title
TITLE = 'Myokit IDE'

# Settings file
SETTINGS_FILE = os.path.join(myokit.DIR_USER, 'myokit-ide.ini')

# Number of recent files to display
N_RECENT_FILES = 5

# About
ABOUT = '<h1>' + TITLE + '</h1>' + """
<p>
    The Myokit IDE provides a user-friendly environment in which mmt files can
    be created, imported, modified and run.
</p>
<p>
    <a href="http://myokit.org">http://myokit.org</a>
</p>
<p>
    System info:
    <br />Python: PYTHON
    <br />Using the BACKEND GUI backend.
</p>
""".replace('BACKEND', myokit.gui.backend).replace('PYTHON', sys.version)

# File filters
# Note: Using the special filter MMT_SAVE with only one extension specified,
# the file save dialog will add the extension if the user didn't specify one.
FILTER_ALL = 'All files (*.*)'
FILTER_MMT_SAVE = 'Myokit mmt files (*.mmt)'
FILTER_MMT = 'Myokit mmt files (*.mmt);;' + FILTER_ALL

FILTER_ABF = 'Axon files (*.abf *.pro);; Axon Binary File (*.abf)' \
    + ';;Axon Protocol File (*.pro);;' + FILTER_ALL
FILTER_CELLML = 'CellML file (*.cellml *.xml);;' + FILTER_ALL
FILTER_CHANNELML = 'ChannelML file (*.channelml *.xml);;' + FILTER_ALL
FILTER_HTML = 'HTML file (*.html *.htm);;' + FILTER_ALL
FILTER_LATEX = 'Tex file (*.tex)' + FILTER_ALL
FILTER_SBML = 'SBML file (*.sbml *.xml)' + FILTER_ALL


# Application icon
def icon():
    icons = [
        'icon-ide.ico',
        'icon-ide-16.xpm',
        'icon-ide-24.xpm',
        'icon-ide-32.xpm',
        'icon-ide-48.xpm',
        'icon-ide-64.xpm',
        'icon-ide-96.xpm',
        'icon-ide-128.xpm',
        'icon-ide-256.xpm',
    ]
    icon = QtGui.QIcon()
    for i in icons:
        icon.addFile(os.path.join(myokit.DIR_DATA, 'gui', i))
    return icon


# Classes & functions
class MyokitIDE(myokit.gui.MyokitApplication):
    """
    New GUI for editing ``.mmt`` files.
    """
    def __init__(self, filename=None):
        super().__init__()

        # Regular expression for navigator
        self._nav_query = QtCore.QRegularExpression(
            r'^\[[a-zA-Z]{1}[a-zA-Z0-9_]*\]')

        # Set application icon
        self.setWindowIcon(icon())

        # Set size, center
        self.resize(950, 720)
        self.setMinimumSize(600, 440)
        qr = self.frameGeometry()
        cp = QtGui.QGuiApplication.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        # Status bar
        self._label_cursor = QtWidgets.QLabel()
        self.statusBar().addPermanentWidget(self._label_cursor)
        self.statusBar().showMessage('Ready')

        # Lists of widgets that are always visible/accessible (e.g. toolbar or
        # menu items) but are specific to the selected tab, so need
        # enabling/disabling depending on which tab is shown
        self._model_widgets = []
        self._protocol_widgets = []
        self._script_widgets = []

        # Menu bar
        self.create_menu()

        # Tool bar
        self.create_toolbar()

        # Create editors, highlighters, and search bars.
        # The highlighters need to be stored, because without a reference to
        # them the python part will be deleted and pyqt (not pyside) gets
        # confused.
        self._model_editor = source.Editor()
        self._model_highlighter = source.ModelHighlighter(
            self._model_editor.document())
        self._model_search = source.FindReplaceWidget(None, self._model_editor)
        self._model_search.find_action.connect(self.statusBar().showMessage)

        # Create protocol editor
        self._protocol_editor = source.Editor()
        self._protocol_highlighter = source.ProtocolHighlighter(
            self._protocol_editor.document())
        self._protocol_search = source.FindReplaceWidget(
            None, self._protocol_editor)
        self._protocol_search.find_action.connect(self.statusBar().showMessage)

        # Create script editor
        self._script_editor = source.Editor()
        self._script_highlighter = source.ScriptHighlighter(
            self._script_editor.document())
        self._script_search = source.FindReplaceWidget(
            None, self._script_editor)
        self._script_search.find_action.connect(self.statusBar().showMessage)

        # Create tool panels and populate tabs
        self._model_tools = TabbedToolBar()
        self._model_tools.tab_toggled.connect(self.change_tool_visibility)
        self._model_tools.add(self._model_search, 'Find/Replace')
        self._model_navigator = ModelNavigator()
        self._model_navigator.item_changed.connect(self.navigator_item_changed)
        self._model_tools.add(self._model_navigator, 'Components')

        self._protocol_tools = TabbedToolBar()
        self._protocol_tools.tab_toggled.connect(self.change_tool_visibility)
        self._protocol_tools.add(self._protocol_search, 'Find/Replace')

        self._script_tools = TabbedToolBar()
        self._script_tools.tab_toggled.connect(self.change_tool_visibility)
        self._script_tools.add(self._script_search, 'Find/Replace')

        # Create editor tabs
        self._model_tab = QtWidgets.QSplitter(Qt.Orientation.Horizontal)
        self._model_tab.editor = self._model_editor
        self._model_tab.search = self._model_search
        self._model_tab.addWidget(self._model_editor)
        self._model_tab.addWidget(self._model_tools)
        self._model_tab.setSizes([400, 100])
        self._model_tab.setCollapsible(0, False)
        self._model_tab.setCollapsible(1, False)

        self._protocol_tab = QtWidgets.QSplitter(Qt.Orientation.Horizontal)
        self._protocol_tab.editor = self._protocol_editor
        self._protocol_tab.search = self._protocol_search
        self._protocol_tab.addWidget(self._protocol_editor)
        self._protocol_tab.addWidget(self._protocol_tools)
        self._protocol_tab.setSizes([400, 100])
        self._protocol_tab.setCollapsible(0, False)
        self._protocol_tab.setCollapsible(1, False)

        self._script_tab = QtWidgets.QSplitter(Qt.Orientation.Horizontal)
        self._script_tab.editor = self._script_editor
        self._script_tab.search = self._script_search
        self._script_tab.addWidget(self._script_editor)
        self._script_tab.addWidget(self._script_tools)
        self._script_tab.setSizes([400, 100])
        self._script_tab.setCollapsible(0, False)
        self._script_tab.setCollapsible(1, False)

        self._editor_tabs = QtWidgets.QTabWidget()
        self._editor_tabs.addTab(self._model_tab, 'Model definition')
        self._editor_tabs.addTab(self._protocol_tab, 'Protocol definition')
        self._editor_tabs.addTab(self._script_tab, 'Embedded script')

        # Track changes in mmt file
        self._have_changes = False
        self._model_changed = False
        self._protocol_changed = False
        self._script_changed = False
        self._model_editor.modificationChanged.connect(
            self.change_modified_model)
        self._protocol_editor.modificationChanged.connect(
            self.change_modified_protocol)
        self._script_editor.modificationChanged.connect(
            self.change_modified_script)

        # Track undo/redo button state
        self._editor_tabs.currentChanged.connect(self.change_editor_tab)
        self._model_editor.undoAvailable.connect(self.change_undo_model)
        self._protocol_editor.undoAvailable.connect(self.change_undo_protocol)
        self._script_editor.undoAvailable.connect(self.change_undo_script)
        self._model_editor.redoAvailable.connect(self.change_redo_model)
        self._protocol_editor.redoAvailable.connect(self.change_redo_protocol)
        self._script_editor.redoAvailable.connect(self.change_redo_script)
        self._model_editor.copyAvailable.connect(self.change_copy_model)
        self._protocol_editor.copyAvailable.connect(self.change_copy_protocol)
        self._script_editor.copyAvailable.connect(self.change_copy_script)

        # Create console
        self._console = Console()
        self._console.write('Loading Myokit IDE')

        # Create central layout: vertical splitter
        self._central_splitter = QtWidgets.QSplitter(Qt.Orientation.Vertical)
        self._central_splitter.addWidget(self._editor_tabs)
        self._central_splitter.addWidget(self._console)
        self._central_splitter.setSizes([580, 120])
        self.setCentralWidget(self._central_splitter)

        # Timer to bundle operations after the model text has changed
        self._model_changed_timer = QtCore.QTimer()
        self._model_changed_timer.setSingleShot(True)
        self._model_changed_timer.timeout.connect(self.change_model_timeout)

        # Model explorer (with simulations)
        self._explorer = None

        # Current path, current file, recent files
        self._path = QtCore.QDir.currentPath()
        self._file = None
        self._recent_files = []

        # Load settings from ini file
        self.load_config()

        # Cached validated model and protocol
        self._valid_model = None
        self._valid_protocol = None

        # Last-found model and protocol error
        self._last_model_error = None
        self._last_protocol_error = None

        # React to changes to model and protocol
        # (For example devalidate model and protocol upon any changes)
        self._model_editor.textChanged.connect(self.change_model)
        self._protocol_editor.textChanged.connect(self.change_protocol)

        # Starting off on the model tab, so disable actions specific to
        # protocol and script
        for widget in self._protocol_widgets:
            widget.setEnabled(False)
        for widget in self._script_widgets:
            widget.setEnabled(False)

        # Open select file, recent file or start new
        if filename is not None:
            # Load or import file, based on extension
            # If it doesn't work, show an error message, as this is something
            # the user explicitly requested.
            base, ext = os.path.splitext(filename)
            ext = ext.lower()[1:]
            if ext == 'cellml':
                self.action_import_model_internal('cellml', filename)
            else:
                # Open as mmt
                try:
                    self.load_file(filename)
                except Exception:
                    self._console.write('Error loading file: ' + str(filename))
                    self.show_exception()
        else:
            if self._file is not None:
                # Try loading the last file, but if it goes wrong continue
                # without error messages
                try:
                    self.load_file(self._file)
                except Exception:
                    self._file = None
            if self._file is None:
                # Create a new file
                self.new_file()

        # Set focus
        self._model_editor.setFocus()

    def action_about(self):
        """
        Displays the about dialog.
        """
        QtWidgets.QMessageBox.about(self, TITLE, ABOUT)

    def action_check_units_tolerant(self):
        """
        Perform a unit check in tolerant mode.
        """
        try:
            model = self.model(errors_in_console=True)
            if not model:
                return
            model.check_units(mode=myokit.UNIT_TOLERANT)
            self._console.write('Units ok! (checked in tolerant mode)')
        except myokit.IncompatibleUnitError as e:
            self._console.write(str(e))

            # Jump to error, if possible
            token = e.token()
            if token is None:
                return
            line, char = token[2], token[3]
            self._editor_tabs.setCurrentWidget(self._model_tab)
            self.statusBar().showMessage(
                'Jumping to (' + str(line) + ',' + str(char) + ').')
            self._model_editor.jump_to(line - 1, char)
        except Exception:
            self.show_exception()

    def action_check_units_strict(self):
        """
        Perform a unit check in strict mode.
        """
        try:
            model = self.model(errors_in_console=True)
            if not model:
                return
            model.check_units(mode=myokit.UNIT_STRICT)
            self._console.write('Units ok! (checked in strict mode)')
        except myokit.IncompatibleUnitError as e:
            self._console.write(str(e))

            # Jump to error, if possible
            token = e.token()
            if token is None:
                return
            line, char = token[2], token[3]
            self._editor_tabs.setCurrentWidget(self._model_tab)
            self.statusBar().showMessage(
                'Jumping to (' + str(line) + ',' + str(char) + ').')
            self._model_editor.jump_to(line - 1, char)
        except Exception:
            self.show_exception()

    def action_clear_units(self):
        """
        Remove all units from expressions in this model.
        """
        try:
            # Ask are you sure?
            msg = 'Remove all units from expressions in model?'
            sb = QtWidgets.QMessageBox.StandardButton
            reply = QtWidgets.QMessageBox.question(
                self, TITLE, msg, sb.Yes | sb.No)
            if reply == sb.No:
                return
            # Strip units
            # Note: lines are used in error handling!
            lines = self._model_editor.get_text().splitlines()
            text = myokit.strip_expression_units(lines)
            self._model_editor.replace(text)
            self._console.write('Removed all expression units.')
        except myokit.ParseError as e:
            self.statusBar().showMessage('Error parsing model')
            self._console.write(myokit.format_parse_error(e, lines))
        except myokit.IntegrityError as e:
            self.statusBar().showMessage('Model integrity error')
            self._console.write('Model integrity error:')
            self._console.write(str(e))
        except Exception:
            self.show_exception()

    def action_comment(self):
        """
        Comments or uncomments the currently selected lines.
        """
        self._editor_tabs.currentWidget().editor.toggle_comment()

    def action_component_cycles(self):
        """
        Checks for interdependency-cycles amongst the components and displays
        them if found.
        """
        try:
            # Validate model
            model = self.model(errors_in_console=True)
            if not model:
                return
            # Check for component cycles
            if model.has_interdependent_components():
                cycles = model.component_cycles()
                cycles = [
                    '  ' + ' > '.join([x.name() for x in c]) for c in cycles]
                cycles = ['Found component cycles:'] + cycles
                self._console.write('\n'.join(cycles))
            else:
                self._console.write('No component cycles found.')
        except Exception:
            self.show_exception()

    def action_component_dependency_graph(self):
        """
        Displays a component dependency graph
        """
        import matplotlib.pyplot as plt
        try:
            model = self.model(errors_in_console=True)
            if not model:
                return
            f = plt.figure()
            a = f.add_subplot(1, 1, 1)
            myokit.lib.deps.plot_component_dependency_graph(
                model, axes=a, omit_states=True, omit_constants=True)
            plt.show()
        except Exception:
            self.show_exception()

    def action_copy(self):
        """
        Copy text in editor (when triggered from menu).
        """
        self._editor_tabs.currentWidget().editor.copy()

    def action_cut(self):
        """
        Cut text in editor (when triggered from menu).
        """
        self._editor_tabs.currentWidget().editor.cut()

    def action_explore(self):
        """
        Opens the explorer
        """
        # Simulation creation method
        def sim():
            QtWidgets.QApplication.processEvents(
                QtCore.QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)
            try:
                # Get model and protocol
                m = self.model(errors_in_console=True)
                if m is False:
                    return 'Errors in model'
                elif m is None:
                    return 'Empty model definition'
                QtWidgets.QApplication.processEvents(
                    QtCore.QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)
                p = self.protocol(errors_in_console=True)
                if p is False:
                    return 'Errors in protocol'
                QtWidgets.QApplication.processEvents(
                    QtCore.QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)
                # Create and return simulation
                self.statusBar().showMessage('Creating simulation...')
                return m, p, myokit.Simulation(m, p)
            except Exception:
                self.show_exception()
        try:
            # Guess duration
            duration = 1000
            m = self.model(errors_in_console=False)
            if m is not False:
                time_unit = m.time().unit()
                if time_unit == myokit.units.second:
                    model_guess = 1
                else:
                    model_guess = 1000
                p = self.protocol(errors_in_console=False)
                if p is None or p is False:
                    duration = model_guess
                else:
                    duration = p.characteristic_time()
                    # Heuristic: If protocol is 1000 (default), but unit is
                    # seconds, then use seconds
                    if duration == 1000 and model_guess == 1:
                        duration = 1
            # Create explorer or update existing one
            if self._explorer is None:
                self._explorer = explorer.Explorer(
                    self, sim, self._console, duration=duration)
            self._explorer.show()
        except Exception:
            self.show_exception()

    def action_export_model(self, name, ext=None, glob=None):
        """
        Exports the model to a file.

        Arguments:

        ``name``
            The exporter name.
        ``ext``
            An optional default file extension to create a suggested filename.
        ``glob``
            An optional filter for the file selection method.

        """
        try:
            # Get model
            m = self.model(errors_in_console=True)
            if m is False:
                return

            # Create exporter
            e = myokit.formats.exporter(name)
            if not e.supports_model():
                raise Exception('Exporter does not support export of model')

            # Suggest a path
            if ext is None:
                path = self._path
            elif self._file is None:
                path = os.path.join(self._path, 'new-model' + ext)
            else:
                path = os.path.splitext(self._file)[0] + ext

            # Ask for real path
            filename = QtWidgets.QFileDialog.getSaveFileName(
                self,
                'Select file to export to',
                path,
                filter=glob)[0]
            if not filename:
                return

            ex = None
            with warnings.catch_warnings(record=True) as ws:
                try:
                    if name in ('cellml1', 'cellml2'):
                        p = self.protocol(errors_in_console=True)
                        if p is False:
                            p = None
                        e.model(filename, m, p)
                    else:
                        e.model(filename, m)
                except myokit.ExportError as ex:
                    pass
            for w in ws:
                self._console.write('Warning: ' + str(w.message))

            if ex is None:
                self._console.write('Export successful.')
                info = e.post_export_info()
                if info:
                    self._console.write(info)
            else:
                self._console.write('Export failed.')
                self._console.write(str(ex))

        except Exception:
            self.show_exception()

    def action_export_runnable(self, name):
        """
        Exports the model and optionally the protocol to a directory.

        Arguments:

        ``name``
            The exporter name.

        """
        try:
            # Get model & protocol
            m = self.model(errors_in_console=True)
            if m is False:
                return
            p = self.protocol(errors_in_console=True)
            if p is False:
                return

            # Create exporter & test compatibility
            e = myokit.formats.exporter(name)
            if not e.supports_runnable():
                raise Exception('Exporter does not support export of runnable')

            # Select dir
            path = QtWidgets.QFileDialog.getSaveFileName(
                self, 'Create directory', self._path)[0]
            if not path:
                return

            ex = None
            with warnings.catch_warnings(record=True) as ws:
                try:
                    e.runnable(path, m, p)
                except myokit.ExportError as ex:
                    pass
            for w in ws:
                self._console.write('Warning: ' + str(w.message))

            if ex is None:
                self._console.write('Export successful.')
                info = e.post_export_info()
                if info:
                    self._console.write(info)
            else:
                self._console.write('Export failed.')
                self._console.write(str(ex))

        except Exception:
            self.show_exception()

    def action_find(self):
        """ Show or reactivate the find/replace bar. """

        current = self._editor_tabs.currentWidget()
        if current == self._model_tab:
            self._model_tools.toggle(self._model_search, True)
            self._model_search.activate()
        if current == self._protocol_tab:
            self._protocol_tools.toggle(self._protocol_search, True)
            self._protocol_search.activate()
        if current == self._script_tab:
            self._script_tools.toggle(self._script_search, True)
            self._script_search.activate()

    def action_format_protocol(self):
        """
        Reformat the protocol.
        """
        try:
            before = self._protocol_editor.get_text()
            p = self.protocol(errors_in_console=True)
            if p is False:
                self._console.write(
                    'Unable to apply formatting: Errors in protocol.')
            elif p is not None:
                after = p.code()
                if after != before:
                    self._protocol_editor.replace(after)
        except Exception:
            self.show_exception()

    def action_import_abf_protocol(self):
        """
        Imports a protocol from an abf (v2) file.
        """
        try:
            if not self.prompt_save_changes(cancel=True):
                return
            filename = QtWidgets.QFileDialog.getOpenFileName(
                self, 'Open ABF file', self._path, filter=FILTER_ABF)[0]
            if not filename:
                return

            # Create importer
            i = myokit.formats.importer('abf')

            # Import
            exception = None
            with warnings.catch_warnings(record=True) as ws:
                try:
                    protocol = i.protocol(filename)
                except myokit.ImportError as ex:
                    exception = ex
            for w in ws:
                self._console.write('Warning: ' + str(w.message))

            # Handle failure
            if exception is not None:
                self._console.write('Protocol import failed.')
                self._console.write(str(exception))
                self.statusBar().showMessage('Protocol import failed.')
                return

            # Import okay, update interface
            self.new_file()
            self._protocol_editor.setPlainText(protocol.code())
            self._console.write('Protocol imported successfully.')

            # Set working directory to file's path
            self._path = os.path.dirname(filename)
            os.chdir(self._path)

            # Save settings file
            try:
                self.save_config()
            except Exception:
                pass

            # Update interface
            self._tool_save.setEnabled(True)
            self.update_window_title()

        except Exception:
            self.show_exception()

    def action_import_model(self, name, glob=None):
        """
        Imports a model definition (asking the user for the filename).

        Arguments:

        ``name``
            The name of the importer to use.
        ``glob``
            A filter for file selection.

        """
        try:
            if not self.prompt_save_changes(cancel=True):
                return
            filename = QtWidgets.QFileDialog.getOpenFileName(
                self, 'Select model file', self._path, filter=glob)[0]
            if not filename:
                return

            self.action_import_model_internal(name, filename)

        except Exception:
            self.show_exception()

    def action_import_model_internal(self, importer, filename):
        """
        Imports a model file, with a known filename.

        Arguments:

        ``importer``
            The name of the importer to use.
        ``filename``
            The file to import.

        """
        try:
            # Set working directory to file's path
            self._path = os.path.dirname(filename)
            os.chdir(self._path)

            # Load file
            i = myokit.formats.importer(importer)

            # Import the model
            exception = None
            with warnings.catch_warnings(record=True) as ws:
                try:
                    model = i.model(filename)
                except myokit.ImportError as e:
                    exception = e
            for w in ws:
                self._console.write('Warning: ' + str(w.message))

            # Import failed?
            if exception is not None:
                self._console.write('Model import failed.')
                self._console.write(str(exception))
                self.statusBar().showMessage('Model import failed.')
                return

            # Try to split off protocol
            protocol = myokit.lib.guess.remove_embedded_protocol(model)

            # No protocol? Then create one
            if protocol is None:
                protocol = myokit.default_protocol(model)

            # Get default script
            script = myokit.default_script(model)

            # Import okay, update interface
            self.new_file()
            self._model_editor.setPlainText(model.code())
            self._protocol_editor.setPlainText(protocol.code())
            self._script_editor.setPlainText(script)

            # Write log to console
            self._console.write('Model imported successfully.')

            # Save settings file
            try:
                self.save_config()
            except Exception:
                pass

            # Update interface
            self._tool_save.setEnabled(True)
            self.update_window_title()
        except Exception:
            self.show_exception()

    def action_jump_to_error(self):
        """
        Jump to the last error in the model tab.
        """
        try:
            t = self._editor_tabs.currentWidget()
            if t is self._model_tab:

                # Check for error
                self.model(console=True)
                if self._last_model_error is None:
                    return

                # Show error
                line = self._last_model_error.line
                char = self._last_model_error.char
                self.statusBar().showMessage(
                    'Jumping to (' + str(line) + ',' + str(char) + ').')
                self._model_editor.jump_to(line - 1, char)

            elif t is self._protocol_tab:

                # Check for error
                self.protocol(console=True)
                if self._last_protocol_error is None:
                    return

                # Show error
                line = self._last_protocol_error.line
                char = self._last_protocol_error.char
                self.statusBar().showMessage(
                    'Jumping to (' + str(line) + ',' + str(char) + ').')
                self._protocol_editor.jump_to(line - 1, char)

            # Can't be called on script tab -- or does nothing
        except Exception:
            self.show_exception()

    def action_license(self):
        """
        Displays this program's licensing information.
        """
        QtWidgets.QMessageBox.about(self, TITLE, myokit.LICENSE_HTML)

    def action_model_stats(self):
        """
        Gathers and displays some basic information about the current model.
        """
        try:
            self.statusBar().showMessage('Gathering model statistics')
            # Get model and editor code
            model = self.model()
            code = self._model_editor.get_text()
            # Create text
            text = []
            text.append('Model statistics')
            text.append('----------------')
            # Add statistics about the model code
            if model:
                text.append('Name: ' + model.name())
            text.append('Number of lines: ' + str(len(code.splitlines())))
            code = code.replace('\n', '')
            text.append('Number of characters: ' + str(len(code)))
            code = code.replace(' ', '')
            text.append('  without whitespace: ' + str(len(code)))
            # Add statistics about the model
            if model is None:
                text.append('No model to parse')
            elif model is False:
                text.append('Unable to parse model')
            else:
                text.append(
                    'Number of components: '
                    + str(model.count_components()))
                text.append(
                    'Number of variables: '
                    + str(model.count_variables(deep=True)))
                text.append(
                    '              bound: '
                    + str(model.count_variables(bound=True, deep=True)))
                text.append(
                    '              state: '
                    + str(model.count_variables(state=True, deep=True)))
                text.append(
                    '       intermediary: '
                    + str(model.count_variables(inter=True, deep=True)))
                text.append(
                    '           constant: '
                    + str(model.count_variables(const=True, deep=True)))
            self._console.write('\n'.join(text))
        except Exception:
            self.statusBar().showMessage('"New file" failed.')
            self.show_exception()

    def action_new(self):
        """
        Create a new model, closing any current one
        """
        try:
            # Attempt to save changes, allow user to cancel
            if not self.prompt_save_changes(cancel=True):
                return
            self.new_file()
        except Exception:
            self.statusBar().showMessage('"New file" failed.')
            self.show_exception()

    def action_open(self):
        """
        Select and open an existing file.
        """
        try:
            if not self.prompt_save_changes(cancel=True):
                return
            filename = QtWidgets.QFileDialog.getOpenFileName(
                self, 'Open mmt file', self._path, filter=FILTER_MMT)[0]
            if filename:
                self.load_file(filename)
        except Exception:
            self.statusBar().showMessage('"Open file" failed')
            self.show_exception()

    def action_open_recent(self):
        """
        Opens a recent file.
        """
        try:
            if not self.prompt_save_changes(cancel=True):
                return
            action = self.sender()
            if action:
                filename = str(action.data())
                if not os.path.isfile(filename):
                    self._console.write(
                        'Failed to load file. The selected file can not be'
                        ' found: ' + str(filename))
                else:
                    self.load_file(filename)
        except Exception:
            self.statusBar().showMessage('"Open recent file" failed')
            self.show_exception()

    def action_paste(self):
        """
        Paste text in editor (when triggered from menu).
        """
        self._editor_tabs.currentWidget().editor.paste()

    def action_preview_protocol(self):
        """
        Displays a preview of the current protocol.
        """
        import matplotlib.pyplot as plt
        try:
            p = self.protocol(errors_in_console=True)
            if p is False:
                self._console.write(
                    'Can\'t display preview: Errors in protocol.')
            elif p is None:
                self._console.write(
                    'Can\'t display preview: No protocol specified.')
            else:
                a = 0
                b = p.characteristic_time()
                if b == 0:
                    b = 1000
                d = p.create_log_for_interval(a, b, for_drawing=True)
                plt.figure()
                plt.plot(d['time'], d['pace'])
                lo, hi = p.range()
                if lo == 0 and hi == 1:
                    plt.ylim(-0.1, 1.1)
                else:
                    r = (hi - lo) * 0.1
                    plt.ylim(lo - r, hi + r)
                plt.show()
        except Exception:
            self.show_exception()

    def action_redo(self):
        """
        Redoes the previously undone text edit operation.
        """
        self._editor_tabs.currentWidget().editor.redo()

    def action_run(self):
        """
        Runs the embedded script.
        """
        pbar = None
        try:
            # Prepare interface
            #self.setEnabled(False)
            self._console.write('Running embedded script.')
            QtWidgets.QApplication.setOverrideCursor(
                QtGui.QCursor(Qt.CursorShape.WaitCursor))
            # Create progress bar
            pbar = progress.ProgressBar(self, 'Running embedded script')
            pbar.show()
            QtWidgets.QApplication.processEvents(
                QtCore.QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)
            # Get model and protocol
            m = self.model(errors_in_console=True)
            if m is False:
                return
            p = self.protocol(errors_in_console=True)
            if p is False:
                return
            QtWidgets.QApplication.processEvents(
                QtCore.QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)
            # Clone model & protocol: the script may modify them!
            if m:
                m = m.clone()
            QtWidgets.QApplication.processEvents(
                QtCore.QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)
            if p:
                p = p.clone()
            QtWidgets.QApplication.processEvents(
                QtCore.QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)
            # Get embedded script
            x = self._script_editor.get_text()
            # Run
            try:
                myokit.run(
                    m, p, x,
                    stdout=self._console,
                    stderr=self._console,
                    progress=pbar.reporter(),
                )
                # Update user
                self._console.write('Done.')
                # Garbage collection
                gc.collect()
            except myokit.SimulationCancelledError:
                self._console.write('Simulation cancelled by user.')
            except Exception:
                self._console.write('An error has occurred')
                self._console.write(traceback.format_exc())
        finally:
            QtWidgets.QApplication.processEvents(
                QtCore.QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)
            # Hide progress bar
            if pbar is not None:
                pbar.close()
                pbar.deleteLater()
            # Work-around for cursor bug on linux
            #pos = QtGui.QCursor.pos()
            #QtGui.QCursor.setPos(0, 0)
            #QtGui.QCursor.setPos(pos)
            # Re-enable
            #self.setEnabled(True)
            # Set focus on editor
            self._editor_tabs.currentWidget().editor.setFocus()
            # Restore cursor
            QtWidgets.QApplication.restoreOverrideCursor()

    def action_save(self):
        """
        Save the current file.
        """
        self.save_file(save_as=False)

    def action_save_as(self):
        """
        Save the current file under a different name.
        """
        self.save_file(save_as=True)

    def action_state_derivatives(self):
        """
        Evaluates all the state derivatives and displays the results. Numerical
        erorrs raised will be displayed.
        """
        self._action_state_derivatives_inner(False)

    def action_state_derivatives2(self):
        """
        Evaluates all the state derivatives and displays the results. Numerical
        errors are ignored.
        """
        self._action_state_derivatives_inner(True)

    def _action_state_derivatives_inner(self, ignore_errors):
        """
        Evaluates all the state derivatives and displays the results.
        """
        try:
            m = self.model(errors_in_console=True)
            if m is None:
                self._console.write('No model found')
                return
            elif not m:
                self._console.write(
                    'Errors found in model. Please fix any remaining issues'
                    ' before using the method.')
                return
            try:
                self._console.write(
                    myokit.step(m, ignore_errors=ignore_errors))
            except myokit.NumericalError as ee:
                self._console.write('A numerical error occurred:')
                self._console.write(str(ee))
        except Exception:
            self.show_exception()

    def action_state_matrix(self):
        """
        Displays a state dependency matrix.
        """
        import matplotlib.pyplot as plt
        try:
            # Validate model
            model = self.model(errors_in_console=True)
            if not model:
                return
            # Show graph
            f = plt.figure()
            a = f.add_subplot(1, 1, 1)
            myokit.lib.deps.plot_state_dependency_matrix(model, axes=a)
            # Tweak figure margins (doesn't always work)
            f.subplots_adjust(
                left=0.1,
                right=1.0,
                bottom=0.08,
                top=0.77,
                wspace=0,
                hspace=0)
            plt.show()
        except Exception:
            self.show_exception()

    def action_toggle_navigator(self):
        """ Show or hide the model navigator. """
        self._model_tools.toggle(self._model_navigator)

    def action_trim_whitespace(self):
        """
        Trims any trailing whitespace from the current editor.
        """
        self._editor_tabs.currentWidget().editor.trim_trailing_whitespace()
        self._console.write('Trailing whitespace removed.')
        self.statusBar().showMessage('Trailing whitespace removed.')

    def action_undo(self):
        """
        Undoes the previous text edit operation.
        """
        self._editor_tabs.currentWidget().editor.undo()

    def action_validate(self):
        """
        Validates the model or the protocol, depending on the editor tab.
        """
        try:
            current = self._editor_tabs.currentWidget()
            if current is self._model_tab:
                self.model(console=True)
            elif current is self._protocol_tab:
                self.protocol(console=True)
            # Can't be called on script tab -- or does nothing
        except Exception:
            self.show_exception()

    def action_variable_definition(self):
        """
        Jump to the variable pointed at by the caret.
        """
        try:
            if self._editor_tabs.currentWidget() != self._model_tab:
                self._console.write(
                    'Variable info can only be displayed for model variables.')
                return
            var = self.selected_variable()
            if var is False:
                return  # Model error
            elif var is None:
                self._console.write(
                    'No variable selected. Please select a variable in the'
                    ' model editing tab.')
                return
            # Jump! (you might as well)
            line = var.model().show_line_of(var, raw=True)
            self.statusBar().showMessage('Jumping to line ' + str(line) + '.')
            self._model_editor.jump_to(line - 1, 0)
        except Exception:
            self.show_exception()

    def action_variable_dependencies(self):
        """
        Finds the variable pointed at by the cursor in the model editor and
        displays all expressions required for its calculation.
        """
        try:
            if self._editor_tabs.currentWidget() != self._model_tab:
                self._console.write(
                    'Variable info can only be displayed for model variables.')
                return
            var = self.selected_variable()
            if var is False:
                return  # Model error
            elif var is None:
                self._console.write(
                    'No variable selected. Please select a variable in the'
                    ' model editing tab.')
                return
            self._console.write(var.model().show_expressions_for(var))
        except Exception:
            self.show_exception()

    def action_variable_dependency_graph(self):
        """
        Displays a variable dependency graph
        """
        import matplotlib.pyplot as plt
        try:
            model = self.model(errors_in_console=True)
            if not model:
                return
            f = plt.figure()
            a = f.add_subplot(1, 1, 1)
            myokit.lib.deps.plot_variable_dependency_graph(model, axes=a)
            plt.show()
        except Exception:
            self.show_exception()

    def action_variable_evaluation(self):
        """
        Finds the variable pointed at by the cursor in the model editor and
        displays its calculation.
        """
        try:
            if self._editor_tabs.currentWidget() != self._model_tab:
                self._console.write(
                    'Variable info can only be displayed for model variables.')
                return
            var = self.selected_variable()
            if var is False:
                return  # Model error
            elif var is None:
                self._console.write(
                    'No variable selected. Please select a variable in the'
                    ' model editing tab.')
                return
            self._console.write(var.model().show_evaluation_of(var))
        except myokit.NumericalError as e:
            self._console.write('Numerical Error' + str(e))
        except Exception:
            self.show_exception()

    def action_variable_graph(self):
        """
        Attempts to graph the variable pointed at by the cursor in the model
        editor.
        """
        try:
            if self._editor_tabs.currentWidget() != self._model_tab:
                self._console.write(
                    'Only variables on the model editing tab can be graphed.')
            var = self.selected_variable()
            if var is False:
                return  # Model editor
            elif var is None:
                self._console.write(
                    'No variable selected. Please select a variable in the'
                    ' model editing tab.')
                return
            if var.is_constant():
                self._console.write('Cannot graph constants.')
                return
            elif var.is_bound():
                self._console.write('Cannot graph bound variables.')
                return
            f, a = var.pyfunc(arguments=True)
            title = 'Graphing ' + var.lhs().var().qname()
            grapher = vargrapher.VarGrapher(self, title, var, f, a)
            grapher.show()
        except Exception:
            self.show_exception()

    def action_variable_info(self):
        """
        Finds the variable pointed at by the cursor and displays its type and
        the line on which it is defined.
        """
        try:
            if self._editor_tabs.currentWidget() != self._model_tab:
                self._console.write(
                    'Variable info can only be displayed for model variables.')
                return
            var = self.selected_variable()
            if var is False:
                return  # Model error
            elif var is None:
                self._console.write(
                    'No variable selected. Please select a variable in the'
                    ' model editing tab.')
                return
            self._console.write(var.model().show_line_of(var))
        except Exception:
            self.show_exception()

    def action_variable_users(self):
        """
        Finds the variable pointed at by the cursor in the model editor and
        displays all variables that depend on it.
        """
        try:
            if self._editor_tabs.currentWidget() != self._model_tab:
                self._console.write(
                    'Variable info can only be displayed for model variables.')
                return
            var = self.selected_variable()
            if var is False:
                return  # Model error
            elif var is None:
                self._console.write(
                    'No variable selected. Please select a variable in the'
                    ' model editing tab.')
                return
            out = []
            if var.is_state():
                name = str(var.lhs())
                users = list(var.refs_by(state_refs=False))
                if users:
                    out.append(
                        'The following variables depend on ' + name + ':')
                    for v in sorted([v.qname() for v in users]):
                        out.append('  ' + v)
                else:
                    out.append('No variables depend on ' + name + '.')
            name = var.qname()
            users = list(var.refs_by(state_refs=var.is_state()))
            if users:
                out.append('The following variables depend on ' + name + ':')
                for v in sorted([v.qname() for v in users]):
                    out.append('  ' + v)
            else:
                out.append('No variables depend on ' + name + '.')
            self._console.write('\n'.join(out))
        except Exception:
            self.show_exception()

    def action_view_model(self):
        """
        View the model tab.
        """
        self._editor_tabs.setCurrentWidget(self._model_tab)
        self._model_editor.setFocus()

    def action_view_protocol(self):
        """
        View the protocol tab.
        """
        self._editor_tabs.setCurrentWidget(self._protocol_tab)
        self._protocol_editor.setFocus()

    def action_view_script(self):
        """
        View the script tab.
        """
        self._editor_tabs.setCurrentWidget(self._script_tab)
        self._script_editor.setFocus()

    def add_recent_file(self, filename):
        """
        Adds the given filename to the list of recent files.
        """
        try:
            # Remove filename from recent files list
            i = self._recent_files.index(filename)
            self._recent_files = \
                self._recent_files[:i] + self._recent_files[i + 1:]
        except ValueError:
            pass
        self._recent_files.insert(0, filename)
        self._recent_files = self._recent_files[:N_RECENT_FILES]
        self.update_recent_files_menu()

    def change_copy_model(self, enabled):
        """ Qt slot: CopyAvailable state of model editor changed. """
        if self._editor_tabs.currentWidget() == self._model_tab:
            self._tool_copy.setEnabled(enabled)
            self._tool_cut.setEnabled(enabled)

    def change_copy_protocol(self, enabled):
        """ Qt slot: CopyAvailable state of protocol editor changed. """
        if self._editor_tabs.currentWidget() == self._protocol_tab:
            self._tool_copy.setEnabled(enabled)
            self._tool_cut.setEnabled(enabled)

    def change_copy_script(self, enabled):
        """ Qt slot: CopyAvailable state of script editor changed. """
        if self._editor_tabs.currentWidget() == self._script_tab:
            self._tool_copy.setEnabled(enabled)
            self._tool_cut.setEnabled(enabled)

    def change_editor_tab(self, index):
        """ Qt slot: Called when the editor tab is changed. """
        # Update copy/cut
        t = self._editor_tabs.currentWidget()
        e = t.editor
        x = e.textCursor().hasSelection()
        self._tool_copy.setEnabled(x)
        self._tool_cut.setEnabled(x)

        # Update undo/redo
        d = e.document()
        self._tool_undo.setEnabled(d.isUndoAvailable())
        self._tool_redo.setEnabled(d.isRedoAvailable())

        # Enabled/disable tab-specific tools
        for widget in self._model_widgets:
            widget.setEnabled(index == 0)
        for widget in self._protocol_widgets:
            widget.setEnabled(index == 1)
        for widget in self._script_widgets:
            widget.setEnabled(index == 2)

        # Update "validate" and "jump to last error" tools
        if t is self._model_tab:
            self._tool_validate.setText('Validate model')
            self._tool_validate.setToolTip('Validate the model.')
            self._tool_validate.setEnabled(True)
            self._tool_jump_to_error.setEnabled(True)
        elif t is self._protocol_tab:
            self._tool_validate.setText('Validate protocol')
            self._tool_validate.setToolTip('Validate the protocol.')
            self._tool_validate.setEnabled(True)
            self._tool_jump_to_error.setEnabled(True)
        else:
            self._tool_validate.setEnabled(False)
            self._tool_jump_to_error.setEnabled(False)

    def change_model(self):
        """ Qt slot: Called whenever the model is changed. """
        self._valid_model = None
        # Bundle events in one-shot timer that calls change_model_timeout
        # Successive calls will restart the timer!
        self._model_changed_timer.start(100)    # in ms

    def change_model_timeout(self):
        """ Called with a slight delay after a change to the model. """
        if self._tool_view_navigator.isChecked():
            self.update_navigator()

    def change_modified_model(self, have_changes):
        """ Qt slot: Called when the model modified state is changed. """
        # Update have_changes status
        self._model_changed = have_changes
        self._have_changes = (
            self._model_changed or self._protocol_changed or
            self._script_changed)
        # Update button states
        self._tool_save.setEnabled(self._have_changes)
        # Update window title
        self.update_window_title()

    def change_modified_protocol(self, have_changes):
        """ Qt slot: Called when the protocol modified state is changed. """
        # Update have_changes status
        self._protocol_changed = have_changes
        self._have_changes = (
            self._model_changed or self._protocol_changed or
            self._script_changed)
        # Update button states
        self._tool_save.setEnabled(self._have_changes)
        # Update window title
        self.update_window_title()

    def change_modified_script(self, have_changes):
        """ Qt slot: Callend when the script modified state is changed. """
        # Update have_changes status
        self._script_changed = have_changes
        self._have_changes = (
            self._model_changed or self._protocol_changed or
            self._script_changed)
        # Update button states
        self._tool_save.setEnabled(self._have_changes)
        # Update window title
        self.update_window_title()

    def change_protocol(self):
        """ Qt slot: Called whenever the protocol is changed. """
        self._valid_protocol = None

    def change_redo_model(self, enabled):
        """ Qt slot: Redo state of model editor changed. """
        if self._editor_tabs.currentWidget() == self._model_tab:
            self._tool_redo.setEnabled(enabled)

    def change_redo_protocol(self, enabled):
        """ Qt slot: Redo state of protocol editor changed. """
        if self._editor_tabs.currentWidget() == self._protocol_tab:
            self._tool_redo.setEnabled(enabled)

    def change_redo_script(self, enabled):
        """ Qt slot: Redo state of script editor changed. """
        if self._editor_tabs.currentWidget() == self._script_tab:
            self._tool_redo.setEnabled(enabled)

    def change_tool_visibility(self, widget, visible):
        """ Qt slot: A tool panel (on the right-hand side) is toggled. """
        if widget == self._model_navigator:
            self._tool_view_navigator.setChecked(visible)

    def change_undo_model(self, enabled):
        """ Qt slot: Undo state of model editor changed. """
        if self._editor_tabs.currentWidget() == self._model_tab:
            self._tool_undo.setEnabled(enabled)

    def change_undo_protocol(self, enabled):
        """ Qt slot: Undo state of protocol editor changed. """
        if self._editor_tabs.currentWidget() == self._protocol_tab:
            self._tool_undo.setEnabled(enabled)

    def change_undo_script(self, enabled):
        """ Qt slot: Undo state of script editor changed. """
        if self._editor_tabs.currentWidget() == self._script_tab:
            self._tool_undo.setEnabled(enabled)

    def closeEvent(self, event=None):
        """
        Called when window is closed. To force a close (and trigger this
        function, call self.close())
        """
        try:
            self.save_config()
        except Exception:
            pass
        # Save changes?
        if not self.prompt_save_changes(cancel=False):
            # Something went wrong when saving changes or use wants to abort
            if event:
                event.ignore()
            return

        # Close all windows, including matplotlib plots
        QtWidgets.QApplication.instance().closeAllWindows()

        # Accept event, closing this window
        if event:
            event.accept()

    def close_explorer(self):
        """
        Closes the explorer, if any.
        """
        if self._explorer is None:
            return
        self._explorer.close()
        self._explorer.deleteLater()
        self._explorer = None

    def create_menu(self):
        """
        Creates this widget's menu.
        """
        self._menu = self.menuBar()
        # File menu
        self._menu_file = self._menu.addMenu('&File')
        # File > New
        self._tool_new = QtGui.QAction('&New', self)
        self._tool_new.setShortcut('Ctrl+N')
        self._tool_new.setStatusTip('Create a new mmt file.')
        self._tool_new.setIcon(myokit.gui.icon('document-new'))
        self._tool_new.triggered.connect(self.action_new)
        self._menu_file.addAction(self._tool_new)
        # File > Open
        self._tool_open = QtGui.QAction('&Open', self)
        self._tool_open.setShortcut('Ctrl+O')
        self._tool_open.setStatusTip('Open an existing mmt file.')
        self._tool_open.setIcon(myokit.gui.icon('document-open'))
        self._tool_open.triggered.connect(self.action_open)
        self._menu_file.addAction(self._tool_open)
        # File > ----
        self._menu_file.addSeparator()
        # File > Save
        self._tool_save = QtGui.QAction('&Save', self)
        self._tool_save.setShortcut('Ctrl+S')
        self._tool_save.setStatusTip('Save the current file')
        self._tool_save.setIcon(myokit.gui.icon('document-save'))
        self._tool_save.triggered.connect(self.action_save)
        self._tool_save.setEnabled(False)
        self._menu_file.addAction(self._tool_save)
        # File > Save as
        self._tool_save_as = QtGui.QAction('Save &as', self)
        self._tool_save_as.setShortcut('Ctrl+Shift+S')
        self._tool_save_as.setStatusTip(
            'Save the current file under a different name.')
        self._tool_save_as.triggered.connect(self.action_save_as)
        self._menu_file.addAction(self._tool_save_as)
        # File > ----
        self._menu_file.addSeparator()
        # File > Recent files
        self._recent_file_tools = []
        for i in range(N_RECENT_FILES):
            tool = QtGui.QAction(self, visible=False)
            tool.triggered.connect(self.action_open_recent)
            self._recent_file_tools.append(tool)
            self._menu_file.addAction(tool)
        # File > ----
        self._menu_file.addSeparator()
        # File > Quit
        self._tool_exit = QtGui.QAction('&Quit', self)
        self._tool_exit.setShortcut('Ctrl+Q')
        self._tool_exit.setStatusTip('Exit application.')
        self._tool_exit.triggered.connect(self.close)
        self._menu_file.addAction(self._tool_exit)
        #
        # Edit menu
        #
        self._menu_edit = self._menu.addMenu('&Edit')
        # Edit > Undo
        self._tool_undo = QtGui.QAction('&Undo', self)
        self._tool_undo.setShortcut('Ctrl+Z')
        self._tool_undo.setStatusTip('Undo the last edit.')
        self._tool_undo.setIcon(myokit.gui.icon('edit-undo'))
        self._tool_undo.triggered.connect(self.action_undo)
        self._tool_undo.setEnabled(False)
        self._menu_edit.addAction(self._tool_undo)
        # Edit > Redo
        self._tool_redo = QtGui.QAction('&Redo', self)
        self._tool_redo.setShortcut('Ctrl+Shift+Z')
        self._tool_redo.setStatusTip('Redo the last undone edit.')
        self._tool_redo.setIcon(myokit.gui.icon('edit-redo'))
        self._tool_redo.triggered.connect(self.action_redo)
        self._tool_redo.setEnabled(False)
        self._menu_edit.addAction(self._tool_redo)
        # Edit > ----
        self._menu_edit.addSeparator()
        # Edit > Cut
        self._tool_cut = QtGui.QAction('&Cut', self)
        self._tool_cut.setShortcut('Ctrl+X')
        self._tool_cut.setStatusTip(
            'Cut the selected text and copy it to the clipboard.')
        #self._tool_cut.setIcon(myokit.gui.icon('edit-cut'))
        self._tool_cut.triggered.connect(self.action_cut)
        self._tool_cut.setEnabled(False)
        self._menu_edit.addAction(self._tool_cut)
        # Edit > Copy
        self._tool_copy = QtGui.QAction('&Copy', self)
        self._tool_copy.setShortcut('Ctrl+C')
        self._tool_copy.setStatusTip(
            'Copy the selected text to the clipboard.')
        #self._tool_copy.setIcon(myokit.gui.icon('edit-copy'))
        self._tool_copy.triggered.connect(self.action_copy)
        self._tool_copy.setEnabled(False)
        self._menu_edit.addAction(self._tool_copy)
        # Edit > Paste
        self._tool_paste = QtGui.QAction('&Paste', self)
        self._tool_paste.setShortcut('Ctrl+V')
        self._tool_paste.setStatusTip(
            'Paste text from the clipboard into the editor.')
        #self._tool_paste.setIcon(myokit.gui.icon('edit-paste'))
        self._tool_paste.triggered.connect(self.action_paste)
        self._menu_edit.addAction(self._tool_paste)
        # Edit > ----
        self._menu_edit.addSeparator()
        # Edit > Find and replace
        self._tool_find = QtGui.QAction('&Find and replace', self)
        self._tool_find.setShortcut('Ctrl+F')
        self._tool_find.setStatusTip('Find and/or replace some text.')
        self._tool_find.setIcon(myokit.gui.icon('edit-find'))
        self._tool_find.triggered.connect(self.action_find)
        self._menu_edit.addAction(self._tool_find)
        # Edit > ----
        self._menu_edit.addSeparator()
        # Edit > Format protocol
        self._tool_format_protocol = QtGui.QAction('Format protocol', self)
        self._tool_format_protocol.setStatusTip(
            'Standardise the formatting of the protocol section.')
        self._tool_format_protocol.triggered.connect(
            self.action_format_protocol)
        self._menu_edit.addAction(self._tool_format_protocol)
        self._protocol_widgets.append(self._tool_format_protocol)
        # Edit > ----
        self._menu_edit.addSeparator()
        # Edit > Comment or uncomment
        self._tool_comment = QtGui.QAction(
            '&Comment/uncomment selected lines', self)
        self._tool_comment.setShortcut('Ctrl+;')
        self._tool_comment.setStatusTip(
            'Comments or uncomments the currently selected lines.')
        self._tool_comment.triggered.connect(self.action_comment)
        self._menu_edit.addAction(self._tool_comment)
        # Edit > Remove units from expressions
        self._tool_remove_units = QtGui.QAction(
            'Remove units from &expressions', self)
        self._tool_remove_units.setStatusTip(
            'Remove all units inside expressions.')
        self._tool_remove_units.triggered.connect(self.action_clear_units)
        self._menu_edit.addAction(self._tool_remove_units)
        self._model_widgets.append(self._tool_remove_units)
        # Edit > Trim whitespace
        self._tool_trim_whitespace = QtGui.QAction(
            'Trim trailing &whitespace', self)
        self._tool_trim_whitespace.setStatusTip(
            'Remove trailing whitespace from each line.')
        self._tool_trim_whitespace.triggered.connect(
            self.action_trim_whitespace)
        self._menu_edit.addAction(self._tool_trim_whitespace)
        #
        # View menu
        #
        self._menu_view = self._menu.addMenu('&View')
        # View > View model definition
        self._tool_view_model = QtGui.QAction('View &model definition', self)
        self._tool_view_model.setShortcut('Alt+1')
        self._tool_view_model.setStatusTip('View the model definition tab')
        self._tool_view_model.triggered.connect(self.action_view_model)
        self._menu_view.addAction(self._tool_view_model)
        # View > View protocol definition
        self._tool_view_protocol = QtGui.QAction(
            'View &protocol definition', self)
        self._tool_view_protocol.setShortcut('Alt+2')
        self._tool_view_protocol.setStatusTip(
            'View the protocol definition tab')
        self._tool_view_protocol.triggered.connect(self.action_view_protocol)
        self._menu_view.addAction(self._tool_view_protocol)
        # View > View embedded script
        self._tool_view_script = QtGui.QAction('View embedded &script', self)
        self._tool_view_script.setShortcut('Alt+3')
        self._tool_view_script.setStatusTip('View the embedded script tab')
        self._tool_view_script.triggered.connect(self.action_view_script)
        self._menu_view.addAction(self._tool_view_script)
        # View > ----
        self._menu_view.addSeparator()
        # View > Show model components (navigator)
        self._tool_view_navigator = QtGui.QAction(
            'Show model &components', self)
        self._tool_view_navigator.setCheckable(True)
        self._tool_view_navigator.setStatusTip(
            'Shows or hides the model navigator pane.')
        self._tool_view_navigator.triggered.connect(
            self.action_toggle_navigator)
        self._menu_view.addAction(self._tool_view_navigator)
        self._model_widgets.append(self._tool_view_navigator)
        # View > ----
        self._menu_view.addSeparator()
        # View > Preview protocol
        self._tool_preview_protocol = QtGui.QAction('&Preview protocol', self)
        self._tool_preview_protocol.setShortcut('Ctrl+P')
        self._tool_preview_protocol.setStatusTip(
            'Show a preview of the current protocol.')
        self._tool_preview_protocol.triggered.connect(
            self.action_preview_protocol)
        self._menu_view.addAction(self._tool_preview_protocol)

        #
        # Convert menu
        #
        self._menu_convert = self._menu.addMenu('&Convert')

        # Convert > Import CellML
        self._tool_import_cellml = QtGui.QAction(
            'Import model from CellML', self)
        self._tool_import_cellml.setStatusTip(
            'Import a model definition from a CellML file.')
        self._tool_import_cellml.triggered.connect(
            lambda: self.action_import_model('cellml', FILTER_CELLML))
        self._menu_convert.addAction(self._tool_import_cellml)
        # Convert > Export CellML 1
        self._tool_export_cellml1 = QtGui.QAction(
            'Export model to CellML 1.0', self)
        self._tool_export_cellml1.setStatusTip(
            'Export a model definition to a CellML 1.0 document.')
        self._tool_export_cellml1.triggered.connect(
            lambda: self.action_export_model(
                'cellml1', '.cellml', FILTER_CELLML))
        self._menu_convert.addAction(self._tool_export_cellml1)
        # Convert > Export CellML 2
        self._tool_export_cellml2 = QtGui.QAction(
            'Export model to CellML 2.0', self)
        self._tool_export_cellml2.setStatusTip(
            'Export a model definition to a CellML 2.0 document.')
        self._tool_export_cellml2.triggered.connect(
            lambda: self.action_export_model(
                'cellml2', '.cellml', FILTER_CELLML))
        self._menu_convert.addAction(self._tool_export_cellml2)

        # Convert > ----
        self._menu_convert.addSeparator()
        # Convert > Import ABF
        self._tool_import_abf = QtGui.QAction('Import protocol from ABF', self)
        self._tool_import_abf.setStatusTip(
            'Import a protocol definition from an ABF file.')
        self._tool_import_abf.triggered.connect(
            self.action_import_abf_protocol)
        self._menu_convert.addAction(self._tool_import_abf)
        # Convert > Import ChannelML
        self._tool_import_channelml = QtGui.QAction(
            'Import model from ChannelML', self)
        self._tool_import_channelml.setStatusTip(
            'Import a channel model from ChannelML.')
        self._tool_import_channelml.triggered.connect(
            lambda: self.action_import_model('channelml', FILTER_CHANNELML))
        self._menu_convert.addAction(self._tool_import_channelml)
        # Convert > Import SBML
        self._tool_import_sbml = QtGui.QAction('Import model from SBML', self)
        self._tool_import_sbml.setStatusTip(
            'Import a model from SBML.')
        self._tool_import_sbml.triggered.connect(
            lambda: self.action_import_model('sbml', FILTER_SBML))
        self._menu_convert.addAction(self._tool_import_sbml)

        # Convert > ----
        self._menu_convert.addSeparator()
        # Convert > Export HTML
        self._tool_export_html = QtGui.QAction('Export model to HTML', self)
        self._tool_export_html.setStatusTip(
            'Export a model definition to an HTML document using presentation'
            ' MathML.')
        self._tool_export_html.triggered.connect(
            lambda: self.action_export_model('html', '.html', FILTER_HTML))
        self._menu_convert.addAction(self._tool_export_html)
        # Convert > Export Latex
        self._tool_export_latex = QtGui.QAction('Export model to Latex', self)
        self._tool_export_latex.setStatusTip(
            'Export a model definition to a Latex document.')
        self._tool_export_latex.triggered.connect(
            lambda: self.action_export_model(
                'latex-article', '.tex', FILTER_LATEX))
        self._menu_convert.addAction(self._tool_export_latex)

        # Convert > ----
        self._menu_convert.addSeparator()

        # Convert > Ansic
        self._tool_export_ansic = QtGui.QAction('Export to Ansi C', self)
        self._tool_export_ansic.setStatusTip(
            'Export to a runnable Ansi C program.')
        self._tool_export_ansic.triggered.connect(
            lambda: self.action_export_runnable('ansic'))
        self._menu_convert.addAction(self._tool_export_ansic)

        # Convert > CUDA
        self._tool_export_cuda = QtGui.QAction('Export to CUDA kernel', self)
        self._tool_export_cuda.setStatusTip(
            'Export a model definition to a CUDA kernel program.')
        self._tool_export_cuda.triggered.connect(
            lambda: self.action_export_runnable('cuda-kernel'))
        self._menu_convert.addAction(self._tool_export_cuda)

        # Convert > CUDA RL
        self._tool_export_cuda_rl = QtGui.QAction(
            'Export to CUDA kernel with RL updates', self)
        self._tool_export_cuda_rl.setStatusTip(
            'Export a model definition to a CUDA kernel program using'
            ' Rush-Larsen updates where possible.')
        self._tool_export_cuda_rl.triggered.connect(
            lambda: self.action_export_runnable('cuda-kernel-rl'))
        self._menu_convert.addAction(self._tool_export_cuda_rl)

        # Convert > EasyML
        self._tool_export_easyml = QtGui.QAction(
            'Export to EasyML (Carp)', self)
        self._tool_export_easyml.setStatusTip(
            'Export to an EasyML script for use with Carp/Carpentry.')
        self._tool_export_easyml.triggered.connect(
            lambda: self.action_export_model('easyml', '.model'))
        self._menu_convert.addAction(self._tool_export_easyml)

        # Convert > Matlab
        self._tool_export_matlab = QtGui.QAction(
            'Export to Matlab/Octave', self)
        self._tool_export_matlab.setStatusTip(
            'Export to a runnable Matlab/Octave script.')
        self._tool_export_matlab.triggered.connect(
            lambda: self.action_export_runnable('matlab'))
        self._menu_convert.addAction(self._tool_export_matlab)

        # Convert > OpenCL
        self._tool_export_opencl = QtGui.QAction(
            'Export to OpenCL kernel', self)
        self._tool_export_opencl.setStatusTip(
            'Export a model definition to an OpenCL kernel program using')
        self._tool_export_opencl.triggered.connect(
            lambda: self.action_export_runnable('opencl'))
        self._menu_convert.addAction(self._tool_export_opencl)

        # Convert > OpenCL RL
        self._tool_export_opencl_rl = QtGui.QAction(
            'Export to OpenCL kernel with RL updates', self)
        self._tool_export_opencl_rl.setStatusTip(
            'Export a model definition to an OpenCL kernel program using'
            ' Rush-Larsen updates where possible.')
        self._tool_export_opencl_rl.triggered.connect(
            lambda: self.action_export_runnable('opencl-rl'))
        self._menu_convert.addAction(self._tool_export_opencl_rl)

        # Convert > Python
        self._tool_export_python = QtGui.QAction('Export to Python', self)
        self._tool_export_python.setStatusTip(
            'Export a model definition to a runnable Python script.')
        self._tool_export_python.triggered.connect(
            lambda: self.action_export_runnable('python'))
        self._menu_convert.addAction(self._tool_export_python)

        #
        # Analysis menu
        #
        self._menu_analysis = self._menu.addMenu('&Analysis')
        # Analysis > Model statistics
        self._tool_stats = QtGui.QAction('Show model statistics', self)
        self._tool_stats.setStatusTip(
            'Displays some basic statistics about the current model.')
        self._tool_stats.triggered.connect(self.action_model_stats)
        self._menu_analysis.addAction(self._tool_stats)
        # Analysis > ----
        self._menu_analysis.addSeparator()
        # Analysis > Check units strict
        self._tool_units_strict = QtGui.QAction('Check units (&strict)', self)
        self._tool_units_strict.setShortcut('F9')
        self._tool_units_strict.setStatusTip(
            'Check this model\'s units in strict mode.')
        self._tool_units_strict.triggered.connect(
            self.action_check_units_strict)
        self._menu_analysis.addAction(self._tool_units_strict)
        # Analysis > Check units tolerant
        self._tool_units_tolerant = QtGui.QAction(
            'Check units (&tolerant)', self)
        self._tool_units_tolerant.setShortcut('F10')
        self._tool_units_tolerant.setStatusTip(
            'Check this model\'s units in tolerant mode.')
        self._tool_units_tolerant.triggered.connect(
            self.action_check_units_tolerant)
        self._menu_analysis.addAction(self._tool_units_tolerant)
        # Analysis > ----
        self._menu_analysis.addSeparator()
        # Analysis > Show variable info
        self._tool_variable_info = QtGui.QAction(
            'Show quick variable info', self)
        self._tool_variable_info.setShortcut('Ctrl+R')
        self._tool_variable_info.setStatusTip(
            'Shows this variable\'s type and where it is defined.')
        self._tool_variable_info.triggered.connect(self.action_variable_info)
        self._menu_analysis.addAction(self._tool_variable_info)
        self._model_widgets.append(self._tool_variable_info)
        # Analysis > Show variable evaluation
        self._tool_variable_evaluation = QtGui.QAction(
            'Show variable evaluation', self)
        self._tool_variable_evaluation.setShortcut('Ctrl+E')
        self._tool_variable_evaluation.setStatusTip(
            'Show how the selected variable is evaluated.')
        self._tool_variable_evaluation.triggered.connect(
            self.action_variable_evaluation)
        self._menu_analysis.addAction(self._tool_variable_evaluation)
        self._model_widgets.append(self._tool_variable_evaluation)
        # Analysis > Show variable dependencies
        self._tool_variable_dependencies = QtGui.QAction(
            'Show variable dependencies', self)
        self._tool_variable_dependencies.setShortcut('Ctrl+D')
        self._tool_variable_dependencies.setStatusTip(
            'Show all expressions needed to calculate the selected variable.')
        self._tool_variable_dependencies.triggered.connect(
            self.action_variable_dependencies)
        self._menu_analysis.addAction(self._tool_variable_dependencies)
        self._model_widgets.append(self._tool_variable_dependencies)
        # Analysis > Show variable users
        self._tool_variable_users = QtGui.QAction(
            'Show variable users', self)
        self._tool_variable_users.setShortcut('Ctrl+U')
        self._tool_variable_users.setStatusTip(
            'Show all expressions dependent on the selected variable.')
        self._tool_variable_users.triggered.connect(
            self.action_variable_users)
        self._menu_analysis.addAction(self._tool_variable_users)
        self._model_widgets.append(self._tool_variable_users)
        # Analysis > Graph variable
        self._tool_variable_graph = QtGui.QAction(
            'Graph selected variable', self)
        self._tool_variable_graph.setShortcut('Ctrl+G')
        self._tool_variable_graph.setStatusTip(
            'Display a graph of the selected variable.')
        self._tool_variable_graph.triggered.connect(self.action_variable_graph)
        self._menu_analysis.addAction(self._tool_variable_graph)
        self._model_widgets.append(self._tool_variable_graph)
        # Analysis > Jump to variable definition
        self._tool_variable_jump = QtGui.QAction(
            'Jump to variable definition', self)
        self._tool_variable_jump.setShortcut('Ctrl+J')
        self._tool_variable_jump.setStatusTip(
            'Jump to the selected variable\'s definition.')
        self._tool_variable_jump.triggered.connect(
            self.action_variable_definition)
        self._menu_analysis.addAction(self._tool_variable_jump)
        self._model_widgets.append(self._tool_variable_jump)

        # Analysis > ----
        self._menu_analysis.addSeparator()
        # Analysis > Evaluate state derivatives
        self._tool_state_derivatives = QtGui.QAction(
            'Evaluate state derivatives', self)
        self._tool_state_derivatives.setShortcut('F7')
        self._tool_state_derivatives.setStatusTip(
            'Evaluate all state derivatives and display the results.')
        self._tool_state_derivatives.triggered.connect(
            self.action_state_derivatives)
        self._menu_analysis.addAction(self._tool_state_derivatives)
        # Analysis > Evaluate state derivatives without error checking
        self._tool_state_derivatives2 = QtGui.QAction(
            'Evaluate state derivatives (no error checking)', self)
        self._tool_state_derivatives2.setShortcut('F8')
        self._tool_state_derivatives2.setStatusTip(
            'Evaluate all state derivatives without checking for numerical'
            ' errors.')
        self._tool_state_derivatives2.triggered.connect(
            self.action_state_derivatives2)
        self._menu_analysis.addAction(self._tool_state_derivatives2)
        # Analysis > ----
        self._menu_analysis.addSeparator()
        # Analysis > Show component dependency graph
        self._tool_component_dependency_graph = QtGui.QAction(
            'Show component dependency graph', self)
        self._tool_component_dependency_graph.setStatusTip(
            'Display a graph of the dependencies between components.')
        self._tool_component_dependency_graph.triggered.connect(
            self.action_component_dependency_graph)
        self._menu_analysis.addAction(self._tool_component_dependency_graph)
        # Analysis > Show variable dependency graph
        self._tool_variable_dependency_graph = QtGui.QAction(
            'Show variable dependency graph', self)
        self._tool_variable_dependency_graph.setStatusTip(
            'Display a graph of the dependencies between variables.')
        self._tool_variable_dependency_graph.triggered.connect(
            self.action_variable_dependency_graph)
        self._menu_analysis.addAction(self._tool_variable_dependency_graph)
        # Analysis > Show state dependency matrix
        self._tool_state_matrix = QtGui.QAction(
            'Show state dependency matrix', self)
        self._tool_state_matrix.setStatusTip(
            'Display a matrix graph of the dependencies between states.')
        self._tool_state_matrix.triggered.connect(self.action_state_matrix)
        self._menu_analysis.addAction(self._tool_state_matrix)
        # Analysis > Show component dependency cycles
        self._tool_component_cycles = QtGui.QAction(
            'Show cyclical component dependencies', self)
        self._tool_component_cycles.setStatusTip(
            'Display a list of cyclical dependencies between components.')
        self._tool_component_cycles.triggered.connect(
            self.action_component_cycles)
        self._menu_analysis.addAction(self._tool_component_cycles)
        #
        # Run menu
        #
        self._menu_run = self._menu.addMenu('&Run')
        # Run > Validate
        self._tool_validate = QtGui.QAction('&Validate model', self)
        self._tool_validate.setShortcut('Ctrl+B')
        self._tool_validate.setStatusTip('Validate the model.')
        self._tool_validate.triggered.connect(self.action_validate)
        self._menu_run.addAction(self._tool_validate)
        # Run > Jump to error
        self._tool_jump_to_error = QtGui.QAction('&Jump to last error', self)
        self._tool_jump_to_error.setShortcut('Ctrl+Space')
        self._tool_jump_to_error.setStatusTip(
            'Jump to the last model error found.')
        self._tool_jump_to_error.triggered.connect(self.action_jump_to_error)
        self._menu_run.addAction(self._tool_jump_to_error)
        # Run > Run embedded script
        self._tool_run = QtGui.QAction('&Run embedded script', self)
        self._tool_run.setShortcut('F5')
        self._tool_run.setStatusTip('Run the embedded script.')
        self._tool_run.setIcon(myokit.gui.icon('media-playback-start'))
        self._tool_run.triggered.connect(self.action_run)
        self._menu_run.addAction(self._tool_run)
        # Run > Run explorer
        self._tool_explore = QtGui.QAction('&Run explorer', self)
        self._tool_explore.setShortcut('F6')
        self._tool_explore.setStatusTip(
            'Run a simulation and display the results in the explorer.')
        self._tool_explore.setIcon(myokit.gui.icon('media-playback-start'))
        self._tool_explore.triggered.connect(self.action_explore)
        self._menu_run.addAction(self._tool_explore)
        #
        # Help menu
        #
        self._menu_help = self._menu.addMenu('&Help')
        # Help > About
        self._tool_about = QtGui.QAction('&About', self)
        self._tool_about.setStatusTip('View information about this program.')
        self._tool_about.triggered.connect(self.action_about)
        self._menu_help.addAction(self._tool_about)
        # Help > License
        self._tool_license = QtGui.QAction('&License', self)
        self._tool_license.setStatusTip('View this program\'s license info.')
        self._tool_license.triggered.connect(self.action_license)
        self._menu_help.addAction(self._tool_license)

    def create_toolbar(self):
        """
        Creates the shared toolbar.
        """
        self._toolbar = self.addToolBar('tools')
        self._toolbar.setFloatable(False)
        self._toolbar.setMovable(False)
        self._toolbar.setToolButtonStyle(myokit.gui.TOOL_BUTTON_STYLE)
        self._toolbar.addAction(self._tool_new)
        self._toolbar.addAction(self._tool_open)
        self._toolbar.addAction(self._tool_save)
        self._toolbar.addSeparator()
        self._toolbar.addAction(self._tool_undo)
        self._toolbar.addAction(self._tool_redo)
        self._toolbar.addSeparator()
        self._toolbar.addAction(self._tool_find)
        self._toolbar.addSeparator()
        self._toolbar.addAction(self._tool_explore)
        self._toolbar.addAction(self._tool_run)

    def load_config(self):
        """
        Loads the user configuration from an ini file.
        """
        # Read ini file
        config = configparser.RawConfigParser()
        try:
            config.read(os.path.expanduser(SETTINGS_FILE))
        except configparser.ParsingError:
            # Partially read config causes all sorts of errors, so discard
            config = configparser.RawConfigParser()

        def getor(section, name, alt):
            """ Get or use alternative """
            kind = type(alt)
            if config.has_option(section, name):
                return kind(config.get(section, name))
            return alt

        # Window dimensions and location
        if config.has_section('window'):
            g = self.geometry()
            x = getor('window', 'x', g.x())
            y = getor('window', 'y', g.y())
            w = getor('window', 'w', g.width())
            h = getor('window', 'h', g.height())
            self.setGeometry(x, y, w, h)

        # Splitter sizes
        if config.has_section('splitter'):
            if config.has_option('splitter', 'top') and config.has_option(
                    'splitter', 'bottom'):
                a = int(config.get('splitter', 'top'))
                b = int(config.get('splitter', 'bottom'))
                self._central_splitter.setSizes([a, b])

        # Current and recent files
        if config.has_section('files'):
            if config.has_option('files', 'file'):
                filename = config.get('files', 'file')
                if os.path.isfile(filename):
                    self._file = filename
            if config.has_option('files', 'path'):
                path = config.get('files', 'path')
                if os.path.isdir(path):
                    # Note: If self._file is a valid file this will be loaded,
                    # which will change _path again. But if no last file is
                    # set, this option is used.
                    self._path = path
            self._recent_files = []
            for i in range(0, N_RECENT_FILES):
                opt = 'recent_' + str(i)
                if config.has_option('files', opt):
                    filename = config.get('files', opt)
                    if os.path.isfile(filename):
                        self._recent_files.append(filename)
            self.update_recent_files_menu()

        # Source editors
        self._model_search.load_config(config, 'model_editor')
        self._protocol_search.load_config(config, 'protocol_editor')
        self._script_search.load_config(config, 'script_editor')

        # Model navigator
        nav = getor('model_navigator', 'visible', 'false').strip().lower()
        if nav == 'true':
            self.action_toggle_navigator()

    def load_file(self, filename):
        """
        Loads a file into the IDE. Does not provide error handling.
        """
        # Close explorer, if required
        self.close_explorer()

        # Allow user directory and relative paths
        filename = os.path.abspath(os.path.expanduser(filename))

        # Set path to filename's path. Do this before we even know the file is
        # valid: if you click the wrong file by mistake you shouldn't have to
        # browse all the way back again).
        self._path = os.path.dirname(filename)

        # Open file, split into segments
        with open(filename, 'r') as f:
            segments = myokit.split(f)

        # Still here? Then set as file.
        self._file = filename

        # Add to recent files
        self.add_recent_file(filename)

        # Update model editor
        self._model_editor.set_text(segments[0].strip())

        # Update protocol editor
        self._protocol_editor.set_text(segments[1].strip())

        # Update script editor
        self._script_editor.set_text(segments[2].strip())

        # Don't validate model or protocol. Opening an invalid file is not an
        # error in itself.
        # Update console
        self._console.write('Opened ' + self._file)

        # Set working directory to file's path
        os.chdir(self._path)

        # Save settings file
        try:
            self.save_config()
        except Exception:
            pass

        # For some reason, setPlainText('') triggers a change event claiming
        # the text has changed. As a result, files with empty sections will
        # always show up as changed. This is prevented manually below:
        # (Triggers will handle the rest)
        self._model_editor.document().setModified(False)
        self._protocol_editor.document().setModified(False)
        self._script_editor.document().setModified(False)

        # Update interface
        self.update_navigator()
        self.update_window_title()

    def model(self, force=False, console=False, errors_in_console=False):
        """
        Validates and returns the model.

        If no model is specified in the model field ``None`` is returned. If
        parse errors occur, the value ``False`` is returned.

        The argument ``force`` can be used to force a reparsing, even if no
        changes were made to the text.

        If ``console`` is set to ``True`` the results of parsing will be
        written to the console. Similarly, the option ``errors_in_console``
        allows errors - but no positive parse results - to be shown in the
        console.
        """
        # Check for cached valid model
        if self._valid_model is not None and not force:
            if console:
                self._console.write(
                    'No changes to model since last build (no errors found).')
            return self._valid_model

        # Parse and validate
        model = None

        # Reset last model error
        self._last_model_error = None

        # Check for empty model field
        lines = self._model_editor.get_text()
        if lines.strip() == '':
            if console:
                self._console.write('No model found.')
            return None

        # Validate and return
        lines = lines.splitlines()
        try:
            # Parse
            model = myokit.parse_model(lines)

            # Show output
            if console:
                self._console.write('No errors found in model definition.')
            if model.has_warnings():
                if console or errors_in_console:
                    self._console.write(model.format_warnings())

            # Cache validated model
            self._valid_model = model
            return model

        except myokit.ParseError as e:
            if console or errors_in_console:
                # Write error to console
                self._console.write(myokit.format_parse_error(e, lines))
                # Store error
                self._last_model_error = e
            return False

        except myokit.IntegrityError as e:
            if console or errors_in_console:
                self.statusBar().showMessage('Model integrity error')
                self._console.write('Model integrity error:')
                self._console.write(str(e))
            return False

    def navigator_item_changed(self, line):
        """ Called whenever the navigator item is changed. """
        if line >= 0 and self._editor_tabs.currentWidget() == self._model_tab:
            self._model_editor.set_cursor(line)

    def new_file(self):
        """
        Replaces the editor contents with a new file. Does not do any error
        handling.
        """
        self._file = None
        # Close explorer, if required
        self.close_explorer()
        # Update editors
        self._model_editor.setPlainText('[[model]]\n')
        self._protocol_editor.setPlainText(myokit.default_protocol().code())
        self._script_editor.setPlainText(myokit.default_script())
        # Update interface
        self._tool_save.setEnabled(True)
        self.update_navigator()
        self.update_window_title()

    def prompt_save_changes(self, cancel=False):
        """
        Asks the user to save changes and does so if required.

        Returns ``True`` if the action can continue, ``False`` if the action
        should halt. A "Cancel" option will be provided if ``cancel=True``.
        """
        if not self._have_changes:
            return True
        if self._file:
            msg = 'Save changes to ' + str(self._file) + '?'
        else:
            msg = 'Save changes to new file?'
        sb = QtWidgets.QMessageBox.StandardButton
        options = sb.Yes | sb.No
        if cancel:
            options |= sb.Cancel
        reply = QtWidgets.QMessageBox.question(self, TITLE, msg, options)
        if reply == sb.Yes:
            # Only allow quitting if save succesful
            return self.save_file(save_as=False)
        elif reply == sb.No:
            return True
        else:
            return False

    def protocol(self, force=False, console=False, errors_in_console=False):
        """
        Validates the entered pacing protocol and returns it.

        If no protocol is specified ``None`` will be returned. If the specified
        protocol has errors, the return value will be ``False``.

        If ``force`` is set to ``True`` the protocol will always be reparsed,
        even if no changes were made.

        If ``console`` is set to ``True`` the results of parsing will be
        written to the console. Similarly, the option ``errors_in_console``
        allows errors - but no positive parse results - to be shown in the
        console.
        """
        # Check for cached valid protocol
        if self._valid_protocol and not force:
            if console:
                self._console.write(
                    'No changes to protocol since last build (no errors'
                    ' found).')
            return self._valid_protocol

        # Parse and validate
        protocol = None

        # Reset last protocol error
        self._last_protocol_error = None

        # Check for empty protocol field
        lines = self._protocol_editor.get_text()
        if lines.strip() == '':
            if console:
                self._console.write('No protocol found.')
            return None

        # Validate and return
        lines = lines.splitlines()
        try:
            # Parse
            protocol = myokit.parse_protocol(lines)
            # Show output
            if console:
                self._console.write('No errors found in protocol.')
            # Cache valid protocol
            self._valid_protocol = protocol
            return protocol
        except myokit.ParseError as e:
            if console or errors_in_console:
                # Write error to console
                self._console.write(myokit.format_parse_error(e, lines))
                # Store error
                self._last_protocol_error = e
            return False

    def save_config(self):
        """
        Saves the user configuration to an ini file.
        """
        config = configparser.RawConfigParser()

        # Window dimensions and location
        config.add_section('window')
        g = self.geometry()
        config.set('window', 'x', str(g.x()))
        config.set('window', 'y', str(g.y()))
        config.set('window', 'w', str(g.width()))
        config.set('window', 'h', str(g.height()))

        # Central splitter
        config.add_section('splitter')
        a, b = self._central_splitter.sizes()
        config.set('splitter', 'top', str(a))
        config.set('splitter', 'bottom', str(b))

        # Current and recent files
        config.add_section('files')
        config.set('files', 'path', self._path)
        config.set('files', 'file', self._file)
        for k, filename in enumerate(self._recent_files):
            config.set('files', 'recent_' + str(k), filename)

        # Source editors
        self._model_search.save_config(config, 'model_editor')
        self._protocol_search.save_config(config, 'protocol_editor')
        self._script_search.save_config(config, 'script_editor')

        # Model navigator visibility
        config.add_section('model_navigator')
        config.set(
            'model_navigator', 'visible',
            str(self._tool_view_navigator.isChecked()))

        # Write configuration to ini file
        inifile = os.path.expanduser(SETTINGS_FILE)
        with open(inifile, 'w') as configfile:
            config.write(configfile)

    def save_file(self, save_as=False):
        """
        Saves the current document. If no file name is known or
        ``save_as=True`` the user is asked for a filename.

        Returns ``True`` if the save was succesful
        """
        # Get file name
        if save_as or self._file is None:
            path = self._file
            if path is None:
                path = os.path.join(self._path, 'new-model.mmt')
            filename = QtWidgets.QFileDialog.getSaveFileName(
                self, 'Save mmt file', path, filter=FILTER_MMT_SAVE)[0]
            if not filename:
                return
            # Set file
            self._file = str(filename)
            # Add to recent files
            self.add_recent_file(self._file)
            # Set path
            self._path = os.path.dirname(self._file)
            # Set working directory to new path
            os.chdir(self._path)
        # Save
        self.statusBar().showMessage('Saving to ' + str(self._file))
        self._tool_save.setEnabled(False)
        self._tool_save_as.setEnabled(False)
        try:
            # Make _sure_ the text is retrieved _before_ attempting to write it
            # to a file. Otherwise, if anything goes wrong in this step, the
            # file is already emptied.
            m = self._model_editor.get_text()
            p = self._protocol_editor.get_text()
            x = self._script_editor.get_text()
            myokit.save(self._file, m, p, x)
            # Update have_changes state (triggers signals that fix the rest)
            self._model_editor.document().setModified(False)
            self._protocol_editor.document().setModified(False)
            self._script_editor.document().setModified(False)
            # Update window title
            self.update_window_title()
            # Inform user
            self.statusBar().showMessage('File saved as ' + str(self._file))
        except IOError:
            self._tool_save.setEnabled(True)
            self._tool_save_as.setEnabled(True)
            self.statusBar().showMessage('Error saving file.')
            self.show_exception()
            return False
        except Exception:
            self._tool_save.setEnabled(True)
            self._tool_save_as.setEnabled(True)
            self.statusBar().showMessage('Unexpected error saving file.')
            self.show_exception()
            return False
        finally:
            self._tool_save_as.setEnabled(True)
        # Save file history
        try:
            self.save_config()
        except Exception:
            pass
        # Finished
        return True

    def selected_variable(self, model=None):
        """
        Returns the variable currently pointed at by the cursor in the model
        editor. If a selection is made only the left side is used.

        If no variable is found ``None`` is returned. If a model error occurs
        ``False`` is returned
        """
        if self._editor_tabs.currentWidget() != self._model_tab:
            return None
        # Get model
        m = self.model(errors_in_console=True)
        if m is None:
            self._console.write('No model found.')
            return False
        elif not m:
            self._console.write(
                'Errors found in model. Please fix any remaining issues before'
                ' using this function.')
            return False
        # Get variable
        line, char = self._model_editor.cursor_position()
        token = m.item_at_text_position(line + 1, char)
        if token is None:
            return None
        if isinstance(token[1], myokit.Variable):
            return token[1]
        elif isinstance(token[1], myokit.Name):
            var = token[1].var()
            if isinstance(var, myokit.ModelPart):
                return var
        return None

    def show_exception(self):
        """
        Displays the last exception.
        """
        # Textwrap the final line
        e1 = traceback.format_exc().splitlines()
        e2 = e1[-1]
        e1 = e1[:-1]
        e2 = textwrap.wrap(e2, width=80)
        text = '\n'.join(e1 + e2)

        # Show the exception
        QtWidgets.QMessageBox.warning(
            self, TITLE,
            '<h1>An error has occurred.</h1>'
            '<pre>' + text + '</pre>')

    def update_navigator(self):
        """ Updates the model navigator contents. """
        # Find all components and store their positions in a list (name, line)
        pos = 0
        found = self._model_editor.document().find(self._nav_query, pos)
        positions = []
        while not found.isNull():
            pos = found.position()
            positions.append((found.selectedText(), pos))
            found = self._model_editor.document().find(self._nav_query, pos)
        self._model_navigator.set_positions(positions)

    def update_recent_files_menu(self):
        """
        Updates the recent files menu.
        """
        for k, filename in enumerate(self._recent_files):
            t = self._recent_file_tools[k]
            t.setText(str(k + 1) + '. ' + os.path.basename(filename))
            t.setStatusTip('Open ' + os.path.abspath(filename))
            t.setData(filename)
            t.setVisible(True)
        for i in range(len(self._recent_files), N_RECENT_FILES):
            self._recent_file_tools[i].setVisible(False)

    def update_window_title(self):
        """
        Sets this window's title based on the current state.
        """
        title = TITLE + ' ' + myokit.__version__
        if self._file:
            title = os.path.basename(self._file) + ' - ' + title
            if self._have_changes:
                title = '*' + title
        self.setWindowTitle(title)


class TabbedToolBar(QtWidgets.QTabWidget):
    """
    Tab widget with tools that are initially hidden, but can be shown upon
    request, and hidden using the "close" button.
    """
    # Signal: Tab show (added) or hidden (removed)
    # Attributes: (widget, status)
    tab_toggled = QtCore.Signal(QtWidgets.QWidget, bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self._close_button_hit)

        # Mapping from widgets to their labels
        self._tabs = {}

        # List of currently visible widgets
        self._visible = []

        # Start without visible tabs, and without being visible
        self.setVisible(False)

    def add(self, widget, name):
        """ Add a tab to this toolbar. """
        self._tabs[widget] = name

    def _close_button_hit(self, index):
        """ Called when the user clicks a "close tab" button. """
        self.toggle(self.widget(index), False)

    def keyPressEvent(self, event):
        """ Qt event: A key-press reaches the widget. """
        key = event.key()
        if key == Qt.Key.Key_Escape:
            self.setFocus()
            self.focusPreviousChild()
        else:
            super().keyPressEvent(event)

    def toggle(self, widget, new_status=None):
        """
        Toggles the visibility of the given widget (which must previously have
        been added with :meth:`add`), and returns its updated visibility
        status.

        An explicit visibility status can be set with ``new_status``.
        """
        # Get index of widget in current visible tabs
        try:
            index = self._visible.index(widget)
        except ValueError:
            index = -1

        # Determine new_status
        if new_status is None:
            new_status = index < 0
        # Setting explicitly? Then skip next steps if already at desired state
        elif new_status == (index >= 0):
            if new_status:
                # Already visible? Then give focus
                self.setCurrentWidget(widget)
                widget.setFocus()
            return

        # Show or hide
        if new_status:
            label = self._tabs[widget]
            self.addTab(widget, label)
            self._visible.append(widget)
            self.setVisible(True)
            self.setCurrentWidget(widget)
            widget.setFocus()
        else:
            del self._visible[index]
            self.removeTab(index)
            if self.count() < 1:
                self.setVisible(False)

        # Fire change event and return
        self.tab_toggled.emit(widget, new_status)


class ModelNavigator(QtWidgets.QWidget):
    """
    Model navigator window used to jump to different model components.
    """
    # Signal: Component selected
    # Attributes: (description)
    item_changed = QtCore.Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        # List widget
        self._list_widget = QtWidgets.QListWidget()
        self._list_widget.currentItemChanged.connect(self.current_item_changed)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self._list_widget)
        self.setLayout(layout)

        # List contents
        self._positions = []

    def current_item_changed(self, item, previous_item):
        """ Called if the navigator item is changed. """
        if item is not None:
            line = item.data(Qt.ItemDataRole.UserRole)
            self.item_changed.emit(line)

    def set_positions(self, positions):
        """ Updates the component list """

        # Check if update is required
        if positions == self._positions:
            return
        self._positions = list(positions)

        # Create new items
        self._list_widget.clear()
        self._list_widget.setSortingEnabled(True)
        for text, pos in self._positions:
            item = QtWidgets.QListWidgetItem(text[1:-1])
            item.setData(Qt.ItemDataRole.UserRole, pos)
            self._list_widget.addItem(item)


class Console(QtWidgets.QPlainTextEdit):
    """
    Console window used to write plain text output to in the IDE. Shows model
    parsing states and output of running explorations / scripts.

    *Extends*: ``QtWidgets.QPlainTextEdit``
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        font = myokit.gui.qtMonospaceFont()
        font.setPointSize(10)
        self.setFont(font)
        self.setFrameStyle(
            QtWidgets.QFrame.Shape.WinPanel | QtWidgets.QFrame.Shadow.Sunken)

    def clear(self):
        """
        Clears the console.
        """
        self.setPlainText('')

    def flush(self):
        """
        Ensures output if written to the screen.
        """
        #QtWidgets.QApplication.processEvents()
        # Calling processEvents() here creates issues when multiprocessing.
        # It appears multiple processes try to flush the stdout stream:
        #import os, sys
        #sys.__stdout__.write(str(os.getpid()) + '\n')
        # This could be caught by checking the process id before doing anything
        # but it's better to make sure child processes simply never call this
        # method!
        # Leaving this out now because there is an auto-flush anyway.

    def write(self, text=None):
        """
        Writes text to the console, prefixes a timestamp.
        """
        # Note that this will crash if other threads/processes try to write
        # to it.
        # Ignore newlines sent by print statements (bit hacky...)
        if text == '\n':
            return
        text = text.rstrip()
        #Note: Ignoring empty strings means a script can't do print('') or
        # print('\n') to clear space!
        #if not text:
        #    return
        # Write text
        self.appendPlainText('[' + myokit.time() + '] ' + str(text))
        # Autoscroll
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())
        # Autoflush
        QtWidgets.QApplication.processEvents(
            QtCore.QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)
