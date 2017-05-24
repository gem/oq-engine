# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2017 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

import unittest
import collections
import mock

import numpy

from openquake.hazardlib import const
from openquake.hazardlib.gsim.base import (
    GMPE, IPE, SitesContext, RuptureContext, DistancesContext,
    NonInstantiableError, NotVerifiedWarning, DeprecationWarning)
from openquake.hazardlib.geo.mesh import Mesh
from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.imt import PGA, PGV
from openquake.hazardlib.site import Site, SiteCollection
from openquake.hazardlib.source.rupture import BaseRupture
from openquake.hazardlib.gsim.base import ContextMaker


class _FakeGSIMTestCase(unittest.TestCase):
    DEFAULT_IMT = PGA
    DEFAULT_COMPONENT = const.IMC.GMRotI50

    def setUp(self):
        class FakeGSIM(IPE):
            DEFINED_FOR_TECTONIC_REGION_TYPE = None
            DEFINED_FOR_INTENSITY_MEASURE_TYPES = set()
            DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = None
            DEFINED_FOR_STANDARD_DEVIATION_TYPES = set()
            REQUIRES_SITES_PARAMETERS = set()
            REQUIRES_RUPTURE_PARAMETERS = set()
            REQUIRES_DISTANCES = set()

            def get_mean_and_stddevs(self, sites, rup, dists, imt,
                                     stddev_types):
                pass

        super(_FakeGSIMTestCase, self).setUp()
        self.gsim_class = FakeGSIM
        self.gsim = self.gsim_class()
        self.cmaker = ContextMaker([self.gsim])
        self.gsim.DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = \
            self.DEFAULT_COMPONENT
        self.gsim.DEFINED_FOR_INTENSITY_MEASURE_TYPES.add(self.DEFAULT_IMT)

    def _get_poes(self, **kwargs):
        default_kwargs = dict(
            sctx=SitesContext(),
            rctx=RuptureContext(),
            dctx=DistancesContext(),
            imt=self.DEFAULT_IMT(),
            imls=[1.0, 2.0, 3.0],
            truncation_level=1.0
        )
        default_kwargs.update(kwargs)
        kwargs = default_kwargs
        return self.gsim.get_poes(**kwargs)

    def _disaggregate_poe(self, **kwargs):
        default_kwargs = dict(
            sctx=SitesContext(),
            rctx=RuptureContext(),
            dctx=DistancesContext(),
            imt=self.DEFAULT_IMT(),
            iml=2.0,
            truncation_level=1.0,
            n_epsilons=3,
        )
        default_kwargs.update(kwargs)
        kwargs = default_kwargs
        return self.gsim.disaggregate_poe(**kwargs)

    def _assert_value_error(self, func, error, **kwargs):
        with self.assertRaises(ValueError) as ar:
            func(**kwargs)
        self.assertEqual(str(ar.exception), error)


class GetPoEsWrongInputTestCase(_FakeGSIMTestCase):
    def test_wrong_imt(self):
        err = 'imt must be an instance of IMT subclass'
        self._assert_value_error(self._get_poes, err, imt='something')
        self._assert_value_error(self._disaggregate_poe, err, imt='something')
        err = 'imt PGV is not supported by FakeGSIM'
        self._assert_value_error(self._get_poes, err, imt=PGV())
        self._assert_value_error(self._disaggregate_poe, err, imt=PGV())

    def test_wrong_truncation_level(self):
        err = 'truncation level must be zero, positive number or None'
        self._assert_value_error(self._get_poes, err, truncation_level=-0.1)
        self._assert_value_error(self._get_poes, err, truncation_level=-1)
        err = 'truncation level must be positive'
        self._assert_value_error(self._disaggregate_poe, err,
                                 truncation_level=-0.1)


