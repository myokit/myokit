# Myokit roadmap

This document presents a high-level overview of the goals for Myokit's future development.

## Compatibility, performance, and ease-of-installation

Myokit's `Simulation` class currently requires users to have a specific compiler installed, as well as a version of Sundials compiled with that compiler.
In addition, the on-the-fly compilation via `distutils`/`setuptools` has gotten slightly slower on linux in recent versions, but can be extremely slow on Windows.
A rewrite of the simulation class to use a precompiled simulation engine and model code generated through llvmlite could solve both problems.

- Tickets related to this "Simulation revamp" are grouped in a [project](https://github.com/myokit/myokit/projects/5), but currently represent only a fraction of the expected work.
- Including precompiled parts will require a change in the way Myokit is distributed; a proof-of-concept can be found [here](https://github.com/myokit/beta/).

## Improved documentation

Myokit's current documentation consists of:

- A [full API documentation](https://myokit.readthedocs.io/) which includes a short user guide.
- A set of [static examples](http://myokit.org/examples/) and [tutorial hand-outs](http://myokit.org/tutorial/).
- [Contributing guidelines](https://github.com/myokit/myokit/blob/main/CONTRIBUTING.md), which also contain a high-level overview of Myokit's code.
- [Technical notes](https://github.com/myokit/examples#technical-notes).

We plan to create an extensive set of Jupyter notebook examples, that build up gradually, allowing use as a "live textbook".
The static examples will be rewritten to be part of this, the tutorials will be converted to "getting started" notebooks suitable for self-study.
The technical notes will retain their form as appendices to this work.

Planned topics can be viewed at [https://github.com/myokit/examples](https://github.com/myokit/examples).

## Features for parameter estimation

Two major improvements are planned:

- Improved calculation of "sensitivities" of simulation results w.r.t. parameters, see this [project](https://github.com/myokit/myokit/projects/6).
 - Issues related to initial conditions with parameter dependecies are group in a separate [project](https://github.com/myokit/myokit/projects/13).
- A rewrite of the HH and Markov model simulations ([project](https://github.com/myokit/myokit/projects/8)).
  - Allow these models to be created independent of the `myokit.Model` class (for model selection studies).
  - Provide compiled simulations for better performance during inference (relies on llvm revamp described above).

## Back-burner

Ongoing projects for which slower progress is expected are

- A unified data and simulation data interface, allowing the Explorer and DataLogViewer to be combined into a single tool that can be used to compare data with predictions ([project](https://github.com/myokit/myokit/projects/15)).
- Unification of multi-cell simulation engines ([project](https://github.com/myokit/myokit/projects/7)).
