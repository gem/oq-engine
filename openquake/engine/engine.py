# Copyright (c) 2010-2014, GEM Foundation.
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

"""Engine: A collection of fundamental functions for initializing and running
calculations."""

import os
import sys
import time
import getpass
import itertools
import operator
from contextlib import contextmanager
from datetime import datetime

import celery.task.control

import openquake.engine

from django.core import exceptions
from django import db as django_db

from openquake.engine import logs
from openquake.engine.db import models
from openquake.engine.utils import config
from openquake.engine.celery_node_monitor import CeleryNodeMonitor
from openquake.engine.writer import CacheInserter
from openquake.engine.settings import DATABASES
from openquake.engine.db.models import Performance
from openquake.engine.db.schema.upgrades import upgrader

from openquake import hazardlib, risklib, commonlib

from openquake.commonlib import readinput, valid


INPUT_TYPES = set(dict(models.INPUT_TYPE_CHOICES))

UNABLE_TO_DEL_HC_FMT = 'Unable to delete hazard calculation: %s'
UNABLE_TO_DEL_RC_FMT = 'Unable to delete risk calculation: %s'

TERMINATE = valid.boolean(config.get('celery', 'terminate_workers_on_revoke'))


class InvalidHazardCalculationID(Exception):
    pass

RISK_HAZARD_MAP = dict(
    scenario_risk='scenario',
    scenario_damage='scenario',
    classical_risk='classical',
    classical_bcr='classical',
    event_based_risk='event_based',
    event_based_bcr='event_based')


def cleanup_after_job(job, terminate):
    """
    Release the resources used by an openquake job.
    In particular revoke the running tasks (if any).

    :param int job_id: the job id
    :param bool terminate: the celery revoke command terminate flag
    """
    # Using the celery API, terminate and revoke and terminate any running
    # tasks associated with the current job.
    task_ids = Performance.objects.filter(
        oq_job=job, operation='storing task id', task_id__isnull=False)\
        .values_list('task_id', flat=True)
    if task_ids:
        logs.LOG.warn('Revoking %d tasks', len(task_ids))
    else:  # this is normal when OQ_NO_DISTRIBUTE=1
        logs.LOG.debug('No task to revoke')
    for tid in task_ids:
        celery.task.control.revoke(tid, terminate=terminate)
        logs.LOG.debug('Revoked task %s', tid)


@contextmanager
def job_stats(job):
    """
    A context manager saving information such as the number of sites
    and the disk space occupation in the job_stats table. The information
    is saved at the end of the job, even if the job fails.
    """
    dbname = DATABASES['default']['NAME']
    curs = models.getcursor('job_init')
    curs.execute("select pg_database_size(%s)", (dbname,))
    dbsize = curs.fetchall()[0][0]

    js = job.jobstats
    job.is_running = True
    job.save()
    try:
        yield
    except:
        conn = django_db.connections['job_init']
        if conn.is_dirty():
            conn.rollback()
        raise
    finally:
        job.is_running = False
        job.save()

        # save job stats
        curs.execute("select pg_database_size(%s)", (dbname,))
        new_dbsize = curs.fetchall()[0][0]
        js.disk_space = new_dbsize - dbsize
        js.stop_time = datetime.utcnow()
        js.save()

        cleanup_after_job(job, terminate=TERMINATE)


def create_job(user_name="openquake", log_level='progress'):
    """
    Create job for the given user, return it.

    :param str username:
        Username of the user who owns/started this job. If the username doesn't
        exist, a user record for this name will be created.
    :param str log_level:
        Defaults to 'progress'. Specify a logging level for this job. This
        level can be passed, for example, from the command line interface using
        the `--log-level` directive.
    :returns:
        :class:`openquake.engine.db.models.OqJob` instance.
    """
    return models.OqJob.objects.create(
        user_name=user_name,
        log_level=log_level,
        oq_version=openquake.engine.__version__,
        hazardlib_version=hazardlib.__version__,
        risklib_version=risklib.__version__,
        commonlib_version=commonlib.__version__,
    )


