# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2010-2018 GEM Foundation
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

import io
import os
import re
import sys
import json
import time
import signal
import getpass
import logging
import traceback
import platform
import numpy
try:
    from setproctitle import setproctitle
except ImportError:
    def setproctitle(title):
        "Do nothing"
from urllib.request import urlopen, Request
from openquake.baselib.python3compat import decode
from openquake.baselib import (
    parallel, general, config, datastore, __version__, zeromq as z)
from openquake.hazardlib import nrml
from openquake.commonlib.oqvalidation import OqParam
from openquake.commonlib import readinput
from openquake.calculators import base, views, export
from openquake.commonlib import logs

OQ_API = 'https://api.openquake.org'
TERMINATE = config.distribution.terminate_workers_on_revoke
OQ_DISTRIBUTE = parallel.oq_distribute()

MB = 1024 ** 2
_PID = os.getpid()  # the PID
_PPID = os.getppid()  # the controlling terminal PID

if OQ_DISTRIBUTE == 'zmq':

    def set_concurrent_tasks_default(job_id):
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
                    logs.LOG.warn('%s is not running', host)
                    continue
                num_workers += sock.send('get_num_workers')
        OqParam.concurrent_tasks.default = num_workers * 3
        logs.LOG.warn('Using %d zmq workers', num_workers)

elif OQ_DISTRIBUTE.startswith('celery'):
    import celery.task.control

    def set_concurrent_tasks_default(job_id):
        """
        Set the default for concurrent_tasks based on the number of available
        celery workers.
        """
        stats = celery.task.control.inspect(timeout=1).stats()
        if not stats:
            logs.LOG.critical("No live compute nodes, aborting calculation")
            logs.dbcmd('finish', job_id, 'failed')
            sys.exit(1)
        ncores = sum(stats[k]['pool']['max-concurrency'] for k in stats)
        OqParam.concurrent_tasks.default = ncores * 3
        logs.LOG.warn('Using %s, %d cores', ', '.join(sorted(stats)), ncores)

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


def expose_outputs(dstore, owner=getpass.getuser(), status='complete'):
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
    if 'curves-rlzs' in dstore and len(rlzs) == 1:
        dskeys.add('loss_curves-rlzs')
    if 'curves-stats' in dstore and len(rlzs) > 1:
        dskeys.add('loss_curves-stats')
    if oq.conditional_loss_poes:  # expose loss_maps outputs
        if 'loss_curves-stats' in dstore:
            dskeys.add('loss_maps-stats')
    if 'all_loss_ratios' in dskeys:
        dskeys.remove('all_loss_ratios')  # export only specific IDs
    if 'ruptures' in dskeys and 'scenario' in calcmode:
        exportable.remove('ruptures')  # do not export, as requested by Vitor
    if 'rup_loss_table' in dskeys:  # keep it hidden for the moment
        dskeys.remove('rup_loss_table')
    if logs.dbcmd('get_job', dstore.calc_id) is None:
        # the calculation has not been imported in the db yet
        logs.dbcmd('import_job', dstore.calc_id, oq.calculation_mode,
                   oq.description + ' [parent]', owner, status,
                   oq.hazard_calculation_id, dstore.datadir)
    keysize = []
    for key in sorted(dskeys & exportable):
        try:
            size_mb = dstore.get_attr(key, 'nbytes') / MB
        except KeyError:
            size_mb = None
        keysize.append((key, size_mb))
    ds_size = os.path.getsize(dstore.hdf5path) / MB
    logs.dbcmd('create_outputs', dstore.calc_id, keysize, ds_size)


class MasterKilled(KeyboardInterrupt):
    "Exception raised when a job is killed manually"


def inhibitSigInt(signum, _stack):
    logs.LOG.warn('Killing job, please wait')


def raiseMasterKilled(signum, _stack):
    """
    When a SIGTERM is received, raise the MasterKilled
    exception with an appropriate error message.

    :param int signum: the number of the received signal
    :param _stack: the current frame object, ignored
    """
    # Disable further CTRL-C to allow tasks revocation when Celery is used
    if OQ_DISTRIBUTE.startswith('celery'):
        signal.signal(signal.SIGINT, inhibitSigInt)

    msg = 'Received a signal %d' % signum
    if signum in (signal.SIGTERM, signal.SIGINT):
        msg = 'The openquake master process was killed manually'

    # kill the calculation only if os.getppid() != _PPID, i.e. the controlling
    # terminal died; in the workers, do nothing
    # NB: there is no SIGHUP on Windows
    if hasattr(signal, 'SIGHUP'):
        if signum == signal.SIGHUP:
            if os.getppid() == _PPID:
                return
            else:
                msg = 'The openquake master lost its controlling terminal'

    raise MasterKilled(msg)


# register the raiseMasterKilled callback for SIGTERM
# when using the Django development server this module is imported by a thread,
# so one gets a `ValueError: signal only works in main thread` that
# can be safely ignored
try:
    signal.signal(signal.SIGTERM, raiseMasterKilled)
    signal.signal(signal.SIGINT, raiseMasterKilled)
    if hasattr(signal, 'SIGHUP'):
        signal.signal(signal.SIGHUP, raiseMasterKilled)
except ValueError:
    pass


