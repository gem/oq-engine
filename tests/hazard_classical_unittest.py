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

import mock
import multiprocessing
import unittest

from openquake import kvs
from openquake import logs
from openquake import shapes

from openquake.hazard import opensha

from tests.utils import helpers
from tests.utils.tasks import (
    test_async_data_reflector, test_compute_hazard_curve, test_data_reflector)

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
        def sample_and_save_source_model_logictree(self, cache, key, seed,
                                                   bin_width):
            """Do nothing."""

        def sample_and_save_gmpe_logictree(self, cache, key, seed):
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
        self.mixin.params = dict(NUMBER_OF_LOGIC_TREE_SAMPLES=2,
                                 WIDTH_OF_MFD_BIN=1)
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
                        curve_task=test_async_data_reflector)
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

    def test_no_do_means_if_disabled(self):
        self.mixin.params['COMPUTE_MEAN_HAZARD_CURVE'] = 'false'
        with helpers.patch('openquake.utils.tasks.distribute') as distribute:
            self.mixin.do_means(self.sites, 1,
                                curve_serializer=None,
                                curve_task=None)
        self.assertEqual(distribute.call_count, 0)


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

        def fake_serializer(sites, quantiles):
            """Fake serialization function to be used in this test."""
            fake_serializer.number_of_calls += 1

        fake_serializer.number_of_calls = 0

        key = helpers.TestStore.put(self.mixin.job_id, self.mock_results)
        self.keys.append(key)
        self.mixin.do_quantiles(self.sites, 1, [0.2, 0.4],
                            curve_serializer=fake_serializer,
                            curve_task=test_async_data_reflector)
        # The serializer is called only once (for all quantiles).
        self.assertEqual(1, fake_serializer.number_of_calls)

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


class ClassicalExecuteTestCase(helpers.TestMixin, unittest.TestCase):
    """Tests the behaviour of ClassicalMixin.execute()."""

    def __init__(self, *args, **kwargs):
        super(ClassicalExecuteTestCase, self).__init__(*args, **kwargs)
        self.sites = [shapes.Site(-121.9, 38.0), shapes.Site(-121.8, 38.0),
                      shapes.Site(-122.9, 38.0), shapes.Site(-122.8, 38.0),
                      shapes.Site(-123.9, 38.0), shapes.Site(-123.8, 38.0),
                      shapes.Site(-124.9, 38.0), shapes.Site(-124.8, 38.0)]
        self.methods = dict()

    class FakeLogicTreeProcessor(object):
        """
        Fake logic tree processor class. This test will not manipulate any
        logic trees.
        """
        def sample_and_save_source_model_logictree(self, cache, key, seed,
                                                   bin_width):
            """Do nothing."""

        def sample_and_save_gmpe_logictree(self, cache, key, seed):
            """Do nothing."""

    def setUp(self):
        self.mixin = self.create_job_with_mixin({'CALCULATION_MODE': 'Hazard'},
                                                opensha.ClassicalMixin)
        # Initialize the mixin instance.
        self.mixin.params = dict(NUMBER_OF_LOGIC_TREE_SAMPLES=2,
                                 WIDTH_OF_MFD_BIN=1, HAZARD_BLOCK_SIZE=3)
        self.mixin.calc = self.FakeLogicTreeProcessor()
        self.mixin.cache = dict()
        self.mixin.sites = self.sites
        for method in ["do_curves", "do_means", "do_quantiles"]:
            self.methods[method] = getattr(self.mixin, method)
            setattr(self.mixin, method,
                    mock.mocksignature(self.methods[method]))

    def tearDown(self):
        for method, original in self.methods.iteritems():
            setattr(self.mixin, method, original)
        self.unload_job_mixin()

    def test_invocations(self):
        """Make sure execute() calls the methods properly.

        We have 8 sites and a block size (`HAZARD_BLOCK_SIZE`) of 3 i.e.
        the methods called by execute() will
            - be called three times
            - get passed 3, 3 and 2 sites on the 1st, 2nd and 3rd invocation
              respectively.
        """
        data_slices = [self.sites[:3], self.sites[3:6], self.sites[6:]]
        # Make sure no real logic is invoked.
        with helpers.patch('openquake.input.logictree.LogicTreeProcessor'):
            self.mixin.execute()
            for method in self.methods:
                mock = getattr(self.mixin, method).mock
                self.assertEqual(3, mock.call_count)
                for idx, data_len in enumerate([3, 3, 2]):
                    # Get the arguments for an invocation identified by `idx`.
                    args = mock.call_args_list[idx][0]
                    self.assertEqual(data_slices[idx], args[0])


