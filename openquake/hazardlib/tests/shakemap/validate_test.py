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
"""
Validation tests for USGS ShakeMaps.
Here are a few codes with interesting errors:

- us6000jllz: ok stations, bad rupture
- usp0001ccb: '3 stations were found, but none of them are seismic'
- us7000n7n8: 'stationlist.json was downloaded, but it contains no features'
- us6000f65h: 'No stations were found'
- us20002926: 'Unable to convert the rupture from the USGS format'
- us7000n05d: USGS geometry == Point
"""

import os
import unittest
from openquake.hazardlib.shakemap.parsers import User
from openquake.hazardlib.shakemap.validate import impact_validate
from openquake.hazardlib.source.rupture import BaseRupture

user = User(level=2, testdir=os.path.join(os.path.dirname(__file__), 'data'))


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
        POST = {'usgs_id': 'us6000jllz', 'approach': 'use_shakemap_from_usgs'}
        _rup, _rupdic, _params, err = impact_validate(POST, user)
        self.assertEqual(err, {})

    def test_1b(self):
        # no rupture, yes stations
        POST = {'usgs_id': 'us6000jllz', 'approach': 'build_rup_from_usgs',
                'msr': 'WC1994', 'aspect_ratio': '3'}
        rup, _rupdic, _params, err = impact_validate(POST, user)
        self.assertIsInstance(rup, BaseRupture)
        self.assertEqual(err, {})

    def test_2a(self):
        POST = {'usgs_id': 'us7000n05d', 'approach': 'build_rup_from_usgs',
                'msr': ''}
        _rup, _rupdic, _params, err = impact_validate(POST, user)
        # msr can not be empty
        self.assertIn('Magnitude scaling relationship', err['error_msg'])

    def test_2b(self):
        POST = {'usgs_id': 'us7000n05d', 'approach': 'build_rup_from_usgs',
                'msr': 'WC1994'}
        _rup, rupdic, _params, err = impact_validate(POST, user)
        self.assertEqual(rupdic['rupture_from_usgs'], True)
        self.assertEqual(rupdic['mosaic_models'], ['SAM'])
        self.assertEqual(err, {})

    def test_3(self):
        # with rupture_file
        rupture_file = os.path.join(
            os.path.dirname(__file__), 'data', 'fault_rupture.xml')
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
            'usgs_id': 'FromFile',
            'approach': 'provide_rup'}

        for stations in (None, 'stationlist_seismic.csv'):
            _rup, rupdic, params, err = impact_validate(
                POST, user, rupture_file, stations)
            expected = {
                'dep': 30.0,
                'dip': 30.08335,
                'lat': 27.6,
                'lon': 84.4,
                'mag': 7.0,
                'mosaic_models': ['CHN', 'IND'],
                'rake': 90.0,
                'rupture_file': rupture_file,
                'rupture_from_usgs': True,
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
                'usgs_id': 'FromFile'}
            for key in expected:
                assert rupdic[key] == expected[key], key
            self.assertEqual(params['asset_hazard_distance'], '15.0')
            self.assertEqual(params['calculation_mode'], 'scenario_risk')
            self.assertEqual(params['time_event'], 'day')
            self.assertEqual(params['maximum_distance'], '100.0')
            self.assertEqual(params['mosaic_model'], 'IND')
            self.assertEqual(params['truncation_level'], '3.0')
            self.assertEqual(params['number_of_ground_motion_fields'], '2'),
            self.assertEqual(params['ses_seed'], '42')
            # self.assertEqual(params['station_data_file'], stations)  # FIXME
            self.assertEqual(err, {})

    def test_4(self):
        # for us7000n7n8 the stations.json does not contain stations
        POST = {'usgs_id': 'us7000n7n8', 'approach': 'build_rup_from_usgs',
                'msr': 'WC1994'}
        _rup, rupdic, _oqparams, err = impact_validate(POST, user)
        self.assertEqual(rupdic['mag'], 7.0)
        self.assertEqual(rupdic['time_event'], 'transit')
        self.assertEqual(rupdic['local_timestamp'], '2024-08-18 07:10:26+12:00')
        self.assertEqual(err, {})

    def test_5(self):
        POST = {'usgs_id': 'us7000n7n8', 'approach': 'build_rup_from_usgs',
                'aspect_ratio': 2, 'msr': 'WC1994'}
        _rup, rupdic, _oqparams, _err = impact_validate(POST, user)
        self.assertIn('msr', rupdic)
