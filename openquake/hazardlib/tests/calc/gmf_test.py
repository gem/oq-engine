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
import mock
import numpy
from numpy.testing import assert_allclose, assert_array_equal

from openquake.hazardlib import const
from openquake.hazardlib.imt import SA, PGV
from openquake.hazardlib.site import Site, SiteCollection
from openquake.hazardlib.geo import Point
from openquake.hazardlib.calc.gmf import (
    ground_motion_fields, CorrelationButNoInterIntraStdDevs, GmfComputer)
from openquake.hazardlib.gsim.base import ContextMaker
from openquake.hazardlib.correlation import JB2009CorrelationModel


class BaseFakeGSIM(object):
    REQUIRES_DISTANCES = set()
    REQUIRES_RUPTURE_PARAMETERS = set()
    REQUIRES_SITES_PARAMETERS = set()

    expect_stddevs = True

    def __init__(self, testcase):
        self.testcase = testcase

    def get_mean_and_stddevs(gsim, mean, std_inter, std_intra, imt,
                             stddev_types):
        raise NotImplementedError

    def to_imt_unit_values(gsim, intensities):
        return intensities - 10.


class FakeGSIMInterIntraStdDevs(BaseFakeGSIM):
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set(
        [const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT]
    )

    def get_mean_and_stddevs(gsim, mean, std_inter, std_intra, imt,
                             stddev_types):
        if gsim.expect_stddevs:
            gsim.testcase.assertEqual(
                stddev_types,
                [const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT])
            # + 10 is needed to make sure that to_imt_unit_values()
            # is called on the result of gmf calc
            return mean + 10, [std_inter, std_intra]
        else:
            gsim.testcase.assertEqual(stddev_types, [])
            return mean + 10, []


class FakeGSIMTotalStdDev(BaseFakeGSIM):
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([const.StdDev.TOTAL])

    def get_mean_and_stddevs(gsim, mean, std_total, not_used, imt,
                             stddev_types):
        if gsim.expect_stddevs:
            gsim.testcase.assertEqual(stddev_types, [const.StdDev.TOTAL])

            # + 10 is needed to make sure that to_imt_unit_values()
            # is called on the result of gmf calc
            return mean + 10, [std_total]
        else:
            gsim.testcase.assertEqual(stddev_types, [])
            return mean + 10, []


class BaseGMFCalcTestCase(unittest.TestCase):
    def setUp(self):
        self.mean1 = 1
        self.mean2 = 5
        self.mean3 = 10
        self.mean4567 = 10
        self.inter1 = 0.4
        self.inter2 = 1
        self.inter3 = 1.4
        self.inter45 = 1e-300
        self.inter67 = 1
        self.intra1 = 0.7
        self.intra2 = 2
        self.intra3 = 0.3
        self.intra45 = 1
        self.intra67 = 1e-300
        self.total1 = 0.6
        self.total2 = 3
        self.total3 = 0.4
        self.total45 = 10
        self.total67 = 0.2
        self.stddev1 = (self.inter1 ** 2 + self.intra1 ** 2) ** 0.5
        self.stddev2 = (self.inter2 ** 2 + self.intra2 ** 2) ** 0.5
        self.stddev3 = (self.inter3 ** 2 + self.intra3 ** 2) ** 0.5
        self.stddev45 = (self.inter45 ** 2 + self.intra45 ** 2) ** 0.5
        self.stddev67 = (self.inter67 ** 2 + self.intra67 ** 2) ** 0.5
        p = [Point(0, 0), Point(0, 0.1), Point(0, 0.2), Point(0, 0.3),
             Point(0, 0.4), Point(0, 0.5), Point(0, 0.6)]
        sites = [Site(p[0], self.mean1, False, self.inter1, self.intra1),
                 Site(p[1], self.mean2, True, self.inter2, self.intra2),
                 Site(p[2], self.mean3, False, self.inter3, self.intra3),
                 Site(p[3], self.mean4567, True, self.inter45, self.intra45),
                 Site(p[4], self.mean4567, False, self.inter45, self.intra45),
                 Site(p[5], self.mean4567, True, self.inter67, self.intra67),
                 Site(p[6], self.mean4567, False, self.inter67, self.intra67)]
        self.sites = SiteCollection(sites)

        sites_total = [
            # `intra` values are not used in this case
            # they're just fake "stand-in" values
            Site(p[0], self.mean1, False, self.total1, self.intra1),
            Site(p[1], self.mean2, True, self.total2, self.intra2),
            Site(p[2], self.mean3, False, self.total3, self.intra3),
            Site(p[3], self.mean4567, True, self.total45, self.intra45),
            Site(p[4], self.mean4567, False, self.total45, self.intra45),
            Site(p[5], self.mean4567, True, self.total67, self.intra67),
            Site(p[6], self.mean4567, False, self.total67, self.intra67)]
        self.sites_total = SiteCollection(sites_total)

        self.rupture = object()
        self.imt1 = SA(10, 5)
        self.imt2 = PGV()

        self.gsim = FakeGSIMInterIntraStdDevs(self)
        self.total_stddev_gsim = FakeGSIMTotalStdDev(self)

        def make_contexts(gsim, sites, rupture):
            return sites.vs30, sites.z1pt0, sites.z2pt5
        self.orig_make_contexts = ContextMaker.make_contexts
        ContextMaker.make_contexts = make_contexts

    def tearDown(self):
        ContextMaker.make_contexts = self.orig_make_contexts


