# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2010-2023 GEM Foundation
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

import os
import pprint
import codecs
import unittest
import collections
from xml.parsers.expat import ExpatError
from copy import deepcopy
import numpy

from openquake.baselib import parallel, hdf5
from openquake.baselib.general import gettemp
import openquake.hazardlib
from openquake.hazardlib import geo, lt, gsim_lt, logictree
from openquake.commonlib import readinput, tests
from openquake.hazardlib.source_reader import get_csm
from openquake.hazardlib.tom import PoissonTOM
from openquake.hazardlib.pmf import PMF
from openquake.hazardlib.mfd import TruncatedGRMFD, EvenlyDiscretizedMFD


DATADIR = os.path.join(os.path.dirname(__file__), 'data')


class CompositeLtTestCase(unittest.TestCase):
    def test(self):
        # logic tree for Canada 2015
        ssmLT = os.path.join(DATADIR, 'ssmLT.xml')
        gmmLT = os.path.join(DATADIR, 'gmmLT.xml')
        smlt = logictree.SourceModelLogicTree(ssmLT, test_mode=True)
        gslt = logictree.GsimLogicTree(gmmLT)
        clt = logictree.compose(smlt, gslt)
        sizes = [len(bset) for bset in clt.branchsets]
        self.assertEqual(sizes, [6, 3, 3, 3, 3, 3, 3, 3])
        num_paths = numpy.prod(sizes)  # 13122
        self.assertEqual(len(clt.get_all_paths()), num_paths)


class _TestableSourceModelLogicTree(logictree.SourceModelLogicTree):
    def __init__(self, filename, files):
        # files is a dictionary name -> text containing also filename
        self.files = files
        f = gettemp(files[filename], suffix='.' + filename)
        super().__init__(f)

    def _get_source_model(self, filename):
        return open(gettemp(self.files[filename]))


def _make_nrml(content):
    return ("""<?xml version="1.0" encoding="UTF-8"?>
    <nrml xmlns:gml="http://www.opengis.net/gml"\
          xmlns="http://openquake.org/xmlns/nrml/0.4">\
        %s
    </nrml>""" % content)


def _whatever_sourcemodel():
    return _make_nrml("""\
    <sourceModel>
        <simpleFaultSource id="src01" name="Mount Diablo Thrust"
                           tectonicRegion="Active Shallow Crust">
            <simpleFaultGeometry>
                <gml:LineString srsName="urn:ogc:def:crs:EPSG::4326">
                    <gml:posList>
                        -121.82290 37.73010  0.0
                        -122.03880 37.87710  0.0
                    </gml:posList>
                </gml:LineString>
                <dip>38</dip>
                <upperSeismoDepth>8.0</upperSeismoDepth>
                <lowerSeismoDepth>13.0</lowerSeismoDepth>
            </simpleFaultGeometry>
            <magScaleRel>WC1994</magScaleRel>
            <ruptAspectRatio>1.5</ruptAspectRatio>
            <truncGutenbergRichterMFD aValue="-3.5" bValue="1.0"
                                      minMag="5.0" maxMag="7.0" />
            <rake>90.0</rake>
        </simpleFaultSource>

        <simpleFaultSource id="src02" name="Mount Diablo Thrust"
                           tectonicRegion="Active Shallow Crust">
            <simpleFaultGeometry>
                <gml:LineString srsName="urn:ogc:def:crs:EPSG::4326">
                    <gml:posList>
                        -121.82290 37.73010  0.0
                        -122.03880 37.87710  0.0
                    </gml:posList>
                </gml:LineString>
                <dip>38</dip>
                <upperSeismoDepth>8.0</upperSeismoDepth>
                <lowerSeismoDepth>13.0</lowerSeismoDepth>
            </simpleFaultGeometry>
            <magScaleRel>WC1994</magScaleRel>
            <ruptAspectRatio>1.5</ruptAspectRatio>
            <truncGutenbergRichterMFD aValue="-3.5" bValue="1.0"
                                      minMag="5.0" maxMag="7.0" />
            <rake>90.0</rake>
        </simpleFaultSource>

        <pointSource id="src03" name="point"
                     tectonicRegion="Active Shallow Crust">
            <pointGeometry>
                <gml:Point>
                    <gml:pos>-122.0 38.0</gml:pos>
                </gml:Point>
                <upperSeismoDepth>0.0</upperSeismoDepth>
                <lowerSeismoDepth>10.0</lowerSeismoDepth>
            </pointGeometry>
            <magScaleRel>WC1994</magScaleRel>
            <ruptAspectRatio>0.5</ruptAspectRatio>
            <truncGutenbergRichterMFD aValue="-3.5" bValue="1.0"
                                      minMag="5.0" maxMag="6.5" />
            <nodalPlaneDist>
                <nodalPlane probability="0.3" strike="0.0"
                            dip="90.0" rake="0.0" />
                <nodalPlane probability="0.7" strike="90.0"
                            dip="45.0" rake="90.0" />
            </nodalPlaneDist>
            <hypoDepthDist>
                <hypoDepth probability="0.5" depth="4.0" />
                <hypoDepth probability="0.5" depth="8.0" />
            </hypoDepthDist>
        </pointSource>
    </sourceModel>
    """)


def _whatever_sourcemodel_lt(sourcemodel_filename):
    return _make_nrml("""\
    <logicTree logicTreeID="lt1">
        <logicTreeBranchingLevel branchingLevelID="bl1">
            <logicTreeBranchSet uncertaintyType="sourceModel"
                                branchSetID="bs1">
                <logicTreeBranch branchID="b1">
                    <uncertaintyModel>%s</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                </logicTreeBranch>
            </logicTreeBranchSet>
        </logicTreeBranchingLevel>
    </logicTree>
    """ % sourcemodel_filename)


