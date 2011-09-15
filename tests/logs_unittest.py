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
import multiprocessing
import threading
import os.path
import time
import socket
import json

import kombu
import kombu.entity
import kombu.messaging

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
        self.assertEqual(record.processName,
                         multiprocessing.current_process().name)

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

    def test_record_serializability(self):
        self.root_logger.info('whatever')
        [record] = self.handler.buffer
        # original args are tuple which becomes list
        # being encoded to json and back
        record.args = list(record.args)
        self.assertEqual(json.loads(json.dumps(record.__dict__)),
                         record.__dict__)

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
    LOGGER_NAME = 'tests.PythonAMQPLogTestCase'
    ROUTING_KEY = 'oq.job.None.%s.#' % LOGGER_NAME

    def setUp(self):
        self.amqp_handler = logs.AMQPHandler(level=logging.DEBUG)
        self.amqp_handler.set_job_id(None)

        self.log = logging.getLogger(self.LOGGER_NAME)
        self.log.setLevel(logging.DEBUG)
        self.log.addHandler(self.amqp_handler)

        cfg = config.get_section('amqp')
        self.connection = kombu.BrokerConnection(hostname=cfg.get('host'),
                                                 userid=cfg['user'],
                                                 password=cfg['password'],
                                                 virtual_host=cfg['vhost'])
        self.channel = self.connection.channel()
        self.exchange = kombu.entity.Exchange(cfg['exchange'], type='topic',
                                              channel=self.channel)
        self.queue = kombu.entity.Queue(exchange=self.exchange,
                                        channel=self.channel,
                                        routing_key=self.ROUTING_KEY,
                                        exclusive=True)
        self.queue.queue_declare()
        self.queue.queue_bind()
        self.consumer = kombu.messaging.Consumer(self.channel, self.queue)
        self.producer = kombu.messaging.Producer(self.channel, self.exchange,
                                                 serializer='json')

    def tearDown(self):
        self.log.removeHandler(self.amqp_handler)
        if self.channel:
            self.channel.close()
        if self.connection:
            self.connection.close()

    def test_amqp_handler(self):
        messages = []

        def consume(data, msg):
            print data
            self.assertEqual(msg.properties['content_type'],
                             'application/json')
            messages.append((msg.delivery_info['routing_key'], data))

            if data['levelname'] == 'WARNING':
                # stop consuming when receive warning
                self.channel.close()
                self.channel = None
                self.connection.close()
                self.connection = None

        self.consumer.register_callback(consume)
        self.consumer.consume()

        self.log.getChild('child1').info('Info message %d %r', 42, 'payload')
        self.log.getChild('child2').warning('Warn message')

        while self.connection:
            self.connection.drain_events()

        self.assertEquals(2, len(messages))
        (info_key, info), (warning_key, warning) = messages

        self.assertEqual(info_key,
                         'oq.job.None.tests.PythonAMQPLogTestCase.child1')
        self.assertEqual(warning_key,
                         'oq.job.None.tests.PythonAMQPLogTestCase.child2')

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
        self.assertEqual(info['funcName'], 'test_amqp_handler')
        thisfile = __file__.rstrip('c')
        self.assertEqual(info['pathname'], thisfile)
        self.assertEqual(info['filename'], os.path.basename(thisfile))
        self.assertEqual(info['lineno'], 213)
        self.assertEqual(info['hostname'], socket.getfqdn())

        self.assertEqual(info['exc_info'], None)
        self.assertEqual(info['exc_text'], None)

        # warning message
        self.assertEqual(warning['name'], 'tests.PythonAMQPLogTestCase.child2')
        self.assertEqual(warning['levelname'], 'WARNING')
        self.assertEqual(warning['levelno'], logging.WARNING)

    def test_amqp_log_source(self):
        timeout = threading.Event()

        class _AMQPLogSource(logs.AMQPLogSource):
            stop_on_timeout = False

            def timeout_callback(self):
                timeout.set()
                if self.stop_on_timeout:
                    raise StopIteration()

        logsource = _AMQPLogSource('oq.testlogger.#', timeout=0.1)
        logsource_thread = threading.Thread(target=logsource.run)
        logsource_thread.start()
        handler = logging.handlers.BufferingHandler(float('inf'))
        logger = logging.getLogger('oq.testlogger')
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        try:
            msg = dict(
                created=12345, msecs=321, relativeCreated=777,
                process=1, processName='prcs', thread=111, threadName='thrd',
                msg='message!', args=[],
                name='oq.testlogger.sublogger',
                levelname='INFO', levelno=logging.INFO,
                module='somemodule', funcName='somefunc', pathname='somepath',
                filename='somefile', lineno=262, hostname='apollo',
                exc_info=None, exc_text=None
            )
            self.producer.publish(msg.copy(),
                                  routing_key='oq.testlogger.sublogger')
            timeout.wait()
            timeout.clear()
            # raising minimum level to make sure that info message
            # no longer can sneak in
            logger.setLevel(logging.WARNING)
            logsource.stop_on_timeout = True
            self.producer.publish(msg, routing_key='oq.testlogger.sublogger')
        finally:
            logger.removeHandler(handler)
            logsource.stop()
            logsource_thread.join()
        self.assertEqual(len(handler.buffer), 1)
        [record] = handler.buffer
        for key in msg:
            self.assertEqual(msg[key], getattr(record, key))

