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


import unittest

from openquake.db.alchemy.db_utils import get_db_session
from openquake.job import Job
from openquake.job.mixins import Mixin
from openquake.output.hazard import *
from openquake.risk.job.classical_psha import ClassicalPSHABasedMixin
from openquake.risk.job.probabilistic import ProbabilisticEventMixin
from openquake.shapes import Site, Region

from tests.utils import helpers


# See data in output_hazard_unittest.py
def HAZARD_CURVE_DATA():
    return [
        (Site(-122.2, 37.5),
         {'investigationTimeSpan': '50.0',
          'IMLValues': [0.778, 1.09, 1.52, 2.13],
          'PoEValues': [0.354, 0.114, 0.023, 0.002],
          'IMT': 'PGA',
          'statistics': 'mean'}),
        (Site(-122.1, 37.5),
         {'investigationTimeSpan': '50.0',
          'IMLValues': [0.778, 1.09, 1.52, 2.13],
          'PoEValues': [0.454, 0.214, 0.123, 0.102],
          'IMT': 'PGA',
          'statistics': 'mean'}),
    ]


def GMF_DATA():
    return [
        {
            Site(-117, 40): {'groundMotion': 0.1},
            Site(-116, 40): {'groundMotion': 0.2},
            Site(-116, 41): {'groundMotion': 0.3},
            Site(-117, 41): {'groundMotion': 0.4},
        },
        {
            Site(-117, 40): {'groundMotion': 0.5},
            Site(-116, 40): {'groundMotion': 0.6},
            Site(-116, 41): {'groundMotion': 0.7},
            Site(-117, 41): {'groundMotion': 0.8},
        },
        {
            Site(-117, 42): {'groundMotion': 1.0},
            Site(-116, 42): {'groundMotion': 1.1},
            Site(-116, 41): {'groundMotion': 1.2},
            Site(-117, 41): {'groundMotion': 1.3},
        },
    ]


class HazardCurveDBReadTestCase(unittest.TestCase, helpers.DbTestMixin):
    """
    Test the code to read hazard curves from DB.
    """
    def setUp(self):
        self.job = self.setup_classic_job()
        session = get_db_session("reslt", "writer")
        output_path = self.generate_output_path(self.job)
        hcw = HazardCurveDBWriter(session, output_path, self.job.id)
        hcw.serialize(HAZARD_CURVE_DATA())

    def tearDown(self):
        if hasattr(self, "job") and self.job:
            self.teardown_job(self.job)
        if hasattr(self, "output") and self.output:
            self.teardown_output(self.output)

    def test_read_curve(self):
        """Verify _get_db_curve."""
        with Mixin(helpers.create_job({}, job_id=self.job.id),
                   ClassicalPSHABasedMixin) as mixin:
            curve1 = mixin._get_db_curve(Site(-122.2, 37.5))
            self.assertEquals(list(curve1.abscissae),
                              [0.005, 0.007, 0.0098, 0.0137])
            self.assertEquals(list(curve1.ordinates),
                              [0.354, 0.114, 0.023, 0.002])

            curve2 = mixin._get_db_curve(Site(-122.1, 37.5))
            self.assertEquals(list(curve2.abscissae),
                              [0.005, 0.007, 0.0098, 0.0137])
            self.assertEquals(list(curve2.ordinates),
                              [0.454, 0.214, 0.123, 0.102])


class GMFDBReadTestCase(unittest.TestCase, helpers.DbTestMixin):
    """
    Test the code to read the ground motion fields from DB.
    """
    def setUp(self):
        self.job = self.setup_classic_job()
        for gmf in GMF_DATA():
            output_path = self.generate_output_path(self.job)
            hcw = GMFDBWriter(output_path, self.job.id)
            hcw.serialize(gmf)

    def tearDown(self):
        if hasattr(self, "job") and self.job:
            self.teardown_job(self.job)
        if hasattr(self, "output") and self.output:
            self.teardown_output(self.output)

    def test_site_keys(self):
        """Verify _sites_to_gmf_keys"""
        params = {
            'REGION_VERTEX': '40,-117, 42,-117, 42,-116, 40,-116',
            'REGION_GRID_SPACING': '1.0'}
        with Mixin(helpers.create_job(params, job_id=self.job.id),
                   ProbabilisticEventMixin) as mixin:
            keys = mixin._sites_to_gmf_keys([Site(-117, 40), Site(-116, 42)])

            self.assertEquals(["0!0", "2!1"], keys)

    def test_read_gmfs(self):
        """Verify _get_db_gmfs."""
        params = {
            'REGION_VERTEX': '40,-117, 42,-117, 42,-116, 40,-116',
            'REGION_GRID_SPACING': '1.0'}
        with Mixin(helpers.create_job(params, job_id=self.job.id),
                   ProbabilisticEventMixin) as mixin:
            self.assertEquals(3, len(mixin._gmf_db_list(self.job.id)))

            # only the keys in gmfs are used
            gmfs = mixin._get_db_gmfs([], self.job.id)
            self.assertEquals({}, gmfs)

            # only the keys in gmfs are used
            sites = [Site(lon, lat)
                            for lon in xrange(-117, -115)
                            for lat in xrange(40, 43)]
            gmfs = mixin._get_db_gmfs(sites, self.job.id)
            # avoid rounding errors
            for k, v in gmfs.items():
                gmfs[k] = [round(i, 1) for i in v]

            self.assertEquals({
                    '0!0': [0.1, 0.5, 0.0],
                    '0!1': [0.2, 0.6, 0.0],
                    '1!0': [0.4, 0.8, 1.3],
                    '1!1': [0.3, 0.7, 1.2],
                    '2!0': [0.0, 0.0, 1.0],
                    '2!1': [0.0, 0.0, 1.1],
                    }, gmfs)
