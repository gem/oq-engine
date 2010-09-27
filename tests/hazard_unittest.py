"""
This is a basic set of tests for hazard engine.

"""

import os
import unittest

import numpy.core.multiarray as ncm
from shapely import geometry

from opengem import logs
from opengem.hazard import engine
from opengem import test
from opengem import shapes

log = logs.HAZARD_LOG

data_dir = os.path.join(os.path.dirname(__file__), 'data')


class HazardEngineWrapperTestCase(unittest.TestCase):
    """Basic unit tests of the Hazard Engine"""
    
    def test_hazard_map_generation(self):
        # get grid of columns and rows from region of coordinates
        hazard_map_region = shapes.Region.from_coordinates(
            [(10, 20), (20, 20), (20, 10), (10, 10)])
        hazard_map_region.cell_size = 1.0
        
