#!/usr/bin/env python3
#
# Tests the myokit.gui.datablock_viewer module.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import configparser
import pathlib
import tempfile
import unittest
import unittest.mock as mock

import numpy as np

import myokit
from myokit.tests import DIR_IO, qt_application


class GuiDataBlockViewerTest(unittest.TestCase):
    """
    Tests the ``DataBlockViewer`` and its helper classes.
    """

    @classmethod
    def setUpClass(cls):
        cls.app = qt_application()
        import myokit.gui.datablock_viewer
        cls.dv = myokit.gui.datablock_viewer
        cls.QtCore = myokit.gui.QtCore
        cls.QtGui = myokit.gui.QtGui
        cls.QtWidgets = myokit.gui.QtWidgets
        cls.Qt = myokit.gui.Qt
        cls.block_path = DIR_IO / 'block2d.zip'

    def setUp(self):
        # Temporary directory, used for settings and all exported files
        self._tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tempdir.cleanup)
        self.temp = pathlib.Path(self._tempdir.name)

        # Never read or write the user's settings file
        self.settings = self.temp / 'DataBlockViewer.ini'
        patcher = mock.patch.object(self.dv, 'SETTINGS_FILE', self.settings)
        patcher.start()
        self.addCleanup(patcher.stop)

        # Never show modal message boxes
        mb = self.QtWidgets.QMessageBox
        for name in ('warning', 'about'):
            patcher = mock.patch.object(mb, name)
            setattr(self, 'mock_' + name, patcher.start())
            self.addCleanup(patcher.stop)

    def viewer(self, filename=None):
        """ Creates a viewer that gets closed and deleted after the test. """
        v = self.dv.DataBlockViewer(filename)

        def close():
            v._timer.stop()
            v._resize_timer.stop()
            v.close()
            v.deleteLater()
            self.QtCore.QCoreApplication.sendPostedEvents(
                None, self.QtCore.QEvent.Type.DeferredDelete)

        self.addCleanup(close)
        return v

    def loaded_viewer(self):
        """ Creates a viewer with ``block2d.zip`` loaded. """
        v = self.viewer()
        v.load_data_file(self.block_path)
        self.assertIsNotNone(v._data)
        return v

    def small_block(self, nt=4, ny=2, nx=3):
        """ Creates a small block with two 2d variables. """
        time = np.arange(nt, dtype=float)
        b = myokit.DataBlock2d(nx, ny, time)
        a = np.arange(nt * ny * nx, dtype=float).reshape((nt, ny, nx))
        b.set2d('membrane.V', a)
        b.set2d('ica.ICa', -a)
        b.set0d('engine.pace', np.zeros(nt))
        return b

    def save_dialog(self, path):
        """ Patches ``QFileDialog.getSaveFileName`` to return ``path``. """
        return mock.patch.object(
            self.QtWidgets.QFileDialog, 'getSaveFileName',
            return_value=(str(path), ''))

    def warning_text(self):
        """ Returns the text of the last warning message box. """
        self.assertTrue(self.mock_warning.called)
        return self.mock_warning.call_args[0][2]

    def test_icon(self):
        # Test the application icon is created
        self.assertFalse(self.dv.icon().isNull())

    def test_construction(self):
        # Test the state of a new viewer, without data
        v = self.viewer()
        self.assertEqual(
            v.windowTitle(),
            f'{self.dv.TITLE} {myokit.__version__}')
        self.assertIsNone(v._data)
        self.assertIsNone(v._file)
        self.assertEqual(v._recent_files, [])
        self.assertEqual(v._frame_field.text(), '0')
        self.assertEqual(v._rate_field.text(), '50')
        self.assertEqual(v._timer.interval(), 50)
        self.assertEqual(v._variable_select.count(), 0)
        self.assertEqual(
            v._colormap_select.count(), len(list(myokit.ColorMap.names())))
        self.assertEqual(v._colormap_select.currentText(), v._colormap)
        self.assertEqual(v.statusBar().currentMessage(), 'Ready')
        for tool in v._recent_file_tools:
            self.assertFalse(tool.isVisible())
        self.assertEqual(
            v._colormap_lower_field.text(), '(Auto)')
        self.assertIsNone(v._colormap_lower_field.value())

        # Non-existent file is ignored
        v = self.viewer(self.temp / 'does-not-exist.zip')
        self.assertIsNone(v._data)
        self.assertFalse(self.mock_warning.called)

    def test_construction_with_file(self):
        # Test a file passed to the constructor is loaded
        v = self.viewer(self.block_path)
        self.assertIsNotNone(v._data)
        self.assertEqual(v._file, self.block_path.absolute())

    def test_load_data_file(self):
        # Test loading a DataBlock2d file
        v = self.viewer()
        v.load_data_file(str(self.block_path))
        path = self.block_path.absolute()
        self.assertEqual(
            v.statusBar().currentMessage(), 'File loaded successfully.')
        self.assertEqual(v._file, path)
        self.assertEqual(v._path, path.parent)
        self.assertTrue(v.windowTitle().startswith('block2d.zip - '))
        self.assertEqual(v._data.shape(), (500, 16, 16))

        # Variable selected
        self.assertEqual(v._variable, 'membrane.V')
        self.assertEqual(v._variable_select.count(), 1)
        self.assertEqual(v._variable_select.currentText(), 'membrane.V')

        # Video frames created, first frame shown
        self.assertEqual(len(v._video_frames), 500)
        self.assertEqual(v._video_iframe, 0)
        self.assertEqual(v._frame_field.text(), '0')
        # Note: the time field truncates to its maximum length (6)
        self.assertEqual(v._time_field.text(), str(v._data.time()[0])[:6])
        self.assertEqual(v._video_pixmap.width(), 16)
        self.assertEqual(v._video_pixmap.height(), 16)
        self.assertEqual(v._colorbar_pixmap.width(), v._colorbar_width)
        self.assertEqual(v._colorbar_pixmap.height(), v._colorbar_height)

        # Slider updated
        self.assertEqual(v._slider.minimum(), 0)
        self.assertEqual(v._slider.maximum(), 499)
        self.assertEqual(v._slider.pageStep(), 25)

        # Recent files updated
        self.assertEqual(v._recent_files, [path])
        tool = v._recent_file_tools[0]
        self.assertTrue(tool.isVisible())
        self.assertEqual(tool.text(), '1. block2d.zip')
        self.assertEqual(tool.data(), path)
        self.assertFalse(v._recent_file_tools[1].isVisible())

        # Graph area has data
        self.assertIs(v._graph_area._data, v._data)

        # Timer not running after load
        self.assertFalse(v._timer.isActive())

    def test_load_1d_block(self):
        # Test a DataBlock1d file is loaded as a 2d block
        b = myokit.DataBlock1d(5, np.arange(3, dtype=float))
        b.set1d('membrane.V', np.arange(15, dtype=float).reshape((3, 5)))
        path = self.temp / 'block1d.zip'
        b.save(path)
        v = self.viewer()
        v.load_data_file(path)
        self.assertEqual(v._data.shape(), (3, 1, 5))
        self.assertEqual(v._variable, 'membrane.V')

    def test_load_variable_preference(self):
        # Test membrane.V is selected, even if it is not the first variable
        b = myokit.DataBlock2d(2, 2, [0, 1])
        b.set2d('a.a', np.zeros((2, 2, 2)))
        b.set2d('membrane.v', np.ones((2, 2, 2)))
        b.set2d('z.z', np.ones((2, 2, 2)))
        v = self.viewer()
        with mock.patch('myokit.DataBlock2d.load', return_value=b):
            v.load_data_file(self.temp / 'x.zip')
        self.assertEqual(v._variable, 'membrane.v')
        self.assertEqual(v._variable_select.count(), 3)

        # Without membrane.V, the first variable is used
        b = myokit.DataBlock2d(2, 2, [0, 1])
        b.set2d('b.b', np.zeros((2, 2, 2)))
        b.set2d('c.c', np.zeros((2, 2, 2)))
        with mock.patch('myokit.DataBlock2d.load', return_value=b):
            v.load_data_file(self.temp / 'x.zip')
        self.assertEqual(v._variable, 'b.b')

        # Variable list is replaced
        self.assertEqual(v._variable_select.count(), 2)

    def test_load_bad_files(self):
        # Test loading files that can't be read as a DataBlock2d
        v = self.viewer()
        for name in ('bad2d-2-no-header.zip', 'bad2d-4-not-a-zip.zip',
                     'goodlog.zip'):
            self.mock_warning.reset_mock()
            v.load_data_file(DIR_IO / name)
            self.assertIn('Unable to read file', self.warning_text())
            self.assertEqual(v.statusBar().currentMessage(), 'Load failed.')
            self.assertIsNone(v._data)
            self.assertIsNone(v._file)
            self.assertEqual(v._recent_files, [])

        # A failed load doesn't affect previously loaded data
        v.load_data_file(self.block_path)
        data = v._data
        v.load_data_file(DIR_IO / 'bad2d-2-no-header.zip')
        self.assertIs(v._data, data)
        self.assertEqual(v._file, self.block_path.absolute())

    def test_load_unexpected_exception(self):
        # Test unexpected errors are shown with a traceback
        v = self.viewer()
        with mock.patch(
                'myokit.DataBlock2d.load', side_effect=RuntimeError('Oops')):
            v.load_data_file(self.block_path)
        text = self.warning_text()
        self.assertIn('An error has occurred', text)
        self.assertIn('RuntimeError: Oops', text)
        self.assertEqual(v.statusBar().currentMessage(), 'Load failed.')
        self.assertIsNone(v._data)

    def test_load_empty_file(self):
        # Test loading a block without 2d data
        b = myokit.DataBlock2d(2, 2, [0, 1])
        b.set0d('engine.pace', [0, 0])
        v = self.viewer()
        with mock.patch('myokit.DataBlock2d.load', return_value=b):
            v.load_data_file(self.temp / 'empty.zip')
        self.assertIn('does not contain any 2d data', self.warning_text())
        self.assertEqual(
            v.statusBar().currentMessage(), 'Load failed: empty file.')
        self.assertIsNone(v._data)

    def test_load_canceled(self):
        # Test canceling the progress dialog while loading
        real = myokit.DataBlock2d.load
        v = self.viewer()

        def cancel_and_load(path, progress=None):
            # Cancel, then use the real method, which checks the reporter
            progress._pd.cancel()
            return real(path, progress=progress)

        with mock.patch(
                'myokit.DataBlock2d.load', side_effect=cancel_and_load):
            v.load_data_file(self.block_path)
        self.assertEqual(v.statusBar().currentMessage(), 'Load canceled.')
        self.assertIsNone(v._data)
        self.assertFalse(self.mock_warning.called)

        # Uncaught exceptions are not swallowed when canceled
        def cancel_and_interrupt(path, progress=None):
            progress._pd.cancel()
            raise KeyboardInterrupt

        with mock.patch(
                'myokit.DataBlock2d.load', side_effect=cancel_and_interrupt):
            self.assertRaises(
                KeyboardInterrupt, v.load_data_file, self.block_path)
        self.assertEqual(v.statusBar().currentMessage(), 'Load canceled.')
        self.assertIsNone(v._data)

    def test_load_progress_reporter(self):
        # Test progress updates are passed to the progress dialog
        values = []

        def load(path, progress=None):
            progress.enter('Loading')
            values.append(progress.update(0.5))
            progress.exit()
            return self.small_block()

        v = self.viewer()
        with mock.patch('myokit.DataBlock2d.load', side_effect=load):
            v.load_data_file(self.temp / 'x.zip')
        self.assertEqual(values, [True])
        self.assertEqual(v._data.shape(), (4, 2, 3))

    def test_action_open(self):
        # Test opening a file with a (mocked) file dialog
        v = self.viewer()
        fd = self.QtWidgets.QFileDialog
        with mock.patch.object(
                fd, 'getOpenFileName', return_value=('', '')) as m:
            v.action_open()
        self.assertTrue(m.called)
        self.assertIsNone(v._data)

        v._timer.start()
        with mock.patch.object(
                fd, 'getOpenFileName',
                return_value=(str(self.block_path), '')):
            v._tool_open.trigger()
        self.assertEqual(v._file, self.block_path.absolute())
        self.assertFalse(v._timer.isActive())

    def test_recent_files(self):
        # Test the recent files list and menu
        v = self.viewer()
        b = self.small_block()
        paths = []
        for i in range(self.dv.N_RECENT_FILES + 2):
            path = self.temp / f'block-{i}.zip'
            b.save(path)
            paths.append(path.absolute())
            v.load_data_file(path)
        n = self.dv.N_RECENT_FILES
        self.assertEqual(v._recent_files, paths[::-1][:n])
        for k, tool in enumerate(v._recent_file_tools):
            self.assertTrue(tool.isVisible())
            self.assertEqual(tool.data(), v._recent_files[k])

        # Reloading moves file to the front, without duplicates
        v.load_data_file(paths[-3])
        self.assertEqual(v._recent_files[0], paths[-3])
        self.assertEqual(len(v._recent_files), n)
        self.assertEqual(len(set(v._recent_files)), n)

        # Open a recent file via the menu action
        tool = v._recent_file_tools[2]
        target = tool.data()
        tool.trigger()
        self.assertEqual(v._file, target)
        self.assertEqual(v._recent_files[0], target)
        self.assertFalse(self.mock_warning.called)

        # Recent file that no longer exists
        tool = v._recent_file_tools[1]
        missing = tool.data()
        missing.unlink()
        tool.trigger()
        self.assertIn('no longer exists', self.warning_text())
        self.assertEqual(v._file, target)

        # Called without a sender: nothing happens
        v.action_recent_file()

    def test_frame_navigation(self):
        # Test moving between frames
        v = self.loaded_viewer()
        time = v._data.time()
        frame0 = v._video_pixmap.toImage()

        v.action_set_frame(10)
        self.assertEqual(v._video_iframe, 10)
        self.assertEqual(v._frame_field.text(), '10')
        self.assertEqual(v._time_field.text(), str(time[10])[:6])
        self.assertEqual(v._slider.value(), 10)
        self.assertEqual(v._graph_area._position, time[10])
        self.assertNotEqual(v._video_pixmap.toImage(), frame0)

        v.action_next_frame()
        self.assertEqual(v._video_iframe, 11)
        self.assertEqual(v._frame_field.text(), '11')

        # Slider changes frame
        v._slider.setValue(100)
        self.assertEqual(v._video_iframe, 100)
        self.assertEqual(v._time_field.text(), str(time[100])[:6])

        # Out of range wraps to 0
        v.action_set_frame(499)
        self.assertEqual(v._video_iframe, 499)
        v.action_next_frame()
        self.assertEqual(v._video_iframe, 0)
        self.assertEqual(v._slider.value(), 0)
        self.assertEqual(v._video_pixmap.toImage(), frame0)
        v.action_set_frame(5)
        v.action_set_frame(-1)
        self.assertEqual(v._video_iframe, 0)

        # Timer advances frames
        v._timer.timeout.emit()
        self.assertEqual(v._video_iframe, 1)

    def test_timer(self):
        # Test starting, stopping, and pausing playback
        v = self.viewer()

        # Without data, timer can't be started
        v.action_start_stop()
        self.assertFalse(v._timer.isActive())

        v.load_data_file(self.block_path)
        v.action_start_stop()
        self.assertTrue(v._timer.isActive())
        v.action_start_stop()
        self.assertFalse(v._timer.isActive())

        # Play button
        v._play_button.pressed.emit()
        self.assertTrue(v._timer.isActive())
        v._play_button.pressed.emit()
        self.assertFalse(v._timer.isActive())

        # Space bar
        Qt = self.Qt
        e = self.QtGui.QKeyEvent(
            self.QtCore.QEvent.Type.KeyPress, Qt.Key.Key_Space,
            Qt.KeyboardModifier.NoModifier)
        v.keyPressEvent(e)
        self.assertTrue(v._timer.isActive())
        e = self.QtGui.QKeyEvent(
            self.QtCore.QEvent.Type.KeyPress, Qt.Key.Key_A,
            Qt.KeyboardModifier.NoModifier)
        v.keyPressEvent(e)
        self.assertTrue(v._timer.isActive())

        # Pausing and depausing a running timer
        v.action_pause_timer()
        self.assertFalse(v._timer.isActive())
        self.assertTrue(v._timer_paused)
        v.action_depause_timer()
        self.assertTrue(v._timer.isActive())
        self.assertFalse(v._timer_paused)

        # Pausing and depausing a stopped timer
        v.action_stop_timer()
        v.action_pause_timer()
        self.assertFalse(v._timer_paused)
        v.action_depause_timer()
        self.assertFalse(v._timer.isActive())

        # Slider press pauses, release depauses
        v.action_start_timer()
        v._slider.sliderPressed.emit()
        self.assertFalse(v._timer.isActive())
        v._slider.sliderReleased.emit()
        self.assertTrue(v._timer.isActive())

        # Resizing pauses, and depauses after a timeout
        v._video_view.resize_event.emit()
        self.assertFalse(v._timer.isActive())
        self.assertTrue(v._resize_timer.isActive())
        v._resize_timeout()
        self.assertFalse(v._resize_timer.isActive())
        self.assertTrue(v._timer.isActive())
        v.action_stop_timer()

    def test_rate_changed(self):
        # Test changing the frame delay
        v = self.viewer()
        v._rate_field.setText('123')
        v._rate_field.editingFinished.emit()
        self.assertEqual(v._timer_interval, 123)
        self.assertEqual(v._timer.interval(), 123)

    def test_colormap_selection(self):
        # Test selecting a colormap
        names = list(myokit.ColorMap.names())
        self.assertGreater(len(names), 1)

        # Without data
        v = self.viewer()
        v.action_set_colormap(names[1])
        self.assertEqual(v._colormap, names[1])
        self.assertEqual(v._colormap_select.currentText(), names[1])

        # Unknown colormap is ignored
        v.action_set_colormap('not-a-colormap')
        self.assertEqual(v._colormap, names[1])

        # With data
        v.load_data_file(self.block_path)
        v.action_set_frame(50)
        v.action_set_colormap(names[0])
        frames0 = v._video_frames
        frame0 = v._video_pixmap.toImage()
        bar0 = v._colorbar_pixmap.toImage()

        # Using the combo box
        v._colormap_select.setCurrentIndex(1)
        v._colormap_select.activated.emit(1)
        self.assertEqual(v._colormap, names[1])
        self.assertIsNot(v._video_frames, frames0)
        self.assertEqual(v._video_iframe, 50)
        self.assertNotEqual(v._video_pixmap.toImage(), frame0)
        self.assertNotEqual(v._colorbar_pixmap.toImage(), bar0)

        # Images match those created by the data block
        expected = v._data.images('membrane.V', names[1])[50]
        np.testing.assert_array_equal(v._video_frames[50], expected)

    def test_colormap_range(self):
        # Test setting the colormap's lower and upper bounds
        v = self.viewer()
        b = self.small_block()
        with mock.patch('myokit.DataBlock2d.load', return_value=b):
            v.load_data_file(self.temp / 'x.zip')
        cmap = v._colormap
        auto = v._video_frames

        v._colormap_lower_field.setText('5')
        v._colormap_upper_field.setText('10')
        self.assertEqual(v._colormap_lower_field.value(), 5)
        v._colormap_upper_field.editingFinished.emit()
        expected = b.images('membrane.V', cmap, 5, 10)
        for x, y in zip(v._video_frames, expected):
            np.testing.assert_array_equal(x, y)
        self.assertFalse(
            all(np.array_equal(x, y) for x, y in zip(auto, expected)))

        # Invalid text reverts to auto
        v._colormap_lower_field.setText('abc')
        v._colormap_upper_field.setText('')
        v._colormap_lower_field.editingFinished.emit()
        v._colormap_upper_field.editingFinished.emit()
        self.assertEqual(v._colormap_lower_field.text(), '(Auto)')
        self.assertEqual(v._colormap_upper_field.text(), '(Auto)')
        for x, y in zip(v._video_frames, auto):
            np.testing.assert_array_equal(x, y)

    def test_variable_selection(self):
        # Test selecting a different variable
        v = self.viewer()

        # Without data
        v.event_variable_selected()
        v.action_set_variable('membrane.V')
        self.assertIsNone(v._video_frames)

        b = self.small_block()
        with mock.patch('myokit.DataBlock2d.load', return_value=b):
            v.load_data_file(self.temp / 'x.zip')
        self.assertEqual(v._variable, 'membrane.V')
        v.action_set_frame(2)
        i = v._variable_select.findText('ica.ICa')
        self.assertGreaterEqual(i, 0)
        v._variable_select.setCurrentIndex(i)
        v._variable_select.activated.emit(i)
        self.assertEqual(v._variable, 'ica.ICa')
        self.assertEqual(v._video_iframe, 2)
        expected = b.images('ica.ICa', v._colormap)
        np.testing.assert_array_equal(v._video_frames[2], expected[2])

        v.action_set_variable('membrane.V')
        self.assertEqual(v._variable_select.currentText(), 'membrane.V')

    def test_video_mouse_move(self):
        # Test the status bar shows the value under the cursor
        v = self.viewer()
        v.event_video_mouse_move(1, 1)
        self.assertEqual(v._label_cursor.text(), '')

        b = self.small_block()
        with mock.patch('myokit.DataBlock2d.load', return_value=b):
            v.load_data_file(self.temp / 'x.zip')
        v.action_set_frame(1)
        v._video_scene.mouse_moved.emit(2, 1)
        z = b.get2d('membrane.V')[1, 1, 2]
        text = v._label_cursor.text()
        self.assertIn(f'{z:< 1.6g}', text)
        self.assertTrue(text.startswith('( 2,  1, '))
        self.assertTrue(text.endswith(')'))
        self.assertEqual(text.count('('), text.count(')'))

        # Outside of the data
        v.event_video_mouse_move(10, 10)
        self.assertTrue(v._label_cursor.text().endswith(', ?)'))

    def test_graph_mouse_move(self):
        # Test the status bar shows the graph coordinates
        v = self.viewer()
        v._graph_area.mouse_moved.emit(1.5, -2.25)
        self.assertEqual(v._label_cursor.text(), '( 1.5, -2.25)')

    def test_video_clicks(self):
        # Test clicking the video adds graphs
        v = self.viewer()
        ga = v._graph_area

        # Without data, clicks are ignored
        v.event_video_single_click(1, 1)
        self.assertIsNone(ga._temp_index)

        b = self.small_block()
        with mock.patch('myokit.DataBlock2d.load', return_value=b):
            v.load_data_file(self.temp / 'x.zip')

        # Single click: temporary graph
        v._video_scene.single_click.emit(1.0, 0.0)
        self.assertEqual(ga._temp_index, (1, 0, 'membrane.V'))
        self.assertEqual(len(ga._frozen), 0)
        v._video_scene.single_click.emit(2.0, 1.0)
        self.assertEqual(ga._temp_index, (2, 1, 'membrane.V'))

        # Double click: frozen graph
        v._video_scene.double_click.emit(0.0, 1.0)
        self.assertIsNone(ga._temp_index)
        self.assertEqual(list(ga._frozen), [(0, 1, 'membrane.V')])

        # Single click on frozen graph: no temporary graph
        v.event_video_single_click(0, 1)
        self.assertIsNone(ga._temp_index)

        # Clear graphs
        v._graph_clear_button.pressed.emit()
        self.assertEqual(len(ga._frozen), 0)
        self.assertIsNone(ga._temp_index)
        self.assertIsNone(ga._last_variable)

    def test_graph_area(self):
        # Test the graph area directly
        ga = self.dv.GraphArea()
        self.addCleanup(ga.deleteLater)
        self.assertEqual(ga.sizeHint(), self.QtCore.QSize(250, 250))
        self.assertEqual(ga.minimumSizeHint(), self.QtCore.QSize(250, 5))

        # Graph area expands in both directions
        P = self.QtWidgets.QSizePolicy
        policy = ga.sizePolicy()
        self.assertIsInstance(policy, P)
        self.assertEqual(policy.horizontalPolicy(), P.Policy.Expanding)
        self.assertEqual(policy.verticalPolicy(), P.Policy.Expanding)

        # Without data
        ga.graph('membrane.V', 0, 0)
        ga.set_position(3)
        self.assertIsNone(ga._temp_index)
        self.assertEqual(ga.log().keys(), set())
        ga.grab()

        # With data
        b = self.small_block(nt=5)
        ga.set_data(b)
        time = b.time()
        self.assertLess(ga._tmin, time[0])
        self.assertGreater(ga._tmax, time[-1])
        self.assertAlmostEqual(ga._trange, ga._tmax - ga._tmin)
        self.assertAlmostEqual(ga._time_scaled[0], 1 / 102)
        self.assertAlmostEqual(ga._time_scaled[-1], 101 / 102)
        ga.set_position(3)
        self.assertEqual(ga._position, time[3])

        # Temporary graph, scaled to [0, 1] with 5% padding
        ga.graph('membrane.V', 1, 1)
        path = ga._temp_path
        self.assertEqual(path.elementCount(), 5)
        ymin, ymax = ga._scaling['membrane.V']
        data = b.get2d('membrane.V')
        d = np.max(data) - np.min(data)
        self.assertAlmostEqual(ymin, np.min(data) - 0.05 * d)
        self.assertAlmostEqual(ymax, np.max(data) + 0.05 * d)
        trace = b.trace('membrane.V', 1, 1)
        for i in range(5):
            e = path.elementAt(i)
            self.assertAlmostEqual(e.x, ga._time_scaled[i])
            self.assertAlmostEqual(e.y, 1 - (trace[i] - ymin) / (ymax - ymin))

        # Same graph again: no change
        ga.graph('membrane.V', 1, 1)
        self.assertIs(ga._temp_path, path)

        # Freeze, add more graphs than there are colors
        ga.freeze()
        self.assertIsNone(ga._temp_path)
        self.assertEqual(list(ga._frozen.values()), [path])
        n = len(ga._color_cycle) + 2
        b2 = self.small_block(nt=5, ny=n, nx=1)
        ga.set_data(b2)
        self.assertEqual(len(ga._frozen), 0)
        for y in range(n):
            ga.graph('membrane.V', 0, y)
            ga.freeze()
        self.assertEqual(len(ga._frozen), n)
        ga.graph('ica.ICa', 0, 0)

        # Freezing without a temp graph does nothing
        ga.freeze()
        ga.freeze()
        self.assertEqual(len(ga._frozen), n + 1)

        # Constant data gets non-zero range
        b3 = myokit.DataBlock2d(1, 1, [0, 1, 2])
        b3.set2d('c', np.ones((3, 1, 1)))
        ga.set_data(b3)
        ga.graph('c', 0, 0)
        self.assertEqual(ga._scaling['c'], (0, 2))

        # Painting
        ga.set_data(b2)
        ga.graph('membrane.V', 0, 0)
        ga.freeze()
        ga.graph('membrane.V', 0, 1)
        ga.resize(200, 100)
        image = ga.grab().toImage()
        self.assertEqual(image.width(), 200)
        white = self.QtGui.QColor(self.Qt.GlobalColor.white)
        self.assertEqual(image.pixelColor(1, 1), white)

        # Log
        d = ga.log()
        self.assertEqual(
            set(d.keys()),
            {'engine.time', '0.0.membrane.V', '0.1.membrane.V'})
        np.testing.assert_array_equal(d['engine.time'], b2.time())
        np.testing.assert_array_equal(
            d['membrane.V', 0, 1], b2.trace('membrane.V', 0, 1))

    def test_graph_area_mouse_move(self):
        # Test mouse movement is converted to graph coordinates
        ga = self.dv.GraphArea()
        self.addCleanup(ga.deleteLater)
        ga.resize(200, 100)
        ga.resizeEvent()
        self.assertAlmostEqual(ga._sw, 1 / 200)
        self.assertAlmostEqual(ga._sh, 1 / 100)

        received = []
        ga.mouse_moved.connect(lambda x, y: received.append((x, y)))
        event = mock.Mock()
        event.pos.return_value = self.QtCore.QPoint(50, 25)

        # No graphs: no event
        ga.mouseMoveEvent(event)
        self.assertEqual(received, [])

        b = self.small_block(nt=5)
        ga.set_data(b)
        ga.graph('membrane.V', 0, 0)
        ga.mouseMoveEvent(event)
        self.assertEqual(len(received), 1)
        x, y = received[0]
        ymin, ymax = ga._scaling['membrane.V']
        self.assertAlmostEqual(x, ga._tmin + 0.25 * ga._trange)
        self.assertAlmostEqual(y, ymin + 0.75 * (ymax - ymin))

        # Zero size
        ga.resize(0, 0)
        ga.resizeEvent()
        self.assertEqual(ga._sw, 1)
        self.assertEqual(ga._sh, 1)

    def test_video_scene(self):
        # Test the video scene's mouse events
        Qt = self.Qt
        scene = self.dv.VideoScene()
        self.addCleanup(scene.deleteLater)
        scene.resize(4, 3)
        self.assertEqual(scene.sceneRect(), self.QtCore.QRectF(0, 0, 4, 3))

        single, double, moved = [], [], []
        scene.single_click.connect(lambda x, y: single.append((x, y)))
        scene.double_click.connect(lambda x, y: double.append((x, y)))
        scene.mouse_moved.connect(lambda x, y: moved.append((x, y)))

        def event(x, y, button=Qt.MouseButton.LeftButton,
                  modifiers=Qt.KeyboardModifier.NoModifier):
            e = mock.Mock()
            e.button.return_value = button
            e.modifiers.return_value = modifiers
            e.scenePos.return_value = self.QtCore.QPointF(x, y)
            return e

        scene.mousePressEvent(event(1.7, 2.2))
        scene.mouseDoubleClickEvent(event(3.5, 0.1))
        scene.mouseMoveEvent(event(-2.5, 7.9))
        self.assertEqual(single, [(1, 2)])
        self.assertEqual(double, [(3, 0)])
        self.assertEqual(moved, [(-2, 7)])

        # Ignored: outside, wrong button, with modifier
        for f in (scene.mousePressEvent, scene.mouseDoubleClickEvent):
            f(event(4, 1))
            f(event(1, 3))
            f(event(-1, 1))
            f(event(1, 1, button=Qt.MouseButton.RightButton))
            f(event(1, 1, modifiers=Qt.KeyboardModifier.ShiftModifier))
        self.assertEqual(len(single), 1)
        self.assertEqual(len(double), 1)

    def test_video_view(self):
        # Test the video view's resize handling
        scene = self.dv.VideoScene()
        view = self.dv.VideoView(scene)
        self.addCleanup(scene.deleteLater)
        self.addCleanup(view.deleteLater)
        scene.resize(10, 5)
        view.resize(200, 200)

        resized = []
        view.resize_event.connect(lambda: resized.append(True))
        view.resizeEvent()
        self.assertEqual(resized, [True])
        self.assertTrue(view._resize_timer.isActive())
        view._resize_timeout()
        self.assertFalse(view._resize_timer.isActive())

        # Scene fits in view, keeping the aspect ratio
        t = view.transform()
        vr = view.viewport().rect()
        xr = min(vr.width() / 10, vr.height() / 5)
        self.assertAlmostEqual(t.m11(), xr)
        self.assertAlmostEqual(t.m22(), xr)

        # Fitting again doesn't change the result
        view.fitInView(scene.sceneRect(), keepAspect=True)
        t = view.transform()
        self.assertAlmostEqual(t.m11(), xr)
        self.assertAlmostEqual(t.m22(), xr)

        # Without keeping aspect ratio
        view.fitInView(scene.sceneRect())
        t = view.transform()
        self.assertAlmostEqual(t.m11(), vr.width() / 10)
        self.assertAlmostEqual(t.m22(), vr.height() / 5)

    def test_auto_float_field(self):
        # Test the AutoFloatField
        f = self.dv.AutoFloatField()
        self.addCleanup(f.deleteLater)
        self.assertEqual(f.text(), '(Auto)')
        self.assertIsNone(f.value())
        self.assertIn('127, 127, 127', f.styleSheet())

        f.setText('1.5e3')
        f.editingFinished.emit()
        self.assertEqual(f.value(), 1500)
        self.assertEqual(f.text(), '1.5e3')
        self.assertNotIn('127, 127, 127', f.styleSheet())

        f.setText('hello')
        f.editingFinished.emit()
        self.assertEqual(f.text(), '(Auto)')
        self.assertIsNone(f.value())

        # Focusing schedules a select all
        with mock.patch.object(self.QtCore.QTimer, 'singleShot') as m:
            f.focusInEvent(self.QtGui.QFocusEvent(
                self.QtCore.QEvent.Type.FocusIn))
        m.assert_called_once_with(0, f.selectAll)

    def test_about(self):
        # Test the about dialog
        v = self.viewer()
        v._tool_about.trigger()
        self.mock_about.assert_called_once()
        self.assertEqual(self.mock_about.call_args[0][2], self.dv.ABOUT)

    def test_export_without_data(self):
        # Test all export functions warn if there is no data
        v = self.viewer()
        fd = self.QtWidgets.QFileDialog
        with mock.patch.object(fd, 'getSaveFileName') as m:
            for tool in (v._tool_exframe, v._tool_exgraph, v._tool_imgframe,
                         v._tool_imgcolor):
                self.mock_warning.reset_mock()
                tool.trigger()
                self.assertIn('No data to export', self.warning_text())
        self.assertFalse(m.called)
        self.assertEqual(list(self.temp.iterdir()), [])

    def test_extract_frame(self):
        # Test exporting the current frame to csv
        v = self.viewer()
        b = self.small_block()
        with mock.patch('myokit.DataBlock2d.load', return_value=b):
            v.load_data_file(self.temp / 'x.zip')
        v.action_set_frame(2)
        path = self.temp / 'frame.csv'

        # Canceled
        with self.save_dialog(''):
            v.action_extract_frame()
        self.assertFalse(path.exists())

        with self.save_dialog(path):
            v._tool_exframe.trigger()
        lines = path.read_text().splitlines()
        self.assertEqual(lines[0], '"x","y","value"')
        self.assertEqual(len(lines), 1 + 2 * 3)
        x, y, z = lines[-1].split(',')
        self.assertEqual((x, y), ('2', '1'))
        self.assertEqual(float(z), b.get2d('membrane.V')[2, 1, 2])

    def test_extract_graphs(self):
        # Test exporting the graphs to csv
        v = self.viewer()
        b = self.small_block()
        with mock.patch('myokit.DataBlock2d.load', return_value=b):
            v.load_data_file(self.temp / 'x.zip')
        path = self.temp / 'graphs.csv'

        # No graphs selected
        with self.save_dialog(path) as dialog:
            v.action_extract_graphs()
        self.assertIn('No graphs to export', self.warning_text())
        self.assertFalse(dialog.called)
        self.assertFalse(path.exists())

        # Canceled
        v.event_video_double_click(1, 0)
        v.event_video_single_click(2, 1)
        with self.save_dialog(''):
            v.action_extract_graphs()
        self.assertFalse(path.exists())

        with self.save_dialog(path):
            v.action_extract_graphs()
        d = myokit.DataLog.load_csv(path)
        self.assertEqual(
            set(d.keys()),
            {'engine.time', '1.0.membrane.V', '2.1.membrane.V'})
        np.testing.assert_array_equal(
            d['membrane.V', 2, 1], b.trace('membrane.V', 2, 1))

    def test_extract_frame_image(self):
        # Test exporting the current frame as an image
        v = self.loaded_viewer()
        v.action_set_frame(20)

        # Canceled
        with self.save_dialog(''):
            v.action_extract_frame_image()
        self.assertEqual(list(self.temp.iterdir()), [])

        # Bad extension
        with self.save_dialog(self.temp / 'frame.gif'):
            v.action_extract_frame_image()
        self.assertIn('Image type not recognized', self.warning_text())
        self.assertEqual(list(self.temp.iterdir()), [])

        path = self.temp / 'frame.png'
        with self.save_dialog(path):
            v._tool_imgframe.trigger()
        image = self.QtGui.QImage(str(path))
        self.assertEqual((image.width(), image.height()), (16, 16))
        self.assertEqual(
            image.convertToFormat(v._video_pixmap.toImage().format()),
            v._video_pixmap.toImage())

        path = self.temp / 'frame.bmp'
        with self.save_dialog(path):
            v.action_extract_frame_image()
        self.assertFalse(self.QtGui.QImage(str(path)).isNull())

    def test_extract_colormap_image(self):
        # Test exporting the colormap as an image
        v = self.loaded_viewer()

        # Canceled
        with self.save_dialog(''):
            v.action_extract_colormap_image()
        self.assertEqual(list(self.temp.iterdir()), [])

        # Bad extension
        with self.save_dialog(self.temp / 'cmap.txt'):
            v.action_extract_colormap_image()
        self.assertIn('Image type not recognized', self.warning_text())
        self.assertEqual(list(self.temp.iterdir()), [])

        # Automatic bounds
        path = self.temp / 'cmap.png'
        with self.save_dialog(path):
            v._tool_imgcolor.trigger()
        image = self.QtGui.QImage(str(path))
        self.assertEqual((image.width(), image.height()), (200, 800))

        # Set bounds
        v._colormap_lower_field.setText('-10')
        v._colormap_upper_field.setText('10')
        path = self.temp / 'cmap.jpg'
        with self.save_dialog(path):
            v.action_extract_colormap_image()
        image = self.QtGui.QImage(str(path))
        self.assertEqual((image.width(), image.height()), (200, 800))

    def test_config(self):
        # Test saving and loading settings
        names = list(myokit.ColorMap.names())
        v = self.viewer()
        v.load_data_file(self.block_path)
        v.action_set_colormap(names[-1])
        v._rate_field.setText('77')
        v.event_rate_changed()
        v.close()
        self.assertTrue(self.settings.is_file())

        config = configparser.RawConfigParser()
        config.read(self.settings)
        self.assertEqual(config.get('video', 'color_map'), names[-1])
        self.assertEqual(config.get('video', 'interval'), '77')
        self.assertEqual(
            config.get('files', 'recent_0'), str(self.block_path.absolute()))
        self.assertEqual(
            config.get('files', 'path'), str(self.block_path.parent))
        for key in ('x', 'y', 'w', 'h'):
            self.assertTrue(config.has_option('window', key))
        self.assertTrue(config.has_option('splitter', 's1'))

        # Settings are restored
        w = self.viewer()
        self.assertEqual(w._colormap, names[-1])
        self.assertEqual(w._colormap_select.currentText(), names[-1])
        self.assertEqual(w._timer_interval, 77)
        self.assertEqual(w._timer.interval(), 77)
        self.assertEqual(w._rate_field.text(), '77')
        self.assertEqual(w._recent_files, [self.block_path.absolute()])
        self.assertTrue(w._recent_file_tools[0].isVisible())
        self.assertEqual(w._path, self.block_path.parent)
        self.assertIsNone(w._data)

    def test_config_partial(self):
        # Test loading settings with missing, invalid, or partial entries
        missing = self.temp / 'missing.zip'
        self.settings.write_text(
            '[window]\n'
            'w = 700\n'
            'h = 500\n'
            '[splitter]\n'
            's1 = 100\n'
            '[files]\n'
            f'path = {self.temp / "not-a-dir"}\n'
            f'recent_0 = {missing}\n'
            f'recent_1 = {self.block_path}\n'
            '[video]\n'
            'color_map = not-a-colormap\n'
            'interval = 0\n'
        )
        v = self.viewer()
        self.assertEqual(v.geometry().width(), 700)
        self.assertEqual(v.geometry().height(), 500)
        self.assertEqual(v._recent_files, [self.block_path.absolute()])
        self.assertNotEqual(v._path, self.temp / 'not-a-dir')
        self.assertEqual(v._colormap, next(iter(myokit.ColorMap.names())))
        self.assertEqual(v._timer_interval, 50)

        # Empty interval
        self.settings.write_text('[video]\ninterval =\n')
        v = self.viewer()
        self.assertEqual(v._timer_interval, 50)

        # Non-integer values are ignored
        self.settings.write_text(
            '[window]\n'
            'x = 10\n'
            'w = wide\n'
            'h = 400.5\n'
            '[splitter]\n'
            's1 = big\n'
            's2 = 100\n'
            '[video]\n'
            'interval = fast\n'
        )
        default = self.viewer()
        default_sizes = default._central_widget.sizes()
        v = self.viewer()
        self.assertEqual(v.geometry().x(), 10)
        self.assertEqual(v.geometry().width(), default.geometry().width())
        self.assertEqual(v.geometry().height(), default.geometry().height())
        self.assertEqual(v._central_widget.sizes(), default_sizes)
        self.assertEqual(v._timer_interval, 50)

    def test_config_parse_error(self):
        # Test an unparseable settings file is ignored
        self.settings.write_text('[video]\ninterval = 99\nthis is not valid')
        v = self.viewer()
        self.assertEqual(v._timer_interval, 50)
        self.assertEqual(v._recent_files, [])


if __name__ == '__main__':
    unittest.main()
