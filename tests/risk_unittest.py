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
import json
import mock
import numpy
import unittest
from math import log

from openquake import job
from openquake import kvs
from openquake import shapes
from tests.utils import helpers

from openquake.risk.job import aggregate_loss_curve as aggregate
from openquake.risk.job.general import Block
from openquake.risk.job.classical_psha import ClassicalPSHABasedMixin
from openquake.risk import probabilistic_event_based as prob
from openquake.risk import classical_psha_based as psha
from openquake.risk import deterministic_event_based as det
from openquake.risk import common


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


class ProbabilisticEventBasedTestCase(unittest.TestCase):

    def setUp(self):
        imls_1 = [0.01, 0.04, 0.07, 0.1, 0.12, 0.22, 0.37, 0.52]
        loss_ratios_1 = [0.001, 0.022, 0.051, 0.08, 0.1, 0.2, 0.405, 0.7]
        covs_1 = [0.0] * 8
        self.vuln_function_1 = shapes.VulnerabilityFunction(imls_1,
            loss_ratios_1, covs_1)

        self.gmfs = GMFs

        self.cum_histogram = numpy.array([112, 46, 26, 18, 14,
                12, 8, 7, 7, 6, 5, 4, 4, 4, 4, 4, 2, 1,
                1, 1, 1, 1, 1, 1])

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
        self.vuln_function_2 = shapes.VulnerabilityFunction(imls_2,
            loss_ratios_2, covs_2)

        self.job_id = 1234

        self.gmfs_1 = {"IMLs": (0.1439, 0.1821, 0.5343, 0.171, 0.2177,
                0.6039, 0.0618, 0.186, 0.5512, 1.2602, 0.2824, 0.2693,
                0.1705, 0.8453, 0.6355, 0.0721, 0.2475, 0.1601, 0.3544,
                0.1756), "TSES": 200, "TimeSpan": 50}

        self.asset_1 = {"vulnerabilityFunctionReference": "ID",
                "assetValue": 22.61}

        self.gmfs_2 = {"IMLs": (0.1507, 0.2656, 0.5422, 0.3685, 0.3172,
                0.6604, 0.1182, 0.1545, 0.7613, 0.5246, 0.2428, 0.2882,
                0.2179, 1.2939, 0.6042, 0.1418, 0.3637, 0.222, 0.3613,
                0.113), "TSES": 200, "TimeSpan": 50}

        self.asset_2 = {"vulnerabilityFunctionReference": "ID",
                "assetValue": 124.27}

        self.gmfs_3 = {"IMLs": (0.156, 0.3158, 0.3968, 0.2827, 0.1915, 0.5862,
                0.1438, 0.2114, 0.5101, 1.0097, 0.226, 0.3443, 0.1693,
                1.0754, 0.3533, 0.1461, 0.347, 0.2665, 0.2977, 0.2925),
                "TSES": 200, "TimeSpan": 50}

        self.asset_3 = {"vulnerabilityFunctionReference": "ID",
                "assetValue": 42.93}

        self.gmfs_4 = {"IMLs": (0.1311, 0.3566, 0.4895, 0.3647, 0.2313,
                0.9297, 0.2337, 0.2862, 0.5278, 0.6603, 0.3537, 0.2997,
                0.1097, 1.1875, 0.4752, 0.1575, 0.4009, 0.2519, 0.2653,
                0.1394), "TSES": 200, "TimeSpan": 50}

        self.asset_4 = {"vulnerabilityFunctionReference": "ID",
                "assetValue": 29.37}

        self.gmfs_5 = {"IMLs": (0.0879, 0.2895, 0.465, 0.2463, 0.1862, 0.763,
                0.2189, 0.3324, 0.3215, 0.6406, 0.5014, 0.3877, 0.1318, 1.0545,
                0.3035, 0.1118, 0.2981, 0.3492, 0.2406, 0.1043),
                "TSES": 200, "TimeSpan": 50}

        self.asset_5 = {"vulnerabilityFunctionReference": "ID",
                "assetValue": 40.68}

        self.gmfs_6 = {"IMLs": (0.0872, 0.2288, 0.5655, 0.2118, 0.2, 0.6633,
                0.2095, 0.6537, 0.3838, 0.781, 0.3054, 0.5375, 0.1361, 0.8838,
                0.3726, 0.0845, 0.1942, 0.4629, 0.1354, 0.1109),
                "TSES": 200, "TimeSpan": 50}

        self.asset_6 = {"vulnerabilityFunctionReference": "ID",
                "assetValue": 178.47}

        # deleting keys in kvs
        kvs.get_client().flushall()

        kvs.set_value_json_encoded(
                kvs.tokens.vuln_key(self.job_id),
                {"ID": self.vuln_function_2.to_json()})

        # store the gmfs
        self._store_gmfs(self.gmfs_1, 1, 1)
        self._store_gmfs(self.gmfs_2, 1, 2)
        self._store_gmfs(self.gmfs_3, 1, 3)
        self._store_gmfs(self.gmfs_4, 1, 4)
        self._store_gmfs(self.gmfs_5, 1, 5)
        self._store_gmfs(self.gmfs_6, 1, 6)

        # store the assets
        self._store_asset(self.asset_1, 1, 1)
        self._store_asset(self.asset_2, 1, 2)
        self._store_asset(self.asset_3, 1, 3)
        self._store_asset(self.asset_4, 1, 4)
        self._store_asset(self.asset_5, 1, 5)
        self._store_asset(self.asset_6, 1, 6)

        self.params = {}
        self.params["OUTPUT_DIR"] = helpers.OUTPUT_DIR
        self.params["AGGREGATE_LOSS_CURVE"] = 1
        self.params["BASE_PATH"] = "."
        self.params["INVESTIGATION_TIME"] = 50.0

        self.job = helpers.create_job(self.params, base_path=".")
        self.job.to_kvs()

        # deleting old file
        self._delete_test_file()

    def tearDown(self):
        self._delete_test_file()

    def _delete_test_file(self):
        try:
            os.remove(os.path.join(helpers.OUTPUT_DIR,
                    aggregate._filename(self.job_id)))
        except OSError:
            pass

    def _store_asset(self, asset, row, column):
        key = kvs.tokens.asset_key(self.job_id, row, column)
        kvs.get_client().rpush(key, json.JSONEncoder().encode(asset))

    def _store_gmfs(self, gmfs, row, column):
        key = kvs.tokens.gmfs_key(self.job_id, column, row)
        kvs.set_value_json_encoded(key, gmfs)

    def test_an_empty_function_produces_an_empty_set(self):
        self.assertEqual(0, prob.compute_loss_ratios(
                shapes.EMPTY_CURVE, self.gmfs, None, None).size)

    def test_an_empty_gmfs_produces_an_empty_set(self):
        self.assertEqual(0, prob.compute_loss_ratios(
                self.vuln_function_1, {"IMLs": ()}, None, None).size)

    def test_with_valid_covs_we_sample_the_loss_ratios(self):
        """With valid covs we need to sample loss ratios.

        If the vulnerability function has some covs greater than 0.0 we need
        to use a different algorithm (sampled based)
        to compute the loss ratios.
        """

        imls = [0.10, 0.30, 0.50, 1.00]
        loss_ratios = [0.05, 0.10, 0.15, 0.30]
        covs = [0.30, 0.30, 0.20, 0.20]
        vuln_function = shapes.VulnerabilityFunction(imls, loss_ratios, covs)

        epsilons = [0.5377, 1.8339, -2.2588, 0.8622, 0.3188, -1.3077, \
                -0.4336, 0.3426, 3.5784, 2.7694]

        expected_asset = object()

        gmfs = {"IMLs": (0.1576, 0.9706, 0.9572, 0.4854, 0.8003,
                0.1419, 0.4218, 0.9157, 0.7922, 0.9595)}

        self.assertTrue(numpy.allclose(numpy.array([0.0722, 0.4106, 0.1800,
                0.1710, 0.2508, 0.0395, 0.1145, 0.2883, 0.4734, 0.4885]),
                prob.compute_loss_ratios(vuln_function, gmfs,
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

        self.assertEqual(0.0, prob.compute_loss_ratios(
                vuln_function, gmfs, EpsilonProvider(
                expected_asset, epsilons), expected_asset)[0])

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
                prob.compute_loss_ratios(self.vuln_function_1,
                {"IMLs": (0.0001, 0.0002, 0.0003)}, None, None)))

        # max IML in this case is 0.52
        self.assertTrue(numpy.allclose(numpy.array([0.700, 0.700]),
                prob.compute_loss_ratios(self.vuln_function_1,
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
                prob.compute_loss_ratios(self.vuln_function_1,
                self.gmfs, None, None)))

    def test_loss_ratios_range_generation(self):
        loss_ratios = numpy.array([0.0, 2.0])
        expected_range = numpy.array([0.0, 0.5, 1.0, 1.5, 2.0])

        self.assertTrue(numpy.allclose(expected_range,
                prob._compute_loss_ratios_range(loss_ratios, 5),
                atol=0.0001))

    def test_builds_the_cumulative_histogram(self):
        loss_ratios = prob.compute_loss_ratios(
                self.vuln_function_1, self.gmfs, None, None)

        loss_ratios_range = prob._compute_loss_ratios_range(loss_ratios)

        self.assertTrue(numpy.allclose(self.cum_histogram,
                prob._compute_cumulative_histogram(
                loss_ratios, loss_ratios_range)))

    def test_computes_the_rates_of_exceedance(self):
        expected_rates = numpy.array([0.12444444, 0.05111111, 0.02888889,
                0.02, 0.01555556, 0.01333333, 0.00888889, 0.00777778,
                0.00777778, 0.00666667, 0.00555556, 0.00444444,
                0.00444444, 0.00444444, 0.00444444, 0.00444444, 0.00222222,
                0.00111111, 0.00111111, 0.00111111, 0.00111111,
                0.00111111, 0.00111111, 0.00111111])

        self.assertTrue(numpy.allclose(expected_rates,
                prob._compute_rates_of_exceedance(
                self.cum_histogram, self.gmfs["TSES"]), atol=0.01))

    def test_tses_is_not_supposed_to_be_zero_or_less(self):
        self.assertRaises(ValueError, prob._compute_rates_of_exceedance,
                self.cum_histogram, 0.0)

        self.assertRaises(ValueError, prob._compute_rates_of_exceedance,
                self.cum_histogram, -10.0)

    def test_computes_probs_of_exceedance(self):
        expected_probs = [0.99801517, 0.92235092, 0.76412292, 0.63212056,
                0.54057418, 0.48658288, 0.35881961, 0.32219042, 0.32219042,
                0.28346869, 0.24253487, 0.1992626, 0.1992626, 0.1992626,
                0.1992626, 0.1992626, 0.10516068, 0.05404053, 0.05404053,
                0.05404053, 0.05404053, 0.05404053, 0.05404053, 0.05404053]

        self.assertTrue(numpy.allclose(expected_probs,
                prob._compute_probs_of_exceedance(
                prob._compute_rates_of_exceedance(
                self.cum_histogram, self.gmfs["TSES"]),
                self.gmfs["TimeSpan"]), atol=0.0001))

    def test_computes_the_loss_ratio_curve(self):
        # manually computed results from V. Silva
        expected_curve = shapes.Curve([(0.085255, 0.988891),
                (0.255765, 0.82622606), (0.426275, 0.77686984),
                (0.596785, 0.52763345), (0.767295, 0.39346934)])

        self.assertEqual(expected_curve, prob.compute_loss_ratio_curve(
                self.vuln_function_2, self.gmfs_1,
                None, None, number_of_samples=6))

        expected_curve = shapes.Curve([(0.0935225, 0.99326205),
                (0.2640675, 0.917915), (0.4346125, 0.77686984),
                (0.6051575, 0.52763345), (0.7757025, 0.22119922)])

        self.assertEqual(expected_curve, prob.compute_loss_ratio_curve(
                self.vuln_function_2, self.gmfs_2,
                None, None, number_of_samples=6))

        expected_curve = shapes.Curve([(0.1047, 0.99326205),
                (0.2584, 0.89460078), (0.4121, 0.63212056),
                (0.5658, 0.39346934), (0.7195, 0.39346934)])

        self.assertEqual(expected_curve, prob.compute_loss_ratio_curve(
                self.vuln_function_2, self.gmfs_3,
                None, None, number_of_samples=6))

        expected_curve = shapes.Curve([(0.09012, 0.99326205),
                (0.25551, 0.93607214), (0.4209, 0.77686984),
                (0.58629, 0.52763345), (0.75168, 0.39346934)])

        self.assertEqual(expected_curve, prob.compute_loss_ratio_curve(
                self.vuln_function_2, self.gmfs_4,
                None, None, number_of_samples=6))

        expected_curve = shapes.Curve([(0.08089, 0.99326205),
                (0.23872, 0.95021293), (0.39655, 0.7134952),
                (0.55438, 0.52763345), (0.71221, 0.39346934)])

        self.assertEqual(expected_curve, prob.compute_loss_ratio_curve(
                self.vuln_function_2, self.gmfs_5,
                None, None, number_of_samples=6))

        expected_curve = shapes.Curve([(0.0717025, 0.99326205),
                (0.2128575, 0.917915), (0.3540125, 0.82622606),
                (0.4951675, 0.77686984), (0.6363225, 0.39346934)])

        self.assertEqual(expected_curve, prob.compute_loss_ratio_curve(
                self.vuln_function_2, self.gmfs_6,
                None, None, number_of_samples=6))

    def test_with_not_earthquakes_we_have_an_empty_curve(self):
        gmfs = dict(self.gmfs)
        gmfs["IMLs"] = ()

        curve = prob.compute_loss_ratio_curve(
                self.vuln_function_1, gmfs, None, None)

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

        self.assertEqual(expected_curve, prob.compute_loss_ratio_curve(
                self.vuln_function_1, gmfs, None, None))

    def test_an_empty_distribution_produces_an_empty_aggregate_curve(self):
        self.assertEqual(shapes.EMPTY_CURVE,
                prob.AggregateLossCurve({}, None).compute())

    def test_computes_the_aggregate_loss_curve(self):
        vuln_functions = {"ID": self.vuln_function_2}

        # no epsilon_provided is needed because the vulnerability
        # function has all the covs equal to zero
        aggregate_curve = prob.AggregateLossCurve(vuln_functions, None)
        aggregate_curve.append(self.gmfs_1, self.asset_1)
        aggregate_curve.append(self.gmfs_2, self.asset_2)
        aggregate_curve.append(self.gmfs_3, self.asset_3)
        aggregate_curve.append(self.gmfs_4, self.asset_4)
        aggregate_curve.append(self.gmfs_5, self.asset_5)
        aggregate_curve.append(self.gmfs_6, self.asset_6)

        expected_losses = numpy.array((7.2636, 57.9264, 187.4893, 66.9082,
                47.0280, 248.7796, 23.2329, 121.3514, 177.4167, 259.2902,
                77.7080, 127.7417, 18.9470, 339.5774, 151.1763, 6.1881,
                71.9168, 97.9514, 56.4720, 11.6513))

        self.assertTrue(numpy.allclose(
                expected_losses, aggregate_curve.losses))

        expected_curve = shapes.Curve([(39.52702042, 0.99326205),
                (106.20489077, 0.917915), (172.88276113, 0.77686984),
                (239.56063147, 0.52763345), (306.23850182, 0.22119922)])

        self.assertEqual(expected_curve, aggregate_curve.compute(6))

    def test_no_distribution_without_gmfs(self):
        aggregate_curve = prob.AggregateLossCurve({}, None)
        self.assertEqual(0, aggregate_curve.losses.size)

    def test_with_no_vuln_function_no_distribution_is_added(self):
        aggregate_curve = prob.AggregateLossCurve(
                {"ID": shapes.EMPTY_VULN_FUNCTION}, None)

        asset = {"vulnerabilityFunctionReference": "WRONG_ID",
                "assetValue": 1.0, "assetID": "ASSET_ID"}

        aggregate_curve.append({"TSES": 1, "TimeSpan": 1, "IMLs": ()}, asset)
        self.assertEqual(0, aggregate_curve.losses.size)

    def test_tses_parameter_must_be_congruent(self):
        aggregate_curve = prob.AggregateLossCurve(
                {"ID": shapes.EMPTY_VULN_FUNCTION}, None)

        asset = {"vulnerabilityFunctionReference": "ID", "assetValue": 1.0}

        aggregate_curve.append({"TSES": 1, "TimeSpan": 1, "IMLs": ()}, asset)

        self.assertRaises(AssertionError,
                aggregate_curve.append, {
                "TSES": 2, "TimeSpan": 1, "IMLs": ()}, asset)

    def test_time_span_parameter_must_be_congruent(self):
        aggregate_curve = prob.AggregateLossCurve(
                {"ID": shapes.EMPTY_VULN_FUNCTION}, None)

        asset = {"vulnerabilityFunctionReference": "ID", "assetValue": 1.0}

        aggregate_curve.append({"TSES": 1, "TimeSpan": 1, "IMLs": ()}, asset)

        self.assertRaises(AssertionError,
                aggregate_curve.append, {
                "TSES": 1, "TimeSpan": 2, "IMLs": ()}, asset)

    def test_gmfs_length_must_be_congruent(self):
        aggregate_curve = prob.AggregateLossCurve(
                {"ID": shapes.EMPTY_VULN_FUNCTION}, None)

        asset = {"vulnerabilityFunctionReference": "ID", "assetValue": 1.0}

        aggregate_curve.append({
                "IMLs": (), "TSES": 1, "TimeSpan": 1}, asset)

        self.assertRaises(AssertionError,
                aggregate_curve.append, {
                "IMLs": (1.0, ), "TSES": 1, "TimeSpan": 1}, asset)

    def test_creating_the_aggregate_curve_from_kvs_loads_the_vuln_model(self):
        # we have just self.vuln_function_2 stored in kvs
        aggregate_curve = prob.AggregateLossCurve.from_kvs(self.job_id, None)

        self.assertEqual(self.vuln_function_2,
                aggregate_curve.vuln_model["ID"])

    def test_creating_the_aggregate_curve_from_kvs_gets_all_the_gmfs(self):
        # we have 6 gmfs stored in kvs
        aggregate_curve = prob.AggregateLossCurve.from_kvs(self.job_id, None)
        self.assertEqual(6, len(aggregate_curve.distribution))

    def test_creating_the_aggregate_curve_from_kvs_gets_all_the_sites(self):
        expected_curve = shapes.Curve([(39.52702042, 0.99326205),
                (106.20489077, 0.917915), (172.88276113, 0.77686984),
                (239.56063147, 0.52763345), (306.23850182, 0.22119922)])

        # result is correct, so we are getting the correct assets
        aggregate_curve = prob.AggregateLossCurve.from_kvs(self.job_id, None)
        self.assertEqual(expected_curve, aggregate_curve.compute(6))

    def test_curve_to_plot_interface_translation(self):
        curve = shapes.Curve([(0.1, 1.0), (0.2, 2.0)])

        expected_data = {}
        expected_data["AggregateLossCurve"] = {}
        expected_data["AggregateLossCurve"]["abscissa"] = (0.1, 0.2)
        expected_data["AggregateLossCurve"]["ordinate"] = (1.0, 2.0)

        expected_data["AggregateLossCurve"]["abscissa_property"] = \
                "Economic Losses"

        expected_data["AggregateLossCurve"]["ordinate_property"] = \
                "PoE in 50.0 years"

        expected_data["AggregateLossCurve"]["curve_title"] = \
            "Aggregate Loss Curve"

        self.assertEqual(expected_data, aggregate._for_plotting(curve, 50.0))

    def test_comp_agg_curve_calls_plotter(self):
        """
        If the AGGREGATE_LOSS_CURVE parameter in the job config file, aggregate
        loss curve SVGs will be produced using
        :py:class:`openquake.output.curve.CurvePlot`

        If AGGREGATE_LOSS_CURVE is defined in the config file (with any value),
        this test ensures that the plotter is called.
        :py:class:`openquake.output.curve.CurvePlot` will be mocked to perform
        this test.
        """
        with mock.patch(
            'openquake.output.curve.CurvePlot.write') as write_mock:
            with mock.patch(
                'openquake.output.curve.CurvePlot.close') as close_mock:
                aggregate.compute_aggregate_curve(self.job)

                # make sure write() and close() were both called
                self.assertEqual(1, write_mock.call_count)
                self.assertEqual(1, close_mock.call_count)

    def test_plots_the_aggregate_curve_only_if_specified(self):
        """
        If the AGGREGATE_LOSS_CURVE parameter in the job config file, aggregate
        loss curve SVGs will be produced using
        :py:class:`openquake.output.curve.CurvePlot`

        If AGGREGATE_LOSS_CURVE is not defined in the config file, this test
        ensures that the plotter is not called.
        :py:class:`openquake.output.curve.CurvePlot` will be mocked to perform
        this test.
        """
        del self.params["AGGREGATE_LOSS_CURVE"]

        # storing a new job definition in kvs
        self.job = helpers.create_job(self.params, base_path=".")
        self.job.to_kvs()

        with mock.patch(
            'openquake.output.curve.CurvePlot.write') as write_mock:
            with mock.patch(
                'openquake.output.curve.CurvePlot.close') as close_mock:
                aggregate.compute_aggregate_curve(self.job)

                # the plotter should not be called
                self.assertEqual(0, write_mock.call_count)
                self.assertEqual(0, close_mock.call_count)


class ClassicalPSHABasedTestCase(unittest.TestCase):

    def _store_asset(self, asset, row, column):
        key = kvs.tokens.asset_key(self.job_id, row, column)
        kvs.get_client().rpush(key, json.JSONEncoder().encode(asset))

    def tearDown(self):
        psha.STEPS_PER_INTERVAL = 5

    def test_empty_loss_curve(self):
        self.assertEqual(common.compute_loss_curve(shapes.EMPTY_CURVE, None),
                shapes.EMPTY_CURVE)

    def test_a_loss_curve_is_not_defined_when_the_asset_is_invalid(self):
        self.assertEqual(common.compute_loss_curve(
                shapes.Curve([(0.1, 1.0), (0.2, 2.0), (0.3, 3.0)]),
                INVALID_ASSET_VALUE),
                shapes.EMPTY_CURVE)

    def test_loss_curve_computation(self):
        loss_ratio_curve = shapes.Curve([(0.1, 1.0), (0.2, 2.0), (0.3, 3.0)])
        loss_curve = common.compute_loss_curve(loss_ratio_curve, ASSET_VALUE)

        self.assertEqual(shapes.Curve([(0.1 * ASSET_VALUE, 1.0),
                (0.2 * ASSET_VALUE, 2.0), (0.3 * ASSET_VALUE, 3.0)]),
                loss_curve)

    def test_lrem_po_computation(self):
        hazard_curve = shapes.Curve([
              (0.01, 0.99), (0.08, 0.96),
              (0.17, 0.89), (0.26, 0.82),
              (0.36, 0.70), (0.55, 0.40),
              (0.70, 0.01)])

        # pre computed values just use one intermediate
        # values between the imls
        psha.STEPS_PER_INTERVAL = 2

        imls = [0.1, 0.2, 0.4, 0.6]
        loss_ratios = [0.05, 0.08, 0.2, 0.4]
        covs = [0.5, 0.3, 0.2, 0.1]
        vuln_function = shapes.VulnerabilityFunction(imls, loss_ratios, covs)

        lrem = psha._compute_lrem(vuln_function)

        lrem_po = psha._compute_lrem_po(vuln_function,
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
                psha._compute_pes_from_imls(hazard_curve, imls),
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
                psha._convert_pes_to_pos(hazard_curve, pes),
                atol=0.00005))

    def test_bin_width_from_imls(self):
        imls = [0.1, 0.2, 0.4, 0.6]
        loss_ratios = [0.05, 0.08, 0.2, 0.4]
        covs = [0.5, 0.5, 0.5, 0.5]

        vuln_function = shapes.VulnerabilityFunction(imls, loss_ratios, covs)

        expected_steps = [0.05, 0.15, 0.3, 0.5, 0.7]

        self.assertTrue(numpy.allclose(expected_steps,
                psha._compute_imls(vuln_function)))

    def test_end_to_end(self):
        # manually computed values by Vitor Silva
        psha.STEPS_PER_INTERVAL = 2
        hazard_curve = shapes.Curve([
              (0.01, 0.99), (0.08, 0.96),
              (0.17, 0.89), (0.26, 0.82),
              (0.36, 0.70), (0.55, 0.40),
              (0.70, 0.01)])

        imls = [0.1, 0.2, 0.4, 0.6]
        loss_ratios = [0.05, 0.08, 0.2, 0.4]
        covs = [0.5, 0.3, 0.2, 0.1]
        vuln_function = shapes.VulnerabilityFunction(imls, loss_ratios, covs)

        loss_ratio_curve = psha.compute_loss_ratio_curve(
                vuln_function, hazard_curve)

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
        self.assertTrue(numpy.allclose(numpy.array([1.0, 2.0]),
                psha._split_loss_ratios([1.0, 2.0], 1)))

    def test_splits_single_interval_with_a_step_between(self):
        self.assertTrue(numpy.allclose(numpy.array([1.0, 1.5, 2.0]),
                psha._split_loss_ratios([1.0, 2.0], 2)))

    def test_splits_single_interval_with_steps_between(self):
        self.assertTrue(numpy.allclose(numpy.array(
                [1.0, 1.25, 1.50, 1.75, 2.0]),
                psha._split_loss_ratios([1.0, 2.0], 4)))

    def test_splits_multiple_intervals_with_a_step_between(self):
        self.assertTrue(numpy.allclose(numpy.array(
                [1.0, 1.5, 2.0, 2.5, 3.0]),
                psha._split_loss_ratios([1.0, 2.0, 3.0], steps=2)))

    def test_splits_multiple_intervals_with_steps_between(self):
        self.assertTrue(numpy.allclose(numpy.array(
                [1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0]),
                psha._split_loss_ratios([1.0, 2.0, 3.0], 4)))

    def test_loss_ratio_curve_is_none_with_unknown_vuln_function(self):

        # mixin "instance"
        mixin = ClassicalPSHABasedMixin()

        # empty vuln curves
        mixin.vuln_curves = {}

        # "empty" asset
        asset = {"vulnerabilityFunctionReference": "ID", "assetID": 1}

        self.assertEqual(None, mixin.compute_loss_ratio_curve(
                         None, asset, None))

    def _compute_risk_classical_psha_setup(self):
        SITE = shapes.Site(1.0, 1.0)
        # deletes all keys from kvs
        kvs.get_client().flushall()

        # at the moment the hazard part doesn't do exp on the 'x'
        # so it's done on the risk part. To adapt the calculation
        # we do the reverse of the exp, i.e. log(x)
        self.hazard_curve = {'curve': [
            {'x': str(log(0.001)), 'y': '0.99'},
            {'x': str(log(0.080)), 'y': '0.96'},
            {'x': str(log(0.170)), 'y': '0.89'},
            {'x': str(log(0.260)), 'y': '0.82'},
            {'x': str(log(0.360)), 'y': '0.70'},
            {'x': str(log(0.550)), 'y': '0.40'},
            {'x': str(log(0.700)), 'y': '0.01'}]}

        # Vitor provided this Vulnerability Function
        imls_1 = [0.03, 0.04, 0.07, 0.1, 0.12, 0.22, 0.37, 0.52]
        loss_ratios_1 = [0.001, 0.022, 0.051, 0.08, 0.1, 0.2, 0.405, 0.700]
        covs_1 = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.vuln_function = shapes.VulnerabilityFunction(imls_1,
            loss_ratios_1, covs_1)

        imls_2 = [0.1, 0.2, 0.4, 0.6]
        loss_ratios_2 = [0.05, 0.08, 0.2, 0.4]
        covs_2 = [0.5, 0.3, 0.2, 0.1]
        self.vuln_function_2 = shapes.VulnerabilityFunction(imls_2,
            loss_ratios_2, covs_2)

        self.job_id = 1234

        self.gmfs_1 = {"IMLs": (0.1439, 0.1821, 0.5343, 0.171, 0.2177,
                0.6039, 0.0618, 0.186, 0.5512, 1.2602, 0.2824, 0.2693,
                0.1705, 0.8453, 0.6355, 0.0721, 0.2475, 0.1601, 0.3544,
                0.1756), "TSES": 200, "TimeSpan": 50}

        self.asset_1 = {"vulnerabilityFunctionReference": "ID",
                "assetValue": 124.27}

        self.region = shapes.RegionConstraint.from_simple(
                (0.0, 0.0), (2.0, 2.0))

        self.block_id = kvs.generate_block_id()
        block = Block((SITE, SITE), self.block_id)
        block.to_kvs()

        self.haz_curve_key = kvs.tokens.mean_hazard_curve_key(
            self.job_id, SITE)

        kvs.set_value_json_encoded(self.haz_curve_key, self.hazard_curve)

        kvs.set_value_json_encoded(
                kvs.tokens.vuln_key(self.job_id),
                {"ID": self.vuln_function.to_json()})

    # Running a complete risk calculation (i.e. invoking compute_risk) requires
    # now a database, but the tests in this module still don't have access to
    # the database.
    # This test needs to be updated once the merging of tests/* and db_tests/*
    # is complete and all the tests will have access to the database.
    # Specifically the part to be updated is the one storing the hazard_curve
    # in the kvs (lines 919-922 above), to store the hazard curve in the
    # database.
    @helpers.skipit
    def test_compute_risk_in_the_classical_psha_mixin(self):
        """
            tests ClassicalPSHABasedMixin.compute_risk by retrieving
            all the loss curves in the kvs and checks their presence
        """

        self._compute_risk_classical_psha_setup()
        # mixin "instance"
        mixin = ClassicalPSHABasedMixin()
        mixin.region = self.region
        mixin.job_id = self.job_id
        mixin.id = self.job_id
        mixin.vuln_curves = {"ID": self.vuln_function}
        mixin.params = {}

        block = Block.from_kvs(self.block_id)

        asset = {"vulnerabilityFunctionReference": "ID",
                 "assetID": 22.61, "assetValue": 1}

        self._store_asset(asset, 10, 10)

        # computes the loss curves and puts them in kvs
        self.assertTrue(mixin.compute_risk(self.block_id,
            point=shapes.GridPoint(None, 10, 20)))

        for point in block.grid(mixin.region):
            asset_key = kvs.tokens.asset_key(self.job_id, point.row,
                point.column)
            for asset in kvs.get_list_json_decoded(asset_key):
                loss_ratio_key = kvs.tokens.loss_ratio_key(
                    self.job_id, point.row, point.column, asset['assetID'])
                self.assertTrue(kvs.get(loss_ratio_key))

                loss_key = kvs.tokens.loss_curve_key(self.job_id, point.row,
                    point.column, asset['assetID'])

                self.assertTrue(kvs.get(loss_key))

    def test_loss_ratio_curve_in_the_classical_psha_mixin(self):

        # mixin "instance"
        mixin = ClassicalPSHABasedMixin()

        hazard_curve = shapes.Curve([
              (0.01, 0.99), (0.08, 0.96),
              (0.17, 0.89), (0.26, 0.82),
              (0.36, 0.70), (0.55, 0.40),
              (0.70, 0.01)])

        imls = [0.1, 0.2, 0.4, 0.6]
        loss_ratios = [0.05, 0.08, 0.2, 0.4]
        covs = [0.5, 0.3, 0.2, 0.1]
        vuln_function = shapes.VulnerabilityFunction(imls, loss_ratios, covs)

        # pre computed values just use one intermediate
        # values between the imls
        psha.STEPS_PER_INTERVAL = 2

        mixin.job_id = 1234
        mixin.vuln_curves = {"ID": vuln_function}

        asset = {"vulnerabilityFunctionReference": "ID", "assetID": 1}

        self.assertTrue(mixin.compute_loss_ratio_curve(
                        shapes.GridPoint(None, 10, 20),
                        asset, hazard_curve) is not None)

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

        self.assertTrue(numpy.allclose(numpy.array(result),
                psha._split_loss_ratios(loss_ratios)))

    def test_splits_with_real_values_from_taiwan(self):
        loss_ratios = [0.0, 1.877E-20, 8.485E-17, 8.427E-14,
                2.495E-11, 2.769E-09, 1.372E-07, 3.481E-06,
                5.042E-05, 4.550E-04, 2.749E-03, 1.181E-02]

        # testing just the length of the result
        self.assertEqual(56, len(psha._split_loss_ratios(loss_ratios)))

    def test_ratio_is_zero_if_probability_is_too_high(self):
        loss_curve = shapes.Curve([(0.21, 0.131), (0.24, 0.108),
                (0.27, 0.089), (0.30, 0.066)])

        self.assertEqual(0.0,
                common.compute_conditional_loss(loss_curve, 0.200))

    def test_ratio_is_max_if_probability_is_too_low(self):
        loss_curve = shapes.Curve([(0.21, 0.131), (0.24, 0.108),
                (0.27, 0.089), (0.30, 0.066)])

        self.assertEqual(0.30,
                common.compute_conditional_loss(loss_curve, 0.050))

    def test_conditional_loss_computation(self):
        loss_curve = shapes.Curve([(0.21, 0.131), (0.24, 0.108),
                (0.27, 0.089), (0.30, 0.066)])

        self.assertAlmostEqual(0.2526, common.compute_conditional_loss(
                loss_curve, 0.100), 4)

    def test_loss_ratio_pe_mid_curve_computation(self):
        loss_ratio_curve = shapes.Curve([(0, 0.3460), (0.06, 0.12),
                (0.12, 0.057), (0.18, 0.04),
                (0.24, 0.019), (0.3, 0.009), (0.45, 0)])

        expected_curve = shapes.Curve([(0.0300, 0.2330), (0.0900, 0.0885),
                (0.1500, 0.0485), (0.2100, 0.0295),
                (0.2700, 0.0140), (0.3750, 0.0045)])

        self.assertEqual(expected_curve,
                common._compute_mid_mean_pe(loss_ratio_curve))

    def test_loss_ratio_po_computation(self):
        loss_ratio_pe_mid_curve = shapes.Curve([(0.0300, 0.2330),
                (0.0900, 0.0885), (0.1500, 0.0485), (0.2100, 0.0295),
                (0.2700, 0.0140), (0.3750, 0.0045)])

        expected_curve = shapes.Curve([(0.0600, 0.1445),
                (0.1200, 0.0400), (0.1800, 0.0190), (0.2400, 0.0155),
                (0.3225, 0.0095)])

        self.assertEqual(expected_curve,
                common._compute_mid_po(loss_ratio_pe_mid_curve))

    def test_mean_loss_ratio_computation(self):
        loss_ratio_curve = shapes.Curve([(0, 0.3460), (0.06, 0.12),
                (0.12, 0.057), (0.18, 0.04),
                (0.24, 0.019), (0.3, 0.009), (0.45, 0)])

# TODO (ac): Check the difference between 0.023305 and 0.023673
        self.assertAlmostEqual(0.023305,
                common.compute_mean_loss(loss_ratio_curve), 3)


class DeterministicEventBasedTestCase(unittest.TestCase):

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
        asset = {"assetValue": 1000}
        loss_ratios = numpy.array([0.20, 0.05, 0.10, 0.05, 0.10])

        self.assertEqual(100, det._mean_loss_from_loss_ratios(
                         loss_ratios, asset))

    def test_computes_the_mean_loss(self):
        asset = {"assetValue": 10}
        epsilon_provider = EpsilonProvider(asset, self.epsilons)

        self.assertTrue(numpy.allclose(2.4887999999999999,
                        det.compute_mean_loss(self.vuln_function, self.gmfs,
                        epsilon_provider, asset), atol=0.0001))

    def test_computes_the_stddev_loss_from_loss_ratios(self):
        asset = {"assetValue": 1000}
        loss_ratios = numpy.array([0.20, 0.05, 0.10, 0.05, 0.10])

        self.assertTrue(numpy.allclose(61.237,
                        det._stddev_loss_from_loss_ratios(
                        loss_ratios, asset), atol=0.001))

    def test_computes_the_stddev_loss(self):
        asset = {"assetValue": 10}
        epsilon_provider = EpsilonProvider(asset, self.epsilons)

        self.assertTrue(numpy.allclose(1.631,
                        det.compute_stddev_loss(self.vuln_function, self.gmfs,
                        epsilon_provider, asset), atol=0.002))

    def test_calls_the_loss_ratios_calculator_correctly(self):
        gmfs = {"IMLs": ()}
        epsilon_provider = object()
        vuln_model = {"ID": self.vuln_function}
        asset = {"assetValue": 10, "vulnerabilityFunctionReference": "ID"}

        def loss_ratios_calculator(
            vuln_function, ground_motion_field_set, epsilon_provider, asset):

            self.assertTrue(asset == asset)
            self.assertTrue(epsilon_provider == epsilon_provider)
            self.assertTrue(ground_motion_field_set == gmfs)
            self.assertTrue(vuln_function == self.vuln_function)

            return numpy.array([])

        calculator = det.SumPerGroundMotionField(
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
        asset = {"assetValue": 100, "vulnerabilityFunctionReference": "ID"}

        calculator = det.SumPerGroundMotionField(
            vuln_model, None, lr_calculator=loss_ratios_calculator)

        self.assertEqual(None, calculator.losses)

        calculator.add(None, asset)
        asset = {"assetValue": 300, "vulnerabilityFunctionReference": "ID"}
        calculator.add(None, asset)
        asset = {"assetValue": 200, "vulnerabilityFunctionReference": "ID"}
        calculator.add(None, asset)

        expected_sum = [62.63191284, 98.16576808,
                        166.2920523, 84.25372286, 23.10280904]

        self.assertTrue(numpy.allclose(expected_sum, calculator.losses))

    def test_computes_the_mean_from_the_current_sum(self):
        calculator = det.SumPerGroundMotionField(None, None)

        sum_of_losses = numpy.array(
            [62.63191284, 98.16576808, 166.2920523, 84.25372286, 23.10280904])

        calculator.losses = sum_of_losses

        self.assertTrue(numpy.allclose(86.88925302, calculator.mean))

    def test_computes_the_stddev_from_the_current_sum(self):
        calculator = det.SumPerGroundMotionField(None, None)

        sum_of_losses = numpy.array(
            [62.63191284, 98.16576808, 166.2920523, 84.25372286, 23.10280904])

        calculator.losses = sum_of_losses

        self.assertTrue(numpy.allclose(52.66886967, calculator.stddev))

    def test_skips_the_distribution_with_unknown_vuln_function(self):
        """The asset refers to an unknown vulnerability function.

        In case the asset defines an unknown vulnerability function
        (key 'vulnerabilityFunctionReference') the given ground
        motion field set is ignored.
        """
        vuln_model = {"ID": self.vuln_function}
        asset = {"assetValue": 100, "assetID": "ID",
                 "vulnerabilityFunctionReference": "XX"}

        calculator = det.SumPerGroundMotionField(vuln_model, None)

        self.assertEqual(None, calculator.losses)

        calculator.add(None, asset)

        # still None, no losses are added
        self.assertEqual(None, calculator.losses)
