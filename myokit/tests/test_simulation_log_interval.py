#!/usr/bin/env python3
#
# Tests the simulation classes' interpretation of log_interval
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import os
import platform
import unittest

import numpy as np

import myokit

from myokit.tests import DIR_DATA, WarningCollector

# Unit testing in Python 2 and 3
try:
    unittest.TestCase.assertRaisesRegex
except AttributeError:
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp

# Extra output
debug = False


class PeriodicTest(unittest.TestCase):
    """
    Tests a simulation class for consistent log entry timing.
    """
    def periodic(self, s):
        # Test periodic logging.
        # Set tolerance for equality testing
        emax = 1e-2     # Time steps for logging are approximate
        # Test 1: Simple 5 ms simulation, log_interval 0.5 ms
        d = s.run(5, log=['engine.time'], log_interval=0.5).npview()
        t = d['engine.time']
        q = np.arange(0, 5, 0.5)
        if debug:
            print(t)
            print(q)
            print('- ' * 10)
        self.assertEqual(len(t), len(q))
        self.assertTrue(np.max(np.abs(t - q)) < emax)
        # Test 2: Very short simulation
        s.reset()
        d = s.run(1, log=['engine.time'], log_interval=0.5).npview()
        t = d['engine.time']
        q = np.arange(0, 1, 0.5)
        if debug:
            print(t)
            print(q)
            print('- ' * 10)
        self.assertEqual(len(t), len(q))
        self.assertTrue(np.max(np.abs(t - q)) < emax)
        # Test 3: Stop and start a simulation
        s.reset()
        d = s.run(1, log=['engine.time'], log_interval=0.5)
        d = s.run(2, log=d, log_interval=0.5)
        d = s.run(2, log=d, log_interval=0.5).npview()
        t = d['engine.time']
        q = np.arange(0, 5, 0.5)
        if debug:
            print(t)
            print(q)
            print('- ' * 10)
        self.assertEqual(len(t), len(q))
        self.assertTrue(np.max(np.abs(t - q)) < emax)


