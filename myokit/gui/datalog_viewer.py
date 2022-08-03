#
# Qt gui for viewing DataBlock2d data files.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

# Standard library imports
import gc
import os
import sys
import traceback

# Qt imports
from myokit.gui import QtWidgets, QtGui, QtCore, Qt

# Myokit
import myokit
import myokit.gui

# Myokit components
import myokit.formats.axon
import myokit.formats.wcp

# Matplotlib (must be imported _after_ gui has had chance to set backend)
import matplotlib
import matplotlib.figure
from myokit.gui import matplotlib_backend as backend

# NumPy
import numpy as np

# ConfigParser in Python 2 and 3
try:
    import ConfigParser as configparser
except ImportError:
    import configparser


# Application title
TITLE = 'Myokit DataLog Viewer (PROTOTYPE)'

# Application icon
# def icon():
#    icons = [
#        'icon-datalog-viewer.ico',
#        'icon-datalog-viewer-16.xpm',
#        'icon-datalog-viewer-24.xpm',
#        'icon-datalog-viewer-32.xpm',
#        'icon-datalog-viewer-48.xpm',
#        'icon-datalog-viewer-64.xpm',
#        'icon-datalog-viewer-96.xpm',
#        'icon-datalog-viewer-128.xpm',
#        'icon-datalog-viewer-256.xpm',
#        ]
#    icon = QtGui.QIcon()
#    for i in icons:
#        icon.addFile(os.path.join(myokit.DIR_DATA, 'gui', i))
#    return icon

# Settings file
SETTINGS_FILE = os.path.join(myokit.DIR_USER, 'DataLogViewer.ini')
# Number of recent files to display
# N_RECENT_FILES = 5

# About
ABOUT = '<h1>' + TITLE + '</h1>' + """
<p>
    The DataLog viewer is a PROTOTYPE utility to examine time series data.
    At the moment, exclusively WinWCP, ABF and CSV files.
</p>
<p>
    System info:
    <br />Python: PYTHON
    <br />Using the BACKEND GUI backend.
</p>
""".replace('BACKEND', myokit.gui.backend).replace('PYTHON', sys.version)

# License
LICENSE = myokit.LICENSE_HTML

# File filters
FILTER_ABF = 'ABF files (*.abf *.pro)'
FILTER_ATF = 'ATF files (*.atf)'
FILTER_CSV = 'CSV files (*.csv)'
FILTER_MAT = 'MAT files (*.mat)'
FILTER_TXT = 'TXT files (*.txt)'
FILTER_WCP = 'WCP files (*.wcp)'
FILTER_ZIP = 'Zipped DataLog files (*.zip)'
FILTER_ANY = 'All files (*.*)'
FILTER_ALL = 'Data files (*.abf *.csv *.mat *.pro *.txt *.wcp *.zip)'
FILTER_LIST = ';;'.join([
    FILTER_ALL,
    FILTER_ABF,
    FILTER_CSV,
    FILTER_MAT,
    FILTER_TXT,
    FILTER_WCP,
    FILTER_ZIP,
    FILTER_ANY,
])


