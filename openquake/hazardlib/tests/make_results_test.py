# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2026 GEM Foundation
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
import numpy
from openquake.baselib.general import DictArray
from openquake.hazardlib.calc.filters import SourceFilter, IntegrationDistance
from openquake.hazardlib.contexts import ContextMaker
from openquake.hazardlib.geo import Point, NodalPlane
from openquake.hazardlib.gsim.cauzzi_2014 import CauzziEtAl2014
from openquake.hazardlib.mfd import TruncatedGRMFD
from openquake.hazardlib.pmf import PMF
from openquake.hazardlib.rmap_maker import RmapMaker, make_results
from openquake.hazardlib.scalerel import WC1994
from openquake.hazardlib.site import Site, SiteCollection
from openquake.hazardlib.source import PointSource
from openquake.hazardlib.tom import PoissonTOM

# a point source 219 km from the site, i.e. at the edge of the maximum
# distance (200 km): it is discarded by the source filter if the maximum
# magnitude is 7.1, but kept if it is 7.4, and the ruptures of magnitude
# 7.05 of the latter are within 200 km (see RmapMaker.gen_ctxs)
LON = 1.892


def make_source(max_mag):
    src = PointSource(
        'src', 'src', 'Active Shallow Crust',
        TruncatedGRMFD(min_mag=4.5, max_mag=max_mag, bin_width=0.1,
                       a_val=-0.42115017, b_val=0.80317407),
        2., WC1994(), 1.5, PoissonTOM(1.), 0.1, 30.,
        Point(LON, 42.04337, 0.),
        PMF([(.25, NodalPlane(strike, 45, 90))
             for strike in (0, 90, 180, 270)]),
        PMF([(1., 10.05)]))
    src.grp_id = 0  # normally set by the calculator
    src.id = 0
    src.weight = 1.
    return src


class MakeResultsTestCase(unittest.TestCase):
    # the MFD variants of a source computed together by make_results must
    # give the same results as the variants computed one at a time, also
    # when the source filter discards the source in some variants only
    def test_source_filter(self):
        site = Site(Point(4.34073, 41.30226, 0.), vs30=800.,
                    vs30measured=True, z1pt0=31., z2pt5=1.)
        sites = SiteCollection([site])
        maxdist = IntegrationDistance.new('200')
        param = dict(imtls=DictArray({'PGA': [.001, .005, .01, .05]}),
                     maximum_distance=maxdist, investigation_time=1.)
        small, big = make_source(7.1), make_source(7.3667)
        # the premise of the test: only the source with the largest
        # maximum magnitude passes the source filter
        sf = SourceFilter(sites, maxdist)
        self.assertIsNone(sf.get_close_sites(small))
        self.assertIsNotNone(sf.get_close_sites(big))
        srcs = [small, big]
        cmakers = [ContextMaker('*', [CauzziEtAl2014()], param)
                   for _ in srcs]
        together = make_results([[src] for src in srcs], cmakers, sites)
        for src, cmaker, dic in zip(srcs, cmakers, together):
            alone = RmapMaker(cmaker, sites, [src]).make()
            numpy.testing.assert_allclose(
                dic['rmap'].array, alone['rmap'].array, rtol=1E-6)
        # the discarded variant has no contribution, the other one has
        self.assertEqual(together[0]['rmap'].array.max(), 0.)
        self.assertGreater(together[1]['rmap'].array.max(), 0.)
