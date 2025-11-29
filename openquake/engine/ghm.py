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
from openquake.baselib import sap
from openquake.baselib.gitwrapper import git
from openquake.engine import engine

def read(manifest_toml):
    with open(manifest_toml, encoding='utf8') as f:
        manifest = toml.load(f)
    manifest['Global']['mosaic_dir'] = os.path.dirname(manifest_toml)
    return manifest


def checkout(manifest_toml):
    manifest = read(manifest_toml)
    glob = manifest['Global']
    inis = []
    t0 = time.time()
    for model, dic in manifest['Hazard'].items():
        repo = os.path.join(glob['mosaic_dir'], model)
        if 'oq-engine' not in repo:
            print(f'============================== {repo}')
            git(repo, ['clean', '-f'])
            git(repo, ['reset', '--hard', dic['checkout']])
        ini = dic.get('ini', 'job_vs30.ini')
        inis.append(os.path.join(repo, 'in', ini))
    dt = time.time() - t0
    print(f'Checked out the repositories in {dt:.0f} seconds')
    return inis


def run(manifest_toml, *, concurrent_jobs: int=1):
    manifest, inis = checkout(manifest_toml)
    ss = manifest['Global'].get('sample_sites')
    if ss:
        os.environ['OQ_SAMPLE_SITES'] = str(ss)
    jobs = engine.create_jobs(inis, tag=manifest['Global']['description'])
    engine.run_jobs(jobs, concurrent_jobs)


if __name__ == '__main__':
    sap.run(dict(checkout=checkout, run=run))