class GMFCalcNoCorrelationTestCase(BaseGMFCalcTestCase):

    def test_total_stddev_only(self):
        truncation_level = None
        numpy.random.seed(37)
        realizations = 1000
        gmfs = ground_motion_fields(self.rupture, self.sites_total,
                                    [self.imt2],
                                    self.total_stddev_gsim,
                                    truncation_level,
                                    realizations=realizations,
                                    correlation_model=None)
        intensity = gmfs[self.imt2]

        assert_allclose((intensity[0].mean(), intensity[0].std()),
                        (self.mean1, self.total1), rtol=4e-2)
        assert_allclose((intensity[1].mean(), intensity[1].std()),
                        (self.mean2, self.total2), rtol=4e-2)
        assert_allclose((intensity[2].mean(), intensity[2].std()),
                        (self.mean3, self.total3), rtol=4e-2)

        assert_allclose((intensity[3].mean(), intensity[3].std()),
                        (self.mean4567, self.total45), rtol=4e-2)
        assert_allclose((intensity[4].mean(), intensity[4].std()),
                        (self.mean4567, self.total45), rtol=4e-2)

        assert_allclose((intensity[5].mean(), intensity[5].std()),
                        (self.mean4567, self.total67), rtol=4e-2)
        assert_allclose((intensity[6].mean(), intensity[6].std()),
                        (self.mean4567, self.total67), rtol=4e-2)

    def test_no_filtering_no_truncation(self):
        truncation_level = None
        numpy.random.seed(3)
        realizations = 2000
        gmfs = ground_motion_fields(self.rupture, self.sites,
                                    [self.imt2], self.gsim,
                                    truncation_level,
                                    realizations=realizations)
        intensity = gmfs[self.imt2]

        assert_allclose((intensity[0].mean(), intensity[0].std()),
                        (self.mean1, self.stddev1), rtol=4e-2)
        assert_allclose((intensity[1].mean(), intensity[1].std()),
                        (self.mean2, self.stddev2), rtol=4e-2)
        assert_allclose((intensity[2].mean(), intensity[2].std()),
                        (self.mean3, self.stddev3), rtol=4e-2)

        assert_allclose((intensity[3].mean(), intensity[3].std()),
                        (self.mean4567, self.stddev45), rtol=4e-2)
        assert_allclose((intensity[4].mean(), intensity[4].std()),
                        (self.mean4567, self.stddev45), rtol=4e-2)

        assert_allclose((intensity[5].mean(), intensity[5].std()),
                        (self.mean4567, self.stddev67), rtol=4e-2)
        assert_allclose((intensity[6].mean(), intensity[6].std()),
                        (self.mean4567, self.stddev67), rtol=4e-2)

        # sites with zero intra-event stddev, should give exactly the same
        # result, since inter-event distribution is sampled only once
        assert_array_equal(intensity[5], intensity[6])

        self.assertFalse((intensity[3] == intensity[4]).all())

    def test_no_filtering_with_truncation(self):
        truncation_level = 1.9
        numpy.random.seed(11)
        realizations = 400
        gmfs = ground_motion_fields(self.rupture, self.sites,
                                    [self.imt1], self.gsim,
                                    realizations=realizations,
                                    truncation_level=truncation_level)
        intensity = gmfs[self.imt1]

        max_deviation1 = (self.inter1 + self.intra1) * truncation_level
        max_deviation2 = (self.inter2 + self.intra2) * truncation_level
        max_deviation3 = (self.inter3 + self.intra3) * truncation_level
        max_deviation4567 = truncation_level
        self.assertLessEqual(intensity[0].max(), self.mean1 + max_deviation1)
        self.assertGreaterEqual(intensity[0].min(),
                                self.mean1 - max_deviation1)
        self.assertLessEqual(intensity[1].max(), self.mean2 + max_deviation2)
        self.assertGreaterEqual(intensity[1].min(),
                                self.mean2 - max_deviation2)
        self.assertLessEqual(intensity[2].max(), self.mean3 + max_deviation3)
        self.assertGreaterEqual(intensity[2].min(),
                                self.mean3 - max_deviation3)

        for i in (3, 4, 5, 6):
            self.assertLessEqual(intensity[i].max(),
                                 self.mean4567 + max_deviation4567)
            self.assertGreaterEqual(intensity[i].min(),
                                    self.mean4567 - max_deviation4567)

        assert_allclose(intensity.mean(axis=1),
                        [self.mean1, self.mean2, self.mean3] +
                        [self.mean4567] * 4,
                        rtol=5e-2)

        self.assertLess(intensity[0].std(), self.stddev1)
        self.assertLess(intensity[1].std(), self.stddev2)
        self.assertLess(intensity[2].std(), self.stddev3)
        self.assertLess(intensity[3].std(), self.stddev45)
        self.assertLess(intensity[4].std(), self.stddev45)
        self.assertLess(intensity[5].std(), self.stddev67)
        self.assertLess(intensity[6].std(), self.stddev67)
        for i in range(7):
            self.assertGreater(intensity[i].std(), 0)

    def test_no_filtering_zero_truncation(self):
        truncation_level = 0
        self.gsim.expect_stddevs = False
        gmfs = ground_motion_fields(self.rupture, self.sites,
                                    [self.imt1, self.imt2], self.gsim,
                                    realizations=100,
                                    truncation_level=truncation_level)
        for intensity in gmfs[self.imt1], gmfs[self.imt2]:
            for i in range(7):
                self.assertEqual(intensity[i].std(), 0)
            self.assertEqual(intensity[0].mean(), self.mean1)
            self.assertEqual(intensity[1].mean(), self.mean2)
            self.assertEqual(intensity[2].mean(), self.mean3)
            self.assertEqual(intensity[3].mean(), self.mean4567)
            self.assertEqual(intensity[4].mean(), self.mean4567)
            self.assertEqual(intensity[5].mean(), self.mean4567)
            self.assertEqual(intensity[6].mean(), self.mean4567)


