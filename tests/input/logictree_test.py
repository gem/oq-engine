# -*- coding: utf-8 -*-

# Copyright (c) 2010-2012, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

"""
Tests for python logic tree processor.
"""

import mock
import numpy
import os
import os.path
import shutil
import tempfile
import unittest

from StringIO import StringIO
from decimal import Decimal
from mock import Mock

import openquake.hazardlib
from openquake.hazardlib.pmf import PMF
from openquake.hazardlib.mfd import TruncatedGRMFD, EvenlyDiscretizedMFD
from openquake.hazardlib.gsim.sadigh_1997 import SadighEtAl1997
from openquake.hazardlib.gsim.chiou_youngs_2008 import ChiouYoungs2008
from openquake.nrmllib.parsers import SourceModelParser

from openquake.engine.input import logictree
from openquake.engine.input.source import nrml_to_hazardlib

from tests.utils import helpers

FAKE_CALC_ID = 7


class _TestableSourceModelLogicTree(logictree.SourceModelLogicTree):
    def __init__(self, filename, files, basepath, calc_id, validate=True):
        self.files = files
        if not validate:
            self.validate_branchset = self.__fail
            self.validate_tree = self.__fail
            self.validate_filters = self.__fail
            self.validate_uncertainty_value = self.__fail
        content = files[filename]
        super(_TestableSourceModelLogicTree, self).__init__(
            content, basepath, filename, calc_id, validate
        )

    def __fail(self, *args, **kwargs):
        raise AssertionError("this method shouldn't be called")


class _TestableGMPELogicTree(logictree.GMPELogicTree):
    def __init__(self, filename, content, basepath, tectonic_region_types,
                 calc_id, validate=True):
        if not validate:
            self.validate_branchset = self.__fail
            self.validate_tree = self.__fail
            self.validate_filters = self.__fail
            self.validate_uncertainty_value = self.__fail
        super(_TestableGMPELogicTree, self).__init__(
            tectonic_region_types, content, basepath, filename, calc_id,
            validate
        )

    def __fail(self, *args, **kwargs):
        raise AssertionError("this method shouldn't be called")


