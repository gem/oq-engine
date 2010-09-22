# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
Test of converter utility
"""

import logging
import os
import sys
import unittest

from opengem import test
from opengem import flags
FLAGS = flags.FLAGS

NSHML_DIR = 'usgs-nshm'
NSHML_URL = "https://github.com/gem/usgs-nshm.git"



class ConverterTestCase(unittest.TestCase):
    """Tests converting NSHMP to NRML"""
    def setUp(self):
        self.dir = os.path.join(test.DATA_DIR, NSHML_DIR)
        #test.guarantee_file(self.file, TEST_FILE_URL)


if __name__ == '__main__':
    sys.argv = FLAGS(sys.argv)
    logging.getLogger().setLevel(logging.DEBUG)
    unittest.main()