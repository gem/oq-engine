# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2016-2019 GEM Foundation
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
import psutil
import operator
from datetime import datetime

from openquake.hazardlib import valid
from openquake.baselib import datastore, general
from openquake.calculators.export import export
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
    DbServer is restarted: the idea is that it is restarted only when
    all computations are completed.

    :param db: a :class:`openquake.server.dbapi.Db` instance
    """
    db("UPDATE job SET is_running=0, status='failed'"
       "WHERE is_running=1 OR status='executing'")


def set_status(db, job_id, status):
    """
    Set the status 'created', 'executing', 'complete', 'failed', 'aborted'
    consistently with `is_running`.

    :param db: a :class:`openquake.server.dbapi.Db` instance
    :param job_id: ID of the current job
    :param status: status string
    """
    assert status in (
        'created', 'submitted', 'executing', 'complete', 'aborted', 'failed'
    ), status
    if status in ('created', 'complete', 'failed', 'aborted'):
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


def create_job(db, datadir):
    """
    Create job for the given user, return it.

    :param db:
        a :class:`openquake.server.dbapi.Db` instance
    :param datadir:
        Data directory of the user who owns/started this job.
    :returns:
        the job ID
    """
    calc_id = get_calc_id(db, datadir) + 1
    job = dict(id=calc_id, is_running=1, description='just created',
               user_name='openquake', calculation_mode='to be set',
               ds_calc_dir=os.path.join('%s/calc_%s' % (datadir, calc_id)))
    return db('INSERT INTO job (?S) VALUES (?X)',
              job.keys(), job.values()).lastrowid


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
               ds_calc_dir=os.path.join('%s/calc_%s' % (datadir, calc_id)))
    db('INSERT INTO job (?S) VALUES (?X)', job.keys(), job.values())


def delete_uncompleted_calculations(db, user):
    """
    Delete the uncompleted calculations of the given user.

    :param db: a :class:`openquake.server.dbapi.Db` instance
    :param user: user name
    """
    db("DELETE FROM job WHERE user_name=?x AND status != 'complete'", user)


def get_job(db, job_id, username=None):
    """
    If job_id is negative, return the last calculation of the current
    user, otherwise returns the job_id unchanged.

    :param db: a :class:`openquake.server.dbapi.Db` instance
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
                     'ORDER BY id DESC LIMIT ?x', username, -job_id)
    else:
        joblist = db('SELECT * FROM job ORDER BY id DESC LIMIT ?x', -job_id)
    if not joblist:  # no jobs
        return
    else:
        return joblist[-1]


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
        a :class:`openquake.server.dbapi.Db` instance
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
            out.append('Some outputs where not shown. You can see the full '
                       'list with the command\n`oq engine --list-outputs`')
    return out


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


DISPLAY_NAME = {
    'asset_risk': 'Exposure + Risk',
    'gmf_data': 'Ground Motion Fields',
    'dmg_by_asset': 'Average Asset Damages',
    'dmg_by_event': 'Aggregate Event Damages',
    'losses_by_asset': 'Average Asset Losses',
    'losses_by_event': 'Aggregate Event Losses',
    'damages-rlzs': 'Asset Damage Distribution',
    'damages-stats': 'Asset Damage Statistics',
    'dmg_by_event': 'Aggregate Event Damages',
    'avg_losses': 'Average Asset Losses',
    'avg_losses-rlzs': 'Average Asset Losses',
    'avg_losses-stats': 'Average Asset Losses Statistics',
    'loss_curves-rlzs': 'Asset Loss Curves',
    'loss_curves-stats': 'Asset Loss Curves Statistics',
    'loss_maps-rlzs': 'Asset Loss Maps',
    'loss_maps-stats': 'Asset Loss Maps Statistics',
    'agg_maps-rlzs': 'Aggregate Loss Maps',
    'agg_maps-stats': 'Aggregate Loss Maps Statistics',
    'agg_curves-rlzs': 'Aggregate Loss Curves',
    'agg_curves-stats': 'Aggregate Loss Curves Statistics',
    'agg_loss_table': 'Aggregate Loss Table',
    'agg_losses-rlzs': 'Aggregate Asset Losses',
    'agg_risk': 'Total Risk',
    'agglosses': 'Aggregate Asset Losses',
    'bcr-rlzs': 'Benefit Cost Ratios',
    'bcr-stats': 'Benefit Cost Ratios Statistics',
    'sourcegroups': 'Seismic Source Groups',
    'ruptures': 'Earthquake Ruptures',
    'hcurves': 'Hazard Curves',
    'hmaps': 'Hazard Maps',
    'uhs': 'Uniform Hazard Spectra',
    'disagg': 'Disaggregation Outputs',
    'disagg-stats': 'Disaggregation Statistics',
    'disagg_by_src': 'Disaggregation by Source',
    'realizations': 'Realizations',
    'fullreport': 'Full Report',
    'input': 'Input Files'
}

