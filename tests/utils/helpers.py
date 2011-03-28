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
import time
import subprocess

import guppy

from openquake.logs import LOG
from openquake import producer
from openquake import flags

FLAGS = flags.FLAGS

flags.DEFINE_boolean('download_test_data', True, 
        'Fetch test data files if needed')
        
DATA_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '../data'))

OUTPUT_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '../data/output'))

SCHEMA_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '../../docs/schema'))

SCHEMA_EXAMPLES_DIR = os.path.abspath(os.path.join(
    SCHEMA_DIR, 'examples'))

WAIT_TIME_STEP_FOR_TASK_SECS = 0.5
MAX_WAIT_LOOPS = 10


def get_data_path(file_name):
    return os.path.join(DATA_DIR, file_name)

def get_output_path(file_name):
    return os.path.join(OUTPUT_DIR, file_name)

def smoketest_file(file_name):
    """ Take a file name and return the full path to the file in the smoketests
    directory """
    return os.path.join(
        os.path.dirname(__file__), "../../smoketests", file_name)

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
            raise Exception("Test data could not be downloaded from %s" % (url))


def timeit(method):
    """Decorator for timing methods"""
    def _timed(*args, **kw):
        """Wrapped function for timed methods"""
        timestart = time.time()
        result = method(*args, **kw)
        timeend = time.time()

        print '%r (%r, %r) %2.2f sec' % \
              (method.__name__, args, kw, timeend-timestart)
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
        result =  method(*args, **kw)
        print guppy.hpy().heap()
        return result
    try:
        import nose
        return nose.tools.make_decorator(method)(_measured)
    except ImportError, _e:
        pass
    return _measured  


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
            raise RuntimeError, "wait too long for celery worker threads"

        time.sleep(wait_time)


class TestStore(object):
    """Simple cache of objects."""

    _last_obj_id = 0
    _store = dict()

    @staticmethod
    def register(obj):
        """Register an object with the store.

        :param obj: The object to be added to the store.
        :returns: The ID for the object added.
        :rtype: integer
        """
        TestStore._last_obj_id += 1
        TestStore._store[TestStore._last_obj_id] =  obj
        return TestStore._last_obj_id

    @staticmethod
    def deregister(oid):
        """Remove object with given identifier from the store.

        :param oid: The identifier associated with the object to be removed.
        """
        del TestStore._store[oid]

    @staticmethod
    def lookup(oid):
        """Return object associated with `oid` or `None`.

        :param oid: The identifier of the object saught.
        """
        return TestStore._store.get(oid)

