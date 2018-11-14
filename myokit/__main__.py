#!/usr/bin/env python
#
# Command line tools for Myokit.
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals


def printline():
    line_width = 60
    print('-' * line_width)


def main():
    """
    Imports myokit. Gets parsing.
    """
    import sys

    # Create parser
    import argparse
    parser = argparse.ArgumentParser(
        usage='myokit',
        description='Command line tools for myokit.',
    )
    subparsers = parser.add_subparsers(
        description='Select one of the available commands from the list below',
        title='Commands',
    )

    # Add subparsers
    add_block_parser(subparsers)            # Launch the DataBlock viewer
    add_compare_parser(subparsers)          # Compare models
    add_compiler_parser(subparsers)         # Show compiler
    add_debug_parser(subparsers)            # Debug an RHS equation
    add_eval_parser(subparsers)             # Evaluate an expression
    add_export_parser(subparsers)           # Export an mmt file
    add_gde_parser(subparsers)              # Launch the graph data extractor
    add_icon_parser(subparsers)             # Install icons
    add_ide_parser(subparsers)              # Launch the IDE
    add_import_parser(subparsers)           # Import a file to mmt
    add_log_parser(subparsers)              # Launch the DataLog viewer
    add_opencl_parser(subparsers)           # Show OpenCL support
    add_opencl_select_parser(subparsers)    # Select OpenCL platform
    add_reset_parser(subparsers)            # Reset config files
    add_run_parser(subparsers)              # Run an mmt file
    add_step_parser(subparsers)             # Load a model, perform 1 step
    add_sundials_parser(subparsers)         # Show Sundials support
    add_system_parser(subparsers)           # Show system information
    add_version_parser(subparsers)          # Show version info
    add_video_parser(subparsers)            # Convert a DataBlock to video

    # Parse!
    if len(sys.argv) == 1:
        parser.print_help()
    else:
        args = parser.parse_args()

        # Get the args' objects attributes as a dictionary
        args = vars(args)

        # Split into function and arguments
        func = args['func']
        del(args['func'])

        # Call the selected function with the parsed arguments
        func(**args)


def block(filename, pyqt4=False, pyqt5=False, pyside=False):
    """
    Runs the DataBlock viewer.
    """
    import myokit
    if pyqt5:
        myokit.FORCE_PYQT5 = True
        myokit.FORCE_PYQT4 = False
        myokit.FORCE_PYSIDE = False
    elif pyqt4:
        myokit.FORCE_PYQT5 = False
        myokit.FORCE_PYQT4 = True
        myokit.FORCE_PYSIDE = False
    elif pyside:
        myokit.FORCE_PYQT4 = False
        myokit.FORCE_PYQT4 = False
        myokit.FORCE_PYSIDE = True
    import myokit.gui
    import myokit.gui.datablock_viewer
    if pyqt5 or pyqt4 or pyside:
        print('Using backend: ' + myokit.gui.backend)
    myokit.gui.run(myokit.gui.datablock_viewer.DataBlockViewer, filename)


def add_block_parser(subparsers):
    """
    Adds a subcommand parser for `block`.
    """
    block_parser = subparsers.add_parser(
        'block',
        description='Runs the DataBlock Viewer.',
        help='Runs the DataBlock Viewer.',
    )
    block_parser.add_argument(
        'filename',
        default=None,
        nargs='?',
        metavar='filename',
        help='The DataBlock zip file to open (optional).',
    )
    block_parser.add_argument(
        '--pyqt5',
        action='store_true',
        help='Run the DataBlock Viewer using the PyQt5 backend.',
    )
    block_parser.add_argument(
        '--pyqt4',
        action='store_true',
        help='Run the DataBlock Viewer using the PyQt4 backend.',
    )
    block_parser.add_argument(
        '--pyside',
        action='store_true',
        help='Run the DataBlock Viewer using the PySide backend.',
    )
    block_parser.set_defaults(func=block)


def compare(model1, model2):
    """
    Compares two models.
    """
    import myokit

    # Load models
    m1 = myokit.load_model(model1)
    m2 = myokit.load_model(model2)

    # Compare
    myokit.ModelComparison(m1, m2, live=True)


