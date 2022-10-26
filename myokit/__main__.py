#
# Command line tools.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import warnings

_line_width = 79


def printline():
    """ Utility method for printing horizontal lines. """
    print('-' * 60)


def colored(color, text):
    """ Utility method for printing colored text. """
    colors = {
        'normal': '\033[0m',
        'warning': '\033[93m',
        'fail': '\033[91m',
        'bold': '\033[1m',
        'underline': '\033[4m',
    }
    return colors[color] + str(text) + colors['normal']


def main():
    """
    Parses command line arguments.
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
    add_test_parser(subparsers)             # Run tests
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
        del args['func']

        # Call the selected function with the parsed arguments
        func(**args)


#
# Data block viewer
#

def block(filename, pyqt4=False, pyqt5=False, pyside=False, pyside2=False):
    """
    Runs the DataBlock viewer.
    """
    import myokit
    if pyqt5:
        myokit.FORCE_PYQT5 = True
        myokit.FORCE_PYQT4 = False
        myokit.FORCE_PYSIDE = False
        myokit.FORCE_PYSIDE2 = False
    elif pyqt4:
        myokit.FORCE_PYQT5 = False
        myokit.FORCE_PYQT4 = True
        myokit.FORCE_PYSIDE = False
        myokit.FORCE_PYSIDE2 = False
    elif pyside:
        myokit.FORCE_PYQT5 = False
        myokit.FORCE_PYQT4 = False
        myokit.FORCE_PYSIDE = True
        myokit.FORCE_PYSIDE2 = False
    elif pyside2:
        myokit.FORCE_PYQT5 = False
        myokit.FORCE_PYQT4 = False
        myokit.FORCE_PYSIDE = False
        myokit.FORCE_PYSIDE2 = True
    import myokit.gui
    import myokit.gui.datablock_viewer
    if pyqt5 or pyqt4 or pyside or pyside2:
        print('Using backend: ' + myokit.gui.backend)
    myokit.gui.run(myokit.gui.datablock_viewer.DataBlockViewer, filename)


def add_block_parser(subparsers):
    """
    Adds a subcommand parser for `block`.
    """
    parser = subparsers.add_parser(
        'block',
        description='Runs the DataBlock Viewer.',
        help='Runs the DataBlock Viewer.',
    )
    parser.add_argument(
        'filename',
        default=None,
        nargs='?',
        metavar='filename',
        help='The DataBlock zip file to open (optional).',
    )
    parser.add_argument(
        '--pyqt5',
        action='store_true',
        help='Run the DataBlock Viewer using the PyQt5 backend.',
    )
    parser.add_argument(
        '--pyqt4',
        action='store_true',
        help='Run the DataBlock Viewer using the PyQt4 backend.',
    )
    parser.add_argument(
        '--pyside',
        action='store_true',
        help='Run the DataBlock Viewer using the PySide backend.',
    )
    parser.add_argument(
        '--pyside2',
        action='store_true',
        help='Run the DataBlock Viewer using the PySide2 backend.',
    )
    parser.set_defaults(func=block)


#
# Compare
#

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
    Adds a subcommand parser for the ``compare`` command.
    """
    parser = subparsers.add_parser(
        'compare',
        description='Compares two models by inspecting their components,'
                    ' variables, meta-data etc.',
        help='Compares two models.',
    )
    parser.add_argument(
        'model1',
        metavar='model1..mmt',
        help='One of the models to compare.',
    )
    parser.add_argument(
        'model2',
        metavar='model2.mmt',
        help='The model to compare with.',
    )
    parser.set_defaults(func=compare)


#
# Compiler
#

def compiler(debug):
    """
    Tests for C compilation support.
    """
    import myokit
    compiler = myokit.Compiler.info(debug)
    if compiler is None:
        print('Compilation with distutils/setuptools failed.')
    else:
        print('Compilation successful. Found: ' + compiler)


def add_compiler_parser(subparsers):
    """
    Adds a subcommand parser for the ``compiler`` command.
    """
    parser = subparsers.add_parser(
        'compiler',
        description='Checks for C compilation support.',
        help='Prints information about C compilation support.',
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Show error output.',
    )
    parser.set_defaults(func=compiler)


#
# Debug
#

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
    Adds a subcommand parser for the ``debug`` command.
    """
    parser = subparsers.add_parser(
        'debug',
        description='Shows how a single variable is calculated from the '
                    'initial conditions. The variable\'s equation and value'
                    ' are displayed, along with the value and formula of any'
                    ' nested variables and the values of all dependencies.',
        help='Shows how a single variable is calculated.',
    )
    parser.add_argument(
        'source',
        metavar='source_file.mmt',
        help='The source file to parse.',
    )
    parser.add_argument(
        'variable',
        metavar='variable',
        help='The variable whose evaluation to display.',
    )
    parser.add_argument(
        '--deps',
        action='store_true',
        help='Show dependencies instead of numerical evaluation.',
    )
    parser.set_defaults(func=debug)


#
# Eval
#

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
    Adds a subcommand parser for the ``eval`` command.
    """
    parser = subparsers.add_parser(
        'eval',
        description='Evaluates an expression in myokit syntax.',
        help='Evaluates an expression in myokit syntax.',
    )
    parser.add_argument(
        'expression',
        metavar='"1 + 2 / 3"',
        help='The expression to evaluate.',
    )
    parser.set_defaults(func=evaluate)


