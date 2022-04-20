# Memory leaks in simulations

The scripts in this directory are used for offline testing for memory leaks.

Unfortunately, this is not straightforward.

## decref.py

This uses `pympler` (install via pip) to see if new objects are added after a
call to a method (e.g. Simulation.run()).

##  memleak.py

This uses the built-in `resource` module to track memory increase after running
a simulation. This can be used to check for C memory leaks (not involving
Python objects). The results are occasionally obfuscated by Python doing things
in the background.


