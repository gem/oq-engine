import os
import unittest
import tempfile

import numpy as np
try:
    from osgeo import gdal
except ImportError:
    gdal = None

from openquake.sep.utils import (
    make_2d_array_strides,
    rolling_array_operation,
    rolling_raster_operation,
    relief,
    make_local_relief_raster,
    sample_raster_at_points,
    slope_angle_to_gradient,
    vs30_from_slope,
    vs30_from_slope_wald_allen_2007,
    vs30_from_slope_wald_allen_2007_active,
    vs30_from_slope_wald_allen_2007_stable,
)


BASE_DATA_PATH = os.path.join(os.path.dirname(__file__), "data")
test_dem = os.path.join(BASE_DATA_PATH, "dem_small.tif")
test_relief = os.path.join(BASE_DATA_PATH, "relief_out.tif")


class testUtils(unittest.TestCase):
    def test_slope_angle_to_gradient_1(self):
        assert slope_angle_to_gradient(0, unit="degree") == 0.0

    def test_slope_angle_to_gradient_2(self):
        assert slope_angle_to_gradient(0, unit="radian") == 0.0

    def test_slope_angle_to_gradient_3(self):
        np.testing.assert_approx_equal(
            slope_angle_to_gradient(45.0, unit="deg"), 1.0
        )

    def test_slope_angle_to_gradient_4(self):
        slopes = np.array([0.0, 0.52359878, 0.78539816, 1.04719755, 1.53588974])
        grads = np.array([0.0, 0.57735027, 1.0, 1.73205081, 28.63625328])
        np.testing.assert_array_almost_equal(
            grads, slope_angle_to_gradient(slopes, unit="rad")
        )


class testWaldAllenVs30(unittest.TestCase):
    def test_wald_allen_vs30_1(self):
        pass


class testVs30(unittest.TestCase):
    def test_Vs30_WaldAllen_deg_vec(self):
        slopes = np.array(
            [0.01, 0.1, 0.2, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 10.0]
        )
        pass