class DataLogViewer(myokit.gui.MyokitApplication):
    """
    Graphical interface for viewing DataLog data.
    """
    def __init__(self, *filenames):
        super(DataLogViewer, self).__init__()
        # Set Title, icon
        self.setWindowTitle(TITLE + ' ' + myokit.__version__)
        # Set size, center
        self.resize(800, 600)
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
        # Add widget for Abf file tabs
        self._tabs = QtWidgets.QTabWidget()
        self._tabs.setTabsClosable(True)
        self._tabs.tabCloseRequested.connect(self.action_close)
        self.setCentralWidget(self._tabs)
        # Menu bar
        self.create_menu()
        # Tool bar
        self.create_toolbar()
        # Status bar
        self.statusBar().showMessage('Ready')
        # Current path
        self._path = QtCore.QDir.currentPath()
        # Load settings from ini file
        self.load_config()
        # Load any selected files
        for filename in filenames:
            self.load_file(filename)

    def action_about(self):
        """
        Displays the about dialog.
        """
        QtWidgets.QMessageBox.about(self, TITLE, ABOUT)

    def action_close(self, index):
        """
        Called when a tab should be closed
        """
        tab = self._tabs.widget(index)
        self._tabs.removeTab(index)
        if tab is not None:
            tab.deleteLater()
        gc.collect()
        del tab

    def action_license(self):
        """
        Displays this program's licensing information.
        """
        QtWidgets.QMessageBox.about(self, TITLE, LICENSE)

    def action_open(self):
        """
        Let the user select and open a file.
        """
        filenames = QtWidgets.QFileDialog.getOpenFileNames(
            self, 'Open data file', self._path, filter=FILTER_LIST)[0]
        if filenames:
            # Save current number of tabs
            tab_count = self._tabs.count()
            # Load files
            for filename in filenames:
                self.load_file(str(filename))
            # If loading went ok, show first of newly loaded files
            if self._tabs.count() > tab_count:
                self._tabs.setCurrentIndex(tab_count)

    def closeEvent(self, event=None):
        """
        Called when window is closed. To force a close (and trigger this
        function, call self.close())
        """
        # Save configuration
        self.save_config()
        if event:
            # Accept the event, close the window
            event.accept()
            # Ignore the event, window stays open
            #event.ignore()

    def create_menu(self):
        """
        Creates this widget's menu.
        """
        self._menu = self.menuBar()
        # File menu
        self._menu_file = self._menu.addMenu('&File')
        # File > Open
        self._tool_open = QtWidgets.QAction('&Open', self)
        self._tool_open.setShortcut('Ctrl+O')
        self._tool_open.setStatusTip('Open a file')
        self._tool_open.setIcon(QtGui.QIcon.fromTheme('document-open'))
        self._tool_open.triggered.connect(self.action_open)
        self._menu_file.addAction(self._tool_open)
        # File > ----
        self._menu_file.addSeparator()
        # File > Quit
        self._tool_exit = QtWidgets.QAction('&Quit', self)
        self._tool_exit.setShortcut('Ctrl+Q')
        self._tool_exit.setStatusTip('Exit application.')
        self._tool_exit.setIcon(QtGui.QIcon.fromTheme('application-exit'))
        self._tool_exit.triggered.connect(self.close)
        self._menu_file.addAction(self._tool_exit)
        # Help menu
        self._menu_help = self._menu.addMenu('&Help')
        # Help > About
        self._tool_about = QtWidgets.QAction('&About', self)
        self._tool_about.setStatusTip('View information about this program.')
        self._tool_about.triggered.connect(self.action_about)
        self._menu_help.addAction(self._tool_about)
        # Help > License
        self._tool_license = QtWidgets.QAction('&License', self)
        self._tool_license.setStatusTip('View this program\'s license info.')
        self._tool_license.triggered.connect(self.action_license)
        self._menu_help.addAction(self._tool_license)

    def create_toolbar(self):
        """
        Creates this widget's toolbar
        """
        self._toolbar = self.addToolBar('tools')
        self._toolbar.setFloatable(False)
        self._toolbar.setMovable(False)
        self._toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self._toolbar.addAction(self._tool_open)
        #self._toolbar.addSeparator()

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

        # Window dimensions and location
        if config.has_section('window'):
            g = self.geometry()

            def getor(name, alt):
                if config.has_option('window', name):
                    return int(config.get('window', name))
                return alt

            x = getor('x', g.x())
            y = getor('y', g.y())
            w = getor('w', g.width())
            h = getor('h', g.height())
            self.setGeometry(x, y, w, h)

        # Current files, directory, etc
        if config.has_section('files'):
            if config.has_option('files', 'path'):
                path = config.get('files', 'path')
                if os.path.isdir(path):
                    self._path = path

    def load_file(self, filename):
        """
        Loads a data file.
        """
        root, ext = os.path.splitext(os.path.basename(filename))
        actions = {
            '.abf': self.load_abf_file,
            '.atf': self.load_atf_file,
            '.csv': self.load_datalog,
            '.mat': self.load_mat_file,
            '.pro': self.load_abf_file,
            '.txt': self.load_txt_file,
            '.wcp': self.load_wcp_file,
            '.zip': self.load_datalog,
        }
        try:
            action = actions[ext.lower()]
        except KeyError:
            QtWidgets.QMessageBox.critical(
                self, TITLE, 'File format not recognized: ' + ext)
            return
        action(filename)

    def load_abf_file(self, filename):
        """
        Loads an abf file.
        """
        try:
            abf = myokit.formats.axon.AbfFile(filename)
        except Exception:
            e = traceback.format_exc()
            QtWidgets.QMessageBox.critical(self, TITLE, e)
            return
        self._path = os.path.dirname(filename)
        self._tabs.addTab(AbfTab(self, abf), os.path.basename(filename))

    def load_atf_file(self, filename):
        """
        Loads an ATF file.
        """
        try:
            atf = myokit.formats.axon.AtfFile(filename)
        except Exception:
            e = traceback.format_exc()
            QtWidgets.QMessageBox.critical(self, TITLE, e)
            return
        self._path = os.path.dirname(filename)
        self._tabs.addTab(AtfTab(self, atf), os.path.basename(filename))

    def load_datalog(self, filename):
        """
        Loads a DataLog from csv or zip file.
        """
        try:
            if filename[-4:].lower() == '.csv':
                log = myokit.DataLog.load_csv(filename)
            else:
                log = myokit.DataLog.load(filename)
            if log.time_key is None:
                raise Exception('Log must contain a suitable time variable.')
        except Exception:
            e = traceback.format_exc()
            QtWidgets.QMessageBox.critical(self, TITLE, e)
            return
        self._path = os.path.dirname(filename)
        name = os.path.basename(filename)
        self._tabs.addTab(CsvTab(self, log, name), name)

    def load_mat_file(self, filename):
        """
        Loads a Matlab file.

        This method requires ``SciPy`` to be installed.
        """
        try:
            from scipy.io import loadmat
            mat = loadmat(filename)
        except Exception:
            e = traceback.format_exc()
            QtWidgets.QMessageBox.critical(self, TITLE, e)
            return
        self._path = os.path.dirname(filename)
        name = os.path.basename(filename)
        self._tabs.addTab(MatTab(self, mat, name), name)

    def load_txt_file(self, filename):
        """
        Loads a csv file.
        """
        try:
            data = np.loadtxt(filename)
        except Exception:
            e = traceback.format_exc()
            QtWidgets.QMessageBox.critical(self, TITLE, e)
            return
        self._path = os.path.dirname(filename)
        name = os.path.basename(filename)
        self._tabs.addTab(TxtTab(self, data, name), name)

    def load_wcp_file(self, filename):
        """
        Loads a wcp file.
        """
        try:
            wcp = myokit.formats.wcp.WcpFile(filename)
        except Exception:
            e = traceback.format_exc()
            QtWidgets.QMessageBox.critical(self, TITLE, e)
            return
        self._path = os.path.dirname(filename)
        self._tabs.addTab(WcpTab(self, wcp), os.path.basename(filename))

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

        # Current files, directory, etc
        config.add_section('files')
        config.set('files', 'path', self._path)

        # Write configuration to ini file
        inifile = os.path.expanduser(SETTINGS_FILE)
        with open(inifile, 'w') as configfile:
            config.write(configfile)

    def show(self):
        """
        Shows this viewer.
        """
        super(DataLogViewer, self).show()
        QtWidgets.QApplication.processEvents()


