#!/usr/bin/env python
# encoding: utf-8
"""
This modules serializes hazard curves in Shaml format.
"""

from lxml import etree

from opengem import writer
from opengem.xml import SHAML_NS, GML_NS

XML_METADATA = '<?xml version="1.0" encoding="UTF-8"?>'

HEADER = """
<shaml:HazardResultList xmlns:shaml="%s" xmlns:gml="%s">
""" % (SHAML_NS, GML_NS)

FOOTER = """</shaml:HazardResultList>
"""

class ShamlWriter(writer.FileWriter):
    
    def __init__(self, path):
        super(ShamlWriter, self).__init__(path)

    def init_file(self):
        super(ShamlWriter, self).init_file()
        
        self.file.write(XML_METADATA)
        self.file.write(HEADER)

    def close(self):
        self.file.write(FOOTER)
        super(ShamlWriter, self).close()
