"""
Test the output of Loss Curve, Loss Ratio Curve and Hazard Curves as XML.

"""


import os
import unittest

from lxml import etree
from opengem import test
from opengem import logs

log = logs.LOG

XML_TEST_DIRECTORY= "examples"
SCHEMA_FILE = 'nrml.xsd'


class SchemaValidationTestCase(unittest.TestCase):
    """Confirm that all XML examples match schema."""
    
    def setUp(self):
        self.example_dir = os.path.join(test.SCHEMA_DIR, XML_TEST_DIRECTORY)
        self.schema_path = os.path.join(test.SCHEMA_DIR, SCHEMA_FILE)
        
    def test_xml_is_valid(self):
        # Test that the doc matches the schema
        xmlschema = etree.XMLSchema(etree.parse(self.schema_path))
        filenames = os.listdir(self.example_dir)
        for xml_example in filenames:
            if xml_example[:1] == ".":
                continue
            example_path = os.path.join(self.example_dir, xml_example)
            if os.path.isdir(example_path):
                continue
            xml_doc = etree.parse(example_path)
            loaded_xml = xml_doc.getroot()
            try:
                xmlschema.assertValid(xml_doc)
            except etree.DocumentInvalid, e:
                print "Invalid doc %s" % example_path
                raise e