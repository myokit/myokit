#
# Contains classes for progress reporting during long operations.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import timeit

import myokit


class ProgressReporter(object):
    """
    Interface for progress updates in Simulations. Also allows some job types
    to be cancelled by the user.

    Many simulation types take an argument ``progress`` that can be used to
    pass in an object implementing this interface. The simulation will use this
    object to report on its progress.

    Note that progress reporters should be re-usable, but the behaviour when
    making calls to a reporter from two different processes (either through
    multi-threading/multi-processing or jobs nested within jobs) is undefined.

    An optional description of the job to run can be passed in at construction
    time as ``msg``.
    """
    def enter(self, msg=None):
        """
        This method will be called when the job that provides progress updates
        is started.

        An optional description of the job to run can be passed in at
        construction time as ``msg``.
        """
        pass

    def exit(self):
        """
        Called when a job is finished and the progress reports should stop.
        """
        pass

    def job(self, msg=None):
        """
        Returns a context manager that will enter and exit this
        :class:`ProgressReporter` using the ``with`` statement.
        """
        return ProgressReporter._Job(self, msg)

    def update(self, progress):
        """
        This method will be called to provides updates about the current
        progress. This is indicated using the floating point value
        ``progress``, which will have a value in the range ``[0, 1]``.

        The return value of this update can be used to signal a job should be
        cancelled: Return ``True`` to keep going, ``False`` to cancel.
        """
        pass

    class _Job(object):
        def __init__(self, parent, msg):
            self._parent = parent
            self._msg = msg

        def __enter__(self):
            self._parent.enter(self._msg)

        def __exit__(self, type, value, traceback):
            self._parent.exit()


class ProgressPrinter(ProgressReporter):
    """
    Writes progress information to stdout, can be used during a simulation.

    For example::

        m, p, x = myokit.load('example')
        s = myokit.Simulation(m, p)
        w = myokit.ProgressPrinter(digits=1)
        d = s.run(10000, progress=w)

    This will print strings like::

        [8.9 minutes] 71.7 % done, estimated 4.2 minutes remaining

    To ``stdout`` during the simulation.

    Output is only written if the new percentage done differs from the old one,
    in a string format specified by the number of ``digits`` to display. The
    ``digits`` parameter accepts the special value ``-1`` to only print out a
    status every ten percent.
    """
    def __init__(self, digits=1):
        super(ProgressPrinter, self).__init__()
        self._b = myokit.tools.Benchmarker()
        self._f = None
        self._d = int(digits)

    def enter(self, msg=None):
        # Reset
        self._b.reset()
        self._f = None

    def update(self, f):
        """
        See: :meth:`ProgressReporter.update()`.
        """
        if self._d < 0:
            f = 10 * int(10 * f)
        else:
            f = round(100 * f, self._d)
        if f != self._f:
            self._f = f
            t = self._b.time()
            if f > 0:
                p = t * (100 / f - 1)
                if p > 60:
                    p = str(round(p / 60, 1))
                    p = ', estimated ' + p + ' minutes remaining'
                else:
                    p = str(int(round(p, 0)))
                    p = ', estimated ' + p + ' seconds remaining'
            else:
                p = ''
            t = str(round(t / 60, 1))
            print('[' + t + ' minutes] ' + str(f) + ' % done' + p)
        return True


class Timeout(ProgressReporter):
    """
    Progress reporter that cancels a simulation after ``timeout`` seconds.
    """
    def __init__(self, timeout):
        super(Timeout, self).__init__()
        self._timeout = float(timeout)

    def enter(self, msg=None):
        self._max_time = timeit.default_timer() + self._timeout

    def update(self, progress):
        return timeit.default_timer() < self._max_time

