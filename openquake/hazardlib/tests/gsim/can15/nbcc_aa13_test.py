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
import numpy
import pandas
from openquake.hazardlib import read_input, IntegrationDistance, contexts
from openquake.hazardlib.calc import gmf

OVERWRITE = False
U32 = numpy.uint32
CWD = os.path.dirname(os.path.dirname(__file__))  # hazardlib/tests/gsim
# rupture around Vancouver (-123, 49)
RUP_XML = os.path.join(CWD, 'data', 'CAN15', 'rup.xml')
GLT_XML = os.path.join(CWD, 'data', 'CAN15', 'gmmLT.xml')


# it is hard to build a test like the others, since NBCC2015_AA13
# is parametric; it is easier to build a scenario using ALL of the
# combinations used in the Canada model 2015
class NBCC2015_AA13TestCase(unittest.TestCase):
    def test_gmf(self):
        param = dict(inputs=dict(rupture_model=RUP_XML,
                                 gsim_logic_tree=GLT_XML),
                     number_of_ground_motion_fields=1,
                     ses_seed=42,
                     sites=[(-123, 48), (-123, 48.5)],
                     reference_vs30_value="760",
                     maximum_distance=IntegrationDistance.new('200'),
                     imtls={'PGA': [0], 'SA(0.1)': [0], 'SA(0.2)': [0]})
        inp = read_input(param)
        [[ebr]] = inp.groups
        param['mags'] = ['%.2f' % ebr.rupture.mag]
        gsim_lt = inp.full_lt.gsim_lt
        for trt in gsim_lt.values:
            rbg = {gsim: U32([g]) for g, gsim in enumerate(gsim_lt.values[trt])}
            cmaker = contexts.ContextMaker(trt, rbg, param)
            cmaker.scenario = True
            ebr.n_occ = len(cmaker.gsims)
            gc = gmf.GmfComputer(ebr, inp.sitecol, cmaker)
            mean_stds = cmaker.get_mean_stds([gc.ctx])
            gmfdata = pandas.DataFrame(gc.compute_all(mean_stds))
            del gmfdata['rlz']  # the info is encoded in the eid
            fname = 'NBCC2015_AA13_%s.csv' % cmaker.trt.replace(' ', '')
            path = os.path.join(CWD, 'data', 'CAN15', fname)
            if OVERWRITE:
                gmfdata.to_csv(path, index=False, lineterminator='\r\n')
            else:
                expected = pandas.read_csv(path)
                for col in expected.columns:
                    numpy.testing.assert_allclose(
                        gmfdata[col].to_numpy(), expected[col].to_numpy(),
                        atol=1E-5)
