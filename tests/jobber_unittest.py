# vim: tabstop=4 shiftwidth=4 softtabstop=4

import unittest
JOBBER_CONFIG_FILE = 'basic-job.yml'

data_dir = os.path.join(os.path.dirname(__file__), 'data')


class JobberTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_parses_job_config(self):
        # Load config file
        config_path = os.path.join(data_dir, JOBBER_CONFIG_FILE)
        
