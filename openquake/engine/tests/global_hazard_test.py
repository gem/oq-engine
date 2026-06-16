# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2024-2025, GEM Foundation
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
from openquake.qa_tests_data import mosaic
from openquake.commonlib.datastore import read
from openquake.calculators.export import export
from openquake.engine import global_hazard

MOSAIC_DIR = os.path.dirname(mosaic.__file__)


# TODO: enable the test
def _test():
    worflow_id = global_hazard.main(MOSAIC_DIR, 'job_vs30.ini')
    dstore = read(worflow_id)
    [fname] = export(('hmaps', 'csv'), dstore)
    breakpoint()
