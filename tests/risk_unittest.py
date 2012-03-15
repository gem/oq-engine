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

from django.contrib.gis.geos import GEOSGeometry
from lxml import etree
from StringIO import StringIO
import numpy
import os
import tempfile
import unittest

from openquake.db import models
from openquake.calculators.risk.classical import core as classical_core
from openquake.calculators.risk.event_based import core as eb_core
from openquake.calculators.risk.general import AggregateLossCurve
from openquake.calculators.risk.general import BaseRiskCalculator
from openquake.calculators.risk.general import Block
from openquake.calculators.risk.general import compute_bcr
from openquake.calculators.risk.general import _compute_conditional_loss
from openquake.calculators.risk.general import _compute_cumulative_histogram
from openquake.calculators.risk.general import compute_loss_curve
from openquake.calculators.risk.general import compute_loss_ratio_curve
from openquake.calculators.risk.general import compute_loss_ratios
from openquake.calculators.risk.general import _compute_loss_ratios_range
from openquake.calculators.risk.general import compute_mean_loss
from openquake.calculators.risk.general import _compute_mid_mean_pe
from openquake.calculators.risk.general import _compute_mid_po
from openquake.calculators.risk.general import _compute_probs_of_exceedance
from openquake.calculators.risk.general import _compute_rates_of_exceedance
from openquake.calculators.risk.general import ProbabilisticRiskCalculator
from openquake.calculators.risk.scenario import core as scenario
from openquake import engine
from openquake import kvs
from openquake import shapes
from openquake.output import hazard

from tests.utils import helpers


ASSET_VALUE = 5.0
INVALID_ASSET_VALUE = 0.0

HAZARD_CURVE = shapes.Curve([(5.0, 0.138), (6.0, 0.099),
        (7.0, 0.068), (8.0, 0.041)])

LOSS_RATIO_EXCEEDANCE_MATRIX = [[0.695, 0.858, 0.990, 1.000],
        [0.266, 0.510, 0.841, 0.999]]

GMFs = {"IMLs": (0.079888, 0.273488, 0.115856, 0.034912, 0.271488, 0.00224,
        0.04336, 0.099552, 0.071968, 0.003456, 0.030704, 0.011744,
        0.024176, 0.002224, 0.008912, 0.004224, 0.033584, 0.041088,
        0.012864, 0.001728, 0.06648, 0.000736, 0.01992, 0.011616,
        0.001104, 0.033264, 0.021552, 0.055088, 0.00176, 0.001088, 0.041872,
        0.005152, 0.007424, 0.002464, 0.008496, 0.019744, 0.025136, 0.005552,
        0.00168, 0.00704, 0.00272, 0.081328, 0.001408, 0.025568, 0.051376,
        0.003456, 0.01208, 0.002496, 0.001152, 0.007552, 0.004944, 0.024944,
        0.01168, 0.027408, 0.00504, 0.003136, 0.20608, 0.00344, 0.01448,
        0.03664, 0.124992, 0.005024, 0.007536, 0.015696, 0.00608,
        0.001248, 0.005744, 0.017328, 0.002272, 0.06384, 0.029104,
        0.001152, 0.016384, 0.002096, 0.00328, 0.004304, 0.020544,
        0.000768, 0.011456, 0.004528, 0.024688, 0.024304, 0.126928,
        0.002416, 0.0032, 0.024768, 0.00608, 0.02544, 0.003392,
        0.381296, 0.013808, 0.002256, 0.181776, 0.038912, 0.023888,
        0.002848, 0.014176, 0.001936, 0.089408, 0.001008, 0.02152,
        0.002464, 0.00464, 0.064384, 0.001712, 0.01584, 0.012544,
        0.028128, 0.005808, 0.004928, 0.025536, 0.008304, 0.112528,
        0.06472, 0.01824, 0.002624, 0.003456, 0.014832, 0.002592,
        0.041264, 0.004368, 0.016144, 0.008032, 0.007344, 0.004976,
        0.00072, 0.022192, 0.002496, 0.001456, 0.044976, 0.055424,
        0.009232, 0.010368, 0.000944, 0.002976, 0.00656, 0.003184,
        0.004288, 0.00632, 0.286512, 0.007568, 0.00104, 0.00144,
        0.004896, 0.053248, 0.046144, 0.0128, 0.033072, 0.02968,
        0.002096, 0.021008, 0.017536, 0.000656, 0.016032, 0.012768,
        0.002752, 0.007392, 0.007072, 0.044112, 0.023072, 0.013232,
        0.001824, 0.020064, 0.008912, 0.039504, 0.00144, 0.000816,
        0.008544, 0.077056, 0.113984, 0.001856, 0.053024, 0.023792,
        0.013056, 0.0084, 0.009392, 0.010928, 0.041904, 0.000496,
        0.041936, 0.035664, 0.03176, 0.003552, 0.00216, 0.0476, 0.028944,
        0.006832, 0.011136, 0.025712, 0.006368, 0.004672, 0.001312,
        0.008496, 0.069136, 0.011568, 0.01576, 0.01072, 0.002336,
        0.166192, 0.00376, 0.013216, 0.000592, 0.002832, 0.052928,
        0.007872, 0.001072, 0.021136, 0.029568, 0.012944, 0.004064,
        0.002336, 0.010832, 0.10104, 0.00096, 0.01296, 0.037104),
        "TSES": 900, "TimeSpan": 50}


class EpsilonProvider(object):

    def __init__(self, asset, epsilons):
        self.asset = asset
        self.epsilons = epsilons

    def epsilon(self, asset):
        assert self.asset is asset
        return self.epsilons.pop(0)


TEST_REGION = shapes.Region.from_simple((11.1, 11.1), (100.2, 100.2))


