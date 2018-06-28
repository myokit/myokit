#!/usr/bin/env python
import numpy as np
import sys
from minilog import DataLog


if len(sys.argv) < 4:
    print('Usage: load <filename> <ncells> <var>')
    sys.exit(1)
fname = str(sys.argv[1])
ncell = int(sys.argv[2])
vname = str(sys.argv[3])

log = DataLog.load_csv(fname).npview()

# Plot
if False:
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D     # noqa
    # Show each cell's trace
    fg = plt.figure()
    ax = fg.gca(projection='3d')
    zz = np.ones(len(time))
    for k, log in enumerate(logs):
        ax.plot(time, k * zz, log)
    plt.show()
else:
    # Create grid data
    time = log['engine.time']
    ntime = len(time)
    x = (np.tile(np.arange(ncell), (ntime, 1))).transpose()
    y = np.tile(time, (ncell, 1))
    z = np.zeros((ncell, ntime))
    for k in range(ncell):
        z[k][:] = log.get(vname, k)
    import matplotlib.pyplot as plt
    f = plt.figure()
    a = f.add_subplot(111)
    r = float(ntime) / ncell
    a.imshow(z, interpolation='nearest', aspect=r)
    plt.show()
