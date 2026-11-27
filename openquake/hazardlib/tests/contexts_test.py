# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2019, GEM Foundation
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import os
import unittest
from unittest import mock
import numpy

from openquake.baselib.general import DictArray, gettemp
from openquake.baselib.performance import Monitor
from openquake.hazardlib import site, contexts, stats
from openquake.hazardlib.pmf import PMF
from openquake.hazardlib.const import TRT
from openquake.hazardlib.tom import PoissonTOM
from openquake.hazardlib.contexts import (
    ContextMaker, get_distances, collapse_ctx, concat)
from openquake.hazardlib import valid
from openquake.hazardlib.geo.surface import SimpleFaultSurface as SFS
from openquake.hazardlib.source.multi_fault import save_and_split
from openquake.hazardlib.source.rupture import \
    get_planar, NonParametricProbabilisticRupture as NPPR
from openquake.hazardlib.geo import Line, Point, Polygon
from openquake.hazardlib.geo.surface.multi import build_secparams
from openquake.hazardlib.site import Site, SiteCollection
from openquake.hazardlib.source import PointSource, AreaSource
from openquake.hazardlib.source.point import grid_point_sources
from openquake.hazardlib.calc.filters import split_source
from openquake.hazardlib.mfd import ArbitraryMFD, TruncatedGRMFD
from openquake.hazardlib.scalerel import WC1994, PointMSR
from openquake.hazardlib.geo.nodalplane import NodalPlane
from openquake.hazardlib.geo.surface.planar import (
    get_distances_planar, build_planar)
from openquake.hazardlib.sourceconverter import SourceConverter
from openquake.hazardlib.nrml import to_python
from openquake.hazardlib.gsim import kuehn_2020
from openquake.hazardlib.gsim.abrahamson_2014 import AbrahamsonEtAl2014
from openquake.hazardlib.gsim.campbell_bozorgnia_2014 import (
    CampbellBozorgnia2014)
from openquake.hazardlib.gsim.mgmpe.modifiable_gmpe import ModifiableGMPE
from openquake.hazardlib.gsim_lt import GsimLogicTree
from openquake.qa_tests_data import mosaic
from openquake.commonlib import readinput
from openquake.hazardlib.rmap_maker import get_cmakers
from openquake.hazardlib.source_reader import (
    get_bset_values, modified_groups)

PLOTTING = False
aac = numpy.testing.assert_allclose
tom = PoissonTOM(50.)
JOB = os.path.join(os.path.dirname(__file__), 'data/context/job.ini')
BASE_PATH = os.path.dirname(__file__)


def rms(delta):
    return numpy.sqrt((delta**2).sum())


def set_msparams(src, sectiondict):
    secparams = build_secparams(sectiondict.values())
    src.set_msparams(secparams, ry0=True)


