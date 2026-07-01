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
import shutil
import tempfile
import types
import filecmp
import difflib
import unittest
import collections
import numpy
from openquake.baselib import hdf5
from openquake.baselib.general import DictArray, gettemp
from openquake.hazardlib import (
    nrml, lt, logictree, sourceconverter, calc, site, valid, contexts,
    _smlt_from_script)
from openquake.hazardlib.calc.hazard_curve import classical
from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.gsim_lt import GsimLogicTree
from openquake.hazardlib.source_reader import get_csm

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
        self.sitecol = site.SiteCollection([site.Site(Point(0, 0), 760.)])
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
            src.num_ruptures
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
        self.assertEqual(paths, ['EAFI', 'AC.I', 'AAEJ', 'CC.G', 'CAFI',
                                 'EAFI', 'EAEG', 'BAFJ', 'BAEG', 'AAEI'])

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
        assert cnt == {'A': 64, 'B': 36}


### TESTS FOR SSC AT RUNTIME TESTS (NO-XML APPROACH) ###
OQ = types.SimpleNamespace(
    investigation_time=50., rupture_mesh_spacing=5.,
    complex_fault_mesh_spacing=None, width_of_mfd_bin=0.1,
    area_source_discretization=None, minimum_magnitude={'default': 0},
    source_id=(), discard_trts='', floating_x_step=0, floating_y_step=0,
    source_nodes=(), infer_occur_rates=False, ses_seed=42,
    disagg_by_src=False, calculation_mode='classical', use_rates=False,
    strict=True, mosaic_model=False
    )


BUILDER_SCRIPT = '''\
_B_VALUES = [0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7]
_PS_XML = """\
<?xml version="1.0" encoding="utf-8"?>
<nrml xmlns="http://openquake.org/xmlns/nrml/0.5"
      xmlns:gml="http://www.opengis.net/gml">
  <sourceModel name="{name}">
    <sourceGroup tectonicRegion="Active Shallow Crust">
      <pointSource id="ps1" name="ps1"
                   tectonicRegion="Active Shallow Crust">
        <pointGeometry>
          <gml:Point><gml:pos>1.0 0.0</gml:pos></gml:Point>
          <upperSeismoDepth>0.0</upperSeismoDepth>
          <lowerSeismoDepth>10.0</lowerSeismoDepth>
        </pointGeometry>
        <magScaleRel>WC1994</magScaleRel>
        <ruptAspectRatio>1.0</ruptAspectRatio>
        <truncGutenbergRichterMFD aValue="3.0"
          bValue="{b_value:.1f}" minMag="5.0" maxMag="7.0"/>
        <nodalPlaneDist>
          <nodalPlane probability="1.0" strike="0.0"
            dip="90.0" rake="0.0"/>
        </nodalPlaneDist>
        <hypoDepthDist>
          <hypoDepth probability="1.0" depth="5.0"/>
        </hypoDepthDist>
      </pointSource>
    </sourceGroup>
  </sourceModel>
</nrml>
"""


def get_source_model_lt():
    return [
        (f"sm_{i}", 0.1, _PS_XML.format(name=f"sm_{i}", b_value=b))
        for i, b in enumerate(_B_VALUES)
    ]
'''


def _sorted_srcs(src_groups):
    return sorted(
        (src for sg in src_groups for src in sg),
        key=lambda s: s.mfd.b_val)


def _assert_src_params(src_rt, src_xml):
    ae(src_rt.source_id, src_xml.source_id)
    ae(src_rt.tectonic_region_type, src_xml.tectonic_region_type)
    ae(src_rt.location.longitude, src_xml.location.longitude)
    ae(src_rt.location.latitude, src_xml.location.latitude)
    ae(src_rt.upper_seismogenic_depth, src_xml.upper_seismogenic_depth)
    ae(src_rt.lower_seismogenic_depth, src_xml.lower_seismogenic_depth)
    ae(src_rt.rupture_aspect_ratio, src_xml.rupture_aspect_ratio)
    numpy.testing.assert_allclose(
        src_rt.mfd.a_val, src_xml.mfd.a_val, atol=1e-10)
    numpy.testing.assert_allclose(
        src_rt.mfd.b_val, src_xml.mfd.b_val, atol=1e-10)
    ae(src_rt.mfd.min_mag, src_xml.mfd.min_mag)
    ae(src_rt.mfd.max_mag, src_xml.mfd.max_mag)


