# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2025 GEM Foundation
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
from openquake.baselib.gitwrapper import git
from openquake.engine import engine


def main(workflow_toml):
    """
    Check out the repositories listed in the checkout dictionary
    """
    for workflow in engine.read_many([workflow_toml]):
        for repo, tag in workflow.checkout.items():
            git(os.path.join(workflow.workflow_dir, repo), ['checkout', tag])

main.workflow_toml = "TOML file associated to a workflow"
