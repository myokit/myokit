***********
``compare``
***********

Allows you to compare two Myokit models

Example::

    $ myokit compare model1.mmt model2.mmt

Example output::

    Comparing:
      [1] decker-2009
      [2] decker-2009
    [1] Missing Variable <calcium.gamma>
    [x] Mismatched RHS <stimulus.amplitude>
    Done
      2 differences found

For the full syntax, see::

    $ myokit compare --help
