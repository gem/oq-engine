#! /usr/bin/env python

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
The OpenQuake job supervisor supervisor process, spawned periodically
to respawn crashed :mod:`supervisors <openquake.supervising.supervisor>`.
"""
import multiprocessing

from openquake.db.models import OqJob
from openquake import supervising
from openquake.supervising.supervisor import supervise


def main():
    """
    Look through all jobs with status "running" and check
    the status of their supervisors: if one is missing --
    do :meth:`openquake.job.spawn_job_supervisor` for it.
    """
    qs = OqJob.objects.filter(status='running') \
                      .values_list('id', 'job_pid', 'supervisor_pid')
    for job_id, job_pid, supervisor_pid in qs:
        if not supervising.is_pid_running(supervisor_pid):
            proc = multiprocessing.Process(target=supervise,
                                           args=(job_id, job_pid))
            proc.start()


if __name__ == '__main__':
    main()
