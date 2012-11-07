# coding=utf-8
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

import shutil
import unittest
import tempfile
import StringIO

from nrml.risk import writers


class LossCurveXMLWriterTestCase(unittest.TestCase):

    def setUp(self):
        _, self.path = tempfile.mkstemp()

    def tearDown(self):
        shutil.rmtree(self.path, ignore_errors=True)

    def test_serialize_an_empty_model(self):
        expected = StringIO.StringIO("""<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml" xmlns="http://openquake.org/xmlns/nrml/0.4"/>
""")

        writer = writers.LossCurveXMLWriter(self.path)
        writer.serialize([])

        self.assertEqual(expected.readlines(),
            open(self.path, 'r').readlines())