class ClosestPointOnTheRuptureTestCase(unittest.TestCase):

    def setUp(self):

        # Create surface
        trc = Line([Point(0.0, 0.0), Point(0.5, 0.0)])
        usd = 0.0
        lsd = 20.0
        dip = 90.0
        spc = 2.5
        self.srfc1 = SFS.from_fault_data(trc, usd, lsd, dip, spc)

        # Create surface
        trc = Line([Point(0.0, 0.0), Point(0.5, 0.0)])
        usd = 0.0
        lsd = 20.0
        dip = 20.0
        spc = 2.5
        self.srfc2 = SFS.from_fault_data(trc, usd, lsd, dip, spc)

    def test_simple_fault_surface_vertical(self):

        # Create the rupture
        mag = 10.0
        rake = 90.0
        trt = TRT.ACTIVE_SHALLOW_CRUST
        hypoc = Point(0.25, 0.0, 5)
        pmf = PMF([(0.8, 0), (0.2, 1)])
        rup = NPPR(mag, rake, trt, hypoc, self.srfc1, pmf)

        # Compute distances
        param = 'clon_clat'
        sites = SiteCollection([Site(Point(0.25, -0.1, 0.0)),
                                Site(Point(-0.1, 0.0, 0.0))])
        dsts = get_distances(rup, sites, param)

        # Check first point
        msg = 'The longitude of the first point is wrong'
        self.assertTrue(abs(dsts[0, 0]-0.25) < 1e-2, msg)
        msg = 'The latitude of the first point is wrong'
        self.assertTrue(abs(dsts[0][1]-0.0) < 1e-2, msg)

        # Check second point
        msg = 'The longitude of the second point is wrong'
        self.assertTrue(abs(dsts[1, 0]-0.0) < 1e-2, msg)
        msg = 'The latitude of the second point is wrong'
        self.assertTrue(abs(dsts[1][1]-0.0) < 1e-2, msg)

    def test_simple_fault_surface_almost_flat(self):

        # Create the rupture
        mag = 10.0
        rake = 90.0
        trt = TRT.ACTIVE_SHALLOW_CRUST
        hypoc = Point(0.25, 0.0, 5)
        pmf = PMF([(0.8, 0), (0.2, 1)])
        rup = NPPR(mag, rake, trt, hypoc, self.srfc2, pmf)

        # Compute distances
        param = 'clon_clat'
        sites = SiteCollection([Site(Point(0.25, -0.6, 0.0))])
        dsts = get_distances(rup, sites, param)

        # Check first point
        msg = 'The longitude of the first point is wrong'
        self.assertTrue(abs(dsts[0, 0]-0.25) < 1e-2, msg)
        msg = 'The latitude of the first point is wrong'
        self.assertTrue(abs(dsts[0][1]+0.4859) < 1e-2, msg)

    def test_point_surface(self):

        sid = 0
        name = 'test'
        trt = TRT.ACTIVE_SHALLOW_CRUST
        mfd = ArbitraryMFD([7.0], [1.])
        rms = 2.5
        msr = WC1994()
        rar = 1.0
        tom = PoissonTOM(1.)
        usd = 0.0
        lsd = 20.0
        loc = Point(0.0, 0.0)
        npd = PMF([(1.0, NodalPlane(90., 90., 90.))])
        hyd = PMF([(1.0, 10.)])
        src = PointSource(sid, name, trt, mfd, rms, msr, rar, tom, usd, lsd,
                          loc, npd, hyd)
        rups = [r for r in src.iter_ruptures()]

        # Compute distances
        param = 'clon_clat'
        sites = SiteCollection([Site(Point(0.0, 0.0, 0.0)),
                                Site(Point(-0.2, 0.0, 0.0))])
        dsts = get_distances(rups[0], sites, param)

        # Check first point
        msg = 'The longitude of the first point is wrong'
        self.assertTrue(abs(dsts[0, 0]-0.0) < 1e-2, msg)
        msg = 'The latitude of the first point is wrong'
        self.assertTrue(abs(dsts[0, 1]-0.0) < 1e-2, msg)

        # Check second point
        msg = 'The longitude of the second point is wrong'
        self.assertTrue(abs(dsts[1, 0]+0.1666) < 1e-2, msg)
        msg = 'The latitude of the second point is wrong'
        self.assertTrue(abs(dsts[1, 1]-0.0) < 1e-2, msg)


class GetCtxs01TestCase(unittest.TestCase):
    """
    Test for calculation of distances with caching
    """
    def setUp(self):
        # Set paths
        path = '../../qa_tests_data/classical/case_75/ruptures_0.xml'
        rup_path = os.path.join(BASE_PATH, path)
        path = '../../qa_tests_data/classical/case_75/ruptures_0_sections.xml'
        geom_path = os.path.join(BASE_PATH, path)

        # Create source
        sc = SourceConverter(investigation_time=1, rupture_mesh_spacing=2.5)
        ssm = to_python(rup_path, sc)
        geom = to_python(geom_path, sc)
        self.src = ssm[0][0]
        save_and_split([self.src], geom.sections, gettemp(suffix='.hdf5'))
        set_msparams(self.src, geom.sections)

        # Create site-collection
        site = Site(Point(0.05, 0.2), vs30=760, z1pt0=30, z2pt5=0.5,
                    vs30measured=True)
        self.sitec = SiteCollection([site])

        # Create the context maker
        gmm = AbrahamsonEtAl2014()
        param = dict(imtls={'PGA': []})
        cm = ContextMaker('*', [gmm], param)

        # extract magnitude 7 context
        ctx = list(cm.get_ctxs(self.src, self.sitec))[-1]
        self.ctx = ctx[ctx.mag == 7.0]

        # extract magnitude 7 rupture
        [self.rup] = [rup for rup in self.src.iter_ruptures() if rup.mag == 7.]

    def test_collapse_tiles(self):
        # the multifault distances are cached on all the sites, so they
        # must be looked up by position when _collapse_by_mag uses tiles
        sitec = SiteCollection([
            Site(Point(x, .1), vs30=760, z1pt0=30, z2pt5=.5,
                 vs30measured=True) for x in numpy.linspace(-.5, .5, 50)])
        self.src.id = 1
        out = []
        for pairs in (5_000_000, 50):  # one tile and many tiles
            with mock.patch.object(contexts, 'COLLAPSE_PAIRS', pairs):
                cm = ContextMaker('*', [AbrahamsonEtAl2014()], dict(
                    imtls={'PGA': [.1]}, collapse_precision=.03))
                ctx = concat(list(cm.get_ctxs(self.src, sitec)))
            out.append(ctx[numpy.lexsort((ctx.rup_id, ctx.sids))])
        for par in ['sids', 'rup_id', 'rrup', 'rjb', 'rx', 'ry0']:
            numpy.testing.assert_array_equal(out[0][par], out[1][par])

    def test_rjb_distance(self):
        rjb = self.rup.surface.get_joyner_boore_distance(self.sitec.mesh)
        self.assertAlmostEqual(rjb, self.ctx.rjb, delta=1e-3)

    def test_rrup_distance(self):
        rrup = self.rup.surface.get_min_distance(self.sitec.mesh)
        self.assertAlmostEqual(rrup, self.ctx.rrup, delta=1e-3)

    def test_rx_distance(self):
        rx = self.rup.surface.get_rx_distance(self.sitec.mesh)
        self.assertAlmostEqual(rx, self.ctx.rx, delta=1e-3)

    def test_ry0_distance(self):
        dst = self.rup.surface.get_ry0_distance(self.sitec.mesh)
        self.assertAlmostEqual(dst, self.ctx.ry0, delta=1e-3)


