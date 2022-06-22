#
# Myokit utility functions. This module gathers functions that are used in
# Myokit, but are not particularly Myokit-dependent, i.e. they could easily be
# stand-alone. Imported by default.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import os
import re
import shutil
import stat
import sys
import tempfile
import threading
import timeit

# StringIO in Python 2 and 3
try:
    from cStringIO import StringIO
except ImportError:  # pragma: no python 2 cover
    from io import StringIO


# Natural sort regex
_natural_sort_regex = re.compile('([0-9]+)')


class Benchmarker(object):
    """
    Allows benchmarking using the with statement.

    Example::

        m,p,x = myokit.load('example')
        s = myokit.Simulation(m, p)
        b = myokit.tools.Benchmarker()
        s.run()
        print(b.time())
        b.reset()
        s.run()
        print(b.time())

    """
    def __init__(self):
        self._start = timeit.default_timer()
        self._last_print = self._start

    def format(self, time=None):
        """
        Formats a (non-integer) number of seconds, returns a string like
        "5 weeks, 3 days, 1 hour, 4 minutes, 9 seconds", or "0.0019 seconds".

        If no ``time`` is passed in, the value from :meth:`time()` is used.
        """
        if time is None:
            time = self.time()
        if time < 60:
            return '1 second' if time == 1 else str(time) + ' seconds'
        output = []
        time = int(round(time))
        units = [
            (604800, 'week'),
            (86400, 'day'),
            (3600, 'hour'),
            (60, 'minute'),
        ]
        for k, name in units:
            f = time // k
            if f > 0 or output:
                output.append(str(f) + ' ' + (name if f == 1 else name + 's'))
            time -= f * k
        output.append('1 second' if time == 1 else str(time) + ' seconds')
        return ', '.join(output)

    def print(self, message):
        """
        Prints a message to stdout, preceded by the benchmarker time in us.
        """
        now = timeit.default_timer()
        tot = int(1e6 * (now - self._start))
        new = int(1e6 * (now - self._last_print))
        self._last_print = now
        print('[{:10d} us ({:5d} us)] '.format(tot, new) + str(message))

    def reset(self):
        """ Resets this timer's start time. """
        self._start = timeit.default_timer()

    def time(self):
        """
        Returns the time since benchmarking started (as a float, in seconds).
        """
        return timeit.default_timer() - self._start


