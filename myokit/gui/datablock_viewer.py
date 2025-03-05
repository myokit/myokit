#
# Qt gui for viewing DataBlock2d data files.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import collections
import configparser
import os
import sys
import traceback

import numpy as np

import myokit
import myokit.gui

from myokit.gui import QtWidgets, QtGui, QtCore, Qt


# Application title
TITLE = 'Myokit DataBlock Viewer'

# Settings file
SETTINGS_FILE = os.path.join(myokit.DIR_USER, 'DataBlockViewer.ini')

# Number of recent files to display
N_RECENT_FILES = 5

# About
ABOUT = f'<h1>{TITLE}</h1>' + f"""
<p>
    Myokit's DataBlock viewer is a utility to examine
    <code>DataBlock1d</code> and <code>DataBlock2d</code> objects
    containing simulation results for rectangular grids of cells.
</p>
<p>
    DataBlocks can be saved to disk and then loaded into the viewer.
    Tissue-response to different 2d variables can be animated, and
    individual cells traces can be viewed in the graph area below. To
    select a cell, click anywhere in the animation.
</p>
<p>
    System info:
    <br />Python: {sys.version}
    <br />Using the {myokit.gui.backend} GUI backend.
</p>
"""

# License
LICENSE = myokit.LICENSE_HTML

# File filters
FILTER_CSV = 'Comma separated file (*.txt *.csv)'
FILTER_IMG = ';;'.join([
    'Type detected by extension (*.png *.jpg *.jpeg *.bmp)',
    'BMP (*.bmp)',
    'JPEG (*.jpeg *.jpg)',
    'PNG (*.png)',
])
IMAGE_TYPES = ['PNG', 'JPG', 'JPEG', 'BMP']


# Application icon
def icon():
    icons = [
        'icon-datablock-viewer.ico',
        'icon-datablock-viewer-16.xpm',
        'icon-datablock-viewer-24.xpm',
        'icon-datablock-viewer-32.xpm',
        'icon-datablock-viewer-48.xpm',
        'icon-datablock-viewer-64.xpm',
        'icon-datablock-viewer-96.xpm',
        'icon-datablock-viewer-128.xpm',
        'icon-datablock-viewer-256.xpm',
    ]
    icon = QtGui.QIcon()
    for i in icons:
        icon.addFile(os.path.join(myokit.DIR_DATA, 'gui', i))
    return icon


