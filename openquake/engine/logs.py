# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2010-2016 GEM Foundation
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

import os.path
import logging
import getpass
from datetime import datetime
from contextlib import contextmanager
from multiprocessing.connection import Client
from openquake.engine.utils.config import DBS_ADDRESS, DBS_AUTHKEY


# Place the new level between info and warning
logging.PROGRESS = 25
logging.addLevelName(logging.PROGRESS, "PROGRESS")

LEVELS = {'debug': logging.DEBUG,
          'info': logging.INFO,
          'warn': logging.WARNING,
          'progress': logging.PROGRESS,
          'error': logging.ERROR,
          'critical': logging.CRITICAL}

LOG_FORMAT = ('[%(asctime)s job #%(job_id)s %(hostname)s '
              '%(levelname)s %(processName)s/%(process)s] %(message)s')

LOG = logging.getLogger()

USER = getpass.getuser()

if USER == 'openquake':  # direct access to the database
    from openquake.server.db import actions

    def dbcmd(action, *args):
        return getattr(actions, action)(*args)

else:  # mediated access via the dbserver
    def dbcmd(action, *args):
        """
        A dispatcher to the database server.

        :param action: database action to perform
        :param args: arguments
        """
        client = Client(DBS_ADDRESS, authkey=DBS_AUTHKEY)
        try:
            client.send((action,) + args)
            res, etype = client.recv()
        finally:
            client.close()
        if etype:
            raise etype(res)
        return res


def touch_log_file(log_file):
    """
    If a log file destination is specified, attempt to open the file in
    'append' mode ('a'). If the specified file is not writable, an
    :exc:`IOError` will be raised.
    """
    open(os.path.abspath(log_file), 'a').close()


def _log_progress(msg, *args, **kwargs):
    """
    Log the message using the progress reporting logging level.

    ``args`` and ``kwargs`` are the same as :meth:`logging.Logger.debug`,
    except that this method has an additional possible keyword: ``indent``.

    Normally, progress messages are logged with a '** ' prefix. If ``indent``
    is `True`, messages will be logged with a '**  >' prefix.

    If ``indent`` is not specified, it will default to `False`.
    """
    indent = kwargs.get('indent')

    if indent is None:
        indent = False
    else:
        # 'indent' is an invalid kwarg for the logger's _log method
        # we need to remove it before we call _log:
        del kwargs['indent']

    if indent:
        prefix = '**  >'
    else:
        prefix = '** '

    msg = '%s %s' % (prefix, msg)
    LOG._log(logging.PROGRESS, msg, args, **kwargs)
LOG.progress = _log_progress


def set_level(level):
    """
    Initialize logs to write records with level `level` or above.
    """
    logging.root.setLevel(LEVELS.get(level, logging.WARNING))


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
        super(LogStreamHandler, self).__init__()
        self.setFormatter(logging.Formatter(LOG_FORMAT))
        self.job_id = job_id

    def emit(self, record):  # pylint: disable=E0202
        _update_log_record(self, record)
        super(LogStreamHandler, self).emit(record)


class LogFileHandler(logging.FileHandler):
    """
    Log file handler
    """
    def __init__(self, job_id, log_file):
        super(LogFileHandler, self).__init__(log_file)
        self.setFormatter(logging.Formatter(LOG_FORMAT))
        self.job_id = job_id
        self.log_file = log_file

    def emit(self, record):  # pylint: disable=E0202
        _update_log_record(self, record)
        super(LogFileHandler, self).emit(record)


class LogDatabaseHandler(logging.Handler):
    """
    Log stream handler
    """
    def __init__(self, job_id):
        super(LogDatabaseHandler, self).__init__()
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
         one of debug, info, warn, progress, error, critical
    :param log_file:
         log file path (if None, logs on stdout only)
    """
    handlers = [LogDatabaseHandler(job_id)]  # log on db always
    if log_file is None:
        handlers.append(LogStreamHandler(job_id))
    else:
        handlers.append(LogFileHandler(job_id, log_file))
    for handler in handlers:
        logging.root.addHandler(handler)
    set_level(log_level)
    try:
        yield
    finally:
        # sanity check to make sure that the logging on file is working
        if log_file and os.path.getsize(log_file) == 0:
            logging.root.warn('The log file %s is empty!?' % log_file)
        for handler in handlers:
            logging.root.removeHandler(handler)
