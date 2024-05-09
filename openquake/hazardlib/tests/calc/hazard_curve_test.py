# The Hazard Library
# Copyright (C) 2012-2023 GEM Foundation
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
from openquake.baselib.general import DictArray
from openquake.baselib.parallel import Starmap, sequential_apply, Monitor
from openquake.hazardlib import nrml
from openquake.hazardlib.geo import Point, Line
from openquake.hazardlib.tom import PoissonTOM
from openquake.hazardlib.calc.hazard_curve import (
    calc_hazard_curve, calc_hazard_curves)
from openquake.hazardlib.calc.filters import SourceFilter, IntegrationDistance
from openquake.hazardlib.site import Site, SiteCollection
from openquake.hazardlib.pmf import PMF
from openquake.hazardlib.geo.nodalplane import NodalPlane
from openquake.hazardlib.scalerel import WC1994, PeerMSR
from openquake.hazardlib.mfd import TruncatedGRMFD, ArbitraryMFD
from openquake.hazardlib.source import PointSource, SimpleFaultSource
from openquake.hazardlib.gsim.sadigh_1997 import SadighEtAl1997
from openquake.hazardlib.gsim.akkar_bommer_2010 import AkkarBommer2010
from openquake.hazardlib.gsim.example_a_2021 import ExampleA2021
from openquake.hazardlib.gsim.chiou_youngs_2014 import ChiouYoungs2014PEER
from openquake.hazardlib.gsim.mgmpe.avg_gmpe import AvgGMPE


class HazardCurvesFiltersTestCase(unittest.TestCase):

    def test_point_sources(self):
        sources = [
            openquake.hazardlib.source.PointSource(
                source_id='point1', name='point1',
                tectonic_region_type="Active Shallow Crust",
                mfd=openquake.hazardlib.mfd.EvenlyDiscretizedMFD(
                    min_mag=4, bin_width=1, occurrence_rates=[5]
                ),
                nodal_plane_distribution=openquake.hazardlib.pmf.PMF([
                    (1, openquake.hazardlib.geo.NodalPlane(strike=0.0,
                                                           dip=90.0,
                                                           rake=0.0))
                ]),
                hypocenter_distribution=openquake.hazardlib.pmf.PMF(
                    [(1, 10.)]),
                upper_seismogenic_depth=0.0,
                lower_seismogenic_depth=10.0,
                magnitude_scaling_relationship=
                openquake.hazardlib.scalerel.PeerMSR(),
                rupture_aspect_ratio=2.,
                temporal_occurrence_model=PoissonTOM(1.),
                rupture_mesh_spacing=1.0,
                location=Point(10, 10)
            ),
            openquake.hazardlib.source.PointSource(
                source_id='point2', name='point2',
                tectonic_region_type="Active Shallow Crust",
                mfd=openquake.hazardlib.mfd.EvenlyDiscretizedMFD(
                    min_mag=4, bin_width=2, occurrence_rates=[5, 6, 7]
                ),
                nodal_plane_distribution=openquake.hazardlib.pmf.PMF([
                    (1, openquake.hazardlib.geo.NodalPlane(strike=0,
                                                           dip=90,
                                                           rake=0.0)),
                ]),
                hypocenter_distribution=openquake.hazardlib.pmf.PMF(
                    [(1, 10.)]),
                upper_seismogenic_depth=0.0,
                lower_seismogenic_depth=10.0,
                magnitude_scaling_relationship=
                openquake.hazardlib.scalerel.PeerMSR(),
                rupture_aspect_ratio=2.,
                temporal_occurrence_model=PoissonTOM(1.),
                rupture_mesh_spacing=1.0,
                location=Point(10, 11)
            ),
        ]
        sites = [openquake.hazardlib.site.Site(Point(11, 10), 1, 2, 3),
                 openquake.hazardlib.site.Site(Point(10, 16), 2, 2, 3),
                 openquake.hazardlib.site.Site(Point(10, 10.6, 1), 3, 2, 3),
                 openquake.hazardlib.site.Site(Point(10, 10.7, -1), 4, 2, 3)]
        sitecol = openquake.hazardlib.site.SiteCollection(sites)
        gsims = {"Active Shallow Crust": SadighEtAl1997()}
        truncation_level = 1
        imts = {'PGA': [0.1, 0.5, 1.3]}
        s_filter = SourceFilter(sitecol, IntegrationDistance.new('30'))
        result = calc_hazard_curves(
            sources, s_filter, imts, gsims, truncation_level)['PGA']
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

        self.assertEqual(result.shape, (4, 3))  # 4 sites, 3 levels
        numpy.testing.assert_allclose(result[0], 0)  # no contrib to site 1
        numpy.testing.assert_allclose(result[1], 0)  # no contrib to site 2


