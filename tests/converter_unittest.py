# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
Test of converter utility
"""

import logging
import os
import sys
import unittest

from openquake import converter
from utils import test
from openquake import flags
FLAGS = flags.FLAGS

NSHML_DIR = 'usgs-nshm'
NSHML_URL = "https://github.com/gem/usgs-nshm.git"

OUTPUT_DIR = 'output'

class ConverterTestCase(unittest.TestCase):
    """Tests converting NSHMP to NRML"""
    def setUp(self):
        self.dir = os.path.join(test.DATA_DIR, NSHML_DIR)
        self.file = os.path.join(test.DATA_DIR, OUTPUT_DIR)
        if not os.path.exists(self.file):
            os.makedirs(self.file)
        #test.guarantee_file(self.file, TEST_FILE_URL)
    
    # For coverage of the converter, please run demo_converter.sh
    @test.skipit
    def test_converter_output_is_nrml(self):
        input_path = self.dir
        
        # Extendable with plugins
        input_type = "openquake.parser.nshmp"
        output_type = "openquake.parser.nrml"
        __import__(input_type)
        __import__(output_type)
        input_module = sys.modules[input_type]
        output_module = sys.modules[output_type]
        
        output_path = self.file
        converter.convert(input_path, input_module,
                            output_path, output_module)
        
        self.assertTrue(True)


if __name__ == '__main__':
    sys.argv = FLAGS(sys.argv)
    logging.getLogger().setLevel(logging.DEBUG)
    unittest.main()
