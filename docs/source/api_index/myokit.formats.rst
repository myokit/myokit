.. _api/index/myokit/formats:

==============
myokit.formats
==============
- :meth:`myokit.formats.exporter`
- :class:`myokit.formats.Exporter`
- :class:`myokit.formats.ExpressionWriter`
- :meth:`myokit.formats.exporters`
- :meth:`myokit.formats.ewriter`
- :meth:`myokit.formats.ewriters`
- :meth:`myokit.formats.importer`
- :class:`myokit.formats.Importer`
- :meth:`myokit.formats.importers`
- :meth:`myokit.formats.register_external_ewriter`
- :meth:`myokit.formats.register_external_importer`
- :meth:`myokit.formats.register_external_exporter`
- :class:`myokit.formats.TemplatedRunnableExporter`

myokit.formats.ansic
--------------------
- :class:`myokit.formats.ansic.AnsiCExporter`
- :class:`myokit.formats.ansic.AnsiCCableExporter`
- :class:`myokit.formats.ansic.AnsiCEulerExporter`
- :class:`myokit.formats.ansic.AnsiCExpressionWriter`
- :meth:`myokit.formats.ansic.exporters`
- :meth:`myokit.formats.ansic.ewriters`

myokit.formats.axon
-------------------
- :class:`myokit.formats.axon.AbfFile`
- :class:`myokit.formats.axon.AbfImporter`
- :class:`myokit.formats.axon.AtfFile`
- :class:`myokit.formats.axon.Channel`
- :meth:`myokit.formats.axon.importers`
- :meth:`myokit.formats.axon.load_atf`
- :meth:`myokit.formats.axon.save_atf`
- :class:`myokit.formats.axon.Sweep`

myokit.formats.cellml
---------------------
- :class:`myokit.formats.cellml.CellMLExporter`
- :class:`myokit.formats.cellml.CellMLExpressionWriter`
- :class:`myokit.formats.cellml.CellMLImporter`
- :class:`myokit.formats.cellml.CellMLImporterError`
- :class:`myokit.formats.cellml.CellML1Exporter`
- :class:`myokit.formats.cellml.CellML2Exporter`
- :meth:`myokit.formats.cellml.ewriters`
- :meth:`myokit.formats.cellml.exporters`
- :meth:`myokit.formats.cellml.importers`

myokit.formats.cellml.v1
------------------------------
- :class:`myokit.formats.cellml.v1.AnnotatableElement`
- :class:`myokit.formats.cellml.v1.CellMLError`
- :class:`myokit.formats.cellml.v1.CellMLParser`
- :class:`myokit.formats.cellml.v1.CellMLParsingError`
- :class:`myokit.formats.cellml.v1.CellMLWriter`
- :meth:`myokit.formats.cellml.v1.clean_identifier`
- :meth:`myokit.formats.cellml.v1.create_unit_name`
- :class:`myokit.formats.cellml.v1.Component`
- :meth:`myokit.formats.cellml.v1.is_valid_identifier`
- :class:`myokit.formats.cellml.v1.Model`
- :meth:`myokit.formats.cellml.v1.parse_file`
- :meth:`myokit.formats.cellml.v1.parse_string`
- :class:`myokit.formats.cellml.v1.Units`
- :class:`myokit.formats.cellml.v1.UnitsError`
- :class:`myokit.formats.cellml.v1.UnsupportedBaseUnitsError`
- :class:`myokit.formats.cellml.v1.UnsupportedUnitOffsetError`
- :class:`myokit.formats.cellml.v1.Variable`
- :meth:`myokit.formats.cellml.v1.write_file`
- :meth:`myokit.formats.cellml.v1.write_string`

myokit.formats.cellml.v2
------------------------------
- :class:`myokit.formats.cellml.v2.AnnotatableElement`
- :class:`myokit.formats.cellml.v2.CellMLError`
- :class:`myokit.formats.cellml.v2.CellMLParser`
- :class:`myokit.formats.cellml.v2.CellMLParsingError`
- :class:`myokit.formats.cellml.v2.CellMLWriter`
- :meth:`myokit.formats.cellml.v2.clean_identifier`
- :meth:`myokit.formats.cellml.v2.create_unit_name`
- :class:`myokit.formats.cellml.v2.Component`
- :meth:`myokit.formats.cellml.v2.is_basic_real_number_string`
- :meth:`myokit.formats.cellml.v2.is_identifier`
- :meth:`myokit.formats.cellml.v2.is_integer_string`
- :meth:`myokit.formats.cellml.v2.is_real_number_string`
- :class:`myokit.formats.cellml.v2.Model`
- :meth:`myokit.formats.cellml.v2.parse_file`
- :meth:`myokit.formats.cellml.v2.parse_string`
- :class:`myokit.formats.cellml.v2.Units`
- :class:`myokit.formats.cellml.v2.Variable`
- :meth:`myokit.formats.cellml.v2.write_file`
- :meth:`myokit.formats.cellml.v2.write_string`

