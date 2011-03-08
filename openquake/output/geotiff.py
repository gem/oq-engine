# This file is part of OpenQuake.
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

# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
A trivial implementation of the GeoTiff format,
using GDAL.

In order to make this run, you'll need GDAL installed,
and on the Mac I couldn't get the brew recipe to work.
I recommend the DMG framework at
http://www.kyngchaos.com/software:frameworks.

I had to add the installed folders to
PYTHONPATH in my .bash_profile file to get them to load.
"""

import numpy
import os
import re

from osgeo import osr, gdal
from scipy.interpolate import interp1d


from openquake import logs
from openquake import writer

from openquake.output import template

LOG = logs.LOG

GDAL_FORMAT = "GTiff"
GDAL_PIXEL_DATA_TYPE = gdal.GDT_Float32
SPATIAL_REFERENCE_SYSTEM = "WGS84"
TIFF_BAND = 4
TIFF_LONGITUDE_ROTATION = 0
TIFF_LATITUDE_ROTATION = 0

RGB_SEGMENTS, RGB_RED_BAND, RGB_GREEN_BAND, RGB_BLUE_BAND = range(0, 4)


# these are some continuous colormaps, as found on
# http://soliton.vm.bytemark.co.uk/pub/cpt-city/index.html
COLORMAP = {'green-red': numpy.array(
    ((0.0, 1.0), (0, 255), (255, 0), (0, 0))),
            'gmt-green-red': numpy.array(
    ((0.0, 1.0), (0, 128), (255, 0), (0, 0))),
            'matlab-polar': numpy.array(
    ((0.0, 0.5, 1.0), (0, 255, 255), (0, 255, 0), (255, 255, 0))),
            'gmt-seis': numpy.array(
  ((0.0, 0.1115, 0.2225, 0.3335, 0.4445, 0.5555, 0.6665, 0.7775, 0.8885, 1.0),
     (170, 255, 255, 255, 255, 255, 90, 0, 0, 0),
     (0, 0, 85, 170, 255, 255, 255, 240, 80, 0),
     (0, 0, 0, 0, 0, 0, 30, 110, 255, 205))),
            }

COLORMAP_DEFAULT = 'green-red'

SCALE_UP = 8


class GeoTiffFile(writer.FileWriter):
    """Rough implementation of the GeoTiff format,
    based on http://adventuresindevelopment.blogspot.com/2008/12/
                python-gdal-adding-geotiff-meta-data.html
    """
    format = GDAL_FORMAT
    normalize = True

    def __init__(self, path, image_grid, init_value=numpy.nan,
                 normalize=False):
        self.grid = image_grid
        self.normalize = normalize
        # NOTE(fab): GDAL initializes the image as columns x rows.
        # numpy arrays, however, have usually rows as first axis,
        # and columns as second axis (as it is the convention for
        # matrices in maths)

        # initialize raster to init_value values (default in NaN)
        self.raster = numpy.ones((self.grid.rows, self.grid.columns),
                                 dtype=numpy.float) * init_value
        self.alpha_raster = numpy.ones((self.grid.rows, self.grid.columns),
                                 dtype=numpy.float) * 32.0
        self.target = None
        super(GeoTiffFile, self).__init__(path)

    def _init_file(self):
        driver = gdal.GetDriverByName(self.format)

        # NOTE(fab): use GDAL data type GDT_Float32 for science data
        pixel_type = GDAL_PIXEL_DATA_TYPE
        if self.normalize:
            pixel_type = gdal.GDT_Byte
        self.target = driver.Create(self.path, self.grid.columns,
            self.grid.rows, TIFF_BAND, pixel_type)

        corner = self.grid.region.upper_left_corner

        # this is the order of arguments to SetGeoTransform()
        # top left x, w-e pixel resolution, rotation,
        # top left y, rotation, n-s pixel resolution
        # rotation is 0 if image is "north up"
        # taken from http://www.gdal.org/gdal_tutorial.html

        # NOTE(fab): the last parameter (grid spacing in N-S direction) is
        # negative, because the reference point for the image is the
        # upper left (north-western) corner
        self.target.SetGeoTransform(
            [corner.longitude, self.grid.cell_size, TIFF_LONGITUDE_ROTATION,
             corner.latitude, TIFF_LATITUDE_ROTATION, -self.grid.cell_size])

        # set the reference info
        srs = osr.SpatialReference()
        srs.SetWellKnownGeogCS(SPATIAL_REFERENCE_SYSTEM)
        self.target.SetProjection(srs.ExportToWkt())

    def write(self, cell, value):
        """Stores the cell values in the NumPy array for later
        serialization. Make sure these are zero-based cell addresses."""
        self.raster[int(cell[0]), int(cell[1])] = float(value)
        # Set AlphaLayer
        if value:
            self.alpha_raster[int(cell[0]), int(cell[1])] = 255.0

    def _normalize(self):
        """ Normalize the raster matrix """
        # NOTE(fab): numpy raster does not have to be transposed, although
        # it has rows x columns
        if self.normalize:
            self.raster = self.raster * 254.0 / self.raster.max()

    def close(self):
        """Make sure the file is flushed, and send exit event"""
        self._normalize()

        self.target.GetRasterBand(1).WriteArray(self.raster)
        self.target.GetRasterBand(2).Fill(0.0)
        self.target.GetRasterBand(3).Fill(0.0)

        # Write alpha channel
        self.target.GetRasterBand(4).WriteArray(self.alpha_raster)

        # Try to write the HTML wrapper
        try:
            self._write_html_wrapper()
        except AttributeError:
            pass

        self.target = None  # This is required to flush the file

    def _write_html_wrapper(self):
        """write an html wrapper that embeds the geotiff."""
        pass

    def serialize(self, iterable):
        # TODO(JMC): Normalize the values
        maxval = max(iterable.values())
        for key, val in iterable.items():
            if self.normalize:
                val = val / maxval * 254
            self.write((key.column, key.row), val)
        self.close()


class MapGeoTiffFile(GeoTiffFile):
    """ Write RGBA geotiff images for loss/hazard maps. Color scale is from
    0(0x00)-100(0xff). In addition, we write out an HTML wrapper around
    the TIFF with a color-scale legend."""

    def write(self, cell, value):
        """Stores the cell values in the NumPy array for later
        serialization. Make sure these are zero-based cell addresses."""
        self.raster[int(cell[0]), int(cell[1])] = float(value)

        # Set AlphaLayer
        if value:
            # 0x10 less than full opacity
            self.alpha_raster[int(cell[0]), int(cell[1])] = float(0xfa)

    def _normalize(self):
        """ Normalize the raster matrix """
        if self.normalize:
            # This gives us a color scale of 0 to 100 with a 16 step.
            self.raster = numpy.abs((255 * self.raster) / 100.0)
            modulo = self.raster % 0x10
            self.raster -= modulo

    def _write_html_wrapper(self):
        """write an html wrapper that <embed>s the geotiff."""

        if self.path.endswith(('tiff', 'TIFF')):
            html_path = ''.join((self.path[0:-4], 'html'))
        else:
            html_path = ''.join((self.path, '.html'))

        # replace placeholders in HTML template with filename, height, width
        html_string = template.generate_html(
            os.path.basename(self.path),
            width=str(self.target.RasterXSize * SCALE_UP),
            height=str(self.target.RasterYSize * SCALE_UP),
            imt='Loss Ratio/percent',
            template=template.HTML_TEMPLATE_LOSSRATIO)

        with open(html_path, 'w') as f:
            f.write(html_string)


class LossMapGeoTiffFile(MapGeoTiffFile):
    """ Write RGBA geotiff images for loss maps. Color scale is from
    0(0x00)-100(0xff). In addition, we write out an HTML wrapper around
    the TIFF with a color-scale legend."""
    pass


class HazardMapGeoTiffFile(MapGeoTiffFile):
    """
    Writes a GeoTiff image for hazard maps with an arbitrary colormap.

    Color scaling can be absolute for the range of IML values defined for the
    calculation, or it can be relative to the only the range IML values
    existing in the map.

    In addition, we write out an HTML wrapper around
    the TIFF with a color-scale legend.
    """
    def __init__(self, path, imls, image_grid, colormap,
                 relative_color_scaling=False):
        """
        :param path: location of output, including file
            name
        :type path: string

        :param imls: list of IML values defined for the calculation which
            produced the hazard map data
        :type imls: list of floats

        :param grid: the geographical area covered by the hazard map
        :type grid: shapes.Grid object

        :param colormap: colormap data, as read by a :py:class: `CPTReader`
            object
        :type colormap: dict

        :param relative_color_scaling:
            False / absolute:
                Color is scaled across the range of possible IML values. This
                is useful when comparing two or more hazard maps.
            True / relative:
                Color is scaled across the range of actual IML values in the
                map. This is useful for showing greater contrast between the
                sites within a single map.
        :type relative_color_scaling: boolean
        """
        super(HazardMapGeoTiffFile, self).__init__(path, image_grid)
        self.imls = imls
        self.colormap = colormap
        self.relative_color_scaling = relative_color_scaling


class GMFGeoTiffFile(GeoTiffFile):
    """Writes RGB GeoTIFF image for ground motion fields. Color scale is
    from green (value 0.0) to red (value 2.0). In addition, writes an
    HTML wrapper around the TIFF with a colorscale legend."""

    CUT_LOWER = 0.0
    CUT_UPPER = 2.0
    COLOR_BUCKETS = 16  # yields 0.125 step size

    def __init__(self, path, image_grid, init_value=numpy.nan,
                 normalize=True, iml_list=None, discrete=True,
                 colormap=None):
        super(GMFGeoTiffFile, self).__init__(path, image_grid, init_value,
                                             normalize)

        # NOTE(fab): for the moment, the image is always normalized
        # and 4-band RGBA (argument normalize is disabled)
        self.normalize = True
        self.discrete = discrete
        self.colormap = COLORMAP_DEFAULT

        if colormap is not None:
            self.colormap = colormap

        if iml_list is None:
            self.iml_list, self.iml_step = numpy.linspace(
                self.CUT_LOWER, self.CUT_UPPER, num=self.COLOR_BUCKETS + 1,
                retstep=True)
            self.color_buckets = self.COLOR_BUCKETS
        else:
            self.iml_list = numpy.array(iml_list)
            self.color_buckets = len(iml_list) - 1
            self.iml_step = None

        # list with pairs of RGB color hex codes and corresponding
        # floats as values
        self.colorscale_values = self._generate_colorscale()

        # set image rasters
        self.raster_r = numpy.zeros((self.grid.rows, self.grid.columns),
                                    dtype=numpy.int)
        self.raster_g = numpy.zeros_like(self.raster_r)
        self.raster_b = numpy.zeros_like(self.raster_r)

    def _normalize(self):
        """ Normalize the raster matrix """

        # for discrete color scale, digitize raster values into
        # IML list values
        if self.discrete is True:
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
        self.raster = self._condense_iml_range_to_unity(
            self.raster, remove_outliers=True)

        self.raster_r, self.raster_g, self.raster_b = _rgb_for(
            self.raster, COLORMAP[self.colormap])

    def close(self):
        """Make sure the file is flushed, and send exit event"""
        self._normalize()

        self.target.GetRasterBand(1).WriteArray(self.raster_r)
        self.target.GetRasterBand(2).WriteArray(self.raster_g)
        self.target.GetRasterBand(3).WriteArray(self.raster_b)

        # set alpha channel to fully opaque
        self.target.GetRasterBand(4).Fill(255)

        # write wrapper before closing file, so that raster dimensions are
        # still accessible
        self._write_html_wrapper()

        self.target = None  # This is required to flush the file

    @property
    def html_path(self):
        """Path to the generated html file"""
        if self.path.endswith(('tiff', 'TIFF')):
            return ''.join((self.path[0:-4], 'html'))
        else:
            return ''.join((self.path, '.html'))

    def _write_html_wrapper(self):
        """Write an html wrapper that embeds the geotiff in an <img> tag.
        NOTE: this cannot be viewed out-of-the-box in all browsers."""

        # replace placeholders in HTML template with filename, height, width
        # TODO(fab): read IMT from config
        html_string = template.generate_html(
            os.path.basename(self.path),
            width=str(self.target.RasterXSize * SCALE_UP),
            height=str(self.target.RasterYSize * SCALE_UP),
            colorscale=self.colorscale_values,
            imt='PGA/g')

        with open(self.html_path, 'w') as f:
            f.write(html_string)

    def _condense_iml_range_to_unity(self, array, remove_outliers=False):
        """Requires a one- or multi-dim. numpy array as argument."""
        array = (array - self.iml_list[0]) / (
            self.iml_list[-1] - self.iml_list[0])

        if remove_outliers is True:
            # cut values to 0.0-0.1 range (remove outliers)
            numpy.putmask(array, array < 0.0, 0.0)
            numpy.putmask(array, array > 1.0, 1.0)

        return array

    def _generate_colorscale(self):
        """Generate a list of pairs of corresponding RGB hex values and
        IML values for the colorscale in HTML output."""
        colorscale = []
        r, g, b = _rgb_for(self._condense_iml_range_to_unity(self.iml_list),
                           COLORMAP[self.colormap])

        for idx, _iml_value in enumerate(self.iml_list):
            colorscale.append(("#%02x%02x%02x" % (int(r[idx]), int(g[idx]),
                int(b[idx])), str(self.iml_list[idx])))

        return colorscale


def _rgb_for(fractional_values, colormap):
    """Return a triple (r, g, b) of numpy arrays with R, G, and B
    color values between 0 and 255, respectively, for a given numpy array
    fractional_values between 0 and 1.
    colormap is a 2-dim. numpy array with fractional values describing the
    color segments in the first row, and R, G, B corner values in the second,
    third, and fourth row, respectively."""
    return (_interpolate_color(fractional_values, colormap, RGB_RED_BAND),
            _interpolate_color(fractional_values, colormap, RGB_GREEN_BAND),
            _interpolate_color(fractional_values, colormap, RGB_BLUE_BAND))


def _interpolate_color(fractional_values, colormap, rgb_band):
    """Compute/create numpy array of rgb color value as interpolated
    from color map. numpy array fractional_values is assumed to hold values
    between 0 and 1. rgb_band can be 1,2,3 for red, green, and blue color
    bands, respectively."""

    color_interpolate = interp1d(colormap[RGB_SEGMENTS], colormap[rgb_band])
    return numpy.reshape(color_interpolate(fractional_values.flatten()),
                         fractional_values.shape)


class CPTReader:
    """This class provides utilities for reading colormap data from cpt files.

    Colormaps have the following properties:
    - z-values: Any sequence of numbers (example: [-2.5, -2.4, ... , 1.4, 1.5])
    - colormap Id (example: seminf-haxby.cpt,v 1.1 2004/02/25 18:15:50 jjg Exp)
    - colormap name (example: seminf-haxby)
    - color model (RGB, HSV, or CMYK)
    - RGB, HSV, or CMYK values associated with the ranges defined by the
      z-values
    - Background color
    - Foreground color
    - NaN color
    - colormap type (discrete or continuous; this is determined by the
      arrangement of z- and color values)

    Example RGB colormap:
        {'id': 'seminf-haxby.cpt,v 1.1 2004/02/25 18:15:50 jjg Exp',
         'name': 'seminf-haxby',
         'type': 'discrete',  # 'discrete' or 'continuous'
         'model': 'RGB',
         'z_values': [0.00, 1.25, 2.50, ... , 28.75, 30.00],
         'red': [255, 208, 186, ... , 244, 238],
         'green': [255, 216, 197, ... , 116, 79],
         'blue': [255, 251, 247, ... , 74, 77],
         'background': [255, 255, 255],
         'foreground': [238, 79, 77],
         'NaN': [0, 0, 0]}

    See also:
        Library of cpt files:
            http://soliton.vm.bytemark.co.uk
        MAKECPT:
            http://www.soest.hawaii.edu/gmt/gmt/doc/gmt/html/man/makecpt.html

    TODO(LB): Currently, only RGB colormaps are supported. HSV and CMYK
    colormaps are not supported.
    """

    SUPPORTED_COLOR_MODELS = ('RGB',)

    NAME_RE = re.compile(r'^(.+).cpt$')
    ID_RE = re.compile(r'\$Id:\s+(.+)\s+\$')
    COLOR_MODEL_RE = re.compile(r'^COLOR_MODEL\s+=\s+(.+)')

    def __init__(self, path):
        """
        :param path: location of a cpt file, including file name
        :type path: string
        """
        self.path = path
        self.colormap = {
            'id': None,
            'name': None,
            'type': None,
            'model': None,
            'z_values': [],
            'red': [],
            'green': [],
            'blue': [],
            'background': None,
            'foreground': None,
            'NaN': None}

    def get_colormap(self):
        """
        Read the input cpt file and attempt to parse colormap data.

        :returns: dict representation of the colormap
        """
        with open(self.path, 'r') as fh:
            for line in fh:
                # ignore empty lines
                if not line.strip():
                    continue
                elif line[0] == '#':
                    self._parse_comment(line)
                elif line[0] in ['B', 'F', 'N']:
                    self._parse_bfn(line)
                else:
                    self._parse_color_table(line)
        if not self.colormap['model'] in self.SUPPORTED_COLOR_MODELS:
            raise ValueError('Color model type %s is not supported' %
                             self.colormap['model'])
        return self.colormap

    def _parse_comment(self, line):
        """
        Looks for name, id, and color model type in a comment line (beginnning
        with a '#').

        :param line: a single line read from the cpt file
        """
        text = line.split('#')[1].strip()
        for attr, regex in  (('name', self.NAME_RE),
                             ('id', self.ID_RE),
                             ('model', self.COLOR_MODEL_RE)):
            # if the attr is already defined, skip it
            if self.colormap[attr]:
                continue
            match = regex.match(text)
            if match:
                self.colormap[attr] = match.group(1)

    def _parse_bfn(self, line):
        """
        Parse Background, Foreground, and NaN values from the color table.

        :param line: a single line read from the cpt file
        """
        for token, key in (('B', 'background'),
                           ('F', 'foreground'),
                           ('N', 'NaN')):
            if line[0] == token:
                _bfn, color = line.split(token)
                self.colormap[key] = [int(x) for x in color.split()]
                return

    def _protect_map_type(self, map_type):
        """
        Prevent the parser from changing map types (discrete vs. continuous),
        which could be caused by a malformed cpt file.

        If a map type is defined (not None) and then changed, this will throw
        an :py:exc: `AssertionError`.

        :param map_type: 'discrete' or 'continuous'
        """
        assert (self.colormap['type'] is None
                or self.colormap['type'] == map_type)

    def _parse_color_table(self, line):
        """
        Parse z-values and color values from the color table.

        The map type (discrete or continuous) is also implicity determined from
        these values.

        :param line: a single line read from the cpt file
        """
        drop_tail_extend = lambda lst, ext: lst[:-1] + [x for x in ext]
        strs_to_ints = lambda strs: [int(x) for x in strs]

        values = line.split()
        assert len(values) == 8

        # there are two columns of values (each containing z and color values)
        z_vals = (float(values[0]), float(values[4]))
        self.colormap['z_values'] = drop_tail_extend(self.colormap['z_values'],
                                                     z_vals)

        rgb1 = strs_to_ints(values[1:4])
        rgb2 = strs_to_ints(values[5:8])
        if rgb1 == rgb2:
            map_type = 'discrete'
        else:
            map_type = 'continuous'
        try:
            self._protect_map_type(map_type)
        except AssertionError:
            raise ValueError("Could not determine map type (discrete or"
                             " continuous). The cpt file could be malformed.")
        self.colormap['type'] = map_type

        for i, color in enumerate(('red', 'green', 'blue')):
            if map_type == 'discrete':
                self.colormap[color].append(rgb1[i])
            elif map_type == 'continuous':
                self.colormap[color] = drop_tail_extend(self.colormap[color],
                                                        (rgb1[i], rgb2[i]))
            else:
                raise ValueError("Unknown map type '%s'" % map_type)
