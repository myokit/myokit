.. _api/simulations/myokit.LongSimulations:

************************
Running long simulations
************************

.. module:: myokit

Simulations can take a long time to run. In these cases, it's desirable to have
some form of communication between the simulation back-end (running in C or
C++) and the python caller. This can be used to provide user feedback about the
task's progess and prevents the application from appearing frozen.

To this end, simulations (and other long running tasks) in Myokit can implement
the :class:`ProgressReporter` interface. In the GUI, this allows a progress bar
to be displayed. Running from the console, a :class:`ProgressPrinter` can be
used to periodically provide status updates.

A special reporter :class:`Timeout` is provided that doesn't provide feedback,
but will cancel a simulation after a given time limit is reached.

.. autoclass:: ProgressReporter

.. autoclass:: ProgressPrinter

.. autoclass:: Timeout
