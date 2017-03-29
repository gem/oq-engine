# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2010-2017 GEM Foundation
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

"""
Tests for python logic tree processor.
"""

import os
import codecs
import random
import unittest
import collections

import numpy
from xml.parsers.expat import ExpatError
from xml.etree import ElementTree as ET
from copy import deepcopy

from io import BytesIO
from decimal import Decimal
from mock import Mock

import openquake.hazardlib
from openquake.hazardlib import geo
from openquake.baselib.general import writetmp
from openquake.hazardlib import valid
from openquake.commonlib import logictree, readinput, tests, source
from openquake.hazardlib.tom import PoissonTOM
from openquake.hazardlib.pmf import PMF
from openquake.hazardlib.mfd import TruncatedGRMFD, EvenlyDiscretizedMFD

DATADIR = os.path.join(os.path.dirname(__file__), 'data')


class StringIO(BytesIO):
    def __repr__(self):
        return '<StringIO>'


class _TestableSourceModelLogicTree(logictree.SourceModelLogicTree):
    def __init__(self, filename, files, basepath, validate=True):
        self.files = files
        if not validate:
            self.validate_branchset = self.__fail
            self.validate_tree = self.__fail
            self.validate_filters = self.__fail
            self.validate_uncertainty_value = self.__fail
        f = writetmp(files[filename], suffix='.' + filename)
        super(_TestableSourceModelLogicTree, self).__init__(f, validate)

    def _get_source_model(self, filename):
        return StringIO(self.files[filename].encode('utf-8'))

    def __fail(self, *args, **kwargs):
        raise AssertionError("this method shouldn't be called")


