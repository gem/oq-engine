# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2016-2025 GEM Foundation
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
import os
import getpass
import operator
from datetime import datetime, timezone

from openquake.baselib import general
from openquake.hazardlib import valid
from openquake.server import __file__ as server_path
from openquake.server.db.schema.upgrades import upgrader
from openquake.server.db import upgrade_manager
from openquake.commonlib.dbapi import NotFound
from openquake.calculators.export import DISPLAY_NAME

UTC = timezone.utc
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

    :param db: a :class:`openquake.commonlib.dbapi.Db` instance
    """
    return upgrader.check_versions(db.conn)


def reset_is_running(db):
    """
    Reset the flag job.is_running to False. This is called when the
    DbServer is restarted: the idea is that it is restarted only when
    all computations are completed.

    :param db: a :class:`openquake.commonlib.dbapi.Db` instance
    """
    db("UPDATE job SET is_running=0, status='failed'"
       "WHERE is_running=1 OR status='executing'")


def set_status(db, job_id, status):
    """
    Set the status 'created', 'executing', 'complete', 'failed', 'aborted'
    consistently with `is_running`.

    :param db: a :class:`openquake.commonlib.dbapi.Db` instance
    :param job_id: ID of the current job
    :param status: status string
    """
    assert status in (
        'created', 'submitted', 'executing', 'complete', 'aborted', 'failed',
        'deleted'), status
    if status in ('created', 'complete', 'failed', 'aborted', 'deleted'):
        is_running = 0
    else:  # 'executing'
        is_running = 1
    if job_id < 0:
        rows = db('SELECT id FROM job ORDER BY id DESC LIMIT ?x', -job_id)
        if not rows:
            return 0
        job_id = rows[-1].id
    cursor = db('UPDATE job SET status=?x, is_running=?x WHERE id=?x',
                status, is_running, job_id)
    return cursor.rowcount


def create_job(db, datadir, calculation_mode='to be set',
               description='just created', user_name=None,
               hc_id=None, host=None):
    """
    Create job for the given user, return it.

    :param db:
        a :class:`openquake.commonlib.dbapi.Db` instance
    :param datadir:
        data directory of the user who owns/started this job.
    :param calculation_mode:
        job kind
    :param description:
        description of the job
    :param user_name:
        name of the user running the job
    :param hc_id:
        ID of the parent job (if any)
    :param host:
        machine where the calculation is running (master)
    :returns:
        the job ID
    """
    # NB: is_running=1 is needed to make views_test.py happy on Jenkins
    job = dict(is_running=1, description=description,
               user_name=user_name or getpass.getuser(),
               calculation_mode=calculation_mode,
               ds_calc_dir=datadir, hazard_calculation_id=hc_id, host=host)
    job_id = db('INSERT INTO job (?S) VALUES (?X)', job.keys(), job.values()
                ).lastrowid
    db('UPDATE job SET ds_calc_dir=?x WHERE id=?x',
       os.path.join(datadir, 'calc_%s' % job_id), job_id)
    return job_id


def import_job(db, calc_id, calc_mode, description, user_name, status,
               hc_id, datadir):
    """
    Insert a calculation inside the database, if calc_id is not taken
    """
    job = dict(id=calc_id,
               calculation_mode=calc_mode,
               description=description,
               user_name=user_name,
               hazard_calculation_id=hc_id,
               is_running=0,
               status=status,
               ds_calc_dir=os.path.join(datadir, 'calc_%s' % calc_id))
    db('INSERT INTO job (?S) VALUES (?X)', job.keys(), job.values())


def delete_uncompleted_calculations(db, user):
    """
    Delete the uncompleted calculations of the given user.

    :param db: a :class:`openquake.commonlib.dbapi.Db` instance
    :param user: user name
    """
    db("UPDATE job SET status = 'deleted' "
       "WHERE user_name=?x AND status != 'complete'", user)


def get_job(db, job_id, username=None):
    """
    If job_id is negative, return the last calculation of the current
    user, otherwise returns the job_id unchanged.

    :param db: a :class:`openquake.commonlib.dbapi.Db` instance
    :param job_id: a job ID (can be negative and can be nonexisting)
    :param username: an user name (if None, ignore it)
    :returns: a valid job or None if the original job ID was invalid
    """
    job_id = int(job_id)

    if job_id > 0:
        dic = dict(id=job_id)
        if username:
            dic['user_name'] = username
        try:
            return db('SELECT * FROM job WHERE ?A', dic, one=True)
        except NotFound:
            return

    # else negative job_id
    if username:
        joblist = db('SELECT * FROM job WHERE user_name=?x '
                     "AND status != 'deleted' ORDER BY id DESC LIMIT ?x",
                     username, -job_id)
    else:
        joblist = db("SELECT * FROM job WHERE status != 'deleted' "
                     'ORDER BY id DESC LIMIT ?x', -job_id)
    if not joblist:  # no jobs
        return
    else:
        return joblist[-1]


def get_weight(db, job_id):
    """
    Return information about the total weight of the source model.

    :param db: a :class:`openquake.commonlib.dbapi.Db` instance
    :param job_id: a job ID
    """
    rows = db("SELECT description, message FROM log, job "
              "WHERE job_id=job.id and job.id = ?x "
              "AND message LIKE '%tot_weight%'", job_id)
    if not rows:
        return "There is no job %d" % job_id
    return rows[0]


def list_calculations(db, job_type, user_name):
    """
    Yield a summary of past calculations.

    :param db: a :class:`openquake.commonlib.dbapi.Db` instance
    :param job_type: 'hazard' or 'risk'
    :param user_name: an user name
    """
    jobs = db('SELECT *, %s FROM job WHERE user_name=?x '
              "AND job_type=?x AND status != 'deleted' ORDER BY start_time"
              % JOB_TYPE, user_name, job_type)
    out = []
    if len(jobs) == 0:
        out.append('None')
    else:
        out.append('job_id |     status |          start_time | '
                   '        description')
        for job in jobs:
            descr = job.description
            start_time = job.start_time
            out.append('%6d | %10s | %s | %s' % (
                job.id, job.status, start_time, descr))
    return out


def list_outputs(db, job_id, full=True):
    """
    List the outputs for a given
    :class:`~openquake.server.db.models.OqJob`.

    :param db:
        a :class:`openquake.commonlib.dbapi.Db` instance
    :param job_id:
        ID of a calculation.
    :param bool full:
        If True produce a full listing, otherwise a short version
    """
    outputs = get_outputs(db, job_id)
    out = []
    if len(outputs) > 0:
        truncated = False
        out.append('  id | name')
        outs = sorted(outputs, key=operator.attrgetter('display_name'))
        for i, o in enumerate(outs):
            if not full and i >= 10:
                out.append(' ... | %d additional output(s)' % (len(outs) - 10))
                truncated = True
                break
            out.append('%4d | %s' % (o.id, o.display_name))
        if truncated:
            out.append(
                'Some outputs were not shown. You can see the full list '
                f'with the command\n`oq engine --list-outputs {job_id}`')
    return out


def get_outputs(db, job_id):
    """
    :param db:
        a :class:`openquake.commonlib.dbapi.Db` instance
    :param job_id:
        ID of a calculation.
    :returns:
        A sequence of :class:`openquake.server.db.models.Output` objects
    """
    return db('SELECT * FROM output WHERE oq_job_id=?x', job_id)


def create_outputs(db, job_id, keysize, ds_size):
    """
    Build a correspondence between the outputs in the datastore and the
    ones in the database. Also, update the datastore size in the job table.

    :param db: a :class:`openquake.commonlib.dbapi.Db` instance
    :param job_id: ID of the current job
    :param keysize: a list of pairs (key, size_mb)
    :param ds_size: total datastore size in MB
    """
    rows = [(job_id, DISPLAY_NAME.get(key, key), key, size)
            for key, size in keysize]
    db('UPDATE job SET size_mb=?x WHERE id=?x', ds_size, job_id)
    db.insert('output', 'oq_job_id display_name ds_key size_mb'.split(), rows)


def finish(db, job_id, status):
    """
    Set the job columns `is_running`, `status`, and `stop_time`.

    :param db:
        a :class:`openquake.commonlib.dbapi.Db` instance
    :param job_id:
        ID of the current job
    :param status:
        a string such as 'successful' or 'failed'
    """
    db('UPDATE job SET ?D WHERE id=?x',
       dict(is_running=False, status=status, stop_time=datetime.now(UTC)),
       job_id)


def del_calc(db, job_id, user, delete_file=True, force=False):
    """
    Delete a calculation and all associated outputs, if possible.

    :param db: a :class:`openquake.commonlib.dbapi.Db` instance
    :param job_id: job ID, can be an integer or a string
    :param user: username
    :param delete_file: also delete the HDF5 file
    :param force: delete even if there are dependent calculations
    :returns: a dict with key "success" and value indicating
        the job id of the calculation or of its ancestor, or key "error"
        and value describing what went wrong
    """
    job_id = int(job_id)
    dependent = db(
        "SELECT id FROM job WHERE hazard_calculation_id=?x "
        "AND status != 'deleted'", job_id)
    job_ids = [dep.id for dep in dependent]
    if not force and job_id in job_ids:  # jobarray
        err = []
        for jid in job_ids:
            res = del_calc(db, jid, user, delete_file, force=True)
            if "error" in res:
                err.append(res["error"])
        if err:
            return {"error": ' '.join(err)}
        else:
            return {"success": 'children_of_%s' % job_id}
    elif not force and dependent:
        return {"error": 'Cannot delete calculation %d: there '
                'are calculations '
                'dependent from it: %s' % (job_id, [j.id for j in dependent])}
    try:
        owner, path = db('SELECT user_name, ds_calc_dir FROM job WHERE id=?x',
                         job_id, one=True)
    except NotFound:
        return {"error": 'Cannot delete calculation %d:'
                ' ID does not exist' % job_id}

    deleted = db("UPDATE job SET status='deleted' WHERE id=?x AND "
                 "user_name=?x", job_id, user).rowcount
    if not deleted:
        return {"error": 'Cannot delete calculation %d: it belongs to '
                '%s and you are %s' % (job_id, owner, user)}

    fname = path + ".hdf5"
    # A calculation could fail before it produces a hdf5, or somebody
    # may have canceled the file, so it could not exist
    if delete_file and os.path.isfile(fname):
        try:
            os.remove(fname)
        except OSError as exc:  # permission error
            return {"error": 'Could not remove %s: %s' % (fname, exc)}
    return {"success": str(job_id), "hdf5path": fname}


def log(db, job_id, timestamp, level, process, message):
    """
    Write a log record in the database.

    :param db:
        a :class:`openquake.commonlib.dbapi.Db` instance
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

    :param db: a :class:`openquake.commonlib.dbapi.Db` instance
    :param job_id: a job ID
    """
    logs = db('SELECT * FROM log WHERE job_id=?x ORDER BY id', job_id)
    out = []
    for log in logs:
        time = str(log.timestamp)[:-4]  # strip decimals
        out.append('[%s #%d %s] %s %s' %
                   (time, job_id, log.level, log.process, log.message))
    return out


def get_output(db, output_id):
    """
    :param db: a :class:`openquake.commonlib.dbapi.Db` instance
    :param output_id: ID of an Output object
    :returns: (ds_key, calc_id, dirname)
    """
    out = db('SELECT output.*, ds_calc_dir FROM output, job '
             'WHERE oq_job_id=job.id AND output.id=?x', output_id, one=True)
    return out.ds_key, out.oq_job_id, os.path.dirname(out.ds_calc_dir)


# used in make_report
def fetch(db, templ, *args):
    """
    Run generic queries directly on the database. See the documentation
    of the dbapi module.

    :param db: a :class:`openquake.commonlib.dbapi.Db` instance
    :param templ: a SQL query template
    :param args: arguments to pass to the template
    """
    return db(templ, *args)


def get_path(db):
    """
    :param db:
        a :class:`openquake.commonlib.dbapi.Db` instance
    :returns: the full path to the dbserver codebase
    """
    return server_path


def get_dbpath(db):
    """
    :param db: a :class:`openquake.commonlib.dbapi.Db` instance
    :returns: the path to the database file.
    """
    rows = db('PRAGMA database_list')
    # return a row with fields (id, dbname, dbpath)
    return rows[0].file


def engine_version(db):
    """
    :returns: git version as seen by the db
    """
    return general.engine_version()


# ########################## upgrade operations ########################## #

def what_if_I_upgrade(db, extract_scripts):
    """
    :param db: a :class:`openquake.commonlib.dbapi.Db` instance
    :param extract_scripts: scripts to extract
    """
    return upgrade_manager.what_if_I_upgrade(
        db.conn, extract_scripts=extract_scripts)


def db_version(db):
    """
    :param db: a :class:`openquake.commonlib.dbapi.Db` instance
    """
    return upgrade_manager.db_version(db.conn)


def upgrade_db(db):
    """
    :param db: a :class:`openquake.commonlib.dbapi.Db` instance
    """
    return upgrade_manager.upgrade_db(db.conn)


# ################### used in Web UI ######################## #

def calc_info(db, calc_id):
    """
    :param db: a :class:`openquake.commonlib.dbapi.Db` instance
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


