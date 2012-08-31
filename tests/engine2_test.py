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
import sys
import unittest

from django.core import exceptions

from openquake import engine2
from openquake.db import models
from openquake.job import validation

from tests.utils import helpers


class PrepareJobTestCase(unittest.TestCase):

    def test_prepare_job_default_user(self):
        job = engine2.prepare_job()

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
        job = engine2.prepare_job(user_name=user_name)

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
        job = engine2.prepare_job(log_level='debug')

        self.assertEqual('debug', job.log_level)


class PrepareUserTestCase(unittest.TestCase):

    def test_prepare_user_exists(self):
        user_name = helpers.random_string()
        existing_user = models.OqUser(
            user_name=user_name, full_name=user_name, organization_id=1
        )
        existing_user.save()

        user = engine2.prepare_user(user_name)
        self.assertEqual(existing_user.id, user.id)

    def test_prepare_user_does_not_exist(self):
        user_name = helpers.random_string()

        # Sanity check; make sure the user doesn't exist yet.
        self.assertEqual(
            0, len(models.OqUser.objects.filter(user_name=user_name))
        )

        engine2.prepare_user(user_name)

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
            'force_inputs': False,
            'calculation_mode': 'classical',
            'region': '1 1 2 2 3 3',
            'bar': 'baz',
        }

        params, _ = engine2.parse_config(source)

        self.assertEqual(expected_params, params)

    def test_parse_config_with_files_force_inputs(self):
        site_model_input = helpers.touch(content="site model")
        sm_lt_input = helpers.touch(content="source model logic tree")
        gsim_lt_input = helpers.touch(content="gsim logic tree")

        source = StringIO.StringIO("""
[hazard_or_whatever]
calculation_mode = classical
gsim_logic_tree_file = %s
source_model_logic_tree_file = %s
site_model_file = %s
not_a_valid_file = foo.xml
""" % (gsim_lt_input, sm_lt_input, site_model_input))

        # Add a 'name' to make this look like a real file:
        source.name = 'path/to/some/job.ini'
        exp_base_path = os.path.dirname(
            os.path.join(os.path.abspath('.'), source.name))

        expected_params = {
            'base_path': exp_base_path,
            'force_inputs': True,
            'calculation_mode': 'classical',
            'not_a_valid_file': 'foo.xml',
        }

        params, files = engine2.parse_config(source, force_inputs=True)

        expected_files = {
            'site_model_file': models.Input.objects.filter(
                input_type='site_model').latest('id'),
            'source_model_logic_tree_file': models.Input.objects.filter(
                input_type='lt_source').latest('id'),
            'gsim_logic_tree_file': models.Input.objects.filter(
                input_type='lt_gsim').latest('id'),
        }

        self.assertEqual(expected_params, params)

        self.assertEqual(len(expected_files), len(files))
        for key in expected_files:
            self.assertEqual(expected_files[key].id, files[key].id)

    def test_parse_config_with_files_no_force_inputs(self):
        site_model_input = helpers.touch(content="foo")

        source = StringIO.StringIO("""
[general]
calculation_mode = classical
[site]
site_model_file = %s
not_a_valid_file = foo.xml
""" % site_model_input)

        # Add a 'name' to make this look like a real file:
        source.name = 'path/to/some/job.ini'
        exp_base_path = os.path.dirname(
            os.path.join(os.path.abspath('.'), source.name))

        expected_params = {
            'base_path': exp_base_path,
            'force_inputs': False,
            'calculation_mode': 'classical',
            'not_a_valid_file': 'foo.xml',
        }

        # Run first with force_inputs=True to create the new Input.
        _, expected_files = engine2.parse_config(source, force_inputs=True)

        # In order for us to reuse the existing input, we need to associate
        # each input with a successful job.
        job = engine2.prepare_job(getpass.getuser())
        job.status = 'complete'
        job.save()
        for inp in expected_files.values():
            i2j = models.Input2job(input=inp, oq_job=job)
            i2j.save()

        # Now run twice with force_inputs=False (the default).
        source.seek(0)
        params1, files1 = engine2.parse_config(source)
        source.seek(0)
        params2, files2 = engine2.parse_config(source)

        # Check the params just for sanity.
        self.assertEqual(expected_params, params1)
        self.assertEqual(expected_params, params2)

        # Finally, check that the Input returned by the latest 2 calls matches
        # the input we created above.
        self.assertEqual(len(expected_files), len(files1))
        self.assertEqual(len(expected_files), len(files2))

        for key in expected_files:
            self.assertEqual(expected_files[key].id, files1[key].id)
            self.assertEqual(expected_files[key].id, files2[key].id)


class FileDigestTestCase(unittest.TestCase):
    """Test the _file_digest() function."""

    PATH = helpers.get_data_path("src_model1.dat")

    def test__file_digest(self):
        # Make sure the digest returned by the function matches the one
        # obtained via /usr/bin/md5sum
        if sys.platform == 'darwin':
            expected = subprocess.check_output(["md5", self.PATH]).split()[-1]
        else:
            expected = subprocess.check_output(
                ["md5sum", self.PATH]).split()[0]
        actual = engine2._file_digest(self.PATH)
        self.assertEqual(expected, actual)


class GetContentTypeTestCase(unittest.TestCase):

    def test__get_content_type(self):
        # no file extension
        self.assertEqual('unknown', engine2._get_content_type('/foo/bar/baz'))
        # xml file extension
        self.assertEqual('xml', engine2._get_content_type('/foo/bar/baz.xml'))
        # hdf5 file extension
        self.assertEqual(
            'HDF5', engine2._get_content_type('/foo/bar/baz.HDF5')
        )


