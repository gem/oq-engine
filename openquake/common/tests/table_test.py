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

class TableTest(unittest.TestCase):

    def setUp(self):
        reclist = [records.FFLimitStateContinuous('severe')]
        self.t = record.Table(records.FFLimitStateContinuous, reclist)

    def test_insert(self):
        self.t.insert(0, records.FFLimitStateContinuous('moderate'))
        self.assertEqual(self.t[0], ['moderate'])
        self.assertEqual(self.t[1], ['severe'])

    def test_insert_update(self):
        self.t[0][0] = 'moderate'
        self.t.insert(0, records.FFLimitStateContinuous('severe'))