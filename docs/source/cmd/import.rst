**********
``import``
**********

Imports a model definition or protocol using any of the available importers.

Syntax::

    $ python myo import <format> <source_file> -o <output_file>
    
If no output file is specified, the generated mmt file is simply printed to
the screen.
    
Examples::
    
    $ python myo import cellml example.cellml
    
    $ python myo import cellml example.cellml test.mmt
    
For the full syntax, see::

    $ python myo import --help