@unittest.skip
class IdenticalInputTestCase(unittest.TestCase, helpers.DbTestCase):
    """Test the _identical_input() function."""

    EXPOM = helpers.get_data_path("exposure.xml")
    FRAGM = os.path.join(helpers.SCHEMA_DIR, "examples/fragm_d.xml")

    # some jobs (first succeeded) ran by user "u2"
    jobs_u2 = []
    # some jobs (first failed) ran by user "u1"
    failed_jobs_u1 = []
    # some jobs (first succeeded) ran by user "u1"
    jobs_u1 = []
    # "New" job for user "u1", _identical_input() will be run for it.
    job = None
    # Fragility model md5sum digest
    fragm_digest = None

    @classmethod
    def setUpClass(cls):
        # In 'failed_jobs_u1' we want the first job to have status "failed".
        # In 'jobs_u1' the first job is fine/"succeeded".
        # In 'jobs_u2' the first job is fine but all the jobs are owned by a
        # different user "u2".
        jdata = (("u1", cls.failed_jobs_u1, 0),
                 ("u1", cls.jobs_u1, 1), ("u2", cls.jobs_u2, 2))
        for ji, (user_name, jl, fidx) in enumerate(jdata):
            num_jobs = ji + 2
            for jj in range(num_jobs):
                job = cls.setup_classic_job(omit_profile=True,
                                            user_name=user_name)
                job.status = "failed" if jj == fidx else "succeeded"
                job.save()
                jl.append(job)
        cls.job = cls.setup_classic_job(user_name="u1")
        cls.job.status = "succeeded"
        cls.job.save()
        if sys.platform == 'darwin':
            cls.fragm_digest = subprocess.check_output(
                ["md5", cls.FRAGM]).split()[-1]
        else:
            cls.fragm_digest = subprocess.check_output(
                ["md5sum", cls.FRAGM]).split()[0]

    @classmethod
    def tearDownClass(cls):
        cls.teardown_job(cls.job)

    def _setup_input(self, input_type, size, path, digest, jobs):
        """Create a model input and associate it with the given jobs.

        Its owner will be the same as the owner of the first job.
        """
        # In order for the tests in this class to work we need to disable any
        # other model inputs that might still be in the database.
        models.Input2job.objects.all().delete()

        mdl = models.Input(input_type=input_type, size=size, path=path,
                           owner=jobs[0].owner, digest=digest)
        mdl.save()
        for job in jobs:
            i2j = models.Input2job(input=mdl, oq_job=job)
            i2j.save()
        return mdl

    def test__identical_input(self):
        # The matching fragility model input is found
        expected = self._setup_input(
            input_type="fragility", size=123, path=self.FRAGM,
            digest=self.fragm_digest, jobs=self.jobs_u1)
        actual = engine2._identical_input("fragility", self.fragm_digest,
                                         self.job.owner.id)
        self.assertEqual(expected.id, actual.id)

    def test__identical_input_and_non_matching_digest(self):
        # The exposure model input is not found since the md5sum digest does
        # not match.
        self._setup_input(
            input_type="exposure", size=123, path=self.EXPOM, digest="0" * 32,
            jobs=self.jobs_u1)
        actual = engine2._identical_input("exposure", "x" * 32,
                                         self.job.owner.id)
        self.assertIs(None, actual)

    def test__identical_input_and_failed_first_job(self):
        # The exposure model input is not found since the first job to have
        # used it has failed.
        self._setup_input(
            input_type="exposure", size=123, path=self.EXPOM, digest="0" * 32,
            jobs=self.failed_jobs_u1)
        actual = engine2._identical_input("exposure", "0" * 32,
                                         self.job.owner.id)
        self.assertIs(None, actual)

    def test__identical_input_and_owner_differing_from_user(self):
        # The exposure model input is not found since its owner is not the user
        # that is running the current job.
        self._setup_input(
            input_type="exposure", size=123, path=self.EXPOM, digest="0" * 32,
            jobs=self.jobs_u2)
        actual = engine2._identical_input("exposure", "0" * 32,
                                         self.job.owner.id)
        self.assertIs(None, actual)


class CreateHazardCalculationTestCase(unittest.TestCase):

    def test_create_hazard_calculation(self):
        # Just the bare minimum set of params to satisfy not null constraints
        # in the db.
        params = {
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

        owner = helpers.default_user()

        site_model = models.Input(digest='123', path='/foo/bar', size=0,
                                  input_type='site_model', owner=owner)
        site_model.save()
        files = [site_model]

        hc = engine2.create_hazard_calculation(owner, params, files)
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

        self.assertEqual(site_model.id, inp2hcs.input.id)


class ReadJobProfileFromConfigFileTestCase(unittest.TestCase):
    """Integration test for basic engine functions.

    Test reading/generating a hazard job profile from a config file, then run
    through the validation form.
    """

    def test_read_and_validate_hazard_config(self):
        cfg = helpers.demo_file('simple_fault_demo_hazard/job.ini')
        job = engine2.prepare_job(getpass.getuser())
        params, files = engine2.parse_config(open(cfg, 'r'))
        calculation = engine2.create_hazard_calculation(
            job.owner, params, files.values())

        form = validation.ClassicalHazardCalculationForm(
            instance=calculation, files=files
        )
        self.assertTrue(form.is_valid())
