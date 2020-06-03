# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2020, GEM Foundation
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

import numpy
import unittest

from openquake.baselib import InvalidFile
from openquake.baselib.hdf5 import read_csv
from openquake.baselib.general import gettemp, DictArray
from openquake.hazardlib.site import ampcode_dt
from openquake.hazardlib.site_amplification import AmplFunction

ampl_func = '''\
#,,,,,,,"vs30_ref=760"
ampcode,from_mag,from_rrup,level,PGA,SA(1.0),sigma_PGA,sigma_SA(1.0)
A,      4.0,      0.0,     0.001,1.0,1.0,    0.3,      0.2
A,      4.0,      0.0,     0.010,1.0,1.0,    0.3,      0.2
A,      4.0,      0.0,     0.050,1.0,1.0,    0.3,      0.2
A,      4.0,      0.0,     0.100,1.0,1.0,    0.3,      0.2
A,      4.0,      0.0,     0.500,1.0,1.0,    0.3,      0.2
A,      4.0,      0.0,     1.000,1.0,1.0,    0.3,      0.2
A,      5.5,      0.0,     0.001,1.0,1.0,    0.3,      0.2
A,      5.5,      0.0,     0.010,1.0,1.0,    0.3,      0.2
A,      5.5,      0.0,     0.050,1.0,1.0,    0.3,      0.2
A,      5.5,      0.0,     0.100,1.0,1.0,    0.3,      0.2
A,      5.5,      0.0,     0.500,1.0,1.0,    0.3,      0.2
A,      5.5,      0.0,     1.000,1.0,1.0,    0.3,      0.2
A,      4.0,     20.0,     0.001,1.0,1.0,    0.3,      0.2
A,      4.0,     20.0,     0.010,1.0,1.0,    0.3,      0.2
A,      4.0,     20.0,     0.050,1.0,1.0,    0.3,      0.2
A,      4.0,     20.0,     0.100,1.0,1.0,    0.3,      0.2
A,      4.0,     20.0,     0.500,1.0,1.0,    0.3,      0.2
A,      4.0,     20.0,     1.000,1.0,1.0,    0.3,      0.2
A,      5.5,     20.0,     0.001,1.0,1.0,    0.3,      0.2
A,      5.5,     20.0,     0.010,1.0,1.0,    0.3,      0.2
A,      5.5,     20.0,     0.050,1.0,1.0,    0.3,      0.2
A,      5.5,     20.0,     0.100,1.0,1.0,    0.3,      0.2
A,      5.5,     20.0,     0.500,1.0,1.0,    0.3,      0.2
A,      5.5,     20.0,     1.000,1.0,1.0,    0.3,      0.2
B,      4.0,      0.0,     0.001,1.0,1.0,    0.3,      0.2
B,      4.0,      0.0,     0.010,1.0,1.0,    0.3,      0.2
B,      4.0,      0.0,     0.050,1.0,1.0,    0.3,      0.2
B,      4.0,      0.0,     0.100,1.0,1.0,    0.3,      0.2
B,      4.0,      0.0,     0.500,1.0,1.0,    0.3,      0.2
B,      4.0,      0.0,     1.000,1.0,1.0,    0.3,      0.2
B,      5.5,      0.0,     0.001,1.0,1.0,    0.3,      0.2
B,      5.5,      0.0,     0.010,1.0,1.0,    0.3,      0.2
B,      5.5,      0.0,     0.050,1.0,1.0,    0.3,      0.2
B,      5.5,      0.0,     0.100,1.0,1.0,    0.3,      0.2
B,      5.5,      0.0,     0.500,1.0,1.0,    0.3,      0.2
B,      5.5,      0.0,     1.000,1.0,1.0,    0.3,      0.2
B,      4.0,     20.0,     0.001,1.0,1.0,    0.3,      0.2
B,      4.0,     20.0,     0.010,1.0,1.0,    0.3,      0.2
B,      4.0,     20.0,     0.050,1.0,1.0,    0.3,      0.2
B,      4.0,     20.0,     0.100,1.0,1.0,    0.3,      0.2
B,      4.0,     20.0,     0.500,1.0,1.0,    0.3,      0.2
B,      4.0,     20.0,     1.000,1.0,1.0,    0.3,      0.2
B,      5.5,     20.0,     0.001,1.0,1.0,    0.3,      0.2
B,      5.5,     20.0,     0.010,1.0,1.0,    0.3,      0.2
B,      5.5,     20.0,     0.050,1.0,1.0,    0.3,      0.2
B,      5.5,     20.0,     0.100,1.0,1.0,    0.3,      0.2
B,      5.5,     20.0,     0.500,1.0,1.0,    0.3,      0.2
B,      5.5,     20.0,     1.000,1.0,1.0,    0.3,      0.2
'''


class AmplificationFunctionTestCase(unittest.TestCase):

    def setUp(self):
        fname = gettemp(ampl_func)
        df = read_csv(fname, {'ampcode': ampcode_dt, None: numpy.float64},
                      index='ampcode')
        df.reset_index(drop=False, inplace=True)
        self.af = AmplFunction.from_compact(df)

    def test_filter_00(self):
        pass

    def test_get_max_sigma(self):
        msg = 'Getting wrong max sigma'
        computed = self.af.get_max_sigma()
        self.assertEqual(computed, 0.3, msg)

    def test_get_median_std(self):
        site = b'A'
        mag = 4.5
        imt = 'PGA'
        imls = [0.1, 0.4, 0.3]
        rrups = [10., 15., 25.]
        self.af.get_mean_std(site, imt, imls, mag, rrups)