class AbfTab(QtWidgets.QTabWidget):
    """
    A widget displaying an ABF file.
    """
    def __init__(self, parent, abf):
        super(AbfTab, self).__init__(parent)
        self.setTabsClosable(False)
        self.setTabPosition(self.East)
        self._abf = abf
        self._figures = []
        self._axes = []
        for i in range(self._abf.data_channels()):
            tab, name = self.create_graph_tab(i)
            self.addTab(tab, name)
        for i in range(self._abf.protocol_channels()):
            tab, name = self.create_protocol_tab(i)
            self.addTab(tab, name)
        self.addTab(self.create_info_tab(), 'Info')
        del self._abf

    def create_graph_tab(self, channel):
        """
        Creates a widget displaying the main data.
        """
        widget = QtWidgets.QWidget(self)
        # Create figure
        figure = matplotlib.figure.Figure()
        figure.suptitle(self._abf.filename())
        canvas = backend.FigureCanvasQTAgg(figure)
        canvas.setParent(widget)
        axes = figure.add_subplot(1, 1, 1)
        toolbar = backend.NavigationToolbar2QT(canvas, widget)
        # Draw lines
        name = 'AD(' + str(channel) + ')'   # Default if no data is present
        times = None
        for i, sweep in enumerate(self._abf):
            if times is None:
                name = 'AD' + str(sweep[channel].number()) + ': ' \
                    + sweep[channel].name()
                times = sweep[channel].times()
            axes.plot(times, sweep[channel].values())
        # Create a layout
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(canvas)
        vbox.addWidget(toolbar)
        widget.setLayout(vbox)
        self._figures.append(figure)
        self._axes.append(axes)
        return widget, name

    def create_protocol_tab(self, channel):
        """
        Creates a widget displaying a stored D/A signal.
        """
        widget = QtWidgets.QWidget(self)
        # Create figure
        figure = matplotlib.figure.Figure()
        figure.suptitle(self._abf.filename())
        canvas = backend.FigureCanvasQTAgg(figure)
        canvas.setParent(widget)
        axes = figure.add_subplot(1, 1, 1)
        toolbar = backend.NavigationToolbar2QT(canvas, widget)
        # Draw lines
        name = 'DA(' + str(channel) + ')'   # Default if no data is present
        times = None
        for i, sweep in enumerate(self._abf.protocol()):
            if times is None:
                name = 'DA' + str(sweep[channel].number()) + ': ' \
                    + sweep[channel].name()
                times = sweep[channel].times()
            axes.plot(times, sweep[channel].values())
        # Create a layout
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(canvas)
        vbox.addWidget(toolbar)
        widget.setLayout(vbox)
        self._figures.append(figure)
        self._axes.append(axes)
        return widget, name

    def create_info_tab(self):
        """
        Creates a tab displaying information about the file.
        """
        widget = QtWidgets.QTextEdit(self)
        widget.setText(self._abf.info(show_header=True))
        widget.setReadOnly(True)
        return widget

    def deleteLater(self):
        """
        Deletes this tab (later).
        """
        for figure in self._figures:
            figure.clear()
        for axes in self._axes:
            axes.cla()
        del self._figures, self._axes
        gc.collect()
        super(AbfTab, self).deleteLater()


