# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2011, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.

"""
Helper functions for our unit and smoke tests.
"""


import functools
import logging
import os
import redis
import shutil
import subprocess
import tempfile
import time
import sys

import guppy
import mock as mock_module

from django.core import exceptions

from openquake import flags
from openquake import logs
from openquake.job import Job
from openquake import producer
from openquake.utils import config

from openquake.db import models

FLAGS = flags.FLAGS

flags.DEFINE_boolean('download_test_data', True,
        'Fetch test data files if needed')

DATA_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '../data'))

OUTPUT_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '../data/output'))

SCHEMA_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '../../openquake/nrml/schema'))

SCHEMA_EXAMPLES_DIR = os.path.abspath(os.path.join(
    SCHEMA_DIR, 'examples'))

WAIT_TIME_STEP_FOR_TASK_SECS = 0.5
MAX_WAIT_LOOPS = 10


#: Wraps mock.patch() to make mocksignature=True by default.
patch = functools.partial(mock_module.patch, mocksignature=True)


def _patched_mocksignature(func, mock=None, skipfirst=False):
    """
    Fixes arguments order and support of staticmethods in mock.mocksignature.
    """
    static = False
    if isinstance(func, staticmethod):
        static = True
        func = func.__func__

    if mock is None:
        mock = mock_module.Mock()
    signature, func = mock_module._getsignature(func, skipfirst)

    checker = eval("lambda %s: None" % signature)
    mock_module._copy_func_details(func, checker)

    def funcopy(*args, **kwargs):
        checker(*args, **kwargs)
        return mock(*args, **kwargs)

    if not hasattr(mock_module, '_setup_func'):
        # compatibility with mock < 0.8
        funcopy.mock = mock
    else:
        mock_module._setup_func(funcopy, mock)
    if static:
        funcopy = staticmethod(funcopy)
    return funcopy
mock_module.mocksignature = _patched_mocksignature


def get_data_path(file_name):
    return os.path.join(DATA_DIR, file_name)


def get_output_path(file_name):
    return os.path.join(OUTPUT_DIR, file_name)


def smoketest_file(file_name):
    """
    Take a file name and return the full path to the file in the smoketests
    directory.
    """
    return os.path.join(
        os.path.dirname(__file__), "../../smoketests", file_name)


def testdata_path(file_name):
    """
    Take a file name and return the full path to the file in the
    tests/data/smoketests directory
    """
    return os.path.normpath(os.path.join(
        os.path.dirname(__file__), "../data/smoketests", file_name))


def job_from_file(config_file_path):
    """
    Create a Job instance from the given configuration file.

    The results are configured to go to XML files.  *No* database record will
    be stored for the job.  This allows running test on jobs without requiring
    a database.
    """

    job = Job.from_file(config_file_path, 'xml')
    cleanup_loggers()

    return job


def create_job(params, **kwargs):
    job_id = kwargs.pop('job_id', 0)

    return Job(params, job_id, **kwargs)


class WordProducer(producer.FileProducer):
    """Simple File parser that looks for three
    space-separated values on each line - lat, long and value"""

    def _parse(self):
        for line in self.file:
            col, row, value = line.strip().split(' ', 2)
            yield ((int(col), int(row)), value)


def guarantee_file(path, url):
    """Based on flag, download test data file or raise error."""
    if not os.path.isfile(path):
        if not FLAGS.download_test_data:
            raise Exception("Test data does not exist")
        logs.LOG.info("Downloading test data for %s", path)
        retcode = subprocess.call(["curl", url, "-o", path])
        if retcode:
            raise Exception(
                "Test data could not be downloaded from %s" % (url))


def timeit(method):
    """Decorator for timing methods"""

    def _timed(*args, **kw):
        """Wrapped function for timed methods"""
        timestart = time.time()
        result = method(*args, **kw)
        timeend = time.time()

        print '%r (%r, %r) %2.2f sec' % (
            method.__name__, args, kw, timeend - timestart)
        return result
    try:
        import nose
        return nose.tools.make_decorator(method)(_timed)
    except ImportError, _e:
        pass
    return _timed


