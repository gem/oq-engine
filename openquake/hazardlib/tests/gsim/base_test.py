# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2023 GEM Foundation
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
import unittest.mock as mock
import numpy

from openquake.hazardlib import const, valid
from openquake.hazardlib.gsim.base import (
    GMPE, gsim_aliases, SitesContext, RuptureContext,
    NotVerifiedWarning, DeprecationWarning)
from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.imt import PGA
from openquake.hazardlib.site import Site, SiteCollection
from openquake.hazardlib.source.rupture import BaseRupture
from openquake.hazardlib.gsim.base import ContextMaker
from openquake.hazardlib.gsim.abrahamson_gulerce_2020 import (
    AbrahamsonGulerce2020SInter)
aac = numpy.testing.assert_allclose


class _FakeGSIMTestCase(unittest.TestCase):
    DEFAULT_IMT = PGA
    DEFAULT_COMPONENT = const.IMC.GMRotI50

    def setUp(self):
        class FakeGSIM(GMPE):
            DEFINED_FOR_TECTONIC_REGION_TYPE = None
            DEFINED_FOR_INTENSITY_MEASURE_TYPES = set()
            DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = None
            DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}
            REQUIRES_SITES_PARAMETERS = set()
            REQUIRES_RUPTURE_PARAMETERS = set()
            REQUIRES_DISTANCES = set()

            def get_mean_and_stddevs(self, sites, rup, dists, imt,
                                     stddev_types):
                pass

        super().setUp()
        self.gsim_class = FakeGSIM
        self.gsim = self.gsim_class()
        self.cmaker = ContextMaker('faketrt', [self.gsim], dict(imtls={}))
        self.gsim.DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = \
            self.DEFAULT_COMPONENT
        self.gsim.DEFINED_FOR_INTENSITY_MEASURE_TYPES = frozenset(
            self.gsim.DEFINED_FOR_INTENSITY_MEASURE_TYPES | {self.DEFAULT_IMT})

    def _assert_value_error(self, func, error, **kwargs):
        with self.assertRaises(ValueError) as ar:
            func(**kwargs)
        self.assertEqual(str(ar.exception), error)


class TGMPE(GMPE):
    DEFINED_FOR_TECTONIC_REGION_TYPE = ()
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = ()
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = None
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}
    REQUIRES_SITES_PARAMETERS = ()
    REQUIRES_RUPTURE_PARAMETERS = ()
    REQUIRES_DISTANCES = ()
    get_mean_and_stddevs = None


