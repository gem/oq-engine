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
import numpy

from openquake.baselib.general import DictArray
from openquake.hazardlib import read_input, calc, site
from openquake.hazardlib.pmf import PMF
from openquake.hazardlib.const import TRT
from openquake.hazardlib.tom import PoissonTOM
from openquake.hazardlib.contexts import (
    Effect, ContextMaker, Collapser, get_distances)
from openquake.hazardlib import valid
from openquake.hazardlib.geo.surface import SimpleFaultSurface as SFS
from openquake.hazardlib.source.rupture import \
    get_planar, NonParametricProbabilisticRupture as NPPR
from openquake.hazardlib.geo import Line, Point
from openquake.hazardlib.site import Site, SiteCollection
from openquake.hazardlib.source import PointSource
from openquake.hazardlib.mfd import ArbitraryMFD
from openquake.hazardlib.scalerel import WC1994
from openquake.hazardlib.geo.nodalplane import NodalPlane
from openquake.hazardlib.geo.surface.planar import (
    get_distances_planar, build_planar)
from openquake.hazardlib.sourceconverter import SourceConverter
from openquake.hazardlib.nrml import to_python
from openquake.hazardlib.gsim.abrahamson_2014 import AbrahamsonEtAl2014

PLOTTING = False
aac = numpy.testing.assert_allclose
dists = numpy.array([0, 10, 20, 30, 40, 50])
intensities = {
    '4.5': numpy.array([1.0, .95, .7, .6, .5, .3]),
    '5.0': numpy.array([1.2, 1.1, .7, .69, .6, .5]),
    '5.5': numpy.array([1.5, 1.2, .89, .85, .82, .6]),
    '6.0': numpy.array([2.0, 1.5, .9, .85, .81, .6])}
tom = PoissonTOM(50.)
JOB = os.path.join(os.path.dirname(__file__), 'data/context/job.ini')
BASE_PATH = os.path.dirname(__file__)


def rms(delta):
    return numpy.sqrt((delta**2).sum())


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
        param = 'closest_point'
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
        param = 'closest_point'
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
        param = 'closest_point'
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


class EffectTestCase(unittest.TestCase):
    def test_dist_by_mag(self):
        effect = Effect(intensities, dists)
        dist = list(effect.dist_by_mag(0).values())
        numpy.testing.assert_allclose(dist, [50, 50, 50, 50])

        dist = list(effect.dist_by_mag(.9).values())
        numpy.testing.assert_allclose(dist, [12, 15, 19.677419, 20])

        dist = list(effect.dist_by_mag(1.1).values())
        numpy.testing.assert_allclose(dist, [0, 10, 13.225806, 16.666667])


