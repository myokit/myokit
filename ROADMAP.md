# Myokit roadmap

This document presents a high-level overview of the goals for Myokit's future development.

## Compatibility, performance, and ease-of-installation (Myokit 2.0)

Myokit's C-based simulation classes require users to install a Python version-specific C compiler and compatible Sundials binaries, which complicates installation (especially on non-linux platforms).
In addition, in recent Python versions on-the-fly compilation via `distutils` / `setuptools` has gotten slightly slower (ms on linux) to significantly slower (minutes on some Windows installs).
A rewrite of the C-based simulation classes to use precompiled simulation engines and model code generated with llvmlite can solve both problems.
The significant change in Myokit's core functionality would warrant an upgrade in major version number.

- Initial tasks related to this conversion are listed in [this issue](https://github.com/myokit/myokit/issues/295).

## Improved documentation

Myokit's current documentation is extensive but fragmented, consisting of:

- The developer docs, including the [full API documentation](https://myokit.readthedocs.io/), and the `mmt` syntax specification.
- A brief "User guide", included with the developer documentation.
- A set of [static examples](http://myokit.org/examples/) and PDF [tutorial hand-outs](http://myokit.org/tutorial/).
- [Technical notes](https://github.com/myokit/examples#technical-notes).
- [Contributing guidelines](https://github.com/myokit/myokit/blob/main/CONTRIBUTING.md), which also contain a high-level overview of Myokit's code.
- Installation instructions, at http://myokit.org/install

To reduce fragmentation, an extensive set of Jupyter notebook examples is planned, which will bring together the user guide, examples, installation guide, and technical notes.
The planned index can be viewed at [https://github.com/myokit/examples](https://github.com/myokit/examples).
Chapters will gradually build up in complexity, and function as a "live textbook" that is regularly tested using CI.

The API documentation and contributing guidelines will remain separate documents.

## Features for parameter estimation

Two major improvements are planned:

- Improved calculation of "sensitivities" of simulation results with respect to model parameters, see this [project](https://github.com/myokit/myokit/projects/6).
  - Issues related to initial conditions with parameter dependecies are grouped in a separate [project](https://github.com/myokit/myokit/projects/13).
- A rewrite of the HH and Markov model simulations ([project](https://github.com/myokit/myokit/projects/8)).
  - Allow these models to be created independent of the `myokit.Model` class (for model selection studies) based on [pilot work by Joey](https://github.com/CardiacModelling/markov-builder).
  - Provide compiled simulations for better performance during inference (relies on LLVM work described above).
  - Provide fast parameter sensitivities for HH model simulations.

##  Maintenance

- Some possible, but low-priority, bugs have been reported: [Tickets here](https://github.com/myokit/myokit/issues?q=is%3Aissue+is%3Aopen+label%3Abug).
- Various potential code improvements have been identified: [Tickets here](https://github.com/myokit/myokit/issues?q=is%3Aissue+is%3Aopen+label%3Acode).
- Use of IDE components needs to be made easier on Mac [#38](https://github.com/myokit/myokit/issues/38) and may even be broken [#692](https://github.com/myokit/myokit/issues/692).

## Back-burner

Projects which are ongoing but not currently prioritised include

- Unification of single ([project](https://github.com/myokit/myokit/projects/5)) multi-cell simulation engines ([project](https://github.com/myokit/myokit/projects/7)).
  - This may become more urgent if it turns out to be possible to distribute compiled OpenCL simulations, in which case it would become part of the major "Compatibility, performance, and ease-of-installation" project.
- A unified data and simulation data interface, allowing the Explorer and DataLogViewer to be combined into a single tool that can be used to compare data with predictions ([project](https://github.com/myokit/myokit/projects/15), see also the [edata tag](https://github.com/myokit/myokit/issues?q=is%3Aissue+is%3Aopen+label%3Aedata)).
  - Alternatively, the data reading parts could be split off into a separate project or merged into other projects like Neo (provided the goals and functionality is sufficiently aligned). See [this ticket](https://github.com/myokit/myokit/issues/259).
- Add more CellML tests, by further developing the [CellML test suite](https://github.com/MichaelClerx/cellml-validation), see also the [tickets](https://github.com/myokit/myokit/issues?q=is%3Aissue+is%3Aopen+label%3ACellML).
- Implement singularity fixes created for [cellmlmanip with Maurice](https://github.com/myokit/myokit/issues/809).
