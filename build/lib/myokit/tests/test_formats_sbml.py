#!/usr/bin/env python3
#
# Tests Myokit's SBML support.
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
import os
import unittest

import numpy as np

import myokit
import myokit.formats
import myokit.formats.sbml

# from shared import DIR_FORMATS, WarningCollector
from myokit.tests import DIR_FORMATS, WarningCollector, TemporaryDirectory


class SBMLExporterTest(unittest.TestCase):
    """
    Tests for :class:`myokit.formats.sbml.SBMLExporter`.
    """

    def test_capability_reporting(self):
        # Test if the right capabilities are reported.
        e = myokit.formats.exporter('sbml')
        self.assertTrue(e.supports_model())
        self.assertFalse(e.supports_runnable())

    def test_stimulus_generation(self):
        # Tests if protocols allow a stimulus current to be added

        e = myokit.formats.exporter('sbml')
        i = myokit.formats.importer('sbml')

        # Load input model
        m1, p1, _ = myokit.load('example')
        org_code = m1.code()

        # 1. Export without a protocol
        with TemporaryDirectory() as d:
            path = d.path('model.sbml')
            with WarningCollector() as w:
                e.model(path, m1)
            m2 = i.model(path)
        self.assertFalse(w.has_warnings())
        self.assertTrue(isinstance(m2.get('global.pace').rhs(), myokit.Number))

        # 2. Export with protocol, but without variable bound to pacing
        m1.get('engine.pace').set_binding(None)
        with TemporaryDirectory() as d:
            path = d.path('model.sbml')
            with WarningCollector() as w:
                e.model(path, m1, p1)
            m2 = i.model(path)
        self.assertTrue(w.has_warnings())
        self.assertTrue(isinstance(m2.get('global.pace').rhs(), myokit.Number))

        # 3. Export with protocol and variable bound to pacing
        m1.get('engine.pace').set_binding('pace')
        with TemporaryDirectory() as d:
            path = d.path('model.cellml')
            with WarningCollector() as w:
                e.model(path, m1, p1)
            m2 = i.model(path)
        self.assertFalse(w.has_warnings())
        rhs = m2.get('global.i_stim').rhs()
        self.assertTrue(rhs, myokit.Multiply)
        self.assertTrue(isinstance(rhs[0], myokit.Piecewise))

        # Check original model is unchanged
        self.assertEqual(org_code, m1.code())


class SBMLImporterTest(unittest.TestCase):
    """
    Tests the SBMLImporter.
    """

    def test_capability_reporting(self):
        # Test if the right capabilities are reported.
        i = myokit.formats.importer('sbml')
        self.assertFalse(i.supports_component())
        self.assertTrue(i.supports_model())
        self.assertFalse(i.supports_protocol())

    def test_model(self):
        # Tests importing the Hodgkin-Huxley model
        i = myokit.formats.importer('sbml')
        with WarningCollector() as w:
            model = i.model(
                os.path.join(DIR_FORMATS, 'sbml', 'HodgkinHuxley.xml'))
        self.assertIn('Unknown SBML namespace', w.text())

        self.assertIsInstance(model, myokit.Model)


class SBMLTestSuiteExamplesTest(unittest.TestCase):
    """
    Tests whether forward simulation of test cases from the SBML test suite
    coincides with the provided time-series data.

    Test Suite examples were taken from http://sbml.org/Facilities/Database/.
    """

    @classmethod
    def setUpClass(cls):
        cls.importer = myokit.formats.importer('sbml')

    def get_sbml_file(self, case):
        return os.path.join(
            DIR_FORMATS, 'sbml', 'model', case + '-sbml-l3v2.xml')

    def get_results(self, case):
        path = os.path.join(
            DIR_FORMATS, 'sbml', 'result', case + '-results.csv')
        data = np.genfromtxt(path, delimiter=',')

        # Eliminate title row
        data = data[1:, :]

        return data

    def test_case_00001(self):
        #
        # From the SBML Test Suite settings:
        #
        # start: 0
        # duration: 5
        # steps: 50
        # variables: S1, S2
        # absolute: 1.000000e-007
        # relative: 0.0001
        # amount: S1, S2
        # concentration:

        case = '00001'

        model = self.importer.model(self.get_sbml_file(case))

        results = self.get_results(case)
        times = results[:, 0]
        s1 = results[:, 1]
        s2 = results[:, 2]

        sim = myokit.Simulation(model)
        output = sim.run(
            duration=times[-1] + 1,
            log=['compartment.S1_amount', 'compartment.S2_amount'],
            log_times=times)

        s1_sim = np.array(output['compartment.S1_amount'])
        np.testing.assert_almost_equal(s1_sim, s1, decimal=6)

        s2_sim = np.array(output['compartment.S2_amount'])
        np.testing.assert_almost_equal(s2_sim, s2, decimal=6)

    def test_case_00004(self):
        #
        # From the SBML Test Suite settings:
        #
        # start: 0
        # duration: 10.0
        # steps: 50
        # variables: S1, S2
        # absolute: 1.000000e-004
        # relative: 0.0001
        # amount: S1, S2
        # concentration:

        case = '00004'

        model = self.importer.model(self.get_sbml_file(case))

        results = self.get_results(case)
        times = results[:, 0]
        s1 = results[:, 1]
        s2 = results[:, 2]

        sim = myokit.Simulation(model)
        output = sim.run(
            duration=times[-1] + 1,
            log=['compartment.S1_amount', 'compartment.S2_amount'],
            log_times=times)

        s1_sim = np.array(output['compartment.S1_amount'])
        np.testing.assert_almost_equal(s1_sim, s1, decimal=4)

        s2_sim = np.array(output['compartment.S2_amount'])
        np.testing.assert_almost_equal(s2_sim, s2, decimal=4)

    def test_case_01103(self):
        #
        # From the SBML Test Suite settings:
        #
        # start: 0
        # duration: 10
        # steps: 100
        # variables: X
        # absolute: 0.0001
        # relative: 0.0001
        # amount: X
        # concentration:

        case = '01103'

        model = self.importer.model(self.get_sbml_file(case))

        results = self.get_results(case)
        times = results[:, 0]
        x = results[:, 1]

        sim = myokit.Simulation(model)
        output = sim.run(
            duration=times[-1] + 1,
            log=['default_compartment.X_amount'],
            log_times=times)

        x_sim = np.array(output['default_compartment.X_amount'])
        np.testing.assert_almost_equal(x_sim, x, decimal=4)


if __name__ == '__main__':
    import warnings
    warnings.simplefilter('always')
    unittest.main()
