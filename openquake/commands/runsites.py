# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2023 GEM Foundation
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
from openquake.baselib import config
from openquake.commonlib.logs import dbcmd
from openquake.calculators.views import text_table
from openquake.engine.aelo import get_params_from
from openquake.engine import engine

def main(fname):
    """
    Run a PSHA analysis on the given sites
    """
    model = os.environ.get('OQ_MODEL', '')
    allparams = []
    tags =[]
    with open(fname) as f:
        for line in f:
            siteid, lon, lat = line.split(',')
            if model in siteid:
                dic = dict(siteid=siteid, lon=float(lon), lat=float(lat))
                tags.append('%(siteid)s(%(lon)s, %(lat)s)' % dic)
                allparams.append(get_params_from(dic))
    logging.root.handlers = []
    logctxs = engine.create_jobs(allparams, config.distribution.log_level,
                                 None, getpass.getuser(), None)
    for logctx, tag in zip(logctxs, tags):
        logctx.tag = tag
    engine.run_jobs(logctxs, concurrent_jobs=8)
    out = []
    for logctx in logctxs:
        job = dbcmd('get_job', logctx.calc_id)
        tb = dbcmd('get_traceback', logctx.calc_id)
        out.append((job.id, job.description, tb[-1] if tb else ''))

    header = ['job_id', 'description', 'error']
    print(text_table(out, header, ext='org'))

main.fname = 'CSV file with fields siteid, lon, lat'
