# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2018-2025 GEM Foundation
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
import pprint
import logging
from openquake.commonlib import logs, datastore
from openquake.calculators.extract import WebExtractor
from openquake.calculators.base import expose_outputs


def main(calc_id):
    """
    Import a remote calculation into the local database. Server, username
    and password must be specified in the openquake.cfg file.
    NB: calc_id can be a local pathname to a datastore not already
    present in the database: in that case it is imported in the db.
    """
    try:
        calc_id = int(calc_id)
    except ValueError:  # assume calc_id is a pathname
        remote = False
        calc_id =  datastore.extract_calc_id_datadir(calc_id)[0]
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
        pprint.pprint(dstore.get_attrs('/'))
        expose_outputs(dstore, status='complete')
    logging.info('Imported calculation %s successfully', calc_id)


main.calc_id = 'calculation ID or pathname ~/oqdata/calc_XXX.hdf5'
