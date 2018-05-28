#!/usr/bin/env python
#
# Tests the most interesting files from the PBMB 2016 publication.
#
# This file is part of Myokit
#  Copyright 2011-2018 Maastricht University, University of Oxford
#  Licensed under the GNU General Public License v3.0
#  See: http://myokit.org
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import os
import myokit
import unittest

from shared import DIR_PUBLICATIONS


def mmt(root, filename):
    """
    Runs an ``mmt`` file, raising exceptions if it fails.
    """
    old_path = os.getcwd()
    path = os.path.join(DIR_PUBLICATIONS, root)
    try:
        os.chdir(path)
        with myokit.PyCapture():
            myokit.run(*myokit.load(os.path.join(path, filename)))
    finally:
        os.chdir(old_path)


class PBMB2016(unittest.TestCase):
    """
    Tests the most interesting examples of the 2016 PBMB publication.
    """

    def setUp(self):
        # Select matplotlib backend that doesn't require a screen
        import matplotlib
        matplotlib.use('template')

    def test_multi_model(self):
        # Multi-model testing
        mmt('pbmb-2016', 'test-example-multi-model-testing.mmt')

    def test_parameter_estimation(self):
        # Parameter estimation with synthetic data
        mmt('pbmb-2016', 'test-example-parameter-estimation.mmt')

    def test_parameter_estimation_2(self):
        # Parameter estimation with real data
        mmt('pbmb-2016', 'test-example-parameter-estimation-2.mmt')
        #'pbmb-2016', 'test-example-ttp-1-model.mmt'
        #'pbmb-2016', 'test-example-ttp-2-transmural-differences.mmt'
        #'pbmb-2016', 'test-example-ttp-3-gto.mmt'
        #'pbmb-2016', 'test-example-ttp-4-sensitivity.mmt'
        #'pbmb-2016', 'test-example-ttp-5-transmural-baseline.mmt'
        #'pbmb-2016', 'test-example-ttp-6-transmural-modified.mmt'
        #'pbmb-2016', 'test-example-ttp-7-transmural-plane.mmt'

if __name__ == '__main__':
    unittest.main()
