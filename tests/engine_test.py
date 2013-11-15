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


import StringIO
import getpass
import mock
import os
import shutil
import subprocess
import tempfile
import unittest
import warnings

from openquake.engine.db import models
from django.core import exceptions

from openquake.engine import engine
from openquake.engine.calculators import base

from tests.utils import helpers


class PrepareJobTestCase(unittest.TestCase):

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


class ParseConfigTestCase(unittest.TestCase):

    def test_parse_config_no_files(self):
        # sections are there just for documentation
        # when we parse the file, we ignore these
        source = StringIO.StringIO("""
[general]
CALCULATION_MODE = classical
region = 1 1 2 2 3 3
[foo]
bar = baz
""")

        # Add a 'name' to make this look like a real file:
        source.name = 'path/to/some/job.ini'
        exp_base_path = os.path.dirname(
            os.path.join(os.path.abspath('.'), source.name))

        expected_params = {
            'base_path': exp_base_path,
            'calculation_mode': 'classical',
            'region': '1 1 2 2 3 3',
            'bar': 'baz',
            'inputs': {},
        }

        params = engine.parse_config(source)

        self.assertEqual(expected_params, params)

    def test_parse_config_with_files(self):
        temp_dir = tempfile.mkdtemp()
        site_model_input = helpers.touch(dir=temp_dir, content="foo")
        job_config = helpers.touch(dir=temp_dir, content="""
[general]
calculation_mode = classical
[site]
site_model_file = %s
maximum_distance=0
truncation_level=0
random_seed=0
    """ % site_model_input)

        try:
            exp_base_path = os.path.dirname(job_config)

            expected_params = {
                'base_path': exp_base_path,
                'calculation_mode': 'classical',
                'truncation_level': '0',
                'random_seed': '0',
                'maximum_distance': '0',
                'inputs': {'site_model': site_model_input},
            }

            params = engine.parse_config(open(job_config, 'r'))
            self.assertEqual(expected_params, params)
            self.assertEqual(['site_model'], params['inputs'].keys())
            self.assertEqual([site_model_input], params['inputs'].values())
        finally:
            shutil.rmtree(temp_dir)

    def test__parse_sites_csv(self):
        expected_wkt = 'MULTIPOINT(0.1 0.2, 2 3, 4.1 5.6)'
        source = StringIO.StringIO("""\
0.1,0.2
2,3
4.1,5.6
""")
        wkt = engine._parse_sites_csv(source)
        self.assertEqual(expected_wkt, wkt)

    def test_parse_config_with_sites_csv(self):
        sites_csv = helpers.touch(content='1.0,2.1\n3.0,4.1\n5.0,6.1')
        try:
            source = StringIO.StringIO("""
[general]
calculation_mode = classical
[geometry]
sites_csv = %s
[misc]
maximum_distance=0
truncation_level=3
random_seed=5
""" % sites_csv)
            source.name = 'path/to/some/job.ini'
            exp_base_path = os.path.dirname(
                os.path.join(os.path.abspath('.'), source.name))

            expected_params = {
                'base_path': exp_base_path,
                'sites': 'MULTIPOINT(1.0 2.1, 3.0 4.1, 5.0 6.1)',
                'calculation_mode': 'classical',
                'truncation_level': '3',
                'random_seed': '5',
                'maximum_distance': '0',
                'inputs': {},
            }

            params = engine.parse_config(source)
            self.assertEqual(expected_params, params)
        finally:
            os.unlink(sites_csv)


