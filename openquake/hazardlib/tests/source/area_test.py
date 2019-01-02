# The Hazard Library
# Copyright (C) 2012-2018 GEM Foundation
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

from openquake.hazardlib.const import TRT
from openquake.hazardlib.scalerel.peer import PeerMSR
from openquake.hazardlib.mfd import TruncatedGRMFD, EvenlyDiscretizedMFD
from openquake.hazardlib.geo import Point, Polygon, NodalPlane
from openquake.hazardlib.pmf import PMF
from openquake.hazardlib.tom import PoissonTOM
from openquake.hazardlib.source.area import AreaSource
from openquake.hazardlib.tests import assert_pickleable


def make_area_source(polygon, discretization, **kwargs):
    default_arguments = {
        'source_id': 'source_id', 'name': 'area source name',
        'tectonic_region_type': TRT.VOLCANIC,
        'mfd': TruncatedGRMFD(a_val=3, b_val=1, min_mag=5,
                              max_mag=7, bin_width=1),
        'nodal_plane_distribution': PMF([(1, NodalPlane(1, 2, 3))]),
        'hypocenter_distribution': PMF([(0.5, 4.0), (0.5, 8.0)]),
        'upper_seismogenic_depth': 1.3,
        'lower_seismogenic_depth': 10.0,
        'magnitude_scaling_relationship': PeerMSR(),
        'rupture_aspect_ratio': 1.333,
        'polygon': polygon,
        'area_discretization': discretization,
        'rupture_mesh_spacing': 12.33,
        'temporal_occurrence_model': PoissonTOM(50.)
    }
    default_arguments.update(kwargs)
    kwargs = default_arguments
    source = AreaSource(**kwargs)
    return source


class AreaSourceIterRupturesTestCase(unittest.TestCase):
    def make_area_source(self, polygon, discretization, **kwargs):
        source = make_area_source(polygon, discretization, **kwargs)
        for key in kwargs:
            self.assertIs(getattr(source, key), kwargs[key])
        assert_pickleable(source)
        return source

    def test_implied_point_sources(self):
        source = self.make_area_source(Polygon([Point(-2, -2), Point(0, -2),
                                                Point(0, 0), Point(-2, 0)]),
                                       discretization=66.7,
                                       rupture_mesh_spacing=5)
        ruptures = list(source.iter_ruptures())
        self.assertEqual(
            len(ruptures), source.count_ruptures())  # 9 * 2 ruptures
        # resulting 3x3 mesh has points in these coordinates:
        lons = [-1.4, -0.8, -0.2]
        lats = [-0.6, -1.2, -1.8]
        depths = [4.0, 8.0]
        ruptures_iter = iter(ruptures)
        for lat in lats:
            for lon in lons:
                r1 = next(ruptures_iter)
                r2 = next(ruptures_iter)
                r3 = next(ruptures_iter)
                r4 = next(ruptures_iter)
                for iloc, rupture in enumerate([r1, r2]):
                    self.assertAlmostEqual(rupture.hypocenter.longitude,
                                           lon, delta=1e-3)
                    self.assertAlmostEqual(rupture.hypocenter.latitude,
                                           lat, delta=1e-3)
                    self.assertAlmostEqual(rupture.hypocenter.depth,
                                           depths[iloc], delta=1e-3)
                self.assertEqual(r1.mag, 5.5)
                self.assertEqual(r2.mag, 5.5)
                self.assertEqual(r3.mag, 6.5)
                self.assertEqual(r4.mag, 6.5)
        self.assertEqual(len(ruptures), 9 * 4)

    def test_occurrence_rate_rescaling(self):
        mfd = EvenlyDiscretizedMFD(min_mag=4, bin_width=1,
                                   occurrence_rates=[3])
        polygon = Polygon([Point(0, 0), Point(0, -0.2248),
                           Point(-0.2248, -0.2248), Point(-0.2248, 0)])
        source = self.make_area_source(polygon, discretization=10, mfd=mfd)
        self.assertIs(source.mfd, mfd)
        ruptures = list(source.iter_ruptures())
        self.assertEqual(len(ruptures), 8)
        for rupture in ruptures:
            self.assertNotEqual(rupture.occurrence_rate, 3)
            self.assertEqual(rupture.occurrence_rate, 3.0 / 8.0)