#
# Export
#

def mmt_export(exporter, source, target):
    """
    Exports a myokit model.
    """
    import sys
    import myokit
    import myokit.formats

    # Get exporter
    name = exporter
    exporter = myokit.formats.exporter(name)
    print(str(exporter.__class__.__name__))

    # Parse input file
    try:
        print('Reading model from ' + myokit.tools.format_path(source))
        model, protocol, script = myokit.load(source)
    except myokit.ParseError as ex:
        print(myokit.format_parse_error(ex, source))
        sys.exit(1)

    # Must have model
    if model is None:
        print('Error: Imported file must contain model definition.')
        sys.exit(1)
    else:
        print('Model read successfully')

    # Export model or runnable
    with warnings.catch_warnings(record=True) as ws:
        if exporter.supports_model():
            # Export model
            print('Exporting model')
            if name == 'cellml':
                exporter.model(target, model, protocol)
            else:
                exporter.model(target, model)
        else:
            # Export runnable
            print('Exporting runnable')
            if protocol is None:
                print('No protocol found.')
            else:
                print('Using embedded protocol.')
            exporter.runnable(target, model, protocol)
    for w in ws:
        print('Warning: ' + str(w.message))
    print('Export successful')

    info = exporter.post_export_info()
    if info:
        print(info)


def add_export_parser(subparsers):
    """
    Adds a subcommand parser for the ``export`` command.
    """
    import myokit
    import myokit.formats

    parser = subparsers.add_parser(
        'export',
        description='Exports a Myokit model using the specified exporter.',
        help='Exports a Myokit model.',
    )
    parser.add_argument(
        'exporter',
        metavar='exporter',
        help='The exporter to use.',
        choices=myokit.formats.exporters(),
    )
    parser.add_argument(
        'source',
        metavar='source',
        help='The source file to parse.',
    )
    parser.add_argument(
        'target',
        metavar='target',
        help='The output file or directory.'
    )
    parser.set_defaults(func=mmt_export)


#
# Icons / installation
#

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
            'Icons for MacOS are not available (yet). See '
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
            varmap = {
                'icons': dir_icons,
                'python': sys.executable,
            }
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

    # Mime-type file
    print('Installing mmt mime-type...')
    path = os.path.join(home, '.local', 'share', 'mime', 'packages')
    place_file(path, 'x-myokit.xml')
    print('Installing CellML mime-type...')
    place_file(path, 'x-cellml.xml')
    print('Installing abf mime-type...')
    place_file(path, 'x-abf.xml')
    print('Installing wcp mime-type...')
    place_file(path, 'x-wcp.xml')

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
    import tempfile

    import menuinst

    import myokit
    import myokit.pype

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
        del p

        # Install
        menuinst.install(output)
        print('Done')

    finally:
        myokit.tools.rmtree(tdir)


def add_icon_parser(subparsers):
    """
    Adds a subcommand parser for the ``icons`` command.
    """
    parser = subparsers.add_parser(
        'icons',
        description='Installs launchers / start menu shortcuts for Myokit.',
        help='Installs launchers / start menu shortcuts for Myokit.',
    )
    parser.set_defaults(func=install)


#
# IDE
#

def ide(filename, pyqt4=False, pyqt5=False, pyside=False, pyside2=False):
    """
    Runs the Myokit IDE.
    """
    import os
    import myokit
    if pyqt5:
        myokit.FORCE_PYQT5 = True
        myokit.FORCE_PYQT4 = False
        myokit.FORCE_PYSIDE = False
        myokit.FORCE_PYSIDE2 = False
    elif pyqt4:
        myokit.FORCE_PYQT5 = False
        myokit.FORCE_PYQT4 = True
        myokit.FORCE_PYSIDE = False
        myokit.FORCE_PYSIDE2 = False
    elif pyside:
        myokit.FORCE_PYQT5 = False
        myokit.FORCE_PYQT4 = False
        myokit.FORCE_PYSIDE = True
        myokit.FORCE_PYSIDE2 = False
    elif pyside2:
        myokit.FORCE_PYQT5 = False
        myokit.FORCE_PYQT4 = False
        myokit.FORCE_PYSIDE = False
        myokit.FORCE_PYSIDE2 = True
    import myokit.gui
    import myokit.gui.ide
    if pyqt5 or pyqt4 or pyside or pyside2:
        print('Using backend: ' + myokit.gui.backend)
    if filename is not None:
        filename = os.path.abspath(os.path.expanduser(filename))
    myokit.gui.run(myokit.gui.ide.MyokitIDE, filename)


