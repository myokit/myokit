#!/usr/bin/env python3
#
# Tests the command line tools in myokit.__main__.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import contextlib
import io
import os
import pathlib
import sys
import tempfile
import unittest
import unittest.mock
import warnings

import myokit
import myokit.__main__ as main
from myokit.tests import DIR_DATA, DIR_FORMATS, DIR_IO

# Commands available in the command line tool
COMMANDS = [
    'block', 'compare', 'compiler', 'debug', 'eval', 'export', 'icons',
    'ide', 'import', 'log', 'opencl', 'opencl-select', 'reset', 'run', 'step',
    'sundials', 'system', 'test', 'version', 'video',
]

# A model with a script that doesn't need compilation
SCRIPT_MMT = '''
[[model]]
c.x = 1

[engine]
time = 0 bind time

[c]
dot(x) = -x

[[protocol]]
1 10 1 0 0

[[script]]
print('Hello from the script')
'''


class MainTest(unittest.TestCase):
    """
    Tests the command line tools in ``myokit.__main__``.
    """

    def setUp(self):
        # Temporary directory for each test
        self._dir = tempfile.TemporaryDirectory()
        self.dir = pathlib.Path(self._dir.name)

    def tearDown(self):
        self._dir.cleanup()

    def call(self, function, *args, **kwargs):
        """
        Calls ``function(*args, **kwargs)`` and returns a tuple
        ``(exit_code, output)``, where ``exit_code`` is ``None`` if
        ``sys.exit`` was not called, and ``output`` is the text written to
        stdout and stderr.
        """
        out = io.StringIO()
        code = None
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            try:
                function(*args, **kwargs)
            except SystemExit as e:
                code = e.code
        return code, out.getvalue()

    def run_main(self, *args):
        """
        Runs ``main()`` with command line arguments ``args``, and returns a
        tuple ``(exit_code, output)``.
        """
        argv = ['myokit'] + [str(x) for x in args]
        with unittest.mock.patch.object(sys, 'argv', argv):
            return self.call(main.main)

    def write(self, name, text):
        """ Writes ``text`` to a file in the temporary directory. """
        path = self.dir / name
        path.write_text(text)
        return path

    def test_utilities(self):
        # Test printline and colored
        code, out = self.call(main.printline)
        self.assertEqual(out, '-' * 60 + '\n')
        self.assertEqual(main.colored('fail', 'x'), '\033[91mx\033[0m')
        self.assertEqual(main.colored('normal', 3), '\033[0m3\033[0m')
        self.assertRaises(KeyError, main.colored, 'pink', 'x')

    def test_main(self):
        # Test the main method and the help for each command

        # No arguments: show help
        code, out = self.run_main()
        self.assertIsNone(code)
        self.assertIn('Command line tools for myokit', out)
        for command in COMMANDS:
            self.assertIn(command, out)

        # Help for each command
        for command in COMMANDS:
            with self.subTest(command=command):
                code, out = self.run_main(command, '-h')
                self.assertEqual(code, 0)
                self.assertIn('usage', out)

        # Unknown command
        code, out = self.run_main('not-a-command')
        self.assertEqual(code, 2)
        self.assertIn('invalid choice', out)

        # Missing arguments
        code, out = self.run_main('eval')
        self.assertEqual(code, 2)
        self.assertIn('required', out)

    def test_read_mmt_and_model(self):
        # Test reading mmt files, with and without errors
        path = DIR_DATA / 'lr-1991.mmt'
        code, out = self.call(main.read_mmt, path)
        self.assertIsNone(code)
        self.assertIn('Reading mmt file', out)
        with contextlib.redirect_stdout(io.StringIO()):
            m, p, x = main.read_mmt(path)
            m2 = main.read_model(path)
        self.assertIsInstance(m, myokit.Model)
        self.assertIsInstance(p, myokit.Protocol)
        self.assertIsInstance(m2, myokit.Model)
        self.assertIsInstance(m, myokit.Model)

        # Silent reading
        code, out = self.call(main.read_model, path)
        self.assertIsNone(code)
        self.assertIn('Reading mmt file', out)
        code, out = self.call(main.read_model, path, silent=True)
        self.assertIsNone(code)
        self.assertEqual(out, '')

        # Parse errors
        bad = self.write('bad.mmt', '[[model]]\nc.x = 1\n[c]\ndot(x) = 1 +\n')
        code, out = self.call(main.read_mmt, bad)
        self.assertEqual(code, 1)
        self.assertIn('\033[91m', out)
        self.assertIn('line 4', out)
        code, out = self.call(main.read_model, bad)
        self.assertEqual(code, 1)
        self.assertIn('line 4', out)

        # No model section
        code, out = self.call(
            main.read_model, DIR_DATA / 'beeler-1977-protocol.mmt')
        self.assertEqual(code, 1)
        self.assertIn('Model section not found.', out)

        # Paths are expanded
        home = pathlib.Path('~').expanduser()
        try:
            rel = os.path.relpath(path, home)
        except ValueError:  # pragma: no cover
            rel = None  # Different drive on Windows
        if rel is not None:
            with contextlib.redirect_stdout(io.StringIO()):
                m = main.read_model(pathlib.Path('~', rel))
            self.assertIsInstance(m, myokit.Model)

    def test_qtforce(self):
        # Test forcing a Qt backend
        flags = (
            'FORCE_PYQT6', 'FORCE_PYQT5', 'FORCE_PYSIDE6', 'FORCE_PYSIDE2')
        old = {x: getattr(myokit, x) for x in flags}
        try:
            # Nothing selected: flags unchanged
            for x in flags:
                setattr(myokit, x, 'unchanged')
            main.qtforce()
            for x in flags:
                self.assertEqual(getattr(myokit, x), 'unchanged')

            # Select one: other flags are reset. Avoid importing myokit.gui
            gui = unittest.mock.MagicMock(backend='Fake')
            kwargs = ('pyqt6', 'pyqt5', 'pyside6', 'pyside2')
            with unittest.mock.patch.dict(sys.modules, {'myokit.gui': gui}):
                for i, kwarg in enumerate(kwargs):
                    with self.subTest(kwarg=kwarg):
                        code, out = self.call(main.qtforce, **{kwarg: True})
                        self.assertIn('Using backend: ', out)
                        for j, x in enumerate(flags):
                            self.assertEqual(getattr(myokit, x), i == j)
        finally:
            for x, v in old.items():
                setattr(myokit, x, v)

    def test_gui_commands(self):
        # Test launching the IDE, DataBlock viewer, and DataLog viewer
        from myokit.tests import qt_application
        qt_application()
        import myokit.gui
        import myokit.gui.datablock_viewer
        import myokit.gui.datalog_viewer
        import myokit.gui.ide

        with unittest.mock.patch('myokit.gui.run') as run:
            # IDE
            code, out = self.run_main('ide')
            run.assert_called_once_with(myokit.gui.ide.MyokitIDE, None)
            run.reset_mock()
            code, out = self.run_main('ide', '~/model.mmt')
            run.assert_called_once_with(
                myokit.gui.ide.MyokitIDE,
                pathlib.Path('~/model.mmt').expanduser())
            run.reset_mock()

            # DataBlock viewer
            code, out = self.run_main('block')
            run.assert_called_once_with(
                myokit.gui.datablock_viewer.DataBlockViewer, None)
            run.reset_mock()
            code, out = self.run_main('block', '~/block.zip')
            run.assert_called_once_with(
                myokit.gui.datablock_viewer.DataBlockViewer,
                pathlib.Path('~/block.zip').expanduser())
            run.reset_mock()

            # DataLog viewer, with zero or more files
            code, out = self.run_main('log')
            run.assert_called_once_with(
                myokit.gui.datalog_viewer.DataLogViewer)
            run.reset_mock()
            code, out = self.run_main('log', 'a.csv', '~/b.zip')
            run.assert_called_once_with(
                myokit.gui.datalog_viewer.DataLogViewer,
                pathlib.Path('a.csv'),
                pathlib.Path('~/b.zip').expanduser())

    def test_compare(self):
        # Test comparing two models
        code, out = self.run_main(
            'compare',
            DIR_DATA / 'beeler-1977-model-compare-a.mmt',
            DIR_DATA / 'beeler-1977-model-compare-b.mmt')
        self.assertIsNone(code)
        self.assertIn('Comparing:', out)
        self.assertIn('[1] beeler-1977', out)
        self.assertIn('[2] beeler-1977-with-differences', out)
        self.assertIn('Mismatched', out)

        # Invalid file
        code, out = self.run_main(
            'compare', DIR_DATA / 'beeler-1977-model-compare-a.mmt',
            DIR_DATA / 'beeler-1977-protocol.mmt')
        self.assertEqual(code, 1)
        self.assertIn('Model section not found', out)

    def test_compiler(self):
        # Test the compiler command
        with unittest.mock.patch(
                'myokit.Compiler.info', return_value='gcc 1.2.3') as info:
            code, out = self.run_main('compiler')
            info.assert_called_once_with(False)
        self.assertIn('Compilation successful. Found: gcc 1.2.3', out)

        with unittest.mock.patch(
                'myokit.Compiler.info', return_value=None) as info:
            code, out = self.run_main('compiler', '--debug')
            info.assert_called_once_with(True)
        self.assertIn('Compilation with distutils/setuptools failed.', out)

    def test_debug(self):
        # Test the debug command
        path = DIR_DATA / 'lr-1991.mmt'
        m = myokit.load_model(path)
        code, out = self.run_main('debug', path, 'ina.INa')
        self.assertIsNone(code)
        self.assertIn(m.show_evaluation_of('ina.INa'), out)

        code, out = self.run_main('debug', path, 'ina.INa', '--deps')
        self.assertIsNone(code)
        self.assertIn(m.show_expressions_for('ina.INa'), out)

        # Unknown variable: a guess is made
        code, out = self.run_main('debug', path, 'ina.Fake')
        self.assertIsNone(code)
        self.assertIn('Variable not found, assuming', out)

    def test_eval(self):
        # Test the eval command
        code, out = self.run_main('eval', '1 + 2 * 3')
        self.assertIsNone(code)
        self.assertEqual(out, '1 + 2 * 3 = 7.0\n')

        code, out = self.run_main('eval', '1 [mV] + 2 [mV]')
        self.assertEqual(out, '1 [mV] + 2 [mV] = 3.0\n')

        # Non-literal expressions are not evaluated
        code, out = self.run_main('eval', 'x + 1')
        self.assertIsNone(code)
        self.assertIn('Unable to evaluate x + 1', out)
        self.assertNotIn('str:', out)

        # Parse errors are shown
        code, out = self.run_main('eval', '1 +')
        self.assertIsNone(code)
        self.assertIn('Syntax error', out)

    def test_export(self):
        # Test exporting models and runnables
        path = DIR_DATA / 'lr-1991.mmt'

        # Model export
        target = self.dir / 'model.cellml'
        code, out = self.run_main('export', 'cellml', path, target)
        self.assertIsNone(code)
        self.assertIn('Exporting model', out)
        self.assertIn('Export successful', out)
        self.assertTrue(target.is_file())
        m = myokit.formats.importer('cellml').model(target)
        self.assertEqual(m.count_states(), 8)

        # Runnable export, with protocol
        target = self.dir / 'ansic'
        code, out = self.run_main('export', 'ansic', path, target)
        self.assertIsNone(code)
        self.assertIn('Exporting runnable', out)
        self.assertIn('Using embedded protocol.', out)
        self.assertTrue((target / 'sim.c').is_file())

        # Runnable export, without protocol
        target = self.dir / 'ansic2'
        code, out = self.run_main(
            'export', 'ansic', DIR_DATA / 'beeler-1977-model.mmt', target)
        self.assertIsNone(code)
        self.assertIn('No protocol found.', out)
        self.assertTrue((target / 'sim.c').is_file())

        # No model
        code, out = self.run_main(
            'export', 'cellml', DIR_DATA / 'beeler-1977-protocol.mmt',
            self.dir / 'x.cellml')
        self.assertEqual(code, 1)
        self.assertIn('File must contain model definition.', out)

        # Unknown exporter
        code, out = self.run_main('export', 'fake', path, self.dir / 'x')
        self.assertEqual(code, 2)
        self.assertIn('invalid choice', out)

        # Warnings and post-export info are shown
        exporter = unittest.mock.MagicMock()
        exporter.supports_model.return_value = True
        exporter.model.side_effect = lambda *a: warnings.warn('Be careful')
        exporter.post_export_info.return_value = 'Some info'
        with unittest.mock.patch(
                'myokit.formats.exporter', return_value=exporter):
            code, out = self.call(
                main.mmt_export, 'cellml', path, self.dir / 'y')
        self.assertIn('Warning: \033[0mBe careful', out)
        self.assertIn('Some info', out)
        exporter.model.assert_called_once()

    def test_import(self):
        # Test importing models
        path = DIR_FORMATS / 'cellml' / 'br-1977.cellml'

        # Write to screen
        code, out = self.run_main('import', 'cellml', path)
        self.assertIsNone(code)
        self.assertIn('CellMLImporter', out)
        self.assertIn('[[model]]', out)
        self.assertIn('[[protocol]]', out)
        self.assertIn('[[script]]', out)

        # Write to file
        target = self.dir / 'br.mmt'
        code, out = self.run_main('import', 'cellml', path, target)
        self.assertIsNone(code)
        self.assertIn(f'Saving output to {target}', out)
        self.assertIn('Done.', out)
        m, p, x = myokit.load(target)
        self.assertEqual(m.count_states(), 8)
        self.assertIsNotNone(p)
        self.assertIsNotNone(x)

        # Embedded protocol is extracted
        model = myokit.parse_model('''
            [[model]]
            c.x = 0
            [engine]
            time = 0 bind time
            pace = 0 bind pace
            [c]
            dot(x) = if(engine.time >= 10 and engine.time < 11, 1, 0)
        ''')
        importer = unittest.mock.MagicMock()

        def model_with_warning(path):
            warnings.warn('Importing with care')
            return model

        importer.model.side_effect = model_with_warning
        with unittest.mock.patch(
                'myokit.formats.importer', return_value=importer):
            code, out = self.call(main.mmt_import, 'cellml', 'model.xyz')
        self.assertIn('Warning: \033[0mImporting with care', out)
        self.assertIn('[[protocol]]', out)

        # Unknown importer
        code, out = self.run_main('import', 'fake', path)
        self.assertEqual(code, 2)

    def test_icons(self):
        # Test the icons command on different platforms

        def run(plat, answer=''):
            with unittest.mock.patch('platform.system', return_value=plat), \
                    unittest.mock.patch(
                        'builtins.input', return_value=answer), \
                    unittest.mock.patch.object(
                        main, 'install_gnome_kde') as lin, \
                    unittest.mock.patch.object(
                        main, 'install_windows') as win:
                code, out = self.run_main('icons')
            return out, lin.call_count, win.call_count

        self.assertEqual(run('Linux', 'n'), ('Aborted\n', 0, 0))
        self.assertEqual(run('Linux', ''), ('Aborted\n', 0, 0))
        self.assertEqual(run('Linux', ' Yes '), ('', 1, 0))
        self.assertEqual(run('Windows', 'no'), ('Aborted\n', 0, 0))
        self.assertEqual(run('Windows', 'y'), ('', 0, 1))
        out, lin, win = run('Darwin')
        self.assertIn('not available', out)
        self.assertEqual((lin, win), (0, 0))
        out, lin, win = run('Plan9')
        self.assertIn('Unknown platform: Plan9', out)
        self.assertEqual((lin, win), (0, 0))

    def test_install_gnome_kde(self):
        # Test installing icons on Linux, in a temporary home directory
        home = self.dir
        with unittest.mock.patch('pathlib.Path.home', return_value=home), \
                unittest.mock.patch('subprocess.call') as call:
            code, out = self.call(main.install_gnome_kde)
        self.assertIsNone(code)
        self.assertIn('Done', out)

        # Desktop files were created from templates
        apps = home / '.local' / 'share' / 'applications'
        for name in ('myokit-ide.desktop', 'myokit-datalog-viewer.desktop',
                     'myokit-datablock-viewer.desktop'):
            path = apps / name
            self.assertTrue(path.is_file(), name)
            text = path.read_text()
            self.assertIn(sys.executable, text)
            self.assertIn(str(myokit.DIR_DATA / 'gui'), text)
            self.assertNotIn('<?', text)

        # Mime types were copied
        mime = home / '.local' / 'share' / 'mime'
        for name in ('x-myokit.xml', 'x-cellml.xml', 'x-abf.xml',
                     'x-wcp.xml'):
            self.assertEqual(
                (mime / 'packages' / name).read_text(),
                (myokit.DIR_DATA / 'install-lin' / name).read_text())

        # Mime database was updated
        call.assert_called_once_with(['update-mime-database', mime])

        # Installing again works (directories exist)
        with unittest.mock.patch('pathlib.Path.home', return_value=home), \
                unittest.mock.patch('subprocess.call'):
            code, out = self.call(main.install_gnome_kde)
        self.assertIsNone(code)
        self.assertNotIn('Creating directory structure', out)

        # Output path exists, but is a file
        home2 = self.dir / 'home2'
        (home2 / '.local' / 'share').mkdir(parents=True)
        (home2 / '.local' / 'share' / 'applications').write_text('x')
        with unittest.mock.patch('pathlib.Path.home', return_value=home2), \
                unittest.mock.patch('subprocess.call') as call:
            code, out = self.call(main.install_gnome_kde)
        self.assertEqual(code, 1)
        self.assertIn('Cannot create output directory', out)
        call.assert_not_called()

        # Template file not found
        with unittest.mock.patch('pathlib.Path.home', return_value=home), \
                unittest.mock.patch('subprocess.call'), \
                unittest.mock.patch.object(
                    myokit, 'DIR_DATA', self.dir / 'nothing'):
            code, out = self.call(main.install_gnome_kde)
        self.assertEqual(code, 1)
        self.assertIn('Error: file not found', out)

    def test_install_windows(self):
        # Test installing icons on Windows

        # Install with a mock menuinst module
        menuinst = unittest.mock.MagicMock()
        icons = str(myokit.DIR_DATA / 'gui').replace('\\', '/')

        def install(path):
            # Check the processed template before it is deleted
            with open(path, 'r') as f:
                install.text = f.read()

        menuinst.install.side_effect = install
        with unittest.mock.patch('platform.system', return_value='Windows'), \
                unittest.mock.patch.dict(sys.modules, menuinst=menuinst):
            code, out = self.call(main.install_windows)
        self.assertIsNone(code)
        self.assertIn('Done', out)
        menuinst.install.assert_called_once()
        self.assertIn(f'"{icons}/icon-ide.ico"', install.text)
        self.assertNotIn('<?', install.text)

        # Not on windows
        with unittest.mock.patch('platform.system', return_value='Linux'):
            self.assertRaisesRegex(
                Exception, 'Not a windows', main.install_windows)

    def test_opencl(self):
        # Test the opencl command
        with unittest.mock.patch(
                'myokit.OpenCL.info', return_value='OpenCL info') as info:
            code, out = self.run_main('opencl')
        info.assert_called_once_with(formatted=True)
        self.assertEqual(out, 'OpenCL info\n')

    def test_opencl_select(self):
        # Test selecting an OpenCL device

        def run(devices, answers, old=(None, None)):
            if not isinstance(answers, list):
                answers = [answers]
            with unittest.mock.patch(
                    'myokit.OpenCL.selection_info', return_value=devices), \
                    unittest.mock.patch(
                        'myokit.OpenCL.load_selection', return_value=old), \
                    unittest.mock.patch(
                        'myokit.OpenCL.save_selection') as save, \
                    unittest.mock.patch(
                        'builtins.input', side_effect=answers):
                code, out = self.run_main('opencl-select')
            return code, out, save

        dev1 = ('Plat 1', 'Dev 1', 'Specs 1')
        dev2 = ('Plat 2', 'Dev 2', 'Specs 2')

        # No devices
        code, out, save = run([], [])
        self.assertEqual(code, 1)
        self.assertIn('No OpenCL devices found!', out)
        save.assert_not_called()

        # Keep current selection
        code, out, save = run([dev1], '', ('Plat 1', None))
        self.assertIsNone(code)
        self.assertIn('typing 1 or 2.', out)
        self.assertIn('Selected platform: Plat 1', out)
        self.assertIn('Selected device  : No preference', out)
        self.assertIn('(2) Platform: Plat 1', out)
        self.assertIn('Device: Dev 1', out)
        self.assertIn('Specs 1', out)
        self.assertIn('Selection unchanged.', out)
        save.assert_not_called()

        # Select a device, after some invalid input
        code, out, save = run([dev1, dev2], ['x', '0', '4', ' 3 '])
        self.assertIsNone(code)
        self.assertIn('typing 1,2 or 3.', out)
        self.assertEqual(out.count('Invalid selection, please retry'), 3)
        self.assertIn('Selection updated.', out)
        save.assert_called_once_with('Plat 2', 'Dev 2')

        # Select automatic
        code, out, save = run([dev1, dev2], '1', ('Plat 2', 'Dev 2'))
        save.assert_called_once_with(None, None)

        # Many devices
        code, out, save = run([dev1] * 6, '7')
        self.assertIn('typing one of 1,2,3,...,7.', out)
        save.assert_called_once_with('Plat 1', 'Dev 1')

        # Abort with Ctrl-C
        code, out, save = run([dev1], KeyboardInterrupt())
        self.assertEqual(code, 0)
        self.assertIn('OpenCL device selection aborted.', out)
        save.assert_not_called()

    def test_reset(self):
        # Test removing the settings files, in a temporary directory
        user = self.dir / 'user'

        def make():
            user.mkdir(exist_ok=True)
            (user / 'myokit.ini').write_text('[x]\n')

        with unittest.mock.patch.object(myokit, 'DIR_USER', user):
            # Abort
            make()
            with unittest.mock.patch('builtins.input', return_value='n'):
                code, out = self.run_main('reset')
            self.assertEqual(code, 1)
            self.assertIn('Aborting.', out)
            self.assertTrue(user.is_dir())

            # Confirm
            with unittest.mock.patch('builtins.input', return_value='Y'):
                code, out = self.run_main('reset')
            self.assertIsNone(code)
            self.assertIn(str(user), out)
            self.assertIn('Done', out)
            self.assertFalse(user.exists())

            # Force
            make()
            with unittest.mock.patch('builtins.input') as inp:
                code, out = self.run_main('reset', '--force')
            inp.assert_not_called()
            self.assertIn('Done', out)
            self.assertFalse(user.exists())

    def test_run(self):
        # Test running an embedded script
        path = self.write('script.mmt', SCRIPT_MMT)
        code, out = self.run_main('run', path)
        self.assertIsNone(code)
        self.assertIn('File loaded in', out)
        self.assertIn("  1 print('Hello from the script')", out)
        self.assertIn('Hello from the script\nDone', out)

        # No script
        code, out = self.run_main('run', DIR_DATA / 'beeler-1977-model.mmt')
        self.assertEqual(code, 1)
        self.assertIn('No embedded script found.', out)

        # Parse error
        bad = self.write('bad.mmt', '[[model]]\nc.x = 1\n[c]\ndot(x) = 1 +\n')
        code, out = self.run_main('run', bad)
        self.assertEqual(code, 1)

        # Debug flags are set (and can't be unset)
        flags = ('sg', 'wg', 'sc', 'sm', 'sp', 'ss')
        old = {x: getattr(myokit, f'DEBUG_{x.upper()}') for x in flags}
        try:
            for x in flags:
                setattr(myokit, f'DEBUG_{x.upper()}', False)
            with unittest.mock.patch('myokit.run') as run:
                code, out = self.run_main(
                    'run', path, '--debug-sc', '--debug-ss')
            run.assert_called_once()
            for x in flags:
                self.assertEqual(
                    getattr(myokit, f'DEBUG_{x.upper()}'), x in ('sc', 'ss'))

            with unittest.mock.patch('myokit.run'):
                code, out = self.run_main('run', path)
            self.assertTrue(myokit.DEBUG_SC)
        finally:
            for x, v in old.items():
                setattr(myokit, f'DEBUG_{x.upper()}', v)

    def test_step(self):
        # Test evaluating derivatives
        path = DIR_DATA / 'lr-1991.mmt'
        model = myokit.load_model(path)
        derivs = model.evaluate_derivatives()

        # Formatted
        code, out = self.run_main('step', path)
        self.assertIsNone(code)
        self.assertIn('Evaluating state vector derivatives...', out)
        self.assertIn('membrane.V', out)
        self.assertIn(myokit.float.str(derivs[0]), out)

        # Raw
        code, out = self.run_main('step', path, '--raw')
        self.assertIsNone(code)
        lines = out.splitlines()
        self.assertEqual(lines, [myokit.float.str(x) for x in derivs])

        # Initial values
        state = [x * 1.01 for x in model.initial_values(as_floats=True)]
        ini = self.dir / 'ini.txt'
        myokit.save_state(ini, state)
        code, out = self.run_main('step', path, '-ini', ini, '--raw')
        self.assertEqual(out.splitlines(), [
            myokit.float.str(x)
            for x in model.evaluate_derivatives(state=state)])
        code, out = self.run_main('step', path, '-ini', ini)
        self.assertIn('Initial value file read successfully.', out)

        # Reference list of derivatives
        ref = self.dir / 'ref.txt'
        myokit.save_state(ref, derivs)
        code, out = self.run_main('step', path, '-ref', ref)
        self.assertIn('as list of derivatives', out)
        self.assertIn('Model check completed without errors.', out)

        # Reference is ignored with --raw
        code, out = self.run_main('step', path, '-ref', ref, '--raw')
        self.assertIsNone(code)
        self.assertEqual(
            out.splitlines(), [myokit.float.str(x) for x in derivs])

        # Reference model
        code, out = self.run_main('step', path, '-ref', path)
        self.assertIn('as mmt model', out)
        self.assertIn('Model check completed without errors.', out)

        # Reference with differences
        ref2 = self.dir / 'ref2.txt'
        myokit.save_state(ref2, [x * 2 + 1 for x in derivs])
        code, out = self.run_main('step', path, '-ref', ref2)
        self.assertIn('Found (8) large mismatches', out)

        # Numerical error
        bad = self.write('bad.mmt', '''
            [[model]]
            c.x = 1
            [engine]
            time = 0 bind time
            [c]
            dot(x) = sqrt(-x)
        ''')
        code, out = self.run_main('step', bad)
        self.assertEqual(code, 1)
        self.assertIn(' Numerical error ', out)
        self.assertIn('A numerical error occurred:', out)
        self.assertIn('sqrt', out)

    def test_sundials(self):
        # Test the sundials command
        with unittest.mock.patch(
                'myokit.Sundials.version', return_value='1.2.3'):
            code, out = self.run_main('sundials')
        self.assertEqual(out, 'Found Sundials version 1.2.3\n')
        with unittest.mock.patch(
                'myokit.Sundials.version', return_value=None):
            code, out = self.run_main('sundials')
        self.assertEqual(out, 'Sundials not found or compilation failed.\n')

    def test_system(self):
        # Test the system command, with a temporary settings file
        user = self.dir
        (user / 'myokit.ini').write_text('[some]\nsetting = value\n')
        with unittest.mock.patch.object(myokit, 'DIR_USER', user), \
                unittest.mock.patch('myokit.system') as system:
            code, out = self.run_main('system')
        system.assert_called_once_with(live_printing=True)
        self.assertIn(f'= {user / "myokit.ini"} =', out)
        self.assertIn('setting = value', out)

    def test_version(self):
        # Test the version command
        code, out = self.run_main('version')
        self.assertEqual(out, myokit.version() + '\n')
        code, out = self.run_main('version', '--raw')
        self.assertEqual(out, myokit.__version__ + '\n')

    def test_video(self):
        # Test the video command, with a mock moviepy module
        src = DIR_IO / 'block2d.zip'

        # No moviepy
        with unittest.mock.patch.dict(sys.modules, {'moviepy': None}):
            code, out = self.run_main('video', src, 'membrane.V')
        self.assertEqual(code, 1)
        self.assertIn('requires MoviePy', out)

        moviepy = unittest.mock.MagicMock()
        with unittest.mock.patch.dict(sys.modules, {'moviepy': moviepy}):

            # Unknown extension
            code, out = self.run_main(
                'video', src, 'membrane.V', '-dst', self.dir / 'x.mov')
            self.assertEqual(code, 1)
            self.assertIn('Unable to determine codec from extension ".mov"',
                          out)
            self.assertIn('  .mp4', out)

            # Invalid frame rate and growth factor
            dst = self.dir / 'movie.webm'
            code, out = self.run_main(
                'video', src, 'membrane.V', '-dst', dst, '-fps', 0)
            self.assertEqual(code, 1)
            self.assertIn('Frame rate must be', out)
            code, out = self.run_main(
                'video', src, 'membrane.V', '-dst', dst, '-grow', 0)
            self.assertEqual(code, 1)
            self.assertIn('Grow must be', out)

            # Invalid colormap
            code, out = self.run_main(
                'video', src, 'membrane.V', '-colormap', 'fake')
            self.assertEqual(code, 2)

            # Unreadable file
            code, out = self.run_main(
                'video', DIR_IO / 'bad2d-4-not-a-zip.zip', 'membrane.V',
                '-dst', dst)
            self.assertEqual(code, 1)
            self.assertIn('DataBlock reading failed', out)

            # Unknown key
            code, out = self.run_main('video', src, 'fake.V', '-dst', dst)
            self.assertEqual(code, 1)
            self.assertIn('Key not found in DataBlock: "fake.V".', out)

            # Empty block
            empty = myokit.DataBlock2d(2, 2, [0, 1])
            empty.set0d('engine.time', [0, 1])
            empty_path = self.dir / 'empty.zip'
            empty.save(empty_path)
            code, out = self.run_main(
                'video', empty_path, 'membrane.V', '-dst', dst)
            self.assertEqual(code, 1)
            self.assertIn('Empty DataBlock loaded!', out)

            # Success
            moviepy.reset_mock()
            code, out = self.run_main(
                'video', src, 'membrane.V', '-dst', dst, '-fps', 10,
                '-grow', 2, '-colormap', 'red')
            self.assertIsNone(code)
            self.assertIn('Loading file: 0%', out)
            self.assertIn('100%', out)
            self.assertIn('nx = 16', out)
            self.assertIn('ny = 16', out)
            self.assertIn('nt = 500', out)

            # Frames passed to moviepy
            moviepy.ImageSequenceClip.assert_called_once()
            args, kwargs = moviepy.ImageSequenceClip.call_args
            frames = args[0]
            self.assertEqual(len(frames), 500)
            self.assertEqual(frames[0].shape, (32, 32, 3))
            self.assertEqual(kwargs, {'fps': 10})

            # Video written
            clip = moviepy.ImageSequenceClip.return_value
            clip.write_videofile.assert_called_once_with(
                dst, fps=24, audio=False, codec='libvpx',
                bitrate=str(16 * 16 * 10 * 4))

    def test_test_parser(self):
        # Test the test command and its subcommands, without running tests

        # In repository: show help or run selected test function
        names = ('coverage', 'doc', 'style', 'unit', 'web')
        funcs = ('test_coverage', 'test_documentation', 'test_style',
                 'test_unit', 'test_examples_web')
        mocks = {x: unittest.mock.MagicMock() for x in funcs}
        with unittest.mock.patch.object(main, 'test_in_repo',
                                        return_value=True), \
                unittest.mock.patch.multiple(main, **mocks):
            code, out = self.run_main('test')
            self.assertIsNone(code)
            self.assertIn('usage', out)
            for name, func in zip(names, funcs):
                code, out = self.run_main('test', name)
                mocks[func].assert_called_once_with({})

            # Disable matplotlib output
            with unittest.mock.patch('matplotlib.use') as use:
                code, out = self.run_main('test', '--nompl', 'unit')
            use.assert_called_once_with('template')
            self.assertIn('Disabling matplotlib output', out)

        # Not in repository: run unit tests
        with unittest.mock.patch.object(main, 'test_in_repo',
                                        return_value=False), \
                unittest.mock.patch.object(main, 'test_unit') as unit:
            code, out = self.run_main('test')
        unit.assert_called_once_with()

        # Detecting the repository
        cwd = os.getcwd()
        try:
            os.chdir(self.dir)
            self.assertFalse(main.test_in_repo())
            (self.dir / 'myokit').mkdir()
            (self.dir / 'myokit' / '__init__.py').write_text('')
            self.assertTrue(main.test_in_repo())
        finally:
            os.chdir(cwd)

    def test_test_unit(self):
        # Test running the unit tests, with mock test discovery and runner
        for success in (True, False):
            with unittest.mock.patch('unittest.defaultTestLoader.discover') \
                    as discover, \
                    unittest.mock.patch('unittest.TextTestRunner') as runner, \
                    unittest.mock.patch('warnings.simplefilter') as sf:
                runner.return_value.run.return_value.wasSuccessful.\
                    return_value = success
                for in_repo in (True, False):
                    with unittest.mock.patch.object(
                            main, 'test_in_repo', return_value=in_repo):
                        code, out = self.call(main.test_unit)
                    self.assertEqual(code, 0 if success else 1)
                    self.assertIn(sys.executable, out)
                    path = discover.call_args[0][0]
                    if in_repo:
                        self.assertEqual(path, pathlib.Path('myokit', 'tests'))
                    else:
                        self.assertEqual(path, myokit.DIR_MYOKIT / 'tests')
                sf.assert_called_with('always')

    def test_test_style(self):
        # Test running the style tests, with a mock subprocess
        for ret in (0, 1):
            with unittest.mock.patch('subprocess.Popen') as popen:
                popen.return_value.wait.return_value = ret
                code, out = self.call(main.test_style, {})
            self.assertEqual(code, ret)
            self.assertIn('Running ruff', out)
            self.assertEqual(
                popen.call_args[0][0], [sys.executable, '-m', 'ruff', 'check'])

    def test_test_coverage(self):
        # Test running the coverage tests, with a mock subprocess, in a
        # temporary directory (as the .coverage file is deleted)
        cwd = os.getcwd()
        try:
            os.chdir(self.dir)

            # Success
            coverage = self.dir / '.coverage'
            coverage.write_text('x')
            with unittest.mock.patch('subprocess.Popen') as popen:
                popen.return_value.wait.return_value = 0
                code, out = self.call(main.test_coverage, {})
            self.assertIsNone(code)
            self.assertIn('Generating coverage report.', out)
            self.assertEqual(popen.call_count, 2)
            self.assertIn('run', popen.call_args_list[0][0][0])
            self.assertIn('report', popen.call_args_list[1][0][0])
            self.assertFalse(coverage.exists())

            # Failure
            coverage.write_text('x')
            with unittest.mock.patch('subprocess.Popen') as popen:
                popen.return_value.wait.return_value = 3
                code, out = self.call(main.test_coverage, {})
            self.assertEqual(code, 3)
            self.assertIn('FAILED', out)
            self.assertEqual(popen.call_count, 1)
            self.assertFalse(coverage.exists())

            # Interrupted
            with unittest.mock.patch('subprocess.Popen') as popen:
                popen.return_value.wait.side_effect = [KeyboardInterrupt, 0]
                popen.return_value.terminate.side_effect = OSError
                code, out = self.call(main.test_coverage, {})
            self.assertEqual(code, 1)
        finally:
            os.chdir(cwd)

    def test_test_documentation(self):
        # Test the documentation tests, with mock checks and subprocess
        objects = (set(), {'myokit.A'}, {'myokit.f'})
        with unittest.mock.patch.object(
                main, 'test_doc_coverage_get_objects', return_value=objects), \
                unittest.mock.patch.object(
                    main, 'test_doc_coverage_index', return_value=True) as i, \
                unittest.mock.patch.object(
                    main, 'test_doc_coverage', return_value=True) as c, \
                unittest.mock.patch('subprocess.Popen') as popen:

            # All okay
            popen.return_value.wait.return_value = 0
            code, out = self.call(main.test_documentation, {})
            self.assertIsNone(code)
            i.assert_called_once_with(*objects)
            c.assert_called_once_with(objects[1], objects[2])
            self.assertEqual(popen.call_args[0][0][0], 'sphinx-build')

            # Sphinx fails
            popen.return_value.wait.return_value = 2
            code, out = self.call(main.test_documentation, {})
            self.assertEqual(code, 2)
            self.assertIn('FAILED', out)

            # Interrupted
            popen.return_value.wait.side_effect = [KeyboardInterrupt, 0]
            code, out = self.call(main.test_documentation, {})
            self.assertEqual(code, 1)
            popen.return_value.terminate.assert_called_once()

            # Coverage check fails: sphinx is not called
            popen.reset_mock()
            c.return_value = False
            code, out = self.call(main.test_documentation, {})
            self.assertEqual(code, 1)
            popen.assert_not_called()

    def test_doc_coverage_checks(self):
        # Test the doc coverage checks on a fake docs directory
        source = self.dir / 'docs' / 'source'
        index = source / 'api_index'
        index.mkdir(parents=True)
        (source / 'a.rst').write_text(
            '.. currentmodule:: myokit\n'
            '.. autoclass:: Model\n'
            '.. autofunction:: load\n'
            '.. module:: myokit.lib\n'
            '.. autoclass:: Extra\n')
        (source / 'b.txt').write_text('.. autoclass:: Ignored\n')
        (index / 'index.rst').write_text(
            ':class:`myokit.Model` :meth:`myokit.load`\n'
            ':class:`myokit.Unknown`\n')

        cwd = os.getcwd()
        try:
            os.chdir(self.dir)

            # Everything documented
            code, out = self.call(
                main.test_doc_coverage,
                {'myokit.Model', 'myokit.lib.Extra'}, {'myokit.load'})
            self.assertIn('Found total of (0) mismatches.', out)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertTrue(main.test_doc_coverage(
                    {'myokit.Model', 'myokit.lib.Extra'}, {'myokit.load'}))

            # Mismatches
            with contextlib.redirect_stdout(io.StringIO()) as out:
                ok = main.test_doc_coverage(
                    {'myokit.Model', 'myokit.New'}, {'myokit.save'})
            out = out.getvalue()
            self.assertFalse(ok)
            self.assertIn('Found (1) classes without documentation', out)
            self.assertIn('myokit.New', out)
            self.assertIn('Found (1) functions without documentation', out)
            self.assertIn('myokit.save', out)
            self.assertIn('Found (1) documented but unknown classes', out)
            self.assertIn('myokit.lib.Extra', out)
            self.assertIn('Found (1) documented but unknown functions', out)
            self.assertIn('myokit.load', out)
            self.assertIn('Found total of (4) mismatches.', out)

            # Index: everything listed
            with contextlib.redirect_stdout(io.StringIO()) as out:
                ok = main.test_doc_coverage_index(
                    set(), {'myokit.Model', 'myokit.Unknown'},
                    {'myokit.load'})
            self.assertTrue(ok)
            self.assertIn('Found (1) files', out.getvalue())

            # Index: mismatches
            with contextlib.redirect_stdout(io.StringIO()) as out:
                ok = main.test_doc_coverage_index(
                    set(), {'myokit.Model', 'myokit.New'}, {'myokit.save'})
            out = out.getvalue()
            self.assertFalse(ok)
            self.assertIn('Found (1) classes not in doc index', out)
            self.assertIn('Found (1) functions not in doc index', out)
            self.assertIn('Found (1) indexed, unknown classes', out)
            self.assertIn('Found (1) indexed, unknown functions', out)
            self.assertIn('Found total of (4) mismatches.', out)
        finally:
            os.chdir(cwd)

    def test_doc_coverage_get_objects(self):
        # Test scanning Myokit for modules, classes, and functions
        root = myokit.DIR_MYOKIT.parent
        if not (root / 'myokit' / '__init__.py').is_file():  # pragma: no cover
            self.skipTest('Not running from repository.')

        # Importing myokit.gui requires Qt
        from myokit.tests import qt_application
        qt_application()

        import matplotlib
        backend = matplotlib.get_backend()
        cwd = os.getcwd()
        try:
            os.chdir(root)
            with contextlib.redirect_stdout(io.StringIO()) as out:
                modules, classes, functions = \
                    main.test_doc_coverage_get_objects()
        finally:
            os.chdir(cwd)
            matplotlib.use(backend)

        self.assertIn('Scanning Myokit modules', out.getvalue())
        self.assertIn('myokit.lib', modules)
        self.assertIn('myokit.formats.cellml', modules)
        # Tests are not scanned, even if imported
        self.assertNotIn('myokit.tests', modules)
        for name in modules | classes | functions:
            self.assertFalse(name.startswith('myokit.tests'), name)
        self.assertIn('myokit.Model', classes)
        self.assertIn('myokit.load', functions)
        for name in classes | functions:
            self.assertNotIn('._', name)

    def test_examples_web(self):
        # Test running the web examples, in a fake directory structure
        fake = self.dir / 'repo' / 'myokit'
        fake.mkdir(parents=True)
        examples = (self.dir / 'repo' / 'dev' / 'web' / 'html' / 'static'
                    / 'download' / 'examples')

        with unittest.mock.patch.object(myokit, 'DIR_MYOKIT', fake):
            # No examples
            code, out = self.call(main.test_examples_web, {})
            self.assertIsNone(code)
            self.assertIn('Skipping.', out)

            # Working examples
            examples.mkdir(parents=True)
            (examples / 'a.mmt').write_text(SCRIPT_MMT)
            code, out = self.call(main.test_examples_web, {})
            self.assertIsNone(code)
            self.assertIn('Hello from the script', out)

            # Failing example
            (examples / 'b.mmt').write_text(
                SCRIPT_MMT.replace("print('Hello", "raise ValueError('Oops"))
            code, out = self.call(main.test_examples_web, {})
            self.assertEqual(code, 1)

    def test_mmt_files(self):
        # Test running all mmt files in a directory
        cwd = os.getcwd()

        # Working files
        self.write('a.mmt', SCRIPT_MMT)
        self.write('b.mmt', SCRIPT_MMT.replace('Hello', 'Hi'))
        self.write('c.txt', SCRIPT_MMT.replace('Hello', 'Hey'))
        code, out = self.call(main.test_mmt_files, self.dir)
        self.assertEqual(os.getcwd(), cwd)
        self.assertIn('Hello from the script', out)
        self.assertIn('Hi from the script', out)
        self.assertNotIn('Hey', out)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main.test_mmt_files(self.dir), 0)

        # Files run in their own directory
        self.write('d.mmt', SCRIPT_MMT.replace(
            "print('Hello from the script')",
            "import os\nprint('In ' + os.getcwd())"))
        code, out = self.call(main.test_mmt_files, self.dir)
        self.assertIn(f'In {os.path.realpath(self.dir)}', out)
        self.assertEqual(os.getcwd(), cwd)

        # Unloadable files are reported, and count as an error
        e = self.write('e.mmt', '[[model]]\nc.x = 1\n[c]\ndot(x) = 1 +\n')
        with contextlib.redirect_stdout(io.StringIO()) as out:
            error = main.test_mmt_files(self.dir)
        self.assertEqual(error, 1)
        self.assertIn('Unable to load.', out.getvalue())
        self.assertEqual(os.getcwd(), cwd)
        e.unlink()

        # Failing files stop the run
        self.write('f.mmt', SCRIPT_MMT.replace(
            "print('Hello", "raise ValueError('Oops"))
        with contextlib.redirect_stdout(io.StringIO()) as out:
            error = main.test_mmt_files(self.dir)
        self.assertEqual(error, 1)
        self.assertIn('ValueError: Oops', out.getvalue())
        self.assertEqual(os.getcwd(), cwd)


if __name__ == '__main__':
    unittest.main()
