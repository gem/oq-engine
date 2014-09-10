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
import logging
import warnings
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
from openquake.engine.utils import config, get_calculator_class
from openquake.engine.celery_node_monitor import CeleryNodeMonitor
from openquake.engine.writer import CacheInserter
from openquake.engine.settings import DATABASES
from openquake.engine.db.models import Performance
from openquake.engine.db.schema.upgrades import upgrader

from openquake import hazardlib
from openquake import risklib
from openquake import nrmllib

from openquake.commonlib import readini, valid


INPUT_TYPES = set(dict(models.INPUT_TYPE_CHOICES))

UNABLE_TO_DEL_HC_FMT = 'Unable to delete hazard calculation: %s'
UNABLE_TO_DEL_RC_FMT = 'Unable to delete risk calculation: %s'

LOG_FORMAT = ('[%(asctime)s %(job_type)s job #%(job_id)s %(hostname)s '
              '%(levelname)s %(processName)s/%(process)s] %(message)s')

TERMINATE = valid.boolean(config.get('celery', 'terminate_workers_on_revoke'))


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


def _update_log_record(self, record):
    """
    Massage a log record before emitting it. Intended to be used by the
    custom log handlers defined in this module.
    """
    if not hasattr(record, 'hostname'):
        record.hostname = '-'
    if not hasattr(record, 'job_type'):
        record.job_type = self.job_type
    if not hasattr(record, 'job_id'):
        record.job_id = self.job.id


class LogStreamHandler(logging.StreamHandler):
    """
    Log stream handler
    """
    def __init__(self, job):
        super(LogStreamHandler, self).__init__()
        self.setFormatter(logging.Formatter(LOG_FORMAT))
        self.job_type = job.job_type
        self.job = job

    def emit(self, record):  # pylint: disable=E0202
        _update_log_record(self, record)
        super(LogStreamHandler, self).emit(record)


class LogFileHandler(logging.FileHandler):
    """
    Log file handler
    """
    def __init__(self, job, log_file):
        super(LogFileHandler, self).__init__(log_file)
        self.setFormatter(logging.Formatter(LOG_FORMAT))
        self.job_type = job.job_type
        self.job = job
        self.log_file = log_file

    def emit(self, record):  # pylint: disable=E0202
        _update_log_record(self, record)
        super(LogFileHandler, self).emit(record)


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

    # create job stats, which implicitly records the start time for the job
    js = models.JobStats.objects.create(oq_job=job)
    job.is_running = True
    job.save()
    try:
        yield
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


def prepare_job(user_name="openquake", log_level='progress'):
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
        nrml_version=nrmllib.__version__,
        hazardlib_version=hazardlib.__version__,
        risklib_version=risklib.__version__,
    )


def create_calculation(model, params):
    """
    Given a params `dict` parsed from the config file, create a
    :class:`~openquake.engine.db.models.HazardCalculation`.

    :param model:
        a Calculation class object
    :param dict params:
        Dictionary of parameter names and values. Parameter names should match
        exactly the field names of
        :class:`openquake.engine.db.model.HazardCalculation`.
    :returns:
        an instance of a newly created `model`
    """
    if "export_dir" in params:
        params["export_dir"] = os.path.abspath(params["export_dir"])

    calc_fields = model._meta.get_all_field_names()

    for param in set(params) - set(calc_fields):
        # the following parameters will be removed by HazardCalculation
        if param in ('ground_motion_correlation_model',
                     'ground_motion_correlation_params',
                     'individual_curves') and param not in (
                'preloaded_exposure_model_id', 'hazard_output_id',
                'hazard_calculation_id'):
            params.pop(param)
    calc = model.create(**params)
    calc.full_clean()
    calc.save()

    return calc


# used by bin/openquake and openquake.server.views
def run_calc(job, log_level, log_file, exports, job_type):
    """
    Run a calculation.

    :param job:
        :class:`openquake.engine.db.model.OqJob` instance which references a
        valid :class:`openquake.engine.db.models.RiskCalculation` or
        :class:`openquake.engine.db.models.HazardCalculation`.
    :param str log_level:
        The desired logging level. Valid choices are 'debug', 'info',
        'progress', 'warn', 'error', and 'critical'.
    :param str log_file:
        Complete path (including file name) to file where logs will be written.
        If `None`, logging will just be printed to standard output.
    :param list exports:
        A (potentially empty) list of export targets. Currently only "xml" is
        supported.
    :param str job_type:
        'hazard' or 'risk'
    """
    # first of all check the database version and exit if the db is outdated
    upgrader.check_versions(django_db.connections['admin'])

    calc_mode = getattr(job, '%s_calculation' % job_type).calculation_mode
    calculator = get_calculator_class(job_type, calc_mode)(job)

    # initialize log handlers
    handler = (LogFileHandler(job, log_file) if log_file
               else LogStreamHandler(job))
    logging.root.addHandler(handler)
    logs.set_level(log_level)
    try:
        with job_stats(job):  # run the job
            _do_run_calc(calculator, exports, job_type)
    finally:
        logging.root.removeHandler(handler)
    return calculator


