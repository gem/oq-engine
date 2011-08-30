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
   - signal through an amqp exchange the outcome of the job
"""

import logging
import os
import signal

from openquake.db.models import OqJob, ErrorMsg
from openquake import signalling
from openquake import supervising
from openquake import kvs


logging.basicConfig(level=logging.INFO)


def terminate_job(pid):
    """
    Terminate an openquake job by killing its process.

    :param pid: the process id
    :type pid: int
    """

    logging.info('Terminating job process %s', pid)

    os.kill(pid, signal.SIGKILL)


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


class SupervisorLogMessageConsumer(signalling.LogMessageConsumer):
    """
    Supervise an OpenQuake job by:

       - handling its messages
       - periodically checking that the job process is still running
    """
    def __init__(self, job_id, pid, **kwargs):
        super(SupervisorLogMessageConsumer, self).__init__(job_id, **kwargs)

        self.pid = pid

    def get_queue_name(self):
        """
        The name of the queue that will contain the messages of this consumer.
        """
        return get_supervisor_queue_name(self.job_id)

    def message_callback(self, msg):
        """
        Handles messages of severe level from the supervised job.
        """
        terminate_job(self.pid)

        signalling.signal_job_outcome(self.job_id, 'failed')

        update_job_status_and_error_msg(self.job_id, 'failed', msg.body)

        cleanup_after_job(self.job_id)

        raise StopIteration

    def timeout_callback(self):
        """
        On timeout expiration check if the job process is still running, and
        act accordingly if not.
        """
        if not supervising.is_pid_running(self.pid):
            logging.info('Process %s not running', self.pid)

            # see what status was left in the database by the exited job
            job_status = get_job_status(self.job_id)

            if job_status == 'succeeded':
                signalling.signal_job_outcome(self.job_id, 'succeeded')
            else:
                signalling.signal_job_outcome(self.job_id, 'failed')

                if job_status == 'running':
                    # The job crashed without having a chance to update the
                    # status in the database.  We do it here.
                    update_job_status_and_error_msg(self.job_id, 'failed',
                                                    'crash')

            cleanup_after_job(self.job_id)

            raise StopIteration


def get_supervisor_queue_name(job_id):
    """
    Return the name for the message queue of a job supervisor.
    """
    return 'supervisor-%s' % job_id


def bind_supervisor_queue(job_id):
    """
    Declare and bind the message queue used by the job supervisor.

    It is safe to call this function more than once.  If the exchange, queue or
    bindings already exists, this function won't create them again.
    """
    return signalling.declare_and_bind_queue(
        job_id, ('error', 'fatal'), get_supervisor_queue_name(job_id))


def supervise(pid, job_id):
    """
    Supervise a job process, entering a loop that ends only when the job
    terminates.

    :param pid: the process id
    :type pid: int
    :param job_id: the job id
    :type job_id: int
    """
    logging.info('Entering supervisor for job %s', job_id)

    with SupervisorLogMessageConsumer(
        job_id, pid, levels=('error', 'fatal'),
        timeout=0.1) as message_consumer:
        message_consumer.run()

    logging.info('Exiting supervisor for job %s', job_id)
