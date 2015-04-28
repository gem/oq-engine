import os
import unittest
import tempfile
from cStringIO import StringIO
from openquake.commonlib.writers import tostring, StreamingXMLWriter, write_csv
from openquake.commonlib.node import LiteralNode
from lxml import etree

import numpy


def assetgen(n):
    "Generate n assets for testing purposes"
    for i in xrange(n):
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
        self.assertEqual(tostring(nrml), '''\
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
            rss = proc.get_memory_info().rss
        except psutil.AccessDenied:
            raise unittest.SkipTest('Memory info not accessible')
        devnull = open(os.devnull, 'w')
        with StreamingXMLWriter(devnull) as writer:
            for asset in assetgen(1000):
                writer.serialize(asset)
        allocated = proc.get_memory_info().rss - rss
        self.assertLess(allocated, 204800)  # < 200 KB

    def test_zero_node(self):
        s = StringIO()
        node = LiteralNode('zero', {}, 0)
        with StreamingXMLWriter(s) as writer:
            writer.serialize(node)
        self.assertEqual(s.getvalue(), '''\
<?xml version="1.0" encoding="utf-8"?>
<zero>
    0
</zero>
''')


class WriteCsvTestCase(unittest.TestCase):
    def assert_export(self, array, expected):
        with tempfile.NamedTemporaryFile(mode='r+') as f:
            write_csv(f.name, array)
            f.seek(0)
            txt = f.read()
        self.assertEqual(txt, expected)

    def test_simple(self):
        a = numpy.array([[1, 2], [3, 4]])
        self.assert_export(a, '1,2\n3,4\n')

    def test_flat(self):
        imt_dt = numpy.dtype([('PGA', int, 3), ('PGV', int, 4)])
        a = numpy.array([([1, 2, 3], [4, 5, 6, 7])], imt_dt)
        self.assert_export(a, 'PGV:int64:4,PGA:int64:3\n4 5 6 7,1 2 3\n')

    def test_nested(self):
        imt_dt = numpy.dtype([('PGA', int, 3), ('PGV', int, 4)])
        gmf_dt = numpy.dtype([('A', imt_dt), ('B', imt_dt),
                              ('idx', numpy.uint32)])
        a = numpy.array([(([1, 2, 3], [4, 5, 6, 7]),
                          ([1, 2, 4], [3, 5, 6, 7]), 8)], gmf_dt)
        self.assert_export(
            a, 'A-PGV:int64:4,A-PGA:int64:3,B-PGV:int64:4,B-PGA:int64:3,'
            'idx:uint32:\n4 5 6 7,1 2 3,3 5 6 7,1 2 4,8\n')
