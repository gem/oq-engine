#!/bin/env python
# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2026, GEM Foundation
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
from unittest.mock import patch
from openquake.baselib import sap, config
from openquake.qa_tests_data.mosaic import workflow
from openquake.engine import engine

def main(mosaic_dir, models='ALL', toml:bool=False, cache:str='false'):
    """
    Storing global SES
    """
    ghm_toml = workflow.ghm(mosaic_dir, models.split(','), toml)
    if toml:
        print(ghm_toml)
        return
    with patch.dict(config.directory, {'mosaic_dir': mosaic_dir}):
        calc_id = engine.run_workflow(ghm_toml, {'cache': cache})
    os.remove(ghm_toml)
    return calc_id

main.mosaic_dir = 'Directory containing the hazard mosaic'
main.models = 'Models to consider (comma-separated)'
main.cache = 'Use the cache to avoid repeating correct calculations'
main.toml = 'Just print the TOML code'

if __name__ == '__main__':
    sap.run(main)
