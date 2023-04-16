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
import numpy as np
import unittest
from openquake.hazardlib.calc import gmf
from openquake.hazardlib import read_input, IntegrationDistance

CWD = os.path.dirname(__file__)
RUP_XML = os.path.join(CWD, 'data', 'rup.xml')


class GmfTestCase(unittest.TestCase):

    def test01(self):
        param = dict(inputs=dict(rupture_model=RUP_XML),
                     number_of_ground_motion_fields=400,
                     gsim='ZhaoEtAl2006Asc',
                     ses_seed=42,
                     sites=[(0, 0.05), (0, 0), (0, -0.05)],
                     reference_vs30_value="300.0",
                     maximum_distance=IntegrationDistance.new('200'),
                     imtls={'PGA': [0],
                            'SA(0.2)': [0]})
        inp = read_input(param)
        # This is an event based rupture. The truncation level in the
        # cmaker is 99. The mesh of the rupture has all longitudes = 0 i.e.
        # it has strike = 0. The rupture breaks the surface.
        [ebr] = inp.group
        gc = gmf.GmfComputer(ebr, inp.sitecol, inp.cmaker)
        # `gmfdata` is an `openquake.baselib.general.AccumDict` instance with
        # keys ['sid', 'eid', 'rlz', 'gmv_0', 'gmv_1']

        gmfdata = gc.compute_all()
        # TODO: I do not understand why len(gmfdata['gmv_1']) gives me 200.
        # I would expect to get 100

        thresholds = [3.0, 12.0]
        num_imts = len(param['imtls'])

        mask = get_mask(gmfdata, thresholds, num_imts)
        while np.sum(~mask) > 0:
            tmp_gmfd = gc.compute_all()
            tmp_mask = get_mask(tmp_gmfd, thresholds, num_imts)
            replace(gmfdata, tmp_gmfd, mask, tmp_mask, num_imts)

        self.assertIn('sid', gmfdata)
        self.assertIn('eid', gmfdata)
        self.assertIn('rlz', gmfdata)
        self.assertIn('gmv_0', gmfdata)


def get_mask(gmfdata, thresholds, num_imts):
    mask = np.ones_like(gmfdata['gmv_0'], dtype=bool)
    for i in range(num_imts):
        tmp = np.array(gmfdata[f'gmv_{i}']) < thresholds[i]
        mask = np.logical_and(mask, tmp)
    return mask

def replace(gmfd0, gmfd1, mask0, mask1, num_imts):
    imax = np.min([np.sum(~mask0), np.sum(mask1)])
    i0 = np.where(~mask0)[0]
    i1 = np.where(mask1)[0]
    for i in range(num_imts):
        a0 = np.array(gmfd0[f'gmv_{i}'])
        a1 = np.array(gmfd1[f'gmv_{i}'])
        a0[i0[:imax]] = a1[i1[:imax]]
        gmfd0[f'gmv_{i}'] = list(a0)
    mask0[i0] = True