class AtfTab(QtWidgets.QTabWidget):
    """
    A widget displaying an AGF file.
    """
    def __init__(self, parent, atf):
        super(AtfTab, self).__init__(parent)
        self._atf = atf

        self.setTabsClosable(False)
        self.setTabPosition(self.East)

        self._figures = []
        self._axes = []
        keys = list(self._atf.keys())
        if len(keys) > 1:
            time = keys[0]  # Time is always first (and regularly sampled)
            for key in keys[1:]:
                self.addTab(self.create_graph_tab(time, key), key)
        self.addTab(self.create_info_tab(), 'Info')
        del self._atf

    def create_graph_tab(self, time, key):
        """
        Creates a widget displaying a graph.
        """
        widget = QtWidgets.QWidget(self)

        # Create figure
        figure = matplotlib.figure.Figure()
        figure.suptitle(self._atf.filename())
        canvas = backend.FigureCanvasQTAgg(figure)
        canvas.setParent(widget)
        axes = figure.add_subplot(1, 1, 1)
        toolbar = backend.NavigationToolbar2QT(canvas, widget)

        # Draw lines
        axes.plot(self._atf[time], self._atf[key])

        # Create a layout
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(canvas)
        vbox.addWidget(toolbar)
        widget.setLayout(vbox)
        self._figures.append(figure)
        self._axes.append(axes)

        # Return widget
        return widget

    def create_info_tab(self):
        """
        Creates a tab displaying information about the file.
        """
        widget = QtWidgets.QTextEdit(self)
        widget.setText(self._atf.info())
        widget.setReadOnly(True)
        return widget

    def deleteLater(self):
        """
        Deletes this tab (later).
        """
        for figure in self._figures:
            figure.clear()
        for axes in self._axes:
            axes.cla()
        del self._figures, self._axes
        gc.collect()
        super(AtfTab, self).deleteLater()