class GetPoEsTestCase(_FakeGSIMTestCase):
    def test_no_truncation(self):
        self.gsim_class.DEFINED_FOR_STANDARD_DEVIATION_TYPES.add(
            const.StdDev.TOTAL
        )

        def get_mean_and_stddevs(sites, rup, dists, imt, stddev_types):
            self.assertEqual(imt, self.DEFAULT_IMT())
            self.assertEqual(stddev_types, [const.StdDev.TOTAL])
            mean = numpy.array([-0.7872268528578843])
            stddev = numpy.array([0.5962393527251486])
            get_mean_and_stddevs.call_count += 1
            return mean, [stddev]

        get_mean_and_stddevs.call_count = 0
        self.gsim.get_mean_and_stddevs = get_mean_and_stddevs
        iml = 0.6931471805599453
        iml_poes = self._get_poes(imt=self.DEFAULT_IMT(), imls=[iml],
                                  truncation_level=None)
        self.assertIsInstance(iml_poes, numpy.ndarray)
        [poe] = iml_poes
        expected_poe = 0.006516701082128207
        self.assertAlmostEqual(float(poe), expected_poe, places=6)
        self.assertEqual(get_mean_and_stddevs.call_count, 1)

    def test_zero_truncation(self):
        def get_mean_and_stddevs(sites, rup, dists, imt, stddev_types):
            return numpy.array([1.1]), [numpy.array([123.45])]
        self.gsim.get_mean_and_stddevs = get_mean_and_stddevs
        imt = self.DEFAULT_IMT()
        imls = [0, 1, 2, 1.1, 1.05]
        [poes] = self._get_poes(imt=imt, imls=imls, truncation_level=0)
        self.assertIsInstance(poes, numpy.ndarray)
        expected_poes = [1, 1, 0, 1, 1]
        self.assertEqual(list(poes), expected_poes)

        self.gsim_class.DEFINED_FOR_STANDARD_DEVIATION_TYPES.add(
            const.StdDev.TOTAL
        )
        [poes] = self._get_poes(imt=imt, imls=imls, truncation_level=0)
        self.assertEqual(list(poes), expected_poes)

    def test_truncated(self):
        self.gsim_class.DEFINED_FOR_STANDARD_DEVIATION_TYPES.add(
            const.StdDev.TOTAL
        )

        def get_mean_and_stddevs(sites, rup, dists, imt, stddev_types):
            return numpy.array([-0.7872268528578843]), \
                [numpy.array([0.5962393527251486])]

        self.gsim.get_mean_and_stddevs = get_mean_and_stddevs
        imls = [-2.995732273553991, -0.6931471805599453, 0.6931471805599453]
        poes = self._get_poes(imt=self.DEFAULT_IMT(), imls=imls,
                              truncation_level=2.0)
        self.assertIsInstance(poes, numpy.ndarray)
        [[poe1, poe2, poe3]] = poes
        self.assertEqual(poe1, 1)
        self.assertEqual(poe3, 0)
        self.assertAlmostEqual(poe2, 0.43432352175355504, places=6)

    def test_several_contexts(self):
        self.gsim_class.DEFINED_FOR_STANDARD_DEVIATION_TYPES.add(
            const.StdDev.TOTAL
        )
        mean_stddev = numpy.array([[3, 4], [5, 6]])

        def get_mean_and_stddevs(sites, rup, dists, imt, stddev_types):
            mean, stddev = mean_stddev
            mean_stddev[0] += 1
            mean_stddev[1] += 2
            return mean, [stddev]
        self.gsim.get_mean_and_stddevs = get_mean_and_stddevs
        imls = [2, 3, 4]
        poes = self._get_poes(imt=self.DEFAULT_IMT(), imls=imls,
                              truncation_level=2.0)
        self.assertIsInstance(poes, numpy.ndarray)
        [[poe11, poe12, poe13], [poe21, poe22, poe23]] = poes
        self.assertAlmostEqual(poe11, 0.617812)
        self.assertAlmostEqual(poe12, 0.559506)
        self.assertAlmostEqual(poe13, 0.5)
        self.assertAlmostEqual(poe21, 0.6531376)
        self.assertAlmostEqual(poe22, 0.6034116)
        self.assertAlmostEqual(poe23, 0.5521092)


