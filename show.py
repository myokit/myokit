#!/usr/bin/env python3
import matplotlib.pyplot as plt
with open("v.txt", "r") as f:
  T, V, S1, S2, S3 = [], [], [], [], []
  for line in f:
    t, v, s1, s2, s3 = [float(x) for x in line.split()]
    T.append(t)
    V.append(v)
    S1.append(s1)
    S2.append(s2)
    S3.append(s3)
plt.figure()
plt.subplot(4, 1, 1)
plt.plot(T, V)
plt.subplot(4, 1, 2)
plt.plot(T, S1)
plt.subplot(4, 1, 3)
plt.plot(T, S2)
plt.subplot(4, 1, 4)
plt.plot(T, S3)
plt.show()

