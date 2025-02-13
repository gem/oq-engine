# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2023-2025 GEM Foundation
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
import sys
import time
import logging
import getpass
import cProfile
import numpy
import pandas
import collections
from openquake.baselib import config, performance
from openquake.qa_tests_data import mosaic
from openquake.commonlib import readinput, logs, datastore, oqvalidation
from openquake.calculators import views
from openquake.engine import engine
from openquake.engine.impact import main_cmd
from openquake.engine.aelo import get_params_from, get_mosaic_df
from openquake.hazardlib.geo.utils import geolocate

FAMOUS = os.path.join(os.path.dirname(mosaic.__file__), 'famous_ruptures.csv')


def engine_profile(jobctx, nrows):
    prof = cProfile.Profile()
    prof.runctx('engine.run_jobs([jobctx])', globals(), locals())
    pstat = 'calc_%d.pstat' % jobctx.calc_id
    prof.dump_stats(pstat)
    print('Saved profiling info in %s' % pstat)
    data = performance.get_pstats(pstat, nrows)
    print(views.text_table(data, ['ncalls', 'cumtime', 'path'],
                           ext='org'))

# ########################## run_site ############################## #


# NB: this is called by the action mosaic/.gitlab-ci.yml
def from_file(fname, mosaic_dir, concurrent_jobs):
    """
    Run an AELO analysis on the given sites and returns an array with
    the ASCE-41 parameters.

    The CSV file must contain in each row a site identifier
    starting with the 3-character code of the mosaic model that covers it, and
    the longitude and latitude of the site, separated by commas.

    It may be convenient also to define environment variables to select or
    exclude subsets of sites from those specified in the CSV file:

    * `OQ_ONLY_MODELS`: a comma-separated list of mosaic models (each
      identified by the corresponding 3-characters code) to be selected,
      excluding sites covered by other models
    * `OQ_EXCLUDE_MODELS`: same as above, but selecting sites covered by
      all models except those specified in this list

    For instance::

      $ OQ_ONLY_MODELS=CAN,AUS oq mosaic run_site sites.csv

    would select from the file `sites.csv` only those for which the site id
    starts with the codes `CAN` or `AUS`, i.e. those covered by the mosaic
    models for Canada and Australia.
    """
    t0 = time.time()
    only_models = os.environ.get('OQ_ONLY_MODELS', '')
    exclude_models = os.environ.get('OQ_EXCLUDE_MODELS', '')
    allparams = []
    ids = {}
    sites_df = pandas.read_csv(fname)  # header ID,Latitude,Longitude
    lonlats = sites_df[['Longitude', 'Latitude']].to_numpy()
    print('Found %d sites' % len(lonlats))
    mosaic_df = get_mosaic_df(buffer=.1)
    sites_df['model'] = geolocate(lonlats, mosaic_df)
    count_sites_per_model = collections.Counter(sites_df.model)
    print(count_sites_per_model)
    for model, df in sites_df.groupby('model'):
        if model in ('???', 'USA', 'GLD'):
            continue
        if exclude_models and model in exclude_models.split(','):
            continue
        if only_models and model not in only_models.split(','):
            continue

        df = df.sort_values(['Longitude', 'Latitude'])
        ids[model] = df.ID.to_numpy()
        sites = ','.join('%s %s' % tuple(lonlat)
                         for lonlat in lonlats[df.index])
        dic = dict(siteid=model + str(ids[model]), sites=sites)
        allparams.append(get_params_from(dic, mosaic_dir))

    logging.root.handlers = []  # avoid too much logging
    loglevel = 'warn' if len(allparams) > 9 else config.distribution.log_level
    logctxs = engine.create_jobs(
        allparams, loglevel, None, getpass.getuser(), None)
    engine.run_jobs(logctxs, concurrent_jobs=concurrent_jobs)
    out = []
    count_errors = 0
    a07s, a41s = [], []
    for logctx in logctxs:
        job = logs.dbcmd('get_job', logctx.calc_id)
        tb = logs.dbcmd('get_traceback', logctx.calc_id)
        out.append((job.id, job.description, tb[-1] if tb else ''))
        if tb:
            count_errors += 1
        dstore = datastore.read(logctx.calc_id)
        try:
            a07s.append(views.view('asce:07', dstore))
            a41s.append(views.view('asce:41', dstore))
        except KeyError:
            # AELO results could not be computed due to some error
            continue

    # printing/saving results
    print(views.text_table(out, ['job_id', 'description', 'error'], ext='org'))
    dt = (time.time() - t0) / 60
    print('Total time: %.1f minutes' % dt)
    if not a07s or not a41s:
        # serious problem to debug
        breakpoint()
    for name, arrays in zip(['asce07', 'asce41'], [a07s, a41s]):
        arr = numpy.concatenate(arrays, dtype=arrays[0].dtype)
        fname = os.path.abspath(name + '.org')
        with open(fname, 'w') as f:
            print(views.text_table(arr, ext='org'), file=f)
        print(f'Stored {fname}')
    if count_errors:
        sys.exit(f'{count_errors} error(s) occurred')