# see also classical/case_24 and classical/case_69
class CollapseTestCase(unittest.TestCase):

    def test_collapse_small(self):
        inp = read_input(JOB)  # has pointsource_distance=50
        cmaker = inp.cmaker
        [[area]] = inp.groups  # there is a single AreaSource
        srcs = list(area)  # split in 3+3 PointSources

        # check the weights
        cmaker.set_weight(srcs, inp.sitecol)
        weights = [src.weight for src in srcs]  # 3 within, 3 outside
        numpy.testing.assert_allclose(
            weights, [10.1, 10.1, 10.1, 0.101, 0.101, 0.101])

        # set different vs30s on the two sites
        inp.sitecol.array['vs30'] = [600., 700.]
        ctxs = cmaker.from_srcs(srcs, inp.sitecol)
        # the 3 sources within are still more distant than the pointsource
        # distance, so the 4 hypocenters are collapsed to 1 and the number
        # of ruptures is down from 30 x 4 to 30
        numpy.testing.assert_equal(len(ctxs[0]), 60)  # 2sites x 3srcs x 10mags

        # compute original curves
        pmap = cmaker.get_pmap(ctxs)
        numpy.testing.assert_equal(cmaker.collapser.cfactor, [60, 60, 10])

        # compute collapsed curves
        cmaker.collapser.cfactor = numpy.zeros(3)
        cmaker.collapser.collapse_level = 1
        cmap = cmaker.get_pmap(ctxs)
        self.assertLess(rms(pmap.array[0] - cmap.array[0]), 7E-4)
        self.assertLess(rms(pmap.array[1] - cmap.array[0]), 7E-4)
        numpy.testing.assert_equal(cmaker.collapser.cfactor, [40, 60, 10])

    def test_collapse_big(self):
        smpath = os.path.join(os.path.dirname(__file__),
                              'data/context/source_model.xml')
        params = dict(
            sites=[(0, 1), (0, 2)],
            maximum_distance=calc.filters.IntegrationDistance.new('300'),
            imtls=dict(PGA=numpy.arange(.1, 5, .1)),
            investigation_time=50.,
            gsim='BooreAtkinson2008',
            reference_vs30_value=600.,
            inputs=dict(source_model=smpath),
            area_source_discretization=1.)
        inp = read_input(params)
        cmaker = inp.cmaker
        [srcs] = inp.groups  # a single area source
        # get the context
        ctxs = cmaker.from_srcs(srcs, inp.sitecol)
        pcurve0 = cmaker.get_pmap(ctxs).array[0]
        cmaker.collapser.cfactor = numpy.zeros(3)
        cmaker.collapser.collapse_level = 1
        pcurve1 = cmaker.get_pmap(ctxs).array[0]
        self.assertLess(numpy.abs(pcurve0 - pcurve1).sum(), 1E-9)
        numpy.testing.assert_equal(cmaker.collapser.cfactor, [94, 11616, 2])

    def test_collapse_azimuth(self):
        # YuEtAl2013Ms has an azimuth distance causing a lower precision
        # in the collapse even if we are collapsing far less than before
        src = '''\
        <simpleFaultSource
        id="3"
        name="Simple Fault Source"
        tectonicRegion="Active Shallow Crust"
        >
        <simpleFaultGeometry>
        <gml:LineString>
        <gml:posList>
          1 -0.2 1.4 0 1.7 0
        </gml:posList>
        </gml:LineString>
        <dip>
          3
        </dip>
        <upperSeismoDepth>
          5
        </upperSeismoDepth>
        <lowerSeismoDepth>
          15
        </lowerSeismoDepth>
        </simpleFaultGeometry>
        <magScaleRel>
          WC1994
        </magScaleRel>
        <ruptAspectRatio>
          2
        </ruptAspectRatio>
        <truncGutenbergRichterMFD
          aValue="4.2" bValue=".9" maxMag="7" minMag="6.5"/>
        <rake>
          90
        </rake>
        </simpleFaultSource>'''
        params = dict(
            sites=[(1.1, -1.1), (1.1, -1.9)],
            maximum_distance=calc.filters.IntegrationDistance.new('300'),
            imtls=dict(PGA=numpy.arange(.001, .45, .001)),
            investigation_time=50.,
            source_string=src,
            rupture_mesh_spacing=10,
            width_of_mfd_bin=.5,  # so that there is a single magnitude
            gsim='YuEtAl2013Ms', inputs={},
            reference_vs30_value=600.)
        inp = read_input(params)
        cmaker = inp.cmaker
        [grp] = inp.groups
        self.assertEqual(len(grp.sources), 1)  # not splittable source
        poes = cmaker.get_poes(grp, inp.sitecol)
        cmaker.collapser = Collapser(
            collapse_level=1, kfields=cmaker.REQUIRES_DISTANCES)
        newpoes = cmaker.get_poes(inp.groups[0], inp.sitecol)
        if PLOTTING:
            import matplotlib.pyplot as plt
            imls = cmaker.imtls['PGA']
            plt.plot(imls, poes[0, :, 0], '-', label='0-old')
            plt.plot(imls, newpoes[0, :, 0], '-', label='0-new')
            plt.plot(imls, poes[1, :, 0], '-', label='1-old')
            plt.plot(imls, newpoes[1, :, 0], '-', label='1-new')
            plt.legend()
            plt.show()
        maxdiff = numpy.abs(newpoes - poes).max(axis=(1, 2))
        print('maxdiff =', maxdiff, cmaker.collapser.cfactor)

    def test_collapse_area(self):
        # collapse an area source using a GMPE with the azimuth distance
        src = '''\
        <areaSource
          id="1"
          name="Area Source"
          tectonicRegion="Active Shallow Crust"
        >
        <areaGeometry>
        <gml:Polygon>
        <gml:exterior>
        <gml:LinearRing>
        <gml:posList>
          -.5 -.5 -.3 -.1 .1 .2 .3 -.8
        </gml:posList>
        </gml:LinearRing>
        </gml:exterior>
        </gml:Polygon>
        <upperSeismoDepth>
        0
        </upperSeismoDepth>
        <lowerSeismoDepth>
        10
        </lowerSeismoDepth>
        </areaGeometry>
        <magScaleRel>
        WC1994
        </magScaleRel>
        <ruptAspectRatio>
        1
        </ruptAspectRatio>
        <truncGutenbergRichterMFD
          aValue="4.5" bValue="1" maxMag="6.5" minMag="5"/>
        <nodalPlaneDist>
        <nodalPlane dip="90" probability="1" rake="0" strike="0"/>
        </nodalPlaneDist>
        <hypoDepthDist>
        <hypoDepth depth="5" probability="1"/>
        </hypoDepthDist>
        </areaSource>
        '''
        params = dict(
            sites=[(1.1, -1.1), (1.1, -1.9)],
            maximum_distance=calc.filters.IntegrationDistance.new('300'),
            imtls=dict(PGA=numpy.arange(.001, .45, .001)),
            investigation_time=50.,
            source_string=src,
            area_source_discretization=10,
            width_of_mfd_bin=.5,  # so that there are only 3 magnitudes
            gsim='YuEtAl2013Ms', inputs={},
            reference_vs30_value=600.)
        inp = read_input(params)
        cmaker = inp.cmaker

        [grp] = inp.groups
        self.assertEqual(len(grp.sources), 52)  # point sources
        poes = cmaker.get_poes(grp, inp.sitecol)  # no collapse

        # collapse_level = 0
        newpoes = cmaker.get_poes(inp.groups[0], inp.sitecol, collapse_level=0)
        if PLOTTING:
            import matplotlib.pyplot as plt
            imls = cmaker.imtls['PGA']
            plt.plot(imls, poes[0, :, 0], '-', label='0-old')
            plt.plot(imls, newpoes[0, :, 0], '-', label='0-new')
            plt.plot(imls, poes[1, :, 0], '-', label='1-old')
            plt.plot(imls, newpoes[1, :, 0], '-', label='1-new')
            plt.legend()
            plt.show()
        maxdiff = numpy.abs(newpoes - poes).max(axis=(1, 2))  # shape NLG => N
        print('maxdiff =', maxdiff)
        self.assertLess(maxdiff[0], 2E-3)
        self.assertLess(maxdiff[1], 6E-4)
        numpy.testing.assert_equal(cmaker.collapser.cfactor, [312, 312, 3])


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
        src = ssm[0][0]
        sections = list(geom.sections.values())
        s2i = {suid: i for i, suid in enumerate(geom.sections)}
        src.rupture_idxs = [tuple(s2i[idx] for idx in idxs)
                            for idxs in src.rupture_idxs]
        src.set_sections(sections)
        self.src = src

        # Create site-collection
        site = Site(Point(0.05, 0.2), vs30=760, z1pt0=30, z2pt5=0.5,
                    vs30measured=True)
        self.sitec = SiteCollection([site])

        # Create the context maker
        gmm = AbrahamsonEtAl2014()
        param = dict(imtls={'PGA': []})
        cm = ContextMaker('*', [gmm], param)

        # extract magnitude 7 context
        [ctx] = cm.get_ctx_iter(self.src, self.sitec)
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
        src = ssm[0][0]
        sections = list(geom.sections.values())
        s2i = {suid: i for i, suid in enumerate(geom.sections)}
        src.rupture_idxs = [tuple(s2i[idx] for idx in idxs)
                            for idxs in src.rupture_idxs]
        src.set_sections(sections)
        self.src = src

        # Create site-collection
        site = Site(Point(0.05, 0.2), vs30=760, z1pt0=30, z2pt5=0.5,
                    vs30measured=True)
        self.sitec = SiteCollection([site])

        # Create the context maker
        gmm = AbrahamsonEtAl2014()
        param = dict(imtls={'PGA': []})
        cm = ContextMaker('*', [gmm], param)

        # extract magnitude 7 context
        [ctx] = cm.get_ctx_iter(self.src, self.sitec)
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
        ctx, = cmaker.get_ctx_iter(src, sites)
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
                              loc.x, loc.y, usd, lsd)[0, 0]
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