def _make_nrml(content):
    return ("""<?xml version="1.0" encoding="UTF-8"?>
    <nrml xmlns:gml="http://www.opengis.net/gml"\
          xmlns="http://openquake.org/xmlns/nrml/0.5">\
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
    def _assert_logic_tree_error(self, filename, files, basepath,
                                 exc_class=logictree.LogicTreeError,
                                 exc_filename=None):
        with self.assertRaises(exc_class) as arc:
            _TestableSourceModelLogicTree(filename, files, basepath)
        exc = arc.exception
        if '.' in exc.filename:
            suffix = exc.filename.rsplit('.')[1]
            self.assertEqual(suffix, exc_filename or filename)
        return exc

    def test_logictree_invalid_xml(self):
        self._assert_logic_tree_error(
            'broken_xml', {'broken_xml': "<?xml foo bar baz"}, 'basepath',
            ExpatError)

    def test_logictree_schema_violation(self):
        source = _make_nrml("""\
            <logicTreeSet>
                <logicTree logicTreeID="lt1"/>
            </logicTreeSet>
        """)
        exc = self._assert_logic_tree_error(
            'screwed_schema', {'screwed_schema': source}, 'base',
            logictree.ValidationError)
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
            'logictree', {'logictree': source}, 'base',
            logictree.ValidationError
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
                                    branchSetID="bs1">
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
            'lt', {'lt': lt, 'sm1': sm, 'sm2': sm}, 'base',
            logictree.ValidationError
        )
        self.assertEqual(exc.lineno, 13)
        error = 'uncertainty of type "sourceModel" can be defined ' \
                'on first branchset only'
        self.assertEqual(exc.message, error,
                         "wrong exception message: %s" % exc.message)

    def test_two_branchsets_on_first_level(self):
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
                <logicTreeBranchSet uncertaintyType="sourceModel"
                                    branchSetID="bs1">
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
            'lt', {'lt': lt, 'sm1': sm, 'sm2': sm}, 'base',
            logictree.ValidationError
        )
        self.assertEqual(exc.lineno, 11)
        error = 'there must be only one branch set on first branching level'
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
            'lt', {'lt': lt, 'sm1': sm, 'sm2': sm}, '/bz',
            logictree.ValidationError
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
            'lo', {'lo': lt, 'sm1': sm, 'sm2': sm}, 'base',
            logictree.ValidationError
        )
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
                    <uncertaintyModel>sm</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
              <logicTreeBranchingLevel branchingLevelID="bl2">
                <logicTreeBranchSet uncertaintyType="bGRRelative"
                                    branchSetID="bs1"
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
        exc = self._assert_logic_tree_error('lt', {'lt': lt, 'sm': sm}, 'base',
                                            logictree.ValidationError)
        self.assertEqual(exc.lineno, 13)
        self.assertEqual(exc.message, "branch 'mssng' is not yet defined",
                         "wrong exception message: %s" % exc.message)

    def test_apply_to_occupied_branch(self):
        lt = _make_nrml("""\
            <logicTree logicTreeID="lt1">
              <logicTreeBranchingLevel branchingLevelID="bl1">
                <logicTreeBranchSet uncertaintyType="sourceModel"
                                    branchSetID="bs1">
                  <logicTreeBranch branchID="b1">
                    <uncertaintyModel>sm</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
              <logicTreeBranchingLevel branchingLevelID="bl2">
                <logicTreeBranchSet uncertaintyType="bGRRelative"
                                    branchSetID="bs1"
                                    applyToBranches="b1">
                  <logicTreeBranch branchID="b2">
                    <uncertaintyModel>123</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
                <logicTreeBranchSet uncertaintyType="bGRRelative"
                                    branchSetID="bs1"
                                    applyToBranches="b1">
                  <logicTreeBranch branchID="b3">
                    <uncertaintyModel>123</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
            </logicTree>
        """)
        sm = _whatever_sourcemodel()
        exc = self._assert_logic_tree_error('lt', {'lt': lt, 'sm': sm}, 'base',
                                            logictree.ValidationError)
        self.assertEqual(exc.lineno, 21)
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
                    <uncertaintyModel>sm</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
              <logicTreeBranchingLevel branchingLevelID="bl2">
                <logicTreeBranchSet uncertaintyType="abGRAbsolute"
                                    applyToSources="src01"
                                    branchSetID="bs1">
                  <logicTreeBranch branchID="b2">
                    <uncertaintyModel>123.45</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
            </logicTree>
        """)

        sm = _whatever_sourcemodel()

        exc = self._assert_logic_tree_error('lt', {'lt': lt, 'sm': sm},
                                            'base',
                                            logictree.ValidationError)
        self.assertEqual(exc.lineno, 17)
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
                    <uncertaintyModel>sm</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
              <logicTreeBranchingLevel branchingLevelID="bl2">
                <logicTreeBranchSet uncertaintyType="bGRRelative"
                                    branchSetID="bs1">
                  <logicTreeBranch branchID="b2">
                    <uncertaintyModel>123.45z</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
            </logicTree>
        """)
        sm = _whatever_sourcemodel()
        exc = self._assert_logic_tree_error('lt', {'lt': lt, 'sm': sm}, 'base',
                                            logictree.ValidationError)
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
                    <uncertaintyModel>sm</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
              <logicTreeBranchingLevel branchingLevelID="bl2">
                <logicTreeBranchSet uncertaintyType="incrementalMFDAbsolute"
                                    branchSetID="bs1">
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
            _TestableSourceModelLogicTree('lt', {'lt': lt, 'sm': sm}, 'base')
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
                    <uncertaintyModel>sm</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
              <logicTreeBranchingLevel branchingLevelID="bl2">
                <logicTreeBranchSet uncertaintyType="simpleFaultGeometryAbsolute"
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
        exc = self._assert_logic_tree_error('lt', {'lt': lt, 'sm': sm}, 'base',
                                            ValueError)
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
                    <uncertaintyModel>sm</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
              <logicTreeBranchingLevel branchingLevelID="bl2">
                <logicTreeBranchSet uncertaintyType="complexFaultGeometryAbsolute"
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
        exc = self._assert_logic_tree_error('lt', {'lt': lt, 'sm': sm}, 'base',
                                            ValueError)
        self.assertIn('Could not convert posList->posList: Found a non-float ',
                      str(exc))

    def test_characteristic_fault_planar_geometry_wrong_format(self):
        lt = _make_nrml("""\
            <logicTree logicTreeID="lt1">
              <logicTreeBranchingLevel branchingLevelID="bl1">
                <logicTreeBranchSet uncertaintyType="sourceModel"
                                    branchSetID="bs1">
                  <logicTreeBranch branchID="b1">
                    <uncertaintyModel>sm</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
              <logicTreeBranchingLevel branchingLevelID="bl2">
                <logicTreeBranchSet uncertaintyType="characteristicFaultGeometryAbsolute"
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
        exc = self._assert_logic_tree_error('lt', {'lt': lt, 'sm': sm}, 'base',
                                            ValueError)
        self.assertIn('Could not convert lat->latitude', str(exc))

    def test_characteristic_fault_simple_geometry_wrong_format(self):
        lt = _make_nrml("""\
            <logicTree logicTreeID="lt1">
              <logicTreeBranchingLevel branchingLevelID="bl1">
                <logicTreeBranchSet uncertaintyType="sourceModel"
                                    branchSetID="bs1">
                  <logicTreeBranch branchID="b1">
                    <uncertaintyModel>sm</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
              <logicTreeBranchingLevel branchingLevelID="bl2">
                <logicTreeBranchSet uncertaintyType="characteristicFaultGeometryAbsolute"
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
        exc = self._assert_logic_tree_error('lt', {'lt': lt, 'sm': sm}, 'base',
                                            ValueError)
        self.assertIn('Could not convert posList->posList: Found a non-float',
                      str(exc))

    def test_characteristic_fault_complex_geometry_wrong_format(self):
        lt = _make_nrml("""\
            <logicTree logicTreeID="lt1">
              <logicTreeBranchingLevel branchingLevelID="bl1">
                <logicTreeBranchSet uncertaintyType="sourceModel"
                                    branchSetID="bs1">
                  <logicTreeBranch branchID="b1">
                    <uncertaintyModel>sm</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
              <logicTreeBranchingLevel branchingLevelID="bl2">
                <logicTreeBranchSet uncertaintyType="characteristicFaultGeometryAbsolute"
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
        exc = self._assert_logic_tree_error('lt', {'lt': lt, 'sm': sm}, 'base',
                                            ValueError)
        self.assertIn('Could not convert posList->posList: Found a non-float',
                      str(exc))

    def test_characteristic_fault_invalid_geometry(self):
        lt = _make_nrml("""\
            <logicTree logicTreeID="lt1">
              <logicTreeBranchingLevel branchingLevelID="bl1">
                <logicTreeBranchSet uncertaintyType="sourceModel"
                                    branchSetID="bs1">
                  <logicTreeBranch branchID="b1">
                    <uncertaintyModel>sm</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
              <logicTreeBranchingLevel branchingLevelID="bl2">
                <logicTreeBranchSet uncertaintyType="characteristicFaultGeometryAbsolute"
                                    branchSetID="bs1"
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
        exc = self._assert_logic_tree_error('lt', {'lt': lt, 'sm': sm}, 'base',
                                            logictree.ValidationError)
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
                    <uncertaintyModel>sm</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
            </logicTree>
        """)
        sm = """ololo"""

        self._assert_logic_tree_error(
            'sm', {'lt': lt, 'sm': sm}, 'base',
            ExpatError, exc_filename='sm')

    def test_source_model_schema_violation(self):
        lt = _make_nrml("""\
            <logicTree logicTreeID="lt1">
              <logicTreeBranchingLevel branchingLevelID="bl1">
                <logicTreeBranchSet uncertaintyType="sourceModel"
                                    branchSetID="bs1">
                  <logicTreeBranch branchID="b1">
                    <uncertaintyModel>sm</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
            </logicTree>
        """)
        sm = _make_nrml("""\
        <sourceModel gml:id="sm1">
            <config/>
            <simpleFaultSource gml:id="src01">
                <gml:name>Mount Diablo Thrust</gml:name>
                <tectonicRegion>Swamps, lots of them</tectonicRegion>
                <rake>90.0</rake>
                <evenlyDiscretizedIncrementalMFD minVal="6.55" binSize="0.1"
                    type="ML">0.0010614989 8.8291627E-4 7.3437777E-4
                              6.108288E-4 5.080653E-4
                </evenlyDiscretizedIncrementalMFD>
                <simpleFaultGeometry gml:id="sfg_1">
                    <faultTrace>
                        <gml:LineString srsName="urn:ogc:def:crs:EPSG::4326">
                            <gml:posList>
                                -121.82290 37.73010  0.0
                                -122.03880 37.87710  0.0
                            </gml:posList>
                        </gml:LineString>
                    </faultTrace>
                    <dip>38</dip>
                    <upperSeismogenicDepth>8.0</upperSeismogenicDepth>
                    <lowerSeismogenicDepth>13.0</lowerSeismogenicDepth>
                </simpleFaultGeometry>
            </simpleFaultSource>
        </sourceModel>
        """)
        error = self._assert_logic_tree_error(
            'lt', {'lt': lt, 'sm': sm}, '/x',
            logictree.ValidationError, exc_filename='lt')
        self.assertIn("node config", str(error.message))

    def test_referencing_over_level_boundaries(self):
        lt = _make_nrml("""\
            <logicTree logicTreeID="lt1">
              <logicTreeBranchingLevel branchingLevelID="bl1">
                <logicTreeBranchSet uncertaintyType="sourceModel"
                                    branchSetID="bs1">
                  <logicTreeBranch branchID="b1">
                    <uncertaintyModel>sm1</uncertaintyModel>
                    <uncertaintyWeight>0.5</uncertaintyWeight>
                  </logicTreeBranch>
                  <logicTreeBranch branchID="b2">
                    <uncertaintyModel>sm2</uncertaintyModel>
                    <uncertaintyWeight>0.5</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
              <logicTreeBranchingLevel branchingLevelID="bl2">
                <logicTreeBranchSet uncertaintyType="abGRAbsolute"
                                    branchSetID="bs1" applyToSources="src01"
                                    applyToBranches="b1">
                  <logicTreeBranch branchID="b3">
                    <uncertaintyModel>1 2</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
              <logicTreeBranchingLevel branchingLevelID="bl3">
                <logicTreeBranchSet uncertaintyType="abGRAbsolute"
                                    branchSetID="bs1" applyToSources="src01"
                                    applyToBranches="b2">
                  <logicTreeBranch branchID="b4">
                    <uncertaintyModel>1 2</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
            </logicTree>
        """)
        sm = _whatever_sourcemodel()
        exc = self._assert_logic_tree_error(
            'lt', {'lt': lt, 'sm1': sm, 'sm2': sm}, 'base',
            logictree.ValidationError
        )
        self.assertEqual(exc.lineno, 27)
        error = 'applyToBranches must reference only branches ' \
                'from previous branching level'
        self.assertEqual(exc.message, error,
                         "wrong exception message: %s" % exc.message)

    def test_gmpe_uncertainty(self):
        lt = _make_nrml("""\
            <logicTree logicTreeID="lt1">
              <logicTreeBranchingLevel branchingLevelID="bl1">
                <logicTreeBranchSet uncertaintyType="sourceModel"
                                    branchSetID="bs1">
                  <logicTreeBranch branchID="b1">
                    <uncertaintyModel>sm</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
              <logicTreeBranchingLevel branchingLevelID="bl2">
                <logicTreeBranchSet uncertaintyType="gmpeModel"
                                    branchSetID="bs1">
                  <logicTreeBranch branchID="b2">
                    <uncertaintyModel>CL_2002_AttenRel</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
            </logicTree>
        """)
        sm = _whatever_sourcemodel()
        exc = self._assert_logic_tree_error('lt', {'lt': lt, 'sm': sm}, 'base',
                                            logictree.ValidationError)
        self.assertEqual(exc.lineno, 13)
        error = 'uncertainty of type "gmpeModel" is not allowed ' \
                'in source model logic tree'
        self.assertEqual(exc.message, error,
                         "wrong exception message: %s" % exc.message)

    def test_filters_on_first_branching_level(self):
        filters = ('applyToSources="src01"',
                   'applyToTectonicRegionType="Active Shallow Crust"',
                   'applyToSourceType="point"')
        for filter_ in filters:
            lt = _make_nrml("""\
                <logicTree logicTreeID="lt1">
                  <logicTreeBranchingLevel branchingLevelID="bl1">
                    <logicTreeBranchSet uncertaintyType="sourceModel"
                                        branchSetID="bs1" %s>
                      <logicTreeBranch branchID="b1">
                        <uncertaintyModel>sm</uncertaintyModel>
                        <uncertaintyWeight>1.0</uncertaintyWeight>
                      </logicTreeBranch>
                    </logicTreeBranchSet>
                  </logicTreeBranchingLevel>
                </logicTree>
            """ % filter_)
            sm = _whatever_sourcemodel()
            exc = self._assert_logic_tree_error(
                'lt', {'lt': lt, 'sm': sm}, 'base', logictree.ValidationError
            )
            self.assertEqual(exc.lineno, 4)
            error = 'filters are not allowed on source model uncertainty'
            self.assertEqual(exc.message, error,
                             "wrong exception message: %s" % exc.message)

    def test_referencing_nonexistent_source(self):
        lt = _make_nrml("""\
            <logicTree logicTreeID="lt1">
              <logicTreeBranchingLevel branchingLevelID="bl1">
                <logicTreeBranchSet uncertaintyType="sourceModel"
                                    branchSetID="bs1">
                  <logicTreeBranch branchID="b1">
                    <uncertaintyModel>sm</uncertaintyModel>
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
        exc = self._assert_logic_tree_error('lt', {'lt': lt, 'sm': sm}, 'base',
                                            logictree.ValidationError)
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
                    <uncertaintyModel>sm</uncertaintyModel>
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
        exc = self._assert_logic_tree_error('lt', {'lt': lt, 'sm': sm}, 'base',
                                            logictree.ValidationError)
        self.assertEqual(exc.lineno, 13)
        error = "source models don't define sources of " \
                "tectonic region type 'Volcanic'"
        self.assertEqual(exc.message, error,
                         "wrong exception message: %s" % exc.message)

    def test_referencing_nonexistent_source_type(self):
        lt = _make_nrml("""\
            <logicTree logicTreeID="lt1">
              <logicTreeBranchingLevel branchingLevelID="bl1">
                <logicTreeBranchSet uncertaintyType="sourceModel"
                                    branchSetID="bs1">
                  <logicTreeBranch branchID="b1">
                    <uncertaintyModel>sm</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
              <logicTreeBranchingLevel branchingLevelID="bl2">
                <logicTreeBranchSet uncertaintyType="maxMagGRRelative"
                                    branchSetID="bs1"
                                    applyToSourceType="complexFault">
                  <logicTreeBranch branchID="b2">
                    <uncertaintyModel>123</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
            </logicTree>
        """)
        sm = _whatever_sourcemodel()
        exc = self._assert_logic_tree_error('lt', {'lt': lt, 'sm': sm}, 'base',
                                            logictree.ValidationError)
        self.assertEqual(exc.lineno, 13)
        error = "source models don't define sources of type 'complexFault'"
        self.assertEqual(exc.message, error,
                         "wrong exception message: %s" % exc.message)

    def test_more_than_one_filters_on_one_branchset(self):
        lt = _make_nrml("""\
            <logicTree logicTreeID="lt1">
              <logicTreeBranchingLevel branchingLevelID="bl1">
                <logicTreeBranchSet uncertaintyType="sourceModel"
                                    branchSetID="bs1">
                  <logicTreeBranch branchID="b1">
                    <uncertaintyModel>sm</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
              <logicTreeBranchingLevel branchingLevelID="bl2">
                <logicTreeBranchSet uncertaintyType="maxMagGRRelative"
                            branchSetID="bs1"
                            applyToSourceType="simpleFault"
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
        exc = self._assert_logic_tree_error('lt', {'lt': lt, 'sm': sm}, 'base',
                                            logictree.ValidationError)
        self.assertEqual(exc.lineno, 13)
        error = 'only one filter is allowed per branchset'
        self.assertEqual(exc.message, error,
                         "wrong exception message: %s" % exc.message)

    def test_wrong_filter_on_absolute_uncertainties(self):
        uncertainties_and_values = [('abGRAbsolute', '123 45'),
                                    ('maxMagGRAbsolute', '678')]
        filters = ('applyToSources="src01 src02"',
                   'applyToTectonicRegionType="Active Shallow Crust"',
                   'applyToSourceType="simpleFault"')
        for uncertainty, value in uncertainties_and_values:
            for filter_ in filters:
                lt = _make_nrml("""\
                    <logicTree logicTreeID="lt1">
                      <logicTreeBranchingLevel branchingLevelID="bl1">
                        <logicTreeBranchSet uncertaintyType="sourceModel"
                                            branchSetID="bs1">
                          <logicTreeBranch branchID="b1">
                            <uncertaintyModel>sm</uncertaintyModel>
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
                exc = self._assert_logic_tree_error('lt', {'lt': lt, 'sm': sm},
                                                    'base',
                                                    logictree.ValidationError)
                self.assertEqual(exc.lineno, 13)
                error = (
                    "uncertainty of type '%s' must define 'applyToSources'"
                    " with only one source id" % uncertainty)
                self.assertEqual(
                    exc.message, error,
                    "wrong exception message: %s" % exc.message)


class SourceModelLogicTreeTestCase(unittest.TestCase):
    def assert_branch_equal(self, branch, branch_id, weight_str, value,
                            child_branchset_args=None):
        self.assertEqual(type(branch), logictree.Branch)
        self.assertEqual(branch.branch_id, branch_id)
        self.assertEqual(branch.weight, Decimal(weight_str))
        self.assertEqual(branch.value, value)
        if child_branchset_args is None:
            self.assertEqual(branch.child_branchset, None)
        else:
            self.assert_branchset_equal(branch.child_branchset,
                                        *child_branchset_args)

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
                        <uncertaintyModel>sm1</uncertaintyModel>
                        <uncertaintyWeight>0.6</uncertaintyWeight>
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
        lt = _TestableSourceModelLogicTree(
            'lt', {'lt': source_model_logic_tree, 'sm1': sm, 'sm2': sm},
            'basepath', validate=False)
        self.assertEqual(lt.samples_by_lt_path(),
                         collections.Counter({('b1',): 1, ('b2',): 1}))

        self.assert_branchset_equal(lt.root_branchset, 'sourceModel', {},
                                    [('b1', '0.6', 'sm1'),
                                     ('b2', '0.4', 'sm2')])

    def test_two_levels(self):
        source_model_logic_tree = _make_nrml("""\
        <logicTree logicTreeID="lt1">
            <logicTreeBranchingLevel branchingLevelID="bl1">
                <logicTreeBranchSet uncertaintyType="sourceModel"
                                    branchSetID="bs1">
                    <logicTreeBranch branchID="b1">
                        <uncertaintyModel>sm</uncertaintyModel>
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
            'lt', {'lt': source_model_logic_tree, 'sm': sm}, '/base',
            validate=False)
        self.assertEqual(
            lt.samples_by_lt_path(),
            collections.Counter({('b1', 'b2'): 1, ('b1', 'b3'): 1}))
        self.assert_branchset_equal(lt.root_branchset,
                                    'sourceModel', {},
                                    [('b1', '1.0', 'sm',
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
                        <uncertaintyModel>sm</uncertaintyModel>
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
            'lt', {'lt': source_model_logic_tree, 'sm': sm}, '/base',
            validate=False)
        self.assert_branchset_equal(
            lt.root_branchset,
            'sourceModel', {},
            [('b1', '1.0', 'sm',
              ('abGRAbsolute', {'applyToSources': ['src01']},
               [('b2', '0.9', (100, 500)),
                ('b3', '0.1', (-1.23, +0.1))])
              )])

    def test_apply_to_branches(self):
        source_model_logic_tree = _make_nrml("""\
        <logicTree logicTreeID="lt1">
            <logicTreeBranchingLevel branchingLevelID="bl1">
                <logicTreeBranchSet uncertaintyType="sourceModel"
                                    branchSetID="bs1">
                    <logicTreeBranch branchID="sb1">
                        <uncertaintyModel>sm1</uncertaintyModel>
                        <uncertaintyWeight>0.6</uncertaintyWeight>
                    </logicTreeBranch>
                    <logicTreeBranch branchID="sb2">
                        <uncertaintyModel>sm2</uncertaintyModel>
                        <uncertaintyWeight>0.3</uncertaintyWeight>
                    </logicTreeBranch>
                    <logicTreeBranch branchID="sb3">
                        <uncertaintyModel>sm3</uncertaintyModel>
                        <uncertaintyWeight>0.1</uncertaintyWeight>
                    </logicTreeBranch>
                </logicTreeBranchSet>
            </logicTreeBranchingLevel>
            <logicTreeBranchingLevel branchingLevelID="bl2">
                <logicTreeBranchSet uncertaintyType="bGRRelative"
                                    branchSetID="bs2"
                                    applyToBranches="sb1 sb3">
                    <logicTreeBranch branchID="b2">
                        <uncertaintyModel>+1</uncertaintyModel>
                        <uncertaintyWeight>1.0</uncertaintyWeight>
                    </logicTreeBranch>
                </logicTreeBranchSet>
                <logicTreeBranchSet uncertaintyType="maxMagGRAbsolute"
                                    branchSetID="bs2"
                                    applyToSources="src01"
                                    applyToBranches="sb2">
                    <logicTreeBranch branchID="b3">
                        <uncertaintyModel>-3</uncertaintyModel>
                        <uncertaintyWeight>1.0</uncertaintyWeight>
                    </logicTreeBranch>
                </logicTreeBranchSet>
            </logicTreeBranchingLevel>
        </logicTree>
        """)
        sm = _whatever_sourcemodel()
        lt = _TestableSourceModelLogicTree(
            'lt', {'lt': source_model_logic_tree,
                   'sm1': sm, 'sm2': sm, 'sm3': sm},
            '/base', validate=False)
        self.assert_branchset_equal(
            lt.root_branchset,
            'sourceModel', {},
            [('sb1', '0.6', 'sm1',
              ('bGRRelative', {},
               [('b2', '1.0', +1)]
               )),
             ('sb2', '0.3', 'sm2',
              ('maxMagGRAbsolute', {'applyToSources': ['src01']},
               [('b3', '1.0', -3)]
               )),
             ('sb3', '0.1', 'sm3',
              ('bGRRelative', {},
               [('b2', '1.0', +1)]
               ))
             ]
            )
        sb1, sb2, sb3 = lt.root_branchset.branches
        self.assertTrue(sb1.child_branchset is sb3.child_branchset)

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
                        <uncertaintyModel>sm</uncertaintyModel>
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
            'lt', {'lt': source_model_logic_tree, 'sm': sm},
            '/base', validate=False)
        self.assert_branchset_equal(
            lt.root_branchset, 'sourceModel', {}, [('b1', '1.0', 'sm')])


class SampleTestCase(unittest.TestCase):

    def test_sample(self):
        branches = [logictree.Branch(1, Decimal('0.2'), 'A'),
                    logictree.Branch(1, Decimal('0.3'), 'B'),
                    logictree.Branch(1, Decimal('0.5'), 'C')]
        samples = logictree.sample(branches, 1000, random.Random(42))

        def count(samples, value):
            counter = 0
            for s in samples:
                if s.value == value:
                    counter += 1
            return counter

        self.assertEqual(count(samples, value='A'), 178)
        self.assertEqual(count(samples, value='B'), 302)
        self.assertEqual(count(samples, value='C'), 520)

    def test_sample_broken_branch_weights(self):
        branches = [logictree.Branch(0, Decimal('0.1'), 0),
                    logictree.Branch(1, Decimal('0.2'), 1)]
        with self.assertRaises(AssertionError):
            logictree.sample(branches, 1000, random.Random(42))

    def test_sample_one_branch(self):
        # always the same branch is returned
        branches = [logictree.Branch(0, Decimal('1.0'), 0)]
        bs = logictree.sample(branches, 10, random.Random(42))
        for b in bs:
            self.assertEqual(b.branch_id, 0)


class BranchSetEnumerateTestCase(unittest.TestCase):
    def test_enumerate(self):
        b0 = logictree.Branch('0', Decimal('0.64'), '0')
        b1 = logictree.Branch('1', Decimal('0.36'), '1')
        b00 = logictree.Branch('0.0', Decimal('0.33'), '0.0')
        b01 = logictree.Branch('0.1', Decimal('0.27'), '0.1')
        b02 = logictree.Branch('0.2', Decimal('0.4'), '0.2')
        b10 = logictree.Branch('1.0', Decimal('1.0'), '1.0')
        b100 = logictree.Branch('1.0.0', Decimal('0.1'), '1.0.0')
        b101 = logictree.Branch('1.0.1', Decimal('0.9'), '1.0.1')
        bs_root = logictree.BranchSet(None, None)
        bs_root.branches = [b0, b1]
        bs0 = logictree.BranchSet(None, None)
        bs0.branches = [b00, b01, b02]
        bs1 = logictree.BranchSet(None, None)
        bs1.branches = [b10]
        b0.child_branchset = bs0
        b1.child_branchset = bs1
        bs10 = logictree.BranchSet(None, None)
        bs10.branches = [b100, b101]
        b10.child_branchset = bs10

        ae = self.assertEqual

        paths = bs_root.enumerate_paths()
        ae(next(paths), (Decimal('0.2112'), [b0, b00]))
        ae(next(paths), (Decimal('0.1728'), [b0, b01]))
        ae(next(paths), (Decimal('0.256'), [b0, b02]))
        ae(next(paths), (Decimal('0.036'), [b1, b10, b100]))
        ae(next(paths), (Decimal('0.32400'), [b1, b10, b101]))
        self.assertRaises(StopIteration, lambda: next(paths))

        paths = bs1.enumerate_paths()
        ae(next(paths), (Decimal('0.1'), [b10, b100]))
        ae(next(paths), (Decimal('0.9'), [b10, b101]))
        self.assertRaises(StopIteration, lambda: next(paths))


class BranchSetGetBranchByIdTestCase(unittest.TestCase):
    def test(self):
        bs = logictree.BranchSet(None, None)
        b1 = logictree.Branch('1', Decimal('0.33'), None)
        b2 = logictree.Branch('2', Decimal('0.33'), None)
        bbzz = logictree.Branch('bzz', Decimal('0.34'), None)
        bs.branches = [b1, b2, bbzz]
        self.assertIs(bs.get_branch_by_id('1'), b1)
        self.assertIs(bs.get_branch_by_id('2'), b2)
        self.assertIs(bs.get_branch_by_id('bzz'), bbzz)

    def test_nonexistent_branch(self):
        bs = logictree.BranchSet(None, None)
        br = logictree.Branch('br', Decimal('1.0'), None)
        bs.branches.append(br)
        self.assertRaises(AssertionError, bs.get_branch_by_id, 'bz')


class BranchSetApplyUncertaintyMethodSignaturesTestCase(unittest.TestCase):
    def test_apply_uncertainty_ab_absolute(self):
        mfd = Mock()
        bs = logictree.BranchSet('abGRAbsolute', {})
        bs._apply_uncertainty_to_mfd(mfd, (0.1, 33.4))
        self.assertEqual(mfd.method_calls,
                         [('modify', ('set_ab',
                                      {'a_val': 0.1, 'b_val': 33.4}), {})])

    def test_apply_uncertainty_b_relative(self):
        mfd = Mock()
        bs = logictree.BranchSet('bGRRelative', {})
        bs._apply_uncertainty_to_mfd(mfd, -1.6)
        self.assertEqual(mfd.method_calls,
                         [('modify', ('increment_b', {'value': -1.6}), {})])

    def test_apply_uncertainty_mmax_relative(self):
        mfd = Mock()
        bs = logictree.BranchSet('maxMagGRRelative', {})
        bs._apply_uncertainty_to_mfd(mfd, 32.1)
        self.assertEqual(
            mfd.method_calls,
            [('modify', ('increment_max_mag', {'value': 32.1}), {})])

    def test_apply_uncertainty_mmax_absolute(self):
        mfd = Mock()
        bs = logictree.BranchSet('maxMagGRAbsolute', {})
        bs._apply_uncertainty_to_mfd(mfd, 55)
        self.assertEqual(mfd.method_calls,
                         [('modify', ('set_max_mag', {'value': 55}), {})])

    def test_apply_uncertainty_incremental_mfd_absolute(self):
        mfd = Mock()
        bs = logictree.BranchSet('incrementalMFDAbsolute', {})
        bs._apply_uncertainty_to_mfd(mfd, (8.0, 0.1, [0.01, 0.005]))
        self.assertEqual(
            mfd.method_calls,
            [('modify', ('set_mfd', {'min_mag': 8.0,
                                     'bin_width': 0.1,
                                     'occurrence_rates': [0.01, 0.005]}),  {})]
        )

    def test_apply_uncertainty_simple_fault_dip_relative(self):
        source = Mock()
        bs = logictree.BranchSet('simpleFaultDipRelative', {})
        bs._apply_uncertainty_to_geometry(source, 15.0)
        self.assertEqual(
            source.method_calls,
            [('modify', ('adjust_dip', {'increment': 15.0}), {})])

    def test_apply_uncertainty_simple_fault_dip_absolute(self):
        source = Mock()
        bs = logictree.BranchSet('simpleFaultDipAbsolute', {})
        bs._apply_uncertainty_to_geometry(source, 45.0)
        self.assertEqual(
            source.method_calls,
            [('modify', ('set_dip', {'dip': 45.0}), {})])

    def test_apply_uncertainty_simple_fault_geometry_absolute(self):
        source = Mock()
        trace = geo.Line([geo.Point(0., 0.), geo.Point(1., 1.)])
        bs = logictree.BranchSet('simpleFaultGeometryAbsolute', {})
        bs._apply_uncertainty_to_geometry(source,
                                          (trace, 0.0, 10.0, 90.0, 1.0))
        self.assertEqual(
            source.method_calls,
            [('modify', ('set_geometry', {'fault_trace': trace,
                                          'upper_seismogenic_depth': 0.0,
                                          'lower_seismogenic_depth': 10.0,
                                          'dip': 90.0,
                                          'spacing': 1.0}), {})])

    def test_apply_uncertainty_complex_fault_geometry_absolute(self):
        source = Mock()
        edges = [
            geo.Line([geo.Point(0.0, 0.0, 0.0), geo.Point(1.0, 0.0, 0.0)]),
            geo.Line([geo.Point(0.0, -0.1, 10.0), geo.Point(1.0, -0.1, 10.0)])
            ]
        bs = logictree.BranchSet('complexFaultGeometryAbsolute', {})
        bs._apply_uncertainty_to_geometry(source, (edges, 5.0))
        self.assertEqual(
            source.method_calls,
            [('modify', ('set_geometry', {'edges': edges,
                                          'spacing': 5.0}), {})])

    def test_apply_uncertainty_characteristic_fault_geometry_absolute(self):
        source = Mock()
        trace = geo.Line([geo.Point(0., 0.), geo.Point(1., 1.)])
        surface = geo.SimpleFaultSurface.from_fault_data(
            trace, 0.0, 10.0, 90.0, 1.0)
        bs = logictree.BranchSet('characteristicFaultGeometryAbsolute', {})
        bs._apply_uncertainty_to_geometry(source, surface)
        self.assertEqual(
            source.method_calls,
            [('modify', ('set_geometry', {'surface': surface}), {})])

    def test_apply_uncertainty_unknown_uncertainty_type(self):
        bs = logictree.BranchSet('makeMeFeelGood', {})
        self.assertRaises(AssertionError,
                          bs.apply_uncertainty, None, None)


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

    def test_unknown_source_type(self):
        bs = logictree.BranchSet('maxMagGRRelative',
                                 {'applyToSourceType': 'forest'})
        self.assertRaises(AssertionError, bs.apply_uncertainty,
                          -1, self.point_source)

    def test_relative_uncertainty(self):
        uncertainties = [('maxMagGRRelative', +1),
                         ('bGRRelative', -0.2)]
        for uncertainty, value in uncertainties:
            branchset = logictree.BranchSet(uncertainty, {})
            branchset.apply_uncertainty(value, self.point_source)
        self.assertEqual(self.point_source.mfd.max_mag, 6.5 + 1)
        self.assertEqual(self.point_source.mfd.b_val, 0.9 - 0.2)

    def test_absolute_uncertainty(self):
        uncertainties = [('maxMagGRAbsolute', 9),
                         ('abGRAbsolute', (-1, 0.2))]
        for uncertainty, value in uncertainties:
            branchset = logictree.BranchSet(uncertainty, {})
            branchset.apply_uncertainty(value, self.point_source)
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
        branchset = logictree.BranchSet(uncertainty, {})
        branchset.apply_uncertainty(value, inc_point_source)
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
                1.0, top_left, top_right, bottom_right, bottom_left))

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
        uncertainty, value = ('simpleFaultDipRelative', -15.)
        branchset = logictree.BranchSet(uncertainty, {})
        branchset.apply_uncertainty(value, new_fault_source)
        self.assertAlmostEqual(new_fault_source.dip, 45.)

    def test_simple_fault_dip_absolute_uncertainty(self):
        self.assertAlmostEqual(self.fault_source.dip, 60.)
        new_fault_source = deepcopy(self.fault_source)
        uncertainty, value = ('simpleFaultDipAbsolute', 55.)
        branchset = logictree.BranchSet(uncertainty, {})
        branchset.apply_uncertainty(value, new_fault_source)
        self.assertAlmostEqual(new_fault_source.dip, 55.)

    def test_simple_fault_geometry_uncertainty(self):
        new_fault_source = deepcopy(self.fault_source)
        new_trace = geo.Line([geo.Point(30.5, 30.0), geo.Point(31.2, 30.)])
        new_dip = 50.
        new_lsd = 12.
        new_usd = 1.
        uncertainty, value = ('simpleFaultGeometryAbsolute',
                              (new_trace, new_usd, new_lsd, new_dip, 1.0))
        branchset = logictree.BranchSet(uncertainty, {})
        branchset.apply_uncertainty(value, new_fault_source)
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

        uncertainty, value = ('complexFaultGeometryAbsolute',
                              ([new_top_edge, new_bottom_edge], 2.0))
        branchset = logictree.BranchSet(uncertainty, {})
        branchset.apply_uncertainty(value, fault_source)
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
        uncertainty, value = ('characteristicFaultGeometryAbsolute',
                              new_surface)
        branchset = logictree.BranchSet(uncertainty, {})
        branchset.apply_uncertainty(value, fault_source)
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
        uncertainty, value = ('characteristicFaultGeometryAbsolute',
                              new_surface)
        new_surface.dip = 65.0
        branchset = logictree.BranchSet(uncertainty, {})
        branchset.apply_uncertainty(value, fault_source)
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
        uncertainty, value = ('characteristicFaultGeometryAbsolute',
                              new_surface)
        branchset = logictree.BranchSet(uncertainty, {})
        branchset.apply_uncertainty(value, fault_source)
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
                    mesh_spacing=1.0, strike=0.0, dip=90.0,
                    top_left=points[0], top_right=points[1],
                    bottom_right=points[3], bottom_left=points[2]
                ),
                rake=0,
                temporal_occurrence_model=PoissonTOM(50.))

    def test_unknown_filter(self):
        bs = logictree.BranchSet(None, {'applyToSources': [1], 'foo': 'bar'})
        self.assertRaises(AssertionError, bs.filter_source, None)

    def test_source_type(self):
        bs = logictree.BranchSet(None, {'applyToSourceType': 'area'})
        for source in (self.simple_fault, self.complex_fault, self.point,
                       self.characteristic_fault):
            self.assertEqual(bs.filter_source(source), False)
        self.assertEqual(bs.filter_source(self.area), True)

        bs = logictree.BranchSet(None, {'applyToSourceType': 'point'})
        for source in (self.simple_fault, self.complex_fault, self.area,
                       self.characteristic_fault):
            self.assertEqual(bs.filter_source(source), False)
        self.assertEqual(bs.filter_source(self.point), True)

        bs = logictree.BranchSet(
            None, {'applyToSourceType': 'simpleFault'}
        )
        for source in (self.complex_fault, self.point, self.area,
                       self.characteristic_fault):
            self.assertEqual(bs.filter_source(source), False)
        self.assertEqual(bs.filter_source(self.simple_fault), True)

        bs = logictree.BranchSet(
            None, {'applyToSourceType': 'complexFault'}
        )
        for source in (self.simple_fault, self.point, self.area,
                       self.characteristic_fault):
            self.assertEqual(bs.filter_source(source), False)
        self.assertEqual(bs.filter_source(self.complex_fault), True)

        bs = logictree.BranchSet(
            None, {'applyToSourceType': 'characteristicFault'}
        )
        for source in (self.simple_fault, self.point, self.area,
                       self.complex_fault):
            self.assertEqual(bs.filter_source(source), False)
        self.assertEqual(bs.filter_source(self.characteristic_fault), True)

    def test_tectonic_region_type(self):
        test = lambda trt, source: \
            logictree.BranchSet(None, {'applyToTectonicRegionType': trt}) \
                     .filter_source(source)

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
        test = lambda sources, source, expected_result: self.assertEqual(
            logictree.BranchSet(
                None, {'applyToSources': [s.source_id for s in sources]}
            ).filter_source(source),
            expected_result
        )

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
            logictree.GsimLogicTree(StringIO(xml), ['Shield'])
        if errormessage is not None:
            self.assertEqual(errormessage, str(exc.exception))

    def parse_valid(self, xml, tectonic_region_types=('Shield',)):
        xmlbytes = xml.encode('utf-8') if hasattr(xml, 'encode') else xml
        return logictree.GsimLogicTree(
            StringIO(xmlbytes), tectonic_region_types)

    def test_not_xml(self):
        self.parse_invalid('xxx', ET.ParseError)
        self.parse_invalid('<?xml foo bar baz', ET.ParseError)

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
            xml, ValueError, 'Unknown GSIM: +100 in file <StringIO>')

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
            xml, logictree.InvalidLogicTree,
            'only uncertainties of type "gmpeModel" are allowed in gmpe '
            'logic tree')

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
        self.parse_invalid(xml, logictree.InvalidLogicTree,
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
            xml, logictree.InvalidLogicTree, "Duplicated branchSetID bs1")

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
            xml, ValueError, "Unknown GSIM: SAdighEtAl1997 in file <StringIO>")

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
            xml, logictree.InvalidLogicTree,
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
                         {'bs1': 4, 'bs2': 5, 'bs3': 2, 'bs4': 1})
        self.assertEqual(fs_bg_model_lt.get_num_branches(),
                         {'bs1': 4, 'bs2': 5, 'bs3': 0, 'bs4': 0})
        self.assertEqual(as_model_lt.get_num_paths(), 40)
        self.assertEqual(fs_bg_model_lt.get_num_paths(), 20)
        self.assertEqual(len(list(as_model_lt)), 5 * 4 * 2 * 1)
        effective_rlzs = set(rlz.uid for rlz in fs_bg_model_lt)
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
        gsim_lt = self.parse_valid(xml, ['Volcanic'])
        for seed in range(1000):
            rlz = logictree.sample_one(gsim_lt, random.Random(seed))
            counter[rlz.lt_path] += 1
        # the percentages will be close to 40% and 60%
        self.assertEqual(counter, {('b1',): 414, ('b2',): 586})

    def test_get_gsim_by_trt(self):
        xml = _make_nrml("""\
    <logicTree logicTreeID='lt1'>
<!-- 1.0 Logic Tree for Active Shallow Crust -->
        <logicTreeBranchingLevel branchingLevelID="bl1">
            <logicTreeBranchSet uncertaintyType="gmpeModel" branchSetID="Active Shallow" applyToTectonicRegionType="Active Shallow Crust">

                <logicTreeBranch branchID="AkkarBommer2010">
 <uncertaintyModel>AkkarBommer2010</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                </logicTreeBranch>
                
               </logicTreeBranchSet>
        </logicTreeBranchingLevel>
<!-- 2.0 Logic Tree for Stable Shallow Crust -->
        <logicTreeBranchingLevel branchingLevelID="bl2">
            <logicTreeBranchSet uncertaintyType="gmpeModel" branchSetID="Stable Shallow" applyToTectonicRegionType="Stable Shallow Crust">

                <logicTreeBranch branchID="AkkarBommer2010">
 <uncertaintyModel>AkkarBommer2010</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                </logicTreeBranch>
                
               </logicTreeBranchSet>
        </logicTreeBranchingLevel>
<!-- 3.0 Logic Tree for Shield -->
        <logicTreeBranchingLevel branchingLevelID="bl3"> 
        <logicTreeBranchSet uncertaintyType="gmpeModel" branchSetID="Shield" applyToTectonicRegionType="Shield">

                <logicTreeBranch branchID="Toro2002SHARE">
 <uncertaintyModel>ToroEtAl2002SHARE</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                </logicTreeBranch>
                
            </logicTreeBranchSet>
        </logicTreeBranchingLevel>
<!-- 4.0 Logic Tree for Subduction Interface -->
        <logicTreeBranchingLevel branchingLevelID="bl4">
            <logicTreeBranchSet uncertaintyType="gmpeModel" branchSetID="Subduction_Interface" applyToTectonicRegionType="Subduction Interface">
                
                <logicTreeBranch branchID="ZhaoEtAl2006SInter">
 <uncertaintyModel>ZhaoEtAl2006SInter</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                    
                </logicTreeBranch>
            </logicTreeBranchSet>
        </logicTreeBranchingLevel>
<!-- 5.0 Logic Tree for Subduction Inslab -->
        <logicTreeBranchingLevel branchingLevelID="bl5">
            <logicTreeBranchSet uncertaintyType="gmpeModel" branchSetID="Subduction_InSlab"
                    applyToTectonicRegionType="Subduction IntraSlab">

               <logicTreeBranch branchID="ZhaoEtAl2006SSlab">
 <uncertaintyModel>ZhaoEtAl2006SSlab</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
         
                </logicTreeBranch>
            </logicTreeBranchSet>
        </logicTreeBranchingLevel>
<!-- 6.0 Logic Tree for Volcanic -->
        <logicTreeBranchingLevel branchingLevelID="bl6">
            <logicTreeBranchSet uncertaintyType="gmpeModel" branchSetID="Volcanic" applyToTectonicRegionType="Volcanic">
                <logicTreeBranch branchID="FaccioliEtAl2010">
                <uncertaintyModel>FaccioliEtAl2010</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                </logicTreeBranch>
            </logicTreeBranchSet>
        </logicTreeBranchingLevel>
<!-- 7.0 Logic Tree for Vrancea -->
        <logicTreeBranchingLevel branchingLevelID="bl7">
            <logicTreeBranchSet uncertaintyType="gmpeModel" branchSetID="Deep" applyToTectonicRegionType="Subduction Deep">

                <logicTreeBranch branchID="LinLee2008SSlab">
 <uncertaintyModel>LinLee2008SSlab</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                </logicTreeBranch>

            </logicTreeBranchSet>
        </logicTreeBranchingLevel>

    </logicTree>""")
        gsim_lt = self.parse_valid(xml, ["Stable Shallow Crust"])
        [rlz] = gsim_lt
        gsim = gsim_lt.get_gsim_by_trt(rlz, 'Stable Shallow Crust')
        self.assertEqual(str(gsim), 'AkkarBommer2010()')
        # this test was broken in release 1.4, a wrong ordering
        # of the value gave back LinLee2008SSlab instead of AkkarBommer2010
        self.assertEqual([str(v) for v in rlz.value], [
            'AkkarBommer2010()', 'AkkarBommer2010()', 'ToroEtAl2002SHARE()',
            'ZhaoEtAl2006SInter()', 'ZhaoEtAl2006SSlab()',
            'FaccioliEtAl2010()', 'LinLee2008SSlab()'])

    def test_gsim_with_kwargs(self):
        class FakeGMPETable(object):
            def __init__(self, gmpe_table):
                self.gmpe_table = gmpe_table

            def __str__(self):
                return 'FakeGMPETable(gmpe_table="%s")' % self.gmpe_table

        valid.GSIM['FakeGMPETable'] = FakeGMPETable
        try:
            xml = _make_nrml("""\
            <logicTree logicTreeID="lt1">
                <logicTreeBranchingLevel branchingLevelID="bl1">
                    <logicTreeBranchSet uncertaintyType="gmpeModel"
                                branchSetID="bs1"
                                applyToTectonicRegionType="Shield">
                        <logicTreeBranch branchID="b1">
                            <uncertaintyModel gmpe_table="Wcrust_rjb_med.hdf5">
                                FakeGMPETable
                            </uncertaintyModel>
                            <uncertaintyWeight>1.0</uncertaintyWeight>
                        </logicTreeBranch>
                    </logicTreeBranchSet>
                </logicTreeBranchingLevel>
            </logicTree>
            """)
            gsim_lt = self.parse_valid(xml, ['Shield'])
            self.assertEqual(repr(gsim_lt), '''<GsimLogicTree
Shield,b1,FakeGMPETable(gmpe_table="Wcrust_rjb_med.hdf5"),w=1.0>''')
        finally:
            del valid.GSIM['FakeGMPETable']