def _make_nrml(content):
    return """\
    <nrml xmlns:gml="http://www.opengis.net/gml"\
          xmlns="http://openquake.org/xmlns/nrml/0.4">\
        %s
    </nrml>""" % content


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

    def setUp(self):
        sm = _whatever_sourcemodel()
        self.gsm_patch = mock.patch('openquake.engine.input.logictree'
                                    '.SourceModelLogicTree._get_source_model')
        self.gsm_mock = self.gsm_patch.start()
        ret_val = Mock()
        ret_val.model_content.raw_content = sm
        ret_val.model_content.raw_content_utf8 = sm
        self.gsm_mock.return_value = ret_val

    def tearDown(self):
        self.gsm_mock.stop()
        self.gsm_patch.stop()

    def _assert_logic_tree_error(self, filename, files, basepath,
                                 exc_class=logictree.LogicTreeError,
                                 exc_filename=None):
        with self.assertRaises(exc_class) as arc:
            _TestableSourceModelLogicTree(filename, files, basepath,
                                          FAKE_CALC_ID)
        exc = arc.exception
        self.assertEqual(exc.filename, exc_filename or filename)
        self.assertEqual(exc.basepath, basepath)
        return exc

    def test_logictree_invalid_xml(self):
        exc = self._assert_logic_tree_error(
            'broken_xml', {'broken_xml': "<?xml foo bar baz"}, 'basepath',
            logictree.ParsingError
        )
        self.assertTrue(exc.message.startswith('Malformed declaration'),
                        "wrong exception message: %s" % exc.message)

    def test_logictree_schema_violation(self):
        source = _make_nrml("""\
            <logicTreeSet>
                <logicTree logicTreeID="lt1"/>
            </logicTreeSet>
        """)
        exc = self._assert_logic_tree_error(
            'screwed_schema', {'screwed_schema': source}, 'base',
            logictree.ParsingError
        )
        error = "'{http://openquake.org/xmlns/nrml/0.4}logicTreeSet': " \
                "This element is not expected."
        self.assertTrue(error in str(exc),
                        "wrong exception message: %s" % exc.message)

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
        self.assertEqual(exc.lineno, 9)
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
        self.assertEqual(exc.lineno, 14)
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
        self.assertEqual(exc.lineno, 22)
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
        self.assertEqual(exc.lineno, 16)
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
        self.assertEqual(exc.lineno, 15)
        self.assertEqual(exc.message, 'expected single float value',
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

        ret_val = Mock()
        ret_val.model_content.raw_content_utf8 = sm
        self.gsm_mock.return_value = ret_val

        exc = self._assert_logic_tree_error('lt', {'lt': lt, 'sm': sm}, 'base',
                                            logictree.ParsingError,
                                            exc_filename='sm')
        self.assertEqual(exc.message, "Document is empty, line 1, column 1",
                         "wrong exception message: %s" % exc.message)

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
        ret_val = Mock()
        ret_val.model_content.raw_content_utf8 = sm
        self.gsm_mock.return_value = ret_val

        self._assert_logic_tree_error('lt', {'lt': lt, 'sm': sm}, '/x',
                                      logictree.ParsingError,
                                      exc_filename='sm')

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
        self.assertEqual(exc.lineno, 28)
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
        self.assertEqual(exc.lineno, 14)
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
        self.assertEqual(exc.lineno, 14)
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
        self.assertEqual(exc.lineno, 14)
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
        self.assertEqual(exc.lineno, 16)
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
                error = "uncertainty of type %r must define 'applyToSources'" \
                        " with only one source id" % uncertainty
                self.assertEqual(exc.message, error,
                                "wrong exception message: %s" % exc.message)


class GMPELogicTreeBrokenInputTestCase(unittest.TestCase):
    def _assert_logic_tree_error(self, filename, content, basepath,
                                 tectonic_region_types,
                                 exc_class=logictree.LogicTreeError):
        with self.assertRaises(exc_class) as arc:
            _TestableGMPELogicTree(filename, content, basepath,
                                    tectonic_region_types, FAKE_CALC_ID)
        exc = arc.exception
        self.assertEqual(exc.filename, filename)
        self.assertEqual(exc.basepath, basepath)
        return exc

    def test_invalid_xml(self):
        gmpe = """zxc<nrml></nrml>"""
        exc = self._assert_logic_tree_error('gmpe', gmpe, 'base', set(),
                                            logictree.ParsingError)
        self.assertTrue(exc.message.startswith('Start tag expected'),
                        "wrong exception message: %s" % exc.message)

    def test_schema_violation(self):
        gmpe = _make_nrml("<logicTree></logicTree>")
        exc = self._assert_logic_tree_error('gmpe', gmpe, '/root', set(),
                                            logictree.ParsingError)
        self.assertTrue("attribute 'logicTreeID' is required" in exc.message,
                        "wrong exception message: %s" % exc.message)

    def test_wrong_uncertainty_type(self):
        gmpe = _make_nrml("""\
        <logicTree logicTreeID="lt1">
            <logicTreeBranchingLevel branchingLevelID="bl1">
                <logicTreeBranchSet uncertaintyType="bGRRelative"
                                    branchSetID="bs1"
                                    applyToTectonicRegionType="Volcanic">
                    <logicTreeBranch branchID="b1">
                        <uncertaintyModel>+1</uncertaintyModel>
                        <uncertaintyWeight>1.0</uncertaintyWeight>
                    </logicTreeBranch>
                </logicTreeBranchSet>
            </logicTreeBranchingLevel>
        </logicTree>
        """)
        exc = self._assert_logic_tree_error('gmpe', gmpe, 'base',
                                            set(['Volcanic']),
                                            logictree.ValidationError)
        error = 'only uncertainties of type "gmpeModel" are allowed ' \
                'in gmpe logic tree'
        self.assertEqual(exc.message, error,
                         "wrong exception message: %s" % exc.message)
        self.assertEqual(exc.lineno, 5)

    def test_two_branchsets_in_one_level(self):
        gmpe = _make_nrml("""\
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
        exc = self._assert_logic_tree_error(
            'gmpe', gmpe, 'base', set(['Volcanic', 'Subduction IntraSlab']),
            logictree.ValidationError
        )
        error = 'only one branchset on each branching level is allowed ' \
                'in gmpe logic tree'
        self.assertEqual(exc.message, error,
                         "wrong exception message: %s" % exc.message)
        self.assertEqual(exc.lineno, 15)

    def test_unavailable_gsim(self):
        gmpe = _make_nrml("""\
        <logicTree logicTreeID="lt1">
            <logicTreeBranchingLevel branchingLevelID="bl1">
                <logicTreeBranchSet uncertaintyType="gmpeModel"
                                    branchSetID="bs1"
                                    applyToTectonicRegionType="Volcanic">
                    <logicTreeBranch branchID="b1">
                        <uncertaintyModel>Site</uncertaintyModel>
                        <uncertaintyWeight>1.0</uncertaintyWeight>
                    </logicTreeBranch>
                </logicTreeBranchSet>
            </logicTreeBranchingLevel>
        </logicTree>
        """)
        exc = self._assert_logic_tree_error('gmpe', gmpe, 'base',
                                            set(['Volcanic']),
                                            logictree.ValidationError)
        error = "unknown class 'Site'; available classes are: ["
        if not exc.message.startswith(error):
            raise RuntimeError("%s, expected something starting with %r" %
                               (exc.message, error))
        self.assertEqual(exc.lineno, 7)

    def test_wrong_filters(self):
        filters = ('',
                   'applyToSources="src01"',
                   'applyToTectonicRegionType="Volcanic" applyToSources="zz"',
                   'applyToSourceType="point"')
        for filter_ in filters:
            gmpe = _make_nrml("""\
            <logicTree logicTreeID="lt1">
              <logicTreeBranchingLevel branchingLevelID="bl1">
                <logicTreeBranchSet uncertaintyType="gmpeModel"
                                    branchSetID="bs1" %s>
                  <logicTreeBranch branchID="b1">
                    <uncertaintyModel>SEA_1999_AttenRel</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
            </logicTree>
            """ % filter_)
            exc = self._assert_logic_tree_error('gmpe', gmpe, 'base',
                                                set(['Volcanic']),
                                                logictree.ValidationError)
            self.assertEqual(exc.lineno, 4)
            error = 'branch sets in gmpe logic tree must define only ' \
                    '"applyToTectonicRegionType" filter'
            self.assertEqual(exc.message, error,
                            "wrong exception message: %s" % exc.message)

    def test_unused_tectonic_region_type(self):
        gmpe = _make_nrml("""\
        <logicTree logicTreeID="lt1">
            <logicTreeBranchingLevel branchingLevelID="bl1">
                <logicTreeBranchSet uncertaintyType="gmpeModel"
                            branchSetID="bs1"
                            applyToTectonicRegionType="Subduction Interface">
                  <logicTreeBranch branchID="b1">
                    <uncertaintyModel>Campbell_1997_AttenRel</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
            </logicTreeBranchingLevel>
        </logicTree>
        """)
        exc = self._assert_logic_tree_error('gmpe', gmpe, 'base',
                                            set(['Active Shallow Crust']),
                                            logictree.ValidationError)
        error = "source models don't define sources of tectonic region " \
                "type 'Subduction Interface'"
        self.assertEqual(exc.message, error,
                         "wrong exception message: %s" % exc.message)
        self.assertEqual(exc.lineno, 5)

    def test_tectonic_region_type_used_twice(self):
        gmpe = _make_nrml("""\
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
        exc = self._assert_logic_tree_error('gmpe', gmpe, 'base',
                                            set(['Subduction Interface']),
                                            logictree.ValidationError)
        error = "gmpe uncertainty for tectonic region type " \
                "'Subduction Interface' has already been defined"
        self.assertEqual(exc.message, error,
                         "wrong exception message: %s" % exc.message)
        self.assertEqual(exc.lineno, 17)

    def test_missing_tectonic_region_type(self):
        gmpe = _make_nrml("""\
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
        </logicTree>
        """)
        exc = self._assert_logic_tree_error(
            'gmpe', gmpe, 'base',
            set(['Subduction Interface', 'Active Shallow Crust', 'Volcanic']),
            logictree.ValidationError
        )
        error = "the following tectonic region types are defined " \
                "in source model logic tree but not in gmpe logic tree: " \
                "['Active Shallow Crust', 'Volcanic']"
        self.assertEqual(exc.message, error,
                         "wrong exception message: %s" % exc.message)
        self.assertEqual(exc.lineno, 1)


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
            'basepath', FAKE_CALC_ID, validate=False
        )
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
            FAKE_CALC_ID, validate=False
        )
        self.assert_branchset_equal(lt.root_branchset,
            'sourceModel', {},
            [('b1', '1.0', 'sm',
                ('maxMagGRRelative', {},
                    [('b2', '0.6', +123),
                     ('b3', '0.4', -123)])
            )]
        )

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
            FAKE_CALC_ID, validate=False)
        self.assert_branchset_equal(lt.root_branchset,
            'sourceModel', {},
            [('b1', '1.0', 'sm',
                ('abGRAbsolute', {'applyToSources': ['src01']},
                    [('b2', '0.9', (100, 500)),
                     ('b3', '0.1', (-1.23, +0.1))])
            )]
        )

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
            'lt', {'lt': source_model_logic_tree, 'sm1': sm, 'sm2': sm, 'sm3': sm}, '/base',
            FAKE_CALC_ID, validate=False
        )
        self.assert_branchset_equal(lt.root_branchset,
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
            '/base', FAKE_CALC_ID, validate=False
        )
        self.assert_branchset_equal(lt.root_branchset,
            'sourceModel', {},
            [('b1', '1.0', 'sm')]
        )