class DataBlockViewer(myokit.gui.MyokitApplication):
    """
    Graphical interface for viewing DataBlock data.
    """

    def __init__(self, filename=None):
        super().__init__()
        # Set application icon
        self.setWindowIcon(icon())

        # Set size, center
        self.resize(800, 600)
        self.setMinimumSize(600, 400)
        qr = self.frameGeometry()
        cp = QtGui.QGuiApplication.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        # Status bar
        self._label_cursor = QtWidgets.QLabel()
        self.statusBar().addPermanentWidget(self._label_cursor)
        self.statusBar().showMessage('Ready')

        # Menu bar
        self.create_menu()

        # Timer
        self._timer_interval = 50
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(self._timer_interval)
        self._timer.setSingleShot(False)
        self._timer.timeout.connect(self.action_next_frame)
        self._timer_paused = False
        self._timer.setTimerType(Qt.TimerType.PreciseTimer)

        # Video widget
        self._video_scene = VideoScene()
        self._video_scene.mouse_moved.connect(self.event_video_mouse_move)
        self._video_scene.single_click.connect(self.event_video_single_click)
        self._video_scene.double_click.connect(self.event_video_double_click)
        self._video_view = VideoView(self._video_scene)
        self._video_view.setMouseTracking(True)
        self._video_view.setCursor(Qt.CursorShape.CrossCursor)
        #self._video_view.setViewport(QtOpenGL.QGLWidget())
        self._video_pixmap = None
        self._video_item = None
        self._video_frames = None
        self._video_iframe = None

        # Colorbar widget
        self._colorbar_width = 20
        self._colorbar_height = 256
        self._colorbar_scene = VideoScene()
        self._colorbar_view = VideoView(self._colorbar_scene)
        self._colorbar_view.setMaximumWidth(self._colorbar_width)
        self._colorbar_pixmap = None
        self._colorbar_item = None

        # Video slider
        self._slider = QtWidgets.QSlider(Qt.Orientation.Horizontal)
        self._slider.setTickPosition(QtWidgets.QSlider.TickPosition.NoTicks)
        self._slider.setSingleStep(1)
        self._slider.setMinimum(0)
        self._slider.setMaximum(0)
        self._slider.sliderPressed.connect(self.action_pause_timer)
        self._slider.sliderReleased.connect(self.action_depause_timer)
        self._slider.valueChanged.connect(self.action_set_frame)

        # Controls
        style = QtWidgets.QApplication.style()

        # Play button
        self._play_icon_play = style.standardIcon(
            style.StandardPixmap.SP_MediaPlay)
        self._play_icon_pause = style.standardIcon(
            style.StandardPixmap.SP_MediaPause)
        self._play_button = QtWidgets.QPushButton()
        self._play_button.setIcon(self._play_icon_play)
        self._play_button.pressed.connect(self.action_start_stop)

        # Frame indicator
        self._frame_label = QtWidgets.QLabel('Frame')
        self._frame_field = QtWidgets.QLineEdit('0')
        self._frame_field.setReadOnly(True)
        self._frame_field.setMaxLength(6)
        self._frame_field.setMaximumWidth(100)
        self._frame_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # Time indicator
        self._time_label = QtWidgets.QLabel('Time')
        self._time_field = QtWidgets.QLineEdit('0')
        self._time_field.setReadOnly(True)
        self._time_field.setMaxLength(6)
        self._time_field.setMaximumWidth(100)
        self._time_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # Speed indicator
        self._rate_label = QtWidgets.QLabel('Delay')
        self._rate_field = QtWidgets.QLineEdit(str(self._timer_interval))
        self._rate_field.setValidator(QtGui.QIntValidator(1, 2**20, self))
        self._rate_field.editingFinished.connect(self.event_rate_changed)
        self._rate_field.setMaximumWidth(100)
        self._rate_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # Graph controls
        self._graph_clear_button = QtWidgets.QPushButton('Clear graphs')
        self._graph_clear_button.pressed.connect(self.action_clear_graphs)

        # Variable selection
        self._variable_select = QtWidgets.QComboBox()
        self._variable_select.activated.connect(self.event_variable_selected)
        self._variable_select.setMinimumWidth(160)

        # Colormap selection
        self._colormap = next(iter(myokit.ColorMap.names()))
        self._colormap_select = QtWidgets.QComboBox()
        for cmap in myokit.ColorMap.names():
            self._colormap_select.addItem(cmap)
        self._colormap_select.activated.connect(self.event_colormap_selected)
        self._colormap_select.setMinimumWidth(120)

        self._colormap_lower_label = QtWidgets.QLabel('Range')
        self._colormap_lower_label.setMaximumWidth(50)
        self._colormap_lower_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._colormap_lower_field = AutoFloatField()
        self._colormap_lower_field.setMaxLength(6)
        self._colormap_lower_field.setMaximumWidth(80)
        self._colormap_lower_field.editingFinished.connect(
            self.event_variable_selected)

        self._colormap_upper_label = QtWidgets.QLabel('to')
        self._colormap_upper_label.setMaximumWidth(20)
        self._colormap_upper_label.setAlignment(
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self._colormap_upper_field = AutoFloatField()
        self._colormap_upper_field.setMaxLength(6)
        self._colormap_upper_field.setMaximumWidth(80)
        self._colormap_upper_field.editingFinished.connect(
            self.event_variable_selected)

        # Control layout
        self._control_layout = QtWidgets.QHBoxLayout()
        self._control_layout.addWidget(self._play_button)
        self._control_layout.addWidget(self._frame_label)
        self._control_layout.addWidget(self._frame_field)
        self._control_layout.addWidget(self._time_label)
        self._control_layout.addWidget(self._time_field)
        self._control_layout.addWidget(self._rate_label)
        self._control_layout.addWidget(self._rate_field)
        self._control_layout.addWidget(self._graph_clear_button)
        self._control_layout.addWidget(self._variable_select)
        self._control_layout.addWidget(self._colormap_select)
        self._control_layout.addWidget(self._colormap_lower_label)
        self._control_layout.addWidget(self._colormap_lower_field)
        self._control_layout.addWidget(self._colormap_upper_label)
        self._control_layout.addWidget(self._colormap_upper_field)

        # Graph area
        self._graph_area = GraphArea()
        self._graph_area.mouse_moved.connect(self.event_graph_mouse_move)
        self._graph_area.setMouseTracking(True)
        self._graph_area.setCursor(Qt.CursorShape.CrossCursor)

        # Video and colorbar layout
        self._video_plus_layout = QtWidgets.QHBoxLayout()
        self._video_plus_layout.addWidget(self._video_view)
        self._video_plus_layout.addWidget(self._colorbar_view)

        # Video Layout
        self._video_layout = QtWidgets.QVBoxLayout()
        self._video_layout.addLayout(self._video_plus_layout)
        self._video_layout.addWidget(self._slider)
        self._video_layout.addLayout(self._control_layout)
        self._video_widget = QtWidgets.QWidget()
        self._video_widget.setLayout(self._video_layout)

        # Central layout
        self._central_widget = QtWidgets.QSplitter(Qt.Orientation.Vertical)
        self._central_widget.addWidget(self._video_widget)
        self._central_widget.addWidget(self._graph_area)
        self.setCentralWidget(self._central_widget)

        # Current path, current file, recent files
        self._path = QtCore.QDir.currentPath()
        self._file = None
        self._recent_files = []

        # Current data block, display variable
        self._data = None
        self._variable = None

        # Load settings from ini file
        self.load_config()
        self.update_window_title()

        # Set controls to correct values
        self._colormap_select.setCurrentIndex(
            self._colormap_select.findText(self._colormap))
        self._rate_field.setText(str(self._timer_interval))
        self._timer.setInterval(self._timer_interval)

        # Pause video playback during resize
        self._resize_timer = QtCore.QTimer()
        self._resize_timer.timeout.connect(self._resize_timeout)
        self._video_view.resize_event.connect(self._resize_started)
        self._colorbar_view.resize_event.connect(self._resize_started)

        # Attempt to load selected file
        if filename and os.path.isfile(filename):
            self.load_data_file(filename)

        # Focus on play button
        self._play_button.setFocus()

    def action_about(self):
        """
        Displays the about dialog.
        """
        QtWidgets.QMessageBox.about(self, TITLE, ABOUT)

    def action_clear_graphs(self):
        """
        Removes all graphs from the graph area.
        """
        self._graph_area.clear()

    def action_depause_timer(self):
        """
        De-pauses the timer, restarting it if was paused, not affecting it if
        it wasn't.
        """
        if self._timer_paused:
            self._timer_paused = False
            if self._data is not None:
                self._timer.start()

    def action_extract_colormap_image(self):
        """ Extracts the current colormap to an image file. """

        if self._data is None:
            QtWidgets.QMessageBox.warning(
                self, TITLE,
                '<h1>No data to export.</h1>'
                '<p>Please open a data file first.</p>')
            return

        fname = QtWidgets.QFileDialog.getSaveFileName(
            self,
            'Extract colormap to image file',
            self._path,
            filter=FILTER_IMG)[0]

        if fname:
            fname = str(fname)
            ext = os.path.splitext(fname)[1][1:].upper()
            if ext not in IMAGE_TYPES:
                QtWidgets.QMessageBox.warning(
                    self, TITLE,
                    '<h1>Image type not recognized.</h1>'
                    f'<p>Unknown image type "{ext}".</p>')
                return

            # Create image
            nx = 200
            ny = 800
            image = myokit.ColorMap.image(self._colormap, nx, ny)
            image = QtGui.QImage(
                image, nx, ny, QtGui.QImage.Format.Format_ARGB32)

            # Add lower and upper bounds
            lower = self._colormap_lower_field.value()
            upper = self._colormap_upper_field.value()
            if lower is None or upper is None:
                data = self._data.get2d(self._variable)
                lower = np.min(data) if lower is None else lower
                upper = np.max(data) if upper is None else upper
            painter = QtGui.QPainter(image)
            painter.drawText(10, 15, str(upper))
            painter.drawText(10, ny - 5, str(lower))
            painter.end()

            # Save
            image.save(fname, ext)

    def action_extract_frame(self):
        """
        Extracts the current frame to a csv file.
        """
        if self._data is None:
            QtWidgets.QMessageBox.warning(
                self, TITLE,
                '<h1>No data to export.</h1>'
                '<p>Please open a data file first.</p>')
            return
        fname = QtWidgets.QFileDialog.getSaveFileName(
            self,
            'Extract frame to csv file',
            self._path,
            filter=FILTER_CSV)[0]
        if fname:
            fname = str(fname)
            self._data.save_frame_csv(
                fname, self._variable, self._video_iframe)

    def action_extract_frame_image(self):
        """
        Extracts the current frame to an image file.
        """
        if self._data is None:
            QtWidgets.QMessageBox.warning(
                self, TITLE,
                '<h1>No data to export.</h1>'
                '<p>Please open a data file first.</p>')
            return
        fname = QtWidgets.QFileDialog.getSaveFileName(
            self,
            'Extract frame to image file',
            self._path,
            filter=FILTER_IMG)[0]
        if fname:
            fname = str(fname)
            ext = os.path.splitext(fname)[1][1:].upper()
            if ext not in IMAGE_TYPES:
                QtWidgets.QMessageBox.warning(
                    self, TITLE,
                    '<h1>Image type not recognized.</h1>'
                    f'<p>Unknown image type "{ext}".</p>')
                return
            nt, ny, nx = self._data.shape()
            image = self._video_frames[self._video_iframe]
            image = QtGui.QImage(
                image, nx, ny, QtGui.QImage.Format.Format_ARGB32)
            image.save(fname, ext)

    def action_extract_graphs(self):
        """
        Extracts the currently displayed graphs to a csv file.
        """
        if self._data is None:
            QtWidgets.QMessageBox.warning(
                self, TITLE,
                '<h1>No data to export.</h1>'
                '<p>Please open a data file first.</p>')
            return
        d = self._graph_area.log()
        if len(d) == 0:
            QtWidgets.QMessageBox.warning(
                self, TITLE,
                '<h1>No graphs to export.</h1>'
                '<p>Please add some graphs to the graph panel by clicking or'
                ' double clicking the video area.</p>')
            return
        fname = QtWidgets.QFileDialog.getSaveFileName(
            self,
            'Extract graphs to csv file',
            self._path,
            filter=FILTER_CSV)[0]
        if fname:
            fname = str(fname)
            d.save_csv(fname)

    def action_license(self):
        """
        Displays this program's licensing information.
        """
        QtWidgets.QMessageBox.about(self, TITLE, LICENSE)

    def action_next_frame(self, e=None):
        """
        Move to next frame!
        """
        self.action_set_frame(self._video_iframe + 1)

    def action_open(self):
        """
        Let the user select a data file to load.
        """
        self.action_stop_timer()
        fname = QtWidgets.QFileDialog.getOpenFileName(
            self, 'Open data file', directory=self._path)[0]
        QtWidgets.QApplication.processEvents()
        if fname:
            fname = str(fname)
            self.load_data_file(fname)

    def action_pause_timer(self):
        """
        Pauses the timer (if running). Only meant to be used for very short
        periods!
        """
        if self._timer.isActive():
            self._timer_paused = True
        self._timer.stop()

    def action_recent_file(self):
        """
        Opens a recent file.
        """
        action = self.sender()
        if action:
            fname = str(action.data())
            if not os.path.isfile(fname):
                QtWidgets.QMessageBox.warning(
                    self, TITLE,
                    '<h1>Failed to load file.</h1>'
                    '<p>The selected file no longer exists.</p>')
            else:
                self.load_data_file(fname)

    def action_start_stop(self):
        """
        Toggles the started/stopped state of the timer.
        """
        if self._timer.isActive():
            self.action_stop_timer()
        else:
            self.action_start_timer()

    def action_set_colormap(self, name):
        """
        Loads the ColorMap specified by ``name``.

        If data is loaded, this will also call :meth:`action_set_variable` to
        update the video frames.
        """
        name = str(name)
        if not myokit.ColorMap.exists(name):
            return  # Silent return?

        # Set colormap
        self._colormap = name

        # Update colormap controls
        self._colormap_select.setCurrentIndex(
            self._colormap_select.findText(self._colormap))

        # Update colorbar
        if self._data is not None:
            nx = self._colorbar_width
            ny = self._colorbar_height
            image = myokit.ColorMap.image(self._colormap, nx, ny)
            image = QtGui.QImage(
                image, nx, ny, QtGui.QImage.Format.Format_ARGB32)
            self._colorbar_pixmap.convertFromImage(image)
            self._colorbar_item.setPixmap(self._colorbar_pixmap)  # qt5
            self.action_set_variable(self._variable)

    def action_set_variable(self, var):
        """
        Loads the variable specified by the name ``var`` into the main display.

        This method is also responsible for converting the data into frames to
        be displayed on the video widget.
        """
        if self._data is None:
            return
        self._variable = str(var)
        self._variable_select.setCurrentIndex(
            self._variable_select.findText(self._variable))
        self.action_pause_timer()
        self._video_frames = self._data.images(
            self._variable,
            self._colormap,
            self._colormap_lower_field.value(),
            self._colormap_upper_field.value()
        )
        self.action_set_frame(self._video_iframe)
        self.action_depause_timer()

    def action_set_frame(self, frame):
        """
        Move to a specific frame.

        This method updates the display to show a video frame created by an
        earlier call to :meth:`action_set_variable`.
        """
        # Check frame index
        nt, ny, nx = self._data.shape()
        frame = int(frame)
        if frame < 0 or frame >= nt:
            frame = 0
        # Update
        if self._video_iframe != frame or True:
            self._video_iframe = frame
            # Update slider
            if self._slider.value() != frame:
                self._slider.setValue(self._video_iframe)
            # Update frame/time information
            self._frame_field.setText(str(frame))
            self._time_field.setText(str(self._data.time()[frame]))
            # Update scene
            image = self._video_frames[self._video_iframe]
            image = QtGui.QImage(
                image, nx, ny, QtGui.QImage.Format.Format_ARGB32)
            self._video_pixmap.convertFromImage(image)
            self._video_item.setPixmap(self._video_pixmap)   # qt5
        # Update graph area
        self._graph_area.set_position(self._video_iframe)

    def action_start_timer(self):
        """
        Starts the timer.
        """
        self._timer_paused = False
        if self._data is not None:
            self._timer.start()
            self._play_button.setIcon(self._play_icon_pause)

    def action_stop_timer(self):
        self._timer_paused = False
        self._timer.stop()
        self._play_button.setIcon(self._play_icon_play)

    def closeEvent(self, event=None):
        # Called when window is closed.
        self.save_config()
        if event:
            event.accept()

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
        self._tool_open.setStatusTip('Open a DataLog for inspection.')
        self._tool_open.setIcon(QtGui.QIcon.fromTheme('document-open'))
        self._tool_open.triggered.connect(self.action_open)
        self._menu_file.addAction(self._tool_open)
        # File > ----
        self._menu_file.addSeparator()
        # File > Recent files
        self._recent_file_tools = []
        for i in range(N_RECENT_FILES):
            tool = QtGui.QAction(self, visible=False)
            tool.triggered.connect(self.action_recent_file)
            self._recent_file_tools.append(tool)
            self._menu_file.addAction(tool)
        # File > ----
        self._menu_file.addSeparator()
        # File > Quit
        self._tool_exit = QtGui.QAction('&Quit', self)
        self._tool_exit.setShortcut('Ctrl+Q')
        self._tool_exit.setStatusTip('Exit application.')
        self._tool_exit.setIcon(QtGui.QIcon.fromTheme('application-exit'))
        self._tool_exit.triggered.connect(self.close)
        self._menu_file.addAction(self._tool_exit)
        # Data menu
        self._menu_data = self._menu.addMenu('&Data')
        # Data > Extract frame
        self._tool_exframe = QtGui.QAction('Extract &frame', self)
        self._tool_exframe.setStatusTip(
            'Extract the current frame as csv file.')
        self._tool_exframe.triggered.connect(self.action_extract_frame)
        self._menu_data.addAction(self._tool_exframe)
        # Data > Extract graphs
        self._tool_exgraph = QtGui.QAction('Extract &graphs', self)
        self._tool_exgraph.setStatusTip('Extract the current graphs.')
        self._tool_exgraph.triggered.connect(self.action_extract_graphs)
        self._menu_data.addAction(self._tool_exgraph)
        # Data > ----
        self._menu_data.addSeparator()
        # Data > Extract frame as image
        self._tool_imgframe = QtGui.QAction('Save frame as &image', self)
        self._tool_imgframe.setStatusTip(
            'Save the current frame as an image file.')
        self._tool_imgframe.triggered.connect(self.action_extract_frame_image)
        self._menu_data.addAction(self._tool_imgframe)
        # Data > Extract colormap as image
        self._tool_imgcolor = QtGui.QAction('Save &colormap as image', self)
        self._tool_imgcolor.setStatusTip('Save the colormap as an image file.')
        self._tool_imgcolor.triggered.connect(
            self.action_extract_colormap_image)
        self._menu_data.addAction(self._tool_imgcolor)
        # Help menu
        self._menu_help = self._menu.addMenu('&Help')
        # Help > About
        self._tool_about = QtGui.QAction('&About', self)
        self._tool_about.setStatusTip('View information about this program.')
        self._tool_about.triggered.connect(self.action_about)
        self._menu_help.addAction(self._tool_about)
        self._tool_license = QtGui.QAction('&License', self)
        self._tool_license.setStatusTip('View this program\'s license info.')
        self._tool_license.triggered.connect(self.action_license)
        self._menu_help.addAction(self._tool_license)

    def display_exception(self):
        """ Displays the last exception in a messagebox. """
        QtWidgets.QMessageBox.warning(
            self, TITLE,
            '<h1>An error has occurred.</h1>'
            f'<pre>{traceback.format_exc()}</pre>')

    def event_colormap_selected(self):
        """ Colormap is selected by user. """
        self.action_set_colormap(str(self._colormap_select.currentText()))

    def event_graph_mouse_move(self, x, y):
        """
        Graph cursur moved: Display the current cursor position on the graph
        scene in the status bar.
        """
        self._label_cursor.setText(f'({x:< 1.6g}, {y:< 1.6g})')

    def event_rate_changed(self, e=None):
        """ User changed frame interval. """
        self._timer_interval = int(self._rate_field.text())
        self._timer.setInterval(self._timer_interval)

    def event_variable_selected(self):
        """ Variable is selected by user. """
        self._variable = self._variable_select.currentText()
        if self._data is not None:
            self.action_set_variable(self._variable)

    def event_video_single_click(self, x, y):
        """ Video clicked: Add a graph at the location of the click. """
        self._graph_area.graph(self._variable, x, y)

    def event_video_double_click(self, x, y):
        """
        Video double clicked: Add a frozen graph at the location of the click
        """
        self._graph_area.graph(self._variable, x, y)
        self._graph_area.freeze()

    def event_video_mouse_move(self, x, y):
        """
        Video cursur moved: Display the current cursor position on the video
        scene in the status bar.
        """
        # Cursor position is in scene coordinates, so already matches datablock
        # dimensions!
        if self._data is not None:
            try:
                z = self._data.get2d(self._variable)[self._video_iframe, y, x]
                z = '{:< 1.6g}'.format(z)
            except IndexError:
                z = '?'
            self._label_cursor.setText(f'({x:< 1.6g}, {y:< 1.6g}, {z}')

    def keyPressEvent(self, e):
        # A key has been pressed

        if e.key() == Qt.Key.Key_Space:
            self.action_start_stop()

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
        # Splitter position
        if config.has_section('splitter'):
            if config.has_option('splitter', 's1') and config.has_option(
                    'splitter', 's2'):
                s = [int(config.get('splitter', x)) for x in ('s1', 's2')]
                self._central_widget.setSizes(s)

        # Current files, directory, etc
        if config.has_section('files'):
            if config.has_option('files', 'path'):
                path = config.get('files', 'path')
                if os.path.isdir(path):
                    self._path = path
            self._recent_files = []
            for i in range(0, N_RECENT_FILES):
                opt = 'recent_' + str(i)
                if config.has_option('files', opt):
                    fname = config.get('files', opt)
                    if os.path.isfile(fname):
                        self._recent_files.append(fname)
            self.update_recent_files_menu()

        # Selected colormap
        if config.has_section('video'):
            if config.has_option('video', 'color_map'):
                cmap = config.get('video', 'color_map')
                self.action_set_colormap(cmap)
            if config.has_option('video', 'interval'):
                ival = config.get('video', 'interval')
                if ival:
                    ival = int(ival)
                    if ival > 0:
                        self._timer_interval = ival

    def load_data_file(self, fname):
        """
        Attempts to load the given data block 2d file.
        """
        self._timer.stop()
        # Fix path
        fname = os.path.abspath(str(fname))
        self._path = os.path.dirname(fname)
        # Try loading file.
        self.statusBar().showMessage('Loading ' + str(fname))
        n = 1000000
        pd = QtWidgets.QProgressDialog('Loading data file...', 'Cancel', 0, n)
        pd.setWindowModality(Qt.WindowModality.WindowModal)
        pd.setValue(0)

        class Reporter(myokit.ProgressReporter):
            def __init__(self, pd):
                self._pd = pd

            def enter(self, msg=None):
                pass

            def exit(self):
                pass

            def update(self, f):
                self._pd.setValue((int)(n * f))
                return not self._pd.wasCanceled()

        reporter = Reporter(pd)
        try:
            data = myokit.DataBlock2d.load(fname, progress=reporter)
            del reporter
        except myokit.DataBlockReadError as e:
            pd.reset()
            self.statusBar().showMessage('Load failed.')
            QtWidgets.QMessageBox.warning(
                self, TITLE,
                '<h1>Unable to read file.</h1>'
                f'<p>The given filename <code>{fname}</code>'
                ' could not be read as a <code>myokit.DataBlock2d</code>.</p>'
                f'<p>{e}</p>'
            )
            return
        except Exception:
            pd.reset()
            self.statusBar().showMessage('Load failed.')
            self.display_exception()
            return
        finally:
            if pd.wasCanceled():
                self.statusBar().showMessage('Load canceled.')
                return

        # Don't load empty files
        if data.len2d() < 1:
            self.statusBar().showMessage('Load failed: empty file.')
            QtWidgets.QMessageBox.warning(
                self, TITLE,
                '<h1>Unable to read file.</h1>'
                f'<p>The given filename <code>{fname}</code>'
                ' does not contain any 2d data.</p>')
            return

        # File loaded okay
        self.statusBar().showMessage('File loaded succesfully.')
        self._file = fname
        self._data = data
        self.update_window_title()

        # Update recent file list
        try:
            # Remove fname from recent files list
            i = self._recent_files.index(fname)
            self._recent_files = \
                self._recent_files[:i] + self._recent_files[i + 1:]
        except ValueError:
            pass
        self._recent_files.insert(0, fname)
        self._recent_files = self._recent_files[:N_RECENT_FILES]
        self.update_recent_files_menu()

        # Update video scene
        nt, ny, nx = self._data.shape()
        self._video_scene.clear()
        self._video_scene.resize(nx, ny)
        self._video_view.resizeEvent()
        self._video_iframe = 0

        # Add empty video item to video scene
        self._video_pixmap = QtGui.QPixmap(nx, ny)
        self._video_item = QtWidgets.QGraphicsPixmapItem(self._video_pixmap)
        self._video_scene.addItem(self._video_item)

        # Update colormap scene
        nx, ny = self._colorbar_width, self._colorbar_height
        self._colorbar_scene.clear()
        self._colorbar_scene.resize(nx, ny)
        self._colorbar_view.resizeEvent()

        # Add empty colormap item to colormap scene
        self._colorbar_pixmap = QtGui.QPixmap(nx, ny)
        self._colorbar_item = QtWidgets.QGraphicsPixmapItem(
            self._colorbar_pixmap)
        self._colorbar_scene.addItem(self._colorbar_item)

        # Move slider to correct position
        self._slider.setMaximum(nt)
        self._slider.setPageStep(int(nt / 20))

        # Update controls
        for i in range(self._variable_select.count(), 0, -1):
            self._variable_select.removeItem(i - 1)
        variable = None
        for name in data.keys2d():
            self._variable_select.addItem(name)
            if variable is None or name in ('membrane.V', 'membrane.v'):
                variable = name
        self.action_set_variable(variable)
        self.action_set_colormap(self._colormap)

        # Update graph area
        self._graph_area.set_data(self._data)

    def _resize_started(self, e=None):
        """
        Called when the video scene is resized, delays video updates by a few
        ms.
        """
        self._resize_timer.start(300)
        self.action_pause_timer()

    def _resize_timeout(self, e=None):
        """
        Called a few ms after a resize.
        """
        self._resize_timer.stop()
        self.action_depause_timer()

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

        # Splitter position
        config.add_section('splitter')
        s = self._central_widget.sizes()
        config.set('splitter', 's1', str(s[0]))
        config.set('splitter', 's2', str(s[1]))

        # Current files, directory, etc
        config.add_section('files')
        config.set('files', 'path', self._path)
        for k, fname in enumerate(self._recent_files):
            config.set('files', 'recent_' + str(k), fname)

        # Current control values
        config.add_section('video')
        config.set('video', 'color_map', self._colormap)
        config.set('video', 'interval', self._timer_interval)

        # Write configuration to ini file
        inifile = os.path.expanduser(SETTINGS_FILE)
        with open(inifile, 'w') as configfile:
            config.write(configfile)

    def update_recent_files_menu(self):
        """
        Updates the recent files menu.
        """
        for k, fname in enumerate(self._recent_files):
            t = self._recent_file_tools[k]
            t.setText(f'{k + 1}. {os.path.basename(fname)}')
            t.setData(fname)
            t.setVisible(True)
        for i in range(len(self._recent_files), N_RECENT_FILES):
            self._recent_file_tools[i].setVisible(False)

    def update_window_title(self):
        """
        Sets this window's title based on the current state.
        """
        title = f'{TITLE} {myokit.__version__}'
        if self._file:
            title = f'{os.path.basename(self._file)} - {title}'
        self.setWindowTitle(title)


class VideoScene(QtWidgets.QGraphicsScene):
    """
    Color data display scene.

    Note that, despite the name, this item does not manage the conversion from
    data to the image. The actual drawing happens by calling ``setPixmap`` on a
    ``QGraphicsPixmapItem`` that gets added to this scene.

    See :meth:`DataBlockViewer.action_set_variable()` and
    :meth:`DataBlockViewer.action_set_frame()`.
    """
    # Signals
    # Somebody moved the mouse
    # Attributes: cell x, cell y
    mouse_moved = QtCore.Signal(int, int)
    # Single click
    # Attributes: cell x, cell y
    single_click = QtCore.Signal(float, float)
    # Double click!
    # Attributes: cell x, cell y
    double_click = QtCore.Signal(float, float)

    def __init__(self, *args):
        super().__init__(*args)
        self.setBackgroundBrush(QtGui.QColor(192, 192, 192))
        self._w = None
        self._h = None
        self._p = None
        self.resize(1, 1)

    def mousePressEvent(self, event):
        # Single-click event
        if event.button() == Qt.MouseButton.LeftButton:
            if event.modifiers() == Qt.KeyboardModifier.NoModifier:
                p = event.scenePos()
                x, y = int(p.x()), int(p.y())
                if x >= 0 and x < self._w and y >= 0 and y < self._h:
                    self.single_click.emit(x, y)
                    return

    def mouseDoubleClickEvent(self, event):
        # Double-click event
        if event.button() == Qt.MouseButton.LeftButton:
            if event.modifiers() == Qt.KeyboardModifier.NoModifier:
                p = event.scenePos()
                x, y = int(p.x()), int(p.y())
                if x >= 0 and x < self._w and y >= 0 and y < self._h:
                    self.double_click.emit(x, y)
                    return

    def mouseMoveEvent(self, event):
        # The mouse has moved!
        p = event.scenePos()
        x, y = int(p.x()), int(p.y())
        self.mouse_moved.emit(x, y)

    def resize(self, w, h):
        """ Resize the scene to match the given dimensions. """
        self._w = float(w)
        self._h = float(h)
        self.setSceneRect(0, 0, self._w, self._h)


class VideoView(QtWidgets.QGraphicsView):
    """
    Views a color data scene.
    """
    # Signals
    # The view was resized
    resize_event = QtCore.Signal()

    def __init__(self, scene):
        super().__init__(scene)
        # Disable scrollbars
        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Set rendering hints
        self.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        self.setViewportUpdateMode(
            QtWidgets.QGraphicsView.ViewportUpdateMode.BoundingRectViewportUpdate)  # noqa

        # Fit scene rect in view
        self.fitInView(self.sceneRect(), keepAspect=True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Delayed resizing
        self._resize_timer = QtCore.QTimer()
        self._resize_timer.timeout.connect(self._resize_timeout)

        # No focus (no keyboard, no border)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    def fitInView(self, rect, keepAspect=False):
        """
        For some reason, Qt has a stupid bug in it that gives the scene a
        (hardcoded) margin of 2px. To remove, this is a re-implementation of
        the fitInView method, loosely based on the original C.

        https://bugreports.qt-project.org/browse/QTBUG-11945
        """
        # Reset the view scale
        unity = self.transform().mapRect(QtCore.QRectF(0, 0, 1, 1))
        w, h = max(1, unity.width()), max(1, unity.height())
        self.scale(1. / w, 1 / h)

        # Find the ideal scaling ratio
        viewRect = self.viewport().rect()
        sceneRect = self.transform().mapRect(rect)
        xr = viewRect.width() / sceneRect.width()
        yr = viewRect.height() / sceneRect.height()
        if keepAspect:
            xr = min(xr, yr)

        # Scale and center
        self.scale(xr, yr)
        self.centerOn(rect.center())

    def resizeEvent(self, event=None):
        # Called when the view is resized.

        # Tell others a resize is happening
        # (This is used to pause the video playback)
        self.resize_event.emit()
        # Schedule delayed (and grouped) resize action
        self._resize_timer.start(100)

    def _resize_timeout(self, event=None):
        """
        Called a few ms after time out.
        """
        self._resize_timer.stop()
        self.fitInView(self.sceneRect(), keepAspect=True)


class GraphArea(QtWidgets.QWidget):
    """
    Area that can draw several graphs.
    """
    # Signals
    # Somebody moved the mouse
    # Attributes: cell x, cell y
    mouse_moved = QtCore.Signal(float, float)

    def __init__(self):
        super().__init__()
        # DataBlock 2d, and its time vector
        self._data = None
        self._time = None

        # Index (x, y, variable) of temporary graph (if any)
        self._temp_index = None
        self._temp_path = None

        # Map from indices to paths for all frozen graphs
        self._frozen = collections.OrderedDict()

        # Last variable used in temp or frozen graph: used to scale mouse y
        # coordinate
        self._last_variable = None

        # Scaling per variable
        self._scaling = {}

        # Time scaled to fit
        self._time_scaled = None
        self._tmin = 0
        self._tmax = 1
        self._trange = self._tmax - self._tmin

        # Current position in time
        self._position = self._tmin

        # Colors for drawing
        self._color_temp = Qt.GlobalColor.black
        self._color_cycle = [
            Qt.GlobalColor.red,
            #Qt.GlobalColor.green,
            Qt.GlobalColor.blue,
            #Qt.GlobalColor.cyan,
            Qt.GlobalColor.magenta,
            #Qt.GlobalColor.yellow,
            Qt.GlobalColor.darkRed,
            Qt.GlobalColor.darkGreen,
            Qt.GlobalColor.darkBlue,
            Qt.GlobalColor.darkCyan,
            Qt.GlobalColor.darkMagenta,
            Qt.GlobalColor.darkYellow,
        ]

        # Scaling factors from pixels to normalized (0, 1) coordinates. Updated
        # after every resize.
        self._sw = 1.0
        self._sh = 1.0

    def clear(self):
        """
        Removes all graphs from the widget.
        """
        self._frozen = collections.OrderedDict()
        self._scaling = {}
        self._temp_path = self._temp_index = None
        self._last_variable = None
        self.update()

    def freeze(self):
        """
        Adds the temporary graph to the set of frozen graphs.
        """
        if self._temp_index and self._temp_path:
            self._frozen[self._temp_index] = self._temp_path
        self._temp_index = self._temp_path = None
        self.update()

    def graph(self, variable, x, y):
        """
        Adds temporary graph to this widget.
        """
        if self._data is None:
            return

        # Create index, check for duplicates
        variable = self._last_variable = str(variable)
        x, y = int(x), int(y)
        index = (x, y, variable)
        if index == self._temp_index:
            return
        if index in self._frozen:
            self._temp_index = self._temp_path = None
            self.update()
            return

        # Get scaling info
        try:
            ymin, ymax = self._scaling[variable]
        except KeyError:
            data = self._data.get2d(variable)
            ymin = np.min(data)
            ymax = np.max(data)
            d = ymax - ymin
            ymin -= 0.05 * d
            ymax += 0.05 * d
            if ymin == ymax:
                ymin -= 1
                ymax += 1
            self._scaling[variable] = (ymin, ymax)

        # Create path, using real time and scaled y data
        xx = iter(self._time_scaled)
        yy = (self._data.trace(variable, x, y) - ymin) / (ymax - ymin)
        yy = iter(1 - yy)
        path = QtGui.QPainterPath()
        x, y = next(xx), next(yy)
        path.moveTo(x, y)
        for i in range(1, len(self._time)):
            x, y = next(xx), next(yy)
            path.lineTo(x, y)
        self._temp_index = index
        self._temp_path = path

        # Update!
        self.update()

    def log(self):
        """
        Returns a myokit DataLog containing the data currently displayed in the
        graph area.
        """
        d = myokit.DataLog()
        if self._data is not None:
            d['engine.time'] = self._data.time()
            for index in self._frozen.keys():
                x, y, variable = index
                d[variable, x, y] = self._data.trace(variable, x, y)
            if self._temp_index:
                x, y, variable = self._temp_index
                d[variable, x, y] = self._data.trace(variable, x, y)
        return d

    def minimumSizeHint(self):
        """
        Returns a minimum size.
        """
        return QtCore.QSize(250, 5)

    def mouseMoveEvent(self, event):
        """
        Trigger mouse moved event with graph coordinates.
        """
        if self._last_variable is None:
            return

        # Get normalized x, y coordinates ([0, 1])
        p = event.pos()
        x = float(p.x()) * self._sw
        y = 1 - float(p.y()) * self._sh

        # Scale x-axis according to time
        x = self._tmin + x * self._trange

        # Scale y-axis according to last shown variable
        ymin, ymax = self._scaling[self._last_variable]
        y = ymin + y * (ymax - ymin)

        # Emit event
        self.mouse_moved.emit(x, y)

    def paintEvent(self, event):
        """
        Draws all the graphs.
        """
        if self._data is None:
            return

        # Create painter
        painter = QtGui.QPainter()
        painter.begin(self)

        # Fill background
        painter.fillRect(self.rect(), QtGui.QBrush(Qt.GlobalColor.white))

        # Create coordinate system for graphs
        painter.scale(self.width(), self.height())
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        # Create pen
        pen = QtGui.QPen()
        pen.setWidth(0)

        # Draw frozen graphs
        colors = iter(self._color_cycle)
        for path in self._frozen.values():
            try:
                pen.setColor(next(colors))
            except StopIteration:
                colors = iter(self._color_cycle)
                pen.setColor(next(colors))
            painter.setPen(pen)
            painter.drawPath(path)

        # Draw temp graph
        if self._temp_path:
            pen.setColor(self._color_temp)
            painter.setPen(pen)
            painter.drawPath(self._temp_path)

        # Show time indicator
        pen.setColor(Qt.GlobalColor.red)
        painter.setPen(pen)
        t = (self._position - self._tmin) / self._trange
        painter.drawLine(QtCore.QLineF(t, 0, t, 1))

        # Finish
        painter.end()

    def resizeEvent(self, e=None):
        """
        Resized.
        """
        s = self.size()
        w, h = s.width(), s.height()
        self._sw = 1.0 / w if w > 0 else 1
        self._sh = 1.0 / h if h > 0 else 1

    def set_data(self, data):
        """
        Passes in the DataBlock2d this graph area extracts its data from.
        """
        self.clear()
        self._data = data
        self._time = data.time()

        self._tmin = self._time[0]
        self._tmax = self._time[-1]
        self._trange = self._tmax - self._tmin
        tpad = 0.01 * self._trange
        self._tmin -= tpad
        self._tmax += tpad
        self._trange += 2 * tpad
        self._time_scaled = (self._time - self._tmin) / self._trange

        self._position = self._tmin

    def set_position(self, pos):
        """
        Sets the position of the time indicator.
        """
        if self._data is not None:
            self._position = self._time[int(pos)]
            self.update()

    def sizeHint(self):
        """
        Returns a size suggestion.
        """
        return QtCore.QSize(250, 250)

    def sizePolicy(self):
        """
        Tells Qt that this widget shout expand.
        """
        return QtCore.QSizePolicy.Expanding


class AutoFloatField(QtWidgets.QLineEdit):
    """
    A QLineEdit that requires floats as input, but will show "(Auto)" when a
    non-float is entered and return ``None`` as its value.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        # Colors
        self._color_ok = QtGui.QTextCharFormat().foreground().color().getRgb()
        self._color_auto = (127, 127, 127)
        self._auto_text = '(Auto)'

        # Show text
        self.editingFinished.connect(self._autofy)
        self._autofy()

    def _autofy(self):
        """ Put (Auto) if not valid """
        if self.value() is None:
            self.setText(self._auto_text)
            c = self._color_auto
        else:
            c = self._color_ok
        self.setStyleSheet(f'color: rgb({c[0]}, {c[1]}, {c[2]})')

    def focusInEvent(self, event):
        super().focusInEvent(event)
        QtCore.QTimer.singleShot(0, self.selectAll)

    def value(self):
        try:
            return float(super().text())
        except ValueError:
            return None

