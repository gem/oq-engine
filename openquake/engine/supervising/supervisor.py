# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2013, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.


"""
This module implements supervise(), a function that monitors an OpenQuake job.

Upon job termination, successful or for an error of whatever level or gravity,
supervise() will:

   - ensure a cleanup of the resources used by the job
   - update status of the job record in the database
"""

import celery.task.control
import logging
import os
import signal

from datetime import datetime

try:
    # setproctitle is optional external dependency
    # apt-get installl python-setproctitle or
    # http://pypi.python.org/pypi/setproctitle/
    from setproctitle import setproctitle
except ImportError:
    setproctitle = lambda title: None  # pylint: disable=C0103

from openquake.engine.db.models import JobStats
from openquake.engine.db.models import OqJob
from openquake.engine.db.models import Performance
from openquake.engine import kvs
from openquake.engine import logs


LOG_FORMAT = ('[%(asctime)s %(calc_domain)s #%(calc_id)s %(hostname)s '
              '%(levelname)s %(processName)s/%(process)s %(name)s] '
              '%(message)s')


def ignore_sigint():
    """
    Setup signal handler on SIGINT in order to ignore it.

    This is needed to avoid premature death of the supervisor and is called
    from :func:`openquake.engine.engine.run_job` for job parent process and
    from :func:`supervise` for supervisor process.
    """
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def terminate_job(pid):
    """
    Terminate an openquake job by killing its process.

    :param pid: the process id
    :type pid: int
    """

    logging.debug('Terminating job process %s', pid)

    os.kill(pid, signal.SIGKILL)


def record_job_stop_time(job_id):
    """
    Call this when a job concludes (successful or not) to record the
    'stop_time' (using the current UTC time) in the uiapi.job_stats table.

    :param job_id: the job id
    :type job_id: int
    """
    logging.debug('Recording stop time for job %s to job_stats', job_id)

    job_stats = JobStats.objects.get(oq_job=job_id)
    job_stats.stop_time = datetime.utcnow()
    job_stats.save(using='job_superv')


def cleanup_after_job(job_id, terminate):
    """
    Release the resources used by an openquake job.

    :param int job_id: the job id
    :param bool terminate: the celery revoke command terminate flag
    """
    logging.debug('Cleaning up after job %s', job_id)

    kvs.cache_gc(job_id)

    # Using the celery API, terminate and revoke and terminate any running
    # tasks associated with the current job.
    task_ids = _get_task_ids(job_id)
    if task_ids:
        logs.LOG.warn('Revoking %d tasks', len(task_ids))
    else:  # this is normal when OQ_NO_DISTRIBUTE=1
        logs.LOG.debug('No task to revoke')
    for tid in task_ids:
        celery.task.control.revoke(tid, terminate=terminate)
        logs.LOG.debug('Revoked task %s', tid)


def _get_task_ids(job_id):
    """
    Get all Celery task IDs for a given ``job_id``.
    """
    return Performance.objects.filter(
        oq_job=job_id, operation='storing task id', task_id__isnull=False)\
        .values_list('task_id', flat=True)


def get_job_status(job_id):
    """
    Return the status of the job stored in its database record.

    :param job_id: the id of the job
    :type job_id: int
    :return: the status of the job
    :rtype: string
    """

    return OqJob.objects.get(id=job_id).status


def update_job_status(job_id):
    """
    Store in the database the status of a job.

    :param int job_id: the id of the job
    """
    job = OqJob.objects.get(id=job_id)
    job.is_running = False
    job.save()


def _update_log_record(self, record):
    """
    Massage a log record before emitting it. Intended to be used by the
    custom log handlers defined in this module.
    """
    if not hasattr(record, 'hostname'):
        record.hostname = '-'
    if not hasattr(record, 'calc_domain'):
        record.calc_domain = self.calc_domain
    if not hasattr(record, 'calc_id'):
        record.calc_id = self.calc_id
    logger_name_prefix = 'oq.%s.%s' % (record.calc_domain, record.calc_id)
    if record.name.startswith(logger_name_prefix):
        record.name = record.name[len(logger_name_prefix):].lstrip('.')
        if not record.name:
            record.name = 'root'


class SupervisorLogStreamHandler(logging.StreamHandler):
    """
    Log stream handler
    """
    def __init__(self, calc_domain, calc_id):
        super(SupervisorLogStreamHandler, self).__init__()
        self.setFormatter(logging.Formatter(LOG_FORMAT))
        self.calc_domain = calc_domain
        self.calc_id = calc_id

    def emit(self, record):  # pylint: disable=E0202
        _update_log_record(self, record)
        super(SupervisorLogStreamHandler, self).emit(record)


class SupervisorLogFileHandler(logging.FileHandler):
    """
    Log file handler
    """
    def __init__(self, calc_domain, calc_id, log_file):
        super(SupervisorLogFileHandler, self).__init__(log_file)
        self.setFormatter(logging.Formatter(LOG_FORMAT))
        self.calc_domain = calc_domain
        self.calc_id = calc_id
        self.log_file = log_file

    def emit(self, record):  # pylint: disable=E0202
        _update_log_record(self, record)
        super(SupervisorLogFileHandler, self).emit(record)


def supervise(pid, job_id, log_file=None):
    """
    Supervise a job process, entering a loop that ends only when the job
    terminates.

    :param int pid:
        the process id
    :param int job_id:
        the job id
    :param str log_file:
        Optional log file location. If specified, log messages will be appended
        to this file. If not specified, log messages will be printed to the
        console.
    """
    the_job = OqJob.objects.get(id=job_id)
    calc_id = the_job.calculation.id
    calc_domain = 'hazard' if the_job.hazard_calculation else 'risk'

    # Set the name of this process (as reported by /bin/ps)
    setproctitle('openquake supervisor for %s calc_id=%s job_pid=%s'
                 % (calc_domain, calc_id, pid))
    ignore_sigint()

    start_logging(calc_id, calc_domain, log_file)


def start_logging(calc_id, calc_domain, log_file):
    """
    Add logging handlers to begin collecting log messages.

    :param int calc_id:
        Hazard or Risk calculation ID.
    :param str calc_domain:
        'hazard' or 'risk'
    :param str log_file:
        Log file path location. Can be `None`. If a path is specified, we will
        create a file handler for logging. Else, we just log to the console.
    """
    if log_file is not None:
        logging.root.addHandler(
            SupervisorLogFileHandler(calc_domain, calc_id, log_file)
        )
    else:
        logging.root.addHandler(
            SupervisorLogStreamHandler(calc_domain, calc_id)
        )
