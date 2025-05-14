#!/usr/bin/env python3
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
import os
import logging
from openquake.baselib import performance, general, python3compat
from openquake.commonlib import readinput, datastore


def get_dupl(src_ids):
    dupl = set()
    for src_id in src_ids:
        if ';' in src_id:
            dupl.add(src_id.split(';')[0])
    return dupl


def main(calc_id: int):
    """
    Reduce the source model of the given (pre)calculation by discarding all
    sources that do not contribute to the hazard.
    """
    if os.environ.get('OQ_DISTRIBUTE') not in ('no', 'processpool'):
        os.environ['OQ_DISTRIBUTE'] = 'processpool'
    with datastore.read(calc_id) as dstore:
        oqparam = dstore['oqparam']
        info = dstore['source_info'][:]
    if oqparam.ps_grid_spacing:
        raise RuntimeError(
            'The source model cannot be reduced since ps_grid_spacing was used '
            'in the precalculation')
    info = info[info['num_sites'] > 0]  # reduce to sources affecting sites
    src_ids = info['source_id']
    num_ids = len(src_ids)
    bad_dupl = get_dupl(python3compat.decode(src_ids))
    if bad_dupl:
        logging.info('Duplicates %s not removed' % bad_dupl)
    ok_ids = general.group_array(info[['source_id', 'code']], 'source_id')
    with performance.Monitor() as mon:
        if 'source_model_logic_tree' in oqparam.inputs:
            good, total = readinput.reduce_source_model(
                oqparam.inputs['source_model_logic_tree'], ok_ids)
        else:
            sms = [oqparam.inputs['source_model']]
            [dic] = readinput.reduce_sm(sms, sorted(ok_ids))
            good, total = dic['good'], dic['total']
    logging.info('Removed %d/%d sources', total - good, num_ids)
    print(mon)


main.calc_id = 'calculation ID'
