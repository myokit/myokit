#
# A set of tools to fit models to data.
#
#---------------------------------  license  ----------------------------------
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
#---------------------------------  credits  ----------------------------------
#
# Some of the local optimisers in this module are simply wrappers around SciPy
# implementations.
#
# Similarly, the CMA-ES method relies on the `cma` package by Nikolaus Hansen.
#
# The xNES and SNES methods are original implementations, but were written
# using both the published papers (see below) and the implementation in PyBrain
# (http://pybrain.org) as references.
#
# The remaining algorithms and optimisation routines are original
# implementations, and try to credit the algorithm's authors were possible.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import gc
import os
import sys
import time
import traceback
import multiprocessing
import numpy as np

# Queue in Python 2 and 3
try:
    import queue
except ImportError:  # pragma: no python 3 cover
    import Queue as queue


#
# This module is deprecated!
#
import logging
logger = logging.getLogger('myokit')
logger.warning(
    'The module myokit.lib.fit is deprecated: it will be removed in future'
    ' version of Myokit. Please have a look at Pints'
    ' (https://github.com/pints-team/pints) instead.'
)


def bfgs(f, x, bounds, max_iter=500, args=None):
    """
    Local optimizer that minimizes a function ``f`` using the constrained
    quasi-Newton method of Broyden, Fletcher, Goldfarb, and Shanno provided by
    SciPy [1,2,3].

    Arguments:

    ``f``
        A function to minimize. The function ``f(x)`` must be callable with
        ``x`` a sequence of ``m`` coordinates and should return a single scalar
        value.
    ``x``
        An initial guess for the ``x`` with the lowest ``f(x)``.
    ``bounds``
        A sequence of tuples ``(xmin, xmax)`` with the boundaries for each
        dimension of ``x``.
    ``max_iter``
        The maximum number of iterations to perform.
    ``args``
        An optional tuple containing extra arguments to ``f``. If ``args`` is
        specified, ``f`` will be called as ``f(x, *args)``.

    The method returns a tuple ``(xopt, fopt)`` where ``xopt`` is the best
    position found and ``fopt = f(xopt)``.

    References:

    [1] http://scipy.org

    [2] A Limited Memory Algorithm for Bound Constrained Optimization. Byrd,
    R H and P Lu and J. Nocedal (1995) SIAM Journal on Scientific and
    Statistical Computing 16 (5): 1190-1208.

    [3] L-BFGS-B: Algorithm 778: L-BFGS-B, FORTRAN routines for large scale
    bound constrained optimization. Zhu, C and R H Byrd and J Nocedal (1997)
    ACM Transactions on Mathematical Software 23 (4): 550-560.

    *Note: This method requires SciPy to be installed.*
    """
    from scipy.optimize import minimize
    if not callable(f):
        raise ValueError('The argument `f` must be a callable function.')
    if args is None:
        args = ()
    elif type(args) != tuple:
        raise ValueError('The argument `args` must be either None or a tuple.')
    max_iter = int(max_iter)
    if max_iter < 1:
        raise ValueError('Maximum number of iterations must be at least 1.')
    res = minimize(
        f, x, bounds=bounds, args=args, method='L-BFGS-B',
        options={'maxiter': max_iter, 'disp': False})
    # The success flag is only false on max_iter (not an error) or max function
    # evaluations (should that be an error?)
    #if not res.success:
    #    raise Exception('Error optimizing function: ' + str(res.message))
    return res.x, res.fun


