# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

"""
Helper functions for our unit and smoke tests.
"""


import functools
import guppy
import logging
import mock as mock_module
import numpy
import os
import random
import redis
import shutil
import string
import subprocess
import sys
import tempfile
import textwrap
import time

from django.core import exceptions

from openquake.calculators.hazard.general import store_gmpe_map
from openquake.calculators.hazard.general import store_source_model
from openquake.db import models
from openquake.engine import JobContext
from openquake import engine
from openquake import logs
from openquake import producer
from openquake.input.logictree import LogicTreeProcessor
from openquake.utils import config

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data'))

OUTPUT_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '../data/output'))

SCHEMA_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '../../openquake/nrml/schema/'))

SCHEMA_EXAMPLES_DIR = os.path.abspath(os.path.join(SCHEMA_DIR, 'examples'))

WAIT_TIME_STEP_FOR_TASK_SECS = 0.5
MAX_WAIT_LOOPS = 10


#: Wraps mock.patch() to make mocksignature=True by default.
patch = functools.partial(mock_module.patch, mocksignature=True)


def default_user():
    """Return the default user to be used for test setups."""
    return models.OqUser.objects.get(user_name="openquake")


def delete_profile(job):
    """Disassociate the job's profile and delete it."""
    [j2p] = models.Job2profile.objects.extra(
        where=["oq_job_id=%s"], params=[job.id])
    jp = j2p.oq_job_profile
    j2p.delete()
    jp.delete()


def insert_inputs(job, inputs):
    """Insert the input records for the given data and job."""
    for imt, imp in inputs:
        iobj = models.Input(path=imp, input_type=imt, owner=job.owner,
                            size=random.randint(1024, 16 * 1024))
        iobj.save()
        i2j = models.Input2job(input=iobj, oq_job=job)
        i2j.save()


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


def demo_file(file_name):
    """
    Take a file name and return the full path to the file in the demos
    directory.
    """
    return os.path.join(
        os.path.dirname(__file__), "../../demos", file_name)


def testdata_path(file_name):
    """
    Take a file name and return the full path to the file in the
    tests/data/demos directory
    """
    return os.path.normpath(os.path.join(
        os.path.dirname(__file__), "../data/demos", file_name))


def job_from_file(config_file_path):
    """
    Create a JobContext instance from the given configuration file.

    The results are configured to go to XML files.  *No* database record will
    be stored for the job.  This allows running test on jobs without requiring
    a database.
    """

    job = engine._job_from_file(config_file_path, 'xml')
    cleanup_loggers()

    return job


def create_job(params, **kwargs):
    job_id = kwargs.pop('job_id', 0)

    return JobContext(params, job_id, **kwargs)


def run_job(config_file, params=None):
    """Given a path to a config file, run openquake as a separate process using
    `subprocess`.

    This function blocks until the openquake job has concluded.

    :param str config_file:
        Path to the calculation config file.
    :param list params:
        List of additional command line params to bin/openquake. Optional.

    :returns:
        The return code of the subprocess.
    :raises:
        If the return code is not 0, a
        :exception:`subprocess.CalledProcessError` is raised.
    """
    args = ["bin/openquake", "--config-file=" + config_file]
    if not params is None:
        args.extend(params)
    return subprocess.check_call(args)


def store_hazard_logic_trees(a_job):
    """Helper function to store the source model and GMPE logic trees in the
    KVS so that it can be read by the Java code. This is basically what the
    @preload decorator does.

    :param a_job:
        :class:`openquake.engine.JobContext` instance.
    """
    lt_proc = LogicTreeProcessor(
        a_job['BASE_PATH'],
        a_job['SOURCE_MODEL_LOGIC_TREE_FILE_PATH'],
        a_job['GMPE_LOGIC_TREE_FILE_PATH'])

    src_model_seed = a_job['SOURCE_MODEL_LT_RANDOM_SEED']
    gmpe_seed = a_job['GMPE_LT_RANDOM_SEED']

    src_model_rnd = random.Random()
    src_model_rnd.seed(src_model_seed)
    gmpe_rnd = random.Random()
    gmpe_rnd.seed(gmpe_seed)

    store_source_model(a_job.job_id, src_model_rnd.getrandbits(32),
                       a_job.params, lt_proc)
    store_gmpe_map(a_job.job_id, gmpe_rnd.getrandbits(32), lt_proc)


