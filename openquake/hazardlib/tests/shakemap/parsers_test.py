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
from openquake.hazardlib.shakemap.parsers import \
    download_rupture_dict, MissingLink

DATA = os.path.join(os.path.dirname(__file__), 'jsondata')


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
            download_rupture_dict('usp0001cc')
        self.assertIn('Unable to download from https://earthquake.usgs.gov/fdsnws/'
                      'event/1/query?eventid=usp0001cc&', str(ctx.exception))

    def test_3(self):
        rupdic = download_rupture_dict('us6000f65h', datadir=DATA)
        self.assertEqual(rupdic, {'lon': -73.475, 'lat': 18.408, 'dep': 10.0,
                                  'mag': 7.2, 'rake': 0.0,
                                  'local_timestamp': '2021-08-13 20:00:00-04:00',
                                  'time_event': 'transit', 'is_point_rup': True,
                                  'pga_map_png': None, 'mmi_map_png': None,
                                  'usgs_id': 'us6000f65h', 'rupture_file': None})

    def test_4(self):
        # point_rup
        rupdic = download_rupture_dict('us6000jllz', datadir=DATA)
        self.assertEqual(rupdic['lon'], 37.0143)
        self.assertEqual(rupdic['lat'], 37.2256)
        self.assertEqual(rupdic['dep'], 10.)
        self.assertEqual(rupdic['is_point_rup'], True)

    def test_5(self):
        # no point_rup
        rupdic = download_rupture_dict('usp0001ccb', datadir=DATA)
        self.assertEqual(rupdic['is_point_rup'], False)


"""
NB: to profile a test you can use

with cProfile.Profile() as pr:
   ...
   pr.print_stats('cumulative')
"""