class SourceModelLogicTreeBrokenInputTestCase(unittest.TestCase):
    def _assert_logic_tree_error(self, filename, files,
                                 exc_class=logictree.LogicTreeError,
                                 exc_filename=None):
        with self.assertRaises(exc_class) as arc:
            _TestableSourceModelLogicTree(filename, files)
        exc = arc.exception
        if '.' in exc.filename:
            suffix = exc.filename.rsplit('.')[1]
            self.assertEqual(suffix, exc_filename or filename)
        return exc

    def test_logictree_invalid_xml(self):
        self._assert_logic_tree_error(
            'broken_xml', {'broken_xml': "<?xml foo bar baz"}, ExpatError)

    def test_logictree_schema_violation(self):
        source = _make_nrml("""\
            <logicTreeSet>
                <logicTree logicTreeID="lt1"/>
            </logicTreeSet>
        """)
        exc = self._assert_logic_tree_error(
            'screwed_schema', {'screwed_schema': source},
            logictree.LogicTreeError)
        self.assertIn('missing logicTree node', exc.message)

    def test_wrong_uncert_type_on_first_branching_level(self):
        source = _make_nrml("""\
            <logicTree logicTreeID="lt1">
              <logicTreeBranchingLevel branchingLevelID="bl1">
                <logicTreeBranchSet uncertaintyType="bGRRelative"
                                    branchSetID="bs1">
                  <logicTreeBranch branchID="b1">
                    <uncertaintyModel>+100</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
            </logicTree>
        """)
        exc = self._assert_logic_tree_error(
            'logictree', {'logictree': source}, logictree.LogicTreeError
        )
        self.assertEqual(exc.lineno, 4)
        error = 'first branchset must define an uncertainty ' \
                'of type "sourceModel"'
        self.assertTrue(error in str(exc),
                        "wrong exception message: %s" % exc)

    def test_source_model_uncert_on_wrong_level(self):
        lt = _make_nrml("""\
            <logicTree logicTreeID="lt1">
              <logicTreeBranchingLevel branchingLevelID="bl1">
                <logicTreeBranchSet uncertaintyType="sourceModel"
                                    branchSetID="bs1">
                  <logicTreeBranch branchID="b1">
                    <uncertaintyModel>sm1</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
              <logicTreeBranchingLevel branchingLevelID="bl1">
                <logicTreeBranchSet uncertaintyType="sourceModel"
                                    branchSetID="bs2">
                  <logicTreeBranch branchID="b2">
                    <uncertaintyModel>sm2</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
            </logicTree>
        """)
        sm = _whatever_sourcemodel()
        exc = self._assert_logic_tree_error(
            'lt', {'lt': lt, 'sm1': sm, 'sm2': sm}, logictree.LogicTreeError
        )
        self.assertEqual(exc.lineno, 13)
        error = 'uncertainty of type "sourceModel" can be defined ' \
                'on first branchset only'
        self.assertEqual(exc.message, error,
                         "wrong exception message: %s" % exc.message)

    def test_branch_id_not_unique(self):
        lt = _make_nrml("""\
            <logicTree logicTreeID="lt1">
              <logicTreeBranchingLevel branchingLevelID="bl1">
                <logicTreeBranchSet uncertaintyType="sourceModel"
                                    branchSetID="bs1">
                  <logicTreeBranch branchID="b1">
                    <uncertaintyModel>sm1</uncertaintyModel>
                    <uncertaintyWeight>0.7</uncertaintyWeight>
                  </logicTreeBranch>
                  <logicTreeBranch branchID="b1">
                    <uncertaintyModel>sm2</uncertaintyModel>
                    <uncertaintyWeight>0.4</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
            </logicTree>
        """)
        sm = _whatever_sourcemodel()
        exc = self._assert_logic_tree_error(
            'lt', {'lt': lt, 'sm1': sm, 'sm2': sm}, logictree.LogicTreeError
        )
        self.assertEqual(exc.lineno, 10)
        self.assertEqual(exc.message, "branchID 'b1' is not unique",
                         "wrong exception message: %s" % exc.message)

    def test_branches_weight_wrong_sum(self):
        lt = _make_nrml("""\
            <logicTree logicTreeID="lt1">
              <logicTreeBranchingLevel branchingLevelID="bl1">
                <logicTreeBranchSet uncertaintyType="sourceModel"
                                    branchSetID="bs1">
                  <logicTreeBranch branchID="b1">
                    <uncertaintyModel>sm1</uncertaintyModel>
                    <uncertaintyWeight>0.7</uncertaintyWeight>
                  </logicTreeBranch>
                  <logicTreeBranch branchID="b2">
                    <uncertaintyModel>sm2</uncertaintyModel>
                    <uncertaintyWeight>0.4</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
            </logicTree>
        """)
        sm = _whatever_sourcemodel()
        exc = self._assert_logic_tree_error(
            'lo', {'lo': lt, 'sm1': sm, 'sm2': sm}, logictree.LogicTreeError)
        self.assertEqual(exc.lineno, 4)
        self.assertEqual(exc.message, "branchset weights don't sum up to 1.0",
                         "wrong exception message: %s" % exc.message)

    def test_apply_to_nonexistent_branch(self):
        lt = _make_nrml("""\
            <logicTree logicTreeID="lt1">
              <logicTreeBranchingLevel branchingLevelID="bl1">
                <logicTreeBranchSet uncertaintyType="sourceModel"
                                    branchSetID="bs1">
                  <logicTreeBranch branchID="b1">
                    <uncertaintyModel>sm.xml</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
              <logicTreeBranchingLevel branchingLevelID="bl2">
                <logicTreeBranchSet uncertaintyType="bGRRelative"
                                    branchSetID="bs2"
                                    applyToBranches="mssng">
                  <logicTreeBranch branchID="b2">
                    <uncertaintyModel>123</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
            </logicTree>
        """)
        sm = _whatever_sourcemodel()
        exc = self._assert_logic_tree_error('lt', {'lt': lt, 'sm.xml': sm},
                                            logictree.LogicTreeError)
        self.assertEqual(exc.lineno, 13)
        self.assertEqual(exc.message, "branch 'mssng' is not yet defined",
                         "wrong exception message: %s" % exc.message)

    def test_apply_to_occupied_branch(self):
        lt = _make_nrml("""\
            <logicTree logicTreeID="lt1">
                <logicTreeBranchSet uncertaintyType="sourceModel"
                                    branchSetID="bs1">
                  <logicTreeBranch branchID="b1">
                    <uncertaintyModel>sm.xml</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
                <logicTreeBranchSet uncertaintyType="bGRRelative"
                                    branchSetID="bs2"
                                    applyToBranches="b1">
                  <logicTreeBranch branchID="b2">
                    <uncertaintyModel>123</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
                <logicTreeBranchSet uncertaintyType="bGRRelative"
                                    branchSetID="bs3"
                                    applyToBranches="b1">
                  <logicTreeBranch branchID="b3">
                    <uncertaintyModel>123</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
            </logicTree>
        """)
        sm = _whatever_sourcemodel()
        exc = self._assert_logic_tree_error('lt', {'lt': lt, 'sm.xml': sm},
                                            logictree.LogicTreeError)
        self.assertEqual(exc.lineno, 18)
        error = "branch 'b1' already has child branchset"
        self.assertEqual(exc.message, error,
                         "wrong exception message: %s" % exc.message)

    def test_ab_gr_absolute_wrong_format(self):
        lt = _make_nrml("""\
            <logicTree logicTreeID="lt1">
              <logicTreeBranchingLevel branchingLevelID="bl1">
                <logicTreeBranchSet uncertaintyType="sourceModel"
                                    branchSetID="bs1">
                  <logicTreeBranch branchID="b1">
                    <uncertaintyModel>sm.xml</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
              <logicTreeBranchingLevel branchingLevelID="bl2">
                <logicTreeBranchSet uncertaintyType="abGRAbsolute"
                                    applyToSources="src01"
                                    branchSetID="bs2">
                  <logicTreeBranch branchID="b2">
                    <uncertaintyModel>123.45</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
            </logicTree>
        """)

        sm = _whatever_sourcemodel()

        exc = self._assert_logic_tree_error('lt', {'lt': lt, 'sm.xml': sm},
                                            logictree.LogicTreeError)
        self.assertEqual(exc.lineno, 17, exc)
        error = "expected a pair of floats separated by space"
        self.assertEqual(exc.message, error,
                         "wrong exception message: %s" % exc.message)

    def test_b_gr_relative_wrong_format(self):
        lt = _make_nrml("""\
            <logicTree logicTreeID="lt1">
              <logicTreeBranchingLevel branchingLevelID="bl1">
                <logicTreeBranchSet uncertaintyType="sourceModel"
                                    branchSetID="bs1">
                  <logicTreeBranch branchID="b1">
                    <uncertaintyModel>sm.xml</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
              <logicTreeBranchingLevel branchingLevelID="bl2">
                <logicTreeBranchSet uncertaintyType="bGRRelative"
                                    branchSetID="bs2">
                  <logicTreeBranch branchID="b2">
                    <uncertaintyModel>123.45z</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
            </logicTree>
        """)
        sm = _whatever_sourcemodel()
        exc = self._assert_logic_tree_error(
            'lt', {'lt': lt, 'sm.xml': sm}, logictree.LogicTreeError)
        self.assertEqual(exc.lineno, 16)
        self.assertEqual(exc.message, 'expected single float value',
                         "wrong exception message: %s" % exc.message)

    def test_incremental_mfd_absolute_wrong_format(self):
        lt = _make_nrml("""\
            <logicTree logicTreeID="lt1">
              <logicTreeBranchingLevel branchingLevelID="bl1">
                <logicTreeBranchSet uncertaintyType="sourceModel"
                                    branchSetID="bs1">
                  <logicTreeBranch branchID="b1">
                    <uncertaintyModel>sm.xml</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
              <logicTreeBranchingLevel branchingLevelID="bl2">
                <logicTreeBranchSet uncertaintyType="incrementalMFDAbsolute"
                                    branchSetID="bs2">
                  <logicTreeBranch branchID="b2">
                    <uncertaintyModel>
                        <incrementalMFD binWidth="0.1" minMag="8.0">
                            <occurRates>-0.01 0.005</occurRates>
                        </incrementalMFD>
                    </uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
            </logicTree>
        """)
        sm = _whatever_sourcemodel()
        with self.assertRaises(ValueError) as arc:
            _TestableSourceModelLogicTree(
                'lt', {'lt': lt, 'sm.xml': sm})
        self.assertIn(
            "Could not convert occurRates->positivefloats: "
            "float -0.01 < 0, line 18", str(arc.exception))

    def test_simple_fault_geometry_absolute_wrong_format(self):
        lt = _make_nrml("""\
            <logicTree logicTreeID="lt1">
              <logicTreeBranchingLevel branchingLevelID="bl1">
                <logicTreeBranchSet uncertaintyType="sourceModel"
                                    branchSetID="bs1">
                  <logicTreeBranch branchID="b1">
                    <uncertaintyModel>sm.xml</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
              <logicTreeBranchingLevel branchingLevelID="bl2">
                <logicTreeBranchSet
                   uncertaintyType="simpleFaultGeometryAbsolute"
                   branchSetID="bs1"
                   applyToSources="src01">
                  <logicTreeBranch branchID="b2">
                    <uncertaintyModel>
                        <simpleFaultGeometry spacing="1.0">
                            <gml:LineString>
                                <gml:posList>
                                    -121.8229 wrong -122.0388 37.8771
                                </gml:posList>
                            </gml:LineString>
                            <dip>
                                45.0
                            </dip>
                            <upperSeismoDepth>
                                10.0
                            </upperSeismoDepth>
                            <lowerSeismoDepth>
                                20.0
                            </lowerSeismoDepth>
                        </simpleFaultGeometry>
                    </uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
            </logicTree>
        """)
        sm = _whatever_sourcemodel()
        exc = self._assert_logic_tree_error(
            'lt', {'lt': lt, 'sm.xml': sm}, ValueError)
        self.assertIn("Found a non-float in -121.8229 wrong "
                      "-122.0388 37.8771: 'wrong' is not a float",
                      str(exc))

    def test_complex_fault_geometry_absolute_wrong_format(self):
        lt = _make_nrml("""\
            <logicTree logicTreeID="lt1">
              <logicTreeBranchingLevel branchingLevelID="bl1">
                <logicTreeBranchSet uncertaintyType="sourceModel"
                                    branchSetID="bs1">
                  <logicTreeBranch branchID="b1">
                    <uncertaintyModel>sm.xml</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
              <logicTreeBranchingLevel branchingLevelID="bl2">
                <logicTreeBranchSet
                   uncertaintyType="complexFaultGeometryAbsolute"
                   branchSetID="bs1"
                   applyToSources="src01">
                  <logicTreeBranch branchID="b2">
                    <uncertaintyModel>
                        <complexFaultGeometry spacing="5.0">
                            <faultTopEdge>
                                <gml:LineString>
                                    <gml:posList>
                                        0.0 0.0 0.0 1.0 0.0 0.0
                                    </gml:posList>
                                </gml:LineString>
                            </faultTopEdge>
                            <faultBottomEdge>
                                <gml:LineString>
                                    <gml:posList>
                                        0.0 -0.1 0.0 1.0 wrong 0.0
                                    </gml:posList>
                                </gml:LineString>
                            </faultBottomEdge>
                        </complexFaultGeometry>
                    </uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
            </logicTree>
        """)
        sm = _whatever_sourcemodel()
        exc = self._assert_logic_tree_error(
            'lt', {'lt': lt, 'sm.xml': sm}, ValueError)
        self.assertIn('Could not convert posList->posList: Found a non-float ',
                      str(exc))

    def test_characteristic_fault_planar_geometry_wrong_format(self):
        lt = _make_nrml("""\
            <logicTree logicTreeID="lt1">
              <logicTreeBranchingLevel branchingLevelID="bl1">
                <logicTreeBranchSet uncertaintyType="sourceModel"
                                    branchSetID="bs1">
                  <logicTreeBranch branchID="b1">
                    <uncertaintyModel>sm.xml</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
              <logicTreeBranchingLevel branchingLevelID="bl2">
                <logicTreeBranchSet
                  uncertaintyType="characteristicFaultGeometryAbsolute"
                  branchSetID="bs1"
                  applyToSources="src01">
                  <logicTreeBranch branchID="b2">
                    <uncertaintyModel>
                        <surface>
                            <planarSurface
                            dip="9.696547068"
                            strike="89.98254582"
                            spacing="1.0"
                            >
                                <topLeft depth="21.0" lat="1.0" lon="-1.0"/>
                                <topRight depth="21.0" lat="rubbish" lon="1.0"/>
                                <bottomLeft depth="59.0" lat="-1.0" lon="-1.0"/>
                                <bottomRight depth="59.0" lat="-1.0" lon="1.0"/>
                            </planarSurface>
                        </surface>
                    </uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
            </logicTree>
        """)
        sm = _whatever_sourcemodel()
        exc = self._assert_logic_tree_error(
            'lt', {'lt': lt, 'sm.xml': sm}, ValueError)
        self.assertIn('Could not convert lat->latitude', str(exc))

    def test_characteristic_fault_simple_geometry_wrong_format(self):
        lt = _make_nrml("""\
            <logicTree logicTreeID="lt1">
              <logicTreeBranchingLevel branchingLevelID="bl1">
                <logicTreeBranchSet uncertaintyType="sourceModel"
                                    branchSetID="bs1">
                  <logicTreeBranch branchID="b1">
                    <uncertaintyModel>sm.xml</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
              <logicTreeBranchingLevel branchingLevelID="bl2">
                <logicTreeBranchSet
                   uncertaintyType="characteristicFaultGeometryAbsolute"
                   branchSetID="bs1"
                   applyToSources="src01">
                  <logicTreeBranch branchID="b2">
                    <uncertaintyModel>
                        <surface>
                            <simpleFaultGeometry spacing="1.0">
                                <gml:LineString>
                                    <gml:posList>
                                        -121.8229 wrong -122.0388 37.8771
                                    </gml:posList>
                                </gml:LineString>
                                <dip>
                                    45.0
                                </dip>
                                <upperSeismoDepth>
                                    10.0
                                </upperSeismoDepth>
                                <lowerSeismoDepth>
                                    20.0
                                </lowerSeismoDepth>
                            </simpleFaultGeometry>
                        </surface>
                    </uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
            </logicTree>
        """)
        sm = _whatever_sourcemodel()
        exc = self._assert_logic_tree_error(
            'lt', {'lt': lt, 'sm.xml': sm}, ValueError)
        self.assertIn('Could not convert posList->posList: Found a non-float',
                      str(exc))

    def test_characteristic_fault_complex_geometry_wrong_format(self):
        lt = _make_nrml("""\
            <logicTree logicTreeID="lt1">
              <logicTreeBranchingLevel branchingLevelID="bl1">
                <logicTreeBranchSet uncertaintyType="sourceModel"
                                    branchSetID="bs1">
                  <logicTreeBranch branchID="b1">
                    <uncertaintyModel>sm.xml</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
              <logicTreeBranchingLevel branchingLevelID="bl2">
                <logicTreeBranchSet
                   uncertaintyType="characteristicFaultGeometryAbsolute"
                   branchSetID="bs1"
                   applyToSources="src01">
                  <logicTreeBranch branchID="b2">
                    <uncertaintyModel>
                        <surface>
                            <complexFaultGeometry spacing="5.0">
                                <faultTopEdge>
                                    <gml:LineString>
                                        <gml:posList>
                                            0.0 0.0 0.0 1.0 0.0 0.0
                                        </gml:posList>
                                    </gml:LineString>
                                </faultTopEdge>
                                <faultBottomEdge>
                                    <gml:LineString>
                                        <gml:posList>
                                            0.0 -0.1 0.0 1.0 wrong 0.0
                                        </gml:posList>
                                    </gml:LineString>
                                </faultBottomEdge>
                            </complexFaultGeometry>
                        </surface>
                    </uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
            </logicTree>
        """)
        sm = _whatever_sourcemodel()
        exc = self._assert_logic_tree_error(
            'lt', {'lt': lt, 'sm.xml': sm}, ValueError)
        self.assertIn('Could not convert posList->posList: Found a non-float',
                      str(exc))

    def test_characteristic_fault_invalid_geometry(self):
        lt = _make_nrml("""\
            <logicTree logicTreeID="lt1">
              <logicTreeBranchingLevel branchingLevelID="bl1">
                <logicTreeBranchSet uncertaintyType="sourceModel"
                                    branchSetID="bs1">
                  <logicTreeBranch branchID="b1">
                    <uncertaintyModel>sm.xml</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
              <logicTreeBranchingLevel branchingLevelID="bl2">
                <logicTreeBranchSet uncertaintyType="characteristicFaultGeometryAbsolute"
                                    branchSetID="bs2"
                                    applyToSources="src01">
                  <logicTreeBranch branchID="b2">
                    <uncertaintyModel>
                        <surface>
                            <badFaultGeometry spacing="5.0">XXX</badFaultGeometry>
                        </surface>
                    </uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
            </logicTree>
        """)
        sm = _whatever_sourcemodel()
        exc = self._assert_logic_tree_error('lt', {'lt': lt, 'sm.xml': sm},
                                            logictree.LogicTreeError)
        self.assertEqual(
            exc.message,
            "Surface geometry type not recognised",
            "wrong exception message: %s" % exc.message)

    def test_source_model_invalid_xml(self):
        lt = _make_nrml("""\
            <logicTree logicTreeID="lt1">
              <logicTreeBranchingLevel branchingLevelID="bl1">
                <logicTreeBranchSet uncertaintyType="sourceModel"
                                    branchSetID="bs1">
                  <logicTreeBranch branchID="b1">
                    <uncertaintyModel>sm.xml</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
            </logicTree>
        """)
        sm = """ololo"""

        self._assert_logic_tree_error(
            'sm', {'lt': lt, 'sm': sm}, ExpatError, exc_filename='sm')

    def test_apply_to_branches(self):
        smlt = _make_nrml("""\
            <logicTree logicTreeID="lt1">
                <logicTreeBranchSet uncertaintyType="sourceModel"
                                    branchSetID="bs1">
                  <logicTreeBranch branchID="b1">
                    <uncertaintyModel>sm1.xml</uncertaintyModel>
                    <uncertaintyWeight>0.5</uncertaintyWeight>
                  </logicTreeBranch>
                  <logicTreeBranch branchID="b2">
                    <uncertaintyModel>sm2.xml</uncertaintyModel>
                    <uncertaintyWeight>0.5</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
                <logicTreeBranchSet uncertaintyType="abGRAbsolute"
                                    branchSetID="bs2" applyToSources="src01"
                                    applyToBranches="b1">
                  <logicTreeBranch branchID="b3">
                    <uncertaintyModel>1 2</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
                <logicTreeBranchSet uncertaintyType="abGRAbsolute"
                                    branchSetID="bs3" applyToSources="src01"
                                    applyToBranches="b2">
                  <logicTreeBranch branchID="b4">
                    <uncertaintyModel>1 2</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
            </logicTree>
        """)
        sm = _whatever_sourcemodel()
        lt = _TestableSourceModelLogicTree(
            'lt', {'lt': smlt, 'sm1.xml': sm, 'sm2.xml': sm})
        self.assertEqual(
            str(lt), '<_TestableSourceModelLogicTree<sourceModel(2)>>')

    def test_gmpe_uncertainty(self):
        lt = _make_nrml("""\
            <logicTree logicTreeID="lt1">
              <logicTreeBranchingLevel branchingLevelID="bl1">
                <logicTreeBranchSet uncertaintyType="sourceModel"
                                    branchSetID="bs1">
                  <logicTreeBranch branchID="b1">
                    <uncertaintyModel>sm.xml</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
              <logicTreeBranchingLevel branchingLevelID="bl2">
                <logicTreeBranchSet uncertaintyType="gmpeModel"
                                    branchSetID="bs2">
                  <logicTreeBranch branchID="b2">
                    <uncertaintyModel>CL_2002_AttenRel</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
            </logicTree>
        """)
        sm = _whatever_sourcemodel()
        exc = self._assert_logic_tree_error(
            'lt', {'lt': lt, 'sm.xml': sm}, logictree.LogicTreeError)
        self.assertEqual(exc.lineno, 13)
        error = 'uncertainty of type "gmpeModel" is not allowed ' \
                'in source model logic tree'
        self.assertEqual(exc.message, error,
                         "wrong exception message: %s" % exc.message)

    def test_referencing_nonexistent_source(self):
        lt = _make_nrml("""\
            <logicTree logicTreeID="lt1">
              <logicTreeBranchingLevel branchingLevelID="bl1">
                <logicTreeBranchSet uncertaintyType="sourceModel"
                                    branchSetID="bs1">
                  <logicTreeBranch branchID="b1">
                    <uncertaintyModel>sm.xml</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
              <logicTreeBranchingLevel branchingLevelID="bl2">
                <logicTreeBranchSet uncertaintyType="maxMagGRRelative"
                                    branchSetID="bs1"
                                    applyToSources="bzzz">
                  <logicTreeBranch branchID="b2">
                    <uncertaintyModel>123</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
            </logicTree>
        """)
        sm = _whatever_sourcemodel()
        exc = self._assert_logic_tree_error('lt', {'lt': lt, 'sm.xml': sm},
                                            logictree.LogicTreeError)
        self.assertEqual(exc.lineno, 13)
        error = "source with id 'bzzz' is not defined in source models"
        self.assertEqual(exc.message, error,
                         "wrong exception message: %s" % exc.message)

    def test_referencing_nonexistent_tectonic_region_type(self):
        lt = _make_nrml("""\
            <logicTree logicTreeID="lt1">
              <logicTreeBranchingLevel branchingLevelID="bl1">
                <logicTreeBranchSet uncertaintyType="sourceModel"
                                    branchSetID="bs1">
                  <logicTreeBranch branchID="b1">
                    <uncertaintyModel>sm.xml</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
              <logicTreeBranchingLevel branchingLevelID="bl2">
                <logicTreeBranchSet uncertaintyType="maxMagGRRelative"
                                    branchSetID="bs1"
                                    applyToTectonicRegionType="Volcanic">
                  <logicTreeBranch branchID="b2">
                    <uncertaintyModel>123</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
            </logicTree>
        """)
        sm = _whatever_sourcemodel()
        exc = self._assert_logic_tree_error('lt', {'lt': lt, 'sm.xml': sm},
                                            logictree.LogicTreeError)
        self.assertEqual(exc.lineno, 13)
        error = "source models don't define sources of " \
                "tectonic region type 'Volcanic'"
        self.assertEqual(exc.message, error,
                         "wrong exception message: %s" % exc.message)

    def test_more_than_one_filters_on_one_branchset(self):
        lt = _make_nrml("""\
            <logicTree logicTreeID="lt1">
              <logicTreeBranchingLevel branchingLevelID="bl1">
                <logicTreeBranchSet uncertaintyType="sourceModel"
                                    branchSetID="bs1">
                  <logicTreeBranch branchID="b1">
                    <uncertaintyModel>sm.xml</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
              <logicTreeBranchingLevel branchingLevelID="bl2">
                <logicTreeBranchSet uncertaintyType="maxMagGRRelative"
                            branchSetID="bs1"
                            applyToTectonicRegionType="Active Shallow Crust"
                            applyToSources="src01">
                  <logicTreeBranch branchID="b2">
                    <uncertaintyModel>123</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
            </logicTree>
        """)
        sm = _whatever_sourcemodel()
        exc = self._assert_logic_tree_error('lt', {'lt': lt, 'sm.xml': sm},
                                            logictree.LogicTreeError)
        self.assertEqual(exc.lineno, 13)
        error = 'only one filter is allowed per branchset'
        self.assertEqual(exc.message, error,
                         "wrong exception message: %s" % exc.message)

    def test_wrong_filter_on_absolute_uncertainties(self):
        uncertainties_and_values = [('abGRAbsolute', '123 45'),
                                    ('maxMagGRAbsolute', '678')]
        filters = ('applyToSources="src01 src02"',
                   'applyToTectonicRegionType="Active Shallow Crust"')
        for uncertainty, value in uncertainties_and_values:
            for filter_ in filters:
                lt = _make_nrml("""\
                    <logicTree logicTreeID="lt1">
                      <logicTreeBranchingLevel branchingLevelID="bl1">
                        <logicTreeBranchSet uncertaintyType="sourceModel"
                                            branchSetID="bs1">
                          <logicTreeBranch branchID="b1">
                            <uncertaintyModel>sm.xml</uncertaintyModel>
                            <uncertaintyWeight>1.0</uncertaintyWeight>
                          </logicTreeBranch>
                        </logicTreeBranchSet>
                      </logicTreeBranchingLevel>
                      <logicTreeBranchingLevel branchingLevelID="bl2">
                        <logicTreeBranchSet uncertaintyType="%s"
                                    branchSetID="bs1" %s>
                          <logicTreeBranch branchID="b2">
                            <uncertaintyModel>%s</uncertaintyModel>
                            <uncertaintyWeight>1.0</uncertaintyWeight>
                          </logicTreeBranch>
                        </logicTreeBranchSet>
                      </logicTreeBranchingLevel>
                    </logicTree>
                """ % (uncertainty, filter_, value))
                sm = _whatever_sourcemodel()
                exc = self._assert_logic_tree_error(
                    'lt', {'lt': lt, 'sm.xml': sm}, logictree.LogicTreeError)
                self.assertEqual(exc.lineno, 13)
                error = (
                    "uncertainty of type '%s' must define 'applyToSources'"
                    " with only one source id" % uncertainty)
                self.assertEqual(
                    exc.message, error,
                    "wrong exception message: %s" % exc.message)

    def test_duplicated_values(self):
        sm = _whatever_sourcemodel()
        lt = _make_nrml("""\
        <logicTree>
         <logicTreeBranchSet uncertaintyType="sourceModel"
                             branchSetID="bs1">
            <logicTreeBranch branchID="b1">
              <uncertaintyModel>sm.xml</uncertaintyModel>
              <uncertaintyWeight>1.0</uncertaintyWeight>
            </logicTreeBranch>
          </logicTreeBranchSet>
          <logicTreeBranchSet branchSetID="bs2" uncertaintyType="bGRRelative">
            <logicTreeBranch branchID="b71">
                 <uncertaintyModel> 7.7 </uncertaintyModel>
                 <uncertaintyWeight>0.333</uncertaintyWeight>
             </logicTreeBranch>
             <logicTreeBranch branchID="b72">
                 <uncertaintyModel> 7.695 </uncertaintyModel>
                 <uncertaintyWeight>0.333</uncertaintyWeight>
             </logicTreeBranch>
             <logicTreeBranch branchID="b73">
                 <uncertaintyModel> 7.7 </uncertaintyModel>
                 <uncertaintyWeight>0.334</uncertaintyWeight>
            </logicTreeBranch>
          </logicTreeBranchSet>
        </logicTree>
        """)
        exc = self._assert_logic_tree_error(
            'lt', {'lt': lt, 'sm.xml': sm}, logictree.LogicTreeError)
        self.assertIn('duplicate values in uncertaintyModel: 7.7 7.695 7.7',
                      str(exc))


