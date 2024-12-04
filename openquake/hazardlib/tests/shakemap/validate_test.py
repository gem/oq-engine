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

import os
import unittest
from openquake.hazardlib.shakemap.validate import aristotle_validate

DATA = os.path.join(os.path.dirname(__file__), 'data')

class AristotleValidateTestCase(unittest.TestCase):
    @classmethod
    def setUp(cls):
        try:
            import timezonefinder
        except ImportError:
            raise unittest.SkipTest('Missing timezonefinder')
        else:
            del timezonefinder

    def test_1(self):
        # without rupture, stations
        POST = {'usgs_id': 'us6000jllz'}
        _rup, rupdic, _params, err = aristotle_validate(POST, datadir=DATA)
        self.assertEqual(rupdic['require_dip_strike'], True)
        self.assertIn('stations', rupdic['station_data_file'])
        self.assertEqual(err, {})

    def test_2(self):
        # with rupture_file
        POST = {
            'asset_hazard_distance': '15',
            'dep': '30',
            'dip': '90',
            'lat': '27.6',
            'local_timestamp': '',
            'lon': '84.4',
            'mag': '7',
            'maximum_distance': '100',
            'maximum_distance_stations': '',
            'mosaic_model': 'IND',
            'number_of_ground_motion_fields': '2',
            'rake': '90',
            'ses_seed': '42',
            'strike': '0',
            'time_event': 'day',
            'trt': 'active shallow crust normal',
            'truncation_level': '3',
            'usgs_id': 'FromFile'}

        for stations in (None, 'stationlist_seismic.csv'):
            _rup, rupdic, params, err = aristotle_validate(
                POST, 'fault_rupture.xml', stations, datadir=DATA)
            self.assertEqual(
                rupdic,
                {'dep': 30.0,
                 'dip': 30.08335,
                 'lat': 27.6,
                 'lon': 84.4,
                 'mag': 7.0,
                 'mosaic_models': ['CHN', 'IND'],
                 'rake': 90.0,
                 'rupture_file': 'fault_rupture.xml',
                 'rupture_from_usgs': True,
                 'station_data_file': stations,
                 'strike': 295.24732,
                 'trts': {'CHN': ['Active Shallow Crust',
                                  'Himalayan Thrust',
                                  'Craton',
                                  'Deep Crust 1',
                                  'Active-Stable Shallow Crust'],
                          'IND': ['active shallow crust normal',
                                  'active shallow crust strike-slip reverse',
                                  'intraplate margin lower',
                                  'intraplate margin upper',
                                  'stable shallow crust',
                                  'subduction interface',
                                  'subduction interface megathrust',
                                  'subduction intraslab Himalayas',
                                  'subduction intraslab']},
                 'usgs_id': 'FromFile'})
            self.assertEqual(params['asset_hazard_distance'], '15.0')
            self.assertEqual(params['calculation_mode'], 'scenario_risk')
            self.assertEqual(params['time_event'], 'day')
            self.assertEqual(params['maximum_distance'], '100.0')
            self.assertEqual(params['mosaic_model'], 'IND')
            self.assertEqual(params['truncation_level'], '3.0')
            self.assertEqual(params['number_of_ground_motion_fields'], '2'),
            self.assertEqual(params['ses_seed'], '42')
            self.assertEqual(err, {})

    def test_4(self):
        # for us7000n7n8 the stations.json does not contain stations
        POST = {'usgs_id': 'us7000n7n8'}
        _rup, rupdic, _params, err = aristotle_validate(POST, datadir=DATA)
        self.assertEqual(rupdic['require_dip_strike'], False)
        self.assertEqual(rupdic['mag'], 7.0)
        self.assertEqual(rupdic['time_event'], 'transit')
        self.assertEqual(rupdic['local_timestamp'], '2024-08-18 07:10:26+12:00')
        self.assertEqual(
            err, {'station_data_issue': ('stationlist.json was downloaded,'
                                         ' but it contains no features')})