class RuntimeSourceModelLTTestCase(unittest.TestCase):
    """
    Tests for RuntimeSourceModelLT SSC LT class, with identical
    results expected against if the same logic tree was defined
    using the XML approach.
    """
    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.mkdtemp()

        # Build the runtime LT via the script defined in BUILDER_SCRIPT
        script_path = os.path.join(cls.tmpdir, 'script.py')
        with open(script_path, 'w') as fh:
            fh.write(BUILDER_SCRIPT)
        cls.rt_smlt = _smlt_from_script(script_path, {}, '')

        # Write XMLs
        for branch_id, xml_str in cls.rt_smlt._branch_xmls.items():
            fname = os.path.join(cls.tmpdir, f'{branch_id}.xml')
            with open(fname, 'w') as fh:
                fh.write(xml_str)

        # Make SSC LT XML text
        smlt_xml = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<nrml xmlns="http://openquake.org/xmlns/nrml/0.4">\n'
            '  <logicTree logicTreeID="lt1">\n'
            '    <logicTreeBranchSet uncertaintyType="sourceModel"'
            ' branchSetID="bs1">\n'
            + '\n'.join(
                f'      <logicTreeBranch branchID="{bid}">\n'
                f'        <uncertaintyModel>{bid}.xml'
                f'</uncertaintyModel>\n'
                f'        <uncertaintyWeight>0.1</uncertaintyWeight>\n'
                f'      </logicTreeBranch>'
                for bid in sorted(cls.rt_smlt._branch_xmls)
            )
            + '\n    </logicTreeBranchSet>\n'
            '  </logicTree>\n</nrml>\n'
        )

        # Write to tmp file
        smlt_path = os.path.join(cls.tmpdir, 'smlt.xml')
        with open(smlt_path, 'w') as fh:
            fh.write(smlt_xml)

        # Get the XML-based SSC LT
        cls.xml_smlt = logictree.SourceModelLogicTree(smlt_path)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir)

    def test_toh5_fromh5(self):
        """
        Test __toh5__ and __fromh5__ methods
        """
        rt = self.rt_smlt
        tmp = gettemp(suffix='.hdf5')
        with hdf5.File(tmp, 'w') as f:
            # Calls __toh5__
            f['smlt'] = rt
        with hdf5.File(tmp, 'r') as f:
            # Calls __fromh5_-
            rt2 = f['smlt']
        ae(rt2._branch_weights, rt._branch_weights)
        ae(rt2.seed, rt.seed)
        ae(rt2.num_samples, rt.num_samples)
        ae(rt2.filename, rt.filename)
        # xml strings are preserved so build_smdict()
        # works on multiple round-trips (to/from hdf5)
        ae(rt2._branch_xmls, rt._branch_xmls)
        bsets = rt2.branchsets
        ae(len(bsets), 1)
        ae(len(bsets[0].branches), 10)
        brs = rt2.branches
        ae(len(brs), 10)
        numpy.testing.assert_allclose(
            sorted(brs[b].weight for b in brs), [0.1] * 10)

        # build_smdict must succeed after the round-trip
        converter = sourceconverter.SourceConverter(
            investigation_time=50., rupture_mesh_spacing=5.)
        smdict_rt = self.rt_smlt.build_smdict(converter)
        smdict_rt2 = rt2.build_smdict(converter)
        ae(sorted(smdict_rt), sorted(smdict_rt2))

    def test_build_smdict(self):
        """
        Check that build_smdict (i.e., parsing the in-memory xml strings)
        versus nrml.read_source_models (i.e., parsing the same XML but
        from a real XML file on disk) provides same values.
        """
        # Get dict of the source model made using runtime class
        converter = sourceconverter.SourceConverter(
            investigation_time=50., rupture_mesh_spacing=5.)
        smdict_rt = self.rt_smlt.build_smdict(converter)
        ae(len(smdict_rt), 10)

        # Get the "on-disk" XMLs
        xml_fnames = [
            os.path.join(self.tmpdir, f'sm_{i}.xml') for i in range(10)]
        
        # Make an equivalent dict using read_source_models
        smdict_xml = {
            sm.fname: sm
            for sm in nrml.read_source_models(xml_fnames, converter)}

        # Check equal params in both cases
        ae(len(smdict_rt), len(smdict_xml))
        srcs_rt = _sorted_srcs(
            sg for sm in smdict_rt.values() for sg in sm.src_groups)
        srcs_xml = _sorted_srcs(
            sg for sm in smdict_xml.values() for sg in sm.src_groups)
        for src_rt, src_xml in zip(srcs_rt, srcs_xml):
            _assert_src_params(src_rt, src_xml)

    def test_get_csm(self):
        """
        Check that get_composite_source_model provides same
        sources from XML and runtime SSC Lts
        """
        # Build Runtime LT
        rt_full_lt = logictree.FullLogicTree(
            self.rt_smlt, GsimLogicTree.from_('[SadighEtAl1997]'))
        
        # Build XML LT
        xml_full_lt = logictree.FullLogicTree(
            self.xml_smlt, GsimLogicTree.from_('[SadighEtAl1997]'))
        
        # Get the composite source models
        csm_rt = get_csm(OQ, rt_full_lt)
        csm_xml = get_csm(OQ, xml_full_lt)

        ae(len(csm_rt.src_groups), len(csm_xml.src_groups))
        srcs_rt = _sorted_srcs(csm_rt.src_groups)
        srcs_xml = _sorted_srcs(csm_xml.src_groups)
        for src_rt, src_xml in zip(srcs_rt, srcs_xml):
            # Check the src params in each src group
            _assert_src_params(src_rt, src_xml)

    def test_bad_weights(self):
        """
        Check incorrect weights raise error
        """
        xmls = list(self.rt_smlt._branch_xmls.values())
        bad = [('br_0', 0.5, xmls[0]), ('br_1', 0.3, xmls[1])]
        with self.assertRaises(ValueError):
            logictree.RuntimeSourceModelLT(bad, script_path='test.py')

    def test_bad_shape(self):
        """
        Direct construction with a non-triple or non-4 tuple
        branch raises.
        """
        bad = [('br_0', 1.0)]  # missing xml_str
        with self.assertRaises(ValueError):
            logictree.RuntimeSourceModelLT(bad, script_path='test.py')

    def test_duplicate_names(self):
        """
        Direct construction with duplicate branch names raises
        """
        xmls = list(self.rt_smlt._branch_xmls.values())
        bad = [('br_0', 0.5, xmls[0]), ('br_0', 0.5, xmls[1])]
        with self.assertRaises(ValueError):
            logictree.RuntimeSourceModelLT(bad, script_path='test.py')

    def test_geom_labels(self):
        """
        Sanity checks for the geom_label feature of RuntimeSourceModelLT:
        """
        xmls = list(self.rt_smlt._branch_xmls.values())

        # 1) A uniform 4-tuple list populates _branch_labels correctly,
        #    including the per-branch None opt-out (no caching for this
        #    source is applied)
        labelled = [
            ('br_0', 0.5, xmls[0], 'geom_A'),
            ('br_1', 0.3, xmls[1], 'geom_A'),
            ('br_2', 0.2, xmls[2], None),
        ]
        smlt = logictree.RuntimeSourceModelLT(labelled, script_path='test.py')
        self.assertEqual(smlt._branch_labels,
                         {'br_0': 'geom_A',
                          'br_1': 'geom_A',
                          'br_2': None}
                          )

        # 2) Mixing 3- and 4-tuples in one list raises ValueError
        mixed = [
            ('br_0', 0.5, xmls[0], 'geom_A'),
            ('br_1', 0.5, xmls[1]),
        ]
        with self.assertRaises(ValueError):
            logictree.RuntimeSourceModelLT(mixed, script_path='test.py')

        # 3) A non-string, non-None label raises ValueError
        bad_label = [('br_0', 1.0, xmls[0], 42)]
        with self.assertRaises(ValueError):
            logictree.RuntimeSourceModelLT(bad_label, script_path='test.py')

        # 4) The labels survive an HDF5 round-trip
        tmp = gettemp(suffix='.hdf5')
        with hdf5.File(tmp, 'w') as h:
            h['smlt'] = smlt # to hdf5
        with hdf5.File(tmp, 'r') as h:
            restored = h['smlt'] # from hdf5
        self.assertEqual(restored._branch_labels, smlt._branch_labels)
