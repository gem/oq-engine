# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2021, GEM Foundation
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
from openquake.hazardlib import read_input, IntegrationDistance
from openquake.hazardlib.calc import gmf

CWD = os.path.dirname(__file__)
RUP_XML = os.path.join(CWD, 'data', 'rup.xml')


class ScenarioTestCase(unittest.TestCase):
    def test1rup(self):
        param = dict(inputs=dict(rupture_model=RUP_XML),
                     number_of_ground_motion_fields=10,
                     gsim='AtkinsonBoore2006',
                     ses_seed=42,
                     sites=[(0, 1), (0, 0)],
                     reference_vs30_value="760",
                     maximum_distance=IntegrationDistance.new('200'),
                     imtls={'PGA': [0]})
        inp = read_input(param)
        [ebr] = inp.group
        gc = gmf.GmfComputer(ebr, inp.sitecol, inp.cmaker)
        gmfdata = gc.compute_all()
        self.assertIn('sid', gmfdata)
        self.assertIn('eid', gmfdata)
        self.assertIn('rlz', gmfdata)
        self.assertIn('gmv_0', gmfdata)
