*********
``video``
*********

If you have ``moviepy`` (http://zulko.github.io/moviepy/) installed, this
script can be used to generate movies from
:class:`DataBlock1d <myokit.DataBlock1d>` or
:class:`DataBlock2d<myokit.DataBlock2d>` files.

The syntax is

    $ python myo video <inputfile> <variable> -dst <outputfile>
    
Here, `<inputfile>` should be the name of a DataBlock1d or 2d file. The
variable to visualized should be given as `<variable>` and the output file
should be given as `<outputfile>`. Supported outut formats are `flv`, `gif`,
`mp4`, `mpeg` and `wmv`.
    
Example::

    $ python myo video results.zip membrane.V -dst movie.mp4
    
For the full syntax, use::

    $ python myo video --help