class DisaggregatePoETestCase(_FakeGSIMTestCase):
    def test_zero_poe(self):
        self.gsim_class.DEFINED_FOR_STANDARD_DEVIATION_TYPES.add(
            const.StdDev.TOTAL
        )

        def get_mean_and_stddevs(sites, rup, dists, imt, stddev_types):
            self.assertEqual(imt, self.DEFAULT_IMT())
            self.assertEqual(stddev_types, [const.StdDev.TOTAL])
            return numpy.array([1.4]), [numpy.array([0.4])]

        self.gsim.get_mean_and_stddevs = get_mean_and_stddevs
        iml = 1.8
        poes = self._disaggregate_poe(imt=self.DEFAULT_IMT(), iml=iml,
                                      n_epsilons=5, truncation_level=1)
        self.assertIsInstance(poes, numpy.ndarray)
        self.assertEqual(poes.shape, (1, 5))
        numpy.testing.assert_equal(poes, 0)

    def test_max_poe(self):
        self.gsim_class.DEFINED_FOR_STANDARD_DEVIATION_TYPES.add(
            const.StdDev.TOTAL
        )

        def get_mean_and_stddevs(sites, rup, dists, imt, stddev_types):
            self.assertEqual(imt, self.DEFAULT_IMT())
            self.assertEqual(stddev_types, [const.StdDev.TOTAL])
            return numpy.array([2.9]), [numpy.array([1.1])]

        self.gsim.get_mean_and_stddevs = get_mean_and_stddevs
        iml = 1.8
        poes = self._disaggregate_poe(imt=self.DEFAULT_IMT(), iml=iml,
                                      n_epsilons=6, truncation_level=1)
        self.assertIsInstance(poes, numpy.ndarray)
        self.assertEqual(poes.shape, (1, 6))
        self.assertAlmostEqual(poes.sum(), 1)
        numpy.testing.assert_almost_equal(
            poes, [[0.13745236, 0.17130599, 0.19124164,
                    0.19124164, 0.17130599, 0.13745236]]
        )

    def test_middle_of_epsilon_bin(self):
        self.gsim_class.DEFINED_FOR_STANDARD_DEVIATION_TYPES.add(
            const.StdDev.TOTAL
        )

        def get_mean_and_stddevs(sites, rup, dists, imt, stddev_types):
            self.assertEqual(imt, self.DEFAULT_IMT())
            self.assertEqual(stddev_types, [const.StdDev.TOTAL])
            mean = numpy.array([9.4])
            stddev = numpy.array([0.75])
            get_mean_and_stddevs.call_count += 1
            return mean, [stddev]

        get_mean_and_stddevs.call_count = 0
        self.gsim.get_mean_and_stddevs = get_mean_and_stddevs
        aaae = numpy.testing.assert_array_almost_equal

        iml = 9.7
        poes = self._disaggregate_poe(imt=self.DEFAULT_IMT(), iml=iml,
                                      n_epsilons=5, truncation_level=2)
        self.assertIsInstance(poes, numpy.ndarray)
        self.assertEqual(poes.shape, (1, 5))
        aaae(poes, [[0, 0, 0, 0.24044908, 0.09672034]])

        iml = 8.5
        poes = self._disaggregate_poe(imt=self.DEFAULT_IMT(), iml=iml,
                                      n_epsilons=5, truncation_level=2)
        self.assertIsInstance(poes, numpy.ndarray)
        self.assertEqual(poes.shape, (1, 5))
        aaae(poes, [[0, 0.24044908, 0.32566115, 0.24044908, 0.09672034]])

        iml = 9.85
        poes = self._disaggregate_poe(imt=self.DEFAULT_IMT(), iml=iml,
                                      n_epsilons=5, truncation_level=2)
        self.assertIsInstance(poes, numpy.ndarray)
        self.assertEqual(poes.shape, (1, 5))
        aaae(poes, [[0, 0, 0, 0.1667716, 0.09672034]])

        self.assertEqual(get_mean_and_stddevs.call_count, 3)

    def test_many_contexts(self):
        self.gsim_class.DEFINED_FOR_STANDARD_DEVIATION_TYPES.add(
            const.StdDev.TOTAL
        )

        def get_mean_and_stddevs(sites, rup, dists, imt, stddev_types):
            mean = numpy.array([3, 4.5, 5, 8])
            stddev = numpy.array([1, 2, 0.5, 0.9])
            return mean, [stddev]

        self.gsim.get_mean_and_stddevs = get_mean_and_stddevs
        aaae = numpy.testing.assert_array_almost_equal

        iml = 5.3
        poes = self._disaggregate_poe(imt=self.DEFAULT_IMT(), iml=iml,
                                      n_epsilons=5, truncation_level=3)
        self.assertIsInstance(poes, numpy.ndarray)
        self.assertEqual(poes.shape, (4, 5))
        epoes = [[0., 0., 0., 0., 0.00939958],
                 [0., 0., 0.07051552, 0.23896796, 0.03467403],
                 [0., 0., 0., 0.23896796, 0.03467403],
                 [0.03467403, 0.23896796, 0.45271601, 0.23896796, 0.03467403]]
        aaae(poes, epoes)