def get_calcs(db, request_get_dict, allowed_users, user_acl_on=False, id=None):
    """
    :param db:
        a :class:`openquake.commonlib.dbapi.Db` instance
    :param request_get_dict:
        a dictionary
    :param allowed_users:
        a list of users
    :param user_acl_on:
        if True, returns only the calculations owned by the user or the group
    :param id:
        if given, extract only the specified calculation
    :returns:
        list of tuples (job_id, user_name, job_status, calculation_mode,
                        job_is_running, job_description, host)
    """
    # helper to get job+calculation data from the oq-engine database
    filterdict = {}

    if id is not None:
        filterdict['id'] = id

    if 'calculation_mode' in request_get_dict:
        filterdict['calculation_mode'] = request_get_dict.get(
            'calculation_mode')

    if 'is_running' in request_get_dict:
        is_running = request_get_dict.get('is_running')
        filterdict['is_running'] = valid.boolean(is_running)

    if 'limit' in request_get_dict:
        limit = int(request_get_dict.get('limit'))
    else:
        limit = 100

    if 'start_time' in request_get_dict:
        # assume an ISO date string
        time_filter = "start_time >= '%s'" % request_get_dict.get('start_time')
    else:
        time_filter = 1

    if user_acl_on:
        users_filter = "user_name IN (?X)"
    else:
        users_filter = 1

    jobs = db('SELECT * FROM job WHERE ?A AND %s AND %s '
              "AND status != 'deleted' OR status == 'shared' ORDER BY id DESC LIMIT %d"
              % (users_filter, time_filter, limit), filterdict, allowed_users)
    return [(job.id, job.user_name, job.status, job.calculation_mode,
             job.is_running, job.description, job.pid,
             job.hazard_calculation_id, job.size_mb, job.host,
             job.start_time)
            for job in jobs]


