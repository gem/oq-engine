#!/usr/bin/env python
# encoding: utf-8
"""
esri.py

Created by Joshua McKenty on 2010-08-01.
"""


class Grid:
    """ESRIGrid format as per http://en.wikipedia.org/wiki/ESRI_grid"""
    def __init__(self, rows, columns, no_data_value=9999):
        self.columns = columns
        self.rows = rows
        self.no_data_value = no_data_value

    def is_no_data_value(self, val):
        return val == self.no_data_value
        
    def check_column(self, point):
        if (self.columns < point.column or point.column < 1):
            raise Exception("Point is not on the Grid")
            
    def check_row(self, point):
        if (self.rows < point.row or point.row < 1):
            raise Exception("Point is not on the Grid")

class Point:
    """Simple (trivial) point class"""
    def __init__(self, row, column):
        self.column = column
        self.row = row

class Site:
    """Site has lat and long"""
    def __init__(self, latitude, longitude):
        self.latitude = latitude
        self.longitude = longitude