class GMFCalcCorrelatedTestCase(BaseGMFCalcTestCase):
    def test_no_truncation(self):
        mean = 10
        inter = 1e-300
        intra = 3
        points = [Point(0, 0), Point(0, 0.05), Point(0.06, 0.025),
                  Point(0, 1.0), Point(-10, -10)]
        sites = [Site(point, mean, False, inter, intra) for point in points]
        self.sites = SiteCollection(sites)

        numpy.random.seed(23)
        cormo = JB2009CorrelationModel(vs30_clustering=False)
        corma = cormo._get_correlation_matrix(self.sites, self.imt1)
        gmfs = ground_motion_fields(
            self.rupture, self.sites, [self.imt1], self.gsim,
            truncation_level=None, realizations=6000,
            correlation_model=cormo
        )

        sampled_corma = numpy.corrcoef(gmfs[self.imt1])
        assert_allclose(corma, sampled_corma, rtol=0, atol=0.02)

    def test_no_correlation_mean_and_intra_respected(self):
        mean1 = 10
        mean2 = 14
        inter = 1e-300
        intra1 = 0.2
        intra2 = 1.6
        p1 = Point(0, 0)
        p2 = Point(0, 0.3)
        sites = [Site(p1, mean1, False, inter, intra1),
                 Site(p2, mean2, False, inter, intra2)]
        self.sites = SiteCollection(sites)

        numpy.random.seed(41)
        cormo = JB2009CorrelationModel(vs30_clustering=False)
        s1_intensity, s2_intensity = ground_motion_fields(
            self.rupture, self.sites, [self.imt1], self.gsim,
            truncation_level=None, realizations=6000,
            correlation_model=cormo,
        )[self.imt1]

        self.assertAlmostEqual(s1_intensity.mean(), mean1, delta=1e-3)
        self.assertAlmostEqual(s2_intensity.mean(), mean2, delta=1e-3)
        self.assertAlmostEqual(s1_intensity.std(), intra1, delta=2e-3)
        self.assertAlmostEqual(s2_intensity.std(), intra2, delta=1e-2)

    def test_correlation_with_total_stddev(self):
        mean1 = 10
        mean2 = 14
        inter = 1e-300
        intra1 = 0.2
        intra2 = 1.6
        p1 = Point(0, 0)
        p2 = Point(0, 0.3)
        sites = [Site(p1, mean1, False, inter, intra1),
                 Site(p2, mean2, False, inter, intra2)]
        self.sites = SiteCollection(sites)

        numpy.random.seed(41)
        cormo = JB2009CorrelationModel(vs30_clustering=False)
        gsim = FakeGSIMTotalStdDev(self)
        with self.assertRaises(CorrelationButNoInterIntraStdDevs):
            ground_motion_fields(
                self.rupture, self.sites, [self.imt1], gsim,
                truncation_level=None, realizations=6000,
                correlation_model=cormo)


class GmfComputerTestCase(unittest.TestCase):
    # NB: the GmfComputer is heavily tested in the engine, in the tests
    # of all the GMF-based calculators
    def test_empty_inputs(self):
        rupture = mock.Mock()
        sites = [mock.Mock()]
        imts = [mock.Mock()]
        gsims = [mock.Mock()]
        with self.assertRaises(ValueError):
            GmfComputer(rupture, [], imts, gsims)
        with self.assertRaises(ValueError):
            GmfComputer(rupture, sites, [], gsims)
        with self.assertRaises(ValueError):
            GmfComputer(rupture, sites, imts, [])
