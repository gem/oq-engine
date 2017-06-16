import sys
from celery import Celery
from openquake.engine.celeryconfig import (BROKER_URL, CELERY_RESULT_BACKEND,
                                           BROKER_CONNECTION_TIMEOUT)


def report():
    app = Celery('openquake', backend=CELERY_RESULT_BACKEND, broker=BROKER_URL)
    ins = app.control.inspect()

    total_workers = 0
    num_active_tasks = 0

    all_stats = ins.stats()
    if all_stats is None:
        print("No active workers")
        sys.exit(0)

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

    print('==========')
    print()
    print('Total workers:       %s' % total_workers)
    print('Active tasks:        %s' % num_active_tasks)
    print('Cluster utilization: %.2f%%' % (
        (float(num_active_tasks) / total_workers) * 100))
