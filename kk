#!/usr/bin/env python3
import myokit
import numpy as np
import matplotlib.pyplot as plt

m, p, _ = myokit.load('test.mmt')

# Run simulations
print('Creating CVODES sim')
b = myokit.Benchmarker()
sensitivities=(
    ['membrane.V', 'ina.INa'],
    ['ina.gNa', 'init(ica.Ca_i)', 'ica.gCa']
)
s = myokit.Simulation(m, p, sensitivities)
print(b.time())

print('running')
b.reset()
d3, e3 = s.run(1000)
e3 = np.array(e3)
print(b.time())
print(e3.shape)

print('Creating P and IC sims')
b.reset()
s1 = myokit.PSimulation(m, p,
    variables=['membrane.V', 'ina.INa'],
    parameters=['ina.gNa', 'ica.gCa'])
s2 = myokit.ICSimulation(m, p)
print(b.time())

print('running')
b.reset()
s1.set_step_size(0.001)
s2.set_step_size(0.001)
d1, e1 = s1.run(1000, log_interval=0.01)
d2, e2 = s2.run(1000, log_interval=0.01)
print(b.time())

print(e1.shape)
print(e2.shape)

# Run a new simulation

print(b.time())

# Plot the results
plt.figure()
plt.subplot(3, 1, 1)
plt.plot(d1.time(), d1['membrane.V'], label='Euler')
plt.plot(d3.time(), d3['membrane.V'], label='CVODES')
plt.subplot(3, 3, 4)
plt.plot(d1.time(), e1[:, 0, 0], label='dV/dgNa')
plt.plot(d3.time(), e3[:, 0, 0], '--', label='CVODES')
plt.legend()
plt.subplot(3, 3, 5)
plt.plot(d1.time(), e1[:, 0, 1], label='dV/dgCa')
plt.plot(d3.time(), e3[:, 0, 2], '--', label='CVODES')
plt.legend()
plt.subplot(3, 3, 6)
plt.plot(d2.time(), e2[:, 0, 7], label='dV/dCai0')
plt.plot(d3.time(), e3[:, 0, 1], '--', label='CVODES')
print(np.min(e3[:, 0, 2]))
print(np.max(e3[:, 0, 2]))


plt.legend()
plt.subplot(3, 3, 7)
plt.plot(d1.time(), e1[:, 1, 0], label='dINa/dgNa')
plt.plot(d3.time(), e3[:, 1, 0], '--', label='CVODES')
plt.xlim(50, 52)
plt.legend()
plt.subplot(3, 3, 8)
plt.plot(d1.time(), e1[:, 1, 1], label='dINa/dgCa')
plt.plot(d3.time(), e3[:, 1, 2], '--', label='CVODES')
plt.xlim(50, 52)
plt.legend()

plt.show()

