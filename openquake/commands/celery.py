#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2018-2019 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import sys
try:
    from celery import Celery
except ImportError:
    pass
else:
    from openquake.baselib import sap
    from openquake.engine.celeryconfig import broker_url, result_backend

    def status():
        app = Celery('openquake', backend=result_backend, broker=broker_url)
        ins = app.control.inspect()

        total_workers = 0
        num_active_tasks = 0

        all_stats = ins.stats()
        if all_stats is None:
            sys.exit("No active workers")

        hostnames = []

        for hostname, stats in all_stats.items():
            num_procs = len(stats['pool']['processes'])
            total_workers += num_procs
            hostnames.append(hostname)

        ping = ins.ping()
        active = ins.active()

        for host in hostnames:
            print('==========')
            print('Host: %s' % host)
            if ping[host]['ok'] == 'pong':
                print('Status: Online')
            else:
                print('Status: Not Responding')
            print('Worker processes: %s' % len(
                all_stats[host]['pool']['processes']))

            worker_activity = active.get(host)
            if worker_activity is not None:
                print('Active tasks: %s' % len(worker_activity))
                num_active_tasks += len(worker_activity)

        print('==========\n')
        print('Total workers:       %s' % total_workers)
        print('Active tasks:        %s' % num_active_tasks)
        print('Cluster utilization: %.2f%%' % (
            (float(num_active_tasks) / total_workers) * 100))

    def inspect():
        app = Celery('openquake', backend=result_backend, broker=broker_url)
        actives = app.control.inspect().active()
        if not actives:
            print('There are no active tasks')
        else:
            for active in sum(actives.values(), []):
                print(active['hostname'], active['args'])

    @sap.script
    def celery(cmd):
        """
        Return information about the celery workers
        """
        globals()[cmd]()

    celery.arg('cmd', 'celery command',
               choices='status inspect'.split())