class SourceModelLogicTreeTestCase(unittest.TestCase):
    def assert_branch_equal(self, branch, branch_id, weight_str, value,
                            bset_args=None):
        self.assertEqual(type(branch), logictree.Branch)
        self.assertEqual(branch.branch_id, branch_id)
        self.assertEqual(branch.weight, float(weight_str))
        self.assertEqual(branch.value, value)
        if bset_args:
            self.assert_branchset_equal(branch.bset, *bset_args)
        else:
            self.assertTrue(branch.is_leaf())

    def assert_branchset_equal(self, branchset, uncertainty_type, filters,
                               branches_args):
        self.assertEqual(type(branchset), logictree.BranchSet)
        self.assertEqual(branchset.uncertainty_type, uncertainty_type)
        self.assertEqual(branchset.filters, filters)
        self.assertEqual(len(branchset.branches), len(branches_args))
        for branch, args in zip(branchset.branches, branches_args):
            self.assert_branch_equal(branch, *args)

    def test_only_source_models(self):
        source_model_logic_tree = _make_nrml("""\
        <logicTree logicTreeID="lt1">
            <logicTreeBranchingLevel branchingLevelID="bl1">
                <logicTreeBranchSet uncertaintyType="sourceModel"
                                    branchSetID="bs1">
                    <logicTreeBranch branchID="b1">
                        <uncertaintyModel>sm1.xml</uncertaintyModel>
                        <uncertaintyWeight>0.6</uncertaintyWeight>
                    </logicTreeBranch>
                    <logicTreeBranch branchID="b2">
                        <uncertaintyModel>sm2.xml</uncertaintyModel>
                        <uncertaintyWeight>0.4</uncertaintyWeight>
                    </logicTreeBranch>
                </logicTreeBranchSet>
            </logicTreeBranchingLevel>
        </logicTree>
        """)
        sm = _whatever_sourcemodel()
        lt = _TestableSourceModelLogicTree(
            'lt',
            {'lt': source_model_logic_tree, 'sm1.xml': sm, 'sm2.xml': sm})
        self.assert_branchset_equal(lt.root_branchset, 'sourceModel', {},
                                    [('b1', '0.6', 'sm1.xml'),
                                     ('b2', '0.4', 'sm2.xml')])

    def test_two_levels(self):
        source_model_logic_tree = _make_nrml("""\
        <logicTree logicTreeID="lt1">
            <logicTreeBranchingLevel branchingLevelID="bl1">
                <logicTreeBranchSet uncertaintyType="sourceModel"
                                    branchSetID="bs1">
                    <logicTreeBranch branchID="b1">
                        <uncertaintyModel>sm.xml</uncertaintyModel>
                        <uncertaintyWeight>1.0</uncertaintyWeight>
                    </logicTreeBranch>
                </logicTreeBranchSet>
            </logicTreeBranchingLevel>
            <logicTreeBranchingLevel branchingLevelID="bl2">
                <logicTreeBranchSet uncertaintyType="maxMagGRRelative"
                                    branchSetID="bs2">
                    <logicTreeBranch branchID="b2">
                        <uncertaintyModel>123</uncertaintyModel>
                        <uncertaintyWeight>0.6</uncertaintyWeight>
                    </logicTreeBranch>
                    <logicTreeBranch branchID="b3">
                        <uncertaintyModel>-123</uncertaintyModel>
                        <uncertaintyWeight>0.4</uncertaintyWeight>
                    </logicTreeBranch>
                </logicTreeBranchSet>
            </logicTreeBranchingLevel>
        </logicTree>
        """)
        sm = _whatever_sourcemodel()
        lt = _TestableSourceModelLogicTree(
            'lt', {'lt': source_model_logic_tree, 'sm.xml': sm})
        self.assert_branchset_equal(lt.root_branchset,
                                    'sourceModel', {},
                                    [('b1', '1.0', 'sm.xml',
                                      ('maxMagGRRelative', {},
                                       [('b2', '0.6', +123),
                                        ('b3', '0.4', -123)])
                                      )])

    def test_filters(self):
        source_model_logic_tree = _make_nrml("""\
        <logicTree logicTreeID="lt1">
            <logicTreeBranchingLevel branchingLevelID="bl1">
                <logicTreeBranchSet uncertaintyType="sourceModel"
                                    branchSetID="bs1">
                    <logicTreeBranch branchID="b1">
                        <uncertaintyModel>sm.xml</uncertaintyModel>
                        <uncertaintyWeight>1.0</uncertaintyWeight>
                    </logicTreeBranch>
                </logicTreeBranchSet>
            </logicTreeBranchingLevel>
            <logicTreeBranchingLevel branchingLevelID="bl2">
                <logicTreeBranchSet uncertaintyType="abGRAbsolute"
                                    branchSetID="bs2"
                                    applyToSources="src01">
                    <logicTreeBranch branchID="b2">
                        <uncertaintyModel>100 500</uncertaintyModel>
                        <uncertaintyWeight>0.9</uncertaintyWeight>
                    </logicTreeBranch>
                    <logicTreeBranch branchID="b3">
                        <uncertaintyModel>-1.23 +0.1</uncertaintyModel>
                        <uncertaintyWeight>0.1</uncertaintyWeight>
                    </logicTreeBranch>
                </logicTreeBranchSet>
            </logicTreeBranchingLevel>
        </logicTree>
        """)
        sm = _whatever_sourcemodel()
        lt = _TestableSourceModelLogicTree(
            'lt', {'lt': source_model_logic_tree, 'sm.xml': sm})
        self.assert_branchset_equal(
            lt.root_branchset,
            'sourceModel', {},
            [('b1', '1.0', 'sm.xml',
              ('abGRAbsolute', {'applyToSources': ['src01']},
               [('b2', '0.9', (100, 500)),
                ('b3', '0.1', (-1.23, +0.1))])
              )])

    def test_apply_to_branches(self):
        source_model_logic_tree = _make_nrml("""\
        <logicTree logicTreeID="lt1">
                <logicTreeBranchSet uncertaintyType="sourceModel"
                                    branchSetID="bs1">
                    <logicTreeBranch branchID="sb1">
                        <uncertaintyModel>sm1.xml</uncertaintyModel>
                        <uncertaintyWeight>0.6</uncertaintyWeight>
                    </logicTreeBranch>
                    <logicTreeBranch branchID="sb2">
                        <uncertaintyModel>sm2.xml</uncertaintyModel>
                        <uncertaintyWeight>0.3</uncertaintyWeight>
                    </logicTreeBranch>
                    <logicTreeBranch branchID="sb3">
                        <uncertaintyModel>sm3.xml</uncertaintyModel>
                        <uncertaintyWeight>0.1</uncertaintyWeight>
                    </logicTreeBranch>
                </logicTreeBranchSet>
                <logicTreeBranchSet uncertaintyType="bGRRelative"
                                    branchSetID="bs2"
                                    applyToBranches="sb1 sb3">
                    <logicTreeBranch branchID="b2">
                        <uncertaintyModel>+1</uncertaintyModel>
                        <uncertaintyWeight>1.0</uncertaintyWeight>
                    </logicTreeBranch>
                </logicTreeBranchSet>
                <logicTreeBranchSet uncertaintyType="maxMagGRAbsolute"
                                    branchSetID="bs3"
                                    applyToSources="src01"
                                    applyToBranches="sb2">
                    <logicTreeBranch branchID="b3">
                        <uncertaintyModel>-3</uncertaintyModel>
                        <uncertaintyWeight>1.0</uncertaintyWeight>
                    </logicTreeBranch>
                </logicTreeBranchSet>
        </logicTree>
        """)
        sm = _whatever_sourcemodel()
        lt = _TestableSourceModelLogicTree(
            'lt', {'lt': source_model_logic_tree,
                   'sm1.xml': sm, 'sm2.xml': sm, 'sm3.xml': sm})
        self.assert_branchset_equal(
            lt.root_branchset,
            'sourceModel', {},
            [('sb1', '0.6', 'sm1.xml',
              ('bGRRelative', {'applyToBranches': ['sb1', 'sb3']},
               [('b2', '1.0', +1)]
               )),
             ('sb2', '0.3', 'sm2.xml',
              ('maxMagGRAbsolute', {'applyToSources': ['src01'],
                                    'applyToBranches': ['sb2']},
               [('b3', '1.0', -3)]
               )),
             ('sb3', '0.1', 'sm3.xml',
              ('bGRRelative', {'applyToBranches': ['sb1', 'sb3']},
               [('b2', '1.0', +1)]
               ))
             ]
            )
        sb1, sb2, sb3 = lt.root_branchset.branches
        self.assertTrue(sb1.bset is sb3.bset)
        self.assertEqual(
            str(lt), '<_TestableSourceModelLogicTree<sourceModel(3)>>')

    def test_comments(self):
        source_model_logic_tree = _make_nrml("""\
        <!-- comment -->
        <logicTree logicTreeID="lt1">
            <!-- comment -->
            <logicTreeBranchingLevel branchingLevelID="bl1">
                <!-- comment -->
                <logicTreeBranchSet uncertaintyType="sourceModel"
                                    branchSetID="bs1">
                    <!-- comment -->
                    <logicTreeBranch branchID="b1">
                        <!-- comment -->
                        <uncertaintyModel>sm.xml</uncertaintyModel>
                        <!-- comment -->
                        <uncertaintyWeight>1.0</uncertaintyWeight>
                        <!-- comment -->
                    </logicTreeBranch>
                    <!-- comment -->
                </logicTreeBranchSet>
                <!-- comment -->
            </logicTreeBranchingLevel>
        <!-- comment -->
        </logicTree>
        <!-- comment -->
        """)
        sm = _whatever_sourcemodel()
        lt = _TestableSourceModelLogicTree(
            'lt', {'lt': source_model_logic_tree, 'sm.xml': sm})
        self.assert_branchset_equal(
            lt.root_branchset, 'sourceModel', {}, [('b1', '1.0', 'sm.xml')])