class GMPELogicTreeTestCase(unittest.TestCase):
    def assert_result(self, lt, result):
        actual_result = {}
        branchset = lt.root_branchset
        while branchset is not None:
            self.assertNotEqual(len(branchset.branches), 0)
            trt = branchset.filters['applyToTectonicRegionType']
            actual_result[trt] = [
                (branch.branch_id, str(branch.weight), type(branch.value))
                for branch in branchset.branches
            ]
            next_branchset = branchset.branches[0].child_branchset
            for branch in branchset.branches:
                self.assertTrue(branch.child_branchset is next_branchset)
            branchset = next_branchset
            self.assertTrue(trt in result)
            self.assertEqual(actual_result[trt], result[trt])
        self.assertEqual(set(actual_result.keys()), set(result.keys()))
        self.assertEqual(actual_result, result)

    def test(self):
        gmpe = _make_nrml("""\
        <logicTree logicTreeID="lt1">
            <logicTreeBranchingLevel branchingLevelID="bl1">
                <logicTreeBranchSet uncertaintyType="gmpeModel"
                            branchSetID="bs1"
                            applyToTectonicRegionType="Subduction Interface">
                    <logicTreeBranch branchID="b1">
                        <uncertaintyModel>
                            SadighEtAl1997
                        </uncertaintyModel>
                        <uncertaintyWeight>0.7</uncertaintyWeight>
                    </logicTreeBranch>
                    <logicTreeBranch branchID="b2">
                        <uncertaintyModel>
                            ChiouYoungs2008
                        </uncertaintyModel>
                        <uncertaintyWeight>0.3</uncertaintyWeight>
                    </logicTreeBranch>
                </logicTreeBranchSet>
            </logicTreeBranchingLevel>
            <logicTreeBranchingLevel branchingLevelID="bl2">
                <logicTreeBranchSet uncertaintyType="gmpeModel"
                            branchSetID="bs2"
                            applyToTectonicRegionType="Active Shallow Crust">
                    <logicTreeBranch branchID="b3">
                        <uncertaintyModel>
                            SadighEtAl1997
                        </uncertaintyModel>
                        <uncertaintyWeight>1.0</uncertaintyWeight>
                    </logicTreeBranch>
                </logicTreeBranchSet>
            </logicTreeBranchingLevel>
            <logicTreeBranchingLevel branchingLevelID="bl3">
                <logicTreeBranchSet uncertaintyType="gmpeModel"
                            branchSetID="bs3"
                            applyToTectonicRegionType="Volcanic">
                    <logicTreeBranch branchID="b4">
                        <uncertaintyModel>
                            ChiouYoungs2008
                        </uncertaintyModel>
                        <uncertaintyWeight>0.1</uncertaintyWeight>
                    </logicTreeBranch>
                    <logicTreeBranch branchID="b5">
                        <uncertaintyModel>
                            SadighEtAl1997
                        </uncertaintyModel>
                        <uncertaintyWeight>0.9</uncertaintyWeight>
                    </logicTreeBranch>
                </logicTreeBranchSet>
            </logicTreeBranchingLevel>
        </logicTree>
        """)
        trts = ['Subduction Interface', 'Active Shallow Crust', 'Volcanic']
        gmpe_lt = _TestableGMPELogicTree('gmpe', gmpe, '/base', trts,
                                         FAKE_CALC_ID, validate=False)
        self.assert_result(gmpe_lt, {
            'Subduction Interface': [
                ('b1', '0.7', SadighEtAl1997),
                ('b2', '0.3', ChiouYoungs2008)
            ],
            'Active Shallow Crust': [
                ('b3', '1.0', SadighEtAl1997)
            ],
            'Volcanic': [
                ('b4', '0.1', ChiouYoungs2008),
                ('b5', '0.9', SadighEtAl1997),
            ]
        })


