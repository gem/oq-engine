# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
This module implements supervise(), a function that monitors an OpenQuake job.

Upon job termination, successful or for an error of whatever level or gravity,
supervise() will:

   - ensure a cleanup of the resources used by the job
   - update status of the job record in the database
"""

import logging
import os
import signal
import socket
from datetime import datetime

from openquake import flags
from openquake.db.models import OqJob, ErrorMsg, JobStats
from openquake import supervising
from openquake import kvs
from openquake import logs


def terminate_job(pid, logger):
    """
    Terminate an openquake job by killing its process.

    :param pid: the process id
    :type pid: int
    """

    logger.info('Terminating job process %s', pid)

    os.kill(pid, signal.SIGKILL)


def record_job_stop_time(job_id, logger):
    """
    Call this when a job concludes (successful or not) to record the
    'stop_time' (using the current UTC time) in the uiapi.job_stats table.

    :param job_id: the job id
    :type job_id: int
    """
    logger.info('Recording stop time for job %s to job_stats', job_id)

    job_stats = JobStats.objects.get(oq_job=job_id)
    job_stats.stop_time = datetime.utcnow()
    job_stats.save(using='job_superv')


def cleanup_after_job(job_id, logger):
    """
    Release the resources used by an openquake job.

    :param job_id: the job id
    :type job_id: int
    """
    logger.info('Cleaning up after job %s', job_id)

    kvs.cache_gc(job_id, logger)


def get_job_status(job_id):
    """
    Return the status of the job stored in its database record.

    :param job_id: the id of the job
    :type job_id: int
    :return: the status of the job
    :rtype: string
    """

    return OqJob.objects.get(id=job_id).status


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
    job = OqJob.objects.get(id=job_id)
    job.status = status
    job.save()

    if error_msg:
        ErrorMsg.objects.using('job_superv')\
                        .create(oq_job=job, detailed=error_msg)


class CallbackLogHandler(logging.Handler):
    def __init__(self, callback):
        self.callback = callback
        super(CallbackLogHandler, self).__init__()

    def emit(self, record):
        self.callback(record)


class SupervisorLogMessageConsumer(logs.AMQPLogSource):
    """
    Supervise an OpenQuake job by:

       - handling its "critical" and "error" messages
       - periodically checking that the job process is still running
    """
    def __init__(self, job_id, job_pid, timeout=1):
        self.selflogger = logging.LoggerAdapter(
            logging.getLogger('oq.supervisor.%d' % job_id),
            extra={'job_id': job_id, 'hostname': socket.getfqdn()}
        )
        self.selflogger.info('Entering supervisor for job %s', job_id)
        logger_name = 'oq.job.%d' % job_id
        key = '%s.#' % logger_name
        super(SupervisorLogMessageConsumer, self).__init__(timeout=timeout,
                                                           routing_key=key)
        self.job_id = job_id
        self.job_pid = job_pid
        self.joblogger = logging.getLogger(key)
        self.jobhandler = CallbackLogHandler(callback=self.log_callback)
        self.joblogger.addHandler(self.jobhandler)

    def run(self):
        """
        Wrap superclass' method just to add cleanup.
        """
        super(SupervisorLogMessageConsumer, self).run()
        self.selflogger.info('Exiting supervisor for job %s', self.job_id)
        self.joblogger.removeHandler(self.jobhandler)

    def log_callback(self, record):
        """
        Handles messages of severe level from the supervised job.
        """
        if record.levelno < logging.ERROR:
            return

        terminate_job(self.job_pid, self.selflogger)

        update_job_status_and_error_msg(self.job_id, 'failed',
                                        record.getMessage())

        record_job_stop_time(self.job_id, self.selflogger)

        cleanup_after_job(self.job_id, self.selflogger)

        self.stop()

    def timeout_callback(self):
        """
        On timeout expiration check if the job process is still running, and
        act accordingly if not.
        """
        if not supervising.is_pid_running(self.job_pid):
            self.selflogger.info('Process %s not running', self.job_pid)

            # see what status was left in the database by the exited job
            job_status = get_job_status(self.job_id)

            self.selflogger.info('job finished with status %r', job_status)

            if job_status != 'succeeded':
                if job_status == 'running':
                    # The job crashed without having a chance to update the
                    # status in the database.  We do it here.
                    update_job_status_and_error_msg(self.job_id, 'failed',
                                                    'crash')

            record_job_stop_time(self.job_id, self.selflogger)

            cleanup_after_job(self.job_id, self.selflogger)

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
    """
    supervisor = SupervisorLogMessageConsumer(job_id, pid, timeout)
    supervisor.start()
    supervisor.join()
