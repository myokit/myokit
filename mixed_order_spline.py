# From approx.py
def fit_mixed_order_polynomial(f, i, abstol=1e-4, reltol=1e-3, max_pieces=20,
        max_order=7):
    """
    Returns a piecewise polynomial fit to ``f`` on the given interval
    ``i=[a,b]``.

    The method starts by applying a single first-order polynomial fit. If this
    fails, the order of the polynomial is increased and the fit is re-tested
    until ``max_order`` is met. If no fit can be made even with the highest
    allowable order the interval is split at the point of largest difference
    with a linear fit and each interval is treated separatly. This process
    continues until the specified tolerance is met or the number of pieces
    exceeds ``max_pieces``.

    Returns a tuple ``(c, p, g, a, r)`` where ``p`` is a sorted vector of
    ``n + 1`` knots on the interval ``[a,b]`` and ``c`` is a list of polynomial
    coefficients for ``n`` polynomials. A PiecewisePolynomail representing the
    fitted function is returned as ``g``. The maximum absolute error between
    ``f`` and ``g`` on the given interval is returned as ``a`` and an estimate
    for the maximum relative error is given as ``r``. (Here "relative error" is
    calculated as ``a`` divided by an estimation of ``f``'s range on i.)

    If no fit can be made a FittingError is raised.
    """
    # Check interval
    try:
        if len(i) != 2:
            raise ValueError('The given interval must have length 2')
    except TypeError:
        raise ValueError('The given interval must contain two values.')
    a, b = i
    if a >= b:
        raise ValueError('The first point in the interval must be smaller than'
            ' the second.')
    a, b = float(a), float(b)
    # Check function
    try:
        f(a)
    except TypeError:
        raise ValueError('The given function must have a single positional'
            ' argument.')
    # Estimate range of function
    n_test_points = 1000
    X = np.linspace(a, b, n_test_points)
    F = f(X)
    H = np.max(F) - np.min(F)
    def fit_part(lo, hi, parts, n_pieces):
        # Appends list of tuples (coeffs, points, rel_max_error)
        n_pieces += 1
        x = np.linspace(lo, hi, n_test_points)
        fit = None
        for n in xrange(1, max_order+1):
            try:
                c,g,a = fit_remez_polynomial(f, (lo, hi), n)
            except ValueError:
                continue
            r = a / H
            fit = c, (lo, hi), a, r
            if a < abstol and r < reltol:
                parts.append(fit)
                return n_pieces
        if fit is None:
            raise FittingError('Unable to create any kind of fit on part of'
                ' interval.')
        if n_pieces >= max_pieces:
            parts.append(fit)
            return n_pieces
        # Divide and continue
        c,g,a = fit_remez_polynomial(f, (lo, hi), 1)
        im = np.argmax(abs(g(x) - f(x)))
        if im == 0 or im == n_test_points - 1:
            im = n_test_points / 2
        xm = x[im]
        n_pieces -= 1
        n_pieces = fit_part(lo, xm, parts, n_pieces)
        n_pieces = fit_part(xm, hi, parts, n_pieces)
        return n_pieces
    # Get fit
    parts = []
    n_pieces = fit_part(a, b, parts, 0)
    if n_pieces > max_pieces:
        raise FittingError('Unable to create fit with allowed number of'
            ' pieces.')
    # Translate parts into output arguments
    c = []
    p = [parts[0][1][1]]
    a = 0
    r = 0
    for part in parts:
        c.append(part[0])
        p.append(part[1][1])
        if part[2] > a: a = part[2]
        if part[3] > r: r = part[3]
    # Test if conditions met
    if a >= abstol or r >= reltol:
        raise FittingError('Unable to reach specified tolerance.')
    # Return created function
    g = PiecewisePolynomial(p, c)
    return c, p, g, a, r
