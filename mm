#!/usr/bin/env python3
import myokit
import numpy as np
import matplotlib.pyplot as plt

m, p, _ = myokit.load('~/dev/models/tentusscher-2006.mmt')

#log_settings = {}
log_settings = {
    'log': myokit.LOG_BOUND+myokit.LOG_STATE,
    'log_interval': 1,
}

# Run simulation
b = myokit.Benchmarker()
s = myokit.Simulation(m, p)
b.reset()
d = s.run(1000 * 1000, **log_settings)
print(b.time())

b = myokit.Benchmarker()
s = myokit.LegacySimulation(m, p)
b.reset()
d = s.run(1000 * 1000, **log_settings)
print(b.time())