class SampleTestCase(unittest.TestCase):

    def test_sample(self):
        branches = [logictree.Branch('BS', 1, 0.2, 'A'),
                    logictree.Branch('BS', 1, 0.3, 'B'),
                    logictree.Branch('BS', 1, 0.5, 'C')]
        probs = lt.random(1000, 42, 'early_weights')
        samples = lt.sample(branches, probs, 'early_weights')

        def count(samples, value):
            return sum(s.value == value for s in samples)

        self.assertEqual(count(samples, value='A'), 225)
        self.assertEqual(count(samples, value='B'), 278)
        self.assertEqual(count(samples, value='C'), 497)

    def test_sample_broken_branch_weights(self):
        branches = [logictree.Branch('BS', 0, 0.1, 0),
                    logictree.Branch('BS', 1, 0.2, 1)]
        probs = lt.random(1000, 42, 'early_weights')
        with self.assertRaises(IndexError):
            lt.sample(branches, probs, 'early_weights')

    def test_sample_one_branch(self):
        # always the same branch is returned
        branches = [logictree.Branch('BS', 0, 1.0, 0)]
        probs = lt.random(1000, 42, 'early_weights')
        bs = lt.sample(branches, probs, 'early_weights')
        for b in bs:
            self.assertEqual(b.branch_id, 0)


