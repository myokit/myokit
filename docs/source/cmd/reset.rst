*********
``reset``
*********

Resets all user settings by removing all Myokit configuration files. This will
cause Myokit to recreate the files with default settings the next time Myokit
is run.

Typical use::

    $ python myo reset
    
This will prompt you to confirm (by typing "yes" or "y") the reset. To bypass
the reset, use::

    $ python myo reset --force
