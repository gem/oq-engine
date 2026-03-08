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
            slab_thickness=sites.slab_thickness.to_numpy(),
        )
        self.sites["crit_accel"] = critical_accel(
            self.sites.Fs, self.sites.slope
        )
        self.pga = np.array([0.29624916, 0.80906772, 0.35025253, 0.78940926, 0.56134898, 0.25358895, 0.10497708, 0.05846073, 0.67329238, 0.69782966])
        self.pgv = np.array([10, 20, 30, 40, 45, 50, 55, 60, 65, 70])

    def test_infinite_slope_fs(self):
        factor_of_safety = np.array([17.743779, 15.241239, 73.159459, 0.781467, 27.547261, 9.90997, 2.789039, 41.665187, 19.554335, 14.753234])
        np.testing.assert_array_almost_equal(
            self.sites["Fs"], factor_of_safety
        )

    def test_critical_accel(self):
        ca = np.array([0.564522, 0.658428, 0.590376, 0.000100, 1.510207, 0.537197, 0.428560, 13.852482, 0.652548, 0.640803])
        np.testing.assert_array_almost_equal(self.sites["crit_accel"], ca)

    def test_newmark_displacement(self):
        self.sites["newmark_disp"] = jibson_2007_model_b(
            pga=self.pga, crit_accel=self.sites["crit_accel"], mag=7.5
        )
        nd = np.array([0.0, 7.899399e-04, 0.0, 2.192335e00, 0.0, 0.0, 0.0, 0.0, 9.145443e-06, 9.660795e-05])
        np.testing.assert_array_almost_equal(self.sites["newmark_disp"], nd)

    def test_nowicki_jessee_18(self):
        prob_ls, coverage = nowicki_jessee_2018(
            pgv=self.pgv,
            slope=self.sites["slope"],
            lithology=self.sites["lithology"],
            landcover=self.sites["landcover"],
            cti=self.sites["cti"],
        )
        zlp = np.array([0.011672, 0.052064, 0.057599, 0.888425, 0.191497, 0.190742, 0.48066, 0.897942, 0.207814, 0.17799])
        cls = np.array([0.053605, 0.065753, 0.067576, 8.119564, 0.126543, 0.126111, 0.484645, 8.884508, 0.136195, 0.119038])
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
        zlp = np.array([0.070513, 0.260801, 0.281926, 0.980824, 0.603409, 0.602239, 0.856018, 0.897942, 0.62758, 0.581753])
        cls = np.array([0, 0.172675, 0, 20.709538, 0.953252, 0.946616, 6.037904, 8.884508, 1.104123, 0.839227])
        np.testing.assert_array_almost_equal(prob_ls, zlp)
        np.testing.assert_array_almost_equal(coverage, cls)
