#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2019-2021 GEM Foundation
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
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.
import os
import getpass
import logging
from openquake.baselib import parallel
from openquake.commonlib import logs, datastore
from openquake.calculators.post_risk import PostRiskCalculator
from openquake.engine import engine


def main(calc_id: int, aggregate_by):
    """
    Re-run the postprocessing after an event based risk calculation
    """
    parent = datastore.read(calc_id)
    oqp = parent['oqparam']
    aggby = aggregate_by.split(',')
    for tagname in aggby:
        if tagname not in oqp.aggregate_by:
            raise ValueError('%r not in %s' % (tagname, oqp.aggregate_by))
    dic = dict(
        calculation_mode='reaggregate',
        description=oqp.description + '[aggregate_by=%s]' % aggregate_by,
        user_name=getpass.getuser(), is_running=1, status='executing',
        pid=os.getpid(), hazard_calculation_id=calc_id)
    log = logs.init('job', dic, logging.INFO)
    if os.environ.get('OQ_DISTRIBUTE') not in ('no', 'processpool'):
        os.environ['OQ_DISTRIBUTE'] = 'processpool'
    with log:
        oqp.hazard_calculation_id = parent.calc_id
        parallel.Starmap.init()
        prc = PostRiskCalculator(oqp, log.calc_id)
        prc.run(aggregate_by=aggby)
        engine.expose_outputs(prc.datastore)


main.calc_id = 'ID of the risk calculation'
main.aggregate_by = 'comma-separated list of tag names'
