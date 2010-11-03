# vim: tabstop=4 shiftwidth=4 softtabstop=4

import os
import unittest
import tempfile

from opengem import shapes

from opengem import flags
FLAGS = flags.FLAGS


POLYGON_WKT = 'POLYGON ((10.0000000000000000 100.0000000000000000,\
 100.0000000000000000 100.0000000000000000, 100.0000000000000000\
 10.0000000000000000, 10.0000000000000000 10.0000000000000000,\
 10.0000000000000000 100.0000000000000000))'


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
        # BOTH will now be "two"! This is correct
        
        self.assertEqual(first_site, second_site)
        self.assertEqual(sites[first_site], "two")
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
        with open(path, 'w') as wkt_file:
            wkt_file.write(POLYGON_WKT)
        
        try:
            constraint = shapes.RegionConstraint.from_file(path)
            self._check_match(constraint)
        finally:
            os.unlink(path)

    def test_from_coordinates(self):
        constraint = shapes.RegionConstraint.from_coordinates(
                [(10.0, 100.0), (100.0, 100.0), (100.0, 10.0), (10.0, 10.0)])
        self._check_match(constraint)

    def test_from_simple(self):
        constraint = shapes.RegionConstraint.from_simple(
            (10.0, 10.0), (100.0, 100.0))
        self._check_match(constraint)
        
    def test_bounding_box(self):
        switzerland = shapes.Region.from_coordinates(
            [(10.0, 100.0), (100.0, 100.0), (100.0, 10.0), (10.0, 10.0)])


class ShapesTestCase(unittest.TestCase):
    
    def test_equals_when_have_the_same_values(self):
        curve1 = shapes.Curve([(0.1, 1.0), (0.2, 2.0)])
        curve2 = shapes.Curve([(0.1, 1.0), (0.2, 2.0)])
        curve3 = shapes.Curve([(0.1, 1.0), (0.2, 5.0)])
        curve4 = shapes.Curve([(0.1, (1.0, 0.3)), (0.2, (2.0, 0.3))])
        curve5 = shapes.Curve([(0.1, (1.0, 0.3)), (0.2, (2.0, 0.3))])
        curve6 = shapes.Curve([(0.1, (1.0, 0.5)), (0.2, (2.0, 0.3))])
        
        self.assertEquals(curve1, curve2)
        self.assertNotEquals(curve1, curve3)
        self.assertNotEquals(curve1, curve4)
        self.assertNotEquals(curve3, curve4)
        self.assertEquals(curve4, curve5)
        self.assertNotEquals(curve5, curve6)
    
    def test_can_construct_a_curve_from_dict(self):
        curve1 = shapes.Curve([(0.1, 1.0), (0.2, 2.0)])
        curve2 = shapes.Curve.from_dict({"0.1": 1.0, "0.2": 2.0})
        curve3 = shapes.Curve([(0.1, (1.0, 0.3)), (0.2, (2.0, 0.3))])
        curve4 = shapes.Curve.from_dict({"0.1": (1.0, 0.3), "0.2": (2.0, 0.3)})
        
        # keys are already floats
        curve5 = shapes.Curve.from_dict({0.1: (1.0, 0.3), 0.2: (2.0, 0.3)})
        
        self.assertEquals(curve1, curve2)
        self.assertEquals(curve3, curve4)
        self.assertEquals(curve3, curve5)
    
    def test_can_serialize_in_json(self):
        curve1 = shapes.Curve([(0.1, 1.0), (0.2, 2.0)])
        curve2 = shapes.Curve([(0.1, (1.0, 0.3)), (0.2, (2.0, 0.3))])
        self.assertEquals(curve1, shapes.Curve.from_json(curve1.to_json()))
        self.assertEquals(curve2, shapes.Curve.from_json(curve2.to_json()))

    def test_can_construct_with_unordered_values(self):
        curve = shapes.Curve([(0.5, 1.0), (0.4, 2.0), (0.3, 2.0)])
        
        self.assertEqual(1.0, curve.ordinate_for(0.5))
        self.assertEqual(2.0, curve.ordinate_for(0.4))
        self.assertEqual(2.0, curve.ordinate_for(0.3))