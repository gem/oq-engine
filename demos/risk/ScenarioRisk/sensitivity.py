# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
# 
# Copyright (C) 2024, GEM Foundation
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
"""
A script to determine the sensitivity of the risk from the strike angle
"""
import os
from openquake.engine import engine


def path(name, cwd=os.path.dirname(__file__)):
    "From path relative to this directory to working path"
    return os.path.join(cwd, name)


base_ini = dict(
    description="scenario_risk with strike ",
    calculation_mode="scenario_risk",
    region="78.0 31.5, 89.5 31.5, 89.5 25.5, 78.0 25.5",
    inputs={'exposure': [path("exposure_model.xml")],
            'structural_vulnerability': path('structural_vulnerability_model.xml')},
    reference_vs30_value="760.0",
    reference_depth_to_1pt0km_per_sec='100.0',
    intensity_measure_types="PGA",
    truncation_level="0",
    maximum_distance="500",
    gsim="ChiouYoungs2008",
    number_of_ground_motion_fields="1")


def run_risk(strikes):
    "Run a scenario_risk calculation for each strike"
    inis = []
    for strike in strikes:
        ini = base_ini.copy()
        ini['description'] += str(strike)
        ini['rupture_dict'] = str({
            'lon': 80, 'lat': 30, 'dep': 10, 'mag': 6, 'rake': 0,
            'strike': strike, 'dip': 90})
        inis.append(ini)
    os.environ['OQ_DISTRIBUTE'] = 'zmq'  # run the jobs in parallel
    engine.run_jobs(engine.create_jobs(inis))


if __name__ == '__main__':
    run_risk(strikes=[0, 90, 180])
