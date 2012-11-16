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
import subprocess
import sys
import unittest
import uuid

from django.contrib.gis.geos import GEOSGeometry
from django.core.exceptions import ObjectDoesNotExist

from openquake.db import models
from openquake import engine

from tests.utils import helpers


class EngineAPITestCase(unittest.TestCase):

    def setUp(self):
        self.job = engine.prepare_job()

    def test_import_job_profile(self):
        # Given a path to a demo config file, ensure that the appropriate
        # database record for OqJobProfile is created.

        # At the moment, the api function used to import the job profile also
        # returns a dict of the config params and a list of config file
        # sections.

        cfg_path = helpers.demo_file('HazardMapTest/config.gem')

        # Default 'openquake' user:
        owner = helpers.default_user()

        smlt_input = models.Input(
            owner=helpers.default_user(),
            path=os.path.abspath(helpers.demo_file(
                'HazardMapTest/source_model_logic_tree.xml')),
            input_type='lt_source', size=653,
            digest="b6c359d292631db3285f0672d4d87816")

        gmpelt_input = models.Input(
            owner=helpers.default_user(),
            path=os.path.abspath(helpers.demo_file(
                'HazardMapTest/gmpe_logic_tree.xml')),
            input_type='lt_gsim', size=758,
            digest="7e19ae114f77d51affc1577ecec94afe")

        src_model_input = models.Input(
            owner=helpers.default_user(),
            path=os.path.abspath(helpers.demo_file(
                'HazardMapTest/source_model.xml')),
            input_type='source', size=1126,
            digest="f58dd65b39268501335331201a7e0bcf")

        expected_inputs_map = dict(
            lt_source=smlt_input, lt_gsim=gmpelt_input, source=src_model_input)

        expected_jp = models.OqJobProfile(
            owner=owner,
            calc_mode='classical',
            job_type=['hazard'],
            region=GEOSGeometry(
                    'POLYGON((-122.2 37.6, -122.2 38.2, '
                    '-121.5 38.2, -121.5 37.6, -122.2 37.6))'),
            region_grid_spacing=0.01,
            min_magnitude=5.0,
            investigation_time=50.0,
            maximum_distance=200.0,
            component='gmroti50',
            imt='pga',
            period=None,
            damping=None,
            truncation_type='twosided',
            truncation_level=3.0,
            imls=[
                0.005, 0.007, 0.0098, 0.0137, 0.0192, 0.0269, 0.0376, 0.0527,
                0.0738, 0.103, 0.145, 0.203, 0.284, 0.397, 0.556, 0.778, 1.09],
            poes=[0.1],
            realizations=1,
            depth_to_1pt_0km_per_sec=100.0,
            vs30_type='measured',
            source_model_lt_random_seed=23,
            gmpe_lt_random_seed=5,
            width_of_mfd_bin=0.1,
            standard_deviation_type='total',
            reference_vs30_value=760.0,
            reference_depth_to_2pt5km_per_sec_param=5.0,
            sadigh_site_type='rock',
            # area sources:
            include_area_sources=True,
            treat_area_source_as='pointsources',
            area_source_discretization=0.1,
            area_source_magnitude_scaling_relationship=(
                'W&C 1994 Mag-Length Rel.'),
            # point sources:
            include_grid_sources=False,
            treat_grid_source_as='pointsources',
            grid_source_magnitude_scaling_relationship=(
                'W&C 1994 Mag-Length Rel.'),
            # simple faults:
            include_fault_source=True,
            fault_rupture_offset=1.0,
            fault_surface_discretization=1.0,
            fault_magnitude_scaling_relationship='Wells & Coppersmith (1994)',
            fault_magnitude_scaling_sigma=0.0,
            rupture_aspect_ratio=2.0,
            rupture_floating_type='downdip',
            # complex faults:
            include_subduction_fault_source=False,
            subduction_fault_rupture_offset=10.0,
            subduction_fault_surface_discretization=10.0,
            subduction_fault_magnitude_scaling_relationship=(
                'W&C 1994 Mag-Length Rel.'),
            subduction_fault_magnitude_scaling_sigma=0.0,
            subduction_rupture_aspect_ratio=1.5,
            subduction_rupture_floating_type='downdip',
            quantile_levels=[],
            compute_mean_hazard_curve=True)

        expected_sections = ['HAZARD', 'general']
        expected_params = {
            'AREA_SOURCE_DISCRETIZATION': '0.1',
            'AREA_SOURCE_MAGNITUDE_SCALING_RELATIONSHIP':
                'W&C 1994 Mag-Length Rel.',
            'BASE_PATH': os.path.abspath(helpers.demo_file('HazardMapTest')),
            'CALCULATION_MODE': 'Classical',
            'COMPONENT': 'Average Horizontal (GMRotI50)',
            'COMPUTE_MEAN_HAZARD_CURVE': 'true',
            'DAMPING': '5.0',
            'DEPTHTO1PT0KMPERSEC': '100.0',
            'FAULT_MAGNITUDE_SCALING_RELATIONSHIP':
                'Wells & Coppersmith (1994)',
            'FAULT_MAGNITUDE_SCALING_SIGMA': '0.0',
            'FAULT_RUPTURE_OFFSET': '1.0',
            'FAULT_SURFACE_DISCRETIZATION': '1.0',
            'GMPE_LOGIC_TREE_FILE': 'gmpe_logic_tree.xml',
            'GMPE_LT_RANDOM_SEED': '5',
            'GMPE_TRUNCATION_TYPE': '2 Sided',
            'GRID_SOURCE_MAGNITUDE_SCALING_RELATIONSHIP':
                'W&C 1994 Mag-Length Rel.',
            'INCLUDE_AREA_SOURCES': 'true',
            'INCLUDE_FAULT_SOURCE': 'true',
            'INCLUDE_GRID_SOURCES': 'false',
            'INCLUDE_SUBDUCTION_FAULT_SOURCE': 'false',
            'INTENSITY_MEASURE_LEVELS': (
                '0.005, 0.007, 0.0098, 0.0137, 0.0192, 0.0269, 0.0376, 0.0527,'
                ' 0.0738, 0.103, 0.145, 0.203, 0.284, 0.397, 0.556, 0.778,'
                ' 1.09'),
            'INTENSITY_MEASURE_TYPE': 'PGA',
            'INVESTIGATION_TIME': '50.0',
            'MAXIMUM_DISTANCE': '200.0',
            'MINIMUM_MAGNITUDE': '5.0',
            'NUMBER_OF_LOGIC_TREE_SAMPLES': '1',
            'OUTPUT_DIR': 'computed_output',
            'PERIOD': '0.0',
            'POES': '0.1',
            'QUANTILE_LEVELS': '',
            'REFERENCE_DEPTH_TO_2PT5KM_PER_SEC_PARAM': '5.0',
            'REFERENCE_VS30_VALUE': '760.0',
            'REGION_GRID_SPACING': '0.01',
            'REGION_VERTEX':
                '37.6, -122.2, 38.2, -122.2, 38.2, -121.5, 37.6, -121.5',
            'RUPTURE_ASPECT_RATIO': '2.0',
            'RUPTURE_FLOATING_TYPE': 'Along strike and down dip',
            'SADIGH_SITE_TYPE': 'Rock',
            'SOURCE_MODEL_LOGIC_TREE_FILE': 'source_model_logic_tree.xml',
            'SOURCE_MODEL_LT_RANDOM_SEED': '23',
            'STANDARD_DEVIATION_TYPE': 'Total',
            'SUBDUCTION_FAULT_MAGNITUDE_SCALING_RELATIONSHIP':
                'W&C 1994 Mag-Length Rel.',
            'SUBDUCTION_FAULT_MAGNITUDE_SCALING_SIGMA': '0.0',
            'SUBDUCTION_FAULT_RUPTURE_OFFSET': '10.0',
            'SUBDUCTION_FAULT_SURFACE_DISCRETIZATION': '10.0',
            'SUBDUCTION_RUPTURE_ASPECT_RATIO': '1.5',
            'SUBDUCTION_RUPTURE_FLOATING_TYPE': 'Along strike and down dip',
            'TREAT_AREA_SOURCE_AS': 'Point Sources',
            'TREAT_GRID_SOURCE_AS': 'Point Sources',
            'TRUNCATION_LEVEL': '3',
            'VS30_TYPE': 'measured',
            'WIDTH_OF_MFD_BIN': '0.1'}

        actual_jp, params, sections = engine.import_job_profile(
            cfg_path, self.job)
        self.assertEqual(expected_params['BASE_PATH'], params['BASE_PATH'])
        self.assertEqual(expected_params, params)
        self.assertEqual(expected_sections, sections)

        # Test the OqJobProfile:
        self.assertTrue(
            models.model_equals(expected_jp, actual_jp, ignore=(
                'id', 'last_update', '_owner_cache')))

        # Test the Inputs:
        actual_inputs = models.inputs4job(self.job.id)
        self.assertEqual(3, len(actual_inputs))

        for act_inp in actual_inputs:
            exp_inp = expected_inputs_map[act_inp.input_type]
            self.assertTrue(
                models.model_equals(
                    exp_inp, act_inp, ignore=(
                        "id",  "last_update", "path", "model", "_owner_cache",
                        "owner_id", "model_content_id")))

    def test_import_job_profile_as_specified_user(self):
        # Test importing of a job profile when a user is specified
        # The username will be randomly generated and unique to give
        # a clean set of test conditions.
        user_name = str(uuid.uuid4())

        # For sanity, check that the user does not exist to begin with.
        self.assertRaises(ObjectDoesNotExist, models.OqUser.objects.get,
                          user_name=user_name)

        cfg_path = helpers.demo_file('HazardMapTest/config.gem')

        job_profile, _params, _sections = engine.import_job_profile(
            cfg_path, self.job, user_name=user_name)

        self.assertEqual(user_name, job_profile.owner.user_name)
        # Check that the OqUser record for this user now exists.
        # If this fails, it will raise an `ObjectDoesNotExist` exception.
        models.OqUser.objects.get(user_name=user_name)


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
        actual = engine._file_digest(self.PATH)
        self.assertEqual(expected, actual)


