# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2010-2017 GEM Foundation
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
import signal
import traceback
import platform
try:
    from setproctitle import setproctitle
except ImportError:
    def setproctitle(title):
        "Do nothing"
from openquake.baselib.performance import Monitor
from openquake.baselib.python3compat import urlopen, Request, decode
from openquake.baselib import (
    parallel, general, config, datastore, __version__, zeromq as z, workerpool)
from openquake.baselib.workerpool import register_abort
from openquake.commonlib.oqvalidation import OqParam
from openquake.commonlib import readinput
from openquake.calculators import base, views, export
from openquake.commonlib import logs

OQ_API = 'https://api.openquake.org'
TERMINATE = config.distribution.terminate_workers_on_revoke
USE_CELERY = os.environ.get('OQ_DISTRIBUTE') == 'celery'
ZMQ = os.environ.get(
    'OQ_DISTRIBUTE', config.distribution.oq_distribute) == 'zmq'

if parallel.oq_distribute() == 'zmq':

    def set_concurrent_tasks_default():
        """
        Set the default for concurrent_tasks based on the available
        worker pools .
        """
        num_workers = 0
        w = config.zworkers
        for host, _cores in [hc.split() for hc in w.host_cores.split(',')]:
            url = 'tcp://%s:%s' % (host, w.ctrl_port)
            with z.Socket(url, z.zmq.REQ, 'connect') as sock:
                if not general.socket_ready(url):
                    logs.LOG.warn('%s is not running', url)
                    continue
                num_workers += sock.send('get_num_workers')
        OqParam.concurrent_tasks.default = num_workers * 3
        logs.LOG.info('Using %d zmq workers', num_workers)

elif USE_CELERY:
    import celery.task.control

    def set_concurrent_tasks_default():
        """
        Set the default for concurrent_tasks based on the number of available
        celery workers.
        """
        stats = celery.task.control.inspect(timeout=1).stats()
        if not stats:
            sys.exit("No live compute nodes, aborting calculation")
        num_cores = sum(stats[k]['pool']['max-concurrency'] for k in stats)
        OqParam.concurrent_tasks.default = num_cores * 3
        logs.LOG.info(
            'Using %s, %d cores', ', '.join(sorted(stats)), num_cores)

    def celery_cleanup(terminate, task_ids=()):
        """
        Release the resources used by an openquake job.
        In particular revoke the running tasks (if any).

        :param bool terminate: the celery revoke command terminate flag
        :param task_ids: celery task IDs
        """
        # Using the celery API, terminate and revoke and terminate any running
        # tasks associated with the current job.
        if task_ids:
            logs.LOG.warn('Revoking %d tasks', len(task_ids))
        else:  # this is normal when OQ_DISTRIBUTE=no
            logs.LOG.debug('No task to revoke')
        for tid in task_ids:
            celery.task.control.revoke(tid, terminate=terminate)
            logs.LOG.debug('Revoked task %s', tid)


def expose_outputs(dstore):
    """
    Build a correspondence between the outputs in the datastore and the
    ones in the database.

    :param dstore: datastore
    """
    oq = dstore['oqparam']
    exportable = set(ekey[0] for ekey in export.export)
    calcmode = oq.calculation_mode
    dskeys = set(dstore) & exportable  # exportable datastore keys
    dskeys.add('fullreport')
    rlzs = dstore['csm_info'].rlzs
    if len(rlzs) > 1:
        dskeys.add('realizations')
    # expose gmf_data only if < 10 MB
    if oq.ground_motion_fields and calcmode == 'event_based':
        nbytes = dstore['gmf_data'].attrs['nbytes']
        if nbytes < 10 * 1024 ** 2:
            dskeys.add('gmf_data')
    if 'scenario' not in calcmode:  # export sourcegroups.csv
        dskeys.add('sourcegroups')
    hdf5 = dstore.hdf5
    if (len(rlzs) == 1 and 'poes' in hdf5) or 'hcurves' in hdf5:
        dskeys.add('hcurves')
        if oq.uniform_hazard_spectra:
            dskeys.add('uhs')  # export them
        if oq.hazard_maps:
            dskeys.add('hmaps')  # export them
    if 'avg_losses-stats' in dstore or (
            'avg_losses-rlzs' in dstore and len(rlzs)):
        dskeys.add('avg_losses-stats')
    if 'curves-stats' in dstore:
        logs.LOG.warn('loss curves are exportable with oq export')
    if oq.conditional_loss_poes:  # expose loss_maps outputs
        if 'loss_curves-stats' in dstore:
            dskeys.add('loss_maps-stats')
    if 'all_loss_ratios' in dskeys:
        dskeys.remove('all_loss_ratios')  # export only specific IDs
    if 'ruptures' in dskeys and 'scenario' in calcmode:
        exportable.remove('ruptures')  # do not export, as requested by Vitor
    if 'rup_loss_table' in dskeys:  # keep it hidden for the moment
        dskeys.remove('rup_loss_table')
    logs.dbcmd('create_outputs', dstore.calc_id, sorted(dskeys & exportable))


class MasterKilled(KeyboardInterrupt):
    "Exception raised when a job is killed manually"


