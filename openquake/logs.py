# -*- coding: utf-8 -*-

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
Set up some system-wide loggers
TODO(jmc): init_logs should take filename, or sysout
TODO(jmc): support debug level per logger.

"""
from amqplib import client_0_8 as amqp
import logging

from celery.log import redirect_stdouts_to_logger

from openquake import flags
from openquake import settings

FLAGS = flags.FLAGS

LEVELS = {'debug': logging.DEBUG,
          'info': logging.INFO,
          'warn': logging.WARNING,
          'error': logging.ERROR,
          'critical': logging.CRITICAL}

# This parameter sets where bin/openquake and the likes will send their
# logging.  This parameter has not effect on the workers.  To have a similar
# effect on the workers use the celeryd --logfile parameter.
flags.DEFINE_string('logfile', '',
    'Path to the log file. Leave empty to log to stderr.')

RISK_LOG = logging.getLogger("risk")
HAZARD_LOG = logging.getLogger("hazard")
LOG = logging.getLogger()


def init_logs(log_type='console', level='warn'):
    """
    Initialize Python logging.

    The function might be called multiple times with different log levels.
    """

    if log_type == 'console':
        init_logs_stdout(level)
    else:
        init_logs_amqp(level)


def init_logs_stdout(level):
    """Load logging config, and set log levels based on flags"""

    logging_level = LEVELS.get(level, 'warn')

    # Add the logging handler to the root logger.  This will be a file or
    # stdout depending on the presence of the logfile parameter.
    #
    # Note that what we are doing here is just a simplified version of what the
    # standard logging.basicConfig is doing.  An important difference is that
    # we add our handler every time init_logs() is called, whereas basicConfig
    # does nothing if there is at least one handler (any handler) present.
    # This allows us to call init_logs multiple times during the unittest, to
    # reinstall our handler after nose (actually its logcapture plugin) throws
    # it away.
    found = False
    for hdlr in LOG.handlers:
        if (isinstance(hdlr, logging.FileHandler)
            or isinstance(hdlr, logging.StreamHandler)):
            found = True

    if not found:
        filename = FLAGS.get('logfile', '')
        if filename:
            hdlr = logging.FileHandler(filename, 'a')
        else:
            hdlr = logging.StreamHandler()

        hdlr.setFormatter(logging.Formatter(logging.BASIC_FORMAT, None))
        LOG.addHandler(hdlr)

    amqp_log = logging.getLogger("amqplib")
    amqp_log.setLevel(logging.ERROR)
    amqp_log.propagate = False

    LOG.setLevel(logging_level)
    RISK_LOG.setLevel(logging_level)
    HAZARD_LOG.setLevel(logging_level)

    # capture java logging (this is what celeryd does with the workers, we use
    # exactly the same system for bin/openquakes and the likes)
    redirect_stdouts_to_logger(LOG)


def init_logs_amqp(level):
    """Init Python and Java logging to log to AMQP"""

    logging_level = LEVELS.get(level, 'warn')

    # initialize Python logging
    found = any(isinstance(hdlr, AMQPHandler) for hdlr in LOG.handlers)

    if not found:
        hdlr = AMQPHandler(
            host=settings.AMQP_HOST,
            username=settings.AMQP_USER,
            password=settings.AMQP_PASSWORD,
            virtual_host=settings.AMQP_VHOST,
            exchange=settings.AMQP_EXCHANGE,
            routing_key='log.%(loglevel)s.%(job_id)s',
            level=logging.DEBUG)

        hdlr.setFormatter(logging.Formatter(logging.BASIC_FORMAT, None))
        LOG.addHandler(hdlr)

    logging.getLogger("amqplib").setLevel(logging.ERROR)

    LOG.setLevel(logging_level)
    RISK_LOG.setLevel(logging_level)
    HAZARD_LOG.setLevel(logging_level)


class AMQPHandler(logging.Handler):  # pylint: disable=R0902
    """
    Logging handler that sends log messages to AMQP

    :param host: AMQP `host:port` pair (port defaults to 5672)
    :param username: AMQP username
    :param password: AMQP password
    :param virtual_host: AMQP virtual host
    :param exchange: AMQP exchange name
    :param routing_key: AMQP routing key (can use the same interpolation
        values valid for a `logging` message format string)
    :param level: logging level
    """

    # mimic Log4j MDC
    MDC = dict()
    """
    A dictionary containing additional values that can be used for log message
    and routing key formatting.

    After doing::

        AMQPHandler.MDC['job_key'] = some_value

    the value can be interpolated in the log message and the routing key
    by using the normal `%(job_key)s` Python syntax.
    """  # pylint: disable=W0105

    LEVELNAMES = {
        'WARNING': 'WARN',
        'CRITICAL': 'FATAL',
    }

    # pylint: disable=R0913
    def __init__(self, host="localhost:5672", username="guest",
                 password="guest", virtual_host="/",
                 exchange="", routing_key="", level=logging.NOTSET):
        logging.Handler.__init__(self, level=level)
        self.host = host
        self.username = username
        self.password = password
        self.virtual_host = virtual_host
        self.exchange = exchange
        self.routing_key = logging.Formatter(routing_key)
        self.connection = None
        self.channel = None

    def _connect(self):
        """Create a new connection to the AMQP server"""
        if self.connection and self.channel:
            return self.channel

        self.connection = amqp.Connection(host=self.host,
                                          userid=self.username,
                                          password=self.password,
                                          virtual_host=self.virtual_host,
                                          insist=False)
        self.channel = self.connection.channel()

        return self.channel

    def _update_record(self, record):
        """
        If the user set some values in the `AMQPHandler.MDC` attribute,
        return a new :class:`logging.LogRecord` objects containing the
        original values plus the values contained in the `MDC`.
        """
        if not self.MDC:
            return record

        # create a new LogRecord object containing the custom keys in the
        # MDC class field
        args = self.MDC.copy()
        args.update(record.args)

        new_record = logging.LogRecord(
            name=record.name, level=record.levelno, pathname=record.pathname,
            lineno=record.lineno, msg=record.msg, args=[args],
            exc_info=record.exc_info, func=record.funcName)

        # the documentation says that formatters use .args; in reality
        # they reach directly into __dict__
        for key, value in self.MDC.items():
            if key not in new_record.__dict__:
                new_record.__dict__[key] = value

        new_record.__dict__['loglevel'] = \
            self.LEVELNAMES.get(new_record.levelname, new_record.levelname)

        return new_record

    def emit(self, record):
        channel = self._connect()
        full_record = self._update_record(record)
        msg = amqp.Message(body=self.format(full_record))
        routing_key = self.routing_key.format(full_record)

        channel.basic_publish(msg, exchange=self.exchange,
                              routing_key=routing_key)
