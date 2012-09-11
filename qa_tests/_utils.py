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

import unittest

from openquake import engine2
from tests.utils import helpers


class BaseQATestCase(unittest.TestCase):
    """
    Base QA test case class with some general functionality built in for
    running QA tests.
    """

    def run_hazard(self, cfg, exports=None):
        """
        Given the path to job config file, run the job and assert that it was
        successful. If this assertion passes, return the completed job.

        :param str cfg:
            Path to a job config file.
        :param list exports:
            A list of export format types. Currently only 'xml' is supported.
        :returns:
            The completed :class:`~openquake.db.models.OqJob`.
        :raises:
            :exc:`AssertionError` if the job was not successfully run.
        """
        if exports is None:
            exports = []

        job = helpers.get_hazard_job(cfg)
        completed_job = engine2._do_run_hazard(job, exports)

        self.assertFalse(completed_job.is_running)
        self.assertEqual('complete', completed_job.status)
        return completed_job
