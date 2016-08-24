#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (C) 2016 GEM Foundation

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
from __future__ import print_function
import os
import operator
from datetime import datetime

from django.core import exceptions
from django import db

from openquake.risklib import valid
from openquake.commonlib import datastore
from openquake.server.db import models
from openquake.server.db.schema.upgrades import upgrader
from openquake.server.db import upgrade_manager

INPUT_TYPES = set(dict(models.INPUT_TYPE_CHOICES))
UNABLE_TO_DEL_HC_FMT = 'Unable to delete hazard calculation: %s'
UNABLE_TO_DEL_RC_FMT = 'Unable to delete risk calculation: %s'


def check_outdated():
    """
    Check if the db is outdated, called before starting anything
    """
    return upgrader.check_versions(db.connection)


def reset_is_running():
    """
    Reset the flag job.is_running to False. This is called when the
    Web UI is re-started: the idea is that it is restarted only when
    all computations are completed.
    """
    db.connection.cursor().execute(  # reset the flag job.is_running
        'UPDATE job SET is_running=0 WHERE is_running=1')


def create_job(calc_mode, description, user_name, datadir, hc_id=None):
    """
    Create job for the given user, return it.

    :param str calc_mode:
        Calculation mode, such as classical, event_based, etc
    :param user_name:
        User who owns/started this job.
    :param datadir:
        Data directory of the user who owns/started this job.
    :param description:
         Description of the calculation
    :param hc_id:
        If not None, then the created job is a risk job
    :returns:
        :class:`openquake.server.db.models.OqJob` instance.
    """
    calc_id = get_calc_id(datadir) + 1
    job = models.OqJob.objects.create(
        id=calc_id,
        calculation_mode=calc_mode,
        description=description,
        user_name=user_name,
        ds_calc_dir=os.path.join('%s/calc_%s' % (datadir, calc_id)))
    if hc_id:
        job.hazard_calculation = models.get(models.OqJob, pk=hc_id)
    job.save()
    return job.id


def delete_uncompleted_calculations(user):
    """
    Delete the uncompleted calculations of the given user
    """
    for job in models.OqJob.objects.filter(
            oqjob__user_name=user).exclude(
            oqjob__status="complete"):
        del_calc(job.id, user)


def get_job_id(job_id, username):
    """
    If job_id is negative, return the last calculation of the current
    user, otherwise returns the job_id unchanged.
    """
    job_id = int(job_id)
    if job_id > 0:
        return job_id
    my_jobs = models.OqJob.objects.filter(user_name=username).order_by('id')
    n = my_jobs.count()
    if n == 0:  # no jobs
        return
    else:  # typically job_id is -1
        return my_jobs[n + job_id].id


def get_calc_id(datadir, job_id=None):
    """
    Return the latest calc_id by looking both at the datastore
    and the database.
    """
    calcs = datastore.get_calc_ids(datadir)
    calc_id = 0 if not calcs else calcs[-1]
    if job_id is None:
        try:
            job_id = models.OqJob.objects.latest('id').id
        except exceptions.ObjectDoesNotExist:
            job_id = 0
    return max(calc_id, job_id)


def list_calculations(job_type, user_name):
    """
    Yield a summary of past calculations.

    :param job_type: 'hazard' or 'risk'
    """
    jobs = [job for job in models.OqJob.objects.filter(
        user_name=user_name).order_by('start_time')
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
                   'with the command\n`oq engine --list-outputs`')


def get_outputs(job_id):
    """
    :param job_id:
        ID of a calculation.
    :returns:
        A sequence of :class:`openquake.server.db.models.Output` objects
    """
    return models.Output.objects.filter(oq_job=job_id)

DISPLAY_NAME = dict(dmg_by_asset='dmg_by_asset_and_collapse_map')


def create_outputs(job_id, dskeys):
    """
    Build a correspondence between the outputs in the datastore and the
    ones in the database.

    :param job_id: ID of the current job
    :param dskeys: a list of datastore keys
    """
    job = models.get(models.OqJob, pk=job_id)
    for key in dskeys:
        models.Output.objects.create_output(
            job, DISPLAY_NAME.get(key, key), ds_key=key)


def finish(job_id, status):
    """
    Set the job columns `is_running`, `status`, and `stop_time`
    """
    job = models.get(models.OqJob, pk=job_id)
    job.is_running = False
    job.status = status
    job.stop_time = datetime.utcnow()
    job.save()


