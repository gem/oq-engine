#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2018, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
import sys
#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2018, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
import logging
from openquake.baselib import sap, datastore
from openquake.commonlib import logs
from openquake.engine import engine
from openquake.server import dbserver
from requests import Session


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
def importcalc(calc_url, username, password):
    """
    Import a remote calculation into the local database
    """
    logging.basicConfig(level=logging.INFO)
    assert '/v1/calc' in calc_url, calc_url
    assert not calc_url.endswith('/')
    # for instance https://oq1.wilson.openquake.org/v1/calc/17740
    prefix, calc_id = calc_url.rsplit('/', 1)
    host = prefix[:-8]  # strip /v1/calc
    calc_id = int(calc_id)
    dbserver.ensure_on()
    job = logs.dbcmd('get_job', calc_id)
    if job is not None:
        sys.exit('There is already a job #%d in the local db' % calc_id)

    datadir = datastore.get_datadir()
    session = login(host, username, password)
    json = session.get('%s/status' % calc_url).json()
    resp = session.get('%s/datastore' % calc_url, stream=True)
    assert resp.status_code == 200, resp.status_code
    fname = '%s/calc_%d.hdf5' % (datadir, calc_id)
    with open(fname, 'wb') as f:
        logging.info('%s -> %s', calc_url, fname)
        for chunk in resp:
            f.write(chunk)
    logs.dbcmd('import_job', calc_id, json['calculation_mode'],
               json['description'], json['owner'], json['status'], datadir)
    with datastore.read(calc_id) as dstore:
        engine.expose_outputs(dstore)
    logging.info('Imported calculation %d successfully', calc_id)

importcalc.arg('calc_url', 'calculation URL')
importcalc.arg('username', 'user name')
importcalc.arg('password', 'user password')
