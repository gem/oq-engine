# Copyright (c) 2013, GEM Foundation.
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
from nose.plugins.attrib import attr
from qa_tests import _utils as qa_utils
from openquake.engine.db import models

from openquake.engine.calculators.hazard.event_based.core import \
    EventBasedHazardCalculator


# test independence from the parameter concurrent_tasks
class EventBasedHazardTestCase(qa_utils.BaseQATestCase):
    expected_tags = ['rlz=00|ses=0001|src=1|i=000',
                     'rlz=00|ses=0001|src=1|i=001',
                     'rlz=00|ses=0001|src=1|i=002',
                     'rlz=00|ses=0001|src=1|i=003',
                     'rlz=00|ses=0001|src=1|i=004',
                     'rlz=00|ses=0001|src=1|i=005',
                     'rlz=00|ses=0001|src=2|i=000']

    @attr('qa', 'hazard', 'event_based')
    def test_64(self):
        tags_64 = self.run_with_concurrent_tasks(64)
        self.assertEqual(tags_64, self.expected_tags)

    def test_3(self):
        tags_3 = self.run_with_concurrent_tasks(3)
        self.assertEqual(tags_3, self.expected_tags)

    def run_with_concurrent_tasks(self, n):
        orig = EventBasedHazardCalculator.concurrent_tasks.im_func
        EventBasedHazardCalculator.concurrent_tasks = lambda self: n
        try:
            cfg = os.path.join(os.path.dirname(__file__), 'job.ini')
            job = self.run_hazard(cfg)
            tags = map(str, models.SESRupture.objects.filter(
                ses__ses_collection__output__oq_job=job.id
                ).values_list('tag', flat=True))
        finally:
            EventBasedHazardCalculator.concurrent_tasks = orig
        return tags
