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


from openquake.calculators.hazard.uhs.ath import completed_task_count
from openquake.calculators.hazard.uhs.ath import remaining_tasks_in_block
from openquake.utils import stats

from tests.calculators.hazard.uhs.core_test import UHSBaseTestCase


class UHSTaskHandlerTestCase(UHSBaseTestCase):
    """Tests for functionality related to the asynchronous task handler code,
    which is used by the mini-framework
    :function:`openquake.utils.tasks.distribute`.
    """

    def test_completed_task_count_no_stats(self):
        # Test `complete_task_count` with no counters set;
        # it should just return 0.
        self.assertEqual(0, completed_task_count(self.job_id))

    def test_complete_task_count_success(self):
        stats.pk_inc(self.job_id, "nhzrd_done")
        self.assertEqual(1, completed_task_count(self.job_id))

    def test_complete_task_count_failures(self):
        stats.pk_inc(self.job_id, "nhzrd_failed")
        self.assertEqual(1, completed_task_count(self.job_id))

    def test_complete_task_count_success_and_fail(self):
        # Test `complete_task_count` with success and fail counters:
        stats.pk_inc(self.job_id, "nhzrd_done")
        stats.pk_inc(self.job_id, "nhzrd_failed")
        self.assertEqual(2, completed_task_count(self.job_id))

    def test_remaining_tasks_in_block(self):
        # Tasks should be submitted to works for one block (of sites) at a
        # time. For each block, we want to look at Redis counters to determine
        # when the block is finished calculating.
        # `remaining_tasks_in_block` is a generator that yields the remaining
        # number of tasks in a block. When there are no more tasks left in the
        # block, a `StopIteration` is raised.
        gen = remaining_tasks_in_block(self.job_id, 4, 0)

        incr_count = lambda: stats.pk_inc(self.job_id, "nhzrd_done")

        self.assertEqual(4, gen.next())
        incr_count()
        self.assertEqual(3, gen.next())
        incr_count()
        incr_count()
        self.assertEqual(1, gen.next())
        incr_count()
        self.assertRaises(StopIteration, gen.next)

    def test_remaining_tasks_in_block_nonzero_start_count(self):
        # Same as the above test, except test with the start_count
        # set to something > 0 (to simulate a mid-calculation block).

        incr_count = lambda: stats.pk_inc(self.job_id, "nhzrd_done")

        # Just for variety, set 5 successful and 5 failed task counters:
        for _ in xrange(5):
            stats.pk_inc(self.job_id, "nhzrd_done")
        for _ in xrange(5):
            stats.pk_inc(self.job_id, "nhzrd_failed")

        # count starts at 10
        gen = remaining_tasks_in_block(self.job_id, 4, 10)

        self.assertEqual(4, gen.next())
        incr_count()
        self.assertEqual(3, gen.next())
        incr_count()
        incr_count()
        self.assertEqual(1, gen.next())
        incr_count()
        self.assertRaises(StopIteration, gen.next)