def add_compare_parser(subparsers):
    """
    Adds a subcommand parser for the `compare` command.
    """
    compare_parser = subparsers.add_parser(
        'compare',
        description='Compares two models by inspecting their components,'
                    ' variables, meta-data etc.',
        help='Compares two models.',
    )
    compare_parser.add_argument(
        'model1',
        metavar='model1..mmt',
        help='One of the models to compare.',
    )
    compare_parser.add_argument(
        'model2',
        metavar='model2.mmt',
        help='The model to compare with.',
    )
    compare_parser.set_defaults(func=compare)


def compiler():
    """
    Tests for C compilation support.
    """
    import myokit
    compiler = myokit.Compiler.info()
    if compiler is None:
        print('Compilation with distutils/setuptools failed.')
    else:
        print('Compilation successful. Found: ' + compiler)


def add_compiler_parser(subparsers):
    """
    Adds a subcommand parser for the ``compiler`` command.
    """
    compiler_parser = subparsers.add_parser(
        'compiler',
        description='Checks for C compilation support.',
        help='Prints information about C compilation support.',
    )
    compiler_parser.set_defaults(func=compiler)


def debug(source, variable, deps=False):
    """
    Shows how a single variable is calculated from the initial conditions.
    """
    import myokit

    # Load model
    m = myokit.load_model(source)

    # Show result
    if deps:
        print(m.show_expressions_for(variable))
    else:
        print(m.show_evaluation_of(variable))


def add_debug_parser(subparsers):
    """
    Adds a subcommand parser for the `debug` command.
    """
    debug_parser = subparsers.add_parser(
        'debug',
        description='Shows how a single variable is calculated from the '
                    'initial conditions. The variable\'s equation and value'
                    ' are displayed, along with the value and formula of any'
                    ' nested variables and the values of all dependencies.',
        help='Shows how a single variable is calculated.',
    )
    debug_parser.add_argument(
        'source',
        metavar='source_file.mmt',
        help='The source file to parse.',
    )
    debug_parser.add_argument(
        'variable',
        metavar='variable',
        help='The variable whose evaluation to display.',
    )
    debug_parser.add_argument(
        '--deps',
        action='store_true',
        help='Show dependencies instead of numerical evaluation.',
    )
    debug_parser.set_defaults(func=debug)


def evaluate(expression):
    """
    Evaluates an expression in mmt syntax.
    """
    import myokit
    try:
        e = myokit.parse_expression(expression)
        e = e.eval() if e.is_literal() else e
        print(expression + ' = ' + str(e))
    except myokit.ParseError as ex:
        print(myokit.format_parse_error(ex, iter([expression])))


def add_eval_parser(subparsers):
    """
    Adds a subcommand parser for the `eval` command.
    """
    eval_parser = subparsers.add_parser(
        'eval',
        description='Evaluates an expression in myokit syntax.',
        help='Evaluates an expression in myokit syntax.',
    )
    eval_parser.add_argument(
        'expression',
        metavar='"1 + 2 / 3"',
        help='The expression to evaluate.',
    )
    eval_parser.set_defaults(func=evaluate)


def mmt_export(exporter, source, target):
    """
    Exports a myokit model.
    """
    import sys
    import myokit
    import myokit.formats

    # Get exporter
    exporter = myokit.formats.exporter(exporter)

    # Set to auto-print
    logger = exporter.logger()
    logger.set_live(True)
    logger.log_flair(str(exporter.__class__.__name__))

    # Parse input file
    try:
        logger.log('Reading model from ' + myokit.format_path(source))
        model, protocol, script = myokit.load(source)
    except myokit.ParseError as ex:
        logger.log(myokit.format_parse_error(ex, source))
        sys.exit(1)

    # Must have model
    if model is None:
        logger.log('Error: Imported file must contain model definition.')
        sys.exit(1)
    else:
        logger.log('Model read successfully')

    # Export model or runnable
    if exporter.supports_model():
        # Export model
        logger.log('Exporting model')
        exporter.model(target, model)
    else:
        # Export runnable
        logger.log('Exporting runnable')
        if protocol is None:
            logger.log('No protocol found.')
        else:
            logger.log('Using embedded protocol.')
        exporter.runnable(target, model, protocol)
    logger.log_flair('Export successful')
    logger.log(exporter.info())


