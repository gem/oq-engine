# Copyright (c) 2011, GEM Foundation.
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


# -*- coding: utf-8 -*-
"""
Set up some system-wide loggers
TODO(jmc): init_logs should take filename, or sysout
TODO(jmc): support debug level per logger.

"""
import logging

from openquake import flags
FLAGS = flags.FLAGS

LEVELS = {'debug': logging.DEBUG,
          'info': logging.INFO,
          'warn': logging.WARNING,
          'error': logging.ERROR,
          'critical': logging.CRITICAL,
          # The default logging levels are: CRITICAL=50, ERROR=40, WARNING=30,
          # INFO=20, DEBUG=10, NOTSET=0
          # The 'validate' log level is defined here as 25 because it is 
          # considered to be less critical than a WARNING but slightly more
          # critical than INFO.
          'validate': 25}

RISK_LOG = logging.getLogger("risk")
HAZARD_LOG = logging.getLogger("hazard")
LOG = logging.getLogger()

def init_logs():
    """Load logging config, and set log levels based on flags"""
    
    level = LEVELS.get(FLAGS.debug, logging.ERROR)
    logging.basicConfig(level=level)
    logging.getLogger("amqplib").setLevel(logging.ERROR)
    
    LOG.setLevel(level)
    RISK_LOG.setLevel(level)
    HAZARD_LOG.setLevel(level)   

def make_job_logger(job_id):
    """Make a special logger object to be used just for a specific job. Acts
    like normal logging.Logger object, but has additional logging method called
    validate which basically wraps a call to logger.log() with the level
    automatically specified as 'validate'."""
    # 
    def _validate(msg, *args, **kwargs):
        """Basically a clone of the standard logger methods (like 'debug()')."""
        # 'close' validate_logger instance inside this wrapper method
        # this is nice because now we can just call logger_obj.validate()
        # to make log entries at the 'validate' level.
        return validate_logger.log(LEVELS.get('validate'), msg, *args, **kwargs)
    
    validate_logger = logging.getLogger(job_id)
    # monkey patch _validate into the logger object
    validate_logger.validate = _validate
    # now the 'validate' logging method can be called on this object

    validate_logger.setLevel(LEVELS.get('validate'))

    # log to file in the CWD
    log_file_path = "%s.log" % job_id
    handler = logging.FileHandler(log_file_path)
    validate_logger.addHandler(handler)
    return validate_logger
