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
    def test_nonexisting_logic_tree(self):
        with self.assertRaises(logictree.ParsingError) as arc:
            _TesteableLogicTree('missing_file', {}, 'base')
        exc = arc.exception
        self.assertEqual(exc.filename, 'missing_file')
        self.assertEqual(exc.basepath, 'base')
        error = "[Errno 2] No such file or directory: 'base/missing_file'"
        self.assertEqual(exc.message, error,
                         "wrong exception message: %s" % exc.message)

    def test_invalid_xml_logic_tree(self):
        source = """<?xml foo bar baz"""
        with self.assertRaises(logictree.ParsingError) as arc:
            _TesteableLogicTree('broken_xml', {'broken_xml': source}, 'base')
        exc = arc.exception
        self.assertEqual(exc.filename, 'broken_xml')
        self.assertEqual(exc.basepath, 'base')
        self.assertTrue(exc.message.startswith('Malformed declaration'),
                        "wrong exception message: %s" % exc.message)

    def _make_nrml(self, content):
        return """
<nrml xmlns:gml="http://www.opengis.net/gml"
      xmlns="http://openquake.org/xmlns/nrml/0.2"
      gml:id="n1">
    %s
</nrml>""" % content

    def test_schema_violation(self):
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
