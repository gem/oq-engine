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


import os
import redis
import time
import subprocess
import functools

import guppy
import mock as mock_module

from openquake import flags
from openquake.job import Job
from openquake.logs import LOG
from openquake import producer
from openquake import settings

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
        mock = Mock()
    signature, func = mock_module._getsignature(func, skipfirst)

    checker = eval("lambda %s: None" % signature)
    mock_module._copy_func_details(func, checker)
    def funcopy(*args, **kwargs):
        checker(*args, **kwargs)
        return mock(*args, **kwargs)
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
    """ Take a file name and return the full path to the file in the smoketests
    directory """
    return os.path.join(
        os.path.dirname(__file__), "../../smoketests", file_name)


def job_from_file(config_file_path):
    """
    Create a Job instance from the given configuration file.

    The results are configured to go to XML files.  *No* database record will
    be stored for the job.  This allows running test on jobs without requiring
    a database.
    """

    return Job.from_file(config_file_path, 'xml_without_db')


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
        LOG.info("Downloading test data for %s", path)
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


class TestStore(object):
    """Simple object store, to be used in tests only."""

    _conn = None

    @staticmethod
    def open():
        """Initialize the test store."""
        if TestStore._conn is not None:
            return
        TestStore._conn = redis.Redis(db=settings.TEST_KVS_DB)

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
