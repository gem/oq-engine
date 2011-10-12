# -*- coding: utf-8 -*-

# Copyright (c) 2010-2011, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.


"""
Unit tests for classic PSHA hazard computations with the hazard engine.
"""

import multiprocessing
import unittest

from openquake import logs
from openquake import shapes

from openquake.hazard.job import opensha

from tests.utils import helpers
from tests.utils.tasks import test_compute_hazard_curve, test_data_reflector

LOG = logs.LOG


class DoCurvesTestCase(helpers.TestMixin, unittest.TestCase):
    """Tests the behaviour of ClassicalMixin.do_curves()."""

    def __init__(self, *args, **kwargs):
        super(DoCurvesTestCase, self).__init__(*args, **kwargs)
        self.keys = []
        self.sites = [shapes.Site(-121.9, 38.0), shapes.Site(-121.8, 38.0),
                      shapes.Site(-122.9, 38.0), shapes.Site(-122.8, 38.0)]

    class FakeLogicTreeProcessor(object):
        """
        Fake logic tree processor class. This test will not manipulate any
        logic trees.
        """
        def sampleAndSaveERFTree(self, cache, key, seed):
            """Do nothing."""

        def sampleAndSaveGMPETree(self, cache, key, seed):
            """Do nothing."""

    mock_results = [
        [
            "hazard_curve!38cdc377!1!-121.9!38.0",
            "hazard_curve!38cdc377!1!-121.8!38.0",
            "hazard_curve!38cdc377!1!-121.7!38.0"],
        [
            "hazard_curve!38cdc377!2!-121.9!38.0",
            "hazard_curve!38cdc377!2!-121.8!38.0",
            "hazard_curve!38cdc377!2!-121.7!38.0"]]

    def setUp(self):
        self.mixin = self.create_job_with_mixin({'CALCULATION_MODE': 'Hazard'},
                                                opensha.ClassicalMixin)
        # Store the canned result data in the KVS.
        key = self.mixin.job_id
        for realization in xrange(2):
            key = "%s/%s" % (self.mixin.job_id, realization + 1)
            helpers.TestStore.put(key, self.mock_results[realization])
            self.keys.append(key)
        LOG.debug("keys = '%s'" % self.keys)
        # Initialize the mixin instance.
        self.mixin.params = dict(NUMBER_OF_LOGIC_TREE_SAMPLES=2)
        self.mixin.calc = self.FakeLogicTreeProcessor()
        self.mixin.cache = dict()

    def tearDown(self):
        # Remove the canned result data from the KVS.
        for key in self.keys:
            helpers.TestStore.remove(key)

        self.unload_job_mixin()

    def test_serializer_called_when_passed(self):
        """The passed serialization function is called for each realization."""

        def fake_serializer(sites, realization):
            """Fake serialization function to be used in this test."""
            self.assertEqual(self.sites, sites)

            fake_serializer.number_of_calls += 1

        # We will count the number of invocations using a property of the fake
        # serializer function.
        fake_serializer.number_of_calls = 0

        self.mixin.do_curves(self.sites, 2, serializer=fake_serializer,
                             the_task=test_compute_hazard_curve)
        self.assertEqual(2, fake_serializer.number_of_calls)