class GetCtxs02TestCase(unittest.TestCase):
    """
    Test for calculation of distances with caching
    """
    def setUp(self):
        # Set paths
        path = './data/context02/ruptures_0.xml'
        rup_path = os.path.join(BASE_PATH, path)
        path = './data/context02/ruptures_0_sections.xml'
        geom_path = os.path.join(BASE_PATH, path)

        # Create source
        sc = SourceConverter(investigation_time=1, rupture_mesh_spacing=2.5)
        ssm = to_python(rup_path, sc)
        geom = to_python(geom_path, sc)
        self.src = ssm[0][0]
        save_and_split([self.src], geom.sections, gettemp(suffix='.hdf5'))
        set_msparams(self.src, geom.sections)

        # Create site-collection
        site = Site(Point(0.05, 0.2), vs30=760, z1pt0=30, z2pt5=0.5,
                    vs30measured=True)
        self.sitec = SiteCollection([site])

        # Create the context maker
        gmm = AbrahamsonEtAl2014()
        param = dict(imtls={'PGA': []})
        cm = ContextMaker('*', [gmm], param)

        # extract magnitude 7 context
        [ctx] = cm.get_ctxs(self.src, self.sitec)
        self.ctx = ctx[ctx.mag == 7.0]

        # extract magnitude 7 rupture
        [self.rup] = [rup for rup in self.src.iter_ruptures() if rup.mag == 7.]

    def test_rjb_distance(self):
        rjb = self.rup.surface.get_joyner_boore_distance(self.sitec.mesh)
        self.assertAlmostEqual(rjb, self.ctx.rjb, delta=1e-3)

    def test_rrup_distance(self):
        rrup = self.rup.surface.get_min_distance(self.sitec.mesh)
        self.assertAlmostEqual(rrup, self.ctx.rrup, delta=1e-3)

    def test_rx_distance(self):
        rx = self.rup.surface.get_rx_distance(self.sitec.mesh)
        self.assertAlmostEqual(rx, self.ctx.rx, delta=1e-3)

    def test_ry0_distance(self):
        dst = self.rup.surface.get_ry0_distance(self.sitec.mesh)
        self.assertAlmostEqual(dst, self.ctx.ry0, delta=1e-3)


