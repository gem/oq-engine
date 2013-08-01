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
import os
import sys
import warnings
from unittest.case import SkipTest
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

    def _test_path(self, relative_path):
        return os.path.join(os.path.dirname(
            sys.modules[self.__class__.__module__].__file__),
            relative_path)

    #: QA test must override this params to feed the risk job with
    #: the proper hazard output
    output_type = "hazard_curve"

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

        # assert actual_data, 'Got no actual data!'

        for i, actual in enumerate(actual_data):
            numpy.testing.assert_allclose(
                expected_data[i], actual,
                rtol=0.01, atol=0.0, err_msg="", verbose=True)

    def get_hazard_job(self):
        """
        :returns: a hazard job
        """
        raise NotImplementedError

    def _run_test(self):
        result_dir = tempfile.mkdtemp()

        try:
            job = self.run_risk(
                self._test_path('job_risk.ini'),
                self.hazard_id(self.get_hazard_job()))

            self.check_outputs(job)

            if hasattr(self, 'expected_outputs'):
                expected_outputs = self.expected_outputs()
                for i, output in enumerate(self.actual_xml_outputs(job)):
                    try:
                        exported_file = export.risk.export(
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

        return job

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
        return job.output_set.filter(
            output_type=self.output_type).latest('last_update').id


class LogicTreeBasedTestCase(object):
    """
    A class meant to mixed-in with a BaseRiskQATestCase
    that runs a risk calculation by giving in input a hazard calculation id
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

    items_per_output = 10

    def check_outputs(self, job):
        outputs = []

        for output in job.output_set.all():
            for item in list(output.output_container)[0:self.items_per_output]:
                outputs.append((item.data_hash, item))

        outputs = dict(outputs)

        for data_hash, expected_output in self.expected_output_data():
            if not data_hash in outputs:
                found = filter(lambda o: o[0] == data_hash[0], outputs)
                raise AssertionError(
                    "The output with hash %s is missing. Found %s" % (
                        str(data_hash), found))
            actual_output = outputs[data_hash]
            try:
                expected_output.assertAlmostEqual(actual_output)
            except AssertionError:
                print "Problems with output %s" % str(data_hash)
                raise

    def _csv(self, filename, *slicer, **kwargs):
        dtype = kwargs.get('dtype', float)
        path = self._test_path("expected/%s.csv" % filename)
        return numpy.genfromtxt(path, dtype, delimiter=",")[slicer]

    def expected_output_data(self):
        """
        :returns:
            an iterable over data objects (e.g. LossCurveData)
        """
        return ()


class FixtureBasedQATestCase(LogicTreeBasedTestCase, BaseRiskQATestCase):
    """
    Run a risk calculation by relying on some preloaded data
    (fixtures) to be present
    """

    #: derived qa test must override this
    hazard_calculation_fixture = None

    def _get_queryset(self):
        return models.HazardCalculation.objects.filter(
            description=self.hazard_calculation_fixture)

    def get_hazard_job(self):
        if not self._get_queryset().exists():
            warnings.warn("fixture not loaded. skipping test")
            raise SkipTest
        else:
            return self._get_queryset()[0].oqjob
