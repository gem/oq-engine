#!/usr/bin/env python
# encoding: utf-8
"""
reader.py

Created by Joshua McKenty on 2010-07-30.
Copyright (c) 2010 __MyCompanyName__. All rights reserved.
"""

import sys
import os
import unittest


class BaseExposureReader:
    """Base class for reading exposure data from file formats"""
	def __init__(self):
		pass

class ESRIBinaryFileExposureReader(BaseExposureReader):
    """Parses and loads ESRI formatted exposure data from files"""
    def __init__(self, filename, exposure_definition):
        super(ESRIBinaryFileExposureReader, self).__init__()
        self.filename = filename
        self.definition = exposure_definition
        self.exposure_file = file(filename)
    
    def readAt(self, site):
        point = self.definition.point_at(site)
        position = self.position_of(point)
        self.exposure_file.seek(position)
        return self.exposure_file.read(4)
        
    def position_of(self, point):
        rows_offset = (point.row - 1) * self.definition.columns
        rows_offset_in_bytes = rows_offset * 4 # All points are doubles
        columns_offset_in_bytes = (point.column - 1) * 4
        return rows_offset_in_bytes + columns_offset_in_bytes
        