"""
Test the output of Loss Curve and Loss Ratio Curve as XML.

"""


import os
import unittest

import lxml
from lxml import etree

from opengem import test
from opengem import logs
from opengem import test
from opengem import xml

log = logs.LOG

XML_TEST_DIRECTORY= "schema"
SCHEMA_FILE = 'nrml.xsd'

data_dir = os.path.join(os.path.dirname(__file__), 'data')
schema_dir = os.path.join(os.path.dirname(__file__), '../docs/schema')

    
class SchemaValidationTestCase(unittest.TestCase):
    """Confirm that all XML examples match schema."""
    
    def setUp(self):
        self.example_dir = os.path.join(data_dir, XML_TEST_DIRECTORY)
        self.schema_path = os.path.join(schema_dir, SCHEMA_FILE)
        
    def test_xml_is_valid(self):
        # Test that the doc matches the schema
        xmlschema = etree.XMLSchema(etree.parse(self.schema_path))
        filenames = os.listdir(self.example_dir)
        for xml_example in filenames:
            example_path = os.path.join(self.example_dir, xml_example)
            xml_doc = etree.parse(example_path)
            loaded_xml = xml_doc.getroot()
            try:
                xmlschema.assertValid(xml_doc)
            except etree.DocumentInvalid, e:
                print "Invalid doc %s" % example_path
                raise e