# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
Performance testing of various xml parsers
"""


import os
import subprocess
import time
import unittest
from xml.etree import ElementTree
from lxml import etree
from xml.sax import saxutils
import xml.sax

import guppy 

TEST_FILE = 'large.xml'
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


def timeit(method):
    """Decorator for timing methods"""
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()

        print '%r (%r, %r) %2.2f sec' % \
              (method.__name__, args, kw, te-ts)
        return result

    return timed    

def skipit(method):
    def skipme(*args, **kw):
        pass
    return skipme


class MySAXHandler(saxutils.XMLGenerator):
    def startElementNS(*_args, **_kw): pass
    def endElementNS(*_args, **_kw): pass
    def startElement(*_args, **_kw): pass
    def endElement(*_args, **_kw): pass
    def startDocument(*_args, **_kw): pass
    def endDocument(*_args, **_kw): pass
    def startPrefixMapping(*_args, **_kw): pass
    def endPrefixMapping(*_args, **_kw): pass
    def characters(*_args, **_kw): pass

class XMLSpeedTestCase(unittest.TestCase):
    def setUp(self):
        self.file = os.path.join(DATA_DIR, TEST_FILE)
        if not os.path.isfile(self.file):
            subprocess.call(["curl", "-O", "http://gemsun02.ethz.ch/~jmckenty/large.xml", "-o", self.file])

    @timeit
    def test_lxml_iterparse(self):
        for event, element in etree.iterparse(self.file,
                                                  events=('start', 'end')):
            # Do something here
            pass
        h = guppy.hpy()
        print h.heap()
    
    @skipit
    @timeit
    def test_native_iterparse(self):
        for event, element in ElementTree.iterparse(self.file,
                                                  events=('start', 'end')):
            # Do something here
            pass
        h = guppy.hpy()
        print h.heap()
    
    @timeit
    def test_native_sax(self):
        handler = MySAXHandler()
        xml.sax.parse(self.file, handler)
        h = guppy.hpy()
        print h.heap()

if __name__ == '__main__':
    unittest.main()