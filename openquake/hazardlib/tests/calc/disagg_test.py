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
import mock
import unittest
import warnings

import numpy

from openquake.hazardlib.calc import disagg
from openquake.hazardlib.calc import filters
from openquake.hazardlib.tom import PoissonTOM
from openquake.hazardlib.geo import Point, Mesh
from openquake.hazardlib.site import Site
from openquake.hazardlib.gsim.base import ContextMaker


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

        def get_probability_no_exceedance(self, poe):
            return (1 - self.probability) ** poe

    class FakeSource(object):
        def __init__(self, source_id, ruptures, tom, tectonic_region_type):
            self.source_id = source_id
            self.ruptures = ruptures
            self.tom = tom
            self.tectonic_region_type = tectonic_region_type

        def iter_ruptures(self):
            return iter(self.ruptures)

    class FailSource(FakeSource):
        def iter_ruptures(self):
            raise ValueError('Something bad happened')

    class FakeGSIM(object):
        REQUIRES_DISTANCES = set()
        REQUIRES_RUPTURE_PARAMETERS = set()
        REQUIRES_SITES_PARAMETERS = set()

        def __init__(self, iml, imt, truncation_level, n_epsilons,
                     disaggregated_poes):
            self.disaggregated_poes = disaggregated_poes
            self.n_epsilons = n_epsilons
            self.iml = iml
            self.imt = imt
            self.truncation_level = truncation_level
            self.dists = object()

        def disaggregate_poe(self, sctx, rctx, dctx, imt, iml,
                             truncation_level, n_epsilons):
            assert truncation_level is self.truncation_level
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
        self.time_span = 10
        self.tom = PoissonTOM(time_span=10)
        self.source1 = self.FakeSource(
            1, [rupture for poes, rupture in self.ruptures_and_poes1],
            self.tom, 'trt1'
        )
        self.source2 = self.FakeSource(
            2, [rupture for poes, rupture in self.ruptures_and_poes2],
            self.tom, 'trt2'
        )
        self.disagreggated_poes = dict(
            (rupture, poes) for (poes, rupture) in self.ruptures_and_poes1 +
            self.ruptures_and_poes2
        )
        self.site = Site(Point(0, 0), 2, False, 4, 5)

        self.iml, self.imt, self.truncation_level = (
            object(), object(), object())
        gsim = self.FakeGSIM(self.iml, self.imt, self.truncation_level,
                             n_epsilons=3,
                             disaggregated_poes=self.disagreggated_poes)
        self.gsim = gsim
        self.gsims = {'trt1': gsim, 'trt2': gsim}
        self.sources = [self.source1, self.source2]

        self.orig_make_contexts = ContextMaker.make_contexts
        ContextMaker.make_contexts = lambda self, sites, rupture: (
            sites, rupture, None)

    def tearDown(self):
        ContextMaker.make_contexts = self.orig_make_contexts


class CollectBinsDataTestCase(_BaseDisaggTestCase):
    def test_no_filters(self):
        (mags, dists, lons, lats, trts, trt_bins, probs_no_exceed) = \
            disagg._collect_bins_data_old(
                self.sources, self.site, self.imt, self.iml, self.gsims,
                self.truncation_level, n_epsilons=3,
                source_site_filter=filters.source_site_noop_filter)

        aae = numpy.testing.assert_array_equal

        aae(mags, [5, 5, 5, 5, 9, 5, 5, 5, 6, 6, 6, 8, 7])
        aae(dists, [3, 11, 12, 13, 14, 11, 11, 10, 12, 12, 11, 5, 5])
        aae(lons, [22, 22, 22, 22, 21, 21, 21, 21, 22, 21, 22, 11, 11])
        aae(lats, [44, 44, 45, 45, 44, 44, 45, 45, 44, 44, 45, 45, 46])
        aae(trts, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1])

        poe = numpy.array([
            [0, 0, 0],
            [0.1, 0.2, 0.1],
            [0, 0, 0.3],
            [0, 0.05, 0.001],
            [0, 0, 0],
            [0, 0, 0.02],
            [0.04, 0.1, 0.04],
            [0.2, 0.3, 0.2],
            [0.3, 0.4, 0.3],
            [0, 0, 0.1],
            [0, 0, 0],
            [0, 0.1, 0.04],
            [0.1, 0.5, 0.1],
        ])
        p_one_more = numpy.array(
            [0.1, 0.2, 0.01, 0.33, 0.4, 0.05, 0.53, 0.066,
             0.1, 0.1, 0.1, 0.04, 0.03]
        ).reshape(13, 1)
        exp_p_ne = (1 - p_one_more) ** poe
        aae(probs_no_exceed, exp_p_ne)
        self.assertEqual(trt_bins, ['trt1', 'trt2'])


