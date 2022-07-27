#!/usr/bin/env python3
#
# This script is used to check if the C extensions are leaking any Python
# objects; i.e. if they are creating new references to Python objects that are
# not decref'd.
#
# The output of this method should show a few iterations (usually 2) where the
# number of objects increases, but then things should stabilise so that the
# output is:
#
#     types |   # objects |   total size
#   ======= | =========== | ============
#
# A leaked object would look something like this:
#
#     types |   # objects |   total size
#   ======= | =========== | ============
#      list |           1 |     88     B
#
# This script requires pympler to be installed (e.g. with pip).
#
# Note (2022-07-27): This only works for objects that Pympler can track. This
# is (1) all objects tracked by gc, and (2) all objects referenced by those
# objects. This means that things not tracked by gc or referenced by some
# object can leak without this script detecting it.
# For a list of non gc tracked:
#   https://docs.python.org/3/library/gc.html#gc.is_tracked
# For example, if I add this to the simulation it gets picked up:
#   PyList_New(123);
# but this does not:
#   PyFloat_FromDouble(1.2);
#
import myokit
import pympler.tracker


def test(command, repeats=10, name=None):
    """
    Tests a method created by calling ``c(*args)``.
    """
    tracker = pympler.tracker.SummaryTracker()
    for _ in range(repeats):
        command()
        tracker.print_diff()
        print()


def simulation(name='plain'):
    # Load model and protocol
    m, p, _ = myokit.load('example')

    sens = (
        ('ina.m', 'dot(ina.m)', 'ina.INa'),
        ('ina.gNa', 'init(ina.m)')
    )

    if name == 'plain':
        s = myokit.Simulation(m, p)

        def c():
            s.run(100)

    elif name == 'sens':
        s = myokit.Simulation(m, p, sens)

        def c():
            s.run(100)

    elif name == 'realtime':
        # Realtime tracking
        # Note: This doesn't show much: Python re-uses strings etc. so can
        # delete some decrefs without seeing it here!
        v = m.get('engine').add_variable('realtime')
        v.set_rhs(0)
        v.set_binding('realtime')
        s = myokit.Simulation(m, p)

        def c():
            s.run(100)

    elif name == 'apd':
        # APD measuring
        # Note: Can remove some decrefs without seeing results here...
        s = myokit.Simulation(m, p)

        def c():
            s.run(1000, apd_variable='membrane.V', apd_threshold=-1)

    elif name == 'log_times':
        # Point-list logging
        s = myokit.Simulation(m, p, sens)
        lt = list(range(0, 1000, 10))

        def c():
            s.reset()
            s.run(1000, log_times=lt)

    elif name == 'log_times_np':
        # Point-list logging
        s = myokit.Simulation(m, p, sens)
        import numpy as np
        lt = np.arange(0, 1000, 10)

        def c():
            s.reset()
            s.run(1000, log_times=lt)

    else:
        raise ValueError(f'Unknown test: simulation {name}')

    print(f'Testing simulation: {name}')
    test(c)


# Test a simulation method
#simulation()
#simulation('sens')
#simulation('realtime')
#simulation('apd')
#simulation('log_times')
simulation('log_times_np')

