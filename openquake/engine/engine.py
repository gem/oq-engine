# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2010-2016 GEM Foundation
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
import time
import getpass
import itertools
import operator
import traceback
from datetime import datetime

import celery.task.control

import openquake.engine

from django.core import exceptions
from django import db as django_db

from openquake.engine import logs
from openquake.server.db import models
from openquake.engine.utils import config, tasks
from openquake.engine.celery_node_monitor import CeleryNodeMonitor
from openquake.server.db.schema.upgrades import upgrader

from openquake.commonlib import readinput, valid, datastore, export
from openquake.calculators import base


def get_calc_id(job_id=None):
    """
    Return the latest calc_id by looking both at the datastore
    and the database.
    """
    calcs = datastore.get_calc_ids(datastore.DATADIR)
    calc_id = 1 if not calcs else calcs[-1]
    if job_id is None:
        try:
            job_id = models.OqJob.objects.latest('id').id
        except exceptions.ObjectDoesNotExist:
            job_id = 1
    return max(calc_id, job_id)

INPUT_TYPES = set(dict(models.INPUT_TYPE_CHOICES))

UNABLE_TO_DEL_HC_FMT = 'Unable to delete hazard calculation: %s'
UNABLE_TO_DEL_RC_FMT = 'Unable to delete risk calculation: %s'

TERMINATE = valid.boolean(
    config.get('celery', 'terminate_workers_on_revoke') or 'false')

USE_CELERY = valid.boolean(config.get('celery', 'use_celery') or 'false')


class InvalidCalculationID(Exception):
    pass

RISK_HAZARD_MAP = dict(
    scenario_risk=['scenario', 'scenario_risk'],
    scenario_damage=['scenario', 'scenario_damage'],
    classical_risk=['classical', 'classical_risk'],
    classical_bcr=['classical', 'classical_bcr'],
    classical_damage=['classical', 'classical_damage'],
    event_based_risk=['event_based', 'event_based_risk'])


# this is called only if USE_CELERY is True
def cleanup_after_job(job, terminate, task_ids=()):
    """
    Release the resources used by an openquake job.
    In particular revoke the running tasks (if any).

    :param int job_id: the job id
    :param bool terminate: the celery revoke command terminate flag
    :param task_ids: celery task IDs
    """
    # Using the celery API, terminate and revoke and terminate any running
    # tasks associated with the current job.
    if task_ids:
        logs.LOG.warn('Revoking %d tasks', len(task_ids))
    else:  # this is normal when OQ_NO_DISTRIBUTE=1
        logs.LOG.debug('No task to revoke')
    for tid in task_ids:
        celery.task.control.revoke(tid, terminate=terminate)
        logs.LOG.debug('Revoked task %s', tid)


def create_job(calc_mode, user_name="openquake", hc_id=None):
    """
    Create job for the given user, return it.

    :param str calc_mode:
        Calculation mode, such as classical, event_based, etc
    :param str username:
        Username of the user who owns/started this job. If the username doesn't
        exist, a user record for this name will be created.
    :param hc_id:
        If not None, then the created job is a risk job
    :returns:
        :class:`openquake.server.db.models.OqJob` instance.
    """
    calc_id = get_calc_id() + 1
    job = models.OqJob.objects.create(
        id=calc_id,
        calculation_mode=calc_mode,
        description='A job',
        user_name=user_name,
        ds_calc_dir=os.path.join(datastore.DATADIR, 'calc_%s' % calc_id))
    if hc_id:
        job.hazard_calculation = models.OqJob.objects.get(pk=hc_id)
    job.save()
    return job


