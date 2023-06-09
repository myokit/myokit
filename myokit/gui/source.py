#
# Source code editor for Myokit.
#
# This code is based in part on examples provided by the PyQt project.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import myokit

from myokit.gui import Qt, QtCore, QtGui, QtWidgets


# GUI components
# Constants
SPACE = ' '
TABS = 4
INDENT = SPACE * TABS
BRACKETS = {
    '(': ')',
    ')': '(',
    '[': ']',
    ']': '['
}
BRACKETS_CLOSE = (')', ']')
FONT = myokit.gui.qtMonospaceFont()
FONT.setPointSize(11)

# Component and model headers
STYLE_HEADER = QtGui.QTextCharFormat()

# Comments
STYLE_COMMENT = QtGui.QTextCharFormat()

# Model annotations (including meta, labels, and units)
STYLE_ANNOT_KEY = QtGui.QTextCharFormat()
STYLE_ANNOT_VAL = QtGui.QTextCharFormat()

# Language keywords
STYLE_KEYWORD_1 = QtGui.QTextCharFormat()
STYLE_KEYWORD_2 = QtGui.QTextCharFormat()

# Literals: Numbers in model/protocol, Also booleans and strings in script
STYLE_LITERAL = QtGui.QTextCharFormat()
STYLE_INLINE_UNIT = QtGui.QTextCharFormat()

# Matching brackets are highlighted
COLOR_BRACKET = QtGui.QColor(240, 100, 0)

# Selected line is highlighted
COLOR_SELECTED_LINE = QtGui.QColor(238, 238, 238)


def _check_for_dark_mode(palette):
    """
    Checks the default editor background color, and adjusts the color scheme
    if it looks like dark-mode is enabled.
    """
    c = palette.base().color()
    c = (c.blueF() + c.greenF() + c.redF()) / 3
    dark = c < 0.5

    # Don't mess with these directly: Use the SVG in myokit-docs
    if not dark:
        STYLE_HEADER.setForeground(QtGui.QColor(0, 31, 231))
        STYLE_COMMENT.setForeground(QtGui.QColor(103, 161, 107))
        STYLE_ANNOT_KEY.setForeground(QtGui.QColor(0, 31, 231))
        STYLE_ANNOT_VAL.setForeground(QtGui.QColor(57, 115, 214))
        STYLE_KEYWORD_1.setForeground(QtGui.QColor(0, 128, 0))
        STYLE_KEYWORD_1.setFontWeight(QtGui.QFont.Weight.Bold)
        STYLE_KEYWORD_2.setForeground(QtGui.QColor(0, 128, 128))
        STYLE_LITERAL.setForeground(QtGui.QColor(255, 20, 215))
        STYLE_INLINE_UNIT.setForeground(QtGui.QColor(128, 0, 128))
    else:
        STYLE_HEADER.setForeground(QtGui.QColor(98, 178, 255))
        STYLE_COMMENT.setForeground(QtGui.QColor(153, 153, 153))
        STYLE_ANNOT_KEY.setForeground(QtGui.QColor(179, 179, 179))
        STYLE_ANNOT_VAL.setForeground(QtGui.QColor(171, 177, 205))
        STYLE_KEYWORD_1.setForeground(QtGui.QColor(10, 195, 87))
        STYLE_KEYWORD_1.setFontWeight(QtGui.QFont.Weight.Bold)
        STYLE_KEYWORD_2.setForeground(QtGui.QColor(10, 195, 87))
        STYLE_LITERAL.setForeground(QtGui.QColor(255, 223, 12))
        STYLE_INLINE_UNIT.setForeground(QtGui.QColor(168, 152, 33))

        global COLOR_SELECTED_LINE
        COLOR_SELECTED_LINE = QtGui.QColor(70, 70, 70)


