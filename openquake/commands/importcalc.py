# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2018-2020 GEM Foundation
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
import sys
import logging
from openquake.baselib import sap, datastore
from openquake.commonlib import logs
from openquake.calculators.extract import WebExtractor
from openquake.engine import engine
from openquake.server import dbserver


@sap.script
def importcalc(calc_id):
    """
    Import a remote calculation into the local database. server, username
    and password must be specified in an openquake.cfg file.
    NB: calc_id can be a local pathname to a datastore not already
    present in the database: in that case it is imported in the db.
    """
    dbserver.ensure_on()
    try:
        calc_id = int(calc_id)
    except ValueError:  # assume calc_id is a pathname
        remote = False
    else:
        remote = True
        job = logs.dbcmd('get_job', calc_id)
        if job is not None:
            sys.exit('There is already a job #%d in the local db' % calc_id)
    if remote:
        datadir = datastore.get_datadir()
        webex = WebExtractor(calc_id)
        hc_id = webex.oqparam.hazard_calculation_id
        if hc_id:
            sys.exit('The job has a parent (#%d) and cannot be '
                     'downloaded' % hc_id)
        webex.dump('%s/calc_%d.hdf5' % (datadir, calc_id))
        webex.close()
    with datastore.read(calc_id) as dstore:
        engine.expose_outputs(dstore, status='complete')
    logging.info('Imported calculation %s successfully', calc_id)


importcalc.arg('calc_id', 'calculation ID or pathname')
