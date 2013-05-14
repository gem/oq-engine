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
import os
import StringIO
import subprocess
import unittest
import warnings

from django.core import exceptions

from openquake.engine import engine
from openquake.engine.db import models
from openquake.engine.job import validation

from tests.utils import helpers


class PrepareJobTestCase(unittest.TestCase):

    def test_prepare_job_default_user(self):
        job = engine.prepare_job()

        self.assertEqual('openquake', job.owner.user_name)
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

        self.assertEqual(user_name, job.owner.user_name)
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


class PrepareUserTestCase(unittest.TestCase):

    def test_prepare_user_exists(self):
        user_name = helpers.random_string()
        existing_user = models.OqUser(
            user_name=user_name, full_name=user_name, organization_id=1
        )
        existing_user.save()

        user = engine.prepare_user(user_name)
        self.assertEqual(existing_user.id, user.id)

    def test_prepare_user_does_not_exist(self):
        user_name = helpers.random_string()

        # Sanity check; make sure the user doesn't exist yet.
        self.assertEqual(
            0, len(models.OqUser.objects.filter(user_name=user_name))
        )

        engine.prepare_user(user_name)

        # Now the user should exist.
        self.assertEqual(
            1, len(models.OqUser.objects.filter(user_name=user_name))
        )


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
        }

        params, _ = engine.parse_config(source)

        self.assertEqual(expected_params, params)

    def test_parse_config_with_files(self):
        site_model_input = helpers.touch(content="foo")

        try:
            source = StringIO.StringIO("""
[general]
calculation_mode = classical
[site]
site_model_file = %s
maximum_distance=0
truncation_level=0
random_seed=0
    """ % site_model_input)

            # Add a 'name' to make this look like a real file:
            source.name = 'path/to/some/job.ini'
            exp_base_path = os.path.dirname(
                os.path.join(os.path.abspath('.'), source.name))

            expected_params = {
                'base_path': exp_base_path,
                'calculation_mode': 'classical',
                'truncation_level': '0',
                'random_seed': '0',
                'maximum_distance': '0'
            }

            params, files = engine.parse_config(source)
            self.assertEqual(expected_params, params)
            self.assertEqual(['site_model_file'], files.keys())
            self.assertEqual('acbd18db4cc2f85cedef654fccc4a4d8',
                             files['site_model_file'].digest)
        finally:
            os.unlink(site_model_input)

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
                'maximum_distance': '0'
            }

            params, _ = engine.parse_config(source)
            self.assertEqual(expected_params, params)
        finally:
            os.unlink(sites_csv)


class GetContentTypeTestCase(unittest.TestCase):

    def test__get_content_type(self):
        # no file extension
        self.assertEqual('unknown', engine._get_content_type('/foo/bar/baz'))
        # xml file extension
        self.assertEqual('xml', engine._get_content_type('/foo/bar/baz.xml'))
        # hdf5 file extension
        self.assertEqual(
            'HDF5', engine._get_content_type('/foo/bar/baz.HDF5')
        )


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

        self.owner = helpers.default_user()

        self.site_model = models.Input(digest='123', path='/foo/bar', size=0,
                                  input_type='site_model', owner=self.owner)
        self.site_model.save()
        self.files = [self.site_model]

    def test_create_hazard_calculation(self):
        hc = engine.create_hazard_calculation(self.owner, self.params,
                                              self.files)
        # Normalize/clean fields by fetching a fresh copy from the db.
        hc = models.HazardCalculation.objects.get(id=hc.id)

        self.assertEqual(hc.calculation_mode, 'classical')
        self.assertEqual(hc.width_of_mfd_bin, 1.0)
        self.assertEqual(hc.rupture_mesh_spacing, 1.0)
        self.assertEqual(hc.area_source_discretization, 2.0)
        self.assertEqual(hc.investigation_time, 50.0)
        self.assertEqual(hc.truncation_level, 0.0)
        self.assertEqual(hc.maximum_distance, 200.0)

        # Test the input2haz_calc link:
        [inp2hcs] = models.Input2hcalc.objects.filter(
            hazard_calculation=hc.id)

        self.assertEqual(self.site_model.id, inp2hcs.input.id)

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
            engine.create_hazard_calculation(self.owner, self.params,
                                             self.files)
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

        owner = helpers.default_user()

        vuln_file = models.Input(digest='123', path='/foo/bar', size=0,
                                 input_type='structural_vulnerability',
                                 owner=owner)
        vuln_file.save()
        exposure_file = models.Input(digest='456', path='/foo/baz', size=0,
                                     input_type='exposure', owner=owner)
        exposure_file.save()

        files = [vuln_file, exposure_file]

        rc = engine.create_risk_calculation(owner, params, files)
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


class ReadJobProfileFromConfigFileTestCase(unittest.TestCase):
    """Integration test for basic engine functions.

    Test reading/generating a hazard job profile from a config file, then run
    through the validation form.
    """

    def test_read_and_validate_hazard_config(self):
        cfg = helpers.get_data_path('simple_fault_demo_hazard/job.ini')
        job = engine.prepare_job(getpass.getuser())
        params, files = engine.parse_config(open(cfg, 'r'))
        calculation = engine.create_hazard_calculation(
            job.owner, params, files.values())

        form = validation.ClassicalHazardForm(
            instance=calculation, files=files
        )
        self.assertTrue(form.is_valid())


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
