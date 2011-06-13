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
import logging

from celery.log import redirect_stdouts_to_logger

from openquake import flags
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


def init_logs():
    """Load logging config, and set log levels based on flags"""

    filename = FLAGS.get('logfile', '')
    if not filename:
        filename = None

    level = LEVELS.get(FLAGS.debug, logging.ERROR)
    logging.basicConfig(filename=filename, level=level)
    logging.getLogger("amqplib").setLevel(logging.ERROR)

    # capture java logging (this is what celeryd does with the workers, we use
    # exactly the same system for bin/openquakes and the likes)
    redirect_stdouts_to_logger(LOG)

    LOG.setLevel(level)
    RISK_LOG.setLevel(level)
    HAZARD_LOG.setLevel(level)
