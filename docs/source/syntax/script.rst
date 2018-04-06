.. _syntax/script:

Embedded script
===============

Myokit files contain embedded python scripts that are used to set up the
simulation and perform post-processing.

These scripts are pure python and run in a separate environment where a number
of "magic" functions are defined:

  - ``model()`` returns the (parsed and validated) model contained in the model
    section of the file
  - ``protocol()`` returns the (parsed and validated) protocol contained in the
    protocol section of the file
    
When running from the GUI or using the :meth:`myokit.run()` method, these magic
functions are passed to the embedded script automatically.
    
For post-processing, Matplotlib is a popular graphing package for python and
works smoothly with Myokit. Info about using matplotlib can be found
:ref:`here <guide/matplotlib>`.