class BranchSetEnumerateTestCase(unittest.TestCase):
    def test_enumerate(self):
        b0 = logictree.Branch('BS1', '0', 0.64, '0')
        b1 = logictree.Branch('BS1', '1', 0.36, '1')
        b00 = logictree.Branch('BS2', '0.0', 0.33, '0.0')
        b01 = logictree.Branch('BS2', '0.1', 0.27, '0.1')
        b02 = logictree.Branch('BS2', '0.2', 0.4, '0.2')
        b10 = logictree.Branch('BS3', '1.0', 1.0, '1.0')
        b100 = logictree.Branch('BS4', '1.0.0', 0.1, '1.0.0')
        b101 = logictree.Branch('BS4', '1.0.1', 0.9, '1.0.1')
        bs_root = logictree.BranchSet(None)
        bs_root.branches = [b0, b1]
        bs0 = logictree.BranchSet(None)
        bs0.branches = [b00, b01, b02]
        bs1 = logictree.BranchSet(None)
        bs1.branches = [b10]
        b0.bset = bs0
        b1.bset = bs1
        bs10 = logictree.BranchSet(None)
        bs10.branches = [b100, b101]
        b10.bset = bs10

        def ae(got, expected):
            self.assertAlmostEqual(got[0], expected[0])  # weight
            self.assertEqual(got[1], expected[1])  # branches

        paths = bs_root.enumerate_paths()
        ae(next(paths), (0.2112, [b0, b00]))
        ae(next(paths), (0.1728, [b0, b01]))
        ae(next(paths), (0.256, [b0, b02]))
        ae(next(paths), (0.036, [b1, b10, b100]))
        ae(next(paths), (0.324, [b1, b10, b101]))
        self.assertRaises(StopIteration, lambda: next(paths))

        paths = bs1.enumerate_paths()
        ae(next(paths), (0.1, [b10, b100]))
        ae(next(paths), (0.9, [b10, b101]))
        self.assertRaises(StopIteration, lambda: next(paths))


class BranchSetGetBranchByIdTestCase(unittest.TestCase):
    def test(self):
        bs = logictree.BranchSet(None)
        b1 = logictree.Branch('BS', '1', 0.33, None)
        b2 = logictree.Branch('BS', '2', 0.33, None)
        bbzz = logictree.Branch('BS', 'bzz', 0.34, None)
        bs.branches = [b1, b2, bbzz]
        self.assertIs(bs['1'], b1)
        self.assertIs(bs['2'], b2)
        self.assertIs(bs['bzz'], bbzz)

    def test_nonexistent_branch(self):
        bs = logictree.BranchSet(None)
        br = logictree.Branch('BS', 'br', 1.0, None)
        bs.branches.append(br)
        self.assertRaises(KeyError, bs.__getitem__, 'bz')


class BranchSetApplyUncertaintyTestCase(unittest.TestCase):
    def setUp(self):
        self.point_source = openquake.hazardlib.source.PointSource(
            source_id='point', name='point',
            tectonic_region_type=
            openquake.hazardlib.const.TRT.ACTIVE_SHALLOW_CRUST,
            mfd=TruncatedGRMFD(a_val=3.1, b_val=0.9, min_mag=5.0,
                               max_mag=6.5, bin_width=0.1),
            nodal_plane_distribution=PMF(
                [(1, openquake.hazardlib.geo.NodalPlane(0.0, 90.0, 0.0))]
            ),
            hypocenter_distribution=PMF([(1, 10)]),
            upper_seismogenic_depth=0.0, lower_seismogenic_depth=10.0,
            magnitude_scaling_relationship=
            openquake.hazardlib.scalerel.PeerMSR(),
            rupture_aspect_ratio=1, location=openquake.hazardlib.geo.Point(
                5, 6),
            rupture_mesh_spacing=1.0,
            temporal_occurrence_model=PoissonTOM(50.)
        )

    def test_relative_uncertainty(self):
        uncertainties = [('maxMagGRRelative', +1),
                         ('bGRRelative', -0.2)]
        for utype, uvalue in uncertainties:
            lt.apply_uncertainty(utype, self.point_source, uvalue)
        self.assertEqual(self.point_source.mfd.max_mag, 6.5 + 1)
        self.assertEqual(self.point_source.mfd.b_val, 0.9 - 0.2)

    def test_absolute_uncertainty(self):
        uncertainties = [('maxMagGRAbsolute', 9),
                         ('abGRAbsolute', (-1, 0.2))]
        for utype, uvalue in uncertainties:
            lt.apply_uncertainty(utype, self.point_source, uvalue)
        self.assertEqual(self.point_source.mfd.max_mag, 9)
        self.assertEqual(self.point_source.mfd.b_val, 0.2)
        self.assertEqual(self.point_source.mfd.a_val, -1)

    def test_absolute_incremental_mfd_uncertainty(self):
        inc_point_source = openquake.hazardlib.source.PointSource(
            source_id='point', name='point',
            tectonic_region_type=
            openquake.hazardlib.const.TRT.ACTIVE_SHALLOW_CRUST,
            mfd=EvenlyDiscretizedMFD(min_mag=8.0, bin_width=0.2,
                                     occurrence_rates=[0.5, 0.1]),
            nodal_plane_distribution=PMF(
                [(1, openquake.hazardlib.geo.NodalPlane(0.0, 90.0, 0.0))]
            ),
            hypocenter_distribution=PMF([(1, 10)]),
            upper_seismogenic_depth=0.0, lower_seismogenic_depth=10.0,
            magnitude_scaling_relationship=
            openquake.hazardlib.scalerel.PeerMSR(),
            rupture_aspect_ratio=1, location=openquake.hazardlib.geo.Point(
                5, 6),
            rupture_mesh_spacing=1.0,
            temporal_occurrence_model=PoissonTOM(50.)
        )
        self.assertEqual(inc_point_source.mfd.min_mag, 8.0)
        self.assertEqual(inc_point_source.mfd.bin_width, 0.2)
        self.assertEqual(inc_point_source.mfd.occurrence_rates[0], 0.5)
        self.assertEqual(inc_point_source.mfd.occurrence_rates[1], 0.1)
        uncertainty, value = ('incrementalMFDAbsolute',
                              (8.5, 0.1, [0.05, 0.01]))
        branchset = logictree.BranchSet(uncertainty)
        lt.apply_uncertainty(
            branchset.uncertainty_type, inc_point_source, value)
        self.assertEqual(inc_point_source.mfd.min_mag, 8.5)
        self.assertEqual(inc_point_source.mfd.bin_width, 0.1)
        self.assertEqual(inc_point_source.mfd.occurrence_rates[0], 0.05)
        self.assertEqual(inc_point_source.mfd.occurrence_rates[1], 0.01)


class BranchSetApplyGeometryUncertaintyTestCase(unittest.TestCase):
    def setUp(self):
        self.trace = geo.Line([geo.Point(30., 30.), geo.Point(31., 30.)])
        self.fault_source = self._make_simple_fault_source(self.trace, 0.,
                                                           10., 60., 1.)

    def _make_simple_fault_source(self, trace, usd, lsd, dip, spacing):
        return openquake.hazardlib.source.SimpleFaultSource(
            source_id="SFLT0", name="Simple Fault",
            tectonic_region_type="Active Shallow Crust",
            mfd=EvenlyDiscretizedMFD(min_mag=7.0, bin_width=0.1,
                                     occurrence_rates=[0.01]),
            rupture_mesh_spacing=spacing,
            magnitude_scaling_relationship=
            openquake.hazardlib.scalerel.PeerMSR(),
            rupture_aspect_ratio=1.0,
            temporal_occurrence_model=PoissonTOM(50.),
            upper_seismogenic_depth=usd, lower_seismogenic_depth=lsd,
            fault_trace=trace, dip=dip, rake=90.0)

    def _make_complex_fault_source(self, edges, spacing):
        return openquake.hazardlib.source.ComplexFaultSource(
            source_id="CFLT0", name="Complex Fault",
            tectonic_region_type="Active Shallow Crust",
            mfd=EvenlyDiscretizedMFD(min_mag=7.0, bin_width=0.1,
                                     occurrence_rates=[0.01]),
            rupture_mesh_spacing=spacing,
            magnitude_scaling_relationship=
            openquake.hazardlib.scalerel.PeerMSR(),
            rupture_aspect_ratio=1.0,
            temporal_occurrence_model=PoissonTOM(50.),
            edges=edges, rake=90.0)

    def _make_planar_surface(self, planes):
        surfaces = []
        for plane in planes:
            top_left = geo.Point(plane[0, 0], plane[0, 1], plane[0, 2])
            top_right = geo.Point(plane[1, 0], plane[1, 1], plane[1, 2])
            bottom_right = geo.Point(plane[2, 0], plane[2, 1], plane[2, 2])
            bottom_left = geo.Point(plane[3, 0], plane[3, 1], plane[3, 2])
            surfaces.append(geo.PlanarSurface.from_corner_points(
                top_left, top_right, bottom_right, bottom_left))

        if len(surfaces) > 1:
            return geo.MultiSurface(surfaces)
        else:
            return surfaces[0]

    def _make_characteristic_fault_source(self, surface):
        return openquake.hazardlib.source.CharacteristicFaultSource(
            source_id="CHARFLT0", name="Characteristic Fault",
            tectonic_region_type="Active Shallow Crust",
            mfd=EvenlyDiscretizedMFD(min_mag=7.0, bin_width=0.1,
                                     occurrence_rates=[0.01]),
            temporal_occurrence_model=PoissonTOM(50.),
            surface=surface, rake=90)

    def test_simple_fault_dip_relative_uncertainty(self):
        self.assertAlmostEqual(self.fault_source.dip, 60.)
        new_fault_source = deepcopy(self.fault_source)
        utype, uvalue = ('simpleFaultDipRelative', -15.)
        lt.apply_uncertainty(utype, new_fault_source, uvalue)
        self.assertAlmostEqual(new_fault_source.dip, 45.)

    def test_simple_fault_dip_absolute_uncertainty(self):
        self.assertAlmostEqual(self.fault_source.dip, 60.)
        new_fault_source = deepcopy(self.fault_source)
        utype, uvalue = ('simpleFaultDipAbsolute', 55.)
        lt.apply_uncertainty(utype, new_fault_source, uvalue)
        self.assertAlmostEqual(new_fault_source.dip, 55.)

    def test_simple_fault_geometry_uncertainty(self):
        new_fault_source = deepcopy(self.fault_source)
        new_trace = geo.Line([geo.Point(30.5, 30.0), geo.Point(31.2, 30.)])
        new_dip = 50.
        new_lsd = 12.
        new_usd = 1.
        utype, uvalue = ('simpleFaultGeometryAbsolute',
                         (new_trace, new_usd, new_lsd, new_dip, 1.0))
        lt.apply_uncertainty(utype, new_fault_source, uvalue)
        self.assertEqual(new_fault_source.fault_trace, new_trace)
        self.assertAlmostEqual(new_fault_source.upper_seismogenic_depth, 1.)
        self.assertAlmostEqual(new_fault_source.lower_seismogenic_depth, 12.)
        self.assertAlmostEqual(new_fault_source.dip, 50.)

    def test_complex_fault_geometry_uncertainty(self):
        top_edge = geo.Line([geo.Point(30.0, 30.1, 0.0),
                             geo.Point(31.0, 30.1, 1.0)])
        bottom_edge = geo.Line([geo.Point(30.0, 30.0, 10.0),
                                geo.Point(31.0, 30.0, 9.0)])
        fault_source = self._make_complex_fault_source([top_edge, bottom_edge],
                                                       2.0)
        new_top_edge = geo.Line([geo.Point(30.0, 30.2, 0.0),
                                 geo.Point(31.0, 30.2, 0.0)])
        new_bottom_edge = geo.Line([geo.Point(30.0, 30.0, 10.0),
                                    geo.Point(31.0, 30.0, 10.0)])

        utype, uvalue = ('complexFaultGeometryAbsolute',
                         ([new_top_edge, new_bottom_edge], 2.0))
        lt.apply_uncertainty(utype, fault_source, uvalue)
        self.assertEqual(fault_source.edges[0], new_top_edge)
        self.assertEqual(fault_source.edges[1], new_bottom_edge)

    def test_characteristic_fault_planar_geometry_uncertainty(self):
        # Define 2-plane fault
        plane1 = numpy.array([[30.0, 30.0, 0.0],
                              [30.5, 30.0, 0.0],
                              [30.5, 30.0, 10.0],
                              [30.0, 30.0, 10.0]])
        plane2 = numpy.array([[30.5, 30.0, 0.0],
                              [30.5, 30.5, 0.0],
                              [30.5, 30.5, 10.0],
                              [30.5, 30.0, 10.0]])
        surface = self._make_planar_surface([plane1, plane2])
        fault_source = self._make_characteristic_fault_source(surface)
        # Move the planes
        plane3 = numpy.array([[30.1, 30.0, 0.0],
                              [30.6, 30.0, 0.0],
                              [30.6, 30.0, 10.0],
                              [30.1, 30.0, 10.0]])
        plane4 = numpy.array([[30.6, 30.0, 0.0],
                              [30.6, 30.5, 0.0],
                              [30.6, 30.5, 10.0],
                              [30.6, 30.0, 10.0]])
        new_surface = self._make_planar_surface([plane3, plane4])
        utype, uvalue = 'characteristicFaultGeometryAbsolute', new_surface
        lt.apply_uncertainty(utype, fault_source, uvalue)
        # Only the longitudes are changing
        numpy.testing.assert_array_almost_equal(
            fault_source.surface.surfaces[0].corner_lons,
            numpy.array([30.1, 30.6, 30.1, 30.6]))
        numpy.testing.assert_array_almost_equal(
            fault_source.surface.surfaces[1].corner_lons,
            numpy.array([30.6, 30.6, 30.6, 30.6]))

    def test_characteristic_fault_simple_geometry_uncertainty(self):
        trace = geo.Line([geo.Point(30., 30.), geo.Point(31., 30.)])
        usd = 0.0
        lsd = 10.0
        dip = 45.
        # Surface
        surface = geo.SimpleFaultSurface.from_fault_data(trace, usd, lsd, dip,
                                                         1.0)
        surface.dip = 45.0
        fault_source = self._make_characteristic_fault_source(surface)
        # Modify dip
        new_surface = geo.SimpleFaultSurface.from_fault_data(trace, usd, lsd,
                                                             65., 1.0)
        utype, uvalue = 'characteristicFaultGeometryAbsolute', new_surface
        new_surface.dip = 65.0
        lt.apply_uncertainty(utype, fault_source, uvalue)
        self.assertAlmostEqual(fault_source.surface.get_dip(), 65.)

    def test_characteristic_fault_complex_geometry_uncertainty(self):
        top_edge = geo.Line([geo.Point(30.0, 30.1, 0.0),
                             geo.Point(31.0, 30.1, 1.0)])
        bottom_edge = geo.Line([geo.Point(30.0, 30.0, 10.0),
                                geo.Point(31.0, 30.0, 9.0)])
        surface = geo.ComplexFaultSurface.from_fault_data(
            [top_edge, bottom_edge],
            5.)
        fault_source = self._make_characteristic_fault_source(surface)
        # New surface
        new_top_edge = geo.Line([geo.Point(30.0, 30.2, 0.0),
                                 geo.Point(31.0, 30.2, 0.0)])
        new_bottom_edge = geo.Line([geo.Point(30.0, 30.0, 10.0),
                                    geo.Point(31.0, 30.0, 10.0)])

        new_surface = geo.ComplexFaultSurface.from_fault_data(
            [new_top_edge, new_bottom_edge], 5.)
        utype, uvalue = 'characteristicFaultGeometryAbsolute', new_surface
        lt.apply_uncertainty(utype, fault_source, uvalue)
        # If the surface has changed the first element in the latitude
        # array of the surface mesh should be 30.2
        self.assertAlmostEqual(new_surface.mesh.lats[0, 0], 30.2)


