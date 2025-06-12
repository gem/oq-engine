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

import os
import filecmp
import difflib
import unittest
import collections
import numpy
from openquake.baselib.general import DictArray, gettemp
from openquake.hazardlib import (
    nrml, lt, sourceconverter, calc, site, valid, contexts)
from openquake.hazardlib.calc.hazard_curve import classical
from openquake.hazardlib.geo.point import Point

CDIR = os.path.dirname(__file__)
ae = numpy.testing.assert_equal

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


# coordinates for the area sources of BCHydro
EN = '''
-121.28842 49.54551 -121.91309 49.34564 -123.08491 50.29564 -125.97668 51.77786 -125.66343 51.90604 -124.78584 51.92274 -123.74283 51.46238 -122.66185 51.12547 -121.94294 50.77203 -121.45788 49.88948 -121.28842 49.54551
'''
EC = '''
-121.7803 49.23488 -121.91309 49.34564 -123.08491 50.29564 -125.97668 51.77786 -125.66343 51.90604 -124.78584 51.92274 -123.74283 51.46238 -122.66185 51.12547 -121.94294 50.77203 -121.45788 49.88948 -121.28842 49.54551 -121.22422 49.41373 -121.7803 49.23488
'''
ES = '''
-121.16104 49.28325 -121.70759 49.10641 -121.7803 49.23488 -121.91309 49.34564 -123.08491 50.29564 -125.97668 51.77786 -125.66343 51.90604 -124.78584 51.92274 -123.74283 51.46238 -122.66185 51.12547 -121.94294 50.77203 -121.45788 49.88948 -121.28842 49.54551 -121.22422 49.41373 -121.16104 49.28325
'''

WN = '''
-121.28842 49.54551 -121.91309 49.34564 -122.15546 49.26664 -122.27591 49.41094 -123.01238 49.82133 -124.68987 50.71523 -125.13614 50.91171 -125.80908 51.11105 -126.56198 51.32721 -126.47716 51.56968 -126.21795 51.67803 -125.97668 51.77786 -125.66343 51.90604 -124.78584 51.92274 -123.74283 51.46238 -122.66185 51.12547 -121.94294 50.77203 -121.45788 49.88948 -121.28842 49.54551
'''
WC = '''
-121.7803 49.23488 -122.05466 49.14506 -122.15546 49.26664 -122.27591 49.41094 -123.01238 49.82133 -124.68987 50.71523 -125.13614 50.91171 -125.80908 51.11105 -126.56198 51.32721 -126.47716 51.56968 -126.21795 51.67803 -125.97668 51.77786 -125.66343 51.90604 -124.78584 51.92274 -123.74283 51.46238 -122.66185 51.12547 -121.94294 50.77203 -121.45788 49.88948 -121.28842 49.54551 -121.22422 49.41373 -121.7803 49.23488
'''

WS = '''
-121.70759 49.10641 -121.94909 49.02693 -122.05466 49.14506 -122.15546 49.26664 -122.27591 49.41094 -123.01238 49.82133 -124.68987 50.71523 -125.13614 50.91171 -125.80908 51.11105 -126.56198 51.32721 -126.47716 51.56968 -126.21795 51.67803 -125.97668 51.77786 -125.66343 51.90604 -124.78584 51.92274 -123.74283 51.46238 -122.66185 51.12547 -121.94294 50.77203 -121.45788 49.88948 -121.28842 49.54551 -121.22422 49.41373 -121.16104 49.28325 -121.70759 49.10641
'''

AREA = '''
<areaGeometry>
  <gml:Polygon>
     <gml:exterior>
       <gml:LinearRing>
         <gml:posList>
         %s
         </gml:posList>
      </gml:LinearRing>
    </gml:exterior>
  </gml:Polygon>
<upperSeismoDepth>
0.0
</upperSeismoDepth>
<lowerSeismoDepth>
15.0
</lowerSeismoDepth>
</areaGeometry>
'''