def raiseMasterKilled(signum, _stack):
    """
    When a SIGTERM is received, raise the MasterKilled
    exception with an appropriate error message.

    :param int signum: the number of the received signal
    :param _stack: the current frame object, ignored
    """
    if signum in (signal.SIGTERM, signal.SIGINT):
        msg = 'The openquake master process was killed manually'
    else:
        msg = 'Received a signal %d' % signum
    if sys.version_info >= (3, 5, 0):
        # Python 2 is buggy and this code would hang
        for pid in parallel.executor.pids:  # when using futures
            try:
                os.kill(pid, signal.SIGKILL)  # SIGTERM is not enough :-(
            except OSError:  # pid not found
                pass
    if ZMQ:
        workerpool.WorkerMaster(**config.zworkers).stop('abort')
        logs.LOG.warn('Sending abort signal to the workers...')
    raise MasterKilled(msg)


def job_from_file(cfg_file, username, hazard_calculation_id=None):
    """
    Create a full job profile from a job config file.

    :param str cfg_file:
        Path to a job.ini file.
    :param str username:
        The user who will own this job profile and all results
    :param str datadir:
        Data directory of the user
    :param hazard_calculation_id:
        ID of a previous calculation or None
    :returns:
        a pair (job_id, oqparam)
    """
    oq = readinput.get_oqparam(cfg_file, hc_id=hazard_calculation_id)
    job_id = logs.dbcmd('create_job', oq.calculation_mode, oq.description,
                        username, datastore.get_datadir(),
                        hazard_calculation_id)
    return job_id, oq


def run_calc(job_id, oqparam, log_level, log_file, exports,
             hazard_calculation_id=None, **kw):
    """
    Run a calculation.

    :param job_id:
        ID of the current job
    :param oqparam:
        :class:`openquake.commonlib.oqvalidation.OqParam` instance
    :param str log_level:
        The desired logging level. Valid choices are 'debug', 'info',
        'progress', 'warn', 'error', and 'critical'.
    :param str log_file:
        Complete path (including file name) to file where logs will be written.
        If `None`, logging will just be printed to standard output.
    :param exports:
        A comma-separated string of export types.
    """
    # register the raiseMasterKilled callback for SIGTERM
    signal.signal(signal.SIGTERM, raiseMasterKilled)
    signal.signal(signal.SIGINT, raiseMasterKilled)
    setproctitle('oq-job-%d' % job_id)
    monitor = Monitor('total runtime', measuremem=True)
    with logs.handle(job_id, log_level, log_file):  # run the job
        if os.environ.get('OQ_DISTRIBUTE') in ('zmq', 'celery'):
            set_concurrent_tasks_default()
        msg = check_obsolete_version(oqparam.calculation_mode)
        if msg:
            logs.LOG.warn(msg)
        calc = base.calculators(oqparam, monitor, calc_id=job_id)
        monitor.hdf5path = calc.datastore.hdf5path
        calc.from_engine = True
        tb = 'None\n'
        try:
            logs.dbcmd('set_status', job_id, 'executing')
            register_abort(job_id, config.dbserver_url)
            _do_run_calc(calc, exports, hazard_calculation_id, **kw)
            duration = monitor.duration
            expose_outputs(calc.datastore)
            monitor.flush()
            records = views.performance_view(calc.datastore)
            logs.dbcmd('save_performance', job_id, records)
            calc.datastore.close()
            logs.LOG.info('Calculation %d finished correctly in %d seconds',
                          job_id, duration)
            logs.dbcmd('finish', job_id, 'complete')
        except BaseException as exc:
            msg = 'aborted' if isinstance(exc, z.Aborted) else 'failed'
            tb = traceback.format_exc()
            try:
                logs.LOG.critical(tb)
                logs.dbcmd('finish', job_id, msg)
            except:  # an OperationalError may always happen
                sys.stderr.write(tb)
            raise
        finally:
            # if there was an error in the calculation, this part may fail;
            # in such a situation, we simply log the cleanup error without
            # taking further action, so that the real error can propagate
            try:
                if USE_CELERY:
                    celery_cleanup(TERMINATE, parallel.Starmap.task_ids)
            except:
                # log the finalization error only if there is no real error
                if tb == 'None\n':
                    logs.LOG.error('finalizing', exc_info=True)
    return calc


def _do_run_calc(calc, exports, hazard_calculation_id, **kw):
    with calc._monitor:
        calc.run(exports=exports, hazard_calculation_id=hazard_calculation_id,
                 close=False, **kw)  # don't close the datastore too soon


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
    if os.environ.get('JENKINS_URL') or os.environ.get('TRAVIS'):
        # avoid flooding our API server with requests from CI systems
        return

    headers = {'User-Agent': 'OpenQuake Engine %s;%s;%s' %
               (__version__, calculation_mode, platform.platform())}
    try:
        req = Request(OQ_API + '/engine/latest', headers=headers)
        # NB: a timeout < 1 does not work
        data = urlopen(req, timeout=1).read()  # bytes
        tag_name = json.loads(decode(data))['tag_name']
        current = version_triple(__version__)
        latest = version_triple(tag_name)
    except:  # page not available or wrong version tag
        return
    if current < latest:
        return ('Version %s of the engine is available, but you are '
                'still using version %s' % (tag_name, __version__))
    else:
        return ''