def add_ide_parser(subparsers):
    """
    Adds a subcommand parser for the ``compare`` command.
    """
    parser = subparsers.add_parser(
        'ide',
        description='Runs the Myokit IDE prototype.',
        help='Runs the Myokit IDE prototype.',
    )
    parser.add_argument(
        'filename',
        default=None,
        nargs='?',
        metavar='filename',
        help='The mmt file to open (optional).',
    )
    parser.add_argument(
        '--pyqt5',
        action='store_true',
        help='Run the IDE using the PyQt5 backend.',
    )
    parser.add_argument(
        '--pyqt4',
        action='store_true',
        help='Run the IDE using the PyQt4 backend.',
    )
    parser.add_argument(
        '--pyside',
        action='store_true',
        help='Run the IDE using the PySide backend.',
    )
    parser.add_argument(
        '--pyside2',
        action='store_true',
        help='Run the DataBlock Viewer using the PySide2 backend.',
    )
    parser.set_defaults(func=ide)


#
# Import
#

def mmt_import(importer, source, target=None):
    """
    Imports a model and saves it in mmt format.
    """
    import myokit

    # Get importer
    importer = myokit.formats.importer(importer)
    print(str(importer.__class__.__name__))

    # Import
    with warnings.catch_warnings(record=True) as ws:
        model = importer.model(source)
    for w in ws:
        print('Warning: ' + str(w.message))

    # Try to split off an embedded protocol
    protocol = myokit.lib.guess.remove_embedded_protocol(model)

    # No protocol? Then create one
    if protocol is None:
        protocol = myokit.default_protocol(model)

    # Get default script
    script = myokit.default_script(model)

    # If a target is specified, save the output
    if target:
        # Save or output model to new location
        print('Saving output to ' + str(target))
        myokit.save(target, model, protocol, script)
        print('Done.')
    else:
        # Write it to screen
        print(myokit.save(None, model, protocol, script))


def add_import_parser(subparsers):
    """
    Adds a subcommand parser for the ``import`` command.
    """
    import myokit
    import myokit.formats

    parser = subparsers.add_parser(
        'import',
        description='Imports a file using any available importer. An output'
                    ' file can be specified or the resulting mmt file can be'
                    ' printed directly to screen.',
        help='Imports a file and generates an mmt file.',
    )
    parser.add_argument(
        'importer',
        metavar='importer',
        help='The importer to use.',
        choices=myokit.formats.importers(),
    )
    parser.add_argument(
        'source',
        metavar='source_file',
        help='The source file to parse.',
    )
    parser.add_argument(
        'target',
        default=None,
        nargs='?',  # ? = Zero or one
        metavar='target_file',
        help='The mmt file to write (optional).',
    )
    parser.set_defaults(func=mmt_import)


#
# Log viewer
#

def log(filenames):
    """
    Runs the DataLog Viewer.
    """
    import myokit.gui
    import myokit.gui.datalog_viewer
    myokit.gui.run(myokit.gui.datalog_viewer.DataLogViewer, *filenames)


def add_log_parser(subparsers):
    """
    Adds a subcommand parser for the ``log`` command.
    """
    import argparse

    parser = subparsers.add_parser(
        'log',
        description='Runs the DataLog Viewer (PROTOTYPE).',
        help='Runs the DataLog Viewer (PROTOTYPE).',
    )
    parser.add_argument(
        'filenames',
        default=None,
        nargs=argparse.REMAINDER,
        metavar='filename',
        help='The DataLog zip file to open (optional).',
    )
    parser.set_defaults(func=log)


#
# OpenCL info
#

def opencl():
    """
    Queries for OpenCL support.
    """
    import myokit
    print(myokit.OpenCL.info(formatted=True))


def add_opencl_parser(subparsers):
    """
    Adds a subcommand parser for the ``opencl`` command.
    """
    parser = subparsers.add_parser(
        'opencl',
        description='Checks for OpenCL support and prints some information'
                    ' about the available devices. If no support is found, an'
                    ' error message is displayed.',
        help='Prints information about OpenCL devices.',
    )
    parser.set_defaults(func=opencl)