def zip(job_ini, archive_zip, oq=None, log=logging.info):
    """
    Zip the given job.ini file into the given archive, together with all
    related files.
    """
    if not os.path.exists(job_ini):
        sys.exit('%s does not exist' % job_ini)
    if isinstance(archive_zip, str):  # actually it should be path-like
        if not archive_zip.endswith('.zip'):
            sys.exit('%s does not end with .zip' % archive_zip)
        if os.path.exists(archive_zip):
            sys.exit('%s exists already' % archive_zip)
    logging.basicConfig(level=logging.INFO)
    # do not validate to avoid permissions error on the export_dir
    oq = oq or readinput.get_oqparam(job_ini, validate=False)
    files = set()

    # collect .hdf5 tables for the GSIMs, if any
    if 'gsim_logic_tree' in oq.inputs or oq.gsim:
        gsim_lt = readinput.get_gsim_lt(oq)
        for gsims in gsim_lt.values.values():
            for gsim in gsims:
                table = getattr(gsim, 'GMPE_TABLE', None)
                if table:
                    files.add(table)

    # collect exposure.csv, if any
    exposure_xml = oq.inputs.get('exposure')
    if exposure_xml:
        dname = os.path.dirname(exposure_xml)
        expo = nrml.read(exposure_xml, stop='asset')[0]
        if not expo.assets:
            exposure_csv = (~expo.assets).strip()
            for csv in exposure_csv.split():
                if csv and os.path.exists(os.path.join(dname, csv)):
                    files.add(os.path.join(dname, csv))

    # collection .hdf5 UCERF file, if any
    if oq.calculation_mode.startswith('ucerf_'):
        sm = nrml.read(oq.inputs['source_model'])
        fname = sm.sourceModel.UCERFSource['filename']
        f = os.path.join(os.path.dirname(oq.inputs['source_model']), fname)
        files.add(os.path.normpath(f))

    # collect all other files
    for key in oq.inputs:
        fname = oq.inputs[key]
        if isinstance(fname, list):
            for f in fname:
                files.add(os.path.normpath(f))
        else:
            files.add(os.path.normpath(fname))
    general.zipfiles(files, archive_zip, log=log)


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
    setproctitle('oq-job-%d' % job_id)
    with logs.handle(job_id, log_level, log_file):  # run the job
        calc = base.calculators(oqparam, calc_id=job_id)
        calc.set_log_format()  # set the log format first of all
        msg = check_obsolete_version(oqparam.calculation_mode)
        if msg:
            logs.LOG.warn(msg)
        if OQ_DISTRIBUTE.startswith(('celery', 'zmq')):
            set_concurrent_tasks_default(job_id)
        calc.from_engine = True
        input_zip = oqparam.inputs.get('input_zip')
        tb = 'None\n'
        try:
            if input_zip:  # the input was zipped from the beginning
                data = open(input_zip, 'rb').read()
            else:  # zip the input
                logs.LOG.info('zipping the input files')
                bio = io.BytesIO()
                zip(oqparam.inputs['job_ini'], bio, oqparam, logging.debug)
                data = bio.getvalue()
            calc.datastore['input_zip'] = numpy.array(data)
            calc.datastore.set_attrs('input_zip', nbytes=len(data))

            logs.dbcmd('update_job', job_id, {'status': 'executing',
                                              'pid': _PID})
            t0 = time.time()
            calc.run(exports=exports,
                     hazard_calculation_id=hazard_calculation_id,
                     close=False, **kw)  # don't close the datastore too soon
            logs.LOG.info('Exposing the outputs to the database')
            expose_outputs(calc.datastore)
            duration = time.time() - t0
            calc._monitor.flush()
            records = views.performance_view(calc.datastore)
            logs.dbcmd('save_performance', job_id, records)
            calc.datastore.close()
            logs.LOG.info('Calculation %d finished correctly in %d seconds',
                          job_id, duration)
            logs.dbcmd('finish', job_id, 'complete')
        except BaseException:
            tb = traceback.format_exc()
            try:
                logs.LOG.critical(tb)
                logs.dbcmd('finish', job_id, 'failed')
            except BaseException:  # an OperationalError may always happen
                sys.stderr.write(tb)
            raise
        finally:
            # if there was an error in the calculation, this part may fail;
            # in such a situation, we simply log the cleanup error without
            # taking further action, so that the real error can propagate
            try:
                if OQ_DISTRIBUTE.startswith('celery'):
                    celery_cleanup(TERMINATE, parallel.Starmap.task_ids)
            except BaseException:
                # log the finalization error only if there is no real error
                if tb == 'None\n':
                    logs.LOG.error('finalizing', exc_info=True)
    return calc


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

    headers = {'User-Agent': 'OpenQuake Engine %s;%s;%s;%s' %
               (__version__, calculation_mode, platform.platform(),
                config.distribution.oq_distribute)}
    try:
        req = Request(OQ_API + '/engine/latest', headers=headers)
        # NB: a timeout < 1 does not work
        data = urlopen(req, timeout=1).read()  # bytes
        tag_name = json.loads(decode(data))['tag_name']
        current = version_triple(__version__)
        latest = version_triple(tag_name)
    except Exception:  # page not available or wrong version tag
        return
    if current < latest:
        return ('Version %s of the engine is available, but you are '
                'still using version %s' % (tag_name, __version__))
    else:
        return ''