class BranchSetSampleTestCase(unittest.TestCase):
    class FakeRandom(object):
        def __init__(self, value):
            self.value = value

        def random(self):
            return self.value

    def test_sample(self):
        bs = logictree.BranchSet(None, None)
        bs.branches = [logictree.Branch(i, Decimal('0.1'), i)
                       for i in xrange(10)]
        self.assertEqual(type(bs.sample()), logictree.Branch)
        r = self.FakeRandom
        self.assertEqual(bs.sample(r(0.05)).value, 0)
        self.assertEqual(bs.sample(r(0.11)).value, 1)
        self.assertEqual(bs.sample(r(0.2)).value, 2)
        self.assertEqual(bs.sample(r(0.88)).value, 8)
        self.assertEqual(bs.sample(r(0.9999999)).value, 9)

    def test_sample_broken_branch_weights(self):
        bs = logictree.BranchSet(None, None)
        bs.branches = [logictree.Branch(0, Decimal('0.1'), 0),
                       logictree.Branch(1, Decimal('0.2'), 1)]
        self.assertRaises(AssertionError, bs.sample, self.FakeRandom(0.8))

    def test_sample_one_branch(self):
        bs = logictree.BranchSet(None, None)
        bs.branches = [logictree.Branch(0, Decimal('1.0'), 0)]
        for i in xrange(10):
            self.assertEqual(bs.sample().branch_id, 0)


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
        ae(paths.next(), (Decimal('0.2112'), [b0, b00]))
        ae(paths.next(), (Decimal('0.1728'), [b0, b01]))
        ae(paths.next(), (Decimal('0.256'), [b0, b02]))
        ae(paths.next(), (Decimal('0.036'), [b1, b10, b100]))
        ae(paths.next(), (Decimal('0.32400'), [b1, b10, b101]))
        self.assertRaises(StopIteration, paths.next)

        paths = bs1.enumerate_paths()
        ae(paths.next(), (Decimal('0.1'), [b10, b100]))
        ae(paths.next(), (Decimal('0.9'), [b10, b101]))
        self.assertRaises(StopIteration, paths.next)


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

    def test_apply_uncertainty_unknown_uncertainty_type(self):
        bs = logictree.BranchSet('makeMeFeelGood', {})
        self.assertRaises(AssertionError,
                          bs._apply_uncertainty_to_mfd, None, None)


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
            rupture_mesh_spacing=1.0
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

    def test_ignore_non_gr_mfd(self):
        uncertainties = [('maxMagGRAbsolute', 10),
                         ('abGRAbsolute', (-1, 0.3))]
        source = self.point_source
        source.mfd = EvenlyDiscretizedMFD(min_mag=3, bin_width=1,
                                          occurrence_rates=[1, 2, 3])
        source.mfd.modify = lambda *args, **kwargs: self.fail()
        for uncertainty, value in uncertainties:
            branchset = logictree.BranchSet(uncertainty, {})
            branchset.apply_uncertainty(value, source)


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
            rupture_mesh_spacing=1.0
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
            area_discretization=10, rupture_mesh_spacing=1.0
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
            dip=45, rake=180
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
                     openquake.hazardlib.geo.Point(1, 1, 2)])]
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
            rake=0
        )


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


