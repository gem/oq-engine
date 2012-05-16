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
import collections

import numpy

from nhlib import const
from nhlib.gsim.base import IPE, SitesContext, RuptureContext, DistancesContext
from nhlib.geo.mesh import Mesh
from nhlib.geo.point import Point
from nhlib.imt import PGA, PGV
from nhlib.site import Site, SiteCollection
from nhlib.source.rupture import Rupture


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

    def _assert_value_error(self, func, error, **kwargs):
        with self.assertRaises(ValueError) as ar:
            func(**kwargs)
        self.assertEqual(str(ar.exception), error)


class GetPoEsWrongInputTestCase(_FakeGSIMTestCase):
    def test_wrong_imt(self):
        err = 'imt must be an instance of IMT subclass'
        self._assert_value_error(self._get_poes, err, imt='something')
        err = 'imt PGV is not supported by FakeGSIM'
        self._assert_value_error(self._get_poes, err, imt=PGV())

    def test_wrong_truncation_level(self):
        err = 'truncation level must be zero, positive number or None'
        self._assert_value_error(self._get_poes, err, truncation_level=-0.1)
        self._assert_value_error(self._get_poes, err, truncation_level=-1)


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
        self.assertAlmostEqual(poe, expected_poe, places=6)
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


class MakeContextsTestCase(_FakeGSIMTestCase):
    def setUp(self):
        super(MakeContextsTestCase, self).setUp()
        self.site1_location = Point(10, 20)
        self.site2_location = Point(-20, -30)
        self.site1 = Site(vs30=456, vs30measured=False,
                          z1pt0=12.1, z2pt5=15.1,
                          location=self.site1_location)
        self.site2 = Site(vs30=1456, vs30measured=True,
                          z1pt0=112.1, z2pt5=115.1,
                          location=self.site2_location)
        min_distance = numpy.array([10, 11])
        rx_distance = numpy.array([4, 5])
        jb_distance = numpy.array([6, 7])
        top_edge_depth = numpy.array([30, 30])

        class FakeSurface(object):
            call_counts = collections.Counter()

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

        self.rupture_hypocenter = Point(20, 30, 40)
        self.rupture = Rupture(
            mag=123.45, rake=123.56,
            tectonic_region_type=const.TRT.VOLCANIC,
            hypocenter=self.rupture_hypocenter, surface=FakeSurface()
        )
        self.gsim_class.DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.VOLCANIC
        self.fake_surface = FakeSurface

    def test_unknown_site_param_error(self):
        self.gsim_class.REQUIRES_SITES_PARAMETERS.add('unknown!')
        err = "FakeGSIM requires unknown site parameter 'unknown!'"
        sites = SiteCollection([self.site1])
        self._assert_value_error(self.gsim.make_contexts, err,
                                 site_collection=sites, rupture=self.rupture)

    def test_unknown_rupture_param_error(self):
        self.gsim_class.REQUIRES_RUPTURE_PARAMETERS.add('stuff')
        err = "FakeGSIM requires unknown rupture parameter 'stuff'"
        sites = SiteCollection([self.site1])
        self._assert_value_error(self.gsim.make_contexts, err,
                                 site_collection=sites, rupture=self.rupture)

    def test_unknown_distance_error(self):
        self.gsim_class.REQUIRES_DISTANCES.add('jump height')
        err = "FakeGSIM requires unknown distance measure 'jump height'"
        sites = SiteCollection([self.site1])
        self._assert_value_error(self.gsim.make_contexts, err,
                                 site_collection=sites, rupture=self.rupture)

    def test_all_values(self):
        self.gsim_class.REQUIRES_DISTANCES = set('rjb ztor rx rrup'.split())
        self.gsim_class.REQUIRES_RUPTURE_PARAMETERS = set(
            'mag rake trt dip'.split()
        )
        self.gsim_class.REQUIRES_SITES_PARAMETERS = set(
            'vs30 vs30measured z1pt0 z2pt5'.split()
        )
        sites = SiteCollection([self.site1, self.site2])
        sctx, rctx, dctx = self.gsim.make_contexts(sites, self.rupture)
        self.assertIsInstance(sctx, SitesContext)
        self.assertIsInstance(rctx, RuptureContext)
        self.assertIsInstance(dctx, DistancesContext)
        self.assertEqual(rctx.mag, 123.45)
        self.assertEqual(rctx.rake, 123.56)
        self.assertEqual(rctx.trt, const.TRT.VOLCANIC)
        self.assertEqual(rctx.dip, 45.4545)
        self.assertTrue((sctx.vs30 == [456, 1456]).all())
        self.assertTrue((sctx.vs30measured == [False, True]).all())
        self.assertTrue((sctx.z1pt0 == [12.1, 112.1]).all())
        self.assertTrue((sctx.z2pt5 == [15.1, 115.1]).all())
        self.assertTrue((dctx.rjb == [6, 7]).all())
        self.assertTrue((dctx.rx == [4, 5]).all())
        self.assertTrue((dctx.rrup == [10, 11]).all())
        self.assertTrue((dctx.ztor == [30, 30]).all())
        self.assertEqual(self.fake_surface.call_counts,
                         {'get_top_edge_depth': 1, 'get_rx_distance': 1,
                          'get_joyner_boore_distance': 1, 'get_dip': 1,
                          'get_min_distance': 1})

    def test_some_values(self):
        self.gsim_class.REQUIRES_DISTANCES = set('rjb rx'.split())
        self.gsim_class.REQUIRES_RUPTURE_PARAMETERS = set('mag rake'.split())
        self.gsim_class.REQUIRES_SITES_PARAMETERS = set('vs30 z1pt0'.split())
        sites = SiteCollection([self.site1, self.site2])
        sctx, rctx, dctx = self.gsim.make_contexts(sites, self.rupture)
        self.assertEqual((rctx.mag, rctx.rake), (123.45, 123.56))
        self.assertTrue((sctx.vs30 == (456, 1456)).all())
        self.assertTrue((sctx.z1pt0 == (12.1, 112.1)).all())
        self.assertTrue((dctx.rx == (4, 5)).all())
        self.assertFalse(hasattr(rctx, 'trt'))
        self.assertFalse(hasattr(rctx, 'dip'))
        self.assertFalse(hasattr(sctx, 'vs30measured'))
        self.assertFalse(hasattr(sctx, 'z2pt0'))
        self.assertFalse(hasattr(dctx, 'rrup'))
        self.assertFalse(hasattr(dctx, 'ztor'))
        self.assertEqual(self.fake_surface.call_counts,
                         {'get_rx_distance': 1,
                          'get_joyner_boore_distance': 1})
