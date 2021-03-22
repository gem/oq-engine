# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2010-2021 GEM Foundation
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
import getpass
import logging
import itertools
import traceback
import platform
import psutil
import numpy
try:
    from setproctitle import setproctitle
except ImportError:
    def setproctitle(title):
        "Do nothing"
from urllib.request import urlopen, Request
from openquake.baselib.python3compat import decode
from openquake.baselib import parallel, general, config, __version__
from openquake.hazardlib import valid
from openquake.commonlib.oqvalidation import OqParam
from openquake.commonlib import readinput
from openquake.calculators import base, export
from openquake.commonlib import logs

OQ_API = 'https://api.openquake.org'
OQ_DISTRIBUTE = parallel.oq_distribute()

MB = 1024 ** 2
_PID = os.getpid()  # the PID
_PPID = os.getppid()  # the controlling terminal PID

GET_JOBS = '''--- executing or submitted
SELECT * FROM job WHERE status IN ('executing', 'submitted')
AND is_running=1 AND pid > 0 ORDER BY id'''


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
    if OQ_DISTRIBUTE in 'no processpool':  # do nothing
        num_workers = 0 if OQ_DISTRIBUTE == 'no' else parallel.Starmap.CT // 2
        logging.warning('Using %d cores on %s', num_workers, platform.node())
        return

    num_workers = sum(total for host, running, total
                      in parallel.workers_wait())
    if num_workers == 0:
        logging.critical("No live compute nodes, aborting calculation")
        logs.dbcmd('finish', calc.datastore.calc_id, 'failed')
        sys.exit(1)

    parallel.Starmap.CT = num_workers * 2
    parallel.Starmap.num_cores = num_workers
    OqParam.concurrent_tasks.default = num_workers * 2
    logging.warning('Using %d %s workers', num_workers, OQ_DISTRIBUTE)


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
    if 'avg_gmf' in dskeys:
        dskeys.remove('avg_gmf')  # hide
    rlzs = dstore['full_lt'].rlzs
    if len(rlzs) > 1:
        dskeys.add('realizations')
    hdf5 = dstore.hdf5
    if 'hcurves-stats' in hdf5 or 'hcurves-rlzs' in hdf5:
        if oq.hazard_stats() or oq.individual_curves or len(rlzs) == 1:
            dskeys.add('hcurves')
        if oq.uniform_hazard_spectra:
            dskeys.add('uhs')  # export them
        if oq.hazard_maps:
            dskeys.add('hmaps')  # export them
    if len(rlzs) > 1 and not oq.individual_curves:
        for out in ['avg_losses-rlzs', 'agg_losses-rlzs', 'agg_curves-rlzs']:
            if out in dskeys:
                dskeys.remove(out)
    if 'curves-rlzs' in dstore and len(rlzs) == 1:
        dskeys.add('loss_curves-rlzs')
    if 'curves-stats' in dstore and len(rlzs) > 1:
        dskeys.add('loss_curves-stats')
    if oq.conditional_loss_poes:  # expose loss_maps outputs
        if 'loss_curves-stats' in dstore:
            dskeys.add('loss_maps-stats')
    if 'ruptures' in dskeys and 'scenario' in calcmode:
        exportable.remove('ruptures')  # do not export, as requested by Vitor
    if 'hmaps' in dskeys and not oq.hazard_maps:
        dskeys.remove('hmaps')  # do not export the hazard maps
    if logs.dbcmd('get_job', dstore.calc_id) is None:
        # the calculation has not been imported in the db yet
        logs.dbcmd('import_job', dstore.calc_id, oq.calculation_mode,
                   oq.description + ' [parent]', owner, status,
                   oq.hazard_calculation_id, dstore.datadir)
    keysize = []
    for key in sorted(dskeys & exportable):
        try:
            size_mb = dstore.getsize(key) / MB
        except (KeyError, AttributeError):
            size_mb = None
        keysize.append((key, size_mb))
    ds_size = dstore.getsize() / MB
    logs.dbcmd('create_outputs', dstore.calc_id, keysize, ds_size)


class MasterKilled(KeyboardInterrupt):
    "Exception raised when a job is killed manually"


def inhibitSigInt(signum, _stack):
    logging.warning('Killing job, please wait')


def manage_signals(signum, _stack):
    """
    Convert a SIGTERM into a SystemExit exception and a SIGINT/SIGHUP into
    a MasterKilled exception with an appropriate error message.

    :param int signum: the number of the received signal
    :param _stack: the current frame object, ignored
    """
    # Disable further CTRL-C to allow tasks revocation when Celery is used
    if OQ_DISTRIBUTE == 'celery':
        signal.signal(signal.SIGINT, inhibitSigInt)

    if signum == signal.SIGINT:
        parallel.workers_stop()
        raise MasterKilled('The openquake master process was killed manually')

    if signum == signal.SIGTERM:
        parallel.workers_stop()
        raise SystemExit('Terminated')

    if hasattr(signal, 'SIGHUP'):  # there is no SIGHUP on Windows
        # kill the calculation only if os.getppid() != _PPID, i.e. the
        # controlling terminal died; in the workers, do nothing
        if signum == signal.SIGHUP and os.getppid() != _PPID:
            parallel.workers_stop()
            raise MasterKilled(
                'The openquake master lost its controlling terminal')


