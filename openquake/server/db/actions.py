#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2016, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
import os
import sys
import zipfile
import getpass
import operator
from datetime import datetime

from django.core import exceptions
from django import db

from openquake.commonlib import datastore, readinput
from openquake.server.db import models
from openquake.engine.export import core
from openquake.server.db.schema.upgrades import upgrader
from openquake.server.db import upgrade_manager


class InvalidCalculationID(Exception):
    pass

RISK_HAZARD_MAP = dict(
    scenario_risk=['scenario', 'scenario_risk'],
    scenario_damage=['scenario', 'scenario_damage'],
    classical_risk=['classical', 'classical_risk'],
    classical_bcr=['classical', 'classical_bcr'],
    classical_damage=['classical', 'classical_damage'],
    event_based_risk=['event_based', 'event_based_risk'])

INPUT_TYPES = set(dict(models.INPUT_TYPE_CHOICES))
UNABLE_TO_DEL_HC_FMT = 'Unable to delete hazard calculation: %s'
UNABLE_TO_DEL_RC_FMT = 'Unable to delete risk calculation: %s'


def check_outdated():
    """
    Check if the db is outdated
    """
    return upgrader.check_versions(db.connection)


def create_job(calc_mode, description, user_name="openquake", hc_id=None):
    """
    Create job for the given user, return it.

    :param str calc_mode:
        Calculation mode, such as classical, event_based, etc
    :param username:
        Username of the user who owns/started this job. If the username doesn't
        exist, a user record for this name will be created.
    :param description:
         Description of the calculation
    :param hc_id:
        If not None, then the created job is a risk job
    :returns:
        :class:`openquake.server.db.models.OqJob` instance.
    """
    calc_id = get_calc_id() + 1
    job = models.OqJob.objects.create(
        id=calc_id,
        calculation_mode=calc_mode,
        description=description,
        user_name=user_name,
        ds_calc_dir=os.path.join(datastore.DATADIR, 'calc_%s' % calc_id))
    if hc_id:
        job.hazard_calculation = models.OqJob.objects.get(pk=hc_id)
    job.save()
    return job


def delete_uncompleted_calculations():
    for job in models.OqJob.objects.filter(
            oqjob__user_name=getpass.getuser()).exclude(
            oqjob__status="successful"):
        del_calc(job.id, True)


def get_hc_id(hc_id):
    """
    If hc_id is negative, return the last calculation of the current user
    """
    hc_id = int(hc_id)
    if hc_id > 0:
        return hc_id
    return models.OqJob.objects.filter(
        user_name=getpass.getuser()).latest('id').id + hc_id + 1


def get_calc_id(job_id=None):
    """
    Return the latest calc_id by looking both at the datastore
    and the database.
    """
    calcs = datastore.get_calc_ids(datastore.DATADIR)
    calc_id = 0 if not calcs else calcs[-1]
    if job_id is None:
        try:
            job_id = models.OqJob.objects.latest('id').id
        except exceptions.ObjectDoesNotExist:
            job_id = 0
    return max(calc_id, job_id)


def list_calculations(job_type):
    """
    Yield a summary of past calculations.

    :param job_type: 'hazard' or 'risk'
    """
    jobs = [job for job in models.OqJob.objects.filter(
        user_name=getpass.getuser()).order_by('start_time')
            if job.job_type == job_type]

    if len(jobs) == 0:
        yield 'None'
    else:
        yield ('job_id |     status |          start_time | '
               '        description')
        for job in jobs:
            descr = job.description
            latest_job = job
            if latest_job.is_running:
                status = 'pending'
            else:
                if latest_job.status == 'complete':
                    status = 'successful'
                else:
                    status = 'failed'
            start_time = latest_job.start_time.strftime(
                '%Y-%m-%d %H:%M:%S %Z'
            )
            yield ('%6d | %10s | %s| %s' % (
                job.id, status, start_time, descr)).encode('utf-8')


def export_outputs(hc_id, target_dir, export_type):
    # make it possible commands like `oq-engine --eos -1 /tmp`
    outputs = models.Output.objects.filter(oq_job=hc_id)
    if not outputs:
        sys.exit('Found nothing to export for job %s' % hc_id)
    for output in outputs:
        yield('Exporting %s...' % output)
        try:
            export_output(output.id, target_dir, export_type)
        except Exception as exc:
            yield(exc)


