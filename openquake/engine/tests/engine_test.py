# Copyright (c) 2010-2014, GEM Foundation.
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

import sys
import getpass
import subprocess
import unittest
from StringIO import StringIO

from openquake.engine.db import models
from django.core import exceptions

from openquake.engine import engine
from openquake.engine.tests.utils import helpers


class JobFromFileTestCase(unittest.TestCase):

    def test_prepare_job_default_user(self):
        job = engine.prepare_job()

        self.assertEqual('openquake', job.user_name)
        self.assertEqual('pre_executing', job.status)
        self.assertEqual('progress', job.log_level)

        # Check the make sure it's in the database.
        try:
            models.OqJob.objects.get(id=job.id)
        except exceptions.ObjectDoesNotExist:
            self.fail('Job was not found in the database')

    def test_prepare_job_specified_user(self):
        user_name = helpers.random_string()
        job = engine.prepare_job(user_name=user_name)

        self.assertEqual(user_name, job.user_name)
        self.assertEqual('pre_executing', job.status)
        self.assertEqual('progress', job.log_level)

        try:
            models.OqJob.objects.get(id=job.id)
        except exceptions.ObjectDoesNotExist:
            self.fail('Job was not found in the database')

    def test_prepare_job_explicit_log_level(self):
        # By default, a job is created with a log level of 'progress'
        # (just to show calculation progress).
        # In this test, we'll specify 'debug' as the log level.
        job = engine.prepare_job(log_level='debug')

        self.assertEqual('debug', job.log_level)

    def test_job_from_file(self):
        # make a hazard job
        haz_cfg = helpers.get_data_path('event_based_hazard/job.ini')
        haz_job = engine.job_from_file(haz_cfg, 'test_user')

        # make a fake Output
        out = models.Output.objects.create(
            oq_job=haz_job, display_name='fake', output_type='gmf')

        # make a risk job
        risk_cfg = helpers.get_data_path('event_based_risk/job.ini')
        risk_job = engine.job_from_file(risk_cfg, 'test_user',
                                        hazard_output_id=out.id)
        # make sure the hazard job is associated correctly
        oqjob = risk_job.risk_calculation.hazard_calculation
        self.assertEqual(oqjob.id, haz_job.id)


class CreateRiskCalculationTestCase(unittest.TestCase):

    def test_create_risk_calculation(self):
        # we need an hazard output to create a risk calculation
        hazard_cfg = helpers.get_data_path('simple_fault_demo_hazard/job.ini')
        hazard_job = helpers.get_job(hazard_cfg, 'openquake')
        hc = hazard_job.get_oqparam()
        lt_model = models.LtSourceModel.objects.create(
            hazard_calculation=hazard_job,
            ordinal=1, sm_lt_path="test_sm")
        rlz = models.LtRealization.objects.create(
            lt_model=lt_model, ordinal=1, weight=None,
            gsim_lt_path="test_gsim")
        hazard_output = models.HazardCurve.objects.create(
            lt_realization=rlz,
            output=models.Output.objects.create_output(
                hazard_job, "Test Hazard output", "hazard_curve"),
            investigation_time=hc.investigation_time,
            imt="PGA", imls=[0.1, 0.2, 0.3])
        params = {
            'hazard_output_id': hazard_output.output.id,
            'base_path': 'path/to/job.ini',
            'export_dir': '/tmp/xxx',
            'calculation_mode': 'classical_risk',
            # just some sample params
            'lrem_steps_per_interval': 5,
            'conditional_loss_poes': '0.01, 0.02, 0.05',
            'region_constraint': [(-0.5, 0.5), (0.5, 0.5), (0.5, -0.5),
                                  (-0.5, -0.5)],
        }

        rc = engine.create_calculation(models.RiskCalculation, params)

        # Normalize/clean fields by fetching a fresh copy from the db.
        rc = models.RiskCalculation.objects.get(id=rc.id)

        self.assertEqual(rc.calculation_mode, 'classical_risk')
        self.assertEqual(rc.lrem_steps_per_interval, 5)
        self.assertEqual(rc.conditional_loss_poes, [0.01, 0.02, 0.05])
        self.assertEqual(
            rc.region_constraint.wkt,
            ('POLYGON ((-0.5000000000000000 0.5000000000000000, '
             '0.5000000000000000 0.5000000000000000, '
             '0.5000000000000000 -0.5000000000000000, '
             '-0.5000000000000000 -0.5000000000000000, '
             '-0.5000000000000000 0.5000000000000000))'))