class FastRatesTestCase(unittest.TestCase):
    """
    Optimized ways to compute the rates for a source
    """
    @classmethod
    def setUpClass(cls):
        job_ini = os.path.join(os.path.dirname(__file__), 'data/area/job.ini')
        oq = readinput.get_oqparam(job_ini)
        csm = readinput.get_composite_source_model(oq)
        # the uncertainties are applied in the workers, one set of
        # realizations at a time, so the groups below are the sets of
        # realizations with the same uncertainties, as in classical
        [cls.grp] = csm.src_groups
        bset_values = get_bset_values(csm.full_lt, cls.grp)
        cls.src_groups = [sg for _trt, sg
                          in modified_groups(cls.grp, bset_values)]
        cls.sources = [sg[0] for sg in cls.src_groups]
        cls.cmakers = get_cmakers([sg[0].trt_smrs for sg in cls.src_groups],
                                  csm.full_lt, oq)
        cls.sitecol = readinput.get_site_collection(oq)
        with Monitor('get_rmap', measuremem=True) as cls.mon:
            cls.rmap = cls.cmakers.get_rmap(cls.src_groups, cls.sitecol)

    def test_get_rmaps(self):
        # changing 100 times abGR on an area sources is 10x faster
        # and allocates 10x less memory with get_rmaps
        with Monitor('get_rmaps', measuremem=True) as mon:
            rmaps = self.cmakers.get_rmaps(self.sources, self.sitecol)
        print(self.mon)
        print(mon)
        aac(self.rmap.array[:, :, 0], rmaps[0].array[:, :, 0])
        aac(self.rmap.array[:, :, 99], rmaps[99].array[:, :, 0])


class PlanarDistancesTestCase(unittest.TestCase):
    """
    Test for calculation of planar distances
    """
    def test(self):
        trt = TRT.ACTIVE_SHALLOW_CRUST
        rms = 2.5
        msr = WC1994()
        rar = 1.0
        tom = PoissonTOM(1.)
        usd = 0.0
        lsd = 20.0
        loc = Point(0.0, 0.0)
        mfd = ArbitraryMFD([7.0], [1.])
        npd = PMF([(1.0, NodalPlane(90., 90., 90.))])
        hdd = PMF([(1.0, 10.)])
        imtls = DictArray({'PGA': [0.01]})
        gsims = [valid.gsim('GulerceEtAl2017'),
                 valid.gsim('Atkinson2015'),
                 valid.gsim('YuEtAl2013Ms')]
        src = PointSource(
            "ps", "pointsource", trt, mfd, rms, msr, rar, tom,
            usd, lsd, loc, npd, hdd)

        sites = SiteCollection([Site(Point(0.25, 0.0, 0.0)),
                                Site(Point(0.35, 0.0, 0.0))])
        cmaker = ContextMaker(
            trt, gsims, dict(imtls=imtls, truncation_level=3.))
        cmaker.tom = tom
        [ctx] = cmaker.get_ctxs(src, sites)
        aac(ctx.rrup, [9.32409196, 20.44343079])
        aac(ctx.rx, [0., 0.])
        aac(ctx.ry0, [9.26597563, 20.38546829])
        aac(ctx.rjb, [9.26597481, 20.3854596])
        aac(ctx.rhypo, [29.54267222, 40.18243627])
        aac(ctx.rjb, [9.26597481, 20.3854596])
        aac(ctx.repi, [27.79873166, 38.91822433])
        aac(ctx.azimuth, [0., 0.])

        magd = [(r, mag) for mag, r in src.get_annual_occurrence_rates()]
        planin = src.get_planin(magd, npd.data)
        planar = build_planar(planin, numpy.array(hdd.data),
                              loc.x, loc.y, usd, lsd, rar)[0, 0]
        for par in ('rx', 'ry0', 'rjb', 'rhypo', 'repi'):
            dist = get_distances_planar(planar, sites, par)[0]
            aac(dist, ctx[par], err_msg=par)

    def test_from_planar(self):
        s = site.Site(Point(0, 0), vs30=760,
                      vs30measured=False, z1pt0=20, z2pt5=30)
        msr = WC1994()
        mag = 5.0
        aratio = 1.
        strike = 0.
        dip = 90.
        rake = 45
        trt = TRT.ACTIVE_SHALLOW_CRUST
        rup = get_planar(s, msr, mag, aratio, strike, dip, rake, trt)
        gsims = [AbrahamsonEtAl2014()]
        cm = ContextMaker(trt, gsims, dict(imtls={'PGA': []}))
        ctx = cm.from_planar(rup, hdist=100, step=5)
        mea, sig, tau, phi = cm.get_mean_stds([ctx])
        # in this example sig, tau, phi are constant on all sites
        aac(sig, .79162428)
        aac(tau, .47)
        aac(phi, .637)

        # test att_curves which are functions N-distances -> (G, M, N) arrays
        mea, sig, tau, phi = cm.get_att_curves(s, msr, mag)
        aac(mea([100., 200.]), [[[-6.21035514, -7.8108702]]])  # shp (1, 1, 2)

    def test_clon_clat_planar(self):
        # point-source ctx has clon/clat filled when the GSIM asks for them,
        # otherwise the planar path would crash looking for a get_clon function
        trt = TRT.SUBDUCTION_INTRASLAB
        tom = PoissonTOM(1.)
        src = PointSource(
            "ps", "pointsource", trt, ArbitraryMFD([7.0], [1.]),
            2.5, WC1994(), 1.0, tom, 0.0, 100.0, Point(0.0, 0.0),
            PMF([(1.0, NodalPlane(90., 90., 90.))]), PMF([(1.0, 50.)]))
        sites = SiteCollection([
            Site(Point(0.1 * i, 0.0, 0.0), vs30=760, vs30measured=True,
                 z1pt0=20, z2pt5=30) for i in range(1, 4)])
        cmaker = contexts.simple_cmaker(
            [valid.gsim('ZhaoEtAl2016SSlabPErg')], ['PGA'])
        cmaker.tom = tom
        [ctx] = cmaker.get_ctxs(src, sites)
        aac(ctx.clat, 0., atol=1e-6)  # sites and source on the equator
        self.assertTrue(numpy.all(numpy.isfinite(ctx.clon)))


