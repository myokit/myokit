# Contributing to Myokit

Contributions to Myokit are very welcome! To streamline our work, please have a look at the guidelines below.

We use [GIT](https://en.wikipedia.org/wiki/Git) and [GitHub](https://en.wikipedia.org/wiki/GitHub) to coordinate our work. When making any kind of update, try to follow the procedure below.

### A. Discussing the proposed changes

1. Before doing any coding, create a GitHub [issue](https://guides.github.com/features/issues/) so that new ideas can be discussed. 
   There might already be something similar in the pipeline, or a feature may have been tried and rejected.
   A bit of pre-discussion can save lots of valuable time!

### B. Setting up your system

2. If you're planning to contribute code to Myokit, don't check out the repo directly, but create a [fork](https://help.github.com/articles/fork-a-repo/) and then [clone](https://help.github.com/articles/cloning-a-repository/) it onto your local system .
3. Install Myokit in development mode, with `$ pip install -e .`.
4. [Test](#testing) if everything's working, using the test script: `$ python test --quick`.

If you run into any issues at this stage, please create an issue on GitHub.

### C. Creating a branch for your issue

5. Now create a [branch](https://help.github.com/articles/creating-and-deleting-branches-within-your-repository/) for the issue you're going to work on. 
   Using branches lets us test out new changes without changing the main repository.

You now have everything you need to start making changes!

### D. Writing your code

6. Commit your changes to your branch with useful, descriptive commit messages.
   Remember, these messages are publically visible and should still make sense a few months ahead in time. 
   While developing, you can keep using the github issue you're working on as a place for discussion.
   [Refer to your commits](https://stackoverflow.com/questions/8910271/how-can-i-reference-a-commit-in-an-issue-comment-on-github) when discussing specific lines of code.
7. If you want to add a dependency on another library, or re-use code you found somewhere else, have a look at [these guidelines](#dependencies-and-reusing-code), and discuss the new dependency in the project's issue.

### E. Finishing touches

8. Please check that your code conforms to the [coding style guidelines](#coding-style-guidelines).
9. [Test your code](#testing), checks will be run before merging to ensure the changes have 100% test coverage.
10. Myokit has online documentation at http://docs.myokit.org/.
    To make sure any new methods or classes you added show up there, please read the [documentation](#documentation) section.

### F. Merging changes

11. When you feel your code is finished, or at least warrants discussion, create a [pull request](https://help.github.com/articles/about-pull-requests/) (PR).
12. In your branch, update the [CHANGELOG.md](./CHANGELOG.MD) with a link to this PR and a concise summary of the changes.
13. Finally, the PR will be tested, reviewed, discussed, and if all goes well it'll be merged into the main source code.

Thanks!





## Project structure

Myokit is written in [Python](https://en.wikipedia.org/wiki/Python_(programming_language)), with occassional bits of (ansi) [C](https://en.wikipedia.org/wiki/ANSI_C).
It uses [CVODE](https://computation.llnl.gov/projects/sundials/cvode) for simulations, and [NumPy](https://en.wikipedia.org/wiki/NumPy) for pre- and post-processing.
[OpenCL](https://en.wikipedia.org/wiki/OpenCL) is used for parallelised multi-cell simulation.

When you clone the Myokit repository, you will see several directories and files.
The main directory `myokit`, contains the Python `myokit` module.
This is the part of the code that will be installed on users systems when they run `pip install myokit`.
Various configuration files for testing and documentation infracstructure are present, which are described in the [Infrastructure & configuration files](#infrastructure--configuration-files) section below.

Inside the `myokit` module, you'll find various submodules.
Most of these are hidden (indicated by an underscore before their name), and are used to split the main `myokit` module up into sections for easier maintainance.
For example, the code for `myokit.Model` lives in the hidden module `myokit._model_api`.

### Key parts of the code

- The file `__init__.py` sets up the main `myokit` module, importing various parts from hidden modules.
- Models, components, and variables live in `_model_api.py`
- Expressions, including names, numbers, operators, functions, and operators, live in `_expressions.py`
- The unit system is implemented in `_unit.py`, and several predefined units are given in `units.py` (a public module).
- Parsing of models and protocols is handled by `_parsing.py`
- Myokit-defined exceptions are stored in `_err.py`

### Simulation infrastructure

- Event-based protocols and a Python "pacing system" are implemented in `_protocol.py`, with protocol-generating methods available in the public model `pacing.py`.
- Simulation results are stored in a `DataLog`, implemented in `_datalog.py`.
- For simulations on rectangular grids, a `DataLog` can be converted to a `DataBlock1d` or a `DataBlock2d`, which provides access to the data in array form.
- Most simulations are written as templates, that are turned into compilable code using the tiny templating engine in `pype.py`.

### Simulation code

- Simulation code is stored in the `_sim` module, which contains several submodules.
- The `cmodel.py` and `cmodel.h` files can be used to generate a set of C functions to evaluate a Myokit model's RHS.
- These are used by the CVODE(s) simulation implemented in `cvodessim.py`, which also uses the template `cvodessim.c` to generate simulation code.
- Event-based pacing and fixed-form pacing are implemented in `pacing.h`.
- OpenCL simulations are implemented in `openclsim.py`, `openclsim.c` and `openclsim.cl`, with utility functions loaded from `mcl.h`.
- Information on how the simulations work can be found in their docstring, and in the technical notes in the [examples](./examples).

### Import and export

- Import and export from and to various formats is implemented in `myokit.formats`.
- Its `__init__.py` defines the `Importer`, `Exporter`, and `ExpressionWriter` classes to import and export models, and to export expressions.
- Additionally, it contains methods such as `myokit.formats.importer(name)`, allowing you to obtain an importer by name (rather than via importing a module).

### Libraries

- Some advanced bits of functionality are stored in `myokit.lib.*` submodules
- Methods for analysis of model variable dependencies are provided in `myokit.lib.deps`.
- Methods for Hodgkin-Huxley style ion-channel models are provided in `myokit.lib.hh`, including methods to isolate HH models, and to run analytic or stochastic (single-channel) simulations.
- Similar methods for Markov models are provided in `myokit.lib.markov`.
- Methods to guess variables with a special meaning (e.g. membrane potential) are provided in `myokit.lib.guess`.

### GUI code

- GUI code is provided in `myokit.gui`, Myokit uses Qt via PyQt or PySide.

### Utilities

- Various auxillary functions that are included in `myokit` are stored in `_aux.py` and `_io.py` (for file system functions).
- Floating point tools are implemented in `float.py`.
- Various general-purpose tools required by Myokit are provided in `tools.py`.
- Command line scripts are implemented in `__main__.py`

### Configuration

- The myokit version number is stored in `_myokit_version.py`.
- Configuration loading and storing is handled in `_config.py`.
- System information is be queried in `_system.py`





## Developer installation

After cloning, Myokit can be installed into your Python system, using

```
$ python3 setup.py develop
```

This will tell other Python modules where to find Myokit, so that you can use `import myokit` anywhere on your system.





## Coding style guidelines

For the Python bits, Myokit follows the [PEP8 recommendations](https://www.python.org/dev/peps/pep-0008/) for coding style.
These are very common guidelines, and community tools have been developed to check how well projects implement them.

We use [flake8](http://flake8.pycqa.org/en/latest/) to check our PEP8 adherence.
To try this on your system, navigate to the Myokit directory in a console and type

```
$ flake8
```

### Naming

Naming is hard, so it's okay to spend time on this.
Aim for descriptive class, method, and argument names.
Avoid abbreviations when possible without making names overly long.

Class names are CamelCase, and start with an upper case letter, for example `SuperDuperSimulation`.
Method and variable names are lower case, and use underscores for word separation, for example `x` or `iteration_count`.

### Python 2 and 3

Myokit runs in Python 2.7+ and 3.5+.
All new code should be written [to work on both](http://python-future.org/compatible_idioms.html).

## Dependencies and reusing code

While it's a bad idea to reinvent the wheel, making code that's easy to install and use on different systems gets harder the more dependencies you include.
For this reason, we try to limit Myokit's dependencies to the bare necessities.
This is a matter of preference / judgement call, so best to discuss these matters on GitHub whenever you feel a new dependency should be added!

Direct inclusion of code from other packages is possible, as long as their license permits it and is compatible with ours, but again should be considered carefully and discussed first.
Snippets from blogs and stackoverflow can often be included without attribution, but if they solve a particularly nasty problem (or are very hard to read) it's often a good idea to attribute (and document) them, by making a comment with a link in the source code.

### Matplotlib

Myokit includes plotting methods, _but_, these should never be vital for its functioning, so that users are free to use Myokit with other plotting libraries.

Secondly, Matplotlib should never be imported at the module level, but always inside methods.
This means that the `myokit` module can be imported without Matplotlib being installed, and used as long as no Matplotlib-reliant methods are called.
It also allows user code to call methods that customise matplotlib behaviour (e.g. back-end selection), which must be run before certain matplotlib modules are imported.





## Testing

Myokit uses the [unittest](https://docs.python.org/3.9/library/unittest.html) package for tests.

To run unit tests:

```
$ python3 -m myokit test unit
```

To run documentation tests:

```
$ python3 -m myokit test doc
```




## Documentation

Every method and every class should have a [docstring](https://www.python.org/dev/peps/pep-0257/) that describes in plain terms what it does, and what the expected input and output is.

Each docstring should start with a one-line explanation.
If more explanation is needed, this one-liner is followed by a blank line and more information in the following paragraphs.

These docstrings can be fairly simple, but can also make use of [reStructuredText](http://docutils.sourceforge.net/docs/user/rst/quickref.html), a markup language designed specifically for writing [technical documentation](https://en.wikipedia.org/wiki/ReStructuredText).
For example, you can link to other classes and methods by writing ```:class:`myokit.Model` ``` and  ```:meth:`run()` ```.

In addition, we write a (very) small bit of documentation in separate reStructuredText files in the `doc` directory.
Most of what these files do is simply import docstrings from the source code. But they also do things like add tables and indexes.
If you've added a new class to a module, search the `doc` directory for the appropriate `.rst` file and add your class.

Using [Sphinx](http://www.sphinx-doc.org/en/stable/) the documentation in `doc` can be converted to HTML, PDF, and other formats.
In particular, we use it to generate the documentation on http://docs.myokit.org/

### Examples

A very short docstring:
```
def eat_biscuits(n):
    """ Eats ``n`` biscuits from the central biscuit repository. """
```

A long form docstring, with argument list and return types:

```
def get_alpha_and_beta(x, v=None):
    """
    Tests if the given ``x`` is a state variable with an expression of the form
    ``(1 - x) * alpha - x * beta``, and returns the variables for ``alpha`` and
    ``beta`` if so.

    Here, ``alpha(v)`` and ``beta(v)`` represent the forward and backward
    reaction rates for ``x``. Both may depend on ``v``, but not on any (other)
    state variable.

    Note that this method performs a shallow check of the equation's shape,
    and does not perform any simplification or rewriting to see if the
    expression can be made to fit the required form.

    Arguments:

    ``x``
        The :class:`myokit.Variable` to check.
    ``v``
        An optional :class:`myokit.Variable` representing the membrane
        potential. If not given, the label ``membrane_potential`` will be used
        to determine ``v``. If ``v=None`` and no membrane potential can be
        found an error will be raised. Membrane potential is typically
        specified as a state, but this is not a requirement.

    Returns a tuple ``(alpha, beta)`` if successful, or ``None`` if not. Both
    ``alpha`` and ``beta`` are :class:`myokit.Variable` objects.
    """
```

### Building the documentation

To test and debug the documentation, it's best to build it locally. 
To do this, make sure you have the relevant dependencies installed (see above), navigate to your Myokit directory in a console, and then type:

```
cd doc
make clean
make html
```

Next, open a browser, and navigate to your local Myokit directory (by typing the path, or part of the path into your location bar). 
Then have a look at `<your myokit path>/doc/build/html/index.html`.





## Infrastructure & configuration files

- Installation happens using `setup.py`, but also information from `MANIFEST.in`.
- Users can find the license in `LICENSE.txt` and a citable reference in `CITATION` ([syntax](https://www.software.ac.uk/blog/2016-10-06-encouraging-citation-software-introducing-citation-files)).
- Tests are run using Github Actions, and configured [here](./.github/workflows).
- Coverage is tested using [codecov.io](https://docs.codecov.io/docs) which builds on [coverage](https://coverage.readthedocs.io/). 
  Configuration file: `.coveragerc` ([syntax](https://coverage.readthedocs.io/en/latest/config.html)).
- Documentation is built using [readthedocs](readthedocs.org) and [published here](https://myokit.readthedocs.io/).
  Configuration file `.readthedocs.txt`.
- Code style is checked using flake8.
  Configuration file: `.flake8` ([syntax](http://flake8.pycqa.org/en/latest/user/configuration.html)).