class LogicTreeProcessorTestCase(unittest.TestCase):
    def setUp(self):
        cfg = helpers.get_data_path('classical_job.ini')
        job = helpers.get_hazard_job(cfg)

        self.proc = logictree.LogicTreeProcessor(job.hazard_calculation.id)

    def test_sample_source_model(self):
        sm_name, branch_ids = self.proc.sample_source_model_logictree(42)
        self.assertEqual(['b1', 'b3', 'b7'], branch_ids)
        self.assertEqual(sm_name, 'example-source-model.xml')

    def test_sample_gmpe(self):
        branch_ids = self.proc.sample_gmpe_logictree(random_seed=124)
        self.assertEqual(['b2', 'b3'], branch_ids)
        branch_ids = self.proc.sample_gmpe_logictree(random_seed=123)
        self.assertEqual(['b1', 'b3'], branch_ids)

    def test_enumerate_paths(self):
        paths = self.proc.enumerate_paths()
        ae = self.assertEqual
        ae(paths.next(), ('example-source-model.xml', Decimal('0.02'),
                          ['b1', 'b3', 'b6'], ['b1', 'b3']))
        ae(paths.next(), ('example-source-model.xml', Decimal('0.02'),
                          ['b1', 'b3', 'b6'], ['b2', 'b3']))
        ae(paths.next(), ('example-source-model.xml', Decimal('0.06'),
                          ['b1', 'b3', 'b7'], ['b1', 'b3']))
        ae(paths.next(), ('example-source-model.xml', Decimal('0.06'),
                          ['b1', 'b3', 'b7'], ['b2', 'b3']))
        ae(paths.next(), ('example-source-model.xml', Decimal('0.02'),
                          ['b1', 'b3', 'b8'], ['b1', 'b3']))
        ae(paths.next(), ('example-source-model.xml', Decimal('0.02'),
                          ['b1', 'b3', 'b8'], ['b2', 'b3']))
        ae(paths.next(), ('example-source-model.xml', Decimal('0.06'),
                          ['b1', 'b4', 'b6'], ['b1', 'b3']))
        ae(paths.next(), ('example-source-model.xml', Decimal('0.06'),
                          ['b1', 'b4', 'b6'], ['b2', 'b3']))
        ae(paths.next(), ('example-source-model.xml', Decimal('0.18'),
                          ['b1', 'b4', 'b7'], ['b1', 'b3']))
        ae(paths.next(), ('example-source-model.xml', Decimal('0.18'),
                          ['b1', 'b4', 'b7'], ['b2', 'b3']))
        ae(paths.next(), ('example-source-model.xml', Decimal('0.06'),
                          ['b1', 'b4', 'b8'], ['b1', 'b3']))
        ae(paths.next(), ('example-source-model.xml', Decimal('0.06'),
                          ['b1', 'b4', 'b8'], ['b2', 'b3']))
        ae(paths.next(), ('example-source-model.xml', Decimal('0.02'),
                          ['b1', 'b5', 'b6'], ['b1', 'b3']))
        ae(paths.next(), ('example-source-model.xml', Decimal('0.02'),
                          ['b1', 'b5', 'b6'], ['b2', 'b3']))
        ae(paths.next(), ('example-source-model.xml', Decimal('0.06'),
                          ['b1', 'b5', 'b7'], ['b1', 'b3']))
        ae(paths.next(), ('example-source-model.xml', Decimal('0.06'),
                          ['b1', 'b5', 'b7'], ['b2', 'b3']))
        ae(paths.next(), ('example-source-model.xml', Decimal('0.02'),
                          ['b1', 'b5', 'b8'], ['b1', 'b3']))
        ae(paths.next(), ('example-source-model.xml', Decimal('0.02'),
                          ['b1', 'b5', 'b8'], ['b2', 'b3']))
        self.assertRaises(StopIteration, paths.next)


