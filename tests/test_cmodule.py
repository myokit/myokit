#!/usr/bin/env python3
#
# Tests the CModule class.
#
# This file is part of Myokit.
# See https://github.com/myokit/myokit for copyright, sharing, and licensing.
#
import logging
import unittest

import myokit


class CModuleTest(unittest.TestCase):
    """
    Tests the CModule class.
    """

    def test_logging_unchanged(self):
        # Compiling should not change the root logger

        model = myokit.Model()
        c = model.add_component('c')
        c.add_variable('t', rhs=0, binding='time')
        c.add_variable('x', rhs=1, initial_value=0)

        root = logging.getLogger()
        handlers, level = list(root.handlers), root.level
        try:
            # Remove all handlers, so that basicConfig() will add new ones
            for h in handlers:
                root.removeHandler(h)
            root.setLevel(logging.ERROR)

            myokit.Simulation(model)

            self.assertEqual(root.handlers, [])
            self.assertEqual(root.level, logging.ERROR)
        finally:
            for h in list(root.handlers):
                root.removeHandler(h)
            for h in handlers:
                root.addHandler(h)
            root.setLevel(level)


if __name__ == '__main__':
    unittest.main()
