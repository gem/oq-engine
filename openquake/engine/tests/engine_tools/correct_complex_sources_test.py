import os
import unittest
from openquake.hazardlib import nrml, sourceconverter, InvalidFile


class CorrectComplexSourceTestCase(unittest.TestCase):
    def test(self):
        fname = os.path.join(os.path.dirname(__file__),
                             'faults_backg_source_model.xml')
        converter = sourceconverter.SourceConverter()
        with self.assertRaises(InvalidFile):
            nrml.SourceModelParser(converter).parse_groups(fname)