# used by bin/openquake and openquake.server.views
def run_calc(job, log_level, log_file, exports):
    """
    Run a calculation.

    :param job:
        :class:`openquake.engine.db.model.OqJob` instance
    :param str log_level:
        The desired logging level. Valid choices are 'debug', 'info',
        'progress', 'warn', 'error', and 'critical'.
    :param str log_file:
        Complete path (including file name) to file where logs will be written.
        If `None`, logging will just be printed to standard output.
    :param exports:
        A comma-separated string of export types.
    """
    # let's import the calculator classes here, when they are needed
    # the reason is that the command `$ oq-engine --upgrade-db`
    # does not need them and would raise strange errors during installation
    # time if the PYTHONPATH is not set and commonlib is not visible
    from openquake.engine.calculators import calculators

    # first of all check the database version and exit if the db is outdated
    upgrader.check_versions(django_db.connections['admin'])

    calculator = calculators(job)
    with logs.handle(job, log_level, log_file), job_stats(job):  # run the job
        _do_run_calc(calculator, exports)
    return calculator


def log_status(job, status):
    """
    Switch to a particular phase of execution.

    :param job:
        An :class:`~openquake.engine.db.models.OqJob` instance.
    :param str job_type:
        calculation type (hazard|risk)
    :param str status:
        one of the following: pre_executing, executing,
        post_executing, post_processing, export, clean_up, complete
    """
    job.status = status
    job.save()
    logs.LOG.progress("%s (%s)", status, job.job_type)


def _do_run_calc(calc, exports):
    """
    Step through all of the phases of a calculation, updating the job
    status at each phase.

    :param calc:
        An :class:`~openquake.engine.calculators.base.Calculator` instance.
    :param exports:
        a (potentially empty) comma-separated string of export targets
    """
    job = calc.job

    log_status(job, "pre_executing")
    calc.pre_execute()

    log_status(job, "executing")
    calc.execute()

    log_status(job, "post_executing")
    calc.post_execute()

    log_status(job, "post_processing")
    calc.post_process()

    log_status(job, "export")
    calc.export(exports=exports)

    log_status(job, "clean_up")
    calc.clean_up()

    CacheInserter.flushall()  # flush caches into the db

    log_status(job, "complete")


def del_calc(job_id):
    """
    Delete a calculation and all associated outputs.

    :param job_id:
        ID of a :class:`~openquake.engine.db.models.OqJob`.
    """
    try:
        job = models.OqJob.objects.get(id=job_id)
    except exceptions.ObjectDoesNotExist:
        raise RuntimeError('Unable to delete hazard calculation: '
                           'ID=%s does not exist' % job_id)

    user = getpass.getuser()
    if job.user_name == user:
        # we are allowed to delete this

        # but first, check if any risk calculations are referencing any of our
        # outputs, or the hazard calculation itself
        msg = UNABLE_TO_DEL_HC_FMT % (
            'The following risk calculations are referencing this hazard'
            ' calculation: %s')

        assoc_outputs = models.OqJob.objects.filter(hazard_calculation=job)
        if assoc_outputs.count() > 0:
            raise RuntimeError(
                msg % ', '.join(str(x.id) for x in assoc_outputs))

        # No risk calculation are referencing what we want to delete.
        # Carry on with the deletion.
        job.delete(using='admin')
    else:
        # this doesn't belong to the current user
        raise RuntimeError(UNABLE_TO_DEL_HC_FMT % 'Access denied')


def list_outputs(job_id, full=True):
    """
    List the outputs for a given
    :class:`~openquake.engine.db.models.OqJob`.

    :param job_id:
        ID of a calculation.
    :param bool full:
        If True produce a full listing, otherwise a short version
    """
    outputs = get_outputs(job_id)
    if models.oqparam(job_id).calculation_mode == 'scenario':
        # ignore SES output
        outputs = outputs.filter(output_type='gmf_scenario')
    print_outputs_summary(outputs, full)


