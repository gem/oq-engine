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
import pandas
from openquake.baselib import sap
from openquake.commonlib import datastore
from openquake.calculators.event_based import (
    starmap_from_rups, event_based)
from openquake.calculators.views import text_table


def main(calc_id: int, rup_id: int):
    """
    An utility to debug event based calculations
    $ python -m openquake.calculators.postproc.debug <calc_id>
    """
    dstore = datastore.read(calc_id)  # read the original calculation
    oq = dstore['oqparam']
    try:
        frups = dstore['filtered_ruptures'][:]
    except KeyError:
        frups = dstore['ruptures'][:]
    
    rups = frups[frups['id'] == rup_id]
    print('model =', rups[0]['model'].decode('ascii'))
    sites = dstore['sitecol']
    os.environ['OQ_RUPTURE'] = str(rup_id)
    dfs = []
    for res in starmap_from_rups(
            event_based, oq, rups[0], sites, None, (), dstore):
        dfs.append(pandas.DataFrame(res['gmfdata']))
    gmf_df = pandas.concat(dfs)
    print(text_table(gmf_df, ext='org'))


if __name__ == '__main__':
    sap.run(main)
