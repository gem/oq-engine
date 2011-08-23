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


import errno
import logging
import os
import signal

from openquake.signalling import LogMessageConsumer
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


def is_pid_running(pid):
    """
    Check if a process is still running.

    :param pid: the process id
    :type pid: int

    :return: True if the process is running, False otherwise
    """
    try:
        os.kill(pid, 0)
    except Exception as e:
        return e.errno != errno.ESRCH
    else:
        return True


class SupervisorLogMessageConsumer(LogMessageConsumer):
    """
    Supervise an OpenQuake job by:

       - handling its messages
       - periodically checking that the job process is still running
    """
    def __init__(self, job_id, pid, **kwargs):
        super(SupervisorLogMessageConsumer, self).__init__(job_id, **kwargs)

        self.pid = pid

    def message_callback(self, msg):
        """
        Handles messages of severe level from the supervised job.
        """
        terminate_job(self.pid)

        cleanup_after_job(self.job_id)

        raise StopIteration

    def timeout_callback(self):
        """
        On timeout expiration check if the job process is still running, and
        act accordingly if not.
        """
        if not is_pid_running(self.pid):
            logging.info('Process %s not running', self.pid)

            cleanup_after_job(self.job_id)

            raise StopIteration


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
        job_id, pid, levels=('ERROR', 'FATAL'),
        timeout=0.1) as message_consumer:
        message_consumer.run()

    logging.info('Exiting supervisor for job %s', job_id)
