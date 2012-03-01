# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2012, GEM Foundation.
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
This module implements supervise(), a function that monitors an OpenQuake job.

Upon job termination, successful or for an error of whatever level or gravity,
supervise() will:

   - ensure a cleanup of the resources used by the job
   - update status of the job record in the database
"""

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

from openquake.db.models import OqCalculation, ErrorMsg, CalcStats
from openquake import supervising
from openquake import kvs
from openquake import logs
from openquake.utils import stats


def ignore_sigint():
    """
    Setup signal handler on SIGINT in order to ignore it.

    This is needed to avoid premature death of the supervisor and is called
    from :func:`openquake.engine.run_calculation` for job parent process and
    from :func:`supervise` for supervisor process.
    """
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def terminate_job(pid):
    """
    Terminate an openquake job by killing its process.

    :param pid: the process id
    :type pid: int
    """

    logging.info('Terminating job process %s', pid)

    os.kill(pid, signal.SIGKILL)


def record_job_stop_time(job_id):
    """
    Call this when a job concludes (successful or not) to record the
    'stop_time' (using the current UTC time) in the uiapi.calc_stats table.

    :param job_id: the job id
    :type job_id: int
    """
    logging.info('Recording stop time for job %s to calc_stats', job_id)

    calc_stats = CalcStats.objects.get(oq_calculation=job_id)
    calc_stats.stop_time = datetime.utcnow()
    calc_stats.save(using='job_superv')


def cleanup_after_job(job_id):
    """
    Release the resources used by an openquake job.

    :param job_id: the job id
    :type job_id: int
    """
    logging.info('Cleaning up after job %s', job_id)

    kvs.cache_gc(job_id)


def get_job_status(job_id):
    """
    Return the status of the job stored in its database record.

    :param job_id: the id of the job
    :type job_id: int
    :return: the status of the job
    :rtype: string
    """

    return OqCalculation.objects.get(id=job_id).status


def update_job_status_and_error_msg(job_id, status, error_msg=None):
    """
    Store in the database the status of a job and optionally an error message.

    :param job_id: the id of the job
    :type job_id: int
    :param status: the status of the job, e.g. 'failed'
    :type status: string
    :param error_msg: the error message, if any
    :type error_msg: string or None
    """
    job = OqCalculation.objects.get(id=job_id)
    job.status = status
    job.save()

    if error_msg:
        ErrorMsg.objects.using('job_superv')\
                        .create(oq_calculation=job, detailed=error_msg)


class SupervisorLogHandler(logging.StreamHandler):
    """
    Log handler intended to be used with :class:`SupervisorLogMessageConsumer`.
    """
    LOG_FORMAT = '[%(asctime)s #%(job_id)s %(hostname)s %(levelname)s ' \
                 '%(processName)s/%(process)s %(name)s] %(message)s'

    def __init__(self, job_id):
        super(SupervisorLogHandler, self).__init__()
        self.setFormatter(logging.Formatter(self.LOG_FORMAT))
        self.job_id = job_id

    def emit(self, record):  # pylint: disable=E0202
        if not hasattr(record, 'hostname'):
            record.hostname = '-'
        if not hasattr(record, 'job_id'):
            record.job_id = self.job_id
        logger_name_prefix = 'oq.job.%s' % record.job_id
        if record.name.startswith(logger_name_prefix):
            record.name = record.name[len(logger_name_prefix):].lstrip('.')
            if not record.name:
                record.name = 'root'
        super(SupervisorLogHandler, self).emit(record)


class SupervisorLogMessageConsumer(logs.AMQPLogSource):
    """
    Supervise an OpenQuake job by:

       - handling its "critical" and "error" messages
       - periodically checking that the job process is still running
    """
    # Failure counter check delay, translates to 20 seconds with the current
    # settings.
    FCC_DELAY = 20

    def __init__(self, job_id, job_pid, timeout=1):
        self.selflogger = logging.getLogger('oq.job.%s.supervisor' % job_id)
        self.selflogger.info('Entering supervisor for job %s', job_id)
        logger_name = 'oq.job.%s' % job_id
        key = '%s.#' % logger_name
        super(SupervisorLogMessageConsumer, self).__init__(timeout=timeout,
                                                           routing_key=key)
        self.job_id = job_id
        self.job_pid = job_pid
        self.joblogger = logging.getLogger(logger_name)
        self.jobhandler = logging.Handler(logging.ERROR)
        self.jobhandler.emit = self.log_callback
        self.joblogger.addHandler(self.jobhandler)
        # Failure counter check delay value
        self.fcc_delay_value = 0

    def run(self):
        """
        Wrap superclass' method just to add cleanup.
        """
        started = datetime.utcnow()
        super(SupervisorLogMessageConsumer, self).run()
        stopped = datetime.utcnow()
        self.selflogger.info('Job %s finished in %s',
                             self.job_id, stopped - started)
        self.joblogger.removeHandler(self.jobhandler)
        self.selflogger.info('Exiting supervisor for job %s', self.job_id)

    def log_callback(self, record):
        """
        Handles messages of severe level from the supervised job.
        """
        if record.name == self.selflogger.name:
            # ignore error log messages sent by selflogger.
            # this way we don't try to kill the job if its
            # process has crashed (or has been stopped).
            # we emit selflogger's error messages from
            # timeout_callback().
            return

        terminate_job(self.job_pid)

        update_job_status_and_error_msg(self.job_id, 'failed',
                                        record.getMessage())

        record_job_stop_time(self.job_id)

        cleanup_after_job(self.job_id)

        self.stop()

    def timeout_callback(self):
        """
        On timeout expiration check if the job process is still running
        and whether it experienced any failures.

        Terminate the job process in the latter case.
        """
        def failure_counters_need_check():
            """Return `True` if failure counters should be checked."""
            self.fcc_delay_value += 1
            result = self.fcc_delay_value >= self.FCC_DELAY
            if result:
                self.fcc_delay_value = 0
            return result

        process_stopped = job_failed = False
        message = None

        if not supervising.is_pid_running(self.job_pid):
            process_stopped = True
        elif failure_counters_need_check():
            # Job process is still running.
            failures = stats.failure_counters(self.job_id)
            if failures:
                terminate_job(self.job_pid)
                message = "job terminated with failures: %s" % failures
                job_failed = True

        if job_failed or process_stopped:
            job_status = get_job_status(self.job_id)
            if process_stopped and job_status == 'succeeded':
                message = 'job process %s succeeded' % self.job_pid
                self.selflogger.info(message)
            elif job_status == 'running':
                # The job crashed without having a chance to update the
                # status in the database, or it has been running even though
                # there were failures. We update the job status here.
                if process_stopped:
                    message = ('job process %s crashed or terminated'
                               % self.job_pid)
                self.selflogger.error(message)
                update_job_status_and_error_msg(self.job_id, 'failed',
                                                message)

            record_job_stop_time(self.job_id)
            cleanup_after_job(self.job_id)
            raise StopIteration()


def supervise(pid, job_id, timeout=1):
    """
    Supervise a job process, entering a loop that ends only when the job
    terminates.

    :param pid: the process id
    :type pid: int
    :param job_id: the job id
    :type job_id: int
    :param timeout: timeout value in seconds
    :type timeout: float
    :param str log_level:
        One of 'debug', 'info', 'warn', 'error', or 'critical'.
    """
    # Set the name of this process (as reported by /bin/ps)
    setproctitle('openquake supervisor for job_id=%s job_pid=%s'
                 % (job_id, pid))
    ignore_sigint()

    logging.root.addHandler(SupervisorLogHandler(job_id))

    supervisor = SupervisorLogMessageConsumer(job_id, pid, timeout)
    supervisor.run()
