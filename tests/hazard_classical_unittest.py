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

import unittest

from openquake import job
from openquake import logs
from openquake import shapes

from openquake.hazard import opensha

from tests.utils import helpers
from tests.utils.tasks import test_compute_hazard_curve, test_data_reflector

LOG = logs.LOG

class DoCurvesTestCase(unittest.TestCase):
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
            "Do nothing."

        def sampleAndSaveGMPETree(self, cache, key, seed):
            "Do nothing."

    mock_results = [
        [
            'hazard_curve!38cdc377!1!-121.9!38.0',
            'hazard_curve!38cdc377!1!-121.8!38.0',
            'hazard_curve!38cdc377!1!-121.7!38.0'],
        [
            'hazard_curve!38cdc377!2!-121.9!38.0',
            'hazard_curve!38cdc377!2!-121.8!38.0',
            'hazard_curve!38cdc377!2!-121.7!38.0']]

    def setUp(self):
        self.mixin = opensha.ClassicalMixin(
            job.Job(dict()), opensha.ClassicalMixin, "hazard")
        # Store the canned result data in the KVS.
        key = self.mixin.id = helpers.TestStore.nextkey()
        self.keys.append(key)
        for realization in xrange(2):
            key = "%s/%s" % (self.mixin.id, realization + 1)
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

    def test_serializer_called_when_passed(self):
        """The passed serialization function is called for each realization."""

        def fake_serializer(kvs_keys):
            """Fake serialization function to be used in this test."""
            # Check that the data returned is the one we expect for the current
            # realization.
            self.assertEqual(
                self.mock_results[fake_serializer.number_of_calls], kvs_keys)
            fake_serializer.number_of_calls += 1

        # We will count the number of invocations using a property of the fake
        # serializer function.
        fake_serializer.number_of_calls = 0

        self.mixin.do_curves(self.sites, serializer=fake_serializer,
                             the_task=test_compute_hazard_curve)
        self.assertEqual(2, fake_serializer.number_of_calls)


class DoMeansTestCase(unittest.TestCase):
    """Tests the behaviour of ClassicalMixin.do_means()."""

    def __init__(self, *args, **kwargs):
        super(DoMeansTestCase, self).__init__(*args, **kwargs)
        self.keys = []
        self.sites = [shapes.Site(-121.9, 38.0), shapes.Site(-121.8, 38.0),
                      shapes.Site(-122.9, 38.0), shapes.Site(-122.8, 38.0)]

    mock_results = [
        'mean_hazard_curve!38cdc377!1!-121.9!38.0',
        'mean_hazard_curve!38cdc377!1!-121.8!38.0',
        'mean_hazard_curve!38cdc377!1!-121.7!38.0']

    def setUp(self):
        self.mixin = opensha.ClassicalMixin(
            job.Job(dict()), opensha.ClassicalMixin, "hazard")
        # Store the canned result data in the KVS.
        key = self.mixin.id = helpers.TestStore.add(self.mock_results)
        self.keys.append(key)
        # Initialize the mixin instance.
        self.mixin.params = dict(COMPUTE_MEAN_HAZARD_CURVE="True")

    def tearDown(self):
        # Remove the canned result data from the KVS.
        for key in self.keys:
            helpers.TestStore.remove(key)

    def test_curve_serializer_called_when_passed(self):
        """The passed mean curve serialization function is called."""

        def fake_serializer(kvs_keys):
            """Fake serialization function to be used in this test."""
            # Check that the data returned is the one we expect for the current
            # realization.
            self.assertEqual(self.mock_results, kvs_keys)
            fake_serializer.number_of_calls += 1

        # Count the number of invocations using this property of the fake
        # serializer function.
        fake_serializer.number_of_calls = 0

        self.mixin.do_means(self.sites, curve_serializer=fake_serializer,
                            curve_task=test_data_reflector)
        self.assertEqual(1, fake_serializer.number_of_calls)

    def test_map_serializer_not_called_unless_configured(self):
        """
        The mean map serialization function is not called unless the
        POES_HAZARD_MAPS parameter was specified in the configuration file.
        """

        def fake_serializer(kvs_keys):
            """Fake serialization function to be used in this test."""
            # Check that the data returned is the one we expect for the current
            # realization.
            fake_serializer.number_of_calls += 1

        fake_serializer.number_of_calls = 0

        self.mixin.do_means(self.sites, curve_serializer=lambda _: True,
                            curve_task=test_data_reflector,
                            map_serializer=fake_serializer)
        self.assertEqual(0, fake_serializer.number_of_calls)

    def test_map_serializer_called_when_configured(self):
        """
        The mean map serialization function is called when the POES_HAZARD_MAPS
        parameter is specified in the configuration file.
        """

        fake_map_keys = list(xrange(3))

        def fake_serializer(kvs_keys):
            """Fake serialization function to be used in this test."""
            # Check that the data returned is the one we expect for the current
            # realization.
            self.assertEqual(fake_map_keys, kvs_keys)
            fake_serializer.number_of_calls += 1

        fake_serializer.number_of_calls = 0

        self.mixin.params["POES_HAZARD_MAPS"] = "0.6 0.8"
        self.mixin.do_means(
            self.sites, curve_serializer=lambda _: True,
            curve_task=test_data_reflector, map_serializer=fake_serializer,
            map_func=lambda _: fake_map_keys)
        self.assertEqual(1, fake_serializer.number_of_calls)

    def test_missing_map_serializer_assertion(self):
        """
        When the mean map serialization function is not set an `AssertionError`
        is raised.

        TODO: once everyone is on python rev. > 2.7 extend the test to check
        for the specific assertion message.
        """

        self.mixin.params["POES_HAZARD_MAPS"] = "0.6 0.8"
        self.assertRaises(
            AssertionError, self.mixin.do_means,
            self.sites, curve_serializer=lambda _: True,
            curve_task=test_data_reflector, map_func=lambda _: [1, 2, 3])

    def test_missing_map_function_assertion(self):
        """
        When the mean map calculation function is not set an `AssertionError`
        is raised.

        TODO: once everyone is on python rev. > 2.7 extend the test to check
        for the specific assertion message.
        """

        self.mixin.params["POES_HAZARD_MAPS"] = "0.6 0.8"
        self.assertRaises(
            AssertionError, self.mixin.do_means, self.sites,
            curve_serializer=lambda _: True, curve_task=test_data_reflector,
            map_serializer=lambda _: True, map_func=None)