class SimulationTest(PeriodicTest):
    """
    Tests myokit.Simulation (which has dynamic, periodic and point-list
    logging) for consistent log entry timing.
    """
    def test_dynamic(self):
        # Test dynamic logging.

        emax = 1e-6     # Used for equality testing
        if debug:
            print('= Simulation :: Dynamic logging =')
        # Load model & protocol
        m, p, x = myokit.load(os.path.join(DIR_DATA, 'lr-1991.mmt'))
        # Define sensitivities
        sens = (['ik1.gK1', 'ikp.IKp'], ['cell.K_o', 'ikp.gKp'])
        # Create simulation
        s = myokit.Simulation(m, p, sens)

        #
        # Test 1: Simple 5 ms simulation, log_interval 0.5 ms
        #
        d, e = s.run(50, log=['engine.time', 'ik1.gK1', 'ikp.IKp'])
        t = d['engine.time']
        if debug:
            print(t[:2])
            print(t[-2:])
            print('- ' * 10)
        # Test first point not double
        self.assertGreater(t[1], t[0])
        # Test last point not double
        self.assertGreater(t[-1], t[-2])
        # Test first point is 0
        self.assertTrue(np.abs(t[0] - 0) < emax)
        # Test last point is 50
        self.assertTrue(np.abs(t[-1] - 50) < emax)
        # Test shape of sensitivities
        n_states = 2
        n_times = len(t)
        n_sens = 2
        self.assertTrue(np.array(e).shape, (n_times, n_states, n_sens))

        #
        # Test 2: Very short simulation
        #
        s.reset()
        d, e = s.run(1, log=['engine.time', 'ik1.gK1', 'ikp.IKp'])
        t = d['engine.time']
        if debug:
            print(t[:2])
            print(t[-2:])
            print('- ' * 10)
        # Test first point not double
        self.assertGreater(t[1], t[0])
        # Test last point not double
        self.assertGreater(t[-1], t[-2])
        # Test first point is 0
        self.assertTrue(np.abs(t[0] - 0) < emax)
        # Test last point is 50
        self.assertTrue(np.abs(t[-1] - 1) < emax)
        # Test shape of sensitivities
        n_states = 2
        n_times = len(t)
        n_sens = 2
        self.assertTrue(np.array(e).shape, (n_times, n_states, n_sens))

        #
        # Test 3: Stop and start a simulation
        #
        s.reset()
        d, e = s.run(2, log=['engine.time', 'ik1.gK1', 'ikp.IKp'])
        t = d['engine.time']
        n = len(d['engine.time'])
        if debug:
            print(d['engine.time'][:2])
        # Test first point not double
        self.assertGreater(t[1], t[0])
        # Test last point not double
        self.assertGreater(t[-1], t[-2])
        # Test first point is 0
        self.assertTrue(np.abs(t[0] - 0) < emax)
        # Test last point is 2
        self.assertTrue(np.abs(t[-1] - 2) < emax)
        # Test shape of sensitivities
        n_states = 2
        n_times = len(t)
        n_sens = 2
        self.assertTrue(np.array(e).shape, (n_times, n_states, n_sens))
        d, e = s.run(13, log=d)
        t = d['engine.time']
        if debug:
            print(t[n - 2:n + 2])
        # Test last point not double
        self.assertGreater(t[-1], t[-2])
        # Test last point is 2+13
        self.assertTrue(np.abs(t[-1] - 15) < emax)
        # Test intermediary points are different
        self.assertGreater(t[n], t[n - 1])
        # Test shape of sensitivities
        n_states = 2
        n_times = len(t)
        n_sens = 2
        self.assertTrue(np.array(e).shape, (n_times, n_states, n_sens))
        n = len(d['engine.time'])
        d, e = s.run(15, log=d)
        t = d['engine.time']
        if debug:
            print(t[n - 2:n + 2])
        # Test last point not double
        self.assertGreater(t[-1], t[-2])
        # Test last point is 2 + 13 + 15
        self.assertTrue(np.abs(t[-1] - 30) < emax)
        # Test intermediary points are different
        self.assertGreater(t[n], t[n - 1])
        # Test shape of sensitivities
        n_states = 2
        n_times = len(t)
        n_sens = 2
        self.assertTrue(np.array(e).shape, (n_times, n_states, n_sens))
        n = len(d['engine.time'])
        d, e = s.run(20, log=d)
        t = d['engine.time']
        if debug:
            print(t[n - 2:n + 2])
            print(t[-2:])
            print('- ' * 10)
        # Test last point not double
        self.assertGreater(t[-1], t[-2])
        # Test last point is 2 + 13 + 15 + 20
        self.assertTrue(np.abs(t[-1] - 50) < emax)
        # Test intermediary points are different
        self.assertGreater(t[n], t[n - 1])
        # Test shape of sensitivities
        n_states = 2
        n_times = len(t)
        n_sens = 2
        self.assertTrue(np.array(e).shape, (n_times, n_states, n_sens))

    def test_periodic(self):
        # Test periodic logging

        m, p, x = myokit.load(os.path.join(DIR_DATA, 'lr-1991.mmt'))
        s = myokit.Simulation(m, p)
        self.periodic(s)

    def test_interpolation_and_pacing(self):
        # Test if interpolation results in correct pacing values.

        # When logging with discontinuous steps, in the adaptive time
        # CVODE sim, the value of pace must be
        #  1. The old value *before* the time of the event
        #  2. The new value *at and after* the time of the event
        #  3. Back to zero *at and after* the end of the event
        #     (Unless it ends sooner due to a new event arriving)
        # Load model
        m = myokit.load_model('example')

        # Voltage-clamp V (but don't bind it directly)
        v = m.label('membrane_potential')
        v.demote()
        v.set_rhs('-80 + 10 * engine.pace')

        # Create protocol
        p = myokit.Protocol()
        p.schedule(level=1, start=0, duration=5, period=10)

        # Create simulation
        s = myokit.Simulation(m, p)

        # Test if this would result in multiple interpolation steps for logging
        # i.e. test if the step before each transition was at least 2 log steps
        # long
        e = s.run(30).npview()
        t = e.time()
        for x in [5, 10, 15, 20, 25]:
            i = e.find_after(x)
            if not t[i] - t[i - 1] > 0.2:
                raise Exception('Issue with test: use longer intervals!')
        del e, t, x, i

        # Now test if correct interpolated values are returned by periodic
        # logging.
        d = s.run(30, log_interval=0.1).npview()

        # Test bound variable
        p = d['engine.pace']
        self.assertTrue(np.all(p[0:50] == 1))
        self.assertTrue(np.all(p[50:100] == 0))
        self.assertTrue(np.all(p[100:150] == 1))
        self.assertTrue(np.all(p[150:200] == 0))
        self.assertTrue(np.all(p[200:250] == 1))
        self.assertTrue(np.all(p[250:300] == 0))

        # Test variable dependent on bound variable
        p = d['membrane.V']
        self.assertTrue(np.all(p[0:50] == -70))
        self.assertTrue(np.all(p[50:100] == -80))
        self.assertTrue(np.all(p[100:150] == -70))
        self.assertTrue(np.all(p[150:200] == -80))
        self.assertTrue(np.all(p[200:250] == -70))
        self.assertTrue(np.all(p[250:300] == -80))

    def test_point_list(self):
        # Test logging with a preset list of points.

        # Load model
        m, p, x = myokit.load(os.path.join(DIR_DATA, 'lr-1991.mmt'))
        # Create simulation
        s = myokit.Simulation(m, p)

        # Don't allow decreasing values
        times = [1, 2, 1]
        self.assertRaisesRegex(
            ValueError, 'non-decreasing', s.run, 5, log_times=times)

        # Can't use together with a log interval
        self.assertRaisesRegex(
            ValueError, 'simultaneously', s.run, 5, log_interval=1,
            log_times=[1, 2, 3])

        # Get some odd times
        times = np.linspace(0, 90, 999)

        # Test!
        s.reset()
        d = s.run(100, log_times=times).npview()
        self.assertTrue(np.all(d.time() == times))

        # Reset and run again
        s.reset()
        d = s.run(100, log_times=times).npview()
        self.assertTrue(np.all(d.time() == times))

        # Run in parts
        s.reset()
        d = s.run(50, log_times=times)
        self.assertEqual(len(d.time()), np.where(times >= 50)[0][0])
        d = s.run(50, log=d, log_times=times).npview()
        self.assertTrue(np.all(d.time() == times))

        # Pre-pacing
        s.reset()
        s.pre(50)
        s.run(100, log_times=times)
        self.assertTrue(np.all(d.time() == times))

        # Partial logging
        s.reset()
        s.run(10)
        d = s.run(10, log_times=times)
        imin = np.where(times >= 10)[0][0]
        imax = np.where(times >= 20)[0][0]
        self.assertEqual(len(d.time()), imax - imin)
        self.assertTrue(np.all(d.time() == times[imin:imax]))
        s.run(20)
        d = s.run(15, log_times=times)
        imin = np.where(times >= 40)[0][0]
        imax = np.where(times >= 55)[0][0]
        self.assertEqual(len(d.time()), imax - imin)
        self.assertTrue(np.all(d.time() == times[imin:imax]))

        # Get some regular times
        times = [0, 1, 2, 3, 4, 5]
        s.reset()
        d = s.run(6, log_times=times).npview()
        self.assertEqual(len(d.time()), len(times))
        self.assertTrue(np.all(d.time() == times))

        # Repeated points
        times = [0, 0, 0, 5, 5, 5]
        s.reset()
        d = s.run(6, log_times=times).npview()
        self.assertEqual(len(d.time()), len(times))
        self.assertTrue(np.all(d.time() == times))

        # End points not included, unless also visited!
        s.reset()
        s.run(5)
        d = s.run(5, log_times=times).npview()
        self.assertEqual(len(d.time()), 3)
        self.assertTrue(np.all(d.time() == times[3:]))
        d = s.run(5, log_times=times).npview()
        self.assertEqual(len(d.time()), 0)

        # Empty list is same as none
        s.reset()
        d = s.run(1, log_times=[])
        self.assertNotEqual(len(d.time()), 0)

    def test_point_list_2(self):
        # Test how the point-list logging performs when some of the logging
        # points overlap with protocol change points.

        # Load model
        m = myokit.load_model(os.path.join(DIR_DATA, 'lr-1991.mmt'))
        # Voltage clamp
        m.binding('pace').set_binding(None)
        v = m.get('membrane.V')
        v.demote()
        v.set_rhs(0)
        v.set_binding('pace')
        #TODO: Implement chaining like this?
        #m.get('membrane.V').demote().set_rhs(0).set_binding('pace')
        # Create step protocol
        dt = 0.1
        steps = [
            [-80, 250.1],
            [-120, 50],
            [-80, 200],
            [40, 1000],
            [-120, 500],
            [-80, 1000],
            [-30, 3500],
            [-120, 500],
            [-80, 1000],
        ]
        p = myokit.Protocol()
        for f, t in steps:
            p.add_step(f, t)
        # Create set of times that overlap with change points
        times = np.arange(80000) * dt
        # Create simulation
        s = myokit.Simulation(m, p)
        # Run
        d = s.run(8000, log_times=times).npview()
        # Check if logging points show correct pacing value
        # In an earlier implementation, rounding errors and a difference in the
        # implementation of passing logpoints and passing protocol points could
        # cause the log point to be just before the protocol change.
        # In this case, a change at t=120.0 would only be picked up at t=120.1
        # (but not consistently!)
        # The below code checks for this
        offset = 0
        for v, t in steps[:-1]:
            offset += t
            e = d.trim(offset - dt, offset + 2 * dt)
            self.assertNotEqual(e['membrane.V'][0], e['membrane.V'][1])