class TGMPE(GMPE):
    DEFINED_FOR_TECTONIC_REGION_TYPE = None
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = None
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = None
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = None
    REQUIRES_SITES_PARAMETERS = None
    REQUIRES_RUPTURE_PARAMETERS = None
    REQUIRES_DISTANCES = None
    get_mean_and_stddevs = None


class TIPE(IPE):
    DEFINED_FOR_TECTONIC_REGION_TYPE = None
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = None
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = None
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = None
    REQUIRES_SITES_PARAMETERS = None
    REQUIRES_RUPTURE_PARAMETERS = None
    REQUIRES_DISTANCES = None
    get_mean_and_stddevs = None


class ToIMTUnitsToDistributionTestCase(unittest.TestCase):
    def test_gmpe(self):
        gmpe = TGMPE()
        lin_intensity = [0.001, 0.1, 0.7, 1.4]
        log_intensity = [-6.90775528, -2.30258509, -0.35667494, 0.33647224]
        numpy.testing.assert_allclose(
            gmpe.to_distribution_values(lin_intensity), log_intensity)
        numpy.testing.assert_allclose(gmpe.to_imt_unit_values(log_intensity),
                                      lin_intensity)

    def test_ipe(self):
        ipe = TIPE()
        intensity = [0.001, 0.1, 0.7, 1.4]
        numpy.testing.assert_equal(ipe.to_distribution_values(intensity),
                                   intensity)
        numpy.testing.assert_equal(ipe.to_imt_unit_values(intensity),
                                   intensity)


