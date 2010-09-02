# vim: tabstop=4 shiftwidth=4 softtabstop=4

import os
import unittest
import tempfile

from opengem import shapes

from opengem import flags
FLAGS = flags.FLAGS


POLYGON_WKT = 'POLYGON ((10.0000000000000000 100.0000000000000000, 100.0000000000000000 100.0000000000000000, 100.0000000000000000 10.0000000000000000, 10.0000000000000000 10.0000000000000000, 10.0000000000000000 100.0000000000000000))'


INSIDE = [(50, 50),
          (11, 11),
          (99, 99)]


OUTSIDE = [(50, 9),
           (9, 50),
           (9, 9),
           (101, 50),
           (50, 101),
           (101, 101)]

class SiteTestCase(unittest.TestCase):
    
    def test_sites_can_be_keys(self):
        """ Site objects can be dictionary keys,
        So must hash reliably."""
        lat = 10.5
        lon = -49.5
        first_site = shapes.Site(lon, lat)
        second_site = shapes.Site(lon, lat)
        sites = {}
        sites[first_site] = "one"
        sites[second_site] = "two"
        self.assertEqual(first_site, second_site)
        self.assertEqual(sites[first_site], "one")
        self.assertEqual(sites[second_site], "two")

    def test_sites_have_geo_accessors(self):    
        lat = 10.5
        lon = -49.5
        first_site = shapes.Site(lon, lat)
        self.assertEqual(first_site.latitude, lat)
        self.assertEqual(first_site.longitude, lon)
    
    def test_site_precision_matters(self):
        FLAGS.distance_precision = 11
        lat = 10.5
        lon = -49.5
        first_site = shapes.Site(lon, lat)
        lat += 0.0000001
        lon += 0.0000001
        second_site = shapes.Site(lon, lat) 
        self.assertEqual(first_site, second_site)
        FLAGS.distance_precision = 12
        self.assertNotEqual(first_site, second_site)
    

class RegionTestCase(unittest.TestCase):
    def _check_match(self, constraint):
        for point in INSIDE:
            self.assert_(constraint.match(point),
                         'did not match inside: %s' % str(point))

        for point in OUTSIDE:
            self.assert_(not constraint.match(point),
                         'matched outside: %s' % str(point))

    def test_from_file(self):
        fd, path = tempfile.mkstemp(suffix='.wkt')
        f = open(path, 'w')
        f.write(POLYGON_WKT)
        f.close()
        
        try:
            constraint = shapes.RegionConstraint.from_file(path)
            self._check_match(constraint)
        finally:
            os.unlink(path)

    def test_from_coordinates(self):
        constraint = shapes.RegionConstraint.from_coordinates(
                [(10, 100), (100, 100), (100, 10), (10, 10)])
        self._check_match(constraint)

    def test_from_simple(self):
        constraint = shapes.RegionConstraint.from_simple((10, 10), (100, 100))
        self._check_match(constraint)
        
    def test_bounding_box(self):
        switzerland = shapes.Region.from_coordinates(
            [(10, 100), (100, 100), (100, 10), (10, 10)])