def solve_mixed_order_spline(f, x, d, criterium=None):
    """
    Fits a mixed-order spline ``f`` to the function ``f`` using the knots
    given by ``x``. At every knot, the first d-derivatives of the connecting
    pieces are guaranteed to be equal (making the spline class d
    differentiable).

    Returns a tuple ``(c, g, a)`` where ``c`` is a list of polynomial
    coefficients for ``n=len(x)-1`` polynomials. A numpy function calculating
    the fitted function is returned as ``g``. And the maximum absolute error
    between ``f`` and ``g`` on the interval ``[x[0], x[-1]] is returned as
    ``a``.

    If no fit can be made a FittingError is raised.

    # UNRESOLVED

    Because these splines are not unique, all possible solutions are tested and
    the best solution is returned. By default, solutions are compared by
    searching for the (estimated) lowest maximum difference between ``f`` and
    ``g``. This
    behavior can be changed by passing in a function handle ``criterium(f, g)``
    that returns a single float. The coefficients for the function with the
    lowest ``criterium()`` value will be returned.

    OR

    Using a random selection of dof per knot

    OR

    Some intelligent way of doing it I've yet to find

    # /UNRESOLVED
    """
    # Number of pieces
    n = len(x) - 1
    if n % 2 == 0:
        raise ValueError('Number of pieces must be odd.')
        # For now, this is easiest #TODO
    # Ensure x is np array
    if not isinstance(x, np.ndarray):
        x = np.array(x, copy=False)
    # Comparison criterium
    if criterium is None:
        n_test_points = 10000
        X = np.linspace(x[0], x[-1], n_test_points)
        #F = f(X)
        def criterium(f, g):
            G = g(X)
            G = G[1:]-G[:-1] # Deriv one (with multiplier)
            G = G[1:]-G[:-1] # Deriv two (with multiplier)
            return np.sum(G*G) # Integral of square
            #return np.max(np.abs(g(X) - F))
    # One piece? Then return simple polynomial matching both x's
    if n == 1:
        fxo = f(x[0])
        slope = (f(x[1]) - fxo) / (x[1] - x[0])
        fxo -=  slope * x[0]
        c = [fxo, slope]
        def g(xx):
            return fxo + slope * xx
        a = criterium(f, g)
        return c, g, a
    # Dof deficit per piece
    dof_deficit = np.zeros(n,dtype=int)
    dof_deficit[1::2] += d
    #print('Deficit',dof_deficit)
    # Minimum dof per piece
    dof_minimum = 2 * np.ones(n,dtype=int)
    dof_minimum[1::2] += d
    #print('Minimum',dof_minimum)
    # Define fitting function
    def fit(dof):
        # Get values at nodes
        F = f(x)
        # Get powers of x
        max_dof = np.max(dof)
        P = [np.ones(len(x))]
        for i in xrange(0, max_dof):
            P.append(P[-1] * x)
        # Get factorials up to max_dof
        factorials = np.ones(1+max_dof, dtype=int)
        for i in xrange(2, 1+max_dof):
            factorials[i:] *= i
        # Get polynomial derivative coefficients z[k][j] = j! / (j - k)!
        Z = []
        for k in xrange(0, 1+d):    # k-th derivative
            zz = np.zeros(max_dof, dtype=int)
            for j in xrange(k, max_dof):
                zz[j] = factorials[j] / factorials[j - k]
            Z.append(zz)
        # Number of equations
        ne = int(2*n + d*(n-1))
        # Construct matrix
        A = np.zeros((ne, ne))
        B = np.zeros(ne)
        # Add top rows: ends of each polynomial must match f
        dofsum = 0
        for i in xrange(0, n):
            for k in xrange(0, dof[i]):
                j = dofsum + k
                A[2*i,   j] = P[k][i]
                A[2*i+1, j] = P[k][i+1]
            dofsum += dof[i]
            B[2*i  ] = F[i]
            B[2*i+1] = F[i+1]
        # Add bottom rows: polynomials must have d equal derivatives at
        # connections
        isum = 2 * n
        jsum = 0
        joff = 0
        sign = 1
        for i in xrange(1, n):              # i-th connection
            for k in xrange(1, d+1):        # k-th derivative
                joff = jsum
                for j in xrange(k, dof[i-1]):
                    A[isum, joff + j] = sign * P[j-k][i] * Z[k][j]
                joff += dof[i-1]
                for j in xrange(k, dof[i]):
                    A[isum, joff + j] = -sign * P[j-k][i] * Z[k][j]
                isum += 1
            sign *= -1
            jsum = joff
        # Find coefficients
        C = np.linalg.solve(A, B)
        # Reformat coefficients for polynomial builder
        c = []
        offset = 0
        for nc in dof:
            c.append(C[offset:offset+nc])
            offset += nc
        return c
    """
    # Strategy 1: Test all possible dofs

    # Define dof distributing function
    def distribute_dofs(initial_dofs, dof_deficit, max_dof):
        n = len(initial_dofs)
        if len(dof_deficit) != n:
            raise ValueError('Both sequences must have same size.')
        def distr(i, dof, dofs):
            ndist = int(dof_deficit[i])
            if i == 0:
                for a in xrange(ndist, -1, -1):
                    d2 = np.array(dof)
                    d2[i  ] += a
                    d2[i+1] += ndist - a
                    if d2[i] > max_dof or d2[i+1] > max_dof:
                        continue
                    distr(i + 1, d2, dofs)
                return
            if i + 1 == n:
                for a in xrange(ndist, -1, -1):
                    d2 = np.array(dof)
                    d2[-2] += a
                    d2[-1] += ndist - a
                    if d2[-2] > max_dof or d2[-1] > max_dof:
                        continue
                    dofs.append(d2)
                return
            else:
                for a in xrange(ndist, -1, -1):
                    for b in xrange(ndist - a, -1, -1):
                        d2 = np.array(dof)
                        d2[i-1] += a
                        d2[i  ] += b
                        d2[i+1] += ndist - a - b
                        if (d2[i-1] > max_dof or d2[i] > max_dof
                                or d2[i+1] > max_dof):
                            continue
                        distr(i + 1, d2, dofs)
                return
        dofs = []
        distr(0, initial_dofs, dofs)
        return dofs
    # Try (sample of) all different dof distributions
    dofs = distribute_dofs(dof, dd, d + 3) # Stick to B-splines
    abest = None
    cbest = None
    gbest = None
    ibest = None
    N_MAX = 200
    if len(dofs) > N_MAX:
        import random
        dofs = random.sample(dofs, N_MAX)
    for i, dof in enumerate(dofs):
        try:
            c = fit(dof)
            g = PiecewisePolynomial(x, c)
            a = criterium(f, g)
            if abest is None or a < abest:
                ibest = i
                abest = a
                cbest = c
                gbest = g
        except np.linalg.LinAlgError:
            pass
    if cbest is None:
        msg = 'Unable to find a fit.'
        if len(x) < 5:
            msg += ' Try adding more knots.'
        raise FittingError(msg)
    return (cbest, gbest, abest)
    """
    """
    # Strategy 2: Try some random distributions

    import random
    dof_org = np.array(dof)
    abest = None
    cbest = None
    gbest = None
    N_TRIES = 20
    for i in xrange(N_TRIES):
        dof = np.array(dof_org)
        for j in xrange(int(dd[0])):
            #dof[np.argmin(dof[0:2])] += 1
            dof[random.randint(0,1)] += 1
        for j in xrange(int(dd[-1])):
            #dof[n-2+np.argmin(dof[-2:])] += 1
            dof[random.randint(-2,-1)] += 1
        for i in xrange(1, n):
            for j in xrange(int(dd[i])):
                #dof[i-1+np.argmin(dof[i-1:i+2])] += 1
                dof[random.randint(i-1, i+1)] += 1
        try:
            c = fit(dof)
            g = PiecewisePolynomial(x, c)
            a = criterium(f, g)
            if abest is None or a < abest:
                abest = a
                cbest = c
                gbest = g
        except np.linalg.LinAlgError:
            pass
    if cbest is None:
        msg = 'Unable to find a fit.'
        if len(x) < 5:
            msg += ' Try adding more knots.'
        raise FittingError(msg)
    return (cbest, gbest, abest)
    """
    # Strategy 3. Start with a reasonable guess, try to optimize
    #
    # Initial degrees of freedom (#coefficients)
    dof = np.array(dof_minimum)
    dof[2::2] += d                  # Pass all free dof to right-most neighbour
    dof[0] = 2 + np.floor(0.5*d)    # Very last one shares some dof with
    dof[-1] = 2 + np.ceil(0.5*d)    # very first one.
    #print('Initial',dof)
    c = fit(dof)
    g = PiecewisePolynomial(x, c)
    a = criterium(f, g)
    cbest = c
    abest = a
    gbest = g
    dbest = dof
    import random
    #print('Initial',a)
    TIMES = min((d+1)*(n // 2), 15000)
    #print('times',TIMES)
    #print('n,d',n, d)
    for i in xrange(0, TIMES):
        # Make random switch
        dof = np.array(dbest)
        k = 2 * random.randint(0, (n - 3) / 2)
        while dof[k] <= dof_minimum[k]:
            k = 2 * random.randint(0, (n - 3) / 2)
        dof[k] -= 1
        dof[k+2] += 1
        #print(dof, dbest)
        try:
            c = fit(dof)
            g = PiecewisePolynomial(x, c)
            a = criterium(f, g)
            if a < abest:
                abest = a
                cbest = c
                gbest = g
                dbest = dof
                #print('New best',a)
        except np.linalg.LinAlgError:
            #print('FAIL!')
            pass
    # Calculate a
    n_test_points = 10000
    X = np.linspace(x[0], x[-1], n_test_points)
    abest = np.max(np.abs(f(X) - gbest(X)))
    return (cbest, gbest, abest)
def fit_mixed_order_spline(f, i, d=5, abstol=None, reltol=0.01, min_pieces=3,
    max_pieces=16, spacing='uniform'):
    """
    Returns a v-spline fit to ``f`` on the given interval ``i=[a,b]``. The
    first ``d`` derivatives of all pieces of the spline are guaranteed to be
    equal at the knots.

    Returns a tuple ``(c, p, g, a, r)`` where ``p`` is a sorted vector of
    ``n - 1`` nodes on the interval ``[a,b]`` and ``c`` is a list of polynomial
    coefficients for ``n`` polynomials. A numpy function calculating the fitted
    function is returned as ``g``. The maximum absolute error between ``f`` and
    ``g`` on the given interval is returned as ``a`` and an estimate for the
    maximum relative error is given as ``r``. (Here "relative error" is
    calculated as ``a`` divided by an estimation of ``f``'s range on i.)

    The knots can be placed in different manners:

    ``spacing="uniform"``
        Uses evenly spaced points
    ``spacing="chebyshev"``
        Uses chebyshev spaced points
    ``spacing="largest_piece"``
        Adds new points in the center of the largest piece
    ``spacing="largest_error"``
        Adds new points at the position of the largest error

    Best results are obtained when min_pieces and max_pieces are *even*
    numbers.
    """
    # Check interval
    try:
        if len(i) != 2:
            raise ValueError('The given interval must have length 2')
    except TypeError:
        raise ValueError('The given interval must contain two values.')
    lb, rb = i
    if lb >= rb:
        raise ValueError('The first point in the interval must be smaller'
            ' than the second.')
    lb, rb = float(lb), float(rb)
    # Check function
    try:
        f(lb)
    except TypeError:
        raise ValueError('The given function must have a single positional'
            ' argument.')
    # Check number of pieces
    if min_pieces < 2:
        raise ValueError('min_pieces must be 2 or higher.')
    if min_pieces > max_pieces:
        raise ValueError('min_pieces must be smaller than max_pieces')
    # Check knot placement
    UNIFORM = 0
    CHEBYSHEV = 1
    LARGEST_PIECE = 2
    LARGEST_ERROR = 3
    spacing_types = {
        'uniform' : UNIFORM,
        'chebyshev' : CHEBYSHEV,
        'largest_piece' : LARGEST_PIECE,
        'largest_error' : LARGEST_ERROR,
        }
    try:
        spacing = spacing_types[spacing]
    except KeyError:
        raise ValueError('spacing must be one of: ['
            + ', '.join([str(x) for x in spacing_types.iteritems()]) + ']')
    # Get estimate of range of function
    n_test_points = 10000
    X = np.linspace(lb, rb, n_test_points)
    F = f(X)
    H = np.max(F) - np.min(F)
    # Best found
    abest = None
    cbest = None
    # n = number of pieces
    if spacing in (LARGEST_PIECE, LARGEST_ERROR):
        x = list(np.linspace(lb, rb, min_pieces + 1))
    # Skip even numbers of points (there are n+1 points so n should be even!)
    for n in xrange(min_pieces, 1 + max_pieces, 2):
        if spacing == UNIFORM:
            print('n =', n)
            # Use uniformly spaced points
            x = np.linspace(lb, rb, n + 1)
        elif spacing == CHEBYSHEV:
            # Use langrange-spaced points
            x = np.arange(n, -1, -1)  # Returns n + 1 points [n, n-1, ..., 0]
            x = np.cos(np.pi * (2*x + 1) / (2*(n+1)))
            x = lb + 0.5 * (x + 1) * (rb - lb)
        try:
            # Fit spline, returns (coeff, absolute error, function handle)
            c, g, a = solve_mixed_order_spline(f, x, d)
            # Estimate relative error
            r = a / H
            if r < reltol and (abstol is None or a < abstol):
                p = np.array(x[1:-1])
                return (c, p, g, a, r)
            if n == max_pieces:
                break
        except FittingError:
            pass
        if spacing == LARGEST_ERROR:
            raise ValueError('Not right now please')
            # Find position with largest error
            e = np.argmax(np.abs(F - g(X)))
            x.append(X[e])
            x.sort()
        elif spacing == LARGEST_PIECE:
            # Unable to find fit, add point in middle of largest piece
            raise ValueError('Not right now please')
            xx = np.array(x)
            yy = f(xx)
            xx = xx[1:] - xx[:-1]
            yy = yy[1:] - yy[:-1]
            dd = xx ** 2 + yy ** 2
            dd = np.argmax(dd)
            x.append(0.5*(x[dd] + x[dd + 1]))
            x.sort()
    raise FittingError('Unable to reach requested tolerance.')






# From simplify.py
class PiecewisePolynomialFitter(Fitter):
    """
    Attempts to simplify a myokit model by approximating functions of a
    single variable with a known range (typically the membrane potential).

    Initially, the function will try to fit a single polynomial of increasing
    degree. If this fails, the domain will be split at the point of maximum
    error and the routine re-run for both parts separately.
    """
    name = 'piecewise_polynomial'
    def __init__(self):
        super(PiecewisePolynomialFitter, self).__init__()
        self.max_order = 5
        self.max_pieces = 10
    def _simplify(self, model, lhs, rng, report):
        var = lhs.var()
        # Build report
        if report:
            self.log('Loading modules to build report')
            from myokit.mxml import TinyHtmlPage
            import matplotlib.pyplot as pl
            # Create report directories
            report = os.path.abspath(report)
            self.log('Saving report to ' + str(report))
            if not os.path.isdir(report):
                self.log('Creating directory...')
                os.makedirs(report)
            # Create html page
            page = TinyHtmlPage()
            title = 'Simplifying ' + model.qname()
            page.set_title(title)
            page.append('h1').text(title)
            page.append('h2').text('Method: ' + self.name.upper())
            div = page.append('div')
            div.append('p').text('Attempting to simplify equations by'
                ' replacing them with a piecewise polynomial.')
            div.append('p').text('Each part has order at most '
                + str(self.max_order) + '.')
            div.append('p').text('Each part has at most '
                + str(self.max_pieces) + ' pieces.')
            div.append('p').text('Accepting approximations if the (estimated)'
                ' maximum error divided by the (estimated) range is less than '
                + str(self.rel_tol) + '.')
            div.append('p').text('Simplifying with respect to ' + str(lhs)
                + ' in the range ' + str(rng) + '.')
        # Replacement functions will be stored here
        fits = {}
        # Get list of suitable lhs,rhs pairs
        suitable = suitable_expressions(model, lhs)
        # Attempt approximations
        count = 0
        for v, rhs in suitable:
            count += 1
            name = v.var().qname()
            # Create python function for evaluations
            f = v.var().pyfunc()
            # Indicate interesting variable has been found
            self.log('Selected: ' + name + ' = ' + str(rhs))
            # Attempt fits of increasing order
            fit = g = abs_err = rel_err = None
            try:
                c, p, g, abs_err, rel_err = approx.fit_mixed_order_polynomial(
                    f, rng, max_order=self.max_order,
                    max_pieces=self.max_pieces)
                n = len(p) + 1
                if rel_err < self.rel_tol:
                    self.log('Found good approximation with '+str(n)+' pieces')
                    fit = g.myokit_form(lhs)
                    self.log('App: ' + fit.code())
            except approx.FittingError as e:
                self.log('FittingError: ' + str(e))
            except Exception as e:
                import traceback
                self.log('Exception ' + '* '*29)
                self.log('')
                self.log(traceback.format_exc())
                self.log('')
                self.log('* '*34)
            if report:
                div = page.append('div')
                div.set_attr('style', 'page-break-before: always;')
                div.append('h2').text(str(count) + '. ' + name)
                div.append('p').math(rhs)
                # Create figure
                pl.figure()
                ax = pl.subplot(111)
                xplot = np.linspace(rng[0], rng[1], 1000)
                pl.plot(xplot, f(xplot), label='f(x)', lw=3)
                if g:
                    pl.plot(xplot, g(xplot), label='L_'+str(n))
                    # Show nodes
                    xnodes = [rng[0]]
                    xnodes.extend(p)
                    xnodes.append(rng[1])
                    xnodes = np.array(xnodes)
                    pl.plot(xnodes, f(xnodes), 'x', label='nodes',markersize=8)
                # Wrote report
                if fit:
                    div.append('h3').text('Accepted approximation using '
                         + str(n) + ' pieces.')
                    #ps = ', '.join(['{:< 1.4e}'.format(x) for x in xnodes])
                    #div.append('p').text('Endpoints at [' + ps + '].')
                else:
                    div.append('h3').text('No acceptable approximation found.')
                div.append('p').text('Max absolute error is ' + str(abs_err))
                div.append('p').text('Max relative error is ' + str(rel_err))
                # Add plot to report
                box = ax.get_position()
                ax.set_position([box.x0,box.y0, box.width*0.8, box.height])
                ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
                iname = os.path.join(report, name + '.png')
                self.log('Saving plot to ' + iname)
                pl.savefig(iname)
                pl.close()
                div.append('h3').text('Graphical representation')
                div.append('img').set_attr('src', iname)
            # Save change to dict
            if fit:
                self.log('Saving approximation...')
                fits[v.var()] = fit
            else:
                self.log('No suitable approximation found.')
        # Create updated model
        for var, fit in fits.iteritems():
            var.set_rhs(fit)
        # Validate model, enable crude fixes!
        model.validate(fix_crudely = True)
        # Write report(s) to file
        if report:
            fname = os.path.join(report, 'index.html')
            self.log('Writing report to ' + fname)
            with open(fname, 'w') as f:
                f.write(page.html(pretty=False))
        # Return updated model
        self.log('Returning model...')
        return model
class MixedOrderSplineFitter(Fitter):
    """
 
    """
    name = 'mixed_order_spline'
    def __init__(self, d=5, abstol=None, reltol=0.01, max_pieces=16):
        super(MixedOrderSplineFitter, self).__init__()
        self.d = d
        self.reltol = reltol
        self.abstol = abstol
        self.max_pieces = max_pieces
    def _simplify(self, model, lhs, rng, report):
        var = lhs.var()
        # Build report
        if report:
            self.log('Loading modules to build report')
            from myokit.mxml import TinyHtmlPage
            import matplotlib.pyplot as pl
            # Create report directories
            report = os.path.abspath(report)
            self.log('Saving report to ' + str(report))
            if not os.path.isdir(report):
                self.log('Creating directory...')
                os.makedirs(report)
            # Create html page
            page = TinyHtmlPage()
            title = 'Simplifying ' + model.qname()
            page.set_title(title)
            page.append('h1').text(title)
            page.append('h2').text('Method: ' + self.name.upper())
            div = page.append('div')
            div.append('p').text('Attempting to simplify equations by'
                ' replacing them with a mixed order spline.')
            div.append('p').text('Each part has ' + str(self.d) + ' matching'
                ' derivatives and maximum order ' + str(self.d + 2) + '.')
            div.append('p').text('Each part has at most '
                + str(self.max_pieces) + ' pieces.')
            div.append('p').text('Accepting approximations if the (estimated)'
                ' maximum error divided by the (estimated) range is less than '
                + str(self.reltol) + '.')
            div.append('p').text('Simplifying with respect to ' + str(lhs)
                + ' in the range ' + str(rng) + '.')
        # Replacement functions will be stored here
        fits = {}
        # Get list of suitable lhs,rhs pairs
        suitable = suitable_expressions(model, lhs)
        # Attempt approximations
        n_considered = 0
        n_simplified = 0
        for v, rhs in suitable:
            name = v.var().qname()
            n_considered += 1
            # Create python function for evaluations
            f = v.var().pyfunc()
            # Indicate interesting variable has been found
            self.log('Selected: ' + name + ' = ' + str(rhs))
            # Attempt fit
            fit = None
            try:
                c,p,g,a,r = approx.fit_mixed_order_spline(f, rng, d=self.d,
                    abstol=self.abstol, reltol=self.reltol,
                    max_pieces=self.max_pieces)
                n = len(p) + 1
                n_simplified += 1
                self.log('Found approximation')
                self.log('    pieces : ' + str(n))
                self.log('    abstol = ' + str(a))
                self.log('    reltol = ' + str(r))
                fit = g.myokit_form(lhs)
            except approx.FittingError as e:
                self.log('FittingError: ' + str(e))
            except Exception as e:
                import traceback
                self.log('Exception ' + '* '*29)
                self.log('')
                self.log(traceback.format_exc())
                self.log('')
                self.log('* '*34)
            if report:
                div = page.append('div')
                div.set_attr('style', 'page-break-before: always;')
                div.append('h2').text(str(n_considered) + '. ' + name)
                div.append('p').math(rhs)
                # Create figure
                pl.figure()
                ax = pl.subplot(111)
                xplot = np.linspace(rng[0], rng[1], 1000)
                pl.plot(xplot, f(xplot), label='f(x)', lw=3)
                if fit:
                    pl.plot(xplot, g(xplot), label='L_'+str(n))
                    # Show nodes
                    xnodes = [rng[0]]
                    xnodes.extend(p)
                    xnodes.append(rng[1])
                    xnodes = np.array(xnodes)
                    pl.plot(xnodes, f(xnodes), 'x', label='nodes',markersize=8)
                # Write report
                if fit:
                    div.append('h3').text('Accepted approximation using '
                         + str(n) + ' pieces.')
                    div.append('p').text('Max absolute error is ' + str(a))
                    div.append('p').text('Max relative error is ' + str(r))
                else:
                    div.append('h3').text('No acceptable approximation found.')
                # Add plot to report
                box = ax.get_position()
                ax.set_position([box.x0,box.y0, box.width*0.8, box.height])
                ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
                iname = os.path.join(report, name + '.png')
                self.log('Saving plot to ' + iname)
                pl.savefig(iname)
                pl.close()
                div.append('h3').text('Graphical representation')
                div.append('img').set_attr('src', iname)
            # Save change to dict
            if fit:
                self.log('Saving approximation...')
                fits[v.var()] = fit
            else:
                self.log('No suitable approximation found.')
        # Create updated model
        for var, fit in fits.iteritems():
            var.set_rhs(fit)
        # Validate model, enable crude fixes!
        model.validate(fix_crudely = True)
        # Write report(s) to file
        if report:
            page.append('h2').text('Summary')
            div = page.append('div')
            div.append('p').text('Attempted to replace ' + str(n_considered)
                + ' equations.')
            div.append('p').text('Replaced ' + str(n_simplified)
                + ' equations.')
            fname = os.path.join(report, 'index.html')
            self.log('Writing report to ' + fname)
            with open(fname, 'w') as f:
                f.write(page.html(pretty=False))
        # Return updated model
        self.log('Returning model...')
        return model
