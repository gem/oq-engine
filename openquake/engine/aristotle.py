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
Master script for running an ARISTOTLE analysis
"""
import os
import getpass
import logging
import numpy
from openquake.baselib import config, hdf5, sap
from openquake.hazardlib import geo
from openquake.hazardlib.shakemap.parsers import get_rupture_dict
from openquake.commonlib import readinput
from openquake.engine import engine

CDIR = os.path.dirname(__file__)  # openquake/engine


def get_trts_around(lon, lat):
    """
    :returns: list of TRTs for the mosaic model covering lon, lat
    """
    lonlats = numpy.array([[lon, lat]])
    mosaic_df = readinput.read_mosaic_df(buffer=0.1)
    [mosaic_model] = geo.utils.geolocate(lonlats, mosaic_df)
    smodel = os.path.join(config.directory.mosaic_dir, 'site_model.hdf5')
    with hdf5.File(smodel) as f:
       df = f.read_df('model_trt_gsim_weight',
                      sel={'model': mosaic_model.encode()})
    return [trt.decode('utf8') for trt in df.trt.unique()]


def get_tmap_keys(exposure_hdf5, countries):
    """
    :returns: list of taxonomy mappings as keys in the the "tmap" data group
    """
    keys = []
    with hdf5.File(exposure_hdf5, 'r') as exp:
        for key in exp['tmap']:
            if set(key.split('_')) & countries:
                keys.append(key)
    return keys


def main(usgs_id, maxdist='300'):
    """
    This script is meant to be called from the WebUI in production mode,
    and from the command-line in testing mode.
    """
    smodel = os.path.join(config.directory.mosaic_dir, 'site_model.hdf5')
    expo = os.path.join(config.directory.mosaic_dir, 'exposure.hdf5')
    inputs = {'exposure': [expo],
              'site_model': [smodel],
              'job_ini': '<in-memory>'}
    rupdic = get_rupture_dict(usgs_id)
    trts = get_trts_around(rupdic['lon'], rupdic['lat'])
    params = dict(calculation_mode='scenario_risk', rupture_dict=str(rupdic),
                  maximum_distance=maxdist,
                  tectonic_region_type=trts[0],
                  truncation_level='3.0',
                  number_of_ground_motion_fields='10',
                  asset_hazard_distance='15',
                  inputs=inputs)
    oq = readinput.get_oqparam(params)
    sitecol, assetcol, discarded = readinput.get_sitecol_assetcol(oq)
    id0s, counts = numpy.unique(assetcol['ID_0'], return_counts=1)
    countries = set(assetcol.tagcol.ID_0[i] for i in id0s)
    tmap_keys = get_tmap_keys(expo, countries)
    logging.root.handlers = []  # avoid breaking the logs
    for key in tmap_keys:
        print('Using taxonomy mapping for %s' % key)
        params['countries'] = key.replace('_', ' ')
        jobs = engine.create_jobs(
            [params], config.distribution.log_level, None,
            getpass.getuser(), None)
        engine.run_jobs(jobs)


main.usgs_id = 'ShakeMap ID'
main.maxdist = 'Maximum distance in km'

if __name__ == '__main__':
    sap.run(main)
