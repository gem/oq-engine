# Copyright (c) 2010-2012, GEM Foundation.
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


import ConfigParser
import getpass
import os
import unittest

from openquake.db.models import OqCalculation
from openquake.db.models import OqUser
from openquake.db.models import Output

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


class CalculationUserAssociation(unittest.TestCase):
    """Tests related to association of the current (shell) user with
    calculation and result artifacts."""

    def test_full_calc_user_assoc(self):
        # Run a full calculation in the same as other QA tests (using
        # `subprocess` to invoke bin/openquake) and check the following:
        # 1. There is an OqUser record for the current user.
        # 2. This user is the owner of all OqJobProfile, OqCalculation,
        #    and Ouput records.
        cfg_path = demo_file('uhs/config.gem')

        run_job(cfg_path)

        # Get the OqUser for the current user
        user = OqUser.objects.get(user_name=getpass.getuser())

        calculation = OqCalculation.objects.latest('id')
        job_profile = calculation.oq_job_profile

        self.assertEqual(user, calculation.owner)
        self.assertEqual(user, job_profile.owner)

        outputs = Output.objects.filter(oq_calculation=calculation.id)
        # We need at least 1 output record, otherwise this test is useless:
        self.assertTrue(len(outputs) > 0)
        for output in outputs:
            self.assertEqual(user, output.owner)
