import os
import unittest
from openquake.nrmllib.writers import tostring, StreamingXMLWriter
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
        self.assertLess(allocated, 102400)  # < 100 KB