class MakeContextsTestCase(_FakeGSIMTestCase):
    def setUp(self):
        super(MakeContextsTestCase, self).setUp()
        self.site1_location = Point(1, 2)
        self.site2_location = Point(-2, -3)
        self.site1 = Site(vs30=456, vs30measured=False,
                          z1pt0=12.1, z2pt5=15.1,
                          location=self.site1_location)
        self.site2 = Site(vs30=1456, vs30measured=True,
                          z1pt0=112.1, z2pt5=115.1,
                          location=self.site2_location)
        min_distance = numpy.array([10, 11])
        rx_distance = numpy.array([4, 5])
        jb_distance = numpy.array([6, 7])
        ry0_distance = numpy.array([8, 9])
        azimuth = numpy.array([12, 34])
        top_edge_depth = 30
        width = 15
        strike = 60.123

        class FakeSurface(object):
            call_counts = collections.Counter()

            def get_azimuth(self, mesh):
                self.call_counts['get_azimuth'] += 1
                return azimuth

            def get_strike(self):
                self.call_counts['get_strike'] += 1
                return strike

            def get_dip(self):
                self.call_counts['get_dip'] += 1
                return 45.4545

            def get_min_distance(fake_surface, mesh):
                self.assertIsInstance(mesh, Mesh)
                [point1, point2] = mesh
                self.assertEqual(point1, self.site1_location)
                self.assertEqual(point2, self.site2_location)
                fake_surface.call_counts['get_min_distance'] += 1
                return min_distance

            def get_rx_distance(fake_surface, mesh):
                self.assertIsInstance(mesh, Mesh)
                [point1, point2] = mesh
                self.assertEqual(point1, self.site1_location)
                self.assertEqual(point2, self.site2_location)
                fake_surface.call_counts['get_rx_distance'] += 1
                return rx_distance

            def get_ry0_distance(fake_surface, mesh):
                self.assertIsInstance(mesh, Mesh)
                [point1, point2] = mesh
                self.assertEqual(point1, self.site1_location)
                self.assertEqual(point2, self.site2_location)
                fake_surface.call_counts['get_ry0_distance'] += 1
                return ry0_distance

            def get_joyner_boore_distance(fake_surface, mesh):
                self.assertIsInstance(mesh, Mesh)
                [point1, point2] = mesh
                self.assertEqual(point1, self.site1_location)
                self.assertEqual(point2, self.site2_location)
                fake_surface.call_counts['get_joyner_boore_distance'] += 1
                return jb_distance

            def get_top_edge_depth(fake_surface):
                fake_surface.call_counts['get_top_edge_depth'] += 1
                return top_edge_depth

            def get_width(fake_surface):
                fake_surface.call_counts['get_width'] += 1
                return width

        self.rupture_hypocenter = Point(2, 3, 40)
        self.rupture = BaseRupture(
            mag=123.45, rake=123.56,
            tectonic_region_type=const.TRT.VOLCANIC,
            hypocenter=self.rupture_hypocenter, surface=FakeSurface(),
            source_typology=object()
        )
        self.gsim_class.DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.VOLCANIC
        self.fake_surface = FakeSurface

    def make_contexts(self, site_collection, rupture):
        return ContextMaker([self.gsim_class]).make_contexts(
            site_collection, rupture)

    def test_unknown_site_param_error(self):
        self.gsim_class.REQUIRES_SITES_PARAMETERS.add('unknown!')
        err = "ContextMaker requires unknown site parameter 'unknown!'"
        sites = SiteCollection([self.site1, self.site2])
        self._assert_value_error(self.make_contexts, err,
                                 site_collection=sites, rupture=self.rupture)

    def test_unknown_rupture_param_error(self):
        self.gsim_class.REQUIRES_RUPTURE_PARAMETERS.add('stuff')
        err = "ContextMaker requires unknown rupture parameter 'stuff'"
        sites = SiteCollection([self.site1])
        self._assert_value_error(self.make_contexts, err,
                                 site_collection=sites, rupture=self.rupture)

    def test_unknown_distance_error(self):
        self.gsim_class.REQUIRES_DISTANCES.add('jump height')
        err = "Unknown distance measure 'jump height'"
        sites = SiteCollection([self.site1, self.site2])
        self._assert_value_error(self.make_contexts, err,
                                 site_collection=sites, rupture=self.rupture)

    def test_all_values(self):
        self.gsim_class.REQUIRES_DISTANCES = set(
            'rjb rx rrup repi rhypo ry0 azimuth'.split()
        )
        self.gsim_class.REQUIRES_RUPTURE_PARAMETERS = set(
            'mag rake strike dip ztor hypo_lon hypo_lat hypo_depth width'.
            split()
        )
        self.gsim_class.REQUIRES_SITES_PARAMETERS = set(
            'vs30 vs30measured z1pt0 z2pt5 lons lats'.split()
        )
        sites = SiteCollection([self.site1, self.site2])
        sctx, rctx, dctx = self.make_contexts(sites, self.rupture)
        self.assertIsInstance(sctx, SitesContext)
        self.assertIsInstance(rctx, RuptureContext)
        self.assertIsInstance(dctx, DistancesContext)
        self.assertEqual(rctx.mag, 123.45)
        self.assertEqual(rctx.rake, 123.56)
        self.assertEqual(rctx.strike, 60.123)
        self.assertEqual(rctx.dip, 45.4545)
        self.assertEqual(rctx.ztor, 30)
        self.assertEqual(rctx.hypo_lon, 2)
        self.assertEqual(rctx.hypo_lat, 3)
        self.assertEqual(rctx.hypo_depth, 40)
        self.assertEqual(rctx.width, 15)
        self.assertTrue((sctx.vs30 == [456, 1456]).all())
        self.assertTrue((sctx.vs30measured == [False, True]).all())
        self.assertTrue((sctx.z1pt0 == [12.1, 112.1]).all())
        self.assertTrue((sctx.z2pt5 == [15.1, 115.1]).all())
        self.assertTrue((sctx.lons == [1, -2]).all())
        self.assertTrue((sctx.lats == [2, -3]).all())
        self.assertTrue((dctx.rjb == [6, 7]).all())
        self.assertTrue((dctx.rx == [4, 5]).all())
        self.assertTrue((dctx.ry0 == [8, 9]).all())
        self.assertTrue((dctx.rrup == [10, 11]).all())
        self.assertTrue((dctx.azimuth == [12, 34]).all())
        numpy.testing.assert_almost_equal(dctx.rhypo,
                                          [162.18749272, 802.72247682])
        numpy.testing.assert_almost_equal(dctx.repi,
                                          [157.17755181, 801.72524895])
        self.assertEqual(self.fake_surface.call_counts,
                         {'get_top_edge_depth': 1, 'get_rx_distance': 1,
                          'get_joyner_boore_distance': 1, 'get_dip': 1,
                          'get_min_distance': 1, 'get_width': 1,
                          'get_strike': 1, 'get_ry0_distance': 1,
                          'get_azimuth': 1})

    def test_some_values(self):
        self.gsim_class.REQUIRES_DISTANCES = set('rjb rx'.split())
        self.gsim_class.REQUIRES_RUPTURE_PARAMETERS = \
            set('mag strike rake hypo_lon'.split())
        self.gsim_class.REQUIRES_SITES_PARAMETERS = \
            set('vs30 z1pt0 lons'.split())
        sites = SiteCollection([self.site1, self.site2])
        sctx, rctx, dctx = self.make_contexts(sites, self.rupture)
        self.assertEqual(
            (rctx.mag, rctx.rake, rctx.strike, rctx.hypo_lon),
            (123.45, 123.56, 60.123, 2)
        )
        self.assertTrue((sctx.vs30 == (456, 1456)).all())
        self.assertTrue((sctx.z1pt0 == (12.1, 112.1)).all())
        self.assertTrue((sctx.lons == [1, -2]).all())
        self.assertTrue((dctx.rx == (4, 5)).all())
        self.assertFalse(hasattr(rctx, 'dip'))
        self.assertFalse(hasattr(rctx, 'hypo_lat'))
        self.assertFalse(hasattr(rctx, 'hypo_depth'))
        self.assertFalse(hasattr(sctx, 'vs30measured'))
        self.assertFalse(hasattr(sctx, 'z2pt0'))
        self.assertFalse(hasattr(dctx, 'rrup'))
        self.assertFalse(hasattr(dctx, 'azimuth'))
        self.assertFalse(hasattr(dctx, 'ztor'))
        self.assertFalse(hasattr(dctx, 'width'))
        self.assertEqual(self.fake_surface.call_counts,
                         {'get_rx_distance': 1,
                          'get_joyner_boore_distance': 1,
                          'get_strike': 1})