class DigitizeLonsTestCase(unittest.TestCase):

    def setUp(self):
        # First test
        self.lons1 = numpy.array([179.2, 179.6, 179.8, -179.9, -179.7, -179.1])
        self.bins1 = numpy.array([179.0, 179.5, 180.0, -179.5, -179])
        # Second test
        self.lons2 = numpy.array([90.0, 90.3, 90.5, 90.7, 91.3])
        self.bins2 = numpy.array([90.0, 90.5, 91.0, 91.5])

    def test1(self):
        idx = disagg._digitize_lons(self.lons1, self.bins1)
        expected = numpy.array([0, 1, 1, 2, 2, 3], dtype=int)
        numpy.testing.assert_equal(idx, expected)

    def test2(self):
        idx = disagg._digitize_lons(self.lons2, self.bins2)
        expected = numpy.array([0, 0, 1, 1, 2], dtype=int)
        numpy.testing.assert_equal(idx, expected)


class DefineBinsTestCase(unittest.TestCase):
    def test(self):
        mags = numpy.array([4.4, 5, 3.2, 7, 5.9])
        dists = numpy.array([4, 1.2, 3.5, 52.1, 17])
        lats = numpy.array([-25, -10, 0.6, -20, -15])
        lons = numpy.array([179, -179, 176.4, -179.55, 180])
        trts = [0, 1, 2, 2, 1]
        trt_bins = ['foo', 'bar', 'baz']

        # This is ignored by _define_bins, but it is returned by
        # _collect_bins_data so we need to maintain that contract
        probs_no_exceed = None

        bins_data = (mags, dists, lons, lats, trts, trt_bins,
                     probs_no_exceed)

        (mag_bins, dist_bins, lon_bins, lat_bins,  eps_bins, trt_bins_
         ) = disagg._define_bins(
            bins_data, mag_bin_width=1, dist_bin_width=4.2,
            coord_bin_width=1.2, truncation_level=1, n_epsilons=4
        )

        aae = numpy.testing.assert_array_equal
        aaae = numpy.testing.assert_array_almost_equal
        aae(mag_bins, [3, 4, 5, 6, 7])
        aaae(dist_bins, [0., 4.2, 8.4, 12.6, 16.8, 21., 25.2, 29.4, 33.6,
                         37.8, 42., 46.2, 50.4, 54.6])
        aaae(lon_bins, [176.4, 177.6, 178.8, -180., -178.8])
        aaae(lat_bins, [-25.2, -24., -22.8, -21.6, -20.4, -19.2, -18., -16.8,
                        -15.6, -14.4, -13.2, -12., -10.8, -9.6, -8.4, -7.2,
                        -6., -4.8, -3.6, -2.4, -1.2, 0., 1.2])
        aae(eps_bins, [-1., -0.5, 0., 0.5, 1.])
        self.assertIs(trt_bins, trt_bins_)


class ArangeDataInBinsTestCase(unittest.TestCase):
    def test(self):
        mags = numpy.array([5, 5], float)
        dists = numpy.array([6, 6], float)
        lons = numpy.array([19, 19], float)
        lats = numpy.array([41.5, 41.5], float)
        trts = numpy.array([0, 0], int)
        trt_bins = ['trt1', 'trt2']

        probs_one_or_more = numpy.array([0.1] * len(mags)).reshape(2, 1)
        probs_exceed_given_rup = numpy.ones((len(mags), 2)) * 0.1
        probs_no_exceed = (1 - probs_one_or_more) ** probs_exceed_given_rup

        bins_data = (mags, dists, lons, lats, trts, trt_bins,
                     probs_no_exceed)

        mag_bins = numpy.array([4, 6, 7], float)
        dist_bins = numpy.array([0, 4, 8], float)
        lon_bins = numpy.array([18, 20, 21], float)
        lat_bins = numpy.array([40, 41, 42], float)
        eps_bins = numpy.array([-2, 0, 2], float)

        bin_edges = mag_bins, dist_bins, lon_bins, lat_bins, eps_bins, trt_bins

        diss_matrix = disagg._arrange_data_in_bins(bins_data, bin_edges)

        self.assertEqual(diss_matrix.shape, (2, 2, 2, 2, 2, 2))

        for idx, value in [((0, 1, 0, 1, 0, 0), 0.02085163763902309),
                           ((0, 1, 0, 1, 1, 0), 0.02085163763902309)]:
            self.assertAlmostEqual(diss_matrix[idx], value)
            diss_matrix[idx] = 0

        self.assertEqual(diss_matrix.sum(), 0)


