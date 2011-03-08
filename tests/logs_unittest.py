# This file is part of OpenQuake.
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
import unittest

from openquake import logs

FAKE_JOB_ID = "8675309"
LOG_FILE_PATH = os.path.join(os.getcwd(), '%s.log' % FAKE_JOB_ID)


def _remove_log_file(job_id):
    """Remove a log file (in the CWD) by job_id."""
    log_path = '%s.log' % job_id
    if os.path.exists(log_path):
        os.system('rm %s' % log_path)

class LogsTestCase(unittest.TestCase):
    
    
    def setUp(self):
        # clean up the default test log file
        _remove_log_file(FAKE_JOB_ID)

    def tearDown(self):
        pass


    def test_validation_logger_write_single_line(self):
        """Test procedure:
        1) Make up some fake job ID
        2) Call logs.make_job_logger(job_id) to make a logger obj
        3) Write one line to the file (file can just be in the CWD) using the 
        'validate' logger method
        4) Verify the contents of the log file
        """
        logger = logs.make_job_logger(FAKE_JOB_ID)
        expected_log_text = "This is a test log entry for job_id = %s." % \
FAKE_JOB_ID
        # write to the log using a monkey patched validate() logging method
        logger.validate(expected_log_text)
       
        self.assertTrue(os.path.exists(LOG_FILE_PATH)) 
        # open the log file
        # read contents and compare
        log_file = open(LOG_FILE_PATH, 'r')
        
        actual_log_text = log_file.readlines()
        # should only be 1 line of text
        self.assertEqual(1, len(actual_log_text))
        self.assertEqual(actual_log_text[0], expected_log_text + '\n')


    def test_validation_logger_write_many_lines(self):
        """Test procedure:
        Basically the same as the single line logger test, except we'll log 
        multiple lines of text."""
        logger = logs.make_job_logger(FAKE_JOB_ID)
        # generate 100 fake log entries
        expected_log_text = [ 'Log entry number %d' % \
x for x in range(100)]
        
        # add the example log text to the log file
        for entry in expected_log_text:
            logger.validate(entry)

        self.assertTrue(os.path.exists(LOG_FILE_PATH))
        # open the log file
        # read the contents and compare
        log_file = open(LOG_FILE_PATH, 'r')

        actual_log_text = log_file.readlines()
        # verify the log file contents
        # append a '\n' to each item of the expected_log_text; this should make
        # the expected and actual match
        self.assertEqual([x + '\n' for x in expected_log_text],\
actual_log_text)


    def test_multiple_loggers(self):
        """Test procedure:
        1) Create 2 loggers (with different job_ids)
        2) Log multiple messages at the 'validate' level to each log file
        3) Verify the contents"""

        job_id_1 = "job314"
        job_id_2 = "job315"
        # first thing, remove logs (if existing) from previous test runs
        _remove_log_file(job_id_1)
        _remove_log_file(job_id_2)

        logger1 = logs.make_job_logger(job_id_1)
        logger2 = logs.make_job_logger(job_id_2)

        # alternate loggers to make sure log entries reach the proper file
        log_1_text = ["Log 1, entry 1", "Log 1, entry 2"]
        log_2_text = ["Log 2, entry 1", "Log 2, entry 2"]

        logger1.validate(log_1_text[0])
        logger2.validate(log_2_text[0])
        logger1.validate(log_1_text[1])
        logger2.validate(log_2_text[1])

        # read the log files and verify the contents
        log_file_1 = open('%s.log' % job_id_1, 'r')
        log_file_2 = open('%s.log' % job_id_2, 'r')

        log_file_1_text = log_file_1.readlines()
        self.assertEqual([x + '\n' for x in log_1_text], log_file_1_text)
        log_file_2_text = log_file_2.readlines()
        self.assertEqual([x + '\n' for x in log_2_text], log_file_2_text)

         