class DoQuantilesTestCase(unittest.TestCase):
    """Tests the behaviour of ClassicalMixin.do_quantiles()."""

    def __init__(self, *args, **kwargs):
        super(DoQuantilesTestCase, self).__init__(*args, **kwargs)
        self.keys = []
        self.sites = [shapes.Site(-121.9, 38.0), shapes.Site(-121.8, 38.0),
                      shapes.Site(-122.9, 38.0), shapes.Site(-122.8, 38.0)]

    mock_results = [
        'quantile_hazard_curve!10!-121.9!38.0!0.2',
        'quantile_hazard_curve!10!-122.9!38.0!0.2',
        'quantile_hazard_curve!10!-121.8!38.0!0.4',
        'quantile_hazard_curve!10!-122.8!38.0!0.4']

    def setUp(self):
        self.mixin = opensha.ClassicalMixin(
            job.Job(dict()), opensha.ClassicalMixin, "hazard")
        # Store the canned result data in the KVS.
        key = self.mixin.id = helpers.TestStore.nextkey()
        helpers.TestStore.put(key, self.mock_results)
        self.keys.append(key)
        # Initialize the mixin instance.
        self.mixin.params = dict()

    def tearDown(self):
        # Remove the canned result data from the KVS.
        for key in self.keys:
            helpers.TestStore.remove(key)

    @staticmethod
    def expected(data, run):
        start = run*2
        return data[start:start+2]

    def test_curve_serializer_called_when_passed(self):
        """The passed quantile curve serialization function is called."""
        mock_data = [
            'quantile_hazard_curve!10!-122.9!38.0!0.2',
            'quantile_hazard_curve!10!-121.9!38.0!0.2',
            'quantile_hazard_curve!10!-122.8!38.0!0.4',
            'quantile_hazard_curve!10!-121.8!38.0!0.4']

        def fake_serializer(kvs_keys):
            """Fake serialization function to be used in this test."""
            # Check that the data returned is the one we expect for the current
            # realization.
            self.assertEqual(
                self.expected(mock_data, fake_serializer.number_of_calls),
                kvs_keys)
            fake_serializer.number_of_calls += 1

        fake_serializer.number_of_calls = 0

        self.mixin.do_quantiles(self.sites, curve_serializer=fake_serializer,
                                curve_task=test_data_reflector)
        self.assertEqual(2, fake_serializer.number_of_calls)

    def test_map_serializer_called_when_configured(self):
        """
        The quantile map serialization function is called when the
        POES_HAZARD_MAPS parameter is specified in the configuration file.
        """
        mock_data = [
            'quantile_hazard_map!10!-122.9!38.0!0.2',
            'quantile_hazard_map!10!-121.9!38.0!0.2',
            'quantile_hazard_map!10!-122.8!38.0!0.4',
            'quantile_hazard_map!10!-121.8!38.0!0.4']

        def fake_serializer(kvs_keys):
            """Fake serialization function to be used in this test."""
            # Check that the data returned is the one we expect for the current
            # realization.
            self.assertEqual(
                self.expected(mock_data, fake_serializer.number_of_calls),
                list(reversed(kvs_keys)))
            fake_serializer.number_of_calls += 1

        fake_serializer.number_of_calls = 0

        self.mixin.params["POES_HAZARD_MAPS"] = "0.6 0.8"
        self.mixin.do_quantiles(
            self.sites, curve_serializer=lambda _: True,
            curve_task=test_data_reflector, map_serializer=fake_serializer,
            map_func=lambda _: mock_data)
        self.assertEqual(2, fake_serializer.number_of_calls)

    def test_map_serializer_not_called_unless_configured(self):
        """
        The quantile map serialization function is not called unless the
        POES_HAZARD_MAPS parameter was specified in the configuration file.
        """

        def fake_serializer(kvs_keys):
            """Fake serialization function to be used in this test."""
            # Check that the data returned is the one we expect for the current
            # realization.
            fake_serializer.number_of_calls += 1

        fake_serializer.number_of_calls = 0

        self.mixin.do_quantiles(self.sites, curve_serializer=lambda _: True,
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

        self.mixin.params["POES_HAZARD_MAPS"] = "0.6 0.8"
        self.assertRaises(
            AssertionError, self.mixin.do_quantiles,
            self.sites, curve_serializer=lambda _: True,
            curve_task=test_data_reflector, map_func=lambda _: [1, 2, 3])

    def test_missing_map_function_assertion(self):
        """
        When the quantile map calculation function is not set an
        `AssertionError` is raised.

        TODO: once everyone is on python rev. > 2.7 extend the test to check
        for the specific assertion message.
        """

        self.mixin.params["POES_HAZARD_MAPS"] = "0.6 0.8"
        self.assertRaises(
            AssertionError, self.mixin.do_quantiles, self.sites,
            curve_serializer=lambda _: True, curve_task=test_data_reflector,
            map_serializer=lambda _: True, map_func=None)