def touch_log_file(log_file):
    """
    If a log file destination is specified, attempt to open the file in
    'append' mode ('a'). If the specified file is not writable, an
    :exc:`IOError` will be raised.
    """
    open(os.path.abspath(log_file), 'a').close()


def print_results(job_id, duration, list_outputs):
    print 'Calculation %d completed in %d seconds. Results:' % (
        job_id, duration)
    list_outputs(job_id, full=False)


def print_outputs_summary(outputs, full=True):
    """
    List of :class:`openquake.engine.db.models.Output` objects.
    """
    if len(outputs) > 0:
        truncated = False
        print '  id | output_type | name'
        for output_type, group in itertools.groupby(
                sorted(outputs, key=operator.attrgetter('output_type')),
                key=operator.attrgetter('output_type')):
            outs = sorted(group, key=operator.attrgetter('display_name'))
            for i, o in enumerate(outs):
                if not full and i >= 10:
                    print ' ... | %s | %d additional output(s)' % (
                        o.get_output_type_display(), len(outs) - 10)
                    truncated = True
                    break
                print '%4d | %s | %s' % (
                    o.id, o.get_output_type_display(), o.display_name)
        if truncated:
            print ('Some outputs where not shown. You can see the full list '
                   'with the command\n`oq-engine --list-outputs`')


def run_job(cfg_file, log_level, log_file, exports='', hazard_output_id=None,
            hazard_calculation_id=None):
    """
    Run a job using the specified config file and other options.

    :param str cfg_file:
        Path to calculation config (INI-style) file.
    :param str log_level:
        'debug', 'info', 'warn', 'error', or 'critical'
    :param str log_file:
        Path to log file.
    :param exports:
        A comma-separated string of export types requested by the user.
        Currently only 'xml' is supported.
    :param str hazard_ouput_id:
        The Hazard Output ID used by the risk calculation (can be None)
    :param str hazard_calculation_id:
        The Hazard Job ID used by the risk calculation (can be None)
    """
    # first of all check the database version and exit if the db is outdated
    upgrader.check_versions(django_db.connections['admin'])
    with CeleryNodeMonitor(openquake.engine.no_distribute(), interval=3):
        hazard = hazard_output_id is None and hazard_calculation_id is None
        if log_file is not None:
            touch_log_file(log_file)

        job = job_from_file(
            cfg_file, getpass.getuser(), log_level, exports, hazard_output_id,
            hazard_calculation_id)

        # Instantiate the calculator and run the calculation.
        t0 = time.time()
        run_calc(job, log_level, log_file, exports)
        duration = time.time() - t0
        if hazard:
            if job.status == 'complete':
                print_results(job.id, duration, list_outputs)
            else:
                sys.exit('Calculation %s failed' % job.id)
        else:
            if job.status == 'complete':
                print_results(job.id, duration, list_outputs)
            else:
                sys.exit('Calculation %s failed' % job.id)


def check_hazard_risk_consistency(haz_job, risk_mode):
    """
    Make sure that the provided hazard job is the right one for the
    current risk calculator.

    :param job:
        an OqJob instance referring to the previous hazard calculation
    :param risk_mode:
        the `calculation_mode` string of the current risk calculation
    """
    if haz_job.job_type == 'risk':
        raise InvalidHazardCalculationID(
            'You provided a risk calculation instead of a hazard calculation!')

    # check for obsolete calculation_mode
    if risk_mode in ('classical', 'event_based', 'scenario'):
        raise ValueError('Please change calculation_mode=%s into %s_risk '
                         'in the .ini file' % (risk_mode, risk_mode))

    # check hazard calculation_mode consistency
    hazard_mode = haz_job.get_param('calculation_mode')
    expected_mode = RISK_HAZARD_MAP[risk_mode]
    if hazard_mode != expected_mode:
        raise InvalidHazardCalculationID(
            'In order to run a risk calculation of kind %r, '
            'you need to provide a hazard calculation of kind %r, '
            'but you provided a %r instead' %
            (risk_mode, expected_mode, hazard_mode))