def add_export_parser(subparsers):
    """
    Adds a subcommand parser for the `export` command.
    """
    import myokit
    import myokit.formats

    export_parser = subparsers.add_parser(
        'export',
        description='Exports a Myokit model using the specified exporter.',
        help='Exports a Myokit model.',
    )
    export_parser.add_argument(
        'exporter',
        metavar='exporter',
        help='The exporter to use.',
        choices=myokit.formats.exporters(),
    )
    export_parser.add_argument(
        'source',
        metavar='source',
        help='The source file to parse.',
    )
    export_parser.add_argument(
        'target',
        metavar='target',
        help='The output file or directory.'
    )
    export_parser.set_defaults(func=mmt_export)


def gde(filename):
    """
    Runs the graph data extractor.
    """
    import myokit.gui
    import myokit.gui.gde
    myokit.gui.run(myokit.gui.gde.GraphDataExtractor, filename)


def add_gde_parser(subparsers):
    """
    Adds a subcommand parser for the `gde` command.
    """
    gde_parser = subparsers.add_parser(
        'gde',
        description='Runs the graph data extractor.',
        help='Runs the graph data extractor.',
    )
    gde_parser.add_argument(
        'filename',
        default=None,
        nargs='?',
        metavar='filename',
        help='The gde file to open (optional).',
    )
    gde_parser.set_defaults(func=gde)


def install():
    """
    Installs icons.
    """
    import platform

    plat = platform.system()
    if plat == 'Linux':
        yesno = \
            'Install launcher icons and file type associations for Gnome/KDE? '
        try:
            yesno = raw_input(yesno)
        except NameError:   # pragma: no python 2 cover
            yesno = input(yesno)
        yesno = (yesno.strip().lower())[:1] == 'y'

        if yesno:
            install_gnome_kde()

    elif plat == 'Windows':
        yesno = 'Install start menu shortcuts? '
        try:
            yesno = raw_input(yesno)
        except NameError:   # pragma: no python 2 cover
            yesno = input(yesno)
        yesno = (yesno.strip().lower())[:1] == 'y'

        if yesno:
            install_windows()

    elif plat == 'Darwin':
        print(
            'Icons for OS/X are not available (yet). See '
            'https://github.com/MichaelClerx/myokit/issues/38')

    else:
        print('Unknown platform: ' + plat)
        print('Icons not available.')


def install_gnome_kde():
    """
    Installs launchers and associates file types for gnome/kde systems.
    """
    import os
    import sys
    import shutil
    import myokit

    # Get user home dir
    home = os.path.expanduser('~')

    # Get template directory
    dir_templates = os.path.join(myokit.DIR_DATA, 'install-lin')

    # Get icon directory
    dir_icons = os.path.join(myokit.DIR_DATA, 'gui')

    # Copies file and creates directory structure
    def place_file(path, name, template=False):
        print('Placing ' + str(name) + ' in ' + str(path))

        orig = os.path.join(dir_templates, name)
        dest = os.path.join(path, name)
        if not os.path.exists(orig):
            print('Error: file not found ' + orig)
            sys.exit(1)
        if os.path.exists(path):
            if not os.path.isdir(path):
                print(
                    'Error: Cannot create output directory. A file exists at '
                    + path)
                sys.exit(1)
        else:
            print('  Creating directory structure: ' + path)
            os.makedirs(path)

        if template:
            # Process templates, create files
            p = myokit.pype.TemplateEngine()
            varmap = {'icons': dir_icons}
            with open(dest, 'w') as f:
                p.set_output_stream(f)
                p.process(orig, varmap)
        else:
            shutil.copyfile(orig, dest)

    # Desktop files
    print('Installing desktop files...')
    path = os.path.join(home, '.local', 'share', 'applications')
    place_file(path, 'myokit-ide.desktop', True)
    place_file(path, 'myokit-datalog-viewer.desktop', True)
    place_file(path, 'myokit-datablock-viewer.desktop', True)
    place_file(path, 'myokit-gde.desktop', True)

    # Mime-type file
    print('Installing mmt mime-type...')
    path = os.path.join(home, '.local', 'share', 'mime', 'packages')
    name = 'x-myokit.xml'
    place_file(path, name)
    print('Installing gde mime-type...')
    path = os.path.join(home, '.local', 'share', 'mime', 'packages')
    name = 'x-gde.xml'
    place_file(path, name)
    print('Installing abf mime-type...')
    path = os.path.join(home, '.local', 'share', 'mime', 'packages')
    name = 'x-abf.xml'
    place_file(path, name)
    print('Installing wcp mime-type...')
    path = os.path.join(home, '.local', 'share', 'mime', 'packages')
    name = 'x-wcp.xml'
    place_file(path, name)
    # Reload mime database
    print('Reloading mime database')
    path = home + '/.local/share/mime/'
    from subprocess import call
    call(['update-mime-database', path])

    # GtkSourceView file
    print('Installing gtksourceview file for mmt syntax highlighting...')
    path = os.path.join(
        home, '.local', 'share', 'gtksourceview-3.0', 'language-specs')
    name = 'myokit.lang'
    place_file(path, name)

    print('Done')


