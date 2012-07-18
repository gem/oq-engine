# nhlib: A New Hazard Library
# Copyright (C) 2012 GEM Foundation
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

from nhlib.calc import disagg
from nhlib.calc import filters
from nhlib.tom import PoissonTOM
from nhlib.geo import Point, Mesh
from nhlib.site import Site


class _BaseDisaggTestCase(unittest.TestCase):
    class FakeSurface(object):
        def __init__(self, distance, lon, lat):
            self.distance = distance
            self.lon = lon
            self.lat = lat
        def get_joyner_boore_distance(self, sites):
            assert len(sites) == 1
            return numpy.array([self.distance], float)
        def get_closest_points(self, sites):
            assert len(sites) == 1
            return Mesh(numpy.array([self.lon], float),
                        numpy.array([self.lat], float),
                        depths=None)

    class FakeRupture(object):
        def __init__(self, mag, probability, distance, lon, lat):
            self.mag = mag
            self.probability = probability
            self.surface = _BaseDisaggTestCase.FakeSurface(distance, lon, lat)
        def get_probability_one_occurrence(self):
            return self.probability

    class FakeSource(object):
        def __init__(self, ruptures, tom, tectonic_region_type):
            self.ruptures = ruptures
            self.tom = tom
            self.tectonic_region_type = tectonic_region_type
        def iter_ruptures(self, tom):
            assert tom is self.tom
            return iter(self.ruptures)

    class FakeGSIM(object):
        def __init__(self, iml, imt, truncation_level, n_epsilons,
                     disaggregated_poes):
            self.disaggregated_poes = disaggregated_poes
            self.n_epsilons = n_epsilons
            self.iml = iml
            self.imt = imt
            self.truncation_level = truncation_level
            self.dists = object()
        def make_contexts(self, sites, rupture):
            return (sites, rupture, self.dists)
        def disaggregate_poe(self, sctx, rctx, dctx, imt, iml,
                             truncation_level, n_epsilons):
            assert truncation_level is self.truncation_level
            assert dctx is self.dists
            assert imt is self.imt
            assert iml is self.iml
            assert n_epsilons is self.n_epsilons
            assert len(sctx) == 1
            return numpy.array([self.disaggregated_poes[rctx]])

    def setUp(self):
        self.ruptures_and_poes1 = [
            ([0, 0, 0], self.FakeRupture(5, 0.1, 3, 22, 44)),
            ([0.1, 0.2, 0.1], self.FakeRupture(5, 0.2, 11, 22, 44)),
            ([0, 0, 0.3], self.FakeRupture(5, 0.01, 12, 22, 45)),
            ([0, 0.05, 0.001], self.FakeRupture(5, 0.33, 13, 22, 45)),
            ([0, 0, 0], self.FakeRupture(9, 0.4, 14, 21, 44)),
            ([0, 0, 0.02], self.FakeRupture(5, 0.05, 11, 21, 44)),
            ([0.04, 0.1, 0.04], self.FakeRupture(5, 0.53, 11, 21, 45)),
            ([0.2, 0.3, 0.2], self.FakeRupture(5, 0.066, 10, 21, 45)),
            ([0.3, 0.4, 0.3], self.FakeRupture(6, 0.1, 12, 22, 44)),
            ([0, 0, 0.1], self.FakeRupture(6, 0.1, 12, 21, 44)),
            ([0, 0, 0], self.FakeRupture(6, 0.1, 11, 22, 45)),
        ]
        self.ruptures_and_poes2 = [
            ([0, 0.1, 0.04], self.FakeRupture(8, 0.04, 5, 11, 45)),
            ([0.1, 0.5, 0.1], self.FakeRupture(7, 0.03, 5, 11, 46))
        ]
        self.tom = PoissonTOM(time_span=10)
        self.source1 = self.FakeSource(
            [rupture for poes, rupture in self.ruptures_and_poes1],
            self.tom, 'trt1'
        )
        self.source2 = self.FakeSource(
            [rupture for poes, rupture in self.ruptures_and_poes2],
            self.tom, 'trt2'
        )
        self.disagreggated_poes = dict(
            (rupture, poes)
            for (poes, rupture) in self.ruptures_and_poes1 \
                                   + self.ruptures_and_poes2
        )
        self.site = Site(Point(0, 0), 2, False, 4, 5)