def _switch_to_job_phase(job, job_type, status):
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
    logs.LOG.progress("%s (%s)", status, job_type)


def _do_run_calc(calc, exports, job_type):
    """
    Step through all of the phases of a calculation, updating the job
    status at each phase.

    :param calc:
        An :class:`~openquake.engine.calculators.base.Calculator` instance.
    :param list exports:
        a (potentially empty) list of export targets, currently only "xml" is
        supported
    :param str job_type:
        calculation type (hazard|risk)
    """
    job = calc.job

    _switch_to_job_phase(job, job_type, "pre_executing")
    calc.pre_execute()

    _switch_to_job_phase(job, job_type, "executing")
    calc.execute()

    _switch_to_job_phase(job, job_type, "post_executing")
    calc.post_execute()

    _switch_to_job_phase(job, job_type, "post_processing")
    calc.post_process()

    _switch_to_job_phase(job, job_type, "export")
    calc.export(exports=exports)

    _switch_to_job_phase(job, job_type, "clean_up")
    calc.clean_up()

    CacheInserter.flushall()  # flush caches into the db

    _switch_to_job_phase(job, job_type, "complete")
    logs.LOG.debug("*> complete")


def del_haz_calc(hc_id):
    """
    Delete a hazard calculation and all associated outputs.

    :param hc_id:
        ID of a :class:`~openquake.engine.db.models.HazardCalculation`.
    """
    try:
        hc = models.HazardCalculation.objects.get(id=hc_id)
    except exceptions.ObjectDoesNotExist:
        raise RuntimeError('Unable to delete hazard calculation: '
                           'ID=%s does not exist' % hc_id)

    user = getpass.getuser()
    if hc.oqjob.user_name == user:
        # we are allowed to delete this

        # but first, check if any risk calculations are referencing any of our
        # outputs, or the hazard calculation itself
        msg = UNABLE_TO_DEL_HC_FMT % (
            'The following risk calculations are referencing this hazard'
            ' calculation: %s'
        )

        # check for a reference to hazard outputs
        assoc_outputs = models.RiskCalculation.objects.filter(
            hazard_output__oq_job__hazard_calculation=hc_id
        )
        if assoc_outputs.count() > 0:
            raise RuntimeError(msg % ', '.join([str(x.id)
                                                for x in assoc_outputs]))

        # check for a reference to the hazard calculation itself
        assoc_calcs = models.RiskCalculation.objects.filter(
            hazard_calculation=hc_id
        )
        if assoc_calcs.count() > 0:
            raise RuntimeError(msg % ', '.join([str(x.id)
                                                for x in assoc_calcs]))

        # No risk calculation are referencing what we want to delete.
        # Carry on with the deletion.
        hc.delete(using='admin')
    else:
        # this doesn't belong to the current user
        raise RuntimeError(UNABLE_TO_DEL_HC_FMT % 'Access denied')


def del_risk_calc(rc_id):
    """
    Delete a risk calculation and all associated outputs.

    :param hc_id:
        ID of a :class:`~openquake.engine.db.models.RiskCalculation`.
    """
    try:
        rc = models.RiskCalculation.objects.get(id=rc_id)
    except exceptions.ObjectDoesNotExist:
        raise RuntimeError('Unable to delete risk calculation: '
                           'ID=%s does not exist' % rc_id)

    if rc.oqjob.user_name == getpass.getuser():
        # we are allowed to delete this
        rc.delete(using='admin')
    else:
        # this doesn't belong to the current user
        raise RuntimeError('Unable to delete risk calculation: '
                           'Access denied')


def list_hazard_outputs(hc_id, full=True):
    """
    List the outputs for a given
    :class:`~openquake.engine.db.models.HazardCalculation`.

    :param hc_id:
        ID of a hazard calculation.
    :param bool full:
        If True produce a full listing, otherwise a short version
    """
    outputs = get_outputs('hazard', hc_id)
    hc = models.HazardCalculation.objects.get(pk=hc_id)
    if hc.calculation_mode == 'scenario':  # ignore SES output
        outputs = outputs.filter(output_type='gmf_scenario')
    print_outputs_summary(outputs, full)


def touch_log_file(log_file):
    """
    If a log file destination is specified, attempt to open the file in
    'append' mode ('a'). If the specified file is not writable, an
    :exc:`IOError` will be raised.
    """
    open(os.path.abspath(log_file), 'a').close()


def print_results(calc_id, duration, list_outputs):
    print 'Calculation %d completed in %d seconds. Results:' % (
        calc_id, duration)
    list_outputs(calc_id, full=False)


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
                   'with the commands\n`openquake --list-hazard-outputs` or '
                   '`openquake --list-risk-outputs`')


