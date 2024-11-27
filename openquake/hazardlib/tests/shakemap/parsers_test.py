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
    def test_1(self):
        # wrong usgs_id
        with self.assertRaises(URLError) as ctx:
            download_rupture_dict('usp0001cc')
        self.assertIn('Unable to download from https://earthquake.usgs.gov/fdsnws/'
                      'event/1/query?eventid=usp0001cc&', str(ctx.exception))
        
    def test_2(self):
        # ignore_shakemap
        with self.assertRaises(MissingLink) as ctx:
            download_rupture_dict('usp0001ccb', ignore_shakemap=True)
        self.assertIn('There is no finite-fault info for usp0001ccb', str(ctx.exception))

    def test_3(self):
        rupdic = download_rupture_dict('us6000jllz', datadir=DATA)
        #rupdic = download_rupture_dict('us6000jllz')
