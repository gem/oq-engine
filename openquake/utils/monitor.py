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


def monitor_compute_nodes(job):
    """Check compute nodes and return the total number of failures.

    Please note that this function counts the total number of node
    failures that occurred during a calculation and *not* the number
    of currently failed nodes.

    :param job: The :class:`openquake.db.models.OqJob` instance to use
    :return: the number of failures i.e. how many nodes went from "up" to
        "down" or "error" *at some time* during the calculation
    """
    live_stats = _live_cnode_status()
    db_stats = _db_cnode_status(job)

    # working nodes according to live stats
    lworking_nodes = set(node for node, status in live_stats.iteritems()
                         if status == "OK")
    # working nodes according to the database
    dworking_nodes = set(cs.node for cs in db_stats.values()
                         if cs.failures == 0)

    # Which working nodes stored in the db have gone bad/down?
    old_failed = set(cs.node for cs in db_stats.values()
                       if cs.current_status != "up")
    total_failures = len(old_failed)
    new_failed = dworking_nodes - lworking_nodes
    for node in new_failed:
        status = "error" if node in live_stats else "down"
        cs = db_stats[node]
        cs.previous_status = cs.current_status
        cs.current_status = status
        cs.save(using="job_superv")
        total_failures += 1

    # Any entirely new nodes?
    new_nodes = set(live_stats.keys()) - set(db_stats.keys())
    for node in new_nodes:
        status = "up" if live_stats[node] == "OK" else "error"
        cs = models.CNodeStats(oq_job=job, node=node, current_status=status)
        cs.save(using="job_superv")

    # Any nodes that came back after a failure?
    recovered_nodes = lworking_nodes.intersection(old_failed)
    for node in recovered_nodes:
        cs = db_stats[node]
        cs.previous_status = cs.current_status
        cs.current_status = "up"
        cs.save(using="job_superv")

    return total_failures


def _live_cnode_status():
    """Get compute node status (from celery).

    :return: a dict with compute node status info e.g.
        `{"oqt": "OK", "usc": "ERROR"}`
    """
    csi = subprocess.check_output("cd /usr/openquake; celeryctl status -C",
                                  shell=True)
    csi = csi.splitlines()
    # now we should have data like this:
    # ['gemsun02: OK', 'gemsun01: OK', 'gemsun03: OK', 'gemsun04: OK',
    #  'gemmicro02: OK', 'bigstar04: OK', 'gemmicro01: OK', '',
    #  '7 nodes online.']
    return dict(tuple(cs.split(": ")) for cs in csi if cs.find(":") > -1)


def _db_cnode_status(job):
    """Get compute node status stored in the database.

    :param job: The :class:`openquake.db.models.OqJob` instance to use
    :return: a potentially empty dictionary where the keys are node names
        and the values are either 'up' or 'down' e.g.
        `{"N1": "up", "N2": "down", "N3": "error"}`
    """
    dbi = models.CNodeStats.objects.filter(oq_job=job).order_by("current_ts")
    return dict((cs.node, cs) for cs in dbi)
