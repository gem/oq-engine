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

import ast
import os
import unittest
from openquake.hazardlib.shakemap.parsers import User
from openquake.hazardlib.shakemap.validate import (
    impact_validate, _check_correlation_models, IMPACT_CORRELATION_MODELS)
from openquake.hazardlib.source.rupture import BaseRupture

user = User(level=2, testdir=os.path.join(os.path.dirname(__file__), 'data'))


class ImpactValidateTestCase(unittest.TestCase):
    @classmethod
    def setUp(cls):
        try:
            import timezonefinder
        except ImportError:
            raise unittest.SkipTest('Missing timezonefinder')
        else:
            del timezonefinder

    def test_correlation_models_by_kind_of_job(self):
        # ShakeMap jobs use LothBaker2013, the other jobs the joint models
        # supporting circulant embedding; any between-event model
        # accepting the IMTs of the job
        models = IMPACT_CORRELATION_MODELS
        self.assertEqual(
            models['within_event_correlation_model', 'shakemap'],
            ['LothBaker2013'])
        self.assertEqual(
            models['within_event_correlation_model', 'rupture'],
            ['LothBaker2013', 'DuNing2021Interpolated', 'MonteiroEtAl2026'])
        # GodaAtkinson2009 does not support the PGV of the ShakeMap jobs
        self.assertEqual(
            models['between_event_correlation_model', 'shakemap'],
            ['AbrahamsonEtAl2014BetweenEvent', 'FullCrossCorrelation',
             'NoCrossCorrelation'])
        self.assertEqual(
            models['between_event_correlation_model', 'rupture'],
            ['AbrahamsonEtAl2014BetweenEvent', 'FullCrossCorrelation',
             'GodaAtkinson2009', 'NoCrossCorrelation'])

    def test_check_correlation_models(self):
        # level 1 users always get the defaults
        params = {'within_event_correlation_model': 'JayaramBaker2009',
                  'within_event_correlation_params': {
                      'vs30_clustering': True},
                  'between_event_correlation_model': 'NoCrossCorrelation'}
        self.assertEqual(_check_correlation_models(
            params, User(level=1), use_shakemap=True), {})
        self.assertEqual(params, {
            'within_event_correlation_model': 'LothBaker2013',
            'between_event_correlation_model':
            'AbrahamsonEtAl2014BetweenEvent',
            'within_event_correlation_params': {}})
        # level 2 users get the defaults for the missing fields
        params = {'between_event_correlation_model': 'GodaAtkinson2009'}
        self.assertEqual(_check_correlation_models(
            params, user, use_shakemap=False), {})
        self.assertEqual(params['within_event_correlation_model'],
                         'LothBaker2013')
        self.assertEqual(params['between_event_correlation_model'],
                         'GodaAtkinson2009')
        # and cannot use a model not available for their kind of job
        for field, model, use_shakemap in [
                ('within_event_correlation_model', 'DuNing2021Interpolated',
                 True),
                ('within_event_correlation_model', 'JayaramBaker2009',
                 False),
                ('between_event_correlation_model', 'GodaAtkinson2009',
                 True)]:
            err = _check_correlation_models(
                {field: model}, user, use_shakemap)
            self.assertEqual(err['invalid_inputs'], [field])
            self.assertIn(f'{model} is not available', err['error_msg'])

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

    def test_nodal_plane_product_is_saved(self):
        POST = {
            'usgs_id': 'us7000n7n8', 'approach': 'build_rup_from_usgs',
            'nodal_plane': 'NP1', 'msr': 'WC1994', 'aspect_ratio': '2',
            'time_event': 'day', 'maximum_distance': '300',
            'truncation_level': '3',
            'number_of_ground_motion_fields': '10',
            'asset_hazard_distance': '15', 'ses_seed': '42'}
        _rup, rupdic, params, err = impact_validate(POST, user)
        self.assertEqual(err, {})
        self.assertEqual(rupdic['nodal_plane'], 'NP1')
        product = rupdic['mechanism_product']
        self.assertEqual(product['type'], 'moment-tensor')
        self.assertTrue(product['id'])
        stored = ast.literal_eval(params['rupture_dict'])
        self.assertEqual(stored['nodal_plane'], 'NP1')
        self.assertEqual(stored['mechanism_product'], product)

    def test_2a(self):
        POST = {'usgs_id': 'us7000n05d', 'approach': 'build_rup_from_usgs',
                'msr': ''}
        _rup, _rupdic, _params, err = impact_validate(POST, user)
        # msr can not be empty
        self.assertIn('Magnitude scaling relationship', err['error_msg'])

    def test_2b(self):
        POST = {'usgs_id': 'us7000n05d', 'approach': 'build_rup_from_usgs',
                'msr': 'WC1994'}
        rup, rupdic, _params, err = impact_validate(POST, user)
        self.assertIsInstance(rup, BaseRupture)
        self.assertEqual(rupdic['rupture_was_loaded'], True)
        self.assertEqual(rupdic['mosaic_models'], ['SAM', 'OPA'])
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
            'within_event_correlation_model': 'DuNing2021Interpolated',
            'between_event_correlation_model': 'GodaAtkinson2009',
            'truncation_level': '3',
            'usgs_id': 'FromFile',
            'approach': 'provide_rup'}

        for stations in (None, 'stationlist_seismic.csv'):
            _rup, rupdic, params, err = impact_validate(
                POST, user, rupture_file, stations)
            expected = {
                # hypocenter was outside the rupture surface and it is
                # moved to the center of the surface
                'dep': 35.0,
                'lat': 28.04196,
                'lon': 84.67006,
                'dip': 30.08335,
                'mag': 7.0,
                'mosaic_models': ['IND', 'CHN'],
                'rake': 90.0,
                'rupture_file': rupture_file,
                'rupture_was_loaded': True,
                'strike': 295.24732,
                'trts': {'CHN': ['Active Shallow Crust',
                                 'Himalayan Thrust',
                                 'Craton',
                                 'Deep Crust 1',
                                 'Active-Stable Shallow Crust',
                                 'Active Shallow Crust TWN'],
                         'IND': ['active shallow crust',
                                 'Himalayan Thrust',
                                 'stable shallow crust',
                                 'intraplate margin lower',
                                 'intraplate margin upper',
                                 'subduction intraslab',
                                 'subduction interface',
                                 'Oceanic Crust without Volcanism',
                                 'Oceanic Crust with Volcanism']},
                'usgs_id': 'FromFile'}
            for key in expected:
                assert rupdic[key] == expected[key], key
            self.assertEqual(params['asset_hazard_distance'], '15.0')
            self.assertEqual(params['calculation_mode'], 'scenario_risk')
            # all the time events are computed, the selected one is
            # used in the country reports
            self.assertNotIn('time_event', params)
            self.assertEqual(params['report_time_event'], 'day')
            self.assertEqual(params['maximum_distance'], '100.0')
            self.assertEqual(params['mosaic_model'], 'IND')
            self.assertEqual(params['truncation_level'], '3.0')
            self.assertEqual(params['number_of_ground_motion_fields'], '2'),
            self.assertEqual(params['ses_seed'], '42')
            self.assertEqual(
                params['correlation_strategy'], 'circulant_embedding')
            self.assertEqual(params['within_event_correlation_model'],
                             'DuNing2021Interpolated')
            self.assertEqual(params['between_event_correlation_model'],
                             'GodaAtkinson2009')
            self.assertEqual(params['within_event_correlation_params'], '{}')
            # self.assertEqual(params['station_data_file'], stations)  # FIXME
            self.assertEqual(err, {})

    def test_4(self):
        # for us7000n7n8 the stations.json does not contain stations
        POST = {'usgs_id': 'us7000n7n8', 'approach': 'build_rup_from_usgs',
                'msr': 'WC1994'}
        _rup, rupdic, _oqparams, err = impact_validate(POST, user)
        self.assertEqual(rupdic['mag'], 7.0)
        self.assertEqual(rupdic['time_event'], 'transit')
        self.assertEqual(rupdic['local_timestamp'],
                         '2024-08-18 07:10:26+12:00')
        self.assertEqual(err, {})

    def test_5(self):
        POST = {'usgs_id': 'us7000n7n8', 'approach': 'build_rup_from_usgs',
                'aspect_ratio': 2, 'msr': 'WC1994'}
        _rup, rupdic, _oqparams, _err = impact_validate(POST, user)
        self.assertIn('msr', rupdic)

    def test_provide_rup_params_correlation_models(self):
        # rupture-only job without ShakeMap keeps the chosen models
        POST = {
            'approach': 'provide_rup_params', 'use_shakemap': 'false',
            'usgs_id': 'UserProvided', 'lon': '84.4', 'lat': '27.6',
            'dep': '30', 'mag': '7', 'dip': '90', 'rake': '90',
            'strike': '0', 'aspect_ratio': '2', 'msr': 'WC1994',
            'mosaic_model': 'IND', 'time_event': 'day',
            'local_timestamp': '', 'maximum_distance': '100',
            'maximum_distance_stations': '',
            'asset_hazard_distance': '15',
            'number_of_ground_motion_fields': '2', 'ses_seed': '42',
            'truncation_level': '3',
            'within_event_correlation_model': 'MonteiroEtAl2026',
            'between_event_correlation_model': 'NoCrossCorrelation'}
        _rup, _rupdic, oqparams, err = impact_validate(POST, user)
        self.assertFalse(err)
        self.assertEqual(oqparams['within_event_correlation_model'],
                         'MonteiroEtAl2026')
        self.assertEqual(oqparams['between_event_correlation_model'],
                         'NoCrossCorrelation')
        self.assertEqual(oqparams['correlation_strategy'],
                         'circulant_embedding')
        self.assertNotIn('shakemap_uri', oqparams)
