from __future__ import division
# The Hazard Library
# Copyright (C) 2012-2017 GEM Foundation
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

from openquake.hazardlib.const import TRT
from openquake.hazardlib.scalerel.peer import PeerMSR
from openquake.hazardlib.mfd import TruncatedGRMFD, EvenlyDiscretizedMFD
from openquake.hazardlib.geo import Point, Polygon, NodalPlane
from openquake.hazardlib.pmf import PMF
from openquake.hazardlib.tom import PoissonTOM
from openquake.hazardlib.source.area import AreaSource

from openquake.hazardlib.tests.source.base_test import \
    SeismicSourceFilterSitesTestCase
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
                    self.assertEqual(rupture.surface.mesh_spacing, 5)
                    self.assertIs(rupture.source_typology, AreaSource)
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


class AreaSourceRupEncPolyTestCase(unittest.TestCase):
    def test_no_dilation(self):
        source = make_area_source(Polygon([Point(-4, -4), Point(-5, -4),
                                           Point(-4, -5)]),
                                  discretization=100)
        polygon = source.get_rupture_enclosing_polygon()
        elons = [
            -3.8843265, -3.8841675, -3.8847229, -3.8863892, -3.8891507,
            -3.8929806, -3.8978421, -3.9036884, -3.9104632, -3.9181013,
            -3.9265289, -3.9356649, -3.9454212, -3.9557038, -3.9664135,
            -3.9774470, -3.9886980, -4.0000580, -4.0114174, -4.0226667,
            -4.0336974, -4.0444032, -4.0546808, -4.0644312, -4.0735603,
            -4.0819801, -5.0819794, -5.0895794, -5.0963177, -5.1021293,
            -5.1069586, -5.1107589, -5.1134939, -5.1151373, -5.1156733,
            -5.1150967, -5.1134133, -5.1106391, -5.1068010, -5.1019359,
            -5.0960906, -5.0893213, -5.0816932, -5.0732797, -5.0641616,
            -5.0544266, -5.0441683, -5.0334855, -5.0224807, -5.0112597,
            -4.9999306, -4.0000694, -3.9887278, -3.9774948, -3.9664787,
            -3.9557855, -3.9455184, -3.9357761, -3.9266527, -3.9182361,
            -3.9106073, -3.9038400, -3.8979993, -3.8931415, -3.8893136,
            -3.8865525, -3.8848847
        ]
        elats = [
            -3.9999909, -4.9999908, -5.0113054, -5.0225111, -5.0334999,
            -5.0441660, -5.0544065, -5.0641226, -5.0732208, -5.0816133,
            -5.0892192, -5.0959651, -5.1017861, -5.1066260, -5.1104381,
            -5.1131856, -5.1148422, -5.1153917, -5.1148289, -5.1131593,
            -5.1103988, -5.1065743, -5.1017224, -5.0958901, -5.0891335,
            -5.0815178, -4.0814048, -4.0730023, -4.0638977, -4.0541785,
            -4.0439382, -4.0332754, -4.0222926, -4.0110954, -3.9997916,
            -3.9884899, -3.9772990, -3.9663264, -3.9556777, -3.9454554,
            -3.9357577, -3.9266778, -3.9183031, -3.9107141, -3.9039838,
            -3.8981768, -3.8933490, -3.8895469, -3.8868069, -3.8851554,
            -3.8846083, -3.8846083, -3.8851566, -3.8868117, -3.8895577,
            -3.8933680, -3.8982061, -3.9040252, -3.9107693, -3.9183735,
            -3.9267644, -3.9358611, -3.9455761, -3.9558157, -3.9664812,
            -3.9774699, -3.9886758
        ]
        numpy.testing.assert_allclose(polygon.lons, elons)
        numpy.testing.assert_allclose(polygon.lats, elats)

    def test_dilated(self):
        source = make_area_source(Polygon([Point(4, 6), Point(5, 6),
                                           Point(4, 5)]),
                                  discretization=100)
        polygon = source.get_rupture_enclosing_polygon(dilation=5)
        elons = [
            3.8387562, 3.8395259, 3.8418396, 3.8456751, 3.8509956, 3.8577500,
            3.8658734, 3.8752878, 3.8859026, 3.8976158, 3.9103145, 3.9238767,
            3.9381718, 3.9530621, 3.9684044, 3.9840509, 3.9998509, 5.0001491,
            5.0159419, 5.0315815, 5.0469172, 5.0618016, 5.0760915, 5.0896495,
            5.1023453, 5.1140566, 5.1246711, 5.1340866, 5.1422127, 5.1489714,
            5.1542977, 5.1581407, 5.1604635, 5.1612438, 5.1604744, 5.1581627,
            5.1543311, 5.1490166, 5.1422703, 5.1341571, 5.1247551, 5.1141547,
            4.1141530, 4.1024651, 4.0897882, 4.0762448, 4.0619656, 4.0470884,
            4.0317568, 4.0161187, 4.0003251, 3.9845284, 3.9688809, 3.9535336,
            3.9386348, 3.9243281, 3.9107516, 3.8980364, 3.8863052, 3.8756714,
            3.8662375, 3.8580948, 3.8513218, 3.8459842, 3.8421334, 3.8398068,
            3.8390269
        ]
        elats = [
            5.9999784, 6.0156881, 6.0312472, 6.0465059, 6.0613173, 6.0755391,
            6.0890342, 6.1016728, 6.1133333, 6.1239034, 6.1332813, 6.1413768,
            6.1481120, 6.1534219, 6.1572555, 6.1595758, 6.1603605, 6.1603605,
            6.1595765, 6.1572583, 6.1534281, 6.1481229, 6.1413937, 6.1333052,
            6.1239352, 6.1133738, 6.1017226, 6.0890937, 6.0756085, 6.0613967,
            6.0465949, 6.0313455, 6.0157950, 6.0000929, 5.9843902, 5.9688377,
            5.9535850, 5.9387786, 5.9245607, 5.9110681, 5.8984302, 5.8867686,
            4.8869567, 4.8763401, 4.8669175, 4.8587797, 4.8520053, 4.8466598,
            4.8427945, 4.8404470, 4.8396398, 4.8403806, 4.8426625, 4.8464633,
            4.8517463, 4.8584606, 4.8665414, 4.8759108, 4.8864782, 4.8981417,
            4.9107887, 4.9242972, 4.9385367, 4.9533698, 4.9686533, 4.9842397,
            4.9999784
        ]
        numpy.testing.assert_allclose(polygon.lons, elons)
        numpy.testing.assert_allclose(polygon.lats, elats)


class AreaSourceFilterSitesBySourceTestCase(SeismicSourceFilterSitesTestCase):
    # test that area source uses base implementation of source-site filtering
    def setUp(self):
        super(AreaSourceFilterSitesBySourceTestCase, self).setUp()
        mfd = TruncatedGRMFD(a_val=3, b_val=1, min_mag=1,
                             max_mag=2, bin_width=1)
        self.source = make_area_source(self.POLYGON, discretization=1,
                                       mfd=mfd)
