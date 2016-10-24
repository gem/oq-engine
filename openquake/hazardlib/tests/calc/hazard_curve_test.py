# The Hazard Library
# Copyright (C) 2012-2016 GEM Foundation
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

import openquake.hazardlib
from openquake.hazardlib import const, imt
from openquake.hazardlib.site import Site, SiteCollection
from openquake.hazardlib.geo import Point
from openquake.hazardlib.tom import PoissonTOM
from openquake.hazardlib.calc.hazard_curve import calc_hazard_curves
from openquake.hazardlib.gsim.base import ContextMaker


class FakeSiteContext(object):
    def __init__(self, sites):
        self.sites = sites
        self.mesh = sites.mesh


class HazardCurvesTestCase(unittest.TestCase):
    class FakeRupture(object):
        def __init__(self, probability, tectonic_region_type):
            self.probability = probability
            self.tectonic_region_type = tectonic_region_type

        def get_probability_no_exceedance(self, poes):
            return (1 - self.probability) ** numpy.array(poes)

    class FakeSource(object):
        def __init__(self, source_id, ruptures, time_span, trt):
            self.source_id = source_id
            self.time_span = time_span
            self.ruptures = ruptures
            self.tectonic_region_type = trt
            self.src_group_id = 0

        def iter_ruptures(self):
            return iter(self.ruptures)

    class FailSource(FakeSource):
        def iter_ruptures(self):
            raise ValueError('Something bad happened')

    class FakeGSIM(object):
        REQUIRES_DISTANCES = set()
        REQUIRES_RUPTURE_PARAMETERS = set()
        REQUIRES_SITES_PARAMETERS = set()

        def __init__(self, truncation_level, imts, poes):
            self.truncation_level = truncation_level
            self.imts = imts
            self.poes = poes

        def get_poes(self, sctx, rctx, dctx, imt, imls, truncation_level):
            assert truncation_level is self.truncation_level
            return numpy.array([self.poes[(epicenter.latitude, rctx, imt)]
                                for epicenter in sctx.mesh])

        def __str__(self):
            return self.__class__.__name__

    def setUp(self):
        self.orig_make_contexts = ContextMaker.make_contexts
        ContextMaker.make_contexts = lambda self, sites, rupture: (
            FakeSiteContext(sites), rupture, None)
        self.truncation_level = 3.4
        self.imts = {'PGA': [1, 2, 3], 'PGD': [2, 4]}
        self.time_span = 49.2

        rup11 = self.FakeRupture(0.23, const.TRT.ACTIVE_SHALLOW_CRUST)
        rup12 = self.FakeRupture(0.15, const.TRT.ACTIVE_SHALLOW_CRUST)
        rup21 = self.FakeRupture(0.04, const.TRT.VOLCANIC)
        self.source1 = self.FakeSource(
            1, [rup11, rup12], self.time_span, const.TRT.ACTIVE_SHALLOW_CRUST)
        self.source2 = self.FakeSource(
            2, [rup21], self.time_span, const.TRT.VOLCANIC)
        self.sources = [self.source1, self.source2]
        site1 = Site(Point(10, 20), 1, True, 2, 3)
        site2 = Site(Point(20, 30), 2, False, 4, 5)
        self.sites = SiteCollection([site1, site2])

        gsim1 = self.FakeGSIM(self.truncation_level, self.imts, poes={
            (site1.location.latitude, rup11, imt.PGA()): [0.1, 0.05, 0.03],
            (site2.location.latitude, rup11, imt.PGA()): [0.11, 0.051, 0.034],
            (site1.location.latitude, rup12, imt.PGA()): [0.12, 0.052, 0.035],
            (site2.location.latitude, rup12, imt.PGA()): [0.13, 0.053, 0.036],

            (site1.location.latitude, rup11, imt.PGD()): [0.4, 0.33],
            (site2.location.latitude, rup11, imt.PGD()): [0.39, 0.331],
            (site1.location.latitude, rup12, imt.PGD()): [0.38, 0.332],
            (site2.location.latitude, rup12, imt.PGD()): [0.37, 0.333],
        })
        gsim2 = self.FakeGSIM(self.truncation_level, self.imts, poes={
            (site1.location.latitude, rup21, imt.PGA()): [0.5, 0.3, 0.2],
            (site2.location.latitude, rup21, imt.PGA()): [0.4, 0.2, 0.1],

            (site1.location.latitude, rup21, imt.PGD()): [0.24, 0.08],
            (site2.location.latitude, rup21, imt.PGD()): [0.14, 0.09],
        })
        self.gsims = {const.TRT.ACTIVE_SHALLOW_CRUST: gsim1,
                      const.TRT.VOLCANIC: gsim2}

    def tearDown(self):
        ContextMaker.make_contexts = self.orig_make_contexts

    def test1(self):
        site1_pga_poe_expected = [0.0639157, 0.03320212, 0.02145989]
        site2_pga_poe_expected = [0.06406232, 0.02965879, 0.01864331]
        site1_pgd_poe_expected = [0.16146619, 0.1336553]
        site2_pgd_poe_expected = [0.15445961, 0.13437589]

        curves = calc_hazard_curves(
            self.sources, self.sites, self.imts,
            self.gsims, self.truncation_level)
        self.assertEqual(set(curves.dtype.fields), set(['PGA', 'PGD']))

        pga_curves = curves['PGA']
        self.assertIsInstance(pga_curves, numpy.ndarray)
        self.assertEqual(pga_curves.shape, (2, 3))  # two sites, three IMLs
        site1_pga_poe, site2_pga_poe = pga_curves
        numpy.testing.assert_allclose(
            site1_pga_poe, site1_pga_poe_expected, 1E-6)
        numpy.testing.assert_allclose(
            site2_pga_poe, site2_pga_poe_expected, 1E-6)

        pgd_curves = curves['PGD']
        self.assertIsInstance(pgd_curves, numpy.ndarray)
        self.assertEqual(pgd_curves.shape, (2, 2))  # two sites, two IMLs
        site1_pgd_poe, site2_pgd_poe = pgd_curves
        numpy.testing.assert_allclose(site1_pgd_poe, site1_pgd_poe_expected)
        numpy.testing.assert_allclose(site2_pgd_poe, site2_pgd_poe_expected)

    def test_source_errors(self):
        # exercise `hazard_curves_poissonian` in the case of an exception,
        # whereby we expect the source_id to be reported in the error message

        fail_source = self.FailSource(self.source2.source_id,
                                      self.source2.ruptures,
                                      self.source2.time_span,
                                      const.TRT.VOLCANIC)
        sources = iter([self.source1, fail_source])

        with self.assertRaises(ValueError) as ae:
            calc_hazard_curves(sources, self.sites, self.imts, self.gsims,
                               self.truncation_level)
        expected_error = (
            'An error occurred with source id=2. Error: Something bad happened'
        )
        self.assertEqual(expected_error, str(ae.exception))