def install_windows():
    """
    Install start-menu icons on windows systems.
    """
    import platform
    if platform.system() != 'Windows':
        raise Exception('Not a windows machine.')

    import os
    #import shutil
    import tempfile

    import myokit
    import myokit.pype
    import menuinst

    # Process template to get icon directory
    tdir = tempfile.mkdtemp()
    try:
        p = myokit.pype.TemplateEngine()
        source = os.path.join(myokit.DIR_DATA, 'install-win', 'menu.json')
        varmap = {'icons': os.path.join(myokit.DIR_DATA, 'gui')}
        output = os.path.join(tdir, 'menu.json')
        with open(output, 'w') as f:
            p.set_output_stream(f)
            p.process(source, varmap)
        del(p)

        # Install
        menuinst.install(output)
        print('Done')

    finally:
        #shutil.rmtree(tdir)
        pass


def add_icon_parser(subparsers):
    """
    Adds a subcommand parser for the ``icons`` command.
    """
    icon_parser = subparsers.add_parser(
        'icons',
        description='Installs launchers / start menu shortcuts for Myokit.',
        help='Installs launchers / start menu shortcuts for Myokit.',
    )
    icon_parser.set_defaults(func=install)


def ide(filename, pyqt4=False, pyqt5=False, pyside=False):
    """
    Runs the Myokit IDE.
    """
    import myokit
    if pyqt5:
        myokit.FORCE_PYQT5 = True
        myokit.FORCE_PYQT4 = False
        myokit.FORCE_PYSIDE = False
    elif pyqt4:
        myokit.FORCE_PYQT5 = False
        myokit.FORCE_PYQT4 = True
        myokit.FORCE_PYSIDE = False
    elif pyside:
        myokit.FORCE_PYQT4 = False
        myokit.FORCE_PYQT4 = False
        myokit.FORCE_PYSIDE = True
    import myokit.gui
    import myokit.gui.ide
    if pyqt5 or pyqt4 or pyside:
        print('Using backend: ' + myokit.gui.backend)
    myokit.gui.run(myokit.gui.ide.MyokitIDE, filename)


def add_ide_parser(subparsers):
    """
    Adds a subcommand parser for the `compare` command.
    """
    ide_parser = subparsers.add_parser(
        'ide',
        description='Runs the Myokit IDE prototype.',
        help='Runs the Myokit IDE prototype.',
    )
    ide_parser.add_argument(
        'filename',
        default=None,
        nargs='?',
        metavar='filename',
        help='The mmt file to open (optional).',
    )
    ide_parser.add_argument(
        '--pyqt5',
        action='store_true',
        help='Run the IDE using the PyQt5 backend.',
    )
    ide_parser.add_argument(
        '--pyqt4',
        action='store_true',
        help='Run the IDE using the PyQt4 backend.',
    )
    ide_parser.add_argument(
        '--pyside',
        action='store_true',
        help='Run the IDE using the PySide backend.',
    )
    ide_parser.set_defaults(func=ide)


def mmt_import(importer, source, target=None):
    """
    Imports a model and saves it in mmt format.
    """
    import myokit

    # Get importer
    importer = myokit.formats.importer(importer)

    # Get logger
    logger = importer.logger()

    # If a target is specified, set the importer to live logging mode
    if target:
        logger.set_live(True)
    logger.log_flair(str(importer.__class__.__name__))

    # Import
    m = importer.model(source)

    # If a target is specified, save the output
    if target:
        # Save or output model to new location
        logger.log('Saving output to ' + str(target))
        myokit.save(target, m)
        logger.log('Done.')
    else:
        # Write it to screen
        print(myokit.save(None, m))


