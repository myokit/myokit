#
# Creates common graphs
# Uses matplotlib
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import numpy as np
# Don't import pyplot yet, this will cause a crash if no window environment
# is loaded.


def simulation_times(
        time=None, realtime=None, evaluations=None, mode='stair', axes=None,
        nbuckets=50, label=None):
    """
    Draws a graph of step sizes used during a simulation.

    Data can be passed in as ``time`` (simulation time) ``realtime``
    (benchmarked time during the simulation) and ``evaluations`` (the number
    of evaluations needed for each step). Which of these fields are required
    dependens on the chosen plot ``mode``:

    ``stair``
        Draws ``time`` on the x-axis, and the step number on the y-axis.
        In this plot, a high slope means the integrator is taking lots of
        steps.
    ``stair_inverse``
        Draws ``time`` on the y-axis, and the step number on the x-axis.
    ``load``
        Draws ``time`` on the x-axis, and log(1 / step size) on the y-axis.
        In this plot, high values on the y-axis should be found near difficult
        times on the x-axis
    ``histo``
        Lumps ``time`` into buckets (whose number can be specified using the
        argument ``nbuckets``) and counts the number of steps in each bucket.
        In the final result, the times corresponding to the buckets are plotted
        on the x axis and the number of evaluations in each bucket is plotted
        on the y axis.
    ``time_per_step``
        Uses the ``realtime`` argument to calculate the time taken to advance
        the solution each step.
        In the resulting plot, the step count is plotted on the x-axis, while
        the y-axis shows the time spent at this point.
    ``eval_per_step``
        Uses the ``evaluations`` entry to calculate the number of rhs
        evaluations required for each step.
        In the resulting plot, the step number is plotted on the x-axis, and
        the number of rhs evaluations for each step is plotted on the y-axis.

    The argument ``axes`` can be used to pass in a matplotlib axes object to be
    used for the plot. If none are given, the current axes obtained from
    ``pyplot.gca()`` are used.

    Returns a matplotlib axes object.
    """
    import matplotlib.pyplot as plt
    if axes is None:
        axes = plt.gca()

    def stair(ax, time, realtime, evaluations):
        if time is None:
            raise ValueError('This plotting mode requires "time" to be set.')
        time = np.array(time, copy=False)
        step = np.arange(0, len(time))
        ax.step(time, step, label=label)

    def stair_inverse(ax, time, realtime, evaluations):
        if time is None:
            raise ValueError('This plotting mode requires "time" to be set.')
        time = np.array(time, copy=False)
        step = np.arange(0, len(time))
        ax.step(step, time, label=label)

    def load(ax, time, realtime, evaluations):
        if time is None:
            raise ValueError('This plotting mode requires "time" to be set.')
        time = np.array(time, copy=False)
        size = np.log(1 / (time[1:] - time[:-1]))
        ax.step(time[1:], size, label=label)

    def histo(ax, time, realtime, evaluations):
        if time is None:
            raise ValueError('This plotting mode requires "time" to be set.')
        time = np.array(time, copy=False)
        zero = float(time[0])
        bucket_w = (time[-1] - zero) / nbuckets
        bucket_x = np.zeros(nbuckets)
        bucket_y = np.zeros(nbuckets)
        hi = zero
        for k in range(nbuckets):
            lo = hi
            hi = zero + (k + 1) * bucket_w
            bucket_x[k] = lo
            bucket_y[k] = np.sum((lo < time) * (time <= hi))
        bucket_y[0] += 1  # First bucket contains point lo == time
        ax.step(bucket_x, bucket_y, where='post', label=label)

    def time_per_step(ax, time, realtime, evaluations):
        if realtime is None:
            raise ValueError(
                'This plotting mode requires "realtime" to be set.')
        real = np.array(realtime)
        real = real[1:] - real[:-1]
        step = np.arange(1, 1 + len(real))
        ax.step(step, real, where='mid', label=label)

    def eval_per_step(ax, time, realtime, evaluations):
        if evaluations is None:
            raise ValueError(
                'This plotting mode requires "evaluations" to be set.')
        evls = np.array(evaluations)
        evls = evls[1:] - evls[:-1]
        step = np.arange(1, 1 + len(evls))
        ax.step(step, evls, where='mid', label=label)

    modes = {
        'stair': stair,
        'stair_inverse': stair_inverse,
        'load': load,
        'histo': histo,
        'time_per_step': time_per_step,
        'eval_per_step': eval_per_step,
    }

    try:
        fn = modes[mode]
    except KeyError:
        raise ValueError(
            'Selected mode not found. Avaiable modes are: '
            + ', '.join(['"' + x + '"' for x in modes.keys()]))
    return fn(axes, time, realtime, evaluations)


