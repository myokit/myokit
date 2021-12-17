.. _api/simulations/backend:

Simulation back-ends
====================

Simulations are run in C or C++ using custom back-ends built for each model on
the fly. To do this, Myokit utilises a number of modules detailed here.

Back-end classes
----------------

.. currentmodule:: myokit

.. autoclass:: CModule
    :private-members:
    :inherited-members:

.. autoclass:: CppModule
    :private-members:
    :inherited-members:

.. autoclass:: Compiler

.. autofunction:: pid_hash


Templating engine
-----------------

Myokit comes with a tiny templating engine called "Pype" that it uses to export
models to various languages and to create source files for on-the-fly
compilation.

It works in a quick-and-dirty way: each file read by Pype is scanned for
php-style tags ``<?`` and ``?>`` as well as the ``<?= value ?>`` operator.
Anything between these tags is left untouched, while everything around it is
turned into a triple quoted python string. The result is an ugly piece of
python code which, when run through the python interpreter, will print the
"processed" version of the template. The final step is then to redirect the
output buffer (stdout), run the script and return the caught output.

*Note: It should be clear from the preceding that Pype is completely unsuitable
for use in a web-based or other insecure environment. Much better packages
exist for such purposes.*


.. module:: myokit.pype

.. autoclass:: TemplateEngine

.. autoclass:: PypeError