class CreateHazardCalculationTestCase(unittest.TestCase):

    def setUp(self):
        # Just the bare minimum set of params to satisfy not null constraints
        # in the db.
        self.params = {
            'base_path': 'path/to/job.ini',
            'calculation_mode': 'classical',
            'region': '1 1 2 2 3 3',
            'width_of_mfd_bin': '1',
            'rupture_mesh_spacing': '1',
            'area_source_discretization': '2',
            'investigation_time': 50,
            'truncation_level': 0,
            'maximum_distance': 200,
            'number_of_logic_tree_samples': 1,
            'intensity_measure_types_and_levels': dict(PGA=[1, 2, 3, 4]),
            'random_seed': 37,
        }

    def test_create_hazard_calculation(self):
        hc = engine.create_calculation(models.HazardCalculation, self.params)

        # Normalize/clean fields by fetching a fresh copy from the db.
        hc = models.HazardCalculation.objects.get(id=hc.id)

        self.assertEqual(hc.calculation_mode, 'classical')
        self.assertEqual(hc.width_of_mfd_bin, 1.0)
        self.assertEqual(hc.rupture_mesh_spacing, 1.0)
        self.assertEqual(hc.area_source_discretization, 2.0)
        self.assertEqual(hc.investigation_time, 50.0)
        self.assertEqual(hc.truncation_level, 0.0)
        self.assertEqual(hc.maximum_distance, 200.0)

    def test_create_hazard_calculation_warns(self):
        # If unknown parameters are specified in the config file, we expect
        # `create_hazard_calculation` to raise warnings and ignore those
        # parameters.

        # Add some random unknown params:
        self.params['blargle'] = 'spork'
        self.params['do_science'] = 'true'

        expected_warnings = [
            "Unknown parameter 'blargle'. Ignoring.",
            "Unknown parameter 'do_science'. Ignoring.",
        ]

        with warnings.catch_warnings(record=True) as w:
            engine.create_calculation(
                models.HazardCalculation, self.params)
        actual_warnings = [msg.message.message for msg in w]
        self.assertEqual(sorted(expected_warnings), sorted(actual_warnings))


class CreateRiskCalculationTestCase(unittest.TestCase):

    def test_create_risk_calculation(self):
        # we need an hazard output to create a risk calculation
        hazard_cfg = helpers.get_data_path('simple_fault_demo_hazard/job.ini')
        hazard_job = helpers.get_hazard_job(hazard_cfg, 'openquake')
        hc = hazard_job.hazard_calculation
        rlz = models.LtRealization.objects.create(
            hazard_calculation=hazard_job.hazard_calculation,
            ordinal=1, seed=1, weight=None,
            sm_lt_path="test_sm", gsim_lt_path="test_gsim",
            is_complete=False, total_items=1, completed_items=1)
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
            'calculation_mode': 'classical',
            # just some sample params
            'lrem_steps_per_interval': 5,
            'conditional_loss_poes': '0.01, 0.02, 0.05',
            'region_constraint': '-0.5 0.5, 0.5 0.5, 0.5 -0.5, -0.5, -0.5',
        }

        rc = engine.create_calculation(models.RiskCalculation, params)

        # Normalize/clean fields by fetching a fresh copy from the db.
        rc = models.RiskCalculation.objects.get(id=rc.id)

        self.assertEqual(rc.calculation_mode, 'classical')
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
        cls.hazard_cfg = helpers.get_data_path('simple_fault_demo_hazard/job.ini')
        cls.risk_cfg = helpers.get_data_path('classical_psha_based_risk/job.ini')

    def test_del_haz_calc(self):
        hazard_job = helpers.get_hazard_job(self.hazard_cfg,
                                            username=getpass.getuser())
        hazard_calc = hazard_job.hazard_calculation

        models.Output.objects.create_output(
            hazard_job, 'test_curves_1', output_type='hazard_curve'
        )
        models.Output.objects.create_output(
            hazard_job, 'test_curves_2', output_type='hazard_curve'
        )

        # Sanity check: make sure the hazard calculation and outputs exist in
        # the database:
        hazard_calcs = models.HazardCalculation.objects.filter(
            id=hazard_calc.id
        )
        self.assertEqual(1, hazard_calcs.count())

        outputs = models.Output.objects.filter(oq_job=hazard_job.id)
        self.assertEqual(2, outputs.count())

        # Delete the calculation
        engine.del_haz_calc(hazard_calc.id)

        # Check that the hazard calculation and its outputs were deleted:
        outputs = models.Output.objects.filter(oq_job=hazard_job.id)
        self.assertEqual(0, outputs.count())

        hazard_calcs = models.HazardCalculation.objects.filter(
            id=hazard_calc.id
        )
        self.assertEqual(0, hazard_calcs.count())

    def test_del_haz_calc_does_not_exist(self):
        self.assertRaises(RuntimeError, engine.del_haz_calc, -1)

    def test_del_haz_calc_no_access(self):
        # Test the case where we try to delete a hazard calculation which does
        # not belong to current user.
        # In this case, deletion is now allowed and should raise an exception.
        hazard_job = helpers.get_hazard_job(self.hazard_cfg,
                                            username=helpers.random_string())
        hazard_calc = hazard_job.hazard_calculation

        self.assertRaises(RuntimeError, engine.del_haz_calc, hazard_calc.id)

    def test_del_haz_calc_referenced_by_risk_calc(self):
        # Test the case where a risk calculation is referencing the hazard
        # calculation we want to delete.
        # In this case, deletion is not allowed and should raise an exception.
        risk_job, _ = helpers.get_fake_risk_job(
            self.risk_cfg, self.hazard_cfg,
            output_type='curves', username=getpass.getuser()
        )
        risk_calc = risk_job.risk_calculation

        hazard_job = risk_job.risk_calculation.hazard_output.oq_job
        hazard_calc = hazard_job.hazard_calculation

        risk_calc.hazard_output = None
        risk_calc.hazard_calculation = hazard_calc
        risk_calc.save(using='admin')

        self.assertRaises(RuntimeError, engine.del_haz_calc, hazard_calc.id)

    def test_del_haz_calc_output_referenced_by_risk_calc(self):
        # Test the case where a risk calculation is referencing one of the
        # belonging to the hazard calculation we want to delete.
        # In this case, deletion is not allowed and should raise an exception.
        risk_job, _ = helpers.get_fake_risk_job(
            self.risk_cfg, self.hazard_cfg,
            output_type='curves', username=getpass.getuser()
        )
        hazard_job = risk_job.risk_calculation.hazard_output.oq_job
        hazard_calc = hazard_job.hazard_calculation

        self.assertRaises(RuntimeError, engine.del_haz_calc, hazard_calc.id)

class DeleteRiskCalcTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.hazard_cfg = helpers.get_data_path('simple_fault_demo_hazard/job.ini')
        cls.risk_cfg = helpers.get_data_path('classical_psha_based_risk/job.ini')

    def test_del_risk_calc(self):
        risk_job, _ = helpers.get_fake_risk_job(
            self.risk_cfg, self.hazard_cfg,
            output_type='curves', username=getpass.getuser()
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
            output_type='curves', username=helpers.random_string()
        )
        risk_calc = risk_job.risk_calculation

        self.assertRaises(RuntimeError, engine.del_risk_calc, risk_calc.id)


class FakeJob(object):
    def __init__(self, hc, rc):
        self.hazard_calculation = hc
        self.risk_calculation = rc
        self.status = ''

class FakeCalc(object):
    def __init__(self, calc_id):
        self.id = calc_id


class RunHazardTestCase(unittest.TestCase):

    def setUp(self):
        mocks = {
            'touch': 'openquake.engine.engine.touch_log_file',
            'job': 'openquake.engine.engine.haz_job_from_file',
            'run': 'openquake.engine.engine.run_calc',
            'complain': 'openquake.engine.engine.complain_and_exit',
            'list': 'openquake.engine.engine.list_hazard_outputs',
        }
        self.mocks = helpers.MultiMock(**mocks)
        self.job = FakeJob(FakeCalc(1), None)
        self.complete_job = FakeJob(FakeCalc(1), None)
        self.complete_job.status = 'complete'


    def test(self):
        with self.mocks:
            self.mocks['job'].return_value = self.job
            self.mocks['run'].return_value = self.complete_job

            engine.run_hazard('job.ini', 'debug', 'oq.log', ['xml', 'geojson'])

            self.assertEqual(1, self.mocks['touch'].call_count)
            self.assertEqual((('oq.log',), {}), self.mocks['touch'].call_args)

            self.assertEqual(1, self.mocks['job'].call_count)
            self.assertEqual(
                (('job.ini', getpass.getuser(), 'debug', ['xml', 'geojson']),
                 {}),
                self.mocks['job'].call_args
            )

            self.assertEqual(1, self.mocks['run'].call_count)
            self.assertEqual(
                ((self.job, 'debug', 'oq.log', ['xml', 'geojson'], 'hazard'),
                 {}),
                self.mocks['run'].call_args
            )

            self.assertEqual(1, self.mocks['list'].call_count)

    def test_job_not_complete(self):
        with self.mocks:
            self.mocks['job'].return_value = self.job
            self.complete_job.status = 'executing'
            self.mocks['run'].return_value = self.complete_job

            engine.run_hazard('job.ini', 'debug', 'oq.log', ['xml', 'geojson'])

            self.assertEqual(0, self.mocks['list'].call_count)
            self.assertEqual(1, self.mocks['complain'].call_count)

    def test_no_log(self):
        with self.mocks:
            self.mocks['job'].return_value = self.job
            self.mocks['run'].return_value = self.complete_job

            engine.run_hazard('job.ini', 'debug', None, ['xml', 'geojson'])

            self.assertEqual(0, self.mocks['touch'].call_count)


