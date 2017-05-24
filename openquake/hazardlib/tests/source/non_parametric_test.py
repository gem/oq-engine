# The Hazard Library
# Copyright (C) 2013-2017 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import unittest
import numpy
from decimal import Decimal

from openquake.hazardlib.source.non_parametric import \
    NonParametricSeismicSource
from openquake.hazardlib.source.rupture import BaseRupture, \
    NonParametricProbabilisticRupture
from openquake.hazardlib.geo import Point, Polygon
from openquake.hazardlib.geo.surface.planar import PlanarSurface
from openquake.hazardlib.pmf import PMF

from openquake.hazardlib.tests import assert_pickleable


def make_non_parametric_source():
    surf1 = PlanarSurface(
        mesh_spacing=2., strike=0, dip=90,
        top_left=Point(0., -1., 0.), top_right=Point(0., 1., 0.),
        bottom_right=Point(0., 1., 10.), bottom_left=Point(0., -1., 10.)
    )
    surf2 = PlanarSurface(
        mesh_spacing=2., strike=90., dip=90.,
        top_left=Point(-1., 0., 0.), top_right=Point(1., 0., 0.),
        bottom_right=Point(1., 0., 10.), bottom_left=Point(-1., 0., 10.)
    )
    rup1 = BaseRupture(
        mag=5., rake=90., tectonic_region_type='ASC',
        hypocenter=Point(0., 0., 5.), surface=surf1, source_typology=None
    )
    rup2 = BaseRupture(
        mag=6, rake=0, tectonic_region_type='ASC',
        hypocenter=Point(0., 0., 5.), surface=surf2, source_typology=None
    )
    pmf1 = PMF([(Decimal('0.7'), 0), (Decimal('0.3'), 1)])
    pmf2 = PMF([(Decimal('0.7'), 0), (Decimal('0.2'), 1), (Decimal('0.1'), 2)])
    kwargs = {
        'source_id': 'source_id', 'name': 'source name',
        'tectonic_region_type': 'tectonic region',
        'data': [(rup1, pmf1), (rup2, pmf2)]
    }
    npss = NonParametricSeismicSource(**kwargs)
    assert_pickleable(npss)
    return npss, kwargs


class NonParametricSourceTestCase(unittest.TestCase):
    def make_non_parametric_source(self):
        source, kwargs = make_non_parametric_source()
        for key in kwargs:
            self.assertIs(getattr(source, key), kwargs[key])

        return source, kwargs

    def test_creation(self):
        self.make_non_parametric_source()

    def test_get_rupture_enclosing_polygon(self):
        source, _ = self.make_non_parametric_source()

        poly = source.get_rupture_enclosing_polygon(dilation=0)
        expected_poly = Polygon(
            [Point(-1, -1), Point(-1, 1), Point(1, 1), Point(1, -1)]
        )
        numpy.testing.assert_equal(poly.lons, expected_poly.lons)
        numpy.testing.assert_equal(poly.lats, expected_poly.lats)

        poly = source.get_rupture_enclosing_polygon(dilation=200)
        poly._init_polygon2d()
        expected_poly = expected_poly.dilate(200)
        expected_poly._init_polygon2d()

        # we check that the percent difference between the two polygons is
        # almost zero
        # in this case the area of the difference is ~ 8 km**2, with
        # respect to area of the computed polygon (~ 352795 km**2) and the area
        # of the predicted polygon (~ 352803 km**2)
        diff = 100 * poly._polygon2d.\
            symmetric_difference(expected_poly._polygon2d).area
        diff /= expected_poly._polygon2d.area
        self.assertAlmostEqual(diff, 0, places=2)

    def test_iter_ruptures(self):
        source, kwargs = self.make_non_parametric_source()
        for i, rup in enumerate(source.iter_ruptures()):
            exp_rup, exp_pmf = kwargs['data'][i]
            self.assertIsInstance(rup, NonParametricProbabilisticRupture)
            self.assertEqual(rup.mag, exp_rup.mag)
            self.assertEqual(rup.rake, exp_rup.rake)
            self.assertEqual(
                rup.tectonic_region_type, source.tectonic_region_type
            )
            self.assertEqual(rup.hypocenter, exp_rup.hypocenter)
            self.assertIsInstance(rup.surface, PlanarSurface)
            self.assertEqual(
                rup.surface.mesh_spacing, exp_rup.surface.mesh_spacing
            )
            self.assertEqual(rup.surface.strike, exp_rup.surface.strike)
            self.assertEqual(rup.surface.dip, exp_rup.surface.dip)
            self.assertEqual(rup.surface.top_left, exp_rup.surface.top_left)
            self.assertEqual(rup.surface.top_right, exp_rup.surface.top_right)
            self.assertEqual(
                rup.surface.bottom_right, exp_rup.surface.bottom_right
            )
            self.assertEqual(rup.source_typology, exp_rup.source_typology)
            numpy.testing.assert_allclose(
                rup.pmf, [prob for prob, occ in exp_pmf.data])

    def test_count_ruptures(self):
        source, _ = self.make_non_parametric_source()
        self.assertEqual(source.count_ruptures(), 2)
