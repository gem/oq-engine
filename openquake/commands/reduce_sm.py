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
import os
import logging
from openquake.baselib import sap, performance, general
from openquake.commonlib import readinput, util


def get_dupl(src_ids):
    dupl = set()
    for src_id in src_ids:
        if ';' in src_id:
            dupl.add(src_id.split(';')[0])
    return dupl


@sap.script
def reduce_sm(calc_id):
    """
    Reduce the source model of the given (pre)calculation by discarding all
    sources that do not contribute to the hazard.
    """
    if os.environ.get('OQ_DISTRIBUTE') not in ('no', 'processpool'):
        os.environ['OQ_DISTRIBUTE'] = 'processpool'
    with util.read(calc_id) as dstore:
        oqparam = dstore['oqparam']
        info = dstore['source_info'][()]
    src_ids = info['source_id']
    num_ids = len(src_ids)
    bad_ids = info[info['eff_ruptures'] == 0]['source_id']
    logging.info('Found %d far away sources', len(bad_ids))
    bad_ids = set(src_id.split(';')[0] for src_id in bad_ids)
    bad_dupl = bad_ids & get_dupl(src_ids)
    if bad_dupl:
        logging.info('Duplicates %s not removed' % bad_dupl)
    ok = info['eff_ruptures'] > 0
    if ok.sum() == 0:
        raise RuntimeError('All sources were filtered away!')
    ok_ids = general.group_array(info[ok][['source_id', 'code']], 'source_id')
    with performance.Monitor() as mon:
        good, total = readinput.reduce_source_model(
            oqparam.inputs['source_model_logic_tree'], ok_ids)
    logging.info('Removed %d/%d sources', total - good, num_ids)
    print(mon)


reduce_sm.arg('calc_id', 'calculation ID', type=int)
