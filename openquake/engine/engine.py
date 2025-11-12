# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2010-2025 GEM Foundation
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
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

"""Engine: A collection of fundamental functions for initializing and running
calculations."""

import os
import re
import sys
import json
import time
import pickle
import socket
import signal
import getpass
import logging
import platform
import functools
from os.path import getsize
from datetime import datetime, timezone
import psutil
import h5py
import numpy
try:
    from setproctitle import setproctitle
except ImportError:
    def setproctitle(title):
        "Do nothing"
from urllib.request import urlopen, Request
from openquake.baselib.python3compat import decode
from openquake.baselib import parallel, general, config, slurm, workerpool as w
from openquake.commonlib.oqvalidation import OqParam
from openquake.commonlib import readinput, logs
from openquake.calculators import base
from openquake.calculators.base import expose_outputs


UTC = timezone.utc
USER = getpass.getuser()
OQ_API = 'https://api.openquake.org'

MB = 1024 ** 2
_PID = os.getpid()  # the PID
_PPID = os.getppid()  # the controlling terminal PID

GET_JOBS = '''--- executing or submitted
SELECT * FROM job WHERE status IN ('executing', 'submitted')
AND host=?x AND is_running=1 AND pid > 0 ORDER BY id'''


def get_zmq_ports():
    """
    :returns: an array with the receiver ports
    """
    start, stop = config.dbserver.receiver_ports.split('-')
    return numpy.arange(int(start), int(stop))


def set_concurrent_tasks_default(calc):
    """
    Look at the number of available workers and update the parameter
    OqParam.concurrent_tasks.default. Abort the calculations if no
    workers are available. Do nothing for trivial distributions.
    """
    dist = parallel.oq_distribute()
    if dist in ('zmq', 'slurm'):
        master = w.WorkerMaster(calc.datastore.calc_id)
        num_workers = sum(total for host, running, total in master.wait())
        if num_workers == 0:
            logging.critical("No live compute nodes, aborting calculation")
            logs.dbcmd('finish', calc.datastore.calc_id, 'failed')
            sys.exit(1)

        parallel.Starmap.CT = num_workers * 2
        OqParam.concurrent_tasks.default = num_workers * 2
    else:
        num_workers = parallel.num_cores
    if dist == 'no':
        logging.warning('Disabled distribution')
    else:
        logging.warning('Using %d %s workers', num_workers, dist)


class MasterKilled(KeyboardInterrupt):
    "Exception raised when a job is killed manually"


def manage_signals(job_id, signum, _stack):
    """
    Convert a SIGTERM into a SystemExit exception and a SIGINT/SIGHUP into
    a MasterKilled exception with an appropriate error message.

    :param int signum: the number of the received signal
    :param _stack: the current frame object, ignored
    """
    if signum == signal.SIGINT:
        raise MasterKilled('The openquake master process was killed manually')

    if signum == signal.SIGTERM:
        sys.exit(f'Killed {job_id}')

    if hasattr(signal, 'SIGHUP'):
        # kill the calculation only if os.getppid() != _PPID, i.e. the
        # controlling terminal died; in the workers, do nothing
        # Note: there is no SIGHUP on Windows
        if signum == signal.SIGHUP and os.getppid() != _PPID:
            raise MasterKilled(
                'The openquake master lost its controlling terminal')


def register_signals(job_id):
    # register the manage_signals callback for SIGTERM, SIGINT, SIGHUP;
    # when using the Django development server this module is imported by a
    # thread, so one gets a `ValueError: signal only works in main thread` that
    # can be safely ignored
    manage = functools.partial(manage_signals, job_id)
    try:
        signal.signal(signal.SIGTERM, manage)
        signal.signal(signal.SIGINT, manage)
        if hasattr(signal, 'SIGHUP'):
            # Do not register our SIGHUP handler if running with 'nohup'
            if signal.getsignal(signal.SIGHUP) != signal.SIG_IGN:
                signal.signal(signal.SIGHUP, manage)
    except ValueError:
        pass


def poll_queue(job_id, poll_time):
    """
    Check the queue of executing/submitted jobs and exit when there is
    a free slot.
    """
    try:
        host = socket.gethostname()
    except Exception:  # gaierror
        host = None
    offset = config.distribution.serialize_jobs - 1
    if offset >= 0:
        first_time = True
        while True:
            running = logs.dbcmd(GET_JOBS, host)
            previous = [job.id for job in running if job.id < job_id - offset]
            if previous:
                if first_time:
                    logs.dbcmd('update_job', job_id,
                               {'status': 'submitted', 'pid': _PID})
                    first_time = False
                    # the logging is not yet initialized, so use a print
                    print('Waiting for jobs %s' % ' '.join(map(str, previous)))
                time.sleep(poll_time)
            else:
                break


