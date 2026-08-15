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
# OpenQuake is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public
# License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

import pathlib
import shutil

from openquake.calculators import checkers
from openquake.commonlib import readinput


DEMO = (pathlib.Path(__file__).parents[3] / 'demos' / 'hazard' /
        'ScenarioCase1')


def test_check_ini_accepts_legacy_aliases(tmp_path):
    demo = tmp_path / DEMO.name
    shutil.copytree(DEMO, demo)

    checkers.check_ini(str(demo / 'job.ini'), hc=False)

    params = readinput.get_params(str(demo / 'job.tmp.ini'))
    assert 'spatial_correlation_model' in params
    assert 'spatial_correlation_params' in params
    assert 'ground_motion_correlation_model' not in params
    assert 'ground_motion_correlation_params' not in params