class ProbabilisticEventBasedTestCase(unittest.TestCase, helpers.DbTestCase):

    job = None
    assets = []
    peb_gmfs = []
    points = []
    emdl = None

    @classmethod
    def setUpClass(cls):
        path = os.path.join(helpers.SCHEMA_EXAMPLES_DIR, "PEB-exposure.yaml")
        inputs = [("exposure", path)]
        cls.job = cls.setup_classic_job(inputs=inputs)
        [input] = models.inputs4job(cls.job.id, input_type="exposure",
                                    path=path)
        owner = models.OqUser.objects.get(user_name="openquake")
        cls.emdl = models.ExposureModel(
            owner=owner, input=input, description="PEB test exposure model",
            category="PEB storages sheds", stco_unit="nuts",
            stco_type="aggregated", reco_unit="pebbles",
            reco_type="aggregated")
        cls.emdl.save()
        values = [22.61, 124.27, 42.93, 29.37, 40.68, 178.47]
        for x, value in zip([float(v) for v in range(20, 27)], values):
            site = shapes.Site(x, x + 11)
            cls.points.append(TEST_REGION.grid.point_at(site))
            location = GEOSGeometry(site.point.to_wkt())
            asset = models.ExposureData(exposure_model=cls.emdl, taxonomy="ID",
                                        asset_ref="asset_%s" % x, stco=value,
                                        site=location, reco=value * 0.75)
            asset.save()
            cls.assets.append(asset)

    @classmethod
    def tearDownClass(cls):
        cls.teardown_job(cls.job)

    def setUp(self):
        imls_1 = [0.01, 0.04, 0.07, 0.1, 0.12, 0.22, 0.37, 0.52]
        loss_ratios_1 = [0.001, 0.022, 0.051, 0.08, 0.1, 0.2, 0.405, 0.7]
        covs_1 = [0.0] * 8
        self.vuln_function_1 = shapes.VulnerabilityFunction(
            imls_1, loss_ratios_1, covs_1)

        self.gmfs = GMFs

        self.cum_histogram = numpy.array([112, 46, 26, 18, 14,
                12, 8, 7, 7, 6, 5, 4, 4, 4, 4, 4, 2, 1, 1, 1, 1, 1, 1, 1])

        imls_2 = [0.0, 0.04, 0.08, 0.12, 0.16, 0.2, 0.24, 0.28, 0.32, 0.36,
            0.4, 0.44, 0.48, 0.53, 0.57, 0.61, 0.65, 0.69, 0.73, 0.77, 0.81,
            0.85, 0.89, 0.93, 0.97, 1.01, 1.05, 1.09, 1.13, 1.17, 1.21, 1.25,
            1.29, 1.33, 1.37, 1.41, 1.45, 1.49, 1.54, 1.58, 1.62, 1.66, 1.7,
            1.74, 1.78, 1.82, 1.86, 1.9, 1.94, 1.98, 2.02, 2.06, 2.1, 2.14,
            2.18, 2.22, 2.26, 2.3, 2.34, 2.38, 2.42, 2.46, 2.51, 2.55, 2.59,
            2.63, 2.67, 2.71, 2.75, 2.79, 2.83, 2.87, 2.91, 2.95, 2.99, 3.03,
            3.07, 3.11, 3.15, 3.19, 3.23, 3.27, 3.31, 3.35, 3.39, 3.43, 3.47,
            3.52, 3.56, 3.6, 3.64, 3.68, 3.72, 3.76, 3.8, 3.84, 3.88, 3.92,
            3.96, 4.0]
        loss_ratios_2 = [0.0, 0.0, 0.0, 0.01, 0.04, 0.07, 0.11, 0.15, 0.2,
            0.25, 0.3, 0.35, 0.39, 0.43, 0.47, 0.51, 0.55, 0.58, 0.61, 0.64,
            0.67, 0.69, 0.71, 0.73, 0.75, 0.77, 0.79, 0.8, 0.81, 0.83, 0.84,
            0.85, 0.86, 0.87, 0.88, 0.89, 0.89, 0.9, 0.91, 0.91, 0.92, 0.92,
            0.93, 0.93, 0.94, 0.94, 0.94, 0.95, 0.95, 0.95, 0.95, 0.96, 0.96,
            0.96, 0.96, 0.97, 0.97, 0.97, 0.97, 0.97, 0.97, 0.98, 0.98, 0.98,
            0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.99, 0.99, 0.99, 0.99,
            0.99, 0.99, 0.99, 0.99, 0.99, 0.99, 0.99, 0.99, 0.99, 0.99, 0.99,
            0.99, 0.99, 0.99, 0.99, 0.99, 0.99, 0.99, 0.99, 0.99, 1.0, 1.0,
            1.0, 1.0, 1.0]
        covs_2 = [0.0] * 100
        self.vuln_function_2 = shapes.VulnerabilityFunction(
            imls_2, loss_ratios_2, covs_2)

        self.params = {}
        self.params["OUTPUT_DIR"] = helpers.OUTPUT_DIR
        self.params["AGGREGATE_LOSS_CURVE"] = 1
        self.params["BASE_PATH"] = "."
        self.params["INVESTIGATION_TIME"] = 50.0

        self.job_ctxt = helpers.create_job(
            self.params, base_path=".", job_id=self.job.id,
            oq_job=self.job, oq_job_profile=models.profile4job(self.job.id))
        self.job_id = self.job_ctxt.job_id
        self.job_ctxt.to_kvs()

        self.peb_gmfs = []
        self.gmfs_1 = {"IMLs": (0.1439, 0.1821, 0.5343, 0.171, 0.2177,
                0.6039, 0.0618, 0.186, 0.5512, 1.2602, 0.2824, 0.2693,
                0.1705, 0.8453, 0.6355, 0.0721, 0.2475, 0.1601, 0.3544,
                0.1756), "TSES": 200, "TimeSpan": 50}
        self.peb_gmfs.append(self.gmfs_1)

        self.gmfs_2 = {"IMLs": (0.1507, 0.2656, 0.5422, 0.3685, 0.3172,
                0.6604, 0.1182, 0.1545, 0.7613, 0.5246, 0.2428, 0.2882,
                0.2179, 1.2939, 0.6042, 0.1418, 0.3637, 0.222, 0.3613,
                0.113), "TSES": 200, "TimeSpan": 50}
        self.peb_gmfs.append(self.gmfs_2)

        self.gmfs_3 = {"IMLs": (0.156, 0.3158, 0.3968, 0.2827, 0.1915, 0.5862,
                0.1438, 0.2114, 0.5101, 1.0097, 0.226, 0.3443, 0.1693,
                1.0754, 0.3533, 0.1461, 0.347, 0.2665, 0.2977, 0.2925),
                "TSES": 200, "TimeSpan": 50}
        self.peb_gmfs.append(self.gmfs_3)

        self.gmfs_4 = {"IMLs": (0.1311, 0.3566, 0.4895, 0.3647, 0.2313,
                0.9297, 0.2337, 0.2862, 0.5278, 0.6603, 0.3537, 0.2997,
                0.1097, 1.1875, 0.4752, 0.1575, 0.4009, 0.2519, 0.2653,
                0.1394), "TSES": 200, "TimeSpan": 50}
        self.peb_gmfs.append(self.gmfs_4)

        self.gmfs_5 = {"IMLs": (0.0879, 0.2895, 0.465, 0.2463, 0.1862, 0.763,
                0.2189, 0.3324, 0.3215, 0.6406, 0.5014, 0.3877, 0.1318, 1.0545,
                0.3035, 0.1118, 0.2981, 0.3492, 0.2406, 0.1043),
                "TSES": 200, "TimeSpan": 50}
        self.peb_gmfs.append(self.gmfs_5)

        self.gmfs_6 = {"IMLs": (0.0872, 0.2288, 0.5655, 0.2118, 0.2, 0.6633,
                0.2095, 0.6537, 0.3838, 0.781, 0.3054, 0.5375, 0.1361, 0.8838,
                0.3726, 0.0845, 0.1942, 0.4629, 0.1354, 0.1109),
                "TSES": 200, "TimeSpan": 50}
        self.peb_gmfs.append(self.gmfs_6)

        # deleting keys in kvs
        kvs.get_client().flushall()

        kvs.set_value_json_encoded(
                kvs.tokens.vuln_key(self.job_id),
                {"ID": self.vuln_function_2.to_json()})
        kvs.set_value_json_encoded(
                kvs.tokens.vuln_key(self.job_id, retrofitted=True),
                {"ID": self.vuln_function_2.to_json()})

        # store the gmfs
        self._store_gmfs(self.gmfs_1, 1, 1)
        self._store_gmfs(self.gmfs_2, 1, 2)
        self._store_gmfs(self.gmfs_3, 1, 3)
        self._store_gmfs(self.gmfs_4, 1, 4)
        self._store_gmfs(self.gmfs_5, 1, 5)
        self._store_gmfs(self.gmfs_6, 1, 6)

    def _store_gmfs(self, gmfs, row, column):
        key = kvs.tokens.gmf_set_key(self.job_id, column, row)
        kvs.set_value_json_encoded(key, gmfs)

    def test_an_empty_function_produces_an_empty_set(self):
        data = compute_loss_ratios(shapes.EMPTY_CURVE, self.gmfs, None, None)
        self.assertEqual(0, data.size)

    def test_an_empty_gmfs_produces_an_empty_set(self):
        data = compute_loss_ratios(self.vuln_function_1, {"IMLs": ()}, None,
                                   None)
        self.assertEqual(0, data.size)

    def test_with_valid_covs_we_sample_the_loss_ratios(self):
        """With valid covs we need to sample loss ratios.

        If the vulnerability function has some covs greater than 0.0 we need to
        use a different algorithm (sampled based) to compute the loss ratios.
        """

        imls = [0.10, 0.30, 0.50, 1.00]
        loss_ratios = [0.05, 0.10, 0.15, 0.30]
        covs = [0.30, 0.30, 0.20, 0.20]
        vuln_function = shapes.VulnerabilityFunction(imls, loss_ratios, covs)

        epsilons = [0.5377, 1.8339, -2.2588, 0.8622, 0.3188, -1.3077,
                    -0.4336, 0.3426, 3.5784, 2.7694]

        expected_asset = object()

        gmfs = {"IMLs": (0.1576, 0.9706, 0.9572, 0.4854, 0.8003,
                0.1419, 0.4218, 0.9157, 0.7922, 0.9595)}

        self.assertTrue(
            numpy.allclose(
                numpy.array([0.0722, 0.4106, 0.1800, 0.1710, 0.2508, 0.0395,
                             0.1145, 0.2883, 0.4734, 0.4885]),
                compute_loss_ratios(vuln_function, gmfs,
                                    EpsilonProvider(expected_asset, epsilons),
                                    expected_asset), atol=0.0001))

    def test_when_the_mean_is_zero_the_loss_ratio_is_zero(self):
        """In sampled based, when an interpolated mean loss ratio is zero,
        the resulting loss ratio is also zero.

        This is how the interpolation is done:
        mean_ratio = vuln_function.ordinate_for(ground_motion_field)

        In this case, the first IML from the GMFs is 0.10 and the
        mean loss ratio in the vulnerability function for that IML
        is zero. So the resulting loss ratio must be zero.
        """

        imls = [0.10, 0.30]
        loss_ratios = [0.00, 0.10]
        covs = [0.30, 0.30]
        vuln_function = shapes.VulnerabilityFunction(imls, loss_ratios, covs)

        epsilons = [0.5377]
        expected_asset = object()

        gmfs = {"IMLs": (0.1000, )}

        self.assertEqual(0.0, compute_loss_ratios(
            vuln_function, gmfs, EpsilonProvider(expected_asset, epsilons),
            expected_asset)[0])

    def test_loss_ratios_boundaries(self):
        """Loss ratios generation given a GMFs and a vulnerability function.

        The vulnerability function used in this test has all covs equal
        to zero, so the mean based algorithm is used. This test checks
        the boundary conditions.

        The resulting loss ratio is zero if the GMF is below the minimum IML
        defined the vulnerability function.

        The resulting loss ratio is equal to the maximum loss ratio
        defined by the function if the GMF is greater than the maximum
        IML defined.
        """
        # min IML in this case is 0.01
        self.assertTrue(numpy.allclose(numpy.array([0.0, 0.0, 0.0]),
                compute_loss_ratios(self.vuln_function_1,
                {"IMLs": (0.0001, 0.0002, 0.0003)}, None, None)))

        # max IML in this case is 0.52
        self.assertTrue(numpy.allclose(numpy.array([0.700, 0.700]),
                compute_loss_ratios(self.vuln_function_1,
                {"IMLs": (0.525, 0.530)}, None, None)))

    def test_loss_ratios_computation_using_gmfs(self):
        """Loss ratios generation given a GMFs and a vulnerability function.

        The vulnerability function used in this test has all covs equal
        to zero, so the mean based algorithm is used. It basically
        takes each IML defined in the GMFs and interpolates them using
        the given vulnerability function.
        """

        # manually computed values by Vitor Silva
        expected_loss_ratios = numpy.array([0.0605584000000000,
                0.273100266666667, 0.0958560000000000, 0.0184384000000000,
                0.270366933333333, 0.0,
                0.0252480000000000, 0.0795669333333333,
                0.0529024000000000, 0.0,
                0.0154928000000000, 0.00222080000000000,
                0.0109232000000000, 0.0,
                0.0, 0.0, 0.0175088000000000, 0.0230517333333333,
                0.00300480000000000,
                0.0, 0.0475973333333333, 0.0, 0.00794400000000000,
                0.00213120000000000, 0.0, 0.0172848000000000,
                0.00908640000000000,
                0.0365850666666667, 0.0, 0.0, 0.0238096000000000,
                0.0, 0.0, 0.0,
                0.0, 0.00782080000000000, 0.0115952000000000,
                0.0, 0.0, 0.0,
                0.0, 0.0619504000000000, 0.0, 0.0118976000000000,
                0.0329968000000000,
                0.0, 0.00245600000000000, 0.0, 0.0, 0.0,
                0.0, 0.0114608000000000,
                0.00217600000000000, 0.0131856000000000,
                0.0, 0.0, 0.186080000000000,
                0.0, 0.00413600000000000, 0.0196480000000000,
                0.104992000000000, 0.0,
                0.0, 0.00498720000000000, 0.0, 0.0, 0.0,
                0.00612960000000000, 0.0,
                0.0450453333333333, 0.0143728000000000,
                0.0, 0.00546880000000000,
                0.0, 0.0, 0.0, 0.00838080000000000,
                0.0, 0.00201920000000000, 0.0,
                0.0112816000000000, 0.0110128000000000,
                0.106928000000000, 0.0,
                0.0, 0.0113376000000000, 0.0, 0.0118080000000000, 0.0,
                0.427215466666667, 0.00366560000000000,
                0.0, 0.161776000000000,
                0.0212384000000000, 0.0107216000000000,
                0.0, 0.00392320000000000,
                0.0, 0.0697610666666667, 0.0, 0.00906400000000000, 0.0, 0.0,
                0.0455712000000000, 0.0,
                0.00508800000000000, 0.00278080000000000,
                0.0136896000000000, 0.0, 0.0, 0.0118752000000000, 0.0,
                0.0925280000000000, 0.0458960000000000, 0.00676800000000000,
                0.0, 0.0, 0.00438240000000000, 0.0, 0.0232218666666667, 0.0,
                0.00530080000000000, 0.0, 0.0, 0.0, 0.0, 0.00953440000000000,
                0.0, 0.0, 0.0268101333333333, 0.0369098666666667, 0.0,
                0.00125760000000000, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                0.290899733333333, 0.0, 0.0, 0.0, 0.0, 0.0348064000000000,
                0.0279392000000000, 0.00296000000000000, 0.0171504000000000,
                0.0147760000000000, 0.0,
                0.00870560000000000, 0.00627520000000000,
                0.0, 0.00522240000000000, 0.00293760000000000, 0.0, 0.0, 0.0,
                0.0259749333333333, 0.0101504000000000,
                0.00326240000000000, 0.0,
                0.00804480000000000, 0.0, 0.0216528000000000, 0.0, 0.0, 0.0,
                0.0578208000000000, 0.0939840000000000,
                0.0, 0.0345898666666667,
                0.0106544000000000, 0.00313920000000000,
                0.0, 0.0, 0.00164960000000000,
                0.0238405333333333, 0.0,
                0.0238714666666667, 0.0189648000000000,
                0.0162320000000000, 0.0, 0.0,
                0.0293466666666667, 0.0142608000000000,
                0.0, 0.00179520000000000,
                0.0119984000000000, 0.0, 0.0, 0.0, 0.0,
                0.0501648000000000, 0.00209760000000000, 0.00503200000000000,
                0.00150400000000000, 0.0, 0.146192000000000,
                0.0, 0.00325120000000000,
                0.0, 0.0, 0.0344970666666667, 0.0, 0.0, 0.00879520000000000,
                0.0146976000000000, 0.00306080000000000,
                0.0, 0.0, 0.00158240000000000,
                0.0810400000000000, 0.0,
                0.00307200000000000, 0.0199728000000000])

        # the length of the result is the length of the gmf
        self.assertTrue(numpy.allclose(expected_loss_ratios,
                compute_loss_ratios(self.vuln_function_1,
                self.gmfs, None, None)))

    def test_loss_ratios_range_generation(self):
        loss_ratios = numpy.array([0.0, 2.0])
        expected_range = numpy.array([0.0, 0.5, 1.0, 1.5, 2.0])

        self.assertTrue(numpy.allclose(expected_range,
                _compute_loss_ratios_range(loss_ratios, 5),
                atol=0.0001))

    def test_builds_the_cumulative_histogram(self):
        loss_ratios = compute_loss_ratios(
                self.vuln_function_1, self.gmfs, None, None)
        loss_histogram_bins = 25

        loss_ratios_range = _compute_loss_ratios_range(
            loss_ratios, loss_histogram_bins)

        self.assertTrue(numpy.allclose(self.cum_histogram,
                _compute_cumulative_histogram(
                loss_ratios, loss_ratios_range)))

    def test_computes_the_rates_of_exceedance(self):
        expected_rates = numpy.array([0.12444444, 0.05111111, 0.02888889,
                0.02, 0.01555556, 0.01333333, 0.00888889, 0.00777778,
                0.00777778, 0.00666667, 0.00555556, 0.00444444,
                0.00444444, 0.00444444, 0.00444444, 0.00444444, 0.00222222,
                0.00111111, 0.00111111, 0.00111111, 0.00111111,
                0.00111111, 0.00111111, 0.00111111])

        self.assertTrue(numpy.allclose(expected_rates,
                _compute_rates_of_exceedance(
                self.cum_histogram, self.gmfs["TSES"]), atol=0.01))

    def test_tses_is_not_supposed_to_be_zero_or_less(self):
        self.assertRaises(ValueError, _compute_rates_of_exceedance,
                self.cum_histogram, 0.0)

        self.assertRaises(ValueError, _compute_rates_of_exceedance,
                self.cum_histogram, -10.0)

    def test_computes_probs_of_exceedance(self):
        expected_probs = [0.99801517, 0.92235092, 0.76412292, 0.63212056,
                0.54057418, 0.48658288, 0.35881961, 0.32219042, 0.32219042,
                0.28346869, 0.24253487, 0.1992626, 0.1992626, 0.1992626,
                0.1992626, 0.1992626, 0.10516068, 0.05404053, 0.05404053,
                0.05404053, 0.05404053, 0.05404053, 0.05404053, 0.05404053]

        self.assertTrue(numpy.allclose(expected_probs,
                _compute_probs_of_exceedance(
                _compute_rates_of_exceedance(
                self.cum_histogram, self.gmfs["TSES"]),
                self.gmfs["TimeSpan"]), atol=0.0001))

    def test_computes_the_loss_ratio_curve(self):
        # manually computed results from V. Silva
        expected_curve = shapes.Curve([(0.085255, 0.988891),
                (0.255765, 0.82622606), (0.426275, 0.77686984),
                (0.596785, 0.52763345), (0.767295, 0.39346934)])

        self.assertEqual(expected_curve, compute_loss_ratio_curve(
                self.vuln_function_2, self.gmfs_1,
                None, None, 6))

        expected_curve = shapes.Curve([(0.0935225, 0.99326205),
                (0.2640675, 0.917915), (0.4346125, 0.77686984),
                (0.6051575, 0.52763345), (0.7757025, 0.22119922)])

        self.assertEqual(expected_curve, compute_loss_ratio_curve(
                self.vuln_function_2, self.gmfs_2,
                None, None, 6))

        expected_curve = shapes.Curve([(0.1047, 0.99326205),
                (0.2584, 0.89460078), (0.4121, 0.63212056),
                (0.5658, 0.39346934), (0.7195, 0.39346934)])

        self.assertEqual(expected_curve, compute_loss_ratio_curve(
                self.vuln_function_2, self.gmfs_3,
                None, None, 6))

        expected_curve = shapes.Curve([(0.09012, 0.99326205),
                (0.25551, 0.93607214), (0.4209, 0.77686984),
                (0.58629, 0.52763345), (0.75168, 0.39346934)])

        self.assertEqual(expected_curve, compute_loss_ratio_curve(
                self.vuln_function_2, self.gmfs_4,
                None, None, 6))

        expected_curve = shapes.Curve([(0.08089, 0.99326205),
                (0.23872, 0.95021293), (0.39655, 0.7134952),
                (0.55438, 0.52763345), (0.71221, 0.39346934)])

        self.assertEqual(expected_curve, compute_loss_ratio_curve(
                self.vuln_function_2, self.gmfs_5,
                None, None, 6))

        expected_curve = shapes.Curve([(0.0717025, 0.99326205),
                (0.2128575, 0.917915), (0.3540125, 0.82622606),
                (0.4951675, 0.77686984), (0.6363225, 0.39346934)])

        self.assertEqual(expected_curve, compute_loss_ratio_curve(
                self.vuln_function_2, self.gmfs_6,
                None, None, 6))

    def test_with_not_earthquakes_we_have_an_empty_curve(self):
        gmfs = dict(self.gmfs)
        gmfs["IMLs"] = ()

        curve = compute_loss_ratio_curve(
                self.vuln_function_1, gmfs, None, None, 25)

        self.assertEqual(shapes.EMPTY_CURVE, curve)

    def test_with_no_ground_motion_the_curve_is_a_single_point(self):
        gmfs = {"IMLs": (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
                "TSES": 900, "TimeSpan": 50}

        # sounds like a curve, but it's a point :-)
        expected_curve = shapes.Curve([
                (0.0, 0.0), (0.0, 0.0), (0.0, 0.0),
                (0.0, 0.0), (0.0, 0.0), (0.0, 0.0),
                (0.0, 0.0), (0.0, 0.0), (0.0, 0.0),
                (0.0, 0.0), (0.0, 0.0), (0.0, 0.0),
                (0.0, 0.0), (0.0, 0.0), (0.0, 0.0),
                (0.0, 0.0), (0.0, 0.0), (0.0, 0.0),
                (0.0, 0.0), (0.0, 0.0), (0.0, 0.0),
                (0.0, 0.0), (0.0, 0.0), (0.0, 0.0)])

        self.assertEqual(expected_curve, compute_loss_ratio_curve(
                self.vuln_function_1, gmfs, None, None, 25))

    def test_an_empty_distribution_produces_an_empty_aggregate_curve(self):
        self.assertEqual(
            shapes.EMPTY_CURVE, AggregateLossCurve().compute(0, 0, 25))

    def test_computes_the_aggregate_loss_curve(self):
        # no epsilon_provided is needed because the vulnerability
        # function has all the covs equal to zero
        loss_ratios = []
        for idx in range(6):
            lr = compute_loss_ratios(self.vuln_function_2, self.peb_gmfs[idx],
                                     None, self.assets[idx])
            loss_ratios.append(lr)

        aggregate_curve = AggregateLossCurve()

        for idx in range(6):
            aggregate_curve.append(loss_ratios[idx] * self.assets[idx].value)

        expected_losses = numpy.array((
            7.2636, 57.9264, 187.4893, 66.9082, 47.0280, 248.7796, 23.2329,
            121.3514, 177.4167, 259.2902, 77.7080, 127.7417, 18.9470, 339.5774,
            151.1763, 6.1881, 71.9168, 97.9514, 56.4720, 11.6513))

        self.assertTrue(numpy.allclose(expected_losses,
                                       aggregate_curve.losses))

        expected_curve = shapes.Curve([
            (39.52702042, 0.99326205), (106.20489077, 0.917915),
            (172.88276113, 0.77686984), (239.56063147, 0.52763345),
            (306.23850182, 0.22119922)])

        self.assertEqual(expected_curve, aggregate_curve.compute(200, 50, 6))

    def test_no_losses_without_gmfs(self):
        aggregate_curve = AggregateLossCurve()
        self.assertEqual(None, aggregate_curve.losses)

    def test_compute_bcr(self):
        cfg_path = helpers.demo_file(
            'probabilistic_event_based_risk/config.gem')
        helpers.delete_profile(self.job)
        job_profile, params, sections = engine.import_job_profile(
            cfg_path, self.job)
        job_profile.calc_mode = 'event_based_bcr'
        job_profile.interest_rate = 0.05
        job_profile.asset_life_expectancy = 50
        job_profile.region = GEOSGeometry(shapes.polygon_ewkt_from_coords(
            '0.0, 0.0, 0.0, 2.0, 2.0, 2.0, 2.0, 0.0'))
        job_profile.region_grid_spacing = 0.1
        job_profile.maximum_distance = 200.0
        job_profile.gmf_random_seed = None
        job_profile.save()

        params.update(dict(CALCULATION_MODE='Event Based BCR',
                           INTEREST_RATE='0.05',
                           ASSET_LIFE_EXPECTANCY='50',
                           MAXIMUM_DISTANCE='200.0',
                           REGION_VERTEX=('0.0, 0.0, 0.0, 2.0, '
                                          '2.0, 2.0, 2.0, 0.0'),
                           REGION_GRID_SPACING='0.1'))

        job_ctxt = engine.JobContext(
            params, self.job_id, sections=sections, oq_job_profile=job_profile)

        calculator = eb_core.EventBasedRiskCalculator(job_ctxt)

        self.block_id = 7
        SITE = shapes.Site(1.0, 1.0)
        block = Block(self.job_id, self.block_id, (SITE, SITE))
        block.to_kvs()

        location = GEOSGeometry(SITE.point.to_wkt())
        asset = models.ExposureData(exposure_model=self.emdl, taxonomy="ID",
                                    asset_ref=22.61, stco=1, reco=123.45,
                                    site=location)
        asset.save()

        calculator.compute_risk(self.block_id)

        result_key = kvs.tokens.bcr_block_key(self.job_id, self.block_id)
        result = kvs.get_value_json_decoded(result_key)
        expected_result = {'bcr': 0.0, 'eal_original': 0.0,
                           'eal_retrofitted': 0.0}
        helpers.assertDeepAlmostEqual(
            self, [[[1, 1], [[expected_result, "22.61"]]]], result)


class ClassicalPSHABasedTestCase(unittest.TestCase, helpers.DbTestCase):

    def setUp(self):
        self.block_id = 7
        self.job = self.setup_classic_job()
        self.job_id = self.job.id

    def tearDown(self):
        if self.job:
            self.teardown_job(self.job)

    def test_empty_loss_curve(self):
        self.assertEqual(compute_loss_curve(shapes.EMPTY_CURVE, None),
                shapes.EMPTY_CURVE)

    def test_a_loss_curve_is_not_defined_when_the_asset_is_invalid(self):
        self.assertEqual(compute_loss_curve(
                shapes.Curve([(0.1, 1.0), (0.2, 2.0), (0.3, 3.0)]),
                INVALID_ASSET_VALUE),
                shapes.EMPTY_CURVE)

    def test_loss_curve_computation(self):
        loss_ratio_curve = shapes.Curve([(0.1, 1.0), (0.2, 2.0), (0.3, 3.0)])
        loss_curve = compute_loss_curve(loss_ratio_curve, ASSET_VALUE)

        self.assertEqual(shapes.Curve([(0.1 * ASSET_VALUE, 1.0),
                (0.2 * ASSET_VALUE, 2.0), (0.3 * ASSET_VALUE, 3.0)]),
                loss_curve)

    def test_lrem_betadist_computation(self):

        # expected beta distributions provided by Vitor
        expected_beta_distributions = [
            [1.0000000, 1.0000000, 1.0000000, 1.0000000, 1.0000000],
            [0.9895151, 0.9999409, 1.0000000, 1.0000000, 1.0000000],
            [0.9175720, 0.9981966, 0.9999997, 1.0000000, 1.0000000],
            [0.7764311, 0.9887521, 0.9999922, 1.0000000, 1.0000000],
            [0.6033381, 0.9633258, 0.9999305, 1.0000000, 1.0000000],
            [0.4364471, 0.9160514, 0.9996459, 1.0000000, 1.0000000],
            [0.2975979, 0.8460938, 0.9987356, 1.0000000, 1.0000000],
            [0.1931667, 0.7574557, 0.9964704, 1.0000000, 1.0000000],
            [0.1202530, 0.6571491, 0.9917729, 0.9999999, 1.0000000],
            [0.0722091, 0.5530379, 0.9832939, 0.9999997, 1.0000000],
            [0.0420056, 0.4521525, 0.9695756, 0.9999988, 1.0000000],
            [0.0130890, 0.2790107, 0.9213254, 0.9999887, 1.0000000],
            [0.0037081, 0.1564388, 0.8409617, 0.9999306, 1.0000000],
            [0.0009665, 0.0805799, 0.7311262, 0.9996882, 1.0000000],
            [0.0002335, 0.0384571, 0.6024948, 0.9988955, 1.0000000],
            [0.0000526, 0.0171150, 0.4696314, 0.9967629, 1.0000000],
            [0.0000022, 0.0027969, 0.2413923, 0.9820831, 1.0000000],
            [0.0000001, 0.0003598, 0.0998227, 0.9364072, 1.0000000],
            [0.0000000, 0.0000367, 0.0334502, 0.8381920, 0.9999995],
            [0.0000000, 0.0000030, 0.0091150, 0.6821293, 0.9999959],
            [0.0000000, 0.0000002, 0.0020162, 0.4909782, 0.9999755],
            [0.0000000, 0.0000000, 0.0000509, 0.1617086, 0.9995033],
            [0.0000000, 0.0000000, 0.0000005, 0.0256980, 0.9945488],
            [0.0000000, 0.0000000, 0.0000000, 0.0016231, 0.9633558],
            [0.0000000, 0.0000000, 0.0000000, 0.0000288, 0.8399534],
            [0.0000000, 0.0000000, 0.0000000, 0.0000001, 0.5409583],
            [0.0000000, 0.0000000, 0.0000000, 0.0000000, 0.3413124],
            [0.0000000, 0.0000000, 0.0000000, 0.0000000, 0.1589844],
            [0.0000000, 0.0000000, 0.0000000, 0.0000000, 0.0421052],
            [0.0000000, 0.0000000, 0.0000000, 0.0000000, 0.0027925],
            [0.0000000, 0.0000000, 0.0000000, 0.0000000, 0.0000000]]

        mean_loss_ratios = [0.050, 0.100, 0.200, 0.400, 0.800]
        covs = [0.500, 0.400, 0.300, 0.200, 0.100]
        imls = [0.100, 0.200, 0.300, 0.450, 0.600]

        vuln_function = shapes.VulnerabilityFunction(imls,
                mean_loss_ratios, covs)
        # computes lrem with probabilisticDistribution='BT' (Beta Distribution)
        # set in the Vulnerabilty Function
        lrem = classical_core._compute_lrem(vuln_function, 5, 'BT')

        helpers.assertDeepAlmostEqual(self, expected_beta_distributions,
            lrem, delta=0.0005)

    def test_lrem_po_computation(self):
        hazard_curve = shapes.Curve([
              (0.01, 0.99), (0.08, 0.96),
              (0.17, 0.89), (0.26, 0.82),
              (0.36, 0.70), (0.55, 0.40),
              (0.70, 0.01)])

        # pre computed values just use one intermediate
        # values between the imls
        lrem_steps = 2

        imls = [0.1, 0.2, 0.4, 0.6]
        loss_ratios = [0.05, 0.08, 0.2, 0.4]
        covs = [0.5, 0.3, 0.2, 0.1]
        vuln_function = shapes.VulnerabilityFunction(imls, loss_ratios, covs)

        lrem = classical_core._compute_lrem(vuln_function, lrem_steps)

        lrem_po = classical_core._compute_lrem_po(vuln_function,
                lrem, hazard_curve)

        self.assertTrue(numpy.allclose(0.07, lrem_po[0][0], atol=0.005))
        self.assertTrue(numpy.allclose(0.06, lrem_po[1][0], atol=0.005))
        self.assertTrue(numpy.allclose(0.13, lrem_po[0][1], atol=0.005))
        self.assertTrue(numpy.allclose(0.47, lrem_po[5][3], atol=0.005))
        self.assertTrue(numpy.allclose(0.23, lrem_po[8][3], atol=0.005))
        self.assertTrue(numpy.allclose(0.00, lrem_po[10][0], atol=0.005))

    def test_pes_from_imls(self):
        hazard_curve = shapes.Curve([
              (0.01, 0.99), (0.08, 0.96),
              (0.17, 0.89), (0.26, 0.82),
              (0.36, 0.70), (0.55, 0.40),
              (0.70, 0.01)])

        expected_pes = [0.9729, 0.9056, 0.7720, 0.4789, 0.0100]
        imls = [0.05, 0.15, 0.3, 0.5, 0.7]

        self.assertTrue(numpy.allclose(numpy.array(expected_pes),
                classical_core._compute_pes_from_imls(hazard_curve, imls),
                atol=0.00005))

    def test_pes_to_pos(self):
        hazard_curve = shapes.Curve([
              (0.01, 0.99), (0.08, 0.96),
              (0.17, 0.89), (0.26, 0.82),
              (0.36, 0.70), (0.55, 0.40),
              (0.70, 0.01)])

        expected_pos = [0.0673, 0.1336, 0.2931, 0.4689]
        pes = [0.05, 0.15, 0.3, 0.5, 0.7]

        self.assertTrue(numpy.allclose(expected_pos,
                classical_core._convert_pes_to_pos(hazard_curve, pes),
                atol=0.00005))

    def test_bin_width_from_imls(self):
        imls = [0.1, 0.2, 0.4, 0.6]
        loss_ratios = [0.05, 0.08, 0.2, 0.4]
        covs = [0.5, 0.5, 0.5, 0.5]

        vuln_function = shapes.VulnerabilityFunction(imls, loss_ratios, covs)

        expected_steps = [0.05, 0.15, 0.3, 0.5, 0.7]

        self.assertTrue(numpy.allclose(expected_steps,
                classical_core._compute_imls(vuln_function)))

    def test_end_to_end(self):
        # manually computed values by Vitor Silva
        lrem_steps = 2
        hazard_curve = shapes.Curve([
              (0.01, 0.99), (0.08, 0.96),
              (0.17, 0.89), (0.26, 0.82),
              (0.36, 0.70), (0.55, 0.40),
              (0.70, 0.01)])

        imls = [0.1, 0.2, 0.4, 0.6]
        loss_ratios = [0.05, 0.08, 0.2, 0.4]
        covs = [0.5, 0.3, 0.2, 0.1]
        vuln_function = shapes.VulnerabilityFunction(imls, loss_ratios, covs)

        loss_ratio_curve = classical_core.compute_loss_ratio_curve(
                vuln_function, hazard_curve, lrem_steps)

        lr_curve_expected = shapes.Curve([(0.0, 0.96),
                (0.025, 0.96), (0.05, 0.91), (0.065, 0.87),
                (0.08, 0.83), (0.14, 0.75), (0.2, 0.60),
                (0.3, 0.47), (0.4, 0.23), (0.7, 0.00),
                (1.0, 0.00)])

        for x_value in lr_curve_expected.abscissae:
            self.assertTrue(numpy.allclose(
                    lr_curve_expected.ordinate_for(x_value),
                    loss_ratio_curve.ordinate_for(x_value), atol=0.005))

    def test_splits_single_interval_with_no_steps_between(self):
        self.assertTrue(
            numpy.allclose(numpy.array([1.0, 2.0]),
                           classical_core._split_loss_ratios([1.0, 2.0], 1)))

    def test_splits_single_interval_with_a_step_between(self):
        self.assertTrue(
            numpy.allclose(numpy.array([1.0, 1.5, 2.0]),
                           classical_core._split_loss_ratios([1.0, 2.0], 2)))

    def test_splits_single_interval_with_steps_between(self):
        self.assertTrue(numpy.allclose(numpy.array(
            [1.0, 1.25, 1.50, 1.75, 2.0]),
            classical_core._split_loss_ratios([1.0, 2.0], 4)))

    def test_splits_multiple_intervals_with_a_step_between(self):
        self.assertTrue(numpy.allclose(numpy.array(
            [1.0, 1.5, 2.0, 2.5, 3.0]),
            classical_core._split_loss_ratios([1.0, 2.0, 3.0], 2)))

    def test_splits_multiple_intervals_with_steps_between(self):
        self.assertTrue(numpy.allclose(numpy.array(
            [1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0]),
            classical_core._split_loss_ratios([1.0, 2.0, 3.0], 4)))

    def test_loss_ratio_curve_is_none_with_unknown_vuln_function(self):

        the_job = helpers.create_job({})
        calculator = classical_core.ClassicalRiskCalculator(the_job)

        # empty vuln curves
        vuln_curves = {}

        # "empty" asset
        asset = models.ExposureData(taxonomy="ID", asset_ref=1)

        self.assertEqual(None, calculator.compute_loss_ratio_curve(
                         None, asset, None, vuln_curves))

    def _compute_risk_classical_psha_setup(self):
        SITE = shapes.Site(1.0, 1.0)
        # deletes all keys from kvs
        kvs.get_client().flushall()

        # at the moment the hazard part doesn't do exp on the 'x'
        # so it's done on the risk part. To adapt the calculation
        # we do the reverse of the exp, i.e. log(x)
        self.hazard_curve = [
            (SITE,
             {'IMLValues': [0.001, 0.080, 0.170, 0.260, 0.360,
                            0.550, 0.700],
              'PoEValues': [0.99, 0.96, 0.89, 0.82, 0.70, 0.40, 0.01],
              'statistics': 'mean'})]

        # Vitor provided this Vulnerability Function
        imls_1 = [0.03, 0.04, 0.07, 0.1, 0.12, 0.22, 0.37, 0.52]
        loss_ratios_1 = [0.001, 0.022, 0.051, 0.08, 0.1, 0.2, 0.405, 0.700]
        covs_1 = [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]
        self.vuln_function = shapes.VulnerabilityFunction(imls_1,
            loss_ratios_1, covs_1)

        imls_2 = [0.1, 0.2, 0.4, 0.6]
        loss_ratios_2 = [0.05, 0.08, 0.2, 0.4]
        covs_2 = [0.5, 0.3, 0.2, 0.1]
        self.vuln_function_2 = shapes.VulnerabilityFunction(imls_2,
            loss_ratios_2, covs_2)

        self.asset_1 = {"taxonomy": "ID", "assetValue": 124.27}

        self.region = shapes.RegionConstraint.from_simple(
                (0.0, 0.0), (2.0, 2.0))

        block = Block(self.job_id, self.block_id, (SITE, SITE))
        block.to_kvs()

        writer = hazard.HazardCurveDBWriter('test_path.xml', self.job_id)
        writer.serialize(self.hazard_curve)

        kvs.set_value_json_encoded(
                kvs.tokens.vuln_key(self.job_id),
                {"ID": self.vuln_function.to_json()})
        kvs.set_value_json_encoded(
                kvs.tokens.vuln_key(self.job_id, retrofitted=True),
                {"ID": self.vuln_function.to_json()})

    def test_compute_risk_in_the_classical_psha_calculator(self):
        """
            tests ClassicalRiskCalculator.compute_risk by retrieving
            all the loss curves in the kvs and checks their presence
        """
        helpers.delete_profile(self.job)
        cls_risk_cfg = helpers.demo_file(
            'classical_psha_based_risk/config.gem')
        job_profile, params, sections = engine.import_job_profile(
            cls_risk_cfg, self.job)

        # We need to adjust a few of the parameters for this test:
        params['REGION_VERTEX'] = '0.0, 0.0, 0.0, 2.0, 2.0, 2.0, 2.0, 0.0'
        job_profile.region = GEOSGeometry(shapes.polygon_ewkt_from_coords(
            params['REGION_VERTEX']))
        job_profile.save()

        job_ctxt = engine.JobContext(
            params, self.job_id, sections=sections, oq_job_profile=job_profile)

        self._compute_risk_classical_psha_setup()

        calculator = classical_core.ClassicalRiskCalculator(job_ctxt)
        calculator.vuln_curves = {"ID": self.vuln_function}

        block = Block.from_kvs(self.job_id, self.block_id)

        # computes the loss curves and puts them in kvs
        self.assertTrue(calculator.compute_risk(self.block_id))

        for point in block.grid(job_ctxt.region):
            assets = BaseRiskCalculator.assets_for_cell(
                self.job_id, point.site)
            for asset in assets:
                loss_ratio_key = kvs.tokens.loss_ratio_key(
                    self.job_id, point.row, point.column, asset.asset_ref)

                self.assertTrue(kvs.get_client().get(loss_ratio_key))

                loss_key = kvs.tokens.loss_curve_key(
                    self.job_id, point.row, point.column, asset.asset_ref)

                self.assertTrue(kvs.get_client().get(loss_key))

    def test_compute_bcr_in_the_classical_psha_calculator(self):
        self._compute_risk_classical_psha_setup()
        helpers.delete_profile(self.job)
        bcr_config = helpers.demo_file('benefit_cost_ratio/config.gem')
        job_profile, params, sections = engine.import_job_profile(
            bcr_config, self.job)

        # We need to adjust a few of the parameters for this test:
        job_profile.imls = [
            0.005, 0.007, 0.0098, 0.0137, 0.0192, 0.0269, 0.0376, 0.0527,
            0.0738, 0.103, 0.145, 0.203, 0.284, 0.397, 0.556, 0.778]
        params['ASSET_LIFE_EXPECTANCY'] = '50'
        job_profile.asset_life_expectancy = 50
        params['REGION_VERTEX'] = '0.0, 0.0, 0.0, 2.0, 2.0, 2.0, 2.0, 0.0'
        job_profile.region = GEOSGeometry(shapes.polygon_ewkt_from_coords(
            params['REGION_VERTEX']))
        job_profile.save()

        job_ctxt = engine.JobContext(
            params, self.job_id, sections=sections, oq_job_profile=job_profile)

        calculator = classical_core.ClassicalRiskCalculator(job_ctxt)

        [input] = models.inputs4job(self.job.id, input_type="exposure")
        emdl = models.ExposureModel(
            owner=self.job.owner, input=input,
            description="c-psha test exposure model",
            category="c-psha power plants", stco_unit="watt",
            stco_type="aggregated", reco_unit="joule", reco_type="aggregated")
        emdl.save()

        Block.from_kvs(self.job_id, self.block_id)
        asset = models.ExposureData(exposure_model=emdl, taxonomy="ID",
                                    asset_ref=22.61, stco=1, reco=123.45,
                                    site=GEOSGeometry("POINT(1.0 1.0)"))
        asset.save()
        calculator.compute_risk(self.block_id)

        result_key = kvs.tokens.bcr_block_key(self.job_id, self.block_id)
        res = kvs.get_value_json_decoded(result_key)
        expected_result = {'bcr': 0.0, 'eal_original': 0.003032,
                           'eal_retrofitted': 0.003032}
        helpers.assertDeepAlmostEqual(
            self, res, [[[1, 1], [[expected_result, "22.61"]]]])

    def test_splits_with_real_values_from_turkey(self):
        loss_ratios = [0.0, 1.96E-15, 2.53E-12, 8.00E-10, 8.31E-08, 3.52E-06,
                7.16E-05, 7.96E-04, 5.37E-03, 2.39E-02, 7.51E-02, 1.77E-01]

        result = [0.0, 3.9199999999999996e-16,
                7.8399999999999992e-16,
                1.1759999999999998e-15, 1.5679999999999998e-15,
                1.9599999999999999e-15, 5.0756799999999998e-13,
                1.0131759999999998e-12, 1.5187839999999998e-12,
                2.024392e-12, 2.5299999999999999e-12,
                1.6202400000000001e-10,
                3.2151800000000003e-10, 4.8101199999999999e-10,
                6.4050600000000006e-10, 8.0000000000000003e-10,
                1.726e-08, 3.372e-08, 5.0179999999999997e-08,
                6.6639999999999993e-08, 8.3099999999999996e-08,
                7.7048000000000005e-07, 1.4578600000000002e-06,
                2.1452400000000005e-06, 2.8326200000000003e-06,
                3.5200000000000002e-06, 1.7136000000000003e-05,
                3.0752000000000006e-05, 4.4368000000000013e-05,
                5.7984000000000013e-05, 7.1600000000000006e-05,
                0.00021648000000000001, 0.00036136000000000002,
                0.00050624000000000003, 0.00065112000000000004,
                0.00079600000000000005, 0.0017108000000000002,
                0.0026256000000000001, 0.0035404, 0.0044552000000000003,
                0.0053699999999999998, 0.0090760000000000007, 0.012782,
                0.016487999999999999, 0.020194, 0.023900000000000001,
                0.034140000000000004, 0.044380000000000003,
                0.054620000000000002, 0.064860000000000001, 0.0751,
                0.095479999999999995, 0.11585999999999999, 0.13624,
                0.15661999999999998, 0.17699999999999999]

        self.assertTrue(
            numpy.allclose(numpy.array(result),
                           classical_core._split_loss_ratios(loss_ratios, 5)))

    def test_splits_with_real_values_from_taiwan(self):
        loss_ratios = [0.0, 1.877E-20, 8.485E-17, 8.427E-14,
                2.495E-11, 2.769E-09, 1.372E-07, 3.481E-06,
                5.042E-05, 4.550E-04, 2.749E-03, 1.181E-02]

        # testing just the length of the result
        self.assertEqual(
            56, len(classical_core._split_loss_ratios(loss_ratios, 5)))

    def test_ratio_is_zero_if_probability_is_too_high(self):
        loss_curve = shapes.Curve([(0.21, 0.131), (0.24, 0.108),
                (0.27, 0.089), (0.30, 0.066)])

        self.assertEqual(0.0,
                _compute_conditional_loss(loss_curve, 0.200))

    def test_ratio_is_max_if_probability_is_too_low(self):
        loss_curve = shapes.Curve([(0.21, 0.131), (0.24, 0.108),
                (0.27, 0.089), (0.30, 0.066)])

        self.assertEqual(0.30,
                _compute_conditional_loss(loss_curve, 0.050))

    def test_conditional_loss_duplicates(self):
        # we feed _compute_conditional_loss with some duplicated data to see if
        # it's handled correctly

        closs1 = _compute_conditional_loss(shapes.Curve([(0.21, 0.131),
        (0.24, 0.108), (0.27, 0.089), (0.30, 0.066)]), 0.100)

        # duplicated y values, different x values, (0.19, 0.131), (0.20, 0.131)
        #should be skipped
        closs2 = _compute_conditional_loss(shapes.Curve([(0.19, 0.131),
            (0.20, 0.131), (0.21, 0.131), (0.24, 0.108), (0.27, 0.089),
            (0.30, 0.066)]), 0.100)

        self.assertEquals(closs1, closs2)

    def test_conditional_loss_computation(self):
        loss_curve = shapes.Curve([(0.21, 0.131), (0.24, 0.108),
                (0.27, 0.089), (0.30, 0.066)])

        self.assertAlmostEqual(0.2526, _compute_conditional_loss(
                loss_curve, 0.100), 4)

    def test_loss_ratio_pe_mid_curve_computation(self):
        loss_ratio_curve = shapes.Curve([(0, 0.3460), (0.06, 0.12),
                (0.12, 0.057), (0.18, 0.04),
                (0.24, 0.019), (0.3, 0.009), (0.45, 0)])

        expected_curve = shapes.Curve([(0.0300, 0.2330), (0.0900, 0.0885),
                (0.1500, 0.0485), (0.2100, 0.0295),
                (0.2700, 0.0140), (0.3750, 0.0045)])

        self.assertEqual(expected_curve,
                _compute_mid_mean_pe(loss_ratio_curve))

    def test_loss_ratio_po_computation(self):
        loss_ratio_pe_mid_curve = shapes.Curve([(0.0300, 0.2330),
                (0.0900, 0.0885), (0.1500, 0.0485), (0.2100, 0.0295),
                (0.2700, 0.0140), (0.3750, 0.0045)])

        expected_curve = shapes.Curve([(0.0600, 0.1445),
                (0.1200, 0.0400), (0.1800, 0.0190), (0.2400, 0.0155),
                (0.3225, 0.0095)])

        self.assertEqual(expected_curve,
                _compute_mid_po(loss_ratio_pe_mid_curve))

    def test_mean_loss_ratio_computation(self):
        loss_ratio_curve = shapes.Curve([(0, 0.3460), (0.06, 0.12),
                (0.12, 0.057), (0.18, 0.04),
                (0.24, 0.019), (0.3, 0.009), (0.45, 0)])

        # TODO (ac): Check the difference between 0.023305 and 0.023673
        self.assertAlmostEqual(0.023305,
                               compute_mean_loss(loss_ratio_curve), 3)


class ScenarioEventBasedTestCase(unittest.TestCase, helpers.DbTestCase):

    job = None
    emdl = None

    @classmethod
    def setUpClass(cls):
        path = os.path.join(helpers.SCHEMA_EXAMPLES_DIR, "SEB-exposure.yaml")
        inputs = [("exposure", path)]
        cls.job = cls.setup_classic_job(inputs=inputs)
        [input] = models.inputs4job(cls.job.id, input_type="exposure",
                                    path=path)
        owner = models.OqUser.objects.get(user_name="openquake")
        cls.emdl = models.ExposureModel(
            owner=owner, input=input, description="SEB test exposure model",
            category="SEB factory buildings", stco_unit="screws",
            stco_type="aggregated")
        cls.emdl.save()

    @classmethod
    def tearDownClass(cls):
        cls.teardown_job(cls.job)

    def setUp(self):
        imls = [0.10, 0.30, 0.50, 1.00]
        loss_ratios = [0.05, 0.10, 0.15, 0.30]
        covs = [0.30, 0.30, 0.20, 0.20]
        self.vuln_function = shapes.VulnerabilityFunction(imls, loss_ratios,
            covs)

        self.epsilons = [0.5377, 1.8339, -2.2588, 0.8622, 0.3188, -1.3077,
                    -0.4336, 0.3426, 3.5784, 2.7694]

        self.gmfs = {"IMLs": (0.1576, 0.9706, 0.9572, 0.4854, 0.8003,
                     0.1419, 0.4218, 0.9157, 0.7922, 0.9595)}

    def test_computes_the_mean_loss_from_loss_ratios(self):
        asset = models.ExposureData(exposure_model=self.emdl, stco=1000)
        loss_ratios = numpy.array([0.20, 0.05, 0.10, 0.05, 0.10])

        self.assertEqual(100, scenario._mean_loss_from_loss_ratios(
                         loss_ratios, asset))

    def test_computes_the_mean_loss(self):
        asset = models.ExposureData(exposure_model=self.emdl, stco=10)
        epsilon_provider = EpsilonProvider(asset, self.epsilons)

        self.assertTrue(numpy.allclose(2.4887999999999999,
                        scenario.compute_mean_loss(
                            self.vuln_function, self.gmfs, epsilon_provider,
                            asset),
                        atol=0.0001))

    def test_computes_the_stddev_loss_from_loss_ratios(self):
        asset = models.ExposureData(exposure_model=self.emdl, stco=1000)
        loss_ratios = numpy.array([0.20, 0.05, 0.10, 0.05, 0.10])

        self.assertTrue(numpy.allclose(61.237,
                        scenario._stddev_loss_from_loss_ratios(
                        loss_ratios, asset), atol=0.001))

    def test_computes_the_stddev_loss(self):
        asset = models.ExposureData(exposure_model=self.emdl, stco=10)
        epsilon_provider = EpsilonProvider(asset, self.epsilons)

        self.assertTrue(numpy.allclose(1.631,
                        scenario.compute_stddev_loss(
                            self.vuln_function, self.gmfs, epsilon_provider,
                            asset),
                        atol=0.002))

    def test_calls_the_loss_ratios_calculator_correctly(self):
        gmfs = {"IMLs": ()}
        epsilon_provider = object()
        vuln_model = {"ID": self.vuln_function}
        asset = models.ExposureData(exposure_model=self.emdl, taxonomy="ID",
                                    stco=10)

        def loss_ratios_calculator(
            vuln_function, ground_motion_field_set, epsilon_provider, asset):

            self.assertTrue(asset == asset)
            self.assertTrue(epsilon_provider == epsilon_provider)
            self.assertTrue(ground_motion_field_set == gmfs)
            self.assertTrue(vuln_function == self.vuln_function)

            return numpy.array([])

        calculator = scenario.SumPerGroundMotionField(
            vuln_model, epsilon_provider, lr_calculator=loss_ratios_calculator)

        calculator.add(gmfs, asset)

    def test_keeps_track_of_the_sum_of_the_losses(self):
        loss_ratios = [
            [0.140147324, 0.151530140, 0.016176042, 0.101786402, 0.025190577],
            [0.154760019, 0.001203867, 0.370820698, 0.220145117, 0.067291408],
            [0.010945875, 0.413257970, 0.267141193, 0.040157738, 0.001981645]]

        def loss_ratios_calculator(
            vuln_function, ground_motion_field_set, epsilon_provider, asset):

            return loss_ratios.pop(0)

        vuln_model = {"ID": self.vuln_function}
        asset = models.ExposureData(exposure_model=self.emdl, taxonomy="ID",
                                    stco=100)

        calculator = scenario.SumPerGroundMotionField(
            vuln_model, None, lr_calculator=loss_ratios_calculator)

        self.assertTrue(numpy.allclose([], calculator.losses))

        calculator.add(None, asset)
        asset = models.ExposureData(exposure_model=self.emdl, taxonomy="ID",
                                    stco=300)
        calculator.add(None, asset)
        asset = models.ExposureData(exposure_model=self.emdl, taxonomy="ID",
                                    stco=200)
        calculator.add(None, asset)

        expected_sum = [62.63191284, 98.16576808,
                        166.2920523, 84.25372286, 23.10280904]

        self.assertTrue(numpy.allclose(expected_sum, calculator.losses))

    def test_handles_empty_losses_correctly(self):
        calculator = scenario.SumPerGroundMotionField(None, None)
        losses = numpy.array([1.0, 2.0])

        self.assertTrue(numpy.allclose([], calculator.losses))

        calculator.sum_losses(numpy.array([]))
        calculator.sum_losses(losses)
        calculator.sum_losses(numpy.array([]))
        calculator.sum_losses(losses)
        calculator.sum_losses(numpy.array([]))

        self.assertTrue(numpy.allclose([2.0, 4.0], calculator.losses))

    def test_computes_the_mean_from_the_current_sum(self):
        calculator = scenario.SumPerGroundMotionField(None, None)

        sum_of_losses = numpy.array(
            [62.63191284, 98.16576808, 166.2920523, 84.25372286, 23.10280904])

        calculator.losses = sum_of_losses

        self.assertTrue(numpy.allclose(86.88925302, calculator.mean))

    def test_computes_the_stddev_from_the_current_sum(self):
        calculator = scenario.SumPerGroundMotionField(None, None)

        sum_of_losses = numpy.array(
            [62.63191284, 98.16576808, 166.2920523, 84.25372286, 23.10280904])

        calculator.losses = sum_of_losses

        self.assertTrue(numpy.allclose(52.66886967, calculator.stddev))

    def test_skips_the_distribution_with_unknown_vuln_function(self):
        """The asset refers to an unknown vulnerability function.

        In case the asset defines an unknown vulnerability function
        (key 'taxonomy') the given ground
        motion field set is ignored.
        """
        vuln_model = {"ID": self.vuln_function}
        asset = models.ExposureData(exposure_model=self.emdl, taxonomy="XX",
                                    asset_ref="ID", stco=100)

        calculator = scenario.SumPerGroundMotionField(vuln_model, None)

        self.assertTrue(numpy.allclose([], calculator.losses))

        calculator.add(None, asset)

        # still None, no losses are added
        self.assertTrue(numpy.allclose([], calculator.losses))


class RiskCommonTestCase(unittest.TestCase):

    def test_compute_bcr(self):
        # numbers are proven to be correct
        eal_orig = 0.00838
        eal_retrofitted = 0.00587
        retrofitting_cost = 0.1
        interest = 0.05
        life_expectancy = 40
        expected_result = 0.43405

        result = compute_bcr(eal_orig, eal_retrofitted, interest,
                             life_expectancy, retrofitting_cost)
        self.assertAlmostEqual(result, expected_result, delta=2e-5)


class RiskJobGeneralTestCase(unittest.TestCase):
    def _make_job(self, params):
        self.job = helpers.create_job(params, base_path=".")
        self.job_id = self.job.job_id
        self.job.to_kvs()

    def _prepare_bcr_result(self):
        self.job.blocks_keys = [19, 20]
        kvs.set_value_json_encoded(kvs.tokens.bcr_block_key(self.job_id, 19), [
            ((-1.1, 19.0), [
                ({'bcr': 35.1, 'eal_original': 12.34, 'eal_retrofitted': 4},
                 'assetID-191'),
                ({'bcr': 35.2, 'eal_original': 2.5, 'eal_retrofitted': 2.2},
                 'assetID-192'),
            ])
        ])
        kvs.set_value_json_encoded(kvs.tokens.bcr_block_key(self.job_id, 20), [
            ((2.3, 20.0), [
                ({'bcr': 35.1, 'eal_original': 1.23, 'eal_retrofitted': 0.3},
                 'assetID-201'),
                ({'bcr': 35.2, 'eal_original': 4, 'eal_retrofitted': 0.4},
                 'assetID-202'),
            ])
        ])

    def test_asset_bcr_per_site(self):
        self._make_job({})
        self._prepare_bcr_result()

        job = BaseRiskCalculator(self.job)

        bcr_per_site = job.asset_bcr_per_site()
        self.assertEqual(bcr_per_site, [
            (shapes.Site(-1.1, 19.0), [
                [{u'bcr': 35.1, 'eal_original': 12.34, 'eal_retrofitted': 4},
                 u'assetID-191'],
                [{u'bcr': 35.2, 'eal_original': 2.5, 'eal_retrofitted': 2.2},
                 u'assetID-192']
            ]),
            (shapes.Site(2.3, 20.0), [
                [{u'bcr': 35.1, 'eal_original': 1.23, 'eal_retrofitted': 0.3},
                 u'assetID-201'],
                [{u'bcr': 35.2, 'eal_original': 4, 'eal_retrofitted': 0.4},
                 u'assetID-202']
            ])
        ])

    def test_write_output_bcr(self):
        self._make_job({})
        self._prepare_bcr_result()

        job = ProbabilisticRiskCalculator(self.job)

        expected_result = """\
<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml"
      xmlns="http://openquake.org/xmlns/nrml/0.3"
      gml:id="undefined">
  <riskResult gml:id="undefined">
    <benefitCostRatioMap gml:id="undefined" endBranchLabel="undefined"
                         lossCategory="undefined" unit="undefined"
                         interestRate="0.12" assetLifeExpectancy="50">
      <BCRNode gml:id="mn_1">
        <site>
          <gml:Point srsName="epsg:4326">
            <gml:pos>-1.1 19.0</gml:pos>
          </gml:Point>
        </site>
        <benefitCostRatioValue assetRef="assetID-191">
          <expectedAnnualLossOriginal>12.34</expectedAnnualLossOriginal>
          <expectedAnnualLossRetrofitted>4</expectedAnnualLossRetrofitted>
          <benefitCostRatio>35.1</benefitCostRatio>
        </benefitCostRatioValue>
        <benefitCostRatioValue assetRef="assetID-192">
          <expectedAnnualLossOriginal>2.5</expectedAnnualLossOriginal>
          <expectedAnnualLossRetrofitted>2.2</expectedAnnualLossRetrofitted>
          <benefitCostRatio>35.2</benefitCostRatio>
        </benefitCostRatioValue>
      </BCRNode>
      <BCRNode gml:id="mn_2">
        <site>
          <gml:Point srsName="epsg:4326">
            <gml:pos>2.3 20.0</gml:pos>
          </gml:Point>
        </site>
        <benefitCostRatioValue assetRef="assetID-201">
          <expectedAnnualLossOriginal>1.23</expectedAnnualLossOriginal>
          <expectedAnnualLossRetrofitted>0.3</expectedAnnualLossRetrofitted>
          <benefitCostRatio>35.1</benefitCostRatio>
        </benefitCostRatioValue>
        <benefitCostRatioValue assetRef="assetID-202">
          <expectedAnnualLossOriginal>4</expectedAnnualLossOriginal>
          <expectedAnnualLossRetrofitted>0.4</expectedAnnualLossRetrofitted>
          <benefitCostRatio>35.2</benefitCostRatio>
        </benefitCostRatioValue>
      </BCRNode>
    </benefitCostRatioMap>
  </riskResult>
</nrml>"""

        output_dir = tempfile.mkdtemp()
        try:
            job.job_ctxt.params = {'OUTPUT_DIR': output_dir,
                                       'INTEREST_RATE': '0.12',
                                       'ASSET_LIFE_EXPECTANCY': '50'}
            job.job_ctxt._base_path = '.'

            resultfile = os.path.join(output_dir, 'bcr-map.xml')

            try:
                job.write_output_bcr()
                result = open(resultfile).read()
            finally:
                if os.path.exists(resultfile):
                    os.remove(resultfile)
        finally:
            os.rmdir(output_dir)

        result = StringIO(result)
        expected_result = StringIO(expected_result)

        events1 = [(elem.tag, elem.attrib, elem.text)
                   for (event, elem) in etree.iterparse(result)]
        events2 = [(elem.tag, elem.attrib, elem.text)
                   for (event, elem) in etree.iterparse(expected_result)]
        self.assertEqual(events1, events2)
