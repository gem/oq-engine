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

from nose.plugins.attrib import attr

from openquake.db import models
from openquake import shapes
from tests.utils import helpers

TEST_NAME = "PeerTestSet1Case2"


class ClassicalPSHACalculatorAssuranceTestCase(
    unittest.TestCase, helpers.DbTestMixin):

    @attr("quality_assurance")
    def test_peerTestSet1Case2(self):
        expected_results = self._load_results()
        job = self._run_job(helpers.smoketest_file(TEST_NAME + "/config.gem"))
        job_db = models.OqJob.objects.get(id=job.job_id)

        for site, curve in expected_results.items():
            gh = geohash.encode(site.latitude, site.longitude, precision=12)

            hc_db = models.HazardCurveData.objects.filter(
                hazard_curve__output__oq_job=job_db,
                hazard_curve__statistic_type="mean").extra(
                where=["ST_GeoHash(location, 12) = %s"], params=[gh]).get()

            self.assertTrue(numpy.allclose(numpy.array(curve),
                    numpy.array(zip(job_db.oq_params.imls, hc_db.poes)),
                    atol=0.005))

        self.teardown_job(job_db)

    def _run_job(self, config_file):
        job = helpers.job_from_file(config_file)
        job.launch()

        return job

    def _load_results(self):
        """Return the expected hazard curves read from the expected_results/ dir.

        :returns: the expected hazard curves.
        :rtype: :py:class:`dict` where each key is an instance of
            :py:class:`openquake.shapes.Site` and each value is a list
            of (IML, PoE) tuples
        """

        # split the x string and get
        # the value at index y casted to float
        get = lambda x, y: float(x.split(",")[y])

        results_dir = helpers.smoketest_file(TEST_NAME + "/expected_results")
        results_files = os.listdir(results_dir)

        results = {}

        for result_file in results_files:
            path = os.path.join(results_dir, result_file)

            with open(path, "rb") as hazard_curve:
                lines = hazard_curve.readlines()[0].split()

                coords = lines.pop(0)

                # the format is latitude,longitude
                site = shapes.Site(get(coords, 1), get(coords, 0))

                results[site] = []

                while len(lines):
                    pair = lines.pop(0)

                    # the format is IML,PoE
                    results[site].append((get(pair, 0), get(pair, 1)))

        return results
