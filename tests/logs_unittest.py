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
        self.python_logger = logging.getLogger('java')
        self.python_logger.addHandler(self.handler)
        self.python_logger.setLevel(logging.DEBUG)

        jlogger_class = self.jvm.JClass("org.apache.log4j.Logger")
        self.root_logger = jlogger_class.getRootLogger()
        self.other_logger = jlogger_class.getLogger('other_logger')

    def tearDown(self):
        self.python_logger.removeHandler(self.handler)
        self.python_logger.setLevel(logging.NOTSET)

    def test_error(self):
        self.root_logger.error('java error msg')
        [record] = self.handler.buffer
        self.assertEqual(record.levelno, logging.ERROR)
        self.assertEqual(record.levelname, 'ERROR')
        self.assertEqual(record.name, 'java')
        self.assertEqual(record.msg, 'java error msg')
        self.assertEqual(record.threadName, 'main')
        self.assertEqual(record.processName, 'java')

    def test_warning(self):
        self.other_logger.warn('warning message')
        [record] = self.handler.buffer
        self.assertEqual(record.levelno, logging.WARNING)
        self.assertEqual(record.levelname, 'WARNING')
        self.assertEqual(record.name, 'java.other_logger')
        self.assertEqual(record.msg, 'warning message')

    def test_debug(self):
        self.other_logger.debug('this is verbose debug info')
        [record] = self.handler.buffer
        self.assertEqual(record.levelno, logging.DEBUG)
        self.assertEqual(record.levelname, 'DEBUG')
        self.assertEqual(record.name, 'java.other_logger')
        self.assertEqual(record.msg, 'this is verbose debug info')

    def test_fatal(self):
        self.root_logger.fatal('something bad has happened')
        [record] = self.handler.buffer
        # java "fatal" records are mapped to python "critical" ones
        self.assertEqual(record.levelno, logging.CRITICAL)
        self.assertEqual(record.levelname, 'CRITICAL')
        self.assertEqual(record.name, 'java')
        self.assertEqual(record.msg, 'something bad has happened')

    def test_info(self):
        self.root_logger.info('information message')
        [record] = self.handler.buffer
        self.assertEqual(record.levelno, logging.INFO)
        self.assertEqual(record.levelname, 'INFO')
        self.assertEqual(record.name, 'java')
        self.assertEqual(record.msg, 'information message')

    def test_custom_level(self):
        # checking that logging with custom levels issues a warning but works

        # org.apache.log4j.Level doesn't allow to be instantiated directly
        # and jpype doesn't support subclassing java in python. that's why
        # in this test we just check JavaLoggingBridge without touching
        # java objects.
        class MockMessage(object):
            def getLevel(self):
                class Level(object):
                    def toInt(self):
                        return 12345
                return Level()
            @property
            def logger(self):
                class Logger(object):
                    def getParent(self):
                        return None
                return Logger()
            def getLocationInformation(self):
                class LocationInformation(object):
                    getFileName = lambda self: 'some/file'
                    getLineNumber = lambda self: '123'
                    getClassName = lambda self: 'someclassname'
                    getMethodName = lambda self: 'somemethod'
                return LocationInformation()
            getLoggerName = lambda self: 'root'
            getMessage = lambda self: 'somemessage'
            getThreadName = lambda self: 'somethread'

        java.JavaLoggingBridge().append(MockMessage())
        # we expect to have two messages logged in this case:
        # first is warning about unknown level used,
        # and second is the actual log message.
        [warning, record] = self.handler.buffer

        self.assertEqual(warning.levelno, logging.WARNING)
        self.assertEqual(warning.name, 'java')
        self.assertEqual(warning.getMessage(), 'unrecognised logging level ' \
                                               '12345 was used')

        self.assertEqual(record.levelno, 12345)
        self.assertEqual(record.levelname, 'Level 12345')
        self.assertEqual(record.name, 'java')
        self.assertEqual(record.msg, 'somemessage')
