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
Ensure that example instance documents validate against NRML schema.
Only check for "new" NRML schema (version 0.2).
"""

import os
import unittest

from lxml import etree
from utils import helpers
from openquake import logs

log = logs.LOG

XML_TEST_DIRECTORY= 'examples'
SCHEMA_FILE = 'nrml.xsd'

class SchemaValidationTestCase(unittest.TestCase):
    """Confirm that all XML examples in docs/schema/examples match schema."""
    
    def setUp(self):
        self.example_dir = os.path.join(helpers.SCHEMA_DIR, XML_TEST_DIRECTORY)
        self.schema_path = os.path.join(helpers.SCHEMA_DIR, SCHEMA_FILE)
        
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