def add_import_parser(subparsers):
    """
    Adds a subcommand parser for the `import` command.
    """
    import myokit
    import myokit.formats

    import_parser = subparsers.add_parser(
        'import',
        description='Imports a file using any available importer. An output'
                    ' file can be specified or the resulting mmt file can be'
                    ' printed directly to screen.',
        help='Imports a file and generates an mmt file.',
    )
    import_parser.add_argument(
        'importer',
        metavar='importer',
        help='The importer to use.',
        choices=myokit.formats.importers(),
    )
    import_parser.add_argument(
        'source',
        metavar='source_file',
        help='The source file to parse.',
    )
    import_parser.add_argument(
        'target',
        default=None,
        nargs='?',  # ? = Zero or one
        metavar='target_file',
        help='The mmt file to write (optional).',
    )
    import_parser.set_defaults(func=mmt_import)


def log(filenames):
    """
    Runs the DataLog Viewer.
    """
    import myokit.gui
    import myokit.gui.datalog_viewer
    myokit.gui.run(myokit.gui.datalog_viewer.DataLogViewer, *filenames)


def add_log_parser(subparsers):
    """
    Adds a subcommand parser for the `log` command.
    """
    import argparse

    log_parser = subparsers.add_parser(
        'log',
        description='Runs the DataLog Viewer (PROTOTYPE).',
        help='Runs the DataLog Viewer (PROTOTYPE).',
    )
    log_parser.add_argument(
        'filenames',
        default=None,
        nargs=argparse.REMAINDER,
        metavar='filename',
        help='The DataLog zip file to open (optional).',
    )
    log_parser.set_defaults(func=log)


def opencl():
    """
    Queries for OpenCL support.
    """
    import myokit
    print(myokit.OpenCL.info(formatted=True))


def add_opencl_parser(subparsers):
    """
    Adds a subcommand parser for the `opencl` command.
    """
    opencl_parser = subparsers.add_parser(
        'opencl',
        description='Checks for OpenCL support and prints some information'
                    ' about the available devices. If no support is found, an'
                    ' error message is displayed.',
        help='Prints information about OpenCL devices.',
    )
    opencl_parser.set_defaults(func=opencl)


def opencl_select():
    """
    Lets the user select the OpenCL device to use.
    """
    import sys
    import myokit

    w = 70
    print('=' * w)
    print('Myokit OpenCL device selection')
    print('=' * w)

    # Get info about devices
    devices = myokit.OpenCL.selection_info()

    # Get current selection
    old_platform, old_device = myokit.OpenCL.load_selection()

    # Display name
    def name(x):
        return 'No preference' if x is None else x

    # Show header
    print('Selected platform: ' + name(old_platform))
    print('Selected device  : ' + name(old_device))
    print('=' * w)
    print('Available devices:')
    print('-' * w)

    # Create and display list of options
    options = []

    # Option 0: Automatic select
    idx = 1
    print('(1) Select automatically.')
    print('-' * w)
    options.append((None, None))

    # Remaining devices
    for platform, device, specs in devices:
        options.append((platform, device))
        idx += 1
        space = ' ' * (3 + len(str(idx)))
        print('(' + str(idx) + ') Platform: ' + platform)
        print(space + 'Device: ' + device)
        print(space + specs)
        print('-' * w)

    # Select
    n = len(options)
    if n < 2:
        print('No OpenCL devices found!')
        sys.exit(1)
    if n == 2:
        q = '1 or 2'
    elif n < 6:
        q = ','.join([str(x) for x in range(1, n)]) + ' or ' + str(n)
    else:
        q = 'one of 1,2,3,...,' + str(n)

    print('Please select an OpenCL device by typing ' + q)
    print('Leave blank to keep current selection.')

    try:
        while True:
            x = 'Select device: '
            try:
                x = raw_input(x)
            except NameError:   # pragma: no python 2 cover
                x = input(x)    # lgtm [py/use-of-input]
            x = x.strip()
            if x == '':
                x = None
                break
            try:
                x = int(x)
                if x > 0 and x <= n:
                    break
            except ValueError:
                pass
            print('Invalid selection, please retry')
    except KeyboardInterrupt:
        print('')
        print('OpenCL device selection aborted.')
        sys.exit(0)

    print('-' * w)

    if x is None:
        platform, device = old_platform, old_device
    else:
        platform, device = options[x - 1]

    print('Selected platform: ' + name(platform))
    print('Selected device  : ' + name(device))

    if x is None:
        print('Selection unchanged.')
    else:
        myokit.OpenCL.save_selection(platform, device)
        print('Selection updated.')