class LogicTreeProcessorParsePathTestCase(unittest.TestCase):
    def setUp(self):
        cfg = helpers.get_data_path('classical_job.ini')
        job = helpers.get_hazard_job(cfg)
        self.uncertainties_applied = []

        def apply_uncertainty(branchset, value, source):
            fingerprint = (branchset.uncertainty_type, value)
            self.uncertainties_applied.append(fingerprint)
        self.original_apply_uncertainty = logictree.BranchSet.apply_uncertainty
        logictree.BranchSet.apply_uncertainty = apply_uncertainty
        self.proc = logictree.LogicTreeProcessor(job.hazard_calculation.id)

    def tearDown(self):
        logictree.BranchSet.apply_uncertainty = self.original_apply_uncertainty

    def test_parse_source_model_logictree_path(self):
        self.proc.parse_source_model_logictree_path(['b1', 'b5', 'b8'])(None)
        self.assertEqual(self.uncertainties_applied,
                         [('maxMagGRRelative', -0.2),
                          ('bGRRelative', -0.1)])
        del self.uncertainties_applied[:]
        self.proc.parse_source_model_logictree_path(['b1', 'b3', 'b6'])(None)
        self.assertEqual(self.uncertainties_applied,
                         [('maxMagGRRelative', 0.2),
                          ('bGRRelative', 0.1)])

    def test_parse_gmpe_model_logictree_path(self):
        from openquake.hazardlib.gsim.sadigh_1997 import SadighEtAl1997
        from openquake.hazardlib.gsim.chiou_youngs_2008 import ChiouYoungs2008
        gmpes = self.proc.parse_gmpe_logictree_path(['b2', 'b3'])
        self.assertIsInstance(gmpes.pop('Active Shallow Crust'),
                              ChiouYoungs2008)
        self.assertIsInstance(gmpes.pop('Subduction Interface'),
                              SadighEtAl1997)
        self.assertEqual(gmpes, {})

        gmpes = self.proc.parse_gmpe_logictree_path(['b1', 'b3'])
        self.assertIsInstance(gmpes.pop('Active Shallow Crust'),
                              SadighEtAl1997)
        self.assertIsInstance(gmpes.pop('Subduction Interface'),
                              SadighEtAl1997)
        self.assertEqual(gmpes, {})


