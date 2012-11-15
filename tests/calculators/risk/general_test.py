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

import itertools
import numpy
import unittest
import json

from openquake.calculators.risk.general import compute_alpha
from openquake.calculators.risk.general import compute_beta
from openquake.calculators.risk.general import load_gmvs_at
from openquake import kvs
from openquake import shapes

from tests.utils import helpers


class BetaDistributionTestCase(unittest.TestCase):
    """ Beta Distribution related testcase """

    def setUp(self):
        self.mean_loss_ratios = [0.050, 0.100, 0.200, 0.400, 0.800]
        self.stddevs = [0.025, 0.040, 0.060, 0.080, 0.080]
        self.covs = [0.500, 0.400, 0.300, 0.200, 0.100]
        self.imls = [0.100, 0.200, 0.300, 0.450, 0.600]

    def test_compute_alphas(self):
        # expected alphas provided by Vitor

        expected_alphas = [3.750, 5.525, 8.689, 14.600, 19.200]

        alphas = [compute_alpha(mean_loss_ratio, stddev) for mean_loss_ratio,
                stddev in itertools.izip(self.mean_loss_ratios, self.stddevs)]
        self.assertTrue(numpy.allclose(alphas, expected_alphas, atol=0.0002))

    def test_compute_betas(self):
        # expected betas provided by Vitor

        expected_betas = [71.250, 49.725, 34.756, 21.900, 4.800]

        betas = [compute_beta(mean_loss_ratio, stddev) for mean_loss_ratio,
                stddev in itertools.izip(self.mean_loss_ratios, self.stddevs)]
        self.assertTrue(numpy.allclose(betas, expected_betas, atol=0.0001))


RISK_DEMO_CONFIG_FILE = helpers.demo_file(
    "classical_psha_based_risk/config.gem")


class LoadGroundMotionValuesTestCase(unittest.TestCase):

    job_id = "1234"
    region = shapes.Region.from_simple((0.1, 0.1), (0.2, 0.2))

    def setUp(self):
        kvs.mark_job_as_current(self.job_id)
        kvs.cache_gc(self.job_id)

    def tearDown(self):
        kvs.mark_job_as_current(self.job_id)
        kvs.cache_gc(self.job_id)

    def test_load_gmvs_at(self):
        """
        Exercise the function
        :func:`openquake.calculators.risk.general.load_gmvs_at`.
        """

        gmvs = [
            {'site_lon': 0.1, 'site_lat': 0.2, 'mag': 0.117},
            {'site_lon': 0.1, 'site_lat': 0.2, 'mag': 0.167},
            {'site_lon': 0.1, 'site_lat': 0.2, 'mag': 0.542}]

        expected_gmvs = [0.117, 0.167, 0.542]
        point = self.region.grid.point_at(shapes.Site(0.1, 0.2))

        # we expect this point to be at row 1, column 0
        self.assertEqual(1, point.row)
        self.assertEqual(0, point.column)

        key = kvs.tokens.ground_motion_values_key(self.job_id, point)

        # place the test values in kvs
        for gmv in gmvs:
            kvs.get_client().rpush(key, json.JSONEncoder().encode(gmv))

        actual_gmvs = load_gmvs_at(self.job_id, point)
        self.assertEqual(expected_gmvs, actual_gmvs)