def run_site(lonlat_or_fname, mosaic_dir=None,
             *, hc: int = None, slowest: int = None,
             concurrent_jobs: int = None, vs30: float = 760,
             asce_version: str = oqvalidation.OqParam.asce_version.default):
    """
    Run a PSHA analysis on the given sites or given a CSV file
    formatted as described in the 'from_file' function. For instance

    # oq mosaic run_site 10,20:30,40:50,60
    """
    if not mosaic_dir and not config.directory.mosaic_dir:
        sys.exit('mosaic_dir is not specified in openquake.cfg')
    mosaic_dir = mosaic_dir or config.directory.mosaic_dir
    if lonlat_or_fname.endswith('.csv'):
        from_file(lonlat_or_fname, mosaic_dir, concurrent_jobs)
        return
    sites = lonlat_or_fname.replace(',', ' ').replace(':', ',')
    params = get_params_from(
        dict(sites=sites, vs30=vs30, asce_version=asce_version), mosaic_dir)
    logging.root.handlers = []  # avoid breaking the logs
    [jobctx] = engine.create_jobs([params], config.distribution.log_level,
                                  None, getpass.getuser(), hc)
    if slowest:
        engine_profile(jobctx, slowest or 40)
    else:
        engine.run_jobs([jobctx], concurrent_jobs=concurrent_jobs)


run_site.lonlat_or_fname = 'lon,lat of the site to analyze or CSV file'
run_site.mosaic_dir = 'mosaic directory'
run_site.hc = 'previous calculation ID'
run_site.slowest = 'profile and show the slowest operations'
run_site.concurrent_jobs = 'maximum number of concurrent jobs'
run_site.vs30 = 'vs30 value for the calculation'
run_site.asce_version = dict(
    help='ASCE version',
    choices=oqvalidation.OqParam.asce_version.validator.choices)

# ######################### sample rups and gmfs ######################### #

EXTREME_GMV = 1000.
TRUNC_LEVEL = -1  # do not change it
MIN_DIST = 0.