class CsvTab(QtWidgets.QTabWidget):
    """
    A widget displaying a CSV file.

    The given log must have a time variable set.
    """
    def __init__(self, parent, log, filename):
        super(CsvTab, self).__init__(parent)
        self.setTabsClosable(False)
        self.setTabPosition(self.East)
        self._log = log.npview()
        self._filename = filename
        self._figures = []
        self._axes = []

        # Check time key was found
        time = log.time_key()
        try:
            self._time = log.time()
        except myokit.InvalidDataLogError:
            if time is None:
                QtWidgets.QMessageBox.critical(
                    self, TITLE,
                    'Unable to load file: no time key set in this log.')
                return
            else:
                raise

        # Check that time series aren't empty
        if log.length() == 0:
            QtWidgets.QMessageBox.critical(
                self, TITLE, 'Unable to load file: no data found.')
            return

        # Add tab for each column
        for k, v in log.items():
            if k == time:
                continue
            self.addTab(self.create_graph_tab(k, v), k)

    def create_graph_tab(self, key, data):
        """
        Creates a widget displaying the ``data`` stored under ``key``.
        """
        widget = QtWidgets.QWidget(self)
        # Create figure
        figure = matplotlib.figure.Figure()
        figure.suptitle(self._filename)
        canvas = backend.FigureCanvasQTAgg(figure)
        canvas.setParent(widget)
        axes = figure.add_subplot(1, 1, 1)
        axes.set_title(key)
        toolbar = backend.NavigationToolbar2QT(canvas, widget)
        # Draw lines
        axes.plot(self._time, data)
        # Create a layout
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(canvas)
        vbox.addWidget(toolbar)
        widget.setLayout(vbox)
        self._figures.append(figure)
        self._axes.append(axes)
        return widget

    def deleteLater(self):
        """
        Deletes this tab (later).
        """
        for figure in self._figures:
            figure.clear()
        for axes in self._axes:
            axes.cla()
        del self._figures, self._axes
        gc.collect()
        super(CsvTab, self).deleteLater()


class MatTab(QtWidgets.QTabWidget):
    """
    A widget displaying a MAT file.
    """
    def __init__(self, parent, mat, filename):
        super(MatTab, self).__init__(parent)
        self.setTabsClosable(False)
        self.setTabPosition(self.East)
        self._figures = []
        self._filename = filename
        self._axes = []

        # Find usable data
        for key in mat.keys():
            if key[:1] == '_':
                continue
            time, data = None, None
            data = mat[key]
            if np.prod(data.shape) == np.max(data.shape):
                # 1d data
                time = None
                data = data.reshape((np.max(data.shape),))
            elif len(data.shape) == 2 and (
                    np.prod(data.shape) == 2 * np.max(data.shape)):
                # 2d data: Only allow len(shape) == 2, otherwise too many cases
                if data.shape[0] == 2:
                    time = data[0]
                    data = data[1]
                else:
                    time = data[:, 0]
                    data = data[:, 1]
                # Check time is increasing
                if np.any(time[1:] < time[:-1]):
                    time, data = data, time
                if np.any(time[1:] < time[:-1]):
                    time, data = None, None
            if data is None:
                continue
            # Create tab
            tab = self.create_graph_tab(time, data)
            self.addTab(tab, key)

        # Nothing that can be used? Show error
        if len(self._figures) == 0:
            QtWidgets.QMessageBox.critical(
                self, TITLE,
                'Unable to load file: no usable data found.')
            return

    def create_graph_tab(self, time, data):
        """
        Creates a widget displaying a time series.
        """
        widget = QtWidgets.QWidget(self)
        # Create figure
        figure = matplotlib.figure.Figure()
        figure.suptitle(self._filename)
        canvas = backend.FigureCanvasQTAgg(figure)
        canvas.setParent(widget)
        axes = figure.add_subplot(1, 1, 1)
        toolbar = backend.NavigationToolbar2QT(canvas, widget)
        # Draw line
        if time is None:
            axes.plot(data)
        else:
            axes.plot(time, data)
        # Create a layout
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(canvas)
        vbox.addWidget(toolbar)
        widget.setLayout(vbox)
        self._figures.append(figure)
        self._axes.append(axes)
        return widget

    def deleteLater(self):
        """
        Deletes this tab (later).
        """
        for figure in self._figures:
            figure.clear()
        for axes in self._axes:
            axes.cla()
        del self._figures, self._axes
        gc.collect()
        super(MatTab, self).deleteLater()