myokit.formats.channelml
------------------------
- :class:`myokit.formats.channelml.ChannelMLError`
- :class:`myokit.formats.channelml.ChannelMLImporter`
- :meth:`myokit.formats.channelml.importers`

myokit.formats.cpp
------------------------
- :class:`myokit.formats.cpp.CppExpressionWriter`
- :meth:`myokit.formats.cpp.ewriters`

myokit.formats.cuda
-------------------
- :class:`myokit.formats.cuda.CudaKernelExporter`
- :class:`myokit.formats.cuda.CudaKernelRLExporter`
- :class:`myokit.formats.cuda.CudaExpressionWriter`
- :meth:`myokit.formats.cuda.exporters`
- :meth:`myokit.formats.cuda.ewriters`

myokit.formats.easyml
---------------------
- :class:`myokit.formats.easyml.EasyMLExporter`
- :class:`myokit.formats.easyml.EasyMLExpressionWriter`
- :meth:`myokit.formats.easyml.exporters`
- :meth:`myokit.formats.easyml.ewriters`

myokit.formats.html
-------------------
- :meth:`myokit.formats.html.exporters`
- :class:`myokit.formats.html.HTMLExporter`
- :meth:`myokit.formats.html.html2ascii`

myokit.formats.latex
---------------------
- :meth:`myokit.formats.latex.exporters`
- :meth:`myokit.formats.latex.ewriters`
- :class:`myokit.formats.latex.LatexExpressionWriter`
- :class:`myokit.formats.latex.PosterExporter`
- :class:`myokit.formats.latex.PdfExporter`

myokit.formats.mathml
---------------------
- :meth:`myokit.formats.mathml.ewriters`
- :class:`myokit.formats.mathml.MathMLError`
- :class:`myokit.formats.mathml.MathMLExpressionWriter`
- :class:`myokit.formats.mathml.MathMLParser`
- :meth:`myokit.formats.mathml.parse_mathml_etree`
- :meth:`myokit.formats.mathml.parse_mathml_string`

myokit.formats.matlab
---------------------
- :meth:`myokit.formats.matlab.exporters`
- :meth:`myokit.formats.matlab.ewriters`
- :class:`myokit.formats.matlab.MatlabExporter`
- :class:`myokit.formats.matlab.MatlabExpressionWriter`

myokit.formats.opencl
---------------------
- :meth:`myokit.formats.opencl.exporters`
- :meth:`myokit.formats.opencl.ewriters`
- :class:`myokit.formats.opencl.OpenCLExporter`
- :class:`myokit.formats.opencl.OpenCLRLExporter`
- :class:`myokit.formats.opencl.OpenCLExpressionWriter`

myokit.formats.python
---------------------
- :meth:`myokit.formats.python.exporters`
- :meth:`myokit.formats.python.ewriters`
- :class:`myokit.formats.python.PythonExporter`
- :class:`myokit.formats.python.PythonExpressionWriter`
- :class:`myokit.formats.python.NumPyExpressionWriter`

myokit.formats.sbml
-------------------
- :class:`myokit.formats.sbml.Compartment`
- :class:`myokit.formats.sbml.CSymbolVariable`
- :class:`myokit.formats.sbml.Model`
- :class:`myokit.formats.sbml.ModifierSpeciesReference`
- :meth:`myokit.formats.sbml.importers`
- :class:`myokit.formats.sbml.Parameter`
- :class:`myokit.formats.sbml.Quantity`
- :class:`myokit.formats.sbml.Reaction`
- :class:`myokit.formats.sbml.SBMLError`
- :class:`myokit.formats.sbml.SBMLImporter`
- :class:`myokit.formats.sbml.SBMLParser`
- :class:`myokit.formats.sbml.SBMLParsingError`
- :class:`myokit.formats.sbml.Species`
- :class:`myokit.formats.sbml.SpeciesReference`

myokit.formats.stan
-------------------
- :meth:`myokit.formats.stan.exporters`
- :meth:`myokit.formats.stan.ewriters`
- :class:`myokit.formats.stan.StanExporter`
- :class:`myokit.formats.stan.StanExpressionWriter`

myokit.formats.sympy
--------------------
- :meth:`myokit.formats.sympy.ewriters`
- :meth:`myokit.formats.sympy.read`
- :class:`myokit.formats.sympy.SymPyExpressionReader`
- :class:`myokit.formats.sympy.SymPyExpressionWriter`
- :meth:`myokit.formats.sympy.write`

myokit.formats.wcp
--------------------
- :class:`myokit.formats.wcp.WcpFile`

myokit.formats.xml
-------------------
- :meth:`myokit.formats.xml.exporters`
- :meth:`myokit.formats.xml.split`
- :class:`myokit.formats.xml.XMLExporter`