#
# OpenCL select
#

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
    Adds a subcommand parser for the ``opencl_select`` command.
    """
    parser = subparsers.add_parser(
        'opencl-select',
        description='Lets you select which OpenCL device Myokit should use.',
        help='Lets you select which OpenCL device Myokit should use.',
    )
    parser.set_defaults(func=opencl_select)


#
# Reset
#

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
        myokit.tools.rmtree(myokit.DIR_USER)
        print('Done')
    else:
        print('Aborting.')
        sys.exit(1)


def add_reset_parser(subparsers):
    """
    Adds a subcommand parser for the ``reset`` command.
    """
    parser = subparsers.add_parser(
        'reset',
        description='Removes all Myokit settings files, resetting Myokit to'
                    ' its default configuration.',
        help='Removes all Myokit settings files.',
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Delete without prompting the user first.',
    )
    parser.set_defaults(func=reset)


#
# Run
#

def run(source, debug_sg, debug_wg, debug_sc, debug_sm, debug_sp):
    """
    Runs an mmt file script.
    """
    import sys
    import myokit

    # Debug modes
    # Show generated code
    myokit.DEBUG_SG = myokit.DEBUG_SG or debug_sg
    # Write generated code to file
    myokit.DEBUG_WG = myokit.DEBUG_WG or debug_wg
    # Show compiler output
    myokit.DEBUG_SC = myokit.DEBUG_SC or debug_sc
    # Show messages when running compiled code
    myokit.DEBUG_SM = myokit.DEBUG_SM or debug_sm
    # Show profiling information when running compiled code
    myokit.DEBUG_SP = myokit.DEBUG_SP or debug_sp

    # Read mmt file
    try:
        print('Reading model from ' + source)
        b = myokit.tools.Benchmarker()
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

    # Normal run
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
    Adds a subcommand parser for the ``run`` command.
    """
    parser = subparsers.add_parser(
        'run',
        description='Runs the embedded script in an mmt file. If no embedded'
                    ' script is available a simulation with a default script'
                    ' is attempted.',
        help='Runs an mmt file.',
    )
    parser.add_argument(
        'source',
        metavar='source_file.mmt',
        help='The source file to parse.',
    )
    parser.add_argument(
        '--debug-sg',
        action='store_true',
        help='Show the generated code instead of executing it.',
        #metavar='debug_sg',
    )
    parser.add_argument(
        '--debug-wg',
        action='store_true',
        help='Write the generated code to file(s) instead of executing it.',
        #metavar='debug_wg',
    )
    parser.add_argument(
        '--debug-sc',
        action='store_true',
        help='Show compiler output.',
        #metavar='debug_sc',
    )
    parser.add_argument(
        '--debug-sm',
        action='store_true',
        help='Show debug messages when executing compiled code.',
        #metavar='debug_sm',
    )
    parser.add_argument(
        '--debug-sp',
        action='store_true',
        help='Show profiling information when executing compiled code.',
        #metavar='debug_sp',
    )
    parser.set_defaults(func=run)


#
# Step
#

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
            print('Model ' + source + ' read successfully.')
    except myokit.ParseError as ex:
        print(myokit.format_parse_error(ex, source))
        sys.exit(1)

    # Ensure proper ordering of reference and initial value files
    if ref and not isinstance(ref, myokit.Model):
        ref = model.map_to_state(ref)

    # Evaluate all derivatives, show the results
    try:
        if raw:
            derivs = model.evaluate_derivatives(state=ini)
            print('\n'.join([myokit.float.str(x) for x in derivs]))
        else:
            print(myokit.step(model, initial=ini, reference=ref))
    except myokit.NumericalError as ee:
        e = 'Numerical error'
        n = _line_width - len(e) - 2
        print('-' * int(n / 2) + ' ' + e + ' ' + '-' * (n - int(n / 2)))
        print('A numerical error occurred:')
        print(str(ee))


def add_step_parser(subparsers):
    """
    Adds a subcommand parser for the ``step`` command.
    """
    parser = subparsers.add_parser(
        'step',
        description='Loads a model and evaluates the state vector derivatives.'
                    ' The optional argument -ref <source_file> can be used to'
                    ' compare the calculated derivatives to a list of'
                    ' pre-calculated floats.',
        help='Evaluates a model\'s derivatives.',
    )
    parser.add_argument(
        'source',
        metavar='source_file',
        help='The source file to parse',
    )
    parser.add_argument(
        '-ref',
        nargs=1,
        metavar='ref',
        help='A text file with a list of numbers to compare against, or a'
             ' reference model to compare against.',
        default=None,
    )
    parser.add_argument(
        '-ini',
        nargs=1,
        metavar='ini',
        help='A text file with a list of initial values for the state'
             ' variables',
        default=None,
    )
    parser.add_argument(
        '--raw',
        action='store_true',
        help='Display the calculated state, without further formatting.',
    )
    parser.set_defaults(func=step)


