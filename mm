#!/usr/bin/env python3
import myokit
import numpy as np
import matplotlib.pyplot as plt

m, p, _ = myokit.load('~/dev/models/tentusscher-2006.mmt')

easy = True

if easy:
    settings = {
        'log': myokit.LOG_NONE,
    }
    max_time_step = None
    #max_time_step = 0.5
else:
    settings = {
        'log': myokit.LOG_BOUND+myokit.LOG_STATE,
        'log_interval': 1,
    }
    max_time_step = 0.5

# Run simulation
s = myokit.Simulation(m, p)
s.set_max_step_size(max_time_step)
b = myokit.Benchmarker()
d = s.run(1000 * 1000, **settings)
print(b.time())

s = myokit.LegacySimulation(m, p)
s.set_max_step_size(max_time_step)
b = myokit.Benchmarker()
d = s.run(1000 * 1000, **settings)
print(b.time())

