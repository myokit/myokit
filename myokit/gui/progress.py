#
# Progress bar for Myokit
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import myokit
from myokit.gui import Qt, QtCore, QtWidgets

# GUI components
# Constants
N = 100000000


class ProgressBar(QtWidgets.QProgressDialog):
    """
    Progress bar dialog for Myokit. Has a method :meth:`reporter()` that will
    return a :class:`myokit.ProgressReporter` for interfacing with simulations
    and other tasks implementing the ``ProgressReporter`` interface.
    """
    def __init__(self, parent, message):
        super().__init__(
            message, 'Cancel', 0, N, parent)
        self.setWindowTitle(' ')
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.setAutoClose(False)
        self.setAutoReset(False)
        self._reporter = ProgressBarReporter(self)

    def reporter(self):
        """
        Returns a :class:`ProgressReporter` for his progress bar.
        """
        return self._reporter

    def was_cancelled(self):
        """
        Pythonic version of Qt class.
        """
        return self.wasCanceled()


class ProgressBarReporter(myokit.ProgressReporter):
    """
    A :class:`myokit.ProgressReporter` that sends updates to a
    :class:`ProgressBar`. To use, create a ``ProgressBar`` and then call its
    :meth:`reporter() <ProgressBar.reporter>` method to obtain a linked
    ``ProgressBarReporter``.
    """

    def __init__(self, pd):
        super().__init__()
        self._pd = pd

    def enter(self, msg=None):
        self._pd.setEnabled(True)
        self._pd.reset()
        if msg is not None:
            self._pd.setLabelText(str(msg))
        self._pd.setValue(0)
        self._pd.repaint()
        QtWidgets.QApplication.processEvents(
            QtCore.QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)

    def exit(self):
        self._pd.setEnabled(False)

    def update(self, f):
        self._pd.setValue((int)(N * f))
        QtWidgets.QApplication.processEvents(
            QtCore.QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)
        self._pd.repaint()
        return not self._pd.wasCanceled()
