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

# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
Performance testing of various xml parsers
"""

import logging
import os
import sys
import time
import unittest
from xml.etree import ElementTree
import xml.sax
from xml.sax import saxutils

import guppy
from lxml import etree

from utils import helpers
from openquake import flags
FLAGS = flags.FLAGS

TEST_FILE = 'large.xml'
TEST_FILE_URL = "http://gemsun02.ethz.ch/~jmckenty/large.xml"


class MySAXHandler(saxutils.XMLGenerator):
    def startElementNS(self, *_args, **_kw):
        pass
    def endElementNS(self, *_args, **_kw): 
        pass
    def startElement(self, *_args, **_kw): 
        pass
    def endElement(self, *_args, **_kw): 
        pass
    def startDocument(self, *_args, **_kw): 
        pass
    def endDocument(self, *_args, **_kw): 
        pass
    def startPrefixMapping(self, *_args, **_kw): 
        pass
    def endPrefixMapping(self, *_args, **_kw): 
        pass
    def characters(self, *_args, **_kw): 
        pass

class XMLSpeedTestCase(unittest.TestCase):
    """Tests parsing of large xml file using several methods"""
    def setUp(self):
        self.file = os.path.join(test.DATA_DIR, TEST_FILE)
        test.guarantee_file(self.file, TEST_FILE_URL)

    @test.timeit
    def test_lxml_iterparse(self):
        """Displays time and memory used for empty lxml parsing"""
        for _event, _element in etree.iterparse(self.file,
                                                  events=('start', 'end')):
            pass
        print guppy.hpy().heap()
    
    @helpers.skipit
    @test.timeit
    def test_native_iterparse(self):
        """Displays time and memory used for empty native parsing"""
        for _event, _element in ElementTree.iterparse(self.file,
                                                  events=('start', 'end')):
            # Do something here
            pass
        print guppy.hpy().heap()
    
    @test.timeit
    def test_native_sax(self):
        """Displays time and memory used for empty native sax parsing"""
        handler = MySAXHandler()
        xml.sax.parse(self.file, handler)
        print guppy.hpy().heap()

if __name__ == '__main__':
    sys.argv = FLAGS(sys.argv)
    logging.getLogger().setLevel(logging.DEBUG)
    unittest.main()