def skipit(method):
    """Decorator for skipping tests"""
    try:
        import nose
        from nose.plugins.skip import SkipTest
    except ImportError, _e:

        def skip_me(*_args, **_kw):
            """The skipped method"""
            print "Can't raise nose SkipTest error, silently skipping %r" % (
                method.__name__)
        return skip_me

    def skipme(*_args, **_kw):
        """The skipped method"""
        print "Raising a nose SkipTest error"
        raise SkipTest("skipping method %r" % method.__name__)

    return nose.tools.make_decorator(method)(skipme)


def measureit(method):
    """Decorator that profiles memory usage"""

    def _measured(*args, **kw):
        """Decorator that profiles memory usage"""
        result = method(*args, **kw)
        print guppy.hpy().heap()
        return result
    try:
        import nose
        return nose.tools.make_decorator(method)(_measured)
    except ImportError, _e:
        pass
    return _measured


def assertDictAlmostEqual(test_case, expected, actual):
    """
    Assert that two dicts are equal. For dict values which are numbers,
    we use :py:meth:`unittest.TestCase.assertAlmostEqual` for number
    comparisons with a reasonable precision tolerance.

    If the `expected` input value contains nested dictionaries, this function
    will recurse through the dicts and check for equality.

    :param test_case: TestCase object on which we can call all of the basic
        'assert' methods.
    :type test_case: :py:class:`unittest.TestCase` object
    :type expected: dict
    :type actual: dict
    """

    test_case.assertEqual(set(expected.keys()), set(actual.keys()))

    for key in expected.keys():
        exp_val = expected[key]
        act_val = actual[key]

        # If it's a number, use assertAlmostEqual to compare
        # the values with a reasonable tolerance.
        if isinstance(exp_val, (int, float, long, complex)):
            test_case.assertAlmostEqual(exp_val, act_val)
        elif isinstance(exp_val, dict):
            # make a recursive call in case there are nested dicts
            assertDictAlmostEqual(test_case, exp_val, act_val)
        else:
            test_case.assertEqual(expected[key], actual[key])


def assertModelAlmostEqual(test_case, expected, actual):
    """
    Assert that two Django models are equal. For values which are numbers,
    we use :py:meth:`unittest.TestCase.assertAlmostEqual` for number
    comparisons with a reasonable precision tolerance.

    If the `expected` input value contains nested models, this function
    will recurse through them and check for equality.

    :param test_case: TestCase object on which we can call all of the basic
        'assert' methods.
    :type test_case: :py:class:`unittest.TestCase` object
    :type expected: dict
    :type actual: dict
    """

    from django.contrib.gis.db import models as gis_models

    test_case.assertEqual(type(expected), type(actual))

    def getattr_or_none(model, field):
        try:
            return getattr(model, field.name)
        except exceptions.ObjectDoesNotExist:
            return None

    for field in expected._meta.fields:
        if field.name == 'last_update':
            continue

        exp_val = getattr_or_none(expected, field)
        act_val = getattr_or_none(actual, field)

        # If it's a number, use assertAlmostEqual to compare
        # the values with a reasonable tolerance.
        if isinstance(exp_val, (int, float, long, complex)):
            test_case.assertAlmostEqual(exp_val, act_val)
        elif isinstance(exp_val, gis_models.Model):
            # make a recursive call in case there are nested models
            assertModelAlmostEqual(test_case, exp_val, act_val)
        else:
            test_case.assertEqual(exp_val, act_val)


def wait_for_celery_tasks(celery_results,
                          max_wait_loops=MAX_WAIT_LOOPS,
                          wait_time=WAIT_TIME_STEP_FOR_TASK_SECS):
    """celery_results is a list of celery task result objects.
    This function waits until all tasks have finished.
    """

    # if a celery task has not yet finished, wait for a second
    # then check again
    counter = 0
    while (False in [result.ready() for result in celery_results]):
        counter += 1

        if counter > max_wait_loops:
            raise RuntimeError("wait too long for celery worker threads")

        time.sleep(wait_time)

