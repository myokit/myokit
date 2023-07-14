#
# Qt gui for viewing DataBlock2d data files.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import configparser
import gc
import os
import sys
import traceback

from myokit.gui import QtWidgets, QtGui, QtCore, Qt

import myokit
import myokit.gui
import myokit.gui.progress
import myokit.formats.axon
import myokit.formats.wcp

# Matplotlib (must be imported _after_ gui has had chance to set backend)
import matplotlib
import matplotlib.figure
from myokit.gui import matplotlib_backend as backend

# NumPy
import numpy as np

# SciPy: Only used to load matlab files.
try:
    import scipy.io
    has_scipy = True
except ImportError:
    has_scipy = False


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
FILTER_MAT = 'Matlab files (*.mat)'
FILTER_DAT = 'PatchMaster files (*.dat)'
FILTER_TXT = 'Text files (*.txt)'
FILTER_WCP = 'WCP files (*.wcp)'
FILTER_ZIP = 'Zipped DataLog files (*.zip)'
FILTER_ANY = 'All files (*.*)'
FILTER_ALL = 'Data files (*.abf *.csv *.dat *.mat *.pro *.txt *.wcp *.zip)'
FILTER_LIST = ';;'.join([
    FILTER_ALL,
    FILTER_ABF,
    FILTER_CSV,
    FILTER_DAT,
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
        super().__init__()

        # Set Title, icon
        self.setWindowTitle(TITLE + ' ' + myokit.__version__)

        # Set size, center
        self.resize(800, 600)
        qr = self.frameGeometry()
        cp = QtGui.QGuiApplication.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        # Add widget for file tabs
        self._tabs = TabWidget()
        self._tabs.setTabsClosable(True)
        self._tabs.tabCloseRequested.connect(self.action_close)
        self._tabs.currentChanged.connect(self.fileTabChangeEvent)
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

        # File-loading methods
        self._load_actions = {
            '.abf': self.load_abf_file,
            '.atf': self.load_atf_file,
            '.csv': self.load_datalog,
            '.dat': self.load_dat_file,
            '.pro': self.load_abf_file,
            '.txt': self.load_txt_file,
            '.wcp': self.load_wcp_file,
            '.zip': self.load_datalog,
        }
        if has_scipy:
            self._load_actions['.mat'] = self.load_mat_file

        # Load any selected files
        for filename in filenames:
            self.load_file(filename)
        tc = self._tabs.count()
        if tc > 0:
            if tc > 1:
                self._tool_next_file.setEnabled(True)
                self._tool_prev_file.setEnabled(True)
            self._tabs.setCurrentIndex(0)

    def action_about(self):
        """
        Displays the about dialog.
        """
        QtWidgets.QMessageBox.about(self, TITLE, ABOUT)

    def action_close(self, index):
        """
        Called when a tab should be closed
        """
        # Remove tab
        tab = self._tabs.widget(index)
        self._tabs.removeTab(index)

        # Update buttons
        if self._tabs.count() < 2:
            self._tool_next_file.setEnabled(False)
            self._tool_prev_file.setEnabled(False)

        # Delete tab
        if tab is not None:
            tab.deleteLater()
        gc.collect()
        del tab

    def action_first_var(self):
        """ Select the first variable in the current file. """
        tab = self._tabs.currentWidget()
        if tab:
            tab.first()

    def action_last_var(self):
        """ Select the last variable in the current file. """
        tab = self._tabs.currentWidget()
        if tab:
            tab.last()

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
            tab_count_new = self._tabs.count()
            if tab_count_new > tab_count:
                self._tabs.setCurrentIndex(tab_count)

                # Enable next/previous file menu items
                if tab_count_new > 1:
                    self._tool_next_file.setEnabled(True)
                    self._tool_prev_file.setEnabled(True)

    def action_next_file(self):
        """
        Select the next open file.
        """
        self._tabs.next()

    def action_next_var(self):
        """
        Select the next variable in the selected file.
        """
        tab = self._tabs.currentWidget()
        if tab:
            tab.next()

    def action_prev_file(self):
        """
        Select the previous open file.
        """
        self._tabs.previous()

    def action_prev_var(self):
        """
        Select the previous variable in the selected file
        """
        tab = self._tabs.currentWidget()
        if tab:
            tab.previous()

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
        self._tool_open = QtGui.QAction('&Open', self)
        self._tool_open.setShortcut('Ctrl+O')
        self._tool_open.setStatusTip('Open a file')
        self._tool_open.setIcon(QtGui.QIcon.fromTheme('document-open'))
        self._tool_open.triggered.connect(self.action_open)
        self._menu_file.addAction(self._tool_open)
        # File > ----
        self._menu_file.addSeparator()
        # File > Quit
        self._tool_exit = QtGui.QAction('&Quit', self)
        self._tool_exit.setShortcut('Ctrl+Q')
        self._tool_exit.setStatusTip('Exit application.')
        self._tool_exit.setIcon(QtGui.QIcon.fromTheme('application-exit'))
        self._tool_exit.triggered.connect(self.close)
        self._menu_file.addAction(self._tool_exit)
        # View menu
        self._menu_view = self._menu.addMenu('&View')
        # View > Next file
        self._tool_next_file = QtGui.QAction('Next file', self)
        self._tool_next_file.setShortcut('Ctrl+PgDown')
        self._tool_next_file.setStatusTip('Select the next open file')
        self._tool_next_file.triggered.connect(self.action_next_file)
        self._tool_next_file.setEnabled(False)
        self._menu_view.addAction(self._tool_next_file)
        # View > Previous file
        self._menu_view.addAction(self._tool_next_file)
        self._tool_prev_file = QtGui.QAction('Previous file', self)
        self._tool_prev_file.setShortcut('Ctrl+PgUp')
        self._tool_prev_file.setStatusTip('Select the previous open file')
        self._tool_prev_file.triggered.connect(self.action_prev_file)
        self._tool_prev_file.setEnabled(False)
        self._menu_view.addAction(self._tool_prev_file)
        # View > ----
        self._menu_view.addSeparator()
        # View > Next variable
        self._tool_next_var = QtGui.QAction('Next variable', self)
        self._tool_next_var.setShortcut('PgDown')
        self._tool_next_var.setStatusTip('Show the next variable')
        self._tool_next_var.triggered.connect(self.action_next_var)
        self._tool_next_var.setEnabled(False)
        self._menu_view.addAction(self._tool_next_var)
        # View > Previous var
        self._tool_prev_var = QtGui.QAction('Previous variable', self)
        self._tool_prev_var.setShortcut('PgUp')
        self._tool_prev_var.setStatusTip('Show the previous variable')
        self._tool_prev_var.triggered.connect(self.action_prev_var)
        self._tool_prev_var.setEnabled(False)
        self._menu_view.addAction(self._tool_prev_var)
        # View > First variable
        self._tool_first_var = QtGui.QAction('First variable', self)
        self._tool_first_var.setShortcut('Home')
        self._tool_first_var.setStatusTip('Show the first variable')
        self._tool_first_var.triggered.connect(self.action_first_var)
        self._tool_first_var.setEnabled(False)
        self._menu_view.addAction(self._tool_first_var)
        # View > Last var
        self._tool_last_var = QtGui.QAction('Last variable', self)
        self._tool_last_var.setShortcut('End')
        self._tool_last_var.setStatusTip('Show the last variable')
        self._tool_last_var.triggered.connect(self.action_last_var)
        self._tool_last_var.setEnabled(False)
        self._menu_view.addAction(self._tool_last_var)
        # Help menu
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
        Creates this widget's toolbar
        """
        self._toolbar = self.addToolBar('tools')
        self._toolbar.setFloatable(False)
        self._toolbar.setMovable(False)
        self._toolbar.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
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
        try:
            action = self._load_actions[ext.lower()]
        except KeyError:
            QtWidgets.QMessageBox.critical(
                self, TITLE, 'File format not recognized: ' + ext)
            return
        action(filename)

    def load_abf_file(self, filename):
        """ Loads an ABF file. """
        try:
            abf = myokit.formats.axon.AbfFile(filename)
        except Exception:
            e = traceback.format_exc()
            QtWidgets.QMessageBox.critical(self, TITLE, e)
            return
        self._path = os.path.dirname(filename)
        self._tabs.addTab(AbfTab(self, abf), os.path.basename(filename))

    def load_atf_file(self, filename):
        """ Loads an ATF file. """
        try:
            atf = myokit.formats.axon.AtfFile(filename)
        except Exception:
            e = traceback.format_exc()
            QtWidgets.QMessageBox.critical(self, TITLE, e)
            return
        self._path = os.path.dirname(filename)
        self._tabs.addTab(AtfTab(self, atf), os.path.basename(filename))

    def load_dat_file(self, filename):
        """ Loads a PatchMaster dat file. """

        pbar = myokit.gui.progress.ProgressBar(
            self, 'Loading groups and series')
        pbar.show()
        reporter = pbar.reporter()
        reporter.enter()

        flag = QtCore.QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents
        QtWidgets.QApplication.processEvents(flag)

        try:
            with myokit.formats.heka.PatchMasterFile(filename) as f:
                n = sum([len(list(g.complete_series())) for g in f])
                i = 0
                stop = False
                for group in f:
                    for series in group.complete_series():
                        self._tabs.addTab(
                            PatchMasterTab(self, series),
                            f'{group.label()} {series.label()}')
                        i += 1
                        if not reporter.update(i / n):
                            stop = True
                            break
                        QtWidgets.QApplication.processEvents(flag)
                    if stop:
                        break
                self._path = os.path.dirname(filename)
        except Exception:
            e = traceback.format_exc()
            QtWidgets.QMessageBox.critical(self, TITLE, e)
            return
        finally:
            reporter.exit()
            pbar.close()
            pbar.deleteLater()

    def load_datalog(self, filename):
        """ Loads a DataLog from csv or zip file. """
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
            mat = scipy.io.loadmat(filename)
        except Exception:
            e = traceback.format_exc()
            QtWidgets.QMessageBox.critical(self, TITLE, e)
            return
        self._path = os.path.dirname(filename)
        name = os.path.basename(filename)
        self._tabs.addTab(MatTab(self, mat, name), name)

    def load_txt_file(self, filename):
        """ Loads a text file. """
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
        """ Loads a WinWCP file. """
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
        super().show()
        QtWidgets.QApplication.processEvents()

    def fileTabChangeEvent(self, index):
        """
        Different file tab selected.
        """
        if index >= 0:
            tab = self._tabs.widget(index)
            if tab.count() > 1:
                self._tool_first_var.setEnabled(True)
                self._tool_last_var.setEnabled(True)
                self._tool_next_var.setEnabled(True)
                self._tool_prev_var.setEnabled(True)
                return
        self._tool_first_var.setEnabled(False)
        self._tool_last_var.setEnabled(False)
        self._tool_prev_var.setEnabled(False)
        self._tool_next_var.setEnabled(False)


class TabWidget(QtWidgets.QTabWidget):
    """ Generic tab widget with first/last next/previous methods. """

    def first(self):
        """ Select the first widget. """
        self.setCurrentIndex(0)

    def last(self):
        """ Select the last widget. """
        self.setCurrentIndex(self.count() - 1)

    def next(self):
        """ Select the next widget. """
        n = self.count()
        if n < 2:
            return
        i = self.currentIndex() + 1
        self.setCurrentIndex(0 if i >= n else i)

    def previous(self):
        """ Select the previous widget. """
        n = self.count()
        if n < 2:
            return
        i = self.currentIndex() - 1
        self.setCurrentIndex(n - 1 if i < 0 else i)


class GraphTabWidget(TabWidget):
    """ Tab widget to graph a data source. """

    def __init__(self, parent):
        super().__init__(parent)

        self.setTabsClosable(False)
        self.setTabPosition(self.TabPosition.East)

        self._figures = []
        self._axes = []

    def deleteLater(self):
        """ Deletes this tab (later). """
        for figure in self._figures:
            figure.clear()
        for axes in self._axes:
            axes.cla()
        del self._figures, self._axes
        gc.collect()
        super().deleteLater()


class SweepSourceTab(GraphTabWidget):
    """ A tab widget for sources implementing the SweepSource interface. """

    def __init__(self, parent, source):
        super().__init__(parent)

        # Add A/D
        for i in range(source.channel_count()):
            self._add_graph_tab(source, i)

        # Add D/A
        for i in range(source.da_count()):
            self._add_graph_tab(source, i, True)

        # Add meta data
        self._add_meta_tab(source)

    def _add_graph_tab(self, source, index, da=False):
        """ Adds a tab for a graph. """

        # Create widget
        widget = QtWidgets.QWidget(self)

        # Create figure
        figure = matplotlib.figure.Figure()
        canvas = backend.FigureCanvasQTAgg(figure)
        canvas.setParent(widget)
        toolbar = backend.NavigationToolbar2QT(canvas, widget)

        # Draw signal
        join_sweeps = not source.equal_length_sweeps()
        if da:
            name = source.da_names(index)
            units = source.da_units(index)
            times, values = source.da(index, join_sweeps)
        else:
            name = source.channel_names(index)
            units = source.channel_units(index)
            times, values = source.channel(index, join_sweeps)

        axes = figure.add_subplot(1, 1, 1)
        axes.set_xlabel(f'Time {source.time_unit()}')
        axes.set_ylabel(f'{name} {units}')
        if join_sweeps:
            axes.plot(times, values)
        else:
            for v in values:
                axes.plot(times[0], v)

        # Store for later deletion
        self._figures.append(figure)
        self._axes.append(axes)

        # Create a layout
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(canvas)
        vbox.addWidget(toolbar)
        widget.setLayout(vbox)

        # Add tab
        self.addTab(widget, name)

    '''
    def debug_tab(self, channel_index, da=True):
        """ Add a tab graphing data using the DataLog method. """
        widget = QtWidgets.QWidget(self)

        # Create widget
        widget = QtWidgets.QWidget(self)

        # Create figure
        figure = matplotlib.figure.Figure()
        figure.suptitle(self._abf.filename())
        canvas = backend.FigureCanvasQTAgg(figure)
        canvas.setParent(widget)
        toolbar = backend.NavigationToolbar2QT(canvas, widget)

        # Draw lines
        p = self._abf.da_protocol(channel_index, tu='s', vu='V')
        times, _ = self._abf.da(channel_index)
        for t in times:
            d = p.log_for_interval(t[0], t[-1], for_drawing=True).npview()
            axes.plot(d['time'] - t[0], d['pace'])

        # Create a layout
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(canvas)
        vbox.addWidget(toolbar)
        widget.setLayout(vbox)

        # Add tab
        self.addTab(widget, name)
'''

    def _add_meta_tab(self, source):

        meta = source.meta_str(True)
        if meta:
            widget = QtWidgets.QTextEdit(self)
            widget.setText(meta)
            widget.setReadOnly(True)
            self.addTab(widget, 'info')


class AbfTab(SweepSourceTab):
    """ A widget displaying an ABF file. """
    pass


class AtfTab(GraphTabWidget):
    """ A widget displaying an ATF file. """
    def __init__(self, parent, atf):
        super().__init__(parent)
        self._atf = atf

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
        """ Creates a tab displaying information about the file. """
        widget = QtWidgets.QTextEdit(self)
        widget.setText(self._atf.info())
        widget.setReadOnly(True)
        return widget


class CsvTab(GraphTabWidget):
    """
    A widget displaying a CSV file.

    The given log must have a time variable set.
    """
    def __init__(self, parent, log, filename):
        super().__init__(parent)

        self._log = log.npview()
        self._filename = filename

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

        # Overlapping sweeps or neighboring cells?
        keys = []
        groups = {}
        for key in log.keys():
            if key == time:
                continue
            index, var = myokit.split_key(key)
            if index:
                group = groups.get(var, None)
                if group is None:
                    groups[var] = [index]
                    keys.append(var)
                else:
                    group.append(index)
            else:
                keys.append(var)

        # Add tab for each column
        for k in keys:
            self.addTab(self.create_graph_tab(k, groups.get(k)), k)

    def create_graph_tab(self, key, indices=None):
        """ Creates a widget displaying the data stored under ``key``. """
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
        if indices is None:
            axes.plot(self._time, self._log[key])
        else:
            for i in indices:
                axes.plot(self._time, self._log[i + key])

        # Create a layout
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(canvas)
        vbox.addWidget(toolbar)
        widget.setLayout(vbox)
        self._figures.append(figure)
        self._axes.append(axes)
        return widget


class MatTab(GraphTabWidget):
    """ A widget displaying a .mat file. """
    def __init__(self, parent, mat, filename):
        super().__init__(parent)

        self._filename = filename

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


class PatchMasterTab(SweepSourceTab):
    """ A widget displaying a PatchMaster series. """
    pass


class TxtTab(GraphTabWidget):
    """ A widget displaying a .txt file (with lots of heuristics!). """

    def __init__(self, parent, data, filename):
        super().__init__(parent)

        self._filename = filename

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


class WcpTab(SweepSourceTab):
    pass