def current_arrows(log, voltage, currents, axes=None):
    """
    Draws a graph of voltage versus time with arrows to indicate which currents
    are active at which stage of the action potential.

    The argument, ``log`` should be a:class:`myokit.DataLog` containing
    the data needed for the plot. The argument ``voltage`` should be the key in
    ``log`` that maps to the membrane potential.

    The list ``currents`` should contain all keys of currents to display.

    Returns a matplotlib axes object.
    """
    import matplotlib.pyplot as plt

    # Get currents, normalize with respect to total current at each time
    log = log.npview()
    traces = [log[x] for x in currents]
    times = log.time()
    memv = log[voltage]

    # Get sum of _absolute_ traces!
    I_total = np.zeros(len(traces[0]))
    for I in traces:
        I_total += abs(I)

    # Create axes
    ax = axes if axes is not None else plt.gca()

    # Plot membrane potential
    ax.plot(times, memv)
    ax.set_title(voltage)

    # Get width of time steps
    steps = np.concatenate((times[0:1], times, times[-1:]))
    steps = 0.5 * steps[2:] - 0.5 * steps[0:-2]

    # Find "zero" points, points of interest
    threshold_abs = 0.1
    for ii, I in enumerate(traces):

        # Capture parts where abs(I) is greather than the threshold and the
        # sign doesn't change
        parts = []
        indices = None
        sign = (I[0] >= 0)
        for k, i in enumerate(I):
            if abs(i) < threshold_abs or sign != (i >= 0):
                # Do nothing
                if indices is not None:
                    parts.append(indices)
                    indices = None
            else:
                # Store indices
                if indices is None:
                    indices = []
                indices.append(k)
            sign = (i >= 0)
        if indices is not None:
            parts.append(indices)

        # For each part, calculate
        #  the weighted midpoint in time
        #  the total charge transferred
        #  the average current
        #  the peak current
        #  the total charge transferred / the total sum charge transferred in
        #  that same time. This last measure can be used as a secondary
        #  threshold
        for part in parts:
            q_total = 0     # Sum of charge transferred
            t_total = 0     # Total time elapsed
            s_total = 0     # Sum of all currents in this time frame
            i_peak = 0      # Max absolute current
            t_mid = 0       # Weighted midpoint in time
            for k in part:
                t_total += steps[k]
                q_total += steps[k] * I[k]
                s_total += steps[k] * I_total[k]
                t_mid += steps[k] * I[k] * times[k]
                i_peak = max(i_peak, abs(I[k]))

            # Weighted midpoint in time (weight is height * width)
            t_mid /= q_total

            # Add sign to peak current
            if sum(I) < 0:
                i_peak *= -1.0

            # Add arrow
            k = np.nonzero(times >= t_mid)[0][0]
            ars = 'rarrow'
            arx = t_mid
            if k + 1 == len(times):
                # Massive current at final point, bit weird but should handle
                # this case...
                ary = memv[k]
                arr = 0
            else:
                t1 = times[k]
                t2 = times[k + 1]
                ary = (
                    (memv[k] * (t2 - t_mid) + memv[k + 1] * (t_mid - t1))
                    / (t2 - t1))
                arr = np.arctan2(t1 - t2, memv[k + 1] - memv[k]) * 180 / np.pi
                if sum(I) > 0:
                    arr += 180
                if abs(arr) > 90:
                    arr = 180 + arr
                    ars = 'larrow'

            bbox_props = dict(
                boxstyle=ars + ',pad=0.3',
                fc='w',
                ec='black',
                lw=1)

            ax.annotate(
                currents[ii],
                xy=(arx, ary),
                ha='center',
                va='center',
                rotation=arr,
                size=14,
                bbox=bbox_props)
    return ax


