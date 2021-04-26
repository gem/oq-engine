# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2020, GEM Foundation
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

import unittest
import numpy
from openquake.baselib.general import DictArray
from openquake.hazardlib import nrml, lt, sourceconverter, calc, site, valid
from openquake.hazardlib.calc.hazard_curve import classical
from openquake.hazardlib.geo.point import Point


# a point source with 2(mag) x 2(npd) x 2(hdd) = 8 ruptures
ps = nrml.get('''\
<pointSource id="P" name="P" tectonicRegion="Active Shallow Crust">
  <pointGeometry>
      <gml:Point><gml:pos>1 0</gml:pos></gml:Point>
      <upperSeismoDepth>0</upperSeismoDepth>
      <lowerSeismoDepth>10</lowerSeismoDepth>
   </pointGeometry>
   <magScaleRel>WC1994</magScaleRel>
   <ruptAspectRatio>1.5</ruptAspectRatio>
   <truncGutenbergRichterMFD aValue="3" bValue="1" maxMag="7" minMag="5"/>
   <nodalPlaneDist>
      <nodalPlane dip="30" probability=".3" rake="0" strike="45"/>
      <nodalPlane dip="30" probability=".7" rake="90" strike="45"/>
   </nodalPlaneDist>
   <hypoDepthDist>
      <hypoDepth depth="4" probability=".5"/>
      <hypoDepth depth="8" probability=".5"/>
   </hypoDepthDist>
</pointSource>''')


def scaling_rates(srcs):
    return [getattr(src, 'scaling_rate', 1.) for src in srcs]


class CollapseTestCase(unittest.TestCase):
    def setUp(self):
        # simple logic tree with 3 realizations
        #    ___/ b11 (w=.2)
        #  _/   \ b12 (w=.2)
        #   \____ b02 (w=.6)
        self.bs0 = bs0 = lt.BranchSet('abGRAbsolute')
        bs0.branches = [lt.Branch('bs0', 'b01', .4, (4.6, 1.1)),
                        lt.Branch('bs0', 'b02', .6, (4.4, 0.9))]

        self.bs1 = bs1 = lt.BranchSet('maxMagGRAbsolute')
        bs1.branches = [lt.Branch('bs1', 'b11', .5, 7.0),
                        lt.Branch('bs1', 'b12', .5, 7.6)]
        bs0.branches[0].bset = bs1

        # setup sitecol, srcfilter, gsims, imtls
        sitecol = site.SiteCollection(
            [site.Site(Point(0, 0), numpy.array([760.]))])
        self.srcfilter = calc.filters.SourceFilter(
            sitecol, calc.filters.MagDepDistance.new('200'))
        self.gsims = [valid.gsim('ToroEtAl2002')]
        self.imtls = DictArray({'PGA': valid.logscale(.01, 1, 5)})
        self.sg = sourceconverter.SourceGroup(ps.tectonic_region_type, [ps])

    def full_enum(self):
        # compute the mean curve with full enumeration
        srcs = []
        weights = []
        grp_id = trt_smr = 0
        for weight, branches in self.bs0.enumerate_paths():
            path = tuple(br.branch_id for br in branches)
            bset_values = self.bs0.get_bset_values(path)
            # first path: [(<b01 b02>, (4.6, 1.1)), (<b11 b12>, 7.0)]
            sg = lt.apply_uncertainties(bset_values, self.sg)
            for src in sg:
                src.grp_id = grp_id
                src.trt_smr = trt_smr
            grp_id += 1
            trt_smr += 1
            srcs.extend(sg)
            weights.append(weight)
        for i, src in enumerate(srcs):
            src.id = i
        N = len(self.srcfilter.sitecol.complete)
        time_span = srcs[0].temporal_occurrence_model.time_span
        res = classical(srcs, self.srcfilter, self.gsims,
                        dict(imtls=self.imtls, truncation_level2=2,
                             collapse_level=2, investigation_time=time_span))
        pmap = res['pmap']
        effrups = sum(nr for nr, ns, dt in res['calc_times'].values())
        curve = pmap.array(N)[0, :, 0]
        return curve, srcs, effrups, weights

    # this tests also the collapsing of the ruptures happening in contexts.py
    def test_point_source_full_enum(self):
        # compute the mean curve
        mean, srcs, effrups, weights = self.full_enum()
        assert weights == [.2, .2, .6]
        assert scaling_rates(srcs) == [1, 1, 1]
        self.assertEqual(effrups, 22)  # less then 8 x 3 = 24

        # compute the partially collapsed curve
        self.bs1.collapsed = True
        coll1, srcs, effrups, weights = self.full_enum()
        assert weights == [.4, .6]  # two rlzs
        # self.plot(mean, coll1)
        assert scaling_rates(srcs) == [1.0, 0.5, 0.5, 1.0]
        self.assertEqual(effrups, 28)  # less then 8 x 4 = 32
        numpy.testing.assert_allclose(mean, coll1, atol=.1)

        # compute the fully collapsed curve
        self.bs0.collapsed = True
        self.bs1.collapsed = True
        coll2, srcs, effrups, weights = self.full_enum()
        assert weights == [1]  # one rlz
        # self.plot(mean, coll2)
        assert scaling_rates(srcs) == [0.4, 0.6, 0.5, 0.5]
        self.assertEqual(effrups, 28)  # much less then 8 x 4 = 32
        numpy.testing.assert_allclose(mean, coll2, atol=.16)

    def plot(self, mean, coll):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        ax.grid(True)
        ax.loglog(self.imtls['PGA'], mean, label='mean')
        ax.loglog(self.imtls['PGA'], coll, label='coll')
        plt.show()
