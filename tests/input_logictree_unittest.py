# -*- coding: utf-8 -*-

# Copyright (c) 2010-2011, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.

"""
Tests for python logic tree processor.
"""

import unittest
import os
from StringIO import StringIO
from decimal import Decimal
import json

from mock import Mock

from openquake.java import jvm, jexception
from openquake.input import logictree
from tests.utils.helpers import patch, get_data_path, assertDeepAlmostEqual


class _TesteableSourceModelLogicTree(logictree.SourceModelLogicTree):
    def __init__(self, filename, files, basepath):
        self.files = files
        super(_TesteableSourceModelLogicTree, self).__init__(basepath,
                                                             filename)

    def _open_file(self, filename):
        if not filename in self.files:
            return super(_TesteableSourceModelLogicTree, self)._open_file(
                filename
            )
        return StringIO(self.files[filename])


class _TesteableGMPELogicTree(logictree.GMPELogicTree):
    def __init__(self, filename, content, basepath, tectonic_region_types):
        self.content = content
        super(_TesteableGMPELogicTree, self).__init__(
            tectonic_region_types, basepath=basepath,
            filename=filename
        )

    def _open_file(self, filename):
        if not self.content:
            return super(_TesteableGMPELogicTree, self)._open_file(
                filename
            )
        return StringIO(self.content)


def _make_nrml(content):
    return """\
    <nrml xmlns:gml="http://www.opengis.net/gml"\
          xmlns="http://openquake.org/xmlns/nrml/0.2"\
          xmlns:qml="http://quakeml.org/xmlns/quakeml/1.1"\
          gml:id="n1">\
        %s
    </nrml>""" % content