def run_job(cfg_file, log_level, log_file, exports=(), hazard_output_id=None,
            hazard_job_id=None):
    """
    Run a job using the specified config file and other options.

    :param str cfg_file:
        Path to calculation config (INI-style) file.
    :param str log_level:
        'debug', 'info', 'warn', 'error', or 'critical'
    :param str log_file:
        Path to log file.
    :param list exports:
        A list of export types requested by the user. Currently only 'xml'
        is supported.
    :param str hazard_ouput_id:
        The Hazard Output ID used by the risk calculation (can be None)
    :param str hazard_job_id:
        The Hazard Job ID used by the risk calculation (can be None)
    """
    # first of all check the database version and exit if the db is outdated
    upgrader.check_versions(django_db.connections['admin'])
    with CeleryNodeMonitor(openquake.engine.no_distribute(), interval=3):
        hazard = hazard_output_id is None and hazard_job_id is None
        if log_file is not None:
            touch_log_file(log_file)

        job = job_from_file(
            cfg_file, getpass.getuser(), log_level, exports, hazard_output_id,
            hazard_job_id)

        # Instantiate the calculator and run the calculation.
        t0 = time.time()
        run_calc(
            job, log_level, log_file, exports, 'hazard' if hazard else 'risk')
        duration = time.time() - t0
        if hazard:
            if job.status == 'complete':
                print_results(job.hazard_calculation.id,
                              duration, list_hazard_outputs)
            else:
                sys.exit('Calculation %s failed' %
                         job.hazard_calculation.id)
        else:
            if job.status == 'complete':
                print_results(job.risk_calculation.id,
                              duration, list_risk_outputs)
            else:
                sys.exit('Calculation %s failed' %
                         job.risk_calculation.id)


@django_db.transaction.commit_on_success
def job_from_file(cfg_file_path, username, log_level='info', exports=(),
                  hazard_output_id=None, hazard_job_id=None):
    """
    Create a full job profile from a job config file.

    :param str cfg_file_path:
        Path to the job.ini.
    :param str username:
        The user who will own this job profile and all results.
    :param str log_level:
        Desired log level.
    :param exports:
        List of desired export types.
    :param int hazard_output_id:
        ID of a hazard output to use as input to this calculation. Specify
        this xor ``hazard_calculation_id``.
    :param int hazard_job_id:
        ID of a complete hazard job to use as input to this
        calculation. Specify this xor ``hazard_output_id``.

    :returns:
        :class:`openquake.engine.db.models.OqJob` object
    :raises:
        `RuntimeError` if the input job configuration is not valid
    """
    # determine the previous hazard job, if any
    if hazard_job_id:
        haz_job = models.OqJob.objects.get(pk=hazard_job_id)
    elif hazard_output_id:  # extract the hazard job from the hazard_output_id
        haz_job = models.Output.objects.get(pk=hazard_output_id).oq_job
    else:
        haz_job = None  # no previous hazard job
    if haz_job:
        assert haz_job.job_type == 'hazard', haz_job

    # create the current job
    job = prepare_job(user_name=username, log_level=log_level)
    # read calculation params and create the calculation profile
    oqparam = readini.parse_config(
        open(cfg_file_path), haz_job.id if haz_job else None, hazard_output_id)
    missing = set(oqparam.inputs) - INPUT_TYPES
    if missing:
        raise ValueError(
            'The parameters %s in the .ini file does '
            'not correspond to a valid input type' % ', '.join(missing))

    params = vars(oqparam).copy()
    job.save_params(params)

    if hazard_output_id is None and hazard_job_id is None:
        # this is a hazard calculation, not a risk one
        del params['hazard_calculation_id']
        del params['hazard_output_id']
        job.hazard_calculation = create_calculation(
            models.HazardCalculation, params)
        job.save()
        return job

    calculation = create_calculation(models.RiskCalculation, params)
    job.risk_calculation = calculation
    job.save()
    return job


def list_risk_outputs(rc_id, full=True):
    """
    List the outputs for a given
    :class:`~openquake.engine.db.models.RiskCalculation`.

    :param rc_id:
        ID of a risk calculation.
    :param bool full:
        If True produce a full listing, otherwise a short version
    """
    print_outputs_summary(get_outputs('risk', rc_id), full)


def get_outputs(job_type, calc_id):
    """
    :param job_type:
        'hazard' or 'risk'
    :param calc_id:
        ID of a calculation.
    :returns:
        A sequence of :class:`openquake.engine.db.models.Output` objects
    """
    if job_type == 'risk':
        return models.Output.objects.filter(oq_job__risk_calculation=calc_id)
    else:
        return models.Output.objects.filter(oq_job__hazard_calculation=calc_id)