def cmaes(
        f, bounds, hint=None, sigma=None, n=None, ipop=0, parallel=False,
        fatol=1e-11, target=1e-6, callback=None, verbose=False, args=None):
    """
    Global/local optimizer that minimizes a function ``f`` within a specified
    set of ``bounds`` using the CMA-ES methods provided by the `cma` module
    [1, 2].

    CMA-ES stands for Covariance Matrix Adaptation Evolution Strategy, and is
    designed for non-linear derivative-free optimization problems [1].
    To run, the `cma` module must have been installed (for example via PIP).

    A parallel (multiprocessing) version of the algorithm can be run by setting
    ``parallel`` to ``True``. Please keep in mind that the objective function
    ``f`` cannot access any shared memory in this scenario. See
    :class:`ParallelEvaluator` for details.

    The method will stop when one of the following criteria is met:

    1. Absolute changes in ``f(x)`` are smaller than ``fatol``
    2. The value of ``f(x)`` is smaller than ``target``.
    3. The maximum number of iterations is reached.

    Arguments:

    ``f``
        A function to minimize. The function ``f(x)`` must be callable with
        ``x`` a sequence of ``m`` coordinates and should return a single scalar
        value.
    ``bounds``
        A list of ``m`` tuples ``(min_i, max_i)`` specifying the minimum and
        maximum values in the search space for each dimension ``i``.
    ``hint=None``
        A suggested starting point. Must be within the given bounds. If no
        hint is given the center of the parameter space is used. A (uniform)
        random point can be selected by setting ``hint='random'``.
    ``sigma=None``
        A suggsted standard deviation; the method works best if the global
        optimum lies within +/- 3*sigma from the initial guess. If no value for
        sigma is given, the default value is ``1/6 * min(upper - lower)``,
        where ``upper`` and ``lower`` are the boundaries on the parameter
        space.
    ``n=None``
        Can be used to manually overrule the population size used in CMA-ES. By
        default, this is set by CMA-ES to be ``4+int(3*np.log(d))`` where ``d``
        is the number of dimensions of the search space. When running in
        parallel, Myokit will round this up to the nearest multiple of the CPU
        count. To set manually, use this parameter.
    ``ipop=0``
        Set to any integer greater than 1 to enable increasing population size
        restarts (IPOP). This will re-run the simulation ``ipop`` times (for a
        total number of ``ipop + 1`` runs). Each re-run will be from a randomly
        chosen starting point (within the boundaries) and with the population
        size increased by a factor 2. The rrecommended value for ``ipop`` is
        either ``0`` or ``8``.
    ``parallel=False``
        Set this to ``True`` to run a multi-process version of the search that
        utilizes all available cores. See :class:`EvaluatorProcess` for the
        details of using multi-process parallelisation and the requirements
        this places on the function ``f``.
    ``fatol``
        The smallest difference in ``f(x)`` between subsequent iterations that
        is acceptable for convergence.
    ``target=1e-6``
        The value of ``f(x)`` that is acceptable for convergence.
    ``callback=None``
        An optional function to be called after each iteration with arguments
        ``(pg, fg)`` where ``pg`` is the current best position and ``fg`` is
        the corresponding score.
    ``verbose``
        Set to ``True`` to enable logging of all sorts of information into the
        console window.
    ``args=None``
        An optional tuple containing extra arguments to ``f``. If ``args`` is
        specified, ``f`` will be called as ``f(x, *args)``.

    The method returns a tuple ``(xbest, fbest)`` where ``xbest`` is the best
    position found and ``fbest = f(xbest)``.

    References:

    [1] https://www.lri.fr/~hansen/cmaesintro.html

    [2] Hansen, Mueller, Koumoutsakos (2006) Reducing the time complexity of
    the derandomized evolution strategy with covariance matrix adaptation
    (CMA-ES).

    *Note: This method requires the `cma` module to be installed.*
    """
    # Test if CMAES is installed
    try:
        import cma
    except ImportError:
        raise ImportError(
            'This method requires the `cma` module to be installed')

    # Test if function is callable
    if not callable(f):
        raise ValueError('The argument f must be a callable function.')

    # Check extra arguments
    if args is None:
        args = ()
    elif type(args) != tuple:
        raise ValueError('The argument `args` must be either None or a tuple.')

    # Check bounds
    d = len(bounds)
    if d < 1:
        raise ValueError('Dimension must be at least 1.')
    lower = np.zeros(d)
    upper = np.zeros(d)
    for i, b in enumerate(bounds):
        if len(b) != 2:
            raise ValueError(
                'Each entry in `bounds` must be a tuple `(min, max)`.')
        lo, up = float(b[0]), float(b[1])
        if not lo < up:
            raise ValueError(
                'The lower bounds must be smaller than the upper bounds.')
        lower[i] = lo
        upper[i] = up
    del(bounds)
    brange = upper - lower

    # Check hint
    if hint is None:
        hint = lower + 0.5 * (upper - lower)
    elif hint == 'random':
        hint = lower + np.random.uniform(0, 1, d) * (upper - lower)
    else:
        hint = np.array(hint, copy=True)
        if hint.shape != lower.shape:
            raise ValueError('Hint must have the shape ' + str(lower.shape))
        if np.any(hint < lower) or np.any(hint > upper):
            j = np.argmax(np.logical_or(hint < lower, hint > upper))
            raise ValueError(
                'Hint must be within the specified bounds (error with'
                ' parameter ' + str(1 + j) + ').')

    # Check sigma hint
    if sigma is not None:
        sigma = float(sigma)
        if sigma <= 0:
            raise ValueError('Sigma must be greater than 0.')
    else:
        # Guess initial sigma as 1/6 of the bounds (CMAES works best if the
        # optimal solution is within +/- 3*sigma from the initial guess, see
        # API docs).
        sigma = np.min(upper - lower) / 6.0

    # Check if parallelization is required
    parallel = bool(parallel)

    # Set population size
    if n is None:
        # Explicitly set default used by cma-es
        n = 4 + int(3 * np.log(d))
        # If parallel, round up to a multiple of the reported number of cores
        if parallel:
            cpu_count = multiprocessing.cpu_count()
            n = (((n - 1) // cpu_count) + 1) * cpu_count
    else:
        # Custom population size
        n = int(n)
        if n < 1:
            raise ValueError(
                'Population size must be `None` or non-zero integer')

    # Check number of IPOP restarts
    ipop = int(ipop)
    if ipop < 0:
        raise ValueError('Number of IPOP restarts must be zero or positive.')

    # Check convergence criteria
    fatol = float(fatol)
    target = float(target)

    # Check callback function
    if callback is not None:
        if not callable(callback):
            raise ValueError(
                'Argument `callback` must be a callable function or `None`.')
    # Check if verbose mode is enabled
    verbose = bool(verbose)

    # Report first point
    if callback is not None:
        callback(np.array(hint, copy=True), f(hint, *args))

    # Create evaluator object
    if parallel:
        evaluator = ParallelEvaluator(f, args=args)
    else:
        evaluator = SequentialEvaluator(f, args=args)

    # Set up simulation options
    try:
        best_solution = cma.BestSolution()
    except AttributeError:
        import cma.optimization_tools
        best_solution = cma.optimization_tools.BestSolution()
    options = cma.CMAOptions()
    options.set('bounds', [list(lower), list(upper)])
    options.set('tolfun', fatol)
    options.set('ftarget', target)
    if not verbose:
        options.set('verbose', -9)

    # If no seed is given, CMAES reseeds. So to get consistent results always
    # pass in a seed. This can be random generated (because then you can still
    # seed np.random to get consistent output).
    options.set('seed', np.random.randint(2**32))

    # Start one or multiple runs
    for i in range(1 + ipop):
        # Set population size, increase for ipop restarts
        options.set('popsize', n)
        if verbose:
            print('Run ' + str(1 + i) + ': population size ' + str(n))
        n *= 2

        # Run repeats from random points
        if i > 0:
            hint = lower + brange * np.random.uniform(0, 1, d)

        # Search
        es = cma.CMAEvolutionStrategy(hint, sigma, options)
        while not es.stop():
            candidates = es.ask()
            es.tell(candidates, evaluator.evaluate(candidates))
            if callback is not None:
                r = es.result()
                callback(np.array(r[0], copy=True), r[1])
            if verbose:
                es.disp()

        # Show result
        if verbose:
            es.result_pretty()

        # Update best solution
        best_solution.update(es.best)

        # Stop if target was already met
        x, fx, evals = best_solution.get()
        if fx is not None and fx < target:
            break

    # No result found? Then return hint and score of hint
    if x is None:
        return (hint, f(hint, *args))

    # Return proper result
    return (x, fx)


class _DiscontinuousBoundedWrapper(object):
    """
    Wraps around a (scalar-valued) score function and returns `inf` for any
    input outside a specified set of bounds.
    """
    def __init__(self, function, lower, upper):
        # Using a class for this, rather than a nested function as a wrapper
        # avoids problems with pickling nested functions. Pickling is required
        # for multiprocessing on Windows.
        self.function = function
        self.lower = lower
        self.upper = upper

    def __call__(self, x, *args):
        if np.any(x < self.lower) or np.any(x > self.upper):
            return float('inf')
        else:
            return self.function(x, *args)


class _DiscontinuousBoundedWrapper2(object):
    """
    Wraps around a (scalar-valued) score function and returns
    `(original input, inf)` for any input outside a specified set of bounds.
    """
    def __init__(self, function, lower, upper):
        self.function = function
        self.lower = lower
        self.upper = upper

    def __call__(self, x, *args):
        if np.any(x < self.lower) or np.any(x > self.upper):
            return (x, float('inf'))
        else:
            return self.function(x, *args)


def evaluate(f, x, parallel=False, args=None):
    """
    Evaluates the function ``f`` on every value present in ``x`` and returns
    a sequence of evaluations ``f(x[i])``.

    To run the evaluations on all available cores, set ``parallel=True``. For
    details see :class:`ParallelEvaluator`.

    Extra arguments to pass to ``f`` can be given in the optional tuple
    ``args``. If used, ``f`` will be called as ``f(x[i], *args)``.
    """
    if parallel:
        evaluator = ParallelEvaluator(f, args)
    else:
        evaluator = SequentialEvaluator(f, args)
    return evaluator.evaluate(x)


class Evaluator(object):
    """
    *Abstract class*

    Interface for classes that take a function (or callable object)
    ``f(x)`` and evaluate it for list of input values ``x``. This interface is
    shared by a parallel and a sequential implementation, allowing easy
    switching between parallel or sequential implementations of the same
    algorithm.

    Arguments:

    ``function``
        A function or other callable object ``f`` that takes a value ``x`` and
        returns an evaluation ``f(x)``.
    ``args``
        An optional sequence of extra arguments to ``f``. If ``args`` is
        specified, ``f`` will be called as ``f(x, *args)``.

    """
    def __init__(self, function, args=None):
        if not callable(function):
            raise ValueError('The given function must be callable.')
        self._function = function
        if args is None:
            self._args = ()
        else:
            try:
                len(args)
            except TypeError:
                raise ValueError(
                    'The argument `args` must be either None or a sequence.')
            self._args = args

    def evaluate(self, positions):
        """
        Evaluate the function for every value in the sequence ``positions``.

        Returns a list with the returned evaluations.
        """
        try:
            len(positions)
        except TypeError:
            raise ValueError(
                'The argument `positions` must be a sequence of input values'
                ' to the evaluator\'s function.')
        return self._evaluate(positions)

    def _evaluate(self, positions):
        """
        Internal version of :meth:`evaluate()`.
        """
        raise NotImplementedError


def loss_surface_colors(x, y, f, xlim=None, ylim=None, markers='+'):
    """
    Takes irregularly spaced points ``(x, y, f)`` and creates a 2d colored
    Voronoi diagram.

    This method is useful to visualize the output of an optimisation routine on
    a 2-dimensional parameter space.

    Most 2d plotting methods (like matplotlib's contour and surf, or mayavi's

    default plotting options) accept only regularly spaced ``(x, y)`` grids as
    input. Unfortunately, the points sampled by an optimisation routine are
    typically dense in some areas and sparse in some. While a plot can still be
    created by interpolating from these points, this may add or remove vital
    detail. The voronoi color plot provides two-dimensional equivalent of a
    zero-order hold graph.

    This method returns a matplotlib figure of a 2d loss surface, represented
    as a Voronoi diagram with colored surfaces.

    Most 2d plotting functions expect a regular 2d grid as input for the x and
    y coordinates. When estimating the shape of a loss surface it may be much
    more accurate to sample densely in some areas and sparsley in others.
    Interpolating this to a regular grid causes loss of detail and an
    unsatisfactory representation. This method attempts to get around this
    issue by creating a voronoi diagram of the sampled points and shading the
    region around each point according to its loss-function value. This is
    essentially a kind of 2d zero hold representation of the loss function.

    Arguments:

    ``x``
        A 1d array of x coordinates.
    ``y``
        A 1d array of y coordinates.
    ``f``
        A 1d array of loss function evaluations, calculated at ``(x, y)``.
    ``xlim``
        A tuple ``(xmin, xmax)`` representing the possible range of x values.
        If set to ``None`` an automatic range will be computed.
    ``ylim``
        A tuple ``(xmin, xmax)`` representing the possible range of x values.
        If set to ``None`` an automatic range will be computed.
    ``markers``
        The markers to use to plot the sampled points. Set to None to disable.

    Returns a matplotlib figure.

    *Note: This method requires Matplotlib to be installed.*
    """
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection

    # Check limits
    if xlim is None:
        xmin = 0.80 * np.min(x)
        xmax = 1.02 * np.max(x)
        xlim = xmin, xmax
    else:
        xmin, xmax = [float(a) for a in xlim]
    if ylim is None:
        ymin = 0.80 * np.min(y)
        ymax = 1.02 * np.max(y)
        ylim = ymin, ymax
    else:
        ymin, ymax = [float(a) for a in ylim]

    # Get voronoi regions
    x, y, f, regions = voronoi_regions(x, y, f, xlim, ylim)

    # Create figure and axes
    figure, axes = plt.subplots()
    axes.set_xlim(xmin, xmax)
    axes.set_ylim(ymin, ymax)
    c = PolyCollection(regions, array=f, edgecolors='none')
    axes.add_collection(c)
    if markers:
        axes.plot(x, y, markers)
    figure.colorbar(c, ax=axes)
    return figure


def loss_surface_mesh(x, y, f):
    """
    Takes irregularly spaced points ``(x, y, f)`` and creates a mesh using
    the ``Mayavi`` package and Delaunay triangulation.

    This method is useful to visualize the output of an optimisation routine on
    a 2-dimensional parameter space.

    *Note: this method requires Mayavi to be installed.*
    """
    # Import mayavi
    from mayavi import mlab

    # Create a figure
    mlab.figure(1, fgcolor=(0, 0, 0), bgcolor=(1, 1, 1))

    # Visualize the points
    p = mlab.points3d(x, y, f, f, scale_mode='none', scale_factor=0)

    # Create and visualize the mesh
    mlab.pipeline.surface(mlab.pipeline.delaunay2d(p))

    # Display the created surface
    mlab.show()


def map_grid(f, bounds, n, parallel=False, args=None):
    """
    Maps a parameter space by evaluating every point in a rectangular grid.

    Arguments:

    ``f``
        A function to map. The function ``f(x)`` must be callable with ``x`` a
        sequence of ``m`` coordinates and should return a single scalar value.
    ``bounds``
        A list of ``m`` tuples ``(min_i, max_i)`` specifying the minimum and
        maximum values in the search space for each dimension ``i``. The mapped
        space will be within these bounds.
    ``n``
        The number of points to sample in each direction. If ``n`` is a scalar
        the function will map a grid of ``n`` points in each direction, so that
        the total number of points is ``n**m``, where ``m`` is the
        dimensionality of the search space. Alternatively, the number of points
        in each dimension can be specified by passing in a length ``m``
        sequence of sizes, so that the total number of points mapped is
        ``n[0] * n[1] * ... * n[m-1]``.
    ``parallel``
        Set to ``True`` to run evaluations on all available cores.
    ``args``
        An optional tuple containing extra arguments to ``f``. If ``args`` is
        specified, ``f`` will be called as ``f(x, *args)``.

    Returns a tuple ``(x, fx)`` where ``x`` is a numpy array containing all the
    tested points and ``fx`` contains the calculated ``f(x)`` for each ``x``.
    """
    # Check bounds, get number of dimensions
    ndims = len(bounds)
    if ndims < 1:
        raise ValueError('Problem must be at least 1-dimensional.')
    for b in bounds:
        if len(b) != 2:
            raise ValueError(
                'A minimum and maximum must be specified for each dimension.')

    # Check number of points
    try:
        len(n)
    except TypeError:
        n = (n,) * ndims
    if len(n) != ndims:
        if len(n) == 1:
            n = (n,) * ndims
        else:
            raise ValueError(
                'The positional argument n must be a scalar or provide a value'
                ' for each dimension.')
    npoints = np.array(n)
    ntotal = np.prod(npoints)

    # Create points
    x = []
    n = iter(npoints)
    for xmin, xmax in bounds:
        x.append(np.linspace(xmin, xmax, next(n)))

    # Create a grid from these points
    x = np.array(np.meshgrid(*x, indexing='ij'))

    # Re-organise the grid to be a series of nd-dimensional points
    x = x.reshape((ndims, ntotal)).transpose()

    # Evaluate and return
    return x, evaluate(f, x, parallel=parallel, args=args)


def nelder_mead(f, x, xatol=1e-4, fatol=1e-4, max_iter=500, args=None):
    """
    Local optimizer that minimizes a function ``f`` using the Nelder-Mead
    simplex method provided by SciPy [1,2].

    The method will stop when one of the following criteria is met:

    1. Absolute changes in ``x`` are smaller than ``xatol`` _and_ absolute
       changes in ``f(x)`` are smaller than ``fatol``
    2. The maximum number of iterations is reached.

    Arguments:

    ``f``
        A function to minimize. The function ``f(x)`` must be callable with
        ``x`` a sequence of ``m`` coordinates and should return a single scalar
        value.
    ``x``
        An initial guess for the ``x`` with the lowest ``f(x)``.
    ``xatol``
        Sets the _absolute_ difference in ``x`` between iterations that is
        acceptable for convergence.
    ``fatol``
        Sets the _absolute_ difference in ``f(x)`` between iterations that is
        acceptable for convergence.
    ``max_iter``
        The maximum number of iterations to perform.
    ``args``
        An optional tuple containing extra arguments to ``f``. If ``args`` is
        specified, ``f`` will be called as ``f(x, *args)``.

    The method returns a tuple ``(xopt, fopt)`` where ``xopt`` is the best
    position found and ``fopt = f(xopt)``.

    References:

    [1] http://scipy.org

    [2] A Simplex Method for Function Minimization. Nelder, J A, and R Mead
    (1965) The Computer Journal 7: 308-13.

    *Note: This method requires SciPy to be installed.*
    """
    from scipy.optimize import minimize
    # Check if function is callable
    if not callable(f):
        raise ValueError('The argument `f` must be a callable function.')
    # Check extra arguments
    if args is None:
        args = ()
    elif type(args) != tuple:
        raise ValueError('The argument `args` must be either None or a tuple.')
    # Check stopping criteria
    # SciPy's Nelder-Mead has the following stopping criteria:
    #  `fatol` (used to be called ftol): Absolute error in x between iterations
    #  `xatol` (used to be called xtol): Absolute error in f between iterations
    #  maxiter: Maximum iterations
    #  maxfev: Maximum number of function evaluations
    # The argument `tol` sets `fatol` and `xatol` simultaneously
    # Both fatol and xatol must be met for the method to halt
    fatol = float(fatol)
    xatol = float(xatol)
    max_iter = int(max_iter)
    if max_iter < 1:
        raise ValueError('Maximum number of iterations must be at least 1.')
    # Minimize
    res = minimize(
        f, x, args=args, method='Nelder-Mead', tol=None, options={
            'xatol': xatol,
            'fatol': fatol,
            'maxiter': max_iter,
            'disp': False
        })
    # The success flag is only false on max_iter (not an error) or max function
    # evaluations (should that be an error?)
    #if not res.success:
    #    raise Exception('Error optimizing function: ' + str(res.message))
    return res.x, res.fun


class _ParameterTransformWrapper(object):
    """
    Wraps around a score function, calls a parameter transform before
    evaluating the function.
    """
    def __init__(self, function, transform):
        self.function = function
        self.transform = transform

    def __call__(self, x, *args):
        return self.function(self.transform(x), *args)


class ParallelEvaluator(Evaluator):
    """
    Evaluates a single-valued function object for any set of input values
    given, using all available cores.

    Shares an interface with the :class:`SequentialEvaluator`, allowing
    parallelism to be switched on and off with minimal hassle. Parallelism
    takes a little time to be set up, so as a general rule of thumb it's only
    useful for if the total run-time is at least ten seconds (anno 2015).

    By default, the number of processes ("workers") used to evaluate the
    function is set equal to the number of CPU cores reported by python's
    ``multiprocessing`` module. To override the number of workers used, set
    ``nworkers`` to some integer greater than 0.

    There are two important caveats for using multiprocessing to evaluate
    functions:

      1. Processes don't share memory. This means the function to be
         evaluated will be duplicated (via pickling) for each process (see
         `Avoid shared state <http://docs.python.org/2/library/\
multiprocessing.html#all-platforms>`_ for details).
      2. On windows systems your code should be within an
         ``if __name__ == '__main__':`` block (see `Windows
         <https://docs.python.org/2/library/multiprocessing.html#windows>`_
         for details).

    Arguments:

    ``function``
        The function to evaluate
    ``nworkers``
        The number of worker processes to use. If left at the default value
        ``nworkers=None`` the number of workers will equal the number of CPU
        cores in the machine this is run on. In many cases this will provide
        good performance.
    ``max_tasks_per_worker``
        Python garbage collection does not seem to be optimized for
        multi-process function evaluation. In many cases, some time can be
        saved by refreshing the worker processes after every
        ``max_tasks_per_worker`` evaluations. This number can be tweaked for
        best performance on a given task / system.
    ``args``
        An optional tuple containing extra arguments to the objective function.

    The evaluator will keep it's subprocesses alive and running until it is
    tidied up by garbage collection.

    Note that while this class uses multiprocessing, it is not thread/process
    safe itself: It should not be used by more than a single thread/process at
    a time.

    *Extends:* :class:`Evaluator`
    """
    def __init__(
            self, function, nworkers=None, max_tasks_per_worker=500,
            args=None):
        super(ParallelEvaluator, self).__init__(function, args)
        # Determine number of workers
        if nworkers is None:
            self._nworkers = max(1, multiprocessing.cpu_count())
        else:
            self._nworkers = int(nworkers)
            if self._nworkers < 1:
                raise ValueError(
                    'Number of workers must be an integer greater than 0 or'
                    ' `None` to use the default value.')
        # Create empty set of workers
        self._workers = []
        # Maximum tasks per worker (for some reason, this saves memory)
        self._max_tasks = int(max_tasks_per_worker)
        if self._max_tasks < 1:
            raise ValueError(
                'Maximum tasks per worker should be at least 1 but probably'
                ' much greater.')
        # Queue with tasks
        self._tasks = multiprocessing.Queue()
        # Queue with results
        self._results = multiprocessing.Queue()
        # Queue used to add an exception object and context to
        self._errors = multiprocessing.Queue()
        # Flag set if an error is encountered
        self._error = multiprocessing.Event()

    def __del__(self):
        # Cancel everything
        try:
            self._stop()
        except Exception:
            pass

    def _clean(self):
        """
        Cleans up any dead workers & return the number of workers tidied up.
        """
        cleaned = 0
        for k in range(len(self._workers) - 1, -1, -1):
            w = self._workers[k]
            if w.exitcode is not None:  # pragma: no cover
                w.join()
                cleaned += 1
                del(self._workers[k])
        if cleaned:     # pragma: no cover
            gc.collect()
        return cleaned

    def _populate(self):
        """
        Populates (but usually repopulates) the worker pool.
        """
        for k in range(self._nworkers - len(self._workers)):
            w = _Worker(
                self._function,
                self._args,
                self._tasks,
                self._results,
                self._max_tasks,
                self._errors,
                self._error,
            )
            self._workers.append(w)
            w.start()

    def _evaluate(self, positions):
        """
        Evaluate all tasks in parallel, in batches of size self._max_tasks.
        """
        # Ensure task and result queues are empty
        # For some reason these lines block when running on windows
        #if not (self._tasks.empty() and self._results.empty()):
        #    raise Exception('Unhandled tasks/results left in queues.')

        # Clean up any dead workers
        self._clean()

        # Ensure worker pool is populated
        self._populate()

        # Start
        try:
            # Enqueue all tasks (non-blocking)
            for k, x in enumerate(positions):
                self._tasks.put((k, x))

            # Collect results (blocking)
            n = len(positions)
            m = 0
            results = [0] * n
            while m < n and not self._error.is_set():
                time.sleep(0.001)   # This is really necessary
                # Retrieve all results
                try:
                    while True:
                        i, f = self._results.get(block=False)
                        results[i] = f
                        m += 1
                except queue.Empty:
                    pass

                # Clean dead workers
                if self._clean():   # pragma: no cover
                    # Repolate
                    self._populate()

        except (IOError, EOFError):     # pragma: no cover
            # IOErrors can originate from the queues as a result of issues in
            # the subprocesses. Check if the error flag is set. If it is, let
            # the subprocess exception handling deal with it. If it isn't,
            # handle it here.
            if not self._error.is_set():
                self._stop()
                raise
            # TODO: Maybe this should be something like while(error is not set)
            # wait for it to be set, then let the subprocess handle it...
        except (Exception, SystemExit, KeyboardInterrupt):  # pragma: no cover
            # All other exceptions, including Ctrl-C and user triggered exits
            # should (1) cause all child processes to stop and (2) bubble up to
            # the caller.
            self._stop()
            raise

        # Error in worker threads
        if self._error.is_set():
            errors = self._stop()

            # Raise exception
            if errors:
                pid, trace = errors[0]
                raise Exception('Exception in subprocess:' + trace)
            else:
                # Don't think this ever happens!
                raise Exception(
                    'Unknown exception in subprocess.')  # pragma: no cover

        # Return results
        return results

    def _stop(self):
        """
        Forcibly halts the workers
        """
        time.sleep(0.1)
        # Terminate workers
        for w in self._workers:
            if w.exitcode is None:
                w.terminate()
        for w in self._workers:
            if w.is_alive():
                w.join()
        self._workers = []

        # Free memory
        gc.collect()

        # Clear queues
        def clear(q):
            items = []
            try:
                while True:
                    items.append(q.get(timeout=0.1))
            except (queue.Empty, IOError, EOFError):
                pass
            return items
        clear(self._tasks)
        clear(self._results)
        errors = clear(self._errors)

        # Create new queues & error event
        self._tasks = multiprocessing.Queue()
        self._results = multiprocessing.Queue()
        self._errors = multiprocessing.Queue()
        self._error = multiprocessing.Event()

        # Return errors
        return errors


def powell(f, x, xtol=1e-4, ftol=1e-4, max_iter=500, args=None):
    """
    Local optimizer that minimizes a function ``f`` using the implementation of
    Powell's conjugate direction method provided by SciPy [1, 2].

    Powell created a number of derivative free optimization methods. The method
    used here is one of the earliest, and is described in [2].

    The method will stop when one of the following criteria is met:

    1. Relative changes in ``x`` are smaller than ``xtol``
    2. Relative changes in ``f(x)`` are smaller than ``ftol``
    3. The maximum number of iterations is reached.

    Arguments:

    ``f``
        A function to minimize. The function ``f(x)`` must be callable with
        ``x`` a sequence of ``m`` coordinates and should return a single scalar
        value.
    ``x``
        An initial guess for the ``x`` with the lowest ``f(x)``.
    ``xtol``
        Sets the _relative_ difference in ``x`` between iterations that is
        acceptable for convergence.
    ``ftol``
        Sets the _relative_ difference in ``f(x)`` between iterations that is
        acceptable for convergence.
    ``max_iter``
        The maximum number of iterations to perform.
    ``args``
        An optional tuple containing extra arguments to ``f``. If ``args`` is
        specified, ``f`` will be called as ``f(x, *args)``.

    The method returns a tuple ``(xopt, fopt)`` where ``xopt`` is the best
    position found and ``fopt = f(xopt)``.

    References:

    [1] http://scipy.org

    [2] An efficient method for finding the minimum of a function of several
    variables without calculating derivatives. Powell, M. J. D. (1964)
    Computer Journal 7 (2): 155-162. doi:10.1093/comjnl/7.2.155

    *Note: This method requires SciPy to be installed.*
    """
    from scipy.optimize import minimize
    # Check if function is callable
    if not callable(f):
        raise ValueError('The argument `f` must be a callable function.')

    # Check extra arguments
    if args is None:
        args = ()
    elif type(args) != tuple:
        raise ValueError('The argument `args` must be either None or a tuple.')

    # Check stopping criteria
    xtol = float(xtol)
    ftol = float(ftol)
    max_iter = int(max_iter)
    if max_iter < 1:
        raise ValueError('Maximum number of iterations must be at least 1.')

    # Minimize
    res = minimize(f, x, args=args, method='Powell', tol=None, options={
        'xtol': xtol, 'ftol': ftol, 'maxiter': max_iter, 'disp': False})
    if not res.success:
        raise Exception('Error optimizing function: ' + str(res.message))
    return res.x, res.fun


def pso(
        f, bounds, hints=None, n=4, r=0.5, v=1e-3, parallel=False, target=1e-6,
        max_iter=500, hybrid=False, return_all=False, callback=None,
        callback_particles=None, verbose=False, args=None):
    """
    Global optimizer that minimizes a function ``f`` within a specified set of
    ``bounds`` using particle swarm optimization (PSO) [1].

    In a particle swarm optimization, the parameter space is explored by ``n``
    independent particles. The particles perform a pseudo-random walk through
    the parameter space, guided by their own personal best score and the global
    optimum found so far.

    A parallel (multiprocessing) version of the algorithm can be run by setting
    ``parallel`` to ``True``. Please keep in mind that the objective function
    ``f`` cannot access any shared memory in this scenario. See
    :class:`ParallelEvaluator` for details.

    The method will stop when one of the following criteria is met:

    1. The value of ``f(x)`` is smaller than ``target``.
    2. The maximum number of iterations is met (where one "iteration" means
       each of the ``n`` particles has been updated).

    Arguments:

    ``f``
        A function to minimize. The function ``f(x)`` must be callable with
        ``x`` a sequence of ``m`` coordinates and should return a single scalar
        value. Alternatively, in hybrid mode (which is disabled by default),
        ``f(x)`` should return a tuple ``(x2, fx2)`` where ``x2`` is a new
        value for ``x`` and ``fx2`` is the score function evaluated at ``x2``.
    ``bounds``
        A list of ``m`` tuples ``(min_i, max_i)`` specifying the minimum and
        maximum values in the search space for each dimension ``i``. The
        returned solution is guaranteed to be within these bounds.
    ``hints``
        A (possibly empty) list of points to use as initial values. Each point
        ``x`` is specified as a sequence of ``m`` coordinates, such as can be
        passed to ``f(x)``. Hints will be used as long as they are available.
        If there are more hints than particles only the first hints in the
        sequence will be used. If there are more particles than hints, the
        remaining particles will be initialized at uniformly random positions
        in the search space.
    ``n=4``
        The number of particles to use in the search.
    ``r=0.5``
        A number between ``0`` and ``1``, specifying the ratio between the
        local attraction (r=1) and global attraction (r=0, see below).
    ``v=1e-3``
        The maximum initial velocity, as a fraction of the bounded space. By
        default, the velocity in each direction ``i`` is set as
        ``vs[i] = U(0, v * (upper[i] - lower[i]))``, where ``U`` is a uniform
        sampling function, and ``upper`` and ``lower`` represent the given
        upper and lower bounds in direction ``i``.
    ``parallel=False``
        Set this to ``True`` to run a multi-process version of the search that
        utilizes all available cores. See :class:`EvaluatorProcess` for the
        details of using multi-process parallelisation and the requirements
        this places on the function ``f``.
    ``target=1e-6``
        The method will stop searching when a score below the target value
        is found.
    ``max_iter=500``
        The maximum number of iterations to perform.
    ``hybrid=False``
        Set this to ``True`` to perform a hybrid optimization. In this case,
        the function passed as the first argument should return a tuple
        ``(x2, fx2)`` where ``x2`` is the updated position and ``fx2`` is its
        score.
    ``return_all=False``
        Set this to ``True`` to return all results, instead of only the best
        particle.
    ``callback=None``
        An optional function to be called after each global step with arguments
        ``(pg, fg)`` where ``pg`` is the current best position and ``fg`` is
        the corresponding score.
    ``callback_particles=None``
        An optional function to be called after each global step with arguments
        ``(xs, vs, fs)`` where ``xs``, ``vs`` and ``fs`` are lists containing
        the current particle positions, velocities and scores respectively.
    ``verbose=False``
        Set to ``True`` to have progress information printed to the terminal.
        If set to any non-zero integer this will determine the number of
        iterations between updates.
    ``args=None``
        An optional tuple containing extra arguments to ``f``. If ``args`` is
        specified, ``f`` will be called as ``f(x, *args)``.

    The method starts by creating a swarm of ``n`` particles and assigning each
    an initial position and initial velocity (see the explanation of the
    arguments ``hints`` and ``v`` for details). Each particle's score is
    calculated and set as the particle's current best local score ``pl``. The
    best score of all the particles is set as the best global score ``pg``.

    Next, an iterative procedure is run that updates each particle's velocity
    ``v`` and position ``x`` using::

        v[k] = v[k-1] + al * (pl - x[k-1]) + ag * (pg - x[k-1])
        x[k] = v[k]

    Here, ``x[t]`` is the particle's current position and ``v[t]`` its current
    velocity. The values ``al`` and ``ag`` are scalars randomly sampled from a
    uniform distribution, with values bound by ``r * 4.1`` and
    ``(1 - r) * 4.1``. Thus a swarm with ``r = 1`` will only use local
    information, while a swarm with ``r = 0`` will only use global information.
    The de facto standard is ``r = 0.5``. The random sampling is done each time
    ``al`` and ``ag`` are used: at each time step every particle performs ``m``
    samplings, where ``m`` is the dimensionality of the search space.

    Pseudo-code algorithm::

        almax = r * 4.1
        agmax = 4.1 - almax
        while stopping criterion not met:
            for i in [1, 2, .., n]:
                if f(x[i]) < f(p[i]):
                    p[i] = x[i]
                pg = min(p[1], p[2], .., p[n])
                for j in [1, 2, .., m]:
                    al = uniform(0, almax)
                    ag = uniform(0, agmax)
                    v[i,j] += al * (p[i,j] - x[i,j]) + ag * (pg[i,j]  - x[i,j])
                    x[i,j] += v[i,j]

    A hybrid PSO method [2] can be implemented by adding the optional argument
    ``hybrid=True`` and changing the score function to return a tuple
    ``(x, fx)`` where ``x`` is an updated position and ``fx`` is its score.
    Suggestions for ``x``'s outside the set boundaries will be ignored.

    The method returns a tuple ``(pg, fg)`` where ``pg`` is the best position
    found and ``fg = f(pg)``. If ``return_all`` was set to ``True``, the tuple
    will contain a vector ``pg`` with each particle's best location and a
    vector ``fg`` with the corresponding scores, sorted best to worst.

    References:

    [1] Kennedy, Eberhart (1995) Particle Swarm Optimization.
    IEEE International Conference on Neural Networks

    [2] Loewe, Wilhems, Seemann et al. (2016) Parameter estimation of ion
    current formulations requires hybrid optimization approach to be both
    accurate and reliable.
    Frontiers in Bioengineering and Biotechnology

    """
    # Test if function is callable
    if not callable(f):
        raise ValueError('The argument f must be a callable function.')
    # Test extra arguments
    if args is None:
        args = ()
    elif type(args) != tuple:
        raise ValueError(
            'The argument `args` must be either None or a tuple.')
    # Check bounds
    d = len(bounds)
    if d < 1:
        raise ValueError('Dimension must be at least 1.')
    lower = np.zeros(d)
    upper = np.zeros(d)
    for i, b in enumerate(bounds):
        if len(b) != 2:
            raise ValueError(
                'Each entry in `bounds` must be a tuple `(min, max)`.')
        lo, up = float(b[0]), float(b[1])
        if not lo < up:
            raise ValueError(
                'The lower bounds must be smaller than the upper bounds.')
        lower[i] = lo
        upper[i] = up
    del(bounds)
    # Check number of particles
    n = int(n)
    if n < 1:
        raise ValueError('The number of particles must be 1 or greater.')
    # Check local/global balance r.
    r = float(r)
    if r < 0 or r > 1:
        raise ValueError('The value of r must be within 0 <= r <= 1.')
    amax = 4.1
    almax = r * amax
    agmax = amax - almax
    # Check initial velocity fraction
    v = float(v)
    if v < 0 or v > 1:
        raise ValueError(
            'The initial velocity fraction v must be between 0 and 1.')
    # Check hints
    if hints:
        _hints = hints
        hints = []
        for i, hint in enumerate(_hints):
            hint = np.array(hint, copy=True)
            if hint.shape != lower.shape:
                raise ValueError(
                    'Each hint must have the shape ' + str(lower.shape))
            if np.any(hint < lower) or np.any(hint > upper):
                j = np.argmax(np.logical_or(hint < lower, hint > upper))
                raise ValueError(
                    'All hints must be within the specified bounds (error with'
                    ' parameter ' + str(1 + j) + ' in hint number '
                    + str(1 + i) + ').')
            hints.append(hint)
        del(_hints)
    else:
        hints = []
    # Check if parallelization is required
    parallel = bool(parallel)
    # Check target
    target = float(target)
    # Check maximum iterations
    max_iter = int(max_iter)
    if max_iter < 1:
        raise ValueError('Maximum iterations must be greater than zero.')
    # Check callback functions
    if callback is not None:
        if not callable(callback):
            raise ValueError(
                'Argument `callback` must be a callable function or `None`.')
    if callback_particles is not None:
        if not callable(callback_particles):
            raise ValueError(
                'Argument `callback_particles` must be a callable or `None`.')
    # Parse verbose argument
    if verbose is True:
        verbose = 100
    else:
        verbose = int(verbose)
        if verbose <= 0:
            verbose = False
    # Give some info at start-up
    if verbose:
        if parallel:
            print('Running in parallel mode with ' + str(n) + ' particles')
        else:
            print('Running in sequential mode with ' + str(n) + ' particles')
        # Set up messaging
        nextMessage = 0
    # Initialize swarm
    xs = []     # Particle coordinate vectors
    vs = []     # Particle velocity vectors
    fs = []     # Particle scores
    fl = []     # Best local score
    pl = []     # Best local position
    fg = 0      # Best global score
    pg = 0      # Best global position
    # Initialize particles
    brange = upper - lower
    nhints = len(hints)
    for i in range(n):
        if i < nhints:
            xs.append(hints[i])
        else:
            xs.append(lower + brange * np.random.uniform(0, 1, d))
        vs.append(v * brange * np.random.uniform(0, 1, d))
        fs.append(float('inf'))
        fl.append(float('inf'))
        pl.append(xs[i])
    del(brange)
    # Set placeholder values for global best position and score
    fg = float('inf')
    pg = xs[0]
    # Report first point (with "inf" as score)
    if callback is not None:
        callback(np.array(pg, copy=True), fg)
    if callback_particles is not None:
        callback_particles(
            [np.array(x, copy=True) for x in xs],
            [np.array(x, copy=True) for x in vs], list(fs))
    # Wrap around function to check bounds
    if hybrid:
        # Create bounded wrapper that returns (x_old, inf)
        function = _DiscontinuousBoundedWrapper2(f, lower, upper)
    else:
        # Create an objective function that returns inf outside of bounds
        function = _DiscontinuousBoundedWrapper(f, lower, upper)
    # Create evaluator object
    if parallel:
        evaluator = ParallelEvaluator(function, args=args)
    else:
        evaluator = SequentialEvaluator(function, args=args)
    # Start searching
    for iteration in range(1, 1 + max_iter):
        # Check target criterion
        if fg <= target:
            if verbose:
                print('Target reached, halting')
            break
        # Calculate scores and, in hybrid mode, update positions
        if hybrid:
            out = evaluator.evaluate(xs)
            xs = np.asarray([i[0] for i in out])
            fs = np.asarray([i[1] for i in out])
        else:
            fs = evaluator.evaluate(xs)
        # Update particles
        for i in range(n):
            # Update best local position and score
            if fs[i] < fl[i]:
                fl[i] = fs[i]
                pl[i] = np.array(xs[i], copy=True)
            # Calculate "velocity"
            al = np.random.uniform(0, almax, d)
            ag = np.random.uniform(0, agmax, d)
            vs[i] += al * (pl[i] - xs[i]) + ag * (pg - xs[i])
            # Update position
            # To reduce the amount of time spent outside the bounds of the
            # search space, the velocity of any particle outside the bounds
            # is reduced by a factor (1 / (1 + number of boundary violations)).
            e = xs[i] + vs[i]
            e = np.logical_or(e > upper, e < lower)
            if np.any(e):
                vs[i] *= 1 / (1 + np.sum(e))
            xs[i] += vs[i]
        i = np.argmin(fl)
        if fl[i] < fg:
            fg = fl[i]
            pg = np.array(pl[i], copy=True)
        # Callbacks
        if callback is not None:
            callback(np.array(pg, copy=True), fg)
        if callback_particles is not None:
            callback_particles(
                [np.array(x, copy=True) for x in xs],
                [np.array(x, copy=True) for x in vs], list(fs))
        # Show progress in verbose mode:
        if verbose:
            if iteration >= nextMessage:
                print(str(iteration) + ': ' + str(fg))
                if iteration < 3:
                    nextMessage = iteration + 1
                else:
                    nextMessage = verbose * (1 + iteration // verbose)
    # Show final iteration
    if verbose:
        if fg > target:
            print('Maximum iterations reached, halting')
        print(str(iteration) + ': ' + str(fg))
    # Return best position and score
    if return_all:
        # Sort from best to worst
        fl = np.array(fl)
        pl = np.array(pl)
        sort_indices = np.argsort(fl)
        fl = fl[sort_indices]
        pl = pl[sort_indices]
        return (pl, fl)
    else:
        return (pg, fg)


class SequentialEvaluator(Evaluator):
    """
    Evaluates a function (or callable object) for a list of input values.

    Runs sequentially, but shares an interface with the
    :class:`ParallelEvaluator`, allowing parallelism to be switched on/off.

    Arguments:

    ``function``
        The function to evaluate.
    ``args``
        An optional tuple containing extra arguments to ``f``. If ``args`` is
        specified, ``f`` will be called as ``f(x, *args)``.

    Returns a list containing the calculated function evaluations.

    *Extends:* :class:`Evaluator`
    """
    def __init__(self, function, args=None):
        super(SequentialEvaluator, self).__init__(function, args)

    def _evaluate(self, positions):
        scores = [0] * len(positions)
        for k, x in enumerate(positions):
            scores[k] = self._function(x, *self._args)
        return scores


def snes(
        f, bounds, hint=None, n=None, parallel=False, target=1e-6,
        max_iter=1000, callback=None, verbose=False, args=None):
    """
    Global/local optimizer that minimizes a function ``f`` within a specified
    set of ``bounds`` using the SNES method described in [1, 2].

    SNES stands for Seperable Natural Evolution Strategy, and is designed for
    non-linear derivative-free optimization problems in high dimensions and
    with many local minima [1].

    A parallel (multiprocessing) version of the algorithm can be run by setting
    ``parallel`` to ``True``. Please keep in mind that the objective function
    ``f`` cannot access any shared memory in this scenario. See
    :class:`ParallelEvaluator` for details.

    The method will stop when one of the following criteria is met:

    1. The value of ``f(x)`` is smaller than ``target``.
    2. The maximum number of iterations is reached.

    Arguments:

    ``f``
        A function to minimize. The function ``f(x)`` must be callable with
        ``x`` a sequence of ``m`` coordinates and should return a single scalar
        value.
    ``bounds``
        A list of ``m`` tuples ``(min_i, max_i)`` specifying the minimum and
        maximum values in the search space for each dimension ``i``.
    ``hint=None``
        A suggested starting point. Must be within the given bounds. If no
        hint is given the center of the parameter space is used. A (uniform)
        random point can be selected by setting ``hint='random'``.
    ``n=None``
        Can be used to manually overrule the population size used in SNES. By
        default, this is set to be `4+int(3*np.log(d))` where ``d`` is the
        number of dimensions of the search space. When running in parallel,
        Myokit will round this default value up to the nearest multiple of the
        cpu count. To overrule these defaults, use this parameter.
    ``parallel=False``
        Set this to ``True`` to run a multi-process version of the search that
        utilizes all available cores. See :class:`EvaluatorProcess` for the
        details of using multi-process parallelisation and the requirements
        this places on the function ``f``.
    ``target=1e-6``
        The value of ``f(x)`` that is acceptable for convergence.
    ``max_iter=500``
        The maximum number of iterations to perform.
    ``callback=None``
        An optional function to be called after each iteration with arguments
        ``(pg, fg)`` where ``pg`` is the current best position and ``fg`` is
        the corresponding score.
    ``verbose=False``
        Set to ``True`` to have progress information printed to the terminal.
        If set to any non-zero integer this will determine the number of
        iterations between updates.
    ``args=None``
        An optional tuple containing extra arguments to ``f``. If ``args`` is
        specified, ``f`` will be called as ``f(x, *args)``.

    The method returns a tuple ``(xbest, fbest)`` where ``xbest`` is the best
    position found and ``fbest = f(xbest)``.

    References:

    [1] Schaul, Glasmachers, Schmidhuber (2011) High dimensions and heavy tails
    for natural evolution strategies.
    Proceedings of the 13th annual conference on Genetic and evolutionary
    computation. ACM, 2011.

    [2] PyBrain: The Python machine learning library (http://pybrain.org)

    """
    # Test if function is callable
    if not callable(f):
        raise ValueError('The argument f must be a callable function.')
    # Test extra arguments
    if args is None:
        args = ()
    elif type(args) != tuple:
        raise ValueError(
            'The argument `args` must be either None or a tuple.')
    # Get dimension of the search space
    d = len(bounds)
    if d < 1:
        raise ValueError('Dimension must be at least 1.')
    # Check bounds
    lower = np.zeros(d)
    upper = np.zeros(d)
    for i, b in enumerate(bounds):
        if len(b) != 2:
            raise ValueError(
                'Each entry in `bounds` must be a tuple `(min, max)`.')
        lo, up = float(b[0]), float(b[1])
        if not lo < up:
            raise ValueError(
                'The lower bounds must be smaller than the upper bounds.')
        lower[i] = lo
        upper[i] = up
    del(bounds)
    # Create periodic parameter space transform to implement boundaries
    transform = _TriangleWaveTransform(lower, upper)
    # Wrap transform around score function
    function = _ParameterTransformWrapper(f, transform)
    # Check hint
    if hint is None:
        hint = lower + 0.5 * (upper - lower)
    elif hint == 'random':
        hint = lower + np.random.uniform(0, 1, d) * (upper - lower)
    else:
        hint = np.array(hint, copy=True)
        if hint.shape != lower.shape:
            raise ValueError('Hint must have the shape ' + str(lower.shape))
        if np.any(hint < lower) or np.any(hint > upper):
            j = np.argmax(np.logical_or(hint < lower, hint > upper))
            raise ValueError(
                'Hint must be within the specified bounds (error with'
                ' parameter ' + str(1 + j) + ').')
    # Check if parallelization is required
    parallel = bool(parallel)
    # Set population size
    if n is None:
        # Explicitly set default
        n = 4 + int(3 * np.log(d))
        # If parallel, round up to a multiple of the reported number of cores
        if parallel:
            cpu_count = multiprocessing.cpu_count()
            n = (((n - 1) // cpu_count) + 1) * cpu_count
    else:
        # Custom population size
        n = int(n)
        if n < 1:
            raise ValueError(
                'Population size must be `None` or non-zero integer')
    # Parse verbose argument
    if verbose is True:
        verbose = 100
    else:
        verbose = int(verbose)
        if verbose <= 0:
            verbose = False
    # Show configuration info
    if verbose:
        if parallel:
            print('Running in parallel mode with population size ' + str(n))
        else:
            print('Running in sequential mode with population size ' + str(n))
    # Check convergence critera parameters
    max_iter = int(max_iter)
    if max_iter < 1:
        raise ValueError('Maximum iterations must be greater than zero.')
    target = float(target)
    # Check callback function
    if callback is not None:
        if not callable(callback):
            raise ValueError(
                'Argument `callback` must be a callable function or `None`.')
    # Create evaluator object
    if parallel:
        evaluator = ParallelEvaluator(function, args=args)
    else:
        evaluator = SequentialEvaluator(function, args=args)
    # Set up progress reporting in verbose mode
    nextMessage = 0
    # Set up algorithm
    # Learning rates
    eta_mu = 1
    eta_sigmas = 0.2 * (3 + np.log(d)) * d ** -0.5
    # Pre-calculated utilities
    us = np.maximum(0, np.log(n / 2 + 1) - np.log(1 + np.arange(n)))
    us /= np.sum(us)
    us -= 1 / n
    # Center of distribution
    mu = hint
    # Sigmas
    sigmas = np.ones(d)
    # Best solution found
    xbest = hint
    fbest = function(hint, *args)
    # Report first point
    if callback is not None:
        callback(np.array(hint, copy=True), fbest)
    # Start running
    for iteration in range(1, 1 + max_iter):
        # Create new samples
        ss = np.array([np.random.normal(0, 1, d) for i in range(n)])
        xs = mu + sigmas * ss
        # Evaluate at the samples
        fxs = evaluator.evaluate(xs)
        # Order the normalized samples according to the scores
        order = np.argsort(fxs)
        ss = ss[order]
        # Update center
        mu += eta_mu * sigmas * np.dot(us, ss)
        # Update variances
        sigmas *= np.exp(0.5 * eta_sigmas * np.dot(us, ss**2 - 1))
        # Update best if needed
        if fxs[order[0]] < fbest:
            xbest = xs[order[0]]
            fbest = fxs[order[0]]
            # Target reached? Then break and return
            if fbest <= target:
                # Report to callback if requested
                if callback is not None:
                    callback(transform(xbest), fbest)
                if verbose:
                    print('Target reached, halting')
                break
        # Report to callback if requested
        if callback is not None:
            callback(transform(xbest), fbest)
        # Show progress in verbose mode:
        if verbose:
            if iteration >= nextMessage:
                print(str(iteration) + ': ' + str(fbest))
                if iteration < 3:
                    nextMessage = iteration + 1
                else:
                    nextMessage = verbose * (1 + iteration // verbose)
    # Show stopping criterion
    if fbest > target:
        if verbose:
            print('Maximum iterations reached, halting')
    # Get final score at mu
    fmu = function(mu, *args)
    if fmu < fbest:
        if verbose:
            print('Final score at mu beats best sample')
        xbest = mu
        fbest = fmu
    # Show final value and return
    if verbose:
        print(str(iteration) + ': ' + str(fbest))
    return transform(xbest), fbest


class _TriangleWaveTransform(object):
    """
    Transforms parameters from an unbounded space to a bounded space, using a
    triangle waveform (``/\/\/\...``).
    """

    def __init__(self, lower, upper):
        self.lower = lower
        self.upper = upper
        self.range = upper - lower
        self.range2 = 2 * self.range

    def __call__(self, x, *args):
        y = np.remainder(x - self.lower, self.range2)
        z = np.remainder(y, self.range)
        return (
            (self.lower + z) * (y < self.range) +
            (self.upper - z) * (y >= self.range))


'''
def trr(f, x, ftol=1e-8, max_nfev=None, args=None):
    """
    Local optimizer that minimizes a function ``f`` using a trust-region
    reflective least squares optimization provided by SciPy [1].

    Arguments:

    ``f``
        A function to minimize. The function ``f(x)`` must be callable with
        ``x`` a sequence of ``m`` coordinates and should return a single scalar
        value.
    ``x``
        An initial guess for the ``x`` with the lowest ``f(x)``.
    ``ftol``
        The relative difference in ``f(x)`` beween iterations that is
        acceptable as convergence.
    ``max_nfev``
        The maximum number of function evaluations to perform.
    ``args``
        An optional tuple containing extra arguments to ``f``. If ``args`` is
        specified, ``f`` will be called as ``f(x, *args)``.

    The method returns a tuple ``(xopt, cost)`` where ``xopt`` is the best
    position found and ``cost`` is the associated cost function value
    calculated by the method.

    [1] http://scipy.org

    """
    #TODO Allow boundaries to be set
    #TODO Can we calculate max_nfev from max_iter and maintain the interface?
    try:
        from scipy.optimize import least_squares
    except ImportError:
        import scipy as sp # Let this raise an error if no scipy is installed
        v = [int(x) for x in sp.__version__.split('.')]
        if v[0] == 0 and v[1] < 17:
            raise ImportError('This method requires SciPy version 0.17.0 or'
                ' newer, found version ' + str(sp.__version__) + '.')
        raise
    # Check if function is callable
    if not callable(f):
        raise ValueError('The argument `f` must be a callable function.')
    # Check extra arguments
    if args is None:
        args = ()
    elif type(args) != tuple:
        raise ValueError('The argument `args` must be either None or a tuple.')
    # Check stopping criteria
    ftol = float(ftol)
    if max_nfev is not None:
        max_nfev = int(max_nfev)
        if max_nfev < 1:
            raise ValueError('Maximum number of function evaluations must be'
                ' at least 1 (or None).')
    res = least_squares(f, x, ftol=ftol, max_nfev=max_nfev, args=args,
        method='trf')
    return res.x, res.cost
'''


def voronoi_regions(x, y, f, xlim, ylim):
    """
    Takes a set of ``(x, y, f)`` points and returns the edgepoints of the
    x-y voronoi region around each point within the bounds specified by
    ``xlim`` and ``ylim``.

    Points and voronoi regions entirely outside the specified bounds will be
    dropped. Voronoi regions partially outside the bounds will be truncated.

    The third array ``f`` will be filtered the same way as ``x`` and ``y`` but
    is otherwise not used.

    Returns a tuple ``(x, y, f, regions)`` where ``x``, ``y`` and ``f`` are the
    coordinates of the accepted points and each ``regions[i]`` is a list of the
    vertices making up the voronoi region for point ``(x[i], y[i])``.

    The code to extract the voronoi regions was (heavily) adapted from:
    http://stackoverflow.com/a/20678647/423420

    *Note: This method requires SciPy to be installed.*
    """
    from scipy.spatial import Voronoi
    from itertools import izip  # Like zip, but works as an iterator

    # Check x, y, f
    x = np.asarray(x)
    y = np.asarray(y)
    f = np.asarray(f)
    if not (x.shape == y.shape == f.shape):
        raise ValueError('x, y and f must all have the same shape.')
    if len(x.shape) > 1:
        axis = -1
        for k, n in x.shape:
            if n > 1:
                if axis < 0:
                    axis = k
                else:
                    raise ValueError('x, y and f must be 1-dimensional.')
        n = x.shape[axis]
        x = x.reshape((n,))
        y = y.reshape((n,))
        f = f.reshape((n,))
    else:
        n = len(x)

    # Check limits
    xmin, xmax = [float(a) for a in sorted(xlim)]
    ymin, ymax = [float(a) for a in sorted(ylim)]

    # Drop any points outside the bounds
    # within_bounds = (x >= xmin) & (x <= xmax) & (y >= ymin) & (y <= ymax)
    # x = x[within_bounds]
    # y = y[within_bounds]
    # f = f[within_bounds]

    # Create voronoi diagram
    vor = Voronoi(np.array([x, y]).transpose())
    # The voronoi diagram consists of a number of ridges drawn between a set
    # of points.
    #   points          Are the points the diagram is based on.
    #   vertices        The coordinates of the vertices connecting the ridges
    #   ridge_points    Is a list of tuples (p1, p2) defining the points each
    #                   ridge belongs to. Points are given as their index in
    #                   the list of points.
    #   ridge_vertices  Is a list of vertices (v1, v2) defining the vertices
    #                   between which each ridge is drawn. Vertices are given
    #                   as their index in the list of vertice coordinates. For
    #                   ridges extending to infinity, one of the vertices will
    #                   be given as -1.
    # Get the center of the voronoi diagram's points and define a radius that
    # will bring us outside the visible area for any starting point / direction
    center = vor.points.mean(axis=0)
    radius2 = 2 * np.sqrt((xmax - xmin)**2 + (ymax - ymin)**2)
    # Create a list containing the set of vertices defining each region
    regions = [set() for i in range(n)]
    for (p1, p2), (v1, v2) in izip(vor.ridge_points, vor.ridge_vertices):
        # Ensure only v1 can every be -1
        if v1 > v2:
            v1, v2 = v2, v1
        # Get vertice coordinates
        x2 = vor.vertices[v2]  # Only v1 can be -1
        if v1 >= 0:
            # Finite vertex
            x1 = vor.vertices[v1]
        else:
            # Replacement vertex needed
            # Tangent line to points involved
            y1, y2 = vor.points[p1], vor.points[p2]
            t = y2 - y1
            t /= np.linalg.norm(t)
            # Normal line
            q = np.array([-t[1], t[0]])
            # Midpoint between involved points
            midpoint = np.mean([y1, y2], axis=0)
            # Point beyond the outer boundary
            x1 = x2 + np.sign(np.dot(midpoint - center, q)) * q * radius2
        # Add vertice coordinates to both region coordinate lists
        x1, x2 = tuple(x1), tuple(x2)  # arrays and lists aren't hashable
        regions[p1].update((x1, x2))
        regions[p2].update((x1, x2))

    # Order vertices in regions counter clockwise and remove regions outside of
    # the bounds.
    good_regions = []
    good_x = []
    good_y = []
    good_f = []
    for k, region in enumerate(regions):
        if len(region) == 0:
            continue
        # Convert set of tuples to 2d array
        region = np.asarray([np.asarray(v) for v in region])
        # Filter out any regions lying entirely outside the bounds
        if not (np.any((region[:, 0] > xmin) | (region[:, 0] < xmax)) or
                np.any((region[:, 1] > ymin) | (region[:, 1] < ymax))):
            continue
        # Sort vertices counter clockwise
        p = vor.points[k]
        angles = np.arctan2(region[:, 1] - p[1], region[:, 0] - p[0])
        region = region[np.argsort(angles)]
        # Store
        good_regions.append(region)
        good_x.append(p[0])
        good_y.append(p[1])
        good_f.append(f[k])
    regions = good_regions
    x = np.asarray(good_x)
    y = np.asarray(good_y)
    f = np.asarray(good_f)
    del(good_regions, good_x, good_y, good_f)

    # Truncate regions at limits
    for i, region in enumerate(regions):
        # Skip contained regions
        if not np.any((region[:, 0] < xmin) | (region[:, 0] > xmax) |
                      (region[:, 1] < ymin) | (region[:, 1] > ymax)):
            continue
        # Drop points outside of boundary and replace by 0, 1 or 2 new points
        # on the actual boundaries.
        # Run twice: once for x violations, once for y violations (two
        # successive corrections may be needed, to solve corner issues).
        new_region = []
        for j, p in enumerate(region):
            if p[0] < xmin:
                q = region[j - 1] if j > 0 else region[-1]
                r = region[j + 1] if j < len(region) - 1 else region[0]
                if q[0] < xmin and r[0] < xmin:
                    # Point connecting two outsiders: drop
                    continue
                if q[0] >= xmin:
                    # Add point on line p-q
                    s = p[1] + (xmin - p[0]) * (q[1] - p[1]) / (q[0] - p[0])
                    new_region.append(np.array([xmin, s]))
                if r[0] >= xmin:
                    # Add point on line p-r
                    s = p[1] + (xmin - p[0]) * (r[1] - p[1]) / (r[0] - p[0])
                    new_region.append(np.array([xmin, s]))
            elif p[0] > xmax:
                q = region[j - 1] if j > 0 else region[-1]
                r = region[j + 1] if j < len(region) - 1 else region[0]
                if q[0] > xmax and r[0] > xmax:
                    # Point connecting two outsiders: drop
                    continue
                if q[0] <= xmax:
                    # Add point on line p-q
                    s = p[1] + (xmax - p[0]) * (q[1] - p[1]) / (q[0] - p[0])
                    new_region.append(np.array([xmax, s]))
                if r[0] <= xmax:
                    # Add point on line p-r
                    s = p[1] + (xmax - p[0]) * (r[1] - p[1]) / (r[0] - p[0])
                    new_region.append(np.array([xmax, s]))
            else:
                # Point is fine, just add
                new_region.append(p)
        region = new_region
        # Run again for y-violations
        new_region = []
        for j, p in enumerate(region):
            if p[1] < ymin:
                q = region[j - 1] if j > 0 else region[-1]
                r = region[j + 1] if j < len(region) - 1 else region[0]
                if q[1] < ymin and r[1] < ymin:
                    # Point connecting two outsiders: drop
                    continue
                if q[1] >= ymin:
                    # Add point on line p-q
                    s = p[0] + (ymin - p[1]) * (q[0] - p[0]) / (q[1] - p[1])
                    new_region.append(np.array([s, ymin]))
                if r[1] >= ymin:
                    # Add point on line p-r
                    s = p[0] + (ymin - p[1]) * (r[0] - p[0]) / (r[1] - p[1])
                    new_region.append(np.array([s, ymin]))
            elif p[1] > ymax:
                q = region[j - 1] if j > 0 else region[-1]
                r = region[j + 1] if j < len(region) - 1 else region[0]
                if q[1] > ymax and r[1] > ymax:
                    # Point connecting two outsiders: drop
                    continue
                if q[1] <= ymax:
                    # Add point on line p-q
                    s = p[0] + (ymax - p[1]) * (q[0] - p[0]) / (q[1] - p[1])
                    new_region.append(np.array([s, ymax]))
                if r[1] <= ymax:
                    # Add point on line p-r
                    s = p[0] + (ymax - p[1]) * (r[0] - p[0]) / (r[1] - p[1])
                    new_region.append(np.array([s, ymax]))
            else:
                # Point is fine, just add
                new_region.append(p)
        # Replace region by new one
        regions[i] = new_region
    # Return output
    return x, y, f, regions


#
# The _Worker class used to be a nested class, nested inside ParallelEvaluator
# However, for some reason nested classes cannot be pickled, which is a problem
# when trying to do multiprocessing on Windows.
#
class _Worker(multiprocessing.Process):
    """
    Worker class for use with :class:`ParallelEvaluator`.

    Evaluates a single-valued function for every point in a ``tasks`` queue
    and places the results on a ``results`` queue.

    Keeps running until it's given the string "stop" as a task.

    Arguments:

    ``function``
        The function to optimize.
    ``args``
        A (possibly empty) tuple containing extra input arguments to the
        objective function.
    ``tasks``
        The queue to read tasks from. Tasks are stored as tuples
        ``(i, p)`` where ``i`` is a task id and ``p`` is the
        position to evaluate.
    ``results``
        The queue to store results in. Results are stored as
        tuples ``(i, p, r)`` where ``i`` is the task id, ``p`` is
        the position evaluated (which can be updated by the
        refinement method!) and ``r`` is the result at ``p``.
    ``max_tasks``
        The maximum number of tasks to perform before dying.
    ``errors``
        A queue to store exceptions on
    ``error``
        This flag will be set by the worker whenever it encounters an
        error.

    *Extends:* ``multiprocessing.Process``
    """

    def __init__(
            self, function, args, tasks, results, max_tasks, errors, error):
        super(_Worker, self).__init__()
        self.daemon = True
        self._function = function
        self._args = args
        self._tasks = tasks
        self._results = results
        self._max_tasks = max_tasks
        self._errors = errors
        self._error = error

    def run(self):
        # Worker processes should never write to stdout or stderr.
        # This can lead to unsafe situations if they have been redicted to
        # a GUI task such as writing to the IDE console.
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')
        try:
            for k in range(self._max_tasks):
                i, x = self._tasks.get()
                f = self._function(x, *self._args)
                self._results.put((i, f))

                # Check for errors in other workers
                if self._error.is_set():
                    return

        except (Exception, KeyboardInterrupt, SystemExit):
            self._errors.put((self.pid, traceback.format_exc()))
            self._error.set()


def xnes(
        f, bounds, hint=None, n=None, parallel=False, target=1e-6,
        max_iter=1000, callback=None, verbose=False, args=None):
    """
    Global/local optimizer that minimizes a function ``f`` within a specified
    set of ``bounds`` using the xNES method described in [1, 2].

    xNES stands for Exponential Natural Evolution Strategy, and is
    designed for non-linear derivative-free optimization problems [1].

    A parallel (multiprocessing) version of the algorithm can be run by setting
    ``parallel`` to ``True``. Please keep in mind that the objective function
    ``f`` cannot access any shared memory in this scenario. See
    :class:`ParallelEvaluator` for details.

    The method will stop when one of the following criteria is met:

    1. The value of ``f(x)`` is smaller than ``target``.
    2. The maximum number of iterations is reached.

    Arguments:

    ``f``
        A function to minimize. The function ``f(x)`` must be callable with
        ``x`` a sequence of ``m`` coordinates and should return a single scalar
        value.
    ``bounds``
        A list of ``m`` tuples ``(min_i, max_i)`` specifying the minimum and
        maximum values in the search space for each dimension ``i``.
    ``hint=None``
        A suggested starting point. Must be within the given bounds. If no
        hint is given the center of the parameter space is used. A (uniform)
        random point can be selected by setting ``hint='random'``.
    ``n=None``
        Can be used to manually overrule the population size used in xNES. By
        default, this is set to be `4+int(3*np.log(d))` where ``d`` is the
        number of dimensions of the search space. When running in parallel,
        Myokit will round this default value up to the nearest multiple of the
        cpu count. To overrule these defaults, use this parameter.
    ``parallel=False``
        Set this to ``True`` to run a multi-process version of the search that
        utilizes all available cores. See :class:`EvaluatorProcess` for the
        details of using multi-process parallelisation and the requirements
        this places on the function ``f``.
    ``target=1e-6``
        The value of ``f(x)`` that is acceptable for convergence.
    ``max_iter=500``
        The maximum number of iterations to perform.
    ``callback=None``
        An optional function to be called after each iteration with arguments
        ``(pg, fg)`` where ``pg`` is the current best position and ``fg`` is
        the corresponding score.
    ``verbose=False``
        Set to ``True`` to have progress information printed to the terminal.
        If set to any non-zero integer this will determine the number of
        iterations between updates.
    ``args=None``
        An optional tuple containing extra arguments to ``f``. If ``args`` is
        specified, ``f`` will be called as ``f(x, *args)``.

    The method returns a tuple ``(xbest, fbest)`` where ``xbest`` is the best
    position found and ``fbest = f(xbest)``.

    References:

    [1] Glasmachers, Schaul, Schmidhuber et al. (2010) Exponential natural
    evolution strategies.
    Proceedings of the 12th annual conference on Genetic and evolutionary
    computation

    [2] PyBrain: The Python machine learning library (http://pybrain.org)

    *Note: This method requires the `scipy` module to be installed.*

    """
    import scipy
    import scipy.linalg

    # Test if function is callable
    if not callable(f):
        raise ValueError('The argument f must be a callable function.')

    # Test extra arguments
    if args is None:
        args = ()
    elif type(args) != tuple:
        raise ValueError(
            'The argument `args` must be either None or a tuple.')

    # Get dimension of the search space
    d = len(bounds)
    if d < 1:
        raise ValueError('Dimension must be at least 1.')

    # Check bounds
    lower = np.zeros(d)
    upper = np.zeros(d)
    for i, b in enumerate(bounds):
        if len(b) != 2:
            raise ValueError(
                'Each entry in `bounds` must be a tuple `(min, max)`.')
        lo, up = float(b[0]), float(b[1])
        if not lo < up:
            raise ValueError(
                'The lower bounds must be smaller than the upper bounds.')
        lower[i] = lo
        upper[i] = up
    del(bounds)

    # Create periodic parameter space transform to implement boundaries
    transform = _TriangleWaveTransform(lower, upper)

    # Wrap transform around score function
    function = _ParameterTransformWrapper(f, transform)

    # Check hint
    if hint is None:
        hint = lower + 0.5 * (upper - lower)
    elif hint == 'random':
        hint = lower + np.random.uniform(0, 1, d) * (upper - lower)
    else:
        hint = np.array(hint, copy=True)
        if hint.shape != lower.shape:
            raise ValueError('Hint must have the shape ' + str(lower.shape))
        if np.any(hint < lower) or np.any(hint > upper):
            j = np.argmax(np.logical_or(hint < lower, hint > upper))
            raise ValueError(
                'Hint must be within the specified bounds (error with'
                ' parameter ' + str(1 + j) + ').')

    # Check if parallelization is required
    parallel = bool(parallel)

    # Set population size
    if n is None:
        # Explicitly set default
        n = 4 + int(3 * np.log(d))
        # If parallel, round up to a multiple of the reported number of cores
        if parallel:
            cpu_count = multiprocessing.cpu_count()
            n = (((n - 1) // cpu_count) + 1) * cpu_count
    else:
        # Custom population size
        n = int(n)
        if n < 1:
            raise ValueError(
                'Population size must be `None` or non-zero integer')

    # Parse verbose argument
    if verbose is True:
        verbose = 100
    else:
        verbose = int(verbose)
        if verbose <= 0:
            verbose = False

    # Show configuration info
    if verbose:
        if parallel:
            print('Running in parallel mode with population size ' + str(n))
        else:
            print('Running in sequential mode with population size ' + str(n))

    # Check convergence critera
    max_iter = int(max_iter)
    if max_iter < 1:
        raise ValueError('Maximum iterations must be greater than zero.')
    target = float(target)

    # Check callback function
    if callback is not None:
        if not callable(callback):
            raise ValueError(
                'Argument `callback` must be a callable function or `None`.')

    # Create evaluator object
    if parallel:
        evaluator = ParallelEvaluator(function, args=args)
    else:
        evaluator = SequentialEvaluator(function, args=args)

    # Set up progress reporting in verbose mode
    nextMessage = 0

    # Set up algorithm
    # Learning rates
    eta_mu = 1
    eta_A = 0.6 * (3 + np.log(d)) * d ** -1.5

    # Pre-calculated utilities
    us = np.maximum(0, np.log(n / 2 + 1) - np.log(1 + np.arange(n)))
    us /= np.sum(us)
    us -= 1 / n

    # Center of distribution
    mu = hint

    # Square root of covariance matrix
    A = np.eye(d)

    # Identity matrix for later use
    I = np.eye(d)

    # Best solution found
    xbest = hint
    fbest = function(hint, *args)

    # Report first point
    if callback is not None:
        callback(np.array(hint, copy=True), fbest)

    # Start running
    for iteration in range(1, 1 + max_iter):

        # Create new samples
        zs = np.array([np.random.normal(0, 1, d) for i in range(n)])
        xs = np.array([mu + np.dot(A, zs[i]) for i in range(n)])

        # Evaluate at the samples
        fxs = evaluator.evaluate(xs)

        # Order the normalized samples according to the scores
        order = np.argsort(fxs)
        zs = zs[order]

        # Update center
        Gd = np.dot(us, zs)
        mu += eta_mu * np.dot(A, Gd)

        # Update best if needed
        if fxs[order[0]] < fbest:
            xbest = xs[order[0]]
            fbest = fxs[order[0]]

            # Target reached? Then break and return
            if fbest <= target:
                # Report to callback if requested
                if callback is not None:
                    callback(transform(xbest), fbest)
                if verbose:
                    print('Target reached, halting')
                break

        # Report to callback if requested
        if callback is not None:
            callback(transform(xbest), fbest)

        # Show progress in verbose mode:
        if verbose:
            if iteration >= nextMessage:
                print(str(iteration) + ': ' + str(fbest))
                if iteration < 3:
                    nextMessage = iteration + 1
                else:
                    nextMessage = verbose * (1 + iteration // verbose)

        # Update root of covariance matrix
        Gm = np.dot(np.array([np.outer(z, z).T - I for z in zs]).T, us)
        A *= scipy.linalg.expm(np.dot(0.5 * eta_A, Gm))

    # Show stopping criterion
    if fbest > target:
        if verbose:
            print('Maximum iterations reached, halting')

    # Get final score at mu
    fmu = function(mu, *args)
    if fmu < fbest:
        if verbose:
            print('Final score at mu beats best sample')
        xbest = mu
        fbest = fmu

    # Show final value and return
    if verbose:
        print(str(iteration) + ': ' + str(fbest))
    return transform(xbest), fbest