# preserve stdout/stderr (note: we want the nose-manipulated stdout/stderr,
# otherwise we could just use __stdout__/__stderr__)
STDOUT = sys.stdout
STDERR = sys.stderr


def cleanup_loggers():
    root = logging.getLogger()

    for h in list(root.handlers):
        if (isinstance(h, logging.FileHandler) or
            isinstance(h, logging.StreamHandler) or
            isinstance(h, logs.AMQPHandler)):
            root.removeHandler(h)

    # restore the damage created by redirect_stdouts_to_logger; this is only
    # necessary because tests perform multiple log initializations, sometimes
    # for AMQP, sometimes for console
    sys.stdout = STDOUT
    sys.stderr = STDERR


class TestStore(object):
    """Simple object store, to be used in tests only."""

    _conn = None

    @staticmethod
    def open():
        """Initialize the test store."""
        if TestStore._conn is not None:
            return
        TestStore._conn = redis.Redis(db=int(config.get("kvs", "test_db")))

    @staticmethod
    def close():
        """Close the test store."""
        TestStore._conn.flushdb()
        TestStore._conn = None

    @staticmethod
    def nextkey():
        """Generate an unused key

        :return: The test store key generated.
        :rtype: integer
        """
        TestStore.open()
        return TestStore._conn.incr('the-key', amount=1)

    @staticmethod
    def add(obj):
        """Add an object to the store and return the key chosen.

        :param obj: The object to be added to the store.
        :returns: The identifier of the object added.
        :rtype: integer
        """
        TestStore.open()
        return TestStore.put(TestStore.nextkey(), obj)

    @staticmethod
    def put(key, obj):
        """Add an object to the store and associate it with the given `key`.

        :param key: The key for the object to be added to the store.
        :param obj: The object to be added to the store.
        :returns: The `key` given.
        """
        TestStore.open()
        if isinstance(obj, list) or isinstance(obj, tuple):
            for elem in obj:
                TestStore._conn.rpush(key, elem)
        else:
            TestStore._conn.rpush(key, obj)
        return key

    @staticmethod
    def remove(oid):
        """Remove object with given identifier from the store.

        :param oid: The identifier associated with the object to be removed.
        """
        TestStore.open()
        TestStore._conn.delete(oid)

    @staticmethod
    def lookup(oid):
        """Return object associated with `oid` or `None`.

        :param oid: The identifier of the object saught.
        """
        TestStore.open()
        num_of_words = TestStore._conn.llen(oid)
        if num_of_words > 1:
            return TestStore._conn.lrange(oid, 0, num_of_words + 1)
        else:
            return TestStore._conn.lindex(oid, 0)


class TestMixin(object):
    """Mixin class with various helper methods."""

    def touch(self, content=None, dir=None, prefix="tmp", suffix="tmp"):
        """Create temporary file with the given content.

        Please note: the temporary file must be deleted bu the caller.

        :param string content: the content to write to the temporary file.
        :param string dir: directory where the file should be created
        :param string prefix: file name prefix
        :param string suffix: file name suffix
        :returns: a string with the path to the temporary file
        """
        if dir is not None:
            if not os.path.exists(dir):
                os.makedirs(dir)
        fh, path = tempfile.mkstemp(dir=dir, prefix=prefix, suffix=suffix)
        if content:
            fh = os.fdopen(fh, "w")
            fh.write(content)
            fh.close()
        return path

    def create_job_with_mixin(self, params, mixin_class):
        """
        Create a Job and mixes in a Mixin.

        This method, and its double `unload_job_mixin`, when called in the
        setUp and tearDown of a TestCase respectively, have the effect of a
        `with mixin_class` spanning a single test.

        :param params: Job parameters
        :type params: :py:class:`dict`
        :param mixin_class: the mixin that will be mixed in the job
        :type mixin_class: :py:class:`openquake.job.Mixin`
        :returns: a Job
        :rtype: :py:class:`openquake.job.Job`
        """
        # preserve some status to be used by unload
        self._calculation_mode = params.get('CALCULATION_MODE')
        self._job = create_job(params)
        self._mixin = mixin_class(self._job, mixin_class)
        return self._mixin._load()

    def unload_job_mixin(self):
        """
        Remove from the job the Mixin mixed in by create_job_with_mixin.
        """
        self._job.params['CALCULATION_MODE'] = self._calculation_mode
        self._mixin._unload()


