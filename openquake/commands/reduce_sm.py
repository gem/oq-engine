#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2018-2019 GEM Foundation
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
from openquake.baselib import sap, datastore, performance
from openquake.commonlib import readinput


@sap.script
def reduce_sm(calc_id):
    """
    Reduce the source model of the given (pre)calculation by discarding all
    sources that do not contribute to the hazard.
    """
    with datastore.read(calc_id) as dstore:
        oqparam = dstore['oqparam']
        info = dstore['source_info'].value
        ok = info['weight'] > 0
        source_ids = set(info[ok]['source_id'])
    with performance.Monitor() as mon:
        readinput.reduce_source_model(
            oqparam.inputs['source_model_logic_tree'], source_ids)
    print(mon)


reduce_sm.arg('calc_id', 'calculation ID', type=int)
