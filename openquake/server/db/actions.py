#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (C) 2016-2017 GEM Foundation

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
import glob
import operator
from datetime import datetime

from openquake.hazardlib import valid
from openquake.commonlib import datastore
from openquake.server import __file__ as server_path
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

    :param db: a :class:`openquake.server.dbapi.Db` instance
    """
    return upgrader.check_versions(db.conn)


def reset_is_running(db):
    """
    Reset the flag job.is_running to False. This is called when the
    Web UI is re-started: the idea is that it is restarted only when
    all computations are completed.

    :param db: a :class:`openquake.server.dbapi.Db` instance
    """
    db('UPDATE job SET is_running=0 WHERE is_running=1')


def set_status(db, job_id, status):
    """
    Set the status 'created', 'executing', 'complete', 'failed'
    consistently with `is_running`.

    :param db: a :class:`openquake.server.dbapi.Db` instance
    :param job_id: ID of the current job
    :param status: status string
    """
    assert status in ('created', 'executing', 'complete', 'failed'), status
    if status in ('created', 'complete', 'failed'):
        is_running = 0
    else:  # 'executing'
        is_running = 1
    cursor = db('UPDATE job SET status=?x, is_running=?x WHERE id=?x',
                status, is_running, job_id)
    return cursor.rowcount


def create_job(db, calc_mode, description, user_name, datadir, hc_id=None):
    """
    Create job for the given user, return it.

    :param db:
        a :class:`openquake.server.dbapi.Db` instance
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
               is_running=0,
               ds_calc_dir=os.path.join('%s/calc_%s' % (datadir, calc_id)))
    job_id = db('INSERT INTO job (?S) VALUES (?X)',
                job.keys(), job.values()).lastrowid
    return job_id


def delete_uncompleted_calculations(db, user):
    """
    Delete the uncompleted calculations of the given user.

    :param db: a :class:`openquake.server.dbapi.Db` instance
    :param user: user name
    """
    db("DELETE FROM job WHERE user_name=?x AND status != 'complete'", user)


def get_job_id(db, job_id, username):
    """
    If job_id is negative, return the last calculation of the current
    user, otherwise returns the job_id unchanged.

    :param db: a :class:`openquake.server.dbapi.Db` instance
    :param job_id: a job ID (can be negative and can be nonexisting)
    :param username: an user name
    :returns: a valid job ID or None if the original job ID was invalid
    """
    job_id = int(job_id)
    if job_id > 0:
        return job_id
    joblist = db('SELECT id FROM job WHERE user_name=?x '
                 'ORDER BY id DESC LIMIT ?x', username, - job_id)
    if not joblist:  # no jobs
        return
    else:
        return joblist[-1].id


def get_calc_id(db, datadir, job_id=None):
    """
    Return the latest calc_id by looking both at the datastore
    and the database.

    :param db: a :class:`openquake.server.dbapi.Db` instance
    :param datadir: the directory containing the datastores
    :param job_id: a job ID; if None, returns the latest job ID
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

    :param db: a :class:`openquake.server.dbapi.Db` instance
    :param job_type: 'hazard' or 'risk'
    :param user_name: an user name
    """
    jobs = db('SELECT *, %s FROM job WHERE user_name=?x '
              'AND job_type=?x ORDER BY start_time' % JOB_TYPE,
              user_name, job_type)

    if len(jobs) == 0:
        yield 'None'
    else:
        yield ('job_id |     status |          start_time | '
               '        description')
        for job in jobs:
            descr = job.description
            start_time = job.start_time
            yield ('%6d | %10s | %s | %s' % (
                job.id, job.status, start_time, descr))


def list_outputs(db, job_id, full=True):
    """
    List the outputs for a given
    :class:`~openquake.server.db.models.OqJob`.

    :param db:
        a :class:`openquake.server.dbapi.Db` instance
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
    :param db:
        a :class:`openquake.server.dbapi.Db` instance
    :param job_id:
        ID of a calculation.
    :returns:
        A sequence of :class:`openquake.server.db.models.Output` objects
    """
    return db('SELECT * FROM output WHERE oq_job_id=?x', job_id)