#
# Sundials
#

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
    Adds a subcommand parser for the ``sundials`` command.
    """
    parser = subparsers.add_parser(
        'sundials',
        description='Checks for Sundials support.',
        help='Prints information about Sundials support.',
    )
    parser.set_defaults(func=sundials)


#
# System
#

def system():
    """
    Displays system information.
    """
    import os
    import myokit
    myokit.system(live_printing=True)

    ini = os.path.join(myokit.DIR_USER, 'myokit.ini')
    print()
    print('= ' + ini + ' =')
    with open(ini, 'r') as f:
        print(f.read())


def add_system_parser(subparsers):
    """
    Adds a subcommand parser for the ``system`` command.
    """
    parser = subparsers.add_parser(
        'system',
        description='Show system information.',
        help='Prints information about the current system.',
    )
    parser.set_defaults(func=system)


#
# Test
#

def add_test_parser(subparsers):
    """
    Adds a parser for all the tests to a subparser.
    """
    parser = subparsers.add_parser(
        'test',
        description='Runs tests',
        help='Runs unit tests, doc tests, etc.',
    )

    # Not in repo? Then run unit tests
    if not test_in_repo():
        parser.set_defaults(func=test_unit)
        return

    # Give full options if in repo
    subparsers = parser.add_subparsers(help='commands')

    # Disable matplotlib output
    parser.add_argument(
        '--nompl',
        action='store_true',
        help='Disable matplotlib output.',
    )

    # Coverage
    coverage_parser = subparsers.add_parser(
        'coverage', help='Run unit tests and print a coverage report.')
    coverage_parser.set_defaults(testfunc=test_coverage)

    # Doctests
    doc_parser = subparsers.add_parser(
        'doc',
        help='Test documentation cover, building, and doc tests.')
    doc_parser.set_defaults(testfunc=test_documentation)

    # Example notebooks
    example_parser = subparsers.add_parser(
        'examples', help='Test example notebooks.')
    example_parser.set_defaults(testfunc=test_examples)

    # Publication examples
    pub_parser = subparsers.add_parser(
        'pub', help='Run publication examples.')
    pub_parser.set_defaults(testfunc=test_examples_pub)

    # Style tests
    style_parser = subparsers.add_parser('style', help='Run code style tests.')
    style_parser.set_defaults(testfunc=test_style)

    # Unit tests
    unit_parser = subparsers.add_parser('unit', help='Run unit tests')
    unit_parser.set_defaults(testfunc=test_unit)

    # Web examples
    web_parser = subparsers.add_parser(
        'web', help='Run web examples.')
    web_parser.set_defaults(testfunc=test_examples_web)

    # Nested test running method: maintains access to `parser`.
    def run_tests(nompl=False, testfunc=None, **args):
        if nompl:
            print('Disabling matplotlib output')
            import matplotlib
            matplotlib.use('template')

        if testfunc is None:
            parser.print_help()
        else:
            testfunc(args)

    parser.set_defaults(func=run_tests)


def test_coverage(args):
    """
    Runs the unit tests and prints a coverage report.
    """
    import os
    import subprocess
    import sys

    try:
        print('Gathering coverage data')
        p = subprocess.Popen([
            'python3',
            '-m',
            'coverage',
            'run',
            'myokit',
            'test',
            'unit',
        ])
        try:
            ret = p.wait()
        except KeyboardInterrupt:
            try:
                p.terminate()
            except OSError:
                pass
            p.wait()
            print('')
            sys.exit(1)
        if ret != 0:
            print('FAILED')
            sys.exit(ret)

        print('Generating coverage report.')
        p = subprocess.Popen([
            'python3',
            '-m',
            'coverage',
            'report',
            '-m',
            '--skip-covered',
        ])
        p.wait()

    finally:
        # Remove coverage file
        if os.path.isfile('.coverage'):
            os.remove('.coverage')


def test_documentation(args):
    """
    Checks if the documentation can be built, runs all doc tests, exits if
    anything fails.
    """
    print('Checking documentation coverage.')

    import subprocess
    import sys

    # Scan Myokit modules for classes and functions
    modules, classes, functions = test_doc_coverage_get_objects()

    # Check if they're all in the index
    ok = test_doc_coverage_index(modules, classes, functions)

    # Check if they're all shown somewhere
    ok = test_doc_coverage(classes, functions) and ok

    # Terminate if failed
    if not ok:
        sys.exit(1)

    # Build docs and run doc tests
    print('Building docs and running doctests.')
    p = subprocess.Popen([
        'sphinx-build',
        '-b',
        'doctest',
        'docs/source',
        'docs/build/html',
        '-W',
    ])
    try:
        ret = p.wait()
    except KeyboardInterrupt:
        try:
            p.terminate()
        except OSError:
            pass
        p.wait()
        print('')
        sys.exit(1)
    if ret != 0:
        print('FAILED')
        sys.exit(ret)


def test_doc_coverage(classes, functions):
    """
    Check all classes and functions exposed by Myokit are included in the docs
    somewhere.

    This method is based on one made by Fergus Cooper for PINTS.
    See https://github.com/pints-team/pints
    """
    import os
    import re

    doc_files = []
    for root, dirs, files in os.walk(os.path.join('docs', 'source')):
        for file in files:
            if file.endswith('.rst'):
                doc_files.append(os.path.join(root, file))

    # Regular expression that would find either 'module' or 'currentmodule':
    # this needs to be prepended to the symbols as x.y.z != x.z
    regex_module = re.compile(r'\.\.\s*\S*module\:\:\s*(\S+)')

    # Regular expressions to find autoclass and autofunction specifiers
    regex_class = re.compile(r'\.\.\s*autoclass\:\:\s*(\S+)')
    regex_funct = re.compile(r'\.\.\s*autofunction\:\:\s*(\S+)')

    # Identify all instances of autoclass and autofunction in all rst files
    doc_classes = []
    doc_functions = []
    for doc_file in doc_files:
        with open(doc_file, 'r') as f:
            # We need to identify which module each class or function is in
            module = ''
            for line in f.readlines():
                m_match = re.search(regex_module, line)
                c_match = re.search(regex_class, line)
                f_match = re.search(regex_funct, line)
                if m_match:
                    module = m_match.group(1) + '.'
                elif c_match:
                    doc_classes.append(module + c_match.group(1))
                elif f_match:
                    doc_functions.append(module + f_match.group(1))

    # Check if documented symbols match known classes and functions
    classes = set(classes)
    functions = set(functions)
    doc_classes = set(doc_classes)
    doc_functions = set(doc_functions)

    undoc_classes = classes - doc_classes
    undoc_functions = functions - doc_functions
    extra_classes = doc_classes - classes
    extra_functions = doc_functions - functions

    # Compare the results
    if undoc_classes:
        n = len(undoc_classes)
        printline()
        print('Found (' + str(n) + ') classes without documentation:')
        print('\n'.join(
            '  ' + colored('warning', y) for y in sorted(undoc_classes)))
    if undoc_functions:
        n = len(undoc_functions)
        printline()
        print('Found (' + str(n) + ') functions without documentation:')
        print('\n'.join(
            '  ' + colored('warning', y) for y in sorted(undoc_functions)))
    if extra_classes:
        n = len(extra_classes)
        printline()
        print('Found (' + str(n) + ') documented but unknown classes:')
        print('\n'.join(
            '  ' + colored('warning', y) for y in sorted(extra_classes)))
    if extra_functions:
        n = len(extra_functions)
        printline()
        print('Found (' + str(n) + ') documented but unknown classes:')
        print('\n'.join(
            '  ' + colored('warning', y) for y in sorted(extra_functions)))
    n = (len(undoc_classes) + len(undoc_functions)
         + len(extra_classes) + len(extra_functions))
    printline()
    print('Found total of (' + str(n) + ') mismatches.')

    return n == 0


def test_doc_coverage_get_objects():
    """
    Scans Myokit and returns a list of modules, a list of classes, and a
    list of functions.
    """
    print('Finding Myokit modules...')
    import importlib
    import inspect
    import os

    def find_modules(root, modules=[], ignore=[]):
        """ Find all modules in the given directory. """

        # Get root as module
        module_root = root.replace('/', '.')

        # Check if this path is on the ignore list
        if root in ignore:
            return modules

        # Check if this is a module
        if os.path.isfile(os.path.join(root, '__init__.py')):
            modules.append(module_root)
        else:
            return modules

        # Look for submodules
        for name in os.listdir(root):
            if name[:1] == '_' or name[:1] == '.':
                continue
            path = os.path.join(root, name)
            if os.path.isdir(path):
                find_modules(path, modules, ignore)
            else:
                base, ext = os.path.splitext(name)
                if ext == '.py':
                    modules.append(module_root + '.' + base)

        # Return found
        return modules

    # Get modules
    import myokit
    modules = find_modules('myokit', ignore=['myokit/tests'])

    # Import all modules
    for module in modules:
        importlib.import_module(module)

    # Find modules, classes, and functions
    def scan(module, root, pref, modules, classes, functions):
        nroot = len(root)
        for name, member in inspect.getmembers(module):
            if name[0] == '_':
                # Don't include private members
                continue

            # Get full name
            full_name = pref + name

            # Module
            if inspect.ismodule(member):
                try:
                    # Don't scan external modules
                    if member.__file__ is None:
                        continue
                    if member.__file__[0:nroot] != root:
                        continue
                except AttributeError:
                    # Built-ins have no __file__ and should not be included
                    continue
                if full_name in modules:
                    continue
                modules.add(full_name)
                mpref = full_name + '.'
                mroot = os.path.join(root, name)
                scan(member, mroot, mpref, modules, classes, functions)

            # Class
            elif inspect.isclass(member):
                if member.__module__.startswith('myokit.'):
                    classes.add(full_name)

            # Function
            elif inspect.isfunction(member):
                if member.__module__.startswith('myokit.'):
                    functions.add(full_name)

        return

    # Scan and return
    print('Scanning Myokit modules...')
    module = myokit
    modules = set()
    classes = set()
    functions = set()
    root = os.path.dirname(module.__file__)
    pre = module.__name__ + '.'
    scan(module, root, pre, modules, classes, functions)

    print(
        'Found (' + str(len(modules)) + ') modules, identified ('
        + str(len(classes)) + ') classes and (' + str(len(functions))
        + ') functions.')

    return modules, classes, functions


def test_doc_coverage_index(modules, classes, functions):
    """
    Checks the documentation index to see if everything is listed and to see if
    nothing is listed that shouldn't be listed.
    """
    import os
    import re

    def scan_docs(path):
        """ Scan api_index docs """
        r = re.compile('(class|meth):`([^`]*)`')

        def read_file(fpath, classes, functions):
            with open(fpath, 'r') as f:
                for m in r.finditer(f.read()):
                    xtype = m.string[m.start(1):m.end(1)]
                    xname = m.string[m.start(2):m.end(2)]
                    if xtype == 'class':
                        classes.add(xname)
                    else:
                        functions.add(xname)

        # Scan directory, read files
        files = set()
        classes = set()
        functions = set()
        for fname in os.listdir(path):
            fpath = os.path.join(path, fname)
            if not os.path.isfile(fpath):
                continue
            if fname[-4:] != '.rst':
                continue
            read_file(fpath, classes, functions)
            files.add(fpath)
        # Return results
        return files, classes, functions

    # Scan api/index files
    print('Reading doc files for api_index')
    docdir = os.path.join('docs', 'source', 'api_index')
    doc_files, doc_classes, doc_functions = scan_docs(docdir)
    print(
        'Found (' + str(len(doc_files)) + ') files, identified ('
        + str(len(doc_classes)) + ') classes and (' + str(len(doc_functions))
        + ') functions.')

    # Compare the results
    n = 0
    x = classes - doc_classes
    if x:
        n += len(x)
        printline()
        print('Found (' + str(len(x)) + ') classes not in doc index:')
        print('\n'.join('  ' + colored('warning', y) for y in sorted(x)))
    x = functions - doc_functions
    if x:
        n += len(x)
        printline()
        print('Found (' + str(len(x)) + ') functions not in doc index:')
        print('\n'.join('  ' + colored('warning', y) for y in sorted(x)))
    x = doc_classes - classes
    if x:
        n += len(x)
        printline()
        print('Found (' + str(len(x)) + ') indexed, unknown classes:')
        print('\n'.join('  ' + colored('warning', y) for y in sorted(x)))
    x = doc_functions - functions
    if x:
        n += len(x)
        printline()
        print('Found (' + str(len(x)) + ') indexed, unknown functions:')
        print('\n'.join('  ' + colored('warning', y) for y in sorted(x)))
    printline()
    print('Found total of (' + str(n) + ') mismatches.')

    return n == 0


def test_examples(args):
    """
    Tests the example notebooks.
    """
    books = test_examples_list('examples')
    print(books)

    print('Found ' + str(len(books)) + ' notebook(s).')
    test_examples_index('examples', books)
    test_examples_all('examples', books)


def test_examples_index(root, books):
    """ Check that every notebook is included in the index. """
    import os
    import sys

    print('Checking index...')

    # Index file is in ./examples/README.md
    index_file = os.path.join(root, 'README.md')
    with open(index_file, 'r') as f:
        index_contents = f.read()

    # Find which are not indexed
    not_indexed = [book for book in books if book not in index_contents]

    # Report any failures
    if len(not_indexed) > 0:
        print('FAIL: Unindexed notebooks')
        for book in sorted(not_indexed):
            print('  ' + str(book))
        sys.exit(1)
    else:
        print('ok: All (' + str(len(books)) + ') notebooks are indexed.')


def test_examples_list(root, recursive=True):
    """ Returns a list of all notebooks in a directory. """
    import os

    def scan(root, recursive, notebooks):
        for filename in os.listdir(root):
            path = os.path.join(root, filename)

            # Add notebook
            if os.path.splitext(path)[1] == '.ipynb':
                notebooks.append(path)

            # Recurse into subdirectories
            elif recursive and os.path.isdir(path):
                # Ignore hidden directories
                if filename[:1] == '.':
                    continue
                scan(path, recursive, notebooks)
        return notebooks

    notebooks = []
    scan(root, recursive, notebooks)
    notebooks = [os.path.relpath(book, root) for book in notebooks]

    return notebooks


def test_examples_single(root, path):
    """ Tests a notebook in a subprocess, exists if it doesn't finish. """
    import myokit
    import nbconvert
    import os
    import subprocess
    import sys

    b = myokit.tools.Benchmarker()
    print('Running ' + path + ' ... ', end='')
    sys.stdout.flush()

    # Load notebook, convert to python
    e = nbconvert.exporters.PythonExporter()
    code, _ = e.from_filename(os.path.join(root, path))

    # Remove coding statement, if present
    code = '\n'.join([x for x in code.splitlines() if x[:9] != '# coding'])

    # Tell matplotlib not to produce any figures
    env = os.environ.copy()
    env['MPLBACKEND'] = 'Template'

    # Run in subprocess
    cmd = [sys.executable, '-c', code]
    curdir = os.getcwd()
    try:
        os.chdir(root)
        p = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env
        )
        stdout, stderr = p.communicate()
        # TODO: Use p.communicate(timeout=3600) if Python3 only
        if p.returncode != 0:
            # Show failing code, output and errors before returning
            print('ERROR')
            print('-- script ' + '-' * (79 - 10))
            for i, line in enumerate(code.splitlines()):
                j = str(1 + i)
                print(j + ' ' * (5 - len(j)) + line)
            print('-- stdout ' + '-' * (79 - 10))
            print(stdout)
            print('-- stderr ' + '-' * (79 - 10))
            print(stderr)
            print('-' * 79)
            return False
    except KeyboardInterrupt:
        p.terminate()
        print('ABORTED')
        sys.exit(1)
    finally:
        os.chdir(curdir)

    # Successfully run
    print('ok (' + b.format(b.time()) + ')')
    return True


