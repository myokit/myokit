#!/usr/bin/env python3
import myokit
import matplotlib.pyplot as plt
import numpy as np

m, p, _ = myokit.load('test.mmt')

#myokit.DEBUG = True

print('Legacy')
b = myokit.Benchmarker()
s = myokit.LegacySimulation(m, p)
print(b.time())
b.reset()
d = s.run(1000)
print(b.time())

print('CVODES')
b = myokit.Benchmarker()
s = myokit.Simulation(m, p)
print(b.time())
b.reset()
e = s.run(1000)
print(b.time())



plt.figure()
plt.plot(d['engine.time'], d['membrane.V'], label='Legacy')
plt.plot(e['engine.time'], e['membrane.V'], '--', label='CVODES')
plt.show()