class EstimateNctxsTestCase(unittest.TestCase):
    def setUp(self):
        self.src = PointSource(
            'ps', 'pointsource', '*',
            ArbitraryMFD([4., 5., 6., 7.], [.1] * 4), 1., PointMSR(), 1.,
            tom, 0., 20., Point(0., 0.),
            PMF([(1., NodalPlane(0., 90., 0.))]),
            PMF([(.5, 5.), (.5, 10.)]))
        self.cmaker = contexts.simple_cmaker(
            [valid.gsim('ToroEtAl2002')], ['PGA'],
            maximum_distance={'default': [(5., 25.), (6., 25.)]},
            pointsource_distance={'default': 10.})
        self.sites = SiteCollection([Site(Point(0., 0., dep))
                                     for dep in [0., 10., 20., 30.]])

    def test_close_and_far(self):
        # Two magnitudes survive. Each has two close sites (including the
        # pointsource-distance boundary), one far site and one outside.
        for max_sites, expected in [(0, 10), (10, 12)]:
            self.cmaker.max_sites_disagg = max_sites
            self.assertEqual(contexts.estimate_nctxs(
                self.cmaker, [self.src], self.sites), expected)
            self.assertEqual(contexts.estimate_nctxs(
                self.cmaker, [self.src] * 2, self.sites), expected * 2)
        self.assertEqual(contexts.estimate_nctxs(
            self.cmaker, [], self.sites), 0)

    def test_filtered_sites(self):
        # The complete collection determines fewsites, even when the
        # filtered collection is below the threshold.
        self.cmaker.max_sites_disagg = 2
        sites = self.sites.filtered([1, 2])
        self.assertEqual(contexts.estimate_nctxs(
            self.cmaker, [self.src], sites), 6)

    def test_magnitude_distance_boundary(self):
        # A site exactly at maximum_distance is counted by the estimate,
        # although it generates no contexts: the estimate is approximate.
        sites = SiteCollection.from_points([0.], [0.], [25.])
        for max_sites in [0, 10]:
            for psdist in [25., 30.]:
                self.cmaker.max_sites_disagg = max_sites
                self.cmaker.pointsource_distance = psdist
                self.assertEqual(contexts.estimate_nctxs(
                    self.cmaker, [self.src], sites), 4)


