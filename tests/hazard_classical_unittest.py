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
import os
import unittest

from openquake import kvs
from openquake import logs
from openquake import shapes
from openquake.calculators.hazard.classical import core as classical
from openquake.calculators.hazard.general import create_java_cache

from tests.utils.helpers import (patch, TestMixin, TestStore, demo_file,
                                 create_job)
from tests.utils.tasks import (
    test_async_data_reflector, test_compute_hazard_curve, test_data_reflector)

LOG = logs.LOG

SIMPLE_FAULT_SRC_MODEL_LT = demo_file(
    'simple_fault_demo_hazard/source_model_logic_tree.xml')
SIMPLE_FAULT_GMPE_LT = demo_file(
    'simple_fault_demo_hazard/gmpe_logic_tree.xml')
SIMPLE_FAULT_BASE_PATH = os.path.abspath(demo_file('simple_fault_demo_hazard'))


class DoCurvesTestCase(TestMixin, unittest.TestCase):
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
        params = dict(
            CALCULATION_MODE='Hazard',
            SOURCE_MODEL_LOGIC_TREE_FILE_PATH=SIMPLE_FAULT_SRC_MODEL_LT,
            GMPE_LOGIC_TREE_FILE_PATH=SIMPLE_FAULT_GMPE_LT,
            BASE_PATH=SIMPLE_FAULT_BASE_PATH)

        self.calc_proxy = create_job(params)
        self.calculator = classical.ClassicalMixin(self.calc_proxy)

        # Store the canned result data in the KVS.
        key = self.calc_proxy.job_id
        for realization in xrange(2):
            key = "%s/%s" % (self.calc_proxy.job_id, realization + 1)
            TestStore.put(key, self.mock_results[realization])
            self.keys.append(key)
        LOG.debug("keys = '%s'" % self.keys)

        self.calc_proxy.params = dict(NUMBER_OF_LOGIC_TREE_SAMPLES=2,
                                 WIDTH_OF_MFD_BIN=1)
        self.calculator.calc = self.FakeLogicTreeProcessor()
        self.calculator.cache = dict()

    def tearDown(self):
        # Remove the canned result data from the KVS.
        for key in self.keys:
            TestStore.remove(key)

    def test_serializer_called_when_passed(self):
        """The passed serialization function is called for each realization."""

        def fake_serializer(sites, realization):
            """Fake serialization function to be used in this test."""
            self.assertEqual(self.sites, sites)

            fake_serializer.number_of_calls += 1

        # We will count the number of invocations using a property of the fake
        # serializer function.
        fake_serializer.number_of_calls = 0

        self.calculator.do_curves(self.sites, 2, serializer=fake_serializer,
                             the_task=test_compute_hazard_curve)
        self.assertEqual(2, fake_serializer.number_of_calls)