# Classes & methods
class Editor(QtWidgets.QPlainTextEdit):
    """
    Source code editor used in Myokit.

    Provides the signal ``find_action(str)`` which is fired everything a find
    action occurred with a description that can be used in an application's
    status bar.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        # Current style
        self._palette = QtGui.QGuiApplication.palette()
        _check_for_dark_mode(self._palette)

        # Apply default settings
        self._default_settings()

        # Add line number area
        self._line_number_area = LineNumberArea(self)
        self._line_number_area.update_width(0)

        # Add current line highlighting and bracket matching
        self.cursorPositionChanged.connect(self.cursor_changed)
        self.cursor_changed()

        # Line position
        try:
            # https://doc.qt.io/qt-5/qfontmetrics.html#horizontalAdvance
            # Qt 5.5.11 and onwards
            self._line_offset = self.fontMetrics().horizontalAdvance(' ' * 79)
        except AttributeError:
            self._line_offset = self.fontMetrics().width(' ' * 79)

        # Number of blocks in page up/down
        self._blocks_per_page = 1

        # Last position in line, used for smart up/down buttons
        self._last_column = None
        self.textChanged.connect(self._text_has_changed)

    def cursor_changed(self):
        """ Slot: Called when the cursor position is changed """
        # Highlight current line
        extra_selections = []
        selection = QtWidgets.QTextEdit.ExtraSelection()
        selection.format.setBackground(COLOR_SELECTED_LINE)
        selection.format.setProperty(
            QtGui.QTextFormat.Property.FullWidthSelection, True)
        selection.cursor = self.textCursor()
        selection.cursor.clearSelection()
        extra_selections.append(selection)

        # Bracket matching
        cursor = self.textCursor()
        if not cursor.hasSelection():
            # Test if in front of or behind an opening or closing bracket
            pos = cursor.position()
            bracket = None
            if not cursor.atEnd():
                cursor.setPosition(
                    pos + 1, QtGui.QTextCursor.MoveMode.KeepAnchor)
                text = cursor.selectedText()
                if text in BRACKETS:
                    bracket = cursor
            elif bracket is None and not cursor.atStart():
                cursor.setPosition(pos - 1)
                cursor.setPosition(pos, QtGui.QTextCursor.MoveMode.KeepAnchor)
                text = cursor.selectedText()
                if text in BRACKETS:
                    bracket = cursor

            if bracket:
                # Find matching partner
                doc = self.document()
                depth = 1
                start = bracket.position()
                while depth > 0:
                    if text in BRACKETS_CLOSE:
                        other = doc.find(
                            text, start - 1,
                            QtGui.QTextDocument.FindFlag.FindBackward)
                        match = doc.find(
                            BRACKETS[text], start - 1,
                            QtGui.QTextDocument.FindFlag.FindBackward)
                    else:
                        other = doc.find(text, start)
                        match = doc.find(BRACKETS[text], start)
                    if match.isNull():
                        break
                    if other.isNull():
                        depth -= 1
                        start = match.position()
                    elif text in BRACKETS_CLOSE:
                        if other.position() < match.position():
                            depth -= 1
                            start = match.position()
                        else:
                            depth += 1
                            start = other.position()
                    else:
                        if match.position() < other.position():
                            depth -= 1
                            start = match.position()
                        else:
                            depth += 1
                            start = other.position()
                if depth == 0:
                    # Apply formatting
                    selection = QtWidgets.QTextEdit.ExtraSelection()
                    selection.cursor = bracket
                    selection.format.setBackground(self._palette.mid())
                    selection.format.setForeground(COLOR_BRACKET)
                    extra_selections.append(selection)
                    selection = QtWidgets.QTextEdit.ExtraSelection()
                    selection.cursor = match
                    selection.format.setBackground(self._palette.mid())
                    selection.format.setForeground(COLOR_BRACKET)
                    extra_selections.append(selection)

        if extra_selections:
            self.setExtraSelections(extra_selections)

    def cursor_position(self):
        """
        Returns a tuple ``(line, char)`` with the current cursor position. If
        a selection is made only the left position is used.

        Line and char counts both start at zero.
        """
        cursor = self.textCursor()
        line = cursor.blockNumber()
        char = cursor.selectionStart() - cursor.block().position()
        return (line, char)

    def _default_settings(self):
        """ Applies this editor's default settings. """
        # Set font
        self.setFont(FONT)
        # Set frame
        self.setFrameStyle(
            QtWidgets.QFrame.Shape.WinPanel | QtWidgets.QFrame.Shadow.Sunken)
        # Disable wrapping
        self.setLineWrapMode(QtWidgets.QPlainTextEdit.LineWrapMode.NoWrap)
        # Set tab width (if ever seen) to 4 spaces
        try:
            # https://doc.qt.io/qt-5/qtextedit-obsolete.html
            # https://doc.qt.io/qt-5/qfontmetrics.html#horizontalAdvance
            # Qt 5.10/5.11 and onwards
            ts = self.fontMetrics().horizontalAdvance(' ' * 4)
            self.setTabStopDistance(ts)
        except AttributeError:
            ts = self.fontMetrics().width(' ' * 4)
            self.setTabStopWidth(ts)

    def get_text(self):
        """ Returns the text in this editor. """
        return self.toPlainText()

    def jump_to(self, line, char):
        """ Jumps to the given line and row (with indices starting at 0). """
        block = self.document().findBlockByNumber(line)
        cursor = self.textCursor()
        cursor.setPosition(block.position() + char)
        self.setTextCursor(cursor)
        self.centerCursor()

    def keyPressEvent(self, event):
        """ Qt event: A key was pressed. """
        K = Qt.Key
        KM = Qt.KeyboardModifier
        MM = QtGui.QTextCursor.MoveMode
        MO = QtGui.QTextCursor.MoveOperation

        # Get key and modifiers
        key = event.key()
        mod = event.modifiers()
        # Possible modifiers:
        #  NoModifier
        #  ShiftModifier, ControlModifier, AltModifiier
        #  MetaModifier (i.e. super key)
        #  KeyPadModifier (button is part of keypad)
        #  GroupSwitchModifier (x11 thing)

        # Ignore the keypad modifier, we don't care!
        if mod & KM.KeypadModifier:
            mod = mod ^ KM.KeypadModifier   # xor!

        # Actions per key/modifier combination
        if key == K.Key_Tab and mod == KM.NoModifier:
            # Indent
            cursor = self.textCursor()
            start, end = cursor.selectionStart(), cursor.selectionEnd()
            if cursor.hasSelection():
                # Add single tab to all lines in selection
                cursor.beginEditBlock()     # Undo grouping
                doc = self.document()
                b = doc.findBlock(start)
                e = doc.findBlock(end).next()
                while b != e:
                    cursor.setPosition(b.position())
                    cursor.insertText(TABS * SPACE)
                    b = b.next()
                cursor.endEditBlock()
            else:
                # Insert spaces until next tab stop
                pos = cursor.positionInBlock()
                cursor.insertText((TABS - pos % TABS) * SPACE)

        elif key == K.Key_Backtab and mod == KM.ShiftModifier:
            # Dedent all lines in selection (or single line if no selection)
            '''
            cursor = self.textCursor()
            start, end = cursor.selectionStart(), cursor.selectionEnd()
            cursor.beginEditBlock() # Undo grouping
            doc = self.document()
            # Get blocks in selection
            blocks = []
            b = doc.findBlock(start)
            while b.isValid() and b.position() <= end:
                blocks.append(b)
                b = b.next()
            # Dedent
            for b in blocks:
                t = b.text()
                p1 = b.position()
                p2 = p1 + min(4, len(t) - len(t.lstrip()))
                c = self.textCursor()
                c.setPosition(p1)
                c.setPosition(p2, MM.KeepAnchor)
                c.removeSelectedText()
            cursor.endEditBlock()
            '''
            # This silly method is required because of a bug in qt5 (and 6?)
            cursor = self.textCursor()
            start, end = cursor.selectionStart(), cursor.selectionEnd()
            first = self.document().findBlock(start)
            q = 0
            new_text = []
            new_start, new_end = start, end
            b = QtGui.QTextBlock(first)
            while b.isValid() and b.position() <= end:
                t = b.text()
                p = min(4, len(t) - len(t.lstrip()))
                new_text.append(t[p:])
                if b == first:
                    new_start -= p
                new_end -= p
                q += p
                b = b.next()
            last = b.previous()
            new_start = max(new_start, first.position())
            new_end = max(new_end, new_start)
            if q > 0:
                # Cut text, replace with new
                cursor.beginEditBlock()
                cursor.setPosition(first.position())
                cursor.setPosition(
                    last.position() + last.length() - 1, MM.KeepAnchor)
                cursor.removeSelectedText()
                cursor.insertText('\n'.join(new_text))
                cursor.endEditBlock()
                # Set new cursor
                cursor.setPosition(new_start)
                cursor.setPosition(new_end, MM.KeepAnchor)
                self.setTextCursor(cursor)

        elif key == K.Key_Enter or key == K.Key_Return:
            # Enter/Return with modifier is overruled here to mean nothing
            # This is very important as the default for shift-enter is to
            # start a new line within the same block (this can't happen with
            # copy-pasting, so it's safe to just catch it here).
            if mod == KM.NoModifier:
                # "Smart" enter:
                #   - If selection, selection is deleted
                #   - Else, autoindenting is performed
                cursor = self.textCursor()
                cursor.beginEditBlock()
                if cursor.hasSelection():
                    # Replace selection with newline,
                    cursor.removeSelectedText()
                    cursor.insertBlock()
                else:
                    # Insert new line with correct indenting
                    b = self.document().findBlock(cursor.position())
                    t = b.text()
                    i = t[:len(t) - len(t.lstrip())]
                    i = i[:cursor.positionInBlock()]
                    cursor.insertBlock()
                    cursor.insertText(i)
                cursor.endEditBlock()
                # Scroll if necessary
                self.ensureCursorVisible()

        elif key == K.Key_Home and (
                mod == KM.NoModifier or mod == KM.ShiftModifier):
            # Plain home button: move to start of line
            # If Control is used: Jump to start of document
            # Ordinary home button: Jump to first column or first
            # non-whitespace character
            cursor = self.textCursor()
            block = cursor.block()
            cp = cursor.position()
            bp = block.position()
            if cp != bp:
                # Jump to first column
                newpos = bp
                # Smart up/down:
                self._last_column = 0
            else:
                # Already at first column: Jump to first non-whitespace or
                # end of line if all whitespace
                t = block.text()
                indent = len(t) - len(t.lstrip())
                newpos = bp + indent
                # Smart up/down:
                self._last_column = indent
            # If Shift is used: only move position (keep anchor, i.e. select)
            cursor.setPosition(
                newpos,
                MM.KeepAnchor if mod == KM.ShiftModifier else MM.MoveAnchor)
            self.setTextCursor(cursor)

        elif key == K.Key_Home and (
                mod == KM.ControlModifier
                or mod == KM.ControlModifier & KM.ShiftModifier):
            # Move to start of document
            # If Shift is used: only move position (keep anchor, i.e. select)
            cursor = self.textCursor()
            cursor.setPosition(
                0, MM.KeepAnchor if mod == KM.ShiftModifier else MM.MoveAnchor)
            self.setTextCursor(cursor)

        elif key in (K.Key_Up, K.Key_Down) and mod == KM.AltModifier:
            # Move selected lines up or down
            # Get current selection
            doc = self.document()
            cursor = self.textCursor()
            start, end = cursor.selectionStart(), cursor.selectionEnd()
            block1 = doc.findBlock(start)
            if start == end:
                block2 = block1
            else:
                block2 = doc.findBlock(end)
                # Whole line selection? Then move end back 1 position
                if end == block2.position():
                    end -= 1
                    block2 = block2.previous()  # always valid
            block2 = block1 if start == end else doc.findBlock(end)
            # Check if we can move
            if key == K.Key_Up:
                if not block1.previous().isValid():
                    return
            elif not block2.next().isValid():
                return
            # Select full line(s)
            b1pos = block1.position()
            cursor.beginEditBlock()
            cursor.setPosition(b1pos)
            cursor.setPosition(end, MM.KeepAnchor)
            cursor.movePosition(MO.EndOfLine, MM.KeepAnchor)
            line = cursor.selectedText()
            size = cursor.selectionEnd() - cursor.selectionStart()
            cursor.removeSelectedText()
            if key == K.Key_Up:
                cursor.deletePreviousChar()
                cursor.movePosition(MO.StartOfLine)
                cursor.insertText(line + '\n')
                cursor.movePosition(MO.Left)
            else:
                cursor.deleteChar()
                cursor.movePosition(MO.EndOfLine)
                cursor.insertText('\n' + line)
            cursor.endEditBlock()
            # Cursor is at the end of the moved lines.
            # Set moved lines as selection
            cursor.movePosition(MO.Left, MM.KeepAnchor, size)
            self.setTextCursor(cursor)

        elif key in (K.Key_Up, K.Key_Down, K.Key_PageUp, K.Key_PageDown) \
                and (mod == KM.NoModifier or mod == KM.ShiftModifier):
            # Move cursor up/down
            # Maintain the column position, even when the current row doesn't
            # have as many characters. Reset this behavior as soon as a
            # left/right home/end action is made or whenever the text is
            # changed.
            # Set up operation
            anchor = (
                MM.KeepAnchor if mod == KM.ShiftModifier else MM.MoveAnchor)
            operation = (MO.PreviousBlock if key in (K.Key_Up, K.Key_PageUp)
                         else MO.NextBlock)
            n = 1 if key in (K.Key_Up, K.Key_Down) else (
                self._blocks_per_page - 3)

            # Move
            cursor = self.textCursor()
            if self._last_column is None:
                # Update "smart" column
                self._last_column = cursor.positionInBlock()
            if cursor.movePosition(operation, anchor, n):
                column = min(cursor.block().length() - 1, self._last_column)
                cursor.setPosition(cursor.position() + column, anchor)
            else:
                # Up/Down beyond document start/end? Move cursor to document
                # start/end and update last column
                if operation == MO.NextBlock:
                    cursor.movePosition(MO.EndOfBlock, anchor)
                else:
                    cursor.movePosition(MO.StartOfBlock, anchor)
                self._last_column = cursor.positionInBlock()
            self.setTextCursor(cursor)

        elif key in (K.Key_Left, K.Key_Right, K.Key_End) and not (
                mod & KM.AltModifier):
            # Allow all modifiers except alt
            # Reset smart up/down behavior
            self._last_column = None
            # Pass to parent class
            super().keyPressEvent(event)

        elif key == K.Key_Insert and mod == KM.NoModifier:
            # Insert/replace
            self.setOverwriteMode(not self.overwriteMode())

        else:
            # Default keyboard shortcuts / functions:
            # Backspace             OK
            # Delete                OK
            # Control+C             OK
            # Control+V             OK
            # Control+X             OK
            # Control+Insert        OK
            # Shift+Insert          OK
            # Shift+Delete          OK
            # Control+Z             OK
            # Control+Y             OK
            # LeftArrow             Overwritten (maintained)
            # RightArrow            Overwritten (maintained)
            # UpArrow               Overwritten (maintained)
            # DownArrow             Overwritten (maintained)
            # Control+RightArrow    OK (Jump to next word)
            # Control+LeftArrow     OK (Jump to previous word)
            # Control+UpArrow       Removed
            # Control+Down Arrow    Removed
            # PageUp                Overwritten (maintained)
            # PageDown              Overwritten (maintained)
            # Home                  Overwritten (maintained)
            # End                   Overwritten (maintained)
            # Control+Home          Overwritten (maintained)
            # Control+End           Overwritten (maintained)
            # Alt+Wheel             OK (Horizontal scrolling)
            # Control+Wheel         OK (Fast scrolling)
            # Control+K             Removed
            # Not listed, but very important:
            # Shift-Enter           Starts new line within the same block!
            #                       Definitely removed
            # Ctrl-i                Undocumented, but inserts tab...
            ctrl_ignore = (K.Key_K, K.Key_I)
            if mod == KM.ControlModifier and key in ctrl_ignore:
                # Control-K: ignore
                pass
            elif key == K.Key_Up or key == K.Key_Down:
                # Up/down with modifiers: ignore
                pass
            else:
                # Let parent class handle it
                super().keyPressEvent(event)

    def _line_number_area_width(self):
        """ Returns the required width for the number area. """
        text = str(max(1, self.blockCount()))
        try:
            # https://doc.qt.io/qt-5/qfontmetrics.html#horizontalAdvance
            # Qt 5.5.11 and onwards
            return 8 + self.fontMetrics().horizontalAdvance(text)
        except AttributeError:
            return 8 + self.fontMetrics().width(text)

    def _line_number_area_paint(self, area, event):
        """ Repaints the line number area. """
        # Area to repaint
        rect = event.rect()
        etop = rect.top()
        ebot = rect.bottom()

        # Font metrics
        metrics = self.fontMetrics()
        height = metrics.height()
        width = area.width()

        # Create painter, set font color
        painter = QtGui.QPainter(area)
        painter.fillRect(rect, self._palette.button())
        painter.setPen(self._palette.buttonText().color())

        # Get top and bottom of first visible block
        block = self.firstVisibleBlock()
        geom = self.blockBoundingGeometry(block)
        btop = int(geom.translated(self.contentOffset()).top())
        bbot = int(btop + geom.height())

        # Iterate over visible blocks
        count = block.blockNumber()
        while block.isValid() and btop <= ebot:
            count += 1
            if block.isVisible() and bbot >= etop:
                painter.drawText(0, btop, width - 4, height,
                                 Qt.AlignmentFlag.AlignRight, str(count))
            block = block.next()
            btop = bbot
            bbot += int(self.blockBoundingRect(block).height())

    def paintEvent(self, e):
        """ Paints this editor. """

        # Paint the editor
        super().paintEvent(e)

        # Paint a line between the editor and the line number area
        x = int(
            self.contentOffset().x()
            + self.document().documentMargin()
            + self._line_offset
        )
        p = QtGui.QPainter(self.viewport())
        p.setPen(QtGui.QPen(QtGui.QColor('#ddd')))
        rect = e.rect()
        p.drawLine(x, rect.top(), x, rect.bottom())

    def replace(self, text):
        """
        Replaces the current text with the given text, in a single operation
        that does not reset undo/redo.
        """
        self.selectAll()
        cursor = self.textCursor()
        cursor.beginEditBlock()
        cursor.removeSelectedText()
        self.appendPlainText(str(text))
        cursor.endEditBlock()

    def resizeEvent(self, event):
        """ Qt event: Editor is resized. """
        super().resizeEvent(event)
        # Update line number area
        rect = self.contentsRect()
        self._line_number_area.setGeometry(
            rect.left(), rect.top(),
            self._line_number_area_width(), rect.height())
        # Set number of "blocks" per page
        font = self.fontMetrics()
        self._blocks_per_page = int(rect.height() / font.height())

    def set_cursor(self, pos):
        """
        Changes the current cursor to the given position and scrolls so that
        its visible.
        """
        cursor = self.textCursor()
        cursor.setPosition(pos)
        self.setTextCursor(cursor)
        self.centerCursor()

    def set_text(self, text):
        """ Replaces the text in this editor. """
        if text:
            self.setPlainText(str(text))
        else:
            # Bizarre workaround for bug:
            #   https://bugreports.qt.io/browse/QTBUG-42318
            self.selectAll()
            cursor = self.textCursor()
            cursor.removeSelectedText()
            doc = self.document()
            doc.clearUndoRedoStacks()
            doc.setModified(False)

    def _text_has_changed(self):
        """
        Called whenever the text has changed, resets the smart up/down
        behavior.
        """
        self._last_column = None

    def toggle_comment(self):
        """ Comments or uncomments the selected lines """
        # Comment or uncomment selected lines
        cursor = self.textCursor()
        start, end = cursor.selectionStart(), cursor.selectionEnd()
        doc = self.document()
        first, last = doc.findBlock(start), doc.findBlock(end)
        # Determine minimum indent and adding or removing
        block = first
        blocks = [first]
        while block != last:
            block = block.next()
            blocks.append(block)
        lines = [block.text() for block in blocks]
        indent = [len(t) - len(t.lstrip()) for t in lines if len(t) > 0]
        indent = min(indent) if indent else 0
        remove = True
        for line in lines:
            if line[indent:indent + 1] != '#':
                remove = False
                break
        cursor.beginEditBlock()
        if remove:
            for block in blocks:
                p = block.position() + indent
                cursor.setPosition(p)
                cursor.setPosition(
                    p + 1, QtGui.QTextCursor.MoveMode.KeepAnchor)
                cursor.removeSelectedText()
        else:

            for block in blocks:
                p = block.position()
                n = len(block.text())
                if len(block.text()) < indent:
                    cursor.setPosition(p)
                    cursor.setPosition(
                        p + n, QtGui.QTextCursor.MoveMode.KeepAnchor)
                    cursor.removeSelectedText()
                    cursor.insertText(' ' * indent + '#')
                else:
                    cursor.setPosition(p + indent)
                    cursor.insertText('#')
        cursor.endEditBlock()

    def trim_trailing_whitespace(self):
        """ Trims all trailing whitespace from this document. """
        block = self.document().begin()
        cursor = self.textCursor()
        cursor.beginEditBlock()     # Undo grouping
        while block.isValid():
            t = block.text()
            a = len(t)
            b = len(t.rstrip())
            if a > b:
                cursor.setPosition(block.position() + b)
                cursor.setPosition(block.position() + a,
                                   QtGui.QTextCursor.MoveMode.KeepAnchor)
                cursor.removeSelectedText()
            block = block.next()
        cursor.endEditBlock()