def test_examples_all(root, books):
    """ Runs all notebooks, and exits if one fails. """
    import sys

    # Ignore books with deliberate errors, but check they still exist
    ignore_list = [
    ]
    books = set(books) - set(ignore_list)

    # Scan and run
    print('Testing notebooks')
    failed = []
    for book in books:
        if not test_examples_single(root, book):
            failed.append(book)
    if failed:
        print('FAIL: Errors encountered in notebooks')
        for book in failed:
            print('  ' + str(book))
        sys.exit(1)
    else:
        print('ok: Successfully ran all (' + str(len(books)) + ') notebooks.')


def test_examples_pub(args):
    """
    Runs all publication examples, exits if one of them fails.
    """
    import os
    import sys
    import myokit

    # Get publications directory
    path = os.path.join(myokit.DIR_MYOKIT, 'tests', 'publications')

    # PBMB 2016. Myokit: A simple interface to cardiac cellular
    # electrophysiology
    if test_mmt_files(os.path.join(path, 'pbmb-2016')):
        sys.exit(1)


def test_examples_web(args):
    """
    Runs all web examples, exits if one of them fails.
    """
    import os
    import sys
    import myokit

    # Get web directory
    path = os.path.join(
        myokit.DIR_MYOKIT,
        '..',
        'dev',
        'web',
        'html',
        'static',
        'download',
        'examples',
    )
    if not os.path.isdir(path):
        print('Web examples not found. Skipping.')
        return

    # Run, exit on error
    if test_mmt_files(path):
        sys.exit(1)


