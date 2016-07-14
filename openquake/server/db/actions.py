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

from openquake.risklib import valid
from openquake.commonlib import datastore
from openquake.server.db.schema.upgrades import upgrader
from openquake.server.db import upgrade_manager
from openquake.server.dbapi import NotFound

JOB_TYPE = '''CASE
WHEN calculation_mode LIKE '%risk'
OR calculation_mode LIKE '%bcr'
OR calculation_mode LIKE '%damage'
THEN 'risk'
ELSE 'hazard'
END AS job_type
'''


def check_outdated(db):
    """
    Check if the db is outdated, called before starting anything
    """
    return upgrader.check_versions(db.conn)


def reset_is_running(db):
    """
    Reset the flag job.is_running to False. This is called when the
    Web UI is re-started: the idea is that it is restarted only when
    all computations are completed.
    """
    db('UPDATE job SET is_running=0 WHERE is_running=1')


def create_job(db, calc_mode, description, user_name, datadir, hc_id=None):
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
    calc_id = get_calc_id(db, datadir) + 1
    job = dict(id=calc_id,
               calculation_mode=calc_mode,
               description=description,
               user_name=user_name,
               hazard_calculation_id=hc_id,
               ds_calc_dir=os.path.join('%s/calc_%s' % (datadir, calc_id)))
    db('INSERT INTO job ($T) VALUES ($S)', job.keys(), job.values())
    job_id = db('SELECT seq FROM sqlite_sequence WHERE name="job"',
                scalar=True)
    return job_id


def delete_uncompleted_calculations(db, user):
    """
    Delete the uncompleted calculations of the given user
    """
    db("DELETE FROM job WHERE user_name=$s AND status != 'complete'", user)


def get_job_id(db, job_id, username):
    """
    If job_id is negative, return the last calculation of the current
    user, otherwise returns the job_id unchanged.
    """
    job_id = int(job_id)
    if job_id > 0:
        return job_id
    my_jobs = db('SELECT id FROM job WHERE user_name=$s ORDER BY id',
                 username)
    n = len(my_jobs)
    if n == 0:  # no jobs
        return
    else:  # typically job_id is -1
        return my_jobs[n + job_id].id


def get_calc_id(db, datadir, job_id=None):
    """
    Return the latest calc_id by looking both at the datastore
    and the database.
    """
    calcs = datastore.get_calc_ids(datadir)
    calc_id = 0 if not calcs else calcs[-1]
    if job_id is None:
        try:
            job_id = db('SELECT seq FROM sqlite_sequence WHERE name="job"',
                        scalar=True)
        except NotFound:
            job_id = 0
    return max(calc_id, job_id)


def list_calculations(db, job_type, user_name):
    """
    Yield a summary of past calculations.

    :param job_type: 'hazard' or 'risk'
    """
    jobs = db('SELECT *, %s FROM job WHERE user_name=$s '
              'AND job_type=$s ORDER BY start_time' % JOB_TYPE,
              user_name, job_type)

    if len(jobs) == 0:
        yield 'None'
    else:
        yield ('job_id |     status |          start_time | '
               '        description')
        for job in jobs:
            descr = job.description
            if job.is_running:
                status = 'pending'
            else:
                if job.status == 'complete':
                    status = 'successful'
                else:
                    status = 'failed'
            start_time = job.start_time
            yield ('%6d | %10s | %s| %s' % (
                job.id, status, start_time, descr)).encode('utf-8')


def list_outputs(db, job_id, full=True):
    """
    List the outputs for a given
    :class:`~openquake.server.db.models.OqJob`.

    :param job_id:
        ID of a calculation.
    :param bool full:
        If True produce a full listing, otherwise a short version
    """
    outputs = get_outputs(db, job_id)
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


def get_outputs(db, job_id):
    """
    :param job_id:
        ID of a calculation.
    :returns:
        A sequence of :class:`openquake.server.db.models.Output` objects
    """
    return db('SELECT * FROM output WHERE oq_job_id=$s', job_id)

DISPLAY_NAME = dict(dmg_by_asset='dmg_by_asset_and_collapse_map')


def create_outputs(db, job_id, dskeys):
    """
    Build a correspondence between the outputs in the datastore and the
    ones in the database.

    :param job_id: ID of the current job
    :param dskeys: a list of datastore keys
    """
    rows = [(job_id, DISPLAY_NAME.get(key, key), key) for key in dskeys]
    db.insert('output', 'oq_job_id display_name ds_key'.split(), rows)


# FIXME: this is not an action
def finish(db, job_id, status):
    """
    Set the job columns `is_running`, `status`, and `stop_time`
    """
    db('UPDATE job SET $D WHERE id=$s',
       dict(is_running=False, status=status, stop_time=datetime.utcnow()),
       job_id)


def del_calc(db, job_id, user):
    """
    Delete a calculation and all associated outputs, if possible.

    :param job_id: job ID
    :param user: username
    :returns: None if everything went fine or an error message
    """
    dependent = db(
        'SELECT id FROM job WHERE hazard_calculation_id=$s', job_id)
    if dependent:
        return ('Cannot delete calculation %d: there are calculations '
                'dependent from it: %s' % job_id, [j.id for j in dependent])
    deleted = db('DELETE FROM job WHERE id=$s', job_id).rowcount
    if not deleted:
        return ('Cannot delete calculation %d: ID does not exist' % job_id)
    deleted = db('DELETE FROM job WHERE id=$s AND user_name=$s',
                 job_id, user).rowcount
    if not deleted:
        return ('Cannot delete calculation %d: belongs to a different user'
                % job_id)