class _BaseSourceModelLogicTreeBlackboxTestCase(unittest.TestCase):
    JOB_CONFIG = None
    NRML_TO_HAZARDLIB_PARAMS = {
        'mesh_spacing': 1,
        'bin_width': 1,
        'area_src_disc': 10,
    }

    def _do_test(self, path, expected_result, expected_branch_ids):
        cfg = helpers.get_data_path(self.JOB_CONFIG)
        job = helpers.get_hazard_job(cfg)
        base_path = job.hazard_calculation.base_path

        proc = logictree.LogicTreeProcessor(job.hazard_calculation.id)

        [branch] = proc.source_model_lt.root_branchset.branches
        all_branches = proc.source_model_lt.branches
        path = iter(path)
        while branch.child_branchset is not None:
            nextbranch = all_branches[next(path)]
            branch.child_branchset.sample = (
                lambda nextbranch: lambda rnd: nextbranch)(nextbranch)
            branch = nextbranch
        assert list(path) == []

        sm_path, branch_ids = proc.sample_source_model_logictree(0)
        self.assertEqual(expected_branch_ids, branch_ids)
        modify_source = proc.parse_source_model_logictree_path(branch_ids)

        expected_result_path = os.path.join(base_path, expected_result)
        e_nrml_sources = SourceModelParser(expected_result_path).parse()
        e_hazardlib_sources = [nrml_to_hazardlib(
                source, **self.NRML_TO_HAZARDLIB_PARAMS)
                               for source in e_nrml_sources]

        original_sm_path = os.path.join(base_path, sm_path)
        a_nrml_sources = SourceModelParser(original_sm_path).parse()
        a_hazardlib_sources = [nrml_to_hazardlib(
                source, **self.NRML_TO_HAZARDLIB_PARAMS)
                               for source in a_nrml_sources]
        for i, source in enumerate(a_hazardlib_sources):
            modify_source(source)

        self.assertEqual(len(e_hazardlib_sources), len(a_hazardlib_sources))
        for i in xrange(len(e_hazardlib_sources)):
            expected_source = e_hazardlib_sources[i]
            actual_source = a_hazardlib_sources[i]
            self.assertTrue(*helpers.deep_eq(expected_source, actual_source))


