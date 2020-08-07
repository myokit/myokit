#!/usr/bin/env python3
import myokit
import numpy as np
import matplotlib.pyplot as plt

m, p, _ = myokit.load('example')

# Run a simulation
b = myokit.Benchmarker()
s1 = myokit.PSimulation(m, p,
    variables=['membrane.V', 'ina.INa'],
    parameters=['ina.gNa', 'ica.gCa'])
s2 = myokit.ICSimulation(m, p)
print(b.time())
b.reset()
d1, e1 = s1.run(1000)
d2, e2 = s2.run(1000)
print(b.time())

print(e1.shape)
print(e2.shape)

# Plot the results
plt.figure()
plt.subplot(3, 1, 1)
plt.plot(d1.time(), d1['membrane.V'])
plt.subplot(3, 3, 4)
plt.plot(d1.time(), e1[:, 0, 0], label='dV/dgNa')
plt.legend()
plt.subplot(3, 3, 5)
plt.plot(d1.time(), e1[:, 0, 1], label='dV/dgCa')
plt.legend()
plt.subplot(3, 3, 6)
plt.plot(d2.time(), e2[:, 0, 7], label='dV/dCai0')
plt.legend()
plt.subplot(3, 3, 7)
plt.plot(d1.time(), e1[:, 1, 0], label='dINa/dgNa')
plt.legend()
plt.subplot(3, 3, 8)
plt.plot(d1.time(), e1[:, 1, 1], label='dINa/dgCa')
plt.legend()

plt.show()