class TxtTab(QtWidgets.QTabWidget):
    """
    A widget displaying a TXT file (with lots of heuristics!).
    """
    def __init__(self, parent, data, filename):
        super(TxtTab, self).__init__(parent)
        self.setTabsClosable(False)
        self.setTabPosition(self.East)
        self._figures = []
        self._filename = filename
        self._axes = []

        # Find usable data
        if np.prod(data.shape) == np.max(data.shape):
            # 1d data
            data = data.reshape((np.max(data.shape),))
            # Create tab
            tab = self.create_graph_tab(None, data)
            self.addTab(tab, 'series 1')
        elif len(data.shape) == 2:
            # 2d data, assume longest axis is time
            if data.shape[0] < data.shape[1]:
                data = data.T
            # Check if first or last entry could be time
            if not np.any(data[0, 1:] < data[0, :-1]):
                time = data[0]
                data = data[1:]
            elif not np.any(data[-1, 1:] < data[-1, :-1]):
                time = data[-1]
                data = data[:-1]
            else:
                time = None
            # Create tabs
            for k, column in enumerate(data):
                tab = self.create_graph_tab(time, data)
                self.addTab(tab, 'series ' + str(1 + k))
        else:
            # Nothing that can be used? Show error
            QtWidgets.QMessageBox.critical(
                self, TITLE,
                'Unable to load file: unable to parse file contents.')
            return

    def create_graph_tab(self, time, data):
        """
        Creates a widget displaying a time series.
        """
        widget = QtWidgets.QWidget(self)
        # Create figure
        figure = matplotlib.figure.Figure()
        figure.suptitle(self._filename)
        canvas = backend.FigureCanvasQTAgg(figure)
        canvas.setParent(widget)
        axes = figure.add_subplot(1, 1, 1)
        toolbar = backend.NavigationToolbar2QT(canvas, widget)
        # Draw line
        if time is None:
            axes.plot(data)
        else:
            axes.plot(time, data)
        # Create a layout
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(canvas)
        vbox.addWidget(toolbar)
        widget.setLayout(vbox)
        self._figures.append(figure)
        self._axes.append(axes)
        return widget

    def deleteLater(self):
        """
        Deletes this tab (later).
        """
        for figure in self._figures:
            figure.clear()
        for axes in self._axes:
            axes.cla()
        del self._figures, self._axes
        gc.collect()
        super(TxtTab, self).deleteLater()


class WcpTab(QtWidgets.QTabWidget):
    """
    A widget displaying a WCP file.
    """
    def __init__(self, parent, wcp):
        super(WcpTab, self).__init__(parent)
        self.setTabsClosable(False)
        self.setTabPosition(self.East)
        self._wcp = wcp
        self._figures = []
        self._axes = []
        for i in range(self._wcp.records()):
            self.addTab(self.create_graph_tab(i), 'Record ' + str(i))
        del self._wcp

    def create_graph_tab(self, record):
        """
        Creates a widget displaying the data in record i
        """
        widget = QtWidgets.QWidget(self)
        # Create figure
        figure = matplotlib.figure.Figure()
        figure.suptitle(self._wcp.filename())
        canvas = backend.FigureCanvasQTAgg(figure)
        canvas.setParent(widget)
        axes = figure.add_subplot(1, 1, 1)
        toolbar = backend.NavigationToolbar2QT(canvas, widget)
        # Draw lines
        for i in range(self._wcp.channels()):
            axes.plot(
                np.array(self._wcp.times(), copy=True),
                np.array(self._wcp.values(record, i), copy=True),
            )
        # Create a layout
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(canvas)
        vbox.addWidget(toolbar)
        widget.setLayout(vbox)
        self._figures.append(figure)
        self._axes.append(axes)
        return widget

    def deleteLater(self):
        """
        Deletes this tab (later).
        """
        for figure in self._figures:
            figure.clear()
        for axes in self._axes:
            axes.cla()
        del self._figures, self._axes
        gc.collect()
        super(WcpTab, self).deleteLater()

