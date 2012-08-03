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


import getpass
import unittest

from openquake.db import models
from openquake.calculators.hazard.event_based import core_next

from tests.utils import helpers


class EventBasedHazardCalculatorTestCase(unittest.TestCase):
    """
    Tests for the core functionality of the event-based hazard calculator.
    """

    def setUp(self):
        cfg = helpers.demo_file('event_based_hazard/job.ini')
        self.job = helpers.get_hazard_job(cfg, username=getpass.getuser())
        self.calc = core_next.EventBasedHazardCalculator(self.job)

    def test_stochastic_event_sets_task(self):
        self.calc.pre_execute()
        self.job.is_running = True
        self.job.status = 'executing'
        self.job.save()

        hc = self.job.hazard_calculation

        rlz1, rlz2 = models.LtRealization.objects.filter(
            hazard_calculation=hc.id)

        rlz1_src_prog = models.SourceProgress.objects.filter(
            lt_realization=rlz1.id)
        rlz1_src_ids = [src.parsed_source.id for src in rlz1_src_prog]
        core_next.stochastic_event_sets(self.job.id, rlz1.id, rlz1_src_ids)
        self.assertTrue(False)