class test_array_funcs_super_simple(unittest.TestCase):
    def setUp(self):
        self.array = np.arange(25).reshape((5, 5))

    def test_make_2d_array_strides(self):
        strides = make_2d_array_strides(self.array, 1)

        strides_result = np.array(
            [
                [
                    [
                        np.nan,
                        np.nan,
                        np.nan,
                        np.nan,
                        0.0,
                        1.0,
                        np.nan,
                        5.0,
                        6.0,
                    ],
                    [np.nan, np.nan, np.nan, 0.0, 1.0, 2.0, 5.0, 6.0, 7.0],
                    [np.nan, np.nan, np.nan, 1.0, 2.0, 3.0, 6.0, 7.0, 8.0],
                    [np.nan, np.nan, np.nan, 2.0, 3.0, 4.0, 7.0, 8.0, 9.0],
                    [
                        np.nan,
                        np.nan,
                        np.nan,
                        3.0,
                        4.0,
                        np.nan,
                        8.0,
                        9.0,
                        np.nan,
                    ],
                ],
                [
                    [np.nan, 0.0, 1.0, np.nan, 5.0, 6.0, np.nan, 10.0, 11.0],
                    [0.0, 1.0, 2.0, 5.0, 6.0, 7.0, 10.0, 11.0, 12.0],
                    [1.0, 2.0, 3.0, 6.0, 7.0, 8.0, 11.0, 12.0, 13.0],
                    [2.0, 3.0, 4.0, 7.0, 8.0, 9.0, 12.0, 13.0, 14.0],
                    [3.0, 4.0, np.nan, 8.0, 9.0, np.nan, 13.0, 14.0, np.nan],
                ],
                [
                    [np.nan, 5.0, 6.0, np.nan, 10.0, 11.0, np.nan, 15.0, 16.0],
                    [5.0, 6.0, 7.0, 10.0, 11.0, 12.0, 15.0, 16.0, 17.0],
                    [6.0, 7.0, 8.0, 11.0, 12.0, 13.0, 16.0, 17.0, 18.0],
                    [7.0, 8.0, 9.0, 12.0, 13.0, 14.0, 17.0, 18.0, 19.0],
                    [8.0, 9.0, np.nan, 13.0, 14.0, np.nan, 18.0, 19.0, np.nan],
                ],
                [
                    [
                        np.nan,
                        10.0,
                        11.0,
                        np.nan,
                        15.0,
                        16.0,
                        np.nan,
                        20.0,
                        21.0,
                    ],
                    [10.0, 11.0, 12.0, 15.0, 16.0, 17.0, 20.0, 21.0, 22.0],
                    [11.0, 12.0, 13.0, 16.0, 17.0, 18.0, 21.0, 22.0, 23.0],
                    [12.0, 13.0, 14.0, 17.0, 18.0, 19.0, 22.0, 23.0, 24.0],
                    [
                        13.0,
                        14.0,
                        np.nan,
                        18.0,
                        19.0,
                        np.nan,
                        23.0,
                        24.0,
                        np.nan,
                    ],
                ],
                [
                    [
                        np.nan,
                        15.0,
                        16.0,
                        np.nan,
                        20.0,
                        21.0,
                        np.nan,
                        np.nan,
                        np.nan,
                    ],
                    [
                        15.0,
                        16.0,
                        17.0,
                        20.0,
                        21.0,
                        22.0,
                        np.nan,
                        np.nan,
                        np.nan,
                    ],
                    [
                        16.0,
                        17.0,
                        18.0,
                        21.0,
                        22.0,
                        23.0,
                        np.nan,
                        np.nan,
                        np.nan,
                    ],
                    [
                        17.0,
                        18.0,
                        19.0,
                        22.0,
                        23.0,
                        24.0,
                        np.nan,
                        np.nan,
                        np.nan,
                    ],
                    [
                        18.0,
                        19.0,
                        np.nan,
                        23.0,
                        24.0,
                        np.nan,
                        np.nan,
                        np.nan,
                        np.nan,
                    ],
                ],
            ]
        )

        np.testing.assert_array_almost_equal(strides, strides_result)

    def test_relief_w_nan(self):
        strides = make_2d_array_strides(self.array, 1)
        relief_result = np.array(
            [
                [np.nan, np.nan, np.nan, np.nan, np.nan],
                [np.nan, 12.0, 12.0, 12.0, np.nan],
                [np.nan, 12.0, 12.0, 12.0, np.nan],
                [np.nan, 12.0, 12.0, 12.0, np.nan],
                [np.nan, np.nan, np.nan, np.nan, np.nan],
            ]
        )

        np.testing.assert_array_almost_equal(relief_result, relief(strides))

    def test_relief_wo_nan(self):
        strides = make_2d_array_strides(self.array, 1)
        strides = np.ma.masked_array(strides, mask=np.isnan(strides))

        relief_result = np.array(
            [
                [6.0, 7.0, 7.0, 7.0, 6.0],
                [11.0, 12.0, 12.0, 12.0, 11.0],
                [11.0, 12.0, 12.0, 12.0, 11.0],
                [11.0, 12.0, 12.0, 12.0, 11.0],
                [6.0, 7.0, 7.0, 7.0, 6.0],
            ]
        )

        np.testing.assert_array_almost_equal(relief_result, relief(strides))

    def test_rolling_array_operation(self):
        relief_result = np.array(
            [
                [6.0, 7.0, 7.0, 7.0, 6.0],
                [11.0, 12.0, 12.0, 12.0, 11.0],
                [11.0, 12.0, 12.0, 12.0, 11.0],
                [11.0, 12.0, 12.0, 12.0, 11.0],
                [6.0, 7.0, 7.0, 7.0, 6.0],
            ]
        )

        relief_res = rolling_array_operation(
            self.array, relief, window_size=3, trim=False
        )

        np.testing.assert_array_almost_equal(relief_res, relief_result)


@unittest.skipIf(gdal is None, "GDAL not always installed correctly")
class test_make_local_relief_raster(unittest.TestCase):

    def test_make_local_relief_raster_geo_transform(self):
        test_relief_raster = gdal.Open(test_relief)
        outfile_handler, outfile = tempfile.mkstemp()
        lrr = make_local_relief_raster(
            test_dem, 5, outfile=outfile, write=False, trim=False
        )
        np.testing.assert_allclose(
            lrr.GetGeoTransform(),
            test_relief_raster.GetGeoTransform(),
        )
        os.remove(outfile)

    def test_make_2d_local_relief_raster_array_vals(self):
        test_relief_raster = gdal.Open(test_relief)
        outfile_handler, outfile = tempfile.mkstemp()
        lrr = make_local_relief_raster(
            test_dem, 5, outfile=outfile, write=False, trim=False
        )
        np.testing.assert_array_almost_equal(
            lrr.GetRasterBand(1).ReadAsArray(),
            test_relief_raster.GetRasterBand(1).ReadAsArray(),
        )
        os.remove(outfile)
