#! /usr/bin/env python

# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2012, GEM Foundation.
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
The OpenQuake job supervisor supervisor process, spawned periodically
to respawn crashed :mod:`supervisors <openquake.supervising.supervisor>`.
"""
import multiprocessing

from openquake.db.models import OqCalculation
from openquake import supervising
from openquake.supervising.supervisor import supervise


def main():
    """
    Look through all jobs with status "running" and check
    the status of their supervisors: if one is missing --
    do :meth:`openquake.job.spawn_job_supervisor` for it.
    """
    qs = OqCalculation.objects.filter(status='running') \
                      .values_list('id', 'job_pid', 'supervisor_pid')
    for job_id, job_pid, supervisor_pid in qs:
        if not supervising.is_pid_running(supervisor_pid):
            proc = multiprocessing.Process(target=supervise,
                                           args=(job_id, job_pid))
            proc.start()


if __name__ == '__main__':
    main()
