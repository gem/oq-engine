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

DATA = os.path.join(os.path.dirname(__file__), 'jsondata')


class PostDict(dict):
    def get(self, key, default=None):
        if key in self:
            return self[key][0]
        return default


class AristotleValidateTestCase(unittest.TestCase):
    def test_1(self):
        POST = PostDict({'usgs_id': ['us6000jllz']})
        rupdic, params, err = aristotle_validate(POST, datadir=DATA)
        self.assertEqual(rupdic['is_point_rup'], True)
        self.assertIn('stations', params[0])
        self.assertEqual(err, {})
    
