# Copyright (c) 2010-2012, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import os
import getpass
import mock
import unittest

from nose.plugins.attrib import attr

from openquake.engine import engine
from openquake.engine.calculators.hazard.disaggregation import core
from openquake.engine.db import models

from openquake.engine.tests.utils import helpers


class DisaggHazardCalculatorTestcase(unittest.TestCase):

    def setUp(self):
        self.job, self.calc = self._setup_a_new_calculator()
        models.JobStats.objects.create(oq_job=self.job, num_sites=0)

    def _setup_a_new_calculator(self):
        cfg = helpers.get_data_path('disaggregation/job.ini')
        job = helpers.get_job(cfg, username=getpass.getuser())
        calc = core.DisaggHazardCalculator(job)
        return job, calc

    @attr('slow')
    def test_workflow(self):
        # Test `pre_execute` to ensure that all stats are properly initialized.
        # Then test the core disaggregation function.
        self.calc.pre_execute()
        engine.save_job_stats(self.job)
        job_stats = models.JobStats.objects.get(oq_job=self.job.id)
        self.assertEqual(2, job_stats.num_sites)

        os.environ['OQ_NO_DISTRIBUTE'] = '1'
        try:
            # to test the disagg function, we first need to compute the hazard
            # curves
            self.calc.execute()
            # TODO: mock more
            base_path = \
                'openquake.engine.calculators.hazard.disaggregation.core'
            with mock.patch('%s.%s' % (base_path, '_save_disagg_matrix')
                            ) as save_mock:
                # Some of these tasks will not compute anything, since the
                # hazard  curves for these few are all 0.0s.
                # 2 poes * 2 imts * 2 sites = 8
                self.calc.post_execute()
                self.assertEqual(8, save_mock.call_count)
        finally:
            del os.environ['OQ_NO_DISTRIBUTE']
