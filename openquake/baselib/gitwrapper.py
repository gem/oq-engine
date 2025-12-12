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

import subprocess
from openquake.baselib import sap

def git(repodir, cmd):
    """
    A thin wrapper over git. It has plenty of limitations but it is
    enough for the purpose of fetching and checking out specific tags.
    """
    print(['git'] + cmd)
    #subprocess.run(['git'] + cmd, cwd=repodir)
git.repodir = 'git repository'
git.cmd = dict(help='git subcommand', nargs='+')

if __name__ == '__main__':
    sap.run(git)
