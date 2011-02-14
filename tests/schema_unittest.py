# -*- coding: utf-8 -*-
"""
Ensure that example instance documents validate against NRML schema.
Only check for "new" NRML schema (version 0.2).
"""

import os
import unittest

from lxml import etree
from openquake import test
from openquake import logs

log = logs.LOG

XML_TEST_DIRECTORY= 'examples'
SCHEMA_FILE = 'nrml.xsd'

class SchemaValidationTestCase(unittest.TestCase):
    """Confirm that all XML examples in docs/schema/examples match schema."""
    
    def setUp(self):
        self.example_dir = os.path.join(test.SCHEMA_DIR, XML_TEST_DIRECTORY)
        self.schema_path = os.path.join(test.SCHEMA_DIR, SCHEMA_FILE)
        
    def test_xml_is_valid(self):
        """Assert that the instance documents in the example directory
        validate against the schema."""
        xmlschema = etree.XMLSchema(etree.parse(self.schema_path))
        filenames = os.listdir(self.example_dir)
        for xml_example in filenames:

            # only validate files with .xml extension, and ignore those
            # that start with a dot character
            if ((not xml_example.endswith(".xml")) or 
                xml_example.startswith(".")):
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