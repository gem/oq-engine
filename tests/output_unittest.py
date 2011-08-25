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


"""
Tests of the supported GEM output formats.
Goals of this test suite should be to test valid and invalid input,
validate all capabilities of the formats (e.g., coordinate and projection),
and (eventually) test performance of various serializers.
"""

import os
import copy
import numpy
import struct
import unittest

from osgeo import gdal, gdalconst

from openquake import writer
from openquake import shapes
from tests.utils import helpers
from openquake.output import geotiff, curve, cpt

# we define some test regions which have a lower-left corner at 0.0/0.0
# the default grid spacing of 0.1 degrees is used
# order of region envelope vertices is:
# (lower-left, lower-right, upper-right, upper-left)
# this is made from a shapely polygon, which has (lon, lat) vertices
# N-S direction is rows, W-E direction is columns of the underlying
# numpy array

# 11x6 px (numpy array: 6x11) test region
TEST_REGION_SMALL = [(0.0, 0.0), (1.0, 0.0), (1.0, 0.5), (0.0, 0.5)]

# 11x11 px test region
TEST_REGION_SQUARE = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]

# 101x51 px (numpy array: 51x101) test region
TEST_REGION_LARGE_ASYMMETRIC = [(0.0, 0.0), (10.0, 0.0), (10.0, 5.0),
                                (0.0, 5.0)]

GEOTIFF_FILENAME_WITHOUT_NUMBER = "test.smallregion.tiff"
GEOTIFF_FILENAME_WITH_NUMBER = "test.smallregion.1.tiff"
GEOTIFF_FILENAME_SQUARE_REGION = "test.squareregion.tiff"
GEOTIFF_FILENAME_LARGE_ASYMMETRIC_REGION = "test.asymmetric.region.tiff"
GEOTIFF_FILENAME_COLORSCALE = "test.colorscale.tiff"
GEOTIFF_FILENAME_COLORSCALE_CUTS = "test.colorscale-cuts.tiff"
GEOTIFF_LOSS_RATIO_MAP_COLORSCALE = "test.loss_ratio_map.tiff"
GEOTIFF_FILENAME_EXPLICIT_COLORSCALE_BINS = "test.colorscale-bins.tiff"
GEOTIFF_FILENAME_NONDEFAULT_COLORSCALE = "test.colorscale-nondefault.tiff"
GEOTIFF_FILENAME_MULTISEGMENT_COLORSCALE = "test.colorscale-multisegment.tiff"
GEOTIFF_FILENAME_DISCRETE_COLORSCALE = "test.colorscale-discrete.tiff"
GEOTIFF_FILENAME_DISCRETE_CUSTOMBIN_COLORSCALE = \
    "test.colorscale-discrete-custombins.tiff"

HAZARDCURVE_PLOT_SIMPLE_FILENAME = "hazard-curves-simple.svg"

HAZARDCURVE_PLOT_FILENAME = "hazard-curves.svg"
HAZARDCURVE_PLOT_INPUTFILE = "example-hazard-curves-for-plotting.xml"

LOSS_CURVE_PLOT_FILENAME = "loss-curves.svg"
LOSS_CURVE_PLOT_INPUTFILE = "example-loss-curves-for-plotting.xml"

LOSS_RATIO_CURVE_PLOT_FILENAME = "loss-ratio-curves.svg"
LOSS_RATIO_CURVE_PLOT_INPUTFILE = "example-loss-ratio-curves-for-plotting.xml"

GEOTIFF_USED_CHANNEL_IDX = 1
GEOTIFF_TOTAL_CHANNELS = 4
GEOTIFF_TEST_PIXEL_VALUE = 1.0

TEST_COLORMAP = {
    'id': 'seminf-haxby.cpt,v 1.1 2004/02/25 18:15:50 jjg Exp',
    'name': 'seminf-haxby',
    'type': 'discrete',
    'model': 'RGB',
    # z_values = [0.0, 1.25, ... , 28.75, 30.0]
    'z_values': [1.25 * x for x in range(25)],
    'red': [255, 208, 186, 143, 97, 0, 25, 12, 24, 49, 67, 96,
            105, 123, 138, 172, 205, 223, 240, 247, 255,
            255, 244, 238],
    'green': [255, 216, 197, 161, 122, 39, 101, 129, 175, 190,
              202, 225, 235, 235, 236, 245, 255, 245, 236,
              215, 189, 160, 116, 79],
    'blue': [255, 251, 247, 241, 236, 224, 240, 248, 255, 255,
             255, 240, 225, 200, 174, 168, 162, 141, 120,
             103, 86, 68, 74, 77],
    'background': [255, 255, 255],
    'foreground': [238, 79, 77],
    'NaN': [0, 0, 0]}

TEST_CONTINUOUS_COLORMAP = {
    'id': 'green-red',
    'name': 'green-red',
    'type': 'continuous',
    'model': 'RGB',
    'z_values': [0.0, 1.0],
    'red': [0, 255],
    'green': [255, 0],
    'blue': [0, 0],
    'background': None,
    'foreground': None,
    'NaN': None}

