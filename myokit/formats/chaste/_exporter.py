#
# Exports to Chaste.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import os
import re

import myokit
import myokit.formats
import myokit.lib.guess as guess


NAME = re.compile(r'^[a-zA-Z]\w*$')


def is_valid_name(name):
    """
    Tests if the given name can be used as a variable or class name.
    """
    from . import keywords
    return not (NAME.match(name) is None or name in keywords)


class ChasteExporter(myokit.formats.TemplatedRunnableExporter):
    """
    This :class:`Exporter <myokit.formats.Exporter>` generates a model for use
    with Chaste.
    """
    def __init__(self):
        super(ChasteExporter, self).__init__()

        # Filename to use for output
        self._model_code_name = 'model'

    def info(self):
        import inspect
        return inspect.getdoc(self)

    def runnable(self, path, model, protocol=None):
        """
        Exports a :class:`myokit.Model` to Chaste.

        The output will be stored in the **directory** ``path``.
        """
        # This method is overridden here so that we can return files with
        # dynamically generated names.

        # Test model is valid
        try:
            model.validate()
        except myokit.MyokitError:
            raise myokit.ExportError('Chaste export requires a valid model.')

        # Get model name suitable for use in code & file names
        name = model.meta.get('name', 'unnamed_model')
        name = re.sub('[^\w]', '_', name)
        name = re.sub('_+', '_', name)
        name = name.lower()
        if NAME.match(name) is None:
            name = 'unnamed_model'
        self._model_code_name = name

        # Continue
        super(ChasteExporter, self).runnable(path, model, protocol)

    def _dir(self, root):
        return os.path.join(root, 'chaste', 'template')

    def _dict(self):
        return {
            'model.cpp': self._model_code_name + '.cpp',
            'model.hpp': self._model_code_name + '.hpp',
        }

    def _vars(self, model, protocol):
        # Create the variables to pass to the template

        #TODO Convert the time variable to milliseconds

        # Get model name
        name = model.meta.get('name', 'unnamed_model')

        # Create class name
        class_name = self._model_code_name
        if is_valid_name(class_name):
            class_name = ''.join([x.title() for x in class_name.split('_')])
            class_name = 'Cell' + class_name + 'FromMyokit'
        else:
            class_name = 'CellModelFromMyokit'

        # Get header file name
        header_file = self._model_code_name + '.hpp'

        # Variable names
        def var_name(lhs):
            if isinstance(lhs, myokit.Variable):
                lhs = myokit.Name(lhs)
            if isinstance(lhs, myokit.Derivative):
                return 'ddt_' + lhs.var().uname()
            else:
                return 'var_' + lhs.var().uname()

        # State vector
        n_states = model.count_states()
        vm = guess.membrane_potential(model)
        if vm is None:
            raise myokit.ExportError(
                'Chaste export cannot find membrane potential variable.')
        elif not vm.is_state():
            raise myokit.ExportError(
                'Chaste export requires membrane potential to be a state.')

        # Return template variables
        return {
            'class_name': class_name,
            'header_file': header_file,
            'model_name': name,
            'model': model,
            'var_name': var_name,
            'vm': vm,
        }