DISPLAY_NAME = dict(dmg_by_asset='dmg_by_asset')


def create_outputs(db, job_id, dskeys):
    """
    Build a correspondence between the outputs in the datastore and the
    ones in the database.

    :param db: a :class:`openquake.server.dbapi.Db` instance
    :param job_id: ID of the current job
    :param dskeys: a list of datastore keys
    """
    rows = [(job_id, DISPLAY_NAME.get(key, key), key) for key in dskeys]
    db.insert('output', 'oq_job_id display_name ds_key'.split(), rows)


def finish(db, job_id, status):
    """
    Set the job columns `is_running`, `status`, and `stop_time`.

    :param db:
        a :class:`openquake.server.dbapi.Db` instance
    :param job_id:
        ID of the current job
    :param status:
        a string such as 'successful' or 'failed'
    """
    db('UPDATE job SET ?D WHERE id=?x',
       dict(is_running=False, status=status, stop_time=datetime.utcnow()),
       job_id)


def del_calc(db, job_id, user):
    """
    Delete a calculation and all associated outputs, if possible.

    :param db: a :class:`openquake.server.dbapi.Db` instance
    :param job_id: job ID, can be an integer or a string
    :param user: username
    :returns: None if everything went fine or an error message
    """
    job_id = int(job_id)
    dependent = db(
        'SELECT id FROM job WHERE hazard_calculation_id=?x', job_id)
    if dependent:
        return ('Cannot delete calculation %d: there are calculations '
                'dependent from it: %s' % (job_id, [j.id for j in dependent]))
    try:
        owner, path = db('SELECT user_name, ds_calc_dir FROM job WHERE id=?x',
                         job_id, one=True)
    except NotFound:
        return ('Cannot delete calculation %d: ID does not exist' % job_id)

    deleted = db('DELETE FROM job WHERE id=?x AND user_name=?x',
                 job_id, user).rowcount
    if not deleted:
        return ('Cannot delete calculation %d: it belongs to '
                '%s and you are %s' % (job_id, owner, user))

    # try to delete datastore and associated files
    # path has typically the form /home/user/oqdata/calc_XXX
    fnames = []
    for fname in glob.glob(path + '.*'):
        try:
            os.remove(fname)
        except OSError as exc:  # permission error
            print('Could not remove %s: %s' % (fname, exc))
        else:
            fnames.append(fname)
    return fnames


def log(db, job_id, timestamp, level, process, message):
    """
    Write a log record in the database.

    :param db:
        a :class:`openquake.server.dbapi.Db` instance
    :param job_id:
        a job ID
    :param timestamp:
        timestamp to store in the log record
    :param level:
        logging level to store in the log record
    :param process:
        process ID to store in the log record
    :param message:
        message to store in the log record
    """
    db('INSERT INTO log (job_id, timestamp, level, process, message) '
       'VALUES (?X)', (job_id, timestamp, level, process, message))


def get_log(db, job_id):
    """
    Extract the logs as a big string

    :param db: a :class:`openquake.server.dbapi.Db` instance
    :param job_id: a job ID
    """
    logs = db('SELECT * FROM log WHERE job_id=?x ORDER BY id', job_id)
    for log in logs:
        time = str(log.timestamp)[:-4]  # strip decimals
        yield '[%s #%d %s] %s' % (time, job_id, log.level, log.message)


def get_output(db, output_id):
    """
    :param db: a :class:`openquake.server.dbapi.Db` instance
    :param output_id: ID of an Output object
    :returns: (ds_key, calc_id, dirname)
    """
    out = db('SELECT output.*, ds_calc_dir FROM output, job '
             'WHERE oq_job_id=job.id AND output.id=?x', output_id, one=True)
    return out.ds_key, out.oq_job_id, os.path.dirname(out.ds_calc_dir)