def del_calc(job_id, user):
    """
    Delete a calculation and all associated outputs.

    :param job_id:
        ID of a :class:`~openquake.server.db.models.OqJob`.
    """
    try:
        job = models.get(models.OqJob, pk=job_id)
    except models.NotFound:
        return ('Unable to delete calculation from db: '
                'ID=%s does not exist' % job_id)
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
        # not using Django since we got strange errors on Ubuntu 12.04
        # like https://ci.openquake.org/job/master_oq-engine/2581/console
        db.connection.cursor().execute(
            'DELETE FROM job WHERE id=%d' % job_id)
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
    db.connection.cursor().execute(
        'INSERT INTO log (job_id, timestamp, level, process, message) VALUES'
        '(%s, %s, %s, %s, %s)', (job_id, timestamp, level, process, message))


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
    out = models.get(models.Output, pk=output_id)
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


# used in make_report
def fetch(templ, *args):
    """
    Run queries directly on the database. Return header + rows
    """
    curs = db.connection.cursor()
    curs.execute(templ, args)
    header = [r[0] for r in curs.description]
    return [header] + curs.fetchall()


def get_dbpath():
    """
    Returns the path to the database file
    """
    curs = db.connection.cursor()
    curs.execute('PRAGMA database_list')
    # return a row with fields (id, dbname, dbpath)
    return curs.fetchall()[0][-1]


# ########################## upgrade operations ########################## #

def what_if_I_upgrade(extract_scripts):
    db.connection.cursor()  # bind the connection
    conn = db.connection.connection
    return upgrade_manager.what_if_I_upgrade(
        conn, extract_scripts=extract_scripts)


def version_db():
    db.connection.cursor()  # bind the connection
    conn = db.connection.connection
    return upgrade_manager.version_db(conn)


def upgrade_db():
    db.connection.cursor()  # bind the connection
    conn = db.connection.connection
    return upgrade_manager.upgrade_db(conn)


# ################### used in Web UI ######################## #

def calc_info(calc_id):
    """
    :param calc_id: calculation ID
    :returns: dictionary of info about the given calculation
    """
    job = models.get(models.OqJob, pk=calc_id)
    response_data = {}
    response_data['user_name'] = job.user_name
    response_data['status'] = job.status
    response_data['start_time'] = str(job.start_time)
    response_data['stop_time'] = str(job.stop_time)
    response_data['is_running'] = job.is_running
    return response_data


def get_calcs(request_get_dict, user_name, user_acl_on=False, id=None):
    """
    :returns:
        list of tuples (job_id, user_name, job_status, job_type,
                        job_is_running, job_description)
    """
    # helper to get job+calculation data from the oq-engine database
    jobs = models.OqJob.objects.filter()

    # user_acl_on is true if settings.ACL_ON = True or when the user is a
    # Django super user
    if user_acl_on:
        jobs = jobs.filter(user_name=user_name)

    if id is not None:
        jobs = jobs.filter(id=id)

    if 'job_type' in request_get_dict:
        job_type = request_get_dict.get('job_type')
        jobs = jobs.filter(hazard_calculation__isnull=job_type == 'hazard')

    if 'is_running' in request_get_dict:
        is_running = request_get_dict.get('is_running')
        jobs = jobs.filter(is_running=valid.boolean(is_running))

    if 'relevant' in request_get_dict:
        relevant = request_get_dict.get('relevant')
        jobs = jobs.filter(relevant=valid.boolean(relevant))

    return [(job.id, job.user_name, job.status, job.job_type,
             job.is_running, job.description) for job in jobs.order_by('-id')]


def set_relevant(calc_id, flag):
    """
    Set the `relevant` field of the given calculation record
    """
    job = models.get(models.OqJob, pk=calc_id)
    job.relevant = flag
    job.save()


def log_to_json(log):
    """
    Convert a log record into a list of strings
    """
    return [log.timestamp.isoformat()[:22],
            log.level, log.process, log.message]


def get_log_slice(calc_id, start, stop):
    """
    Get a slice of the calculation log as a JSON list of rows
    """
    start = start or 0
    stop = stop or None
    rows = models.Log.objects.filter(job_id=calc_id)[start:stop]
    return [log_to_json(row) for row in rows]


def get_log_size(calc_id):
    """
    Get a slice of the calculation log as a JSON list of rows
    """
    return models.Log.objects.filter(job_id=calc_id).count()


def get_traceback(calc_id):
    """
    Return the traceback of the given calculation as a list of lines.
    The list is empty if the calculation was successful.
    """
    # strange: understand why the filter returns two lines
    log = list(models.Log.objects.filter(job_id=calc_id, level='CRITICAL'))[-1]
    response_data = log.message.splitlines()
    return response_data


def get_result(result_id):
    """
    :returns: (job_id, job_status, datadir, datastore_key)
    """
    output = models.get(models.Output, pk=result_id)
    job = output.oq_job
    return job.id, job.status, os.path.dirname(job.ds_calc_dir), output.ds_key


def get_results(job_id):
    """
    :returns: (datadir, datastore_keys)
    """
    job = models.get(models.OqJob, pk=job_id)
    datadir = os.path.dirname(job.ds_calc_dir)
    return datadir, [output.ds_key for output in get_outputs(job_id)]