class DbTestMixin(TestMixin):
    """Mixin class with various helper methods."""

    IMLS = [0.005, 0.007, 0.0098, 0.0137, 0.0192, 0.0269, 0.0376, 0.0527,
            0.0738, 0.103, 0.145, 0.203, 0.284, 0.397, 0.556, 0.778]

    def default_user(self):
        return models.OqUser.objects.get(user_name="openquake")

    def setup_upload(self, dbkey=None):
        """Create an upload with associated inputs.

        :param integer dbkey: if set use the upload record with given db key.
        :returns: a :py:class:`db.models.Upload` instance
        """
        if dbkey:
            return models.Upload.objects.get(id=dbkey)

        user = models.OqUser.objects.get(user_name="openquake")
        user.save()

        upload = models.Upload(owner=user, path=tempfile.mkdtemp())
        upload.save()

        return upload

    def teardown_upload(self, upload, filesystem_only=True):
        """
        Tear down the file system (and potentially db) artefacts for the
        given upload.

        :param upload: the :py:class:`db.models.Upload` instance
            in question
        :param bool filesystem_only: if set the upload/input database records
            will be left intact. This saves time and the test db will be
            dropped/recreated prior to the next db test suite run anyway.
        """
        # This is like "rm -rf path"
        shutil.rmtree(upload.path, ignore_errors=True)
        if filesystem_only:
            return
        upload.delete()

    def teardown_input_set(self, input_set, filesystem_only):
        if input_set.upload is not None:
            self.teardown_upload(input_set.upload,
                                 filesystem_only=filesystem_only)
        if filesystem_only:
            return
        input_set.delete()

    def setup_classic_job(self, create_job_path=True, upload_id=None):
        """Create a classic job with associated upload and inputs.

        :param integer upload_id: if set use upload record with given db key.
        :param bool create_job_path: if set the path for the job will be
            created and captured in the job record
        :returns: a :py:class:`db.models.OqJob` instance
        """
        assert upload_id is None  # temporary

        owner = models.OqUser.objects.get(user_name="openquake")

        input_set = models.InputSet(owner=owner)
        input_set.save()

        oqp = models.OqParams()
        oqp.job_type = "classical"
        oqp.input_set = input_set
        oqp.region_grid_spacing = 0.01
        oqp.min_magnitude = 5.0
        oqp.investigation_time = 50.0
        oqp.component = "gmroti50"
        oqp.imt = "pga"
        oqp.truncation_type = "twosided"
        oqp.truncation_level = 3
        oqp.reference_vs30_value = 760
        oqp.imls = self.IMLS
        oqp.poes = [0.01, 0.10]
        oqp.realizations = 1
        oqp.width_of_mfd_bin = 0.1
        oqp.treat_grid_source_as = 'Point Sources'
        oqp.treat_area_source_as = 'Point Sources'
        oqp.subduction_rupture_floating_type = 'Along strike and down dip'
        oqp.subduction_rupture_aspect_ratio = 1.5
        oqp.subduction_fault_surface_discretization = 0.5
        oqp.subduction_fault_rupture_offset = 10.0
        oqp.subduction_fault_magnitude_scaling_sigma = 0.0
        oqp.subduction_fault_magnitude_scaling_relationship = \
            'W&C 1994 Mag-Length Rel.'
        oqp.standard_deviation_type = 'total'
        oqp.sadigh_site_type = 'Rock'
        oqp.rupture_floating_type = 'Along strike and down dip'
        oqp.rupture_aspect_ratio = 1.5
        oqp.reference_depth_to_2pt5km_per_sec_param = 5.0
        oqp.quantile_levels = [0.25, 0.50]
        oqp.maximum_distance = 200
        oqp.include_subductive_fault = True
        oqp.include_subduction_fault_source = True
        oqp.include_grid_sources = True
        oqp.include_fault_source = True
        oqp.include_area_sources = True
        oqp.fault_surface_discretization = 1.0
        oqp.fault_rupture_offset = 5.0
        oqp.fault_magnitude_scaling_sigma = 0.0
        oqp.fault_magnitude_scaling_relationship = 'W&C 1994 Mag-Length Rel.'
        oqp.compute_mean_hazard_curve = True
        oqp.area_source_magnitude_scaling_relationship = \
            'W&C 1994 Mag-Length Rel.'
        oqp.area_source_discretization = 0.1
        oqp.treat_area_source_as = 'pointsources'
        oqp.subduction_rupture_floating_type = 'downdip'
        oqp.rupture_floating_type = 'downdip'
        oqp.sadigh_site_type = 'rock'
        oqp.region = (
            "POLYGON((-81.3 37.2, -80.63 38.04, -80.02 37.49, -81.3 37.2))")
        oqp.save()

        job = models.OqJob(oq_params=oqp, owner=owner,
                           job_type="classical")
        job.save()

        if create_job_path:
            job.path = os.path.join(tempfile.mkdtemp(), str(job.id))
            job.save()

            os.mkdir(job.path)
            os.chmod(job.path, 0777)

        return job

    def teardown_job(self, job, filesystem_only=True):
        """
        Tear down the file system (and potentially db) artefacts for the
        given job.

        :param job: the :py:class:`db.models.OqJob` instance
            in question
        :param bool filesystem_only: if set the oq_job/oq_param/upload/input
            database records will be left intact. This saves time and the test
            db will be dropped/recreated prior to the next db test suite run
            anyway.
        """
        oqp = job.oq_params
        if oqp.input_set is not None:
            self.teardown_input_set(oqp.input_set,
                                    filesystem_only=filesystem_only)
        if filesystem_only:
            return

        job.delete()
        oqp.delete()

    def setup_output(self, job_to_use=None, output_type="hazard_map",
                     db_backed=True):
        """Create an output object of the given type.

        :param job_to_use: if set use the passed
            :py:class:`db.models.OqJob` instance as opposed to
            creating a new one.
        :param str output_type: map type, one of "hazard_map", "loss_map"
        :param bool db_backed: initialize the property of the newly created
            :py:class:`db.models.Output` instance with this value.
        :returns: a :py:class:`db.models.Output` instance
        """
        job = job_to_use if job_to_use else self.setup_classic_job()
        output = models.Output(owner=job.owner, oq_job=job,
                               output_type=output_type,
                               db_backed=db_backed)
        output.path = self.generate_output_path(job, output_type)
        output.display_name = os.path.basename(output.path)
        output.save()

        return output

    def generate_output_path(self, job, output_type="hazard_map"):
        """Return a random output path for the given job."""
        path = self.touch(
            dir=os.path.join(job.path, "computed_output"), suffix=".xml",
            prefix="hzrd." if output_type == "hazard_map" else "loss.")
        return path

    def teardown_output(self, output, teardown_job=True, filesystem_only=True):
        """
        Tear down the file system (and potentially db) artefacts for the
        given output.

        :param output: the :py:class:`db.models.Output` instance
            in question
        :param bool teardown_job: the associated job and its related artefacts
            shall be torn down as well.
        :param bool filesystem_only: if set the various database records will
            be left intact. This saves time and the test db will be
            dropped/recreated prior to the next db test suite run anyway.
        """
        job = output.oq_job
        if not filesystem_only:
            output.delete()
        if teardown_job:
            self.teardown_job(job, filesystem_only=filesystem_only)