class DisaggregateTestCase(_BaseDisaggTestCase):
    def test(self):
        self.gsim.truncation_level = self.truncation_level = 1
        bin_edges, matrix = disagg.disaggregation(
            self.sources, self.site, self.imt, self.iml, self.gsims,
            self.truncation_level, n_epsilons=3,
            mag_bin_width=3, dist_bin_width=4, coord_bin_width=2.4
        )
        mag_bins, dist_bins, lon_bins, lat_bins, eps_bins, trt_bins = bin_edges
        aaae = numpy.testing.assert_array_almost_equal
        aaae(mag_bins, [3, 6, 9])
        aaae(dist_bins, [0, 4, 8, 12, 16])
        aaae(lon_bins, [9.6, 12., 14.4, 16.8, 19.2, 21.6, 24.])
        aaae(lat_bins, [43.2, 45.6, 48.])
        aaae(eps_bins, [-1, -0.3333333, 0.3333333, 1])
        self.assertEqual(trt_bins, ['trt1', 'trt2'])
        for idx, value in [((0, 2, 5, 0, 0, 0), 0.022067231457071457),
                           ((0, 2, 5, 0, 1, 0), 0.043647500209963),
                           ((0, 2, 5, 0, 2, 0), 0.022067231457071457),
                           ((0, 3, 5, 0, 1, 0), 0.01982473192105061),
                           ((0, 3, 5, 0, 2, 0), 0.003409751870464106),
                           ((0, 2, 4, 0, 0, 0), 0.04290887394265486),
                           ((0, 2, 4, 0, 1, 0), 0.09152318417708383),
                           ((0, 2, 4, 0, 2, 0), 0.0438902176307755),
                           ((1, 3, 5, 0, 0, 0), 0.03111383880273666),
                           ((1, 3, 5, 0, 1, 0), 0.041268484485817325),
                           ((1, 3, 5, 0, 2, 0), 0.03111383880273666),
                           ((1, 3, 4, 0, 2, 0), 0.010480741793785553),
                           ((1, 1, 0, 0, 1, 1), 0.004073878602149361),
                           ((1, 1, 0, 0, 2, 1), 0.0016315473579483486),
                           ((1, 1, 0, 1, 0, 1), 0.003041286638106211),
                           ((1, 1, 0, 1, 1, 1), 0.015114219820389518),
                           ((1, 1, 0, 1, 2, 1), 0.003041286638106211)]:
            self.assertAlmostEqual(matrix[idx], value)
            matrix[idx] = 0

        self.assertEqual(matrix.sum(), 0)

    def test_cross_idl(self):
        # test disaggregation with source generating ruptures crossing
        # internation date line
        ruptures_and_poes = [
            ([0, 0.2, 0.3], self.FakeRupture(5.5, 0.04, 55, -179.5, 45.5)),
            ([0.4, 0.5, 0.6], self.FakeRupture(7.5, 0.03, 75, 179.5, 46.5))
        ]
        source = self.FakeSource(
            1, [rupture for poes, rupture in ruptures_and_poes],
            self.tom, 'trt1'
        )

        disagreggated_poes = dict(
            (rupture, poes) for (poes, rupture) in ruptures_and_poes
        )
        gsim = self.FakeGSIM(self.iml, self.imt, truncation_level=1,
                             n_epsilons=3,
                             disaggregated_poes=disagreggated_poes)

        bin_edges, matrix = disagg.disaggregation(
            [source], self.site, self.imt, self.iml, {'trt1': gsim},
            truncation_level=1, n_epsilons=3,
            mag_bin_width=1, dist_bin_width=10, coord_bin_width=1.0
        )
        mag_bins, dist_bins, lon_bins, lat_bins, eps_bins, trt_bins = bin_edges
        aaae = numpy.testing.assert_array_almost_equal
        aaae(mag_bins, [5, 6, 7, 8])
        aaae(dist_bins, [50, 60, 70, 80])
        aaae(lon_bins, [179., -180, -179.])
        aaae(lat_bins, [45., 46., 47.])
        aaae(eps_bins, [-1, -0.3333333, 0.3333333, 1])
        self.assertEqual(trt_bins, ['trt1'])
        for idx, value in [((0, 0, 1, 0, 0, 0), 0),
                           ((0, 0, 1, 0, 1, 0), 0.008131160717433694),
                           ((0, 0, 1, 0, 2, 0), 0.012171913957925717),
                           ((2, 2, 0, 1, 0, 0), 0.012109762440985716),
                           ((2, 2, 0, 1, 1, 0), 0.015114219820389518),
                           ((2, 2, 0, 1, 2, 0), 0.01810953978371055)]:
            self.assertAlmostEqual(matrix[idx], value)
            matrix[idx] = 0

        self.assertEqual(matrix.sum(), 0)

    def test_source_errors(self):
        # exercise the case where an error occurs while computing on a given
        # seismic source; in this case, we expect an error to be raised which
        # signals the id of the source in question
        fail_source = self.FailSource(self.source2.source_id,
                                      self.source2.ruptures,
                                      self.source2.tom,
                                      self.source2.tectonic_region_type)
        sources = iter([self.source1, fail_source])

        with self.assertRaises(ValueError) as ae:
            bin_edges, matrix = disagg.disaggregation(
                sources, self.site, self.imt, self.iml, self.gsims,
                self.truncation_level, n_epsilons=3,
                mag_bin_width=3, dist_bin_width=4, coord_bin_width=2.4
            )
        expected_error = (
            'An error occurred with source id=2. Error: Something bad happened'
        )
        self.assertEqual(expected_error, str(ae.exception))

    def test_no_contributions_from_ruptures(self):
        # Test that the `disaggregation` function returns `None, None` if no
        # ruptures contribute to the hazard level.
        array = numpy.array
        float64 = numpy.float64
        int64 = numpy.int64
        # This is the result we get if the sources produce no ruptures:
        fake_bins_data = (array([], dtype=float64), array([], dtype=float64),
                          array([], dtype=float64), array([], dtype=float64),
                          array([], dtype=float64), array([], dtype=int64), [])

        with mock.patch(
            'openquake.hazardlib.calc.disagg._collect_bins_data_old'
        ) as cbd:
            with warnings.catch_warnings(record=True) as w:
                cbd.return_value = fake_bins_data

                self.gsim.truncation_level = self.truncation_level = 1
                bin_edges, matrix = disagg.disaggregation(
                    self.sources, self.site, self.imt, self.iml, self.gsims,
                    self.truncation_level, n_epsilons=3,
                    mag_bin_width=3, dist_bin_width=4, coord_bin_width=2.4,
                )

                # We expect to get back 2 `None` values:
                self.assertIsNone(bin_edges)
                self.assertIsNone(matrix)

                # Also check for the warning that should be raised:
                expected_warning_msg = (
                    'No ruptures have contributed to the hazard at site '
                    '<Location=<Latitude=0.000000, Longitude=0.000000, '
                    'Depth=0.0000>, Vs30=2.0000, Vs30Measured=False, '
                    'Depth1.0km=4.0000, Depth2.5km=5.0000, Backarc=False>'
                )
                self.assertEqual(1, len(w))
                [warning] = list(w)
                self.assertEqual(expected_warning_msg, str(warning.message))