@django_db.transaction.commit_on_success
def job_from_file(cfg_file_path, username, log_level='info', exports='',
                  hazard_output_id=None, hazard_calculation_id=None, **extras):
    """
    Create a full job profile from a job config file.

    :param str cfg_file_path:
        Path to the job.ini.
    :param str username:
        The user who will own this job profile and all results.
    :param str log_level:
        Desired log level.
    :param exports:
        Comma-separated sting of desired export types.
    :param int hazard_output_id:
        ID of a hazard output to use as input to this calculation. Specify
        this xor ``hazard_calculation_id``.
    :param int hazard_calculation_id:
        ID of a complete hazard job to use as input to this
        calculation. Specify this xor ``hazard_output_id``.
    :params extras:
        Extra parameters (used only in the tests to override the params)
    :returns:
        :class:`openquake.engine.db.models.OqJob` object
    :raises:
        `RuntimeError` if the input job configuration is not valid
    """
    assert os.path.exists(cfg_file_path), cfg_file_path

    from openquake.engine.calculators import calculators

    # determine the previous hazard job, if any
    if hazard_calculation_id:
        haz_job = models.OqJob.objects.get(pk=hazard_calculation_id)
    elif hazard_output_id:  # extract the hazard job from the hazard_output_id
        haz_job = models.Output.objects.get(pk=hazard_output_id).oq_job
    else:
        haz_job = None  # no previous hazard job

    # create the current job
    job = create_job(user_name=username, log_level=log_level)
    models.JobStats.objects.create(oq_job=job)
    with logs.handle(job, log_level):
        # read calculation params and create the calculation profile
        params = readinput.get_params(cfg_file_path)
        params.update(extras)
        if haz_job:  # for risk calculations
            check_hazard_risk_consistency(haz_job, params['calculation_mode'])
            if haz_job.user_name != username:
                logs.LOG.warn(
                    'You are using a hazard calculation ran by %s',
                    haz_job.user_name)
            if hazard_output_id and params.get('quantile_loss_curves'):
                logs.LOG.warn(
                    'quantile_loss_curves is on, but you passed a single '
                    'hazard output: the statistics will not be computed')

        # build and validate an OqParam object
        oqparam = readinput.get_oqparam(params, calculators)
        oqparam.hazard_calculation_id = \
            haz_job.id if haz_job and not hazard_output_id else None
        oqparam.hazard_output_id = hazard_output_id

    params = vars(oqparam).copy()
    if 'quantile_loss_curves' not in params:
        params['quantile_loss_curves'] = []
    if 'poes_disagg' not in params:
        params['poes_disagg'] = []
    if 'sites_disagg' not in params:
        params['sites_disagg'] = []
    if 'specific_assets' not in params:
        params['specific_assets'] = []
    if 'conditional_loss_poes' not in params:
        params['conditional_loss_poes'] = []
    if haz_job:
        params['hazard_calculation_id'] = haz_job.id
    job.save_params(params)

    if hazard_output_id is None and hazard_calculation_id is None:
        # this is a hazard calculation, not a risk one
        del params['hazard_calculation_id']
        del params['hazard_output_id']
    else:  # this is a risk calculation
        job.hazard_calculation = haz_job

    job.save()
    return job


# this is patched in the tests
def get_outputs(job_id):
    """
    :param job_id:
        ID of a calculation.
    :returns:
        A sequence of :class:`openquake.engine.db.models.Output` objects
    """
    return models.Output.objects.filter(oq_job=job_id)