class MakeContextsTestCase(_FakeGSIMTestCase):
    def setUp(self):
        super().setUp()
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

            def get_min_distance(fake_surface, sitecol):
                [point1, point2] = sitecol
                self.assertEqual(point1.location, self.site1_location)
                self.assertEqual(point2.location, self.site2_location)
                fake_surface.call_counts['get_min_distance'] += 1
                return min_distance

            def get_rx_distance(fake_surface, sitecol):
                [point1, point2] = sitecol
                self.assertEqual(point1.location, self.site1_location)
                self.assertEqual(point2.location, self.site2_location)
                fake_surface.call_counts['get_rx_distance'] += 1
                return rx_distance

            def get_ry0_distance(fake_surface, sitecol):
                [point1, point2] = sitecol
                self.assertEqual(point1.location, self.site1_location)
                self.assertEqual(point2.location, self.site2_location)
                fake_surface.call_counts['get_ry0_distance'] += 1
                return ry0_distance

            def get_joyner_boore_distance(fake_surface, sitecol):
                [point1, point2] = sitecol
                self.assertEqual(point1.location, self.site1_location)
                self.assertEqual(point2.location, self.site2_location)
                fake_surface.call_counts['get_joyner_boore_distance'] += 1
                return jb_distance

            def get_top_edge_depth(fake_surface):
                fake_surface.call_counts['get_top_edge_depth'] += 1
                return top_edge_depth

            def get_width(fake_surface):
                fake_surface.call_counts['get_width'] += 1
                return width

            def get_closest_points(fake_surface, sitecol):
                return sitecol

        self.rupture_hypocenter = Point(2, 3, 40)
        self.rupture = BaseRupture(
            mag=4.5, rake=123.56,
            tectonic_region_type=const.TRT.VOLCANIC,
            hypocenter=self.rupture_hypocenter, surface=FakeSurface())
        self.gsim_class.DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.VOLCANIC
        self.fake_surface = FakeSurface

    def get_ctx(self, rupture, site_collection):
        cmaker = ContextMaker('*', [self.gsim_class], dict(imtls={}))
        [ctx] = cmaker.get_ctx_iter([rupture], site_collection, src_id=0)
        return ctx

    def test_unknown_distance_error(self):
        self.gsim_class.REQUIRES_DISTANCES = frozenset(
            self.gsim_class.REQUIRES_DISTANCES | {'jump height'})
        err = "Unknown distance measure 'jump height'"
        sites = SiteCollection([self.site1, self.site2])
        self._assert_value_error(
            self.get_ctx, err, site_collection=sites, rupture=self.rupture)

    def test_all_values(self):
        self.gsim_class.REQUIRES_DISTANCES = frozenset(
            'rjb rx rrup repi rhypo ry0 azimuth'.split())
        self.gsim_class.REQUIRES_RUPTURE_PARAMETERS = set(
            'mag rake strike dip ztor hypo_lon hypo_lat hypo_depth width'.
            split())
        self.gsim_class.REQUIRES_SITES_PARAMETERS = frozenset(
            'vs30 vs30measured z1pt0 z2pt5 lon lat'.split())
        sites = SiteCollection([self.site1, self.site2])
        ctx = self.get_ctx(self.rupture, sites)
        aac(ctx.mag, 4.5)
        aac(ctx.rake, 123.56)
        aac(ctx.strike, 60.123)
        aac(ctx.dip, 45.4545)
        aac(ctx.ztor, 30)
        aac(ctx.hypo_lon, 2)
        aac(ctx.hypo_lat, 3)
        aac(ctx.hypo_depth, 40)
        aac(ctx.width, 15)
        aac(ctx.vs30, [456, 1456])
        aac(ctx.vs30measured, [False, True])
        aac(ctx.z1pt0, [12.1, 112.1])
        aac(ctx.z2pt5, [15.1, 115.1])
        aac(ctx.lon, [1, -2])
        aac(ctx.lat, [2, -3])
        aac(ctx.rjb, [6, 7])
        aac(ctx.rx, [4, 5])
        aac(ctx.ry0, [8, 9])
        aac(ctx.rrup, [10, 11])
        aac(ctx.azimuth, [12, 34])
        aac(ctx.rhypo, [162.18749272, 802.72247682])
        aac(ctx.repi, [157.17755181, 801.72524895])
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
            set('vs30 z1pt0 lon'.split())
        sites = SiteCollection([self.site1, self.site2])
        ctx = self.get_ctx(self.rupture, sites)
        aac(ctx.mag, 4.5)
        aac(ctx.rake, 123.56)
        aac(ctx.strike, 60.123)
        aac(ctx.hypo_lon, 2)
        aac(ctx.vs30, (456, 1456))
        aac(ctx.z1pt0, (12.1, 112.1))
        aac(ctx.lon, [1, -2])
        aac(ctx.rx, (4, 5))
        self.assertEqual(self.fake_surface.call_counts,
                         {'get_min_distance': 1,
                          'get_joyner_boore_distance': 1,
                          'get_rx_distance': 1, 'get_strike': 1})


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

    def test_recarray_conversion(self):
        # automatic recarray conversion for backward compatibility
        imt = PGA()
        gsim = AbrahamsonGulerce2020SInter()
        ctx = RuptureContext()
        ctx.src_id = 0
        ctx.rup_id = 0
        ctx.mag = 5.
        ctx.sids = [0, 1]
        ctx.vs30 = [760., 760.]
        ctx.rrup = [100., 110.]
        ctx.occurrence_rate = .000001
        mean, _stddevs = gsim.get_mean_and_stddevs(ctx, ctx, ctx, imt, [])
        numpy.testing.assert_allclose(mean, [-5.81116004, -6.00192455])


class GsimInstantiationTestCase(unittest.TestCase):
    def test_deprecated(self):
        # check that a deprecation warning is raised when a deprecated
        # GSIM is instantiated

        class NewGMPE(TGMPE):
            'The version which is not deprecated'

        class OldGMPE(NewGMPE):
            'The version which is deprecated'
            superseded_by = NewGMPE

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


class AliasesTestCase(unittest.TestCase):
    """
    Check that all aliases are valid
    """
    def test_valid(self):
        n = 0
        for toml in gsim_aliases.values():
            valid.gsim(toml)
            n += 1
        print('Checked %d valid aliases' % n)
