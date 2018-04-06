# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2018 GEM Foundation
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
import os
import sys
import logging
from openquake.baselib import sap, datastore, general
from openquake.commonlib import logs
from openquake.engine import engine
from openquake.server import dbserver
from requests import Session

CHUNKSIZE = 4*1024**2  # 4 MB


# NB: it is really difficult to test this automatically, so it is only
# tested manually
def login(host, username, password):
    session = Session()
    login_url = host + '/accounts/ajax_login/'
    session_resp = session.post(
        login_url, data={"username": username, "password": password},
        timeout=10)
    assert session_resp.status_code == 200, 'Login failed'
    return session


@sap.Script
def importcalc(host, calc_id, username, password):
    """
    Import a remote calculation into the local database
    """
    logging.basicConfig(level=logging.INFO)
    if '/' in host.split('//', 1)[1]:
        sys.exit('Wrong host ending with /%s' % host.rsplit('/', 1)[1])
    calc_url = '/'.join([host, 'v1/calc', str(calc_id)])
    dbserver.ensure_on()
    job = logs.dbcmd('get_job', calc_id)
    if job is not None:
        sys.exit('There is already a job #%d in the local db' % calc_id)

    datadir = datastore.get_datadir()
    session = login(host, username, password)
    status = session.get('%s/status' % calc_url)
    if 'Log in to an existing account' in status.text:
        sys.exit('Could not login')
    json = status.json()
    if json["parent_id"]:
        sys.exit('The job has a parent (#%(parent_id)d) and cannot be '
                 'downloaded' % json)
    resp = session.get('%s/datastore' % calc_url, stream=True)
    assert resp.status_code == 200, resp.status_code
    fname = '%s/calc_%d.hdf5' % (datadir, calc_id)
    down = 0
    with open(fname, 'wb') as f:
        logging.info('%s -> %s', calc_url, fname)
        for chunk in resp.iter_content(CHUNKSIZE):
            f.write(chunk)
            down += len(chunk)
            general.println('Downloaded {:,} bytes'.format(down))
    print()
    logs.dbcmd('import_job', calc_id, json['calculation_mode'],
               json['description'], json['owner'], json['status'],
               json['parent_id'], datadir)
    with datastore.read(calc_id) as dstore:
        engine.expose_outputs(dstore)
    logging.info('Imported calculation %d successfully', calc_id)

importcalc.arg('host', 'remote host (ex. https://oq1.wilson.openquake.org/)')
importcalc.arg('calc_id', 'calculation ID', type=int)
importcalc.arg('username', 'user name')
importcalc.arg('password', 'user password')