class SharedGSIMTestCase(unittest.TestCase):
    def test_europe_backbones(self):
        fname = os.path.join(os.path.dirname(mosaic.__file__),
                             'EUR', 'in', 'gmmLT.xml')
        trts = ('Shallow Default', 'Craton', 'Subduction Interface',
                'Subduction Inslab', 'Non-Subduction Deep',
                'Iceland Atlantic Active Region')
        gsims_by_trt = GsimLogicTree(fname, trts).values
        for trt in trts:
            with self.subTest(trt=trt):
                cm = contexts.simple_cmaker(gsims_by_trt[trt],
                                            ['PGA', 'SA(0.5)'])
                ctx = cm.new_ctx(2)
                ctx.mag = [6.0, 7.2]
                ctx.rrup = [30.0, 110.0]
                ctx.vs30 = [300.0, 900.0]
                if 'rjb' in ctx.dtype.names:
                    ctx.rjb = ctx.rrup - 5
                if 'hypo_depth' in ctx.dtype.names:
                    ctx.hypo_depth = [18.0, 55.0]
                if 'xvf' in ctx.dtype.names:
                    ctx.xvf = [-80.0, 80.0]
                with mock.patch.object(cm, '_compute_group',
                                       wraps=cm._compute_group) as grouped:
                    actual = cm.get_mean_stds([ctx[:1], ctx[1:]])
                groups = [call.args[1] for call in grouped.call_args_list]
                sizes = [len(pairs) for pairs in groups]
                self.assertEqual(sizes.count(5), 3)
                expected = numpy.stack([
                    cm.get_4MN([ctx[:1], ctx[1:]], gsim)
                    for gsim in cm.gsims], axis=1)
                numpy.testing.assert_array_equal(actual, expected)

    def test_nshmp_preserves_poe_adjustment(self):
        gsims = [
            valid.gsim(f'AbrahamsonEtAl2014NSHMP{suffix}')
            for suffix in ('Lower', 'Mean', 'Upper')]
        cm = contexts.simple_cmaker(gsims, ['PGA', 'SA(0.5)'])
        ctx = cm.new_ctx(2)
        ctx.mag = [5.8, 7.2]
        ctx.rrup = [7.0, 40.0]
        ctx.rjb = [5.0, 35.0]
        ctx.vs30 = [300.0, 900.0]
        ctx.dip = 60.0
        ctx.width = 15.0
        slices = [ctx[:1], ctx[1:]]
        for maker in (cm, cm.copy(gsims=gsims + [gsims[1]])):
            with self.subTest(branches=len(maker.gsims)):
                expected = numpy.stack([maker.get_4MN(slices, gsim)
                                        for gsim in maker.gsims], axis=1)
                adj = [gsim.adj.copy() for gsim in maker.gsims]
                with mock.patch.object(maker, '_compute_group',
                                       wraps=maker._compute_group) as grouped:
                    actual = maker.get_mean_stds(slices, split_by_mag=False)
                grouped.assert_called_once()
                numpy.testing.assert_array_equal(actual, expected)
                for gsim, expected_adj in zip(maker.gsims, adj):
                    numpy.testing.assert_array_equal(gsim.adj, expected_adj)

    def test_shared_kwargs_preserve_coefficient_overrides(self):
        coeffs = {'PGA': {'c0': -4.}}
        lower = CampbellBozorgnia2014(coeffs=coeffs, sigma_mu_epsilon=-1.)
        coeffs['PGA']['c0'] = -3.
        upper = CampbellBozorgnia2014(coeffs=coeffs, sigma_mu_epsilon=1.)
        cm = contexts.simple_cmaker([lower, upper], ['PGA'])
        ctx = cm.new_ctx(1)
        ctx.mag, ctx.vs30, ctx.rrup, ctx.rjb = 6.2, 350., 10., 9.
        ctx.rx, ctx.z2pt5, ctx.rake = 2., 1.2, 0.
        ctx.dip, ctx.ztor, ctx.width, ctx.hypo_depth = 60., 4., 16., 10.
        expected = numpy.stack([cm.get_4MN([ctx], gsim)
                                for gsim in cm.gsims], axis=1)
        numpy.testing.assert_array_equal(cm.get_mean_stds([ctx]), expected)

    def test_independent_median_and_sigma_scaling(self):
        options = {'gmpe': {'AkkarEtAlRjb2014': {}},
                   'set_scale_total_sigma_vector': {
                       'scaling_factor': {'PGA': 0.8}}}
        lower = ModifiableGMPE(
            **options, set_scale_median_scalar={'scaling_factor': 0.9})
        options['set_scale_total_sigma_vector']['scaling_factor']['PGA'] = 1.2
        upper = ModifiableGMPE(
            **options, set_scale_median_scalar={'scaling_factor': 1.1})
        cm = contexts.simple_cmaker([lower, upper], ['PGA'])
        ctx = cm.new_ctx(1)
        ctx.mag, ctx.vs30, ctx.rjb, ctx.rake = 6.2, 350., 9., 0.
        with mock.patch.object(lower.gmpe, 'compute',
                               wraps=lower.gmpe.compute) as backbone:
            actual = cm.get_mean_stds([ctx])
        backbone.assert_called_once()
        self.assertEqual(lower.central_key, upper.central_key)
        expected = numpy.stack([cm.get_4MN([ctx], gsim)
                                for gsim in cm.gsims], axis=1)
        numpy.testing.assert_array_equal(actual, expected)

    def test_kuehn_interpolates_once_per_imt_and_slice(self):
        gsims = [kuehn_2020.KuehnEtAl2020SInter(sigma_mu_epsilon=eps)
                 for eps in (0., -1., 1.)]
        cm = contexts.simple_cmaker(gsims, ['PGA', 'SA(0.5)'])
        ctx = cm.new_ctx(2)
        ctx.mag, ctx.rrup, ctx.vs30 = [6., 7.2], [30., 110.], [300., 900.]
        slices = [ctx[:1], ctx[1:]]
        get_adjustment = kuehn_2020.get_sigma_mu_adjustment
        with mock.patch.object(kuehn_2020, 'get_sigma_mu_adjustment',
                               wraps=get_adjustment) as interpolate:
            actual = cm.get_mean_stds(slices, split_by_mag=False)
        self.assertEqual(interpolate.call_count, len(cm.imts) * len(slices))
        expected = numpy.stack([cm.get_4MN(slices, gsim)
                                for gsim in cm.gsims], axis=1)
        numpy.testing.assert_array_equal(actual, expected)


