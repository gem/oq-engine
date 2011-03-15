#!/usr/bin/env python
# encoding: utf-8

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




"""This module contains classes to parse ESRI stuff ported from
the Java version of the risk engine.

This module is not currently used and there isn't any test coverage.
"""

import math
import struct

class Grid:
    """ESRIGrid format as per http://en.wikipedia.org/wiki/ESRI_grid."""
    def __init__(self, rows, columns, no_data_value=9999):
        self.columns = columns
        self.rows = rows
        self.no_data_value = no_data_value

    def is_no_data_value(self, val):
        """ Return true if the value matches our grid no_data_value """
        return val == self.no_data_value
        
    def check_column(self, point):
        """ Raise if the point is out of bounds """
        if (self.columns < point.column or point.column < 1):
            raise Exception("Point is not on the Grid")
            
    def check_row(self, point):
        """ Raise if the point is out of bounds """
        if (self.rows < point.row or point.row < 1):
            raise Exception("Point is not on the Grid")

class Point:
    """Simple (trivial) point class."""
    def __init__(self, row, column):
        self.column = column
        self.row = row

class Site:
    """Site has lat and long."""
    def __init__(self, latitude, longitude):
        self.latitude = latitude
        self.longitude = longitude

class BaseExposureReader(object):
    """Base class for reading exposure data from file formats."""
    def __init__(self, filename, exposure_definition):
        self.filename = filename
        self.definition = exposure_definition
        self.exposure_file = open(filename, "rb")

class ESRIBinaryFileExposureReader(BaseExposureReader):
    """Parses and loads ESRI formatted exposure data from files."""
    
    def __init__(self, filename, exposure_definition):
        super(ESRIBinaryFileExposureReader, self).__init__(
                filename, exposure_definition)
    
    def read_at(self, site):
        """ Return the unpacked value of the point at the site """
        point = self.definition.point_at(site)
        position = self.position_of(point)
        print "pos is %s" % position
        self.exposure_file.seek(position)
        val = self.exposure_file.read(4)
        return float(struct.unpack("<f", val)[0])
        
    def position_of(self, point):
        """ Return the row/column of the point in bytes """
        rows_offset = (point.row - 1) * self.definition.grid.columns
        rows_offset_in_bytes = rows_offset * 4 # All points are doubles
        columns_offset_in_bytes = (point.column - 1) * 4
        return rows_offset_in_bytes + columns_offset_in_bytes

class AsciiFileHazardIMLReader(BaseExposureReader):
    """ Stubbed reader for Ascii Hazard IML """
    pass

class ESRIRasterMetadata():
    """Object loaded from (various) ESRI header files."""
    def __init__(self, cell_size, grid, lower_left_corner):
        self.cell_size = cell_size
        self.grid = grid
        self.lower_left_corner = lower_left_corner
    
    @classmethod
    def load_esri_header(cls, filename):
        """ Build an ESRIRasterMetadata object from an ESRI header file """
        with open(filename, "r") as header_file:
            columns = int(header_file.readline().split()[1])
            rows = int(header_file.readline().split()[1])
            xllcorner = float(header_file.readline().split()[1])
            yllcorner = float(header_file.readline().split()[1])
            cell_size = float(header_file.readline().split()[1])
            no_data_value = int(header_file.readline().split()[1])

        lower_left_corner = Site(xllcorner, yllcorner)
        grid = Grid(rows, columns, no_data_value)
        return cls(cell_size, grid, lower_left_corner)
        
    @classmethod
    def load_hazard_iml(cls, filename):
        """ Build an ESRIRasterMetadata object from an hazard IML file """
        with open(filename, "r") as header_file:
            header_file.readline() # Skip one line
            tokens = header_file.readline().split()
            print tokens
            # [78 36  27.225  39.825  0.05]
            rows = int(tokens[1])
            xllcorner = float(tokens[2])
            yllcorner = float(tokens[3])
            columns = int(tokens[0].replace("[", ""))
            cell_size = float(tokens[4].replace("]", ""))

        lower_left_corner = Site(xllcorner, yllcorner)
        grid = Grid(rows, columns, 0)
        return cls(cell_size, grid, lower_left_corner)

    def _latitude_to_row(self, latitude):
        """Calculate row from latitude value."""
        latitude_offset = math.fabs(latitude - self.lower_left_corner.latitude)
        print "lat offset = %s" % latitude_offset
        return int(self.grid.rows - (latitude_offset / self.cell_size)) + 1

    def _longitude_to_column(self, longitude):
        """Calculate column from longitude value."""
        longitude_offset = longitude - self.lower_left_corner.longitude
        print "long offset = %s" % longitude_offset
        return int((longitude_offset / self.cell_size) + 1)

    def point_at(self, site):
        """Translates a site into a matrix bidimensional point."""
        print "%s, %s" % (site.latitude, site.longitude)
        row = self._latitude_to_row(site.latitude)
        column = self._longitude_to_column(site.longitude)
        result = Point(row, column)
        print "%s, %s" % (row, column)
        self.grid.check_row(result)
        self.grid.check_column(result)
        return result