class CollapseTestCase(unittest.TestCase):
    def setUp(self):
        # simple logic tree with 3 realizations
        #    ___/ b11 (w=.2)
        #  _/   \ b12 (w=.2)
        #   \____ b02 (w=.6)
        self.bs0 = bs0 = lt.BranchSet('abGRAbsolute')
        bs0.branches = [lt.Branch('A', (4.6, 1.1), .4, 'bs0'),
                        lt.Branch('B', (4.4, 0.9), .6, 'bs0')]

        self.bs1 = bs1 = lt.BranchSet('maxMagGRAbsolute',
                                      dict(applyToBranches=['A']))
        bs1.branches = [lt.Branch('C', 7.0, .5, 'bs1'),
                        lt.Branch('D', 7.6, .5, 'bs1')]

        self.clt = lt.CompositeLogicTree([bs0, bs1])

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
                      maximum_distance=idist('default'), af=None)
        cmaker = contexts.ContextMaker(
            srcs[0].tectonic_region_type, self.gsims, params)
        res = classical(srcs, self.sitecol, cmaker)
        pmap = ~res['rmap']
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
        _coll2, srcs, effctxs, weights = self.full_enum()
        assert weights == [1]  # one rlz
        # self.plot(mean, coll2)
        assert scaling_rates(srcs) == [0.4, 0.6, 0.5, 0.5]
        self.assertEqual(effctxs, 36)

    def test_apply_all(self):
        rlz0, rlz1, rlz2 = self.clt
        src0, src1, src2 = self.clt.apply_all(self.sg[0])
        self.assertEqual(src0.mfd.a_val, 4.6)
        self.assertEqual(src0.mfd.b_val, 1.1)
        self.assertEqual(src0.mfd.max_mag, 7.0)

        self.assertEqual(src1.mfd.a_val, 4.6)
        self.assertEqual(src1.mfd.b_val, 1.1)
        self.assertEqual(src1.mfd.max_mag, 7.6)

        self.assertEqual(src2.mfd.a_val, 4.4)
        self.assertEqual(src2.mfd.b_val, 0.9)
        self.assertEqual(src2.mfd.max_mag, 7.0)

        ae(rlz0.value, [(4.6, 1.1), 7.0])
        ae(rlz1.value, [(4.6, 1.1), 7.6])
        ae(rlz2.value, [(4.4, 0.9), None])

    def plot(self, mean, coll):
        import matplotlib.pyplot as plt
        _fig, ax = plt.subplots()
        ax.grid(True)
        ax.loglog(self.imtls['PGA'], mean, label='mean')
        ax.loglog(self.imtls['PGA'], coll, label='coll')
        plt.show()


EXPECTED_LT = '''<?xml version="1.0" encoding="utf-8"?>
<nrml
xmlns="http://openquake.org/xmlns/nrml/0.5"
xmlns:gml="http://www.opengis.net/gml"
>
    <logicTree
    logicTreeID="lt"
    >
        <logicTreeBranchSet
        branchSetID="bs0"
        uncertaintyType="abGRAbsolute"
        >
            <logicTreeBranch
            branchID="A"
            >
                <uncertaintyModel>
                    4.6000000E+00 1.1000000E+00
                </uncertaintyModel>
                <uncertaintyWeight>
                    4.0000000E-01
                </uncertaintyWeight>
            </logicTreeBranch>
            <logicTreeBranch
            branchID="B"
            >
                <uncertaintyModel>
                    4.4000000E+00 9.0000000E-01
                </uncertaintyModel>
                <uncertaintyWeight>
                    6.0000000E-01
                </uncertaintyWeight>
            </logicTreeBranch>
        </logicTreeBranchSet>
        <logicTreeBranchSet
        applyToBranches="A"
        branchSetID="bs1"
        uncertaintyType="maxMagGRAbsolute"
        >
            <logicTreeBranch
            branchID="C"
            >
                <uncertaintyModel>
                    7.0000000E+00
                </uncertaintyModel>
                <uncertaintyWeight>
                    5.0000000E-01
                </uncertaintyWeight>
            </logicTreeBranch>
            <logicTreeBranch
            branchID="D"
            >
                <uncertaintyModel>
                    7.6000000E+00
                </uncertaintyModel>
                <uncertaintyWeight>
                    5.0000000E-01
                </uncertaintyWeight>
            </logicTreeBranch>
        </logicTreeBranchSet>
        <logicTreeBranchSet
        applyToBranches="CD"
        branchSetID="bs2"
        uncertaintyType="applyToTectonicRegionType"
        >
            <logicTreeBranch
            branchID="E"
            >
                <uncertaintyModel>
                    A
                </uncertaintyModel>
                <uncertaintyWeight>
                    3.0000000E-01
                </uncertaintyWeight>
            </logicTreeBranch>
            <logicTreeBranch
            branchID="F"
            >
                <uncertaintyModel>
                    B
                </uncertaintyModel>
                <uncertaintyWeight>
                    7.0000000E-01
                </uncertaintyWeight>
            </logicTreeBranch>
        </logicTreeBranchSet>
    </logicTree>
</nrml>
'''