class RunRiskTestCase(RunHazardTestCase):

    def setUp(self):
        mocks = {
            'touch': 'openquake.engine.engine.touch_log_file',
            'job': 'openquake.engine.engine.risk_job_from_file',
            'run': 'openquake.engine.engine.run_calc',
            'complain': 'openquake.engine.engine.complain_and_exit',
            'list': 'openquake.engine.engine.list_risk_outputs',
        }
        self.mocks = helpers.MultiMock(**mocks)
        self.job = FakeJob(None, FakeCalc(1))
        self.complete_job = FakeJob(None, FakeCalc(1))
        self.complete_job.status = 'complete'

    def test(self):
        with self.mocks:
            self.mocks['job'].return_value = self.job
            self.mocks['run'].return_value = self.complete_job

            engine.run_risk('job.ini', 'debug', 'oq.log', ['xml', 'geojson'],
                            None, 1)

            self.assertEqual(1, self.mocks['touch'].call_count)
            self.assertEqual((('oq.log',), {}), self.mocks['touch'].call_args)

            self.assertEqual(1, self.mocks['job'].call_count)
            self.assertEqual(
                (('job.ini', getpass.getuser(), 'debug', ['xml', 'geojson'],
                  None, 1),
                 {}),
                self.mocks['job'].call_args
            )

            self.assertEqual(1, self.mocks['run'].call_count)
            self.assertEqual(
                ((self.job, 'debug', 'oq.log', ['xml', 'geojson'], 'risk'),
                 {}),
                self.mocks['run'].call_args
            )

            self.assertEqual(1, self.mocks['list'].call_count)

    def test_job_not_complete(self):
        with self.mocks:
            self.mocks['job'].return_value = self.job
            self.complete_job.status = 'executing'
            self.mocks['run'].return_value = self.complete_job

            engine.run_risk('job.ini', 'debug', 'oq.log', ['xml', 'geojson'],
                            1, None)

            self.assertEqual(0, self.mocks['list'].call_count)
            self.assertEqual(1, self.mocks['complain'].call_count)

    def test_no_log(self):
        with self.mocks:
            self.mocks['job'].return_value = self.job
            self.mocks['run'].return_value = self.complete_job

            engine.run_risk('job.ini', 'debug', None, ['xml', 'geojson'], 1,
                            None)

            self.assertEqual(0, self.mocks['touch'].call_count)


