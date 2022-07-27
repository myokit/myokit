#!/usr/bin/env python3
#
# This script is intended to show increases in memory* that occur when a
# simulation is run.
# Although this is intended to monitor the C extensions, there are various
# reasons why Python might increase its usage, so care needs to be taken when
# interpreting the results.
#
# *More specifically, in "resident set size":
# https://en.wikipedia.org/wiki/Resident_set_size
#
import gc
import resource

import numpy as np

import myokit


def test(c, *args, warmup=10, repeats=1000, duration=20, name=None, log=False,
         log_times=None):
    """
    Tests a method created by calling ``c(*args)``.
    """
    if name is None:
        name = c.__name__

    print(f'Testing {name} ... ', end='')

    log = None if log else myokit.LOG_NONE

    s = c(*args)
    for i in range(warmup):
        s.run(duration, log=log)
        s.reset()

    increases = 0
    us = [0] * repeats
    for i in range(repeats):
        u1 = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        s.run(duration, log=log, log_times=log_times)
        u2 = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if u2 > u1:
            increases += 1
        us[i] = u2
        s.reset()
    del(s)

    d = us[-1] - us[0]
    if increases > 1 and repeats > 1:
        print(f'[failed with {d} kb and {increases} increases]')
    elif d:
        print(f'[ok? {d} kb in a single increase ({repeats} repeats)')
    else:
        print('[ok]')

    if d:
        print('Running gc')
        n = gc.collect()
        u2 = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        us.append(u2)
        print('Collected objects:', n)
        print('Uncollectable:', gc.garbage)

        import matplotlib.pyplot as plt
        plt.figure()
        plt.xlabel('Run')
        plt.ylabel('Memory usage (kB)')
        plt.plot(us)
        plt.show()

    return int(d > 0)


# Load model and protocol
m = myokit.load_model('example')
#p = myokit.load_protocol('example')
p = myokit.pacing.blocktrain(500, 0.5, offset=0.1)

# Shortcut to Fiber Tissue, for one-line commenting when debugging
ft = myokit.FiberTissueSimulation

# Sensitivities
sens = (
    ('ina.m', 'dot(ina.m)', 'ina.INa'),
    ('ina.gNa', 'init(ina.m)')
)

sens2 = [v for v in m.variables(const=True) if v.is_literal()]
sens2 = (m.states(), sens2)

# Test all simulation methods
lt = np.linspace(0, 20, 1000)
c = 0
#c += test(myokit.Simulation, m, p, repeats=300, duration=20)
#c += test(myokit.Simulation, m, p, repeats=300, duration=20, log=True)
c += test(myokit.Simulation, m, p, repeats=300, duration=20, log=True, log_times=lt)  # noqa
#c += test(myokit.Simulation, m, p, sens, name='Sensitivities 1')
#c += test(myokit.Simulation, m, p, sens2, duration=1, name='Sensitivities 2')
#c += test(myokit.LegacySimulation, m, p, name='Legacy simulation')
#c += test(myokit.Simulation1d, m, p, duration=1)
#c += test(myokit.SimulationOpenCL, m, p, 5, duration=1, repeats=10)
#c += test(ft, m, m, p, (5, 2), (5, 5), duration=1, repeats=2)
# Skipping deprecated PSimulation and ICSimulation

