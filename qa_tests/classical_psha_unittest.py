# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2012, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

from collections import defaultdict
from lxml import etree
from nose.plugins.attrib import attr
import geohash
import numpy
import os
import shutil
import unittest

from openquake.db import models
from openquake import shapes
from openquake.utils import stats

from tests.utils import helpers


def load_exp_hazcurve_results(test_name):
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
        if not (result_file.startswith('site')
                and result_file.endswith('.dat')):
            continue

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


def verify_hazcurve_results(
    tc, job, exp_results_file, end_branch_label=None, statistic_type=None):
    """Given a job, a path to an expected results file, and a few optional
    parameters (end_branch_label and statistic_type), load in expected results
    from the text file and compare the data to the results in the database.

    :param tc:
        :class:`unittest.TestCase` object (for test assertions).
    :param job:
        :class:`openquake.job.Job` instance
    :param exp_results_file:
        Path to the expected results file (text file).
    :param int end_branch_label:
        Optional. Can specified if we need to query the database for hazard
        curve data for a particular end branch label/sample.
    :param statistic_type:
        Optional. Can be 'mean', 'quantile', etc. Defaults to `None`.
    """
    curve_data = open(exp_results_file, 'r').readlines()

    # The actual curve data;
    # Pairs of (site_coords, poes) for each curve:
    sites_poes = zip(curve_data[::2], curve_data[1::2])

    for site, poes in sites_poes:
        # lon, lat is the order which GML uses for coord pairs.
        lon, lat = [float(x) for x in site.split()]
        poes = [float(x) for x in poes.split()]

        # Pay attention to the lat, lon ordering here;
        # It's reversed from above.
        gh = geohash.encode(lat, lon)

        hc = models.HazardCurveData.objects.filter(
            hazard_curve__output__oq_job=job,
            hazard_curve__end_branch_label=end_branch_label,
            hazard_curve__statistic_type=statistic_type).extra(
                where=["ST_GeoHash(location, 12) = %s"],
                params=[gh]).get()

        tc.assertTrue(numpy.allclose(poes, hc.poes))


def verify_hazcurve_nrml(tc, nrml_path, exp_results_file):
    """
    Given a NRML path and a path to an expected results file, load the
    expected hazard curve results from the latter and compare them with the
    data contained in the NRML file.

    :param tc: :class:`unittest.TestCase` object (for test assertions).
    :param string nrml_path: path to the nrml file to check
    :param string exp_results_file: path to the expected results file
    """
    root = etree.parse(nrml_path)
    hcns = root.xpath("//ns:HCNode",
                      namespaces={"ns": "http://openquake.org/xmlns/nrml/0.3"})

    # Example "-122.7 47.8": [0.0850461222404, .., 0.0]
    nrml_data = dict(
        [(hcn[0][0][0].text, [float(x) for x in hcn[1][0].text.split()])
         for hcn in hcns])

    curve_data = [line.strip()
                  for line in open(exp_results_file, 'r').readlines()]

    sites_poes = dict(zip(curve_data[::2], curve_data[1::2]))

    tc.assertEqual(len(sites_poes), len(nrml_data))

    for site, poes in sites_poes.iteritems():
        poes = [float(x) for x in poes.split()]
        tc.assertTrue(numpy.allclose(poes, nrml_data[site]))


def verify_hazmap_nrml(tc, nrml_path, exp_results_file):
    """
    Given a NRML path and a path to an expected results file, load the
    expected hazard map results from the latter and compare them with the
    data contained in the NRML file.

    :param tc: :class:`unittest.TestCase` object (for test assertions).
    :param string nrml_path: path to the nrml file to check
    :param string exp_results_file: path to the expected results file
    """
    root = etree.parse(nrml_path)
    hmns = root.xpath("//ns:HMNode",
                      namespaces={"ns": "http://openquake.org/xmlns/nrml/0.3"})

    # Example "-122.7 47.8": 0.15097656969
    nrml_data = dict([(hmn[0][0][0].text, float(hmn[1].text)) for hmn in hmns])

    map_data = [line.strip() for line in
                open(exp_results_file, 'r').readlines()]

    # Example line: "-122.7 47.8 0.15097656969"
    map_data = dict(line.rsplit(" ", 1) for line in map_data)

    tc.assertEqual(len(map_data), len(nrml_data))

    for site, iml in map_data.iteritems():
        iml = float(iml)
        numpy.testing.assert_approx_equal(iml, nrml_data[site])