def add_opencl_select_parser(subparsers):
    """
    Adds a subcommand parser for the `opencl_select` command.
    """
    opencl_select_parser = subparsers.add_parser(
        'opencl-select',
        description='Lets you select which OpenCL device Myokit should use.',
        help='Lets you select which OpenCL device Myokit should use.',
    )
    opencl_select_parser.set_defaults(func=opencl_select)


def reset(force=False):
    """
    Removes all Myokit settings files.
    """
    import sys
    import myokit

    # Ask user if settings should be deleted
    if force:
        remove = True
    else:
        yesno = 'Remove all Myokit settings files? '
        try:
            yesno = raw_input(yesno)
        except NameError:           # pragma: no python 2 cover
            yesno = input(yesno)    # lgtm [py/use-of-input]
        yesno = yesno.strip().lower()
        remove = (yesno[:1] == 'y')
    if remove:
        print('Removing')
        print('  ' + myokit.DIR_USER)
        import shutil
        shutil.rmtree(myokit.DIR_USER)
        print('Done')
    else:
        print('Aborting.')
        sys.exit(1)


def add_reset_parser(subparsers):
    """
    Adds a subcommand parser for the `reset` command.
    """
    reset_parser = subparsers.add_parser(
        'reset',
        description='Removes all Myokit settings files, resetting Myokit to'
                    ' its default configuration.',
        help='Removes all Myokit settings files.',
    )
    reset_parser.add_argument(
        '--force',
        action='store_true',
        help='Delete without prompting the user first.',
    )
    reset_parser.set_defaults(func=reset)


def run(source, debug, debugfile):
    """
    Runs an mmt file script.
    """
    import sys
    import myokit

    # Debug?
    myokit.DEBUG = myokit.DEBUG or debug or debugfile

    # Read mmt file
    try:
        print('Reading model from ' + source)
        b = myokit.Benchmarker()
        (model, protocol, script) = myokit.load(source)
        print('File loaded in ' + str(b.time()) + ' seconds')
        if model is None:
            print('No model definition found')
        else:
            print('Model read successfully')
            print(model.format_warnings())
            model.solvable_order()
    except myokit.ParseError as ex:
        print(myokit.format_parse_error(ex, source))
        sys.exit(1)

    # Set up pacing protocol
    if protocol is None:
        print('No protocol definition found')
        print('Preparing default pacing protocol (1ms stimulus, 1bpm)')
        protocol = myokit.pacing.blocktrain(1000, 1)

    # Set up script
    if script is None:
        if model is None:
            print('No script or model found, terminating')
            sys.exit(1)
        else:
            print('No embedded script found, using default.')
            script = myokit.default_script()
    else:
        print('Using embedded script')

    # Run, capture output and write to file
    if debugfile:
        debugfile = debugfile[0]
        with open(debugfile, 'w') as f:
            stdout = sys.stdout
            try:
                sys.stdout = f
                line_numbers = myokit.DEBUG_LINE_NUMBERS
                myokit.DEBUG_LINE_NUMBERS = False
                myokit.run(model, protocol, script)
            except SystemExit:
                pass
            finally:
                sys.stdout = stdout
                myokit.DEBUG_LINE_NUMBERS = line_numbers
            print('Output written to ' + str(debugfile))

    else:

        # Show script
        printline()
        lines = script.splitlines()
        template = '{:>3d} {:s}'
        i = 0
        for line in lines:
            i += 1
            print(template.format(i, line))
        printline()

        # Run!
        myokit.run(model, protocol, script)


def add_run_parser(subparsers):
    """
    Adds a subcommand parser for the `run` command.
    """
    run_parser = subparsers.add_parser(
        'run',
        description='Runs the embedded script in an mmt file. If no embedded'
                    ' script is available a simulation with a default script'
                    ' is attempted.',
        help='Runs an mmt file.',
    )
    run_parser.add_argument(
        'source',
        metavar='source_file.mmt',
        help='The source file to parse.',
    )
    run_parser.add_argument(
        '--debug',
        action='store_true',
        help='Show the generated code instead of executing it.',
    )
    run_parser.add_argument(
        '--debugfile',
        nargs=1,
        metavar='debugfile',
        help='Write the generated code to a file instead of executing it.',
        default=None,
    )
    run_parser.set_defaults(func=run)