class LogicTreeProcessorTestCase(unittest.TestCase):
    def setUp(self):
        # this is an example with number_of_logic_tree_samples = 1
        oqparam = tests.get_oqparam('classical_job.ini')
        self.source_model_lt = readinput.get_source_model_lt(oqparam)
        self.gmpe_lt = readinput.get_gsim_lt(
            oqparam, ['Active Shallow Crust', 'Subduction Interface'])
        self.rnd = random.Random(oqparam.random_seed)

    def test_sample_source_model(self):
        [(sm_name, weight, branch_ids, _, _)] = self.source_model_lt
        self.assertEqual(sm_name, 'example-source-model.xml')
        self.assertEqual(('b1', 'b5', 'b8'), branch_ids)

    def test_multi_sampling(self):
        orig_samples = self.source_model_lt.num_samples
        self.source_model_lt.num_samples = 10
        samples_dic = self.source_model_lt.samples_by_lt_path()
        try:
            self.assertEqual(samples_dic, collections.Counter(
                {('b1', 'b4', 'b7'): 6, ('b1', 'b3', 'b7'): 2,
                 ('b1', 'b5', 'b8'): 1, ('b1', 'b3', 'b6'): 1}))
        finally:
            self.source_model_lt.num_samples = orig_samples

    def test_sample_gmpe(self):
        (value, weight, branch_ids, _, _) = logictree.sample_one(
            self.gmpe_lt, self.rnd)
        self.assertEqual(value, ('ChiouYoungs2008()', 'SadighEtAl1997()'))
        self.assertEqual(weight, 0.5)
        self.assertEqual(('b2', 'b3'), branch_ids)