class capture(object):
    """
    Context manager that temporarily redirects the current standard output and
    error streams, and captures anything that's written to them.

    Example::

        with myokit.tools.capture() as a:
            print('This will be captured')

    Within a single thread, captures can be nested, for example::

        with myokit.tools.capture() as a:
            print('This will be captured by a')
            with myokit.tools.capture() as b:
                print('This will be captured by b, not a')
            print('This will be captured by a again')

    Capturing is thread-safe: a lock is used to ensure only a single thread is
    capturing at any time. For example, if we have a function::

        def f(i):
            with myokit.tools.capture() as a:
                print(i)
                ...

            return a.text()

    and this is called from several threads, the ``capture`` acts as a lock (a
    ``threading.RLock``) so that one thread will need to finish executing the
    code within the ``with`` statement before a second thread can start
    capturing.

    In multiprocessing, no locks are used, and no memory or streams are shared
    so that this should also be safe.

    By default, this method works by simply redirecting ``sys.stdout`` and
    ``sys.stderr``. This captures any output written by the Python interpreter,
    but does not catch output from C/C++ extensions or subrocesses. To also
    catch that output start the capture with the optional argument
    ``fd=True``, which enables a file descriptor duplication method of
    redirection.

    To easily switch capturing on/off, a switch ``enabled=False`` can be passed
    in to create a context manager that doesn't do anything.
    """
    # Note: It seems we need to capture both streams to make the file
    # descriptor method work, and we want both anyway throughout Myokit, so
    # there are no options to choose stdout or stderr here.

    # Lock to stop other threads from capturing while this thread is capturing.
    _rlock = threading.RLock()

    def __init__(self, fd=False, enabled=True):

        # Are we already capturing? This is needed in case someone enters the
        # same context twice.
        self._active_count = 0

        # Captured text
        self._txt_out = None
        self._txt_err = None

        # Capturing mode
        self._fd = bool(fd)

        # Shared by both modes
        self._org_out = None     # Original stdout object
        self._org_err = None     # Original stderr object

        # Python stream redirects only
        self._tmp_out = None    # Temporary stdout StringIO object
        self._tmp_err = None    # Temporary stderr StringIO object

        # File descriptor redirects only
        self._out_fd = None      # File descriptor used for output
        self._err_fd = None      # File descriptor used for errors
        self._org_out_fd = None  # Back-up of original stdout file descriptor
        self._org_err_fd = None  # Back-up of original stderr file descriptor
        self._file_out = None    # Temporary file to write output to
        self._file_err = None    # Temporary file to write errors to

        # Capturing enabled
        self._enabled = bool(enabled)

    def __enter__(self):
        """Called when the context is entered."""
        if not self._enabled:
            return self

        # Avoid entering the same context object twice
        self._active_count += 1
        if self._active_count == 1:

            # Wait until other threads have stopped capturing
            capture._rlock.acquire()

            # Set up redirection
            self._start()

        # Return context
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Called when exiting the context."""
        if not self._enabled:
            return

        self._active_count -= 1
        if self._active_count == 0:
            self._stop()
            capture._rlock.release()

    def _start(self):
        """Starts capturing output to stdout and stderr."""

        # Clear any cached text
        self._txt_out = None
        self._txt_err = None

        # Save the current output / error streams
        self._org_out = sys.stdout
        self._org_err = sys.stderr

        # Redirect
        if not self._fd:
            # Create temporary output and error streams
            self._tmp_out = StringIO()
            self._tmp_err = StringIO()

            # Redirect, attempting to flush first
            try:
                sys.stdout.flush()
            except AttributeError:  # pragma: no cover
                pass
            finally:
                sys.stdout = self._tmp_out

            try:
                sys.stderr.flush()
            except AttributeError:  # pragma: no cover
                pass
            finally:
                sys.stderr = self._tmp_err

        else:
            # File-descriptor redirection

            # Get file descriptors used for output and errors.
            #
            # These represent open files, and are the low-level equivalent of
            # sys.stdout and sys.stderr: all subprocesses etc. use these
            # descriptors to write output to.
            #
            # Note that we get these file descriptors from __stdout__ and
            # __stderr__, to get the original streams that subprocesses etc.
            # will use, even if someone has redirected the Python-level
            # streams.
            #
            # On https://docs.python.org/3/library/sys.html#module-sys, it says
            # that stdout/err as well as __stdout__ can be None (e.g. in spyder
            # on windows).  In other cases (pythonw.exe) they can be set but
            # return a negative file descriptor (indicating it's invalid).
            # So here we check if __stdout__ is None and if so set a negative
            # fileno so that we can catch both cases at once in the rest of the
            # code.
            #
            if sys.__stdout__ is not None:
                self._out_fd = sys.__stdout__.fileno()
            else:   # pragma: no cover
                self._out_fd = -1
            if sys.__stderr__ is not None:
                self._err_fd = sys.__stderr__.fileno()
            else:   # pragma: no cover
                self._err_fd = -1

            # We start by making a copy of these file descriptors using dup(),
            # meaning that two file numbers will point to the same file. In a
            # later step we use dup2() to write a different value into the
            # descriptor, so that all output gets redirected. When exiting, we
            # will use dup2() again to copy the original value back in.
            #
            # We check if the fd >= 0 first, because the previous code could
            # get a negative (invalid) value either when __stdxxx__ is None or
            # when a negative value is returned.
            #
            # On windows, the order is important: First dup both stdout and
            # stderr, then dup2 the new descriptors in. This prevents a weird
            # infinite recursion on windows ipython / python shell.
            #
            if self._out_fd >= 0:
                self._org_out_fd = os.dup(self._out_fd)
            if self._err_fd >= 0:
                self._org_err_fd = os.dup(self._err_fd)

            # Create temporary files to redirect the output to. Make sure they
            # aren't opened in binary mode, and specify + for reading and
            # writing.
            self._file_out = tempfile.TemporaryFile(mode='w+')
            self._file_err = tempfile.TemporaryFile(mode='w+')

            # Apply Python-level redirection of sys.stdxxx in addition to the
            # lower-level redirect of sys.__stdxxx___.
            try:
                sys.stdout.flush()
            except AttributeError:  # pragma: no cover
                pass
            finally:
                sys.stdout = self._file_out
            try:
                sys.stderr.flush()
            except AttributeError:  # pragma: no cover
                pass
            finally:
                sys.stderr = self._file_err

            # If possible, overwrite the stdout and stderr file descriptors
            # with the file descriptor for our files. C/C++ code etc. will
            # still look in this location for a descriptor, so that output is
            # redirected.
            if self._out_fd >= 0:
                sys.__stdout__.flush()
                os.dup2(self._file_out.fileno(), self._out_fd)
            if self._err_fd >= 0:
                sys.__stderr__.flush()
                os.dup2(self._file_err.fileno(), self._err_fd)

    def _stop(self):
        """Stops capturing output."""

        # Flush any remaining output
        sys.stdout.flush()
        sys.stderr.flush()

        # Undo redirect
        if not self._fd:
            # Direct back at original
            sys.stdout = self._org_out
            sys.stderr = self._org_err

            # Store text
            self._txt_out = self._tmp_out.getvalue()
            self._txt_err = self._tmp_err.getvalue()

            # Tidy
            self._tmp_out = self._tmp_err = None

        else:
            # Undo redirection
            sys.stdout = self._org_out
            if self._org_out_fd is not None:
                # Copy our backup of the original fd into out_fd
                os.dup2(self._org_out_fd, self._out_fd)
                # And close our backup
                os.close(self._org_out_fd)

            sys.stderr = self._org_err
            if self._org_err_fd is not None:
                os.dup2(self._org_err_fd, self._err_fd)
                os.close(self._org_err_fd)

            # Close temporary files and store capture output
            try:
                self._file_out.seek(0)
                self._txt_out = self._file_out.read()
                self._file_out.close()
            except ValueError:  # pragma: no cover
                # In rare cases, I've seen a ValueError, "underlying buffer has
                # been detached".
                pass
            try:
                self._file_err.seek(0)
                self._txt_err = self._file_err.read()
                self._file_err.close()
            except ValueError:  # pragma: no cover
                pass

            # Tidy
            self._out_fd = self._err_fd = None
            self._org_out_fd = self._org_err_fd = None
            self._file_out = self._file_err = None

        # Unset reference to original streams (for proper decreffing etc.)
        self._stdout = self._stderr = None

    def err(self):
        """
        Returns the text captured from stderr, or an empty string if nothing
        was captured or capturing is still active.
        """
        if self._txt_err is None:
            return ''
        text = self._txt_err

        # In Python 2, the text needs to be decoded from ascii
        if sys.hexversion < 0x03000000:  # pragma: no python 3 cover
            text = text.decode('ascii', 'ignore')

        return text

    def out(self):
        """
        Returns the text captured from stdout, or an empty string if nothing
        was captured or capturing is still active.
        """
        if self._txt_out is None:
            return ''
        text = self._txt_out

        # In Python 2, the text needs to be decoded from ascii
        if sys.hexversion < 0x03000000:  # pragma: no python 3 cover
            text = text.decode('ascii', 'ignore')

        return text

    def text(self):
        """
        Returns the combined text captured from output and error text, if any
        (output first, then error text).
        """
        return self.out() + self.err()


def format_path(path, root='.'):
    """
    Formats a path for use in user messages. If the given path is a
    subdirectory of the current directory this part is chopped off.

    Alternatively, a ``root`` directory may be given explicitly: any
    subdirectory of this path will be formatted relative to ``root``.

    This function differs from os.path.relpath() in the way it handles paths
    *outside* the root: In these cases relpath returns a relative path such as
    '../../' while this function returns an absolute path.
    """
    if path == '':
        path = '.'
    try:
        path = os.path.relpath(path, root)
    except ValueError:  # pragma: no cover
        # This can happen on windows, if `path` is on a different drive than
        # root (so that no relative path from one to the other can be made).
        return path

    if '..' in path:
        path = os.path.abspath(os.path.join(root, path))
    return path


def lvsd(s, t):
    """Returns the Levenshtein distance between two strings ``s`` and ``t``."""
    # This implementation is adapted from wikipedia:
    # en.wikipedia.org/wiki/Levenshtein_distance#Iterative_with_full_matrix
    if s == t:
        return 0
    if len(s) == 0:
        return len(t)
    if len(t) == 0:
        return len(s)

    n = len(t) + 1
    v0 = list(range(n))
    v1 = [None] * n
    for i, si in enumerate(s):
        v1[0] = i + 1
        for j, tj in enumerate(t):
            v1[j + 1] = min(
                v0[j + 1] + 1, v1[j] + 1, v0[j] if si == tj else v0[j] + 1)
        v0, v1 = v1, v0
    return v0[n - 1]


def natural_sort_key(s):
    """
    Function to use as ``key`` in a sort, to get natural sorting of strings
    (e.g. "2" before "10").

    Usage examples::

        names.sort(key=myokit.tools.natural_sort_key)

        variables.sort(key=lambda v: myokit.tools.natural_sort_key(v.qname()))

    """
    # Code adapted from: http://stackoverflow.com/questions/4836710/
    return [
        int(text) if text.isdigit() else text.lower()
        for text in _natural_sort_regex.split(s)]


def rmtree(path, silent=False):
    """
    Version of ``shutil.rmtree`` that handles Windows "access denied" errors
    (when the user is lacking write permissions, but is allowed to set them).

    If ``silent=True`` any other exceptions will be caught and ignored.
    """
    # From https://stackoverflow.com/questions/2656322
    def onerror(function, path, excinfo):   # pragma: no cover
        if not os.access(path, os.W_OK):
            # Give user write permissions (remove read-only flag)
            os.chmod(path, stat.S_IWUSR)
            function(path)
        else:
            raise

    if silent:
        try:
            shutil.rmtree(path, ignore_errors=False, onerror=onerror)
        except Exception:
            pass
    else:
        shutil.rmtree(path, ignore_errors=False, onerror=onerror)

