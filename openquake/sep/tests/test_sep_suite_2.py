import os
import unittest

import numpy as np
import pandas as pd

from openquake.sep.landslide.common import static_factor_of_safety
from openquake.sep.landslide.newmark import (
    newmark_critical_accel,
    newmark_displ_from_pga_M,
    prob_failure_given_displacement,
)

from openquake.sep.liquefaction import (
    HAZUS_LIQUEFACTION_PGA_THRESHOLD_TABLE,
    hazus_liquefaction_probability,
    zhu_etal_2015_liquefaction_probability_general,
    zhu_etal_2017_liquefaction_probability_coastal,
    zhu_etal_2017_liquefaction_probability_general,
    bozzoni_etal_2021_liquefaction_probability_europe
)

from openquake.sep.liquefaction.lateral_spreading import (
    hazus_lateral_spreading_displacement
)

BASE_DATA_PATH = os.path.join(os.path.dirname(__file__), "data")
site_data_file = os.path.join(BASE_DATA_PATH, "test_site_params.csv")

class test_landslides_cali_small(unittest.TestCase):
    def setUp(self):
        sites = pd.read_csv(site_data_file)
        self.sites = sites

        self.sites["Fs"] = static_factor_of_safety(
            slope=sites.slope,
            cohesion=sites.cohesion_mid,
            friction_angle=sites.friction_mid,
            saturation_coeff=sites.saturation,
            soil_dry_density=sites.dry_density,
        )

        self.sites["crit_accel"] = newmark_critical_accel(self.sites.Fs, 
            self.sites.slope)

        self.pga = np.array([0.29624916, 0.80906772, 0.35025253, 0.78940926,
            0.56134898, 0.25358895, 0.10497708, 0.05846073, 0.67329238,
            0.69782966])


    def test_static_factor_of_safety(self):
        factor_of_safety = np.array([17.74377843, 15.24124039, 73.15947545,
            0.78146658, 27.54726138, 9.90996951, 2.789039 , 41.66518694,
            19.55433591, 14.75323389])
        
        np.testing.assert_array_almost_equal(self.sites["Fs"], factor_of_safety)

    def test_critical_accel(self):
        ca = np.array([5.53795977, 6.45917414, 5.791588, 0., 14.81513269,
            5.26990181, 4.20417316, 135.89284561, 6.40149393, 6.28627584])

        np.testing.assert_array_almost_equal(self.sites["crit_accel"], ca)

    def test_newmark_displacement(self):
        self.sites["newmark_disp"] = newmark_displ_from_pga_M(pga=self.pga,
            critical_accel=self.sites['crit_accel'], M=7.5)

        nd = np.array([0., 0., 0., 2.19233517, 0., 0., 0., 0., 0., 0.])

        np.testing.assert_array_almost_equal(self.sites["newmark_disp"], nd)

    def test_newmark_prob_displacement(self):
        self.sites["newmark_disp"] = newmark_displ_from_pga_M(pga=self.pga,
            critical_accel=self.sites['crit_accel'], M=7.5)

        self.sites["prob_disp"] = prob_failure_given_displacement(
            self.sites["newmark_disp"]
        )

        prob_d = np.array([0., 0., 0., 0.335, 0., 0., 0., 0., 0., 0.])

        np.testing.assert_array_almost_equal(self.sites["prob_disp"], prob_d)

        

class test_liquefaction_cali_small(unittest.TestCase):

    def setUp(self):
        sites = pd.read_csv(site_data_file)
        self.sites = sites
        self.mag = 7.5
        self.map_proportion_flag = True

        self.pga = np.array([0.29624916, 0.80906772, 0.35025253, 0.78940926,
            0.56134898, 0.25358895, 0.10497708, 0.05846073, 0.67329238,
            0.69782966])
        
        self.pgv = np.array([10, 20, 30, 40, 45, 50, 55, 60, 65, 70])

    def test_hazus_liquefaction_prob(self):
        self.sites["haz_liq_prob"] = hazus_liquefaction_probability(
            pga=self.pga, mag=self.mag, liq_susc_cat=self.sites["liq_susc_cat"],
            groundwater_depth=self.sites["gwd"],
            do_map_proportion_correction=self.map_proportion_flag)

        lp = np.array([0.20710826, 0.04829711, 0.20710826, 0.04664702,
            0.20710826, 0.20710826, 0. , 0. , 0.04664702, 0.04664702])

        np.testing.assert_array_almost_equal(self.sites["haz_liq_prob"], lp)


    def test_zhu_liquefaction_prob(self):
        self.sites["zhu_liq_prob"] = zhu_etal_2015_liquefaction_probability_general(
            pga=self.pga, mag=self.mag, cti=self.sites["cti"], 
            vs30=self.sites["vs30"])

        zlp = np.array([0.506859, 0.383202, 0.438535, 0.807301,
            0.807863, 0.595353, 0.079580, 0.003111, 0.792592,
            0.603895])

        np.testing.assert_array_almost_equal(self.sites["zhu_liq_prob"], zlp)

    def test_bozzoni_liquefaction_prob(self):
        self.sites["bozzoni_liq_prob"] = bozzoni_etal_2021_liquefaction_probability_europe(
            pga=self.pga, mag=self.mag, cti=self.sites["cti"], 
            vs30=self.sites["vs30"])

        zlp = np.array([1, 1, 0.999999, 1, 1, 0.999999, 0.999989, 0.999922, 1, 1])

        np.testing.assert_array_almost_equal(self.sites["bozzoni_liq_prob"], zlp)

    def test_zhu_coastal_liquefaction_prob(self):
        self.sites["zhu17_coastal_liq_prob"] = zhu_etal_2017_liquefaction_probability_coastal(
            pgv=self.pgv, vs30=self.sites["vs30"], dr=self.sites["dr"], dc=self.sites["dc"], 
            precip=self.sites["precip"])

        zlp = np.array([0.147724296, 0.059958674, 0.206449471, 0.142744967, 0.218298201,
                        0.342584912, 0.217105303, 0.088124828, 0.234620795, 0.13528652])

        np.testing.assert_array_almost_equal(self.sites["zhu17_coastal_liq_prob"], zlp)

    def test_zhu_general_liquefaction_prob(self):
        self.sites["zhu17_general_liq_prob"] = zhu_etal_2017_liquefaction_probability_general(
            pgv=self.pgv, vs30=self.sites["vs30"], dw=self.sites["dw"], wtd=self.sites["gwd"], 
            precip=self.sites["precip"])

        zlp = np.array([0.238647776, 0.134912013, 0.325250532, 0.253336248, 0.34605218,
                        0.458236498, 0.334831618, 0.1798869, 0.359086043, 0.252791617])

        np.testing.assert_array_almost_equal(self.sites["zhu17_general_liq_prob"], zlp)

    
    def test_hazus_liquefaction_displacements(self):

        self.sites["hazus_lat_disp"] = hazus_lateral_spreading_displacement(
            mag=self.mag, pga=self.pga, liq_susc_cat=self.sites["liq_susc_cat"]
        )

        disps = np.array([0.53306034, 2.33933074, 0.74434279, 2.168416,
            3.84597609, 0.36615681, 0., 0., 1.15887168, 1.3722039 ])

        np.testing.assert_array_almost_equal(self.sites.hazus_lat_disp, disps)