class IdenticalInputTestCase(unittest.TestCase, helpers.DbTestCase):
    """Test the _identical_input() function."""

    SRC_MODEL = helpers.demo_file(
        "simple_fault_demo_hazard/dissFaultModel.xml")
    SITE_MODEL = helpers.demo_file("_site_model/site_model.xml")

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
                if jj != fidx:
                    job.status = 'complete'
                job.is_running = False
                job.save()
                jl.append(job)
        cls.job = cls.setup_classic_job(user_name="u1")
        cls.job.status = "complete"
        cls.job.save()
        if sys.platform == 'darwin':
            cls.fragm_digest = subprocess.check_output(
                ["md5", cls.SITE_MODEL]).split()[-1]
        else:
            cls.fragm_digest = subprocess.check_output(
                ["md5sum", cls.SITE_MODEL]).split()[0]

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

    def test__identical_input_and_non_matching_digest(self):
        # The exposure model input is not found since the md5sum digest does
        # not match.
        self._setup_input(
            input_type="exposure", size=123, path=self.SRC_MODEL,
            digest="0" * 32, jobs=self.jobs_u1)
        actual = engine._identical_input("exposure", "x" * 32,
                                         self.job.owner.id)
        self.assertIs(None, actual)

    def test__identical_input_and_failed_first_job(self):
        # The exposure model input is not found since the first job to have
        # used it has failed.
        self._setup_input(
            input_type="exposure", size=123, path=self.SRC_MODEL,
            digest="0" * 32, jobs=self.failed_jobs_u1)
        actual = engine._identical_input("exposure", "0" * 32,
                                         self.job.owner.id)
        self.assertIs(None, actual)

    def test__identical_input_and_owner_differing_from_user(self):
        # The exposure model input is not found since its owner is not the user
        # that is running the current job.
        self._setup_input(
            input_type="exposure", size=123, path=self.SRC_MODEL,
            digest="0" * 32, jobs=self.jobs_u2)
        actual = engine._identical_input("exposure", "0" * 32,
                                         self.job.owner.id)
        self.assertIs(None, actual)