def export_output(output_id, target_dir, export_type):
    """
    Simple UI wrapper around
    :func:`openquake.engine.export.core.export` which yields a summary
    of files exported, if any.
    """
    queryset = models.Output.objects.filter(pk=output_id)
    if not queryset.exists():
        yield 'No output found for OUTPUT_ID %s' % output_id
        return

    if queryset.all()[0].oq_job.status != "complete":
        yield ("Exporting output produced by a job which did not run "
               "successfully. Results might be uncomplete")

    the_file = core.export(output_id, target_dir, export_type)
    if the_file.endswith('.zip'):
        dname = os.path.dirname(the_file)
        fnames = zipfile.ZipFile(the_file).namelist()
        yield('Files exported:')
        for fname in fnames:
            yield(os.path.join(dname, fname))
    else:
        yield('File exported: %s' % the_file)


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
    return print_outputs_summary(outputs, full)


def print_outputs_summary(outputs, full=True):
    """
    List of :class:`openquake.server.db.models.Output` objects.
    """
    if len(outputs) > 0:
        truncated = False
        yield '  id | name'
        outs = sorted(outputs, key=operator.attrgetter('display_name'))
        for i, o in enumerate(outs):
            if not full and i >= 10:
                yield ' ... | %d additional output(s)' % (len(outs) - 10)
                truncated = True
                break
            yield '%4d | %s' % (o.id, o.display_name)
        if truncated:
            yield ('Some outputs where not shown. You can see the full list '
                   'with the command\n`oq-engine --list-outputs`')


def get_outputs(job_id):
    """
    :param job_id:
        ID of a calculation.
    :returns:
        A sequence of :class:`openquake.server.db.models.Output` objects
    """
    return models.Output.objects.filter(oq_job=job_id)


@db.transaction.atomic
def job_from_file(cfg_file, username, hazard_calculation_id=None):
    """
    Create a full job profile from a job config file.

    :param str cfg_file:
        Path to a job.ini file.
    :param str username:
        The user who will own this job profile and all results.
    :param hazard_calculation_id:
        ID of a previous calculation or None
    :returns:
        a pair (job_id, oqparam)
    """
    oq = readinput.get_oqparam(cfg_file)
    job = create_job(oq.calculation_mode, oq.description,
                     username, hazard_calculation_id)
    return job.id, oq

DISPLAY_NAME = dict(dmg_by_asset='dmg_by_asset_and_collapse_map')


def create_outputs(job_id, dskeys):
    """
    Build a correspondence between the outputs in the datastore and the
    ones in the database.

    :param job_id: ID of the current job
    :param dskeys: a list of datastore keys
    """
    job = models.OqJob.objects.get(pk=job_id)
    for key in dskeys:
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


def finish(job_id, status):
    """
    Set the job columns `is_running`, `status`, and `stop_time`
    """
    job = models.OqJob.objects.get(pk=job_id)
    job.is_running = False
    job.status = status
    job.stop_time = datetime.utcnow()
    job.save()


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
        curs = db.connection.cursor()
        curs.execute('DELETE FROM job WHERE id=%s', (job_id,))
    else:
        # this doesn't belong to the current user
        raise RuntimeError(UNABLE_TO_DEL_HC_FMT % 'Access denied')
    try:
        os.remove(job.ds_calc_dir + '.hdf5')
    except:  # already removed or missing permission
        pass


def log(job_id, timestamp, level, process, message):
    """
    Write a log record in the database
    """
    models.Log.objects.create(
        job_id=job_id, timestamp=timestamp,
        level=level, process=process, message=message)


def get_log(job_id):
    """
    Extract the logs as a big string
    """
    logs = models.Log.objects.filter(job=job_id).order_by('id')
    for log in logs:
        time = str(log.timestamp)[:-4]  # strip decimals
        yield '[%s #%d %s] %s' % (time, job_id, log.level, log.message)


def get_output(output_id):
    """
    :param output_id: ID of an Output object
    :returns: (ds_key, calc_id, dirname)
    """
    out = models.Output.objects.get(pk=output_id)
    return out.ds_key, out.oq_job.id, os.path.dirname(out.oq_job.ds_calc_dir)


def save_performance(job_id, records):
    """
    Save in the database the performance information about the given job
    """
    for rec in records:
        models.Performance.objects.create(
            job_id=job_id, operation=rec['operation'],
            time_sec=rec['time_sec'], memory_mb=rec['memory_mb'],
            counts=rec['counts'])


# ########################## upgrade operations ########################## #

def what_if_I_upgrade(extract_scripts):
    conn = db.connection.connection
    return upgrade_manager.what_if_I_upgrade(
        conn, extract_scripts=extract_scripts)


def version_db():
    conn = db.connection.connection
    return upgrade_manager.version_db(conn)


def upgrade_db():
    conn = db.connection.connection
    return upgrade_manager.upgrade_db(conn)
