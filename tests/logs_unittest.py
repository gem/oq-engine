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
        # This is safe to call even if the jvm was already running from a
        # previous test.
        # Even better would be to start with a fresh jvm but this is currently
        # not possible (see
        # http://jpype.sourceforge.net/doc/user-guide/userguide.html#limitation
        # )
        java.jvm()

        # save the java stdout and stderr that will be trashed during this test
        cls.old_java_out = jpype.java.lang.System.out
        cls.old_java_err = jpype.java.lang.System.err

        try:
            os.remove(LOG_FILE_PATH)
        except OSError:
            pass

    @classmethod
    def tearDownClass(cls):
        # restore the java stdout and stderr that were trashed during this test
        jpype.java.lang.System.setOut(cls.old_java_out)
        jpype.java.lang.System.setErr(cls.old_java_err)

        try:
            os.remove(LOG_FILE_PATH)
        except OSError:
            pass

    def setUp(self):
        # we init the logs before each test because nosetest redefines
        # sys.stdout and removes all the handlers from the rootLogger
        flags.FLAGS.debug = 'warn'
        flags.FLAGS.logfile = LOG_FILE_PATH
        logs.init_logs()

        java._set_java_log_level('WARN')
        java._setup_java_capture(sys.stdout, sys.stderr)

    def _slurp_file(self):
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

    def assert_file_last_line_equal(self, line):
        msg = None

        log_lines = self._slurp_file()

        if not log_lines:
            msg = "Last file line <EMPTY> != %r" % line
        elif log_lines[-1] != line:
            msg = "Last file line %r != %r" % (log_lines[-1], line)

        if msg:
            raise self.failureException(msg)

    def assert_file_last_line_ends_with(self, line):
        msg = None

        log_lines = self._slurp_file()

        if not log_lines:
            msg = "Last file line <EMPTY> doesn't end with %r" % line
        elif not log_lines[-1].endswith(line):
            msg = "Last file line %r doesn't end with %r"\
                % (log_lines[-1], line)

        if msg:
            raise self.failureException(msg)

    def test_python_printing(self):
        msg = 'This is a test print statement'
        print msg
        self.assert_file_last_line_equal('WARNING:root:' + msg)

    def test_python_logging(self):
        msg = 'This is a test log entry'
        logs.LOG.error(msg)

        self.assert_file_last_line_equal('ERROR:root:' + msg)

    def test_java_printing(self):
        msg = 'This is a test java print statement'
        jpype.java.lang.System.out.println(msg)

        self.assert_file_last_line_ends_with(msg)

    def test_java_logging(self):
        msg = 'This is a test java log entry'
        root_logger = jpype.JClass("org.apache.log4j.Logger").getRootLogger()
        root_logger.error(msg)

        self.assert_file_last_line_ends_with(msg)
