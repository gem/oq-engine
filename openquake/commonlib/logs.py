# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2010-2021 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.
"""
Set up some system-wide loggers
"""
import logging
from datetime import datetime
from contextlib import contextmanager
from openquake.commonlib.datastore import dbcmd, init  # keep it here!

LEVELS = {'debug': logging.DEBUG,
          'info': logging.INFO,
          'warn': logging.WARNING,
          'error': logging.ERROR,
          'critical': logging.CRITICAL}


def _update_log_record(self, record):
    """
    Massage a log record before emitting it. Intended to be used by the
    custom log handlers defined in this module.
    """
    if not hasattr(record, 'hostname'):
        record.hostname = '-'
    if not hasattr(record, 'job_id'):
        record.job_id = self.job_id


class LogStreamHandler(logging.StreamHandler):
    """
    Log stream handler
    """
    def __init__(self, job_id):
        super().__init__()
        self.job_id = job_id

    def emit(self, record):  # pylint: disable=E0202
        _update_log_record(self, record)
        super().emit(record)


class LogFileHandler(logging.FileHandler):
    """
    Log file handler
    """
    def __init__(self, job_id, log_file):
        super().__init__(log_file)
        self.job_id = job_id
        self.log_file = log_file

    def emit(self, record):  # pylint: disable=E0202
        _update_log_record(self, record)
        super().emit(record)


class LogDatabaseHandler(logging.Handler):
    """
    Log stream handler
    """
    def __init__(self, job_id):
        super().__init__()
        self.job_id = job_id

    def emit(self, record):  # pylint: disable=E0202
        if record.levelno >= logging.INFO:
            dbcmd('log', self.job_id, datetime.utcnow(), record.levelname,
                  '%s/%s' % (record.processName, record.process),
                  record.getMessage())


@contextmanager
def handle(job_id, log_level='info', log_file=None):
    """
    Context manager adding and removing log handlers.

    :param job_id:
         ID of the current job
    :param log_level:
         one of debug, info, warn, error, critical
    :param log_file:
         log file path (if None, logs on stdout only)
    """
    handlers = [LogDatabaseHandler(job_id)]  # log on db always
    if log_file is None:
        # add a StreamHandler if not already there
        if not any(h for h in logging.root.handlers
                   if isinstance(h, logging.StreamHandler)):
            handlers.append(LogStreamHandler(job_id))
    else:
        handlers.append(LogFileHandler(job_id, log_file))
    for handler in handlers:
        logging.root.addHandler(handler)
    init(job_id, LEVELS.get(log_level, logging.WARNING))
    try:
        yield
    finally:
        for handler in handlers:
            logging.root.removeHandler(handler)
