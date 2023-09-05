import os
import unittest

import numpy as np

from openquake.sep.liquefaction import liquefaction


class test_zhu_functions(unittest.TestCase):
    def test_idriss_magnitude_weighting_factor(self):
        mags = np.array([6.0, 7.0, 8.0])
        test_res = np.array([0.5650244, 0.83839945, 1.18007706])
        np.testing.assert_array_almost_equal(
            liquefaction._idriss_magnitude_weighting_factor(mags), test_res
        )


class test_hazus_liquefaction_functions(unittest.TestCase):
    def test_hazus_magnitude_correction_factor(self):
        # magnitudes selected to roughly replicate Fig. 4.7 in the Hazus manual
        mags = np.array([5.1, 6.1, 6.8, 7.6, 8.4])
        Km = liquefaction._hazus_magnitude_correction_factor(mags)
        test_res = np.array(
            [1.5344407, 1.2845917, 1.1357584, 1.0000432, 0.9089488]
        )
        np.testing.assert_array_almost_equal(Km, test_res)

    def test_hazus_gw_correction_factor_ft(self):
        # replicates Fig. 4.8 in the Hazus manual
        depth_ft = np.arange(4, 36, 4)
        Kw = liquefaction._hazus_groundwater_correction_factor(depth_ft)
        test_res = np.array(
            [1.018, 1.106, 1.194, 1.282, 1.37, 1.458, 1.546, 1.634]
        )
        np.testing.assert_array_almost_equal(Kw, test_res)

    def test_hazus_conditional_liquefaction_probability_vl(self):
        # replicates Fig. 4.6 in the Hazus manual
        pga_vl = np.linspace(0.2, 0.6, num=10)
        cond_vl = liquefaction._hazus_conditional_liquefaction_probability(pga_vl, "vl")
        test_res = np.array(
            [
                0.0,
                0.0,
                0.12177778,
                0.30666667,
                0.49155556,
                0.67644444,
                0.86133333,
                1.0,
                1.0,
                1.0,
            ]
        )

        np.testing.assert_array_almost_equal(cond_vl, test_res)

    def test_hazus_conditional_liquefaction_probability_l(self):
        # Replicates Fig. 4.6 in the Hazus manual
        # However values do not match figure exactly, though
        # the formula and coefficients are double-checked...
        pga_l = np.linspace(0.2, 0.6, num=10)
        cond_l = liquefaction._hazus_conditional_liquefaction_probability(pga_l, "l")
        test_res = np.array(
            [
                0.0,
                0.18155556,
                0.42911111,
                0.67666667,
                0.92422222,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
            ]
        )

        np.testing.assert_array_almost_equal(cond_l, test_res)

    def test_hazus_conditional_liquefaction_probability_m(self):
        # Replicates Fig. 4.6 in the Hazus manual
        # However values do not match figure exactly, though
        # the formula and coefficients are double-checked...
        pga_m = np.linspace(0.1, 0.4, num=10)
        cond_m = liquefaction._hazus_conditional_liquefaction_probability(pga_m, "m")
        test_res = np.array(
            [
                0.0,
                0.0,
                0.11166667,
                0.334,
                0.55633333,
                0.77866667,
                1.0,
                1.0,
                1.0,
                1.0,
            ]
        )

        np.testing.assert_array_almost_equal(cond_m, test_res)

    def test_hazus_conditional_liquefaction_probability_h(self):
        # Replicates Fig. 4.6 in the Hazus manual
        # However values do not match figure exactly, though
        # the formula and coefficients are double-checked...
        pga_h = np.linspace(0.1, 0.3, num=10)
        cond_h = liquefaction._hazus_conditional_liquefaction_probability(pga_h, "h")
        test_res = np.array(
            [
                0.0,
                0.01744444,
                0.18788889,
                0.35833333,
                0.52877778,
                0.69922222,
                0.86966667,
                1.0,
                1.0,
                1.0,
            ]
        )

        np.testing.assert_array_almost_equal(cond_h, test_res)

    def test_hazus_conditional_liquefaction_probability_vh(self):
        # Replicates Fig. 4.6 in the Hazus manual
        # However values do not match figure exactly, though
        # the formula and coefficients are double-checked...
        pga_vh = np.linspace(0.05, 0.25, num=10)
        cond_vh = liquefaction._hazus_conditional_liquefaction_probability(pga_vh, "vh")
        test_res = np.array(
            [0.0, 0.0, 0.0385, 0.2405, 0.4425, 0.6445, 0.8465, 1.0, 1.0, 1.0]
        )

        np.testing.assert_array_almost_equal(cond_vh, test_res)
