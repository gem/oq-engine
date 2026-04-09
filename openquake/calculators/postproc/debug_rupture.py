# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
# 
# Copyright (C) 2026, GEM Foundation
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
import logging
from unittest.mock import patch
import numpy
import pandas
from openquake.baselib import sap
from openquake.commonlib import datastore
from openquake.calculators.base import save_version_checksum
from openquake.calculators.event_based import (
    starmap_from_rups, event_based)


# tested in event_based test_case_2
def main(calc_id: int, rup_id: str):
    """
    An utility to debug event based calculations
    $ python -m openquake.calculators.postproc.debug <calc_id> <rup1>,<rup2>
    """
    rup_ids = numpy.uint32(rup_id.split(','))
    parent = datastore.read(calc_id)
    oq = parent['oqparam']
    try:
        frups = parent['filtered_ruptures'][:]
    except KeyError:
        frups = parent['ruptures'][:]
    rups = frups[numpy.isin(frups['id'], rup_ids)]
    logging.info('model = %s', rups[0]['model'].decode('ascii'))

    sites = parent['sitecol']
    job, dstore = datastore.create_job_dstore(f'GMFs for {rup_id=}', parent)
    with job, patch.dict(os.environ, {'OQ_RUPTURE': rup_id}):
        dfs = []
        sig_eps = []
        for res in starmap_from_rups(
                event_based, oq, rups[0], sites, None, (), dstore):
            dfs.append(pandas.DataFrame(res['gmfdata']))
            sig_eps.append(res['sig_eps'])
        gmf_df = pandas.concat(dfs)
        dstore.create_dset('gmf_data/sigma_epsilon', numpy.concatenate(sig_eps))
        dstore.create_df('gmf_data', gmf_df)
        dstore['sitecol'] = sites
        save_version_checksum(oq, dstore)
        logging.info(f'Created {dstore.filename}')
    return dstore

main.calc_id = 'Calculation ID'
main.rup_id = 'Comma-separated rupture IDs'

if __name__ == '__main__':
    sap.run(main)
