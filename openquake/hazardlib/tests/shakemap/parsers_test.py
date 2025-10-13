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

import os
import unittest
import csv
from openquake.hazardlib.shakemap.parsers import (
    get_rup_dic, User, utc_to_local_time, get_stations_from_usgs,
    get_shakemap_versions, get_nodal_planes_and_info)
from openquake.hazardlib.source.rupture import BaseRupture
from openquake.hazardlib.geo.surface.complex_fault import ComplexFaultSurface

user = User(level=2, testdir=os.path.join(os.path.dirname(__file__), 'data'))


class ShakemapParsersTestCase(unittest.TestCase):
    @classmethod
    def setUp(cls):
        try:
            import timezonefinder
        except ImportError:
            raise unittest.SkipTest('Missing timezonefinder')
        else:
            del timezonefinder

    def test_utc_to_local_time(self):
        loctime = utc_to_local_time('2011-01-01T12:00:00.0Z', 10., 45.)
        self.assertEqual(str(loctime.tzinfo), 'Europe/Rome')

    def test_1(self):
        # wrong usgs_id
        _rup, _rupdic, err = get_rup_dic(
            {'usgs_id': 'usp0001cc', 'approach': 'use_shakemap_from_usgs'},
            User(level=2, testdir=''), use_shakemap=True)
        self.assertIn(
            'Unable to download from https://earthquake.usgs.gov/fdsnws/'
            'event/1/query?eventid=usp0001cc&', err['error_msg'])

    def test_2(self):
        _rup, dic, _err = get_rup_dic(
                {'usgs_id': 'usp0001ccb', 'approach': 'use_shakemap_from_usgs'},
                user=user, use_shakemap=True)
        self.assertIsNotNone(dic['shakemap_array'])
        _rup, dic, _err = get_rup_dic(
            {'usgs_id': 'usp0001ccb', 'approach': 'use_shakemap_from_usgs'},
            user=user, use_shakemap=False)
        self.assertIsNone(dic['shakemap_array'])

    def test_3(self):
        usgs_id = 'us6000f65h'
        _rup, dic, _err = get_rup_dic(
            {'usgs_id': usgs_id, 'approach': 'use_pnt_rup_from_usgs'},
            user=user, use_shakemap=True)
        self.assertEqual(dic['lon'], -73.4822)
        self.assertEqual(dic['lat'], 18.4335)
        self.assertEqual(dic['dep'], 10.0)
        self.assertEqual(dic['mag'], 7.2)
        self.assertEqual(dic['rake'], 0.0)
        self.assertEqual(dic['local_timestamp'], '2021-08-14 08:29:08-04:00')
        self.assertEqual(dic['time_event'], 'transit')
        self.assertEqual(dic['pga_map_png'], None)
        self.assertEqual(dic['mmi_map_png'], None)
        self.assertEqual(dic['usgs_id'], 'us6000f65h')
        self.assertEqual(dic['rupture_file'], None)
        self.assertIsNotNone(dic['mmi_file'])
        station_data_file, n_stations, station_err = get_stations_from_usgs(
            usgs_id, user=user, shakemap_version='usgs_preferred')
        self.assertIsNone(station_data_file)
        self.assertEqual(n_stations, 0)
        self.assertEqual(station_err['error_msg'], 'No stations were found')

    def test_3b(self):
        rup, _dic, _err = get_rup_dic(
            {'usgs_id': 'usp0001ccb', 'approach': 'use_shakemap_fault_rup_from_usgs'},
            user=user, use_shakemap=True)
        self.assertIsInstance(rup, BaseRupture)

    def test_3c(self):
        _rup, _dic, err = get_rup_dic(
            {'usgs_id': 'us6000f65h', 'approach': 'use_shakemap_fault_rup_from_usgs'},
            user=user, use_shakemap=True)
        self.assertIn('Unable to retrieve rupture geometries', err['error_msg'])

    def test_3d(self):
        # TODO: make it possible to convert this kind of geometries
        usgs_id = 'us6000jllz'
        _rup, dic, _err = get_rup_dic(
            {'usgs_id': usgs_id, 'approach': 'use_shakemap_fault_rup_from_usgs'},
            user=user, use_shakemap=True)
        self.assertIn('Unable to convert the rupture', dic['rupture_issue'])
        station_data_file, n_stations, station_err = get_stations_from_usgs(
            usgs_id, user=user, shakemap_version='usgs_preferred')
        self.assertIn('stations', station_data_file)
        self.assertEqual(n_stations, 1)
        self.assertEqual(station_err, {})

    def test_3e(self):
        usgs_id = 'us7000pn9s'
        station_data_file, n_stations, station_err = get_stations_from_usgs(
            usgs_id, user=user, shakemap_version='usgs_preferred')
        self.assertIn('stations', station_data_file)
        self.assertEqual(n_stations, 1)
        self.assertEqual(station_err, {})
        with open(station_data_file, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            row = next(reader)
            pga_value = float(row['PGA_VALUE'])
            self.assertEqual(pga_value, 0.62308)

    def test_4(self):
        # point_rup
        _rup, dic, _err = get_rup_dic(
            {'usgs_id': 'us6000jllz', 'approach': 'use_shakemap_from_usgs'},
            user=user, use_shakemap=True)
        self.assertEqual(dic['lon'], 37.0143)
        self.assertEqual(dic['lat'], 37.2256)
        self.assertEqual(dic['dep'], 10.)

    def test_5(self):
        for approach in ['use_shakemap_fault_rup_from_usgs', 'use_shakemap_from_usgs']:
            rup, _dic, _err = get_rup_dic(
                {'usgs_id': 'us20002926', 'approach': approach},
                user=user, use_shakemap=True)
            self.assertIsInstance(rup.surface, ComplexFaultSurface)

    def test_6(self):
        usgs_id = 'usp0001ccb'
        _rup, dic, _err = get_rup_dic(
            {'usgs_id': usgs_id, 'approach': 'use_pnt_rup_from_usgs'},
            user=user, use_shakemap=True)
        self.assertEqual(dic['mag'], 6.7)
        station_data_file, n_stations, station_err = get_stations_from_usgs(
            usgs_id, user=user, shakemap_version='usgs_preferred')
        self.assertIsNone(station_data_file)
        self.assertEqual(n_stations, 0)
        self.assertEqual(station_err['error_msg'],
                         '3 stations were found, but none of them are seismic')

    def test_7(self):
        usgs_id = 'us6000jllz'
        expected_nodal_planes = {
            'NP1': {'dip': 88.71, 'rake': -179.18, 'strike': 317.63},
            'NP2': {'dip': 89.18, 'rake': -1.29, 'strike': 227.61}
        }
        expected_info = {'lon': '37.0143', 'lat': '37.2256', 'dep': '10', 'mag': '7.8'}
        nodal_planes, info, _err = get_nodal_planes_and_info(usgs_id, user=user)
        self.assertEqual(nodal_planes, expected_nodal_planes)
        self.assertEqual(info, expected_info)

    def test_7b(self):
        # Case reading nodal planes first from the moment-tensor (not found)
        # then falling back to reading them from the focal-mechanism
        usgs_id = 'usp0001ccb'
        expected_nodal_planes = {
            'NP1': {'dip': 37.0, 'rake': -64.0, 'strike': 285.0},
            'NP2': {'dip': 57.0, 'rake': -109.0, 'strike': 73.0}
        }
        expected_info = {'lon': '22.934', 'lat': '38.222', 'dep': '33', 'mag': '6.7'}
        nodal_planes, info, _err = get_nodal_planes_and_info(usgs_id, user=user)
        self.assertEqual(nodal_planes, expected_nodal_planes)
        self.assertEqual(info, expected_info)

    def test_8(self):
        dic_in = {'usgs_id': 'us6000jllz', 'lon': 37.0143, 'lat': 37.2256,
                  'dep': 10.0, 'mag': 7.8, 'rake': 0.0,
                  'approach': 'use_pnt_rup_from_usgs'}
        rup, dic, _err = get_rup_dic(dic_in, user=user, use_shakemap=True)
        self.assertEqual(dic['msr'], 'PointMSR')
        self.assertAlmostEqual(rup.surface.length, 0.0133224)
        self.assertAlmostEqual(rup.surface.width, 0.0070800)

    def test_9(self):
        dic_in = {
            'usgs_id': 'us6000jllz', 'lon': 37.0143, 'lat': 37.2256, 'dep': 10,
            'mag': 7.8, 'msr': 'WC1994', 'aspect_ratio': 3,
            'rake': -179.18, 'dip': 88.71, 'strike': 317.63,
            'approach': 'build_rup_from_usgs'}
        _rup, dic, _err = get_rup_dic(dic_in, user=user, use_shakemap=True)
        self.assertEqual(dic['dep'], 10)
        self.assertEqual(dic['dip'], 88.71)
        self.assertEqual(dic['lat'], 37.2256)
        self.assertEqual(dic['lon'], 37.0143)
        self.assertEqual(dic['mag'], 7.8)
        self.assertEqual(dic['msr'], 'WC1994')
        self.assertEqual(dic['rake'], -179.18)
        self.assertEqual(dic['strike'], 317.63)
        self.assertEqual(dic['aspect_ratio'], 3)

    def test_10(self):
        dic_in = {'usgs_id': 'us6000jllz',
                  'lon': 37.0143, 'lat': 37.2256, 'dep': 10.0,
                  'mag': 7.8, 'msr': 'WC1994', 'aspect_ratio': 2.0,
                  'rake': -179.18, 'dip': 88.71, 'strike': 317.63,
                  'approach': 'build_rup_from_usgs'}
        _rup, _dic, err = get_rup_dic(
            dic_in, user=user, use_shakemap=True)
        self.assertIn('The depth must be greater', err['error_msg'])

    def test_11(self):
        dic_in = {'usgs_id': 'UserProvided', 'lon': -9, 'lat': 43, 'dep': 10,
                  'mag': 8.5, 'msr': 'WC1994', 'aspect_ratio': 1,
                  'rake': 90, 'dip': 90, 'strike': 0,
                  'approach': 'provide_rup_params'}
        _rup, _dic, err = get_rup_dic(
            dic_in, user=user, use_shakemap=False)
        self.assertIn('The depth must be greater', err['error_msg'])

    def test_12(self):
        current_dir = os.path.dirname(__file__)
        rupture_file_path = os.path.join(current_dir, 'data', 'fault_rupture.xml')
        dic_in = {'usgs_id': 'FromFile', 'approach': 'provide_rup'}
        rup, dic, _err = get_rup_dic(
            dic_in, user=user, use_shakemap=False, rupture_file=rupture_file_path)
        self.assertIsInstance(rup, BaseRupture)
        # hypocenter was outside the rupture surface and it is moved to the
        # center of the surface
        self.assertAlmostEqual(dic['lon'], 84.67005814)
        self.assertAlmostEqual(dic['lat'], 28.0419600)
        self.assertAlmostEqual(dic['dep'], 35.0)
        self.assertEqual(dic['mag'], 7.0)
        self.assertEqual(dic['rake'], 90.0)
        self.assertAlmostEqual(dic['strike'], 295.2473184)
        self.assertAlmostEqual(dic['dip'], 30.0833517)
        self.assertEqual(dic['usgs_id'], 'FromFile')
        self.assertIn('.xml', dic['rupture_file'])

    def test_12b(self):
        current_dir = os.path.dirname(__file__)
        rupture_file_path = os.path.join(current_dir, 'data', 'fault_rupture.csv')
        dic_in = {'usgs_id': 'FromFile', 'approach': 'provide_rup'}
        rup, dic, _err = get_rup_dic(
            dic_in, user=user, use_shakemap=False, rupture_file=rupture_file_path)
        self.assertIsInstance(rup, BaseRupture)
        self.assertEqual(dic['lon'], -55.938899993896484)
        self.assertEqual(dic['lat'], 44.51041030883789)
        self.assertEqual(dic['dep'], 10.5)
        self.assertEqual(dic['mag'], 7.050000190734863)
        self.assertEqual(dic['rake'], 0.0)
        self.assertAlmostEqual(dic['strike'], 0.0)
        self.assertAlmostEqual(dic['dip'], 90.0)
        self.assertEqual(dic['usgs_id'], 'FromFile')
        self.assertIn('.csv', dic['rupture_file'])

    def test_13(self):
        usgs_id = 'us7000n7n8'
        station_data_file, n_stations, station_err = get_stations_from_usgs(
            usgs_id, user=user, shakemap_version='usgs_preferred')
        self.assertIsNone(station_data_file)
        self.assertEqual(n_stations, 0)
        self.assertEqual(station_err['error_msg'],
                         'stationlist.json was downloaded, but it contains no features')

    def test_14(self):
        usgs_id = 'us20002926'
        shakemap_versions, usgs_preferred_version, err = get_shakemap_versions(
            usgs_id, user=user)
        self.assertEqual(err, {})
        self.assertEqual(len(shakemap_versions), 3)
        self.assertEqual(usgs_preferred_version,
                         'urn:usgs-product:atlas:shakemap:us20002926:1594162031303')
        first_version = shakemap_versions[0]
        self.assertIn('id', first_version)
        self.assertIn('utc_date_time', first_version)
        usgs_id = 'does_not_exist'
        shakemap_versions, usgs_preferred_version, err = get_shakemap_versions(usgs_id)
        self.assertIsNone(shakemap_versions)
        self.assertIsNone(usgs_preferred_version)
        self.assertIn('Unable to download', err['error_msg'])

    def test_15(self):
        usgs_id = 'usp0001ccb'
        shakemap_versions, _usgs_preferred_version, _err = get_shakemap_versions(
            usgs_id, user=user)
        first_version = shakemap_versions[0]
        _rup, dic, _err = get_rup_dic(
                {'usgs_id': 'usp0001ccb', 'approach': 'use_shakemap_from_usgs'},
                user=user, use_shakemap=True, shakemap_version=first_version['id'])
        self.assertIsNotNone(dic['shakemap_array'])

    def test_16(self):
        _rup, _dic, err = get_rup_dic(
            {'usgs_id': 'usp0001ccb', 'approach': 'use_finite_fault_model_from_usgs'},
            user=user, use_shakemap=True)
        self.assertIn('The finite-fault was not found', err['error_msg'])

    def test_17(self):
        rup, dic, _err = get_rup_dic(
            {'usgs_id': 'us6000jllz', 'approach': 'use_finite_fault_model_from_usgs'},
            user=user, use_shakemap=True)
        self.assertIsInstance(rup, BaseRupture)
        # ignoring file paths
        expected_dic = {
            'lon': 37.0485, 'lat': 37.25841, 'dep': 14.0, 'mag': 7.899000177543584,
            'rake': 0.0, 'strike': 41.59611892700195, 'dip': 80.92811584472656,
            'usgs_id': 'us6000jllz',
            'title': 'M 7.8 - Pazarcik earthquake, Kahramanmaras earthquake sequence',
            'shakemap_desc': 'v17: 2023-04-14 18:07:22'}
        for key in expected_dic:
            self.assertEqual(dic[key], expected_dic[key])


"""
NB: to profile a test you can use

with cProfile.Profile() as pr:
   ...
   pr.print_stats('cumulative')
"""