class LineNumberArea(QtWidgets.QWidget):
    """
    Line number area widget for the editor. All real actions are delegated to
    the text area class.

    The line number is drawn in the left margin of the :class:`Editor` widget,
    the space to do so is created by setting the editor's viewport margins.
    """

    def __init__(self, editor):
        super().__init__(editor)
        self._editor = editor
        self._editor.blockCountChanged.connect(self.update_width)
        self._editor.updateRequest.connect(self.update_contents)

    def paintEvent(self, event):
        """ Qt event: Paint this area. """
        self._editor._line_number_area_paint(self, event)

    def sizeHint(self):
        """ Qt event: Suggest a size for this area. """
        return QtCore.QSize(self._editor._line_number_area_width(), 0)

    def update_contents(self, rect, scroll):
        """
        Slot: Invoked when the text editor view has changed and the line
        numbers need to be redrawn.
        """
        if scroll:
            # Scroll
            self.scroll(0, scroll)
        else:
            self.update()

    def update_width(self, count):
        """
        Slot: Invoked when the number of lines in the text area changed, which
        might change the size of the number area.
        """
        # Update the editor margins, so that the line number area can be
        # painted in the margins.
        self._editor.setViewportMargins(
            2 + self._editor._line_number_area_width(), 0, 0, 0)