TEST_IML_LIST = [
    0.005, 0.007, 0.0098, 0.0137, 0.0192, 0.0269, 0.0376,
    0.0527, 0.0738, 0.103, 0.145, 0.203, 0.284, 0.397,
    0.556, 0.778, 1.09, 1.52, 2.13]


class OutputTestCase(unittest.TestCase):
    """Test all our output file formats, generally against sample content"""

    def test_geotiff_generation_discrete_colorscale_custom_bins(self):
        """Check RGB geotiff generation with colorscale for GMF. Use
        discrete colorscale based on IML values, with custom IML."""
        path = helpers.get_output_path(
            GEOTIFF_FILENAME_DISCRETE_CUSTOMBIN_COLORSCALE)
        asymmetric_region = shapes.Region.from_coordinates(
            TEST_REGION_LARGE_ASYMMETRIC)

        iml_list = TEST_IML_LIST

        gwriter = geotiff.GMFGeoTiffFile(
            path, asymmetric_region.grid, iml_list=iml_list, discrete=True,
            colormap=geotiff.COLORMAPS['matlab-polar'])

        reference_raster = numpy.zeros((asymmetric_region.grid.rows,
                                        asymmetric_region.grid.columns),
                                       dtype=numpy.float)
        self._fill_rasters(asymmetric_region, gwriter, reference_raster,
            self._colorscale_cuts_fill)
        gwriter.close()

    def test_geotiff_generation_discrete_colorscale(self):
        """Check RGB geotiff generation with colorscale for GMF. Use
        discrete colorscale based on IML values, with default IML."""
        path = helpers.get_output_path(GEOTIFF_FILENAME_DISCRETE_COLORSCALE)
        asymmetric_region = shapes.Region.from_coordinates(
            TEST_REGION_LARGE_ASYMMETRIC)

        gwriter = geotiff.GMFGeoTiffFile(
            path, asymmetric_region.grid, iml_list=None, discrete=True,
            colormap=geotiff.COLORMAPS['gmt-seis'])

        reference_raster = numpy.zeros((asymmetric_region.grid.rows,
                                        asymmetric_region.grid.columns),
                                       dtype=numpy.float)
        self._fill_rasters(asymmetric_region, gwriter, reference_raster,
            self._colorscale_cuts_fill)
        gwriter.close()

    def test_geotiff_generation_multisegment_colorscale(self):
        """Check RGB geotiff generation with colorscale for GMF. Use
        multisegment colorscale."""
        path = helpers.get_output_path(
            GEOTIFF_FILENAME_MULTISEGMENT_COLORSCALE)
        asymmetric_region = shapes.Region.from_coordinates(
            TEST_REGION_LARGE_ASYMMETRIC)

        gwriter = geotiff.GMFGeoTiffFile(
            path, asymmetric_region.grid, iml_list=None, discrete=False,
            colormap=geotiff.COLORMAPS['gmt-seis'])

        reference_raster = numpy.zeros((asymmetric_region.grid.rows,
                                        asymmetric_region.grid.columns),
                                       dtype=numpy.float)
        self._fill_rasters(asymmetric_region, gwriter, reference_raster,
            self._colorscale_cuts_fill)
        gwriter.close()

    def test_geotiff_generation_nondefault_colorscale(self):
        """Check RGB geotiff generation with colorscale for GMF. Use
        alternative colorscale."""
        path = helpers.get_output_path(GEOTIFF_FILENAME_NONDEFAULT_COLORSCALE)
        asymmetric_region = shapes.Region.from_coordinates(
            TEST_REGION_LARGE_ASYMMETRIC)

        gwriter = geotiff.GMFGeoTiffFile(
            path, asymmetric_region.grid, iml_list=None, discrete=False,
            colormap=geotiff.COLORMAPS['gmt-green-red'])

        reference_raster = numpy.zeros((asymmetric_region.grid.rows,
                                        asymmetric_region.grid.columns),
                                       dtype=numpy.float)
        self._fill_rasters(asymmetric_region, gwriter, reference_raster,
            self._colorscale_cuts_fill)
        gwriter.close()

    def test_geotiff_generation_explicit_colorscale_bins(self):
        """Check RGB geotiff generation with colorscale for GMF. Limits
        and bins of colorscale are explicitly given."""
        path = helpers.get_output_path(
            GEOTIFF_FILENAME_EXPLICIT_COLORSCALE_BINS)
        asymmetric_region = shapes.Region.from_coordinates(
            TEST_REGION_LARGE_ASYMMETRIC)

        for test_number, test_list in enumerate(([0.9, 0.95, 1.0, 1.05],
                                                 None)):

            curr_path = "%s.%s.tiff" % (path[0:-5], test_number)
            gwriter = geotiff.GMFGeoTiffFile(curr_path,
                asymmetric_region.grid, iml_list=test_list, discrete=False)

            reference_raster = numpy.zeros((asymmetric_region.grid.rows,
                                            asymmetric_region.grid.columns),
                                           dtype=numpy.float)
            self._fill_rasters(asymmetric_region, gwriter, reference_raster,
                self._colorscale_cuts_fill)
            gwriter.close()

    def test_geotiff_generation_colorscale_cuts(self):
        """Check RGB geotiff generation with colorscale for GMF."""
        path = helpers.get_output_path(GEOTIFF_FILENAME_COLORSCALE_CUTS)
        asymmetric_region = shapes.Region.from_coordinates(
            TEST_REGION_LARGE_ASYMMETRIC)
        gwriter = geotiff.GMFGeoTiffFile(path, asymmetric_region.grid,
            discrete=False)

        reference_raster = numpy.zeros((asymmetric_region.grid.rows,
                                        asymmetric_region.grid.columns),
                                        dtype=numpy.float)
        self._fill_rasters(asymmetric_region, gwriter, reference_raster,
            self._colorscale_cuts_fill)
        gwriter.close()

    def test_geotiff_generation_colorscale(self):
        """Check RGB geotiff generation with colorscale for GMF."""
        path = helpers.get_output_path(GEOTIFF_FILENAME_COLORSCALE)
        asymmetric_region = shapes.Region.from_coordinates(
            TEST_REGION_LARGE_ASYMMETRIC)
        gwriter = geotiff.GMFGeoTiffFile(path, asymmetric_region.grid,
            discrete=False)

        reference_raster = numpy.zeros((asymmetric_region.grid.rows,
                                        asymmetric_region.grid.columns),
                                        dtype=numpy.float)
        self._fill_rasters(asymmetric_region, gwriter, reference_raster,
            self._colorscale_fill)
        gwriter.close()

    def test_geotiff_loss_ratio_map_colorscale(self):
        path = helpers.get_output_path(GEOTIFF_LOSS_RATIO_MAP_COLORSCALE)
        asymmetric_region = shapes.Region.from_coordinates(
            TEST_REGION_LARGE_ASYMMETRIC)

        gwriter = geotiff.LossMapGeoTiffFile(
            path, asymmetric_region.grid, pixel_type=gdal.GDT_Byte)
        reference_raster = numpy.zeros((asymmetric_region.grid.rows,
                                        asymmetric_region.grid.columns),
                                        dtype=numpy.float)

        color_fill = lambda x, y:  (x * y) / 50
        self._fill_rasters(asymmetric_region, gwriter, reference_raster,
            color_fill)
        gwriter.close()

        self._assert_geotiff_metadata_is_correct(path, asymmetric_region)
        self._assert_geotiff_band_min_max_values(path,
            GEOTIFF_USED_CHANNEL_IDX, 0, 240)

    def test_loss_ratio_curve_plot_generation_multiple_sites(self):
        """Create SVG plots for loss ratio curves read from an NRML file. The
        file contains data for several sites.
        For each site, a separate SVG file is created."""

        path = helpers.get_output_path(LOSS_RATIO_CURVE_PLOT_FILENAME)
        loss_ratio_curve_path = helpers.get_data_path(
            LOSS_RATIO_CURVE_PLOT_INPUTFILE)

        plotter = curve.RiskCurvePlotter(path, loss_ratio_curve_path,
            mode='loss_ratio')

        # delete expected output files, if existing
        for svg_file in plotter.filenames():
            if os.path.isfile(svg_file):
                os.remove(svg_file)

        plotter.plot(autoscale_y=False)

        # assert that for each site in the NRML file an SVG has been created
        for svg_file in plotter.filenames():
            self.assertTrue(os.path.getsize(svg_file) > 0)

    def test_loss_curve_plot_generation_multiple_sites(self):
        """Create SVG plots for loss curves read from an NRML file. The
        file contains data for several sites.
        For each site, a separate SVG file is created."""

        path = helpers.get_output_path(LOSS_CURVE_PLOT_FILENAME)
        loss_curve_path = helpers.get_data_path(LOSS_CURVE_PLOT_INPUTFILE)

        plotter = curve.RiskCurvePlotter(path, loss_curve_path, mode='loss',
            curve_title="This is a test loss curve")

        # delete expected output files, if existing
        for svg_file in plotter.filenames():
            if os.path.isfile(svg_file):
                os.remove(svg_file)

        plotter.plot(autoscale_y=True)

        # assert that for each site in the NRML file an SVG has been created
        for svg_file in plotter.filenames():
            self.assertTrue(os.path.getsize(svg_file) > 0)

    def test_loss_curve_plot_generation_multiple_sites_render_multi(self):
        """Create SVG plots for loss curves read from an NRML file. The
        file contains data for several sites.
        For each site, a separate SVG file is created."""

        path = helpers.get_output_path(LOSS_CURVE_PLOT_FILENAME)
        loss_curve_path = helpers.get_data_path(LOSS_CURVE_PLOT_INPUTFILE)

        plotter = curve.RiskCurvePlotter(path, loss_curve_path, mode='loss',
            curve_title="This is a test loss curve", render_multi=True)

        # delete expected output files, if existing
        for svg_file in plotter.filenames():
            if os.path.isfile(svg_file):
                os.remove(svg_file)

        plotter.plot(autoscale_y=True)

        for svg_file in plotter.filenames():
            self.assertTrue(os.path.getsize(svg_file) > 0)

    def test_simple_curve_plot_generation(self):
        """Create an SVG plot of a single (hazard) curve for a single site
        from a dictionary."""

        test_site = shapes.Site(-122, 38)
        test_end_branch = '1_1'
        test_hc_data = {test_end_branch:
                {'abscissa': [0.0, 1.0, 1.8],
                 'ordinate': [1.0, 0.5, 0.2],
                 'abscissa_property': 'PGA',
                 'ordinate_property': 'Probability of Exceedance',
                 'curve_title': 'Hazard Curve',
                 'Site': test_site}}

        path = helpers.get_output_path(HAZARDCURVE_PLOT_SIMPLE_FILENAME)
        plot = curve.CurvePlot(path)
        plot.write(test_hc_data)
        plot.close()

        # assert that file has been created and is not empty
        self.assertTrue(os.path.getsize(path) > 0)
        os.remove(path)

    def test_hazardcurve_plot_generation_multiple_sites_multiple_curves(self):
        """Create SVG plots for hazard curves read from an NRML file. The
        file contains data for several sites, and several end branches of
        the logic tree. For each site, a separate SVG file is created."""

        path = helpers.get_output_path(HAZARDCURVE_PLOT_FILENAME)
        hazardcurve_path = helpers.get_data_path(HAZARDCURVE_PLOT_INPUTFILE)

        plotter = curve.HazardCurvePlotter(path, hazardcurve_path,
            curve_title='Example Hazard Curves')

        # delete expected output files, if existing
        for svg_file in plotter.filenames():
            if os.path.isfile(svg_file):
                os.remove(svg_file)

        plotter.plot()

        # assert that for each site in the NRML file an SVG has been created
        # and is not empty
        for svg_file in plotter.filenames():
            self.assertTrue(os.path.getsize(svg_file) > 0)
            os.remove(svg_file)

    def test_geotiff_generation_and_metadata_validation(self):
        """Create a GeoTIFF, and check if it has the
        correct metadata."""
        path = helpers.get_output_path(GEOTIFF_FILENAME_WITHOUT_NUMBER)
        smallregion = shapes.Region.from_coordinates(TEST_REGION_SMALL)
        gwriter = geotiff.LossMapGeoTiffFile(
            path, smallregion.grid, normalize=False)
        gwriter.close()

        self._assert_geotiff_metadata_is_correct(path, smallregion)

    def test_lossmap_geotiff_generation_with_number_in_filename(self):
        """Create a GeoTIFF with a number in its filename. This
        test has been written because it has been reported that numbers in the
        filename do not work."""
        path = helpers.get_output_path(GEOTIFF_FILENAME_WITH_NUMBER)
        smallregion = shapes.Region.from_coordinates(TEST_REGION_SMALL)
        gwriter = geotiff.LossMapGeoTiffFile(
            path, smallregion.grid, normalize=False)
        gwriter.close()

        self._assert_geotiff_metadata_is_correct(path, smallregion)

    def test_lossmap_geotiff_generation_initialize_raster(self):
        """Create a GeoTIFF and initialize the raster to a given value. Then
        check through metadata if it has been done correctly. We check the
        minumum and maximum values of the band, which are expected to have
        the value of the raster nodes."""
        path = helpers.get_output_path(GEOTIFF_FILENAME_WITH_NUMBER)
        smallregion = shapes.Region.from_coordinates(TEST_REGION_SMALL)
        gwriter = geotiff.LossMapGeoTiffFile(
            path, smallregion.grid, init_value=GEOTIFF_TEST_PIXEL_VALUE,
            pixel_type=gdal.GDT_Byte, normalize=False)
        gwriter.close()

        self._assert_geotiff_metadata_is_correct(path, smallregion)

        # assert that all raster pixels have the desired value
        self._assert_geotiff_band_min_max_values(path,
            GEOTIFF_USED_CHANNEL_IDX,
            GEOTIFF_TEST_PIXEL_VALUE,
            GEOTIFF_TEST_PIXEL_VALUE)

    def test_geotiff_generation_and_simple_raster_validation(self):
        """Create a GeoTIFF and assign values to the raster nodes according
        to a simple function. Then check if the raster values have been set
        correctly."""
        path = helpers.get_output_path(GEOTIFF_FILENAME_SQUARE_REGION)
        squareregion = shapes.Region.from_coordinates(TEST_REGION_SQUARE)
        gwriter = geotiff.LossMapGeoTiffFile(
            path, squareregion.grid, normalize=False)

        reference_raster = numpy.zeros((squareregion.grid.rows,
                                        squareregion.grid.columns),
                                        dtype=numpy.float)
        self._fill_rasters(squareregion, gwriter, reference_raster,
            self._trivial_fill)
        gwriter.close()

        self._assert_geotiff_metadata_and_raster_is_correct(path,
            squareregion, GEOTIFF_USED_CHANNEL_IDX, reference_raster)

    def test_geotiff_generation_asymmetric_pattern(self):
        """Create a GeoTIFF and assign values to the raster nodes according
        to a simple function. Use a somewhat larger, non-square region for
        that. Then check if the raster values have been set correctly."""
        path = helpers.get_output_path(
            GEOTIFF_FILENAME_LARGE_ASYMMETRIC_REGION)
        asymmetric_region = shapes.Region.from_coordinates(
            TEST_REGION_LARGE_ASYMMETRIC)
        gwriter = geotiff.LossMapGeoTiffFile(
            path, asymmetric_region.grid, pixel_type=gdal.GDT_Float32,
            normalize=False)

        reference_raster = numpy.zeros((asymmetric_region.grid.rows,
                                        asymmetric_region.grid.columns),
                                       dtype=numpy.float)
        self._fill_rasters(asymmetric_region, gwriter, reference_raster,
            self._trivial_fill)
        gwriter.close()

        self._assert_geotiff_metadata_and_raster_is_correct(path,
            asymmetric_region, GEOTIFF_USED_CHANNEL_IDX, reference_raster)

    def _assert_geotiff_metadata_is_correct(self, path, region):
        """
        Verifies:
            * number of rows/cols (1px per cell)
            * lon/lat
            * geo transform data

        :param path: path to a pre-existing geotiff file

        :param region: region definition
        :type region: shapes.Region object
        """
        # open GeoTIFF file and assert that metadata is correct
        dataset = gdal.Open(path, gdalconst.GA_ReadOnly)
        self.assertEqual(dataset.RasterXSize, region.grid.columns)
        self.assertEqual(dataset.RasterYSize, region.grid.rows)
        self.assertEqual(dataset.RasterCount, GEOTIFF_TOTAL_CHANNELS)

        (origin_lon, lon_pixel_size, lon_rotation, origin_lat, lat_rotation,
            lat_pixel_size) = dataset.GetGeoTransform()

        self.assertAlmostEqual(origin_lon,
            region.upper_left_corner.longitude)
        self.assertAlmostEqual(origin_lat,
            region.upper_left_corner.latitude)
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
            band_raster[row_idx, :] = tuple_of_floats  # couldn't find a way to
                                                       # comply with pep8

        self.assertTrue(numpy.allclose(band_raster, raster))

    def _assert_geotiff_metadata_and_raster_is_correct(self, path, region,
                                                       band_index, raster):
        self._assert_geotiff_metadata_is_correct(path, region)
        self._assert_geotiff_raster_is_correct(path, GEOTIFF_USED_CHANNEL_IDX,
            raster)

    def _fill_rasters(self, region, writer, reference_raster, fill_function):
        for row_idx in xrange(region.grid.rows):
            for col_idx in xrange(region.grid.columns):
                writer.write((row_idx, col_idx), fill_function(row_idx,
                                                               col_idx))
                reference_raster[row_idx, col_idx] = fill_function(row_idx,
                                                                   col_idx)

    def _trivial_fill(self, row_idx, col_idx):
        return float((row_idx + 1) * (col_idx + 1))

    def _colorscale_fill(self, row_idx, col_idx):
        """if used with asymmetic large region, return value range 0..2"""
        return row_idx * col_idx / (5.0 * 10.0 * 100.0)

    def _colorscale_cuts_fill(self, row_idx, col_idx):
        """if used with asymmetic large region, return value
        range -1..4"""
        return (row_idx * col_idx / (10.0 * 100.0)) - 1.0

    def test_color_map_from_cpt_good_discrete(self):
        """
        Tests the CPTReader class by reading a known-good cpt file
        containing a discrete color scale.
        """
        test_file = 'seminf-haxby.cpt'
        test_path = os.path.join(helpers.DATA_DIR, test_file)

        reader = cpt.CPTReader(test_path)
        expected_map = TEST_COLORMAP

        actual_map = reader.get_colormap()
        self.assertEqual(expected_map, actual_map)

    def test_hazard_map_geotiff_constructor_raises(self):
        """
        Test the parameter validation of the HazardMapGeoTiffFile constructor.
        """

        test_file_path = 'test.tiff'  # this test won't actually write anything
        test_region = shapes.Region.from_coordinates(TEST_REGION_SMALL)

        bad_test_data = (
            ('foo', 'bar'),
            ('foo', 17),
            (17, 'foo'),
            (-1.0, 5.5),
            (-2, -0.5),
            (2.13, 0.005))
        for bad in bad_test_data:
            self.assertRaises(
                (ValueError, AssertionError), geotiff.HazardMapGeoTiffFile,
                test_file_path, test_region.grid, TEST_COLORMAP,
                iml_min_max=bad)

    def test_hazard_map_geotiff_scaling(self):
        """
        Scaling type for a HazardMapGeoTiffFile is 'fixed' if iml_min_max is
        defined, else 'relative.

        This test ensures the scaling type is set properly.
        """

    def test_rgb_values_from_colormap(self):
        # get colors for 8 points
        indices = [0, 23, 3, 2, 17, 1, 19, 22]
        red_expected = numpy.array([255, 238, 143, 186, 223, 208, 247, 244])
        green_expected = numpy.array([255, 79, 161, 197, 245, 216, 215, 116])
        blue_expected = numpy.array([255, 77, 241, 247, 141, 251, 103, 74])

        red, green, blue = geotiff.rgb_values_from_colormap(
            TEST_COLORMAP, indices)

        for expected, actual in (
            (red_expected, red),
            (green_expected, green),
            (blue_expected, blue)):
            # values here are numpy.array objects
            self.assertTrue((expected == actual).all())

    def test_rgb_values_from_bad_colormap(self):
        colormap = copy.deepcopy(TEST_COLORMAP)
        indices = []  # these don't matter in this test
        # the lists of r, g, and b values should all be the same length
        # let's create a failure:
        colormap['green'].pop()
        self.assertRaises(
                AssertionError, geotiff.rgb_values_from_colormap, colormap,
                indices)

    def test_rgb_from_raster(self):
        # 3x3 image example
        raster = numpy.array(
            [[0.0, -0.01, 0.1],
             [30.0, 28.75, 30.1],
             [10.0, 10.333, 11.249]])
        expected_red = numpy.array(
            [[255, 255, 255],
             [238, 238, 238],
             [24, 24, 24]])
        expected_green = numpy.array(
            [[255, 255, 255],
             [79, 79, 79],
             [175, 175, 175]])
        expected_blue = numpy.array(
            [[255, 255, 255],
             [77, 77, 77],
             [255, 255, 255]])

        actual_red, actual_green, actual_blue = \
            geotiff.rgb_from_raster(TEST_COLORMAP, raster)

        for expected, actual in (
            (expected_red, actual_red),
            (expected_green, actual_green),
            (expected_blue, actual_blue)):
            # numpy array objects
            print "expected %s" % expected
            print "actual %s" % actual
            self.assertTrue((expected == actual).all())

    def test_condense_to_unity(self):
        test_input = numpy.array([0.005, 0.007, 0.0098])
        expected_output = numpy.array([0.0, 0.416666666667, 1.0])

        actual_output = geotiff.condense_to_unity(test_input)

        self._assert_numpy_arrays_almost_equal(expected_output, actual_output)

    def test_condense_to_unity_with_min_max(self):
        test_input = numpy.array([0.4, 0.7, 1.3, 2.2, 4.1])
        expected_output = numpy.array([0.0, 0.0, 0.15625, 0.4375, 1.0])
        fixed_min_max = (0.8, 4.0)

        actual_output = geotiff.condense_to_unity(
            test_input, min_max=fixed_min_max)

        self._assert_numpy_arrays_almost_equal(expected_output, actual_output)

    def test_condense_to_unity_2d(self):
        test_input = numpy.array([[0.005, 0.007], [0.0098, 0.005]])
        expected_output = numpy.array([[0.0, 0.416666666667], [1.0, 0.0]])

        actual_output = geotiff.condense_to_unity(test_input)

        self._assert_numpy_arrays_almost_equal(expected_output, actual_output)

    def test_condense_to_unity_no_change(self):
        test_input = numpy.array([0.0, 0.25, 0.5, 0.75, 1.0])
        # input should be the same as output

        actual_output = geotiff.condense_to_unity(test_input)

        self._assert_numpy_arrays_almost_equal(test_input, actual_output)

    def _assert_numpy_arrays_almost_equal(self, expected, actual, precision=6):
        """
        Compares 1- or 2-dimensional numpy.arrays of floats for equality,
        up to 6 digits of precision (by default).
        """
        self.assertEqual(len(expected), len(actual))
        self.assertEqual(len(expected.flatten()), len(actual.flatten()))
        for i, exp in enumerate(expected):
            if type(exp) is numpy.ndarray:
                # handle 2-d arrays
                for j, exp2 in enumerate(exp):
                    print "i, j: %s, %s" % (i, j)
                    self.assertAlmostEqual(exp2, actual[i][j], precision)
            else:
                self.assertAlmostEqual(exp, actual[i], precision)

    def test_interpolate_color(self):
        iml_fractions = numpy.array(
            [[0.0, 0.22988505747126439], [0.55172413793103448, 1.0]])
        colormap = TEST_CONTINUOUS_COLORMAP

        expected_red = numpy.array([[0.0, 58.62068966], [140.68965517, 255.0]])
        expected_green = \
            numpy.array([[255.0, 196.37931034], [114.31034483, 0.0]])
        expected_blue = numpy.array([[0.0, 0.0], [0.0, 0.0]])

        actual_red = geotiff.interpolate_color(iml_fractions, colormap, 'red')
        actual_green = \
            geotiff.interpolate_color(iml_fractions, colormap, 'green')
        actual_blue = \
            geotiff.interpolate_color(iml_fractions, colormap, 'blue')

        self._assert_numpy_arrays_almost_equal(expected_red, actual_red)
        self._assert_numpy_arrays_almost_equal(expected_green, actual_green)
        self._assert_numpy_arrays_almost_equal(expected_blue, actual_blue)

    def test_rgb_for_continuous(self):
        iml_fractions = numpy.array(
            [[0.0, 0.22988505747126439], [0.55172413793103448, 1.0]])
        colormap = TEST_CONTINUOUS_COLORMAP

        expected_red = numpy.array([[0.0, 58.62068966], [140.68965517, 255.0]])
        expected_green = \
            numpy.array([[255.0, 196.37931034], [114.31034483, 0.0]])
        expected_blue = numpy.array([[0.0, 0.0], [0.0, 0.0]])

        actual_red, actual_green, actual_blue = \
            geotiff.rgb_for_continuous(iml_fractions, colormap)

        self._assert_numpy_arrays_almost_equal(expected_red, actual_red)
        self._assert_numpy_arrays_almost_equal(expected_green, actual_green)
        self._assert_numpy_arrays_almost_equal(expected_blue, actual_blue)

    def test_discrete_colorscale(self):

        min = 0.8
        max = 0.4
        expected_output = [
            ('#ffffff', '0.80 - 0.93'), ('#d0d8fb', '0.93 - 1.07'),
            ('#bac5f7', '1.07 - 1.20'), ('#8fa1f1', '1.20 - 1.33'),
            ('#617aec', '1.33 - 1.47'), ('#0027e0', '1.47 - 1.60'),
            ('#1965f0', '1.60 - 1.73'), ('#0c81f8', '1.73 - 1.87'),
            ('#18afff', '1.87 - 2.00'), ('#31beff', '2.00 - 2.13'),
            ('#43caff', '2.13 - 2.27'), ('#60e1f0', '2.27 - 2.40'),
            ('#69ebe1', '2.40 - 2.53'), ('#7bebc8', '2.53 - 2.67'),
            ('#8aecae', '2.67 - 2.80'), ('#acf5a8', '2.80 - 2.93'),
            ('#cdffa2', '2.93 - 3.07'), ('#dff58d', '3.07 - 3.20'),
            ('#f0ec78', '3.20 - 3.33'), ('#f7d767', '3.33 - 3.47'),
            ('#ffbd56', '3.47 - 3.60'), ('#ffa044', '3.60 - 3.73'),
            ('#f4744a', '3.73 - 3.87'), ('#ee4f4d', '3.87 - 4.00')]

        colorscale = geotiff.discrete_colorscale(TEST_COLORMAP, 0.8, 4.0)
        self.assertEqual(expected_output, colorscale)

    def test_continuous_colorscale(self):
        iml_list = numpy.array([0.005, 0.007, 0.0098, 0.0137])
        colormap = TEST_CONTINUOUS_COLORMAP
        expected_output = [
            ('#00ff00', '0.005'), ('#3ac400', '0.007'), ('#8c7200', '0.0098'),
            ('#ff0000', '0.0137')]

        actual_output = geotiff.continuous_colorscale(colormap, iml_list)

        self.assertEqual(expected_output, actual_output)

    def _assert_image_rgb_is_correct(
        self, path, expected_red, expected_green, expected_blue):
        """
        :param path: path to an existing geotiff file

        :param expected_red: 2-dimensional numpy.array representing
            the red intensity for each pixel

        :param expected_green: 2-dimensional numpy.array representing
            the green intensity for each pixel

        :param expected_blue: 2-dimensional numpy.array representing
            the blue intensity for each pixel
        """
        # read the image file
        dataset = gdal.Open(path, gdalconst.GA_ReadOnly)
        red_vals = dataset.GetRasterBand(1).ReadAsArray()
        green_vals = dataset.GetRasterBand(2).ReadAsArray()
        blue_vals = dataset.GetRasterBand(3).ReadAsArray()

        self._assert_numpy_arrays_almost_equal(expected_red, red_vals)
        self._assert_numpy_arrays_almost_equal(expected_green, green_vals)
        self._assert_numpy_arrays_almost_equal(expected_blue, blue_vals)

    def test_write_hazard_map_geotiff(self):
        """
        Tests writing hazard maps using two methods:
            * relative scaling
            * fixed scaling

        Relative scaling: Colors are scaled from the lowest IML value
            (min) in the hazard map to the highest IML value (max). This
            is useful for showing higher resolution/detail within a single
            hazard map.

        Fixed scaling: The most common use case. Colors are are applied
            to the map with a specified min and max. This is useful if you
            want to compare two different maps using the same color scale.

        These tests assume that the default color map is used.
        """
        def _test_hazard_map_fixed_scaling(region, hm_data):
            path = helpers.get_output_path(
                'TEST_HAZARD_MAP_fixed_scaling.tiff')

            # expected colors for each pixel in the map:
            exp_red_vals = numpy.array([
                [238, 255, 247, 238, 255, 238],
                [238, 255, 238, 238, 247, 238],
                [244, 247, 238, 255, 244, 238],
                [255, 238, 247, 244, 238, 244],
                [247, 255, 238, 255, 238, 238],
                [247, 244, 255, 238, 238, 238]])
            exp_green_vals = numpy.array([
                [79, 160, 215, 79, 160, 79],
                [79, 160, 79, 79, 215, 79],
                [116, 215, 79, 160, 116, 79],
                [160, 79, 215, 116, 79, 116],
                [215, 160, 79, 160, 79, 79],
                [215, 116, 189, 79, 79, 79]])
            exp_blue_vals = numpy.array([
                [77, 68, 103, 77, 68, 77],
                [77, 68, 77, 77, 103, 77],
                [74, 103, 77, 68, 74, 77],
                [68, 77, 103, 74, 77, 74],
                [103, 68, 77, 68, 77, 77],
                [103, 74, 86, 77, 77, 77]])

            iml_min = 0.0
            iml_max = 0.3

            hm_writer = geotiff.HazardMapGeoTiffFile(
                path, small_region.grid, html_wrapper=True,
                iml_min_max=(iml_min, iml_max))

            hm_writer.serialize(hm_data)

            self._assert_image_rgb_is_correct(
                path, exp_red_vals, exp_green_vals, exp_blue_vals)

        def _test_hazard_map_relative_scaling(region, hm_data):
            path = helpers.get_output_path(
                'TEST_HAZARD_MAP_relative_scaling.tiff')

            # expected colors for each pixel in the map:
            exp_red_vals = numpy.array([
                [49, 186, 255, 138, 186, 24],
                [0, 208, 67, 0, 255, 24],
                [143, 255, 123, 186, 143, 0],
                [186, 0, 255, 186, 238, 143],
                [255, 186, 0, 186, 12, 205],
                [255, 143, 208, 238, 97, 0]])
            exp_green_vals = numpy.array([
                [190, 197, 255, 236, 197, 175],
                [39, 216, 202, 39, 255, 175],
                [161, 255, 235, 197, 161, 39],
                [197, 39, 255, 197, 79, 161],
                [255, 197, 39, 197, 129, 255],
                [255, 161, 216, 79, 122, 39]])
            exp_blue_vals = numpy.array([
                [255, 247, 255, 174, 247, 255],
                [224, 251, 255, 224, 255, 255],
                [241, 255, 200, 247, 241, 224],
                [247, 224, 255, 247, 77, 241],
                [255, 247, 224, 247, 248, 162],
                [255, 241, 251, 77, 236, 224]])

            hm_writer = geotiff.HazardMapGeoTiffFile(
                path, small_region.grid, html_wrapper=True)

            hm_writer.serialize(hm_data)

            self._assert_image_rgb_is_correct(
                path, exp_red_vals, exp_green_vals, exp_blue_vals)

        # 8x8 px
        small_region_coords = [(0.0, 0.0), (0.5, 0.0), (0.5, 0.5), (0.0, 0.5)]
        small_region = shapes.Region.from_coordinates(small_region_coords)

        hm_point_data = {
            'investigationTimeSpan': '50.0',
            'statistics': 'quantile',
            'vs30': 760.0,
            'IMT': 'PGA',
            'poE': 0.1,
            'IML': None,
            'quantileValue': 0.25}

        iml_list = [
            0.361937801476,
            0.273532008508,
            0.242229898865,
            0.419417963875,
            0.272285730608,
            0.348273115152,
            0.305440556821,
            0.264260394999,
            0.377844386865,
            0.313182264442,
            0.249751814648,
            0.351339245536,
            0.27965491195,
            0.245197064505,
            0.404364061323,
            0.274841943048,
            0.281393272007,
            0.304689514445,
            0.267924606026,
            0.308982744041,
            0.249441042426,
            0.275752227615,
            0.528185455822,
            0.280781760955,
            0.247868614611,
            0.270997983466,
            0.309521592277,
            0.268810429387,
            0.33831815943,
            0.451071839091,
            0.244078269563,
            0.284520817008,
            0.261061308897,
            0.540030551854,
            0.29261888758,
            0.306303457108]
        hm_data = []

        for i, site in enumerate(small_region.sites):
            data = copy.copy(hm_point_data)
            data['IML'] = iml_list[i]
            hm_data.append((site, data))

        _test_hazard_map_fixed_scaling(small_region, hm_data)
        _test_hazard_map_relative_scaling(small_region, hm_data)

    def test_hazard_map_geotiff_scaling_fixed(self):
        """
        Scaling type for a HazardMapGeoTiffFile is 'fixed' if the iml_min_max
        is specified in the constructor.

        This test ensures the scaling type is properly set to 'fixed'.
        """
        # Nothing is actually written to this file in this test
        test_file_path = "test.tiff"
        test_region = shapes.Region.from_coordinates(TEST_REGION_SMALL)
        test_iml_min_max = ('0.0', '4.8')

        # test 'fixed' color scaling
        hm_writer = geotiff.HazardMapGeoTiffFile(
            test_file_path, test_region.grid, TEST_COLORMAP,
            iml_min_max=test_iml_min_max)
        self.assertEqual('fixed', hm_writer.scaling)

    def test_hazard_map_geotiff_scaling_relative(self):
        """
        Scaling type for a HazardMapGeoTiffFile is 'relative' if the
        iml_min_max is not specified in the constructor. Instead, the min and
        max values are derived from the lowest and highest existing values in
        the hazard map raster (the min and max values are calculated later when
        the raw raster values are normalized; see the HazardMapGeoTiffFile
        class doc for more info).

        This test ensures that the scaling type is properly set to 'relative'.
        """
        # Nothing is actually written to this file in this test
        test_file_path = "test.tiff"
        test_region = shapes.Region.from_coordinates(TEST_REGION_SMALL)

        # test 'relative' color scaling
        hm_writer = geotiff.HazardMapGeoTiffFile(
            test_file_path, test_region.grid, TEST_COLORMAP)
        self.assertEqual('relative', hm_writer.scaling)


class WriterTestCase(unittest.TestCase):
    def test_composite_accepts_null_writer(self):
        w = writer.CompositeWriter(None)
        w.serialize([1, 20, 300])

    def test_composite_writer(self):
        class Writer(object):
            def __init__(self):
                self.serialized = []

            def serialize(self, iterable):
                for item in iterable:
                    self.serialized.append(item)

        w_a = Writer()
        w_b = Writer()
        w = writer.CompositeWriter(w_a, w_b)
        data = [1, 20, 300]
        w.serialize(data)
        self.assertEqual(w_a.serialized, data)
        self.assertEqual(w_b.serialized, data)