class DoMeansTestCase(helpers.TestMixin, unittest.TestCase):
    """Tests the behaviour of ClassicalMixin.do_means()."""

    def __init__(self, *args, **kwargs):
        super(DoMeansTestCase, self).__init__(*args, **kwargs)
        self.keys = []
        self.sites = [shapes.Site(-121.9, 38.0), shapes.Site(-121.8, 38.0),
                      shapes.Site(-122.9, 38.0), shapes.Site(-122.8, 38.0)]

        self.mixin = None

    mock_results = [
        "mean_hazard_curve!38cdc377!1!-121.9!38.0",
        "mean_hazard_curve!38cdc377!1!-121.8!38.0",
        "mean_hazard_curve!38cdc377!1!-121.7!38.0"]

    def setUp(self):
        params = {
            'CALCULATION_MODE': 'Hazard',
            'COMPUTE_MEAN_HAZARD_CURVE': 'True',
        }

        self.mixin = self.create_job_with_mixin(params, opensha.ClassicalMixin)

    def tearDown(self):
        # Remove the canned result data from the KVS.
        for key in self.keys:
            helpers.TestStore.remove(key)

        self.unload_job_mixin()

    def test_curve_serializer_called_when_passed(self):
        """The passed mean curve serialization function is called."""

        def fake_serializer(sites):
            """Fake serialization function to be used in this test."""
            self.assertEqual(self.sites, sites)
            fake_serializer.number_of_calls += 1

        # Count the number of invocations using this property of the fake
        # serializer function.
        fake_serializer.number_of_calls = 0

        key = helpers.TestStore.put(self.mixin.job_id, self.mock_results)
        self.keys.append(key)
        self.mixin.do_means(self.sites, 1,
                        curve_serializer=fake_serializer,
                        curve_task=test_data_reflector)
        self.assertEqual(1, fake_serializer.number_of_calls)

    def test_map_serializer_not_called_unless_configured(self):
        """
        The mean map serialization function is not called unless the
        POES parameter was specified in the configuration file.
        """

        def fake_serializer(kvs_keys):
            """Fake serialization function to be used in this test."""
            # Check that the data returned is the one we expect for the current
            # realization.
            fake_serializer.number_of_calls += 1

        fake_serializer.number_of_calls = 0

        key = helpers.TestStore.put(self.mixin.job_id, self.mock_results)
        self.keys.append(key)
        self.mixin.do_means(self.sites, 1,
                        curve_serializer=lambda _: True,
                        curve_task=test_data_reflector)
        self.assertEqual(0, fake_serializer.number_of_calls)

    def test_map_serializer_called_when_configured(self):
        """
        The mean map serialization function is called when the POES
        parameter is specified in the configuration file.
        """

        def fake_serializer(sites, poes):
            """Fake serialization function to be used in this test."""
            # Check that the data returned is the one we expect for the current
            # realization.
            fake_serializer.number_of_calls += 1

        def fake_map_func(*args):
            return list(xrange(3))

        fake_serializer.number_of_calls = 0

        key = helpers.TestStore.put(self.mixin.job_id, self.mock_results)
        self.keys.append(key)
        self.mixin.params["POES"] = "0.6 0.8"
        self.mixin.do_means(self.sites, 1,
            curve_serializer=lambda _: True,
            curve_task=test_data_reflector,
            map_func=fake_map_func,
            map_serializer=fake_serializer)
        self.assertEqual(1, fake_serializer.number_of_calls)

    def test_missing_map_serializer_assertion(self):
        """
        When the mean map serialization function is not set an `AssertionError`
        is raised.

        TODO: once everyone is on python rev. > 2.7 extend the test to check
        for the specific assertion message.
        """

        key = helpers.TestStore.put(self.mixin.job_id, self.mock_results)
        self.keys.append(key)
        self.mixin.params["POES"] = "0.6 0.8"
        self.assertRaises(
            AssertionError, self.mixin.do_means,
            self.sites, 1,
            curve_serializer=lambda _: True,
            curve_task=test_data_reflector, map_func=lambda _: [1, 2, 3])

    def test_missing_map_function_assertion(self):
        """
        When the mean map calculation function is not set an `AssertionError`
        is raised.

        TODO: once everyone is on python rev. > 2.7 extend the test to check
        for the specific assertion message.
        """

        key = helpers.TestStore.put(self.mixin.job_id, self.mock_results)
        self.keys.append(key)
        self.mixin.params["POES"] = "0.6 0.8"
        self.assertRaises(
            AssertionError, self.mixin.do_means,
            self.sites, 1,
            curve_serializer=lambda _: True, curve_task=test_data_reflector,
            map_serializer=lambda _: True, map_func=None)