class BranchSetFilterTestCase(unittest.TestCase):
    def setUp(self):
        self.point = openquake.hazardlib.source.PointSource(
            source_id='point', name='point',
            tectonic_region_type=
            openquake.hazardlib.const.TRT.ACTIVE_SHALLOW_CRUST,
            mfd=TruncatedGRMFD(a_val=3.1, b_val=0.9, min_mag=5.0,
                               max_mag=6.5, bin_width=0.1),
            nodal_plane_distribution=PMF(
                [(1, openquake.hazardlib.geo.NodalPlane(0.0, 90.0, 0.0))]
            ),
            hypocenter_distribution=PMF([(1, 10)]),
            upper_seismogenic_depth=0.0, lower_seismogenic_depth=10.0,
            magnitude_scaling_relationship=
            openquake.hazardlib.scalerel.PeerMSR(),
            rupture_aspect_ratio=1, location=openquake.hazardlib.geo.Point(
                5, 6),
            rupture_mesh_spacing=1.0,
            temporal_occurrence_model=PoissonTOM(50.),
        )
        self.area = openquake.hazardlib.source.AreaSource(
            source_id='area', name='area',
            tectonic_region_type=
            openquake.hazardlib.const.TRT.ACTIVE_SHALLOW_CRUST,
            mfd=TruncatedGRMFD(a_val=3.1, b_val=0.9, min_mag=5.0,
                               max_mag=6.5, bin_width=0.1),
            nodal_plane_distribution=PMF(
                [(1, openquake.hazardlib.geo.NodalPlane(0.0, 90.0, 0.0))]
            ),
            hypocenter_distribution=PMF([(1, 10)]),
            upper_seismogenic_depth=0.0, lower_seismogenic_depth=10.0,
            magnitude_scaling_relationship=
            openquake.hazardlib.scalerel.PeerMSR(),
            rupture_aspect_ratio=1,
            polygon=openquake.hazardlib.geo.Polygon(
                [openquake.hazardlib.geo.Point(0, 0),
                 openquake.hazardlib.geo.Point(0, 1),
                 openquake.hazardlib.geo.Point(1, 0)]),
            area_discretization=10, rupture_mesh_spacing=1.0,
            temporal_occurrence_model=PoissonTOM(50.),
        )
        self.simple_fault = openquake.hazardlib.source.SimpleFaultSource(
            source_id='simple_fault', name='simple fault',
            tectonic_region_type=openquake.hazardlib.const.TRT.VOLCANIC,
            mfd=TruncatedGRMFD(a_val=3.1, b_val=0.9, min_mag=5.0,
                               max_mag=6.5, bin_width=0.1),
            upper_seismogenic_depth=0.0, lower_seismogenic_depth=10.0,
            magnitude_scaling_relationship=
            openquake.hazardlib.scalerel.PeerMSR(),
            rupture_aspect_ratio=1, rupture_mesh_spacing=2.0,
            fault_trace=openquake.hazardlib.geo.Line(
                [openquake.hazardlib.geo.Point(0, 0),
                 openquake.hazardlib.geo.Point(1, 1)]),
            dip=45, rake=180,
            temporal_occurrence_model=PoissonTOM(50.)
        )
        self.complex_fault = openquake.hazardlib.source.ComplexFaultSource(
            source_id='complex_fault', name='complex fault',
            tectonic_region_type=openquake.hazardlib.const.TRT.VOLCANIC,
            mfd=TruncatedGRMFD(a_val=3.1, b_val=0.9, min_mag=5.0,
                               max_mag=6.5, bin_width=0.1),
            magnitude_scaling_relationship=
            openquake.hazardlib.scalerel.PeerMSR(),
            rupture_aspect_ratio=1, rupture_mesh_spacing=2.0, rake=0,
            edges=[openquake.hazardlib.geo.Line(
                [openquake.hazardlib.geo.Point(0, 0, 1),
                 openquake.hazardlib.geo.Point(1, 1, 1)]),
                openquake.hazardlib.geo.Line(
                    [openquake.hazardlib.geo.Point(0, 0, 2),
                     openquake.hazardlib.geo.Point(1, 1, 2)])],
            temporal_occurrence_model=PoissonTOM(50.),
        )

        lons = numpy.array([-1., 1., -1., 1.])
        lats = numpy.array([0., 0., 0., 0.])
        depths = numpy.array([0., 0., 10., 10.])

        points = [openquake.hazardlib.geo.Point(lon, lat, depth)
                  for lon, lat, depth in
                  zip(lons, lats, depths)]
        self.characteristic_fault = \
            openquake.hazardlib.source.CharacteristicFaultSource(
                source_id='characteristic_fault',
                name='characteristic fault',
                tectonic_region_type=openquake.hazardlib.const.TRT.VOLCANIC,
                mfd=TruncatedGRMFD(a_val=3.1, b_val=0.9, min_mag=5.0,
                                   max_mag=6.5, bin_width=0.1),
                surface=openquake.hazardlib.geo.PlanarSurface(
                    strike=0.0, dip=90.0,
                    top_left=points[0], top_right=points[1],
                    bottom_right=points[3], bottom_left=points[2]
                ),
                rake=0,
                temporal_occurrence_model=PoissonTOM(50.))

    def test_unknown_filter(self):
        bs = logictree.BranchSet(
            None, filters={'applyToSources': [1], 'foo': 'bar'})
        self.assertRaises(AssertionError, bs.filter_source, None)

    def test_tectonic_region_type(self):
        test = lambda trt, source: \
            logictree.BranchSet(
                None, filters={'applyToTectonicRegionType': trt}
            ).filter_source(source)

        asc = 'Active Shallow Crust'
        vlc = 'Volcanic'
        ssc = 'Stable Shallow Crust'
        sif = 'Subduction Interface'
        sic = 'Subduction IntraSlab'

        source = self.simple_fault

        source.tectonic_region_type = sic
        for wrong_trt in (asc, vlc, ssc, sif):
            self.assertEqual(test(wrong_trt, source), False)
        self.assertEqual(test(sic, source), True)

        source.tectonic_region_type = vlc
        for wrong_trt in (asc, sic, ssc, sif):
            self.assertEqual(test(wrong_trt, source), False)
        self.assertEqual(test(vlc, source), True)

        source.tectonic_region_type = sif
        for wrong_trt in (asc, vlc, ssc, sic):
            self.assertEqual(test(wrong_trt, source), False)
        self.assertEqual(test(sif, source), True)

        source.tectonic_region_type = ssc
        for wrong_trt in (asc, vlc, sic, sif):
            self.assertEqual(test(wrong_trt, source), False)
        self.assertEqual(test(ssc, source), True)

        source.tectonic_region_type = asc
        for wrong_trt in (sic, vlc, ssc, sif):
            self.assertEqual(test(wrong_trt, source), False)
        self.assertEqual(test(asc, source), True)

    def test_sources(self):
        def test(sources, source, expected_result):
            return self.assertEqual(
                logictree.BranchSet(
                    None,
                    filters={'applyToSources': [s.source_id for s in sources]}
                ).filter_source(source),
                expected_result)

        test([self.simple_fault, self.area], self.point, False)
        test([self.simple_fault, self.area], self.area, True)
        test([self.complex_fault, self.simple_fault], self.area, False)
        test([self.area], self.area, True)
        test([self.point, self.simple_fault], self.simple_fault, True)
        test([self.point, self.complex_fault], self.simple_fault, False)


