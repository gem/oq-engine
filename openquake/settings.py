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


""" Settings for OpenQuake.  """

KVS_PORT = 6379
KVS_HOST = "localhost"

TEST_KVS_DB = 3

AMQP_HOST = "localhost"
AMQP_PORT = 5672
AMQP_USER = "guest"
AMQP_PASSWORD = "guest"
AMQP_VHOST = "/"
AMQP_EXCHANGE = 'oq.signalling'

# Keep the Python and Java formats in sync!
LOGGING_AMQP_FORMAT = '%(asctime)s %(loglevel)-5s %(processName)s' \
    ' [%(name)s] - Job %(job_id)s - %(message)s'
LOG4J_AMQP_FORMAT = '%d %-5p %X{processName} [%c] - Job %X{job_id} - %m'

LOGGING_STDOUT_FORMAT = '%(levelname)-5s %(processName)s' \
    ' [%(name)s] - %(message)s'
LOG4J_STDOUT_FORMAT = '%-5p %X{processName} [%c] - Job %X{job_id} - %m%n'

LOG4J_STDOUT_SETTINGS = {
    'log4j.rootLogger': '%(level)s, stdout',

    'log4j.appender.stdout': 'org.apache.log4j.ConsoleAppender',
    'log4j.appender.stdout.follow': 'true',
    'log4j.appender.stdout.layout': 'org.apache.log4j.PatternLayout',
    'log4j.appender.stdout.layout.ConversionPattern': LOG4J_STDOUT_FORMAT,
}

LOG4J_AMQP_SETTINGS = {
    'log4j.rootLogger': '%(level)s, amqp',

    'log4j.appender.amqp': 'org.gem.log.AMQPAppender',
    'log4j.appender.amqp.host': AMQP_HOST,
    'log4j.appender.amqp.port': str(AMQP_PORT),
    'log4j.appender.amqp.username': AMQP_USER,
    'log4j.appender.amqp.password': AMQP_PASSWORD,
    'log4j.appender.amqp.virtualHost': AMQP_VHOST,
    'log4j.appender.amqp.routingKeyPattern': 'log.%p.%X{job_id}',
    'log4j.appender.amqp.exchange': AMQP_EXCHANGE,
    'log4j.appender.amqp.layout': 'org.apache.log4j.PatternLayout',
    'log4j.appender.amqp.layout.ConversionPattern': LOG4J_AMQP_FORMAT,
}

LOGGING_BACKEND = 'console'