def build_params(model, trunclevel, mindist, extreme_gmv, gmf):
    ini = os.path.join(
        config.directory.mosaic_dir, model, 'in', 'job_vs30.ini')
    params = readinput.get_params(ini)
    # change the parameters to produce an eff_time of 100,000 years
    itime = int(round(float(params['investigation_time'])))
    params['number_of_logic_tree_samples'] = 1000
    params['ses_per_logic_tree_path'] = str(100 // itime)
    params['calculation_mode'] = 'event_based'
    params.pop('ps_grid_spacing', None)  # ignored in event based
    if 'minimum_distance' not in params:
        params['minimum_distance'] = str(mindist)
    if 'extreme_gmv' not in params:
        params['extreme_gmv'] = str(extreme_gmv)
    if gmf:
        params['minimum_magnitude'] = '7.0'
        if trunclevel != TRUNC_LEVEL:
            params['truncation_level'] = str(trunclevel)
        # params['minimum_intensity'] = '1.0'
        os.environ['OQ_SAMPLE_SITES'] = '.01'
    else:  # rups only
        params['minimum_magnitude'] = '5.0'
        params['ground_motion_fields'] = 'false'
        params['inputs'].pop('site_model', None)
    for p in ('number_of_logic_tree_samples', 'ses_per_logic_tree_path',
              'investigation_time', 'minimum_magnitude', 'truncation_level',
              'minimum_distance', 'extreme_gmv'):
        logging.info('%s = %s' % (p, params[p]))
    logging.root.handlers = []  # avoid breaking the logs
    params['mosaic_model'] = logs.get_tag(ini)
    return params


def sample_rups(models, gmfs=False, *,
                trunclevel: float = TRUNC_LEVEL,
                mindist: float = MIN_DIST,
                extreme_gmv: float = EXTREME_GMV,
                slowest: int = None):
    """
    Sample the ruptures of the given models in the mosaic
    with an effective investigation time of 100,000 years
    """
    if not config.directory.mosaic_dir:
        sys.exit('mosaic_dir is not specified in openquake.cfg')

    models = models.split(',')
    hc = None
    if len(models) == 1:
        params = build_params(
            models[0], trunclevel, mindist, extreme_gmv, gmfs)
        [jobctx] = engine.create_jobs([params], config.distribution.log_level,
                                      None, getpass.getuser(), hc)
        if slowest:
            engine_profile(jobctx, slowest or 40)
        else:
            engine.run_jobs([jobctx])
        return
    allparams = [build_params(model, trunclevel, mindist, extreme_gmv, gmfs)
                 for model in models]
    jobs = engine.create_jobs(allparams, config.distribution.log_level,
                              None, getpass.getuser(), hc)
    engine.run_jobs(jobs)


sample_rups.models = '3-letter names of the models, comma-separated'
sample_rups.trunclevel = 'truncation level (default: the one in job_vs30.ini)'
sample_rups.mindist = 'minimum_distance (default: 0)'
sample_rups.extreme_gmv = 'threshold above which a GMV is extreme'
sample_rups.gmfs = 'compute GMFs'
sample_rups.slowest = 'profile and show the slowest operations'


impact_res = dict(count_errors=0, res_list=[])


def callback(job_id, params, exc=None):
    if exc:
        logging.error(str(exc), exc_info=True)
        impact_res['count_errors'] += 1
        error = str(exc)
    else:
        error = ''
    description = params['description']
    impact_res['res_list'].append((job_id, description, error))


def impact(exposure_hdf5='', *,
           rupfname=FAMOUS,
           stations='',
           mosaic_model='',
           maximum_distance='300',
           maximum_distance_stations='',
           asset_hazard_distance='15',
           number_of_ground_motion_fields='10'):
    """
    Run OQImpact calculations starting from a rupture file that can be
    an XML or a CSV (by default "famous_ruptures.csv"). You must pass
    a directory containing two files site_model.hdf5 and exposure.hdf5
    with a well defined structure.
    """
    if not exposure_hdf5 and not config.directory.mosaic_dir:
        sys.exit('mosaic_dir is not specified in openquake.cfg')
    trt = ''
    truncation_level = '3'
    ses_seed = '42'
    t0 = time.time()
    if rupfname.endswith('.csv'):
        rupture_file = None
        df = pandas.read_csv(rupfname)
        for i, row in df.iterrows():
            usgs_id = row['usgs_id']
            print('###################### %s [%d/%d] #######################' %
                  (usgs_id, i + 1, len(df)))
            main_cmd(
                usgs_id, rupture_file, callback,
                maximum_distance=maximum_distance,
                mosaic_model=mosaic_model,
                trt=trt, truncation_level=truncation_level,
                number_of_ground_motion_fields=number_of_ground_motion_fields,
                asset_hazard_distance=asset_hazard_distance,
                ses_seed=ses_seed, exposure_hdf5=exposure_hdf5,
                station_data_file=stations,
                maximum_distance_stations=maximum_distance_stations)
    else:  # assume .xml
        main_cmd('WithRuptureFile', rupfname, callback,
                 maximum_distance=maximum_distance,
                 mosaic_model=mosaic_model,
                 trt=trt, truncation_level=truncation_level,
                 number_of_ground_motion_fields=number_of_ground_motion_fields,
                 asset_hazard_distance=asset_hazard_distance,
                 ses_seed=ses_seed, exposure_hdf5=exposure_hdf5,
                 station_data_file=stations,
                 maximum_distance_stations=maximum_distance_stations)
    header = ['job_id', 'description', 'error']
    print(views.text_table(impact_res['res_list'], header, ext='org'))
    dt = (time.time() - t0) / 60
    print('Total time: %.1f minutes' % dt)
    if impact_res['count_errors']:
        sys.exit(f'{impact_res["count_errors"]} error(s) occurred')


impact.exposure_hdf5 = 'Path to the file exposure.hdf5'
impact.rupfname = ('Filename with the same format as famous_ruptures.csv '
                      'or file rupture_model.xml')
impact.stations = 'Path to a csv file with the station data'
impact.mosaic_model = 'Mosaic model 3-characters code'
impact.maximum_distance = 'Maximum distance in km'
impact.maximum_distance_stations = "Maximum distance from stations in km"
impact.number_of_ground_motion_fields = 'Number of ground motion fields'

# ################################## main ################################## #

main = dict(run_site=run_site, impact=impact,
            sample_rups=sample_rups)
