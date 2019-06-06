# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2019 GEM Foundation
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
import json
import requests
from openquake.baselib import sap, config
from openquake.hazardlib import valid


@sap.script
def submit(job_ini, hc=None):
    """Post a local file to the WebUI"""
    job_ini = os.path.abspath(job_ini)
    dic = dict(job_ini=job_ini, hazard_job_id=hc)
    # NB: there is no WebUI port in openquake.cfg for the moment
    resp = requests.post("%s/v1/calc/submit" % config.webapi.server, dic)
    print(json.loads(resp.text))


submit.arg('job_ini', 'calculation configuration file (or zip archive)')
submit.opt('hc', 'previous calculation ID', type=valid.hazard_id)