@unittest.skipIf(platform.system() != 'Linux', 'Legacy CVODE tests')
class LegacySimulationTest(PeriodicTest):
    """
    Tests myokit.LegacySimulation (which has dynamic, periodic and point-list
    logging) for consistent log entry timing.
    """
    def test_dynamic(self):
        # Test dynamic logging.

        emax = 1e-6     # Used for equality testing
        if debug:
            print('= Simulation :: Dynamic logging =')
        # Load model & protocol
        m, p, x = myokit.load(os.path.join(DIR_DATA, 'lr-1991.mmt'))
        # Create simulation
        s = myokit.LegacySimulation(m, p)

        #
        # Test 1: Simple 5 ms simulation, log_interval 0.5 ms
        #
        d = s.run(50, log=['engine.time'])
        t = d['engine.time']
        if debug:
            print(t[:2])
            print(t[-2:])
            print('- ' * 10)
        # Test first point not double
        self.assertGreater(t[1], t[0])
        # Test last point not double
        self.assertGreater(t[-1], t[-2])
        # Test first point is 0
        self.assertTrue(np.abs(t[0] - 0) < emax)
        # Test last point is 50
        self.assertTrue(np.abs(t[-1] - 50) < emax)

        #
        # Test 2: Very short simulation
        #
        s.reset()
        d = s.run(1, log=['engine.time'])
        t = d['engine.time']
        if debug:
            print(t[:2])
            print(t[-2:])
            print('- ' * 10)
        # Test first point not double
        self.assertGreater(t[1], t[0])
        # Test last point not double
        self.assertGreater(t[-1], t[-2])
        # Test first point is 0
        self.assertTrue(np.abs(t[0] - 0) < emax)
        # Test last point is 50
        self.assertTrue(np.abs(t[-1] - 1) < emax)

        #
        # Test 3: Stop and start a simulation
        #
        s.reset()
        d = s.run(2, log=['engine.time'])
        t = d['engine.time']
        n = len(d['engine.time'])
        if debug:
            print(d['engine.time'][:2])
        # Test first point not double
        self.assertGreater(t[1], t[0])
        # Test last point not double
        self.assertGreater(t[-1], t[-2])
        # Test first point is 0
        self.assertTrue(np.abs(t[0] - 0) < emax)
        # Test last point is 2
        self.assertTrue(np.abs(t[-1] - 2) < emax)
        d = s.run(13, log=d)
        t = d['engine.time']
        if debug:
            print(t[n - 2:n + 2])
        # Test last point not double
        self.assertGreater(t[-1], t[-2])
        # Test last point is 2+13
        self.assertTrue(np.abs(t[-1] - 15) < emax)
        # Test intermediary points are different
        self.assertGreater(t[n], t[n - 1])
        n = len(d['engine.time'])
        d = s.run(15, log=d)
        t = d['engine.time']
        if debug:
            print(t[n - 2:n + 2])
        # Test last point not double
        self.assertGreater(t[-1], t[-2])
        # Test last point is 2 + 13 + 15
        self.assertTrue(np.abs(t[-1] - 30) < emax)
        # Test intermediary points are different
        self.assertGreater(t[n], t[n - 1])
        n = len(d['engine.time'])
        d = s.run(20, log=d)
        t = d['engine.time']
        if debug:
            print(t[n - 2:n + 2])
            print(t[-2:])
            print('- ' * 10)
        # Test last point not double
        self.assertGreater(t[-1], t[-2])
        # Test last point is 2 + 13 + 15 + 20
        self.assertTrue(np.abs(t[-1] - 50) < emax)
        # Test intermediary points are different
        self.assertGreater(t[n], t[n - 1])

    def test_periodic(self):
        # Test periodic logging

        m, p, x = myokit.load(os.path.join(DIR_DATA, 'lr-1991.mmt'))
        s = myokit.LegacySimulation(m, p)
        self.periodic(s)

    def test_interpolation_and_pacing(self):
        # Test if interpolation results in correct pacing values.

        # When logging with discontinuous steps, in the adaptive time
        # CVODE sim, the value of pace must be
        #  1. The old value *before* the time of the event
        #  2. The new value *at and after* the time of the event
        #  3. Back to zero *at and after* the end of the event
        #     (Unless it ends sooner due to a new event arriving)
        # Load model
        m = myokit.load_model('example')

        # Voltage-clamp V (but don't bind it directly)
        v = m.label('membrane_potential')
        v.demote()
        v.set_rhs('-80 + 10 * engine.pace')

        # Create protocol
        p = myokit.Protocol()
        p.schedule(level=1, start=0, duration=5, period=10)

        # Create simulation
        s = myokit.LegacySimulation(m, p)

        # Test if this would result in multiple interpolation steps for logging
        # i.e. test if the step before each transition was at least 2 log steps
        # long
        e = s.run(30).npview()
        t = e.time()
        for x in [5, 10, 15, 20, 25]:
            i = e.find_after(x)
            if not t[i] - t[i - 1] > 0.2:
                raise Exception('Issue with test: use longer intervals!')
        del e, t, x, i

        # Now test if correct interpolated values are returned by periodic
        # logging.
        d = s.run(30, log_interval=0.1).npview()

        # Test bound variable
        p = d['engine.pace']
        self.assertTrue(np.all(p[0:50] == 1))
        self.assertTrue(np.all(p[50:100] == 0))
        self.assertTrue(np.all(p[100:150] == 1))
        self.assertTrue(np.all(p[150:200] == 0))
        self.assertTrue(np.all(p[200:250] == 1))
        self.assertTrue(np.all(p[250:300] == 0))

        # Test variable dependent on bound variable
        p = d['membrane.V']
        self.assertTrue(np.all(p[0:50] == -70))
        self.assertTrue(np.all(p[50:100] == -80))
        self.assertTrue(np.all(p[100:150] == -70))
        self.assertTrue(np.all(p[150:200] == -80))
        self.assertTrue(np.all(p[200:250] == -70))
        self.assertTrue(np.all(p[250:300] == -80))

    def test_point_list(self):
        # Test logging with a preset list of points.

        # Load model
        m, p, x = myokit.load(os.path.join(DIR_DATA, 'lr-1991.mmt'))
        # Create simulation
        s = myokit.LegacySimulation(m, p)

        # Don't allow decreasing values
        times = [1, 2, 1]
        self.assertRaisesRegex(
            ValueError, 'non-decreasing', s.run, 5, log_times=times)

        # Can't use together with a log interval
        self.assertRaisesRegex(
            ValueError, 'simultaneously', s.run, 5, log_interval=1,
            log_times=[1, 2, 3])

        # Get some odd times
        times = np.linspace(0, 90, 999)

        # Test!
        s.reset()
        d = s.run(100, log_times=times).npview()
        self.assertTrue(np.all(d.time() == times))

        # Reset and run again
        s.reset()
        d = s.run(100, log_times=times).npview()
        self.assertTrue(np.all(d.time() == times))

        # Run in parts
        s.reset()
        d = s.run(50, log_times=times)
        self.assertEqual(len(d.time()), np.where(times >= 50)[0][0])
        d = s.run(50, log=d, log_times=times).npview()
        self.assertTrue(np.all(d.time() == times))

        # Pre-pacing
        s.reset()
        s.pre(50)
        s.run(100, log_times=times)
        self.assertTrue(np.all(d.time() == times))

        # Partial logging
        s.reset()
        s.run(10)
        d = s.run(10, log_times=times)
        imin = np.where(times >= 10)[0][0]
        imax = np.where(times >= 20)[0][0]
        self.assertEqual(len(d.time()), imax - imin)
        self.assertTrue(np.all(d.time() == times[imin:imax]))
        s.run(20)
        d = s.run(15, log_times=times)
        imin = np.where(times >= 40)[0][0]
        imax = np.where(times >= 55)[0][0]
        self.assertEqual(len(d.time()), imax - imin)
        self.assertTrue(np.all(d.time() == times[imin:imax]))

        # Get some regular times
        times = [0, 1, 2, 3, 4, 5]
        s.reset()
        d = s.run(6, log_times=times).npview()
        self.assertEqual(len(d.time()), len(times))
        self.assertTrue(np.all(d.time() == times))

        # Repeated points
        times = [0, 0, 0, 5, 5, 5]
        s.reset()
        d = s.run(6, log_times=times).npview()
        self.assertEqual(len(d.time()), len(times))
        self.assertTrue(np.all(d.time() == times))

        # End points not included, unless also visited!
        s.reset()
        s.run(5)
        d = s.run(5, log_times=times).npview()
        self.assertEqual(len(d.time()), 3)
        self.assertTrue(np.all(d.time() == times[3:]))
        d = s.run(5, log_times=times).npview()
        self.assertEqual(len(d.time()), 0)

        # Empty list is same as none
        s.reset()
        d = s.run(1, log_times=[])
        self.assertNotEqual(len(d.time()), 0)

    def test_point_list_2(self):
        # Test how the point-list logging performs when some of the logging
        # points overlap with protocol change points.

        # Load model
        m = myokit.load_model(os.path.join(DIR_DATA, 'lr-1991.mmt'))
        # Voltage clamp
        m.binding('pace').set_binding(None)
        v = m.get('membrane.V')
        v.demote()
        v.set_rhs(0)
        v.set_binding('pace')
        #TODO: Implement chaining like this?
        #m.get('membrane.V').demote().set_rhs(0).set_binding('pace')
        # Create step protocol
        dt = 0.1
        steps = [
            [-80, 250.1],
            [-120, 50],
            [-80, 200],
            [40, 1000],
            [-120, 500],
            [-80, 1000],
            [-30, 3500],
            [-120, 500],
            [-80, 1000],
        ]
        p = myokit.Protocol()
        for f, t in steps:
            p.add_step(f, t)
        # Create set of times that overlap with change points
        times = np.arange(80000) * dt
        # Create simulation
        s = myokit.LegacySimulation(m, p)
        # Run
        d = s.run(8000, log_times=times).npview()
        # Check if logging points show correct pacing value
        # In an earlier implementation, rounding errors and a difference in the
        # implementation of passing logpoints and passing protocol points could
        # cause the log point to be just before the protocol change.
        # In this case, a change at t=120.0 would only be picked up at t=120.1
        # (but not consistently!)
        # The below code checks for this
        offset = 0
        for v, t in steps[:-1]:
            offset += t
            e = d.trim(offset - dt, offset + 2 * dt)
            self.assertNotEqual(e['membrane.V'][0], e['membrane.V'][1])


