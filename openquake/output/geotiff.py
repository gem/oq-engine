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
A trivial implementation of the GeoTiff format,
using GDAL.

In order to make this run, you'll need GDAL installed.
"""

import numpy
import os

from osgeo import osr, gdal
from scipy import interpolate


from openquake import logs
from openquake import writer

from openquake.output import template

GDAL_FORMAT = "GTiff"
GDAL_PIXEL_DATA_TYPE = gdal.GDT_Float32
SPATIAL_REFERENCE_SYSTEM = "WGS84"
TIFF_BAND = 4
TIFF_LONGITUDE_ROTATION = 0
TIFF_LATITUDE_ROTATION = 0

COLORMAPS = {
    'green-red': {
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
        'NaN': None},
    'gmt-green-red': {
        'id': 'gmt-green-red',
        'name': 'gmt-green-red',
        'type': 'continuous',
        'model': 'RGB',
        'z_values': [0.0, 1.0],
        'red': [0, 128],
        'green': [255, 0],
        'blue': [0, 0],
        'background': None,
        'foreground': None,
        'NaN': None},
    'matlab-polar': {
        'id': 'matlab-polar',
        'name': 'matlab-polar',
        'type': 'continuous',
        'model': 'RGB',
        'z_values': [0.0, 0.5, 1.0],
        'red': [0, 255, 255],
        'green': [0, 255, 0],
        'blue': [255, 255, 0],
        'background': None,
        'foreground': None,
        'NaN': None},
    'gmt-seis': {
        'id': 'gmt-seis',
        'name': 'gmt-seis',
        'type': 'continuous',
        'model': 'RGB',
        'z_values': [0.0, 0.1115, 0.2225, 0.3335, 0.4445, 0.5555, 0.6665,
            0.7775, 0.8885, 1.0],
        'red': [170, 255, 255, 255, 255, 255, 90, 0, 0, 0],
        'green': [0, 0, 85, 170, 255, 255, 255, 240, 80, 0],
        'blue': [0, 0, 0, 0, 0, 0, 30, 110, 255, 205],
        'background': None,
        'foreground': None,
        'NaN': None},
    'seminf-haxby': {
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
        'NaN': [0, 0, 0]},
}


SCALE_UP = 8


class GeoTiffFile(writer.FileWriter):
    """Rough implementation of the GeoTiff format,
    based on http://adventuresindevelopment.blogspot.com/2008/12/
                python-gdal-adding-geotiff-meta-data.html
    """
    format = GDAL_FORMAT
    html_template = None

    def __init__(
        self, path, image_grid, init_value=numpy.nan, html_wrapper=True,
        pixel_type=gdal.GDT_Byte):
        """
        :param path: location of output file, including file name
        :type path: string

        :param grid: the geographical area covered by the hazard map
        :type grid: shapes.Grid object

        :param init_value: initial value for each member of the raster matrix
        :type init_value: float

        :param html_wrapper: if True, a simple html wrapper file will be
            created to display the geotiff and a color legend
        :type html_wrapper: boolean

        :param pixel_type: data type for each pixel in the image raster (for
            example: gdal.GDT_Byte, gdal.GDT_Float32)
        :type pixel_type: gdal numeric data type
        """
        super(GeoTiffFile, self).__init__(path)
        self.grid = image_grid
        self.html_wrapper = html_wrapper
        # NOTE(fab): GDAL initializes the image as columns x rows.
        # numpy arrays, however, have usually rows as first axis,
        # and columns as second axis (as it is the convention for
        # matrices in maths)

        # initialize raster to init_value values (default in NaN)
        self.raster = numpy.ones((self.grid.rows, self.grid.columns),
                                 dtype=numpy.float) * init_value
        self.alpha_raster = numpy.ones((self.grid.rows, self.grid.columns),
                                 dtype=numpy.float) * 32.0
        self.target = make_target(
            self.path, self.grid, GDAL_FORMAT, pixel_type)

    @property
    def html_path(self):
        """
        Path to the generated html file.
        """
        if self.path.endswith(('tiff', 'TIFF')):
            return ''.join((self.path[0:-4], 'html'))
        else:
            return ''.join((self.path, '.html'))

    def write(self, coords, value):
        """
        Plot an IML value to the image raster. These values will need to be
        converted to color values before writing the geotiff file.

        :param coords: matrix coordinates where we want to store the input
            value; coordinates are zero-based
        :type coords: tuple of integers (row, column)

        :param value: raw IML value; this will be transformed to a color value
            and written to the geotiff
        :type value: float
        """
        self.raster[int(coords[0]), int(coords[1])] = float(value)
        # Set AlphaLayer
        if value:
            # set the alpha at this point to fully opqaue
            # TODO (LB): we might want to make this configurable in the future
            self.alpha_raster[int(coords[0]), int(coords[1])] = 255.0

    def _normalize(self):
        """
        Convert the range of pixel intensity values in the raster to color
        values.

        Subclasses will be responsible for specific implementation.

        For more information, see:
        http://en.wikipedia.org/wiki/Normalization_(image_processing)
        """
        raise NotImplementedError

    def _generate_colorscale(self):
        """
        Override this in subclasses. Typically, the return value should be a
        list of tuples of (hex color string, value range string), which will be
        rendered in an html file as a color legend.

        Exact implementation of this method will vary between subclasses.

        If no color scale is required for the subclass, simply override and
        return None.
        """
        raise NotImplementedError

    def _get_rgb(self):
        """
        Get red, green, and blue values for each pixel in the image. Raster
        values should be normalized before this is called.

        :returns: List of numpy.arrays: [red, green, blue]. Each array is the
            same shape as the image raster (self.raster).
        """
        raise NotImplementedError

    def close(self):
        self._normalize()

        red, green, blue = self._get_rgb()
        # red band
        self.target.GetRasterBand(1).WriteArray(red)
        # green band
        self.target.GetRasterBand(2).WriteArray(green)
        # blue band
        self.target.GetRasterBand(3).WriteArray(blue)
        # alpha band
        self.target.GetRasterBand(4).WriteArray(self.alpha_raster)

        if self.html_wrapper:
            self._write_html_wrapper()

        self.target = None  # This is required to flush the file
        self.file.close()

    def _write_html_wrapper(self):
        """Write an html wrapper that embeds the geotiff in an <img> tag.
        NOTE: this cannot be viewed out-of-the-box in all browsers."""
        if self.html_wrapper:
            # replace placeholders in HTML template with filename, height,
            # width
            # TODO(fab): read IMT from config
            html_string = template.generate_html(
                os.path.basename(self.path),
                width=str(self.target.RasterXSize * SCALE_UP),
                height=str(self.target.RasterYSize * SCALE_UP),
                colorscale=self._generate_colorscale(),
                imt='PGA/g',
                template=self.html_template)

            with open(self.html_path, 'w') as f:
                f.write(html_string)


class LossMapGeoTiffFile(GeoTiffFile):
    """ Write RGBA geotiff images for loss maps. Color scale is from
    0(0x00)-100(0xff). In addition, we write out an HTML wrapper around
    the TIFF with a color-scale legend."""

    html_template = template.HTML_TEMPLATE_LOSSRATIO

    def __init__(
        self, path, grid, init_value=numpy.nan, pixel_type=gdal.GDT_Byte,
        normalize=True):
        """
        :param path: path to output file, include file name

        :param grid: defines the geographic region associated with this map
        :type grid: shapes.Grid object

        :param init_value: initial value for each point in the image raster

        :param pixel_type: data type for each pixel in the image raster
            (gdal.GDT_Byte, gdal.GDT_Float32, etc.)
        :type pixel_type: gdal numeric data type

        :param normalize: if true, the raster data will be normalized; else,
            the raw data values in the raster are converted to rgb and written
            to the image
        """
        super(LossMapGeoTiffFile, self).__init__(
            path, grid, init_value=init_value, pixel_type=pixel_type)
        self.normalize = normalize

    def write(self, cell, value):
        """Stores the cell values in the NumPy array for later
        serialization. Make sure these are zero-based cell addresses."""
        self.raster[int(cell[0]), int(cell[1])] = float(value)

        # Set AlphaLayer
        if value:
            # TODO (LB): I don't like this hard-coded alpha value
            # this should probably be configurable
            self.alpha_raster[int(cell[0]), int(cell[1])] = 250.0

    def _normalize(self):
        """ Normalize the raster matrix """
        if self.normalize:
            # This gives us a color scale of 0 to 100 with a 16 step.
            self.raster = numpy.abs((255 * self.raster) / 100.0)
            modulo = self.raster % 16
            self.raster -= modulo

    def close(self):
        """Make sure the file is flushed, and send exit event"""
        self._normalize()

        self.target.GetRasterBand(1).WriteArray(self.raster)
        self.target.GetRasterBand(2).Fill(0.0)
        self.target.GetRasterBand(3).Fill(0.0)

        # Write alpha channel
        self.target.GetRasterBand(4).WriteArray(self.alpha_raster)

        # Try to write the HTML wrapper
        # try:
        self._write_html_wrapper()
        # except AttributeError:
        #     pass

        self.target = None  # This required to flush the file
        self.file.close()

    def _generate_colorscale(self):
        """
        Loss maps currently do not have color scale legend.
        """
        return None

    def _get_rgb(self):
        """
        Not used.
        """
        return None


class HazardMapGeoTiffFile(GeoTiffFile):
    """
    Writes a GeoTiff image for hazard maps with an arbitrary colormap.
    Colormap input is expected to be a dict and can be produced from a standard
    cpt file by the :py:class: `cpt.CPTReader` class.

    IML values for each site in the map are represented by a color. Color
    scaling can be applied in one of two ways: 'fixed' or 'relative'.
        - fixed: colors are mapped across a range of min and max IML values
            (defined in the job config)
        - relative: Colors are mapped across only the min and max IML values
            existing in a given map

    In addition, we write out an HTML wrapper around
    the TIFF with a color-scale legend.
    """

    DEFAULT_COLORMAP = COLORMAPS['seminf-haxby']

    def __init__(self, path, image_grid, colormap=None, iml_min_max=None,
                 html_wrapper=False):
        """
        :param path: location of output, including file
            name
        :type path: string

        :param grid: the geographical area covered by the hazard map
        :type grid: shapes.Grid object

        :param colormap: colormap data, as produced by a
            :py:class: `cpt.CPTReader` object
        :type colormap: dict (see :py:class: `cpt.CPTReader` documentation for
            details about the dict structure)

        :param iml_min_max: defines the min and max values of the IML scale for
            this hazard map; if defined, map color scaling will be 'fixed';
            else, 'relative'
        :type iml_min_max: tuple of a pair of floats (example: (0.005, 2.13))

        :param html_wrapper: if True, a simple html wrapper file will be
            created to display the geotiff and a color legend
        :type html_wrapper: boolean

        TODO (LB): In the future, we may also want this class to track the map
        mode (mean or quantile) so we can display this to the user.
        """
        super(HazardMapGeoTiffFile, self).__init__(path, image_grid,
            html_wrapper=html_wrapper)
        self.colormap = colormap  # TODO: Validate the rgb list lengths
        if not self.colormap:
            self.colormap = self.DEFAULT_COLORMAP
        self.html_wrapper = html_wrapper
        self.iml_min = None
        self.iml_max = None
        if iml_min_max:
            # if the iml min/max are defined, let's do some validation
            assert isinstance(iml_min_max, tuple), "Wrong data type"
            assert len(iml_min_max) == 2, "More (or less) than two values"
            self.iml_min = float(iml_min_max[0])
            self.iml_max = float(iml_min_max[1])
            assert self.iml_min >= 0.0, "Negative min value"
            assert self.iml_max >= 0.0, "Negative max value"
            assert self.iml_max > self.iml_min, "Min value exceeds max value"
        if not None in (self.iml_min, self.iml_max):
            self.scaling = 'fixed'
        else:
            self.scaling = 'relative'

    def write(self, site, haz_map_data):
        """
        Plot hazard curve data for a single point on the map.

        :param site: location associated with the data to be written
        :type site: shapes.Site object

        :param haz_map_data: hazard curve data, either 'quantile' or 'mean'
            Quantile hazard curve example:
            {'investigationTimeSpan': '50.0',
             'statistics': 'quantile',
             'vs30': 760.0,
             'IMT': 'PGA',
             'poE': 0.10000000000000001,
             'IML': 0.27353200850839826,
             'quantileValue': 0.25}

            Mean hazard curve example:
            {'investigationTimeSpan': '50.0',
             'endBranchLabel': '1_1',
             'vs30': 760.0,
             'IMT': 'PGA',
             'poE': 0.10000000000000001,
             'IML': 0.27353200850839826}
        :type haz_map_data: dict
        """
        # TODO (LB): Typically, hazard maps display IML values (with a fixed
        # probability). In the future, we may need to support the opposite
        # (display probablilities with a fixed IML value).
        point = self.grid.point_at(site)
        return super(HazardMapGeoTiffFile, self).write(
            (point.row, point.column), haz_map_data['IML'])

    def _normalize(self):
        """
        Transform the raw IML values in the raster to the corresponding color
        intensity value in the colormap.
        """

        def _normalize_continuous():
            """
            Continuous colormaps not currently suppported for hazard maps.
            """
            # TODO (LB): Add support for continuous
            raise NotImplementedError("Continuous colormaps are not currently"
                " supported for rendering hazard maps")

        def _normalize_discrete():
            """
            Use a typical graphics normalization formula to map an arbitrary
            range of intensity values (IMLs) to a range of z-values
            (0.0 to 1.0, inclusive).

            More info:
            http://en.wikipedia.org/wiki/Normalization_(image_processing)
            """
            if self.scaling == 'relative':
                # we need to hold on to the min/max values for html colorscale
                # generation later
                self.iml_min = self.raster.min()
                self.iml_max = self.raster.max()
            _min = self.iml_min
            _max = self.iml_max

            z_vals = self.colormap['z_values']
            normalize = lambda raster, z_vals: \
                (raster - _min) * z_vals[-1] / (_max - _min)
            self.raster = normalize(self.raster, z_vals)

        if self.colormap['type'] == 'continuous':
            return _normalize_continuous()
        elif self.colormap['type'] == 'discrete':
            return _normalize_discrete()
        else:
            raise ValueError("Unsupported colormap type '%s'" %
                self.colormap['type'])

    def _get_rgb(self):
        """
        Get red, green, and blue values for each pixel in the image. Raster
        values should be normalized before this is called.

        :returns: List of numpy.arrays: [red, green, blue]. Each array is the
            same shape as the image raster (self.raster).
        """
        return rgb_from_raster(self.colormap, self.raster)

    def _generate_colorscale(self):
        """
        Generates a discrete or continous colorscale legend to be rendered in
        an html file.

        See :py:func: `continuous_colorscale` and
        :py:func: `discrete_colorscale` for more info.
        """
        if self.colormap['type'] == 'continuous':
            return continuous_colorscale(self.colormap, self.raster)
        elif self.colormap['type'] == 'discrete':
            return discrete_colorscale(
                self.colormap, self.iml_min, self.iml_max)
        else:
            raise ValueError("Unsupported colormap type '%s'" %
                self.colormap['type'])


class GMFGeoTiffFile(GeoTiffFile):
    """Writes RGB GeoTIFF image for ground motion fields. Color scale is
    from green (value 0.0) to red (value 2.0). In addition, writes an
    HTML wrapper around the TIFF with a colorscale legend."""

    CUT_LOWER = 0.0
    CUT_UPPER = 2.0
    COLOR_BUCKETS = 16  # yields 0.125 step size
    DEFAULT_COLORMAP = COLORMAPS['green-red']

    def __init__(
        self, path, image_grid, init_value=numpy.nan, iml_list=None,
        discrete=True, colormap=None):
        """
        :param path: path to the output file, including file name

        :param image_grid: geographical location associated with this GMF
        :type image_grid: shapes.Grid

        :param init_value: initial value for each pixel in the image raster

        :param iml_list: entire list of IMLs defined in the job config (hazard
            section)
        :type iml_list: list of floats

        :param discrete: if true, apply discrete color scaling
        :type discrete: boolean

        :param colormap: colormap as read by the :py:class: `cpt.CPTReader`
            class
        """
        super(GMFGeoTiffFile, self).__init__(path, image_grid, init_value)

        # NOTE(fab): for the moment, the image is always normalized
        # and 4-band RGBA (argument normalize is disabled)
        self.discrete = discrete
        self.colormap = colormap
        if not self.colormap:
            self.colormap = self.DEFAULT_COLORMAP

        if iml_list is None:
            self.iml_list, self.iml_step = numpy.linspace(
                self.CUT_LOWER, self.CUT_UPPER, num=self.COLOR_BUCKETS + 1,
                retstep=True)
            self.color_buckets = self.COLOR_BUCKETS
        else:
            self.iml_list = numpy.array(iml_list)
            self.color_buckets = len(iml_list) - 1
            self.iml_step = None

        # set image rasters
        self.raster_r = numpy.zeros((self.grid.rows, self.grid.columns),
                                    dtype=numpy.int)
        self.raster_g = numpy.zeros_like(self.raster_r)
        self.raster_b = numpy.zeros_like(self.raster_r)

    def _normalize(self):
        """ Normalize the raster matrix """

        # for discrete color scale, digitize raster values into
        # IML list values
        if self.discrete:
            index_raster = numpy.digitize(self.raster.flatten(), self.iml_list)

            # fix out-of-bounds values (set to first/last bin)
            # NOTE(fab): doing so, the upper end of the color scale is
            # never reached
            numpy.putmask(index_raster, index_raster < 1, 1)
            numpy.putmask(index_raster, index_raster > len(index_raster) - 1,
                len(index_raster) - 1)
            self.raster = numpy.reshape(self.iml_list[index_raster - 1],
                                        self.raster.shape)

        # condense desired target value range given in IML list to
        # interval 0..1 (because color map segments are given in this scale)
        self.raster = (self.raster - self.iml_list[0]) / (
            self.iml_list[-1] - self.iml_list[0])
        # remove outliers
        numpy.putmask(self.raster, self.raster < 0.0, 0.0)
        numpy.putmask(self.raster, self.raster > 1.0, 1.0)

        self.raster_r, self.raster_g, self.raster_b = rgb_for_continuous(
            self.raster, self.colormap)

    def _get_rgb(self):
        return self.raster_r, self.raster_g, self.raster_b

    def _generate_colorscale(self):
        # TODO: what about discrete colorscale support?
        return continuous_colorscale(self.colormap, self.iml_list)


def condense_to_unity(array, min_max=None):
    """
    Condense an array of values to the interval 0.0..1.0. Uses the following
    formula to do the transformation:

    A = array
    B = range from 0.0 to 1.0
    for each old_value in A:
        new_value = (old_value - min(A)) * max(B) / (max(A) - min(A))

    This is basically the same procedure used in image processing
    normalization:
    http://en.wikipedia.org/wiki/Normalization_(image_processing)

    Example:
        Input: numpy.array([0.005, 0.007, 0.0098])
        Output: numpy.array([0.0, 0.416666666667, 1.0])

    :param array: initial values
    :type array: 1- or 2-dimensional numpy.array of floats

    :param min_max: tuple of floats representing the min and max range
        values (example: (0.8, 4.0))
        If not specified, the min and max for this calculation will default to
        the min and max values in the input iml_list

    :returns: numpy.array of the same length and shape as the input
    """
    if min_max:
        _min, _max = min_max
    else:
        _min = array.min()
        _max = array.max()
    array = (array - _min) * 1.0 / (_max - _min)

    # fold in the outliers
    # if a value is < 0.0, set it to 0.0
    # if a value is > 1.0, set it to 1.0
    numpy.putmask(array, array < 0.0, 0.0)
    numpy.putmask(array, array > 1.0, 1.0)
    return array


def discrete_colorscale(colormap, _min, _max):
    """
    Generate a list of pairs of corresponding RGB hex values (as strings) and
    IML value ranges (as strings) for the colorscale in HTML output.

    Color intervals range from 'Min' to 'Max'. The number of color segments is
    equal to the number of colors defined in the colormap.

    Note: Currently, IML values are displayed only up to 2 decimal places.

    :param colormap: colormap as produced by the :py:class: `cpt.CPTReader`
    :type colormap: dict

    :param _min: lowest IML value to be displayed on the colorscale
    :type _min: integer

    :param _max: highest IML value to be displayed on the colorscale
    :type _max: integer

    :returns: list of tuples of hex color and value ranges, like so:
        [('#ffffff', '0.80 - 0.93'),
         ('#d0d8fb', '0.93 - 1.07'),
         ...
         ('#ee4f4d', '3.87 - 4.00')]
    """
    if colormap['type'] == 'discrete':
        # discrete: (color count == len(z_values) + 1)
        num_colors = len(colormap['z_values']) - 1
    elif colormap['type'] == 'continuous':
        # continuous: (color count == len(z_values))
        num_colors = len(colormap['z_values'])
    else:
        raise ValueError("Invalid colormap type '%s'" % colormap['type'])

    delta = (_max - _min) / num_colors
    # color segment interval 'fence posts'
    seg_intervals = [_min + (n * delta) for n in range(num_colors + 1)]

    colorscale = []
    for i in range(len(seg_intervals) - 1):
        seg_range = "%.2f - %.2f" % (seg_intervals[i], seg_intervals[i + 1])
        hex_color = "#%02x%02x%02x" % (
            colormap['red'][i],
            colormap['green'][i],
            colormap['blue'][i])
        colorscale.append((hex_color, seg_range))

    return colorscale


def continuous_colorscale(colormap, iml_list):
    """
    Generate a list of pairs of corresponding RGB hex values (as strings) and
    IML values (as strings) for the colorscale in HTML output.

    :param colormap: colormap as produced by the :py:class: `cpt.CPTReader`
        class
    :type colormap: dict

    :param iml_list: complete list of IML values defined in the job config
    :type iml_list: 1-dimensional numpy.array of IML values (as floats)

    :returns: list of tuples of (<color hex string>, <IML intensity value>);
        For example:
        [('#0000ff', '0.005'), ('#0000ff', '0.007'), ... , ('#ff0000', '2.13')]
    """
    colorscale = []

    condensed_imls = condense_to_unity(iml_list)

    red, green, blue = rgb_for_continuous(condensed_imls, colormap)

    for i, iml in enumerate(iml_list):
        hex_color = "#%02x%02x%02x" % (
            int(red[i]), int(green[i]), int(blue[i]))
        colorscale.append((hex_color, str(iml)))

    return colorscale


def rgb_for_continuous(fractional_values, colormap):
    """
    Given a color map and a numpy.array of normalized raster values
    (normalized to the colormap's scale), get a tuple of 3 numpy.array objects
    (red, green, and blue). Each numpy.array is the same size and shape as the
    input fractional_values array.

    Actual color values are interpolated from the color ranges defined in the
    colormap.

    :param fractional_values: array of normalized raster values
    :type fractional_values: numpy.array

    :param colormap: colormap as produced by the :py:class: `cpt.CPTReader`
        class
    :type colormap: dict

    :returns: a tuple of 3 numpy.arrays representing red, green, and blue
        values for each pixel in the image
    """
    return (interpolate_color(fractional_values, colormap, 'red'),
            interpolate_color(fractional_values, colormap, 'green'),
            interpolate_color(fractional_values, colormap, 'blue'))


def interpolate_color(fractional_values, colormap, color):
    """
    Given a list of normalized raster values, a colormap, and a color key (red,
    green, or blue), generate an array of color values for the given color key
    by interpolating a color value within the color range defined by the
    colormap.

    :param fractional_values: array of normalized raster_values
    :type fractional_values: numpy.array

    :param colormap: colormap as produced by the :py:class: `cpt.CPTReader`
        class
    :type colormap: dict

    :param color: 'red', 'green', or 'blue'
    :type color: string

    :returns: a numpy.array of color values for each pixel in the image from
        the color band defined by the input color parameter
    """
    color_interpolate = interpolate.interp1d(
        condense_to_unity(numpy.array(colormap['z_values'])),
        colormap[color])
    return numpy.reshape(
        color_interpolate(fractional_values.flatten()),
        fractional_values.shape)


def rgb_from_raster(colormap, raster):
    """
    Given raw intensity values in a raster, calculate colormap values and
    return 3 numpy.arrays, 1 for each (red, green, blue).

    Handles continuous and discrete color maps.

    :param colormap: colormap dict as produced by the
        :py:class: `cpt.CPTReader` class
    :type colormap: dict

    :param raster: raw intensity values for the
        image
    :type raster: numpy.array (should be 2-dimensional)
    """
    if colormap['type'] == 'continuous':
        raise NotImplementedError
    elif colormap['type'] == 'discrete':
        # now figure out the proper colors
        # we need to build a list of indices to grab the right
        # colors from the colormap
        bins = numpy.digitize(raster.flatten(), colormap['z_values'])
        # type is discrete; we need the bins to correspond to color indices
        # we subtract 1 because (len(z_vals) == len(rgb_vals) + 1)
        bins -= 1
        # the last z_val range is inclusive on the high end
        # i.e., [a, b), [c, d), ... , [y, z]

        # handle low-end outliers (set to lowest value in range):
        numpy.putmask(bins, bins < 0, 0)
        # handle high-end outliers (set to highest value in range):
        numpy.putmask(
            bins,
            bins > len(colormap['red']) - 1,
            len(colormap['red']) - 1)
        # TODO: verify color value list lengths in the constructor
        # all of them should be equal
        red, green, blue = rgb_values_from_colormap(colormap, bins)
        # now re-shape the color lists per the image shape and return
        return [numpy.reshape(color, raster.shape) for color in \
            (red, green, blue)]


def rgb_values_from_colormap(colormap, index_list):
    """
    Given a list of color band indices, get the color values at each index from
    the given colormap.

    Example:
        Input colormap:
        {'id': 'seminf-haxby.cpt,v 1.1 2004/02/25 18:15:50 jjg Exp',
         'name': 'seminf-haxby',
         'type': 'discrete',
         'model': 'RGB',
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

        Input index_list:
        [0, 1, 2, 3, 23]

        Returns (in the order of red, green, then blue):
        (numpy.array([255, 208, 186, 143, 238]),
         numpy.array([255, 216, 197, 161, 79]),
         numpy.array([255, 251, 247, 241, 77]))

    :param colormap: colormap as read by a :py:class: `cpt.CPTReader` object
    :type colormap: dict

    :param index_list: color value indices
    :type index_list: list of integers

    :returns: tuple of three 1-dimensional numpy.array objects (red, green,
        blue)
    """
    # make sure the color value lists are equal in length
    # if they're not, this is a bad colormap
    assert len(colormap['red']) == len(colormap['green']) \
        and len(colormap['red']) == len(colormap['blue'])

    get_colors = lambda color_list: \
        numpy.array([color_list[i] for i in index_list])
    red, green, blue = \
        [get_colors(colormap[j]) for j in ('red', 'green', 'blue')]
    return red, green, blue


def make_target(path, grid, output_format, pixel_type, bands=4):
    """
    Boiler plate stuff for creating a target for writing geotiffs.

    :param path: path to the output file, including file name
    :type path: string

    :param output_format: string representing to output format type (for
        example, 'GTiff')

    :param pixel_type: integer representing the pixel data type, which
        corresponds to a GDAL data type (for example, gdal.GDT_Byte,
        gdal.GDT_Float32, etc.)

    :param bands: number of raster bands; 4 is default (R,G,B, and Alpha)

    :returns: gdal.Dataset object representing the file target
    """
    driver = gdal.GetDriverByName(output_format)

    target = driver.Create(path, grid.columns, grid.rows, bands, pixel_type)

    # upper left corner of the region
    ul_corner = grid.region.upper_left_corner

    # this is the order of arguments to SetGeoTransform()
    # top left x, w-e pixel resolution, rotation,
    # top left y, rotation, n-s pixel resolution
    # rotation is 0 if image is "north up"
    # taken from http://www.gdal.org/gdal_tutorial.html
    target.SetGeoTransform(
        [ul_corner.longitude, grid.cell_size, TIFF_LONGITUDE_ROTATION,
         ul_corner.latitude, TIFF_LATITUDE_ROTATION, -grid.cell_size])

    # set the reference info
    srs = osr.SpatialReference()
    srs.SetWellKnownGeogCS(SPATIAL_REFERENCE_SYSTEM)
    target.SetProjection(srs.ExportToWkt())

    return target