class DoMeansTestCase(TestMixin, unittest.TestCase):
    """Tests the behaviour of ClassicalMixin.do_means()."""

    def __init__(self, *args, **kwargs):
        super(DoMeansTestCase, self).__init__(*args, **kwargs)
        self.keys = []
        self.sites = [shapes.Site(-121.9, 38.0), shapes.Site(-121.8, 38.0),
                      shapes.Site(-122.9, 38.0), shapes.Site(-122.8, 38.0)]

    mock_results = [
        "mean_hazard_curve!38cdc377!1!-121.9!38.0",
        "mean_hazard_curve!38cdc377!1!-121.8!38.0",
        "mean_hazard_curve!38cdc377!1!-121.7!38.0"]

    def setUp(self):
        params = dict(
            CALCULATION_MODE='Hazard',
            COMPUTE_MEAN_HAZARD_CURVE='true',
            SOURCE_MODEL_LOGIC_TREE_FILE_PATH=SIMPLE_FAULT_SRC_MODEL_LT,
            GMPE_LOGIC_TREE_FILE_PATH=SIMPLE_FAULT_GMPE_LT,
            BASE_PATH=SIMPLE_FAULT_BASE_PATH)

        self.calc_proxy = create_job(params)
        self.calculator = classical.ClassicalMixin(self.calc_proxy)

    def tearDown(self):
        # Remove the canned result data from the KVS.
        for key in self.keys:
            TestStore.remove(key)

    def test_curve_serializer_called_when_passed(self):
        """The passed mean curve serialization function is called."""

        def fake_serializer(sites):
            """Fake serialization function to be used in this test."""
            self.assertEqual(self.sites, sites)
            fake_serializer.number_of_calls += 1

        # Count the number of invocations using this property of the fake
        # serializer function.
        fake_serializer.number_of_calls = 0

        key = TestStore.put(self.calc_proxy.job_id, self.mock_results)
        self.keys.append(key)
        self.calculator.do_means(self.sites, 1,
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

        key = TestStore.put(self.calc_proxy.job_id, self.mock_results)
        self.keys.append(key)
        self.calculator.do_means(self.sites, 1,
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

        key = TestStore.put(self.calc_proxy.job_id, self.mock_results)
        self.keys.append(key)
        self.calc_proxy.params["POES"] = "0.6 0.8"
        self.calculator.do_means(self.sites, 1,
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

        key = TestStore.put(self.calc_proxy.job_id, self.mock_results)
        self.keys.append(key)
        self.calc_proxy.params["POES"] = "0.6 0.8"
        self.assertRaises(
            AssertionError, self.calculator.do_means,
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

        key = TestStore.put(self.calc_proxy.job_id, self.mock_results)
        self.keys.append(key)
        self.calc_proxy.params["POES"] = "0.6 0.8"
        self.assertRaises(
            AssertionError, self.calculator.do_means,
            self.sites, 1,
            curve_serializer=lambda _: True, curve_task=test_data_reflector,
            map_serializer=lambda _: True, map_func=None)

    def test_no_do_means_if_disabled(self):
        self.calc_proxy.params['COMPUTE_MEAN_HAZARD_CURVE'] = (
            'false')
        with patch('openquake.utils.tasks.distribute') as distribute:
            self.calculator.do_means(self.sites, 1,
                                curve_serializer=None,
                                curve_task=None)
        self.assertEqual(distribute.call_count, 0)


class DoQuantilesTestCase(TestMixin, unittest.TestCase):
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
        params = dict(
            CALCULATION_MODE='Hazard',
            SOURCE_MODEL_LOGIC_TREE_FILE_PATH=SIMPLE_FAULT_SRC_MODEL_LT,
            GMPE_LOGIC_TREE_FILE_PATH=SIMPLE_FAULT_GMPE_LT,
            BASE_PATH=SIMPLE_FAULT_BASE_PATH)

        self.calc_proxy = create_job(params)
        self.calculator = classical.ClassicalMixin(self.calc_proxy)

    def tearDown(self):
        # Remove the canned result data from the KVS.
        for key in self.keys:
            TestStore.remove(key)

    def test_curve_serializer_called_when_passed(self):
        """The passed quantile curve serialization function is called."""

        def fake_serializer(sites, quantiles):
            """Fake serialization function to be used in this test."""
            fake_serializer.number_of_calls += 1

        fake_serializer.number_of_calls = 0

        key = TestStore.put(self.calc_proxy.job_id, self.mock_results)
        self.keys.append(key)
        self.calculator.do_quantiles(self.sites, 1, [0.2, 0.4],
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

        key = TestStore.put(self.calc_proxy.job_id,
                            self.mock_results)
        self.keys.append(key)
        self.calc_proxy.params["POES"] = "0.6 0.8"
        self.calculator.do_quantiles(
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

        key = TestStore.put(self.calc_proxy.job_id, self.mock_results)
        self.keys.append(key)
        self.calculator.do_quantiles(self.sites, 1, [],
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

        key = TestStore.put(self.calc_proxy.job_id, self.mock_results)
        self.keys.append(key)
        self.calc_proxy.params["POES"] = "0.6 0.8"
        self.assertRaises(
            AssertionError, self.calculator.do_quantiles,
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

        key = TestStore.put(self.calc_proxy.job_id, self.mock_results)
        self.keys.append(key)
        self.calc_proxy.params["POES"] = "0.6 0.8"
        self.assertRaises(
            AssertionError, self.calculator.do_quantiles,
            self.sites, 1, [0.5],
            curve_serializer=lambda _, __: True,
            curve_task=test_data_reflector,
            map_serializer=lambda _, __, ___: True, map_func=None)


class NumberOfTasksTestCase(TestMixin, unittest.TestCase):
    """Tests the behaviour of ClassicalMixin.number_of_tasks()."""

    def setUp(self):
        params = dict(
            CALCULATION_MODE='Hazard',
            SOURCE_MODEL_LOGIC_TREE_FILE_PATH=SIMPLE_FAULT_SRC_MODEL_LT,
            GMPE_LOGIC_TREE_FILE_PATH=SIMPLE_FAULT_GMPE_LT,
            BASE_PATH=SIMPLE_FAULT_BASE_PATH)

        self.calc_proxy = create_job(params)

        self.calculator = classical.ClassicalMixin(self.calc_proxy)

    def test_number_of_tasks_with_param_not_set(self):
        """
        When the `HAZARD_TASKS` parameter is not set the expected value is
        twice the number of CPUs/cores.
        """
        self.calc_proxy.params = dict()
        self.assertEqual(
            2 * multiprocessing.cpu_count(), self.calculator.number_of_tasks())

    def test_number_of_tasks_with_param_set_and_valid(self):
        """
        When the `HAZARD_TASKS` parameter *is* set and a valid integer its
        value will be returned.
        """
        self.calc_proxy.params = dict(HAZARD_TASKS="5")
        self.assertEqual(5, self.calculator.number_of_tasks())

    def test_number_of_tasks_with_param_set_but_invalid(self):
        """
        When the `HAZARD_TASKS` parameter is set but not a valid integer a
        `ValueError` will be raised.
        """
        self.calc_proxy.params = dict(HAZARD_TASKS="this-is-not-a-number")
        self.assertRaises(ValueError, self.calculator.number_of_tasks)

    def test_number_of_tasks_with_param_set_but_all_whitespace(self):
        """
        When the `HAZARD_TASKS` parameter is set to whitespace a
        `ValueError` will be raised.
        """
        self.calc_proxy.params = dict(HAZARD_TASKS=" 	")
        self.assertRaises(ValueError, self.calculator.number_of_tasks)


class ClassicalExecuteTestCase(TestMixin, unittest.TestCase):
    """Tests the behaviour of ClassicalMixin.execute()."""

    def __init__(self, *args, **kwargs):
        super(ClassicalExecuteTestCase, self).__init__(*args, **kwargs)
        self.sites = [shapes.Site(-121.9, 38.0), shapes.Site(-121.8, 38.0),
                      shapes.Site(-122.9, 38.0), shapes.Site(-122.8, 38.0),
                      shapes.Site(-123.9, 38.0), shapes.Site(-123.8, 38.0),
                      shapes.Site(-124.9, 38.0), shapes.Site(-124.8, 38.0)]
        self.methods = dict()
        self.patchers = []

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
        params = dict(
            CALCULATION_MODE='Hazard',
            NUMBER_OF_LOGIC_TREE_SAMPLES=2,
            WIDTH_OF_MFD_BIN=1,
            SOURCE_MODEL_LOGIC_TREE_FILE_PATH=SIMPLE_FAULT_SRC_MODEL_LT,
            GMPE_LOGIC_TREE_FILE_PATH=SIMPLE_FAULT_GMPE_LT,
            BASE_PATH=SIMPLE_FAULT_BASE_PATH,
            SITES=('38.0, -121.9, 38.0, -121.8, 38.0, -122.9, 38.0, -122.8 '
                   '38.0, -123.9, 38.0, -123.8, 38.0, -124.9, 38.0, -124.8'))

        self.calc_proxy = create_job(params)
        self.calculator = classical.ClassicalMixin(self.calc_proxy)

        # Initialize the mixin instance.
        self.calculator.calc = self.FakeLogicTreeProcessor()
        self.calculator.cache = dict()
        for method in ["do_curves", "do_means", "do_quantiles"]:
            self.methods[method] = getattr(self.calculator, method)
            setattr(self.calculator, method,
                    mock.mocksignature(self.methods[method]))
        patcher = patch("openquake.utils.config.hazard_block_size")
        patcher.start().return_value = 3
        self.patchers.append(patcher)

    def tearDown(self):
        for patcher in self.patchers:
            patcher.stop()
        for method, original in self.methods.iteritems():
            setattr(self.calculator, method, original)

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
        with patch("openquake.input.logictree.LogicTreeProcessor"):
            self.calculator.execute()
            for method in self.methods:
                mmock = getattr(self.calculator, method).mock
                self.assertEqual(3, mmock.call_count)
                for idx, data_len in enumerate([3, 3, 2]):
                    # Get the arguments for an invocation identified by `idx`.
                    args = mmock.call_args_list[idx][0]
                    self.assertEqual(data_slices[idx], args[0])

    def test_release_data_from_kvs_called(self):
        """Make sure execute() calls release_data_from_kvs() properly.

        We have 8 sites and a block size (`HAZARD_BLOCK_SIZE`) of 3 i.e.
        the methods called by execute() will
            - be called three times
            - get passed 3, 3 and 2 sites on the 1st, 2nd and 3rd invocation
              respectively.
        """
        data_slices = [self.sites[:3], self.sites[3:6], self.sites[6:]]
        # Make sure no real logic is invoked.
        with patch("openquake.input.logictree.LogicTreeProcessor"):
            with patch("openquake.calculators.hazard.classical.core"
                       ".release_data_from_kvs") as m:
                self.calculator.execute()
                self.assertEqual(3, m.call_count)
                for idx, data_len in enumerate([3, 3, 2]):
                    # Get the arguments for an invocation identified by `idx`.
                    args = m.call_args_list[idx][0]
                    self.assertEqual(data_slices[idx], args[1])


class ReleaseDataFromKvsTestCase(TestMixin, unittest.TestCase):
    """Tests the behaviour of classical.release_data_from_kvs()."""

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
        classical.release_data_from_kvs(job_id, *self.ARGS)
        self.assertFalse(self._keys_found(job_id, keys))

    def test_curve_data(self):
        """Hazard curve data is purged correctly."""
        # example: ::JOB::%s::!hazard_curve_poes!0!-4803231368264023776
        kt = "::JOB::%%s::!hazard_curve_poes!%s!"
        keys = []
        for sample in range(self.REALIZATIONS):
            skt = kt % sample
            keys.extend(skt + str(hash(s)) for s in self.SITES)
        self._test(keys, 1)

    def test_mean_curve_data(self):
        """Mean hazard curve data is purged correctly."""
        # example: ::JOB::%s::!mean_hazard_curve!-1656082506525860821
        kt = "::JOB::%%s::!mean_hazard_curve!%s"
        keys = [kt % hash(s) for s in self.SITES]
        self._test(keys, 2)

    def test_quantile_curve_data(self):
        """Quantile hazard curve data is purged correctly."""
        # example: ::JOB::%s::!quantile_hazard_curve!-1656082506525860821!0.25
        kt = "::JOB::%%s::!quantile_hazard_curve!%s!"
        keys = []
        skeys = [kt % hash(s) for s in self.SITES]
        for skey in skeys:
            keys.extend(skey + str(quantile) for quantile in self.QUANTILES)
        self._test(keys, 3)

    def test_mean_map_data(self):
        """Mean hazard map data is purged correctly."""
        # example: ::JOB::%s::!mean_hazard_map!-1656082506525860821!0.01
        kt = "::JOB::%%s::!mean_hazard_map!%s!"
        keys = []
        skeys = [kt % hash(s) for s in self.SITES]
        for skey in skeys:
            keys.extend(skey + str(poe) for poe in self.POES)
        self._test(keys, 4)

    def test_quantile_map_data(self):
        """Quantile hazard map data is purged correctly."""
        # example:
        #   ::JOB::%s::!quantile_hazard_map!-1656082506525860821!0.01!0.25
        kt = "::JOB::%%s::!quantile_hazard_map!%s!"
        keys = []
        skeys = [kt % hash(s) for s in self.SITES]
        for skey in skeys:
            for poe in self.POES:
                pkey = skey + str(poe) + '!'
                for quantile in self.QUANTILES:
                    keys.append(pkey + str(quantile))
        self._test(keys, 5)


class CreateJavaCacheTestCase(TestMixin, unittest.TestCase):
    """Tests the behaviour of
    :function:`openquake.calculators.hazard.general.create_java_cache`."""

    class Fake(object):
        """Fake calculator class."""
        def __init__(self):
            self.cache = None

        @create_java_cache
        def calculate1(self):
            """Fake calculator method."""
            return self.cache

        @create_java_cache
        def calculate2(self):
            """Fake calculator method."""
            return self.cache

    def test_create_java_cache(self):
        """The cache is instantiated."""
        fake = self.Fake()
        self.assertIs(None, fake.cache)
        result = fake.calculate1()
        self.assertIs(result, fake.cache)

    def test_create_java_cache_same_instance_used(self):
        """The cache is instantiated and used for all decorated functions."""
        fake = self.Fake()
        with patch("openquake.kvs.cache_connections") as mfunc:
            mfunc.return_value = True
            result1 = fake.calculate1()
            result2 = fake.calculate2()
            self.assertIs(result1, result2)

    def test_create_java_cache_without_caching(self):
        """
        Different `Cache` instances are used when kvs connection caching is
        turned off.
        """
        fake = self.Fake()
        with patch("openquake.kvs.cache_connections") as mfunc:
            mfunc.return_value = False
            result1 = fake.calculate1()
            result2 = fake.calculate2()
            self.assertIsNot(result1, result2)
