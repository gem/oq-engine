# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2017 GEM Foundation
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
import unittest
import tempfile
from io import BytesIO
from openquake.baselib.performance import memory_info
from openquake.commonlib.writers import write_csv
from openquake.baselib.node import Node, tostring, StreamingXMLWriter
from xml.etree import ElementTree as etree

import numpy


def assetgen(n):
    "Generate n assets for testing purposes"
    for i in range(n):
        asset = etree.Element(
            'asset',  dict(id=str(i), number='10', taxonomy='TAXO'))
        etree.SubElement(
            asset, 'location', dict(lon='10.1', lat='40.9'))
        yield asset


class StreamingXMLWriterTestCase(unittest.TestCase):
    def test_tostring(self):
        nrml = etree.Element(
            'nrml', {'xmlns': 'http://openquake.org/xmlns/nrml/0.4'})
        em = etree.SubElement(
            nrml, 'exposureModel',
            {'id': "my_exposure_model_for_population",
             'category': "population",
             'taxonomySource': "fake population datasource"})

        descr = etree.SubElement(em, 'description')
        descr.text = 'Sample population'
        etree.SubElement(em, 'assets')
        self.assertEqual(tostring(nrml), b'''\
<nrml
xmlns="http://openquake.org/xmlns/nrml/0.4"
>
    <exposureModel
    category="population"
    id="my_exposure_model_for_population"
    taxonomySource="fake population datasource"
    >
        <description>
            Sample population
        </description>
        <assets />
    </exposureModel>
</nrml>
''')

    def test_memory(self):
        # make sure the memory occupation is low
        # (to protect against bad refactoring of the XMLWriter)
        try:
            import psutil
        except ImportError:
            raise unittest.SkipTest('psutil not installed')
        proc = psutil.Process(os.getpid())
        try:
            rss = memory_info(proc).rss
        except psutil.AccessDenied:
            raise unittest.SkipTest('Memory info not accessible')
        devnull = open(os.devnull, 'wb')
        with StreamingXMLWriter(devnull) as writer:
            for asset in assetgen(1000):
                writer.serialize(asset)
        allocated = memory_info(proc).rss - rss
        self.assertLess(allocated, 204800)  # < 200 KB

    def test_zero_node(self):
        s = BytesIO()
        node = Node('zero', {}, 0)
        with StreamingXMLWriter(s) as writer:
            writer.serialize(node)
        self.assertEqual(s.getvalue(), b'''\
<?xml version="1.0" encoding="utf-8"?>
<zero>
    0
</zero>
''')

I32 = numpy.int32


class WriteCsvTestCase(unittest.TestCase):
    def assert_export(self, array, expected, header=None):
        fname = tempfile.NamedTemporaryFile().name
        write_csv(fname, array, header=header)
        with open(fname) as f:
            txt = f.read()
        self.assertEqual(txt, expected)

    def test_simple(self):
        a = numpy.array([[1, 2], [3, 4]])
        self.assert_export(a, '1,2\n3,4\n')

    def test_header(self):
        a = numpy.array([[1, 2], [3, 4]])
        self.assert_export(a, 'a,b\n1,2\n3,4\n', header='ab')

    def test_flat(self):
        imt_dt = numpy.dtype([('PGA', I32, 3), ('PGV', I32, 4)])
        a = numpy.array([([1, 2, 3], [4, 5, 6, 7])], imt_dt)
        self.assert_export(a, 'PGA:int32:3,PGV:int32:4\n1 2 3,4 5 6 7\n')

    def test_nested(self):
        imt_dt = numpy.dtype([('PGA', I32, 3), ('PGV', I32, 4)])
        gmf_dt = numpy.dtype([('A', imt_dt), ('B', imt_dt),
                              ('idx', I32)])
        a = numpy.array([(([1, 2, 3], [4, 5, 6, 7]),
                          ([1, 2, 4], [3, 5, 6, 7]), 8)], gmf_dt)
        self.assert_export(
            a, 'A~PGA:int32:3,A~PGV:int32:4,B~PGA:int32:3,B~PGV:int32:4,'
            'idx:int32\n1 2 3,4 5 6 7,1 2 4,3 5 6 7,8\n')