class FindReplaceWidget(QtWidgets.QWidget):
    """
    Find/replace widget for :class:`Editor`.
    """
    # Signal: Find action happened, update with text
    # Attributes: (description)
    find_action = QtCore.Signal(str)

    def __init__(self, parent, editor):
        super().__init__(parent)
        self._editor = editor

        # Create widgets
        self._replace_all_button = QtWidgets.QPushButton('Replace all')
        self._replace_all_button.clicked.connect(self.action_replace_all)
        self._replace_button = QtWidgets.QPushButton('Replace')
        self._replace_button.clicked.connect(self.action_replace)
        self._find_button = QtWidgets.QPushButton('Find')
        self._find_button.clicked.connect(self.action_find)
        self._search_label = QtWidgets.QLabel('Search for')
        self._search_field = QtWidgets.QLineEdit()
        self._replace_label = QtWidgets.QLabel('Replace with')
        self._replace_field = QtWidgets.QLineEdit()
        self._case_check = QtWidgets.QCheckBox('Case sensitive')
        self._whole_check = QtWidgets.QCheckBox('Match whole word only')

        # Create layout
        text_layout = QtWidgets.QGridLayout()
        text_layout.addWidget(self._search_label, 0, 0)
        text_layout.addWidget(self._search_field, 0, 1)
        text_layout.addWidget(self._replace_label, 1, 0)
        text_layout.addWidget(self._replace_field, 1, 1)
        check_layout = QtWidgets.QBoxLayout(
            QtWidgets.QBoxLayout.Direction.TopToBottom)
        check_layout.addWidget(self._case_check)
        check_layout.addWidget(self._whole_check)
        button_layout = QtWidgets.QGridLayout()
        button_layout.addWidget(self._replace_all_button, 0, 1)
        button_layout.addWidget(self._replace_button, 0, 2)
        button_layout.addWidget(self._find_button, 0, 3)

        layout = QtWidgets.QBoxLayout(
            QtWidgets.QBoxLayout.Direction.TopToBottom)
        layout.addLayout(text_layout)
        layout.addLayout(check_layout)
        layout.addLayout(button_layout)
        layout.addStretch(1)
        self.setLayout(layout)

        # Accept keyboard focus on search and replace fields
        self._search_field.setEnabled(True)
        self._replace_field.setEnabled(True)

    def action_find(self):
        """ Qt slot: Find (next) item. """
        query = self._search_field.text()
        if query == '':
            self.find_action.emit('No query set')
            return
        flags = QtGui.QTextDocument.FindFlag(0)
        if self._case_check.isChecked():
            flags |= QtGui.QTextDocument.FindFlag.FindCaseSensitively
        if self._whole_check.isChecked():
            flags |= QtGui.QTextDocument.FindFlag.FindWholeWords
        if flags:
            found = self._editor.find(query, flags)
        else:
            found = self._editor.find(query)
        if found is False:
            # Not found? Try from top of document
            previous_cursor = self._editor.textCursor()
            previous_scroll = self._editor.verticalScrollBar().value()
            cursor = self._editor.textCursor()
            cursor.setPosition(0)
            self._editor.setTextCursor(cursor)
            if flags:
                found = self._editor.find(query, flags)
            else:
                found = self._editor.find(query)
            if found is False:
                self._editor.setTextCursor(previous_cursor)
                self._editor.verticalScrollBar().setValue(previous_scroll)
                self.find_action.emit('Query not found.')
                return
        cursor = self._editor.textCursor()
        line = 1 + cursor.blockNumber()
        char = cursor.selectionStart() - cursor.block().position()
        self.find_action.emit(
            'Match found on line ' + str(line) + ' char ' + str(char) + '.')

    def action_replace(self):
        """ Qt slot: Replace found item with replacement. """
        query = self._search_field.text()
        replacement = self._replace_field.text()
        if query == '':
            self.find_action.emit('No query set')
            return
        cursor = self._editor.textCursor()
        a, b = cursor.selectedText(), query
        if not self._case_check.isChecked():
            a, b = a.lower(), b.lower()
        if a == b:
            cursor.insertText(replacement)
        self.action_find()

    def action_replace_all(self):
        """ Qt slot: Replace all found items with replacement """
        query = self._search_field.text()
        replacement = self._replace_field.text()
        if query == '':
            self.find_action.emit('No query set')
            return
        flags = QtGui.QTextDocument.FindFlag(0)
        if self._case_check.isChecked():
            flags |= QtGui.QTextDocument.FindFlag.FindCaseSensitively
        if self._whole_check.isChecked():
            flags |= QtGui.QTextDocument.FindFlag.FindWholeWords
        n = 0
        found = True
        scrollpos = self._editor.verticalScrollBar().value()
        grouping = self._editor.textCursor()
        grouping.beginEditBlock()
        continue_from_top = True
        while found:
            if flags:
                found = self._editor.find(query, flags)
            else:
                found = self._editor.find(query)
            if not found and continue_from_top:
                # Not found? Try from top of document
                cursor = self._editor.textCursor()
                cursor.setPosition(0)
                self._editor.setTextCursor(cursor)
                if flags:
                    found = self._editor.find(query, flags)
                else:
                    found = self._editor.find(query)
                # Don't keep going round and round
                # (This can happen if you replace something with itself, or
                # with a different case version of itself in a case-insensitive
                # search).
                continue_from_top = False
            if found:
                cursor = self._editor.textCursor()
                cursor.insertText(replacement)
                n += 1
        grouping.endEditBlock()
        self._editor.setTextCursor(grouping)
        self._editor.verticalScrollBar().setValue(scrollpos)
        self.find_action.emit('Replaced ' + str(n) + ' occurrences.')

    def activate(self):
        """ Updates the contents of the search field and gives it focus. """
        cursor = self._editor.textCursor()
        if cursor.hasSelection():
            self._search_field.setText(cursor.selectedText())
        self._search_field.selectAll()
        self._search_field.setFocus()

    def keyPressEvent(self, event):
        """ Qt event: A key-press reaches the widget. """
        key = event.key()
        if key == Qt.Key.Key_Enter or key == Qt.Key.Key_Return:
            self.action_find()
        else:
            super().keyPressEvent(event)

    def load_config(self, config, section):
        """
        Loads this search's configuration using the given :class:`ConfigParser`
        ``config``. Loads all settings from the section ``section``.
        """
        if config.has_section(section):
            # Find options: case sensitive / whole word
            if config.has_option(section, 'case_sensitive'):
                self._case_check.setChecked(
                    config.getboolean(section, 'case_sensitive'))
            if config.has_option(section, 'whole_word'):
                self._whole_check.setChecked(
                    config.getboolean(section, 'whole_word'))

    def save_config(self, config, section):
        """
        Saves this search's configuration using the given :class:`ConfigParser`
        ``config``. Stores all settings in the section ``section``.
        """
        config.add_section(section)
        # Find options: case sensitive / whole word
        config.set(section, 'case_sensitive', self._case_check.isChecked())
        config.set(section, 'whole_word', self._whole_check.isChecked())


