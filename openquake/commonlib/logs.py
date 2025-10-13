# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2010-2025 GEM Foundation
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
import os
import re
import getpass
import logging
from datetime import datetime, timezone
from openquake.baselib import config, zeromq, parallel, workerpool as w
from openquake.commonlib import readinput, dbapi

UTC = timezone.utc
LEVELS = {'debug': logging.DEBUG,
          'info': logging.INFO,
          'warn': logging.WARNING,
          'error': logging.ERROR,
          'critical': logging.CRITICAL}
SIMPLE_TYPES = (str, int, float, bool, datetime, list, tuple, dict, type(None))
CALC_REGEX = r'(calc|cache)_(\d+)\.hdf5'
MODELS = []  # to be populated in get_tag


def get_tag(job_ini):
    """
    :returns: the name of the model if job_ini belongs to the mosaic_dir
    """
    if not MODELS:  # first time
        MODELS.extend(readinput.read_mosaic_df(buffer=.1).code)
    splits = job_ini.split('/')  # es. /home/michele/mosaic/EUR/in/job.ini
    if len(splits) > 3 and splits[-3] in MODELS:
        return splits[-3]  # EUR
    return ''


def on_workers(action):
    master = w.WorkerMaster(-1)  # current job
    return getattr(master, action[8:])()  # workers_(stop|kill)


def dbcmd(action, *args):
    """
    A dispatcher to the database server.

    :param string action: database action to perform
    :param tuple args: arguments
    """
    # make sure the passed arguments are simple (i.e. not Django
    # QueryDict that cannot be deserialized without settings.py)
    for arg in args:
        if type(arg) not in SIMPLE_TYPES:
            raise TypeError(f'{arg} is not a simple type')
    dbhost = os.environ.get('OQ_DATABASE', config.dbserver.host)
    if (action.startswith('workers_') and config.zworkers.host_cores
          == '127.0.0.1 -1'):  # local zmq
        return on_workers(action)
    elif dbhost == '127.0.0.1' and getpass.getuser() != 'openquake':
        # no server mode, access the database directly
        if action.startswith('workers_'):
            return on_workers(action)
        from openquake.server.db import actions
        try:
            func = getattr(actions, action)
        except AttributeError:
            return dbapi.db(action, *args)
        else:
            return func(dbapi.db, *args)

    # send a command to the database
    tcp = 'tcp://%s:%s' % (dbhost, config.dbserver.port)
    sock = zeromq.Socket(tcp, zeromq.zmq.REQ, 'connect',
                         timeout=600)  # when the system is loaded
    with sock:
        res = sock.send((action,) + args)
        if isinstance(res, parallel.Result):
            return res.get()
    return res


def dblog(level: str, job_id: int, task_no: int, msg: str):
    """
    Log on the database
    """
    task = 'task #%d' % task_no
    return dbcmd('log', job_id, datetime.now(UTC), level, task, msg)


def get_datadir():
    """
    Extracts the path of the directory where the openquake data are stored
    from the environment ($OQ_DATADIR) or from the shared_dir in the
    configuration file.
    """
    datadir = os.environ.get('OQ_DATADIR')
    if not datadir:
        shared_dir = config.directory.shared_dir
        if shared_dir:
            user = getpass.getuser()
            # special case for /opt/openquake/openquake -> /opt/openquake
            datadir = os.path.join(shared_dir, user, 'oqdata').replace(
                'openquake/openquake', 'openquake')
        else:  # use the home of the user
            datadir = os.path.join(os.path.expanduser('~'), 'oqdata')
    return datadir


def get_calc_ids(datadir=None):
    """
    Extract the available calculation IDs from the datadir, in order.
    """
    datadir = datadir or get_datadir()
    if not os.path.exists(datadir):
        return []
    calc_ids = set()
    for f in os.listdir(datadir):
        mo = re.match(CALC_REGEX, f)
        if mo:
            calc_ids.add(int(mo.group(2)))
    return sorted(calc_ids)


def get_last_calc_id(datadir=None):
    """
    Extract the latest calculation ID from the given directory.
    If none is found, return 0.
    """
    datadir = datadir or get_datadir()
    calcs = get_calc_ids(datadir)
    if not calcs:
        return 0
    return calcs[-1]


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

    def emit(self, record):
        if record.levelname != 'CRITICAL':
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

    def emit(self, record):
        _update_log_record(self, record)
        super().emit(record)


class LogDatabaseHandler(logging.Handler):
    """
    Log stream handler
    """
    def __init__(self, job_id):
        super().__init__()
        self.job_id = job_id

    def emit(self, record):
        dbcmd('log', self.job_id, datetime.now(UTC), record.levelname,
              '%s/%s' % (record.processName, record.process),
              record.getMessage())


