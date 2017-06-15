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
import sys
import signal
import traceback

from openquake.baselib.performance import Monitor
from openquake.hazardlib import valid
from openquake.baselib import parallel
from openquake.commonlib.oqvalidation import OqParam
from openquake.commonlib import datastore, config, readinput
from openquake.calculators import base, views, export
from openquake.commonlib import logs

TERMINATE = valid.boolean(
    config.get('distribution', 'terminate_workers_on_revoke') or 'false')

USE_CELERY = config.get('distribution', 'oq_distribute') == 'celery'

if USE_CELERY:
    import celery.task.control

    def set_concurrent_tasks_default():
        """
        Set the default for concurrent_tasks.
        Returns the number of live celery nodes (i.e. the number of machines).
        """
        stats = celery.task.control.inspect(timeout=1).stats()
        if not stats:
            sys.exit("No live compute nodes, aborting calculation")
        num_cores = sum(stats[k]['pool']['max-concurrency'] for k in stats)
        OqParam.concurrent_tasks.default = num_cores * 5
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
    try:
        rlzs = list(dstore['realizations'])
    except KeyError:
        rlzs = []
    # expose gmf_data only if < 10 MB
    if oq.ground_motion_fields and calcmode == 'event_based':
        nbytes = dstore['gmf_data'].attrs['nbytes']
        if nbytes < 10 * 1024 ** 2:
            dskeys.add('gmf_data')
    if 'scenario' not in calcmode:  # export sourcegroups.csv
        dskeys.add('sourcegroups')
    if 'poes' in dstore or 'hcurves' in dstore:
        dskeys.add('hcurves')
        if oq.uniform_hazard_spectra:
            dskeys.add('uhs')  # export them
        if oq.hazard_maps:
            dskeys.add('hmaps')  # export them
    if 'avg_losses-rlzs' in dstore and rlzs:
        dskeys.add('avg_losses-stats')
    if oq.conditional_loss_poes:  # expose loss_maps outputs
        if 'rcurves-rlzs' in dstore or 'loss_curves-rlzs' in dstore:
            dskeys.add('loss_maps-rlzs')
        if 'rcurves-stats' in dstore or 'loss_curves-stats' in dstore:
            if len(rlzs) > 1:
                dskeys.add('loss_maps-stats')
    if 'all_loss_ratios' in dskeys:
        dskeys.remove('all_loss_ratios')  # export only specific IDs
    if 'realizations' in dskeys and len(rlzs) <= 1:
        dskeys.remove('realizations')  # do not export a single realization
    if 'ruptures' in dskeys and 'scenario' in calcmode:
        exportable.remove('ruptures')  # do not export, as requested by Vitor
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
    if signum == signal.SIGTERM:
        msg = 'The openquake master process was killed manually'
    else:
        msg = 'Received a signal %d' % signum
    raise MasterKilled(msg)


# register the raiseMasterKilled callback for SIGTERM
# when using the Django development server this module is imported by a thread,
# so one gets a `ValueError: signal only works in main thread` that
# can be safely ignored
try:
    signal.signal(signal.SIGTERM, raiseMasterKilled)
except ValueError:
    pass


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
    oq = readinput.get_oqparam(cfg_file)
    job_id = logs.dbcmd('create_job', oq.calculation_mode, oq.description,
                        username, datastore.DATADIR, hazard_calculation_id)
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
    monitor = Monitor('total runtime', measuremem=True)
    with logs.handle(job_id, log_level, log_file):  # run the job
        if USE_CELERY and os.environ.get('OQ_DISTRIBUTE') == 'celery':
            set_concurrent_tasks_default()
        calc = base.calculators(oqparam, monitor, calc_id=job_id)
        calc.from_engine = True
        tb = 'None\n'
        try:
            logs.dbcmd('set_status', job_id, 'executing')
            _do_run_calc(calc, exports, hazard_calculation_id, **kw)
            expose_outputs(calc.datastore)
            records = views.performance_view(calc.datastore)
            logs.dbcmd('save_performance', job_id, records)
            calc.datastore.close()
            logs.LOG.info('Calculation %d finished correctly in %d seconds',
                          job_id, calc._monitor.duration)
            logs.dbcmd('finish', job_id, 'complete')
        except:
            tb = traceback.format_exc()
            try:
                logs.LOG.critical(tb)
                logs.dbcmd('finish', job_id, 'failed')
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