class Simulation1dTest(PeriodicTest):
    """
    Tests myokit.Simulation1d for consistent log entry timing.
    """
    def test_periodic(self):
        # Test periodic logging.

        m, p, x = myokit.load(os.path.join(DIR_DATA, 'lr-1991.mmt'))
        s = myokit.Simulation1d(m, p, ncells=1)
        self.periodic(s)


class PSimulationTest(unittest.TestCase):
    """
    Tests myokit.PSimulation for consistent log entry timing.
    """
    def test_periodic(self):
        # Test periodic logging.

        m, p, x = myokit.load(os.path.join(DIR_DATA, 'lr-1991.mmt'))
        with WarningCollector():
            s = myokit.PSimulation(
                m, p, variables=['membrane.V'], parameters=['ina.gNa'])
        # Set tolerance for equality testing
        emax = 1e-2     # Time steps for logging are approximate

        # Test 1: Simple 5 ms simulation, log_interval 0.5 ms
        d, e = s.run(5, log=['engine.time'], log_interval=0.5)
        d = d.npview()
        t = d['engine.time']
        q = np.arange(0, 5, 0.5)
        if debug:
            print(t)
            print(q)
            print('- ' * 10)
        self.assertEqual(len(t), len(q))
        self.assertTrue(np.max(np.abs(t - q)) < emax)

        # Test 2: Very short simulation
        s.reset()
        d, e = s.run(1, log=['engine.time'], log_interval=0.5)
        d = d.npview()
        t = d['engine.time']
        q = np.arange(0, 1, 0.5)
        if debug:
            print(t)
            print(q)
            print('- ' * 10)
        self.assertEqual(len(t), len(q))
        self.assertTrue(np.max(np.abs(t - q)) < emax)

        # Test 3: Stop and start a simulation
        s.reset()
        d, e = s.run(1, log=['engine.time'], log_interval=0.5)
        d, e = s.run(2, log=d, log_interval=0.5)
        d, e = s.run(2, log=d, log_interval=0.5)
        d = d.npview()
        t = d['engine.time']
        q = np.arange(0, 5, 0.5)
        if debug:
            print(t)
            print(q)
            print('- ' * 10)
        self.assertEqual(len(t), len(q))
        self.assertTrue(np.max(np.abs(t - q)) < emax)

        # Negative or 0 log interval --> Log every step
        s.set_step_size(0.01)
        d, dp = s.run(1, log_interval=0)
        self.assertEqual(len(d.time()), 101)
        d, dp = s.run(1, log_interval=-1)
        self.assertEqual(len(d.time()), 101)