class RunCalcTestCase(unittest.TestCase):

    def setUp(self):
        class FakeCalc(object):
            def __init__(self, job):
                self.job = job

            def __eq__(self, other):
                return self.job.id == other.job.id

        mocks = dict(
            save_job_stats='openquake.engine.engine.save_job_stats',
            get_calc='openquake.engine.engine.get_calculator_class',
            job_stats='openquake.engine.engine._create_job_stats',
            job_exec='openquake.engine.engine._job_exec',
            cleanup=('openquake.engine.supervising.supervisor'
                     '.cleanup_after_job'),
            supervise=('openquake.engine.supervising.supervisor'
                       '.supervise'),
            get_job='openquake.engine.engine._get_job',
            fork='os.fork',
        )
        self.mm = helpers.MultiMock(**mocks)
        self.job = mock.Mock()
        self.job.id = 1984
        self.job.hazard_calculation.calculation_mode = 'classical'

        self.calc_class = FakeCalc
        self.calc_instance = self.calc_class(self.job)

    def test_supervised(self):
        # Due to the way the executor/supervisor process/forking logic is
        # defined, we can't really test the supervisor part of the workflow;
        # we can only test the job executor.
        mm = self.mm

        with mm:
            mm['get_job'].return_value = self.job
            mm['get_calc'].return_value = self.calc_class

            mm['fork'].return_value = 0

            engine.run_calc(self.job, 'debug', 'oq.log', ['geojson'], 'hazard',
                            supervised=True)

        # Check the intermediate function calls and the flow of data:
        self.assertEqual(1, mm['get_calc'].call_count)
        self.assertEqual((('hazard', 'classical'), {}),
                         mm['get_calc'].call_args)

        self.assertEqual(1, mm['job_stats'].call_count)
        self.assertEqual(((self.job, ), {}), mm['job_stats'].call_args)

        self.assertEqual(1, mm['job_exec'].call_count)
        self.assertEqual(
            ((self.job, 'debug', ['geojson'], 'hazard',
              self.calc_instance),
             {}),
            mm['job_exec'].call_args
        )

    def test_unsupervised(self):
        mm = self.mm

        with mm:
            mm['get_job'].return_value = self.job
            mm['get_calc'].return_value = self.calc_class

            engine.run_calc(self.job, 'debug', 'oq.log', ['geojson'], 'hazard',
                            supervised=False)

        self.assertEqual(1, mm['save_job_stats'].call_count)

        # Check the intermediate function calls and the flow of data:
        self.assertEqual(1, mm['get_calc'].call_count)
        self.assertEqual((('hazard', 'classical'), {}),
                         mm['get_calc'].call_args)

        self.assertEqual(1, mm['job_stats'].call_count)
        self.assertEqual(((self.job, ), {}), mm['job_stats'].call_args)

        self.assertEqual(1, mm['job_exec'].call_count)
        self.assertEqual(
            ((self.job, 'debug', ['geojson'], 'hazard', self.calc_instance),
             {}),
            mm['job_exec'].call_args
        )

        self.assertEqual(1, mm['cleanup'].call_count)
        self.assertEqual(((1984, ), {'terminate': False}),
                         mm['cleanup'].call_args)

        self.assertEqual(1, mm['get_job'].call_count)
        self.assertEqual(((1984, ), {}), mm['get_job'].call_args)


class ProgressHandlerTestCase(unittest.TestCase):
    class FakeCalc(base.Calculator):
        class Task(object):
            subtask = lambda fn: fn
        core_calc_task = Task

        hc = mock.Mock()

        def block_size(self):
            return -1

        def task_arg_gen(self, block_size):
            return (range(block_size) for _ in range(block_size))

        def _get_outputs_for_export(self):
            return []

    def setUp(self):
        pass

    def test_do_run_calc(self):
        with helpers.MultiMock(
                sj='openquake.engine.engine._switch_to_job_phase'):
            progress_handler = mock.Mock()
            calc = self.FakeCalc(mock.Mock())
            calc.register_progress_handler(progress_handler)

            engine._do_run_calc(calc.job, [], calc, "hazard")

        self.assertTrue(progress_handler.call_count > 0)
        self.assertEqual((('calculation complete', self.FakeCalc.hc), {}),
                         progress_handler.call_args)
