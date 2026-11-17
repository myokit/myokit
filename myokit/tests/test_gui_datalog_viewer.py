#!/usr/bin/env python3
#
# Tests the myokit.gui.datalog_viewer module.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import configparser
import os
import pathlib
import tempfile
import unittest
import unittest.mock
import warnings

import numpy as np

import myokit
from myokit.tests import DIR_DATA, DIR_FORMATS, qt_application

# Test data
ABF1 = os.path.join(DIR_FORMATS, 'abf-v1.abf')
ABF2 = os.path.join(DIR_FORMATS, 'abf-v2.abf')
PRO = os.path.join(DIR_FORMATS, 'abf-protocol.pro')
WCP = os.path.join(DIR_FORMATS, 'wcp-file.wcp')
WCP_EMPTY = os.path.join(DIR_FORMATS, 'wcp-file-empty.wcp')
CSV = os.path.join(DIR_DATA, 'io', 'datalog.csv')
ZIP = os.path.join(DIR_DATA, 'io', 'goodlog.zip')
BAD_ZIP = os.path.join(DIR_DATA, 'io', 'badlog-3-not-a-zip.zip')
BAD_CSV = os.path.join(DIR_DATA, 'io', 'datalog-17-non-float-data.csv')


class GuiDataLogViewerTest(unittest.TestCase):
    """ Tests the DataLog viewer. """

    @classmethod
    def setUpClass(cls):
        cls.app = qt_application()
        import myokit.gui.datalog_viewer
        cls.m = myokit.gui.datalog_viewer

    def setUp(self):
        # Redirect the settings file to a temporary directory
        self._tempdir = tempfile.TemporaryDirectory()
        self.temp = pathlib.Path(self._tempdir.name)
        self.settings = self.temp / 'DataLogViewer.ini'
        patcher = unittest.mock.patch.object(
            self.m, 'SETTINGS_FILE', self.settings)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self._tempdir.cleanup)

        # Catch any message boxes
        patcher = unittest.mock.patch.object(
            self.m.QtWidgets.QMessageBox, 'critical')
        self.critical = patcher.start()
        self.addCleanup(patcher.stop)

        self._widgets = []

    def tearDown(self):
        for w in self._widgets:
            w.close()
            w.deleteLater()
        self._widgets = []
        self.app.processEvents()

    def viewer(self, *filenames):
        """ Creates a viewer, which will be closed after the test. """
        v = self.m.DataLogViewer(*filenames)
        self._widgets.append(v)
        return v

    def widget(self, w):
        """ Registers a widget to be closed after the test. """
        self._widgets.append(w)
        return w

    def tab_names(self, tabs):
        """ Returns the names of the tabs in a tab widget. """
        return [tabs.tabText(i) for i in range(tabs.count())]

    def test_construction(self):
        # Test creating an empty viewer
        v = self.viewer()
        self.assertIn(self.m.TITLE, v.windowTitle())
        self.assertIn(myokit.__version__, v.windowTitle())
        self.assertEqual(v._tabs.count(), 0)
        self.assertEqual(v.statusBar().currentMessage(), 'Ready')
        self.assertTrue(v._tool_open.isEnabled())
        self.assertFalse(v._tool_close.isEnabled())
        self.assertFalse(v._tool_close_all.isEnabled())
        self.assertFalse(v._tool_next_file.isEnabled())
        self.assertFalse(v._tool_prev_file.isEnabled())
        self.assertFalse(v._tool_next_var.isEnabled())
        self.assertFalse(v._tool_prev_var.isEnabled())
        self.assertFalse(v._tool_first_var.isEnabled())
        self.assertFalse(v._tool_last_var.isEnabled())
        self.assertEqual(
            v._path, pathlib.Path(os.getcwd()).absolute())

        # All supported extensions have a loader
        for ext in ('.abf', '.atf', '.csv', '.dat', '.pro', '.txt', '.wcp',
                    '.zip'):
            self.assertIn(ext, v._load_actions)
        self.assertEqual('.mat' in v._load_actions, self.m.has_scipy)
        self.critical.assert_not_called()

        # Show and close
        v.show()
        self.assertTrue(v.isVisible())
        v.close()
        self.assertFalse(v.isVisible())

    def test_construction_with_files(self):
        # Test creating a viewer with a single file
        v = self.viewer(ABF1)
        self.assertEqual(v._tabs.count(), 1)
        self.assertEqual(v._tabs.currentIndex(), 0)
        self.assertTrue(v._tool_close.isEnabled())
        self.assertTrue(v._tool_close_all.isEnabled())
        self.assertFalse(v._tool_next_file.isEnabled())
        self.assertFalse(v._tool_prev_file.isEnabled())

        # Test creating a viewer with multiple files
        v = self.viewer(ABF1, CSV, ZIP)
        self.assertEqual(
            self.tab_names(v._tabs),
            ['abf-v1.abf', 'datalog.csv', 'goodlog.zip'])
        self.assertEqual(v._tabs.currentIndex(), 0)
        self.assertTrue(v._tool_close.isEnabled())
        self.assertTrue(v._tool_close_all.isEnabled())
        self.assertTrue(v._tool_next_file.isEnabled())
        self.assertTrue(v._tool_prev_file.isEnabled())
        self.critical.assert_not_called()

    def test_load_abf(self):
        # Test loading ABF files
        v = self.viewer()
        v.load_file(ABF1)
        self.critical.assert_not_called()
        self.assertEqual(v._tabs.count(), 1)
        self.assertEqual(v._tabs.tabText(0), 'abf-v1.abf')
        self.assertEqual(v._path, pathlib.Path(DIR_FORMATS).absolute())
        tab = v._tabs.widget(0)
        self.assertIsInstance(tab, self.m.AbfTab)
        self.assertIsInstance(tab, self.m.SweepSourceTab)

        # One A/D channel, one D/A channel, and meta data
        abf = myokit.formats.axon.AbfFile(ABF1)
        names = self.tab_names(tab)
        self.assertEqual(len(names), 3)
        self.assertEqual(names[0], f'A/D: {abf.channel_names(0)}')
        self.assertEqual(names[1], f'D/A: {abf.da_names(0)}')
        self.assertEqual(names[2], 'info')
        self.assertIsInstance(tab.widget(2), self.m.QtWidgets.QTextEdit)
        self.assertTrue(tab.widget(2).isReadOnly())
        self.assertEqual(tab.widget(2).toPlainText(), abf.meta_str(True))

        # Equal length sweeps: one line per sweep
        self.assertEqual(len(tab._figures), 2)
        self.assertEqual(len(tab._axes), 2)
        for axes in tab._axes:
            self.assertEqual(len(axes.get_lines()), abf.sweep_count())
            self.assertIn(abf.time_unit().__str__(), axes.get_xlabel())
        self.assertIn(abf.channel_names(0), tab._axes[0].get_ylabel())

        # Version 2 file
        v.load_file(ABF2)
        self.critical.assert_not_called()
        self.assertEqual(v._tabs.count(), 2)
        tab = v._tabs.widget(1)
        self.assertIsInstance(tab, self.m.AbfTab)
        abf = myokit.formats.axon.AbfFile(ABF2)
        self.assertEqual(len(tab._axes), 2)
        self.assertEqual(len(tab._axes[0].get_lines()), abf.sweep_count())

        # Protocol file: no A/D channels, only D/A
        v.load_file(PRO)
        self.critical.assert_not_called()
        self.assertEqual(v._tabs.count(), 3)
        self.assertEqual(v._tabs.tabText(2), 'abf-protocol.pro')
        tab = v._tabs.widget(2)
        names = self.tab_names(tab)
        self.assertTrue(names[0].startswith('D/A: '))
        self.assertFalse(any(x.startswith('A/D') for x in names))
        self.assertEqual(names[-1], 'info')

    def test_load_wcp(self):
        # Test loading WinWCP files
        v = self.viewer()
        v.load_file(WCP)
        self.critical.assert_not_called()
        self.assertEqual(v._tabs.count(), 1)
        tab = v._tabs.widget(0)
        self.assertIsInstance(tab, self.m.WcpTab)
        wcp = myokit.formats.wcp.WcpFile(WCP)
        n = wcp.channel_count()
        self.assertEqual(len(tab._axes), n + wcp.da_count())
        names = self.tab_names(tab)
        for i in range(n):
            self.assertEqual(names[i], f'A/D: {wcp.channel_names(i)}')
            self.assertEqual(
                len(tab._axes[i].get_lines()), wcp.sweep_count())

        # Empty file: no graphs
        v.load_file(WCP_EMPTY)
        self.critical.assert_not_called()
        self.assertEqual(v._tabs.count(), 2)
        tab = v._tabs.widget(1)
        self.assertIsInstance(tab, self.m.WcpTab)
        self.assertEqual(len(tab._figures), 0)
        self.assertTrue(all(
            x == 'info' for x in self.tab_names(tab)))

    def test_load_atf(self):
        # Test loading an ATF file
        t = np.linspace(0, 1, 101)
        log = myokit.DataLog(time='time')
        log['time'] = t
        log['a'] = np.sin(t)
        log['b'] = np.cos(t)
        path = self.temp / 'test.atf'
        myokit.formats.axon.save_atf(log, path)

        v = self.viewer()
        with warnings.catch_warnings():
            # No deprecated methods are used
            warnings.simplefilter('error')
            v.load_file(str(path))
        self.critical.assert_not_called()
        self.assertEqual(v._tabs.count(), 1)
        self.assertEqual(v._tabs.tabText(0), 'test.atf')
        self.assertEqual(v._path, self.temp.absolute())
        tab = v._tabs.widget(0)
        self.assertIsInstance(tab, self.m.AtfTab)
        self.assertEqual(self.tab_names(tab), ['a', 'b', 'Info'])
        self.assertFalse(hasattr(tab, '_atf'))
        self.assertEqual(len(tab._axes), 2)
        self.assertEqual(tab._axes[0].get_xlabel(), 'time')
        self.assertEqual(tab._axes[0].get_ylabel(), 'a')
        line = tab._axes[1].get_lines()[0]
        self.assertTrue(np.allclose(line.get_xdata(), t))
        self.assertTrue(np.allclose(line.get_ydata(), np.cos(t), atol=1e-6))
        info = tab.widget(2)
        self.assertTrue(info.isReadOnly())
        self.assertEqual(
            info.toPlainText(),
            myokit.formats.axon.AtfFile(path).meta_str())

    def test_load_datalog(self):
        # Test loading DataLogs from csv and zip files
        v = self.viewer()
        v.load_file(CSV)
        self.critical.assert_not_called()
        tab = v._tabs.widget(0)
        self.assertIsInstance(tab, self.m.CsvTab)
        self.assertEqual(v._tabs.tabText(0), 'datalog.csv')
        self.assertEqual(self.tab_names(tab), ['v'])
        log = myokit.DataLog.load_csv(CSV)
        line = tab._axes[0].get_lines()[0]
        self.assertTrue(np.all(line.get_xdata() == np.array(log['time'])))
        self.assertTrue(np.all(line.get_ydata() == np.array(log['v'])))
        self.assertEqual(tab._axes[0].get_xlabel(), 'time')
        self.assertEqual(tab._axes[0].get_ylabel(), 'v')

        # Upper case extensions also work
        path = self.temp / 'DATALOG.CSV'
        log.save_csv(path)
        v.load_file(path)
        self.critical.assert_not_called()
        self.assertEqual(v._tabs.count(), 2)
        self.assertIsInstance(v._tabs.widget(1), self.m.CsvTab)

        # Binary format
        v.load_file(ZIP)
        self.critical.assert_not_called()
        self.assertEqual(v._tabs.count(), 3)
        tab = v._tabs.widget(2)
        self.assertIsInstance(tab, self.m.CsvTab)
        self.assertEqual(self.tab_names(tab), ['membrane.V', 'ina.INa'])
        self.assertEqual(tab._axes[0].get_xlabel(), 'engine.time')

    def test_csv_tab(self):
        # Test the CsvTab with logs created in memory
        v = self.viewer()

        # Log without time key: index used as time
        log = myokit.DataLog()
        log['x'] = [1, 2, 3, 4]
        log['y'] = [4, 3, 2, 1]
        tab = self.widget(self.m.CsvTab(v, log, 'name'))
        self.assertEqual(self.tab_names(tab), ['x', 'y'])
        self.assertEqual(tab._axes[0].get_xlabel(), 'Index')
        line = tab._axes[1].get_lines()[0]
        self.assertEqual(list(line.get_xdata()), [0, 1, 2, 3])
        self.assertEqual(list(line.get_ydata()), [4, 3, 2, 1])

        # Multi-dimensional log: indexed variables grouped, meta data shown
        log = myokit.DataLog(time='t')
        log['t'] = [0, 1, 2]
        log['0.x'] = [1, 2, 3]
        log['1.x'] = [2, 3, 4]
        log['2.x'] = [3, 4, 5]
        log['y'] = [5, 5, 5]
        log.meta['author'] = 'Myokit'
        log.meta['note'] = 'test'
        tab = self.widget(self.m.CsvTab(v, log, 'name'))
        self.assertEqual(self.tab_names(tab), ['x', 'y', 'info'])
        self.assertEqual(len(tab._axes[0].get_lines()), 3)
        self.assertEqual(len(tab._axes[1].get_lines()), 1)
        ys = [list(x.get_ydata()) for x in tab._axes[0].get_lines()]
        self.assertEqual(ys, [[1, 2, 3], [2, 3, 4], [3, 4, 5]])
        info = tab.widget(2)
        self.assertTrue(info.isReadOnly())
        self.assertEqual(
            info.toPlainText(), 'author: Myokit\nnote: test')
        self.critical.assert_not_called()

        # Empty log: error raised
        log = myokit.DataLog()
        self.assertRaisesRegex(
            ValueError, 'no data', self.m.CsvTab, v, log, 'name')

        # Time key set but not usable: error raised
        log = myokit.DataLog(time='t')
        log['x'] = [1, 2, 3]
        self.assertRaisesRegex(
            ValueError, 'no time key', self.m.CsvTab, v, log, 'name')
        self.critical.assert_not_called()

        # Loading a log that can't be shown: error shown, no tab added
        path = self.temp / 'empty.csv'
        with open(path, 'w') as f:
            f.write('"time","x"\n')
        v.load_file(path)
        self.critical.assert_called_once()
        self.assertIn('no data', self.critical.call_args[0][2])
        self.assertEqual(v._tabs.count(), 0)
        self.assertNotEqual(v._path, self.temp.absolute())

    def test_load_txt(self):
        # Test loading text files
        v = self.viewer()

        # 1d data
        path = self.temp / 'one.txt'
        np.savetxt(path, np.array([1, 2, 3, 2, 1.]))
        v.load_file(path)
        self.critical.assert_not_called()
        self.assertEqual(v._tabs.count(), 1)
        tab = v._tabs.widget(0)
        self.assertIsInstance(tab, self.m.TxtTab)
        self.assertEqual(self.tab_names(tab), ['series 1'])
        line = tab._axes[0].get_lines()[0]
        self.assertEqual(list(line.get_ydata()), [1, 2, 3, 2, 1])

        # 2d data in columns: time and two series
        t = np.linspace(0, 1, 11)
        a, b = np.sin(t), np.cos(t)
        path = self.temp / 'columns.txt'
        np.savetxt(path, np.array([t, a, b]).T)
        v.load_file(path)
        self.critical.assert_not_called()
        self.assertEqual(v._tabs.count(), 2)
        tab = v._tabs.widget(1)
        self.assertEqual(self.tab_names(tab), ['series 1', 'series 2'])
        for axes, y in zip(tab._axes, (a, b)):
            lines = axes.get_lines()
            self.assertEqual(len(lines), 1)
            self.assertTrue(np.allclose(lines[0].get_xdata(), t))
            self.assertTrue(np.allclose(lines[0].get_ydata(), y))

        # 2d data in rows, time last
        path = self.temp / 'rows.txt'
        np.savetxt(path, np.array([b, t]))
        v.load_file(path)
        self.critical.assert_not_called()
        tab = v._tabs.widget(2)
        self.assertEqual(self.tab_names(tab), ['series 1'])
        line = tab._axes[0].get_lines()[0]
        self.assertTrue(np.allclose(line.get_xdata(), t))
        self.assertTrue(np.allclose(line.get_ydata(), b))

        # 2d data without a time series
        tab = self.widget(self.m.TxtTab(
            v, np.array([[3, 2, 1], [1, 3, 2], [2, 1, 3], [1, 1, 0]]), 'x'))
        self.assertEqual(
            self.tab_names(tab), ['series 1', 'series 2', 'series 3'])
        line = tab._axes[0].get_lines()[0]
        self.assertEqual(list(line.get_xdata()), [0, 1, 2, 3])
        self.assertEqual(list(line.get_ydata()), [3, 1, 2, 1])

        # Text tab created directly with 3d data: error raised
        self.assertRaisesRegex(
            ValueError, 'unable to parse',
            self.m.TxtTab, v, np.zeros((2, 3, 4)), 'x')
        self.critical.assert_not_called()

    def test_mat_tab(self):
        # Test the MatTab with data as returned by scipy.io.loadmat
        t = np.linspace(0, 1, 11)
        y = np.sin(t) + 2
        mat = {
            '__header__': b'Ignored',
            'one': y.reshape((1, 11)),                  # 1d data
            'rows': np.array([t, y]),                   # 2 x n
            'cols': np.array([t, y]).T,                 # n x 2
            'swapped': np.array([y[::-1], t]).T,        # time in 2nd column
            'bad': np.array([[3, 2, 1], [1, 3, 2]]),    # no increasing axis
            'square': np.eye(3),                        # unsupported shape
            'cube': np.zeros((2, 3, 4)),                # unsupported shape
            'empty': np.zeros((0, 0)),                  # no data
            'text': np.array(['abc']),                  # not numbers
        }
        v = self.viewer()
        tab = self.widget(self.m.MatTab(v, mat, 'test.mat'))
        self.critical.assert_not_called()
        names = self.tab_names(tab)
        self.assertEqual(names, ['one', 'rows', 'cols', 'swapped'])
        axes = dict(zip(names, tab._axes))
        line = axes['one'].get_lines()[0]
        self.assertTrue(np.allclose(line.get_xdata(), np.arange(11)))
        self.assertTrue(np.allclose(line.get_ydata(), y))
        for key in ('rows', 'cols'):
            line = axes[key].get_lines()[0]
            self.assertTrue(np.allclose(line.get_xdata(), t))
            self.assertTrue(np.allclose(line.get_ydata(), y))
        line = axes['swapped'].get_lines()[0]
        self.assertTrue(np.allclose(line.get_xdata(), t))
        self.assertTrue(np.allclose(line.get_ydata(), y[::-1]))
        self.assertEqual(axes['one'].get_ylabel(), 'one')

        # No usable data: error raised
        bad = {'bad': np.array([[3, 2, 1], [1, 3, 2]]), 'square': np.eye(3)}
        self.assertRaisesRegex(
            ValueError, 'no usable data', self.m.MatTab, v, bad, 'x.mat')
        self.critical.assert_not_called()

    def test_load_mat(self):
        # Test loading Matlab files
        v = self.viewer()
        path = self.temp / 'test.mat'
        if not self.m.has_scipy:
            # Without SciPy, mat files are not supported
            v.load_file(path)
            self.critical.assert_called_once()
            self.assertIn('.mat', self.critical.call_args[0][2])
            self.assertEqual(v._tabs.count(), 0)
            return

        import scipy.io
        t = np.linspace(0, 1, 11)
        scipy.io.savemat(
            path, {'x': np.array([t, t ** 2])})
        v.load_file(path)
        self.critical.assert_not_called()
        self.assertEqual(v._tabs.count(), 1)
        tab = v._tabs.widget(0)
        self.assertIsInstance(tab, self.m.MatTab)
        self.assertEqual(self.tab_names(tab), ['x'])

        # File without usable data: error shown, no tab added
        path = self.temp / 'bad.mat'
        scipy.io.savemat(path, {'x': np.eye(3)})
        v.load_file(path)
        self.critical.assert_called_once()
        self.assertIn('no usable data', self.critical.call_args[0][2])
        self.assertEqual(v._tabs.count(), 1)

    def test_load_dat(self):
        # Test loading PatchMaster files, using a mock file
        class Series:
            def __init__(self, name):
                self._name = name

            def label(self):
                return self._name

            def sweep_count(self):
                return 0

            def meta_str(self, verbose=False):
                return f'Series {self._name}'

        class Group(list):
            def label(self):
                return 'Group'

        group = Group([Series('a'), Series('b')])
        f = unittest.mock.MagicMock()
        f.__enter__.return_value = [group]
        v = self.viewer()
        with unittest.mock.patch(
                'myokit.formats.heka.PatchMasterFile', return_value=f) as p:
            v.load_file(self.temp / 'test.dat')
        p.assert_called_once()
        self.critical.assert_not_called()
        self.assertEqual(self.tab_names(v._tabs), ['Group a', 'Group b'])
        tab = v._tabs.widget(1)
        self.assertIsInstance(tab, self.m.PatchMasterTab)
        self.assertEqual(self.tab_names(tab), ['info'])
        self.assertEqual(tab.widget(0).toPlainText(), 'Series b')
        self.assertEqual(v._path, self.temp.absolute())

    def test_load_errors(self):
        # Test error handling when loading files
        v = self.viewer()
        path = v._path

        # Unknown extension
        v.load_file(self.temp / 'file.xyz')
        self.critical.assert_called_once()
        self.assertIn('.xyz', self.critical.call_args[0][2])
        self.critical.reset_mock()

        # Bad or missing files of each type
        garbage = b'This is not a valid file\n\x00\x01\x02'
        for ext in ('.abf', '.atf', '.mat', '.txt', '.wcp', '.dat'):
            p = self.temp / f'bad{ext}'
            with open(p, 'wb') as f:
                f.write(garbage)
            if ext == '.mat' and not self.m.has_scipy:
                continue
            with self.subTest(ext=ext):
                v.load_file(p)
                self.critical.assert_called_once()
                self.assertIn('Traceback', self.critical.call_args[0][2])
                self.critical.reset_mock()

        for p in (BAD_ZIP, BAD_CSV, self.temp / 'missing.csv'):
            with self.subTest(path=p):
                v.load_file(p)
                self.critical.assert_called_once()
                self.critical.reset_mock()

        # Nothing loaded, path unchanged
        self.assertEqual(v._tabs.count(), 0)
        self.assertEqual(v._path, path)

    def test_action_open(self):
        # Test opening files via the (mocked) file dialog
        v = self.viewer()
        dialog = 'myokit.gui.QtWidgets.QFileDialog.getOpenFileNames'

        # User cancels
        with unittest.mock.patch(dialog, return_value=([], '')) as d:
            v.action_open()
        d.assert_called_once()
        self.assertEqual(d.call_args[1]['filter'], self.m.FILTER_LIST)
        self.assertEqual(v._tabs.count(), 0)
        self.assertFalse(v._tool_close.isEnabled())

        # Open a single file
        with unittest.mock.patch(dialog, return_value=([CSV], '')):
            v.action_open()
        self.assertEqual(v._tabs.count(), 1)
        self.assertEqual(v._tabs.currentIndex(), 0)
        self.assertTrue(v._tool_close.isEnabled())
        self.assertTrue(v._tool_close_all.isEnabled())
        self.assertFalse(v._tool_next_file.isEnabled())

        # Open two more: first of new files is selected
        with unittest.mock.patch(dialog, return_value=([ZIP, ABF1], '')):
            v.action_open()
        self.assertEqual(v._tabs.count(), 3)
        self.assertEqual(v._tabs.currentIndex(), 1)
        self.assertTrue(v._tool_next_file.isEnabled())
        self.assertTrue(v._tool_prev_file.isEnabled())

        # Opening a bad file doesn't change the selection
        with unittest.mock.patch(dialog, return_value=([BAD_ZIP], '')):
            v.action_open()
        self.critical.assert_called_once()
        self.assertEqual(v._tabs.count(), 3)
        self.assertEqual(v._tabs.currentIndex(), 1)

    def test_close_tabs(self):
        # Test closing tabs and associated button states
        v = self.viewer(CSV, ZIP, ABF1)
        self.assertEqual(v._tabs.count(), 3)

        # Close a specific tab
        v.action_close(1)
        self.assertEqual(
            self.tab_names(v._tabs), ['datalog.csv', 'abf-v1.abf'])
        self.assertTrue(v._tool_next_file.isEnabled())

        # Close current tab
        v._tabs.setCurrentIndex(1)
        v.action_close_current()
        self.assertEqual(self.tab_names(v._tabs), ['datalog.csv'])
        self.assertFalse(v._tool_next_file.isEnabled())
        self.assertFalse(v._tool_prev_file.isEnabled())
        self.assertTrue(v._tool_close.isEnabled())
        self.assertTrue(v._tool_close_all.isEnabled())

        # Close last tab
        v.action_close_current()
        self.assertEqual(v._tabs.count(), 0)
        self.assertFalse(v._tool_close.isEnabled())
        self.assertFalse(v._tool_close_all.isEnabled())

        # Closing without tabs does nothing
        v.action_close_current()
        v.action_close_all()
        self.assertEqual(v._tabs.count(), 0)

        # Close via the tab bar's close request signal
        v.load_file(CSV)
        v._tabs.tabCloseRequested.emit(0)
        self.assertEqual(v._tabs.count(), 0)

        # Close all tabs
        v = self.viewer(CSV, ZIP, ABF1)
        tabs = [v._tabs.widget(i) for i in range(3)]
        v.action_close_all()
        self.assertEqual(v._tabs.count(), 0)
        self.assertFalse(v._tool_close.isEnabled())
        self.assertFalse(v._tool_close_all.isEnabled())
        self.assertFalse(v._tool_next_file.isEnabled())
        self.assertFalse(v._tool_prev_file.isEnabled())

        # Graph tabs have released their figures
        for tab in tabs:
            self.assertFalse(hasattr(tab, '_figures'))
            self.assertFalse(hasattr(tab, '_axes'))

    def test_file_navigation(self):
        # Test selecting next/previous files
        v = self.viewer(CSV, ZIP, ABF1)
        self.assertEqual(v._tabs.currentIndex(), 0)
        v.action_next_file()
        self.assertEqual(v._tabs.currentIndex(), 1)
        v.action_next_file()
        self.assertEqual(v._tabs.currentIndex(), 2)
        v.action_next_file()
        self.assertEqual(v._tabs.currentIndex(), 0)
        v.action_prev_file()
        self.assertEqual(v._tabs.currentIndex(), 2)
        v.action_prev_file()
        self.assertEqual(v._tabs.currentIndex(), 1)

        # Via the menu actions
        v._tool_next_file.trigger()
        self.assertEqual(v._tabs.currentIndex(), 2)
        v._tool_prev_file.trigger()
        self.assertEqual(v._tabs.currentIndex(), 1)

        # Single tab: next/previous does nothing
        v = self.viewer(CSV)
        v.action_next_file()
        self.assertEqual(v._tabs.currentIndex(), 0)
        v.action_prev_file()
        self.assertEqual(v._tabs.currentIndex(), 0)

        # Empty viewer: nothing happens
        v = self.viewer()
        v.action_next_file()
        v.action_prev_file()
        self.assertEqual(v._tabs.currentIndex(), -1)

    def test_variable_navigation(self):
        # Test selecting variables within a file
        v = self.viewer(ZIP, CSV)

        # First file has 2 variables: variable navigation enabled
        self.assertTrue(v._tool_next_var.isEnabled())
        self.assertTrue(v._tool_prev_var.isEnabled())
        self.assertTrue(v._tool_first_var.isEnabled())
        self.assertTrue(v._tool_last_var.isEnabled())

        tab = v._tabs.widget(0)
        self.assertEqual(tab.currentIndex(), 0)
        v.action_next_var()
        self.assertEqual(tab.currentIndex(), 1)
        v.action_next_var()
        self.assertEqual(tab.currentIndex(), 0)
        v.action_prev_var()
        self.assertEqual(tab.currentIndex(), 1)
        v.action_first_var()
        self.assertEqual(tab.currentIndex(), 0)
        v.action_last_var()
        self.assertEqual(tab.currentIndex(), 1)
        v._tool_prev_var.trigger()
        self.assertEqual(tab.currentIndex(), 0)

        # Second file has a single variable: navigation disabled
        v.action_next_file()
        self.assertEqual(v._tabs.widget(1).count(), 1)
        self.assertFalse(v._tool_next_var.isEnabled())
        self.assertFalse(v._tool_prev_var.isEnabled())
        self.assertFalse(v._tool_first_var.isEnabled())
        self.assertFalse(v._tool_last_var.isEnabled())

        # Switching back enables it again
        v.action_prev_file()
        self.assertTrue(v._tool_next_var.isEnabled())

        # Closing all tabs disables it
        v.action_close_all()
        self.assertFalse(v._tool_next_var.isEnabled())
        self.assertFalse(v._tool_last_var.isEnabled())

        # Variable actions without tabs do nothing
        v.action_next_var()
        v.action_prev_var()
        v.action_first_var()
        v.action_last_var()

    def test_menu(self):
        # Test that each action appears in the menu only once
        v = self.viewer()
        actions = [a for a in v._menu_view.actions() if not a.isSeparator()]
        self.assertEqual(len(actions), len(set(actions)))
        self.assertIn(v._tool_next_file, actions)
        self.assertIn(v._tool_prev_file, actions)

    def test_tab_widget(self):
        # Test the generic TabWidget
        tabs = self.widget(self.m.TabWidget())
        for i in range(3):
            tabs.addTab(self.m.QtWidgets.QWidget(), str(i))
        tabs.last()
        self.assertEqual(tabs.currentIndex(), 2)
        tabs.next()
        self.assertEqual(tabs.currentIndex(), 0)
        tabs.previous()
        self.assertEqual(tabs.currentIndex(), 2)
        tabs.first()
        self.assertEqual(tabs.currentIndex(), 0)

    def test_config(self):
        # Test saving and loading the configuration
        self.assertFalse(self.settings.exists())

        # Closing the viewer stores the configuration
        v = self.viewer()
        v._path = self.temp
        v.setGeometry(10, 20, 640, 480)
        v.close()
        self.assertTrue(self.settings.exists())
        config = configparser.RawConfigParser()
        config.read(self.settings)
        self.assertEqual(config.get('files', 'path'), str(self.temp))
        self.assertEqual(config.get('window', 'w'), '640')
        self.assertEqual(config.get('window', 'h'), '480')

        # New viewer picks up the stored path and size
        v = self.viewer()
        self.assertEqual(v._path, self.temp.absolute())
        self.assertEqual(v.geometry().width(), 640)
        self.assertEqual(v.geometry().height(), 480)

        # Loading a file updates the path
        v.load_file(CSV)
        v.save_config()
        config = configparser.RawConfigParser()
        config.read(self.settings)
        self.assertEqual(
            config.get('files', 'path'),
            str(pathlib.Path(CSV).absolute().parent))

        # Non-existent paths and missing options are ignored
        with open(self.settings, 'w') as f:
            f.write('[window]\nw = 500\n[files]\n')
            f.write(f'path = {self.temp / "does-not-exist"}\n')
        v = self.viewer()
        self.assertEqual(v._path, pathlib.Path(os.getcwd()).absolute())
        self.assertEqual(v.geometry().width(), 500)

        # Unparseable files are ignored
        with open(self.settings, 'w') as f:
            f.write('this is not\nan ini file\n')
        v = self.viewer()
        self.assertEqual(v._path, pathlib.Path(os.getcwd()).absolute())
        self.assertEqual(v.geometry().width(), 800)

        # Calling closeEvent without an event still saves
        os.remove(self.settings)
        v.closeEvent()
        self.assertTrue(self.settings.exists())

    def test_about(self):
        # Test the about dialog (mocked)
        v = self.viewer()
        with unittest.mock.patch(
                'myokit.gui.QtWidgets.QMessageBox.about') as about:
            v._tool_about.trigger()
        about.assert_called_once()
        self.assertEqual(about.call_args[0][1], self.m.TITLE)
        self.assertIn('DataLog viewer', about.call_args[0][2])


if __name__ == '__main__':
    unittest.main()