class DoQuantilesTestCase(helpers.TestMixin, unittest.TestCase):
    """Tests the behaviour of ClassicalMixin.do_quantiles()."""

    def __init__(self, *args, **kwargs):
        super(DoQuantilesTestCase, self).__init__(*args, **kwargs)
        self.keys = []
        self.sites = [shapes.Site(-121.9, 38.0), shapes.Site(-121.8, 38.0),
                      shapes.Site(-122.9, 38.0), shapes.Site(-122.8, 38.0)]

    mock_results = [
        "quantile_hazard_curve!10!-121.9!38.0!0.2",
        "quantile_hazard_curve!10!-122.9!38.0!0.2",
        "quantile_hazard_curve!10!-121.8!38.0!0.4",
        "quantile_hazard_curve!10!-122.8!38.0!0.4"]

    def setUp(self):
        self.mixin = self.create_job_with_mixin({'CALCULATION_MODE': 'Hazard'},
                                                opensha.ClassicalMixin)

    def tearDown(self):
        # Remove the canned result data from the KVS.
        for key in self.keys:
            helpers.TestStore.remove(key)

        self.unload_job_mixin()

    def test_curve_serializer_called_when_passed(self):
        """The passed quantile curve serialization function is called."""
        def fake_serializer(sites, quantile):
            """Fake serialization function to be used in this test."""
            fake_serializer.number_of_calls += 1

        fake_serializer.number_of_calls = 0

        key = helpers.TestStore.put(self.mixin.job_id, self.mock_results)
        self.keys.append(key)
        self.mixin.do_quantiles(self.sites, 1, [0.2, 0.4],
                            curve_serializer=fake_serializer,
                            curve_task=test_data_reflector)
        # The serializer is called once for each quantile.
        self.assertEqual(2, fake_serializer.number_of_calls)

    def test_map_serializer_called_when_configured(self):
        """
        The quantile map serialization function is called when the
        POES parameter is specified in the configuration file.
        """
        def fake_serializer(*args):
            """Fake serialization function to be used in this test."""
            fake_serializer.number_of_calls += 1

        fake_serializer.number_of_calls = 0

        def fake_map_func(*args):
            return ["quantile_hazard_map!10!-122.9!38.0!0.2",
                    "quantile_hazard_map!10!-121.9!38.0!0.2",
                    "quantile_hazard_map!10!-122.8!38.0!0.4",
                    "quantile_hazard_map!10!-121.8!38.0!0.4"]

        key = helpers.TestStore.put(self.mixin.job_id, self.mock_results)
        self.keys.append(key)
        self.mixin.params["POES"] = "0.6 0.8"
        self.mixin.do_quantiles(
            self.sites, 1, [0.2, 0.4],
            curve_serializer=lambda _, __: True,
            curve_task=test_data_reflector,
            map_func=fake_map_func,
            map_serializer=fake_serializer)
        # The serializer is called once for each quantile.
        self.assertEqual(2, fake_serializer.number_of_calls)

    def test_map_serializer_not_called_unless_configured(self):
        """
        The quantile map serialization function is not called unless the
        POES parameter was specified in the configuration file.
        """

        def fake_serializer(kvs_keys):
            """Fake serialization function to be used in this test."""
            # Check that the data returned is the one we expect for the current
            # realization.
            fake_serializer.number_of_calls += 1

        fake_serializer.number_of_calls = 0

        key = helpers.TestStore.put(self.mixin.job_id, self.mock_results)
        self.keys.append(key)
        self.mixin.do_quantiles(self.sites, 1, [],
                            curve_serializer=lambda _: True,
                            curve_task=test_data_reflector,
                            map_serializer=fake_serializer)
        self.assertEqual(0, fake_serializer.number_of_calls)

    def test_missing_map_serializer_assertion(self):
        """
        When the quantile map serialization function is not set an
        `AssertionError` is raised.

        TODO: once everyone is on python rev. > 2.7 extend the test to check
        for the specific assertion message.
        """

        key = helpers.TestStore.put(self.mixin.job_id, self.mock_results)
        self.keys.append(key)
        self.mixin.params["POES"] = "0.6 0.8"
        self.assertRaises(
            AssertionError, self.mixin.do_quantiles,
            self.sites, 1, [0.5],
            curve_serializer=lambda _, __: True,
            curve_task=test_data_reflector, map_func=lambda _: [1, 2, 3])

    def test_missing_map_function_assertion(self):
        """
        When the quantile map calculation function is not set an
        `AssertionError` is raised.

        TODO: once everyone is on python rev. > 2.7 extend the test to check
        for the specific assertion message.
        """

        key = helpers.TestStore.put(self.mixin.job_id, self.mock_results)
        self.keys.append(key)
        self.mixin.params["POES"] = "0.6 0.8"
        self.assertRaises(
            AssertionError, self.mixin.do_quantiles,
            self.sites, 1, [0.5],
            curve_serializer=lambda _, __: True,
            curve_task=test_data_reflector,
            map_serializer=lambda _, __, ___: True, map_func=None)


class NumberOfTasksTestCase(helpers.TestMixin, unittest.TestCase):
    """Tests the behaviour of ClassicalMixin.number_of_tasks()."""

    def setUp(self):
        params = {'CALCULATION_MODE': 'Hazard'}

        self.mixin = self.create_job_with_mixin(params, opensha.ClassicalMixin)

    def tearDown(self):
        self.unload_job_mixin()

    def test_number_of_tasks_with_param_not_set(self):
        """
        When the `HAZARD_TASKS` parameter is not set the expected value is
        twice the number of CPUs/cores.
        """
        self.mixin.params = dict()
        self.assertEqual(
            2 * multiprocessing.cpu_count(), self.mixin.number_of_tasks())

    def test_number_of_tasks_with_param_set_and_valid(self):
        """
        When the `HAZARD_TASKS` parameter *is* set and a valid integer its
        value will be returned.
        """
        self.mixin.params = dict(HAZARD_TASKS="5")
        self.assertEqual(5, self.mixin.number_of_tasks())

    def test_number_of_tasks_with_param_set_but_invalid(self):
        """
        When the `HAZARD_TASKS` parameter is set but not a valid integer a
        `ValueError` will be raised.
        """
        self.mixin.params = dict(HAZARD_TASKS="this-is-not-a-number")
        self.assertRaises(ValueError, self.mixin.number_of_tasks)

    def test_number_of_tasks_with_param_set_but_all_whitespace(self):
        """
        When the `HAZARD_TASKS` parameter is set to whitespace a
        `ValueError` will be raised.
        """
        self.mixin.params = dict(HAZARD_TASKS=" 	")
        self.assertRaises(ValueError, self.mixin.number_of_tasks)
