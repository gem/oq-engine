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

from openquake.engine.db import models
from openquake.engine import engine

from tests.utils import helpers


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
