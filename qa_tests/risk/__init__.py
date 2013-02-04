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

import tempfile
import numpy
import StringIO
import shutil

from qa_tests import _utils as qa_utils
from tests.utils import helpers

from openquake import export
from openquake.db import models


class BaseRiskQATestCase(qa_utils.BaseQATestCase):
    """
    Base abstract class for risk QA tests. Derived class must define

    0) a test method (properly annotated) that executes run_test
    1) a cfg property holding the path to job.ini to execute
    2) a method hazard_id() that creates a proper hazard input
    3) a method actual_data that gets a list of
       individual risk output (e.g. a `openquake.db.models.LossCurveData`)
    4) a method expected_data to assert against the actual_data
    5) a method actual_outputs that gets a list of the created risk
       `openquake.db.models.Output`
    6) a method expected_outputs to assert against the actual_outputs
    """

    def run_risk(self, cfg, hazard_id):
        """
        Given the path to job config file, run the job and assert that it was
        successful. If this assertion passes, return the completed job.

        :param str cfg:
            Path to a job config file.
        :param int hazard_id:
            ID of the hazard output used by the risk calculation
        :returns:
            The completed :class:`~openquake.db.models.OqJob`.
        :raises:
            :exc:`AssertionError` if the job was not successfully run.
        """
        job_status = helpers.run_risk_job_sp(cfg, hazard_id, silence=True)
        self.assertEqual(0, job_status)

        completed_job = models.OqJob.objects.latest('last_update')
        self.assertEqual('complete', completed_job.status)
        return completed_job

    def _run_test(self):
        result_dir = tempfile.mkdtemp()

        try:
            expected_data = self.expected_data()
            job = self.run_risk(self.cfg, self.hazard_id())

            actual_data = self.actual_data(job)

            for i, actual in enumerate(actual_data):
                numpy.testing.assert_allclose(
                    expected_data[i], actual,
                    rtol=0.01, atol=0.0, err_msg="", verbose=True)

            expected_outputs = self.expected_outputs()

            for i, output in enumerate(models.Output.objects.filter(
                    oq_job=job).order_by('id')):
                [exported_file] = export.risk.export(output.id, result_dir)
                self.assert_xml_equal(
                    StringIO.StringIO(expected_outputs[i]), exported_file)
        finally:
            shutil.rmtree(result_dir)
