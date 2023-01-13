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

import sys
import pickle
import getpass
from openquake.baselib import config, sap
from openquake.hazardlib import valid
from openquake.engine import engine
from openquake.server import dbserver


def fake_run(lon, lat, vs30):
    # stub for the real calculation
    print(lon, lat, vs30)


def main(lon: valid.longitude,
         lat: valid.latitude,
         vs30: valid.positivefloat,
         siteid: valid.simple_id,
         pikfname='',
         ):
    """
    This script is meant to be called from the WebUI with pikfname.
    During debugging, however, it is useful to call it from the command line
    without specifying pikfname.
    """
    if pikfname:
        # use the job context and callback passed by the WebUI
        with open(pikfname, 'rb') as f:
            jobctx, callback = pickle.load(f)
    else:
        # create a new job context
        [jobctx] = engine.create_jobs(
            [dict(calculation_mode='custom', description='AELO for ' + siteid)],
        config.distribution.log_level, None, getpass.getuser(), None)

        # define a do-nothing callback
        def callback(job_id, exc=None):
            if exc:
                sys.exit('There was an error: %s' % exc)

    with jobctx:
        try:
            fake_run()
        except Exception as exc:
            callback(jobctx.calc_id, exc)
        else:
            callback(jobctx.calc_id)


if __name__ == '__main__':
    dbserver.ensure_on()
    sap.run(main)
