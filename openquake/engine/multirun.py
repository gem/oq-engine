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

import os
import sys
import time
from openquake.baselib import sap
from openquake.commonlib.readinput import get_params
from openquake.engine.engine import create_jobs, run_jobs


# for instance, to run the demos in parallel:
# python -m openquake.engine.multirun demos/hazard
def main(dirname, job_ini='job.ini', concurrent=0, **kw):
    assert os.path.exists(dirname), dirname
    inis = []
    for cwd, dirs, files in os.walk(dirname):
        for f in files:
            if f == job_ini:
                inis.append(os.path.join(cwd, f))
    if not inis:
        sys.exit('No %s files found' % job_ini)

    inis.sort()
    print('running ' + ' '.join(inis))
    inis = [get_params(ini, kw) for ini in inis]
    t0 = time.time()
    if concurrent:  # in parallel
        ctxs = run_jobs(create_jobs(inis), concurrent)
        out = [(ctx.calc_id, ini) for ctx, ini in zip(ctxs, inis)]
    else:  # sequentially
        out = []
        for ini in inis:
            [ctx] = run_jobs(create_jobs([ini]))
            out.append((ctx.calc_id, ini))
    dt = time.time() - t0
    print('Total time: %.1f minutes' % (dt/60))
    return out


if __name__ == '__main__':
    sap.run(main)
