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
from StringIO import StringIO

from openquake.input import logictree


class _TesteableLogicTree(logictree.LogicTree):
    def __init__(self, filename, files, basepath):
        self.files = files
        super(_TesteableLogicTree, self).__init__(filename=filename,
                                                  basepath=basepath)

    def _open_file(self, filename):
        if not filename in self.files:
            return super(_TesteableLogicTree, self)._open_file(filename)
        return StringIO(self.files[filename])


class LogicTreeBrokenInputTestCase(unittest.TestCase):
    def test_nonexisting_logictree(self):
        with self.assertRaises(logictree.ParsingError) as arc:
            _TesteableLogicTree('missing_file', {}, 'base')
        exc = arc.exception
        self.assertEqual(exc.filename, 'missing_file')
        self.assertEqual(exc.basepath, 'base')
        error = "[Errno 2] No such file or directory: 'base/missing_file'"
        self.assertEqual(exc.message, error,
                         "wrong exception message: %s" % exc.message)

    def test_logictree_invalid_xml(self):
        source = """<?xml foo bar baz"""
        with self.assertRaises(logictree.ParsingError) as arc:
            _TesteableLogicTree('broken_xml', {'broken_xml': source}, 'base')
        exc = arc.exception
        self.assertEqual(exc.filename, 'broken_xml')
        self.assertEqual(exc.basepath, 'base')
        self.assertTrue(exc.message.startswith('Malformed declaration'),
                        "wrong exception message: %s" % exc.message)

    def _make_nrml(self, content):
        return """\
        <nrml xmlns:gml="http://www.opengis.net/gml"\
              xmlns="http://openquake.org/xmlns/nrml/0.2"\
              gml:id="n1">\
            %s
        </nrml>""" % content

    def _whatever_sourcemodel(self):
        return self._make_nrml("""\
        <sourceModel gml:id="sm1">
            <config/>
            <simpleFaultSource gml:id="src01">
                <gml:name>Mount Diablo Thrust</gml:name>
                <tectonicRegion>Active Shallow Crust</tectonicRegion>
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

    def test_logictree_schema_violation(self):
        source = self._make_nrml("""\
            <logicTreeSet>
                <logicTree logicTreeID="lt1"/>
            </logicTreeSet>
        """)
        with self.assertRaises(logictree.ParsingError) as arc:
            _TesteableLogicTree('screwed_schema',
                                {'screwed_schema': source}, 'base')
        exc = arc.exception
        self.assertEqual(exc.filename, 'screwed_schema')
        self.assertEqual(exc.basepath, 'base')
        error = "'{http://openquake.org/xmlns/nrml/0.2}logicTreeSet': " \
                "This element is not expected."
        self.assertTrue(error in exc.message,
                        "wrong exception message: %s" % exc.message)

    def test_missing_source_model_file(self):
        source = self._make_nrml("""\
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
        with self.assertRaises(logictree.ParsingError) as arc:
            _TesteableLogicTree('logictree', {'logictree': source}, 'base')
        exc = arc.exception
        error = "[Errno 2] No such file or directory: 'base/source_model1.xml'"
        self.assertEqual(exc.message, error,
                        "wrong exception message: %s" % exc.message)

    def test_wrong_uncert_type_on_first_branching_level(self):
        source = self._make_nrml("""\
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
        with self.assertRaises(logictree.ValidationError) as arc:
            _TesteableLogicTree('logictree', {'logictree': source}, 'base')
        exc = arc.exception
        self.assertEqual(exc.filename, 'logictree')
        self.assertEqual(exc.basepath, 'base')
        self.assertEqual(exc.lineno, 4)
        error = 'first branchset must define an uncertainty ' \
                'of type "sourceModel"'
        self.assertEqual(exc.message, error,
                        "wrong exception message: %s" % exc.message)

    def test_source_model_uncert_on_wrong_level(self):
        lt = self._make_nrml("""\
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
        sm = self._whatever_sourcemodel()
        with self.assertRaises(logictree.ValidationError) as arc:
            _TesteableLogicTree('lt', {'lt': lt, 'sm1': sm, 'sm2': sm}, 'base')
        exc = arc.exception
        self.assertEqual(exc.filename, 'lt')
        self.assertEqual(exc.basepath, 'base')
        self.assertEqual(exc.lineno, 13)
        error = 'uncertainty of type "sourceModel" can be defined ' \
                'on first branchset only'
        self.assertEqual(exc.message, error,
                        "wrong exception message: %s" % exc.message)

    def test_two_branchsets_on_first_level(self):
        lt = self._make_nrml("""\
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
        sm = self._whatever_sourcemodel()
        with self.assertRaises(logictree.ValidationError) as arc:
            _TesteableLogicTree('lt', {'lt': lt, 'sm1': sm, 'sm2': sm}, 'base')
        exc = arc.exception
        self.assertEqual(exc.filename, 'lt')
        self.assertEqual(exc.basepath, 'base')
        self.assertEqual(exc.lineno, 11)
        error = 'there must be only one branch set on first branching level'
        self.assertEqual(exc.message, error,
                        "wrong exception message: %s" % exc.message)

    def test_branch_id_not_unique(self):
        lt = self._make_nrml("""\
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
        sm = self._whatever_sourcemodel()
        with self.assertRaises(logictree.ValidationError) as arc:
            _TesteableLogicTree('lt', {'lt': lt, 'sm1': sm, 'sm2': sm}, '/bz')
        exc = arc.exception
        self.assertEqual(exc.filename, 'lt')
        self.assertEqual(exc.basepath, '/bz')
        self.assertEqual(exc.lineno, 9)
        self.assertEqual(exc.message, "branchID 'b1' is not unique",
                        "wrong exception message: %s" % exc.message)

    def test_branches_weight_wrong_sum(self):
        lt = self._make_nrml("""\
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
        sm = self._whatever_sourcemodel()
        with self.assertRaises(logictree.ValidationError) as arc:
            _TesteableLogicTree('lo', {'lo': lt, 'sm1': sm, 'sm2': sm}, 'base')
        exc = arc.exception
        self.assertEqual(exc.filename, 'lo')
        self.assertEqual(exc.basepath, 'base')
        self.assertEqual(exc.lineno, 4)
        self.assertEqual(exc.message, "branchset weights don't sum up to 1.0",
                        "wrong exception message: %s" % exc.message)

    def test_apply_to_nonexistent_branch(self):
        lt = self._make_nrml("""\
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
        sm = self._whatever_sourcemodel()
        with self.assertRaises(logictree.ValidationError) as arc:
            _TesteableLogicTree('lt', {'lt': lt, 'sm': sm}, 'base')
        exc = arc.exception
        self.assertEqual(exc.filename, 'lt')
        self.assertEqual(exc.basepath, 'base')
        self.assertEqual(exc.lineno, 14)
        self.assertEqual(exc.message, "branch 'mssng' is not yet defined",
                        "wrong exception message: %s" % exc.message)

    def test_apply_to_occupied_branch(self):
        lt = self._make_nrml("""\
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
        sm = self._whatever_sourcemodel()
        with self.assertRaises(logictree.ValidationError) as arc:
            _TesteableLogicTree('lt', {'lt': lt, 'sm': sm}, 'base')
        exc = arc.exception
        self.assertEqual(exc.filename, 'lt')
        self.assertEqual(exc.basepath, 'base')
        self.assertEqual(exc.lineno, 22)
        error = "branch 'b1' already has child branchset"
        self.assertEqual(exc.message, error,
                        "wrong exception message: %s" % exc.message)

    def test_ab_gr_absolute_wrong_format(self):
        lt = self._make_nrml("""\
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
                                    branchSetID="bs1">
                  <logicTreeBranch branchID="b2">
                    <uncertaintyModel>123.45</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
                </logicTreeBranchSet>
              </logicTreeBranchingLevel>
            </logicTree>
        """)
        sm = self._whatever_sourcemodel()
        with self.assertRaises(logictree.ValidationError) as arc:
            _TesteableLogicTree('lt', {'lt': lt, 'sm': sm}, 'base')
        exc = arc.exception
        self.assertEqual(exc.filename, 'lt')
        self.assertEqual(exc.basepath, 'base')
        self.assertEqual(exc.lineno, 15)
        error = 'expected two float values separated by space'
        self.assertEqual(exc.message, error,
                        "wrong exception message: %s" % exc.message)

    def test_b_gr_relative_wrong_format(self):
        lt = self._make_nrml("""\
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
        sm = self._whatever_sourcemodel()
        with self.assertRaises(logictree.ValidationError) as arc:
            _TesteableLogicTree('lt', {'lt': lt, 'sm': sm}, 'base')
        exc = arc.exception
        self.assertEqual(exc.filename, 'lt')
        self.assertEqual(exc.basepath, 'base')
        self.assertEqual(exc.lineno, 15)
        self.assertEqual(exc.message, 'expected single float value',
                        "wrong exception message: %s" % exc.message)

    def test_source_model_invalid_xml(self):
        source = self._make_nrml("""\
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
        with self.assertRaises(logictree.ParsingError) as arc:
            _TesteableLogicTree('lt', {'lt': source, 'sm': sm}, 'base')
        exc = arc.exception
        self.assertEqual(exc.message, "Document is empty, line 1, column 1",
                        "wrong exception message: %s" % exc.message)

    def test_source_model_schema_violation(self):
        source = self._make_nrml("""\
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
        sm = self._make_nrml("""\
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
        with self.assertRaises(logictree.ParsingError) as arc:
            _TesteableLogicTree('lt', {'lt': source, 'sm': sm}, 'base')
        exc = arc.exception
        self.assertTrue("is not an element of the set" in exc.message,
                        "wrong exception message: %s" % exc.message)