# used by bin/openquake and openquake.server.views
def run_calc(job, log_level, log_file, exports, hazard_calculation_id=None):
    """
    Run a calculation.

    :param job:
        :class:`openquake.server.db.model.OqJob` instance
    :param str log_level:
        The desired logging level. Valid choices are 'debug', 'info',
        'progress', 'warn', 'error', and 'critical'.
    :param str log_file:
        Complete path (including file name) to file where logs will be written.
        If `None`, logging will just be printed to standard output.
    :param exports:
        A comma-separated string of export types.
    """
    # first of all check the database version and exit if the db is outdated
    upgrader.check_versions(django_db.connections['admin'])
    with logs.handle(job, log_level, log_file):  # run the job
        tb = 'None\n'
        try:
            _do_run_calc(job, exports, hazard_calculation_id)
            job.status = 'complete'
        except:
            tb = traceback.format_exc()
            try:
                logs.LOG.critical(tb)
                job.status = 'failed'
            except:  # an OperationalError may always happen
                sys.stderr.write(tb)
            raise
        finally:
            # try to save the job stats on the database and then clean up;
            # if there was an error in the calculation, this part may fail;
            # in such a situation, we simply log the cleanup error without
            # taking further action, so that the real error can propagate
            try:
                job.is_running = False
                job.stop_time = datetime.utcnow()
                job.save()
                if USE_CELERY:
                    cleanup_after_job(
                        job, TERMINATE, tasks.OqTaskManager.task_ids)
            except:
                # log the finalization error only if there is no real error
                if tb == 'None\n':
                    logs.LOG.error('finalizing', exc_info=True)
        expose_outputs(job.calc.datastore, job)
    return job.calc


# keep this as a private function, since it is mocked by engine_test.py
def _do_run_calc(job, exports, hazard_calculation_id):
    job.calc.run(exports=exports, hazard_calculation_id=hazard_calculation_id)