# this example originally came from the Hazard Modeler Toolkit
def example_calc(apply):
    sitecol = SiteCollection([
        Site(Point(30.0, 30.0), 760., 1.0, 1.0),
        Site(Point(30.25, 30.25), 760., 1.0, 1.0),
        Site(Point(30.4, 30.4), 760., 1.0, 1.0)])
    mfd_1 = TruncatedGRMFD(4.5, 8.0, 0.1, 4.0, 1.0)
    mfd_2 = TruncatedGRMFD(4.5, 7.5, 0.1, 3.5, 1.1)
    trt = 'Active Shallow Crust'
    sources = [PointSource('001', 'Point1', trt,
                           mfd_1, 1.0, WC1994(), 1.0, PoissonTOM(50.0),
                           0.0, 30.0, Point(30.0, 30.5),
                           PMF([(1.0, NodalPlane(0.0, 90.0, 0.0))]),
                           PMF([(1.0, 10.0)])),
               PointSource('002', 'Point2', trt,
                           mfd_2, 1.0, WC1994(), 1.0, PoissonTOM(50.0),
                           0.0, 30.0, Point(30.0, 30.5),
                           PMF([(1.0, NodalPlane(0.0, 90.0, 0.0))]),
                           PMF([(1.0, 10.0)]))]
    imtls = {'PGA': [0.01, 0.1, 0.2, 0.5, 0.8],
             'SA(0.5)': [0.01, 0.1, 0.2, 0.5, 0.8]}
    gsims = {trt: AkkarBommer2010()}
    return calc_hazard_curves(sources, sitecol, imtls, gsims, apply=apply)


class HazardCurvesParallelTestCase(unittest.TestCase):
    def test_same_curves_as_sequential(self):
        curves_par = example_calc(Starmap.apply)  # use multiprocessing
        curves_seq = example_calc(sequential_apply)  # sequential computation
        for name in curves_par.dtype.names:
            numpy.testing.assert_almost_equal(
                curves_seq[name], curves_par[name])

    @classmethod
    def tearDown(cls):
        Starmap.shutdown()


class AvgGMPETestCase(unittest.TestCase):
    def test(self):
        sitecol = SiteCollection([Site(Point(30.0, 30.0), 760., 1.0, 1.0)])
        mfd = TruncatedGRMFD(4.5, 8.0, 0.1, 4.0, 1.0)
        sources = [PointSource('001', 'Point1', 'Active Shallow Crust',
                               mfd, 1.0, WC1994(), 1.0, PoissonTOM(50.0),
                               0.0, 30.0, Point(30.0, 30.5),
                               PMF([(1.0, NodalPlane(0.0, 90.0, 0.0))]),
                               PMF([(1.0, 10.0)]))]
        imtls = {'PGA': [0.01, 0.1, 0.2, 0.5, 0.8]}
        hc1 = calc_hazard_curves(sources, sitecol, imtls, {
            'Active Shallow Crust': AkkarBommer2010()})['PGA']
        hc2 = calc_hazard_curves(sources, sitecol, imtls, {
            'Active Shallow Crust': SadighEtAl1997()})['PGA']
        hc = .6 * hc1 + .4 * hc2
        ag = AvgGMPE(b1=dict(AkkarBommer2010={'weight': .6}),
                     b2=dict(SadighEtAl1997={'weight': .4}))
        hcm = calc_hazard_curves(sources, sitecol, imtls, {
            'Active Shallow Crust': ag})['PGA']
        # NB: the AvgGMPE is NOT producing the mean of the PoEs
        numpy.testing.assert_almost_equal(hc, hcm, decimal=3)


class MixtureModelGMPETestCase(unittest.TestCase):
    """
    Test the Mixture Model using the 2018 PEER Test Set 2 Case 5,
    as described in Hale et al. (2018)
    """
    def test(self):
        sitecol = SiteCollection([Site(Point(-65.13490, 0.0),
                                  vs30=760., z1pt0=48.0, z2pt5=0.607,
                                  vs30measured=True)])
        mfd = ArbitraryMFD([6.0], [0.01604252])
        trace = Line([Point(-65.0000, -0.11240), Point(-65.000, 0.11240)])
        # 1.0 km Mesh Spacing
        mesh_spacing = 1.0
        msr = PeerMSR()
        sources = [SimpleFaultSource("001", "PEER Fault Set 2.5",
                                     "Active Shallow Crust", mfd,
                                     mesh_spacing,  msr, 2.0, PoissonTOM(1.0),
                                     0.0, 12., trace, 90., 0.)]
        imtls = {"PGA": [0.001, 0.01, 0.05, 0.1, 0.2, 0.4, 0.6, 0.8, 1.0,
                         1.25, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 7.0]}
        gmpe = ChiouYoungs2014PEER()
        gmpe.mixture_model = {"factors": [0.8, 1.2], "weights": [0.5, 0.5]}
        hcm = calc_hazard_curves(sources, sitecol, imtls,
                                 {"Active Shallow Crust": gmpe})
        # Match against the benchmark is not exact - but differences in the
        # log space should be on the order of less than 0.04%
        expected = numpy.array([-4.140470001, -4.140913368, -4.259457496,
                                -4.724733842, -5.900747959, -7.734816415,
                                -9.019329629, -10.03864778, -10.90333404,
                                -11.83885783, -12.65826442, -14.05429951,
                                -15.22535996, -16.23988897, -17.94685518,
                                -19.36079032, -20.57460101, -21.64201335])
        expected = numpy.around(expected, 5)
        hcm_lnpga = numpy.around(numpy.log(hcm["PGA"].flatten()), 5)
        perc_diff = 100.0 * ((hcm_lnpga / expected) - 1.0)
        numpy.testing.assert_allclose(perc_diff, numpy.zeros(len(perc_diff)),
                                      atol=0.04)