def run_calc(log):
    """
    Run a calculation.

    :param log:
        LogContext of the current job
    """
    register_signals(log.calc_id)
    setproctitle('oq-job-%d' % log.calc_id)
    with log:
        # check the available memory before starting
        while True:
            used_mem = psutil.virtual_memory().percent
            if used_mem < 80:  # continue if little memory is in use
                break
            logging.info('Memory occupation %d%%, the user should free '
                         'some memory', used_mem)
            time.sleep(5)
        oqparam = log.get_oqparam()
        calc = base.calculators(oqparam, log.calc_id)
        try:
            hostname = socket.gethostname()
        except Exception:  # gaierror
            hostname = 'localhost'
        logging.info('%s@%s running %s [--hc=%s]',
                     USER,
                     hostname,
                     calc.oqparam.inputs['job_ini'],
                     calc.oqparam.hazard_calculation_id)
        obsolete_msg = check_obsolete_version(oqparam.calculation_mode)
        # NB: the warning should not be logged for users with
        # an updated LTS version
        if obsolete_msg:
            logging.warning(obsolete_msg)
        calc.from_engine = True
        set_concurrent_tasks_default(calc)
        t0 = time.time()
        calc.run(shutdown=True)
        logging.info('Exposing the outputs to the database')
        expose_outputs(calc.datastore)
        calc.datastore.close()
        outs = '\n'.join(logs.dbcmd('list_outputs', log.calc_id, False))
        logging.info(outs)
        path = calc.datastore.filename
        size = general.humansize(getsize(path))
        logging.info(
            'Stored %s on %s in %d seconds', size, path, time.time() - t0)
        # sanity check to make sure that the logging on file is working
        if (log.log_file and log.log_file != os.devnull and
                getsize(log.log_file) == 0):
            logging.warning('The log file %s is empty!?' % log.log_file)
    return calc


def check_directories(calc_id):
    """
    Make sure that the datadir and the scratch_dir (if any) are writeable
    """
    datadir = logs.get_datadir()
    scratch_dir = parallel.scratch_dir(calc_id)
    for dir in (datadir, scratch_dir):
        assert os.path.exists(dir), dir
        fname = os.path.join(dir, 'check')
        open(fname, 'w').close()  # check writeable
        os.remove(fname)


def create_jobs(job_inis, log_level=logging.INFO, log_file=None,
                user_name=USER, hc_id=None, host=None):
    """
    Create job records on the database.

    :param job_inis: a list of pathnames or a list of dictionaries
    :returns: a list of LogContext objects
    """
    try:
        host = socket.gethostname()
    except Exception:  # gaierror
        host = None
    jobs = []
    for job_ini in job_inis:
        if isinstance(job_ini, dict):
            dic = job_ini
        else:
            # NB: `get_params` must NOT log, since the logging is not
            # configured yet, otherwise the log will disappear :-(
            dic = readinput.get_params(job_ini)
        jobs.append(logs.init(dic, None, log_level, log_file,
                              user_name, hc_id, host))
    check_directories(jobs[0].calc_id)
    return jobs


def start_workers(job_id, dist, nodes):
    """
    Start the workers via the DbServer or via slurm
    """
    if dist == 'zmq':
        print('Starting the workers %s' % config.zworkers.host_cores)
        logs.dbcmd('workers_start', dict(config.zworkers))
    elif dist == 'slurm':
        slurm.start_workers(job_id, nodes)
        slurm.wait_workers(job_id, nodes)


def stop_workers(job_id):
    """
    Stop the workers spawned by the current job via the WorkerMaster
    """
    print(w.WorkerMaster(job_id).stop())


def watchdog(calc_id, pid, timeout):
    """
    If the job takes longer than the timeout, kills it
    """
    while True:
        time.sleep(30)
        [(start, status)] = logs.dbcmd(
            'SELECT start_time, status FROM job WHERE id=?x', calc_id)
        if status != 'executing':
            break
        elif (datetime.now() - start).seconds > timeout:
            os.kill(pid, signal.SIGTERM)
            logs.dbcmd('finish', calc_id, 'aborted')
            break


def _run(jobctxs, dist, job_id, nodes, sbatch, precalc, concurrent_jobs):
    for job in jobctxs:
        dic = {'status': 'executing', 'pid': _PID,
               'start_time': datetime.now(UTC)}
        logs.dbcmd('update_job', job.calc_id, dic)
    try:
        if dist in ('zmq', 'slurm') and w.WorkerMaster(job_id).status() == []:
            start_workers(job_id, dist, nodes)

        # run the jobs sequentially or in parallel, with slurm or without
        if dist == 'slurm' and sbatch:
            scratch_dir = parallel.scratch_dir(job_id)
            with open(os.path.join(scratch_dir, 'jobs.pik'), 'wb') as f:
                pickle.dump(jobctxs, f)
            w.WorkerMaster(job_id).send_jobs()
            print('oq engine --show-log %d to see the progress' % job_id)
        elif len(jobctxs) > 1 and dist in ('zmq', 'slurm'):
            if precalc:
                run_calc(jobctxs[0])
                args = [(ctx,) for ctx in jobctxs[1:]]
            else:
                args = [(ctx,) for ctx in jobctxs]
            #with multiprocessing.pool.Pool(concurrent_jobs) as pool:
            #    pool.starmap(run_calc, args)
            parallel.multispawn(run_calc, args, concurrent_jobs or 1)
        elif concurrent_jobs:
            nc = 1 + parallel.num_cores // concurrent_jobs
            logging.warning('Using %d pools of %d cores each',
                            concurrent_jobs, nc)
            os.environ['OQ_NUM_CORES'] = str(nc)
            parallel.multispawn(
                run_calc, [(ctx,) for ctx in jobctxs], concurrent_jobs)
        else:
            for jobctx in jobctxs:
                run_calc(jobctx)
    finally:
        if dist == 'zmq' or (dist == 'slurm' and not sbatch):
            stop_workers(job_id)


