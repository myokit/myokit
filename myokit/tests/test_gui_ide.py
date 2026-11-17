#!/usr/bin/env python3
#
# Tests the myokit.gui.ide module.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import os
import pathlib
import tempfile
import unittest
import unittest.mock
import warnings

import myokit
from myokit.tests import DIR_DATA, DIR_FORMATS, qt_application

# Test files
LR = str(DIR_DATA / 'lr-1991.mmt')
BR = str(DIR_DATA / 'beeler-1977-model.mmt')

# A small model, with a bound variable, two constants, and a state
SMALL_MODEL = '''[[model]]
name: small
c.x = 1

[e]
t = 0 [ms] bind time
    in [ms]

[c]
a = 3 [1/ms]
    in [1/ms]
b = 2 * a
    in [1/ms]
dot(x) = -b * x
    in [1]
'''

# A similar model, but with a syntax error on line 10
BAD_MODEL = '''[[model]]
name: small
c.x = 1

[e]
t = 0 [ms] bind time
    in [ms]

[c]
a = 3 [1/ms] +
'''


class GuiIdeTest(unittest.TestCase):
    """ Tests the classes in ``myokit.gui.ide``. """

    @classmethod
    def setUpClass(cls):
        cls.app = qt_application()
        import myokit.gui.ide
        cls.ide = myokit.gui.ide
        cls.Qt = myokit.gui.Qt
        cls.QtCore = myokit.gui.QtCore
        cls.QtGui = myokit.gui.QtGui
        cls.QtWidgets = myokit.gui.QtWidgets

    def setUp(self):
        # Restore working directory after each test (the IDE changes it)
        cwd = os.getcwd()
        self.addCleanup(os.chdir, cwd)

        # Temporary directory, used for settings file and saved files
        tdir = tempfile.TemporaryDirectory()
        self.addCleanup(tdir.cleanup)
        self.tdir = pathlib.Path(tdir.name)
        self.settings = self.tdir / 'myokit-ide.ini'

        # Patch settings file, modal dialogs, and plt.show()
        mb = self.QtWidgets.QMessageBox
        fd = self.QtWidgets.QFileDialog
        self.question = self._patch(
            mb, 'question', return_value=mb.StandardButton.No)
        self.warning = self._patch(mb, 'warning')
        self.about = self._patch(mb, 'about')
        self.get_open = self._patch(fd, 'getOpenFileName',
                                    return_value=('', ''))
        self.get_save = self._patch(fd, 'getSaveFileName',
                                    return_value=('', ''))
        import matplotlib.pyplot as plt
        self.show = self._patch(plt, 'show')
        p = unittest.mock.patch.object(
            self.ide, 'SETTINGS_FILE', self.settings)
        p.start()
        self.addCleanup(p.stop)

        self.windows = []

    def _patch(self, obj, name, **kwargs):
        """ Patches ``obj.name`` with a mock until the end of the test. """
        p = unittest.mock.patch.object(obj, name, **kwargs)
        m = p.start()
        self.addCleanup(p.stop)
        return m

    def tearDown(self):
        import matplotlib.pyplot as plt
        for w in self.windows:
            try:
                for e in (w._model_editor, w._protocol_editor,
                          w._script_editor):
                    e.document().setModified(False)
                w.close_explorer()
                w.close()
                w.deleteLater()
            except RuntimeError:    # pragma: no cover
                pass
        self.windows = []
        plt.close('all')
        self.QtWidgets.QApplication.processEvents()

    def create(self, filename=None):
        """ Creates and returns an IDE, which is closed at tear down. """
        w = self.ide.MyokitIDE(filename)
        self.windows.append(w)
        return w

    def console(self, ide):
        """ Returns the console text. """
        return ide._console.toPlainText()

    def set_text(self, editor, code):
        """ Replaces the code in an editor, as if typed by a user. """
        editor.selectAll()
        editor.insertPlainText(code)

    def set_model(self, ide, code):
        """ Replaces the model code, as if typed by a user. """
        self.set_text(ide._model_editor, code)

    def goto(self, editor, text):
        """ Places the cursor of ``editor`` at the start of ``text``. """
        pos = editor.get_text().index(text)
        cursor = editor.textCursor()
        cursor.setPosition(pos)
        editor.setTextCursor(cursor)

    def test_new(self):
        # Test creating an IDE without a file
        ide = self.create()
        self.assertIsNone(ide._file)
        self.assertEqual(
            ide.windowTitle(), f'Myokit IDE {myokit.__version__}')
        self.assertEqual(ide._model_editor.get_text(), '[[model]]\n')
        self.assertEqual(
            ide._protocol_editor.get_text(), myokit.default_protocol().code())
        self.assertEqual(
            ide._script_editor.get_text(), myokit.default_script())
        self.assertIn('Loading Myokit IDE', self.console(ide))
        self.assertTrue(ide._tool_save.isEnabled())

        # Model is empty, protocol is valid
        self.assertIs(ide.model(console=True), False)
        self.assertIn('No variable bound to time', self.console(ide))
        self.assertIsInstance(ide.protocol(), myokit.Protocol)

        # Model-specific tools enabled, protocol/script tools disabled
        self.assertTrue(ide._tool_variable_info.isEnabled())
        self.assertFalse(ide._tool_format_protocol.isEnabled())

    def test_icon(self):
        # Test the icon method
        icon = self.ide.icon()
        self.assertIsInstance(icon, self.QtGui.QIcon)
        self.assertFalse(icon.isNull())

    def test_load_file(self):
        # Test loading a file via the constructor
        ide = self.create(LR)
        path = pathlib.Path(LR).absolute()
        self.assertEqual(ide._file, path)
        self.assertEqual(ide._recent_files, [path])
        self.assertEqual(pathlib.Path(os.getcwd()), path.parent)
        self.assertTrue(ide._model_editor.get_text().startswith('[[model]]'))
        self.assertIn('[[protocol]]', ide._protocol_editor.get_text())
        self.assertIn('[[script]]', ide._script_editor.get_text())
        self.assertFalse(ide._have_changes)
        self.assertFalse(ide._tool_save.isEnabled())
        self.assertTrue(ide.windowTitle().startswith('lr-1991.mmt - '))
        self.assertIn(f'Opened {path}', self.console(ide))

        # Recent files menu is updated
        tool = ide._recent_file_tools[0]
        self.assertTrue(tool.isVisible())
        self.assertEqual(tool.text(), '1. lr-1991.mmt')
        self.assertFalse(ide._recent_file_tools[1].isVisible())

        # Navigator is populated with components
        lw = ide._model_navigator._list_widget
        names = [lw.item(i).text() for i in range(lw.count())]
        self.assertIn('membrane', names)
        self.assertIn('engine', names)

        # Model and protocol can be parsed
        m = ide.model()
        self.assertIsInstance(m, myokit.Model)
        self.assertEqual(m.name(), 'Luo-Rudy model (1991)')
        self.assertIsInstance(ide.protocol(), myokit.Protocol)

        # Settings were stored in temporary settings file
        self.assertTrue(self.settings.is_file())
        with open(self.settings, 'r') as f:
            self.assertIn(str(path), f.read())

    def test_load_file_error(self):
        # Test loading a non-existent file via the constructor
        path = self.tdir / 'does-not-exist.mmt'
        ide = self.create(path)
        self.assertIsNone(ide._file)
        self.assertIn('Error loading file', self.console(ide))
        self.warning.assert_called_once()
        self.assertIn('An error has occurred', self.warning.call_args[0][2])

        # A new file is shown instead
        self.assertEqual(ide._model_editor.get_text(), '[[model]]\n')

    def test_load_cellml(self):
        # Test importing a CellML file via the constructor
        ide = self.create(str(DIR_FORMATS / 'cellml' / 'br-1977.cellml'))
        self.assertIn('Model imported successfully.', self.console(ide))
        self.assertIsNone(ide._file)
        self.warning.assert_not_called()

        # The imported model is shown
        m = ide.model()
        self.assertIsInstance(m, myokit.Model)
        self.assertEqual(m.count_states(), 8)
        self.assertIsInstance(ide.protocol(), myokit.Protocol)

        # A failed import shows a new file
        path = self.tdir / 'bad.cellml'
        path.write_text('not cellml')
        ide = self.create(str(path))
        self.assertIn('Model import failed.', self.console(ide))
        self.assertIsNone(ide._file)
        self.assertEqual(ide._model_editor.get_text(), '[[model]]\n')

    def test_config(self):
        # Test saving and loading the configuration file

        # Create IDE, load files, change some settings
        ide = self.create(BR)
        ide.load_file(LR)
        ide.action_toggle_navigator()
        ide._model_search._case_check.setChecked(True)
        ide.save_config()
        self.assertTrue(self.settings.is_file())

        # New IDE loads last file, recent files, and settings
        ide2 = self.create()
        self.assertEqual(ide2._file, pathlib.Path(LR).absolute())
        self.assertEqual(
            ide2._recent_files,
            [pathlib.Path(LR).absolute(), pathlib.Path(BR).absolute()])
        self.assertTrue(ide2._tool_view_navigator.isChecked())
        self.assertTrue(ide2._model_search._case_check.isChecked())
        self.assertFalse(ide2._protocol_search._case_check.isChecked())

        # Last file that can't be loaded is ignored
        with open(self.settings, 'w') as f:
            f.write('[files]\n')
            f.write(f'file = {self.tdir / "bad.mmt"}\n')
            f.write(f'path = {self.tdir}\n')
            f.write('recent_0 = /this/file/does/not/exist.mmt\n')
        with open(self.tdir / 'bad.mmt', 'wb') as f:
            f.write(b'\xff\xfe\x00\x81')
        ide3 = self.create()
        self.assertIsNone(ide3._file)
        self.assertEqual(ide3._recent_files, [])
        self.warning.assert_not_called()

        # Invalid ini file is ignored
        with open(self.settings, 'w') as f:
            f.write('this is not an ini file\n[[[')
        ide4 = self.create()
        self.assertIsNone(ide4._file)
        self.assertEqual(ide4._recent_files, [])

    def test_model_validation(self):
        # Test the model() method and validate/jump actions
        ide = self.create()
        self.set_model(ide, SMALL_MODEL)
        m = ide.model(console=True)
        self.assertIsInstance(m, myokit.Model)
        self.assertIn(
            'No errors found in model definition.', self.console(ide))

        # Cached model is returned
        self.assertIs(ide.model(console=True), m)
        self.assertIn('No changes to model since last build',
                      self.console(ide))
        self.assertIsNot(ide.model(force=True), m)

        # Any change invalidates the cache
        ide._model_editor.appendPlainText('# Comment')
        self.assertIsNone(ide._valid_model)

        # Model with warnings
        ide._model_editor.appendPlainText('[d]\nunused = 3')
        ide.model(errors_in_console=True)

        # Parse error
        self.set_model(ide, BAD_MODEL)
        ide._model_editor.jump_to(0, 0)
        ide.action_validate()
        self.assertIsNotNone(ide._last_model_error)
        self.assertEqual(ide._last_model_error.line, 10)
        self.assertIn('Syntax error', self.console(ide))

        # Jump to error
        ide.action_jump_to_error()
        line, char = ide._model_editor.cursor_position()
        self.assertEqual(line, ide._last_model_error.line - 1)

        # No error: no jump
        self.set_model(ide, SMALL_MODEL)
        ide._model_editor.jump_to(0, 0)
        ide.action_jump_to_error()
        self.assertEqual(ide._model_editor.cursor_position(), (0, 0))

        # Integrity error (normally wrapped in a ParseError by the parser)
        self.set_model(ide, SMALL_MODEL + '# Changed\n')
        with unittest.mock.patch(
                'myokit.parse_model',
                side_effect=myokit.IntegrityError('Bad model')):
            self.assertIs(ide.model(console=True), False)
        self.assertIn('Model integrity error', self.console(ide))
        self.assertEqual(
            ide.statusBar().currentMessage(), 'Model integrity error')

        # Empty model
        self.set_model(ide, '')
        self.assertIsNone(ide.model(console=True))

    def test_protocol_validation(self):
        # Test the protocol() method and validate/jump actions
        ide = self.create()
        ide.action_view_protocol()
        p = ide.protocol(console=True)
        self.assertIsInstance(p, myokit.Protocol)
        self.assertIn('No errors found in protocol.', self.console(ide))
        self.assertIs(ide.protocol(console=True), p)
        self.assertIn('No changes to protocol since last build',
                      self.console(ide))

        # Changes invalidate the cache
        self.set_text(ide._protocol_editor, 
            '[[protocol]]\n1 0 10 1000 0\n2 100 10 0 0\n')
        self.assertIsNone(ide._valid_protocol)
        p = ide.protocol()
        self.assertEqual(len(p), 2)

        # Parse error
        self.set_text(
            ide._protocol_editor, '[[protocol]]\n1 0 10 1000 0\nx y\n')
        ide._protocol_editor.jump_to(0, 0)
        ide.action_validate()
        self.assertIsNotNone(ide._last_protocol_error)
        ide.action_jump_to_error()
        self.assertEqual(ide._protocol_editor.cursor_position()[0],
                         ide._last_protocol_error.line - 1)

        # Error is not shown when not requested
        ide._last_protocol_error = None
        self.assertIs(ide.protocol(force=True), False)
        self.assertIsNone(ide._last_protocol_error)

        # Protocol without events is cached
        self.set_text(ide._protocol_editor, '[[protocol]]\n')
        p = ide.protocol()
        self.assertIsInstance(p, myokit.Protocol)
        self.assertEqual(len(p), 0)
        self.assertIs(ide.protocol(), p)

        # Empty protocol
        self.set_text(ide._protocol_editor, '')
        self.assertIsNone(ide.protocol(console=True))
        self.assertIn('No protocol found.', self.console(ide))

        # Format protocol
        self.set_text(ide._protocol_editor, 
            '[[protocol]]\n1    0  10 1000 0\n')
        ide.action_format_protocol()
        self.assertEqual(
            ide._protocol_editor.get_text().strip(),
            ide.protocol().code().strip())
        self.assertNotIn('1    0', ide._protocol_editor.get_text())
        self.set_text(ide._protocol_editor, '[[protocol]]\nx\n')
        ide.action_format_protocol()
        self.assertIn('Unable to apply formatting', self.console(ide))

        # Validate and jump to error do nothing on script tab
        ide.action_view_script()
        n = len(self.console(ide))
        ide.action_validate()
        ide.action_jump_to_error()
        self.assertEqual(n, len(self.console(ide)))

    def test_editing_undo_redo(self):
        # Test editing, modification tracking, and undo/redo
        ide = self.create(LR)
        original = ide._model_editor.get_text()
        self.assertFalse(ide._tool_undo.isEnabled())

        ide._model_editor.jump_to(0, 0)
        ide._model_editor.insertPlainText('# Hello\n')
        self.assertTrue(ide._have_changes)
        self.assertTrue(ide._model_changed)
        self.assertTrue(ide._tool_save.isEnabled())
        self.assertTrue(ide._tool_undo.isEnabled())
        self.assertFalse(ide._tool_redo.isEnabled())
        self.assertTrue(ide.windowTitle().startswith('*lr-1991.mmt'))

        # Undo
        ide.action_undo()
        self.assertEqual(ide._model_editor.get_text(), original)
        self.assertFalse(ide._have_changes)
        self.assertTrue(ide._tool_redo.isEnabled())
        self.assertFalse(ide.windowTitle().startswith('*'))

        # Redo
        ide.action_redo()
        self.assertTrue(ide._model_editor.get_text().startswith('# Hello'))
        self.assertTrue(ide._have_changes)

        # Protocol and script changes are tracked separately
        ide.action_view_protocol()
        self.assertFalse(ide._tool_undo.isEnabled())
        ide._protocol_editor.insertPlainText('# Hi\n')
        self.assertTrue(ide._protocol_changed)
        self.assertTrue(ide._tool_undo.isEnabled())
        ide.action_undo()
        self.assertFalse(ide._protocol_changed)
        self.assertTrue(ide._tool_redo.isEnabled())
        ide.action_view_script()
        ide._script_editor.insertPlainText('# Hi\n')
        self.assertTrue(ide._script_changed)
        self.assertTrue(ide._tool_undo.isEnabled())
        ide.action_undo()
        self.assertFalse(ide._script_changed)
        ide.action_redo()
        self.assertTrue(ide._script_changed)

    def test_tab_switching(self):
        # Test tool states when switching tabs
        ide = self.create()
        ide.action_view_protocol()
        self.assertIs(ide._editor_tabs.currentWidget(), ide._protocol_tab)
        self.assertEqual(ide._tool_validate.text(), 'Validate protocol')
        self.assertTrue(ide._tool_validate.isEnabled())
        self.assertTrue(ide._tool_format_protocol.isEnabled())
        self.assertFalse(ide._tool_variable_info.isEnabled())
        self.assertFalse(ide._tool_remove_units.isEnabled())

        ide.action_view_script()
        self.assertIs(ide._editor_tabs.currentWidget(), ide._script_tab)
        self.assertFalse(ide._tool_validate.isEnabled())
        self.assertFalse(ide._tool_jump_to_error.isEnabled())
        self.assertFalse(ide._tool_format_protocol.isEnabled())

        ide.action_view_model()
        self.assertIs(ide._editor_tabs.currentWidget(), ide._model_tab)
        self.assertEqual(ide._tool_validate.text(), 'Validate model')
        self.assertTrue(ide._tool_jump_to_error.isEnabled())
        self.assertTrue(ide._tool_variable_info.isEnabled())
        self.assertFalse(ide._tool_format_protocol.isEnabled())

    def test_cut_copy_paste(self):
        # Test cut, copy, paste actions
        ide = self.create()
        clipboard = self.QtWidgets.QApplication.clipboard()
        e = ide._model_editor
        self.set_model(ide, '[[model]]\nhello world')
        self.assertFalse(ide._tool_copy.isEnabled())
        e.selectAll()
        self.assertTrue(ide._tool_copy.isEnabled())
        self.assertTrue(ide._tool_cut.isEnabled())
        ide.action_copy()
        self.assertEqual(clipboard.text(), '[[model]]\nhello world')
        ide.action_cut()
        self.assertEqual(e.get_text(), '')
        self.assertFalse(ide._tool_copy.isEnabled())
        ide.action_paste()
        self.assertEqual(e.get_text(), '[[model]]\nhello world')

        # Copy state on other tabs
        ide.action_view_protocol()
        self.assertFalse(ide._tool_copy.isEnabled())
        ide._protocol_editor.selectAll()
        self.assertTrue(ide._tool_copy.isEnabled())
        ide.action_view_script()
        self.assertFalse(ide._tool_copy.isEnabled())
        ide._script_editor.selectAll()
        self.assertTrue(ide._tool_cut.isEnabled())

    def test_find_replace(self):
        # Test the find/replace bar
        ide = self.create()
        self.set_model(ide, SMALL_MODEL)
        self.assertFalse(ide._model_tools.isVisibleTo(ide))

        # Select text, then activate find: selection becomes query
        e = ide._model_editor
        self.goto(e, 'b = 2')
        cursor = e.textCursor()
        cursor.movePosition(
            self.QtGui.QTextCursor.MoveOperation.Right,
            self.QtGui.QTextCursor.MoveMode.KeepAnchor)
        e.setTextCursor(cursor)
        ide.action_find()
        search = ide._model_search
        self.assertTrue(ide._model_tools.isVisibleTo(ide))
        self.assertIn(search, ide._model_tools._visible)
        self.assertEqual(search._search_field.text(), 'b')

        # Find
        search._search_field.setText('dot(x)')
        search.action_find()
        self.assertEqual(e.textCursor().selectedText(), 'dot(x)')
        self.assertEqual(
            ide.statusBar().currentMessage(), 'Match found on line 14 char 0.')
        search._search_field.setText('notthere')
        search.action_find()
        self.assertEqual(ide.statusBar().currentMessage(), 'Query not found.')

        # Replace all
        search._search_field.setText('a')
        search._replace_field.setText('alpha')
        search._whole_check.setChecked(True)
        search._case_check.setChecked(True)
        search.action_replace_all()
        self.assertIn('alpha = 3', e.get_text())
        self.assertIn('b = 2 * alpha', e.get_text())
        self.assertIn(
            'Replaced 2 occurrences', ide.statusBar().currentMessage())
        self.assertIsInstance(ide.model(), myokit.Model)

        # Undo find/replace in one step
        ide.action_undo()
        self.assertEqual(e.get_text(), SMALL_MODEL)

        # Find on other tabs
        ide.action_view_protocol()
        ide.action_find()
        self.assertTrue(ide._protocol_tools.isVisibleTo(ide))
        ide._protocol_search._search_field.setText('Level')
        ide._protocol_search.action_find()
        self.assertEqual(
            ide._protocol_editor.textCursor().selectedText(), 'Level')
        ide.action_view_script()
        ide.action_find()
        self.assertTrue(ide._script_tools.isVisibleTo(ide))

        # Calling find again keeps bar visible
        ide.action_find()
        self.assertTrue(ide._script_tools.isVisibleTo(ide))

    def test_navigator(self):
        # Test the model navigator
        ide = self.create()
        self.set_model(ide, SMALL_MODEL)
        self.assertFalse(ide._tool_view_navigator.isChecked())
        ide.action_toggle_navigator()
        self.assertTrue(ide._tool_view_navigator.isChecked())
        self.assertTrue(ide._model_tools.isVisibleTo(ide))

        # Navigator is updated after change
        ide.change_model_timeout()
        lw = ide._model_navigator._list_widget
        self.assertEqual([lw.item(i).text() for i in range(lw.count())],
                         ['c', 'e'])

        # Selecting an item moves the cursor
        # (The stored position is the end of the component header)
        lw.setCurrentRow(0)
        pos = SMALL_MODEL.index('[c]') + 3
        self.assertEqual(ide._model_editor.textCursor().position(), pos)
        lw.setCurrentRow(1)
        pos = SMALL_MODEL.index('[e]') + 3
        self.assertEqual(ide._model_editor.textCursor().position(), pos)

        # Hide again
        ide.action_toggle_navigator()
        self.assertFalse(ide._tool_view_navigator.isChecked())
        self.assertFalse(ide._model_tools.isVisibleTo(ide))

    def test_comment_and_whitespace(self):
        # Test commenting and trimming whitespace
        ide = self.create()
        self.set_model(ide, SMALL_MODEL)
        e = ide._model_editor
        self.goto(e, 'b = 2')
        ide.action_comment()
        self.assertIn('#b = 2', e.get_text())
        ide.action_comment()
        self.assertNotIn('#b = 2', e.get_text())
        self.assertIn('b = 2', e.get_text())

        self.set_model(ide, '[[model]]   \n[c]  \nx = 1   \n')
        ide.action_trim_whitespace()
        self.assertEqual(e.get_text(), '[[model]]\n[c]\nx = 1\n')
        self.assertIn('Trailing whitespace removed.', self.console(ide))

    def test_save(self):
        # Test save and save-as
        ide = self.create()
        self.set_model(ide, SMALL_MODEL)
        self.assertTrue(ide._have_changes)

        # Save as, cancelled
        ide.action_save()
        self.get_save.assert_called_once()
        self.assertIsNone(ide._file)
        self.assertTrue(ide._have_changes)

        # Save as
        path = self.tdir / 'test.mmt'
        self.get_save.return_value = (str(path), '')
        ide.action_save()
        self.assertEqual(ide._file, path)
        self.assertTrue(path.is_file())
        self.assertFalse(ide._have_changes)
        self.assertFalse(ide._tool_save.isEnabled())
        self.assertTrue(ide._tool_save_as.isEnabled())
        self.assertEqual(ide._recent_files[0], path)
        self.assertEqual(pathlib.Path(os.getcwd()), self.tdir)
        self.assertEqual(
            ide.statusBar().currentMessage(), f'File saved as {path}')
        self.assertEqual(ide.windowTitle(),
                         f'test.mmt - Myokit IDE {myokit.__version__}')
        m, p, x = myokit.load(path)
        self.assertEqual(m.name(), 'small')
        self.assertIsInstance(p, myokit.Protocol)
        self.assertIn(x.strip(), myokit.default_script())

        # Save (without dialog)
        self.get_save.reset_mock()
        ide._model_editor.appendPlainText('[d]\ny = 4')
        self.assertTrue(ide._have_changes)
        ide.action_save()
        self.get_save.assert_not_called()
        self.assertFalse(ide._have_changes)
        m = myokit.load_model(path)
        self.assertTrue(m.has_variable('d.y'))

        # Save as other file
        path2 = self.tdir / 'test2.mmt'
        self.get_save.return_value = (str(path2), '')
        ide.action_save_as()
        self.get_save.assert_called_once()
        self.assertEqual(ide._file, path2)
        self.assertTrue(path2.is_file())
        self.assertEqual(ide._recent_files, [path2, path])

        # Settings were saved
        with open(self.settings, 'r') as f:
            self.assertIn(str(path2), f.read())

    def test_save_error(self):
        # Test error handling when saving
        ide = self.create()
        ide._file = self.tdir   # A directory, so can't write
        self.assertFalse(ide.save_file())
        self.warning.assert_called_once()
        self.assertEqual(
            ide.statusBar().currentMessage(), 'Error saving file.')
        self.assertTrue(ide._tool_save.isEnabled())
        self.assertTrue(ide._tool_save_as.isEnabled())

        # Unexpected error
        self.warning.reset_mock()
        ide._file = self.tdir / 'x.mmt'
        with unittest.mock.patch('myokit.save', side_effect=ValueError('x')):
            self.assertFalse(ide.save_file())
        self.warning.assert_called_once()
        self.assertEqual(
            ide.statusBar().currentMessage(), 'Unexpected error saving file.')
        self.assertFalse(os.path.exists(ide._file))

        # Save as, to a directory that doesn't exist
        self.warning.reset_mock()
        ide._file = self.tdir / 'x.mmt'
        self.get_save.return_value = (
            str(self.tdir / 'missing' / 'y.mmt'), '')
        self.assertFalse(ide.save_file(save_as=True))
        self.warning.assert_called_once()
        self.assertEqual(
            ide.statusBar().currentMessage(), 'Error saving file.')
        self.assertEqual(ide._file, self.tdir / 'x.mmt')

    def test_prompt_save_changes(self):
        # Test asking to save changes
        sb = self.QtWidgets.QMessageBox.StandardButton
        ide = self.create()
        ide._model_editor.document().setModified(False)
        ide._protocol_editor.document().setModified(False)
        ide._script_editor.document().setModified(False)

        # No changes: no question
        self.assertTrue(ide.prompt_save_changes(cancel=True))
        self.question.assert_not_called()

        # Changes: No, Cancel, Yes (but cancel save), Yes
        self.set_model(ide, SMALL_MODEL)
        self.question.return_value = sb.No
        self.assertTrue(ide.prompt_save_changes(cancel=True))
        self.assertIn('new file', self.question.call_args[0][2])
        self.assertEqual(self.question.call_args[0][3],
                         sb.Yes | sb.No | sb.Cancel)
        self.question.return_value = sb.Cancel
        self.assertFalse(ide.prompt_save_changes(cancel=True))
        self.question.return_value = sb.Yes
        self.assertFalse(ide.prompt_save_changes())
        self.assertEqual(self.question.call_args[0][3], sb.Yes | sb.No)
        path = self.tdir / 'saved.mmt'
        self.get_save.return_value = (str(path), '')
        self.assertTrue(ide.prompt_save_changes())
        self.assertTrue(path.is_file())
        self.assertFalse(ide._have_changes)

        # Message includes file name
        ide._model_editor.appendPlainText('# Hi')
        self.question.return_value = sb.No
        ide.prompt_save_changes()
        self.assertIn(str(path), self.question.call_args[0][2])

    def test_new_and_open(self):
        # Test the new and open actions
        sb = self.QtWidgets.QMessageBox.StandardButton
        ide = self.create(LR)
        lr_code = ide._model_editor.get_text()

        # New, without changes
        ide.action_new()
        self.question.assert_not_called()
        self.assertIsNone(ide._file)
        self.assertEqual(ide._model_editor.get_text(), '[[model]]\n')

        # New, with changes, cancelled
        self.set_model(ide, SMALL_MODEL)
        self.question.return_value = sb.Cancel
        ide.action_new()
        self.assertEqual(ide._model_editor.get_text(), SMALL_MODEL)

        # Open, cancelled at question
        ide.action_open()
        self.get_open.assert_not_called()

        # Open, cancelled at dialog
        self.question.return_value = sb.No
        ide.action_open()
        self.get_open.assert_called_once()
        self.assertEqual(ide._model_editor.get_text(), SMALL_MODEL)

        # Open file
        self.get_open.return_value = (LR, '')
        ide.action_open()
        self.assertEqual(ide._file, pathlib.Path(LR).absolute())
        self.assertEqual(ide._model_editor.get_text(), lr_code)

        # Open file that doesn't exist
        self.get_open.return_value = (str(self.tdir / 'nope.mmt'), '')
        ide.action_open()
        self.warning.assert_called_once()
        self.assertEqual(
            ide.statusBar().currentMessage(), '"Open file" failed')
        self.assertEqual(ide._file, pathlib.Path(LR).absolute())

        # New, with changes, accepted
        self.set_model(ide, SMALL_MODEL)
        ide.action_new()
        self.assertEqual(ide._model_editor.get_text(), '[[model]]\n')

    def test_open_recent(self):
        # Test opening a recent file
        ide = self.create(LR)
        ide.load_file(BR)
        lr = pathlib.Path(LR).absolute()
        br = pathlib.Path(BR).absolute()
        self.assertEqual(ide._recent_files, [br, lr])
        self.assertEqual(ide._recent_file_tools[1].text(), '2. lr-1991.mmt')

        # Open via the menu action
        with unittest.mock.patch.object(
                ide, 'sender', return_value=ide._recent_file_tools[1]):
            ide.action_open_recent()
        self.assertEqual(ide._file, lr)
        self.assertEqual(ide._recent_files, [lr, br])

        # Missing file
        copy = self.tdir / 'copy.mmt'
        with open(LR, 'r') as f, open(copy, 'w') as g:
            g.write(f.read())
        ide.load_file(copy)
        os.remove(copy)
        with unittest.mock.patch.object(
                ide, 'sender', return_value=ide._recent_file_tools[0]):
            ide.action_open_recent()
        self.assertIn('Failed to load file', self.console(ide))

        # Recent files are limited
        for i in range(self.ide.N_RECENT_FILES + 2):
            ide.add_recent_file(self.tdir / f'{i}.mmt')
        self.assertEqual(len(ide._recent_files), self.ide.N_RECENT_FILES)
        for t in ide._recent_file_tools:
            self.assertTrue(t.isVisible())

    def test_import_model(self):
        # Test importing models with a file dialog
        sb = self.QtWidgets.QMessageBox.StandardButton
        ide = self.create()
        self.set_model(ide, SMALL_MODEL)

        # Cancelled at question
        self.question.return_value = sb.Cancel
        ide.action_import_model('cellml')
        self.get_open.assert_not_called()

        # Cancelled at dialog
        self.question.return_value = sb.No
        ide.action_import_model('cellml')
        self.get_open.assert_called_once()
        self.assertEqual(ide._model_editor.get_text(), SMALL_MODEL)

        # CellML
        path = str(DIR_FORMATS / 'cellml' / 'lr-1991-exported-2.cellml')
        self.get_open.return_value = (path, '')
        ide.action_import_model('cellml')
        self.assertIn('Model imported successfully.', self.console(ide))
        self.assertIsInstance(ide.model(), myokit.Model)

        # Invalid file
        path = str(DIR_FORMATS / 'cellml' / 'invalid-file.cellml')
        self.get_open.return_value = (path, '')
        ide.action_import_model('cellml')
        self.assertIn('Model import failed.', self.console(ide))
        self.assertEqual(
            ide.statusBar().currentMessage(), 'Model import failed.')

        # Unknown importer
        self.get_open.return_value = (path, '')
        ide.action_import_model('not-an-importer')
        self.warning.assert_called_once()

    def test_import_abf_protocol(self):
        # Test importing a protocol from an ABF file
        ide = self.create()

        # Cancelled
        ide.action_import_abf_protocol()
        self.get_open.assert_called_once()

        # Import
        path = str(DIR_FORMATS / 'abf-v2.abf')
        self.get_open.return_value = (path, '')
        ide.action_import_abf_protocol()
        self.assertIn('Protocol imported successfully.', self.console(ide))
        p = ide.protocol()
        self.assertIsInstance(p, myokit.Protocol)
        self.assertTrue(len(p) > 0)
        self.assertEqual(ide._path, pathlib.Path(str(DIR_FORMATS)).absolute())

        # Failed import, with warnings
        def protocol(path):
            warnings.warn('Careful now')
            raise myokit.ImportError('Not an ABF file')

        importer = unittest.mock.Mock()
        importer.protocol.side_effect = protocol
        with unittest.mock.patch(
                'myokit.formats.importer', return_value=importer):
            ide.action_import_abf_protocol()
        self.assertIn('Warning: Careful now', self.console(ide))
        self.assertIn('Protocol import failed.', self.console(ide))
        self.assertIn('Not an ABF file', self.console(ide))
        self.assertEqual(
            ide.statusBar().currentMessage(), 'Protocol import failed.')
        self.warning.assert_not_called()

        # Unexpected error
        path = self.tdir / 'bad.abf'
        with open(path, 'wb') as f:
            f.write(b'Not an ABF file at all')
        self.get_open.return_value = (str(path), '')
        ide.action_import_abf_protocol()
        self.warning.assert_called_once()

    def test_export(self):
        # Test exporting models and runnables
        ide = self.create(LR)

        # Cancelled
        ide.action_export_model('html', '.html', self.ide.FILTER_HTML)
        self.get_save.assert_called_once()
        self.assertIn('lr-1991.html', self.get_save.call_args[0][2])
        self.assertNotIn('Export successful.', self.console(ide))

        # Export model
        path = self.tdir / 'model.html'
        self.get_save.return_value = (str(path), '')
        ide.action_export_model('html', '.html', self.ide.FILTER_HTML)
        self.assertTrue(path.is_file())
        self.assertIn('Export successful.', self.console(ide))

        # Export to CellML (uses protocol)
        path = self.tdir / 'model.cellml'
        self.get_save.return_value = (str(path), '')
        ide.action_export_model('cellml2', '.cellml')
        self.assertTrue(path.is_file())
        m = myokit.formats.importer('cellml').model(path)
        self.assertIsInstance(m, myokit.Model)

        # Suggested path for new file, and without extension
        ide.action_new()
        self.set_model(ide, SMALL_MODEL)
        self.get_save.return_value = ('', '')
        ide.action_export_model('html', '.html')
        self.assertIn('new-model.html', self.get_save.call_args[0][2])
        ide.action_export_model('html')
        self.assertEqual(self.get_save.call_args[0][2], str(ide._path))

        # Exporter that doesn't support models
        self.warning.assert_not_called()
        ide.action_export_model('ansic')
        self.warning.assert_called_once()
        self.assertIn('does not support export of model',
                      self.warning.call_args[0][2])

        # Model with errors
        self.get_save.reset_mock()
        self.set_model(ide, BAD_MODEL)
        ide.action_export_model('html', '.html')
        self.get_save.assert_not_called()
        ide.action_export_runnable('ansic')
        self.get_save.assert_not_called()

        # Export runnable
        ide.load_file(LR)
        path = self.tdir / 'runnable'
        self.get_save.return_value = (str(path), '')
        ide.action_export_runnable('ansic')
        self.assertTrue(path.is_dir())
        self.assertTrue(len(os.listdir(path)) > 0)
        self.assertIn('Export successful.', self.console(ide))

        # Exporter that doesn't support runnables
        self.warning.reset_mock()
        ide.action_export_runnable('html')
        self.warning.assert_called_once()

        # Protocol with errors
        self.get_save.reset_mock()
        self.set_text(ide._protocol_editor, '[[protocol]]\nx\n')
        ide.action_export_runnable('ansic')
        self.get_save.assert_not_called()

        # Export errors are reported as failures
        ide.load_file(LR)
        ide._console.clear()
        self.get_save.return_value = (str(self.tdir / 'fail'), '')
        err = myokit.ExportError('Something went wrong')
        with unittest.mock.patch(
                'myokit.formats.html.HTMLExporter.model', side_effect=err):
            ide.action_export_model('html')
        text = self.console(ide)
        self.assertIn('Export failed.', text)
        self.assertIn('Something went wrong', text)
        self.assertNotIn('Export successful.', text)
        ide._console.clear()
        with unittest.mock.patch(
                'myokit.formats.ansic.AnsiCExporter.runnable',
                side_effect=err):
            ide.action_export_runnable('ansic')
        text = self.console(ide)
        self.assertIn('Export failed.', text)
        self.assertIn('Something went wrong', text)
        self.assertNotIn('Export successful.', text)

    def test_model_stats(self):
        # Test showing model statistics
        ide = self.create()
        self.set_model(ide, '')
        ide.action_model_stats()
        self.assertIn('No model to parse', self.console(ide))
        self.set_model(ide, BAD_MODEL)
        ide.action_model_stats()
        self.assertIn('Unable to parse model', self.console(ide))
        self.set_model(ide, SMALL_MODEL)
        ide._console.clear()
        self.assertEqual(self.console(ide), '')
        ide.action_model_stats()
        text = self.console(ide)
        self.assertIn('Name: small', text)
        self.assertIn('Number of components: 2', text)
        self.assertIn('Number of variables: 4', text)
        self.assertIn('state:  1', text)

        # Errors
        with unittest.mock.patch.object(
                ide._model_editor, 'get_text', side_effect=ValueError('x')):
            ide.action_model_stats()
        self.warning.assert_called_once()
        self.assertEqual(ide.statusBar().currentMessage(),
                         'Gathering model statistics failed.')

    def test_units(self):
        # Test unit checking and removal of units
        sb = self.QtWidgets.QMessageBox.StandardButton
        ide = self.create()
        self.set_model(ide, SMALL_MODEL)
        ide.action_check_units_strict()
        self.assertIn('Units ok! (checked in strict mode)', self.console(ide))
        ide.action_check_units_tolerant()
        self.assertIn('Units ok! (checked in tolerant mode)',
                      self.console(ide))

        # Incompatible units: jump to error
        code = SMALL_MODEL.replace('b = 2 * a', 'b = 2 * a + 1 [mV]')
        self.set_model(ide, code)
        ide._model_editor.jump_to(0, 0)
        ide.action_check_units_strict()
        self.assertIn('Incompatible units', self.console(ide))
        self.assertEqual(ide._model_editor.cursor_position()[0], 11)
        ide._model_editor.jump_to(0, 0)
        ide.action_check_units_tolerant()
        self.assertEqual(ide._model_editor.cursor_position()[0], 11)

        # Model errors
        ide._console.clear()
        self.set_model(ide, BAD_MODEL)
        ide.action_check_units_strict()
        ide.action_check_units_tolerant()
        self.assertNotIn('Units ok', self.console(ide))

        # Remove units, cancelled
        self.set_model(ide, SMALL_MODEL)
        ide.action_clear_units()
        self.question.assert_called_once()
        self.assertEqual(ide._model_editor.get_text(), SMALL_MODEL)

        # Remove units (literals keep their units)
        self.question.return_value = sb.Yes
        self.set_model(ide, code.replace('[mV]', '[1/ms]'))
        ide.action_clear_units()
        text = ide._model_editor.get_text()
        self.assertIn('b = 2 * a + 1\n', text)
        self.assertIn('a = 3 [1/ms]\n', text)
        self.assertIn('    in [1/ms]', text)
        self.assertIn('Removed all expression units.', self.console(ide))
        self.assertIsInstance(ide.model(), myokit.Model)

        # Remove units, with error in model
        self.set_model(ide, BAD_MODEL)
        ide.action_clear_units()
        self.assertEqual(
            ide.statusBar().currentMessage(), 'Error parsing model')
        self.set_model(ide, SMALL_MODEL)
        with unittest.mock.patch(
                'myokit.strip_expression_units',
                side_effect=myokit.IntegrityError('Bad model')):
            ide.action_clear_units()
        self.assertEqual(
            ide.statusBar().currentMessage(), 'Model integrity error')
        self.assertEqual(ide._model_editor.get_text(), SMALL_MODEL)

        # Unexpected error
        self.warning.assert_not_called()
        with unittest.mock.patch(
                'myokit.strip_expression_units', side_effect=ValueError):
            ide.action_clear_units()
        self.warning.assert_called_once()

    def test_analysis(self):
        # Test component cycles and state derivatives
        ide = self.create()
        self.set_model(ide, SMALL_MODEL)
        ide.action_component_cycles()
        self.assertIn('No component cycles found.', self.console(ide))

        ide.action_state_derivatives()
        self.assertIn('c.x', self.console(ide))
        self.assertIn('-6', self.console(ide))
        ide._console.clear()
        ide.action_state_derivatives2()
        self.assertIn('c.x', self.console(ide))

        # Numerical error
        self.set_model(
            ide, SMALL_MODEL.replace('b = 2 * a', 'b = 2 * a / 0 [1]'))
        ide.action_state_derivatives()
        self.assertIn('A numerical error occurred', self.console(ide))
        ide._console.clear()
        ide.action_state_derivatives2()
        self.assertNotIn('A numerical error occurred', self.console(ide))
        self.assertIn('c.x', self.console(ide))

        # Component cycles
        code = SMALL_MODEL + '[d]\ny = c.a + 1 [1/ms]\n    in [1/ms]\n'
        code = code.replace('b = 2 * a\n', 'b = 2 * d.y\n')
        self.set_model(ide, code)
        ide.action_component_cycles()
        self.assertIn('Found component cycles:', self.console(ide))

        # Errors and empty models
        ide._console.clear()
        self.set_model(ide, BAD_MODEL)
        ide.action_component_cycles()
        ide.action_state_derivatives()
        self.assertIn('Errors found in model', self.console(ide))
        self.set_model(ide, '')
        ide.action_state_derivatives()
        self.assertIn('No model found', self.console(ide))
        self.warning.assert_not_called()

    def test_variable_actions(self):
        # Test the actions working on the selected variable
        ide = self.create()
        self.set_model(ide, SMALL_MODEL)
        e = ide._model_editor

        # No variable selected
        e.jump_to(0, 0)
        self.assertIsNone(ide.selected_variable())
        ide.action_variable_info()
        self.assertIn('No variable selected.', self.console(ide))
        for action in (
                ide.action_variable_definition,
                ide.action_variable_dependencies,
                ide.action_variable_evaluation,
                ide.action_variable_users,
                ide.action_variable_graph):
            ide._console.clear()
            action()
            self.assertIn('No variable selected.', self.console(ide))

        # Variable selected
        self.goto(e, 'b = 2')
        b = ide.selected_variable()
        self.assertIsInstance(b, myokit.Variable)
        self.assertEqual(b.qname(), 'c.b')
        ide._console.clear()
        ide.action_variable_info()
        self.assertIn('c.b', self.console(ide))
        ide._console.clear()
        ide.action_variable_evaluation()
        self.assertIn('c.b = 2 * c.a', self.console(ide))
        ide._console.clear()
        ide.action_variable_dependencies()
        self.assertIn('c.a = 3', self.console(ide))
        ide._console.clear()
        ide.action_variable_users()
        self.assertIn('The following variables depend on c.b:',
                      self.console(ide))
        self.assertIn('  c.x', self.console(ide))

        # Name in an expression points to variable
        self.goto(e, 'a\n    in [1/ms]\ndot')
        self.assertEqual(ide.selected_variable().qname(), 'c.a')
        ide.action_variable_definition()
        line = SMALL_MODEL.splitlines().index('a = 3 [1/ms]')
        self.assertEqual(e.cursor_position(), (line, 0))

        # State users
        self.goto(e, 'dot(x)')
        ide._console.clear()
        ide.action_variable_users()
        self.assertIn('No variables depend on dot(c.x).', self.console(ide))
        self.assertIn('The following variables depend on c.x:',
                      self.console(ide))

        # Variable without users
        self.goto(e, 't = 0')
        ide._console.clear()
        ide.action_variable_users()
        self.assertIn('No variables depend on e.t.', self.console(ide))

        # Errors in model
        self.set_model(ide, BAD_MODEL)
        self.goto(e, 'a = 3')
        self.assertIs(ide.selected_variable(), False)
        ide._console.clear()
        ide.action_variable_info()
        self.assertIn('Errors found in model', self.console(ide))
        self.set_model(ide, '')
        self.assertIs(ide.selected_variable(), False)

        # Not on model tab
        ide.action_view_protocol()
        self.assertIsNone(ide.selected_variable())
        for action in (
                ide.action_variable_definition,
                ide.action_variable_dependencies,
                ide.action_variable_evaluation,
                ide.action_variable_info,
                ide.action_variable_users):
            ide._console.clear()
            action()
            self.assertIn('can only be displayed for model variables',
                          self.console(ide))
        ide._console.clear()
        ide.action_variable_graph()
        self.assertIn('Only variables on the model editing tab',
                      self.console(ide))
        self.warning.assert_not_called()

    def test_variable_graph(self):
        # Test graphing a variable
        ide = self.create()
        self.set_model(ide, SMALL_MODEL)
        e = ide._model_editor

        self.goto(e, 'a = 3')
        ide.action_variable_graph()
        self.assertIn('Cannot graph constants.', self.console(ide))
        self.goto(e, 't = 0')
        ide.action_variable_graph()
        self.assertIn('Cannot graph bound variables.', self.console(ide))

        # Only variables on the model tab can be graphed
        import myokit.gui.vargrapher as vargrapher
        ide.action_view_protocol()
        self.goto(e, 'dot(x)')
        with unittest.mock.patch.object(vargrapher, 'VarGrapher') as g:
            ide.action_variable_graph()
            g.assert_not_called()
        self.assertIn('Only variables on the model editing tab',
                      self.console(ide))
        ide.action_view_model()

        with unittest.mock.patch.object(vargrapher.VarGrapher, 'show') as s:
            self.goto(e, 'dot(x)')
            ide.action_variable_graph()
            s.assert_called_once()
        graphers = ide.findChildren(vargrapher.VarGrapher)
        self.assertEqual(len(graphers), 1)
        for g in graphers:
            g.close()
            g.deleteLater()
        self.warning.assert_not_called()

    def test_plots(self):
        # Test the actions that create matplotlib figures
        import matplotlib.pyplot as plt
        ide = self.create(LR)
        for action in (
                ide.action_component_dependency_graph,
                ide.action_variable_dependency_graph,
                ide.action_state_matrix,
                ide.action_preview_protocol):
            plt.close('all')
            self.show.reset_mock()
            action()
            self.show.assert_called_once()
            self.assertEqual(len(plt.get_fignums()), 1)
        self.warning.assert_not_called()
        plt.close('all')

        # Protocol preview with non-default range
        self.set_text(
            ide._protocol_editor,
            '[[protocol]]\n-80 0 100 0 0\n20 200 100 0 0\n')
        ide.action_preview_protocol()
        self.assertEqual(plt.gca().get_ylim(), (-90, 30))
        plt.close('all')

        # Errors: no figures created
        self.show.reset_mock()
        self.set_model(ide, BAD_MODEL)
        self.set_text(ide._protocol_editor, '[[protocol]]\nx\n')
        ide.action_component_dependency_graph()
        ide.action_variable_dependency_graph()
        ide.action_state_matrix()
        ide.action_preview_protocol()
        self.assertIn('Errors in protocol', self.console(ide))
        self.set_text(ide._protocol_editor, '')
        ide.action_preview_protocol()
        self.assertIn('No protocol specified', self.console(ide))
        self.show.assert_not_called()
        self.assertEqual(len(plt.get_fignums()), 0)
        self.warning.assert_not_called()

        # Unexpected errors are shown in a dialog
        ide.load_file(LR)
        with unittest.mock.patch(
                'myokit.lib.deps.plot_component_dependency_graph',
                side_effect=ValueError('Oops')):
            ide.action_component_dependency_graph()
        self.warning.assert_called_once()
        self.assertIn('ValueError: Oops', self.warning.call_args[0][2])

    def test_run(self):
        # Test running the embedded script
        ide = self.create()
        self.set_model(ide, SMALL_MODEL)
        self.set_text(ide._script_editor, 
            '[[script]]\n'
            'm = get_model()\n'
            'p = get_protocol()\n'
            'print(m.name() + " with " + str(len(p)) + " events")\n')
        ide.action_run()
        text = self.console(ide)
        self.assertIn('Running embedded script.', text)
        self.assertIn('small with 1 events', text)
        self.assertIn('Done.', text)
        self.assertIsNone(self.QtWidgets.QApplication.overrideCursor())

        # Script modifies a clone, not the cached model
        self.set_text(ide._script_editor, 
            '[[script]]\nget_model().get("c.a").set_rhs(7)\n')
        ide.action_run()
        self.assertEqual(ide.model().get('c.a').eval(), 3)

        # Script error
        ide._console.clear()
        self.set_text(
            ide._script_editor, '[[script]]\nraise ValueError("x")\n')
        ide.action_run()
        self.assertIn('An error has occurred', self.console(ide))
        self.assertIn('ValueError', self.console(ide))

        # Cancelled simulation
        ide._console.clear()
        self.set_text(ide._script_editor, 
            '[[script]]\nimport myokit\n'
            'raise myokit.SimulationCancelledError()\n')
        ide.action_run()
        self.assertIn('Simulation canceled by user.', self.console(ide))

        # Model or protocol error: script is not run
        ide._console.clear()
        self.set_text(ide._script_editor, '[[script]]\nprint("Hello")\n')
        self.set_model(ide, BAD_MODEL)
        ide.action_run()
        self.assertNotIn('Hello', self.console(ide))
        self.set_model(ide, SMALL_MODEL)
        self.set_text(ide._protocol_editor, '[[protocol]]\nx\n')
        ide.action_run()
        self.assertNotIn('Hello', self.console(ide))
        self.assertIsNone(self.QtWidgets.QApplication.overrideCursor())

        # Empty model and protocol: script still runs
        self.set_model(ide, '')
        self.set_text(ide._protocol_editor, '')
        ide.action_run()
        self.assertIn('Hello', self.console(ide))

    def test_explorer(self):
        # Test opening and closing the explorer (without running it)
        import myokit.gui.explorer as explorer
        ide = self.create()
        self.set_model(ide, SMALL_MODEL)
        with unittest.mock.patch.object(explorer.Explorer, 'show') as s:
            ide.action_explore()
            s.assert_called_once()
        ex = ide._explorer
        self.assertIsInstance(ex, explorer.Explorer)
        self.assertEqual(float(ex._run_field.text()), 1000)

        # Explorer is re-used
        with unittest.mock.patch.object(explorer.Explorer, 'show'):
            ide.action_explore()
        self.assertIs(ide._explorer, ex)

        # Simulation creation method
        sim = ex._sim_method
        self.set_text(ide._protocol_editor, '[[protocol]]\nx\n')
        self.assertEqual(sim(), 'Errors in protocol')
        self.set_model(ide, BAD_MODEL)
        self.assertEqual(sim(), 'Errors in model')
        self.set_model(ide, '')
        self.assertEqual(sim(), 'Empty model definition')

        # Loading a file closes the explorer
        ide.new_file()
        self.assertIsNone(ide._explorer)
        ide.close_explorer()
        self.assertIsNone(ide._explorer)

        # Duration in seconds
        self.set_model(ide, SMALL_MODEL.replace('[ms]', '[s]').replace(
            '[1/ms]', '[1/s]'))
        self.set_text(ide._protocol_editor, '')
        with unittest.mock.patch.object(explorer.Explorer, 'show'):
            ide.action_explore()
        self.assertEqual(float(ide._explorer._run_field.text()), 1)
        ide.close_explorer()

        self.set_text(ide._protocol_editor, myokit.default_protocol().code())
        with unittest.mock.patch.object(explorer.Explorer, 'show'):
            ide.action_explore()
        self.assertEqual(float(ide._explorer._run_field.text()), 1)

    def test_about(self):
        # Test the about dialog
        ide = self.create()
        ide.action_about()
        self.about.assert_called_once()
        self.assertIn('Myokit IDE', self.about.call_args[0][2])

    def test_close_event(self):
        # Test closing the IDE
        sb = self.QtWidgets.QMessageBox.StandardButton
        ide = self.create()
        self.set_model(ide, SMALL_MODEL)

        # Cancel close, by not completing save
        self.question.return_value = sb.Yes
        event = self.QtGui.QCloseEvent()
        ide.closeEvent(event)
        self.assertFalse(event.isAccepted())
        self.assertTrue(self.settings.is_file())

        # Close without saving
        self.question.return_value = sb.No
        event = self.QtGui.QCloseEvent()
        event.ignore()
        ide.closeEvent(event)
        self.assertTrue(event.isAccepted())

        # Without event
        ide.closeEvent()

    def test_tabbed_toolbar(self):
        # Test the TabbedToolBar class
        bar = self.ide.TabbedToolBar()
        self.addCleanup(bar.deleteLater)
        w1 = self.QtWidgets.QWidget()
        w2 = self.QtWidgets.QWidget()
        bar.add(w1, 'One')
        bar.add(w2, 'Two')
        events = []
        bar.tab_toggled.connect(lambda w, v: events.append((w, v)))
        self.assertEqual(bar.count(), 0)
        self.assertFalse(bar.isVisibleTo(bar.parentWidget()))

        bar.toggle(w1)
        self.assertEqual(bar.count(), 1)
        self.assertEqual(bar.tabText(0), 'One')
        self.assertEqual(events, [(w1, True)])
        bar.toggle(w2, True)
        self.assertEqual(bar.count(), 2)
        self.assertIs(bar.currentWidget(), w2)

        # Explicitly setting to current status does nothing
        bar.toggle(w1, True)
        self.assertIs(bar.currentWidget(), w1)
        bar.toggle(w1, True)
        self.assertEqual(bar.count(), 2)
        self.assertEqual(len(events), 2)

        # Close button
        bar._close_button_hit(0)
        self.assertEqual(bar.count(), 1)
        self.assertEqual(events[-1], (w1, False))
        bar.toggle(w1, False)
        self.assertEqual(len(events), 3)
        bar.toggle(w2)
        self.assertEqual(bar.count(), 0)
        self.assertEqual(events[-1], (w2, False))

        # Key presses
        Qt = self.Qt
        event = self.QtGui.QKeyEvent(
            self.QtCore.QEvent.Type.KeyPress, Qt.Key.Key_Escape,
            Qt.KeyboardModifier.NoModifier)
        bar.keyPressEvent(event)
        event = self.QtGui.QKeyEvent(
            self.QtCore.QEvent.Type.KeyPress, Qt.Key.Key_A,
            Qt.KeyboardModifier.NoModifier)
        bar.keyPressEvent(event)

    def test_model_navigator(self):
        # Test the ModelNavigator class
        nav = self.ide.ModelNavigator()
        self.addCleanup(nav.deleteLater)
        lines = []
        nav.item_changed.connect(lines.append)
        nav.set_positions([('[b]', 10), ('[a]', 20)])
        lw = nav._list_widget
        self.assertEqual([lw.item(i).text() for i in range(lw.count())],
                         ['a', 'b'])
        lw.setCurrentRow(0)
        lw.setCurrentRow(1)
        self.assertEqual(lines, [20, 10])

        # Same positions: no update
        nav.set_positions([('[b]', 10), ('[a]', 20)])
        self.assertEqual(lw.currentRow(), 1)
        nav.set_positions([])
        self.assertEqual(lw.count(), 0)

    def test_console(self):
        # Test the Console class
        c = self.ide.Console()
        self.addCleanup(c.deleteLater)
        self.assertTrue(c.isReadOnly())
        c.write('Hello  \n')
        c.write('\n')
        c.flush()
        text = c.toPlainText()
        self.assertEqual(len(text.splitlines()), 1)
        self.assertTrue(text.endswith('] Hello'))
        self.assertTrue(text.startswith('['))
        c.clear()
        self.assertEqual(c.toPlainText(), '')

        # Write without text, or with non-string objects
        c.write()
        c.write(None)
        c.write(12)
        lines = c.toPlainText().splitlines()
        self.assertEqual(len(lines), 3)
        self.assertTrue(lines[0].rstrip().endswith(']'))
        self.assertTrue(lines[2].endswith('] 12'))
        c.clear()

        # Use as stdout
        import contextlib
        with contextlib.redirect_stdout(c):
            print('Hi there')
        self.assertIn('Hi there', c.toPlainText())


if __name__ == '__main__':
    unittest.main()
