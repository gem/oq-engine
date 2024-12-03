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
import sys
import os
import getpass
import logging
from openquake.baselib import sap
from openquake.hazardlib.shakemap.validate import AristotleParam
from openquake.engine import engine

CDIR = os.path.dirname(__file__)  # openquake/engine


def trivial_callback(
        job_id, params, job_owner_email=None, outputs_uri=None, exc=None):
    if exc:
        logging.error('', exc_info=True)
        sys.exit('There was an error: %s' % exc)
    print('Finished job(s) %d correctly. Params: %s' % (job_id, params))


def main_web(allparams, jobctxs,
             job_owner_email=None, outputs_uri=None,
             callback=trivial_callback):
    """
    This script is meant to be called from the WebUI
    """
    for params, job in zip(allparams, jobctxs):
        try:
            engine.run_jobs([job])
        except Exception as exc:
            callback(job.calc_id, params, job_owner_email,
                     outputs_uri, exc=exc)
        else:  # success
            callback(job.calc_id, params, job_owner_email, outputs_uri)


def main_cmd(usgs_id, rupture_file=None, rupture_dict=None,
             callback=trivial_callback, *,
             time_event='day',
             maximum_distance='300', mosaic_model=None, trt=None,
             truncation_level='3',
             number_of_ground_motion_fields='10', asset_hazard_distance='15',
             ses_seed='42',
             local_timestamp=None, exposure_hdf5=None, station_data_file=None,
             maximum_distance_stations=None):
    """
    This script is meant to be called from the command-line
    """
    if rupture_dict is None:
        rupture_dict = dict(usgs_id=usgs_id, rupture_file=rupture_file)
    try:
        oqparams = AristotleParam(
            rupture_dict, time_event, maximum_distance, mosaic_model,
            trt, truncation_level,
            number_of_ground_motion_fields, asset_hazard_distance,
            ses_seed, local_timestamp, exposure_hdf5, station_data_file,
            maximum_distance_stations).get_params()
    except Exception as exc:
        callback(None, dict(usgs_id=usgs_id), exc=exc)
        return
    # in  testing mode create new job contexts
    user = getpass.getuser()
    [job] = engine.create_jobs([oqparams], 'warn', None, user, None)
    try:
        engine.run_jobs([job])
    except Exception as exc:
        callback(job.calc_id, oqparams, exc=exc)
    else:
        callback(job.calc_id, oqparams, exc=None)


main_cmd.usgs_id = 'ShakeMap ID'  # i.e. us6000m0xl
main_cmd.rupture_file = 'XML file with the rupture model (optional)'
main_cmd.rupture_dict = 'Used by the command `oq mosaic aristotle`'
main_cmd.callback = ''
main_cmd.time_event = 'Time of the event (avg, day, night or transit)'
main_cmd.maximum_distance = 'Maximum distance in km'
main_cmd.mosaic_model = 'Mosaic model 3-characters code (optional)'
main_cmd.trt = 'Tectonic region type'
main_cmd.truncation_level = 'Truncation level'
main_cmd.number_of_ground_motion_fields = 'Number of ground motion fields'
main_cmd.asset_hazard_distance = 'Asset hazard distance'
main_cmd.ses_seed = 'SES seed'
main_cmd.local_timestamp = 'Local timestamp of the event (optional)'
main_cmd.station_data_file = 'CSV file with the station data'
main_cmd.maximum_distance_stations = 'Maximum distance from stations in km'
main_cmd.exposure_hdf5 = ('File containing the exposure, site model '
                          'and vulnerability functions')

if __name__ == '__main__':
    sap.run(main_cmd)
