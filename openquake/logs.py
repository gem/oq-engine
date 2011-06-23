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

    level = LEVELS.get(FLAGS.debug, 'warn')
    logging.getLogger("amqplib").setLevel(logging.ERROR)

    LOG.setLevel(level)
    RISK_LOG.setLevel(level)
    HAZARD_LOG.setLevel(level)

    # capture java logging (this is what celeryd does with the workers, we use
    # exactly the same system for bin/openquakes and the likes)
    redirect_stdouts_to_logger(LOG)