def run_jobs(jobctxs, concurrent_jobs=None, nodes=1, sbatch=False,
             precalc=False):
    """
    Run jobs using the specified config file and other options.

    :param jobctxs:
        List of LogContexts
    :param concurrent_jobs:
        How many jobs to run concurrently (default num_cores/4)
    """
    dist = parallel.oq_distribute()
    if dist == 'slurm':
        # check the total number of required cores
        tot_cores = parallel.num_cores * nodes
        max_cores = int(config.distribution.max_cores)
        if tot_cores > max_cores:
            raise ValueError('You can use at most %d nodes' %
                             (max_cores // parallel.num_cores))

    job_id = jobctxs[0].calc_id
    if precalc:
        # assume the first job is a precalculation from which the other starts
        for jobctx in jobctxs[1:]:
            jobctx.params['hazard_calculation_id'] = job_id
    else:
        for jobctx in jobctxs:
            hc_id = jobctx.params.get('hazard_calculation_id')
            if hc_id:
                job = logs.dbcmd('get_job', hc_id)
                ppath = job.ds_calc_dir + '.hdf5'
                if os.path.exists(ppath):
                    version = logs.dbcmd('engine_version')
                    with h5py.File(ppath, 'r') as f:
                        prev_version = f.attrs['engine_version']
                        if prev_version != version:
                            # here the logger is not initialized yet
                            print('Starting from a hazard (%s) computed with'
                                  ' an obsolete version of the engine: %s' %
                                  (hc_id, prev_version))
    if dist == 'slurm' and sbatch:
        pass  # do not wait in the job queue
    else:
        try:
            poll_queue(job_id, poll_time=15)
            # wait for an empty slot or a CTRL-C
        except BaseException:
            # the job aborted even before starting
            for job in jobctxs:
                logs.dbcmd('finish', job.calc_id, 'aborted')
            raise
    _run(jobctxs, dist, job_id, nodes, sbatch, precalc, concurrent_jobs)
    return jobctxs


def version_triple(tag):
    """
    returns: a triple of integers from a version tag
    """
    groups = re.match(r'v?(\d+)\.(\d+)\.(\d+)', tag).groups()
    return tuple(int(n) for n in groups)


def check_obsolete_version(calculation_mode='WebUI'):
    """
    Check if there is a newer version of the engine.

    :param calculation_mode:
         - the calculation mode when called from the engine
         - an empty string when called from the WebUI
    :returns:
        - a message if the running version of the engine is obsolete
        - the empty string if the engine is updated
        - None if the check could not be performed (i.e. github is down)
    """
    if os.environ.get('JENKINS_URL') or os.environ.get('CI'):
        # avoid flooding our API server with requests from CI systems
        return

    version = logs.dbcmd('engine_version')
    logging.info('Using engine version %s', version)
    headers = {'User-Agent': 'OpenQuake Engine %s;%s;%s;%s' %
               (version, calculation_mode, platform.platform(),
                config.distribution.oq_distribute)}
    try:
        req = Request(OQ_API + '/engine/latest', headers=headers)
        # NB: a timeout < 1 does not work
        data = urlopen(req, timeout=1).read()  # bytes
        tag_name = json.loads(decode(data))['tag_name']
        current = version_triple(version)
        latest = version_triple(tag_name)
    except Exception:  # page not available or wrong version tag
        msg = ('An error occurred while calling %s/engine/latest to check'
               ' if the installed version of the engine is up to date.' %
               OQ_API)
        logging.warning(msg)
        return
    if current < latest:
        return ('Version %s of the engine is available, but you are '
                'still using version %s' % (tag_name, version))
    else:
        return ''


if __name__ == '__main__':
    # run LogContexts stored in jobs.pik, called by job.yaml or slurm
    with open(sys.argv[1], 'rb') as f:
        jobctxs = pickle.load(f)
    try:
        if len(jobctxs) > 1 and jobctxs[0].multi:
            parallel.multispawn(run_calc, [(ctx,) for ctx in jobctxs],
                                parallel.Starmap.CT // 10 or 1)
        else:
            for jobctx in jobctxs:
                run_calc(jobctx)
    except Exception:
        ids = [jc.calc_id for jc in jobctxs]
        rows = logs.dbcmd("SELECT id FROM job WHERE id IN (?X) "
                          "AND status IN ('created', 'executing')", ids)
        for jid, in rows:
            logs.dbcmd("set_status", jid, 'failed')
        raise
    finally:
        stop_workers(jobctxs[0].calc_id)
