import os
import unittest
from cStringIO import StringIO
from openquake.commonlib.writers import tostring, StreamingXMLWriter
from openquake.commonlib.node import LiteralNode
from lxml import etree


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
