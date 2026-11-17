#!/usr/bin/env python3
#
# Tests the myokit.gui module.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import unittest
import unittest.mock

from myokit.tests import qt_application


class GuiTest(unittest.TestCase):
    """
    Tests the methods and settings in ``myokit.gui``.
    """

    @classmethod
    def setUpClass(cls):
        cls.app = qt_application()

    def test_backend(self):
        # Test the selected backend and the Qt modules it provides
        import myokit.gui as gui
        self.assertIn(gui.backend, ('PyQt5', 'PyQt6', 'PySide2', 'PySide6'))
        self.assertIn(gui.qtversion, (5, 6))
        self.assertEqual(gui.qtversion, int(gui.backend[-1]))
        for name in ('QtCore', 'QtGui', 'QtWidgets', 'Qt'):
            self.assertTrue(hasattr(gui, name))

        # PySide-style names are available for every backend
        self.assertTrue(hasattr(gui.QtCore, 'Signal'))
        self.assertTrue(hasattr(gui.QtCore, 'Slot'))
        self.assertTrue(hasattr(gui.QtGui, 'QAction'))

        # Temporary variables are removed
        for name in ('pyqt5', 'pyqt6', 'pyside2', 'pyside6'):
            self.assertFalse(hasattr(gui, name))

        # Toolbar style is set
        self.assertIsInstance(
            gui.TOOL_BUTTON_STYLE, gui.Qt.ToolButtonStyle)

    def test_icon(self):
        # Test creating icons
        import myokit.gui as gui

        # All fallback icons exist
        for path in gui.ICONS.values():
            self.assertTrue(path.is_file(), str(path))

        # Known icons
        for name in gui.ICONS:
            icon = gui.icon(name)
            self.assertIsInstance(icon, gui.QtGui.QIcon)
            self.assertFalse(icon.isNull(), name)

        # Unknown icons
        self.assertRaises(KeyError, gui.icon, 'not-an-icon')

    def test_in_dark_mode(self):
        # Test dark mode detection
        import myokit.gui as gui

        palette = gui.QtGui.QPalette()
        palette.setColor(
            gui.QtGui.QPalette.ColorRole.Base, gui.QtGui.QColor(255, 255, 255))
        self.assertFalse(gui._in_dark_mode(palette))
        palette.setColor(
            gui.QtGui.QPalette.ColorRole.Base, gui.QtGui.QColor(0, 0, 0))
        self.assertTrue(gui._in_dark_mode(palette))
        palette.setColor(
            gui.QtGui.QPalette.ColorRole.Base, gui.QtGui.QColor(30, 40, 200))
        self.assertTrue(gui._in_dark_mode(palette))
        palette.setColor(
            gui.QtGui.QPalette.ColorRole.Base,
            gui.QtGui.QColor(200, 200, 100))
        self.assertFalse(gui._in_dark_mode(palette))

        # Works with the application palette
        self.assertIsInstance(
            gui._in_dark_mode(gui.QtGui.QGuiApplication.palette()), bool)

    def test_monospace_font(self):
        # Test creating a monospace font
        import myokit.gui as gui

        font = gui.qtMonospaceFont()
        self.assertIsInstance(font, gui.QtGui.QFont)
        self.assertIn(
            font.styleHint(),
            (gui.QtGui.QFont.StyleHint.Monospace,
             gui.QtGui.QFont.StyleHint.TypeWriter))
        self.assertEqual(
            font.hintingPreference(),
            gui.QtGui.QFont.HintingPreference.PreferVerticalHinting)

    def test_run(self):
        # Test running an application, without starting an event loop
        import myokit.gui as gui

        # Only MyokitApplication subclasses can be run
        self.assertRaisesRegex(
            TypeError, 'MyokitApplication', gui.run, object)
        self.assertRaisesRegex(
            TypeError, 'MyokitApplication', gui.run,
            gui.QtWidgets.QMainWindow)

        # Run a minimal application with mocked QApplication and sys.exit
        created = []

        class App(gui.MyokitApplication):
            def __init__(self, title):
                super().__init__()
                self.setWindowTitle(title)
                created.append(self)

        qapp = unittest.mock.MagicMock()
        qapp.exec.return_value = 3
        with unittest.mock.patch.object(
                gui.QtWidgets, 'QApplication', return_value=qapp), \
                unittest.mock.patch('signal.signal') as sig, \
                unittest.mock.patch('sys.exit') as exit:
            gui.run(App, 'Hello')

        try:
            # App was created with the given arguments, and shown
            self.assertEqual(len(created), 1)
            self.assertEqual(created[0].windowTitle(), 'Hello')
            self.assertTrue(created[0].isVisible())

            # Event loop was started, and its return value passed to exit
            qapp.exec.assert_called_once_with()
            exit.assert_called_once_with(3)
            qapp.lastWindowClosed.connect.assert_called_once_with(qapp.quit)

            # A SIGINT handler was installed that closes all windows
            import signal
            sig.assert_called_once()
            signum, handler = sig.call_args[0]
            self.assertEqual(signum, signal.SIGINT)
            qapp.closeAllWindows.assert_not_called()
            handler(signal.SIGINT, None)
            qapp.closeAllWindows.assert_called_once_with()
        finally:
            for window in created:
                window.close()
                window.deleteLater()


if __name__ == '__main__':
    unittest.main()
