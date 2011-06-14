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



import os
import re
import sys
import unittest

import jpype

from openquake import flags
from openquake import java
from openquake import logs

LOG_FILE_PATH = os.path.join(os.getcwd(), 'test.log')

class LogsTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        try:
            os.remove(LOG_FILE_PATH)
        except OSError:
            pass

    @classmethod
    def tearDownClass(cls):
        try:
            os.remove(LOG_FILE_PATH)
        except OSError:
            pass

    def setUp(self):
        # we init the logs before each test because nosetest redefines
        # sys.stdout too.
        flags.FLAGS.debug = 'warn'
        flags.FLAGS.logfile = LOG_FILE_PATH
        logs.init_logs()

    def tearDown(self):
        pass

    def _slurpFile(self):
        # Flush all the logs into the logging file.  This is a little bit
        # tricky.  sys.stdout has been redefined by init_logs() to be a
        # celery.log.LoggingProxy. This proxy has a flush() method that does
        # nothing, but its logger attribute is an instance of the standard
        # logging.Logger python class.  From there we can reach the handler and
        # finally flush it.
        for handler in sys.stdout.logger.handlers:
            handler.flush()

        log_file = open(LOG_FILE_PATH, 'r')

        return [line.strip() for line in log_file.readlines()]

    def assertFileLastLineEqual(self, line):
        msg = None

        log_lines = self._slurpFile()

        if not log_lines:
            msg = "Last file line <EMPTY> != %r" % line
        elif log_lines[-1] != line:
            msg = "Last file line %r != %r" % (log_lines[-1], line)

        if msg:
            raise self.failureException(msg)

    def assertFileLastLineEndsWith(self, line):
        msg = None

        log_lines = self._slurpFile()

        if not log_lines:
            msg = "Last file line <EMPTY> doesn't end with %r" % line
        elif not log_lines[-1].endswith(line):
            msg = "Last file line %r doesn't end with %r" % (log_lines[-1], line)

        if msg:
            raise self.failureException(msg)

    def test_python_printing(self):
        msg = 'This is a test print statement'
        print msg
        self.assertFileLastLineEqual('WARNING:root:'+msg)

    def test_python_logging(self):
        # invoke nosetest with --nologcapture
        msg = 'This is a test log entry'
        logs.LOG.error(msg)

        self.assertFileLastLineEqual('ERROR:root:'+msg)

    def test_java_printing(self):
        java.jvm()

        msg = 'This is a test java print statement'
        jpype.java.lang.System.out.println(msg)

        self.assertFileLastLineEndsWith(msg)

    def test_java_logging(self):
        java.jvm()

        msg = 'This is a test java log entry'
        root_logger = jpype.JClass("org.apache.log4j.Logger").getRootLogger()
        root_logger.error(msg)

        self.assertFileLastLineEndsWith(msg)