def cumulative_current(
        log, currents, axes=None, labels=None, colors=None, integrate=False,
        normalise=False, max_currents=None, line_args={}, fill_args={}):
    """
    Plots a number of currents, one on top of the other, with the positive and
    negative parts of the current plotted separately.

    The advantage of this type of plot is that it shows the relative size of
    each current versus the others, and gives an indication of the total
    positive and negative current in a model.

    Accepts the following arguments:

    ``log``
        A:class:`myokit.DataLog` containing all the data to plot.
    ``currents``
        A list of keys, where each key corresponds to a current stored in
        ``log``.
    ``axes``
        The matplotlib axes to create the plot on.
    ``labels``
        Can be used to pass in a list containing the label to set for each
        current.
    ``colors``
        Can be used to pass in a list containing the colors to set for each
        current.
    ``integrate``
        Set this to ``True`` to plot total carried charge instead of currents.
    ``normalise``
        Set this to ``True`` to normalise the graph at every point, so that the
        relative contribution of each current is shown.
    ``max_currents``
        Set this to any integer n to display only the first n currents, and
        group the rest together in a remainder current.
    ``line_args``
        An optional dict with keyword arguments to pass in when drawing lines.
    ``fill_args``
        An optional dict with keyword arguments to pass in when drawing shaded
        areas.

    The best results are obtained if relatively constant currents are specified
    early. Another rule of thumb is to specify the currents roughly in the
    order they appear during an AP.
    """
    import matplotlib
    import matplotlib.pyplot as plt

    # Get axes
    if axes is None:
        axes = plt.gca()

    # Get numpy version of log
    log = log.npview()

    # Get time
    t = log.time()

    # Get currents or charges
    if integrate:
        pos = np.array([log.integrate(c) for c in currents])
    else:
        pos = np.array([log[c] for c in currents])

    # Split positive and negative
    neg = np.minimum(pos, 0)
    pos = np.maximum(pos, 0)

    # Normalise
    if normalise:
        pos /= np.maximum(np.sum(pos, axis=0), 1e-99)
        neg /= -np.minimum(np.sum(neg, axis=0), -1e-99)

    # Number of currents to show
    nc = len(currents)
    if max_currents is None or max_currents + 1 >= nc:
        show_remainder = False
    else:
        show_remainder = True
        max_currents = int(max_currents)
        nc = 1 + max_currents

    # Colors
    if colors:
        while len(colors) < nc:
            colors.extend(colors)
    else:
        # Colormap
        cmap = matplotlib.cm.get_cmap(name='tab20')
        colors = [cmap(i) for i in range(nc)]

    # Line drawing keyword arguments
    if 'color' not in line_args:
        line_args['color'] = 'k'
    if 'lw' not in line_args:
        line_args['lw'] = 1

    # Plot
    op = on = 0
    for k in range(nc):
        if k == max_currents:
            # Color and label for remainder
            color = '#cccccc'
            label = 'Remainder'

            # Positive and negative remainder parts
            p = op + np.sum(pos[k:], axis=0)
            n = on + np.sum(neg[k:], axis=0)

        else:
            # Get color
            color = colors[k]

            # Get label
            if labels:
                label = labels[k]
            else:
                c = currents[k]
                if integrate:
                    label = 'Q(' + c[c.find('.') + 1:] + ')'
                else:
                    label = c[c.find('.') + 1:]

            # Get positive and negative parts
            p, n = op + pos[k], on + neg[k]

        # Plot!
        axes.fill_between(t, p, op, facecolor=color, label=label, **fill_args)
        axes.fill_between(t, n, on, facecolor=color, **fill_args)
        axes.plot(t, p, **line_args)
        axes.plot(t, n, **line_args)
        on = n
        op = p
