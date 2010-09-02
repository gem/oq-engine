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

from opengem import test
from opengem import flags
FLAGS = flags.FLAGS

TEST_FILE = 'large.xml'
TEST_FILE_URL = "http://gemsun02.ethz.ch/~jmckenty/large.xml"


def timeit(method):
    """Decorator for timing methods"""
    def _timed(*args, **kw):
        timestart = time.time()
        result = method(*args, **kw)
        timeend = time.time()

        print '%r (%r, %r) %2.2f sec' % \
              (method.__name__, args, kw, timeend-timestart)
        return result

    return _timed    

def skipit(_method):
    """Decorator for skipping tests"""
    def _skipme(*_args, **_kw):
        pass
    return _skipme


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

    @timeit
    def test_lxml_iterparse(self):
        """Displays time and memory used for empty lxml parsing"""
        for _event, _element in etree.iterparse(self.file,
                                                  events=('start', 'end')):
            pass
        print guppy.hpy().heap()
    
    @skipit
    @timeit
    def test_native_iterparse(self):
        """Displays time and memory used for empty native parsing"""
        for _event, _element in ElementTree.iterparse(self.file,
                                                  events=('start', 'end')):
            # Do something here
            pass
        print guppy.hpy().heap()
    
    @timeit
    def test_native_sax(self):
        """Displays time and memory used for empty native sax parsing"""
        handler = MySAXHandler()
        xml.sax.parse(self.file, handler)
        print guppy.hpy().heap()

if __name__ == '__main__':
    sys.argv = FLAGS(sys.argv)
    logging.getLogger().setLevel(logging.DEBUG)
    unittest.main()