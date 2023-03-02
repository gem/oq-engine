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
from openquake.baselib import config
from openquake.hazardlib import valid
from openquake.engine import engine
from openquake.engine.postproc import disagg_by_rel_sources
from openquake.engine.aelo import get_params_from


def main(lon: valid.longitude, lat: valid.latitude):
    """
    Run a PSHA analysis on the given lon, lat
    """
    if not config.directory.mosaic_dir:
        sys.exit('mosaic_dir is not specified in openquake.cfg')

    params = get_params_from(dict(lon=lon, lat=lat))
    [jobctx] = engine.create_jobs([params], config.distribution.log_level,
                                  None, getpass.getuser(), None)
    with jobctx:
        engine.run_jobs([jobctx])
    #disagg_by_rel_sources.main(jobctx.calc_id)

main.lon = 'longitude of the site to analyze'
main.lat = 'latitude of the site to analyze'
