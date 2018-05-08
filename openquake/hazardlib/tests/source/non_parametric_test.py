# The Hazard Library
# Copyright (C) 2013-2018 GEM Foundation
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

from openquake.hazardlib.source.non_parametric import \
    NonParametricSeismicSource
from openquake.hazardlib.source.rupture import BaseRupture, \
    NonParametricProbabilisticRupture
from openquake.hazardlib.geo import Point
from openquake.hazardlib.geo.surface.planar import PlanarSurface
from openquake.hazardlib.pmf import PMF

from openquake.hazardlib.tests import assert_pickleable


def make_non_parametric_source():
    surf1 = PlanarSurface(
        strike=0, dip=90,
        top_left=Point(0., -1., 0.), top_right=Point(0., 1., 0.),
        bottom_right=Point(0., 1., 10.), bottom_left=Point(0., -1., 10.)
    )
    surf2 = PlanarSurface(
        strike=90., dip=90.,
        top_left=Point(-1., 0., 0.), top_right=Point(1., 0., 0.),
        bottom_right=Point(1., 0., 10.), bottom_left=Point(-1., 0., 10.)
    )
    rup1 = BaseRupture(
        mag=5., rake=90., tectonic_region_type='ASC',
        hypocenter=Point(0., 0., 5.), surface=surf1)
    rup2 = BaseRupture(
        mag=6, rake=0, tectonic_region_type='ASC',
        hypocenter=Point(0., 0., 5.), surface=surf2)
    pmf1 = PMF([(0.7, 0), (0.3, 1)])
    pmf2 = PMF([(0.7, 0), (0.2, 1), (0.1, 2)])
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
            self.assertEqual(rup.surface.strike, exp_rup.surface.strike)
            self.assertEqual(rup.surface.dip, exp_rup.surface.dip)
            self.assertEqual(rup.surface.top_left, exp_rup.surface.top_left)
            self.assertEqual(rup.surface.top_right, exp_rup.surface.top_right)
            self.assertEqual(
                rup.surface.bottom_right, exp_rup.surface.bottom_right)
            numpy.testing.assert_allclose(
                rup.pmf, [prob for prob, occ in exp_pmf.data])

    def test_count_ruptures(self):
        source, _ = self.make_non_parametric_source()
        self.assertEqual(source.count_ruptures(), 2)