def register_signals():
    # register the manage_signals callback for SIGTERM, SIGINT, SIGHUP
    # when using the Django development server this module is imported by a
    # thread, so one gets a `ValueError: signal only works in main thread` that
    # can be safely ignored
    try:
        signal.signal(signal.SIGTERM, manage_signals)
        signal.signal(signal.SIGINT, manage_signals)
        if hasattr(signal, 'SIGHUP'):
            # Do not register our SIGHUP handler if running with 'nohup'
            if signal.getsignal(signal.SIGHUP) != signal.SIG_IGN:
                signal.signal(signal.SIGHUP, manage_signals)
    except ValueError:
        pass


def poll_queue(job_id, poll_time):
    """
    Check the queue of executing/submitted jobs and exit when there is
    a free slot.
    """
    offset = config.distribution.serialize_jobs - 1
    if offset >= 0:
        first_time = True
        while True:
            jobs = logs.dbcmd(GET_JOBS)
            failed = [job.id for job in jobs if not psutil.pid_exists(job.pid)]
            if failed:
                for job in failed:
                    logs.dbcmd('update_job', job,
                               {'status': 'failed', 'is_running': 0})
            elif any(j.id < job_id - offset for j in jobs):
                if first_time:
                    logging.warning(
                        'Waiting for jobs %s', [j.id for j in jobs
                                                if j.id < job_id - offset])
                    logs.dbcmd('update_job', job_id,
                               {'status': 'submitted', 'pid': _PID})
                    first_time = False
                time.sleep(poll_time)
            else:
                break


def run_calc(job_id, oqparam, exports, log_level='info', log_file=None, **kw):
    """
    Run a calculation.

    :param job_id:
        ID of the current job
    :param oqparam:
        :class:`openquake.commonlib.oqvalidation.OqParam` instance
    :param exports:
        A comma-separated string of export types.
    """
    register_signals()
    setproctitle('oq-job-%d' % job_id)
    logs.init(job_id, getattr(logging, log_level.upper()))
    with logs.handle(job_id, log_level, log_file):
        calc = base.calculators(oqparam, calc_id=job_id)
        logging.info('%s running %s [--hc=%s]',
                     getpass.getuser(),
                     calc.oqparam.inputs['job_ini'],
                     calc.oqparam.hazard_calculation_id)
        logging.info('Using engine version %s', __version__)
        msg = check_obsolete_version(oqparam.calculation_mode)
        if msg:
            logging.warning(msg)
        calc.from_engine = True
        tb = 'None\n'
        try:
            if config.zworkers['host_cores']:
                set_concurrent_tasks_default(calc)
            else:
                logging.warning('Assuming %d %s workers',
                                parallel.Starmap.num_cores, OQ_DISTRIBUTE)
            t0 = time.time()
            calc.run(exports=exports, **kw)
            logging.info('Exposing the outputs to the database')
            expose_outputs(calc.datastore)
            path = calc.datastore.filename
            size = general.humansize(os.path.getsize(path))
            logging.info('Stored %s on %s in %d seconds',
                         size, path, time.time() - t0)
            logs.dbcmd('finish', job_id, 'complete')
            calc.datastore.close()
            for line in logs.dbcmd('list_outputs', job_id, False):
                general.safeprint(line)
        except BaseException as exc:
            if isinstance(exc, MasterKilled):
                msg = 'aborted'
            else:
                msg = 'failed'
            tb = traceback.format_exc()
            try:
                logging.critical(tb)
                logs.dbcmd('finish', job_id, msg)
            except BaseException:  # an OperationalError may always happen
                sys.stderr.write(tb)
            raise
        finally:
            parallel.Starmap.shutdown()
    # sanity check to make sure that the logging on file is working
    if log_file and log_file != os.devnull and os.path.getsize(log_file) == 0:
        logging.warning('The log file %s is empty!?' % log_file)
    return calc


def _init_logs(dic, lvl):
    if '_job_id' in dic:  # reuse job_id
        logs.init(dic['_job_id'], lvl)
    else:  # create a new job_id
        dic['_job_id'] = logs.init('job', lvl)


