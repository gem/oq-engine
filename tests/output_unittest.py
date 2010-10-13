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

from opengem import shapes
from opengem import test
from opengem.output import geotiff


class OutputTestCase(unittest.TestCase):
    """Test all our output file formats, generally against sample content"""
    def test_geotiff_output(self):
        """Generate a geotiff file with a smiley face."""
        path = os.path.join(test.DATA_DIR, "test.tiff")
        switzerland = shapes.Region.from_coordinates(
            [(10.0, 100.0), (100.0, 100.0), (100.0, 10.0), (10.0, 10.0)])
        image_grid = switzerland.grid
        gwriter = geotiff.GeoTiffFile(path, image_grid)
        for xpoint in range(0, 320):
            for ypoint in range(0, 320):
                gwriter.write((xpoint, ypoint), int(xpoint*254/320))
        gwriter.close()
        comp_path = os.path.join(test.DATA_DIR, "test.tiff")
        retval = subprocess.call(["tiffcmp", "-t", path, comp_path], 
            stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
        self.assertTrue(retval == 0)
        # TODO(jmc): Figure out how to validate the geo coordinates as well
        # TODO(jmc): Use validation that supports tiled geotiffs