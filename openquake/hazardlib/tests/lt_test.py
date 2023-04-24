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
from openquake.hazardlib import (
    nrml, lt, sourceconverter, calc, site, valid, contexts)
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
        self.sitecol = site.SiteCollection(
            [site.Site(Point(0, 0), numpy.array([760.]))])
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
        time_span = srcs[0].temporal_occurrence_model.time_span
        idist = calc.filters.IntegrationDistance.new('200')
        params = dict(imtls=self.imtls, truncation_level2=2,
                      collapse_level=1, investigation_time=time_span,
                      maximum_distance=idist('default'))
        cmaker = contexts.ContextMaker(
            srcs[0].tectonic_region_type, self.gsims, params)
        res = classical(srcs, self.sitecol, cmaker)
        pmap = res['pmap']
        effrups = sum(res['source_data']['nrupts'])
        curve = pmap.array[0, :, 0]
        return curve, srcs, effrups, weights

    # this tests also the collapsing of the ruptures happening in contexts.py
    def test_point_source_full_enum(self):
        # compute the mean curve
        mean, srcs, effctxs, weights = self.full_enum()
        assert weights == [.2, .2, .6]
        assert scaling_rates(srcs) == [1, 1, 1]
        self.assertEqual(effctxs, 28)

        # compute the partially collapsed curve
        self.bs1.collapsed = True
        coll1, srcs, effctxs, weights = self.full_enum()
        assert weights == [.4, .6]  # two rlzs
        # self.plot(mean, coll1)
        assert scaling_rates(srcs) == [1.0, 0.5, 0.5, 1.0]
        self.assertEqual(effctxs, 36)
        numpy.testing.assert_allclose(mean, coll1, atol=.1)

        # compute the fully collapsed curve
        self.bs0.collapsed = True
        self.bs1.collapsed = True
        coll2, srcs, effctxs, weights = self.full_enum()
        assert weights == [1]  # one rlz
        # self.plot(mean, coll2)
        assert scaling_rates(srcs) == [0.4, 0.6, 0.5, 0.5]
        self.assertEqual(effctxs, 36)
        numpy.testing.assert_allclose(mean, coll2, atol=.21)  # big diff

    def plot(self, mean, coll):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        ax.grid(True)
        ax.loglog(self.imtls['PGA'], mean, label='mean')
        ax.loglog(self.imtls['PGA'], coll, label='coll')
        plt.show()


class CompositeLogicTreeTestCase(unittest.TestCase):
    def test(self):
        # simple logic tree with 5 realizations
        #        _C/ E
        #    _A_/  \ F
        #   /   \_D/ E
        #          \ F
        #   \_______
        #            B..
        bs0 = lt.BranchSet('abGRAbsolute')
        bs0.branches = [lt.Branch('bs0', 'A', .4, (4.6, 1.1)),
                        lt.Branch('bs0', 'B', .6, (4.4, 0.9))]

        bs1 = lt.BranchSet('maxMagGRAbsolute',
                           filters={'applyToBranches': 'A'})
        bs1.branches = [lt.Branch('bs1', 'C', .5, 7.0),
                        lt.Branch('bs1', 'D', .5, 7.6)]

        bs2 = lt.BranchSet('applyToTRT',
                           filters={'applyToBranches': 'CD'})
        bs2.branches = [lt.Branch('bs2', 'E', .3, 'A'),
                        lt.Branch('bs2', 'F', .7, 'B')]
        for branch in bs1.branches:
            branch.bset = bs2
        clt = lt.CompositeLogicTree([bs0, bs1, bs2])
        self.assertEqual(lt.count_paths(bs0.branches), 5)
        self.assertEqual(clt.get_all_paths(),
                         ['ACE', 'ACF', 'ADE', 'ADF', 'B..'])
        self.assertEqual(clt.basepaths,
                         ['A**', 'B**', '*C*', '*D*', '**E', '**F'])

    def test_build(self):
        clt = lt.build(['sourceModel', '',
                        ['A', 'common1', 0.6],
                        ['B', 'common2', 0.4]],
                       ['extendModel', 'A',
                        ['C', 'extra1', 0.4],
                        ['D', 'extra2', 0.2],
                        ['E', 'extra3', 0.2],
                        ['F', 'extra4', 0.2]],
                       ['extendModel', 'B',
                        ['G', 'extra5', 0.4],
                        ['H', 'extra6', 0.2],
                        ['I', 'extra7', 0.2],
                        ['J', 'extra8', 0.2]])
        self.assertEqual(clt.get_all_paths(),  # 4 + 4 rlzs
                         ['AC.', 'AD.', 'AE.', 'AF..',
                          'BG.', 'BH.', 'BI.', 'BJ.'])

        clt = lt.build(['sourceModel', '',
                        ['A', 'common1', 0.6],
                        ['B', 'common2', 0.4]],
                       ['extendModel', 'A',
                        ['C', 'extra1', 0.6],
                        ['D', 'extra2', 0.2],
                        ['E', 'extra3', 0.2]])
        self.assertEqual(clt.get_all_paths(), ['AC', 'AD', 'AE', 'B.'])

        clt = lt.build(['sourceModel', '',
                        ['A', 'common1', 0.6],
                        ['B', 'common2', 0.4]],
                       ['extendModel', 'B',
                        ['C', 'extra1', 0.6],
                        ['D', 'extra2', 0.2],
                        ['E', 'extra3', 0.2]])
        self.assertEqual(clt.get_all_paths(), ['A.', 'BC', 'BD', 'BE'])

        clt = lt.build(['sourceModel', '',
                        ['A', 'common1', 0.6],
                        ['B', 'common2', 0.4]],
                       ['extendModel', 'AB',
                        ['C', 'extra1', 0.6],
                        ['D', 'extra2', 0.2],
                        ['E', 'extra3', 0.2]])
        self.assertEqual(clt.get_all_paths(),
                         ['AC', 'AD', 'AE', 'BC', 'BD', 'BE'])
