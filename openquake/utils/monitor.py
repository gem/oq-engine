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
Utility functions related to monitoring.
"""


import subprocess

from openquake.db import models


def monitor_celery_nodes(job_id):
    """Check what celery nodes are running and return the delta (if any).

    :param int job_id: identifier of the job at hand
    :return: a 2-tuple where the first and second element is a list of celery
        nodes that became available and unavailable since the last call.
    """
    ccs = _get_celery_status()
    dbi = _get_db_status()


def _get_celery_status():
    """Call `celeryctl status` and return the results.

    :return: a list of strings with celery node status info e.g.
        ['gemsun02: OK', 'gemsun01: OK', '', '2 nodes online.']
    """
    csi = subprocess.check_output("cd /usr/openquake; celeryctl status -C",
                                  shell=True)
    csi = csi.splitlines()
    # now we should have data like this:
    # ['gemsun02: OK', 'gemsun01: OK', 'gemsun03: OK', 'gemsun04: OK',
    #  'gemmicro02: OK', 'bigstar04: OK', 'gemmicro01: OK', '',
    #  '7 nodes online.']
    return dict(tuple(cs.split(": ")) for cs in csi if cs.find(":") > -1)


def _get_db_status(job_id):
    """Get the compute node information stored in the database.

    :param int job_id: identifier of the job at hand
    :return: a potentially empty dictionary where the keys are node names
        and the values are either 'up' or 'down'.
    """
    dbi = models.NodeStats.objects.filter(oq_job__id=job_id).\
                                     order_by("updated_at")
    return dict((ns.node, ns.status) for ns in dbi)
