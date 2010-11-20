# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
Tests of the supported GEM output formats.
Goals of this test suite should be to test valid and invalid input,
validate all capabilities of the formats (e.g., coordinate and projection),
and (eventually) test performance of various serializers.
"""

import os
import numpy
import struct
import subprocess
import unittest

from osgeo import gdal, gdalconst

from opengem import shapes
from opengem import test
from opengem.output import geotiff

# make test region that has 5 cells in N-S direction ("rows"),
# and 10 cells in W-E direction ("columns")
# start at lon/lat 0.0, default grid spacing is 0.1 degrees
# order of region envelope vertices is:
# lower-left, lower_right, upper-right, upper-left
# this is made from a shapely polygon, which has (lon, lat) vertices
TEST_REGION_SMALL = [(0.0, 0.0), (1.0, 0.0), (1.0, 0.5), (0.0, 0.5)]
TEST_REGION_SQUARE = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
TEST_REGION_LARGE_ASYMMETRIC = [(0.0, 0.0), (10.0, 0.0), (10.0, 5.0), (0.0, 5.0)]

GEOTIFF_FILENAME_WITHOUT_NUMBER = "test.smallregion.tiff"
GEOTIFF_FILENAME_WITH_NUMBER = "test.smallregion.1.tiff"
GEOTIFF_FILENAME_SQUARE_REGION = "test.squareregion.tiff"
GEOTIFF_FILENAME_LARGE_ASYMMETRIC_REGION = "test.asymmetric.region.tiff"

GEOTIFF_USED_CHANNEL_IDX = 1
GEOTIFF_TEST_PIXEL_VALUE = 1.0

class OutputTestCase(unittest.TestCase):
    """Test all our output file formats, generally against sample content"""

    def test_geotiff_generation_and_metadata_validation(self):
        path = os.path.join(test.DATA_DIR, GEOTIFF_FILENAME_WITHOUT_NUMBER)
        smallregion = shapes.Region.from_coordinates(TEST_REGION_SMALL)
        gwriter = geotiff.GeoTiffFile(path, smallregion.grid)
        gwriter.close()

        self._assert_geotiff_metadata_is_correct(path, smallregion)
    
    def test_geotiff_generation_with_number_in_filename(self):
        path = os.path.join(test.DATA_DIR, GEOTIFF_FILENAME_WITH_NUMBER)
        smallregion = shapes.Region.from_coordinates(TEST_REGION_SMALL)
        gwriter = geotiff.GeoTiffFile(path, smallregion.grid)
        gwriter.close()

        self._assert_geotiff_metadata_is_correct(path, smallregion)

    def test_geotiff_generation_initialize_raster(self):
        path = os.path.join(test.DATA_DIR, GEOTIFF_FILENAME_WITH_NUMBER)
        smallregion = shapes.Region.from_coordinates(TEST_REGION_SMALL)
        gwriter = geotiff.GeoTiffFile(path, smallregion.grid, GEOTIFF_TEST_PIXEL_VALUE)
        gwriter.close()

        self._assert_geotiff_metadata_is_correct(path, smallregion)

        # assert that all raster pixels have the desired value
        self._assert_geotiff_band_min_max_values(path,
            GEOTIFF_USED_CHANNEL_IDX, 
            GEOTIFF_TEST_PIXEL_VALUE, 
            GEOTIFF_TEST_PIXEL_VALUE)

    def test_geotiff_generation_and_simple_raster_validation(self):
        path = os.path.join(test.DATA_DIR, GEOTIFF_FILENAME_SQUARE_REGION)
        squareregion = shapes.Region.from_coordinates(TEST_REGION_SQUARE)
        gwriter = geotiff.GeoTiffFile(path, squareregion.grid)
        
        reference_raster = numpy.zeros((squareregion.grid.rows, 
                                        squareregion.grid.columns), 
                                       dtype=numpy.float)
        self._fill_rasters(squareregion, gwriter, reference_raster, self._trivial_fill)
        gwriter.close()

        self._assert_geotiff_metadata_and_raster_is_correct(path, 
            squareregion, GEOTIFF_USED_CHANNEL_IDX, reference_raster)

    def test_geotiff_generation_asymmetric_pattern(self):
        path = os.path.join(test.DATA_DIR, 
                            GEOTIFF_FILENAME_LARGE_ASYMMETRIC_REGION)
        asymmetric_region = shapes.Region.from_coordinates(
            TEST_REGION_LARGE_ASYMMETRIC)
        gwriter = geotiff.GeoTiffFile(path, asymmetric_region.grid)

        reference_raster = numpy.zeros((asymmetric_region.grid.rows, 
                                        asymmetric_region.grid.columns),
                                       dtype=numpy.float)
        self._fill_rasters(asymmetric_region, gwriter, reference_raster, self._trivial_fill)
        gwriter.close()

        self._assert_geotiff_metadata_and_raster_is_correct(path, 
            asymmetric_region, GEOTIFF_USED_CHANNEL_IDX, reference_raster)

    @test.skipit
    def test_geotiff_output(self): 
        """Generate a geotiff file with a smiley face."""
        path = os.path.join(test.DATA_DIR, "test.1.tiff")
        switzerland = shapes.Region.from_coordinates(
            [(10.0, 100.0), (100.0, 100.0), (100.0, 10.0), (10.0, 10.0)])
        image_grid = switzerland.grid
        gwriter = geotiff.GeoTiffFile(path, image_grid)
        for xpoint in range(0, 320):
            for ypoint in range(0, 320):
                gwriter.write((xpoint, ypoint), int(xpoint*254/320))
        gwriter.close()

        comp_path = os.path.join(test.DATA_DIR, "test.tiff")
        retval = subprocess.call(["tiffcmp", "-t", path, comp_path], 
            stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
        self.assertTrue(retval == 0)
        # TODO(jmc): Figure out how to validate the geo coordinates as well
        # TODO(jmc): Use validation that supports tiled geotiffs

    def _assert_geotiff_metadata_is_correct(self, path, region):

        # open GeoTIFF file and assert that metadata is correct
        dataset = gdal.Open(path, gdalconst.GA_ReadOnly)
        self.assertEqual(dataset.RasterXSize, region.grid.columns)
        self.assertEqual(dataset.RasterYSize, region.grid.rows)
        self.assertEqual(dataset.RasterCount, GEOTIFF_USED_CHANNEL_IDX)

        (origin_lon, lon_pixel_size, lon_rotation, origin_lat, lat_rotation, 
            lat_pixel_size ) = dataset.GetGeoTransform()

        self.assertAlmostEqual(origin_lon, 
            region.grid.region.upper_left_corner.longitude)
        self.assertAlmostEqual(origin_lat, 
            region.grid.region.upper_left_corner.latitude)
        self.assertAlmostEqual(lon_pixel_size, region.grid.cell_size)
        self.assertAlmostEqual(lat_pixel_size, -region.grid.cell_size)

    def _assert_geotiff_band_min_max_values(self, path, band_index, 
        min_value, max_value):

        # open GeoTIFF file and assert that min and max values 
        # of a band are correct
        dataset = gdal.Open(path, gdalconst.GA_ReadOnly)
        band = dataset.GetRasterBand(band_index)
        (band_min, band_max) = band.ComputeRasterMinMax(band_index)

        self.assertAlmostEqual(band_min, min_value)
        self.assertAlmostEqual(band_max, max_value)

    def _assert_geotiff_raster_is_correct(self, path, band_index, raster):

        # open GeoTIFF file and assert that the image raster is correct
        dataset = gdal.Open(path, gdalconst.GA_ReadOnly)
        band = dataset.GetRasterBand(band_index)

        band_raster = numpy.zeros((band.YSize, band.XSize), dtype=numpy.float)
        for row_idx in xrange(band.YSize):

            scanline = band.ReadRaster(0, row_idx, band.XSize, 1, 
                band.XSize, 1, geotiff.GDAL_PIXEL_DATA_TYPE)

            tuple_of_floats = struct.unpack('f' * band.XSize, scanline)
            band_raster[row_idx,:] = tuple_of_floats

        self.assertTrue(numpy.allclose(band_raster, raster))

    def _assert_geotiff_metadata_and_raster_is_correct(self, path, region, 
                                                       band_index, raster):
        self._assert_geotiff_metadata_is_correct(path, region)
        self._assert_geotiff_raster_is_correct(path, GEOTIFF_USED_CHANNEL_IDX,
            raster)

    def _fill_rasters(self, region, writer, reference_raster, fill_function):
        for row_idx in xrange(region.grid.rows):
            for col_idx in xrange(region.grid.columns):
                writer.write((row_idx, col_idx), 
                    float((row_idx + 1) * (col_idx + 1)))
                reference_raster[row_idx, col_idx] = fill_function(row_idx, 
                                                                   col_idx)

    def _trivial_fill(self, row_idx, col_idx):
        return float((row_idx + 1) * (col_idx + 1))