class ContextTestCase(unittest.TestCase):
    def test_equality(self):
        sctx1 = SitesContext()
        sctx1.vs30 = numpy.array([500., 600., 700.])
        sctx1.vs30measured = True
        sctx1.z1pt0 = numpy.array([40., 50., 60.])
        sctx1.z2pt5 = numpy.array([1, 2, 3])

        sctx2 = SitesContext()
        sctx2.vs30 = numpy.array([500., 600., 700.])
        sctx2.vs30measured = True
        sctx2.z1pt0 = numpy.array([40., 50., 60.])
        sctx2.z2pt5 = numpy.array([1, 2, 3])

        self.assertTrue(sctx1 == sctx2)

        sctx2 = SitesContext()
        sctx2.vs30 = numpy.array([500., 600.])
        sctx2.vs30measured = True
        sctx2.z1pt0 = numpy.array([40., 50., 60.])
        sctx2.z2pt5 = numpy.array([1, 2, 3])

        self.assertTrue(sctx1 != sctx2)

        sctx2 = SitesContext()
        sctx2.vs30 = numpy.array([500., 600., 700.])
        sctx2.vs30measured = False
        sctx2.z1pt0 = numpy.array([40., 50., 60.])
        sctx2.z2pt5 = numpy.array([1, 2, 3])

        self.assertTrue(sctx1 != sctx2)

        sctx2 = SitesContext()
        sctx2.vs30 = numpy.array([500., 600., 700.])
        sctx2.vs30measured = True
        sctx2.z1pt0 = numpy.array([40., 50., 60.])

        self.assertTrue(sctx1 != sctx2)

        rctx = RuptureContext()
        rctx.mag = 5.
        self.assertTrue(sctx1 != rctx)


