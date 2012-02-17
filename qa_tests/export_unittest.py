import ConfigParser
import os
import unittest

from openquake.db.models import OqCalculation

from tests.utils.helpers import demo_file
from tests.utils.helpers import run_job


class CalculationDescriptionTestCase(unittest.TestCase):
    """Test running a calculation with a DESCRIPTION specified in the config"""

    def test_run_calc_with_description(self):
        # Test importing and running a job with a config containing the
        # optional DESCRIPTION parameter.

        description = 'Classical PSHA hazard test description'

        orig_cfg_path = demo_file('PeerTestSet1Case2/config.gem')
        mod_cfg_path = os.path.join(demo_file('PeerTestSet1Case2'),
                                    'modified_config.gem')

        # Use ConfigParser to add the DESCRIPTION param to an existing config
        # profile and write a new temporary config file:
        cfg_parser = ConfigParser.ConfigParser()
        cfg_parser.readfp(open(orig_cfg_path, 'r'))
        cfg_parser.set('general', 'DESCRIPTION', description) 
        cfg_parser.write(open(mod_cfg_path, 'w'))

        run_job(mod_cfg_path)
        calculation = OqCalculation.objects.latest('id')
        job_profile = calculation.oq_job_profile

        self.assertEqual(description, job_profile.description)
        self.assertEqual(description, calculation.description)

        # Clean up the temporary config file:
        os.unlink(mod_cfg_path)