def verify_hazmap_results(tc, job, expected_map, poe, statistic_type):
    """Given a job object and a dict of map results, verify the computed hazmap
    in the database with the expected results.

    :param tc:
        :class:`unittest.TestCase` instance (for test assertions).
    :param job:
        :class:`openquake.job.Job` instance.
    :param expected_map:
        Dict with expected results in the following structure::
            {'a': 15}
    :"""
    for site, value in expected_map.items():
        gh = geohash.encode(site.latitude, site.longitude, precision=12)

        hm_db = models.HazardMapData.objects.filter(
            hazard_map__output__oq_job=job,
            hazard_map__statistic_type=statistic_type,
            hazard_map__poe=poe).extra(
            where=["ST_GeoHash(location, 12) = %s"], params=[gh]).get()

        tc.assertTrue(numpy.allclose(value, hm_db.value))


class ClassicalPSHACalculatorAssuranceTestCase(
    unittest.TestCase, helpers.DbTestCase):

    job = None

    def tearDown(self):
        self.teardown_job(self.job)
        self.job = None

    @attr("qa")
    def test_peer_test_set_1_case_2(self):
        expected_results = load_exp_hazcurve_results("PeerTestSet1Case2")

        helpers.run_job(helpers.demo_file(
            os.path.join("PeerTestSet1Case2", "config.gem")))

        self._assert_hazcurve_results_are(expected_results)

    @attr("qa")
    def test_peer_test_set_1_case_5(self):
        expected_results = load_exp_hazcurve_results("PeerTestSet1Case5")

        helpers.run_job(helpers.demo_file(
            os.path.join("PeerTestSet1Case5", "config.gem")))

        self._assert_hazcurve_results_are(expected_results)

    @attr("qa")
    def test_peer_test_set_1_case_8a(self):
        expected_results = load_exp_hazcurve_results(
            "PeerTestSet1Case8a")

        helpers.run_job(helpers.demo_file(
            os.path.join("PeerTestSet1Case8a", "config.gem")))

        self._assert_hazcurve_results_are(expected_results)

    @attr("qa")
    def test_peer_test_set_1_case_10(self):
        expected_results = load_exp_hazcurve_results(
            "PeerTestSet1Case10")

        helpers.run_job(helpers.demo_file(
            os.path.join("PeerTestSet1Case10", "config.gem")))

        self._assert_hazcurve_results_are(expected_results)

    @attr("qa")
    def test_hazard_map_test(self):
        helpers.run_job(helpers.demo_file(
            os.path.join("HazardMapTest", "config.gem")))

        self.job = models.OqJob.objects.latest("id")

        path = helpers.demo_file(os.path.join("HazardMapTest",
            "expected_results", "meanHazardMap0.1.dat"))
        expected_map = load_expected_map(path)

        poe = 0.1
        statistic_type = "mean"
        verify_hazmap_results(self, self.job, expected_map, poe,
                              statistic_type)

    @attr("qa")
    def test_complex_fault_demo_hazard(self):
        """Run the `complex_fault_demo_hazard` demo and verify all of the
        resulting hazard curve and hazard map data."""
        job_cfg = helpers.demo_file(os.path.join(
            "complex_fault_demo_hazard", "config.gem"))

        exp_results_dir = os.path.join("complex_fault_demo_hazard",
                                       "expected_results")

        helpers.run_job(job_cfg)

        self.job = models.OqJob.objects.latest("id")

        # Check hazard curves for sample 0:
        # Hazard curve expected results for logic tree sample 0:
        hazcurve_0 = helpers.demo_file(os.path.join(exp_results_dir,
                                                     "hazardcurve-0.dat"))
        verify_hazcurve_results(
            self, self.job, hazcurve_0, end_branch_label=0)

        # Check mean hazard curves:
        hazcurve_mean = helpers.demo_file(os.path.join(exp_results_dir,
                                                       "hazardcurve-mean.dat"))
        verify_hazcurve_results(
            self, self.job, hazcurve_mean, statistic_type="mean")

        # Check hazard map mean 0.02:
        hazmap_mean_0_02 = helpers.demo_file(
            os.path.join(exp_results_dir, "hazardmap-0.02-mean.dat"))
        verify_hazmap_results(
            self, self.job, load_expected_map(hazmap_mean_0_02), 0.02, "mean")

        # Check hazard map mean 0.1:
        hazmap_mean_0_1 = helpers.demo_file(
            os.path.join(exp_results_dir, "hazardmap-0.1-mean.dat"))
        verify_hazmap_results(
            self, self.job, load_expected_map(hazmap_mean_0_1), 0.1, "mean")

    def _assert_hazcurve_results_are(self, expected_results):
        """Compare the expected hazard curve results with the results
        computed by the current job."""

        self.job = models.OqJob.objects.latest("id")

        errors = []
        for site, curve in expected_results.items():
            gh = geohash.encode(site.latitude, site.longitude, precision=12)

            hc_db = models.HazardCurveData.objects.filter(
                hazard_curve__output__oq_job=self.job,
                hazard_curve__statistic_type="mean").extra(
                where=["ST_GeoHash(location, 12) = %s"], params=[gh]).get()

            try:
                self._assert_curve_is(
                    curve, zip(self.job.profile().imls, hc_db.poes),
                    site, tolerance=0.005)
            except AssertionError as exc:
                errors.append(str(exc))
        if errors:
            raise AssertionError('\n' + '\n'.join(errors))

    def _assert_curve_is(self, expected, actual, site, tolerance):
        errors = []
        for i in xrange(max(len(expected), len(actual))):
            self.assertEqual(expected[i][0], actual[i][0])
            exp_val, act_val = expected[i][1], actual[i][1]
            msg = '{:<22} PoE {:5}: expected {:.2E} != actual {:.2E}'.format(
                site, expected[i][0], exp_val, act_val
            )
            try:
                self.assertAlmostEqual(act_val, exp_val, delta=tolerance,
                                       msg=msg)
            except AssertionError as exc:
                errors.append(str(exc))
        if errors:
            raise AssertionError('\n'.join(errors))

    @attr("qa")
    def test_complex_fault_demo_hazard_nrml(self):
        """
        Run the `complex_fault_demo_hazard` demo and verify all of the
        generated NRML data.
        """
        job_cfg = helpers.demo_file(os.path.join(
            "complex_fault_demo_hazard", "config.gem"))

        exp_results_dir = os.path.join("complex_fault_demo_hazard",
                                       "expected_results")

        helpers.run_job(job_cfg, ['--output-type=xml'])

        self.job = models.OqJob.objects.latest("id")

        copath = helpers.demo_file(os.path.join(
            "complex_fault_demo_hazard", "computed_output"))

        try:
            # Check hazard curves for sample 0:
            # Hazard curve expected results for logic tree sample 0:
            hazcurve_0 = helpers.demo_file(
                os.path.join(exp_results_dir, "hazardcurve-0.dat"))
            nrml_path = os.path.join(copath, "hazardcurve-0.xml")
            verify_hazcurve_nrml(self, nrml_path, hazcurve_0)

            # Check mean hazard curves:
            hazcurve_mean = helpers.demo_file(
                os.path.join(exp_results_dir, "hazardcurve-mean.dat"))
            nrml_path = os.path.join(copath, "hazardcurve-mean.xml")
            verify_hazcurve_nrml(self, nrml_path, hazcurve_mean)

            # Check hazard map mean 0.02:
            hazmap_mean_0_02 = helpers.demo_file(
                os.path.join(exp_results_dir, "hazardmap-0.02-mean.dat"))
            nrml_path = os.path.join(copath, "hazardmap-0.02-mean.xml")
            verify_hazmap_nrml(self, nrml_path, hazmap_mean_0_02)

            # Check hazard map mean 0.1:
            hazmap_mean_0_1 = helpers.demo_file(
                os.path.join(exp_results_dir, "hazardmap-0.1-mean.dat"))
            nrml_path = os.path.join(copath, "hazardmap-0.1-mean.xml")
            verify_hazmap_nrml(self, nrml_path, hazmap_mean_0_1)
        finally:
            shutil.rmtree(copath)

    @attr("qa")
    def test_complex_fault_demo_hazard_nrml_written_once(self):
        """
        Run the `complex_fault_demo_hazard` demo and verify that the
        NRML files are written only once.
        """

        def filter_multi():
            """Filter and return files that were written more than once."""
            counts = defaultdict(int)
            files = stats.kvs_op("lrange", key, 0, -1)
            for file in files:
                counts[file] += 1
            return [(f, c) for f, c in counts.iteritems() if c > 1]

        job_cfg = helpers.demo_file(os.path.join(
            "complex_fault_demo_hazard", "config.gem"))

        helpers.run_job(job_cfg, ['--output-type=xml'])

        self.job = models.OqJob.objects.latest("id")

        key = stats.key_name(
            self.job.id, *stats.STATS_KEYS["hcls_xmlcurvewrites"])
        if key:
            multi_writes = filter_multi()
            self.assertFalse(multi_writes, str(multi_writes))
        key = stats.key_name(
            self.job.id, *stats.STATS_KEYS["hcls_xmlmapwrites"])
        if key:
            multi_writes = filter_multi()
            self.assertFalse(multi_writes, str(multi_writes))