class HazardCurvesFiltersTestCase(unittest.TestCase):
    class SitesCounterSourceSitesFilter(object):
        def __init__(self, chained_generator):
            self.counts = []
            self.chained_generator = chained_generator

        def __call__(self, sources, sites):
            for source, sites in self.chained_generator(sources, sites):
                self.counts.append(
                    (source.source_id, list(map(int, sites.vs30))))
                yield source, sites

    class SitesCounterRuptureFilter(object):
        def __init__(self, chained_generator):
            self.counts = []
            self.chained_generator = chained_generator

        def __call__(self, ruptures, sites):
            for rupture, sites in self.chained_generator(ruptures, sites):
                self.counts.append((rupture.mag, list(map(int, sites.vs30))))
                yield rupture, sites

    def test_point_sources(self):
        sources = [
            openquake.hazardlib.source.PointSource(
                source_id='point1', name='point1',
                tectonic_region_type=const.TRT.ACTIVE_SHALLOW_CRUST,
                mfd=openquake.hazardlib.mfd.EvenlyDiscretizedMFD(
                    min_mag=4, bin_width=1, occurrence_rates=[5]
                ),
                nodal_plane_distribution=openquake.hazardlib.pmf.PMF([
                    (1, openquake.hazardlib.geo.NodalPlane(strike=0.0,
                                                           dip=90.0,
                                                           rake=0.0))
                ]),
                hypocenter_distribution=openquake.hazardlib.pmf.PMF([(1, 10)]),
                upper_seismogenic_depth=0.0,
                lower_seismogenic_depth=10.0,
                magnitude_scaling_relationship=
                openquake.hazardlib.scalerel.PeerMSR(),
                rupture_aspect_ratio=2,
                temporal_occurrence_model=PoissonTOM(1.),
                rupture_mesh_spacing=1.0,
                location=Point(10, 10)
            ),
            openquake.hazardlib.source.PointSource(
                source_id='point2', name='point2',
                tectonic_region_type=const.TRT.ACTIVE_SHALLOW_CRUST,
                mfd=openquake.hazardlib.mfd.EvenlyDiscretizedMFD(
                    min_mag=4, bin_width=2, occurrence_rates=[5, 6, 7]
                ),
                nodal_plane_distribution=openquake.hazardlib.pmf.PMF([
                    (1, openquake.hazardlib.geo.NodalPlane(strike=0,
                                                           dip=90,
                                                           rake=0.0)),
                ]),
                hypocenter_distribution=openquake.hazardlib.pmf.PMF([(1, 10)]),
                upper_seismogenic_depth=0.0,
                lower_seismogenic_depth=10.0,
                magnitude_scaling_relationship=
                openquake.hazardlib.scalerel.PeerMSR(),
                rupture_aspect_ratio=2,
                temporal_occurrence_model=PoissonTOM(1.),
                rupture_mesh_spacing=1.0,
                location=Point(10, 11)
            ),
        ]
        sites = [openquake.hazardlib.site.Site(Point(11, 10), 1, True, 2, 3),
                 openquake.hazardlib.site.Site(Point(10, 16), 2, True, 2, 3),
                 openquake.hazardlib.site.Site(Point(10, 10.6), 3, True, 2, 3),
                 openquake.hazardlib.site.Site(Point(10, 10.7), 4, True, 2, 3)]
        sitecol = openquake.hazardlib.site.SiteCollection(sites)

        from openquake.hazardlib.gsim.sadigh_1997 import SadighEtAl1997
        gsims = {const.TRT.ACTIVE_SHALLOW_CRUST: SadighEtAl1997()}
        truncation_level = 1
        imts = {'PGA': [0.1, 0.5, 1.3]}

        from openquake.hazardlib.calc import filters
        source_site_filter = self.SitesCounterSourceSitesFilter(
            filters.SourceSitesFilter(30))
        calc_hazard_curves(
            sources, sitecol, imts, gsims, truncation_level,
            source_site_filter=source_site_filter)
        # there are two sources and four sites. The first source contains only
        # one rupture, the second source contains three ruptures.
        #
        # the first source has 'maximum projection radius' of 0.707 km
        # the second source has 'maximum projection radius' of 500.0 km
        #
        # the epicentral distances for source 1 are: [ 109.50558394,
        # 667.16955987,   66.71695599,   77.83644865]
        # the epicentral distances for source 2 are: [ 155.9412148 ,
        # 555.97463322,   44.47797066,   33.35847799]
        #
        # Considering that the source site filtering distance is set to 30 km,
        # for source 1, all sites have epicentral distance larger than
        # 0.707 + 30 km. This means that source 1 ('point 1') is not considered
        # in the calculation because too far.
        # for source 2, the 1st, 3rd and 4th sites have epicentral distances
        # smaller than 500.0 + 30 km. This means that source 2 ('point 2') is
        # considered in the calculation for site 1, 3, and 4.
        #
        # JB distances for rupture 1 in source 2 are: [ 155.43860273,
        #  555.26752644,   43.77086388,   32.65137121]
        # JB distances for rupture 2 in source 2 are: [ 150.98882575,
        #  548.90356541,   37.40690285,   26.28741018]
        # JB distances for rupture 3 in source 2 are: [ 109.50545819,
        # 55.97463322,    0.        ,    0.        ]
        #
        # Considering that the rupture site filtering distance is set to 30 km,
        # rupture 1 (magnitude 4) is not considered because too far, rupture 2
        # (magnitude 6) affect only the 4th site, rupture 3 (magnitude 8)
        # affect the 3rd and 4th sites.
        self.assertEqual(source_site_filter.counts,
                         [('point2', [1, 3, 4])])