def log(db, job_id, timestamp, level, process, message):
    """
    Write a log record in the database
    """
    db('INSERT INTO log (job_id, timestamp, level, process, message) '
       'VALUES ($S)', (job_id, timestamp, level, process, message))


def get_log(db, job_id):
    """
    Extract the logs as a big string
    """
    logs = db('SELECT * FROM log WHERE job_id=$s ORDER BY id', job_id)
    for log in logs:
        time = str(log.timestamp)[:-4]  # strip decimals
        yield '[%s #%d %s] %s' % (time, job_id, log.level, log.message)


def get_output(db, output_id):
    """
    :param output_id: ID of an Output object
    :returns: (ds_key, calc_id, dirname)
    """
    out = db('SELECT output.*, ds_calc_dir FROM output, job '
             'WHERE oq_job_id=job.id AND output.id=$s', output_id, one=True)
    return out.ds_key, out.oq_job_id, os.path.dirname(out.ds_calc_dir)


def save_performance(db, job_id, records):
    """
    Save in the database the performance information about the given job
    """
    rows = [(job_id, rec['operation'], rec['time_sec'], rec['memory_mb'],
             rec['counts']) for rec in records]
    db.insert('performance',
              'job_id operation time_sec memory_mb counts'.split(), rows)


# used in make_report
def fetch(db, templ, *args):
    """
    Run queries directly on the database. Return header + rows
    """
    return db(templ, *args, header=True)


def get_dbpath(db):
    """
    Returns the path to the database file
    """
    curs = db('PRAGMA database_list')
    # return a row with fields (id, dbname, dbpath)
    return curs.fetchall()[0][-1]


# ########################## upgrade operations ########################## #

def what_if_I_upgrade(db, extract_scripts):
    return upgrade_manager.what_if_I_upgrade(
        db.conn, extract_scripts=extract_scripts)


def version_db(db):
    return upgrade_manager.version_db(db.conn)


def upgrade_db(db):
    return upgrade_manager.upgrade_db(db.conn)


# ################### used in Web UI ######################## #

def calc_info(db, calc_id):
    """
    :param calc_id: calculation ID
    :returns: dictionary of info about the given calculation
    """
    job = db('SELECT * FROM job WHERE id=$s', calc_id, one=True)
    response_data = {}
    response_data['user_name'] = job.user_name
    response_data['status'] = job.status
    response_data['start_time'] = str(job.start_time)
    response_data['stop_time'] = str(job.stop_time)
    response_data['is_running'] = job.is_running
    return response_data


def get_calcs(db, request_get_dict, user_name, user_acl_on=False, id=None):
    """
    :returns:
        list of tuples (job_id, user_name, job_status, job_type,
                        job_is_running, job_description)
    """
    # helper to get job+calculation data from the oq-engine database
    filterdict = {}

    # user_acl_on is true if settings.ACL_ON = True or when the user is a
    # Django super user
    if user_acl_on:
        filterdict['user_name'] = user_name

    if id is not None:
        filterdict['id'] = id

    if 'job_type' in request_get_dict:
        filterdict['job_type'] = request_get_dict.get('job_type')

    if 'is_running' in request_get_dict:
        is_running = request_get_dict.get('is_running')
        filterdict['is_running'] = valid.boolean(is_running)

    if 'relevant' in request_get_dict:
        relevant = request_get_dict.get('relevant')
        filterdict['relevant'] = valid.boolean(relevant)
    jobs = db('SELECT *, %s FROM job WHERE $A ORDER BY id DESC' % JOB_TYPE,
              filterdict)
    return [(job.id, job.user_name, job.status, job.job_type,
             job.is_running, job.description) for job in jobs]


def set_relevant(db, calc_id, flag):
    """
    Set the `relevant` field of the given calculation record
    """
    db('UPDATE job SET relevant=$s WHERE id=$s', flag, calc_id)


def get_log_slice(db, calc_id, start, stop):
    """
    Get a slice of the calculation log as a JSON list of rows
    """
    start = int(start)
    stop = int(stop)
    limit = -1 if stop == 0 else stop - start
    logs = db('SELECT * FROM log WHERE job_id=$s '
              'ORDER BY id LIMIT $t OFFSET $t',
              calc_id, limit, start)
    return [[log.timestamp[:22], log.level, log.process, log.message]
            for log in logs]


def get_log_size(db, calc_id):
    """
    Get a slice of the calculation log as a JSON list of rows
    """
    return db('SELECT count(id) FROM log WHERE job_id=$s', calc_id,
              scalar=True)


def get_traceback(db, calc_id):
    """
    Return the traceback of the given calculation as a list of lines.
    The list is empty if the calculation was successful.
    """
    # strange: understand why the filter returns two lines
    log = db("SELECT * FROM log WHERE job_id=$s AND level='CRITICAL'",
             calc_id)[-1]
    response_data = log.message.splitlines()
    return response_data


def get_result(db, result_id):
    """
    :returns: (job_id, job_status, datadir, datastore_key)
    """
    job = db('SELECT job.*, ds_key FROM job, output WHERE '
             'oq_job_id=job.id AND output.id=$s', result_id, one=True)
    return job.id, job.status, os.path.dirname(job.ds_calc_dir), job.ds_key


def get_results(db, job_id):
    """
    :returns: (datadir, datastore_keys)
    """
    ds_calc_dir = db('SELECT ds_calc_dir FROM job WHERE id=$s', job_id,
                     scalar=True)
    datadir = os.path.dirname(ds_calc_dir)
    return datadir, [output.ds_key for output in get_outputs(db, job_id)]
