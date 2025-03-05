#
# Exports model definitions to Latex files.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import os

import myokit

from ._ewriter import LatexExpressionWriter


class PdfExporter(myokit.formats.Exporter):
    """
    This :class:`Exporter <myokit.formats.Exporter>` exports model equations to
    a simple latex document.
    """
    def __init__(self):
        super().__init__()

    def _clean(self, text):
        """
        Cleans some text for use in latex.
        """
        return text.replace('_', r'\_')

    def post_export_info(self):
        return '\n'.join((
            'To create a pdf using pdflatex::',
            '',
            '  pdflatex filename.tex',
            '',
        ))

    def model(self, path, model, protocol=None):
        """
        Export to an xml document.
        """
        # Create an expression writer
        e = LatexExpressionWriter()

        # Write a simple file
        with open(path, 'w') as f:
            f.write('\\documentclass[fleqn]{article}\n')
            f.write('\\usepackage[a4paper,margin=0.7in]{geometry}\n')

            # Nice math stuff (\text{})
            f.write('\\usepackage{amsmath}\n')

            # Break lines automatically
            f.write('\\usepackage{breqn}\n')
            f.write('\\begin{document}\n')
            title = model.name() or 'Model'
            author = 'Dr. ' + self._clean(self.__class__.__name__)
            f.write('\\title{' + title + '}\n')
            f.write('\\author{' + author + '}\n')
            f.write('\\maketitle\n')

            # Introduction
            try:
                text = model.meta['desc']
                text = str(text)
                text.replace('\\', '\\\\')
                f.write('\\section{Introduction}\n')
                f.write(text)
            except KeyError:    # pragma: no cover
                # No need to test this
                pass

            # Initial conditions
            f.write('\\section{Initial conditions}\n')
            for v in model.states():
                f.write('\\begin{dmath}\n')
                f.write(e.ex(myokit.Name(v)))
                f.write(' = ')
                f.write(e.ex(v.initial_value()))
                f.write('\\end{dmath}\n')

            # Write each component
            for c in model.components():
                f.write('\\section{' + self._clean(c.name()) + '}\n')
                try:
                    text = c.meta['desc']
                    text = str(text)
                    text.replace('\\', '\\\\')
                    f.write(text)
                except KeyError:
                    pass
                for v in c.variables(deep=True):
                    f.write('\\begin{dmath}\n')
                    f.write(e.eq(v.eq()) + '\n')
                    f.write('\\end{dmath}\n')

            # End of document
            f.write('\\end{document}\n')

    def supports_model(self):
        """
        Returns ``True``
        """
        return True


class PosterExporter(myokit.formats.Exporter):
    """
    This :class:`Exporter <myokit.formats.Exporter>` exports model equations to
    a terrifying poster format, designed to strike fear into the heart of its
    beholders.
    """
    def __init__(self):
        super().__init__()

    def post_export_info(self):
        return '\n'.join((
            'To create a pdf using pdflatex::',
            '',
            '  pdflatex filename.tex',
            '',
            'This may require installing some latex packages.',
        ))

    def model(self, path, model, protocol=None):
        """
        Exports a model to an xml document.
        """
        path = os.path.abspath(os.path.expanduser(path))

        # Create an expression writer
        e = LatexExpressionWriter()

        # Write a simple file
        with open(path, 'w') as f:
            f.write('\\documentclass{article}\n')
            f.write('\\usepackage[a4paper,landscape,margin=0.7in]{geometry}\n')

            # Nice math stuff (\text{})
            f.write('\\usepackage{amsmath}\n')

            # Break lines automatically
            f.write('\\usepackage{breqn}\n')

            # Growing page
            f.write('\\usepackage[active,tightpage]{preview}\n')
            f.write('\\renewcommand{\\PreviewBorder}{1in}\n')
            f.write('\\begin{document}\n')
            f.write('\\begin{preview}\n')
            title = model.name() or 'Model'
            f.write('\\title{' + title + '}\n')
            f.write('\\author{}\n')
            f.write('\\date{}\n')
            f.write('\\maketitle\n')

            # Write each component
            for c in model.components():
                for v in c.variables(deep=True):
                    f.write('\\(\n')
                    f.write(e.eq(v.eq()) + '\n')
                    f.write('\\)\n')

            # End of document
            f.write('\\end{preview}\n')
            f.write('\\end{document}\n')

    def supports_model(self):
        """
        Returns ``True``.
        """
        return True