class ReleaseDataFromKvsTestCase(helpers.TestMixin, unittest.TestCase):
    """Tests the behaviour of opensha.release_data_from_kvs()."""

    SITES = [shapes.Site(-118.3, 33.76), shapes.Site(-118.2, 33.76),
             shapes.Site(-118.1, 33.76), shapes.Site(-118.3, 33.86),
             shapes.Site(-118.2, 33.86), shapes.Site(-118.1, 33.86)]
    REALIZATIONS = 2
    POES = [0.01, 0.1]
    QUANTILES = [0.25, 0.5]
    ARGS = (SITES, REALIZATIONS, QUANTILES, POES, None)

    def _populate_data_in_kvs(self, job_id, keys):
        """Load the data to be purged into the kvs."""
        conn = kvs.get_client()
        for idx, key in enumerate(keys):
            conn.set(key % job_id, idx + 1)

    def _keys_found(self, job_id, keys):
        """Return the keys found in kvs."""
        result = []
        conn = kvs.get_client()
        for key in keys:
            key %= job_id
            if conn.get(key) is not None:
                result.append(key)
        return result

    def _test(self, keys, job_id):
        """Perform the actual test.

        This involves
            1 - populating the kvs with the keys passed
            2 - making sure step 1 worked
            3 - calling the function under test (release_data_from_kvs())
            4 - ascertaining the keys in question have been purged from kvs.
        """
        self._populate_data_in_kvs(job_id, keys)
        self.assertEqual(sorted(k % job_id for k in keys),
                         sorted(self._keys_found(job_id, keys)))
        opensha.release_data_from_kvs(job_id, *self.ARGS)
        self.assertFalse(self._keys_found(job_id, keys))

    def test_curve_data(self):
        """Hazard curve data is purged correctly."""
        keys = [
            "::JOB::%s::!hazard_curve_poes!0!-1656082506525860821",
            "::JOB::%s::!hazard_curve_poes!0!-3197290148354731068",
            "::JOB::%s::!hazard_curve_poes!0!-3431201036734844224",
            "::JOB::%s::!hazard_curve_poes!0!-4803231368264023776",
            "::JOB::%s::!hazard_curve_poes!0!6691116160089896596",
            "::JOB::%s::!hazard_curve_poes!0!-9103945534382545143",
            "::JOB::%s::!hazard_curve_poes!1!-1656082506525860821",
            "::JOB::%s::!hazard_curve_poes!1!-3197290148354731068",
            "::JOB::%s::!hazard_curve_poes!1!-3431201036734844224",
            "::JOB::%s::!hazard_curve_poes!1!-4803231368264023776",
            "::JOB::%s::!hazard_curve_poes!1!6691116160089896596",
            "::JOB::%s::!hazard_curve_poes!1!-9103945534382545143"]
        self._test(keys, 1)

    def test_mean_curve_data(self):
        """Mean hazard curve data is purged correctly."""
        keys = [
            "::JOB::%s::!mean_hazard_curve!-1656082506525860821",
            "::JOB::%s::!mean_hazard_curve!-3197290148354731068",
            "::JOB::%s::!mean_hazard_curve!-3431201036734844224",
            "::JOB::%s::!mean_hazard_curve!-4803231368264023776",
            "::JOB::%s::!mean_hazard_curve!6691116160089896596",
            "::JOB::%s::!mean_hazard_curve!-9103945534382545143"]
        self._test(keys, 2)

    def test_quantile_curve_data(self):
        """Quantile hazard curve data is purged correctly."""
        keys = [
            "::JOB::%s::!quantile_hazard_curve!-1656082506525860821!0.25",
            "::JOB::%s::!quantile_hazard_curve!-1656082506525860821!0.5",
            "::JOB::%s::!quantile_hazard_curve!-3197290148354731068!0.25",
            "::JOB::%s::!quantile_hazard_curve!-3197290148354731068!0.5",
            "::JOB::%s::!quantile_hazard_curve!-3431201036734844224!0.25",
            "::JOB::%s::!quantile_hazard_curve!-3431201036734844224!0.5",
            "::JOB::%s::!quantile_hazard_curve!-4803231368264023776!0.25",
            "::JOB::%s::!quantile_hazard_curve!-4803231368264023776!0.5",
            "::JOB::%s::!quantile_hazard_curve!6691116160089896596!0.25",
            "::JOB::%s::!quantile_hazard_curve!6691116160089896596!0.5",
            "::JOB::%s::!quantile_hazard_curve!-9103945534382545143!0.25",
            "::JOB::%s::!quantile_hazard_curve!-9103945534382545143!0.5"]
        self._test(keys, 3)

    def test_mean_map_data(self):
        """Mean hazard map data is purged correctly."""
        keys = [
            "::JOB::%s::!mean_hazard_map!-1656082506525860821!0.01",
            "::JOB::%s::!mean_hazard_map!-1656082506525860821!0.1",
            "::JOB::%s::!mean_hazard_map!-3197290148354731068!0.01",
            "::JOB::%s::!mean_hazard_map!-3197290148354731068!0.1",
            "::JOB::%s::!mean_hazard_map!-3431201036734844224!0.01",
            "::JOB::%s::!mean_hazard_map!-3431201036734844224!0.1",
            "::JOB::%s::!mean_hazard_map!-4803231368264023776!0.01",
            "::JOB::%s::!mean_hazard_map!-4803231368264023776!0.1",
            "::JOB::%s::!mean_hazard_map!6691116160089896596!0.01",
            "::JOB::%s::!mean_hazard_map!6691116160089896596!0.1",
            "::JOB::%s::!mean_hazard_map!-9103945534382545143!0.01",
            "::JOB::%s::!mean_hazard_map!-9103945534382545143!0.1"]
        self._test(keys, 4)

    def test_quantile_map_data(self):
        """Quantile hazard map data is purged correctly."""
        keys = [
            "::JOB::%s::!quantile_hazard_map!-1656082506525860821!0.01!0.25",
            "::JOB::%s::!quantile_hazard_map!-1656082506525860821!0.01!0.5",
            "::JOB::%s::!quantile_hazard_map!-1656082506525860821!0.1!0.25",
            "::JOB::%s::!quantile_hazard_map!-1656082506525860821!0.1!0.5",
            "::JOB::%s::!quantile_hazard_map!-3197290148354731068!0.01!0.25",
            "::JOB::%s::!quantile_hazard_map!-3197290148354731068!0.01!0.5",
            "::JOB::%s::!quantile_hazard_map!-3197290148354731068!0.1!0.25",
            "::JOB::%s::!quantile_hazard_map!-3197290148354731068!0.1!0.5",
            "::JOB::%s::!quantile_hazard_map!-3431201036734844224!0.01!0.25",
            "::JOB::%s::!quantile_hazard_map!-3431201036734844224!0.01!0.5",
            "::JOB::%s::!quantile_hazard_map!-3431201036734844224!0.1!0.25",
            "::JOB::%s::!quantile_hazard_map!-3431201036734844224!0.1!0.5",
            "::JOB::%s::!quantile_hazard_map!-4803231368264023776!0.01!0.25",
            "::JOB::%s::!quantile_hazard_map!-4803231368264023776!0.01!0.5",
            "::JOB::%s::!quantile_hazard_map!-4803231368264023776!0.1!0.25",
            "::JOB::%s::!quantile_hazard_map!-4803231368264023776!0.1!0.5",
            "::JOB::%s::!quantile_hazard_map!6691116160089896596!0.01!0.25",
            "::JOB::%s::!quantile_hazard_map!6691116160089896596!0.01!0.5",
            "::JOB::%s::!quantile_hazard_map!6691116160089896596!0.1!0.25",
            "::JOB::%s::!quantile_hazard_map!6691116160089896596!0.1!0.5",
            "::JOB::%s::!quantile_hazard_map!-9103945534382545143!0.01!0.25",
            "::JOB::%s::!quantile_hazard_map!-9103945534382545143!0.01!0.5",
            "::JOB::%s::!quantile_hazard_map!-9103945534382545143!0.1!0.25",
            "::JOB::%s::!quantile_hazard_map!-9103945534382545143!0.1!0.5"]
        self._test(keys, 5)