def update_job(db, job_id, dic):
    """
    Update the given calculation record.

    :param db:
        a :class:`openquake.commonlib.dbapi.Db` instance
    :param job_id:
        a job ID
    :param dic:
        a dictionary of valid field/values for the job table
    """
    db('UPDATE job SET ?D WHERE id=?x', dic, job_id)


def share_job(db, job_id, share):
    """
    Make the job visible to all users by setting its status to 'shared'.

    :param db:
        a :class:`openquake.commonlib.dbapi.Db` instance
    :param job_id:
        a job ID
    :param share: if False, revert the status to 'complete'
    """
    new_status = 'shared' if share else 'complete'
    initial_status = db('SELECT status FROM job WHERE id=?x', job_id)[0].status
    if new_status == initial_status:
        return {'success': f'Calculation {job_id} was already {initial_status}'}
    if initial_status not in ('complete', 'shared'):
        if share:
            err_msg = (f'Can not share calculation {job_id} from'
                       f' status "{initial_status}"')
        else:
            err_msg = (f'Can not force the status of calculation {job_id}'
                       f' from "{initial_status}" to "complete"')
        return {'error': err_msg}
    shared = db('UPDATE job SET ?D WHERE id=?x',
                {'status': new_status}, job_id).rowcount
    if not shared:
        return {'error':
                f'Can not change the status of calculation {job_id}'
                f' from "{initial_status}" to "{new_status}"'}
    return {'success': f'The status of calculation {job_id} was changed'
                       f' from "{initial_status}" to "{new_status}"'}


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
        a :class:`openquake.commonlib.dbapi.Db` instance
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
        a :class:`openquake.commonlib.dbapi.Db` instance
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
        a :class:`openquake.commonlib.dbapi.Db` instance
    :param job_id:
        a job ID
    """
    log = db("SELECT * FROM log WHERE job_id=?x AND level='CRITICAL'",
             job_id)
    if not log:
        return []
    response_data = log[-1].message.splitlines()
    return response_data


def get_result(db, result_id):
    """
    :param db:
        a :class:`openquake.commonlib.dbapi.Db` instance
    :param result_id:
        a result ID
    :returns: (job_id, job_status, datadir, datastore_key)
    """
    job = db('SELECT job.*, ds_key FROM job, output WHERE '
             'oq_job_id=job.id AND output.id=?x', result_id, one=True)
    return (job.id, job.status, job.user_name,
            os.path.dirname(job.ds_calc_dir), job.ds_key)


def get_results(db, job_id):
    """
    :param db:
        a :class:`openquake.commonlib.dbapi.Db` instance
    :param job_id:
        a job ID
    :returns: (datadir, datastore_keys)
    """
    ds_calc_dir = db('SELECT ds_calc_dir FROM job WHERE id=?x', job_id,
                     scalar=True)
    datadir = os.path.dirname(ds_calc_dir)
    return datadir, [output.ds_key for output in get_outputs(db, job_id)]


# ############################### db commands ########################### #

class List(list):
    _fields = ()


def get_executing_jobs(db):
    """
    :param db:
        a :class:`openquake.commonlib.dbapi.Db` instance
    :returns:
        (id, user_name, start_time) tuples
    """
    fields = 'id,pid,user_name,start_time'
    running = List()
    running._fields = fields.split(',')
    query = ('''-- executing jobs
SELECT %s FROM job WHERE is_running=1
AND start_time > datetime('now', '-2 days')
ORDER BY id desc''' % fields)
    running.extend(db(query))
    return running


def get_calc_ids(db, user):
    """
    :returns: calculation IDs of the given user
    """
    return [r.id for r in db('SELECT id FROM job WHERE user_name=?x', user)]


def get_longest_jobs(db):
    """
    :param db:
        a :class:`openquake.commonlib.dbapi.Db` instance
    :returns:
        (id, user_name, days) tuples
    """
    query = '''-- completed jobs taking more than one hour
SELECT id, user_name, julianday(stop_time) - julianday(start_time) AS days
FROM job WHERE status='complete' AND days > 0.04 ORDER BY days desc'''
    return db(query)


def find(db, description):
    """
    :param db:
        a :class:`openquake.commonlib.dbapi.Db` instance
    :param description:
        job description, used in a case-insensitive LIKE clause
    """
    query = '''-- completed jobs
SELECT id, description, user_name,
  (julianday(stop_time) - julianday(start_time)) * 24 AS hours
FROM job WHERE status='complete' AND description LIKE lower(?x)
ORDER BY julianday(stop_time) - julianday(start_time)'''
    return db(query, description.lower())


# checksums

def add_checksum(db, job_id, value):
    """
    :param db:
        a :class:`openquake.commonlib.dbapi.Db` instance
    :param job_id:
        job ID
    :param value:
        value of the checksum (32 bit integer)
    """
    return db('INSERT INTO checksum VALUES (?x, ?x)', job_id, value).lastrowid


def update_job_checksum(db, job_id, checksum):
    """
    :param db:
        a :class:`openquake.commonlib.dbapi.Db` instance
    :param job_id:
        job ID
    :param checksum:
        the checksum (32 bit integer)
    """
    db('UPDATE checksum SET job_id=?x WHERE hazard_checksum=?x',
       job_id, checksum)


def get_checksum_from_job(db, job_id):
    """
    :param db:
        a :class:`openquake.commonlib.dbapi.Db` instance
    :param job_id:
        job ID
    :returns:
        the value of the checksum or 0
    """
    checksum = db('SELECT hazard_checksum FROM checksum WHERE job_id=?x',
                  job_id, scalar=True)
    return checksum


def get_job_from_checksum(db, checksum):
    """
    :param db:
        a :class:`openquake.commonlib.dbapi.Db` instance
    :param job_id:
        job ID
    :returns:
        the job associated to the checksum or None
    """
    # there is an UNIQUE constraint both on hazard_checksum and job_id
    jobs = db('SELECT * FROM job WHERE id = ('
              'SELECT job_id FROM checksum WHERE hazard_checksum=?x)',
              checksum)  # 0 or 1 jobs
    if not jobs:
        return
    return jobs[0]