def test_in_repo():
    """
    Returns ``True`` iff it thinks we're in the Myokit repo root directory.
    """
    import os
    return os.path.isfile(os.path.join('myokit', '_myokit_version.py'))


def test_mmt_files(path):
    """
    Run all the `mmt` files in a given directory `path`, returns 0 iff nothing
    goes wrong.
    """
    import fnmatch
    import gc
    import os
    import traceback

    import myokit

    # Get absolute path
    path = os.path.abspath(path)

    # Show what we're running
    print('Running mmt files for:')
    print('  ' + path)

    # Error state
    error = 0

    # Set working directory that that path
    wdir = os.getcwd()
    try:
        os.chdir(path)

        # Run all
        glob = '*.mmt'
        for fn in fnmatch.filter(os.listdir(path), glob):
            # Load and run
            try:
                print('Loading ' + fn)
                m, p, x = myokit.load(os.path.join(path, fn))
                try:
                    print('Running...')
                    myokit.run(m, p, x)
                except Exception:
                    error = 1
                    print(traceback.format_exc())
                del m, p, x
            except Exception:
                print('Unable to load.')
                print(traceback.format_exc())

            # Tidy up
            gc.collect()
            print('-' * 70)

            # Quit on error
            if error:
                break
    finally:
        os.chdir(wdir)

    # Return error status 0
    return error


