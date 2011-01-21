# -*- coding: utf-8 -*-
"""
This is a basic set of tests for risk engine.
"""

import json
import os
import numpy
import unittest

from scipy.interpolate import interp1d
from shapely import geometry

from openquake import job
from openquake import logs
from openquake import risk
from openquake import kvs 
from openquake import shapes
from openquake import test

from openquake.kvs import tokens
from openquake.risk.job import aggregate_loss_curve as aggregate
from openquake.risk import engines
from openquake.output import risk as risk_output
from openquake.parser import vulnerability
from openquake.risk import probabilistic_event_based as prob
from openquake.risk import classical_psha_based as psha
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
# TSES = TimeSpan times number of Realizations

class ProbabilisticEventBasedTestCase(unittest.TestCase):
    
    def setUp(self):
        self.vuln_function = shapes.Curve([(0.01, (0.001, 1.00)),
                (0.04, (0.022, 1.0)), (0.07, (0.051, 1.0)),
                (0.10, (0.080, 1.0)), (0.12, (0.100, 1.0)),
                (0.22, (0.200, 1.0)), (0.37, (0.405, 1.0)),
                (0.52, (0.700, 1.0))])

        self.gmfs = GMFs

        self.cum_histogram = numpy.array([112, 31, 17, 12, 7, 7, 5, 4, 4, 4, 1,
                1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0])

    def test_an_empty_function_produces_an_empty_set(self):
        self.assertEqual([], prob.compute_loss_ratios(
                shapes.EMPTY_CURVE, self.gmfs))

    def test_an_empty_gmfs_produces_an_empty_set(self):
        self.assertEqual([], prob.compute_loss_ratios(
                self.vuln_function, {"IMLs": ()}))

    def test_loss_ratios_boundaries(self):
        # loss ratio is zero if the gmf iml is below the minimum iml
        # defined by the function min iml in this case is 0.01
        self.assertTrue(numpy.allclose(numpy.array([0.0, 0.0, 0.0]),
                prob.compute_loss_ratios(self.vuln_function,
                {"IMLs": (0.0001, 0.0002, 0.0003)})))

        # loss ratio is equal to the maximum iml defined by the
        # function is greater than that max iml in this case is 0.52
        self.assertTrue(numpy.allclose(numpy.array([0.52, 0.52]),
                prob.compute_loss_ratios(self.vuln_function,
                {"IMLs": (0.525, 0.53)})))

    def test_loss_ratios_computation_using_gmfs(self):
        # manually computed values by Vitor Silva
        expected_loss_ratios = numpy.array([0.0605584000000000,
                0.273100266666667,
                0.0958560000000000,	0.0184384000000000, 0.270366933333333, 0.0,
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
                0.0, 0.00498720000000000,	0.0, 0.0, 0.0,
                0.00612960000000000, 0.0,
                0.0450453333333333,	0.0143728000000000,
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
                0.0147760000000000,	0.0,
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
                prob.compute_loss_ratios(self.vuln_function, self.gmfs)))

    def test_loss_ratios_range_generation(self):
        expected_range = numpy.array([0.0000, 0.0292, 0.0583, 0.0875, 0.1167,
                0.1458, 0.1750, 0.2042, 0.2333, 0.2625, 0.2917, 0.3208,
                0.3500, 0.3792, 0.4083, 0.4375, 0.4667, 0.4958, 0.5250,
                0.5542, 0.5833, 0.6125, 0.6417, 0.6708, 0.700])

        self.assertTrue(numpy.allclose(expected_range,
                prob.compute_loss_ratios_range(self.vuln_function),
                atol=0.0001))

    def test_builds_the_cumulative_histogram(self):
        self.assertTrue(numpy.allclose(self.cum_histogram,
                prob.compute_cumulative_histogram(
                prob.compute_loss_ratios(self.vuln_function, self.gmfs),
                prob.compute_loss_ratios_range(self.vuln_function))))

    def test_computes_the_rates_of_exceedance(self):
        expected_rates = numpy.array([0.124, 0.0344, 0.0189, 0.0133,
                0.0078, 0.0078, 0.0056, 0.0044, 0.0044, 0.0044,
                0.0011, 0.0011, 0.0011, 0.0011, 0.011, 0.0, 0.0,
                0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

        self.assertTrue(numpy.allclose(expected_rates,
                prob.compute_rates_of_exceedance(
                self.cum_histogram, self.gmfs["TSES"]), atol=0.01))

    def test_TSES_is_not_supposed_to_be_zero_or_less(self):
        self.assertRaises(ValueError, prob.compute_rates_of_exceedance,
                self.cum_histogram, 0.0)
        
        self.assertRaises(ValueError, prob.compute_rates_of_exceedance,
                self.cum_histogram, -10.0)

    def test_computes_probs_of_exceedance(self):
        expected_probs = [0.9980, 0.8213, 0.6111, 0.4866, 0.3222, 0.3222,
                0.2425, 0.1993, 0.1993, 0.1993, 0.0540,
                0.0540, 0.0540, 0.0540, 0.0540, 0.0, 0.0, 0.0, 0.0,
                0.0, 0.0, 0.0, 0.0, 0.0]

        self.assertTrue(numpy.allclose(expected_probs, 
                prob.compute_probs_of_exceedance(
                prob.compute_rates_of_exceedance(
                self.cum_histogram, self.gmfs["TSES"]),
                self.gmfs["TimeSpan"]), atol=0.0001))

    def test_computes_the_loss_ratio_curve(self):
        expected_curve = shapes.Curve([
                (0.014583333333333332, 0.99801517),
                (0.043749999999999997, 0.82133133505033484),
                (0.072916666666666657, 0.61110443601077713),
                (0.10208333333333333, 0.48658288096740798),
                (0.13124999999999998, 0.32219042199454972),
                (0.16041666666666665, 0.32219042199454972),
                (0.18958333333333333, 0.24253487160303355),
                (0.21874999999999997, 0.19926259708319194),
                (0.24791666666666662, 0.19926259708319194),
                (0.27708333333333329, 0.19926259708319194),
                (0.30624999999999997, 0.054040531093234589),
                (0.33541666666666664, 0.054040531093234589),
                (0.36458333333333331, 0.054040531093234589),
                (0.39374999999999993, 0.054040531093234589),
                (0.42291666666666661, 0.054040531093234589),
                (0.45208333333333328, 0.0), (0.48124999999999996, 0.0),
                (0.5395833333333333, 0.0), (0.59791666666666665, 0.0),
                (0.51041666666666663, 0.0), (0.56874999999999987, 0.0),
                (0.62708333333333321, 0.0), (0.65625, 0.0),
                (0.68541666666666656, 0.0)])

        self.assertEqual(expected_curve, prob.compute_loss_ratio_curve(
                self.vuln_function, self.gmfs))

    def test_an_empty_gmfs_produces_an_empty_loss_ratio_curve(self):
        gmfs = dict(self.gmfs)
        gmfs["IMLs"] = ()

        curve = prob.compute_loss_ratio_curve(self.vuln_function, gmfs)
        self.assertEqual(shapes.EMPTY_CURVE, curve)

    def test_loss_ratio_curve_with_null_gmf(self):
        gmfs = {"IMLs": (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
                "TSES": 900, "TimeSpan": 50}
        
        expected_curve = shapes.Curve([
                (0.014583333333333332, 0.0),
                (0.043749999999999997, 0.0),
                (0.072916666666666657, 0.0),
                (0.10208333333333333, 0.0),
                (0.13124999999999998, 0.0),
                (0.16041666666666665, 0.0),
                (0.18958333333333333, 0.0),
                (0.21874999999999997, 0.0),
                (0.24791666666666662, 0.0),
                (0.27708333333333329, 0.0),
                (0.30624999999999997, 0.0),
                (0.33541666666666664, 0.0),
                (0.36458333333333331, 0.0),
                (0.39374999999999993, 0.0),
                (0.42291666666666661, 0.0),
                (0.45208333333333328, 0.0),
                (0.48124999999999996, 0.0),
                (0.5395833333333333, 0.0),
                (0.59791666666666665, 0.0),
                (0.51041666666666663, 0.0),
                (0.56874999999999987, 0.0),
                (0.62708333333333321, 0.0),
                (0.65625, 0.0),
                (0.68541666666666656, 0.0)])

        self.assertEqual(expected_curve, prob.compute_loss_ratio_curve(
                self.vuln_function, gmfs))

    def test_losses_aggregation(self):
        # we don't care about PoEs in this case
        loss_curve_1 = shapes.Curve([(1.0, 0.0), (2.0, 0.0), 
                (3.0, 0.0), (4.0, 0.0)])

        loss_curve_2 = shapes.Curve([(5.0, 0.0), (6.0, 0.0), 
                (7.0, 0.0), (8.0, 0.0)])

        loss_curve_3 = shapes.Curve([(9.0, 0.0), (10.0, 0.0), 
                (11.0, 0.0), (12.0, 0.0)])

        aggregate_curve = prob.AggregateLossCurve()
        aggregate_curve.append(loss_curve_1)
        aggregate_curve.append(loss_curve_2)
        aggregate_curve.append(loss_curve_3)

        expected_losses = numpy.array((15.0, 18.0, 21.0, 24.0))
        self.assertTrue(numpy.allclose(expected_losses, aggregate_curve.losses))

    def test_losses_aggregation_with_empty_input_set(self):
        aggregate_curve = prob.AggregateLossCurve()
        self.assertEqual([], aggregate_curve.losses)

    def test_input_loss_curves_must_be_of_same_size(self):
        loss_curve_1 = shapes.Curve([(1.0, 0.0), (2.0, 0.0)])
        loss_curve_2 = shapes.Curve([(5.0, 0.0)])

        aggregate_curve = prob.AggregateLossCurve()
        aggregate_curve.append(loss_curve_1)

        self.assertRaises(ValueError, aggregate_curve.append, loss_curve_2)

    def test_can_build_an_aggregate_curve_from_kvs(self):
        curve_1 = shapes.Curve([(1.0, 0.0), (2.0, 0.0), 
                (3.0, 0.0), (4.0, 0.0)])

        curve_2 = shapes.Curve([(5.0, 0.0), (6.0, 0.0), 
                (7.0, 0.0), (8.0, 0.0)])

        curve_3 = shapes.Curve([(9.0, 0.0), (10.0, 0.0), 
                (11.0, 0.0), (12.0, 0.0)])
        
        job_id = 1234
        kvs.set(tokens.loss_curve_key(job_id, 1, 1, 5), curve_1.to_json())
        kvs.set(tokens.loss_curve_key(job_id, 1, 2, 5), curve_2.to_json())
        kvs.set(tokens.loss_curve_key(job_id, 1, 3, 5), curve_3.to_json())

        aggregate_curve = prob.AggregateLossCurve.from_kvs(job_id)

        expected_losses = numpy.array((15.0, 18.0, 21.0, 24.0))
        self.assertTrue(numpy.allclose(expected_losses, aggregate_curve.losses))


class ClassicalPSHABasedTestCase(unittest.TestCase):

    def setUp(self):
        self.job_id = kvs.generate_random_id()

        self.vuln_curve_code_test = "TEST"
        vuln_curve_test = shapes.Curve([(5.0, (0.25, 0.5)),
                (6.0, (0.4, 0.4)), (7.0, (0.6, 0.3))])

        self.vulnerability_curves = vulnerability.register_vuln_curves(
                {self.vuln_curve_code_test: vuln_curve_test.to_json(),
                vulnerability.EMPTY_CODE: shapes.EMPTY_CURVE.to_json()}, 
                self.job_id)

    def tearDown(self):
        # flush vulnerability curves in kvs
        vulnerability.delete_vuln_curves(self.job_id)

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

    def test_empty_lrem_po(self):
        self.assertEqual([], psha._compute_lrem_po(
                shapes.EMPTY_CURVE, [], None))

    def test_lrem_po_computation(self):
        lrem_po = psha._compute_lrem_po(shapes.Curve.from_json(
                self.vulnerability_curves[self.vuln_curve_code_test]), 
                LOSS_RATIO_EXCEEDANCE_MATRIX, HAZARD_CURVE)

        self.assertAlmostEquals(0.0959, lrem_po[0][0], 4)
        self.assertAlmostEquals(0.0367, lrem_po[1][0], 4)
        self.assertAlmostEquals(0.0849, lrem_po[0][1], 4)
        self.assertAlmostEquals(0.05049, lrem_po[1][1], 4)
        self.assertAlmostEquals(0.0673, lrem_po[0][2], 4)
        self.assertAlmostEquals(0.05718, lrem_po[1][2], 4)

    def test_empty_loss_ratio_curve(self):
        self.assertEqual(shapes.EMPTY_CURVE,
                psha.compute_loss_ratio_curve(None, []))

    def test_end_to_end(self):
        # manually computed values by Vitor Silva
        hazard_curve = shapes.Curve(
                [(5.0, 0.4), (6.0, 0.2), (7.0, 0.05)])

        lrem = psha._compute_lrem(shapes.Curve.from_json(
                self.vulnerability_curves[self.vuln_curve_code_test]))

        loss_ratio_curve = psha.compute_loss_ratio_curve(
                shapes.Curve.from_json(
                self.vulnerability_curves[self.vuln_curve_code_test]),
                hazard_curve)

        lr_curve_expected = shapes.Curve([(0.0, 0.650), 
                (0.05, 0.650), (0.10, 0.632), (0.15, 0.569),
                (0.20, 0.477), (0.25, 0.382), (0.28, 0.330),
                (0.31, 0.283), (0.34, 0.241), (0.37, 0.205),
                (0.40, 0.173), (0.44, 0.137), (0.48, 0.108),
                (0.52, 0.085), (0.56, 0.066), (0.60, 0.051)])

        for x_value in lr_curve_expected.abscissae:
            self.assertAlmostEqual(lr_curve_expected.ordinate_for(x_value),
                    loss_ratio_curve.ordinate_for(x_value), 3)

    def test_empty_lrem(self):
        self.assertEqual([None], psha._compute_lrem(shapes.Curve.from_json(
            self.vulnerability_curves[vulnerability.EMPTY_CODE]),
            shapes.EMPTY_CURVE))

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
                psha._split_loss_ratios([1.0, 2.0, 3.0], 2)))

    def test_splits_multiple_intervals_with_steps_between(self):
        self.assertTrue(numpy.allclose(numpy.array(
                [1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0]),
                psha._split_loss_ratios([1.0, 2.0, 3.0], 4)))

    def test_splits_with_real_values_from_turkey(self):
        loss_ratios = [0.0, 1.96E-15, 2.53E-12, 8.00E-10, 8.31E-08, 3.52E-06,
                7.16E-05, 7.96E-04, 5.37E-03, 2.39E-02, 7.51E-02, 1.77E-01]

        result =  [0.0, 3.9199999999999996e-16,
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

    # TODO (bw): Should we check also if the curve has no values?
    def test_ratio_is_zero_if_probability_is_out_of_bounds(self):
        loss_curve = shapes.Curve([(0.21, 0.131), (0.24, 0.108),
                (0.27, 0.089), (0.30, 0.066)])

        self.assertEqual(0.0,
                common.compute_conditional_loss(loss_curve, 0.050))

        self.assertEqual(0.0,
                common.compute_conditional_loss(loss_curve, 0.200))        

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


class AggregateLossCurveMixinTestCase(unittest.TestCase):
    
    def setUp(self):
        self.job_id = 1234
        
        self.params = {}
        self.params["OUTPUT_DIR"] = test.OUTPUT_DIR
        
        # parameters needed to compute tses and time span
        self.params["NUMBER_OF_SEISMICITY_HISTORIES"] = 10
        self.params["NUMBER_OF_LOGIC_TREE_SAMPLES"] = 2
        self.params["INVESTIGATION_TIME"] = 50.0
        self.params["AGGREGATE_LOSS_CURVE"] = 1

        self.engine = job.Job(self.params,  self.job_id, ".")
        
        # adding the curves to kvs
        kvs.set(tokens.loss_curve_key(self.job_id, 1, 1, 5),
                shapes.Curve([(1.0, 0.1), (2.0, 0.1)]).to_json())

        kvs.set(tokens.loss_curve_key(self.job_id, 1, 2, 5),
                shapes.Curve([(3.0, 0.1), (4.0, 0.1)]).to_json())

        kvs.set(tokens.loss_curve_key(self.job_id, 1, 3, 5),
                shapes.Curve([(5.0, 0.1), (6.0, 0.1)]).to_json())
        
        # deleting old file
        self._delete_test_file()
    
    def tearDown(self):
        self._delete_test_file()

    def _delete_test_file(self):
        try:
            os.remove(os.path.join(test.OUTPUT_DIR, 
                    aggregate.filename(self.job_id)))
        except OSError:
            pass
    
    def _execute_mixin(self):
        with job.Mixin(self.engine, aggregate.AggregateLossCurveMixin):
            self.engine.execute()
    
    def test_curve_to_plot_interface_translation(self):
        curve = shapes.Curve([(0.1, 1.0), (0.2, 2.0)])
        
        expected_data = {}
        expected_data["AggregateLossCurve"] = {}
        expected_data["AggregateLossCurve"]["abscissa"] = (0.1, 0.2)
        expected_data["AggregateLossCurve"]["ordinate"] = (1.0, 2.0)
        expected_data["AggregateLossCurve"]["abscissa_property"] = "Loss"
        expected_data["AggregateLossCurve"]["ordinate_property"] = "PoE"
        expected_data["AggregateLossCurve"] \
                ["curve_title"] = "Aggregate Loss Curve"

        self.assertEqual(expected_data, aggregate.for_plotting(curve))

    def test_plots_the_aggregate_curve(self):
        self._execute_mixin()
        self._assert_plot_is_produced()

    def test_plots_the_aggregate_curve_only_if_specified(self):
        del(self.params["AGGREGATE_LOSS_CURVE"])

        self._execute_mixin()
        self._assert_plot_is_not_produced()

    def _assert_plot_is_not_produced(self):
        self.assertFalse(os.path.exists(
                os.path.join(test.OUTPUT_DIR,
                aggregate.filename(self.job_id))))

    def _assert_plot_is_produced(self):
        self.assertTrue(os.path.exists(
                os.path.join(test.OUTPUT_DIR,
                aggregate.filename(self.job_id))))


# LOSS_XML_OUTPUT_FILE = 'loss-curves.xml'
# LOSS_RATIO_XML_OUTPUT_FILE = 'loss-ratio-curves.xml'
# EXPOSURE_INPUT_FILE = 'FakeExposurePortfolio.xml'
# VULNERABILITY_INPUT_FILE = 'VulnerabilityModelFile-jobber-test.xml'
#
# JOB_ID = 1
# BLOCK_ID = 1
# SITE = shapes.Site(1.0, 1.0)
#
# class ProbabilisticEventBasedCalculatorTestCase(unittest.TestCase):
#     
#     def setUp(self):
#         self.memcached_client = kvs.get_client(binary=False)
#         self.calculator = engines.ProbabilisticEventBasedCalculator(JOB_ID, BLOCK_ID)
# 
#         self.key_exposure = kvs.generate_product_key(JOB_ID,
#             risk.EXPOSURE_KEY_TOKEN, BLOCK_ID, SITE)
# 
#         self.key_gmf = kvs.generate_product_key(JOB_ID,
#             risk.GMF_KEY_TOKEN, BLOCK_ID, SITE)
# 
#         # delete old keys
#         self.memcached_client.delete(self.key_exposure)
#         self.memcached_client.delete(kvs.generate_job_key(JOB_ID))
#         self.memcached_client.delete(self.key_gmf)
# 
#     def tearDown(self):
#         kvs.get_client().flushdb()
#     
#     def test_no_loss_curve_with_no_asset_value(self):
#         self.assertEqual(None, self.calculator.compute_loss_curve(
#                 SITE, shapes.EMPTY_CURVE))
#     
#     def test_computes_the_loss_curve(self):
#         kvs.set_value_json_encoded(self.key_exposure, {"AssetValue": 5.0})
# 
#         loss_ratio_curve = shapes.Curve([(0.1, 1.0), (0.2, 2.0)])
#         
#         self.assertEqual(shapes.Curve([(0.5, 1.0), (1.0, 2.0)]), 
#                 self.calculator.compute_loss_curve(SITE, loss_ratio_curve))
#         
#     def test_computes_the_loss_ratio_curve(self):
#         # saving in memcached the vuln function
#         vuln_curve = self.vuln_function = shapes.Curve([
#                 (0.01, (0.001, 1.00)), (0.04, (0.022, 1.0)), 
#                 (0.07, (0.051, 1.0)), (0.10, (0.080, 1.0)),
#                 (0.12, (0.100, 1.0)), (0.22, (0.200, 1.0)),
#                 (0.37, (0.405, 1.0)), (0.52, (0.700, 1.0))])
#         
#         # ugly, it shouldn't take the json format
#         vulnerability.write_vuln_curves_to_kvs(JOB_ID,
#             {"Type1": vuln_curve.to_json()})
#         
#         # recreate the calculator to get the vuln function
#         calculator = engines.ProbabilisticEventBasedCalculator(JOB_ID, BLOCK_ID)
#         
#         # saving the exposure
#         kvs.set_value_json_encoded(self.key_exposure, 
#             {"AssetValue": 5.0, "VulnerabilityFunction": "Type1"})
#         
#         # saving the ground motion field
#         kvs.set_value_json_encoded(self.key_gmf, GMF)
#         
#         # manually computed curve
#         expected_curve = shapes.Curve([
#                 (0.014583333333333332, 0.99999385578764666),
#                 (0.043749999999999997, 0.82133133505033484),
#                 (0.072916666666666657, 0.61110443601077713),
#                 (0.10208333333333333, 0.48658288096740798),
#                 (0.13124999999999998, 0.32219042199454972),
#                 (0.16041666666666665, 0.32219042199454972),
#                 (0.18958333333333333, 0.24253487160303355),
#                 (0.21874999999999997, 0.19926259708319194),
#                 (0.24791666666666662, 0.19926259708319194),
#                 (0.27708333333333329, 0.19926259708319194),
#                 (0.30624999999999997, 0.054040531093234589),
#                 (0.33541666666666664, 0.054040531093234589),
#                 (0.36458333333333331, 0.054040531093234589),
#                 (0.39374999999999993, 0.054040531093234589),
#                 (0.42291666666666661, 0.054040531093234589),
#                 (0.45208333333333328, 0.0), (0.48124999999999996, 0.0),
#                 (0.5395833333333333, 0.0), (0.59791666666666665, 0.0),
#                 (0.51041666666666663, 0.0), (0.56874999999999987, 0.0),
#                 (0.62708333333333321, 0.0), (0.65625, 0.0),
#                 (0.68541666666666656, 0.0)])
#         
#         self.assertEqual(expected_curve, calculator.compute_loss_ratio_curve(SITE))
# 
# 
# 
# 
# class RiskEngineTestCase(unittest.TestCase):
#     """Basic unit tests of the Risk Engine"""
# 
#     def test_loss_map_generation(self):
#         # get grid of columns and rows from region of coordinates
#         loss_map_region = shapes.Region.from_coordinates(
#             [(10, 20), (20, 20), (20, 10), (10, 10)])
#         loss_map_region.cell_size = 1.0
# 
#         # Fill the region up with loss curve sites
#         loss_curves = {}
#         for site in loss_map_region:
#             loss_curves[site] = shapes.Curve([
#                 ('0.0', 0.24105392741891271), 
#                 ('1280.0', 0.23487103910274165), 
#                 ('2560.0', 0.22617525423987336), 
#                 ('3840.0', 0.21487350918336773), 
#                 ('5120.0', 0.20130828974113113), 
#                 ('6400.0', 0.18625699583339819), 
#                 ('8320.0', 0.16321642950263798), 
#                 ('10240.0', 0.14256493660395209), 
#                 ('12160.0', 0.12605402369513649), 
#                 ('14080.0', 0.11348740908284834), 
#                 ('16000.0', 0.103636128778507), 
#                 ('21120.0', 0.083400493736596762), 
#                 ('26240.0', 0.068748634724073318), 
#                 ('31360.0', 0.059270296098829112), 
#                 ('36480.0', 0.052738173061141945), 
#                 ('41600.0', 0.047128144517224253), 
#                 ('49280.0', 0.039134392774233986), 
#                 ('56960.0', 0.032054271427490524), 
#                 ('64640.0', 0.026430436298219544), 
#                 ('72320.0', 0.022204123970325802), 
#                 ('80000.0', 0.018955490690565201), 
#                 ('90240.0', 0.01546384521034673), 
#                 ('100480.0', 0.01253420544337625), 
#                 ('110720.0', 0.010091272074791734), 
#                 ('120960.0', 0.0081287946107584975), 
#                 ('131200.0', 0.0065806376555058105), 
#                 ('140160.0', 0.0054838330271587809), 
#                 ('149120.0', 0.0045616733509618087), 
#                 ('158080.0', 0.0037723441973124923), 
#                 ('167040.0', 0.0030934392072837253), 
#                 ('176000.0', 0.0025140588978909578), 
#                 ('189440.0', 0.0018158701863753069), 
#                 ('202880.0', 0.0012969740515868437), 
#                 ('216320.0', 0.00092183863089347865), 
#                 ('229760.0', 0.00065389822562465858), 
#                 ('243200.0', 0.00046282828510792824)])
#             
#         grid = loss_map_region.grid
# 
#         # NOTE(fab): in numpy, the order of axes in a 2-dim array 
#         # is (rows, columns)
#         losses = numpy.zeros((grid.rows, grid.columns), dtype=float)
#         probability = 0.01
#         
#         # check that the loss is the expected value
#         self.assertAlmostEqual(111196.24804, engines.compute_loss(loss_curves[site], 0.01))
#         self.assertAlmostEqual(77530.7057443, engines.compute_loss(loss_curves[site], 0.02))
#         self.assertAlmostEqual(38978.9972802, engines.compute_loss(loss_curves[site], 0.05))
#         self.assertAlmostEqual(16920.0096418, engines.compute_loss(loss_curves[site], 0.10))
#         
#         #interpolation intervals are defined as [1%, 2%, 5%, 10%] in 50 years
#         intervals = [0.01, 0.02, 0.05, 0.10]
#         for interval in intervals:
#             for gridpoint in grid:
#                 loss_value = engines.compute_loss(loss_curves[site], interval)
#                 losses[gridpoint.row-1][gridpoint.column-1] = loss_value
# 
#         logger.debug('%s= losses', losses)
#         logger.debug('%s = loss_value', loss_value)
#         logger.debug('%s = gridpoint', gridpoint)
#         logger.debug('%s = interval', interval)
#         logger.debug('%s = loss_value', loss_value)
#         logger.debug('%s = loss_curves', loss_curves[site])
# 
#     def test_zero_curve_produces_zero_loss(self):
#         # check that curves of zero produce zero loss (and no error)
#         zero_curve = shapes.Curve([('0.0', 0.0), ('0.0', 0.0),])        
#         loss_value = engines.compute_loss(zero_curve, 0.01)
#         self.assertEqual(0.0, loss_value)
#         
#     def test_loss_value_interpolation_bounds(self):
#         # for a set of example loss ratio curves and a single invest. interval,
#         interval = 0.01
#         zero_curve = shapes.EMPTY_CURVE
#         huge_curve = shapes.Curve([(10.0, 10.0)])
#         normal_curve = shapes.Curve([(0.1, 0.2), (0.2, 0.21)])
#         loss_curves = [zero_curve, normal_curve, huge_curve]
#     
#         # check that curves with no point < 5 don't throw an error
#             
#     @test.skipit
#     def test_site_intersections(self):
#         """Loss ratios and loss curves can only be computed when we have:
#         
#          1. A hazard curve for the site
#          2. An exposed asset for the site
#          3. The vulnerability curve for the asset
#          4. A region of interest that includes the site
# 
#         TODO(fab): This test should be split, and the fragments should be
#         assigned to tests for other modules:
#         1) The first part that asserts that the first point is not contained 
#            in the convex hull of the three other points should be moved to 
#            the tests for the 'shapes' module.
#         2) The second part that asserts that exceptions are raised if hazard
#            and exposure are not given for the same sites should be moved to
#            tests for the 'jobber' module.
#         """
# 
#         # NOTE(fab): these points are all on a line, so the convex hull of
#         # their union will be a LINESTRING
#         first_site = shapes.Site(10.0, 10.0)
#         second_site = shapes.Site(11.0, 11.0)
#         third_site = shapes.Site(12.0, 12.0)
#         fourth_site = shapes.Site(13.0, 13.0)
#         
#         multi_point = \
#             second_site.point.union(third_site.point).union(fourth_site.point)
#         region_of_interest = shapes.Region(multi_point.convex_hull)
#         
#         logger.debug("Region of interest bounds are %s", 
#             str(region_of_interest.bounds))
#         
#         self.assertRaises(Exception, region_of_interest.grid.point_at, first_site)
# 
#         second_gp = region_of_interest.grid.point_at(second_site)
#         third_gp = region_of_interest.grid.point_at(third_site)
#         fourth_gp = region_of_interest.grid.point_at(fourth_site)
#         
#         logger.debug("Second GP is at %s: %s, %s", 
#             str(second_gp), second_gp.row, second_gp.column)
#         
#         hazard_curves = {}
#         # hazard_curves[first_gp] = shapes.Curve([('6.0', 0.0), ('7.0', 0.0)])
#         hazard_curves[second_gp] = shapes.Curve([('6.0', 0.0), ('7.0', 0.0)])
#         hazard_curves[third_gp] = shapes.Curve([('6.0', 0.0), ('7.0', 0.0)])
#         
#         ratio_results = {}
#         loss_results = {}
#         
#         # TODO(fab): use vulnerability file for tests, 
#         vulnerability_curves = {}
#         vulnerability_curves['RC/ND-FR-D/HR'] = shapes.Curve(
#             [(5.0, (0.25, 0.5)),
#              (6.0, (0.4, 0.4)),
#              (7.0, (0.6, 0.3))])
#         
#         # TODO(fab): use exposure file for tests
#         exposure_portfolio = {}
#         exposure_portfolio[fourth_gp] = {'AssetValue': 320000.0, 'PortfolioID': 'PAV01', 
#             'VulnerabilityFunction': 'RC/ND-FR-D/HR', 'AssetID': '06', 
#             'PortfolioDescription': 'Collection of existing building in downtown Pavia', 
#             'AssetDescription': 'Moment-resisting ductile concrete frame high rise'}
#         
#         # TODO(fab): use memcached-enabled engine, through jobber
#         risk_engine = engines.ProbabilisticLossRatioCalculator(hazard_curves, 
#                                 exposure_portfolio)
#                                   
#         for gridpoint in region_of_interest.grid:
#             ratio_results[gridpoint] = \
#                 risk_engine.compute_loss_ratio_curve(gridpoint)
#             loss_results[gridpoint] = \
#                 risk_engine.compute_loss_curve(gridpoint, 
#                                                ratio_results[gridpoint])
#         
#         logger.debug("Ratio Results keys are %s" % ratio_results.keys())
#         
#         #self.assertFalse(first_gp in ratio_results.keys())
#         self.assertEqual(ratio_results[third_gp], None)
#         self.assertEqual(ratio_results[second_gp], None) # No asset, 
#         
#         # No exposure at second site, so no loss results
#         self.assertEqual(loss_results[second_gp], None)
#         # self.assertNotEqual(loss_results[fourth_gp], None)
