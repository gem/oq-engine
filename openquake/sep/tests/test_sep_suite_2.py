import os
import unittest

import numpy as np
import pandas as pd

from openquake.sep.landslide.static_safety_factor import (
    infinite_slope_fs,
)
from openquake.sep.landslide.displacement import (
    critical_accel,
    jibson_2007_model_b,
)

from openquake.sep.landslide.probability import (
    nowicki_jessee_2018,
    allstadt_etal_2022_b,
)

from openquake.sep.classes import (
    PicklableInferenceSession,
    TodorovicSilva2022NonParametric,
)

from openquake.sep.liquefaction import (
    hazus_liquefaction_probability,
    zhu_etal_2015_general,
    zhu_etal_2017_coastal,
    zhu_etal_2017_general,
    rashidian_baise_2020,
    allstadt_etal_2022,
    akhlagi_etal_2021_model_a,
    akhlagi_etal_2021_model_b,
    bozzoni_etal_2021_europe,
    todorovic_silva_2022_nonparametric_general,
)

from openquake.sep.liquefaction.lateral_spreading import (
    hazus_lateral_spreading_displacement,
)

BASE_DATA_PATH = os.path.join(os.path.dirname(__file__), "data")
site_data_file = os.path.join(BASE_DATA_PATH, "test_site_params.csv")