def test_style(args):
    """
    Runs flake8 in a subprocess, exits if it doesn't finish.
    """
    print('Running flake8 ... ')

    import subprocess
    import sys

    sys.stdout.flush()
    p = subprocess.Popen(['flake8', '-j4'], stderr=subprocess.PIPE)
    try:
        ret = p.wait()
    except KeyboardInterrupt:
        try:
            p.terminate()
        except OSError:
            pass
        p.wait()
        print('')
        sys.exit(1)
    if ret == 0:
        print('ok')
    else:
        print('FAILED')
        sys.exit(ret)


def test_unit(args=None):
    """
    Runs unit tests, exits if anything fails.
    """
    import os
    import sys
    import unittest
    import warnings

    print('Running tests with ' + sys.executable)

    # Don't hide repeat warnings: This makes it possible to check that warnings
    # are being raised in a consistent manner.
    warnings.simplefilter('always')

    if test_in_repo():
        path = os.path.join('myokit', 'tests')
    else:
        import myokit
        path = os.path.join(myokit.DIR_MYOKIT, 'tests')

    suite = unittest.defaultTestLoader.discover(path, pattern='test*.py')
    res = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if res.wasSuccessful() else 1)


#
# Version
#

def version(raw=False):
    """ Show the version number. """
    import myokit
    print(myokit.version(raw))


def add_version_parser(subparsers):
    """
    Adds a subcommand parser for the ``version`` command.
    """
    parser = subparsers.add_parser(
        'version',
        description='Prints Myokit\'s version number.',
        help='Prints Myokit\'s version number.',
    )
    parser.add_argument(
        '--raw',
        action='store_true',
        help='Only print the version number, no other information.',
    )
    parser.set_defaults(func=version)


#
# Video
#

def video(src, key, dst, fps, grow, colormap):
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

    # Get multiplier
    grow = int(grow)
    if grow < 1:
        print('Grow must be integer greater than zero.')
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
        del reporter

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
    frames = data.colors(key, colormap=colormap, multiplier=grow)
    print('Compiling frames into video clip.')
    video = mpy.ImageSequenceClip(frames, fps=fps)
    rate = str(nx * ny * fps * 4)
    video.write_videofile(dst, fps=24, audio=False, codec=codec, bitrate=rate)


def add_video_parser(subparsers):
    """
    Adds a subcommand parser for the ``video`` command.
    """
    import myokit

    parser = subparsers.add_parser(
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
    parser.add_argument(
        'src',
        metavar='datablock.zip',
        help='The DataBlock file to convert',
    )
    parser.add_argument(
        'key',
        metavar='membrane.V',
        help='The 2d time series in the DataBlock to convert to video',
    )
    parser.add_argument(
        '-dst',
        metavar='movie.mp4',
        help='The video file to write',
        default='movie.mp4',
    )
    parser.add_argument(
        '-fps',
        metavar='fps',
        help='The number of (DataBlock) frames per second',
        default=16,
    )
    parser.add_argument(
        '-grow',
        metavar='grow',
        help='Set to larger than 1 to turn each cell into multiple pixels.',
        default=1,
    )
    parser.add_argument(
        '-colormap',
        metavar='colormap',
        help='The ColorMap to use when converting the DataBlock.',
        default='traditional',
        choices=myokit.ColorMap.names(),
    )
    parser.set_defaults(func=video)


if __name__ == '__main__':
    main()