def _whatever_sourcemodel():
    return _make_nrml("""\
    <sourceModel gml:id="sm1">
        <config/>
        <simpleFaultSource gml:id="src01">
            <gml:name>Mount Diablo Thrust</gml:name>
            <tectonicRegion>Active Shallow Crust</tectonicRegion>
            <rake>90.0</rake>
            <truncatedGutenbergRichter>
                <aValueCumulative>3.6786313049897035</aValueCumulative>
                <bValue>1.0</bValue>
                <minMagnitude>5.0</minMagnitude>
                <maxMagnitude>7.0</maxMagnitude>
            </truncatedGutenbergRichter>
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
        <simpleFaultSource gml:id="src02">
            <gml:name>Mount Diablo Thrust</gml:name>
            <tectonicRegion>Active Shallow Crust</tectonicRegion>
            <rake>90.0</rake>
            <truncatedGutenbergRichter>
                <aValueCumulative>3.6786313049897035</aValueCumulative>
                <bValue>1.0</bValue>
                <minMagnitude>5.0</minMagnitude>
                <maxMagnitude>7.0</maxMagnitude>
            </truncatedGutenbergRichter>
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
        <pointSource gml:id="doublemfd">
          <gml:name></gml:name>
          <tectonicRegion>Active Shallow Crust</tectonicRegion>
          <location>
            <gml:Point><gml:pos>-125.4 42.9</gml:pos></gml:Point>
          </location>
          <ruptureRateModel>
            <truncatedGutenbergRichter>
                <aValueCumulative>3.6786313049897035</aValueCumulative>
                <bValue>1.0</bValue>
                <minMagnitude>5.0</minMagnitude>
                <maxMagnitude>7.0</maxMagnitude>
            </truncatedGutenbergRichter>
            <focalMechanism publicID="smi:fm1/0">
              <qml:nodalPlanes>
                <qml:nodalPlane1>
                  <qml:strike><qml:value>0.0</qml:value></qml:strike>
                  <qml:dip><qml:value>90.0</qml:value></qml:dip>
                  <qml:rake><qml:value>0.0</qml:value></qml:rake>
                </qml:nodalPlane1>
              </qml:nodalPlanes>
            </focalMechanism>
          </ruptureRateModel>
          <ruptureRateModel>
            <truncatedGutenbergRichter>
                <aValueCumulative>3.6786313049897035</aValueCumulative>
                <bValue>1.0</bValue>
                <minMagnitude>5.0</minMagnitude>
                <maxMagnitude>7.0</maxMagnitude>
            </truncatedGutenbergRichter>
            <focalMechanism publicID="smi:fm1/1">
              <qml:nodalPlanes>
                <qml:nodalPlane1>
                  <qml:strike><qml:value>0.0</qml:value></qml:strike>
                  <qml:dip><qml:value>90.0</qml:value></qml:dip>
                  <qml:rake><qml:value>0.0</qml:value></qml:rake>
                </qml:nodalPlane1>
              </qml:nodalPlanes>
            </focalMechanism>
          </ruptureRateModel>
          <ruptureDepthDistribution>
            <magnitude>6.0 6.5</magnitude>
            <depth>5.0 1.0</depth>
          </ruptureDepthDistribution>
          <hypocentralDepth>5.0</hypocentralDepth>
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
            _TesteableSourceModelLogicTree(filename, files, basepath)
        exc = arc.exception
        self.assertEqual(exc.filename, exc_filename or filename)
        self.assertEqual(exc.basepath, basepath)
        return exc

    def test_nonexistent_logictree(self):
        exc = self._assert_logic_tree_error('missing_file', {}, 'base',
                                            logictree.ParsingError)
        error = "[Errno 2] No such file or directory: 'base/missing_file'"
        self.assertEqual(exc.message, error,
                         "wrong exception message: %s" % exc.message)

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
        error = "'{http://openquake.org/xmlns/nrml/0.2}logicTreeSet': " \
                "This element is not expected."
        self.assertTrue(error in exc.message,
                        "wrong exception message: %s" % exc.message)

    def test_missing_source_model_file(self):
        source = _make_nrml("""\
            <logicTree logicTreeID="lt1">
              <logicTreeBranchingLevel branchingLevelID="bl1">
                <logicTreeBranchSet uncertaintyType="sourceModel"
                                    branchSetID="bs1">
                  <logicTreeBranch branchID="b1">
                    <uncertaintyModel>source_model1.xml</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
            </logicTree>
        """)
        exc = self._assert_logic_tree_error(
            'logictree', {'logictree': source}, 'base',
            logictree.ParsingError, exc_filename='source_model1.xml'
        )
        error = "[Errno 2] No such file or directory: 'base/source_model1.xml'"
        self.assertEqual(exc.message, error,
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
        self.assertEqual(exc.message, error,
                        "wrong exception message: %s" % exc.message)

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
                    <uncertaintyWeight>0.3</uncertaintyWeight>
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
        exc = self._assert_logic_tree_error('lt', {'lt': lt, 'sm': sm}, 'base',
                                            logictree.ValidationError)
        self.assertEqual(exc.lineno, 16)
        error = "expected list of 2 float(s) separated by space, " \
                "as source 'src01' has 1 GR MFD(s)"
        self.assertEqual(exc.message, error,
                        "wrong exception message: %s" % exc.message)

    def test_ab_gr_absolute_wrong_number_of_pairs(self):
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
                                    applyToSources="doublemfd"
                                    branchSetID="bs1">
                  <logicTreeBranch branchID="b2">
                    <uncertaintyModel>
                        123 321
                        345 567
                        142 555
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
        self.assertEqual(exc.lineno, 16)
        error = "expected list of 4 float(s) separated by space, " \
                "as source 'doublemfd' has 2 GR MFD(s)"
        self.assertEqual(exc.message, error,
                        "wrong exception message: %s" % exc.message)

    def test_max_mag_absolute_wrong_number_of_numbers(self):
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
                <logicTreeBranchSet uncertaintyType="maxMagGRAbsolute"
                                    applyToSources="doublemfd"
                                    branchSetID="bs1">
                  <logicTreeBranch branchID="b2">
                    <uncertaintyModel>
                        345 567
                        142 555
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
        self.assertEqual(exc.lineno, 16)
        error = "expected list of 2 float(s) separated by space, " \
                "as source 'doublemfd' has 2 GR MFD(s)"
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
        exc = self._assert_logic_tree_error('lt', {'lt': lt, 'sm': sm}, '/x',
                                            logictree.ParsingError,
                                            exc_filename='sm')
        self.assertTrue("is not an element of the set" in exc.message,
                        "wrong exception message: %s" % exc.message)

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
        error = "source ids ['bzzz'] are not defined in source models"
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
            _TesteableGMPELogicTree(filename, content, basepath,
                                    tectonic_region_types)
        exc = arc.exception
        self.assertEqual(exc.filename, filename)
        self.assertEqual(exc.basepath, basepath)
        return exc

    def test_nonexistent_file(self):
        exc = self._assert_logic_tree_error('missing', None, 'base', set(),
                                            logictree.ParsingError)
        error = "[Errno 2] No such file or directory: 'base/missing'"
        self.assertEqual(exc.message, error,
                         "wrong exception message: %s" % exc.message)

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
                        <uncertaintyModel>CL_2002_AttenRel</uncertaintyModel>
                        <uncertaintyWeight>1.0</uncertaintyWeight>
                    </logicTreeBranch>
                </logicTreeBranchSet>
                <logicTreeBranchSet uncertaintyType="gmpeModel"
                            branchSetID="bs2"
                            applyToTectonicRegionType="Subduction IntraSlab">
                    <logicTreeBranch branchID="b2">
                        <uncertaintyModel>CB_2008_AttenRel</uncertaintyModel>
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
        self.assertEqual(exc.lineno, 13)

    def test_unavailable_gmpe(self):
        gmpe = _make_nrml("""\
        <logicTree logicTreeID="lt1">
            <logicTreeBranchingLevel branchingLevelID="bl1">
                <logicTreeBranchSet uncertaintyType="gmpeModel"
                                    branchSetID="bs1"
                                    applyToTectonicRegionType="Volcanic">
                    <logicTreeBranch branchID="b1">
                        <uncertaintyModel>no-such-gmpe</uncertaintyModel>
                        <uncertaintyWeight>1.0</uncertaintyWeight>
                    </logicTreeBranch>
                </logicTreeBranchSet>
            </logicTreeBranchingLevel>
        </logicTree>
        """)
        exc = self._assert_logic_tree_error('gmpe', gmpe, 'base',
                                            set(['Volcanic']),
                                            logictree.ValidationError)
        self.assertEqual(exc.message, "gmpe 'no-such-gmpe' is not available",
                        "wrong exception message: %s" % exc.message)
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
                        <uncertaintyModel>AS_1997_AttenRel</uncertaintyModel>
                        <uncertaintyWeight>1.0</uncertaintyWeight>
                    </logicTreeBranch>
                </logicTreeBranchSet>
            </logicTreeBranchingLevel>
            <logicTreeBranchingLevel branchingLevelID="bl2">
                <logicTreeBranchSet uncertaintyType="gmpeModel"
                            branchSetID="bs2"
                            applyToTectonicRegionType="Subduction Interface">
                    <logicTreeBranch branchID="b2">
                        <uncertaintyModel>BA_2008_AttenRel</uncertaintyModel>
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
        self.assertEqual(exc.lineno, 15)

    def test_missing_tectonic_region_type(self):
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
        lt_source = _make_nrml("""\
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
        lt = _TesteableSourceModelLogicTree(
            'lt', {'lt': lt_source, 'sm1': sm, 'sm2': sm}, 'basepath'
        )
        self.assert_branchset_equal(lt.root_branchset, 'sourceModel', {},
                                    [('b1', '0.6', 'basepath/sm1'),
                                     ('b2', '0.4', 'basepath/sm2')])

    def test_two_levels(self):
        lt_source = _make_nrml("""\
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
        lt = _TesteableSourceModelLogicTree('lt', {'lt': lt_source, 'sm': sm},
                                            '/base')
        self.assert_branchset_equal(lt.root_branchset,
            'sourceModel', {},
            [('b1', '1.0', '/base/sm',
                ('maxMagGRRelative', {},
                    [('b2', '0.6', +123),
                     ('b3', '0.4', -123)])
            )]
        )

    def test_filters(self):
        lt_source = _make_nrml("""\
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
        lt = _TesteableSourceModelLogicTree('lt', {'lt': lt_source, 'sm': sm},
                                            '/base')
        self.assert_branchset_equal(lt.root_branchset,
            'sourceModel', {},
            [('b1', '1.0', '/base/sm',
                ('abGRAbsolute', {'applyToSources': ['src01']},
                    [('b2', '0.9', [(100, 500)]),
                     ('b3', '0.1', [(-1.23, +0.1)])])
            )]
        )

    def test_apply_to_branches(self):
        lt_source = _make_nrml("""\
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
        lt = _TesteableSourceModelLogicTree(
            'lt', {'lt': lt_source, 'sm1': sm, 'sm2': sm, 'sm3': sm}, '/base'
        )
        self.assert_branchset_equal(lt.root_branchset,
            'sourceModel', {},
            [('sb1', '0.6', '/base/sm1',
                ('bGRRelative', {},
                    [('b2', '1.0', +1)]
                )),
             ('sb2', '0.3', '/base/sm2',
                 ('maxMagGRAbsolute', {'applyToSources': ['src01']},
                    [('b3', '1.0', [-3])]
                )),
             ('sb3', '0.1', '/base/sm3',
                ('bGRRelative', {},
                    [('b2', '1.0', +1)]
                ))
            ]
        )
        sb1, sb2, sb3 = lt.root_branchset.branches
        self.assertTrue(sb1.child_branchset is sb3.child_branchset)

    def test_mixed_mfd_types_absolute_uncertainties(self):
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
                <logicTreeBranchSet uncertaintyType="maxMagGRAbsolute"
                                    branchSetID="bs2"
                                    applyToSources="triplemfd">
                    <logicTreeBranch branchID="b2">
                        <uncertaintyModel>10 11</uncertaintyModel>
                        <uncertaintyWeight>1.0</uncertaintyWeight>
                    </logicTreeBranch>
                </logicTreeBranchSet>
            </logicTreeBranchingLevel>
        </logicTree>
        """)
        # source model has three mfds, from which
        # only first and third are GR.
        sm = _make_nrml("""\
        <sourceModel gml:id="sm1">
            <config/>
            <pointSource gml:id="triplemfd">
              <gml:name></gml:name>
              <tectonicRegion>Active Shallow Crust</tectonicRegion>
              <location>
                <gml:Point><gml:pos>-125.4 42.9</gml:pos></gml:Point>
              </location>

              <ruptureRateModel>
                <truncatedGutenbergRichter>
                    <aValueCumulative>3.6786313049897035</aValueCumulative>
                    <bValue>1.0</bValue>
                    <minMagnitude>5.0</minMagnitude>
                    <maxMagnitude>7.0</maxMagnitude>
                </truncatedGutenbergRichter>
                <focalMechanism publicID="smi:fm1/0">
                  <qml:nodalPlanes>
                    <qml:nodalPlane1>
                      <qml:strike><qml:value>0.0</qml:value></qml:strike>
                      <qml:dip><qml:value>90.0</qml:value></qml:dip>
                      <qml:rake><qml:value>0.0</qml:value></qml:rake>
                    </qml:nodalPlane1>
                  </qml:nodalPlanes>
                </focalMechanism>
              </ruptureRateModel>

              <ruptureRateModel>
                <evenlyDiscretizedIncrementalMFD minVal="6.55" binSize="0.1"
                    type="ML">
                    0.0010614989 8.8291627E-4 7.3437777E-4
                    6.108288E-4 5.080653E-4
                </evenlyDiscretizedIncrementalMFD>
                <focalMechanism publicID="smi:fm1/1">
                  <qml:nodalPlanes>
                    <qml:nodalPlane1>
                      <qml:strike><qml:value>0.0</qml:value></qml:strike>
                      <qml:dip><qml:value>90.0</qml:value></qml:dip>
                      <qml:rake><qml:value>0.0</qml:value></qml:rake>
                    </qml:nodalPlane1>
                  </qml:nodalPlanes>
                </focalMechanism>
              </ruptureRateModel>

              <ruptureRateModel>
                <truncatedGutenbergRichter>
                    <aValueCumulative>3.6786313049897035</aValueCumulative>
                    <bValue>1.0</bValue>
                    <minMagnitude>5.0</minMagnitude>
                    <maxMagnitude>7.0</maxMagnitude>
                </truncatedGutenbergRichter>
                <focalMechanism publicID="smi:fm1/1">
                  <qml:nodalPlanes>
                    <qml:nodalPlane1>
                      <qml:strike><qml:value>0.0</qml:value></qml:strike>
                      <qml:dip><qml:value>90.0</qml:value></qml:dip>
                      <qml:rake><qml:value>0.0</qml:value></qml:rake>
                    </qml:nodalPlane1>
                  </qml:nodalPlanes>
                </focalMechanism>
              </ruptureRateModel>

              <ruptureDepthDistribution>
                <magnitude>6.0 6.5</magnitude>
                <depth>5.0 1.0</depth>
              </ruptureDepthDistribution>
              <hypocentralDepth>5.0</hypocentralDepth>
            </pointSource>
        </sourceModel>
        """)
        # check that source and logic tree are valid
        _TesteableSourceModelLogicTree('lt', {'lt': lt, 'sm': sm}, '')


class GMPELogicTreeTestCase(unittest.TestCase):
    def assert_result(self, lt, result):
        actual_result = {}
        branchset = lt.root_branchset
        while branchset is not None:
            self.assertNotEqual(len(branchset.branches), 0)
            trt = branchset.filters['applyToTectonicRegionType']
            actual_result[trt] = [
                (branch.branch_id, str(branch.weight), branch.value)
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
                        <uncertaintyModel>AS_1997_AttenRel</uncertaintyModel>
                        <uncertaintyWeight>0.7</uncertaintyWeight>
                    </logicTreeBranch>
                    <logicTreeBranch branchID="b2">
                        <uncertaintyModel>BW_1997_AttenRel</uncertaintyModel>
                        <uncertaintyWeight>0.3</uncertaintyWeight>
                    </logicTreeBranch>
                </logicTreeBranchSet>
            </logicTreeBranchingLevel>
            <logicTreeBranchingLevel branchingLevelID="bl2">
                <logicTreeBranchSet uncertaintyType="gmpeModel"
                            branchSetID="bs2"
                            applyToTectonicRegionType="Active Shallow Crust">
                    <logicTreeBranch branchID="b3">
                        <uncertaintyModel>BA_2008_AttenRel</uncertaintyModel>
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
                            Abrahamson_2000_AttenRel
                        </uncertaintyModel>
                        <uncertaintyWeight>0.1</uncertaintyWeight>
                    </logicTreeBranch>
                    <logicTreeBranch branchID="b5">
                        <uncertaintyModel>
                            GouletEtAl_2006_AttenRel
                        </uncertaintyModel>
                        <uncertaintyWeight>0.8</uncertaintyWeight>
                    </logicTreeBranch>
                    <logicTreeBranch branchID="b6">
                        <uncertaintyModel>
                            Field_2000_AttenRel
                        </uncertaintyModel>
                        <uncertaintyWeight>0.1</uncertaintyWeight>
                    </logicTreeBranch>
                </logicTreeBranchSet>
            </logicTreeBranchingLevel>
        </logicTree>
        """)
        trts = ['Subduction Interface', 'Active Shallow Crust', 'Volcanic']
        gmpe_lt = _TesteableGMPELogicTree('gmpe', gmpe, '/base', trts)
        self.assert_result(gmpe_lt, {
            'Subduction Interface': [
                ('b1', '0.7', 'AS_1997_AttenRel'),
                ('b2', '0.3', 'BW_1997_AttenRel')
            ],
            'Active Shallow Crust': [
                ('b3', '1.0', 'BA_2008_AttenRel')
            ],
            'Volcanic': [
                ('b4', '0.1', 'Abrahamson_2000_AttenRel'),
                ('b5', '0.8', 'GouletEtAl_2006_AttenRel'),
                ('b6', '0.1', 'Field_2000_AttenRel')
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


class BranchSetApplyUncertaintyMethodSignaturesTestCase(unittest.TestCase):
    def test_apply_uncertainty_ab_absolute(self):
        mfd = Mock()
        bs = logictree.BranchSet('abGRAbsolute', {})
        bs._apply_uncertainty_to_mfd(mfd, (0.1, 33.4))
        self.assertEqual(mfd.method_calls, [('setAB', (0.1, 33.4), {})])

    def test_apply_uncertainty_b_relative(self):
        mfd = Mock()
        bs = logictree.BranchSet('bGRRelative', {})
        bs._apply_uncertainty_to_mfd(mfd, -1.6)
        self.assertEqual(mfd.method_calls, [('incrementB', (-1.6, ), {})])

    def test_apply_uncertainty_mmax_relative(self):
        mfd = Mock()
        bs = logictree.BranchSet('maxMagGRRelative', {})
        bs._apply_uncertainty_to_mfd(mfd, 32.1)
        self.assertEqual(mfd.method_calls,
                         [('incrementMagUpper', (32.1, ), {})])

    def test_apply_uncertainty_mmax_absolute(self):
        mfd = Mock()
        bs = logictree.BranchSet('maxMagGRAbsolute', {})
        bs._apply_uncertainty_to_mfd(mfd, 55)
        self.assertEqual(mfd.method_calls, [('setMagUpper', (55, ), {})])

    def test_apply_uncertainty_unknown_uncertainty_type(self):
        bs = logictree.BranchSet('makeMeFeelGood', {})
        self.assertRaises(AssertionError,
                          bs._apply_uncertainty_to_mfd, None, None)


class BranchSetApplyUncertaintyTestCase(unittest.TestCase):
    def setUp(self):
        super(BranchSetApplyUncertaintyTestCase, self).setUp()
        self.MFD = jvm().JClass(
            'org.opensha.sha.magdist.GutenbergRichterMagFreqDist'
        )
        SourceModelReader = jvm().JClass('org.gem.engine.hazard.' \
                                         'parsers.SourceModelReader')
        srcfile = get_data_path('example-source-model.xml')
        self.single_mfd_sources = list(SourceModelReader(srcfile, 0.1).read())
        self.non_gr_mfd_source = self.single_mfd_sources[0]
        # filtering out first source (has non-gr mfd)
        self.single_mfd_sources = self.single_mfd_sources[1:]
        srcfile = get_data_path('example-source-model-double-mfds.xml')
        self.double_mfd_sources = list(SourceModelReader(srcfile, 0.1).read())
        _apply_uncertainty = logictree.BranchSet._apply_uncertainty_to_mfd
        self.mock = patch('openquake.input.logictree.' \
                          'BranchSet._apply_uncertainty_to_mfd').start()
        self.mock.side_effect = _apply_uncertainty

    def tearDown(self):
        super(BranchSetApplyUncertaintyTestCase, self).tearDown()
        self.mock.stop()

    def test_unknown_source_type(self):
        bs = logictree.BranchSet('maxMagGRRelative', {})
        self.assertRaises(AssertionError, bs.apply_uncertainty,
                          -1, None)

    def test_relative_uncertainty_single_mfd(self):
        uncertainties = [('maxMagGRRelative', +1),
                         ('bGRRelative', -0.2)]
        for uncertainty, value in uncertainties:
            branchset = logictree.BranchSet(uncertainty, {})
            for source in self.single_mfd_sources:
                branchset.apply_uncertainty(value, source)
                self.assertEqual(self.mock.call_count, 1)
                [(bs, mfd, call_value), kwargs] = self.mock.call_args
                self.assertEqual(kwargs, {})
                self.assertEqual(type(mfd), self.MFD)
                self.assertEqual(value, call_value)
                self.mock.reset_mock()

    def test_relative_uncertainty_double_mfd(self):
        uncertainties = [('maxMagGRRelative', -1.1),
                         ('bGRRelative', +2)]
        for uncertainty, value in uncertainties:
            branchset = logictree.BranchSet(uncertainty, {})
            for source in self.double_mfd_sources:
                branchset.apply_uncertainty(value, source)
                self.assertEqual(self.mock.call_count, 2)
                [((bs, mfd, call_value), kwargs),
                 ((bs, mfd2, call_value2), kwargs2)] = self.mock.call_args_list
                self.assertEqual(kwargs, {})
                self.assertEqual(kwargs2, {})
                self.assertEqual(type(mfd), self.MFD)
                self.assertEqual(type(mfd2), self.MFD)
                self.assertTrue(mfd2 is not mfd)
                self.assertEqual(value, call_value)
                self.assertEqual(value, call_value2)
                self.mock.reset_mock()

    def test_absolute_uncertainty_single_mfd(self):
        uncertainties = [('maxMagGRAbsolute', [9]),
                         ('abGRAbsolute', [(-1, -0.2)])]
        for uncertainty, value in uncertainties:
            branchset = logictree.BranchSet(uncertainty, {})
            for source in self.single_mfd_sources:
                branchset.apply_uncertainty(value, source)
                self.assertEqual(self.mock.call_count, 1)
                [(bs, mfd, call_value), kwargs] = self.mock.call_args
                self.assertEqual(kwargs, {})
                self.assertEqual(type(mfd), self.MFD)
                self.assertEqual(value, [call_value])
                self.mock.reset_mock()

    def test_absolute_uncertainty_double_mfd(self):
        uncertainties = [('maxMagGRAbsolute', [10, 11.1]),
                         ('abGRAbsolute', [(-1, -0.2), (+1, +2)])]
        for uncertainty, value in uncertainties:
            branchset = logictree.BranchSet(uncertainty, {})
            for source in self.double_mfd_sources:
                branchset.apply_uncertainty(value, source)
                self.assertEqual(self.mock.call_count, 2)
                [((bs, mfd, call_value), kwargs),
                 ((bs, mfd2, call_value2), kwargs2)] = self.mock.call_args_list
                self.assertEqual(kwargs, {})
                self.assertEqual(kwargs2, {})
                self.assertEqual(type(mfd), self.MFD)
                self.assertEqual(type(mfd2), self.MFD)
                self.assertTrue(mfd2 is not mfd)
                self.assertEqual(value[0], call_value)
                self.assertEqual(value[1], call_value2)
                self.mock.reset_mock()

    def test_ignore_non_gr_mfd(self):
        uncertainties = [('maxMagGRAbsolute', [10, 11.1]),
                         ('abGRAbsolute', [(-1, -0.2), (+1, +2)])]
        for uncertainty, value in uncertainties:
            branchset = logictree.BranchSet(uncertainty, {})
            branchset.apply_uncertainty(value, self.non_gr_mfd_source)
            self.assertEqual(self.mock.call_count, 0)


class BranchSetFilterTestCase(unittest.TestCase):
    def setUp(self):
        super(BranchSetFilterTestCase, self).setUp()
        SourceModelReader = jvm().JClass('org.gem.engine.hazard.' \
                                         'parsers.SourceModelReader')
        srcfile = get_data_path('example-source-model.xml')
        self.simple_fault, self.complex_fault, self.area, self.point, _ \
                = SourceModelReader(srcfile, 0.1).read()

    def test_unknown_filter(self):
        bs = logictree.BranchSet(None, {'applyToSources': [1], 'foo': 'bar'})
        self.assertRaises(AssertionError, bs.filter_source, None)

    def test_source_type(self):
        bs = logictree.BranchSet(None, {'applyToSourceType': 'area'})
        for source in (self.simple_fault, self.complex_fault, self.point):
            self.assertEqual(bs.filter_source(source), False)
        self.assertEqual(bs.filter_source(self.area), True)

        bs = logictree.BranchSet(None, {'applyToSourceType': 'point'})
        for source in (self.simple_fault, self.complex_fault, self.area):
            self.assertEqual(bs.filter_source(source), False)
        self.assertEqual(bs.filter_source(self.point), True)

        bs = logictree.BranchSet(None, {'applyToSourceType': 'simpleFault'})
        for source in (self.complex_fault, self.point, self.area):
            self.assertEqual(bs.filter_source(source), False)
        self.assertEqual(bs.filter_source(self.simple_fault), True)

        bs = logictree.BranchSet(None, {'applyToSourceType': 'complexFault'})
        for source in (self.simple_fault, self.point, self.area):
            self.assertEqual(bs.filter_source(source), False)
        self.assertEqual(bs.filter_source(self.complex_fault), True)

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

        source.tectReg.name = sic
        for wrong_trt in (asc, vlc, ssc, sif):
            self.assertEqual(test(wrong_trt, source), False)
        self.assertEqual(test(sic, source), True)

        source.tectReg.name = vlc
        for wrong_trt in (asc, sic, ssc, sif):
            self.assertEqual(test(wrong_trt, source), False)
        self.assertEqual(test(vlc, source), True)

        source.tectReg.name = sif
        for wrong_trt in (asc, vlc, ssc, sic):
            self.assertEqual(test(wrong_trt, source), False)
        self.assertEqual(test(sif, source), True)

        source.tectReg.name = ssc
        for wrong_trt in (asc, vlc, sic, sif):
            self.assertEqual(test(wrong_trt, source), False)
        self.assertEqual(test(ssc, source), True)

        source.tectReg.name = asc
        for wrong_trt in (sic, vlc, ssc, sif):
            self.assertEqual(test(wrong_trt, source), False)
        self.assertEqual(test(asc, source), True)

    def test_sources(self):
        test = lambda sources, source, expected_result: self.assertEqual(
            logictree.BranchSet(None,
                                {'applyToSources': [s.id for s in sources]}) \
                     .filter_source(source),
            expected_result
        )

        test([self.simple_fault, self.area], self.point, False)
        test([self.simple_fault, self.area], self.area, True)
        test([self.complex_fault, self.simple_fault], self.area, False)
        test([self.area], self.area, True)
        test([self.point, self.simple_fault], self.simple_fault, True)
        test([self.point, self.complex_fault], self.simple_fault, False)


class LogicTreeProcessorTestCase(unittest.TestCase):
    BASE_PATH = get_data_path('')
    SOURCE_MODEL_LT = get_data_path('example-source-model-logictree.xml')
    GMPE_LT = get_data_path('example-gmpe-logictree.xml')

    def setUp(self):
        self.proc = logictree.LogicTreeProcessor(
            self.BASE_PATH, self.SOURCE_MODEL_LT, self.GMPE_LT
        )

    def test_sample_source_model(self):
        result = self.proc.sample_source_model_logictree(random_seed=42,
                                                         mfd_bin_width=0.1)
        result = json.loads(result)
        first_source = {
            'dip': 38.0,
            'floatRuptureFlag': True,
            'id': 'src01',
            'mfd': {
                'D': False,
                'delta': 0.1,
                'first': True,
                'info': '',
                'maxX': 6.95,
                'minX': 6.55,
                'name': u'',
                'num': 5,
                'points': [0.001062, 0.000883, 0.000734, 0.000611, 0.000508],
                'tolerance': 1e-07
            },
            'name': 'Mount Diablo Thrust',
            'rake': 90.0,
            'seismDepthLow': 13.0,
            'seismDepthUpp': 8.0,
            'tectReg': 'ACTIVE_SHALLOW',
            'trace': [{'depth': 0.0, 'lat': 0.658514, 'lon': -2.126210},
                      {'depth': 0.0, 'lat': 0.661080, 'lon': -2.129978}]
        }
        assertDeepAlmostEqual(self, first_source, result[0], delta=1e-5)

    def test_sample_gmpe(self):
        result = json.loads(self.proc.sample_gmpe_logictree(random_seed=123))
        expected = {
            u'Active Shallow Crust': \
                u'org.opensha.sha.imr.attenRelImpl.BA_2008_AttenRel',
            u'Subduction Interface': \
                u'org.opensha.sha.imr.attenRelImpl.McVerryetal_2000_AttenRel'
        }
        self.assertEqual(expected, result)

    def test_sample_and_save_source_model_logictree(self):
        mockcache = Mock(spec=['set'])
        key = 'zxczxc'
        random_seed = 12345
        mfd_bin_width = 0.123
        json_result = 'asd'
        with patch('openquake.input.logictree.LogicTreeProcessor.' \
                   'sample_source_model_logictree') as samplemock:
            samplemock.return_value = json_result
            self.proc.sample_and_save_source_model_logictree(
                mockcache, key, random_seed, mfd_bin_width
            )
            samplemock.assert_called_once_with(self.proc, random_seed,
                                               mfd_bin_width)
            mockcache.set.assert_called_once_with(key, json_result)

    def test_sample_and_save_gmpe_logictree(self):
        mockcache = Mock(spec=['set'])
        key = 'sdasda'
        random_seed = 124112
        json_result = 'jsnrslt'
        with patch('openquake.input.logictree.LogicTreeProcessor.' \
                   'sample_gmpe_logictree') as samplemock:
            samplemock.return_value = json_result
            self.proc.sample_and_save_gmpe_logictree(mockcache, key,
                                                     random_seed)
            samplemock.assert_called_once_with(self.proc, random_seed)
            mockcache.set.assert_called_once_with(key, json_result)