class LogicTreeProcessorParsePathTestCase(unittest.TestCase):
    def setUp(self):
        oqparam = tests.get_oqparam('classical_job.ini')

        self.uncertainties_applied = []

        def apply_uncertainty(branchset, value, source):
            fingerprint = (branchset.uncertainty_type, value)
            self.uncertainties_applied.append(fingerprint)
        self.original_apply_uncertainty = logictree.BranchSet.apply_uncertainty
        logictree.BranchSet.apply_uncertainty = apply_uncertainty

        self.source_model_lt = readinput.get_source_model_lt(oqparam)
        self.gmpe_lt = readinput.get_gsim_lt(
            oqparam, ['Active Shallow Crust', 'Subduction Interface'])

    def tearDown(self):
        logictree.BranchSet.apply_uncertainty = self.original_apply_uncertainty

    def test_parse_source_model_logictree_path(self):
        make_apply_un = self.source_model_lt.make_apply_uncertainties
        make_apply_un(['b1', 'b5', 'b8'])(None)
        self.assertEqual(self.uncertainties_applied,
                         [('maxMagGRRelative', -0.2),
                          ('bGRRelative', -0.1)])
        del self.uncertainties_applied[:]
        make_apply_un(['b1', 'b3', 'b6'])(None)
        self.assertEqual(self.uncertainties_applied,
                         [('maxMagGRRelative', 0.2),
                          ('bGRRelative', 0.1)])

    def test_parse_invalid_smlt(self):
        smlt = os.path.join(DATADIR, 'source_model_logic_tree.xml')
        with self.assertRaises(Exception) as ctx:
            for smpath in source.collect_source_model_paths(smlt):
                pass
        exc = ctx.exception
        self.assertIn('not well-formed (invalid token)', str(exc))
        self.assertEqual(exc.lineno, 5)
        self.assertEqual(exc.offset, 61)
        self.assertEqual(exc.filename, smlt)
