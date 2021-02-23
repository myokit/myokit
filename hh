#!/usr/bin/env python3
import myokit
import matplotlib.pyplot as plt
import numpy as np

m, p, _ = myokit.load('test.mmt')

b = myokit.Benchmarker()

print('Legacy')
b.reset()
s2 = myokit.LegacySimulation(m, p)
print(b.time())

print('CVODES')
b.reset()
s1 = myokit.Simulation(m, p)
print(b.time())


t1 = []
t2 = []

for i in range(25):
    s1.reset()
    s2.reset()

    if np.random.random() < 0.5:
        b.reset()
        s1.run(1000)
        t1.append(b.time())
        b.reset()
        s2.run(1000)
        t2.append(b.time())
    else:
        b.reset()
        s2.run(1000)
        t2.append(b.time())
        b.reset()
        s1.run(1000)
        t1.append(b.time())

t1 = np.array(t1) * 1e3
t2 = np.array(t2) * 1e3

print('Best, cvodes:', np.min(t1))
print('Best, cvode :', np.min(t2))

plt.figure()
plt.xlabel('Run')
plt.ylabel('Duration (ms)')
plt.plot(t2, label='CVODE, dirty code')
plt.plot(t1, label='CVODES, clean code')
plt.axhline(np.min(t2), ls='--', color='tab:blue')
plt.axhline(np.min(t1), ls='--', color='tab:orange')

plt.ylim(np.min(t1) - 0.1, np.min(t1) + 2)

plt.legend()

plt.show()