class OpenquakeCliTestCase(unittest.TestCase):
    """
    Run "openquake --version" as a separate
    process using `subprocess`.
    """

    def test_run_version(self):
        args = [helpers.RUNNER, "--version"]

        print 'Running:', ' '.join(args)  # this is useful for debugging
        return subprocess.check_call(args)


class DeleteHazCalcTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.hazard_cfg = helpers.get_data_path(
            'simple_fault_demo_hazard/job.ini')
        cls.risk_cfg = helpers.get_data_path(
            'classical_psha_based_risk/job.ini')

    def test_del_haz_calc(self):
        hazard_job = helpers.get_job(
            self.hazard_cfg, username=getpass.getuser())

        models.Output.objects.create_output(
            hazard_job, 'test_curves_1', output_type='hazard_curve'
        )
        models.Output.objects.create_output(
            hazard_job, 'test_curves_2', output_type='hazard_curve'
        )

        # Sanity check: make sure the hazard calculation and outputs exist in
        # the database:
        hazard_jobs = models.OqJob.objects.filter(id=hazard_job.id)
        self.assertEqual(1, hazard_jobs.count())

        outputs = models.Output.objects.filter(oq_job=hazard_job.id)
        self.assertEqual(2, outputs.count())

        # Delete the calculation
        engine.del_haz_calc(hazard_job.id)

        # Check that the hazard calculation and its outputs were deleted:
        outputs = models.Output.objects.filter(oq_job=hazard_job.id)
        self.assertEqual(0, outputs.count())

        hazard_jobs = models.OqJob.objects.filter(id=hazard_job.id)
        self.assertEqual(0, hazard_jobs.count())

    def test_del_haz_calc_does_not_exist(self):
        self.assertRaises(RuntimeError, engine.del_haz_calc, -1)

    def test_del_haz_calc_no_access(self):
        # Test the case where we try to delete a hazard calculation which does
        # not belong to current user.
        # In this case, deletion is now allowed and should raise an exception.
        hazard_job = helpers.get_job(
            self.hazard_cfg, username=helpers.random_string())
        self.assertRaises(RuntimeError, engine.del_haz_calc, hazard_job.id)

    def test_del_haz_calc_referenced_by_risk_calc(self):
        # Test the case where a risk calculation is referencing the hazard
        # calculation we want to delete.
        # In this case, deletion is not allowed and should raise an exception.
        risk_job, _ = helpers.get_fake_risk_job(
            self.risk_cfg, self.hazard_cfg,
            output_type='curve', username=getpass.getuser()
        )
        risk_calc = risk_job.risk_calculation

        hazard_job = risk_job.risk_calculation.hazard_output.oq_job

        risk_calc.hazard_output = None
        risk_calc.hazard_calculation = hazard_job
        risk_calc.save(using='admin')

        self.assertRaises(RuntimeError, engine.del_haz_calc, hazard_job.id)

    def test_del_haz_calc_output_referenced_by_risk_calc(self):
        # Test the case where a risk calculation is referencing one of the
        # belonging to the hazard calculation we want to delete.
        # In this case, deletion is not allowed and should raise an exception.
        risk_job, _ = helpers.get_fake_risk_job(
            self.risk_cfg, self.hazard_cfg,
            output_type='curve', username=getpass.getuser()
        )
        hazard_job = risk_job.risk_calculation.hazard_output.oq_job
        self.assertRaises(RuntimeError, engine.del_haz_calc, hazard_job.id)


class DeleteRiskCalcTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.hazard_cfg = helpers.get_data_path(
            'simple_fault_demo_hazard/job.ini')
        cls.risk_cfg = helpers.get_data_path(
            'classical_psha_based_risk/job.ini')

    def test_del_risk_calc(self):
        risk_job, _ = helpers.get_fake_risk_job(
            self.risk_cfg, self.hazard_cfg,
            output_type='curve', username=getpass.getuser()
        )
        risk_calc = risk_job.risk_calculation

        models.Output.objects.create_output(
            risk_job, 'test_curves_1', output_type='loss_curve'
        )
        models.Output.objects.create_output(
            risk_job, 'test_curves_2', output_type='loss_curve'
        )

        # Sanity check: make sure the risk calculation and outputs exist in
        # the database:
        risk_calcs = models.RiskCalculation.objects.filter(
            id=risk_calc.id
        )
        self.assertEqual(1, risk_calcs.count())

        outputs = models.Output.objects.filter(oq_job=risk_job.id)
        self.assertEqual(2, outputs.count())

        # Delete the calculation
        engine.del_risk_calc(risk_calc.id)

        # Check that the risk calculation and its outputs were deleted:
        outputs = models.Output.objects.filter(oq_job=risk_job.id)
        self.assertEqual(0, outputs.count())

        risk_calcs = models.RiskCalculation.objects.filter(
            id=risk_calc.id
        )
        self.assertEqual(0, risk_calcs.count())

    def test_del_risk_calc_does_not_exist(self):
        self.assertRaises(RuntimeError, engine.del_risk_calc, -1)

    def test_del_risk_calc_no_access(self):
        # Test the case where we try to delete a risk calculation which does
        # not belong to current user.
        # In this case, deletion is now allowed and should raise an exception.
        risk_job, _ = helpers.get_fake_risk_job(
            self.risk_cfg, self.hazard_cfg,
            output_type='curve', username=helpers.random_string()
        )
        risk_calc = risk_job.risk_calculation

        self.assertRaises(RuntimeError, engine.del_risk_calc, risk_calc.id)


class FakeOutput(object):
    def __init__(self, id, output_type, display_name):
        self.id = id
        self.output_type = output_type
        self.display_name = display_name

    def get_output_type_display(self):
        return self.display_name + str(self.id)


class PrintSummaryTestCase(unittest.TestCase):
    outputs = [FakeOutput(i, 'gmf', 'gmf') for i in range(1, 12)]

    def print_outputs_summary(self, full):
        orig_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            engine.print_outputs_summary(self.outputs, full)
            got = sys.stdout.getvalue()
        finally:
            sys.stdout = orig_stdout
        return got

    def test_print_outputs_summary_full(self):
        self.assertEqual(self.print_outputs_summary(full=True), '''\
  id | output_type | name
   1 | gmf1 | gmf
   2 | gmf2 | gmf
   3 | gmf3 | gmf
   4 | gmf4 | gmf
   5 | gmf5 | gmf
   6 | gmf6 | gmf
   7 | gmf7 | gmf
   8 | gmf8 | gmf
   9 | gmf9 | gmf
  10 | gmf10 | gmf
  11 | gmf11 | gmf
''')

    def test_print_outputs_summary_short(self):
        self.assertEqual(
            self.print_outputs_summary(full=False), '''\
  id | output_type | name
   1 | gmf1 | gmf
   2 | gmf2 | gmf
   3 | gmf3 | gmf
   4 | gmf4 | gmf
   5 | gmf5 | gmf
   6 | gmf6 | gmf
   7 | gmf7 | gmf
   8 | gmf8 | gmf
   9 | gmf9 | gmf
  10 | gmf10 | gmf
 ... | gmf11 | 1 additional output(s)
Some outputs where not shown. You can see the full list with the commands
`openquake --list-hazard-outputs` or `openquake --list-risk-outputs`
''')
