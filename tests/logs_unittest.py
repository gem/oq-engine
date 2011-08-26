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
import multiprocessing
import sys
import unittest

import jpype

from openquake import flags
from openquake import java
from openquake import logs
from openquake import job
from openquake.utils import config

from tests.utils.helpers import cleanup_loggers


class LogsTestCase(unittest.TestCase):
    def setUp(self):
        java.jvm()

    def test_java_logging(self):
        msg = 'This is a test java log entry'
        root_logger = jpype.JClass("org.apache.log4j.Logger").getRootLogger()
        other_logger = jpype.JClass("org.apache.log4j.Logger").getLogger('grr')

        root_logger.error(msg)
        other_logger.warn('warning message')
        other_logger.debug('this is verbose debug info')
        root_logger.fatal('something bad has happend')
        root_logger.info('information message')
        1/0
