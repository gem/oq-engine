import os
import unittest

import numpy as np
from osgeo import gdal

from openquake.sep.utils import make_local_relief_raster
from openquake.sep.calculators import calc_newmark_soil_slide_event_set


class TestNewmarkCalculators(unittest.TestCase):
    def setUp(self):
        pass

