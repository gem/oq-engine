# vim: tabstop=4 shiftwidth=4 softtabstop=4

import os
import unittest

from opengem.output import geotiff

class OutputTestCase(unittest.TestCase):
    def test_geotiff_output(self):
        """Generate a geotiff file with a smiley face."""
        gwriter = geotiff.GeoTiffFile("test.tiff", 320, 320, 123.25, 48.35, 0.1)
        gwriter.write((10, 10), 254)
        gwriter.write((20, 20), 128)
        gwriter.close()