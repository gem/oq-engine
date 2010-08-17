# vim: tabstop=4 shiftwidth=4 softtabstop=4
import sys
sys.path.append("/Users/benwyss/Projects/opengem")
import os
import unittest
import tempfile

from opengem import region


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
            constraint = region.RegionConstraint.from_file(path)
            self._check_match(constraint)
        finally:
            os.unlink(path)

    def test_from_coordinates(self):
        constraint = region.RegionConstraint.from_coordinates(
                [(10, 100), (100, 100), (100, 10), (10, 10)])
        self._check_match(constraint)

    def test_from_simple(self):
        constraint = region.RegionConstraint.from_simple((10, 10), (100, 100))
        self._check_match(constraint)