class GsimInstantiationTestCase(unittest.TestCase):
    def test_deprecated(self):
        # check that a deprecation warning is raised when a deprecated
        # GSIM is instantiated

        class NewGMPE(TGMPE):
            'The version which is not deprecated'

        class OldGMPE(NewGMPE):
            'The version which is deprecated'
            deprecated = True

        with mock.patch('warnings.warn') as warn:
            OldGMPE()  # instantiating this class will call warnings.warn

        warning_msg, warning_type = warn.call_args[0]
        self.assertIs(warning_type, DeprecationWarning)
        self.assertEqual(
            warning_msg, 'OldGMPE is deprecated - use NewGMPE instead')

    def test_non_verified(self):
        # check that a NonVerifiedWarning is raised when a non-verified
        # GSIM is instantiated

        class MyGMPE(TGMPE):
            non_verified = True

        with mock.patch('warnings.warn') as warn:
            MyGMPE()  # instantiating this class will call warnings.warn

        warning_msg, warning_type = warn.call_args[0]
        self.assertIs(warning_type, NotVerifiedWarning)
        self.assertEqual(
            warning_msg, 'MyGMPE is not independently verified - '
            'the user is liable for their application')

    def test_non_instantiable(self):
        # check that a NonInstantiableError is raised when a non-instantiable
        # GSIM is instantiated
        class MyGMPE(TGMPE):
            pass
        with self.assertRaises(NonInstantiableError):
            with TGMPE.forbid_instantiation():
                MyGMPE()


class GsimOrderingTestCase(unittest.TestCase):
    def test_ordering_and_equality(self):
        a = TGMPE()
        b = TIPE()
        self.assertLess(a, b)  # 'TGMPE' < 'TIPE'
        self.assertGreater(b, a)
        self.assertNotEqual(a, b)
        a1 = TGMPE()
        b1 = TIPE()
        self.assertEqual(a, a1)
        self.assertEqual(b, b1)
        self.assertNotEqual(a, b1)
