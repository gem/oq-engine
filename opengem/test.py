# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
Helper functions for our unit and smoke tests.
"""


import os
import time
import subprocess

import guppy

from opengem.logs import LOG
from opengem import producer
from opengem import flags

FLAGS = flags.FLAGS

flags.DEFINE_boolean('download_test_data', True, 
        'Fetch test data files if needed')
        
DATA_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '../tests/data'))

SCHEMA_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '../docs/schema'))


def test_file(file_name):
    return os.path.join(DATA_DIR, file_name)

def smoketest_file(file_name):
    return os.path.join(os.path.dirname(__file__), "../smoketests", file_name)

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
        result =  method(*args, **kw)
        print guppy.hpy().heap()
        return result
    try:
        import nose
        return nose.tools.make_decorator(method)(_measured)
    except ImportError, _e:
        pass
    return _measured  
