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
import logging
import numpy
from openquake.baselib import performance, sap, hdf5
from openquake.hazardlib import gsim_lt
from openquake.commonlib import readinput, datastore
from openquake.calculators import base
from openquake.engine import engine


MODELS = sorted('''
ALS AUS CEA EUR HAW KOR NEA PHL ARB IDN MEX NWA PNG SAM TWN
CND CHN IND MIE NZL SEA USA ZAF CCA JPN NAF PAC SSA WAF GLD
'''.split())

dt = [('model', '<S3'), ('trt', '<S61'), ('gsim', hdf5.vstr), ('weight', float)]


def read_job_inis(mosaic_dir, INPUTS):
    out = []
    rows = []
    for model in INPUTS.pop('models'):
        fname = os.path.join(mosaic_dir, model, 'in', 'job_vs30.ini')
        dic = readinput.get_params(fname)
        del dic['intensity_measure_types_and_levels']
        dic.update(INPUTS)
        if 'truncation_level' not in dic:  # CAN
            dic['truncation_level'] = '5'
        if model in ("KOR", "JPN"):
            dic['investigation_time'] = '50'
            dic['ses_per_logic_tree_path'] = str(
                int(dic['ses_per_logic_tree_path']) // 50)
        dic['mosaic_model'] = model
        gslt = gsim_lt.GsimLogicTree(dic['inputs']['gsim_logic_tree'])
        for trt, gsims in gslt.values.items():
            for gsim in gsims:
                q = (model, trt, gsim._toml, gsim.weight['default'])
                rows.append(q)
        out.append(dic)
    return out, rows


def main(mosaic_dir, out, models='ALL', *,
         number_of_logic_tree_samples:int=2000,
         ses_per_logic_tree_path:int=50, minimum_magnitude:float=5):
    """
    Storing global SES
    """
    if models == 'ALL':
        models = MODELS
    else:
        models = models.split(',')
        for model in models:
            assert model in MODELS, model
    if 'KOR' in models or 'JPN' in models:
        if ses_per_logic_tree_path % 50:
            raise SystemExit("ses_per_logic_tree_path must be divisible by 50!")
    INPUTS = dict(
        calculation_mode='event_based',
        number_of_logic_tree_samples= str(number_of_logic_tree_samples),
        ses_per_logic_tree_path = str(ses_per_logic_tree_path),
        investigation_time='1',
        ground_motion_fields='false',
        models=models)
    if minimum_magnitude:
        INPUTS['minimum_magnitude'] = str(minimum_magnitude)
    job_inis, rows = read_job_inis(mosaic_dir, INPUTS)
    with performance.Monitor(measuremem=True) as mon:
        with hdf5.File(out, 'w') as h5:
            h5['models'] = models
            h5['model_trt_gsim_weight'] = numpy.array(rows, dt)
        jobs = engine.run_jobs(
            engine.create_jobs(job_inis, log_level=logging.WARN))
        fnames = [datastore.read(job.calc_id).filename for job in jobs]
        logging.warning(f'Saving {out}')
        with hdf5.File(out, 'a') as h5:
            base.import_sites_hdf5(h5, fnames)
            base.import_ruptures_hdf5(h5, fnames)
            h5['/'].attrs.update(INPUTS)
    print(mon)
    return fnames

main.mosaic_dir = 'Directory containing the hazard mosaic'
main.out = 'Output file'
main.models = 'Models to consider (comma-separated)'
main.number_of_logic_tree_samples = 'Number of samples'
main.ses_per_logic_tree_path = 'Number of SES'
main.minimum_magnitude = 'Discard ruptures below this magnitude'

if __name__ == '__main__':
    sap.run(main)
