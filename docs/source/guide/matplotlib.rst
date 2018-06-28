.. _guide/matplotlib:

Visualization with Matplotlib
=============================

Matplotlib is a popular graphing package for python and works smoothly with
myokit.

Matplotlib has its own documentation_.
For convenience, the most important commands are listed here:

.. _documentation: http://matplotlib.sourceforge.net/contents.html

``figure()``
    Creates a new figure

``subplot(321)``
    Indicates the next figure will be 1st part of a subplot containing 3 rows
    and 2 columns. An alternative syntax is ``subplot(3,2,1)``.
    (`docs <http://matplotlib.sourceforge.net/api/pyplot_api.html>`__)

``plot(x,y)``
    Creates a plot of y versus x

    The type of marker can be set with the third positional argument::

        plot(x, y, '*')

    Label, color and line width can be set with::

        plot(x, y, label='y versus x', color='blue', lw=3)
``show()``
    Displays the created plots

``figure.savefig(filename)``
    Saves a figure to a file.
    (`docs <http://matplotlib.org/api/figure_api.html#matplotlib.figure.Figure.savefig>`__)

``title(text)``
    Sets a title

``suptitle(t)``
    Adds a title *above* the normal title

``axis([xmin, xmax, ymin, ymax])``
    Sets the limits for the currents axes. Make sure to use axis with an 'i'!
    The ``axes`` command creates a new subplot.

    Run without arguments to obtain to current axis.

``xlim(min, max), ylim(min, max)``
    Limits can be set individually with xlim() and ylim(). Call without
    arguments to obtain the current limits.

``legend()``
    Using plot(x,y,label='abc') you can create labelled plots. The ``legend()``
    commands will use these to build a legend.

    The legend's location can be set with the ``loc`` keyword and string values
    such as "upper right", "left", "lower" or "center". To create multi-column
    legends, use the keyword ``ncol``, for example ``ncol=2``.

``grid()``
    Toggles the grid ub the current subplot. Use ``True`` or ``False`` to set
    the state of the grid explicitly.

``figtext(x, y, s)``
    Add text s at coordinates x and y (both in range [0..1])

``text(x, y, s)``
    Add text at plotted coordinates x and y

``loglog(x,y)``
    Using loglog, semilogx or semilogy instead of plot() you can create plots
    on logarithmic axes.

``quiver(x,y,u,v)``
    Creates vector plots::

        x = linspace(0,10,11)
        y = linspace(0,15,16)
        (X,Y) = meshgrid(x,y)
        u = 5*X
        v = 5*Y
        quiver(X,Y,u,v,angles='xy',scale=1000,color='r')

``xlabel(s), ylabel(s)``
    Add or set label on x or y axis



Customizing the axes
--------------------
To further customize the axis, use the axes object returned by the ``subplot``

Example
-------
The following is an example plot script for running in the GUI::

    [[script]]
    import myokit
    import matplotlib.pyplot as plt

    # Get model & protocol from magic methods
    m = get_model()
    p = get_protocol()

    # Create simulation
    s = myokit.Simulation(m, p)

    # Run simulation
    d = s.run(1000)

    # Display the result
    t = d['environment.t']
    v = d['membrane.V']
    plt.plot(t, v)
    plt.grid(True)
    plt.title('Membrane potential versus time')
    plt.show()