class RelSMLTBBTestCase(_BaseSourceModelLogicTreeBlackboxTestCase):
    JOB_CONFIG = helpers.get_data_path(
        'LogicTreeRelativeUncertaintiesTest/rel_uncert.ini')

    def test_b4(self):
        self._do_test(['b2', 'b4'], 'result_b4.xml', ['b1', 'b2', 'b4'])

    def test_b5(self):
        self._do_test(['b2', 'b5'], 'result_b5.xml', ['b1', 'b2', 'b5'])

    def test_b6(self):
        self._do_test(['b3', 'b6'], 'result_b6.xml', ['b1', 'b3', 'b6'])

    def test_b7(self):
        self._do_test(['b3', 'b7'], 'result_b7.xml', ['b1', 'b3', 'b7'])


class AbsSMLTBBTestCase(_BaseSourceModelLogicTreeBlackboxTestCase):
    JOB_CONFIG = helpers.get_data_path(
        'LogicTreeAbsoluteUncertaintiesTest/abs_uncert.ini')

    def test_b4(self):
        self._do_test(['b2', 'b4'], 'result_b4.xml', ['b1', 'b2', 'b4'])

    def test_b5(self):
        self._do_test(['b2', 'b5'], 'result_b5.xml', ['b1', 'b2', 'b5'])

    def test_b7(self):
        self._do_test(['b3', 'b7'], 'result_b7.xml', ['b1', 'b3', 'b7'])

    def test_b8(self):
        self._do_test(
            ['b3', 'b6', 'b8'], 'result_b8.xml', ['b1', 'b3', 'b6', 'b8'])

    def test_b9(self):
        self._do_test(
            ['b3', 'b6', 'b9'], 'result_b9.xml', ['b1', 'b3', 'b6', 'b9'])
