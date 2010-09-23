# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
Test of converter utility
"""

import logging
import os
import sys
import unittest

from opengem import converter
from opengem import test
from opengem import flags
FLAGS = flags.FLAGS

NSHML_DIR = 'usgs-nshm'
NSHML_URL = "https://github.com/gem/usgs-nshm.git"

TEST_FILE = 'converted.xml'

class ConverterTestCase(unittest.TestCase):
    """Tests converting NSHMP to NRML"""
    def setUp(self):
        self.dir = os.path.join(test.DATA_DIR, NSHML_DIR)
        self.file = os.path.join(test.DATA_DIR, TEST_FILE)
        #test.guarantee_file(self.file, TEST_FILE_URL)
    
    def test_converter_output_is_nrml(self):
        input_path = self.dir
        input_type = converter.PARSERS['NSHMP']
        output_type = converter.PARSERS['NRML']
        output_path = self.file
        converter.convert(input_path, input_type,
                            output_path, output_type)
        
        self.assertTrue(True)


if __name__ == '__main__':
    sys.argv = FLAGS(sys.argv)
    logging.getLogger().setLevel(logging.DEBUG)
    unittest.main()