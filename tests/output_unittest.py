# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2012, GEM Foundation.
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
import unittest

from openquake import writer
from openquake import shapes
from tests.utils import helpers
from openquake.output import curve

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
