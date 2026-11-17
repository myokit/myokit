#!/usr/bin/env python3
#
# Tests the myokit.gui.source module.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import configparser
import io
import unittest
import unittest.mock

from myokit.tests import qt_application


class GuiSourceTest(unittest.TestCase):
    """ Tests the source code editor and highlighters in myokit.gui.source """

    @classmethod
    def setUpClass(cls):
        cls.app = qt_application()
        import myokit.gui
        import myokit.gui.source
        cls.s = myokit.gui.source
        cls.Qt = myokit.gui.Qt
        cls.QtCore = myokit.gui.QtCore
        cls.QtGui = myokit.gui.QtGui
        cls.QtWidgets = myokit.gui.QtWidgets

    def setUp(self):
        self._widgets = []

    def tearDown(self):
        for w in reversed(self._widgets):
            w.close()
            w.deleteLater()
        self._widgets = []
        self.app.processEvents()

    # Helpers

    def editor(self, text=None):
        """ Creates an editor, optionally with text, closed on teardown. """
        e = self.s.Editor()
        self._widgets.append(e)
        e.resize(400, 300)
        if text is not None:
            e.set_text(text)
        return e

    def finder(self, editor):
        """ Creates a find/replace widget for an editor. """
        f = self.s.FindReplaceWidget(None, editor)
        self._widgets.append(f)
        return f

    def key(self, widget, key, mod=None, text=''):
        """ Sends a key press event directly to ``widget.keyPressEvent``. """
        Qt = self.Qt
        if mod is None:
            mod = Qt.KeyboardModifier.NoModifier
        event = self.QtGui.QKeyEvent(
            self.QtCore.QEvent.Type.KeyPress, key, mod, text)
        widget.keyPressEvent(event)
        return event

    def select(self, editor, start, end):
        """ Selects from ``start`` to ``end`` in an editor. """
        c = editor.textCursor()
        c.setPosition(start)
        c.setPosition(end, self.QtGui.QTextCursor.MoveMode.KeepAnchor)
        editor.setTextCursor(c)

    def pos(self, editor):
        return editor.textCursor().position()

    def highlight(self, highlighter_class, text):
        """
        Creates an editor with the given text and highlighter, and returns a
        list ``(text, state, formats)`` per block, where ``formats`` is a
        list of tuples ``(start, length, format)``.
        """
        e = self.editor(text)
        h = highlighter_class(e.document())
        h.rehighlight()
        blocks = []
        b = e.document().begin()
        while b.isValid():
            blocks.append((
                b.text(),
                b.userState(),
                [(f.start, f.length, f.format) for f in b.layout().formats()],
            ))
            b = b.next()
        return blocks

    def fmt(self, formats, position):
        """ Returns the format applied at ``position``, or ``None``. """
        result = None
        for start, length, f in formats:
            if start <= position < start + length:
                result = f
        return result

    def assertFmt(self, formats, position, style):
        f = self.fmt(formats, position)
        self.assertIsNotNone(f, f'No format at position {position}')
        self.assertEqual(f, style, f'Unexpected format at {position}')

    def assertNoFmt(self, formats, position):
        self.assertIsNone(self.fmt(formats, position))

    # Editor: text and cursor

    def test_get_set_text(self):
        # Test setting and getting text, including the empty case
        e = self.editor()
        self.assertEqual(e.get_text(), '')
        e.set_text('hello\nworld')
        self.assertEqual(e.get_text(), 'hello\nworld')
        self.assertEqual(e.blockCount(), 2)

        # Non-string values are converted
        e.set_text(123)
        self.assertEqual(e.get_text(), '123')

        # Empty text clears and resets undo/modified state
        e.set_text('abc')
        e.document().setModified(True)
        e.set_text('')
        self.assertEqual(e.get_text(), '')
        self.assertFalse(e.document().isModified())
        self.assertFalse(e.document().isUndoAvailable())
        e.set_text(None)
        self.assertEqual(e.get_text(), '')

    def test_replace(self):
        # Replace keeps undo history
        e = self.editor('original text')
        e.replace('new text')
        self.assertEqual(e.get_text(), 'new text')
        e.replace(42)
        self.assertEqual(e.get_text(), '42')
        e.undo()
        self.assertEqual(e.get_text(), 'new text')

    def test_cursor_position_and_jump(self):
        e = self.editor('line zero\nline one\nline two')
        self.assertEqual(e.cursor_position(), (0, 0))
        e.jump_to(1, 5)
        self.assertEqual(e.cursor_position(), (1, 5))
        self.assertEqual(self.pos(e), 10 + 5)
        e.jump_to(2, 0)
        self.assertEqual(e.cursor_position(), (2, 0))

        # set_cursor uses absolute positions
        e.set_cursor(12)
        self.assertEqual(e.cursor_position(), (1, 2))
        self.assertEqual(self.pos(e), 12)

        # With a selection, the left side is used
        self.select(e, 17, 13)
        self.assertEqual(e.cursor_position(), (1, 3))
        self.select(e, 13, 17)
        self.assertEqual(e.cursor_position(), (1, 3))

    def test_default_settings(self):
        e = self.editor()
        self.assertEqual(
            e.lineWrapMode(), e.LineWrapMode.NoWrap)
        self.assertEqual(e.font().pointSize(), 11)
        self.assertGreater(e.tabStopDistance(), 0)

    def test_trim_trailing_whitespace(self):
        e = self.editor('a  \n  b\t\n   \nc')
        e.trim_trailing_whitespace()
        self.assertEqual(e.get_text(), 'a\n  b\n\nc')
        # Single undo step
        e.undo()
        self.assertEqual(e.get_text(), 'a  \n  b\t\n   \nc')

    # Editor: commenting

    def test_toggle_comment_single_line(self):
        e = self.editor('    x = 1\ny = 2')
        e.set_cursor(6)
        e.toggle_comment()
        self.assertEqual(e.get_text(), '    #x = 1\ny = 2')
        e.toggle_comment()
        self.assertEqual(e.get_text(), '    x = 1\ny = 2')

    def test_toggle_comment_multiple_lines(self):
        # Comments are inserted at the minimum indent
        text = '    a\n  b\n\n      c\nd'
        e = self.editor(text)
        self.select(e, 0, 17)   # Lines 0 to 3
        e.toggle_comment()
        self.assertEqual(e.get_text(), '  #  a\n  #b\n  #\n  #    c\nd')

        # Toggling again removes the comments
        self.select(e, 0, 23)
        e.toggle_comment()
        self.assertEqual(e.get_text(), '    a\n  b\n  \n      c\nd')

        # Only uncomments if all lines are commented
        e = self.editor('#a\nb\n#c')
        self.select(e, 0, len(e.get_text()))
        e.toggle_comment()
        self.assertEqual(e.get_text(), '##a\n#b\n##c')

        # Single undo step
        e.undo()
        self.assertEqual(e.get_text(), '#a\nb\n#c')

    # Editor: keyboard handling

    def test_tab_indent(self):
        K = self.Qt.Key
        # No selection: insert spaces up to next tab stop
        e = self.editor('ab')
        e.set_cursor(1)
        self.key(e, K.Key_Tab)
        self.assertEqual(e.get_text(), 'a   b')
        self.assertEqual(self.pos(e), 4)
        self.key(e, K.Key_Tab)
        self.assertEqual(e.get_text(), 'a       b')

        # With selection: indent all selected lines
        e = self.editor('a\nb\nc\nd')
        self.select(e, 2, 5)
        self.key(e, K.Key_Tab)
        self.assertEqual(e.get_text(), 'a\n    b\n    c\nd')
        e.undo()
        self.assertEqual(e.get_text(), 'a\nb\nc\nd')

    def test_backtab_dedent(self):
        K = self.Qt.Key
        S = self.Qt.KeyboardModifier.ShiftModifier

        # Single line, no selection
        e = self.editor('      a\nb')
        e.set_cursor(7)
        self.key(e, K.Key_Backtab, S)
        self.assertEqual(e.get_text(), '  a\nb')
        self.assertEqual(self.pos(e), 3)
        self.key(e, K.Key_Backtab, S)
        self.assertEqual(e.get_text(), 'a\nb')
        # Nothing left to dedent: no change
        self.key(e, K.Key_Backtab, S)
        self.assertEqual(e.get_text(), 'a\nb')

        # Multiple lines, selection is updated
        e = self.editor('x\n    a\n  b\n        c\ny')
        start = 2
        end = len('x\n    a\n  b\n        c')
        self.select(e, start, end)
        self.key(e, K.Key_Backtab, S)
        self.assertEqual(e.get_text(), 'x\na\nb\n    c\ny')
        c = e.textCursor()
        self.assertEqual(c.selectionStart(), 2)
        self.assertEqual(c.selectionEnd(), len('x\na\nb\n    c'))

    def test_enter_auto_indent(self):
        K = self.Qt.Key
        e = self.editor('    abc')
        e.set_cursor(7)
        self.key(e, K.Key_Return)
        self.assertEqual(e.get_text(), '    abc\n    ')
        self.assertEqual(e.cursor_position(), (1, 4))

        # Indent is limited to the cursor position
        e = self.editor('    abc')
        e.set_cursor(2)
        self.key(e, K.Key_Enter)
        self.assertEqual(e.get_text(), '  \n    abc')

        # Selection is replaced by newline
        e = self.editor('    abcdef')
        self.select(e, 5, 8)
        self.key(e, K.Key_Return)
        self.assertEqual(e.get_text(), '    a\nef')

        # Enter with modifiers does nothing
        e = self.editor('abc')
        e.set_cursor(1)
        self.key(e, K.Key_Return, self.Qt.KeyboardModifier.ShiftModifier)
        self.assertEqual(e.get_text(), 'abc')
        self.assertEqual(e.blockCount(), 1)

    def test_home_key(self):
        K = self.Qt.Key
        KM = self.Qt.KeyboardModifier
        e = self.editor('x\n    abc')
        e.set_cursor(8)

        # First press: start of line
        self.key(e, K.Key_Home)
        self.assertEqual(self.pos(e), 2)
        # Second press: first non-whitespace character
        self.key(e, K.Key_Home)
        self.assertEqual(self.pos(e), 6)
        # Third press: start of line again
        self.key(e, K.Key_Home)
        self.assertEqual(self.pos(e), 2)

        # Shift+Home selects
        e.set_cursor(8)
        self.key(e, K.Key_Home, KM.ShiftModifier)
        c = e.textCursor()
        self.assertEqual((c.selectionStart(), c.selectionEnd()), (2, 8))

        # Keypad modifier is ignored
        e.set_cursor(8)
        self.key(e, K.Key_Home, KM.KeypadModifier)
        self.assertEqual(self.pos(e), 2)

        # Control+Home: start of document
        e.set_cursor(8)
        self.key(e, K.Key_Home, KM.ControlModifier)
        self.assertEqual(self.pos(e), 0)
        self.assertFalse(e.textCursor().hasSelection())

        # Control+Shift+Home: select to start of document
        e.set_cursor(8)
        self.key(e, K.Key_Home, KM.ControlModifier | KM.ShiftModifier)
        c = e.textCursor()
        self.assertEqual(c.position(), 0)
        self.assertEqual((c.selectionStart(), c.selectionEnd()), (0, 8))

        # Control+Shift+Home is handled by the editor, not by Qt
        with unittest.mock.patch.object(
                self.QtWidgets.QPlainTextEdit, 'keyPressEvent') as kpe:
            e.set_cursor(8)
            self.key(e, K.Key_Home, KM.ControlModifier | KM.ShiftModifier)
            kpe.assert_not_called()
        c = e.textCursor()
        self.assertEqual((c.selectionStart(), c.selectionEnd()), (0, 8))

    def test_up_down_smart_column(self):
        K = self.Qt.Key
        KM = self.Qt.KeyboardModifier
        e = self.editor('abcdef\nab\nabcdef')
        e.set_cursor(5)

        # Moving down through a short line remembers the column
        self.key(e, K.Key_Down)
        self.assertEqual(e.cursor_position(), (1, 2))
        self.key(e, K.Key_Down)
        self.assertEqual(e.cursor_position(), (2, 5))
        self.key(e, K.Key_Up)
        self.assertEqual(e.cursor_position(), (1, 2))
        self.key(e, K.Key_Up)
        self.assertEqual(e.cursor_position(), (0, 5))

        # Up beyond start: move to start of line
        self.key(e, K.Key_Up)
        self.assertEqual(self.pos(e), 0)

        # Down beyond end: move to end of document
        e.set_cursor(15)
        self.key(e, K.Key_Down)
        self.assertEqual(self.pos(e), len(e.get_text()))

        # Shift+Down selects
        e.set_cursor(0)
        self.key(e, K.Key_Right)    # Resets smart column
        self.key(e, K.Key_Down, KM.ShiftModifier)
        c = e.textCursor()
        self.assertEqual((c.selectionStart(), c.selectionEnd()), (1, 8))

        # Left/right reset the smart column
        e.set_cursor(4)
        self.key(e, K.Key_Right)    # Resets smart column
        self.key(e, K.Key_Down)
        self.assertEqual(e.cursor_position(), (1, 2))
        self.key(e, K.Key_Left)
        self.assertEqual(e.cursor_position(), (1, 1))
        self.key(e, K.Key_Down)
        self.assertEqual(e.cursor_position(), (2, 1))

        # Text changes reset the smart column
        e.set_cursor(4)
        self.key(e, K.Key_Right)    # Resets smart column
        self.key(e, K.Key_Down)
        self.assertIsNotNone(e._last_column)
        e.insertPlainText('x')
        self.assertIsNone(e._last_column)

        # Moving the cursor in another way resets the smart column
        e = self.editor('abcdef\nab\nabcdef\nabcdef')
        e.set_cursor(5)
        self.key(e, K.Key_Down)
        self.assertEqual(e.cursor_position(), (1, 2))
        self.assertEqual(e._last_column, 5)
        e.jump_to(2, 1)
        self.assertIsNone(e._last_column)
        self.key(e, K.Key_Down)
        self.assertEqual(e.cursor_position(), (3, 1))

        # Mouse clicks (or other cursor changes) also reset it
        e.set_cursor(5)
        self.key(e, K.Key_Down)
        self.assertEqual(e._last_column, 5)
        c = e.textCursor()
        c.setPosition(14)
        e.setTextCursor(c)
        self.assertIsNone(e._last_column)
        self.key(e, K.Key_Down)
        self.assertEqual(e.cursor_position(), (3, 4))

        # Up/down with other modifiers are ignored
        e.set_cursor(1)
        self.key(e, K.Key_Down, KM.ControlModifier)
        self.assertEqual(self.pos(e), 1)

    def test_page_up_down(self):
        K = self.Qt.Key
        e = self.editor('\n'.join(str(i) for i in range(100)))
        e._blocks_per_page = 13     # Moves 10 blocks
        self.key(e, K.Key_PageDown)
        self.assertEqual(e.cursor_position(), (10, 0))
        self.key(e, K.Key_PageDown)
        self.assertEqual(e.cursor_position(), (20, 0))
        self.key(e, K.Key_PageUp)
        self.assertEqual(e.cursor_position(), (10, 0))

        # Very small pages: always move at least one block
        for bpp in (0, 1, 3, 4):
            e._blocks_per_page = bpp
            e.jump_to(10, 0)
            self.key(e, K.Key_PageDown)
            self.assertEqual(e.cursor_position(), (11, 0))
            self.key(e, K.Key_PageUp)
            self.assertEqual(e.cursor_position(), (10, 0))

    def test_move_lines(self):
        K = self.Qt.Key
        A = self.Qt.KeyboardModifier.AltModifier
        e = self.editor('one\ntwo\nthree')

        # Move single line down
        e.set_cursor(5)
        self.key(e, K.Key_Down, A)
        self.assertEqual(e.get_text(), 'one\nthree\ntwo')
        self.assertEqual(e.textCursor().selectedText(), 'two')

        # Can't move last line down
        self.key(e, K.Key_Down, A)
        self.assertEqual(e.get_text(), 'one\nthree\ntwo')

        # Move it back up
        self.key(e, K.Key_Up, A)
        self.assertEqual(e.get_text(), 'one\ntwo\nthree')
        self.assertEqual(e.textCursor().selectedText(), 'two')

        # Can't move first line up
        e.set_cursor(1)
        self.key(e, K.Key_Up, A)
        self.assertEqual(e.get_text(), 'one\ntwo\nthree')

        # Move a multi-line selection
        e = self.editor('a\nb\nc\nd')
        self.select(e, 2, 5)
        self.key(e, K.Key_Up, A)
        self.assertEqual(e.get_text(), 'b\nc\na\nd')
        self.key(e, K.Key_Down, A)
        self.key(e, K.Key_Down, A)
        self.assertEqual(e.get_text(), 'a\nd\nb\nc')

        # Whole-line selection (ending at start of next line)
        e = self.editor('a\nb\nc')
        self.select(e, 0, 2)
        self.key(e, K.Key_Down, A)
        self.assertEqual(e.get_text(), 'b\na\nc')

        # Undo restores in one step
        e.undo()
        self.assertEqual(e.get_text(), 'a\nb\nc')

    def test_insert_toggles_overwrite(self):
        K = self.Qt.Key
        e = self.editor('abc')
        self.assertFalse(e.overwriteMode())
        self.key(e, K.Key_Insert)
        self.assertTrue(e.overwriteMode())
        self.key(e, K.Key_Insert)
        self.assertFalse(e.overwriteMode())

    def test_ignored_and_default_keys(self):
        K = self.Qt.Key
        C = self.Qt.KeyboardModifier.ControlModifier
        e = self.editor('abc')
        e.set_cursor(3)

        # Control+K and Control+I are ignored
        self.key(e, K.Key_K, C, 'k')
        self.key(e, K.Key_I, C, '\t')
        self.assertEqual(e.get_text(), 'abc')

        # Ordinary keys are handled by Qt
        self.key(e, K.Key_X, text='x')
        self.assertEqual(e.get_text(), 'abcx')
        self.key(e, K.Key_Backspace)
        self.key(e, K.Key_Backspace)
        self.assertEqual(e.get_text(), 'ab')

        # End is passed to Qt
        e.set_cursor(0)
        self.key(e, K.Key_End)
        self.assertEqual(self.pos(e), 2)

    # Editor: bracket matching and painting

    def test_bracket_matching(self):
        e = self.editor('a(b[c](d))')
        n = len(e.extraSelections())
        self.assertEqual(n, 1)  # Just the current line

        def brackets():
            sel = e.extraSelections()[1:]
            return sorted(s.cursor.selectionStart() for s in sel)

        # In front of opening bracket
        e.set_cursor(1)
        self.assertEqual(brackets(), [1, 9])
        e.set_cursor(3)
        self.assertEqual(brackets(), [3, 5])
        e.set_cursor(6)
        self.assertEqual(brackets(), [6, 8])

        # In front of closing bracket
        e.set_cursor(9)
        self.assertEqual(brackets(), [1, 9])
        e.set_cursor(5)
        self.assertEqual(brackets(), [3, 5])

        # Behind closing bracket at end of document
        e.set_cursor(10)
        self.assertEqual(brackets(), [1, 9])

        # Behind opening bracket, not at end of document
        e.set_cursor(2)
        self.assertEqual(brackets(), [1, 9])
        e.set_cursor(4)
        self.assertEqual(brackets(), [3, 5])

        # Behind closing bracket, not at end of document
        e = self.editor('(a)b')
        e.set_cursor(3)
        self.assertEqual(brackets(), [0, 2])

        # In front of and behind a bracket: bracket in front is used
        e = self.editor('(a)(b)')
        e.set_cursor(3)
        self.assertEqual(brackets(), [3, 5])

        # Not at a bracket
        e = self.editor('a(b[c](d))')
        e.set_cursor(0)
        self.assertEqual(brackets(), [])
        e = self.editor('(ab)')
        e.set_cursor(2)
        self.assertEqual(brackets(), [])

        # Unmatched bracket
        e = self.editor('((a)')
        e.set_cursor(0)
        self.assertEqual(brackets(), [])
        e.set_cursor(1)
        self.assertEqual(brackets(), [1, 3])

        # With a selection, no bracket matching
        self.select(e, 1, 2)
        self.assertEqual(brackets(), [])

    def test_line_numbers_and_painting(self):
        e = self.editor('\n'.join('line' for i in range(200)))
        area = e._line_number_area
        w1 = e._line_number_area_width()
        self.assertEqual(area.sizeHint().width(), w1)
        self.assertEqual(e.viewportMargins().left(), 2 + w1)

        # Width grows with number of digits
        e.set_text('\n'.join('line' for i in range(2000)))
        w2 = e._line_number_area_width()
        self.assertGreater(w2, w1)
        self.assertEqual(e.viewportMargins().left(), 2 + w2)

        # Resizing updates blocks per page and line number geometry
        e.resize(300, 500)
        e.show()
        self.app.processEvents()
        self.assertGreater(e._blocks_per_page, 1)
        self.assertEqual(area.width(), w2)

        # Painting (to a pixmap), and scrolling
        e.grab()
        area.grab()
        e.verticalScrollBar().setValue(50)
        self.app.processEvents()
        e.grab()
        area.update_contents(area.rect(), 0)
        area.update_contents(area.rect(), 3)

    # Find and replace

    def test_find(self):
        e = self.editor('Apple banana\napple pineapple\nAPPLE')
        f = self.finder(e)
        messages = []
        f.find_action.connect(messages.append)

        # No query
        f.action_find()
        self.assertEqual(messages[-1], 'No query set')

        # Case insensitive search, wraps around
        f._search_field.setText('apple')
        f.action_find()
        self.assertEqual(e.textCursor().selectionStart(), 0)
        self.assertEqual(messages[-1], 'Match found on line 1 char 0.')
        f.action_find()
        self.assertEqual(e.cursor_position(), (1, 0))
        f.action_find()
        self.assertEqual(e.cursor_position(), (1, 10))
        f.action_find()
        self.assertEqual(e.cursor_position(), (2, 0))
        f.action_find()
        self.assertEqual(e.cursor_position(), (0, 0))

        # Case sensitive
        f._case_check.setChecked(True)
        f.action_find()
        self.assertEqual(e.cursor_position(), (1, 0))
        f.action_find()
        self.assertEqual(e.cursor_position(), (1, 10))
        f.action_find()
        self.assertEqual(e.cursor_position(), (1, 0))

        # Whole words
        f._whole_check.setChecked(True)
        f.action_find()
        self.assertEqual(e.cursor_position(), (1, 0))
        f.action_find()
        self.assertEqual(e.cursor_position(), (1, 0))
        self.assertEqual(messages[-1], 'Match found on line 2 char 0.')

        # Not found: cursor is restored
        f._search_field.setText('cherry')
        e.set_cursor(3)
        f.action_find()
        self.assertEqual(messages[-1], 'Query not found.')
        self.assertEqual(self.pos(e), 3)

        # Not found with flags
        f._case_check.setChecked(False)
        f._whole_check.setChecked(False)
        f.action_find()
        self.assertEqual(messages[-1], 'Query not found.')

        # Enter in widget triggers find
        f._search_field.setText('banana')
        self.key(f, self.Qt.Key.Key_Return)
        self.assertEqual(e.textCursor().selectedText(), 'banana')
        self.assertEqual(messages[-1], 'Match found on line 1 char 6.')

        # Other keys are passed on
        self.key(f, self.Qt.Key.Key_A, text='a')

    def test_replace_single(self):
        e = self.editor('cat dog cat')
        f = self.finder(e)
        messages = []
        f.find_action.connect(messages.append)

        f.action_replace()
        self.assertEqual(messages[-1], 'No query set')

        f._search_field.setText('CAT')
        f._replace_field.setText('cow')

        # First press only selects the next match
        f.action_replace()
        self.assertEqual(e.get_text(), 'cat dog cat')
        self.assertEqual(e.textCursor().selectionStart(), 0)

        # Second press replaces it and finds next
        f.action_replace()
        self.assertEqual(e.get_text(), 'cow dog cat')
        self.assertEqual(e.textCursor().selectionStart(), 8)
        f.action_replace()
        self.assertEqual(e.get_text(), 'cow dog cow')
        self.assertEqual(messages[-1], 'Query not found.')

        # Case sensitive: selection must match exactly
        e.set_text('Cat cat')
        f._case_check.setChecked(True)
        f._search_field.setText('cat')
        self.select(e, 0, 3)
        f.action_replace()
        self.assertEqual(e.get_text(), 'Cat cat')
        self.assertEqual(e.textCursor().selectionStart(), 4)
        f.action_replace()
        self.assertEqual(e.get_text(), 'Cat cow')

    def test_replace_all(self):
        e = self.editor('cat dog cat\nCat catalog')
        f = self.finder(e)
        messages = []
        f.find_action.connect(messages.append)

        f.action_replace_all()
        self.assertEqual(messages[-1], 'No query set')

        # Case insensitive, starting halfway through the document
        f._search_field.setText('cat')
        f._replace_field.setText('cow')
        e.set_cursor(5)
        f.action_replace_all()
        self.assertEqual(e.get_text(), 'cow dog cow\ncow cowalog')
        self.assertEqual(messages[-1], 'Replaced 4 occurrences.')

        # Undo in one step
        e.undo()
        self.assertEqual(e.get_text(), 'cat dog cat\nCat catalog')

        # Case sensitive and whole word
        f._case_check.setChecked(True)
        f._whole_check.setChecked(True)
        f.action_replace_all()
        self.assertEqual(e.get_text(), 'cow dog cow\nCat catalog')
        self.assertEqual(messages[-1], 'Replaced 2 occurrences.')

        # Replacing with itself terminates
        f._case_check.setChecked(False)
        f._whole_check.setChecked(False)
        f._search_field.setText('dog')
        f._replace_field.setText('DOG')
        f.action_replace_all()
        self.assertEqual(e.get_text(), 'cow DOG cow\nCat catalog')
        self.assertEqual(messages[-1], 'Replaced 1 occurrences.')

        # Nothing found
        f._search_field.setText('horse')
        f.action_replace_all()
        self.assertEqual(messages[-1], 'Replaced 0 occurrences.')

    def test_find_activate(self):
        e = self.editor('hello world')
        f = self.finder(e)
        f._search_field.setText('old')
        f.activate()
        self.assertEqual(f._search_field.text(), 'old')
        self.assertEqual(f._search_field.selectedText(), 'old')
        self.select(e, 6, 11)
        f.activate()
        self.assertEqual(f._search_field.text(), 'world')
        self.assertEqual(f._search_field.selectedText(), 'world')

    def test_find_config(self):
        e = self.editor()
        f = self.finder(e)

        # Save and load roundtrip (RawConfigParser, as used by the IDE)
        f._case_check.setChecked(True)
        f._whole_check.setChecked(False)
        config = configparser.RawConfigParser()
        f.save_config(config, 'search')
        # Values are stored as strings
        self.assertEqual(config.get('search', 'case_sensitive'), 'True')
        self.assertEqual(config.get('search', 'whole_word'), 'False')
        buf = io.StringIO()
        config.write(buf)
        config = configparser.RawConfigParser()
        config.read_string(buf.getvalue())
        self.assertTrue(config.getboolean('search', 'case_sensitive'))
        self.assertFalse(config.getboolean('search', 'whole_word'))

        g = self.finder(e)
        g._whole_check.setChecked(True)
        g.load_config(config, 'search')
        self.assertTrue(g._case_check.isChecked())
        self.assertFalse(g._whole_check.isChecked())

        # Missing section or options: no change
        g.load_config(configparser.RawConfigParser(), 'search')
        self.assertTrue(g._case_check.isChecked())
        config = configparser.RawConfigParser()
        config.add_section('search')
        config.set('search', 'whole_word', 'true')
        g.load_config(config, 'search')
        self.assertTrue(g._case_check.isChecked())
        self.assertTrue(g._whole_check.isChecked())

        # Saving works with a (non-raw) ConfigParser too
        config = configparser.ConfigParser()
        g.save_config(config, 'search')
        h = self.finder(e)
        h.load_config(config, 'search')
        self.assertTrue(h._case_check.isChecked())
        self.assertTrue(h._whole_check.isChecked())

    def test_highlighter_styles_without_editor(self):
        # Highlighters set the styles, even if no editor was created
        s = self.s
        styles = (s.STYLE_HEADER, s.STYLE_COMMENT, s.STYLE_LITERAL)
        for style in styles:
            style.clearForeground()
            self.assertFalse(style.hasProperty(
                self.QtGui.QTextFormat.Property.ForegroundBrush))
        for cls in (
                s.ModelHighlighter, s.ProtocolHighlighter,
                s.ScriptHighlighter):
            doc = self.QtGui.QTextDocument()
            h = cls(doc)
            for style in styles:
                self.assertTrue(style.hasProperty(
                    self.QtGui.QTextFormat.Property.ForegroundBrush))
                style.clearForeground()
            del h, doc

    # Highlighters

    def test_model_highlighter(self):
        s = self.s
        blocks = self.highlight(s.ModelHighlighter, '\n'.join([
            '[[model]]',
            '[engine]',
            'time = 0 [ms] bind time',
            '    in [ms]',
            '    label membrane_potential',
            'x = 1.5e3 + y2 * 2  # A comment with 3 and use',
            'y = if(a and b or not c, 1, 2)',
            'use membrane.V as V',
            'desc: Hello there',
            'desc: """First line',
            '  middle 123',
            'last""" + 2',
            'z: """single line""" # 4',
            '#desc: """not a string',
            'y = 3',
        ]))

        # Headers
        text, state, f = blocks[0]
        self.assertFmt(f, 0, s.STYLE_HEADER)
        self.assertFmt(f, 8, s.STYLE_HEADER)
        text, state, f = blocks[1]
        self.assertFmt(f, 0, s.STYLE_HEADER)
        self.assertFmt(f, 7, s.STYLE_HEADER)

        # Literal, inline unit, bind
        text, state, f = blocks[2]
        self.assertNoFmt(f, 0)
        self.assertFmt(f, text.index('0'), s.STYLE_LITERAL)
        self.assertFmt(f, text.index('[ms]'), s.STYLE_INLINE_UNIT)
        self.assertFmt(f, text.index('bind'), s.STYLE_ANNOT_KEY)
        self.assertFmt(f, text.index('time', 5), s.STYLE_ANNOT_VAL)

        # Variable unit
        text, state, f = blocks[3]
        self.assertFmt(f, 4, s.STYLE_ANNOT_KEY)
        self.assertFmt(f, 7, s.STYLE_ANNOT_VAL)

        # Label
        text, state, f = blocks[4]
        self.assertFmt(f, 4, s.STYLE_ANNOT_KEY)
        self.assertFmt(f, 10, s.STYLE_ANNOT_VAL)

        # Numbers and comments
        text, state, f = blocks[5]
        self.assertFmt(f, 4, s.STYLE_LITERAL)
        self.assertFmt(f, 8, s.STYLE_LITERAL)
        self.assertNoFmt(f, text.index('y2') + 1)  # No number in name
        self.assertFmt(f, text.index('* 2') + 2, s.STYLE_LITERAL)
        i = text.index('#')
        self.assertFmt(f, i, s.STYLE_COMMENT)
        self.assertFmt(f, text.index(' 3 ') + 1, s.STYLE_COMMENT)
        self.assertFmt(f, len(text) - 1, s.STYLE_COMMENT)

        # Keywords
        text, state, f = blocks[6]
        self.assertFmt(f, text.index('and'), s.STYLE_KEYWORD_2)
        self.assertFmt(f, text.index('or'), s.STYLE_KEYWORD_2)
        self.assertFmt(f, text.index('not'), s.STYLE_KEYWORD_2)
        self.assertNoFmt(f, text.index('if'))
        text, state, f = blocks[7]
        self.assertFmt(f, 0, s.STYLE_KEYWORD_1)
        self.assertFmt(f, text.index('as'), s.STYLE_KEYWORD_1)
        self.assertNoFmt(f, text.index('membrane'))

        # Meta data
        text, state, f = blocks[8]
        self.assertFmt(f, 0, s.STYLE_ANNOT_KEY)
        self.assertFmt(f, 4, s.STYLE_ANNOT_KEY)
        self.assertFmt(f, 6, s.STYLE_ANNOT_VAL)
        self.assertFmt(f, len(text) - 1, s.STYLE_ANNOT_VAL)
        self.assertEqual(state, 0)

        # Multi-line string
        text, state, f = blocks[9]
        self.assertEqual(state, 1)
        self.assertFmt(f, 0, s.STYLE_ANNOT_KEY)
        self.assertFmt(f, 6, s.STYLE_ANNOT_VAL)
        self.assertFmt(f, len(text) - 1, s.STYLE_ANNOT_VAL)
        text, state, f = blocks[10]
        self.assertEqual(state, 1)
        self.assertEqual(f, [(0, len(text), s.STYLE_ANNOT_VAL)])
        text, state, f = blocks[11]
        self.assertEqual(state, 0)
        self.assertFmt(f, 0, s.STYLE_ANNOT_VAL)
        self.assertFmt(f, 6, s.STYLE_ANNOT_VAL)
        self.assertNoFmt(f, 8)
        self.assertFmt(f, len(text) - 1, s.STYLE_LITERAL)

        # Single-line string followed by comment
        text, state, f = blocks[12]
        self.assertEqual(state, 0)
        self.assertFmt(f, 0, s.STYLE_ANNOT_KEY)
        self.assertFmt(f, 3, s.STYLE_ANNOT_VAL)
        self.assertFmt(f, text.index('line'), s.STYLE_ANNOT_VAL)
        self.assertFmt(f, text.index('#'), s.STYLE_COMMENT)

        # Commented string start doesn't start string
        text, state, f = blocks[13]
        self.assertEqual(state, 0)
        self.assertEqual(f, [(0, len(text), s.STYLE_COMMENT)])
        text, state, f = blocks[14]
        self.assertFmt(f, 4, s.STYLE_LITERAL)

    def test_model_highlighter_string_contents(self):
        # Number or comment characters inside strings aren't highlighted
        s = self.s
        blocks = self.highlight(
            s.ModelHighlighter, 'x: """a # 12""" 3')
        text, state, f = blocks[0]
        self.assertFmt(f, text.index('#'), s.STYLE_ANNOT_VAL)
        self.assertFmt(f, text.index('12'), s.STYLE_ANNOT_VAL)
        self.assertFmt(f, len(text) - 1, s.STYLE_LITERAL)

    def test_protocol_highlighter(self):
        s = self.s
        blocks = self.highlight(s.ProtocolHighlighter, '\n'.join([
            '[[protocol]]',
            '# Level  Start    Length   Period   Multiplier',
            '-80      10       0.5e3    1000     0',
            '-120     next     100      0        0  # comment',
        ]))
        text, state, f = blocks[0]
        self.assertFmt(f, 0, s.STYLE_HEADER)
        self.assertFmt(f, len(text) - 1, s.STYLE_HEADER)
        text, state, f = blocks[1]
        self.assertEqual(f, [(0, len(text), s.STYLE_COMMENT)])
        text, state, f = blocks[2]
        self.assertNoFmt(f, 0)    # Unsigned
        self.assertFmt(f, 1, s.STYLE_LITERAL)
        self.assertFmt(f, text.index('0.5e3'), s.STYLE_LITERAL)
        self.assertFmt(f, text.index('e3'), s.STYLE_LITERAL)
        self.assertNoFmt(f, 4)
        text, state, f = blocks[3]
        self.assertFmt(f, text.index('next'), s.STYLE_KEYWORD_1)
        self.assertFmt(f, text.index('#'), s.STYLE_COMMENT)
        self.assertFmt(f, len(text) - 1, s.STYLE_COMMENT)

    def test_script_highlighter(self):
        s = self.s
        blocks = self.highlight(s.ScriptHighlighter, '\n'.join([
            '[[script]]',
            'import myokit',
            'for i in range(10):',
            '    x = len("abc # 5") + None  # comment "q"',
            "y = 'it' if True else False",
            'z = """multi',
            'line 5',
            'end""" + 3',
            "w = '''also",
            "multi''' # done",
            'u = "esc\\"aped" + 7',
            'v = "unterminated + 8',
            'print(2)',
        ]))

        # Header
        text, state, f = blocks[0]
        self.assertFmt(f, 0, s.STYLE_HEADER)

        # Keywords
        text, state, f = blocks[1]
        self.assertFmt(f, 0, s.STYLE_KEYWORD_1)
        self.assertNoFmt(f, text.index('myokit'))
        text, state, f = blocks[2]
        self.assertFmt(f, 0, s.STYLE_KEYWORD_1)
        self.assertFmt(f, text.index('in'), s.STYLE_KEYWORD_1)
        self.assertFmt(f, text.index('range'), s.STYLE_KEYWORD_2)
        self.assertFmt(f, text.index('10'), s.STYLE_LITERAL)
        self.assertNoFmt(f, text.index('i '))

        # Strings with comments inside, comments with strings inside
        text, state, f = blocks[3]
        self.assertFmt(f, text.index('len'), s.STYLE_KEYWORD_2)
        self.assertFmt(f, text.index('"abc'), s.STYLE_LITERAL)
        self.assertFmt(f, text.index('# 5'), s.STYLE_LITERAL)
        self.assertFmt(f, text.index('None'), s.STYLE_LITERAL)
        self.assertFmt(f, text.index('# comment'), s.STYLE_COMMENT)
        self.assertFmt(f, text.index('"q"'), s.STYLE_COMMENT)

        # Single quotes and booleans
        text, state, f = blocks[4]
        self.assertFmt(f, text.index("'it'"), s.STYLE_LITERAL)
        self.assertFmt(f, text.index('if'), s.STYLE_KEYWORD_1)
        self.assertFmt(f, text.index('True'), s.STYLE_LITERAL)
        self.assertFmt(f, text.index('else'), s.STYLE_KEYWORD_1)
        self.assertFmt(f, text.index('False'), s.STYLE_LITERAL)

        # Multi-line strings with """
        text, state, f = blocks[5]
        self.assertEqual(state, 1)
        self.assertFmt(f, text.index('"""'), s.STYLE_LITERAL)
        self.assertFmt(f, len(text) - 1, s.STYLE_LITERAL)
        self.assertNoFmt(f, 0)
        text, state, f = blocks[6]
        self.assertEqual(state, 1)
        self.assertEqual(f, [(0, len(text), s.STYLE_LITERAL)])
        text, state, f = blocks[7]
        self.assertEqual(state, 0)
        self.assertFmt(f, 0, s.STYLE_LITERAL)
        self.assertFmt(f, 5, s.STYLE_LITERAL)
        self.assertNoFmt(f, 7)
        self.assertFmt(f, len(text) - 1, s.STYLE_LITERAL)

        # Multi-line strings with '''
        text, state, f = blocks[8]
        self.assertEqual(state, 2)
        self.assertFmt(f, len(text) - 1, s.STYLE_LITERAL)
        text, state, f = blocks[9]
        self.assertEqual(state, 0)
        self.assertFmt(f, 0, s.STYLE_LITERAL)
        self.assertFmt(f, text.index('#'), s.STYLE_COMMENT)

        # Escaped quote: highlighting continues to the real end of string
        text, state, f = blocks[10]
        self.assertFmt(f, len(text) - 1, s.STYLE_LITERAL)

        # Unterminated single-line string: not a string, no state change
        text, state, f = blocks[11]
        self.assertEqual(state, 0)
        self.assertNoFmt(f, text.index('"'))
        self.assertFmt(f, len(text) - 1, s.STYLE_LITERAL)
        text, state, f = blocks[12]
        self.assertFmt(f, 0, s.STYLE_KEYWORD_2)
        self.assertFmt(f, text.index('2'), s.STYLE_LITERAL)

    def test_script_highlighter_commented_string(self):
        # A quote inside a comment does not start a string
        s = self.s
        blocks = self.highlight(
            s.ScriptHighlighter, "# it's a '''comment\nx = 1")
        text, state, f = blocks[0]
        self.assertEqual(state, 0)
        self.assertEqual(f, [(0, len(text), s.STYLE_COMMENT)])
        text, state, f = blocks[1]
        self.assertFmt(f, 4, s.STYLE_LITERAL)

    def test_dark_mode(self):
        # Test switching style for dark mode
        s = self.s
        self.editor()   # Styles are initialized when an editor is created
        p = self.QtGui.QGuiApplication.palette()
        light = self.QtGui.QColor(s.COLOR_SELECTED_LINE)
        header = self.QtGui.QColor(s.STYLE_HEADER.foreground().color())
        try:
            with unittest.mock.patch(
                    'myokit.gui._in_dark_mode', return_value=True):
                s._adapt_for_dark_mode(p)
            self.assertEqual(
                s.STYLE_HEADER.foreground().color(),
                self.QtGui.QColor(98, 178, 255))
            self.assertEqual(
                s.COLOR_SELECTED_LINE, self.QtGui.QColor(70, 70, 70))
            with unittest.mock.patch(
                    'myokit.gui._in_dark_mode', return_value=False):
                s._adapt_for_dark_mode(p)
            self.assertEqual(
                s.STYLE_HEADER.foreground().color(),
                self.QtGui.QColor(0, 31, 231))
        finally:
            # Restore original state
            s.COLOR_SELECTED_LINE = light
            s._adapt_for_dark_mode(p)
            self.assertEqual(s.STYLE_HEADER.foreground().color(), header)


if __name__ == '__main__':
    unittest.main()
