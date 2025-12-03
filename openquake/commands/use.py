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
import sys
import time
import toml
from openquake.baselib import sap
from openquake.baselib.gitwrapper import git
from openquake.commonlib import readinput
from openquake.engine import engine

def read(manifest_toml):
    """
    Read the manifest file and set 'mosaic_dir' and 'inis'
    """
    mosaic_dir = os.path.dirname(manifest_toml)
    with open(manifest_toml, encoding='utf8') as f:
        manifest = toml.load(f)
    gl = manifest['Global']
    inis = []
    for model, dic in manifest['Hazard'].items():
        repo = os.path.join(mosaic_dir, model)
        ini = dic.get('ini', 'job_vs30.ini')
        params = readinput.get_params(os.path.join(repo, 'in', ini))
        if n := dic.get('number_of_logic_tree_samples',
                        gl.get('number_of_logic_tree_samples')):
            params['number_of_logic_tree_samples'] = str(n)
        inis.append(params)
    manifest['mosaic_dir'] = mosaic_dir
    manifest['inis'] = inis
    return manifest


class Command:
    def __init__(self, manifest_toml):
        self.man = read(manifest_toml)

    def checkout(self):
        """
        Checkout the repositories listed in the manifest
        """
        t0 = time.time()
        # do not checkout folders in the oq-engine tree
        change = 'oq-engine' not in os.path.abspath(self.man['mosaic_dir'])
        for model, dic in self.man['Hazard'].items():
            repo = os.path.join(self.man['mosaic_dir'], model)
            if change:
                print(f"Setting {repo} at {dic['checkout']}")
                git(repo, ['clean', '-f'])
                git(repo, ['reset', '--hard', dic['checkout']])
        dt = time.time() - t0
        if change:
            print(f'Checked out the repositories in {dt:.0f} seconds')

    def run(self, *, concurrent_jobs: int=1):
        """
        Run the models listed in the manifest
        """
        gl = self.man['Global']
        if ss := gl.get('sample_sites'):
            os.environ['OQ_SAMPLE_SITES'] = str(ss)
        if ss := gl.get('sample_sources'):
            os.environ['OQ_SAMPLE_SOURCES'] = str(ss)
        if cm := gl.get('calculation_mode'):
            for ini in self.man['inis']:
                ini['calculation_mode'] = cm
        jobs = engine.create_jobs(self.man['inis'], tag=gl['description'])
        engine.run_jobs(jobs, concurrent_jobs)

    def help(self):
        """
        List the available subcommands
        """
        print(f'Available subcommands: {", ".join(sap.methdict(self))}')


def main(manifest, sub, arg):
    """
    Manager for multiple repositories and calculations based on a TOML
    configuration file (the manifest). You can get help with
    `oq use manifest.toml help`.
    """
    cmd = Command(sys.argv[2])
    sap.run(sap.methdict(cmd), sys.argv[3:])
main.manifest = 'Manifest file (.toml)'
main.sub = 'Name of a subcommand'
main.arg = dict(help='Argument of the subcommand (optional)', nargs='*')
