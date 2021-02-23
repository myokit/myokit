#!/usr/bin/env python3
import myokit
import numpy as np
import matplotlib.pyplot as plt

m, p, _ = myokit.load('test.mmt')

# Run simulation
b = myokit.Benchmarker()
s = myokit.Simulation(m, p)
b.reset()
d = s.run(1000)
print(b.time())

plt.figure()
plt.plot(d.time(), d['membrane.V'])
plt.show()