def create_jobs(job_inis, loglvl, kw):
    """
    Create job records on the database (if not already there) and configure
    the logging.
    """
    dicts = []
    for i, job_ini in enumerate(job_inis):
        if isinstance(job_ini, dict):
            dic = job_ini
        else:
            # NB: `get_params` must NOT log, since the logging is not
            # configured yet, otherwise the log will disappear :-(
            dic = readinput.get_params(job_ini, kw)
        if 'sensitivity_analysis' in dic:
            analysis = valid.dictionary(dic['sensitivity_analysis'])
            for values in itertools.product(*analysis.values()):
                new = dic.copy()
                _init_logs(new, loglvl)
                if '_job_id' in dic:
                    del dic['_job_id']
                pars = dict(zip(analysis, values))
                for param, value in pars.items():
                    new[param] = str(value)
                new['description'] = '%s %s' % (new['description'], pars)
                logging.info('Job with %s', pars)
                dicts.append(new)
        else:
            _init_logs(dic, loglvl)
            dicts.append(dic)
    return dicts


def run_jobs(job_inis, log_level='info', log_file=None, exports='',
             username=getpass.getuser(), **kw):
    """
    Run jobs using the specified config file and other options.

    :param str job_inis:
        A list of paths to .ini files, or a list of job dictionaries
    :param str log_level:
        'debug', 'info', 'warn', 'error', or 'critical'
    :param str log_file:
        Path to log file.
    :param exports:
        A comma-separated string of export types requested by the user.
    :param username:
        Name of the user running the job
    :param kw:
        Extra parameters like hazard_calculation_id and calculation_mode
    """
    jobparams = []
    multi = kw.pop('multi', None)
    loglvl = getattr(logging, log_level.upper())
    jobs = create_jobs(job_inis, loglvl, kw)  # inizialize the logs
    if kw.get('hazard_calculation_id'):
        hc_id = int(kw['hazard_calculation_id'])
    else:
        hc_id = None
    for job in jobs:
        job_id = job['_job_id']
        job['hazard_calculation_id'] = hc_id
        with logs.handle(job_id, log_level, log_file):
            dic = dict(calculation_mode=job['calculation_mode'],
                       description=job['description'],
                       user_name=username, is_running=1)
            if hc_id:
                dic['hazard_calculation_id'] = hc_id
            logs.dbcmd('update_job', job_id, dic)
            if (not jobparams and not multi and
                    'hazard_calculation_id' not in kw and
                    'sensitivity_analysis' not in job):
                hc_id = job_id
            try:
                oqparam = readinput.get_oqparam(job)
            except BaseException:
                tb = traceback.format_exc()
                logging.critical(tb)
                logs.dbcmd('finish', job_id, 'failed')
                raise
        jobparams.append((job_id, oqparam))
    jobarray = len(jobparams) > 1 and multi
    try:
        poll_queue(job_id, poll_time=15)
        # wait for an empty slot or a CTRL-C
    except BaseException:
        # the job aborted even before starting
        for job_id, oqparam in jobparams:
            logs.dbcmd('finish', job_id, 'aborted')
        return jobparams
    else:
        for job_id, oqparam in jobparams:
            dic = {'status': 'executing', 'pid': _PID}
            if jobarray:
                dic['hazard_calculation_id'] = jobparams[0][0]
            logs.dbcmd('update_job', job_id, dic)
    try:
        if config.zworkers['host_cores'] and parallel.workers_status() == []:
            logging.info('Asking the DbServer to start the workers')
            logs.dbcmd('workers_start')  # start the workers
        allargs = [(job_id, oqparam, exports, log_level, log_file)
                   for job_id, oqparam in jobparams]
        if jobarray:
            with general.start_many(run_calc, allargs):
                pass
        else:
            for args in allargs:
                run_calc(*args)
    finally:
        if config.zworkers['host_cores']:
            logging.info('Stopping the workers')
            parallel.workers_stop()
    return jobparams


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
    except KeyError:  # 'tag_name' not found
        # NOTE: for unauthenticated requests, the rate limit allows for up
        # to 60 requests per hour. Therefore, sometimes the api returns the
        # following message:
        # b'{"message":"API rate limit exceeded for aaa.aaa.aaa.aaa. (But'
        # ' here\'s the good news: Authenticated requests get a higher rate'
        # ' limit. Check out the documentation for more details.)",'
        # ' "documentation_url":'
        # ' "https://developer.github.com/v3/#rate-limiting"}'
        msg = ('An error occurred while calling %s/engine/latest to check'
               ' if the installed version of the engine is up to date.\n'
               '%s' % (OQ_API, data.decode('utf8')))
        logging.warning(msg)
        return
    except Exception:  # page not available or wrong version tag
        msg = ('An error occurred while calling %s/engine/latest to check'
               ' if the installed version of the engine is up to date.' %
               OQ_API)
        logging.warning(msg, exc_info=True)
        return
    if current < latest:
        return ('Version %s of the engine is available, but you are '
                'still using version %s' % (tag_name, __version__))
    else:
        return ''