def del_calc(job_id):
    """
    Delete a calculation and all associated outputs.

    :param job_id:
        ID of a :class:`~openquake.server.db.models.OqJob`.
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
        # Carry on with the deletion. Notice that we cannot use job.delete()
        # directly because Django is so stupid that it reads from the database
        # all the records to delete before deleting them: thus, it runs out
        # of memory for large calculations
        curs = models.getcursor('admin')
        curs.execute('DELETE FROM uiapi.oq_job WHERE id=%s', (job_id,))
    else:
        # this doesn't belong to the current user
        raise RuntimeError(UNABLE_TO_DEL_HC_FMT % 'Access denied')
    try:
        os.remove(job.ds_calc_dir + '.hdf5')
    except:
        pass
    else:
        print('Removed %s' % job.ds_calc_dir + '.hdf5')


def list_outputs(job_id, full=True):
    """
    List the outputs for a given
    :class:`~openquake.server.db.models.OqJob`.

    :param job_id:
        ID of a calculation.
    :param bool full:
        If True produce a full listing, otherwise a short version
    """
    outputs = get_outputs(job_id)
    if models.oqparam(job_id).calculation_mode == 'scenario':
        # ignore SES output
        outputs = [o for o in outputs if o.output_type != 'ses']
    print_outputs_summary(outputs, full)


def print_results(job_id, duration, list_outputs):
    print 'Calculation %d completed in %d seconds. Results:' % (
        job_id, duration)
    list_outputs(job_id, full=False)


def print_outputs_summary(outputs, full=True):
    """
    List of :class:`openquake.server.db.models.Output` objects.
    """
    if len(outputs) > 0:
        truncated = False
        print '  id | name'
        outs = sorted(outputs, key=operator.attrgetter('display_name'))
        for i, o in enumerate(outs):
            if not full and i >= 10:
                print ' ... | %d additional output(s)' % (len(outs) - 10)
                truncated = True
                break
            print '%4d | %s' % (o.id, o.display_name)
        if truncated:
            print ('Some outputs where not shown. You can see the full list '
                   'with the command\n`oq-engine --list-outputs`')


# this function is called only by openquake_cli.py, not by the engine server
def run_job(cfg_file, log_level, log_file, exports='',
            hazard_output_id=None, hazard_calculation_id=None):
    """
    Run a job using the specified config file and other options.

    :param str cfg_file:
        Path to calculation config (INI-style) files.
    :param str log_level:
        'debug', 'info', 'warn', 'error', or 'critical'
    :param str log_file:
        Path to log file.
    :param exports:
        A comma-separated string of export types requested by the user.
        Currently only 'xml' is supported.
    """
    # first of all check the database version and exit if the db is outdated
    upgrader.check_versions(django_db.connections['admin'])
    with CeleryNodeMonitor(openquake.engine.no_distribute(), interval=3):
        job = job_from_file(
            cfg_file, getpass.getuser(), log_level, exports,
            hazard_output_id=hazard_output_id,
            hazard_calculation_id=hazard_calculation_id)
        t0 = time.time()
        run_calc(job, log_level, log_file, exports,
                 hazard_calculation_id=hazard_calculation_id)
        duration = time.time() - t0
        if job.status == 'complete':
            print_results(job.id, duration, list_outputs)
        else:
            sys.exit('Calculation %s failed' % job.id)
    return job

DISPLAY_NAME = dict(dmg_by_asset='dmg_by_asset_and_collapse_map')


def expose_outputs(dstore, job):
    """
    Build a correspondence between the outputs in the datastore and the
    ones in the database.

    :param dstore: a datastore instance
    :param job: an OqJob instance
    """
    exportable = set(ekey[0] for ekey in export.export)
    oq = job.get_oqparam()

    # small hack: remove the sescollection outputs from scenario
    # calculators, as requested by Vitor
    calcmode = oq.calculation_mode
    if 'scenario' in calcmode and 'sescollection' in exportable:
        exportable.remove('sescollection')
    uhs = oq.uniform_hazard_spectra
    if uhs and 'hmaps' in dstore:
        models.Output.objects.create_output(job, 'uhs', ds_key='uhs')

    for key in dstore:
        if key in exportable:
            if key == 'realizations' and len(dstore['realizations']) == 1:
                continue  # there is no point in exporting a single realization
            models.Output.objects.create_output(
                job, DISPLAY_NAME.get(key, key), ds_key=key)


def check_hazard_risk_consistency(haz_job, risk_mode):
    """
    Make sure that the provided hazard job is the right one for the
    current risk calculator.

    :param job:
        an OqJob instance referring to the previous hazard calculation
    :param risk_mode:
        the `calculation_mode` string of the current risk calculation
    """
    # check for obsolete calculation_mode
    if risk_mode in ('classical', 'event_based', 'scenario'):
        raise ValueError('Please change calculation_mode=%s into %s_risk '
                         'in the .ini file' % (risk_mode, risk_mode))

    # check calculation_mode consistency
    prev_mode = haz_job.calculation_mode
    ok_mode = RISK_HAZARD_MAP[risk_mode]
    if prev_mode not in ok_mode:
        raise InvalidCalculationID(
            'In order to run a risk calculation of kind %r, '
            'you need to provide a calculation of kind %r, '
            'but you provided a %r instead' %
            (risk_mode, ok_mode, prev_mode))


@django_db.transaction.atomic
def job_from_file(cfg_file, username, log_level='info', exports='',
                  hazard_output_id=None, hazard_calculation_id=None, **extras):
    """
    Create a full job profile from a job config file.

    :param str cfg_file:
        Path to the job.ini files.
    :param str username:
        The user who will own this job profile and all results.
    :param str log_level:
        Desired log level.
    :param exports:
        Comma-separated sting of desired export types
    :param hazard_output_id:
        Hazard output ID
    :param hazard_calculation_id:
        Hazard calculation ID
    :params extras:
        Extra parameters (used only in the tests to override the params)

    :returns:
        :class:`openquake.server.db.models.OqJob` object
    :raises:
        `RuntimeError` if the input job configuration is not valid
    """
    # read calculation params and create the calculation profile
    params = readinput.get_params([cfg_file])
    params.update(extras)
    # build and validate an OqParam object
    oq = readinput.get_oqparam(params)
    # create the current job
    job = create_job(oq.calculation_mode, username, hazard_calculation_id)
    calc = base.calculators(oq, calc_id=job.id)
    calc.save_params()
    job.description = oq.description
    job.calc = calc
    return job


# this is patched in the tests
def get_outputs(job_id):
    """
    :param job_id:
        ID of a calculation.
    :returns:
        A sequence of :class:`openquake.server.db.models.Output` objects
    """
    return models.Output.objects.filter(oq_job=job_id)
