# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2023, GEM Foundation
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
"""
Master script for running an AELO analysis
"""
import os
import sys
import getpass
from openquake.baselib import config, sap
from openquake.hazardlib import valid
from openquake.commonlib import readinput
from openquake.engine import engine
from openquake.server import dbserver


def get_params_from(lon, lat, vs30, siteid):
    """
    Build the job.ini parameters for the given lon, lat extracting them
    from the mosaic files.
    """
    model = 'GLD'    # TODO: change to model = get_model_from(lon, lat)
    ini = os.path.join(config.directory.mosaic_dir, model, 'in', 'job.ini')
    params = readinput.get_params(ini)
    params['description'] = 'AELO for ' + siteid
    params['reference_vs30_value'] = str(vs30)
    params['sites'] = '%s %s' % (lon, lat)
    del params['inputs']['sites']
    # TODO: add disaggregation parameters
    return params


def fake_run(jobctx, lon, lat, vs30):
    # stub for the real calculation
    print(jobctx.get_oqparam(), lon, lat, vs30)


def trivial_callback(job_id, exc=None):
    if exc:
        sys.exit('There was an error: %s' % exc)


def main(lon: valid.longitude,
         lat: valid.latitude,
         vs30: valid.positivefloat,
         siteid: valid.simple_id,
         jobctx=None,
         callback=trivial_callback,
         ):
    """
    This script is meant to be called from the WebUI.
    """
    if jobctx is None:
        # create a new job context
        dic = dict(calculation_mode='custom', description='AELO')
        [jobctx] = engine.create_jobs([dic], config.distribution.log_level,
                                      None, getpass.getuser(), None)
    with jobctx:
        jobctx.params.update(get_params_from(lon, lat, vs30, siteid))
        try:
            fake_run(jobctx, lon, lat, vs30)
        except Exception as exc:
            callback(jobctx.calc_id, exc)
        else:
            callback(jobctx.calc_id)


if __name__ == '__main__':
    dbserver.ensure_on()
    sap.run(main)