class PMFExtractorsTestCase(unittest.TestCase):
    def setUp(self):
        super(PMFExtractorsTestCase, self).setUp()

        self.aae = numpy.testing.assert_almost_equal

        # test matrix is not normalized, but that's fine for test
        self.matrix = numpy.array(
            [  # magnitude
                [  # distance
                    [  # longitude
                        [  # latitude
                            [  # epsilon
                                [0.00, 0.20, 0.50],  # trt
                                [0.33, 0.44, 0.55],
                                [0.10, 0.11, 0.12]],
                            [
                                [0.60, 0.30, 0.20],
                                [0.50, 0.50, 0.30],
                                [0.00, 0.10, 0.20]]],
                        [
                            [
                                [0.10, 0.50, 0.78],
                                [0.15, 0.31, 0.21],
                                [0.74, 0.20, 0.95]],
                            [
                                [0.05, 0.82, 0.99],
                                [0.55, 0.02, 0.63],
                                [0.52, 0.49, 0.21]]]],
                    [
                        [
                            [
                                [0.98, 0.59, 0.13],
                                [0.72, 0.40, 0.12],
                                [0.16, 0.61, 0.53]],
                            [
                                [0.04, 0.94, 0.84],
                                [0.13, 0.03, 0.31],
                                [0.95, 0.34, 0.31]]],
                        [
                            [
                                [0.25, 0.46, 0.34],
                                [0.79, 0.71, 0.17],
                                [0.5, 0.61, 0.7]],
                            [
                                [0.79, 0.15, 0.29],
                                [0.79, 0.14, 0.72],
                                [0.40, 0.84, 0.24]]]]],
                [
                    [
                        [
                            [
                                [0.49, 0.73, 0.79],
                                [0.54, 0.20, 0.04],
                                [0.40, 0.32, 0.06]],
                            [
                                [0.73, 0.04, 0.60],
                                [0.53, 0.65, 0.71],
                                [0.47, 0.93, 0.70]]],
                        [
                            [
                                [0.32, 0.78, 0.97],
                                [0.75, 0.07, 0.59],
                                [0.03, 0.94, 0.12]],
                            [
                                [0.12, 0.15, 0.47],
                                [0.12, 0.62, 0.02],
                                [0.93, 0.13, 0.23]]]],
                    [
                        [
                            [
                                [0.17, 0.14, 1.00],
                                [0.34, 0.27, 0.08],
                                [0.11, 0.85, 0.85]],
                            [
                                [0.76, 0.03, 0.86],
                                [0.97, 0.30, 0.80],
                                [0.67, 0.84, 0.41]]],
                        [
                            [
                                [0.27, 0.36, 0.96],
                                [0.52, 0.77, 0.35],
                                [0.39, 0.88, 0.20]],
                            [
                                [0.86, 0.17, 0.07],
                                [0.48, 0.44, 0.69],
                                [0.14, 0.61, 0.67]]]]]])

    def test_mag(self):
        pmf = disagg.mag_pmf(self.matrix)
        self.aae(pmf, [1.0, 1.0])

    def test_dist(self):
        pmf = disagg.dist_pmf(self.matrix)
        self.aae(pmf, [1.0, 1.0])

    def test_trt(self):
        pmf = disagg.trt_pmf(self.matrix)
        self.aae(pmf, [1.0, 1.0, 1.0])

    def test_mag_dist(self):
        pmf = disagg.mag_dist_pmf(self.matrix)
        self.aae(pmf, [[0.999999999965, 1.0],
                       [1.0, 1.0]])

    def test_mag_dist_eps(self):
        pmf = disagg.mag_dist_eps_pmf(self.matrix)
        self.aae(pmf, [[[0.999984831616, 0.997766176716, 0.998979249671],
                        [0.999997772739, 0.999779959211, 0.999985036077]],
                       [[0.999994665686, 0.999473519718, 0.999989748277],
                        [1.0, 0.999987940219, 0.999995956695]]])

    def test_lon_Lat(self):
        pmf = disagg.lon_lat_pmf(self.matrix)
        self.aae(pmf, [[1.0, 1.0],
                       [1.0, 1.0]])

    def test_mag_lon_lat(self):
        pmf = disagg.mag_lon_lat_pmf(self.matrix)
        self.aae(pmf, [[[0.999992269326, 0.999996551231],
                        [0.999999622937, 0.999999974769]],
                       [[1.0, 0.999999999765],
                        [0.999999998279, 0.999993421953]]])

    def test_lon_lat_trt(self):
        pmf = disagg.lon_lat_trt_pmf(self.matrix)
        self.aae(pmf, [[[0.999805340359, 0.999470893656, 1.0],
                        [0.999998665328, 0.999969082487, 0.999980380612]],
                       [[0.999447922645, 0.999996344798, 0.999999678475],
                        [0.999981572755, 0.999464007617, 0.999983196102]]])
