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

import sys
import getpass
import cProfile
from openquake.baselib import config, performance
from openquake.hazardlib import valid
from openquake.calculators import views
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


def main(lon: valid.longitude, lat: valid.latitude, *,
         hc: int=None, slowest: int=None):
    """
    Run a PSHA analysis on the given lon, lat
    """
    if not config.directory.mosaic_dir:
        sys.exit('mosaic_dir is not specified in openquake.cfg')

    params = get_params_from(dict(lon=lon, lat=lat))
    [jobctx] = engine.create_jobs([params], config.distribution.log_level,
                                  None, getpass.getuser(), hc)
    with jobctx:
        if slowest:
            engine_profile(jobctx, slowest or 40)
        else:
            engine.run_jobs([jobctx])

main.lon = 'longitude of the site to analyze'
main.lat = 'latitude of the site to analyze'
main.hc = 'previous calculation ID'
main.slowest = 'profile and show the slowest operations'
