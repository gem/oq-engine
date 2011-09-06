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
import json
import multiprocessing
import threading
import os.path
import time

from amqplib import client_0_8 as amqp

from openquake import java
from openquake import logs
from openquake.utils import config


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
        self.assertEqual(record.pathname, 'some/file')
        self.assertEqual(record.lineno, 123)
        self.assertEqual(record.funcName, 'someclassname.somemethod')


class PythonAMQPLogTestCase(unittest.TestCase):
    TOPIC = 'oq-unittest.topic'
    LOGGER_NAME = 'tests.PythonAMQPLogTestCase'
    ROUTING_KEY = '%s.*' % LOGGER_NAME

    def setUp(self):
        self.amqp_handler = logs.AMQPHandler(
            host=config.get("amqp", "host"),
            username=config.get("amqp", "user"),
            password=config.get("amqp", "password"),
            virtual_host=config.get("amqp", "vhost"),
            exchange='oq-unittest.topic',
            level=logging.DEBUG)

        self.log = logging.getLogger(self.LOGGER_NAME)
        self.log.setLevel(logging.DEBUG)
        self.log.addHandler(self.amqp_handler)

    def tearDown(self):
        self.log.removeHandler(self.amqp_handler)

    def setup_queue(self):
        # connect to localhost and bind to a queue
        conn = amqp.Connection(host=config.get("amqp", "host"),
                               userid=config.get("amqp", "user"),
                               password=config.get("amqp", "password"),
                               virtual_host=config.get("amqp", "vhost"))
        ch = conn.channel()
        ch.access_request(config.get("amqp", "vhost"), active=False, read=True)
        ch.exchange_declare(self.TOPIC, 'topic', auto_delete=True)
        qname, _, _ = ch.queue_declare()
        ch.queue_bind(qname, self.TOPIC, routing_key=self.ROUTING_KEY)

        return conn, ch, qname

    def consume_messages(self, conn, ch, qname, callback):
        ch.basic_consume(qname, callback=callback)

        while ch.callbacks:
            ch.wait()

        ch.close()
        conn.close()

    def test_amqp_logging(self):
        conn, ch, qname = self.setup_queue()

        self.log.getChild('child1').info('Info message %d %r', 42, 'payload')
        self.log.getChild('child2').warning('Warn message')

        # process the messages
        messages = []

        def consume(msg):
            data = json.loads(msg.body)
            messages.append((msg.delivery_info['routing_key'], data))

            if data['levelname'] == 'WARNING':
                # stop consuming when receive warning
                ch.basic_cancel(msg.consumer_tag)

        self.consume_messages(conn, ch, qname, consume)

        self.assertEquals(2, len(messages))
        (info_key, info), (warning_key, warning) = messages

        self.assertEqual(info_key, 'tests.PythonAMQPLogTestCase.child1')
        self.assertEqual(warning_key, 'tests.PythonAMQPLogTestCase.child2')

        # checking info message
        self.assertAlmostEqual(info['created'], time.time(), delta=1)
        self.assertAlmostEqual(info['msecs'], (info['created'] % 1) * 1000)
        self.assertAlmostEqual(info['relativeCreated'] / 1000.,
                               time.time() - logging._startTime, delta=1)

        self.assertEqual(info['process'],
                         multiprocessing.current_process().ident)
        self.assertEqual(info['processName'],
                         multiprocessing.current_process().name)
        self.assertEqual(info['thread'], threading.current_thread().ident)
        self.assertEqual(info['threadName'], threading.current_thread().name)

        self.assertEqual(info['args'], [])
        self.assertEqual(info['msg'], "Info message 42 'payload'")

        self.assertEqual(info['name'], 'tests.PythonAMQPLogTestCase.child1')
        self.assertEqual(info['levelname'], 'INFO')
        self.assertEqual(info['levelno'], logging.INFO)

        self.assertEqual(info['module'], "logs_unittest")
        self.assertEqual(info['funcName'], 'test_amqp_logging')
        thisfile = __file__.rstrip('c')
        self.assertEqual(info['pathname'], thisfile)
        self.assertEqual(info['filename'], os.path.basename(thisfile))
        self.assertEqual(info['lineno'], 191)

        self.assertEqual(info['exc_info'], None)
        self.assertEqual(info['exc_text'], None)

        # warning message
        self.assertEqual(warning['name'], 'tests.PythonAMQPLogTestCase.child2')
        self.assertEqual(warning['levelname'], 'WARNING')
        self.assertEqual(warning['levelno'], logging.WARNING)
