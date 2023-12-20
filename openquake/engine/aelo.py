# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2023, GEM Foundation
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
Master script for running an AELO analysis
"""
import os
import sys
import getpass
import logging
from openquake.baselib import config, sap
from openquake.hazardlib import valid
from openquake.commonlib import readinput, global_model_getter
from openquake.engine import engine

CDIR = os.path.dirname(__file__)  # openquake/engine

IMTLS = '''\
{"PGA": logscale(0.005, 3.00, 25),
 "SA(0.2)": logscale(0.005, 9.00, 25),
 "SA(1.0)": logscale(0.005, 3.60, 25)}
'''

PRELIMINARY_MODELS = ['CEA', 'CHN', 'NEA']
PRELIMINARY_MODEL_WARNING = (
    'Results are preliminary. The seismic hazard model used for the site'
    ' is under review and will be updated' ' during Year 3.')


def get_params_from(inputs, mosaic_dir=config.directory.mosaic_dir):
    """
    :param inputs: a dictionary with lon, lat, vs30, siteid

    Build the job.ini parameters for the given lon, lat extracting them
    from the mosaic files.
    """
    getter = global_model_getter.GlobalModelGetter()
    model = getter.get_model_by_lon_lat(inputs['lon'], inputs['lat'])
    ini = os.path.join(mosaic_dir, model, 'in', 'job_vs30.ini')
    params = readinput.get_params(ini)
    params['model'] = model
    if 'siteid' in inputs:
        params['description'] = 'AELO for ' + inputs['siteid']
    else:
        params['description'] += ' (%(lon)s, %(lat)s)' % inputs
    params['ps_grid_spacing'] = '0.'  # required for disagg_by_src
    params['pointsource_distance'] = '100.'
    params['intensity_measure_types_and_levels'] = IMTLS
    params['truncation_level'] = '3.'
    params['disagg_by_src'] = 'true'
    params['uniform_hazard_spectra'] = 'true'
    params['use_rates'] = 'true'
    params['sites'] = '%(lon)s %(lat)s' % inputs
    if 'vs30' in inputs:
        params['override_vs30'] = '%(vs30)s' % inputs
    params['distance_bin_width'] = '20'
    params['num_epsilon_bins'] = '10'
    params['mag_bin_width'] = '0.1'
    params['epsilon_star'] = 'true'
    params['postproc_func'] = 'compute_rtgm.main'
    if float(params['investigation_time']) == 1:
        params['poes'] = '0.000404 0.001025 0.002105 0.004453 0.013767'
    elif float(params['investigation_time']) == 50:
        params['poes'] = '0.02 0.05 0.10 0.20 0.50'
    else:
        raise ValueError('Invalid investigation time %(investigation_time)s'
                         % params)

    # params['cachedir'] = datastore.get_datadir()
    return params


def trivial_callback(
        job_id, job_owner_email, outputs_uri, inputs, exc=None, warnings=None):
    if exc:
        sys.exit('There was an error: %s' % exc)
    print('Finished job %d correctly' % job_id)


def main(lon: valid.longitude,
         lat: valid.latitude,
         vs30: valid.positivefloat,
         siteid: valid.simple_id,
         job_owner_email=None,
         outputs_uri=None,
         jobctx=None,
         callback=trivial_callback,
         ):
    """
    This script is meant to be called from the WebUI in production mode,
    and from the command-line in testing mode.
    """
    inputs = dict(lon=lon, lat=lat, vs30=vs30, siteid=siteid)
    if jobctx is None:
        # in  testing mode create a new job context
        config.directory.mosaic_dir = os.path.join(
            os.path.dirname(CDIR), 'qa_tests_data/mosaic')
        dic = dict(calculation_mode='custom', description='AELO')
        [jobctx] = engine.create_jobs([dic], config.distribution.log_level,
                                      None, getpass.getuser(), None)

    if not config.directory.mosaic_dir:
        sys.exit('mosaic_dir is not specified in openquake.cfg')
    warnings = []
    try:
        jobctx.params.update(get_params_from(inputs))
        if jobctx.params['model'] in PRELIMINARY_MODELS:
            warnings.append(PRELIMINARY_MODEL_WARNING)
        logging.root.handlers = []  # avoid breaking the logs
    except Exception as exc:
        # This can happen for instance:
        # - if no model covers the given coordinates.
        # - if no ini file was found
        callback(jobctx.calc_id, job_owner_email, outputs_uri, inputs,
                 exc=exc, warnings=warnings)
        raise exc
    try:
        engine.run_jobs([jobctx])
    except Exception as exc:
        callback(jobctx.calc_id, job_owner_email, outputs_uri, inputs,
                 exc=exc, warnings=warnings)
    else:
        callback(jobctx.calc_id, job_owner_email, outputs_uri, inputs,
                 exc=None, warnings=warnings)


if __name__ == '__main__':
    sap.run(main)
