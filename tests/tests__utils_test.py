# Copyright (c) 2010-2012, GEM Foundation.
#
# NRML is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# NRML is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with NRML.  If not, see <http://www.gnu.org/licenses/>.


import unittest

from openquake.nrmllib import models
import _utils


class DeepEqTestCase(unittest.TestCase):
    """:function:`_utils.deep_eq` is a non-trivial util function used for
    test. We want to make sure it's working properly and not giving false
    positives or negatives.
    """

    POLY = ('POLYGON((-122.0 38.113, -122.114 38.113, -122.57 38.111, '
            '-122.0 38.113))')
    POLY2 = ('POLYGON((-122.1 38.113, -122.114 38.113, -122.57 38.111, '
             '-122.0 38.113))')

    POINT = 'POINT(-122.0 38.113)'

    def setUp(self):
        self.s1 = models.SourceModel(name='s1')
        self.a1 = models.AreaSource(
            name='a1',
            geometry=models.AreaGeometry(wkt=self.POLY))
        self.p1 = models.PointSource(
            name='p1',
            geometry=models.PointGeometry(wkt=self.POINT))
        self.s1.sources = [self.a1, self.p1]

        self.s2 = models.SourceModel(name='s1')
        self.a2 = models.AreaSource(
            name='a1',
            geometry=models.AreaGeometry(wkt=self.POLY))
        self.p2 = models.PointSource(
            name='p1',
            geometry=models.PointGeometry(wkt=self.POINT))
        self.s2.sources = [self.a2, self.p2]

    def test_deep_eq_primitives(self):
        # It should work with primitives also.
        self.assertTrue(*_utils.deep_eq(5, 5.0))
        self.assertTrue(*_utils.deep_eq(5, 5))
        self.assertTrue(*_utils.deep_eq('foo', 'foo'))

        self.assertFalse(*_utils.deep_eq('foo', 'bar'))
        self.assertFalse(*_utils.deep_eq(5, '5'))

    def test_deep_eq_generators(self):
        gen_a = (x for x in range(10))
        gen_b = (x for x in range(10))
        self.assertTrue(*_utils.deep_eq(gen_a, gen_b))

        gen_c = (x for x in range(9))
        self.assertFalse(*_utils.deep_eq(gen_a, gen_c))

    def test_deep_eq_mixed_iterables(self):
        gen = (x for x in range(10))
        xr = xrange(10)
        self.assertTrue(*_utils.deep_eq(gen, xr))

    def test_deep_eq_list_with_generator(self):
        a = [1, 2, 3, (x for x in range(10))]
        b = [1, 2, 3, xrange(10)]

        self.assertTrue(*_utils.deep_eq(a, b))

    def test_deep_eq_dict_with_generator(self):
        a = dict(a=1, b=2, c=(x for x in range(10)))
        b = dict(a=1, b=2, c=xrange(10))

        self.assertTrue(*_utils.deep_eq(a, b))

    def test_deep_eq(self):
        # Typical case.
        self.assertTrue(*_utils.deep_eq(self.s1, self.s2))

    def test_deep_eq_mixed_up_types(self):
        # Here, we specify the wrong type of geometry (area geom for a point)
        self.p2.geometry = models.AreaGeometry(wkt=self.POINT)

        self.assertFalse(*_utils.deep_eq(self.s1, self.s2))

    def test_deep_eq_neq(self):
        # Test with different polygon geometries nested inside of source model
        # objects.
        self.a2.geometry = models.AreaGeometry(wkt=self.POLY2)

        self.assertFalse(*_utils.deep_eq(self.s1, self.s2))