class CollapseCtxTestCase(unittest.TestCase):
    def test(self):
        # the first two rows have the same site, rupture parameters and
        # distances within 1%, so they are merged; the others differ by
        # distance, site or rake
        ctx = numpy.rec.fromarrays(
            [[0, 0, 0, 1, 0], [6.5] * 5, [90., 90., 90., 90., 0.],
             [106., 106.2, 150., 106., 106.], [107., 107.2, 152., 107., 107.],
             [.01, .03, .01, .01, .01]],
            names='sids,mag,rake,rjb,rrup,occurrence_rate')
        out = collapse_ctx(ctx, {'mag', 'rake'}, {'rjb'}, .01)
        self.assertEqual(len(out), 4)
        [row] = out[(out.sids == 0) & (out.rake == 90.) & (out.rjb < 120)]
        numpy.testing.assert_allclose(row.occurrence_rate, .04)
        numpy.testing.assert_allclose(row.rjb, (106 * .01 + 106.2 * .03) / .04)
        numpy.testing.assert_allclose(row.rrup, (107 * .01 + 107.2 * .03) / .04)

        # nonpoissonian ruptures are not collapsed
        ctx.occurrence_rate[:] = numpy.nan
        self.assertEqual(len(collapse_ctx(ctx, {'mag'}, {'rjb'}, .01)), 5)

    def test_exact_rupture_parameters(self):
        # Small differences must survive, including for signed parameters.
        for par, value in [('mag', 6.5), ('hypo_lon', -120.), ('hypo_lat', -30.),
                           ('hypo_depth', -.1), ('ztor', 5.)]:
            with self.subTest(par=par):
                ctx = numpy.rec.fromarrays(
                    [[0] * 3, [value, value, value + .0001],
                     [106.] * 3, [.01, .03, .02]],
                    names=f'sids,{par},rrup,occurrence_rate')
                out = collapse_ctx(ctx, {par}, {'rrup'}, .01)
                self.assertEqual(len(out), 2)
                numpy.testing.assert_array_equal(
                    out[par], [value, value + .0001])
                numpy.testing.assert_allclose(out.occurrence_rate, [.04, .02])

    def test_rounded_angles(self):
        # Group by rounded angles while retaining original context values.
        for par, value in [('dip', 30.), ('strike', 120.), ('rake', -90.)]:
            with self.subTest(par=par):
                angles = [value + .01, value + .04, value + .06]
                ctx = numpy.rec.fromarrays(
                    [[0] * 3, angles, [106.] * 3, [.01, .03, .02]],
                    names=f'sids,{par},rrup,occurrence_rate')
                out = collapse_ctx(ctx, {par}, {'rrup'}, .01)
                self.assertEqual(len(out), 2)
                numpy.testing.assert_array_equal(out[par],
                                                 [angles[0], angles[2]])
                numpy.testing.assert_allclose(out.occurrence_rate, [.04, .02])

    def test_rounded_width(self):
        # The width is rounded to 0.1 km, since the widths of the ruptures
        # of a fault differ by mesh noise; NaN parameters compare equal
        widths = [10.01, 10.04, 10.06]
        ctx = numpy.rec.fromarrays(
            [[0] * 3, widths, [numpy.nan] * 3, [106.] * 3, [.01, .03, .02]],
            names='sids,width,crjb,rrup,occurrence_rate')
        out = collapse_ctx(ctx, {'width', 'crjb'}, {'rrup'}, .01)
        self.assertEqual(len(out), 2)
        numpy.testing.assert_array_equal(out.width, [widths[0], widths[2]])
        numpy.testing.assert_allclose(out.occurrence_rate, [.04, .02])


