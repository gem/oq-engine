# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

import os
import unittest
import geohash
import numpy
import subprocess

from nose.plugins.attrib import attr

from openquake.db import models
from openquake import shapes
from tests.utils import helpers


def load_expected_map(path):
    """Load expected map data from the given expected results file. Map data
    are expected to be stored in a space-delimited table form. The table
    columns are expected to be ordered ``lat lon value``.

    :param path:
        Path to the expected results file.
    :returns:
        A dict of map values (as floats), keyed by a :class:`shapes.Site`
        object.
    """
    map_data = {}

    for line in open(path):
        lat, lon, value = line.split()
        map_data[shapes.Site(lat, lon)] = float(value)

    return map_data


def run_job(config_file):
    """Given a path to a config file, run openquake as a separate process using
    `subprocess`.

    This function blocks until the openquake job has concluded.

    :returns:
        The return code of the subprocess.
    """
    return subprocess.call(["bin/openquake", "--config_file=" + config_file])


class ClassicalPSHACalculatorAssuranceTestCase(
    unittest.TestCase, helpers.DbTestMixin):

    job = None

    def tearDown(self):
        self.teardown_job(self.job)
        self.job = None

    @attr("qa")
    def test_peer_test_set_1_case_2(self):
        expected_results = self._load_results("PeerTestSet1Case2")

        run_job(helpers.demo_file(
            os.path.join("PeerTestSet1Case2", "config.gem")))

        self._assert_hazcurve_results_are(expected_results)

    @attr("qa")
    def test_peer_test_set_1_case_5(self):
        expected_results = self._load_results("PeerTestSet1Case5")

        run_job(helpers.demo_file(
            os.path.join("PeerTestSet1Case5", "config.gem")))

        self._assert_hazcurve_results_are(expected_results)

    @attr("qa")
    def test_peer_test_set_1_case_8a(self):
        expected_results = self._load_results("PeerTestSet1Case8a")

        run_job(helpers.demo_file(
            os.path.join("PeerTestSet1Case8a", "config.gem")))

        self._assert_hazcurve_results_are(expected_results)

    @attr("qa")
    def test_peer_test_set_1_case_10(self):
        expected_results = self._load_results("PeerTestSet1Case10")

        run_job(helpers.demo_file(
            os.path.join("PeerTestSet1Case10", "config.gem")))

        self._assert_hazcurve_results_are(expected_results)

    @attr("qa")
    def test_hazard_map_test(self):
        path = helpers.demo_file(os.path.join("HazardMapTest",
            "expected_results", "meanHazardMap0.1.dat"))

        expected_map = load_expected_map(path)

        run_job(helpers.demo_file(
            os.path.join("HazardMapTest", "config.gem")))

        self.job = models.OqJob.objects.latest("id")

        for site, value in expected_map.items():
            gh = geohash.encode(site.latitude, site.longitude, precision=12)

            hm_db = models.HazardMapData.objects.filter(
                hazard_map__output__oq_job=self.job,
                hazard_map__statistic_type="mean",
                hazard_map__poe=0.1).extra(
                where=["ST_GeoHash(location, 12) = %s"], params=[gh]).get()

            self.assertTrue(numpy.allclose(numpy.array(value),
                    numpy.array(hm_db.value)))

    def _assert_hazcurve_results_are(self, expected_results):
        """Compare the expected hazard curve results with the results
        computed by the current job."""

        self.job = models.OqJob.objects.latest("id")

        for site, curve in expected_results.items():
            gh = geohash.encode(site.latitude, site.longitude, precision=12)

            hc_db = models.HazardCurveData.objects.filter(
                hazard_curve__output__oq_job=self.job,
                hazard_curve__statistic_type="mean").extra(
                where=["ST_GeoHash(location, 12) = %s"], params=[gh]).get()

            self._assert_curve_is(
                curve, zip(self.job.oq_params.imls, hc_db.poes), 0.005)

    def _assert_curve_is(self, expected, actual, tolerance):
        self.assertTrue(numpy.allclose(
                numpy.array(expected), numpy.array(actual), atol=tolerance),
                "Expected %s within a tolerance of %s, but was %s"
                % (expected, tolerance, actual))


    def _load_results(self, test_name):
        """Return the hazard curves read from the expected_results/ dir.

        :returns: the expected hazard curves.
        :rtype: :py:class:`dict` where each key is an instance of
            :py:class:`openquake.shapes.Site` and each value is a list
            of (IML, PoE) tuples
        """

        # split the x string and get
        # the value at index y casted to float
        get = lambda x, y: float(x.split(",")[y])

        results_dir = helpers.demo_file(
            os.path.join(test_name, "expected_results"))

        results_files = os.listdir(results_dir)

        results = {}

        for result_file in results_files:
            path = os.path.join(results_dir, result_file)

            with open(path) as hazard_curve:
                lines = hazard_curve.readlines()
                coords = lines.pop(0)

                # the format is latitude,longitude
                site = shapes.Site(get(coords, 1), get(coords, 0))

                results[site] = []

                for pair in lines:
                    # the format is IML,PoE
                    results[site].append((get(pair, 0), get(pair, 1)))

        return results
