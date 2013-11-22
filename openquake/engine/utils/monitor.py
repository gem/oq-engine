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
Utility functions related to monitoring.
"""

from celery.task.control import inspect

from openquake.engine.db import models


def count_failed_nodes(job):
    """Check compute nodes and return the total number of failures.

    Please note that this function counts the total number of node
    failures that occurred during a calculation and *not* the number
    of currently failed nodes.

    :param job: The :class:`openquake.engine.db.models.OqJob` instance to use
    :return: the number of failures i.e. how many nodes went from "up" to
        "down" *at some time* during the calculation
    """
    live_nodes = _live_cnode_status()
    db_stats = _db_cnode_status(job)

    if not live_nodes and not db_stats:
        # No live compute nodes and nothing stored in the database; this will
        # never work -> indicate failure
        return -1

    def set_status(node, status):
        """Update the status of the given node in the database."""
        cs = db_stats[node]
        cs.current_status = status
        cs.save(using="job_init")

    # working nodes according to the database
    dworking_nodes = set(cs.node for cs in db_stats.values()
                         if cs.current_status == "up" and cs.failures == 0)
    # nodes that have failed at least once at some time during the calculation
    dfailed_nodes = set(cs.node for cs in db_stats.values() if cs.failures > 0)

    # Which working nodes stored in the db have gone bad/down?
    total_failures = len(dfailed_nodes)
    new_failed = dworking_nodes - live_nodes
    for node in new_failed:
        set_status(node, "down")
        total_failures += 1

    # Any entirely new nodes?
    new_nodes = live_nodes - set(db_stats.keys())
    for node in new_nodes:
        cs = models.CNodeStats(oq_job=job, node=node, current_status="up")
        cs.save(using="job_init")

    # Any nodes that came back after a failure?
    for node in live_nodes.intersection(dfailed_nodes):
        set_status(node, "up")

    return total_failures


def _live_cnode_status():
    """Get compute node status (from celery).

    The main reason this function exists is that mocking any celery artefact
    (for the purpose of testing) is a nightmare.

    :return: a set with the names of the live nodes
    """
    ins = inspect()
    live_nodes = ins.ping()
    # ping returns a dict like this:
    #   {'gemsun04': 'pong', 'gemsun01': 'pong', 'bigstar04': 'pong'}
    return set(live_nodes) if live_nodes else set()


def _db_cnode_status(job):
    """Get compute node status stored in the database.

    :param job: The :class:`openquake.engine.db.models.OqJob` instance to use
    :return: a potentially empty dictionary where the keys are node names
        and the values are either 'up' or 'down' e.g.
        `{"N1": "up", "N2": "down", "N3": "down"}`
    """
    dbi = models.CNodeStats.objects.filter(oq_job=job).order_by("current_ts")
    return dict((cs.node, cs) for cs in dbi)