class ModelHighlighter(QtGui.QSyntaxHighlighter):
    """
    Syntax highlighter for ``mmt`` model definitions.
    """
    KEYWORD_1 = ['use', 'as']
    KEYWORD_2 = ['and', 'or', 'not']
    ANNOT_KEYS = ['in', 'bind', 'label']

    def __init__(self, document):
        super().__init__(document)

        # Expressions used to find strings & comments
        R = QtCore.QRegularExpression
        self._string = R(r'"""')

        # Headers
        name = r'[a-zA-Z]+[a-zA-Z0-9_]*'
        self._rule_head = R(r'^\s*(\[{1,2}' + name + '\]{1,2})')

        # Simple rules
        self._rules = []

        # Numbers
        pattern = R(r'\b[+-]?[0-9]*\.?[0-9]+([eE][+-]?[0-9]+)?\b')
        self._rules.append((pattern, STYLE_LITERAL))
        unit = r'\[([a-zA-Z0-9/^-]|\*)+\]'
        self._rules.append((R(unit), STYLE_INLINE_UNIT))

        # Keywords
        for keyword in self.KEYWORD_1:
            self._rules.append((R(r'\b' + keyword + r'\b'), STYLE_KEYWORD_1))
        for keyword in self.KEYWORD_2:
            self._rules.append((R(r'\b' + keyword + r'\b'), STYLE_KEYWORD_2))

        # Meta-data coloring
        self._rules_labels = [
            R(r'(\s*)(bind)\s+(' + name + ')'),
            R(r'(\s*)(label)\s+(' + name + ')'),
        ]
        self._rule_meta = R(r'^\s*(' + name + r':)(\s*)(.+)')
        self._rule_var_unit = R(r'^(\s*)(in)(\s*)(' + unit + ')')

        # Comment
        self._comment = R(r'#')

    def _highlight_ok(self, strings, start, length):
        """ Checks if the string ``start`` to ``length`` needs formatted. """
        for lo, hi in strings:
            if lo <= start < hi or lo <= start + length < hi:
                return False
        return True

    def highlightBlock(self, text):
        """ Qt: Called whenever a block should be highlighted. """

        # To avoid formatting within strings each is stored as a (start, end).
        strings = []
        # If the start has been handled, set the offset.
        offset = 0
        # If the end has been handled, chop it off the string

        # Multi-line strings are done first, because they overrule a lot of
        # things and we can skip formatting if we're inside one.
        # Block states: 0=No string, 1=A """ string
        self.setCurrentBlockState(0)

        # Continuing a multi-line string?
        if self.previousBlockState() == 1:
            # Search for string stop
            ms = self._string.match(text)
            if ms.hasMatch():
                # Terminate the multi-line string
                offset = ms.capturedEnd(0)
                self.setFormat(0, offset, STYLE_ANNOT_VAL)
            else:
                # Whole line in the string
                self.setCurrentBlockState(1)
                self.setFormat(0, len(text), STYLE_ANNOT_VAL)
                return
        else:
            # Search for string start
            ms = self._string.match(text)
            if ms.hasMatch():
                # Potential start, but check that it's not commented out
                start = ms.capturedStart()
                mc = self._comment.match(text)
                if not (mc.hasMatch() and mc.capturedStart() < start):
                    # Definitely a string start. See if it ends on this line
                    me = self._string.match(text, offset=ms.capturedEnd())
                    if me.hasMatch():
                        # Terminate the single-line string
                        end = me.capturedEnd()
                        self.setFormat(start, end - start, STYLE_ANNOT_VAL)
                        strings.append((start, end))
                    else:
                        # Multi-line string
                        self.setCurrentBlockState(1)
                        self.setFormat(start, len(text), STYLE_ANNOT_VAL)

        # Comment
        i = self._comment.globalMatch(text, offset=offset)
        while i.hasNext():
            m = i.next()
            x = m.capturedStart()
            if self._highlight_ok(strings, x, 1):
                self.setFormat(x, len(text) - x, STYLE_COMMENT)
                text = text[:x]
                break

        # Rule-based formatting
        for (pattern, style) in self._rules:
            i = pattern.globalMatch(text, offset=offset)
            while i.hasNext():
                m = i.next()
                x, w = m.capturedStart(), m.capturedLength()
                if self._highlight_ok(strings, x, w):
                    self.setFormat(x, w, style)

        # Model and component headers (must be at start of string)
        if offset == 0:
            m = self._rule_head.match(text)
            if m.hasMatch():
                x, w = m.capturedStart(1), m.capturedLength(1)
                self.setFormat(x, w, STYLE_HEADER)

        # Variable units (must be at start of string)
        if offset == 0:
            m = self._rule_var_unit.match(text)
            if m.hasMatch():
                self.setFormat(
                    m.capturedStart(2), m.capturedLength(2), STYLE_ANNOT_KEY)
                self.setFormat(
                    m.capturedStart(4), m.capturedLength(4), STYLE_ANNOT_VAL)

        # Binds and labels
        for pattern in self._rules_labels:
            i = pattern.globalMatch(text, offset=offset)
            while i.hasNext():
                m = i.next()
                x, w = m.capturedStart(), m.capturedLength()
                if self._highlight_ok(strings, x, w):
                    self.setFormat(m.capturedStart(2), m.capturedLength(2),
                                   STYLE_ANNOT_KEY)
                    self.setFormat(m.capturedStart(3), m.capturedLength(3),
                                   STYLE_ANNOT_VAL)

        # Meta properties (must be at start of string)
        if offset == 0:
            m = self._rule_meta.match(text)
            if m.hasMatch():
                self.setFormat(
                    m.capturedStart(1), m.capturedLength(1), STYLE_ANNOT_KEY)
                # Don't reformat strings (or bits after string end!)
                if m.captured(3)[:3] != '"""':
                    self.setFormat(m.capturedStart(3), m.capturedLength(3),
                                   STYLE_ANNOT_VAL)


