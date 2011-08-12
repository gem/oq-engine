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


from amqplib import client_0_8 as amqp
import logging
import os
import sys
import unittest

import jpype

from openquake import flags
from openquake import java
from openquake import logs
from openquake import settings

LOG_FILE_PATH = os.path.join(os.getcwd(), 'test_file_for_the_logs_module.log')


class PreserveJavaIO(object):
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

    @classmethod
    def tearDownClass(cls):
        # restore the java stdout and stderr that were trashed during this test
        jpype.java.lang.System.setOut(cls.old_java_out)
        jpype.java.lang.System.setErr(cls.old_java_err)


class LogsTestCase(PreserveJavaIO, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(LogsTestCase, cls).setUpClass()

        try:
            os.remove(LOG_FILE_PATH)
        except OSError:
            pass

    @classmethod
    def tearDownClass(cls):
        super(LogsTestCase, cls).tearDownClass()

        try:
            os.remove(LOG_FILE_PATH)
        except OSError:
            pass

    def setUp(self):
        # we init the logs before each test because nosetest redefines
        # sys.stdout and removes all the handlers from the rootLogger

        # reset logging config (otherwise will ignore logfile flag)
        root = logging.getLogger()
        for h in list(root.handlers):
            root.removeHandler(h)

        flags.FLAGS.debug = 'warn'
        flags.FLAGS.logfile = LOG_FILE_PATH
        logs.init_logs('warn')
        java.init_logs('warn')

    def tearDown(self):
        # reset logging config
        root = logging.getLogger()
        for h in list(root.handlers):
            root.removeHandler(h)

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


class AMQPLogTestBase(unittest.TestCase):
    def setup_queue(self):
        # connect to localhost and bind to a queue
        conn = amqp.Connection(host=settings.AMQP_HOST,
                               userid=settings.AMQP_USER,
                               password=settings.AMQP_PASSWORD,
                               virtual_host=settings.AMQP_VHOST)
        ch = conn.channel()
        ch.access_request(settings.AMQP_VHOST, active=False, read=True)
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


class JavaAMQPLogTestCase(AMQPLogTestBase):
    TOPIC = 'oq-unittest.topic'
    ROUTING_KEY = 'oq-unittest-log.*'

    def tearDown(self):
        # reconfigure Log4j with the default settings
        jvm = java.jvm()

        jvm.JClass("org.apache.log4j.BasicConfigurator").resetConfiguration()
        java.init_logs('warn')

    def setUp(self):
        jvm = java.jvm()

        props = jvm.JClass("java.util.Properties")()
        props.setProperty('log4j.rootLogger', 'DEBUG, rabbit')

        for key, value in [
            ('', 'org.gem.log.AMQPAppender'),
            ('.host', settings.AMQP_HOST),
            ('.port', str(settings.AMQP_PORT)),
            ('.username', settings.AMQP_USER),
            ('.password', settings.AMQP_PASSWORD),
            ('.virtualHost', settings.AMQP_VHOST),
            ('.routingKeyPattern', 'oq-unittest-log.%p'),
            ('.exchange', 'oq-unittest.topic'),
            ('.layout', 'org.apache.log4j.PatternLayout'),
            ('.layout.ConversionPattern', '%p - %m')]:
            props.setProperty('log4j.appender.rabbit' + key, value)

        jvm.JClass("org.apache.log4j.BasicConfigurator").resetConfiguration()
        jvm.JClass("org.apache.log4j.PropertyConfigurator").configure(props)

    def test_amqp_sanity(self):
        """We can talk to ourselves from Python using RabbitMQ"""
        conn, ch, qname = self.setup_queue()

        # now there is a queue, send a test message
        sender = java.AMQPConnection()
        sender.setHost(settings.AMQP_HOST)
        sender.setPort(settings.AMQP_PORT)
        sender.setUsername(settings.AMQP_USER)
        sender.setPassword(settings.AMQP_PASSWORD)
        sender.setVirtualHost(settings.AMQP_VHOST)
        sender.publish('oq-unittest.topic', 'oq-unittest-log.FOO', 0, 'WARN',
                       'Hi there')
        sender.close()

        # process the messaages
        messages = []

        def consume(msg):
            messages.append(msg)
            ch.basic_cancel(msg.consumer_tag)

        self.consume_messages(conn, ch, qname, consume)

        self.assertEquals(1, len(messages))
        self.assertEquals('Hi there', messages[0].body)

    def test_amqp_java_logger(self):
        """We can talk to ourselves from Java using RabbitMQ"""
        conn, ch, qname = self.setup_queue()

        # now there is a queue, send the log messages
        root_logger = jpype.JClass("org.apache.log4j.Logger").getRootLogger()
        root_logger.info('Info message')
        root_logger.warn('Warn message')

        # process the messages
        messages = []

        def consume(msg):
            messages.append(msg)

            if msg.body == 'WARN - Warn message':
                ch.basic_cancel(msg.consumer_tag)

        self.consume_messages(conn, ch, qname, consume)

        self.assertEquals(2, len(messages))

        self.assertEquals('INFO - Info message', messages[0].body)
        self.assertEquals('oq-unittest-log.INFO',
                          messages[0].delivery_info['routing_key'])

        self.assertEquals('WARN - Warn message', messages[1].body)
        self.assertEquals('oq-unittest-log.WARN',
                          messages[1].delivery_info['routing_key'])


class PythonAMQPLogTestCase(AMQPLogTestBase):
    TOPIC = 'oq-unittest.topic'
    ROUTING_KEY = 'oq-unittest-log.*'

    def setUp(self):
        self.amqp = logs.AMQPHandler(
            host=settings.AMQP_HOST,
            username=settings.AMQP_USER,
            password=settings.AMQP_PASSWORD,
            virtual_host=settings.AMQP_VHOST,
            exchange='oq-unittest.topic',
            routing_key='oq-unittest-log.%(levelname)s',
            level=logging.DEBUG)

        self.log = logging.getLogger('tests.PythonAMQPLogTestCase')
        self.log.setLevel(logging.DEBUG)
        self.log.addHandler(self.amqp)

    def tearDown(self):
        self.log.removeHandler(self.amqp)

    def test_amqp_logging(self):
        """We can talk to ourselves from Python using RabbitMQ"""
        conn, ch, qname = self.setup_queue()

        self.log.info('Info message')
        self.log.warn('Warn message')

        # process the messages
        messages = []

        def consume(msg):
            messages.append(msg)

            if msg.body == 'Warn message':
                ch.basic_cancel(msg.consumer_tag)

        self.consume_messages(conn, ch, qname, consume)

        self.assertEquals(2, len(messages))

        self.assertEquals('Info message', messages[0].body)
        self.assertEquals('oq-unittest-log.INFO',
                          messages[0].delivery_info['routing_key'])

        self.assertEquals('Warn message', messages[1].body)
        self.assertEquals('oq-unittest-log.WARNING',
                          messages[1].delivery_info['routing_key'])