def step(source, ref, ini, raw):
    """
    Loads a model and evaluates the state vector derivatives.
    """
    import sys
    import myokit

    # Parse reference file, if given
    if ref and not raw:
        print('Reading reference file...')
        try:
            ref = myokit.load_model(ref[0])
            print('Reference model loaded successfully.')
        except Exception:
            ref = myokit.load_state(ref[0])
            print('Reference file read successfully.')

    # Parse initial value file, if given
    if ini:
        if not raw:
            print('Reading initial value file...')
        ini = myokit.load_state(ini[0])
        if not raw:
            print('Initial value file read successfully.')

    # Load myokit model
    try:
        if not raw:
            print('Reading model from ' + source + '...')
        model = myokit.load_model(source)
        if not raw:
            print('Model ' + model.name() + ' read successfully.')
    except myokit.ParseError as ex:
        print(myokit.format_parse_error(ex, source))
        sys.exit(1)

    # Ensure proper ordering of reference and initial value files
    if ref and not isinstance(ref, myokit.Model):
        ref = model.map_to_state(ref)

    # Evaluate all derivatives, show the results
    try:
        if raw:
            derivs = model.eval_state_derivatives(state=ini)
            print('\n'.join([myokit.strfloat(x) for x in derivs]))
        else:
            print(myokit.step(model, initial=ini, reference=ref))
    except myokit.NumericalError as ee:
        e = 'Numerical error'
        n = line_width - len(e) - 2
        print('-' * int(n / 2) + ' ' + e + ' ' + '-' * (n - int(n / 2)))
        print('A numerical error occurred:')
        print(str(ee))


def add_step_parser(subparsers):
    """
    Adds a subcommand parser for the `step` command.
    """
    step_parser = subparsers.add_parser(
        'step',
        description='Loads a model and evaluates the state vector derivatives.'
                    ' The optional argument -ref <source_file> can be used to'
                    ' compare the calculated derivatives to a list of'
                    ' pre-calculated floats.',
        help='Evaluates a model\'s derivatives.',
    )
    step_parser.add_argument(
        'source',
        metavar='source_file',
        help='The source file to parse',
    )
    step_parser.add_argument(
        '-ref',
        nargs=1,
        metavar='ref',
        help='A text file with a list of numbers to compare against, or a'
             ' reference model to compare against.',
        default=None,
    )
    step_parser.add_argument(
        '-ini',
        nargs=1,
        metavar='ini',
        help='A text file with a list of initial values for the state'
             ' variables',
        default=None,
    )
    step_parser.add_argument(
        '--raw',
        action='store_true',
        help='Display the calculated state, without further formatting.',
    )
    step_parser.set_defaults(func=step)


def sundials():
    """
    Queries for Sundials support.
    """
    import myokit
    version = myokit.Sundials.version()
    if version is None:
        print('Sundials not found or compilation failed.')
    else:
        print('Found Sundials version ' + version)


def add_sundials_parser(subparsers):
    """
    Adds a subcommand parser for the `sundials` command.
    """
    sundials_parser = subparsers.add_parser(
        'sundials',
        description='Checks for Sundials support.',
        help='Prints information about Sundials support.',
    )
    sundials_parser.set_defaults(func=sundials)


def system():
    """
    Displays system information.
    """
    import myokit
    myokit.system(live_printing=True)


def add_system_parser(subparsers):
    """
    Adds a subcommand parser for the `system` command.
    """
    sundials_parser = subparsers.add_parser(
        'system',
        description='Show system information.',
        help='Prints information about the current system.',
    )
    sundials_parser.set_defaults(func=system)


def version(raw=False):
    import myokit
    print(myokit.version(raw))


def add_version_parser(subparsers):
    """
    Adds a subcommand parser for the `version` command.
    """
    version_parser = subparsers.add_parser(
        'version',
        description='Prints Myokit\'s version number.',
        help='Prints Myokit\'s version number.',
    )
    version_parser.add_argument(
        '--raw',
        action='store_true',
        help='Only print the version number, no other information.',
    )
    version_parser.set_defaults(func=version)


