#
# This hidden module contains the GUI elements used throughout Myokit.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import os
import platform
import signal
import sys

import myokit

# Detect platform
platform = platform.system()

# Select Qt library to use
pyqt5 = False
pyqt6 = False
pyside2 = False
pyside6 = False

# Allow overriding automatic selection
if myokit.FORCE_PYQT6:
    pyqt6 = True
if myokit.FORCE_PYQT5:
    pyqt5 = True
elif myokit.FORCE_PYSIDE6:
    pyside6 = True
elif myokit.FORCE_PYSIDE2:
    pyside2 = True
else:
    # Automatic selection
    try:
        import PyQt6  # noqa
        pyqt6 = True
    except ImportError:
        try:
            import PySide6  # noqa
            pyside6 = True
        except ImportError:
            try:
                import PyQt5  # noqa
                pyqt5 = True
            except ImportError:
                try:
                    import PySide2  # noqa
                    pyside2 = True
                except ImportError:
                    raise ImportError(
                        'Unable to find PyQt6, PyQt5, PySide6, or PySide2.')


# Import and configure Qt
if pyqt6:
    from PyQt6 import QtGui, QtWidgets, QtCore
    from PyQt6.QtCore import Qt

    # Use PySide signal names
    QtCore.Signal = QtCore.pyqtSignal
    QtCore.Slot = QtCore.pyqtSlot
    QtCore.Property = QtCore.pyqtProperty

    # Set backend variables
    backend = 'PyQt6'
    qtversion = 6

elif pyqt5:
    from PyQt5 import QtGui, QtWidgets, QtCore
    from PyQt5.QtCore import Qt

    # Mimic PyQt6 API changes
    # https://doc.qt.io/qt-6/widgets-changes-qt6.html
    QtGui.QAction = QtWidgets.QAction
    QtWidgets.QApplication.exec = QtWidgets.QApplication.exec_

    # Use PySide signal names
    QtCore.Signal = QtCore.pyqtSignal
    QtCore.Slot = QtCore.pyqtSlot
    QtCore.Property = QtCore.pyqtProperty

    # Set backend variables
    backend = 'PyQt5'
    qtversion = 5

elif pyside6:
    from PySide6 import QtGui, QtWidgets, QtCore
    from PySide6.QtCore import Qt

    # Mimic PyQt6 API changes
    QtWidgets.QApplication.exec = QtWidgets.QApplication.exec_

    # Set backend variables
    backend = 'PySide6'
    qtversion = 6

elif pyside2:
    from PySide2 import QtGui, QtWidgets, QtCore
    from PySide2.QtCore import Qt

    # Mimic PyQt6 API changes
    QtGui.QAction = QtWidgets.QAction
    QtWidgets.QApplication.exec = QtWidgets.QApplication.exec_

    # Set backend variables
    backend = 'PySide2'
    qtversion = 5

else:
    raise Exception('Selection of qt version failed.')


# Configure Matplotlib for use with Qt
import matplotlib  # noqa
try:
    matplotlib.use('QtAgg')
except ImportError:
    # In matplotlib 3.7.0 this raises ImportErrors if a previous backend
    # was already set.
    pass
try:
    # New Matplotlib no longer has qt4agg/qt5agg, but now uses qtagg for all
    import matplotlib.backends.back_qtagg as matplotlib_backend  # noqa
except ImportError:
    # https://matplotlib.org/stable/api/backend_qt_api.html
    import matplotlib.backends.backend_qt5agg as matplotlib_backend  # noqa

# Delete temporary variables
del pyqt5, pyqt6, pyside2, pyside6


# Load Gnome theme on Wayland (for icons)
if platform == 'Linux':
    icon = QtGui.QIcon.fromTheme('document-new')
    if icon.isNull():
        QtGui.QIcon.setThemeName('gnome')

# Icons with fallback for apple and windows
ICON_PATH = os.path.join(myokit.DIR_DATA, 'gui')
ICONS = {
    'document-new': 'new.png',
    'document-open': 'open.png',
    'document-save': 'save.png',
    'edit-undo': 'undo.png',
    'edit-redo': 'redo.png',
    'edit-find': 'find.png',
    'media-playback-start': 'run.png',
}
for k, v in ICONS.items():
    ICONS[k] = os.path.join(ICON_PATH, v)

# Toolbar style suitable for platform
TOOL_BUTTON_STYLE = Qt.ToolButtonStyle.ToolButtonTextUnderIcon
if platform == 'Windows':   # pragma: no linux cover
    TOOL_BUTTON_STYLE = Qt.ToolButtonStyle.ToolButtonIconOnly
elif platform == 'Darwin':  # pragma: no linux cover
    TOOL_BUTTON_STYLE = Qt.ToolButtonStyle.ToolButtonTextOnly


# Stand alone applications
class MyokitApplication(QtWidgets.QMainWindow):
    """
    Base class for Myokit applications.

    *Extends*: ``QtWidgets.QMainWindow``.
    """


def icon(name):
    """
    Returns a QtIcon created either from the theme or from one of the fallback
    icons.

    Raises a ``KeyError`` if no such icon is available.
    """
    return QtGui.QIcon.fromTheme(name, QtGui.QIcon(ICONS[name]))


def qtMonospaceFont():
    """
    Attempts to create and return a monospace font.
    """
    font = QtGui.QFont('monospace')
    if platform == 'Windows':   # pragma: no linux cover
        font.setStyleHint(QtGui.QFont.StyleHint.TypeWriter)
    else:
        font.setStyleHint(QtGui.QFont.StyleHint.Monospace)
    font.setHintingPreference(
        QtGui.QFont.HintingPreference.PreferVerticalHinting)
    return font


def run(app, *args):
    """
    Runs a Myokit gui app as a stand-alone application.

    Arguments:

    ``app``
        The application to run, specified as a class object (not an instance).
    ``*args``
        Any arguments to pass to the app's constructor.

    Example usage:

        load(myokit.gui.MyokitIDE, 'model.mmt')


    """
    # Test application class
    if not issubclass(app, MyokitApplication):
        raise ValueError(
            'Application must be specified as a type extending'
            ' MyokitApplication.')

    # Create Qt app
    a = QtWidgets.QApplication([])

    # Apply custom styling if required
    #_style_application(a)
    # Close with last window
    a.lastWindowClosed.connect(a.quit)

    # Close on Ctrl-C
    def int_signal(signum, frame):
        a.closeAllWindows()
    signal.signal(signal.SIGINT, int_signal)

    # Create app and show
    app = app(*args)
    app.show()

    # For some reason, Qt needs focus to handle the SIGINT catching...
    timer = QtCore.QTimer()
    timer.start(500)  # Flags timeout every 500ms
    timer.timeout.connect(lambda: None)

    # Wait for app to exit
    sys.exit(a.exec())