class CollectBinsDataTestCase(_BaseDisaggTestCase):
    def setUp(self):
        super(CollectBinsDataTestCase, self).setUp()
        self.iml, self.imt, self.truncation_level = object(), object(), \
                                                    object()
        gsim = self.FakeGSIM(self.iml, self.imt, self.truncation_level,
                             n_epsilons=3,
                             disaggregated_poes=self.disagreggated_poes)
        self.gsims = {'trt1': gsim, 'trt2': gsim}
        self.sources = [self.source1, self.source2]

    def test_no_filters(self):
        mags, dists, lons, \
        lats, joint_probs, tect_reg_types = disagg._collect_bins_data(
            self.sources, self.site, self.iml, self.imt, self.gsims,
            self.tom, self.truncation_level, n_epsilons=3,
            source_site_filter=filters.source_site_noop_filter,
            rupture_site_filter=filters.rupture_site_noop_filter
        )

        aae = numpy.testing.assert_array_equal
        aaae = numpy.testing.assert_array_almost_equal

        aae(mags, [5,  5,  5,  5,  9,  5,  5,  5,  6,  6,  6,  8,  7])
        aae(dists, [3, 11, 12, 13, 14, 11, 11, 10, 12, 12, 11, 5, 5])
        aae(lons, [22, 22, 22, 22, 21, 21, 21, 21, 22, 21, 22, 11, 11])
        aae(lats, [44, 44, 45, 45, 44, 44, 45, 45, 44, 44, 45, 45, 46])
        aaae(joint_probs, [[0., 0., 0.],
                           [0.02, 0.04, 0.02],
                           [0., 0., 0.003],
                           [0., 0.0165, 0.00033],
                           [0., 0., 0.],
                           [0., 0., 0.001],
                           [0.0212, 0.053, 0.0212],
                           [0.0132, 0.0198, 0.0132],
                           [0.03, 0.04, 0.03],
                           [0., 0., 0.01],
                           [0., 0., 0.],
                           [0., 0.004, 0.0016],
                           [0.003, 0.015, 0.003]])
        self.assertEqual(tect_reg_types, set(('trt1', 'trt2')))

    def test_filters(self):
        def source_site_filter(sources_sites):
            for source, sites in sources_sites:
                if source is self.source2:
                    continue
                yield source, sites
        def rupture_site_filter(rupture_sites):
            for rupture, sites in rupture_sites:
                if rupture.mag < 6:
                    continue
                yield rupture, sites

        mags, dists, lons, \
        lats, joint_probs, tect_reg_types = disagg._collect_bins_data(
            self.sources, self.site, self.iml, self.imt, self.gsims,
            self.tom, self.truncation_level, n_epsilons=3,
            source_site_filter=source_site_filter,
            rupture_site_filter=rupture_site_filter
        )

        aae = numpy.testing.assert_array_equal
        aaae = numpy.testing.assert_array_almost_equal

        aae(mags, [9, 6, 6, 6])
        aae(dists, [14, 12, 12, 11])
        aae(lons, [21, 22, 21, 22])
        aae(lats, [44, 44, 44, 45])
        aaae(joint_probs, [[0., 0., 0.],
                           [0.03, 0.04, 0.03],
                           [0., 0., 0.01],
                           [0., 0., 0.]])
        self.assertEqual(tect_reg_types, set(('trt1', )))


class DefineBinsTestCase(unittest.TestCase):
    def test(self):
        mags = numpy.array([4.4, 5, 3.2, 7, 5.9])
        dists = numpy.array([4, 1.2, 3.5, 52.1, 17])
        lats = numpy.array([-25, -10, 0.6, -20, -15])
        lons = numpy.array([179, -179, 176.4, -179.55, 180])
        joint_probs = None
        tect_region_types = set(['foo', 'bar', 'baz'])

        bins_data = mags, dists, lons, lats, joint_probs, tect_region_types

        mag_bins, dist_bins, lon_bins, lat_bins, \
        eps_bins, trt_bins = disagg._define_bins(
            bins_data, mag_bin_width=1, dist_bin_width=4.2,
            coord_bin_width=1.2, truncation_level=1, n_epsilons=5
        )

        aae = numpy.testing.assert_array_equal
        aaae = numpy.testing.assert_array_almost_equal
        aae(mag_bins, [3, 4, 5, 6])
        aaae(dist_bins, [0., 4.2, 8.4, 12.6, 16.8, 21., 25.2, 29.4, 33.6,
                         37.8, 42., 46.2, 50.4])
        aaae(lon_bins, [176.4, 177.91578947, 179.43157895, -179.05263158, -178.8])
        aaae(lat_bins, [-25.2, -24., -22.8, -21.6, -20.4, -19.2, -18., -16.8,
                        -15.6, -14.4, -13.2, -12., -10.8, -9.6, -8.4, -7.2,
                        -6., -4.8, -3.6, -2.4, -1.2, 0.])
        aae(eps_bins, [-1., -0.5, 0. , 0.5, 1. ])
        self.assertIsInstance(trt_bins, list)
        self.assertEqual(set(trt_bins), tect_region_types)
