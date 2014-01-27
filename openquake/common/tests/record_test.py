#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2013, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import unittest
from openquake.common import record, records

class RecordTest(unittest.TestCase):
    def test1(self):
        self.r = records.Exposure(id='1', category='population',
                                  taxonomySource='', description='test',
                                  area_type='', area_unit='')
        self.assertEqual(self.r.to_tuple(), ('1', 'population', '', 'test',
                                             None, None, None, None))
        self.assertTrue(self.r.is_valid())

    def test2(self):
        self.r = records.Exposure(id='1', category='population',
                                  taxonomySource='', description='test',
                                  area_type='per_asset', area_unit='km^2')
        self.assertEqual(self.r.to_tuple(), ('1', 'population', '', 'test',
                                             'per_asset', 'km^2', None, None))
        self.assertTrue(self.r.is_valid())

    def test3(self):
        self.r = records.Exposure(id='1', category='population',
                                  taxonomySource='', description='test',
                                  area_type='', area_unit='km^2')
        self.assertEqual(self.r.to_tuple(), ('1', 'population', '', 'test',
                                             None, 'km^2', None, None))
        self.assertFalse(self.r.is_valid())

    def test4(self):
        self.r = records.Exposure(id='1', category='population',
                                  taxonomySource='', description='test',
                                  area_type='per_asset', area_unit='')
        self.assertEqual(self.r.to_tuple(), ('1', 'population', '', 'test',
                                             'per_asset', None, None, None))
        self.assertFalse(self.r.is_valid())
