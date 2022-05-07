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
from openquake.hazardlib import read_input, calc
from openquake.hazardlib.pmf import PMF
from openquake.hazardlib.const import TRT
from openquake.hazardlib.tom import PoissonTOM
from openquake.hazardlib.contexts import (
    Effect, RuptureContext, ContextMaker, Collapser, get_distances)
from openquake.hazardlib import valid
from openquake.hazardlib.geo.surface import SimpleFaultSurface as SFS
from openquake.hazardlib.source.rupture import \
    NonParametricProbabilisticRupture as NPPR
from openquake.hazardlib.geo import Line, Point
from openquake.hazardlib.site import Site, SiteCollection
from openquake.hazardlib.source import PointSource
from openquake.hazardlib.mfd import ArbitraryMFD
from openquake.hazardlib.scalerel import WC1994
from openquake.hazardlib.geo.nodalplane import NodalPlane
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

    def test_get_pmap(self):
        truncation_level = 3
        imtls = DictArray({'PGA': [0.01]})
        gsims = [valid.gsim('AkkarBommer2010')]
        ctxs = []
        for occ_rate in (.001, .002):
            ctx = RuptureContext()
            ctx.mag = 5.5
            ctx.rake = 90
            ctx.occurrence_rate = occ_rate
            ctx.sids = numpy.array([0.])
            ctx.vs30 = numpy.array([760.])
            ctx.rrup = numpy.array([100.])
            ctx.rjb = numpy.array([99.])
            ctx.weight = 0.
            ctxs.append(ctx)
        cmaker = ContextMaker(
            'TRT', gsims, dict(imtls=imtls, truncation_level=truncation_level))
        cmaker.tom = PoissonTOM(time_span=50)
        pmap = cmaker.get_pmap(ctxs)
        numpy.testing.assert_almost_equal(pmap[0].array, 0.066381)


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
            weights, [7.8, 7.8, 7.8, 1, 1, 1])

        # set different vs30s on the two sites
        inp.sitecol.array['vs30'] = [600., 700.]
        ctxs = cmaker.from_srcs(srcs, inp.sitecol)
        # the 3 sources within are still more distant than the pointsource
        # distance, so the 4 hypocenters are collapsed to 1 and the number
        # of ruptures is down from 30 x 4 to 30
        numpy.testing.assert_equal(len(ctxs), 30)  # 3x10 mags

        # compute original curves
        pmap = cmaker.get_pmap(ctxs)
        numpy.testing.assert_equal(cmaker.collapser.cfactor, [34, 60])

        # compute collapsed curves
        cmaker.collapser.cfactor = numpy.zeros(2)
        cmaker.collapser.collapse_level = 1
        cmap = cmaker.get_pmap(ctxs)
        self.assertLess(rms(pmap[0].array - cmap[0].array), 3E-4)
        self.assertLess(rms(pmap[1].array - cmap[1].array), 3E-4)
        numpy.testing.assert_equal(cmaker.collapser.cfactor, [34, 60])

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
            source_model_file=smpath,
            area_source_discretization=1.)
        inp = read_input(params)
        cmaker = inp.cmaker
        [srcs] = inp.groups  # a single area source
        # get the context
        ctxs = cmaker.from_srcs(srcs, inp.sitecol)
        numpy.testing.assert_equal(len(ctxs), 5808)
        pcurve0 = cmaker.get_pmap(ctxs)[0]
        cmaker.collapser.cfactor = numpy.zeros(2)
        cmaker.collapser.collapse_level = 1
        pcurve1 = cmaker.get_pmap(ctxs)[0]
        self.assertLess(numpy.abs(pcurve0.array - pcurve1.array).sum(), 1E-6)
        numpy.testing.assert_equal(cmaker.collapser.cfactor, [218, 11616])

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
            gsim='YuEtAl2013Ms',
            reference_vs30_value=600.)
        inp = read_input(params)
        cmaker = inp.cmaker
        [grp] = inp.groups
        self.assertEqual(len(grp.sources), 1)  # not splittable source
        poes = cmaker.get_poes(grp, inp.sitecol)
        cmaker.collapser = Collapser(collapse_level=1, dist_type='azimuth')
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
        maxdiff = (newpoes - poes).max(axis=(1, 2))
        print('maxdiff =', maxdiff, cmaker.collapser.cfactor)

        # collapse_level=2
        cmaker.collapser = Collapser(collapse_level=2, dist_type='azimuth')
        newpoes = cmaker.get_poes(inp.groups[0], inp.sitecol)
        maxdiff = (newpoes - poes).max(axis=(1, 2))
        print('maxdiff =', maxdiff, cmaker.collapser.cfactor)

    def test_collapse_area(self):
        # collapse an area source
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
            gsim='YuEtAl2013Ms',
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
        maxdiff = (newpoes - poes).max(axis=(1, 2))
        print('maxdiff =', maxdiff)
        # this is a case where the precision on site 1 is perfect, while
        # on on site 0 if far from perfect
        self.assertLess(maxdiff[0], 3E-3)
        self.assertLess(maxdiff[1], 5E-10)
        numpy.testing.assert_equal(cmaker.collapser.cfactor, [63, 312])

        # collapse_level = 4
        cmaker.collapser = Collapser(4, 'azimuth', False)
        newpoes = cmaker.get_poes(inp.groups[0], inp.sitecol, collapse_level=4)
        maxdiff = (newpoes - poes).max(axis=(1, 2))
        print('maxdiff =', maxdiff)
        # this is a case where the precision on site 0 is perfect, while
        # on on site 1 if far from perfect
        self.assertLess(maxdiff[0], 1.4E-16)
        self.assertLess(maxdiff[1], 1.4E-16)
        numpy.testing.assert_equal(cmaker.collapser.cfactor, [284, 312])


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
        src.set_sections(geom.sections)
        self.src = src

        # Create site-collection
        site = Site(Point(0.05, 0.2), vs30=760, z1pt0=30, z2pt5=0.5,
                    vs30measured=True)
        self.sitec = SiteCollection([site])

        # Create the context maker
        gmm = AbrahamsonEtAl2014()
        param = dict(imtls={'PGA': []})
        cm = ContextMaker('*', [gmm], param)

        # With this we get a list with six RuptureContexts
        ctxs = cm.get_ctxs(self.src, self.sitec)

        # Find index of rupture with three sections
        for i, ctx in enumerate(ctxs):
            if ctx.mag == 7.0:
                idx = i
        self.ctx = ctxs[idx]

    def test_rjb_distance(self):
        rjb = self.ctx.surface.get_joyner_boore_distance(self.sitec.mesh)
        self.assertAlmostEqual(rjb, self.ctx.rjb, delta=1e-3)

    def test_rrup_distance(self):
        rrup = self.ctx.surface.get_min_distance(self.sitec.mesh)
        self.assertAlmostEqual(rrup, self.ctx.rrup, delta=1e-3)

    def test_rx_distance(self):
        rx = self.ctx.surface.get_rx_distance(self.sitec.mesh)
        self.assertAlmostEqual(rx, self.ctx.rx, delta=1e-3)

    def test_ry0_distance(self):
        dst = self.ctx.surface.get_ry0_distance(self.sitec.mesh)
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
        src.set_sections(geom.sections)
        self.src = src

        # Create site-collection
        site = Site(Point(0.05, 0.2), vs30=760, z1pt0=30, z2pt5=0.5,
                    vs30measured=True)
        self.sitec = SiteCollection([site])

        # Create the context maker
        gmm = AbrahamsonEtAl2014()
        param = dict(imtls={'PGA': []})
        cm = ContextMaker('*', [gmm], param)

        # With this we get a list with six RuptureContexts
        ctxs = cm.get_ctxs(self.src, self.sitec)

        # Find index of rupture with three sections
        for i, ctx in enumerate(ctxs):
            if ctx.mag == 7.0:
                idx = i
        self.ctx = ctxs[idx]

    def test_rjb_distance(self):
        rjb = self.ctx.surface.get_joyner_boore_distance(self.sitec.mesh)
        self.assertAlmostEqual(rjb, self.ctx.rjb, delta=1e-3)

    def test_rrup_distance(self):
        rrup = self.ctx.surface.get_min_distance(self.sitec.mesh)
        self.assertAlmostEqual(rrup, self.ctx.rrup, delta=1e-3)

    def test_rx_distance(self):
        rx = self.ctx.surface.get_rx_distance(self.sitec.mesh)
        self.assertAlmostEqual(rx, self.ctx.rx, delta=1e-3)

    def test_ry0_distance(self):
        dst = self.ctx.surface.get_ry0_distance(self.sitec.mesh)
        self.assertAlmostEqual(dst, self.ctx.ry0, delta=1e-3)
