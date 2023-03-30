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
import sys
import time
import logging
import getpass
import cProfile
from openquake.baselib import config, performance
from openquake.commonlib.logs import dbcmd
from openquake.calculators import views
from openquake.server import dbserver
from openquake.engine import engine
from openquake.engine.aelo import get_params_from


def engine_profile(jobctx, nrows):
    prof = cProfile.Profile()
    prof.runctx('engine.run_jobs([jobctx])', globals(), locals())
    pstat = 'calc_%d.pstat' % jobctx.calc_id
    prof.dump_stats(pstat)
    print('Saved profiling info in %s' % pstat)
    data = performance.get_pstats(pstat, nrows)
    print(views.text_table(data, ['ncalls', 'cumtime', 'path'],
                           ext='org'))


def from_file(fname, concurrent_jobs=8):
    """
    Run a PSHA analysis on the given sites
    """
    t0 = time.time()
    only_models = os.environ.get('OQ_ONLY_MODELS', '')
    exclude_models = os.environ.get('OQ_EXCLUDE_MODELS', '')
    only_siteids = os.environ.get('OQ_ONLY_SITEIDS', '')
    exclude_siteids = os.environ.get('OQ_EXCLUDE_SITEIDS', '')
    max_sites_per_model = int(os.environ.get('OQ_MAX_SITES_PER_MODEL', 1))
    allparams = []
    tags = []
    count_sites_per_model = {}
    with open(fname) as f:
        for line in f:
            siteid, lon, lat = line.split(',')
            if exclude_siteids and siteid in exclude_siteids.split(','):
                continue
            if only_siteids and siteid not in only_siteids.split(','):
                continue
            curr_model = siteid[:3]
            if exclude_models and curr_model in exclude_models:
                continue
            if only_models and curr_model not in only_models:
                continue
            try:
                count_sites_per_model[curr_model] += 1
            except KeyError:
                count_sites_per_model[curr_model] = 1
            if (max_sites_per_model > 0 and
                    count_sites_per_model[curr_model] > max_sites_per_model):
                continue
            dic = dict(siteid=siteid, lon=float(lon), lat=float(lat))
            tags.append(siteid)
            allparams.append(get_params_from(dic))

    logging.root.handlers = []
    logctxs = engine.create_jobs(allparams, config.distribution.log_level,
                                 None, getpass.getuser(), None)
    for logctx, tag in zip(logctxs, tags):
        logctx.tag = tag
    engine.run_jobs(logctxs, concurrent_jobs=concurrent_jobs)
    out = []
    count_errors = 0
    for logctx in logctxs:
        job = dbcmd('get_job', logctx.calc_id)
        tb = dbcmd('get_traceback', logctx.calc_id)
        out.append((job.id, job.description, tb[-1] if tb else ''))
        if tb:
            count_errors += 1

    header = ['job_id', 'description', 'error']
    print(views.text_table(out, header, ext='org'))
    dt = (time.time() - t0) / 60
    print('Total time: %.1f minutes' % dt)
    if count_errors:
        sys.exit(f'{count_errors} error(s) occurred')


def main(lonlat_or_fname, *, hc: int = None, slowest: int = None,
         concurrent_jobs: int = 8):
    """
    Run a PSHA analysis on the given lon, lat
    """
    dbserver.ensure_on()
    print(f'Concurrent jobs: {concurrent_jobs}')
    if not config.directory.mosaic_dir:
        sys.exit('mosaic_dir is not specified in openquake.cfg')

    if lonlat_or_fname.endswith('.csv'):
        from_file(lonlat_or_fname, concurrent_jobs)
        return
    lon, lat = lonlat_or_fname.split(',')
    params = get_params_from(dict(lon=lon, lat=lat))
    logging.root.handlers = []  # avoid breaking the logs
    [jobctx] = engine.create_jobs([params], config.distribution.log_level,
                                  None, getpass.getuser(), hc)
    if slowest:
        engine_profile(jobctx, slowest or 40)
    else:
        engine.run_jobs([jobctx], concurrent_jobs=concurrent_jobs)


main.lonlat_or_fname = 'lon,lat of the site to analyze or CSV file'
main.hc = 'previous calculation ID'
main.slowest = 'profile and show the slowest operations'
main.concurrent_jobs = 'maximum number of concurrent jobs'