class WordProducer(producer.FileProducer):
    """Simple File parser that looks for three
    space-separated values on each line - lat, long and value"""

    def _parse(self):
        for line in self.file:
            col, row, value = line.strip().split(' ', 2)
            yield ((int(col), int(row)), value)


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
    except ImportError:
        pass
    return _timed


def skipit(method):
    """Decorator for skipping tests"""
    try:
        import nose
        from nose.plugins.skip import SkipTest
    except ImportError:

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
    except ImportError:
        pass
    return _measured


def assertDeepAlmostEqual(test_case, expected, actual, *args, **kwargs):
    """
    Assert that two complex structures have almost equal contents.

    Compares lists, dicts and tuples recursively. Checks numeric values
    using test_case's :py:meth:`unittest.TestCase.assertAlmostEqual` and
    checks all other values with :py:meth:`unittest.TestCase.assertEqual`.
    Accepts additional positional and keyword arguments and pass those
    intact to assertAlmostEqual() (that's how you specify comparison
    precision).

    :param test_case: TestCase object on which we can call all of the basic
        'assert' methods.
    :type test_case: :py:class:`unittest.TestCase` object
    """
    is_root = not '__trace' in kwargs
    trace = kwargs.pop('__trace', 'ROOT')
    try:
        if isinstance(expected, (int, float, long, complex)):
            test_case.assertAlmostEqual(expected, actual, *args, **kwargs)
        elif isinstance(expected, (list, tuple, numpy.ndarray)):
            test_case.assertEqual(len(expected), len(actual))
            for index in xrange(len(expected)):
                v1, v2 = expected[index], actual[index]
                assertDeepAlmostEqual(test_case, v1, v2,
                                      __trace=repr(index), *args, **kwargs)
        elif isinstance(expected, dict):
            test_case.assertEqual(set(expected), set(actual))
            for key in expected:
                assertDeepAlmostEqual(test_case, expected[key], actual[key],
                                      __trace=repr(key), *args, **kwargs)
        else:
            test_case.assertEqual(expected, actual)
    except AssertionError as exc:
        exc.__dict__.setdefault('traces', []).append(trace)
        if is_root:
            trace = ' -> '.join(reversed(exc.traces))
            exc = AssertionError("%s\nTRACE: %s" % (exc.message, trace))
        raise exc


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
    """Simple key value store, to be used in tests only."""

    _conn = None

    @staticmethod
    def kvs():
        TestStore.open()
        return TestStore._conn

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
        """Add a datum to the store and return the key chosen.

        :param obj: The datum to be added to the store.
        :returns: The identifier of the datum added.
        :rtype: integer
        """
        TestStore.open()
        return TestStore.put(TestStore.nextkey(), obj)

    @staticmethod
    def put(key, obj):
        """Append the datum to the kvs list identified the given `key`.

        :param key: The key for the datum to be added to the store.
        :param obj: The datum to be added to the store.
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
        """Remove the datum with given identifier from the store.

        :param oid: The identifier associated with the datum to be removed.
        """
        TestStore.open()
        TestStore._conn.delete(oid)

    @staticmethod
    def lookup(oid):
        """Return the datum associated with `oid` or `None`.

        :param oid: The identifier of the datum sought.
        """
        TestStore.open()
        num_of_words = TestStore._conn.llen(oid)
        if num_of_words > 1:
            return TestStore._conn.lrange(oid, 0, num_of_words + 1)
        else:
            return TestStore._conn.lindex(oid, 0)

    @staticmethod
    def set(key, obj):
        """Asssociate a single datum with the given `key`.

        :param key: The key for the datum to be added to the store.
        :param obj: The datum to be added to the store.
        :returns: The `key` given.
        """
        TestStore.open()
        TestStore._conn.set(key, obj)

    @staticmethod
    def get(key):
        """Return the datum associated with the given `key` or `None`.

        :param key: The key of the datum sought.
        :returns: The datum associated with the given `key` or `None`.
        """
        TestStore.open()
        return TestStore._conn.get(key)


def touch(content=None, dir=None, prefix="tmp", suffix="tmp"):
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


class DbTestCase(object):
    """Class which contains various db-related testing helpers."""

    IMLS = [0.005, 0.007, 0.0098, 0.0137, 0.0192, 0.0269, 0.0376, 0.0527,
            0.0738, 0.103, 0.145, 0.203, 0.284, 0.397, 0.556, 0.778]

    @staticmethod
    def teardown_upload(upload, filesystem_only=True):
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

    @staticmethod
    def teardown_inputs(inputs, filesystem_only):
        if filesystem_only:
            return
        [input.delete() for input in inputs]

    @classmethod
    def setup_job_profile(cls, job):
        """Create a profile for the given job."""
        oqjp = models.OqJobProfile()
        oqjp.owner = job.owner
        oqjp.calc_mode = "classical"
        oqjp.job_type = ['hazard']
        oqjp.region_grid_spacing = 0.01
        oqjp.min_magnitude = 5.0
        oqjp.investigation_time = 50.0
        oqjp.component = "gmroti50"
        oqjp.imt = "pga"
        oqjp.truncation_type = "twosided"
        oqjp.truncation_level = 3
        oqjp.reference_vs30_value = 760
        oqjp.imls = cls.IMLS
        oqjp.poes = [0.01, 0.10]
        oqjp.realizations = 1
        oqjp.width_of_mfd_bin = 0.1
        oqjp.treat_grid_source_as = 'pointsources'
        oqjp.treat_area_source_as = 'pointsources'
        oqjp.subduction_rupture_floating_type = 'Along strike and down dip'
        oqjp.subduction_rupture_aspect_ratio = 1.5
        oqjp.subduction_fault_surface_discretization = 0.5
        oqjp.subduction_fault_rupture_offset = 10.0
        oqjp.subduction_fault_magnitude_scaling_sigma = 0.0
        oqjp.subduction_fault_magnitude_scaling_relationship = \
            'W&C 1994 Mag-Length Rel.'
        oqjp.standard_deviation_type = 'total'
        oqjp.sadigh_site_type = 'Rock'
        oqjp.rupture_floating_type = 'Along strike and down dip'
        oqjp.rupture_aspect_ratio = 1.5
        oqjp.reference_depth_to_2pt5km_per_sec_param = 5.0
        oqjp.quantile_levels = [0.25, 0.50]
        oqjp.maximum_distance = 200
        oqjp.include_subductive_fault = True
        oqjp.include_subduction_fault_source = True
        oqjp.include_grid_sources = True
        oqjp.include_fault_source = True
        oqjp.include_area_sources = True
        oqjp.fault_surface_discretization = 1.0
        oqjp.fault_rupture_offset = 5.0
        oqjp.fault_magnitude_scaling_sigma = 0.0
        oqjp.fault_magnitude_scaling_relationship = 'W&C 1994 Mag-Length Rel.'
        oqjp.compute_mean_hazard_curve = True
        oqjp.area_source_magnitude_scaling_relationship = \
            'W&C 1994 Mag-Length Rel.'
        oqjp.area_source_discretization = 0.1
        oqjp.treat_area_source_as = 'pointsources'
        oqjp.subduction_rupture_floating_type = 'downdip'
        oqjp.rupture_floating_type = 'downdip'
        oqjp.sadigh_site_type = 'rock'
        oqjp.region = (
            "POLYGON((-81.3 37.2, -80.63 38.04, -80.02 37.49, -81.3 37.2))")
        oqjp.source_model_lt_random_seed = 23
        oqjp.gmpe_lt_random_seed = 5
        oqjp.save()
        return oqjp

    @classmethod
    def setup_classic_job(cls, create_job_path=True, upload_id=None,
                          inputs=None):
        """Create a classic job with associated upload and inputs.

        :param bool create_job_path: if set the path for the job will be
            created and captured in the job record
        :param integer upload_id: if set use upload record with given db key.
        :param list inputs: a list of 2-tuples where the first and the second
            element are the input type and path respectively
        :returns: a :py:class:`db.models.OqJob` instance
        """
        assert upload_id is None  # temporary

        job = engine.prepare_job()
        oqjp = cls.setup_job_profile(job)
        models.Job2profile(oq_job=job, oq_job_profile=oqjp).save()

        # Insert input model files
        if inputs:
            insert_inputs(job, inputs)

        if create_job_path:
            job.path = os.path.join(tempfile.mkdtemp(), str(job.id))
            job.save()

            os.mkdir(job.path)
            os.chmod(job.path, 0777)

        return job

    @staticmethod
    def teardown_job(job, filesystem_only=True):
        """
        Tear down the file system (and potentially db) artefacts for the
        given job.

        :param job: a :py:class:`db.models.OqJob` instance
        :param bool filesystem_only: if set the oq_job/oq_param/upload/
            input database records will be left intact. This saves time and the
            test db will be dropped/recreated prior to the next db test suite
            run anyway.
        """
        DbTestCase.teardown_inputs(models.inputs4job(job.id),
                                   filesystem_only=filesystem_only)
        if filesystem_only:
            return

        job.delete()
        try:
            oqjp = models.profile4job(job.id)
            oqjp.delete()
        except ValueError:
            # no job profile for this job
            pass

    def generate_output_path(self, job, output_type="hazard_map"):
        """Return a random output path for the given job."""
        path = touch(
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


class ConfigTestCase(object):
    """Class which contains various configuration- and environment-related
    testing helpers."""

    def setup_config(self):
        self.orig_env = os.environ.copy()
        os.environ.clear()
        # Move the local configuration file out of the way if it exists.
        # Otherwise the tests that follow will break.
        local_path = "%s/openquake.cfg" % os.path.abspath(os.getcwd())
        if os.path.isfile(local_path):
            shutil.move(local_path, "%s.test_bakk" % local_path)

    def teardown_config(self):
        os.environ.clear()
        os.environ.update(self.orig_env)
        # Move the local configuration file back into place if it was stashed
        # away.
        local_path = "%s/openquake.cfg" % os.path.abspath(os.getcwd())
        if os.path.isfile("%s.test_bakk" % local_path):
            shutil.move("%s.test_bakk" % local_path, local_path)
        config.Config().cfg.clear()
        config.Config()._load_from_file()

    def prepare_config(self, section, data=None):
        """Set up a configuration with the given `max_mem` value."""
        if data is not None:
            data = '\n'.join(["%s=%s" % item for item in data.iteritems()])
            content = """
                [%s]
                %s""" % (section, data)
        else:
            content = ""
        site_path = touch(content=textwrap.dedent(content))
        os.environ["OQ_SITE_CFG_PATH"] = site_path
        config.Config().cfg.clear()
        config.Config()._load_from_file()


class RedisTestCase(object):
    """Redis-related utilities for testing."""

    def connect(self, *args, **kwargs):
        host = config.get("kvs", "host")
        port = config.get("kvs", "port")
        port = int(port) if port else 6379
        stats_db = config.get("kvs", "stats_db")
        stats_db = int(stats_db) if stats_db else 15
        args = {"host": host, "port": port, "db": stats_db}
        return redis.Redis(**args)


def random_string(length=16):
    """Generate a random string of the given length."""
    result = ""
    while len(result) < length:
        result += random.choice(string.letters + string.digits)
    return result


def prepare_cli_output(raw_output, discard_header=True):
    """Given a huge string of output from a `subprocess.check_output` call,
    split on newlines, strip, and discard empty lines.

    If ``discard_header`` is `True`, drop the first row in the output.

    Returns a `list` of strings, 1 for each row in the CLI output.
    """
    lines = raw_output.split('\n')
    # strip and drop empty lines
    lines = [x.strip() for x in lines if len(x.strip()) > 0]

    if discard_header:
        lines.pop(0)

    return lines