class CaliSmallLandslideTestCase(unittest.TestCase):
    def setUp(self):
        sites = pd.read_csv(site_data_file)
        self.sites = sites
        self.sites["Fs"] = infinite_slope_fs(
            slope=sites.slope.to_numpy(),
            cohesion=sites.cohesion_mid.to_numpy(),
            friction_angle=sites.friction_mid.to_numpy(),
            saturation_coeff=sites.saturation.to_numpy(),
            soil_dry_density=sites.dry_density.to_numpy(),
            slab_thickness = sites.slab_thickness.to_numpy(),
        )
        self.sites["crit_accel"] = critical_accel(
            self.sites.Fs, self.sites.slope
        )
        self.pga = np.array(
            [
                0.29624916,
                0.80906772,
                0.35025253,
                0.78940926,
                0.56134898,
                0.25358895,
                0.10497708,
                0.05846073,
                0.67329238,
                0.69782966,
            ]
        )
        self.pgv = np.array([10, 20, 30, 40, 45, 50, 55, 60, 65, 70])

    def test_infinite_slope_fs(self):
        factor_of_safety = np.array(
            [
                17.74377843,
                15.24124039,
                73.15947545,
                0.78146658,
                27.54726138,
                9.90996951,
                2.789039,
                41.66518694,
                19.55433591,
                14.75323389,
            ]
        )
        np.testing.assert_array_almost_equal(
            self.sites["Fs"], factor_of_safety
        )

    def test_critical_accel(self):
        ca = np.array(
            [
                5.537960,
                6.459174,
                5.791588,
                0.0001,
                14.815133,
                5.269902,
                4.204173,
                135.892846,
                6.401494,
                6.286276,
            ]
        )
        np.testing.assert_array_almost_equal(self.sites["crit_accel"], ca)

    def test_newmark_displacement(self):
        self.sites["newmark_disp"] = jibson_2007_model_b(
            pga=self.pga, crit_accel=self.sites["crit_accel"], mag=7.5
        )
        nd = np.array(
            [0.0, 0.0, 0.0, 2.19233517, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        )
        np.testing.assert_array_almost_equal(self.sites["newmark_disp"], nd)

    def test_nowicki_jessee_18(self):
        prob_ls, coverage = nowicki_jessee_2018(
            pgv=self.pgv,
            slope=self.sites["slope"],
            lithology=self.sites["lithology"],
            landcover=self.sites["landcover"],
            cti=self.sites["cti"],
        )
        zlp = np.array(
            [
                0.011672,
                0.052064,
                0.057599,
                0.888425,
                0.191497,
                0.190742,
                0.48066,
                0.897942,
                0.207814,
                0.17799,
            ]
        )
        cls = np.array(
            [
                0.053605,
                0.065753,
                0.067576,
                8.119564,
                0.126543,
                0.126111,
                0.484645,
                8.884508,
                0.136195,
                0.119038,
            ]
        )
        np.testing.assert_array_almost_equal(prob_ls, zlp)
        np.testing.assert_array_almost_equal(coverage, cls)


    def test_allstadt_etal_2022_b(self):
        prob_ls, coverage = allstadt_etal_2022_b(
            pga=self.pga,
            pgv=self.pgv,
            slope=self.sites["slope"],
            lithology=self.sites["lithology"],
            landcover=self.sites["landcover"],
            cti=self.sites["cti"],
        )
        zlp = np.array(
            [
                0.070513,
                0.260801,
                0.281926,
                0.980824,
                0.603409,
                0.602239,
                0.856018,
                0.897942,
                0.62758,
                0.581753,
            ]
        )
        cls = np.array(
            [
                0,
                0.172675,
                0,
                20.709538,
                0.953252,
                0.946616,
                6.037904,
                8.884508,
                1.104123,
                0.839227,
            ]
        )
        np.testing.assert_array_almost_equal(prob_ls, zlp)
        np.testing.assert_array_almost_equal(coverage, cls)


class CaliSmallLiquefactionTestCase(unittest.TestCase):
    def setUp(self):
        sites = pd.read_csv(site_data_file)
        self.sites = sites
        self.mag = 7.5
        self.map_proportion_flag = True
        self.pga = np.array(
            [
                0.29624916,
                0.80906772,
                0.35025253,
                0.78940926,
                0.56134898,
                0.25358895,
                0.10497708,
                0.05846073,
                0.67329238,
                0.69782966,
            ]
        )
        self.pgv = np.array([10, 20, 30, 40, 45, 50, 55, 60, 65, 70])

    def test_hazus_liquefaction_prob(self):
        self.sites["haz_liq_prob"] = hazus_liquefaction_probability(
            pga=self.pga,
            mag=self.mag,
            liq_susc_cat=self.sites["liq_susc_cat"],
            groundwater_depth=self.sites["gwd"],
            do_map_proportion_correction=self.map_proportion_flag,
        )
        lp = np.array(
            [
                0.20710826,
                0.04829711,
                0.20710826,
                0.04664702,
                0.20710826,
                0.20710826,
                0.0,
                0.0,
                0.04664702,
                0.04664702,
            ]
        )
        np.testing.assert_array_almost_equal(self.sites["haz_liq_prob"], lp)

    def test_zhu15_general(self):
        prob_liq, out_class = zhu_etal_2015_general(
            pga=self.pga,
            mag=self.mag,
            cti=self.sites["cti"],
            vs30=self.sites["vs30"],
        )
        zlp = np.array(
            [
                0.506859,
                0.383202,
                0.438535,
                0.807301,
                0.807863,
                0.595353,
                0.079580,
                0.003111,
                0.792592,
                0.603895,
            ]
        )
        clq = np.array([1, 1, 1, 1, 1, 1, 0, 0, 1, 1])
        np.testing.assert_array_almost_equal(prob_liq, zlp)
        np.testing.assert_array_almost_equal(out_class, clq)

    def test_bozzoni_europe(self):
        prob_liq, out_class = bozzoni_etal_2021_europe(
            pga=self.pga,
            mag=self.mag,
            cti=self.sites["cti"],
            vs30=self.sites["vs30"],
        )
        zlp = np.array(
            [1, 1, 0.999999, 1, 1, 0.999999, 0.999989, 0.999922, 1, 1]
        )
        clq = np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
        np.testing.assert_array_almost_equal(prob_liq, zlp)
        np.testing.assert_array_almost_equal(out_class, clq)

    def test_zhu17_coastal(self):
        prob_liq, out_class, LSE = zhu_etal_2017_coastal(
            pgv=self.pgv,
            vs30=self.sites["vs30"],
            dr=self.sites["dr"],
            dc=self.sites["dc"],
            precip=self.sites["precip"],
        )
        zlp = np.array(
            [
                0.147724296,
                0.059958674,
                0.206449471,
                0.142744967,
                0.218298201,
                0.342584912,
                0.217105303,
                0.088124828,
                0.234620795,
                0.13528652,
            ]
        )
        clq = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        lse = np.array(
            [
                0.266467348,
                0.039739528,
                0.880926509,
                0.239906371,
                1.107989336,
                8.333205144,
                1.082937311,
                0.073922458,
                1.50712136,
                0.204819111,
            ]
        )
        np.testing.assert_array_almost_equal(prob_liq, zlp)
        np.testing.assert_array_almost_equal(out_class, clq)
        np.testing.assert_array_almost_equal(LSE, lse)

    def test_zhu17_general(self):
        prob_liq, out_class, LSE = zhu_etal_2017_general(
            pgv=self.pgv,
            vs30=self.sites["vs30"],
            dw=self.sites["dw"],
            wtd=self.sites["gwd"],
            precip=self.sites["precip"],
        )
        zlp = np.array(
            [
                0.238647776,
                0.134912013,
                0.325250532,
                0.253336248,
                0.34605218,
                0.458236498,
                0.334831618,
                0.1798869,
                0.359086043,
                0.252791617,
            ]
        )
        clq = np.array([0, 0, 0, 0, 0, 1, 0, 0, 0, 0])
        lse = np.array(
            [
                1.482171022,
                0.277301525,
                4.948255956,
                1.846543588,
                6.368079142,
                18.36402489,
                5.569162964,
                0.586570244,
                7.395635138,
                1.831734979,
            ]
        )
        np.testing.assert_array_almost_equal(prob_liq, zlp)
        np.testing.assert_array_almost_equal(out_class, clq)
        np.testing.assert_array_almost_equal(LSE, lse)

    def test_rashidian_baise_2020(self):
        prob_liq, out_class, LSE = rashidian_baise_2020(
            pgv=self.pgv,
            pga=self.pga,
            vs30=self.sites["vs30"],
            dw=self.sites["dw"],
            wtd=self.sites["gwd"],
            precip=self.sites["precip"],
        )
        zlp = np.array(
            [
                0.238647776,
                0.134912013,
                0.325250532,
                0.253336248,
                0.34605218,
                0.458236498,
                0.334831618,
                0,
                0.359086043,
                0.252791617,
            ]
        )
        clq = np.array([0, 0, 0, 0, 0, 1, 0, 0, 0, 0])
        lse = np.array(
            [
                1.482171022,
                0.277301525,
                4.948255956,
                1.846543588,
                6.368079142,
                18.36402489,
                5.569162964,
                0.026094205,
                7.395635138,
                1.831734979,
            ]
        )
        np.testing.assert_array_almost_equal(prob_liq, zlp)
        np.testing.assert_array_almost_equal(out_class, clq)
        np.testing.assert_array_almost_equal(LSE, lse)

    def test_allstadt_2022(self):
        prob_liq, out_class, LSE = allstadt_etal_2022(
            pgv=self.pgv,
            pga=self.pga,
            mag=self.mag,
            vs30=self.sites["vs30"],
            dw=self.sites["dw"],
            wtd=self.sites["gwd"],
            precip=self.sites["precip"],
        )
        zlp = np.array(
            [
                0.235711715,
                0.133029207,
                0.321699203,
                0.25027888,
                0.342388975,
                0.454210576,
                0.33122703,
                0,
                0.355359841,
                0.249738624,
            ]
        )
        clq = np.array([0, 0, 0, 0, 0, 1, 0, 0, 0, 0])
        lse = np.array(
            [
                1.417553345,
                0.268584431,
                4.732082598,
                1.764759601,
                6.098616151,
                17.83890389,
                5.329037755,
                0.026094205,
                7.090862255,
                1.750645015,
            ]
        )
        np.testing.assert_array_almost_equal(prob_liq, zlp)
        np.testing.assert_array_almost_equal(out_class, clq)
        np.testing.assert_array_almost_equal(LSE, lse)

    def test_akhlagi_2021_model_a(self):
        prob_liq, out_class = akhlagi_etal_2021_model_a(
            pgv=self.pgv,
            tri=self.sites["tri"],
            dc=self.sites["dc"],
            dr=self.sites["dr"],
            zwb=self.sites["zwb"],
        )
        zlp = np.array(
            [
                0.949740,
                0.660622,
                0.982408,
                0.972950,
                0.989203,
                0.992851,
                0.000016,
                0.526811,
                0.988699,
                0.908844,
            ]
        )
        clq = np.array([1, 1, 1, 1, 1, 1, 0, 1, 1, 1])
        np.testing.assert_array_almost_equal(prob_liq, zlp)
        np.testing.assert_array_almost_equal(out_class, clq)

    def test_akhlagi_2021_b(self):
        prob_liq, out_class = akhlagi_etal_2021_model_b(
            pgv=self.pgv,
            vs30=self.sites["vs30"],
            dc=self.sites["dc"],
            dr=self.sites["dr"],
            zwb=self.sites["zwb"],
        )
        zlp = np.array(
            [
                0.973289,
                0.974526,
                0.988385,
                0.988594,
                0.990865,
                0.992976,
                0.991752,
                0.989183,
                0.992784,
                0.990591,
            ]
        )
        clq = np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
        np.testing.assert_array_almost_equal(prob_liq, zlp)
        np.testing.assert_array_almost_equal(out_class, clq)

    def test_todorovic_2022(self):
        model_instance = TodorovicSilva2022NonParametric()
        model_instance.prepare(self.sites)
        inference_session = PicklableInferenceSession(model_instance.model)
        out_class, out_prob = todorovic_silva_2022_nonparametric_general(
            pgv=self.pgv,
            vs30=self.sites["vs30"],
            dw=self.sites["dw"],
            wtd=self.sites["gwd"],
            precip=self.sites["precip"],
            session=inference_session,
        )
        clq = np.array([0, 0, 0, 0, 0, 1, 0, 0, 1, 1])
        zlp = np.array(
            [
                0.142747,
                0.084723,
                0.483987,
                0.419369,
                0.444786,
                0.706952,
                0.323834,
                0.394872,
                0.934869,
                0.607842,
            ]
        )
        np.testing.assert_array_almost_equal(out_class, clq)
        np.testing.assert_array_almost_equal(out_prob, zlp)

    def test_hazus_liquefaction_displacements(self):
        self.sites["hazus_lat_disp"] = hazus_lateral_spreading_displacement(
            mag=self.mag, pga=self.pga, liq_susc_cat=self.sites["liq_susc_cat"]
        )
        disps = np.array(
            [
                0.53306034,
                2.33933074,
                0.74434279,
                2.168416,
                3.84597609,
                0.36615681,
                0.0,
                0.0,
                1.15887168,
                1.3722039,
            ]
        )
        np.testing.assert_array_almost_equal(self.sites.hazus_lat_disp, disps)
