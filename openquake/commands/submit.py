# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2024 GEM Foundation
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

from openquake.baselib import config
from openquake.commonlib import readinput

script = '''#!/bin/bash
job_id=(`oq create_jobs %(n)d`)
%(lines)s
time oq collect_jobs ${job_id[@]}
'''

def main(n: int, job_ini):
    """
    Print a bash script generating many calculations
    """
    descr = readinput.get_params(job_ini)['description']
    lines = []
    for i in range(n):
        spec = '[%d,%d]' % (i+1, n) 
        params = "tile_spec='%s' description=\"%s%s\" job_id=${job_id[%d]}" % (
            spec, descr, spec, i)
        lines.append(config.distribution.submit_cmd + f" {job_ini} -p {params}")
    print(script % dict(n=len(lines), lines='\n'.join(lines)))

main.n = dict(help='number of jobs to generate')
main.job_ini = dict(help='path to .ini file')