class ICSimulationTest(unittest.TestCase):
    """
    Tests myokit.ICSimulation for consistent log entry timing.
    """
    def test_periodic(self):
        # Test periodic logging.

        m, p, x = myokit.load(os.path.join(DIR_DATA, 'lr-1991.mmt'))
        with WarningCollector():
            s = myokit.ICSimulation(m, p)
        # Set tolerance for equality testing
        emax = 1e-2     # Time steps for logging are approximate
        # Test 1: Simple 5 ms simulation, log_interval 0.5 ms
        d, e = s.run(5, log=['engine.time'], log_interval=0.5)
        d = d.npview()
        t = d['engine.time']
        q = np.arange(0, 5, 0.5)
        if debug:
            print(t)
            print(q)
            print('- ' * 10)
        self.assertEqual(len(t), len(q))
        self.assertTrue(np.max(np.abs(t - q)) < emax)
        # Test 2: Very short simulation
        s.reset()
        d, e = s.run(1, log=['engine.time'], log_interval=0.5)
        d = d.npview()
        t = d['engine.time']
        q = np.arange(0, 1, 0.5)
        if debug:
            print(t)
            print(q)
            print('- ' * 10)
        self.assertEqual(len(t), len(q))
        self.assertTrue(np.max(np.abs(t - q)) < emax)
        # Test 3: Stop and start a simulation
        s.reset()
        d, e = s.run(1, log=['engine.time'], log_interval=0.5)
        d, e = s.run(2, log=d, log_interval=0.5)
        d, e = s.run(2, log=d, log_interval=0.5)
        d = d.npview()
        t = d['engine.time']
        q = np.arange(0, 5, 0.5)
        if debug:
            print(t)
            print(q)
            print('- ' * 10)
        self.assertEqual(len(t), len(q))
        self.assertTrue(np.max(np.abs(t - q)) < emax)


if __name__ == '__main__':
    print('Add -v for more debug output')
    import sys
    if '-v' in sys.argv:
        debug = True
    unittest.main()
