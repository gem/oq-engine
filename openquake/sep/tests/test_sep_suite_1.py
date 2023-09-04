import os
import unittest

import numpy as np

try:
    import xarray as xr
    xr_import = True
except:
    xr_import = False

from openquake.sep.utils import make_local_relief_raster
from openquake.sep.calculators import (
    calc_newmark_soil_slide_single_event,
    calc_newmark_soil_slide_event_set,
)


BASE_DATA_PATH = os.path.join(os.path.dirname(__file__), "data")
test_dem = os.path.join(BASE_DATA_PATH, "dem_small.tif")
test_relief = os.path.join(BASE_DATA_PATH, "relief_out.tif")
test_slope = os.path.join(BASE_DATA_PATH, "slope_small.tif")
test_saturation = os.path.join(BASE_DATA_PATH, "saturation.tif")
test_friction = os.path.join(BASE_DATA_PATH, "friction.tif")
test_cohesion = os.path.join(BASE_DATA_PATH, "cohesion.tif")
test_pga = os.path.join(BASE_DATA_PATH, "pga.nc")
test_Dn_single = os.path.join(BASE_DATA_PATH, "Dn_single.nc")
test_Dn_set = os.path.join(BASE_DATA_PATH, "Dn_set.nc")

@unittest.skipIf(xr_import == False, "XArray not available")
class test_sec_perils_cali_small_xr(unittest.TestCase):
    """
    Integration test suite for secondary perils, with small set of realistic
    inputs.  This is for using a possibly-obselete interface that uses XArray,
    which is not currently part of the OpenQuake engine dependencies.
    """
    @unittest.skipIf(xr_import == False, "XArray not available")
    def setUp(self):
        self.relief_map = xr.open_rasterio(test_relief, parse_coordinates=True)[
            0
        ]
        self.slope_map = xr.open_rasterio(test_slope, parse_coordinates=True)[0]
        self.pga = xr.open_dataset(test_pga)
        self.saturation = xr.open_rasterio(
            test_saturation, parse_coordinates=True
        )[0]
        self.friction = xr.open_rasterio(test_friction, parse_coordinates=True)[
            0
        ]
        self.cohesion = xr.open_rasterio(test_cohesion, parse_coordinates=True)[
            0
        ]
        self.Dn_single = xr.open_dataset(test_Dn_single)["Dn"]
        self.Dn_set = xr.open_dataset(test_Dn_set)

        (
            self.relief_map,
            self.slope_map,
            self.pga,
            self.saturation,
            self.friction,
            self.cohesion,
        ) = xr.align(
            self.relief_map,
            self.slope_map,
            self.pga,
            self.saturation,
            self.friction,
            self.cohesion,
            join="override",
        )

    @unittest.skipIf(xr_import == False, "XArray not available")
    def test_calc_newmark_soil_slide_single_event(self):
        eq_pga = self.pga["1286"]

        Dn = calc_newmark_soil_slide_single_event(
            pga=eq_pga,
            M=eq_pga.attrs["mag"],
            slope=self.slope_map,
            cohesion=self.cohesion,
            friction_angle=self.friction,
            saturation_coeff=self.saturation,
            out_name="Dn",
        )

        np.testing.assert_array_almost_equal(Dn, self.Dn_single)

    @unittest.skipIf(xr_import == False, "XArray not available")
    def test_calc_newmark_soil_slide_event_set(self):
        Dn_set = calc_newmark_soil_slide_event_set(
            pga=self.pga,
            M=None,
            slope=self.slope_map,
            cohesion=self.cohesion,
            friction_angle=self.friction,
            saturation_coeff=self.saturation,
        )

        for key, val in Dn_set.items():
            np.testing.assert_array_almost_equal(
                val.values, self.Dn_set[key].values
            )
