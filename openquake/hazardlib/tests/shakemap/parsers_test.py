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
from urllib.error import URLError
from openquake.hazardlib.shakemap.parsers import get_rup_dic

DATA = os.path.join(os.path.dirname(__file__), 'data')


class ShakemapParsersTestCase(unittest.TestCase):
    @classmethod
    def setUp(cls):
        try:
            import timezonefinder
        except ImportError:
            raise unittest.SkipTest('Missing timezonefinder')
        else:
            del timezonefinder

    def test_1(self):
        # wrong usgs_id
        with self.assertRaises(URLError) as ctx:
            get_rup_dic('usp0001cc')
        self.assertIn('Unable to download from https://earthquake.usgs.gov/fdsnws/'
                      'event/1/query?eventid=usp0001cc&', str(ctx.exception))

    def test_3(self):
        _rup, dic = get_rup_dic('us6000f65h', datadir=DATA)
        self.assertEqual(dic['lon'], -73.475)
        self.assertEqual(dic['lat'], 18.408)
        self.assertEqual(dic['dep'], 10.0)
        self.assertEqual(dic['mag'], 7.2)
        self.assertEqual(dic['rake'], 0.0)
        self.assertEqual(dic['local_timestamp'], '2021-08-13 20:00:00-04:00')
        self.assertEqual(dic['time_event'], 'transit')
        self.assertEqual(dic['require_dip_strike'], True)
        self.assertEqual(dic['pga_map_png'], None)
        self.assertEqual(dic['mmi_map_png'], None)
        self.assertEqual(dic['usgs_id'], 'us6000f65h')
        self.assertEqual(dic['rupture_file'], None)
        self.assertEqual(dic['station_data_file_from_usgs'], True)
        self.assertEqual(dic['station_data_issue'], 'No stations were found')

    def test_4(self):
        # point_rup
        _rup, dic = get_rup_dic('us6000jllz', datadir=DATA)
        self.assertEqual(dic['lon'], 37.0143)
        self.assertEqual(dic['lat'], 37.2256)
        self.assertEqual(dic['dep'], 10.)
        self.assertEqual(dic['require_dip_strike'], True)

    def test_5(self):
        # 12 vertices instead of 4 in rupture.json
        rup, dic = get_rup_dic('us20002926', datadir=DATA)
        self.assertIsNone(rup)
        self.assertEqual(dic['require_dip_strike'], True)
        self.assertEqual(dic['rupture_issue'],
                         'Unable to convert the rupture from the USGS format')

    def test_6(self):
        rup, dic = get_rup_dic('usp0001ccb', datadir=DATA)
        self.assertEqual(rup.mag, 6.7)
        self.assertEqual(dic['require_dip_strike'], False)
        self.assertEqual(dic['station_data_issue'],
                         '3 stations were found, but none of them are seismic')


"""
NB: to profile a test you can use

with cProfile.Profile() as pr:
   ...
   pr.print_stats('cumulative')
"""
