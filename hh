#!/usr/bin/env python3
import myokit
import matplotlib.pyplot as plt
import numpy as np

m, p, _ = myokit.load('test.mmt')

#myokit.DEBUG = True

b = myokit.Benchmarker()
s = myokit.Simulation(m, p)
d = s.run(1000)
print(b.time())