class ProtocolHighlighter(QtGui.QSyntaxHighlighter):
    """
    Syntax highlighter for ``mmt`` protocol definitions.
    """
    def __init__(self, document):
        super().__init__(document)

        # Headers and units
        R = QtCore.QRegularExpression
        self._rule_head = R(r'^\s*(\[\[[a-zA-Z0-9_]+\]\])')

        # Highlighting rules
        self._rules = []

        # Numbers
        self._rules.append(
            (R(r'\b[+-]?[0-9]*\.?[0-9]+([eE][+-]?[0-9]+)?\b'), STYLE_LITERAL))

        # Keyword "next"
        self._rules.append((R(r'\bnext\b'), STYLE_KEYWORD_1))

        # Comments
        self._rules.append((R(r'#[^\n]*'), STYLE_COMMENT))

    def highlightBlock(self, text):
        """ Qt: Called whenever a block should be highlighted. """

        # Rule based formatting
        for (pattern, style) in self._rules:
            i = pattern.globalMatch(text)
            while i.hasNext():
                m = i.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), style)

        # Protocol header (must be at strart of string)
        m = self._rule_head.match(text)
        if m.hasMatch():
            self.setFormat(
                m.capturedStart(1), m.capturedLength(1), STYLE_HEADER)


class ScriptHighlighter(QtGui.QSyntaxHighlighter):
    """
    Syntax highlighter for ``mmt`` script files.
    """
    def __init__(self, document):
        super().__init__(document)

        # Script header
        R = QtCore.QRegularExpression
        self._rule_head = R(r'^\s*(\[\[[a-zA-Z0-9_]+\]\])')

        # Highlighting rules
        self._rules = []

        # Keywords
        import keyword
        for kw in keyword.kwlist:
            self._rules.append((R(r'\b' + kw + r'\b'), STYLE_KEYWORD_1))

        # Built-in essential functions
        for func in _PYFUNC:
            self._rules.append((R(r'\b' + str(func) + r'\b'), STYLE_KEYWORD_2))

        # Literals: numbers, True, False, None
        # Override some keywords
        self._rules.append((R(r'\b[+-]?[0-9]*\.?[0-9]+([eE][+-]?[0-9]+)?\b'),
                            STYLE_LITERAL))
        self._rules.append((R(r'\bTrue\b'), STYLE_LITERAL))
        self._rules.append((R(r'\bFalse\b'), STYLE_LITERAL))
        self._rules.append((R(r'\bNone\b'), STYLE_LITERAL))

        # Strings
        self._s1 = R(r'"')
        self._s2 = R(r"'")
        self._ms1 = R(r'"""')
        self._ms2 = R(r"'''")
        self._s_start = R(r'"""|\'\'\'|"|\'')
        self._s_end = {
            '"': self._s1, "'": self._s2, '"""': self._ms1, "'''": self._ms2}

        # Comments
        self._comment = R(r'#')

    def _highlight_ok(self, strings, start, length):
        """ Checks if the string ``start`` to ``length`` needs formatted. """
        for lo, hi in strings:
            if lo <= start < hi or lo <= start + length < hi:
                return False
        return True

    def highlightBlock(self, text):
        """ Qt: Called whenever a block should be highlighted. """

        # To avoid formatting within strings each is stored as a (start, end).
        strings = []
        # If the start has been handled, set the offset.
        offset = 0
        # If the end has been handled, chop it off the string

        # Multi-line strings are done first, because they overrule a lot of
        # things and we can skip formatting if we're inside one.
        # Block states: 0=No string, 1=A " " " string, 2=A ' ' ' string
        self.setCurrentBlockState(0)

        # Continuing a multi-line string?
        previous = self.previousBlockState()
        if previous == 1 or previous == 2:
            # Search for string stop
            r = self._ms1 if previous == 1 else self._ms2
            ms = r.match(text)
            if ms.hasMatch():
                # Terminate the multi-line string, and increase global offset
                offset = ms.capturedEnd(0)
                self.setFormat(0, offset, STYLE_LITERAL)
            else:
                # Whole line in the string
                self.setCurrentBlockState(previous)
                self.setFormat(0, len(text), STYLE_LITERAL)
                return

        # Search for string starts (single or multi-line)
        stroff = offset     # Offset for string start/end searching
        m1 = self._s_start.match(text, offset=stroff)
        while m1.hasMatch():
            stroff = m1.capturedEnd()
            start = m1.capturedStart()
            # Are we in a comment?
            mc = self._comment.match(text)
            if (mc.hasMatch() and mc.capturedStart() < start):
                # No point searching for further string starts
                stroff = len(text)
            else:
                # Find string end
                m2 = self._s_end[m1.captured()].match(text, offset=stroff)
                if m2.hasMatch():
                    stroff = m2.capturedEnd()
                    # Ignore if escaped
                    if text[m2.capturedStart() - 1] != '\\':
                        # Terminate the single line string and move on
                        self.setFormat(start, stroff - start, STYLE_LITERAL)
                        strings.append((start, stroff))
                elif m1.capturedLength() > 1:
                    # Multi-line string start. Block finished!
                    self.setCurrentBlockState(
                        1 if m1.captured() == '"""' else 2)
                    self.setFormat(start, len(text) - start, STYLE_LITERAL)
                    return
                # No Match? Then not a string so ignore and continue
            m1 = self._s_start.match(text, offset=stroff)

        # Comment
        i = self._comment.globalMatch(text, offset=offset)
        while i.hasNext():
            m = i.next()
            x = m.capturedStart()
            if self._highlight_ok(strings, x, 1):
                self.setFormat(x, len(text) - x, STYLE_COMMENT)
                text = text[:x]
                break

        # Script header (must be at start of string)
        if offset == 0:
            m = self._rule_head.match(text)
            if m.hasMatch():
                self.setFormat(
                    m.capturedStart(1), m.capturedLength(1), STYLE_HEADER)

        # Rule based formatting
        for (pattern, style) in self._rules:
            i = pattern.globalMatch(text, offset=offset)
            while i.hasNext():
                m = i.next()
                x, w = m.capturedStart(), m.capturedLength()
                if self._highlight_ok(strings, x, w):
                    self.setFormat(x, w, style)


