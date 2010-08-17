# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
Tests of the supported GEM output formats.
Goals of this test suite should be to test valid and invalid input,
validate all capabilities of the formats (e.g., coordinate and projection),
and (eventually) test performance of various serializers.
"""

import subprocess
import os
import unittest

from opengem import grid
from opengem.output import geotiff


class OutputTestCase(unittest.TestCase):
    """Test all our output file formats, generally against sample content"""
    def test_geotiff_output(self):
        """Generate a geotiff file with a smiley face."""
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        path = os.path.join(data_dir, "test.tiff")
        image_grid = grid.Grid(ncols=320, nrows=320, 
                        xllcorner=123.25, yllcorner=48.35, cellsize=0.1)
        gwriter = geotiff.GeoTiffFile(path, image_grid)
        for xpoint in range(0, 320):
            for ypoint in range(0, 320):
                gwriter.write((xpoint, ypoint), int(xpoint*254/320))
        gwriter.close()
        comp_path = os.path.join(data_dir, "test.tiff")
        retval = subprocess.call(["tiffcmp", "-t", path, comp_path], 
            stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
        self.assertTrue(retval == 0)