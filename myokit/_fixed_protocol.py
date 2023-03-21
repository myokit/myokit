#
# Defines the python classes that represent a fixed form pacing protocol.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals


class FixedProtocol(object):
    """
    Represents a pacing protocol as a sequence of time value pairs and an
    interpolation method (currently only linear interpolation is supported).

    A 1D time-series should be given as input. During the simulation, the value
    of the pacing variable will be determined by interpolating between the two
    nearest points in the series. If the simulation time is outside the bounds
    of the time-series, the first or last value in the series will be used.

    Protocols can be compared with ``==``, which will check if the sequence of
    time value pairs is the same, and the interpolation method is the same.
    Protocols can be serialised with ``pickle``.

    """

    def __init__(self, times, values, method=None):
        super(FixedProtocol, self).__init__()

        if len(times) != len(values):
            raise ValueError('Times and values array must have same size.')
        self._times, self._values = zip(*[
            (t, v) for t, v in sorted(zip(times, values))
        ])
        if method is None:
            method = 'linear'
        else:
            method = str(method).lower()
            if method not in ['linear']:
                raise ValueError('Unknown interpolation method: ' + method)
        self._method = method

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, FixedProtocol):
            return False
        return (
            self._times == other._times
            and self._values == other._values
            and self._method == other._method
        )

    def __getstate__(self):
        return {
            'times': self._times,
            'values': self._values,
            'method': self._method,
        }

    def clone(self):
        """
        Returns a clone of this protocol.
        """
        return FixedProtocol(self._times, self._values, self._method)

    def __setstate__(self, values):
        self._times = values['times']
        self._values = values['values']
        self._method = values['method']



