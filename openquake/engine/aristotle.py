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
from openquake.risklib import asset
from openquake.risklib.countries import code2country
from openquake.commonlib import readinput
from openquake.engine import engine

CDIR = os.path.dirname(__file__)  # openquake/engine


def get_countries_around(rupdic, maxdist, expo, smodel):
    """
    :returns: (country_codes, counts) for the countries around rupdic
    """
    sm = readinput.get_site_model_around(smodel, rupdic, maxdist)
    gh3 = numpy.array(sorted(set(geo.utils.geohash3(sm['lon'], sm['lat']))))
    exposure = asset.Exposure.read_around(expo, gh3)
    id0s, counts = numpy.unique(exposure.assets['ID_0'], return_counts=1)
    return [exposure.tagcol.ID_0[i + 1] for i in id0s]


def get_trts_around(lon, lat):
    """
    :returns: list of TRTs for the mosaic model covering lon, lat
    """
    lonlats = numpy.array([[lon, lat]])
    mosaic_df = readinput.read_mosaic_df(buffer=0.1)
    [mosaic_model] = geo.utils.geolocate(lonlats, mosaic_df)
    smodel = os.path.join(config.directory.mosaic_dir, 'site_model.hdf5')
    with hdf5.File(smodel) as f:
       df = f.read_df('model_trt_gsim_weight', sel={'model': mosaic_model.encode()})
    return [trt.decode('utf8') for trt in df.trt.unique()]


def main(usgs_id, maxdist='200'):
    """
    This script is meant to be called from the WebUI in production mode,
    and from the command-line in testing mode.
    """
    smodel = os.path.join(config.directory.mosaic_dir, 'site_model.hdf5')
    expo = os.path.join(config.directory.mosaic_dir, 'exposure.hdf5')
    inputs = {'exposure': [expo], 'site_model': [smodel], 'job_ini': '<in-memory>'}
    logging.root.handlers = []  # avoid breaking the logs

    rupdic = get_rupture_dict(usgs_id)
    trts = get_trts_around(rupdic['lon'], rupdic['lat'])
    countries = get_countries_around(rupdic, maxdist, expo, smodel)
    cnames = [code2country.get(code, code) for code in countries]
    logging.info('Affecting %s', ' '.join(cnames))
    allparams = []
    for country in countries:
        params = dict(calculation_mode='scenario_risk', rupture_dict=str(rupdic),
                      maximum_distance=maxdist,
                      tectonic_region_type=trts[0],
                      truncation_level='3.0',
                      number_of_ground_motion_fields='10',
                      asset_hazard_distance='50',
                      country=country,
                      inputs=inputs)
        allparams.append(params)
    jobs = engine.create_jobs(
        allparams, config.distribution.log_level, None, getpass.getuser(), None)
    engine.run_jobs(jobs)

main.usgs_id = 'ShakeMap ID'


if __name__ == '__main__':
    sap.run(main)