class CompositeLogicTreeTestCase(unittest.TestCase):

    def test5(self):
        # simple logic tree with 5 realizations
        #        _C/ E
        #    _A_/  \ F
        #   /   \_D/ E
        #          \ F
        #   \_______
        #            B..
        bs0 = lt.BranchSet('abGRAbsolute')
        bs0.branches = [lt.Branch('A', (4.6, 1.1), .4, 'bs0'),
                        lt.Branch('B', (4.4, 0.9), .6, 'bs0')]

        bs1 = lt.BranchSet('maxMagGRAbsolute',
                           filters={'applyToBranches': 'A'})
        bs1.branches = [lt.Branch('C', 7.0, .5, 'bs1'),
                        lt.Branch('D', 7.6, .5, 'bs1')]

        bs2 = lt.BranchSet('applyToTectonicRegionType',
                           filters={'applyToBranches': 'CD'})
        bs2.branches = [lt.Branch('E', 'A', .3, 'bs2'),
                        lt.Branch('F', 'B', .7, 'bs2')]
        for branch in bs1.branches:
            branch.bset = bs2
        clt = lt.CompositeLogicTree([bs0, bs1, bs2])
        self.assertEqual(lt.count_paths(bs0.branches), 5)
        self.assertEqual(clt.get_all_paths(),
                         ['ACE', 'ACF', 'ADE', 'ADF', 'B..'])
        self.assertEqual(clt.basepaths,
                         ['A**', 'B**', '*C*', '*D*', '**E', '**F'])

        xml = clt.to_nrml()
        self.assertEqual(xml, EXPECTED_LT)

    def test_build0(self):
        clt = lt.build(['sourceModel', [],
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

        clt = lt.build(['sourceModel', [],
                        ['A', 'common1', 0.6],
                        ['B', 'common2', 0.4]],
                       ['extendModel', 'A',
                        ['C', 'extra1', 0.6],
                        ['D', 'extra2', 0.2],
                        ['E', 'extra3', 0.2]])
        self.assertEqual(clt.get_all_paths(), ['AC', 'AD', 'AE', 'B.'])

        clt = lt.build(['sourceModel', [],
                        ['A', 'common1', 0.6],
                        ['B', 'common2', 0.4]],
                       ['extendModel', 'B',
                        ['C', 'extra1', 0.6],
                        ['D', 'extra2', 0.2],
                        ['E', 'extra3', 0.2]])
        self.assertEqual(clt.get_all_paths(), ['A.', 'BC', 'BD', 'BE'])

        clt = lt.build(['sourceModel', [],
                        ['A', 'common1', 0.6],
                        ['B', 'common2', 0.4]],
                       ['extendModel', 'AB',
                        ['C', 'extra1', 0.6],
                        ['D', 'extra2', 0.2],
                        ['E', 'extra3', 0.2]])
        self.assertEqual(clt.get_all_paths(),
                         ['AC', 'AD', 'AE', 'BC', 'BD', 'BE'])

    def test_build1(self):
        clt = lt.build(['sourceModel', [],
                        ['ssm1', 'common1', 0.6],
                        ['ssm2', 'common2', 0.4]],
                       ['setLowerSeismDepthAbsolute', ['ssm1'],
                        ['lsd10', '10', 0.3],
                        ['lsd15', '15', 0.7]])
        self.assertEqual(clt.get_all_paths(),
                         ['AA', 'AB', 'B.'])

    def test_build2(self):
        ltl = [
            ['sourceModel', [],
             ['ssm1', 'ssm1.xml', 0.134],
             ['ssm2', 'ssm2.xml', 0.402],
             ['ssm3', 'ssm3.xml', 0.134],
             ['ssm4', 'ssm4.xml', 0.066],
             ['ssm5', 'ssm5.xml', 0.198],
             ['ssm6', 'ssm6.xml', 0.066]],
            ['extendModel', [],
             ['em0', 'empty1.xml', 0.7],
             ['em1', 'empty2.xml', 0.1],
             ['em2', 'empty3.xml', 0.2]],
            ['abGRAbsolute', ['em0'],
             ['ab_1', '1.0 1.0', 0.2],
             ['ab_2', '1.1 0.9', 0.5],
             ['ab_3', '1.2 0.8', 0.3]],
            ['maxMagGRAbsolute', [],
             ['mmax_6pt8', '6.8', 0.3],
             ['mmax_7pt0', '7.0', 0.3],
             ['mmax_7pt3', '7.3', 0.3],
             ['mmax_7pt6', '7.6', 0.1]]
        ]
        ltssc = lt.build(*ltl)
        paths = ltssc.get_all_paths()
        # The third branchset increases the number of branches from 3 to 5 for
        # each of the original 6 branches leading to 30 branches in total.
        # These are multiplied by 4 with the last branchset.
        self.assertEqual(len(paths), 120)
        paths = ltssc.sample_paths(10)
        self.assertEqual(paths, ['BC.H', 'BADI', 'CB.J', 'EADG', 'BAEG',
                                 'CAEH', 'BB.H', 'CAEG', 'AC.I', 'BAEH'])

    def test_build3(self):
        # test with applyToSources for the BCHydro project
        clt = lt.build(
            ['sourceModel', [],
             ['ssm', 'nva.xml', 1.0]
             ],
            ['areaSourceGeometryAbsolute', [],
             ['es', AREA % ES, .134],
             ['en', AREA % EN, .402],
             ['ec', AREA % EC, .134],
             ['ws', AREA % WS, .066],
             ['wn', AREA % WN, .198],
             ['wc', AREA % WC, .066],
             ],
            ['abGRAbsolute', [],
             ['ab0', '1.144375 0.5535', 8.6824159E-03],
             ['ab1', '1.555686 0.6813', 2.6117011E-02],
             ['ab2', '1.970773 0.809', 3.0156485E-02],
             ['ab3', '2.386173 0.9368', 1.5198986E-02],
             ['ab4', '2.801201 1.0645', 3.6951018E-03],
             ['ab5', '1.266199 0.5535', 1.9593201E-02],
             ['ab6', '1.681187 0.6813', 7.4035943E-02],
             ['ab7', '2.096274 0.809', 1.0132525E-01],
             ['ab8', '2.511673 0.9368', 5.8015175E-02],
             ['ab9', '2.926702 1.0645', 1.5533167E-02],
             ['ab10', '1.363446 0.5535', 1.7662801E-02],
             ['ab11', '1.778434 0.6813',8.5165169E-02],
             ['ab12', '2.193522 0.80', 1.3994067E-01],
             ['ab13', '2.60892 0.9368', 9.2004240E-02],
             ['ab14', '3.02395 1.0645', 2.7369319E-02],
             ['ab15', '1.476012 0.5535', 6.1173179E-03],
             ['ab16', '1.891 0.6813', 4.0550596E-02],
             ['ab17', '2.306088 0.809', 8.4531934E-02],
             ['ab18', '2.721487 0.9368', 6.6527816E-02],
             ['ab19', '3.136516 1.0645', 2.2700337E-02],
             ['ab20', '1.565326 0.5535', 9.4576404E-04],
             ['ab21', '1.980314 0.6813', 8.8379121E-03],
             ['ab22', '2.395402 0.809', 2.3747118E-02],
             ['ab23', '2.810801 0.936', 2.2620635E-02],
             ['ab24', '3.22583 1.0645', 8.9256359E-03],
             ],
            ['setLowerSeismDepthAbsolute', [],
             ['lsd15', 15, .3],
             ['lsd20', 20, .4],
             ['lsd25', 25, .3],
             ],
            ['maxMagGRAbsolute', [],
             ['mm6pt8', 6.8, .3],
             ['mm7pt0', 7.0, .3],
             ['mm7pt3', 7.3, .3],
             ['mm7pt6', 7.5, .1],
             ],
            applyToSources='nva')
        
        fname = gettemp(clt.to_nrml(), suffix='.xml')
        expected = os.path.join(CDIR, 'lt_test.xml')
        with open(fname) as got, open(expected) as exp:
            msg = f'The two files do not match:\n{expected}\n{fname}\n'
            diff = difflib.unified_diff(
                exp.readlines(),
                got.readlines(),
                fromfile='expected',
                tofile='computed',
            )
            for line in diff:
                msg += line
                msg += '\n'
        self.assertTrue(filecmp.cmp(expected, fname, shallow=True), msg)

    def test_zero_weight(self):
        # check that branches with zero weight are not sampled
        clt = lt.build(['sourceModel', [],
                        ['A', 'common1', 0.65],
                        ['B', 'common2', 0.35],
                        ['C', 'dummy', 0.0]])
        clt.num_samples = 100
        rlzs = list(clt)
        paths = [''.join(rlz.lt_path) for rlz in rlzs]
        cnt = collections.Counter(paths)
        assert cnt == {'A': 68, 'B': 32}