class GsimLogicTreeTestCase(unittest.TestCase):
    def parse_invalid(self, xml, errorclass, errormessage=None):
        if hasattr(xml, 'encode'):
            xml = xml.encode('utf8')
        with self.assertRaises(errorclass) as exc:
            logictree.GsimLogicTree(gettemp(xml), ['Shield'])
        if errormessage is not None:
            self.assertIn(errormessage, str(exc.exception))

    def parse_valid(self, xml, tectonic_region_types=('Shield',)):
        xml = xml.decode('utf-8') if hasattr(xml, 'decode') else xml
        return logictree.GsimLogicTree(gettemp(xml), tectonic_region_types)

    def test_not_xml(self):
        self.parse_invalid('xxx', ExpatError)
        self.parse_invalid('<?xml foo bar baz', ExpatError)

    def test_invalid_schema(self):
        xml = _make_nrml("""\
            <logicTreeSet>
                <logicTree logicTreeID="lt1"/>
            </logicTreeSet>
        """)
        self.parse_invalid(xml, AttributeError,
                           "No subnode named 'logicTree' found in 'nrml'")

    def test_not_a_gsim_logic_tree(self):
        xml = _make_nrml("""\
            <logicTree logicTreeID="lt1">
              <logicTreeBranchingLevel branchingLevelID="bl1">
                <logicTreeBranchSet uncertaintyType="gmpeModel"
                                    branchSetID="bs1">
                  <logicTreeBranch branchID="b1">
                    <uncertaintyModel>+100</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
            </logicTree>
        """)
        self.parse_invalid(
            xml, ValueError, "Invalid group name '+100'. Try quoting it.")

    def test_gmpe_uncertainty(self):
        xml = _make_nrml("""\
        <logicTree logicTreeID="lt1">
            <logicTreeBranchingLevel branchingLevelID="bl1">
                <logicTreeBranchSet uncertaintyType="bGRRelative"
                                    branchSetID="bs1"
                                    applyToTectonicRegionType="Shield">
                    <logicTreeBranch branchID="b1">
                        <uncertaintyModel>+1</uncertaintyModel>
                        <uncertaintyWeight>1.0</uncertaintyWeight>
                    </logicTreeBranch>
                </logicTreeBranchSet>
            </logicTreeBranchingLevel>
        </logicTree>""")
        self.parse_invalid(
            xml, gsim_lt.InvalidLogicTree,
            'only uncertainties of type "gmpeModel" are allowed '
            'in gmpe logic tree')

    def test_two_branchsets_in_one_level(self):
        xml = _make_nrml("""\
        <logicTree logicTreeID="lt1">
            <logicTreeBranchingLevel branchingLevelID="bl1">
                <logicTreeBranchSet uncertaintyType="gmpeModel"
                                    branchSetID="bs1"
                                    applyToTectonicRegionType="Volcanic">
                    <logicTreeBranch branchID="b1">
                        <uncertaintyModel>
                            SadighEtAl1997
                        </uncertaintyModel>
                        <uncertaintyWeight>1.0</uncertaintyWeight>
                    </logicTreeBranch>
                </logicTreeBranchSet>
                <logicTreeBranchSet uncertaintyType="gmpeModel"
                            branchSetID="bs2"
                            applyToTectonicRegionType="Subduction IntraSlab">
                    <logicTreeBranch branchID="b2">
                        <uncertaintyModel>
                            SadighEtAl1997
                        </uncertaintyModel>
                        <uncertaintyWeight>1.0</uncertaintyWeight>
                    </logicTreeBranch>
                </logicTreeBranchSet>
            </logicTreeBranchingLevel>
        </logicTree>
        """)
        self.parse_invalid(
            xml, gsim_lt.InvalidLogicTree,
            'Branching level bl1 has multiple branchsets')

    def test_branchset_id_not_unique(self):
        xml = _make_nrml("""\
            <logicTree logicTreeID="lt1">
              <logicTreeBranchingLevel branchingLevelID="bl1">
                <logicTreeBranchSet uncertaintyType="gmpeModel"
                                    branchSetID="bs1"
                  applyToTectonicRegionType="Shield">
                  <logicTreeBranch branchID="b1">
                    <uncertaintyModel>ChiouYoungs2008</uncertaintyModel>
                    <uncertaintyWeight>0.7</uncertaintyWeight>
                  </logicTreeBranch>
                  <logicTreeBranch branchID="b2">
                    <uncertaintyModel>SadighEtAl1997</uncertaintyModel>
                    <uncertaintyWeight>0.3</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
              <logicTreeBranchingLevel branchingLevelID="bl2">
                <logicTreeBranchSet uncertaintyType="gmpeModel"
                                    branchSetID="bs1"
                  applyToTectonicRegionType="Subduction Interface">
                  <logicTreeBranch branchID="b3">
                    <uncertaintyModel>ChiouYoungs2008</uncertaintyModel>
                    <uncertaintyWeight>0.6</uncertaintyWeight>
                  </logicTreeBranch>
                  <logicTreeBranch branchID="b4">
                    <uncertaintyModel>SadighEtAl1997</uncertaintyModel>
                    <uncertaintyWeight>0.4</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
            </logicTree>
        """)
        self.parse_invalid(
            xml, gsim_lt.InvalidLogicTree,
            "Duplicated branchSetID bs1")

    def test_invalid_gsim(self):
        xml = _make_nrml("""\
        <logicTree logicTreeID="lt1">
            <logicTreeBranchingLevel branchingLevelID="bl1">
                <logicTreeBranchSet uncertaintyType="gmpeModel"
                            branchSetID="bs1"
                            applyToTectonicRegionType="Shield">
                    <logicTreeBranch branchID="b1">
                        <uncertaintyModel>
                            SAdighEtAl1997
                        </uncertaintyModel>
                        <uncertaintyWeight>1.0</uncertaintyWeight>
                    </logicTreeBranch>
                </logicTreeBranchSet>
            </logicTreeBranchingLevel>
        </logicTree>
        """)
        self.parse_invalid(
            xml, ValueError, "Unknown GSIM: SAdighEtAl1997")

    def test_tectonic_region_type_used_twice(self):
        xml = _make_nrml("""\
        <logicTree logicTreeID="lt1">
            <logicTreeBranchingLevel branchingLevelID="bl1">
                <logicTreeBranchSet uncertaintyType="gmpeModel"
                            branchSetID="bs1"
                            applyToTectonicRegionType="Subduction Interface">
                    <logicTreeBranch branchID="b1">
                        <uncertaintyModel>
                            SadighEtAl1997
                        </uncertaintyModel>
                        <uncertaintyWeight>1.0</uncertaintyWeight>
                    </logicTreeBranch>
                </logicTreeBranchSet>
            </logicTreeBranchingLevel>
            <logicTreeBranchingLevel branchingLevelID="bl2">
                <logicTreeBranchSet uncertaintyType="gmpeModel"
                            branchSetID="bs2"
                            applyToTectonicRegionType="Subduction Interface">
                    <logicTreeBranch branchID="b2">
                        <uncertaintyModel>
                            ChiouYoungs2008
                        </uncertaintyModel>
                        <uncertaintyWeight>1.0</uncertaintyWeight>
                    </logicTreeBranch>
                </logicTreeBranchSet>
            </logicTreeBranchingLevel>
        </logicTree>
        """)
        self.parse_invalid(
            xml, gsim_lt.InvalidLogicTree,
            "Found duplicated applyToTectonicRegionType="
            "['Subduction Interface', 'Subduction Interface']")

    def test_SHARE(self):
        # this is actually a reduced version of the full SHARE logic tree
        xml = codecs.open(
            os.path.join(DATADIR, 'gmpe_logic_tree_share_reduced.xml'),
            encoding='utf8').read().encode('utf8')
        as_model_trts = ['Active Shallow Crust', 'Stable Shallow Crust',
                         'Shield', 'Volcanic']
        fs_bg_model_trts = ['Active Shallow Crust', 'Stable Shallow Crust']
        as_model_lt = self.parse_valid(xml, as_model_trts)
        fs_bg_model_lt = self.parse_valid(xml, fs_bg_model_trts)
        self.assertEqual(as_model_lt.get_num_branches(),
                         {'Active Shallow Crust': 4,
                          'Shield': 2,
                          'Stable Shallow Crust': 5,
                          'Volcanic': 1})
        self.assertEqual(fs_bg_model_lt.get_num_branches(),
                         {'Active Shallow Crust': 4,
                          'Stable Shallow Crust': 5})
        self.assertEqual(as_model_lt.get_num_paths(), 40)
        self.assertEqual(fs_bg_model_lt.get_num_paths(), 20)
        self.assertEqual(len(list(as_model_lt)), 5 * 4 * 2 * 1)
        effective_rlzs = set(rlz.pid for rlz in fs_bg_model_lt)
        self.assertEqual(len(effective_rlzs), 5 * 4)

    def test_sampling(self):
        xml = _make_nrml("""\
        <logicTree logicTreeID="lt1">
            <logicTreeBranchingLevel branchingLevelID="bl1">
                <logicTreeBranchSet uncertaintyType="gmpeModel"
                                    branchSetID="bs1"
                                    applyToTectonicRegionType="Volcanic">
                    <logicTreeBranch branchID="b1">
                        <uncertaintyModel>
                            SadighEtAl1997
                        </uncertaintyModel>
                        <uncertaintyWeight>0.4</uncertaintyWeight>
                    </logicTreeBranch>
                    <logicTreeBranch branchID="b2">
                        <uncertaintyModel>
                            ToroEtAl2002
                        </uncertaintyModel>
                        <uncertaintyWeight>0.6</uncertaintyWeight>
                    </logicTreeBranch>
                </logicTreeBranchSet>
            </logicTreeBranchingLevel>
        </logicTree>
        """)
        # test a large number of samples with the algorithm used in the engine
        counter = collections.Counter()
        gsim_rlzs = list(self.parse_valid(xml, ['Volcanic']))
        probs = lt.random(1000, 42, 'early_weights')
        rlzs = lt.sample(gsim_rlzs, probs, 'early_weights')
        for rlz in rlzs:
            counter[rlz.lt_path] += 1
        # the percentages will be close to 40% and 60%
        self.assertEqual(counter, {('gA0',): 421, ('gB0',): 579})


class LogicTreeProcessorTestCase(unittest.TestCase):
    def setUp(self):
        # this is an example with number_of_logic_tree_samples = 1
        oqparam = tests.get_oqparam('classical_job.ini')
        self.source_model_lt = readinput.get_source_model_lt(oqparam)
        self.gmpe_lt = readinput.get_gsim_lt(
            oqparam, ['Active Shallow Crust', 'Subduction Interface'])
        self.seed = oqparam.random_seed

    def test_sample_source_model(self):
        [rlz] = self.source_model_lt
        self.assertEqual(rlz.value, ['example-source-model.xml', -0.2, 0.0])
        self.assertEqual(('b1', 'b5', 'b7'), rlz.lt_path)

    def test_sample_gmpe(self):
        probs = lt.random(1, self.seed, 'early_weights')
        [rlz] = lt.sample(list(self.gmpe_lt), probs, 'early_weights')
        self.assertEqual(rlz.value, ('[ChiouYoungs2008]', '[SadighEtAl1997]'))
        self.assertEqual(rlz.weight['default'], 0.5)
        self.assertEqual(('gB0', 'gA1'), rlz.lt_path)


class LogicTreeProcessorParsePathTestCase(unittest.TestCase):
    def setUp(self):
        oqparam = tests.get_oqparam('classical_job.ini')
        self.source_model_lt = readinput.get_source_model_lt(oqparam)
        self.gmpe_lt = readinput.get_gsim_lt(
            oqparam, ['Active Shallow Crust', 'Subduction Interface'])

    def test_parse_invalid_smlt(self):
        smlt = os.path.join(DATADIR, 'source_model_logic_tree.xml')
        with self.assertRaises(Exception) as ctx:
            logictree.collect_info(smlt)
        exc = ctx.exception
        self.assertIn('not well-formed (invalid token)', str(exc))
        self.assertEqual(exc.lineno, 5)
        self.assertEqual(exc.offset, 61)
        self.assertEqual(exc.filename, smlt)


