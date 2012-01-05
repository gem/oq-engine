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


"""The 'Engine' is responsible for instantiating calculators and running jobs.
"""


import os

from django.db import close_connection

from openquake import logs

from openquake.flags import FLAGS
from openquake.job import Job
from openquake.supervising import supervisor

from openquake.db.models import OqCalculation
from openquake.hazard.calc import CALCULATORS as HAZ_CALCS
from openquake.risk.calc import CALCULATORS as RISK_CALCS


CALCS = dict(hazard=HAZ_CALCS, risk=RISK_CALCS)


def run_job(job_file, output_type):
    """
    Given a job_file, run the job.

    :param job_file: the path of the configuration file for the job
    :type job_file: string
    :param output_type: the desired format for the results, one of 'db', 'xml'
    :type output_type: string
    """
    a_job = Job.from_file(job_file, output_type)
    a_job.set_status('running')

    # closing all db connections to make sure they're not shared between
    # supervisor and job executor processes. otherwise if one of them closes
    # the connection it immediately becomes unavailable for other
    close_connection()

    job_pid = os.fork()
    if not job_pid:
        # job executor process
        try:
            logs.init_logs_amqp_send(level=FLAGS.debug, job_id=a_job.job_id)
            launch(a_job)
        except Exception, ex:
            logs.LOG.critical("Job failed with exception: '%s'" % str(ex))
            a_job.set_status('failed')
            raise
        else:
            a_job.set_status('succeeded')
        return

    supervisor_pid = os.fork()
    if not supervisor_pid:
        # supervisor process
        supervisor_pid = os.getpid()
        job = OqCalculation.objects.get(id=a_job.job_id)
        job.supervisor_pid = supervisor_pid
        job.job_pid = job_pid
        job.save()
        supervisor.supervise(job_pid, a_job.job_id)
        return

    # parent process

    # ignore Ctrl-C as well as supervisor process does. thus only
    # job executor terminates on SIGINT
    supervisor.ignore_sigint()
    # wait till both child processes are done
    os.waitpid(job_pid, 0)
    os.waitpid(supervisor_pid, 0)


def launch(a_job):
    """Based on the behavior specified in the configuration, mix in the correct
    behavior for job and execute it.

    :param a_job:
        :class:`openquake.job.Job` instance.
    """
    # TODO: This needs to be done as a pre-execution step of calculation.
    a_job._record_initial_stats()  # pylint: disable=W0212

    output_dir = os.path.join(a_job.base_path, a_job['OUTPUT_DIR'])
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for job_type in ('hazard', 'risk'):
        if not job_type.upper() in a_job.sections:
            continue

        calc_mode = a_job['CALCULATION_MODE']
        calc_class = CALCS[job_type][calc_mode]

        calculator = calc_class(a_job)

        calculator.execute()
