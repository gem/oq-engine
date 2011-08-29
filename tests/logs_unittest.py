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

import logging.handlers
import unittest

from openquake import java


class JavaLogsTestCase(unittest.TestCase):
    def setUp(self):
        self.jvm = java.jvm()
        self.handler = logging.handlers.BufferingHandler(capacity=float('inf'))
        self.logger = logging.getLogger('java')
        self.logger.addHandler(self.handler)
        self.logger.setLevel(logging.DEBUG)

    def tearDown(self):
        self.logger.removeHandler(self.handler)
        self.logger.setLevel(logging.NOTSET)

    def test_java_logging(self):
        jlogger_class = self.jvm.JClass("org.apache.log4j.Logger")
        root_logger = jlogger_class.getRootLogger()
        other_logger = jlogger_class.getLogger('other_logger')

        root_logger.error('java error msg')
        other_logger.warn('warning message')
        other_logger.debug('this is verbose debug info')
        root_logger.fatal('something bad has happened')
        root_logger.info('information message')

        records = self.handler.buffer
        self.assertEqual(records[0].levelno, logging.ERROR)
        self.assertEqual(records[0].levelname, 'ERROR')
        self.assertEqual(records[0].name, 'java')
        self.assertEqual(records[0].msg, 'java error msg')
        self.assertEqual(records[0].threadName, 'main')
        self.assertEqual(records[0].processName, 'java')

        self.assertEqual(records[1].levelno, logging.WARNING)
        self.assertEqual(records[1].levelname, 'WARNING')
        self.assertEqual(records[1].name, 'java.other_logger')
        self.assertEqual(records[1].msg, 'warning message')

        self.assertEqual(records[2].levelno, logging.DEBUG)
        self.assertEqual(records[2].levelname, 'DEBUG')
        self.assertEqual(records[2].name, 'java.other_logger')
        self.assertEqual(records[2].msg, 'this is verbose debug info')

        self.assertEqual(records[3].levelno, logging.CRITICAL)
        self.assertEqual(records[3].levelname, 'CRITICAL')
        self.assertEqual(records[3].name, 'java')
        self.assertEqual(records[3].msg, 'something bad has happened')

        self.assertEqual(records[4].levelno, logging.INFO)
        self.assertEqual(records[4].levelname, 'INFO')
        self.assertEqual(records[4].name, 'java')
        self.assertEqual(records[4].msg, 'information message')
