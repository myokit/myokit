#
# A tiny templating engine using a php style syntax.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import ast
import re
import sys
import traceback

import myokit

try:
    # Python 2
    from cStringIO import StringIO
except ImportError:
    # Python3
    from io import StringIO


class TemplateEngine(object):
    """
    A tiny templating engine using a php style syntax.

    Not intended for use in websites or with untrusted templates.

    Basic syntax::

        Hello <? print("world") ?>

    Fast syntax to write expressions::

        Hello <?= "world" ?>

    All processed template data is printed to the standard output stream or a
    stream specified by the user.
    """
    def __init__(self):
        super(TemplateEngine, self).__init__()
        self.stream = None
        self.error = None

    def error_details(self):
        """
        After a PypeError has been thrown, calling this will method will return
        a detailed (multi-line) error message.

        If no PypeError occurred the return value will be ``None``.
        """
        return self.error

    def process(self, filename, variables={}):
        """
        Processes the file stored at ``filename``. Any variables required by
        this template should be passed in through the dict ``variables``.
        """
        # Reset error log
        self.error = None

        # Check input
        if not type(variables) == dict:
            raise ValueError(
                'Second argument passed to process() must be dict'
                ' (variable_name : value)')

        # Convert script, any exceptions are thrown as PypeErrors
        script = self._convert(filename)

        # Get or create output stream
        stdout = self.stream if self.stream else StringIO()
        stderr = StringIO()

        # Run and handle errors
        error = None
        try:
            # Run, but catch any output + any occurring exception
            sysout = syserr = None
            try:
                sysout = sys.stdout
                syserr = sys.stderr
                sys.stdout = stdout
                sys.stderr = stderr
                myokit._exec(script, variables)
            except Exception:
                error = sys.exc_info()
            finally:
                if sysout:
                    sys.stdout = sysout
                if syserr:
                    sys.stderr = syserr    # Ignore error output

            if error:
                # Add exception traceback to error message
                msg = traceback.format_exception(*error)
                line = None

                # Search for error occurring in <string> (IE the executable
                # template)
                try:
                    # Try checking the last exception, see if its filename
                    # property is set and if it is equal to <string>
                    if error[1].filename == '<string>':
                        line = error[1].lineno  # pragma: no cover
                    else:
                        raise AttributeError
                except AttributeError:
                    # No filename or lineno property or filename not equal to
                    # <string>. Attempt to scan the strack trace for a frame
                    # with filename <string> and extract the line number.
                    next = error[2]
                    try:
                        while next:
                            if next.tb_frame.f_code.co_filename == '<string>':
                                line = next.tb_lineno
                                break
                            next = next.tb_next
                    finally:
                        del next

                if line:
                    # Error during template execution
                    sep = '- ' * 39 + '-'
                    msg.append(sep)
                    msg.append('An error occurred during execution of the'
                               ' processed template shown below.')
                    msg.append(sep)
                    lines = script.splitlines()
                    f = '{:>' + str(1 + len(str(line))) + '} '
                    for k, line in enumerate(lines[0:line]):
                        msg.append(f.format(1 + k) + line)
                    msg.append(sep)
                    msg.append(msg[0])
                self.error = '\n'.join(msg)
                print(self.error)
                raise PypeError('Error during template execution step.')

        finally:
            # Retrieving stack in except clause creates self reference in
            # stack, causing the garbage handler never to delete it. Solve
            # by deleting reference.
            # See: http://docs.python.org/library/sys.html#sys.exc_info
            if error:
                del error

        # Custom stream? Then don't interfere. If not, return stream contents.
        return None if self.stream else stdout.getvalue()

    def _convert(self, source):
        """
        Translates a pype file to a python file
        """
        with open(source, 'r') as f:
            source = f.read()

        # Define token recognising regex, helpers
        tags = [r'<\?=', r'<\?', r'\?>']
        rTags = re.compile(r'(' + '|'.join(tags) + ')')
        rQuot = re.compile(r'(""")')
        rEol = re.compile('[\n]{1}')
        rWhite = re.compile(r'[ \f\t]*')
        indent = ''

        # Convert
        tag_open = None
        out = ['import sys']
        for part in rTags.split(source):

            if part == '?>':
                if tag_open is None:
                    self.error = 'Closing tag found without opening tag'
                    raise PypeError(self.error)
                tag_open = None

            elif part == '<?' or part == '<?=':
                if tag_open is not None:
                    self.error = 'Nested opening tag found'
                    raise PypeError(self.error)
                tag_open = part

            elif tag_open == '<?':
                # Full python statement, remember final indenting
                line = rEol.split(part).pop()
                m = rWhite.match(line)
                indent = line[0:m.end()]
                out.append(part)

            elif tag_open == '<?=':
                # Quick printing statement, python code must be expression
                part = part.strip()
                try:
                    e = ast.parse(part)
                    assert len(e.body) == 1
                    assert isinstance(e.body[0], ast.Expr)
                except Exception:
                    msg = 'Code within <?= ?> tags can only contain a single' \
                          ' expression.'
                    err = traceback.format_exc().splitlines()
                    err.append(msg)
                    self.error = '\n'.join(err)
                    raise PypeError(msg)

                out.append(
                    indent + 'sys.stdout.write(str(' + part + '))')

            else:
                # Non-python code, just print
                # Triple quoted strings should be handled separately
                for part2 in rQuot.split(part):
                    if part2 == '"""':
                        out.append(indent + 'sys.stdout.write(\'"""\')')
                        continue

                    # If part ends in a ", this will cause problems, so...
                    nQuotes = 0
                    while part2[-1:] == '"':
                        part2 = part2[0:-1]
                        nQuotes += 1

                    out.append(
                        indent + 'sys.stdout.write(r"""' + part2 + '""")')

                    if nQuotes > 0:
                        out.append(
                            indent + 'sys.stdout.write(\'' + '"' * nQuotes
                            + '\')')

        return '\n'.join(out)

    def set_output_stream(self, stream):
        """
        When handling a template, all output will be directed into this stream.
        If no stream is specified, the standard output stream stdout is used.
        """
        self.stream = stream


class PypeError(Exception):
    """
    An error thrown by the :class:`TemplateEngine`

    *Extends:* Exception
    """
    def __init__(self, message):
        super(PypeError, self).__init__(message)