# the rows of a context array sorted, to compare arrays built in a
# different order
def _sorted_rows(ctx):
    fields = ['sids', 'mag', 'rrup', 'rjb', 'occurrence_rate']
    idx = numpy.lexsort([ctx[f] for f in reversed(fields)])
    return [ctx[f][idx] for f in fields]


class FromSrcsPsdistsTestCase(unittest.TestCase):
    def test_batch_magnitudes(self):
        # Batching must preserve magnitude-dependent filtering and the
        # original context rows, including the few-sites rupture IDs.
        src = PointSource(
            'ps', 'pointsource', '*',
            ArbitraryMFD([4., 5., 6., 7.], [.1] * 4), 1., WC1994(), 1.5,
            tom, 0., 20., Point(0., 0.),
            PMF([(1., NodalPlane(0., 45., 90.))]), PMF([(1., 5.)]))
        sites = SiteCollection([Site(Point(lon, 0.))
                                for lon in [0., .1, .4, 1.]])
        cmaker = contexts.simple_cmaker(
            [valid.gsim('ToroEtAl2002')], ['PGA'],
            maximum_distance={'default': [(5., 25.), (6., 100.)]})
        for max_sites in [0, 10]:
            cmaker.max_sites_disagg = max_sites
            expected = cmaker.from_srcs([src], sites, [15., 100.])
            batched = cmaker.copy(batch_point_sources=True)
            actual = batched.from_srcs([src], sites, [15., 100.])
            for psd in expected:
                numpy.testing.assert_array_equal(actual[psd], expected[psd])

    def test(self):
        # the contexts built at once for several pointsource distances
        # must be the same as the contexts built for each distance
        src = AreaSource(
            'area', 'area', '*', TruncatedGRMFD(5., 7.5, .25, 3., 1.), 2.,
            WC1994(), 1.5, PoissonTOM(1.), 0., 20.,
            PMF([(.5, NodalPlane(0., 90., 0.)),
                 (.5, NodalPlane(90., 45., 90.))]),
            PMF([(.5, 5.), (.5, 10.)]),
            Polygon([Point(0., 0.), Point(0., 1.), Point(1., 1.),
                     Point(1., 0.)]), 10.)
        srcs = grid_point_sources(list(split_source(src)), 25.)
        self.assertTrue(any(s.code == b'p' for s in srcs))  # collapsed
        sites = SiteCollection([Site(Point(lon, lat))
                                for lon in numpy.linspace(-1., 2., 7)
                                for lat in numpy.linspace(-1., 2., 7)])
        cmaker = contexts.simple_cmaker(
            [valid.gsim('ToroEtAl2002')], ['PGA'],
            maximum_distance={'default': [(5., 200.), (8., 200.)]})
        psds = [15., 25., 50., 100.]
        ctxs = cmaker.from_srcs(srcs, sites, psds)
        nctxs = [len(ctxs[psd]) for psd in psds]
        self.assertEqual(nctxs, sorted(set(nctxs)))  # strictly growing
        for psd in psds:
            exp = cmaker.copy(pointsource_distance=psd).from_srcs(srcs, sites)
            for got, ex in zip(_sorted_rows(ctxs[psd]), _sorted_rows(exp)):
                numpy.testing.assert_array_equal(got, ex)


class CubicPoETestCase(unittest.TestCase):
    def test_grid_and_truncation(self):
        # Exercise table centres, midpoints, cutoff, tails, and exact path.
        for cutoff in (1e-9, .68, 5., 9.):
            phi = stats.ndtr(cutoff)
            tmax = stats.get_tmax(phi)
            x = numpy.r_[numpy.arange(-10., 10., 1/128), tmax,
                         numpy.nextafter(tmax, numpy.inf), numpy.nan,
                         -numpy.inf, numpy.inf]
            mean_std = numpy.zeros((2, 1, 1))
            mean_std[1] = 1.
            actual = numpy.empty((len(x), 1), numpy.float32)
            contexts._set_poes(mean_std, x[None, :], phi, actual)
            exact = [stats._truncnorm_sf(phi, tmax, v) for v in x]
            aac(actual[:, 0], exact, atol=1e-8, rtol=1e-5)
            self.assertTrue((actual[x > tmax] == 0.).all())
