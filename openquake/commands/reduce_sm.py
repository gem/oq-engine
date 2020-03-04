#!/usr/bin/env python3
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
import logging
import numpy as np
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
        info = dstore['source_info'][()]
        source_ids, source_counts = np.unique(
            info['source_id'], return_counts=True)
        duplicate_source_ids = np.array([
            item for item in zip(source_ids, source_counts) if item[1] > 1])
        if duplicate_source_ids:
            logging.warning(
                'Duplicate source ids were found and they will not be removed:'
                ' %s', duplicate_source_ids)
        ok = info['eff_ruptures'] > 0
        source_ids = set(info[ok]['source_id'])
    if ok.sum() == 0:
        raise RuntimeError('All sources were filtered away!')
    with performance.Monitor() as mon:
        readinput.reduce_source_model(
            oqparam.inputs['source_model_logic_tree'], source_ids)
    print(mon)


reduce_sm.arg('calc_id', 'calculation ID', type=int)
