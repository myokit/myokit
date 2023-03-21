#
# Defines the python classes that represent a fixed form pacing protocol.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals
from __future__ import annotations
from bisect import bisect_left
from typing import List


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
        times_tpl, values_tpl = zip(*[
            (float(t), float(v)) for t, v in sorted(zip(times, values))
        ])
        self._times = list(times_tpl)
        self._values = list(values_tpl)
        if method is None:
            method = 'linear'
        else:
            method = str(method).lower()
            if method not in ['linear']:
                raise ValueError('Unknown interpolation method: ' + method)
        self._method = method

    def times(self) -> List[float]:
        """
        Returns a list of the times in this protocol.
        """
        return self._times

    def values(self) -> List[float]:
        """
        Returns a list of the values in this protocol.
        """
        return self._values

    def pace(self, t: float) -> float:
        """
        Returns the value of the pacing variable at time ``t``.
        """
        if t < self._times[0]:
            return self._values[0]
        if t > self._times[-1]:
            return self._values[-1]
        i = bisect_left(self._times, t) - 1
        return self._values[i] + (t - self._times[i]) * (
            self._values[i + 1] - self._values[i]
        ) / (self._times[i + 1] - self._times[i])

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

    def clone(self) -> FixedProtocol:
        """
        Returns a clone of this protocol.
        """
        return FixedProtocol(self._times, self._values, self._method)

    def __setstate__(self, values):
        self._times = values['times']
        self._values = values['values']
        self._method = values['method']



