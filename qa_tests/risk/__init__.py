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
import tempfile
import numpy
import StringIO
import shutil

from qa_tests import _utils as qa_utils
from tests.utils import helpers

from openquake.engine import export
from openquake.engine.db import models


class BaseRiskQATestCase(qa_utils.BaseQATestCase):
    """
    Base abstract class for risk QA tests.
    """

    #: holds the path to a job.ini. Derived classes must define it
    risk_cfg = None

    def test(self):
        raise NotImplementedError

    def run_risk(self, cfg, hazard_id):
        """
        Given the path to job config file, run the job and assert that it was
        successful. If this assertion passes, return the completed job.

        :param str cfg:
            Path to a job config file.
        :param int hazard_id:
            ID of the hazard output used by the risk calculation
        :returns:
            The completed :class:`~openquake.engine.db.models.OqJob`.
        :raises:
            :exc:`AssertionError` if the job was not successfully run.
        """
        completed_job = helpers.run_risk_job(cfg, hazard_output_id=hazard_id)
        self.assertEqual('complete', completed_job.status)

        return completed_job

    def check_outputs(self, job):
        expected_data = self.expected_data()
        actual_data = self.actual_data(job)

        for i, actual in enumerate(actual_data):
            numpy.testing.assert_allclose(
                expected_data[i], actual,
                rtol=0.01, atol=0.0, err_msg="", verbose=True)

    def get_hazard(self):
        """
        :returns: an hazard job
        """
        raise NotImplementedError

    def _run_test(self):
        result_dir = tempfile.mkdtemp()

        try:
            risk_calc = os.getenv('PRELOADED_RISK', False)
            if not risk_calc:
                job = self.run_risk(
                    self.risk_cfg, self.hazard_id(self.get_hazard()))
            else:
                job = models.RiskCalculation.objects.get(
                    pk=risk_calc).oqjob_set.all()[0]

            self.check_outputs(job)

            if hasattr(self, 'expected_outputs'):
                expected_outputs = self.expected_outputs()
                for i, output in enumerate(self.actual_xml_outputs(job)):
                    try:
                        [exported_file] = export.risk.export(
                            output.id, result_dir)
                    except:
                        print "Error in exporting %s" % output
                        raise

                    msg = "not enough outputs (expected=%d, got=%s)" % (
                        len(expected_outputs), self.actual_xml_outputs(job))
                    assert i < len(expected_outputs), msg

                    self.assert_xml_equal(
                        StringIO.StringIO(expected_outputs[i]), exported_file)
        finally:
            shutil.rmtree(result_dir)

    def actual_xml_outputs(self, job):
        """
        Returns all the outputs produced by `job` that will be checked
        against expected data by `assert_xml_equal`. Default
        implementation is to consider all the outputs (it expects that
        all the outputs will and can be exported in XML).

        QA test may override this if they want to check outputs in
        format different than XML (like CSV).
        """
        return models.Output.objects.filter(oq_job=job).order_by('id')

    def actual_data(self, _job):
        """
        Derived QA tests must implement this in order to also check
        data stored on the database
        """
        return []

    def expected_data(self):
        """
        Derived QA tests must implement this in order to also check
        data stored on the database
        """
        return []

    def hazard_id(self, job):
        return job.output_set.latest('last_update').id


class End2EndRiskQATestCase(BaseRiskQATestCase):
    """
    Run an end-to-end calculation (by first running an hazard
    calculation, then running a risk calculation
    """

    def get_hazard(self):
        hazard_calc_id = os.getenv('PRELOADED_HAZARD', False)

        if hazard_calc_id:
            return models.HazardCalculation.objects.get(
                pk=hazard_calc_id).oqjob_set.all()[0]
        else:
            return super(End2EndRiskQATestCase, self).run_hazard(
                self.hazard_cfg, False).id


class LogicTreeBasedTestCase(object):
    """
    A class meant to mixed-in with a BaseRiskQATestCase or
    End2EndRiskQATestCase that runs a risk calculation by giving in
    input an hazard calculation id
    """

    def run_risk(self, cfg, hazard_id):
        """
        Given the path to job config file, run the job and assert that it was
        successful. If this assertion passes, return the completed job.

        :param str cfg:
            Path to a job config file.
        :param int hazard_id:
            ID of the hazard calculation used by the risk calculation
        :returns:
            The completed :class:`~openquake.engine.db.models.OqJob`.
        :raises:
            :exc:`AssertionError` if the job was not successfully run.
        """
        completed_job = helpers.run_risk_job(
            cfg, hazard_calculation_id=hazard_id)
        self.assertEqual('complete', completed_job.status)

        return completed_job

    def hazard_id(self, job):
        """
        :returns: the hazard calculation id for the given `job`
        """
        return job.hazard_calculation.id


class CompleteTestCase(object):
    """
    A class to be mixed-in with a RiskQATest. It redefines the
    protocol in order to check every output (stored in the db) of a
    calculation apart the ones that satisfy #should_skip
    """

    # a sentinal symbol to highlight the fact that we are not checking
    # the value of an existing output
    DO_NOT_CHECK = None

    def check_outputs(self, job):
        for output in job.output_set.all():
            if self.should_skip(output):
                continue
            container = output.output_container
            expected_data = self.expected_output_data()

            for item in container:
                if not item.data_hash in expected_data:
                    raise AssertionError(
                        "The output with hash %s is missing" % str(
                            item.data_hash))
                expected_output = expected_data[item.data_hash]
                if expected_output is not None:
                    expected_output.assertAlmostEqual(item)

    def expected_output_data(self):
        """
        :returns:
            an iterable over data objects (e.g. LossCurveData)
        """
        raise NotImplementedError