class LogicTreeSourceSpecificUncertaintyTest(unittest.TestCase):
    """
    Test the applications of a source-specific uncertainty
    """
    value = {'b1_b21': 1, 'b1_b22': 1, 'b1_b23': 1,
             'b1_b24': 1, 'b1_b25': 1, 'b1_b26': 1,
             'b2_.': 1.2, 'b3_.': 1.3}

    def mean(self, rlzs):
        R = len(rlzs)
        paths = ['_'.join(rlz.sm_lt_path) for rlz in rlzs]
        return sum(self.value[path] * rlz.weight['weight']
                   for rlz, path in zip(rlzs, paths)) / R

    def test_full_path(self):
        path = os.path.join(DATADIR, 'source_specific_uncertainty')
        fname_ini = os.path.join(path, 'job.ini')

        oqparam = readinput.get_oqparam(fname_ini)
        full_lt = readinput.get_full_lt(oqparam)

        mags = [5.7, 5.98, 6.26, 6.54, 6.82, 7.1]
        csm = get_csm(oqparam, full_lt)
        for src in csm.src_groups[0][0]:
            if src.source_id == 'a2':
                self.assertEqual(src.mfd.max_mag, 6.5)
            elif src.source_id == 'a1':
                msg = "Wrong mmax value assigned to source 'a1'"
                self.assertIn(src.mfd.max_mag, mags, msg)

        rlzs = full_lt.get_realizations()  # 6+2 = 8 realizations
        paths = ['b1_b21', 'b1_b22', 'b1_b23', 'b1_b24', 'b1_b25', 'b1_b26',
                 'b2_.', 'b3_.']
        self.assertEqual(['_'.join(rlz.sm_lt_path) for rlz in rlzs], paths)
        weights = [0.064988,  # b1_b21
                   0.14077,   # b1_b22
                   0.185878,  # b1_b23
                   0.163723,  # b1_b24
                   0.100569,  # b1_b25
                   0.044072,  # b1_b26
                   0.2,       # b2_.
                   0.1]       # b3_.
        # b1_b21 has weight 0.7 * 0.09284 = 0.064988
        numpy.testing.assert_almost_equal(
            weights, [rlz.weight['weight'] for rlz in rlzs])

        numpy.testing.assert_almost_equal(self.mean(rlzs), 0.13375)

    def test_sampling_early_weights(self):
        fname_ini = os.path.join(
            os.path.join(DATADIR, 'source_specific_uncertainty'), 'job.ini')
        oqparam = readinput.get_oqparam(fname_ini)
        oqparam.number_of_logic_tree_samples = 10
        oqparam.sampling_method = 'early_weights'
        full_lt = readinput.get_full_lt(oqparam)
        rlzs = full_lt.get_realizations()  # 10 realizations
        paths = ['b1_b22', 'b1_b23', 'b1_b23', 'b1_b24', 'b1_b25', 'b1_b26',
                 'b1_b26', 'b2_.', 'b2_.', 'b2_.']
        self.assertEqual(['_'.join(rlz.sm_lt_path) for rlz in rlzs], paths)

        # the weights are all equal
        weights = [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]
        numpy.testing.assert_almost_equal(
            weights, [rlz.weight['weight'] for rlz in rlzs])
        numpy.testing.assert_almost_equal(self.mean(rlzs), 0.106)

    def test_sampling_late_weights(self):
        fname_ini = os.path.join(
            os.path.join(DATADIR, 'source_specific_uncertainty'), 'job.ini')
        oqparam = readinput.get_oqparam(fname_ini)
        oqparam.number_of_logic_tree_samples = 10
        oqparam.sampling_method = 'late_weights'
        full_lt = readinput.get_full_lt(oqparam)
        rlzs = full_lt.get_realizations()  # 10 realizations
        paths = ['b1_b22', 'b1_b23', 'b1_b25', 'b1_b26',
                 'b2_.', 'b2_.', 'b2_.', 'b3_.', 'b3_.', 'b3_.']
        self.assertEqual(['_'.join(rlz.sm_lt_path) for rlz in rlzs], paths)
        weights = [0.04438889044, 0.05861275966, 0.031712341,
                   0.01389718817, 0.18919751558, 0.189197515,
                   0.18919751558, 0.09459875780, 0.094598757,
                   0.09459875779]
        numpy.testing.assert_almost_equal(
            weights, [rlz.weight['weight'] for rlz in rlzs])
        numpy.testing.assert_almost_equal(self.mean(rlzs), 0.119865739)

    def test_smlt_bad(self):
        # apply to a source that does not exist in the given branch
        path = os.path.join(DATADIR, 'source_specific_uncertainty')
        job_ini = os.path.join(path, 'job.ini')
        oqparam = readinput.get_oqparam(job_ini)
        oqparam.inputs['source_model_logic_tree'] = os.path.join(
            oqparam.base_path, 'smlt_bad.xml')
        with self.assertRaises(ValueError) as ctx:
            readinput.get_composite_source_model(oqparam)
        self.assertIn('The source c1 is not in the source model, please fix '
                      'applyToSources', str(ctx.exception))


class SerializeSmltTestCase(unittest.TestCase):
    def test(self):
        sm = '''\
<?xml version='1.0' encoding='utf-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml"
      xmlns="http://openquake.org/xmlns/nrml/0.4">
    <sourceModel name="">
        <areaSource id="1" name="A" tectonicRegion="Active Shallow Crust">
            <areaGeometry>
                <gml:Polygon>
                    <gml:exterior>
                        <gml:LinearRing>
                            <gml:posList>
                             -0.5 -0.5 -0.5  0.0 0.0  0.0 0.0 -0.5
                            </gml:posList>
                        </gml:LinearRing>
                    </gml:exterior>
                </gml:Polygon>
                <upperSeismoDepth>0.0</upperSeismoDepth>
                <lowerSeismoDepth>10.0</lowerSeismoDepth>
            </areaGeometry>
            <magScaleRel>WC1994</magScaleRel>
            <ruptAspectRatio>1.0</ruptAspectRatio>
            <truncGutenbergRichterMFD aValue="2.0" bValue="1.0"
                                      minMag="5.0" maxMag="6.5" />
            <nodalPlaneDist>
                <nodalPlane probability="1.0"
                            strike="0.0" dip="90.0" rake="0.0" />
            </nodalPlaneDist>
            <hypoDepthDist>
                <hypoDepth probability="1." depth="5.0" />
            </hypoDepthDist>
        </areaSource>
    </sourceModel>
</nrml>'''

        lt = '''\
<?xml version="1.0" encoding="UTF-8"?>
<nrml xmlns:gml="http://www.opengis.net/gml"
      xmlns="http://openquake.org/xmlns/nrml/0.4">
    <logicTree logicTreeID="lt1">
            <logicTreeBranchSet uncertaintyType="sourceModel"
                                branchSetID="bs1">
                <logicTreeBranch branchID="b11">
                    <uncertaintyModel>source_model.xml</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                </logicTreeBranch>
            </logicTreeBranchSet>

            <logicTreeBranchSet uncertaintyType="abGRAbsolute"
                                applyToSources="1" branchSetID="bs21">
                <logicTreeBranch branchID="b21">
                    <uncertaintyModel>2.2 1.2</uncertaintyModel>
                    <uncertaintyWeight>0.1</uncertaintyWeight>
                </logicTreeBranch>
                <logicTreeBranch branchID="b22">
                    <uncertaintyModel>2.1 1.1</uncertaintyModel>
                    <uncertaintyWeight>0.9</uncertaintyWeight>
                </logicTreeBranch>
            </logicTreeBranchSet>

            <logicTreeBranchSet uncertaintyType="maxMagGRAbsolute"
                                applyToSources="1" branchSetID="bs31">
                <logicTreeBranch branchID="b31">
                    <uncertaintyModel>6.3</uncertaintyModel>
                    <uncertaintyWeight>0.4</uncertaintyWeight>
                </logicTreeBranch>
                <logicTreeBranch branchID="b32">
                    <uncertaintyModel>6.5</uncertaintyModel>
                    <uncertaintyWeight>0.6</uncertaintyWeight>
                </logicTreeBranch>
            </logicTreeBranchSet>
    </logicTree>
</nrml>
'''
        smlta = _TestableSourceModelLogicTree(
            'lt', {'lt': lt, 'source_model.xml': sm})
        with hdf5.File.temporary() as h5:
            h5['smlt'] = smlta
        with hdf5.File(h5.path) as h5:  # deserialize
            smltb = h5['smlt']
        # check the deserialized SMLT is equal to the original one
        for brid in ['b11', 'b21', 'b31']:
            ba = smlta.branches[brid]
            bb = smltb.branches[brid]
            self.assertEqual(repr(ba), repr(bb))


class ReduceLtTestCase(unittest.TestCase):
    def test(self):
        raise unittest.SkipTest('Not used')
        ssmLT = os.path.join(DATADIR, 'ssmLT.xml')
        gmmLT = os.path.join(DATADIR, 'gmmLT.xml')
        smlt = logictree.SourceModelLogicTree(ssmLT, test_mode=True)
        gslt = logictree.GsimLogicTree(gmmLT)
        paths = '''\
[ABCDEF]~[AB][DEF][GHI][JKL][M][PQR][ST]
[ABCDEF]~[C][DEF][GHI][JKL][O][PQR][U]
[ABCDEF]~[B][DEF][GHI][JKL][O][PQR][ST]
[ABCDEF]~[AB][DEF][GHI][JKL][N][PQR][ST]
[ABCDEF]~[C][DEF][GHI][JKL][M][PQR][U]
[ABCDEF]~[C][DEF][GHI][JKL][M][PQR][ST]
[ABCDEF]~[AB][DEF][GHI][JKL][O][PQR][U]
[ABCDEF]~[ABC][DEF][GHI][JKL][N][PQR][U]
[ABCDEF]~[AB][DEF][GHI][JKL][M][PQR][U]
[ABCDEF]~[A][DEF][GHI][JKL][O][PQR][ST]
[ABCDEF]~[C][DEF][GHI][JKL][O][PQR][ST]
[ABCDEF]~[C][DEF][GHI][JKL][N][PQR][ST]'''.split()
        full_lt = unittest.mock.Mock(source_model_lt=smlt, gsim_lt=gslt)
        dic = logictree.reduce_full(full_lt, paths)
        pprint.pprint(dic)


class TaxonomyMappingTestCase(unittest.TestCase):
    taxonomies = '? taxo1 taxo2 taxo3 taxo4'.split()

    def test_missing_taxo(self):
        xml = '''taxonomy,conversion,weight
taxo1,taxo1,1
taxo2,taxo2,1
taxo3,taxo3,1
'''
        with self.assertRaises(openquake.hazardlib.InvalidFile) as ctx:
            inp = dict(taxonomy_mapping=gettemp(xml))
            oq = unittest.mock.Mock(inputs=inp, loss_types=['structural'])
            readinput.taxonomy_mapping(oq, self.taxonomies)
        self.assertIn("{'taxo4'} are in the exposure but not in",
                      str(ctx.exception))

    def test_wrong_weight(self):
        xml = '''taxonomy,conversion,weight
taxo1,taxo1,1
taxo2,taxo2,1
taxo3,taxo3,1
taxo4,taxo1,.5
taxo4,taxo2,.4
'''
        with self.assertRaises(openquake.hazardlib.InvalidFile) as ctx:
            inp = dict(taxonomy_mapping=gettemp(xml))
            oq = unittest.mock.Mock(inputs=inp, loss_types=['structural'])
            readinput.taxonomy_mapping(oq, self.taxonomies)
        self.assertIn("the weights do not sum up to 1 for taxo4",
                      str(ctx.exception))

    def test_mixed_lines(self):
        xml = '''taxonomy,conversion,weight
taxo1,taxo1,1
taxo2,taxo2,1
taxo4,taxo2,.5
taxo3,taxo3,1
taxo4,taxo1,.5
'''
        inp = dict(taxonomy_mapping=gettemp(xml))
        oq = unittest.mock.Mock(inputs=inp, loss_types=['structural'])
        lst = readinput.taxonomy_mapping(oq, self.taxonomies)['structural']
        self.assertEqual(lst, [[('?', 1)],
                               [('taxo1', 1)],
                               [('taxo2', 1)],
                               [('taxo3', 1)],
                               [('taxo2', 0.5), ('taxo1', 0.5)]])


def teardown_module():
    parallel.Starmap.shutdown()
