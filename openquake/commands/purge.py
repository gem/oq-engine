# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2025 GEM Foundation
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
import os
import re
import shutil
import getpass
from openquake.baselib import config
from openquake.baselib.general import humansize
from openquake.commonlib import logs

datadir = logs.get_datadir()


def purge_one(calc_id, user, force):
    """
    Remove one calculation ID from the database and remove its datastore
    """
    logs.dbcmd('del_calc', calc_id, user, False, force)
    f1 = os.path.join(datadir, 'calc_%s.hdf5' % calc_id)
    f2 = os.path.join(datadir, 'calc_%s_tmp.hdf5' % calc_id)
    for f in [f1, f2]:
        if os.path.exists(f):  # not removed yet
            os.remove(f)
            print('Removed %s' % f)


# used in the reset command
def purge_all(user=None):
    """
    Remove all calculations of the given user
    """
    user = user or getpass.getuser()
    if os.path.exists(datadir):
        for fname in os.listdir(datadir):
            if fname.endswith('.pik'):
                os.remove(os.path.join(datadir, fname))
            mo = re.match(r'calc_(\d+)(_tmp)?\.hdf5', fname)
            if mo is not None:
                calc_id = int(mo.group(1))
                purge_one(calc_id, user, force=True)
    custom_tmp = config.directory.custom_tmp
    if custom_tmp and os.path.exists(custom_tmp):
        for path in os.listdir(custom_tmp):
            fullpath = os.path.join(custom_tmp, path)
            if os.path.isdir(fullpath):
                try:
                    shutil.rmtree(fullpath)
                except PermissionError:
                    pass
                else:
                    print(f'Removed {fullpath}')


def purge_orphan(force):
    """
    Purge orphan files not referenced in the database
    """
    # first purge non-relevant workflows, thus leaving orphan calculations
    logs.dbcmd("DELETE FROM job WHERE calculation_mode='workflow'"
               " AND not relevant")
    logs.dbcmd("VACUUM")
    dbfiles = {rec[0] for rec in logs.dbcmd(
        'SELECT ds_calc_dir || ".hdf5" FROM job')}
    hdf5files = {os.path.join(datadir, f)
                 for f in os.listdir(datadir)
                 if f.endswith('.hdf5')}
    n = 0
    size = 0
    for orphan in hdf5files - dbfiles:
        if os.access(orphan, os.W_OK):
            size += os.path.getsize(orphan)
            if force:
                os.remove(orphan)
            n += 1

    if force:
        print(f'Removed {n:_d} orphan files [{humansize(size)}]')
    else:
        print(f'Found {n:_d} orphan files [{humansize(size)}]')
        print('Use --force to really delete the files')


# NB: by looking at the database start_time we are not removing calculations
# used in the cache, however orphan files may linger in the filesystem
def purge_db(status, days, force):
    """
    Remove calculations of the given `status` older than `days`, unless they
    belong to a workflow.
    """
    query = 'SELECT id, ds_calc_dir || ".hdf5" FROM job '
    query += "WHERE workflow_id is NULL "
    query += f"AND start_time < datetime('now', '-{days} days')"
    if status:
        query += f'AND status IN {status}'
    todelete = []
    totsize = 0
    calc_ids = []
    for calc_id, fname in logs.dbcmd(query):
        if os.path.exists(fname) and os.access(fname, os.W_OK):
            calc_ids.append(calc_id)
            todelete.append(fname)
            totsize += os.path.getsize(fname)
            tname = fname.replace('.hdf5', '_tmp.hdf5')
            if os.path.exists(tname) and os.access(tname, os.W_OK):
                todelete.append(tname)
                totsize += os.path.getsize(tname)
    for fname in set(todelete):  # avoid possible duplicates due to the cache
        print(fname)
        if force:
            os.remove(fname)
    size = humansize(totsize)
    if force:
        print('Removed %d HDF5 files, %s' % (len(todelete), size))
        logs.dbcmd('DELETE FROM job WHERE id in (?X)', calc_ids)
    elif todelete:
        print('Found %d HDF5 files, %s' % (len(todelete), size))
        print('Use --force to really delete the calculations and jobs')


def main(what:str, force:bool=False, *, days:int=30):
    """
    Remove calculations from the database and the file system.
    If you want to remove everything,  use oq reset.
    """
    if what == 'failed':
        purge_db(('failed', 'aborted'), '0 days', force)
        return
    elif what == 'orphan':
        purge_orphan(force)
        return
    elif what == 'old':
        purge_db((), days, force)
        return
    calc_id = int(what)
    if calc_id < 0:
        try:
            calc_id = logs.get_calc_ids(datadir)[calc_id]
        except IndexError:
            print('Calculation %d not found' % calc_id)
            return
    purge_one(calc_id, getpass.getuser(), force)


main.what = 'a calculation ID or the string "failed", "old" or "orphan"'
main.days = 'purge calculations older than days, if given'
main.force = 'really remove, otherwise just print a message'