class InsertInputFilesTestCase(unittest.TestCase, helpers.DbTestCase):
    """Test the _insert_input_files() function."""

    GLT = "gmpe_logic_tree.xml"
    SLT = "source_model_logic_tree.xml"

    PARAMS = {
        "GMPE_LOGIC_TREE_FILE": GLT,
        "SOURCE_MODEL_LOGIC_TREE_FILE": SLT,
        "BASE_PATH": helpers.demo_file("simple_fault_demo_hazard")
    }

    old_job = None
    job = None

    @classmethod
    def setUpClass(cls):
        cls.old_job = cls.setup_classic_job()
        cls.old_job.status = "complete"
        cls.old_job.save()

    @classmethod
    def tearDownClass(cls):
        cls.teardown_job(cls.old_job)

    def setUp(self):
        # md5sum digest incorrect
        self.glt_i = models.Input(input_type="lt_gsim", size=123,
                                  path=self.GLT, owner=self.old_job.owner,
                                  digest="0" * 32)
        self.glt_i.save()
        i2j = models.Input2job(input=self.glt_i, oq_job=self.old_job)
        i2j.save()
        # md5sum digest correct
        slt_path = os.path.join(self.PARAMS['BASE_PATH'], self.SLT)
        if sys.platform == 'darwin':
            digest = subprocess.check_output(["md5", slt_path]).split()[-1]
        else:
            digest = subprocess.check_output(["md5sum", slt_path]).split()[0]
        self.slt_i = models.Input(input_type="lt_source", size=123,
                                  path=self.SLT, owner=self.old_job.owner,
                                  digest=digest)
        self.slt_i.save()
        i2j = models.Input2job(input=self.slt_i, oq_job=self.old_job)
        i2j.save()
        self.job = self.setup_classic_job()

    def tearDown(self):
        self.teardown_job(self.job)

    def test_model_content_single_file(self):
        # The contents of input files (such as logic trees, exposure models,
        # etc.) should be saved to the uiapi.model_content table.
        slt_path = os.path.join(self.PARAMS['BASE_PATH'], self.SLT)
        expected_content = open(slt_path, 'r').read()
        engine._insert_input_files(self.PARAMS, self.job, True)
        [slt] = models.inputs4job(self.job.id, input_type="lt_source")

        self.assertEqual('xml', slt.model_content.content_type)
        self.assertEqual(expected_content, slt.model_content.raw_content)

    def test_model_content_many_files(self):
        slt_path = os.path.join(self.PARAMS['BASE_PATH'], self.SLT)
        slt_content = open(slt_path, 'r').read()
        glt_path = os.path.join(self.PARAMS['BASE_PATH'], self.GLT)
        glt_content = open(glt_path, 'r').read()

        engine._insert_input_files(self.PARAMS, self.job, True)
        [slt] = models.inputs4job(self.job.id, input_type="lt_source")
        [glt] = models.inputs4job(self.job.id, input_type="lt_gsim")

        self.assertEqual('xml', slt.model_content.content_type)
        self.assertEqual(slt_content, slt.model_content.raw_content)

        self.assertEqual('xml', glt.model_content.content_type)
        self.assertEqual(glt_content, glt.model_content.raw_content)

    def test_model_content_detect_content_type(self):
        # Test detection of the content type (using the file extension).
        test_file = helpers.touch(suffix=".html")

        # We use the gmpe logic tree as our test target because there is no
        # parsing required in the function under test. Thus, we can put
        # whatever test garbage we want in the file, or just use an empty file
        # (which is the case here).
        params = dict(GMPE_LOGIC_TREE_FILE=test_file, BASE_PATH='/')
        engine._insert_input_files(params, self.job, True)

        [glt] = models.inputs4job(self.job.id, input_type="lt_gsim")
        self.assertEqual('html', glt.model_content.content_type)

    def test_model_content_unknown_content_type(self):
        test_file = helpers.touch()

        params = dict(GMPE_LOGIC_TREE_FILE=test_file, BASE_PATH='/')
        engine._insert_input_files(params, self.job, True)

        [glt] = models.inputs4job(self.job.id, input_type="lt_gsim")
        self.assertEqual('unknown', glt.model_content.content_type)