def save_performance(db, job_id, records):
    """
    Save in the database the performance information about the given job.

    :param db: a :class:`openquake.server.dbapi.Db` instance
    :param job_id: a job ID
    :param records: a list of performance records
    """
    # NB: rec['counts'] is a numpy.uint64 which is not automatically converted
    # into an int in Ubuntu 12.04, so we convert it manually below
    rows = [(job_id, rec['operation'], rec['time_sec'], rec['memory_mb'],
             int(rec['counts'])) for rec in records]
    db.insert('performance',
              'job_id operation time_sec memory_mb counts'.split(), rows)


# used in make_report
def fetch(db, templ, *args):
    """
    Run generic queries directly on the database. See the documentation
    of the dbapi module.

    :param db: a :class:`openquake.server.dbapi.Db` instance
    :param templ: a SQL query template
    :param args: arguments to pass to the template
    """
    return db(templ, *args)


def get_path(db):
    """
    :param db:
        a :class:`openquake.server.dbapi.Db` instance
    :returns: the full path to the dbserver codebase
    """
    return server_path


def get_dbpath(db):
    """
    :param db: a :class:`openquake.server.dbapi.Db` instance
    :returns: the path to the database file.
    """
    rows = db('PRAGMA database_list')
    # return a row with fields (id, dbname, dbpath)
    return rows[0].file


# ########################## upgrade operations ########################## #

def what_if_I_upgrade(db, extract_scripts):
    """
    :param db: a :class:`openquake.server.dbapi.Db` instance
    :param extract_scripts: scripts to extract
    """
    return upgrade_manager.what_if_I_upgrade(
        db.conn, extract_scripts=extract_scripts)


def version_db(db):
    """
    :param db: a :class:`openquake.server.dbapi.Db` instance
    """
    return upgrade_manager.version_db(db.conn)


def upgrade_db(db):
    """
    :param db: a :class:`openquake.server.dbapi.Db` instance
    """
    return upgrade_manager.upgrade_db(db.conn)


# ################### used in Web UI ######################## #

def calc_info(db, calc_id):
    """
    :param db: a :class:`openquake.server.dbapi.Db` instance
    :param calc_id: calculation ID
    :returns: dictionary of info about the given calculation
    """
    job = db('SELECT * FROM job WHERE id=?x', calc_id, one=True)
    response_data = {}
    response_data['user_name'] = job.user_name
    response_data['status'] = job.status
    response_data['start_time'] = str(job.start_time)
    response_data['stop_time'] = str(job.stop_time)
    response_data['is_running'] = job.is_running
    return response_data


