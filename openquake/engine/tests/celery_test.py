#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2016, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import os
import mock
import unittest
import subprocess

from openquake.qa_tests_data.classical import case_3

CELERYCONFIGDIR = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(__file__))))


class CeleryTestCase(unittest.TestCase):
    def setUp(self):
        if not os.path.exists('/usr/bin/celery'):
            raise unittest.SkipTest
        self.cel = subprocess.Popen(['/usr/bin/celery', 'worker'],
                                    cwd=CELERYCONFIGDIR)

    def _test_ok(self):
        with mock.patch.dict(os.environ, OQ_DISTRIBUTE='celery'):
            from openquake.commonlib import readinput
            from openquake.calculators import base
            oq = readinput.get_oqparam('job.ini', case_3)
            base.calculators(oq).run()

    def test_wrong_import(self):
        from openquake.commonlib import readinput
        from openquake.calculators import base
        with mock.patch.dict(os.environ, OQ_DISTRIBUTE='celery'):
            oq = readinput.get_oqparam('job.ini', case_3)
            base.calculators(oq).run()

    def tearDown(self):
        self.cel.kill()
