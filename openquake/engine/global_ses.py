#!/bin/env python
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
"""This first version of the global_ses script, available from engine-3.22, is
able to generate the Global Stochastic Event Set for the entire world
from the GEM mosaic of hazard models. The workflow is a follows:

1. clone the mosaic repositories and set the right branch/commit on each repo
2. run this script with the right python, for instance on cole

$ /opt/openquake/venv/bin/python -m openquake.engine.global_ses

3. the script accepts five arguments:

- the directory where the mosaic is stored (i.e. /home/hazard/mosaic)
- the name of the generated output file (i.e. ruptures.hdf5);
- the number_of_logic_tree_samples
- the ses_per_logic_tree_path and
- minimum_magnitude

4. by default the script samples 2000 realizations with 50 SES per
   logic tree path, with an investigation time of 1, i.e. 100,000 years
   with a minimum magnitude of 5.  Such parameters are currently
   hard-coded by easily changeable in the script itself.

After the file ruptures.hdf5 has been generated, it can be used in
event based calculations by simply setting in the job.ini

rupture_model_file = ruptures.hdf5

The GMFs will then be generated starting from the global ruptures on the
sites specified in the job.ini file. Currently the sites can be specified
in a CSV with longitude and latitudes, or as a region in the job.ini.
The site parameters are inferreded from the site parameters in the mosaic
via an association with the closest site in the site model;
the GSIMs to use are also inferred from the GSIMs in the mosaic via an
association table (model, trt_smr) -> rlzs_by_gsim.

Note 1: the GLD model is excluded since it has no vs30 data.
Note 2: for JPN and KOR instead of using 50 ses x 1 year,
        we use 1 ses x 50 years, since the models require so.
Note 3: ruptures.hdf5 will contain a global site model with all the
        available site parameters merged together, with zeros for missing
        parameters (i.e. xvf will be zero for most models).

"""
import os
from openquake.baselib import sap
from openquake.commonlib import datastore
from openquake.engine import engine

MODELS = sorted('''
ALS AUS CEA EUR HAW KOR NEA PHL ARB IDN MEX NWA PNG SAM TWN
CND CHN IND MIE NZL SEA USA ZAF CCA JPN NAF PAC SSA WAF GLD
OAT OPA'''.split())

TOML = '''\
[global]
calculation_mode = "event_based"
ground_motion_fields = false
number_of_logic_tree_samples = {}
ses_per_logic_tree_path = {}
minimum_magnitude = {}

[success]
func = "openquake.engine.postjobs.build_ses"
out_file = "{}"
{}
'''

def main(mosaic_dir, out, *,
         number_of_logic_tree_samples:int=2000,
         ses_per_logic_tree_path:int=50, minimum_magnitude:float=5):
    """
    Storing global SES
    """
    inis = []
    calcs = []
    for model in MODELS:
        ini = os.path.join(mosaic_dir, model, 'in', 'job_vs30.ini')
        if os.path.exists(ini):
            calcs.append(f'\n[{model}]')
            calcs.append(f'ini = "{model}/in/job_vs30.ini"')
            if model in ("JPN", "KOR"):
                s = ses_per_logic_tree_path // 50  # investigation time
                calcs.append(f'ses_per_logic_tree_path={s}')
            inis.append(ini)

    ses_toml = os.path.join(mosaic_dir, 'ses.toml')
    with open(ses_toml, 'w') as f:
        f.write(TOML.format(number_of_logic_tree_samples,
                            ses_per_logic_tree_path,
                            minimum_magnitude,
                            out,
                            '\n'.join(calcs)))
    jobs = engine.run_toml([ses_toml], 'global SES')
    return [datastore.read(job.calc_id).filename for job in jobs]
                    
main.mosaic_dir = 'Directory containing the hazard mosaic'
main.out = 'Output file'
main.number_of_logic_tree_samples = 'Number of samples'
main.ses_per_logic_tree_path = 'Number of SES'
main.minimum_magnitude = 'Discard ruptures below this magnitude'

if __name__ == '__main__':
    sap.run(main)
