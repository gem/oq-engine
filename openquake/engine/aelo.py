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
import functools
from openquake.baselib import config, sap
from openquake.hazardlib import valid, geo
from openquake.commonlib import readinput, oqvalidation
from openquake.engine import engine
from openquake.qa_tests_data import mosaic

CDIR = os.path.dirname(__file__)  # openquake/engine
PRELIMINARY_MODELS = []
PRELIMINARY_MODEL_WARNING_MSG = (
    'Results are preliminary. The seismic hazard model used for the site'
    ' is under review and will be updated' ' during Year 3.')


def get_boundaries_file(mosaic_dir, other_dir):
    """
    Search the passed mosaic_dir and then qa_tests_data/mosaic
    for ModelBoundaries.gpkg|shp
    """
    fname = config.directory.mosaic_boundaries_file
    if fname:
        assert os.path.exists(fname), fname
        return fname
    for mdir in (mosaic_dir, other_dir):
        fname = os.path.join(mdir, 'ModelBoundaries.gpkg')
        if os.path.exists(fname):
            return fname
        fname = os.path.join(mdir, 'ModelBoundaries.shp')
        if os.path.exists(fname):
            return fname
    raise FileNotFoundError('ModelBoundaries')


@functools.lru_cache
def get_mosaic_df(buffer, mosaic_dir=config.directory.mosaic_dir):
    """
    :returns: a DataFrame with the mosaic geometries used in AELO
    """
    path = get_boundaries_file(mosaic_dir, os.path.dirname(mosaic.__file__))
    logging.info(f'Reading {path}')
    df = readinput.read_geometries(path, 'name', buffer)
    return df


def get_params_from(inputs, mosaic_dir, exclude=(), ini=None):
    """
    :param inputs:
        a dictionary with sites, vs30, siteid, asce_version, site_class
    :param mosaic_dir:
        directory where the mosaic is located
    :param ini:
        path of the job ini file (if specified, mosaic_dir will be ignored)

    Build the job.ini parameters for the given lon, lat by extracting them
    from the mosaic files.
    """
    mosaic_df = get_mosaic_df(buffer=0)
    lonlats = valid.coordinates(inputs['sites'])
    models = geo.utils.geolocate(lonlats, mosaic_df, exclude)
    if len(set(models)) > 1:
        raise ValueError("The sites must all belong to the same model, got %s"
                         % set(models))
    lon, lat, _dep = lonlats[0]
    if models[0] == '???':
        raise ValueError(
            f'Site at lon={lon} lat={lat} is not covered by any model!')
    if ini is None:
        ini = os.path.join(mosaic_dir, models[0], 'in', 'job_vs30.ini')
    params = readinput.get_params(ini)
    params['mosaic_model'] = models[0]
    if 'siteid' in inputs:
        params['description'] = 'AELO for ' + inputs['siteid']
    else:
        # in aelo_test.py
        params['description'] += f' ({lon}, {lat})'
    params['ps_grid_spacing'] = '0.'  # required for disagg_by_src
    params['pointsource_distance'] = '100.'
    params['truncation_level'] = '3.'
    params['disagg_by_src'] = 'true'
    params['uniform_hazard_spectra'] = 'true'
    params['use_rates'] = 'true'
    params['sites'] = inputs['sites']
    params['max_sites_disagg'] = len(lonlats)
    if 'vs30' in inputs:
        if inputs['vs30']:
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
    params['export_dir'] = ''
    params['asce_version'] = inputs.get(
        'asce_version', oqvalidation.OqParam.asce_version.default)
    if params['asce_version'] == 'ASCE7-16':
        params['intensity_measure_types_and_levels'] = (
            '{"PGA": logscale(0.005, 3.00, 25),'
            ' "SA(0.2)": logscale(0.005, 9.00, 25),'
            ' "SA(1.0)": logscale(0.005, 3.00, 25)}')
    params['site_class'] = inputs.get(
        'site_class', oqvalidation.OqParam.site_class.default)
    return params


def trivial_callback(
        job_id, job_owner_email, outputs_uri, inputs, exc=None, warnings=None):
    if exc:
        sys.exit('There was an error: %s' % exc)
    print('Finished job %d correctly' % job_id)


def main(lon: valid.longitude,
         lat: valid.latitude,
         vs30: valid.positivefloat,
         siteid: str,
         asce_version: str,
         site_class: str,
         job_owner_email=None,
         outputs_uri=None,
         jobctx=None,
         callback=trivial_callback,
         ):
    """
    This script is meant to be called from the WebUI in production mode,
    and from the command-line in testing mode.
    """
    oqvalidation.OqParam.asce_version.validator(asce_version)
    oqvalidation.OqParam.site_class.validator(site_class)
    inputs = dict(sites='%s %s' % (lon, lat), vs30=vs30, siteid=siteid,
                  asce_version=asce_version, site_class=site_class)
    warnings = []
    if jobctx is None:
        # in  testing mode create a new job context
        config.directory.mosaic_dir = os.path.join(
            os.path.dirname(CDIR), 'qa_tests_data/mosaic')
        dic = dict(calculation_mode='custom', description='AELO')
        [jobctx] = engine.create_jobs([dic], config.distribution.log_level,
                                      None, getpass.getuser(), None)
    else:
        # in production mode update jobctx.params
        try:
            jobctx.params.update(get_params_from(
                inputs, config.directory.mosaic_dir, exclude=['USA']))
        except Exception as exc:
            # This can happen for instance:
            # - if no model covers the given coordinates.
            # - if no ini file was found
            callback(jobctx.calc_id, job_owner_email, outputs_uri, inputs,
                     exc=exc, warnings=warnings)
            raise exc

    if jobctx.params['mosaic_model'] in PRELIMINARY_MODELS:
        warnings.append(PRELIMINARY_MODEL_WARNING_MSG)
    logging.root.handlers = []  # avoid breaking the logs
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
