.. _api/simulations/myokit.DataLog:

*********
Data logs
*********
.. module:: myokit

Simulations log their results in a :class:`DataLog`. This is a versatile
logging class which makes few assumptions about the type of data being logged.
When analysing the results of 1d or 2d, rectangular simulations, it can be
useful to convert to a :class:`DataBlock1d` or :class:`DataBlock2d`.

.. autoclass:: DataLog

.. autoclass:: LoggedVariableInfo

.. autofunction:: prepare_log

.. autofunction:: split_key

