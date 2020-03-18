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


ps = nrml.object('''\
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


bs0 = lt.BranchSet('abGRAbsolute')
bs0.branches = [lt.Branch('bs0', 'b01', .4, (4.6, 1.1)),
                lt.Branch('bs0', 'b02', .6, (4.4, 0.9))]

bs1 = lt.BranchSet('maxMagGRAbsolute')
bs1.branches = [lt.Branch('bs1', 'b11', .5, 7.0),
                lt.Branch('bs1', 'b12', .5, 7.6)]

bs0.branches[0].bset = bs1

sitecol = site.SiteCollection([site.Site(Point(0, 0), numpy.array([760.]))])
gsims = [valid.gsim('ToroEtAl2002')]
imtls = DictArray({'PGA': valid.logscale(.1, 1, 10)})
srcfilter = calc.filters.SourceFilter(sitecol, {'default': 200})


class CollapseTestCase(unittest.TestCase):
    def test_point_source(self):
        sg = sourceconverter.SourceGroup(ps.tectonic_region_type, [ps])
        srcs = []
        for weight, branches in bs0.enumerate_paths():
            path = tuple(br.branch_id for br in branches)
            new = lt.apply_uncertainties(bs0.get_bset_values(path), sg)
            srcs.extend(new.sources)
        for i, src in enumerate(srcs):
            src.id = i
            src.grp_id = 0
        pmap = classical(srcs, srcfilter, gsims,
                         dict(imtls=imtls, truncation_level2=2))['pmap']
        print(pmap[0].array)