# an area source with 388 point sources and 4656 ruptures
asource = nrml.get('''\
<areaSource
  id="1"
  name="Area Source"
  tectonicRegion="Stable Continental Crust">
  <areaGeometry>
      <gml:Polygon>
          <gml:exterior>
              <gml:LinearRing>
                  <gml:posList>
                    -1.5 -1.5 -1.3 -1.1 1.1 .2 1.3 -1.8
                  </gml:posList>
              </gml:LinearRing>
          </gml:exterior>
      </gml:Polygon>
      <upperSeismoDepth>0</upperSeismoDepth>
      <lowerSeismoDepth>10 </lowerSeismoDepth>
  </areaGeometry>
  <magScaleRel>WC1994</magScaleRel>
  <ruptAspectRatio>1</ruptAspectRatio>
  <truncGutenbergRichterMFD aValue="4.5" bValue="1" maxMag="7" minMag="5"/>
  <nodalPlaneDist>
    <nodalPlane dip="90" probability=".33" rake="0" strike="0"/>
    <nodalPlane dip="60" probability=".33" rake="0" strike="0"/>
    <nodalPlane dip="30" probability=".34" rake="0" strike="0"/>
  </nodalPlaneDist>
  <hypoDepthDist>
     <hypoDepth depth="5" probability=".5"/>
     <hypoDepth depth="10" probability=".5"/>
  </hypoDepthDist>
</areaSource>''')


class NewApiTestCase(unittest.TestCase):
    """
    Test the 2021 new API for hazarlib.gsim
    """
    def test_single_site(self):
        # NB: the performance of get_mean_std is totally dominated by two
        # concomitant factors:
        # 1) source splitting (do not split the area source)
        # 2) collect the contexts in a single array
        # together they give a 200x speedup
        # numba is totally useless
        site = Site(Point(0, 0), vs30=760., z1pt0=48.0, z2pt5=0.607,
                    vs30measured=True)
        sitecol = SiteCollection([site])
        imtls = {"PGA": [.123]}
        for period in numpy.arange(.1, 1.3, .1):
            imtls['SA(%.2f)' % period] = [.123]
        assert len(imtls) == 13  # 13 periods
        oq = unittest.mock.Mock(
            imtls=DictArray(imtls),
            investigation_time=1.0,
            maximum_distance=IntegrationDistance.new('300'))
        mon = Monitor()
        hcurve = calc_hazard_curve(
            sitecol, asource, [ExampleA2021()], oq, mon)
        for child in mon.children:
            print(child)
        got = hcurve.array[:, 0]
        exp = [0.103379, 0.468937, 0.403896, 0.278772, 0.213645, 0.142985,
               0.103438, 0.079094, 0.062861, 0.051344, 0.04066, 0.031589,
               0.024935]
        numpy.testing.assert_allclose(got, exp, atol=1E-5)

    def test_two_sites(self):
        site1 = Site(Point(0, 0), vs30=760., z1pt0=48.0, z2pt5=0.607,
                     vs30measured=True)
        site2 = Site(Point(0, 0.5), vs30=760., z1pt0=48.0, z2pt5=0.607,
                     vs30measured=True)
        sitecol = SiteCollection([site1, site2])
        srcfilter = SourceFilter(sitecol, IntegrationDistance.new('200'))
        imtls = {"PGA": [.123]}
        for period in numpy.arange(.1, .5, .1):
            imtls['SA(%.2f)' % period] = [.123]
        assert len(imtls) == 5  # 5 periods
        gsim_by_trt = {'Stable Continental Crust': ExampleA2021()}
        hcurves = calc_hazard_curves(
            [asource], srcfilter, DictArray(imtls), gsim_by_trt)
        print(hcurves)