# List of essential built-in python functions
_PYFUNC = [
    'abs()',
    'aiter()',
    'all()',
    'any()',
    'anext()',
    'ascii()',
    'bin()',
    'bool()',
    'breakpoint()',
    'bytearray()',
    'bytes()',
    'callable()',
    'chr()',
    'classmethod()',
    'compile()',
    'complex()',
    'delattr()',
    'dict()',
    'dir()',
    'divmod()',
    'enumerate()',
    'eval()',
    'exec()',
    'filter()',
    'float()',
    'format()',
    'frozenset()',
    'getattr()',
    'globals()',
    'hasattr()',
    'hash()',
    'help()',
    'hex()',
    'id()',
    'input()',
    'int()',
    'isinstance()',
    'issubclass()',
    'iter()',
    'len()',
    'list()',
    'locals()',
    'map()',
    'max()',
    'memoryview()',
    'min()',
    'next()',
    'object()',
    'oct()',
    'open()',
    'ord()',
    'pow()',
    'print()',
    'property()',
    'range()',
    'repr()',
    'reversed()',
    'round()',
    'set()',
    'setattr()',
    'slice()',
    'sorted()',
    'staticmethod()',
    'str()',
    'sum()',
    'super()',
    'tuple()',
    'type()',
    'vars()',
    'zip()',
    '__import__()',
]