def video(src, key, dst, fps, colormap):
    """
    Use "moviepy" to create an animation from a DataBlock2d.
    """
    import os
    import sys
    import myokit

    # Test if moviepy is installed
    print('Loading moviepy.')
    try:
        import moviepy.editor as mpy
    except ImportError:
        print('This function requires MoviePy to be installed.')
        sys.exit(1)
    print('Done.')

    # Get filename
    src = os.path.abspath(os.path.expanduser(str(src)))

    # Supported codecs
    codecs = {
        # Uncompressed avi doesn't seem to work!
        '.avi': 'png',          # AVI with png compression
        '.flv': 'flv',          # Flash video...
        '.gif': 'gif',
        '.mp4': None,           # libx264 mp4 compression
        '.mpeg': 'mpeg1video',  # Older mpeg1 compression
        #'.ogv': 'libvorbis',
        '.webm': 'libvpx',      # For HTML5
        '.wmv': 'wmv1',         # Windows media
    }

    # Get codec from destination file
    ext = os.path.splitext(dst)[1].lower()
    try:
        codec = codecs[ext]
    except KeyError:
        print('Unable to determine codec for "' + ext + '"')
        print('Known extensions:')
        for ext in codecs:
            print('  ' + ext)
        sys.exit(1)

    # Get frame rate
    fps = int(fps)
    if fps < 1:
        print('Frame rate must be integer greater than zero.')
        sys.exit(1)

    # Open file
    class Reporter(myokit.ProgressReporter):
        def __init__(self):
            self._last = 0

        def enter(self, msg=None):
            sys.stdout.write('Loading file: 0%' + chr(8) * 2)
            sys.stdout.flush()

        def exit(self):
            sys.stdout.write('\n')
            sys.stdout.flush()

        def update(self, f):
            p = int(f * 100)
            if p > self._last:
                self._last = p
                p = str(p) + '%'
                sys.stdout.write(p + chr(8) * len(p))
                sys.stdout.flush()
            return True

    reporter = Reporter()

    try:
        data = myokit.DataBlock2d.load(src, progress=reporter)
    except myokit.DataBlockReadError as e:
        print('DataBlock reading failed\n: ' + str(e))
        sys.exit(1)
    finally:
        del(reporter)

    # Don't load empty files
    if data.len2d() < 1:
        print('Empty DataBlock loaded!')
        sys.exit(1)

    # Check if key exists in 2d data
    try:
        data.get2d(key)
    except KeyError:
        print('Key not found in DataBlock: <' + str(key) + '>.')
        sys.exit(1)

    # File loaded okay
    nt, ny, nx = data.shape()
    print('Done.')
    print('  nx = ' + str(nx))
    print('  ny = ' + str(ny))
    print('  nt = ' + str(nt))

    # Create movie
    print('Converting data into image frames.')
    frames = data.colors(key, colormap=colormap)
    print('Compiling frames into video clip.')
    video = mpy.ImageSequenceClip(frames, fps=fps)
    rate = str(nx * ny * fps * 4)
    video.write_videofile(dst, fps=24, audio=False, codec=codec, bitrate=rate)


def add_video_parser(subparsers):
    """
    Adds a subcommand parser for the `video` command.
    """
    import myokit

    video_parser = subparsers.add_parser(
        'video',
        description='Uses "moviepy" to convert a DataBlock to a video file.'
                    ' The video format to use is guessed based on the'
                    ' extension of the output file.',
        help='Creates video files from DataBlocks.',
        usage='\nCreate video files:'
              '\n  myokit video datablock.zip membrane.V -dst movie.mp4'
              '\nMore options:'
              '\n  myokit -h',
    )
    video_parser.add_argument(
        'src',
        metavar='datablock.zip',
        help='The DataBlock file to convert',
    )
    video_parser.add_argument(
        'key',
        metavar='membrane.V',
        help='The 2d time series in the DataBlock to convert to video',
    )
    video_parser.add_argument(
        '-dst',
        metavar='movie.mp4',
        help='The video file to write',
        default='movie.mp4',
    )
    video_parser.add_argument(
        '-fps',
        metavar='fps',
        help='The number of (DataBlock) frames per second',
        default=16,
    )
    video_parser.add_argument(
        '-colormap',
        metavar='colormap',
        help='The ColorMap to use when converting the DataBlock.',
        default='traditional',
        choices=myokit.ColorMap.names(),
    )
    video_parser.set_defaults(func=video)


if __name__ == '__main__':
    main()