# sanity check, all display name keys must be exportable
dic = general.groupby(export, operator.itemgetter(0))
for key in DISPLAY_NAME:
    assert key in dic, key


def create_outputs(db, job_id, keysize, ds_size):
    """
    Build a correspondence between the outputs in the datastore and the
    ones in the database. Also, update the datastore size in the job table.

    :param db: a :class:`openquake.server.dbapi.Db` instance
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
        return {"error": 'Cannot delete calculation %d: there '
                'are calculations '
                'dependent from it: %s' % (job_id, [j.id for j in dependent])}
    try:
        owner, path = db('SELECT user_name, ds_calc_dir FROM job WHERE id=?x',
                         job_id, one=True)
    except NotFound:
        return {"error": 'Cannot delete calculation %d:'
                ' ID does not exist' % job_id}

    deleted = db('DELETE FROM job WHERE id=?x AND user_name=?x',
                 job_id, user).rowcount
    if not deleted:
        return {"error": 'Cannot delete calculation %d: it belongs to '
                '%s and you are %s' % (job_id, owner, user)}

    # try to delete datastore and associated file
    # path has typically the form /home/user/oqdata/calc_XXX
    fname = path + ".hdf5"
    try:
        os.remove(fname)
    except OSError as exc:  # permission error
        return {"error": 'Could not remove %s: %s' % (fname, exc)}
    return {"success": fname}


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
    out = []
    for log in logs:
        time = str(log.timestamp)[:-4]  # strip decimals
        out.append('[%s #%d %s] %s' % (time, job_id, log.level, log.message))
    return out


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


def db_version(db):
    """
    :param db: a :class:`openquake.server.dbapi.Db` instance
    """
    return upgrade_manager.db_version(db.conn)


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


def get_calcs(db, request_get_dict, allowed_users, user_acl_on=False, id=None):
    """
    :param db:
        a :class:`openquake.server.dbapi.Db` instance
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
                        job_is_running, job_description)
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

    if user_acl_on:
        users_filter = "user_name IN (?X)"
    else:
        users_filter = 1

    jobs = db('SELECT * FROM job WHERE ?A AND %s AND %s'
              ' ORDER BY id DESC LIMIT %d'
              % (users_filter, time_filter, limit), filterdict, allowed_users)
    return [(job.id, job.user_name, job.status, job.calculation_mode,
             job.is_running, job.description, job.pid,
             job.hazard_calculation_id, job.size_mb) for job in jobs]


def update_job(db, job_id, dic):
    """
    Update the given calculation record.

    :param db:
        a :class:`openquake.server.dbapi.Db` instance
    :param job_id:
        a job ID
    :param dic:
        a dictionary of valid field/values for the job table
    """
    db('UPDATE job SET ?D WHERE id=?x', dic, job_id)


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
    # strange: understand why the filter returns two lines or zero lines
    log = db("SELECT * FROM log WHERE job_id=?x AND level='CRITICAL'",
             job_id)
    if not log:
        return []
    response_data = log[-1].message.splitlines()
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
    return (job.id, job.status, job.user_name,
            os.path.dirname(job.ds_calc_dir), job.ds_key)


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

class List(list):
    _fields = ()


def get_executing_jobs(db):
    """
    :param db:
        a :class:`openquake.server.dbapi.Db` instance
    :returns:
        (id, pid, user_name, start_time) tuples
    """
    fields = 'id,pid,user_name,start_time'
    running = List()
    running._fields = fields.split(',')

    query = ('''-- executing jobs
SELECT %s FROM job WHERE status='executing' ORDER BY id desc''' % fields)
    rows = db(query)
    for r in rows:
        # if r.pid is 0 it means that such information
        # is not available in the database
        if r.pid and psutil.pid_exists(r.pid):
            running.append(r)
    return running


def get_longest_jobs(db):
    """
    :param db:
        a :class:`openquake.server.dbapi.Db` instance
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
        a :class:`openquake.server.dbapi.Db` instance
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
        a :class:`openquake.server.dbapi.Db` instance
    :param job_id:
        job ID
    :param value:
        value of the checksum (32 bit integer)
    """
    return db('INSERT INTO checksum VALUES (?x, ?x)', job_id, value).lastrowid


def update_job_checksum(db, job_id, checksum):
    """
    :param db:
        a :class:`openquake.server.dbapi.Db` instance
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
        a :class:`openquake.server.dbapi.Db` instance
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
        a :class:`openquake.server.dbapi.Db` instance
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