class LogContext:
    """
    Context manager managing the logging functionality
    """
    oqparam = None

    def __init__(self, params, log_level='info', log_file=None,
                 user_name=None, hc_id=None, host=None, tag=''):
        if not dbcmd("SELECT name FROM sqlite_master WHERE name='job'"):
            raise RuntimeError('You forgot to run oq engine --upgrade-db -y')
        self.log_level = log_level
        self.log_file = log_file
        self.user_name = user_name or getpass.getuser()
        self.params = params
        if 'inputs' not in self.params:  # for reaggregate
            self.tag = tag
        else:
            inputs = self.params['inputs']
            self.tag = tag or get_tag(inputs.get('job_ini', '<in-memory>'))
        if hc_id:
            self.params['hazard_calculation_id'] = hc_id
        calc_id = int(params.get('job_id', 0))
        if calc_id == 0:
            datadir = get_datadir()
            self.calc_id = dbcmd(
                'create_job', datadir,
                self.params['calculation_mode'],
                self.params.get('description', 'test'),
                user_name, hc_id, host)
            path = os.path.join(datadir, 'calc_%d.hdf5' % self.calc_id)
            if os.path.exists(path):  # sanity check on the calculation ID
                raise RuntimeError('There is a pre-existing file %s' % path)
            self.usedb = True
        else:
            # assume the calc_id was alreay created in the db
            assert calc_id > 0, calc_id
            self.calc_id = calc_id
            self.usedb = True

    def get_oqparam(self, validate=True):
        """
        :returns: an OqParam instance
        """
        if self.oqparam:  # set by submit_job
            return self.oqparam
        return readinput.get_oqparam(self.params, validate=validate)

    def __enter__(self):
        if not logging.root.handlers:  # first time
            level = LEVELS.get(self.log_level, self.log_level)
            logging.basicConfig(level=level, handlers=[])
        f = '[%(asctime)s #{} {}%(levelname)s] %(message)s'.format(
            self.calc_id, self.tag + ' ' if self.tag else '')
        self.handlers = [LogDatabaseHandler(self.calc_id)] \
            if self.usedb else []
        if self.log_file is None:
            # add a StreamHandler if not already there
            if not any(h for h in logging.root.handlers
                       if isinstance(h, logging.StreamHandler)):
                self.handlers.append(LogStreamHandler(self.calc_id))
        else:
            self.handlers.append(LogFileHandler(self.calc_id, self.log_file))
        for handler in self.handlers:
            handler.setFormatter(
                logging.Formatter(f, datefmt='%Y-%m-%d %H:%M:%S'))
            logging.root.addHandler(handler)
        if os.environ.get('NUMBA_DISABLE_JIT'):
            logging.warning('NUMBA_DISABLE_JIT is set')
        return self

    def __exit__(self, etype, exc, tb):
        if tb:
            if etype is SystemExit:
                dbcmd('finish', self.calc_id, 'aborted')
            else:
                # remove StreamHandler to avoid logging twice
                logging.root.removeHandler(self.handlers[-1])
                logging.exception(f'{etype.__name__}: {exc}')
                dbcmd('finish', self.calc_id, 'failed')
        else:
            dbcmd('finish', self.calc_id, 'complete')
        for handler in self.handlers:
            logging.root.removeHandler(handler)
        parallel.Starmap.shutdown()

    def __getstate__(self):
        # ensure pickleability
        return dict(calc_id=self.calc_id, params=self.params, usedb=self.usedb,
                    log_level=self.log_level, log_file=self.log_file,
                    user_name=self.user_name, oqparam=self.oqparam,
                    tag=self.tag)

    def __repr__(self):
        hc_id = self.params.get('hazard_calculation_id')
        return '<%s#%d, hc_id=%s>' % (self.__class__.__name__,
                                      self.calc_id, hc_id)


def init(job_ini, dummy=None, log_level='info', log_file=None,
         user_name=None, hc_id=None, host=None, tag=''):
    """
    :param job_ini: path to the job.ini file or dictionary of parameters
    :param dummy: ignored parameter, exists for backward compatibility
    :param log_level: the log level as a string or number
    :param log_file: path to the log file (if any)
    :param user_name: user running the job (None means current user)
    :param hc_id: parent calculation ID (default None)
    :param host: machine where the calculation is running (default None)
    :param tag: tag (for instance the model name) to show before the log
        message
    :returns: a LogContext instance

    1. initialize the root logger (if not already initialized)
    2. set the format of the root log handlers (if any)
    3. create a job in the database if job_or_calc == "job"
    4. return a LogContext instance associated to a calculation ID
    """
    if job_ini in ('job', 'calc'):  # backward compatibility
        job_ini = dummy
    if not isinstance(job_ini, dict):
        job_ini = readinput.get_params(job_ini)
    return LogContext(job_ini, log_level, log_file,
                      user_name, hc_id, host, tag)
