# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
# 
# Copyright (C) 2025, GEM Foundation
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
import time
import toml
from openquake.baselib import sap, config
from openquake.baselib.gitwrapper import git
from openquake.engine import engine

def path_to(model):
    return os.path.join(config.directory.mosaic_dir, model)


def main(manifest_toml):
    with open(manifest_toml, encoding='utf8') as f:
        manifest = toml.load(f)
    inis = []
    t0 = time.time()
    for model, dic in manifest['Hazard'].items():
        repo = path_to(model)
        print(f'============================== {repo}')
        git(repo, ['clean', '-f'])
        git(repo, ['reset', '--hard', dic['checkout']])
        inis.append(os.path.join(repo, 'in', 'job_vs30.ini'))
    dt = time.time() - t0
    print(f'Checked out the repositories in {dt:.0f} seconds')
    os.environ['OQ_SAMPLE_SITES'] = '.04'
    jobs = engine.create_jobs(inis, tag=manifest['Global']['description'])
    engine.run_jobs(jobs, concurrent_jobs=1)

if __name__ == '__main__':
    sap.run(main)