def get_calcs(db, request_get_dict, user_name, user_acl_on=False, id=None):
    """
    :param db:
        a :class:`openquake.server.dbapi.Db` instance
    :param request_get_dict:
        a dictionary
    :param user_name:
        user name
    :param user_acl_on:
        if True, returns only the calculations owned by the user
    :param id:
        if given, extract only the specified calculation
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

    if 'limit' in request_get_dict:
        limit = int(request_get_dict.get('limit'))
    else:
        limit = 100

    if 'start_time' in request_get_dict:
        # assume an ISO date string
        time_filter = "start_time >= '%s'" % request_get_dict.get('start_time')
    else:
        time_filter = 1

    jobs = db('SELECT *, %s FROM job WHERE ?A AND %s ORDER BY id DESC LIMIT %d'
              % (JOB_TYPE, time_filter, limit), filterdict)
    return [(job.id, job.user_name, job.status, job.job_type,
             job.is_running, job.description) for job in jobs]


def set_relevant(db, job_id, flag):
    """
    Set the `relevant` field of the given calculation record.

    :param db:
        a :class:`openquake.server.dbapi.Db` instance
    :param job_id:
        a job ID
    :param flag:
        flag for the field job.relevant
    """
    db('UPDATE job SET relevant=?x WHERE id=?x', flag, job_id)


def update_parent_child(db, parent_child):
    """
    Set hazard_calculation_id (parent) on a job_id (child)
    """
    db('UPDATE job SET hazard_calculation_id=?x WHERE id=?x',
       *parent_child)


def get_log_slice(db, job_id, start, stop):
    """
    Get a slice of the calculation log as a JSON list of rows

    :param db:
        a :class:`openquake.server.dbapi.Db` instance
    :param job_id:
        a job ID
    :param start:
        start of the slice
    :param stop:
        end of the slice (the last element is excluded)
    """
    start = int(start)
    stop = int(stop)
    limit = -1 if stop == 0 else stop - start
    logs = db('SELECT * FROM log WHERE job_id=?x '
              'ORDER BY id LIMIT ?s OFFSET ?s',
              job_id, limit, start)
    # NB: .isoformat() returns a string like '2016-08-29T15:42:34.984756'
    # we consider only the first 22 characters, i.e. '2016-08-29T15:42:34.98'
    return [[log.timestamp.isoformat()[:22], log.level,
             log.process, log.message] for log in logs]


def get_log_size(db, job_id):
    """
    Get a slice of the calculation log as a JSON list of rows.

    :param db:
        a :class:`openquake.server.dbapi.Db` instance
    :param job_id:
        a job ID
    """
    return db('SELECT count(id) FROM log WHERE job_id=?x', job_id,
              scalar=True)


def get_traceback(db, job_id):
    """
    Return the traceback of the given calculation as a list of lines.
    The list is empty if the calculation was successful.

    :param db:
        a :class:`openquake.server.dbapi.Db` instance
    :param job_id:
        a job ID
    """
    # strange: understand why the filter returns two lines
    log = db("SELECT * FROM log WHERE job_id=?x AND level='CRITICAL'",
             job_id)[-1]
    response_data = log.message.splitlines()
    return response_data


def get_result(db, result_id):
    """
    :param db:
        a :class:`openquake.server.dbapi.Db` instance
    :param result_id:
        a result ID
    :returns: (job_id, job_status, datadir, datastore_key)
    """
    job = db('SELECT job.*, ds_key FROM job, output WHERE '
             'oq_job_id=job.id AND output.id=?x', result_id, one=True)
    return job.id, job.status, os.path.dirname(job.ds_calc_dir), job.ds_key


def get_job(db, job_id, username):
    """
    :param db:
        a :class:`openquake.server.dbapi.Db` instance
    :param job_id:
        ID of the current job
    :param username:
        user name
    :returns: the full path to the datastore
    """
    calc_id = get_job_id(db, job_id, username) or job_id
    return db('SELECT * FROM job WHERE id=?x', calc_id, one=True)


def get_results(db, job_id):
    """
    :param db:
        a :class:`openquake.server.dbapi.Db` instance
    :param job_id:
        a job ID
    :returns: (datadir, datastore_keys)
    """
    ds_calc_dir = db('SELECT ds_calc_dir FROM job WHERE id=?x', job_id,
                     scalar=True)
    datadir = os.path.dirname(ds_calc_dir)
    return datadir, [output.ds_key for output in get_outputs(db, job_id)]


# ############################### db commands ########################### #

def get_longest_jobs(db):
    """
    :param db:
        a :class:`openquake.server.dbapi.Db` instance
    """
    query = '''-- completed jobs taking more than one hour
SELECT id, user_name, julianday(stop_time) - julianday(start_time) AS days
FROM job WHERE status='complete' AND days > 0.04 ORDER BY days desc'''
    return db(query)


def find(db, description):
    """
    :param db:
        a :class:`openquake.server.dbapi.Db` instance
    :param description:
        job description, used in a case-insensitive LIKE clause
    """
    query = '''-- completed jobs
SELECT id, description, user_name,
  (julianday(stop_time) - julianday(start_time)) * 24 AS hours
FROM job WHERE status='complete' AND description LIKE lower(?x)
ORDER BY id desc'''
    return db(query, description.lower())
