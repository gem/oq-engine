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
A,      4.0,      0.0,     0.001,1.00,1.0,    0.30,      0.2
A,      4.0,      0.0,     0.010,1.10,1.0,    0.30,      0.2
A,      4.0,      0.0,     0.050,1.20,1.0,    0.30,      0.2
A,      4.0,      0.0,     0.100,1.30,1.0,    0.30,      0.2
A,      4.0,      0.0,     0.500,1.40,1.0,    0.30,      0.2
A,      4.0,      0.0,     1.000,1.50,1.0,    0.30,      0.2
A,      5.5,      0.0,     0.002,1.01,1.0,    0.31,      0.2
A,      5.5,      0.0,     0.012,1.11,1.0,    0.31,      0.2
A,      5.5,      0.0,     0.052,1.21,1.0,    0.31,      0.2
A,      5.5,      0.0,     0.102,1.31,1.0,    0.31,      0.2
A,      5.5,      0.0,     0.502,1.41,1.0,    0.31,      0.2
A,      5.5,      0.0,     1.002,1.51,1.0,    0.31,      0.2
A,      4.0,     20.0,     0.003,1.02,1.0,    0.32,      0.2
A,      4.0,     20.0,     0.013,1.12,1.0,    0.32,      0.2
A,      4.0,     20.0,     0.053,1.22,1.0,    0.32,      0.2
A,      4.0,     20.0,     0.103,1.32,1.0,    0.32,      0.2
A,      4.0,     20.0,     0.503,1.42,1.0,    0.32,      0.2
A,      4.0,     20.0,     1.003,1.52,1.0,    0.32,      0.2
A,      5.5,     20.0,     0.004,1.03,1.0,    0.33,      0.2
A,      5.5,     20.0,     0.014,1.13,1.0,    0.33,      0.2
A,      5.5,     20.0,     0.054,1.23,1.0,    0.33,      0.2
A,      5.5,     20.0,     0.104,1.33,1.0,    0.33,      0.2
A,      5.5,     20.0,     0.504,1.43,1.0,    0.33,      0.2
A,      5.5,     20.0,     1.004,1.53,1.0,    0.33,      0.2
B,      4.0,      0.0,     0.001,1.0,1.0,    0.3,      0.2
B,      4.0,      0.0,     0.010,1.1,1.0,    0.3,      0.2
B,      4.0,      0.0,     0.050,1.2,1.0,    0.3,      0.2
B,      4.0,      0.0,     0.100,1.3,1.0,    0.3,      0.2
B,      4.0,      0.0,     0.500,1.4,1.0,    0.3,      0.2
B,      4.0,      0.0,     1.000,1.5,1.0,    0.3,      0.2
B,      5.5,      0.0,     0.001,1.0,1.0,    0.3,      0.2
B,      5.5,      0.0,     0.010,1.1,1.0,    0.3,      0.2
B,      5.5,      0.0,     0.050,1.2,1.0,    0.3,      0.2
B,      5.5,      0.0,     0.100,1.3,1.0,    0.3,      0.2
B,      5.5,      0.0,     0.500,1.4,1.0,    0.3,      0.2
B,      5.5,      0.0,     1.000,1.5,1.0,    0.3,      0.2
B,      4.0,     20.0,     0.001,1.0,1.0,    0.3,      0.2
B,      4.0,     20.0,     0.010,1.1,1.0,    0.3,      0.2
B,      4.0,     20.0,     0.050,1.2,1.0,    0.3,      0.2
B,      4.0,     20.0,     0.100,1.3,1.0,    0.3,      0.2
B,      4.0,     20.0,     0.500,1.4,1.0,    0.3,      0.2
B,      4.0,     20.0,     1.000,1.5,1.0,    0.3,      0.2
B,      5.5,     20.0,     0.001,1.0,1.0,    0.3,      0.2
B,      5.5,     20.0,     0.010,1.1,1.0,    0.3,      0.2
B,      5.5,     20.0,     0.050,1.2,1.0,    0.3,      0.2
B,      5.5,     20.0,     0.100,1.3,1.0,    0.3,      0.2
B,      5.5,     20.0,     0.500,1.4,1.0,    0.3,      0.2
B,      5.5,     20.0,     1.000,1.5,1.0,    0.31,      0.2
'''


class AmplificationFunctionTestCase(unittest.TestCase):

    def setUp(self):
        fname = gettemp(ampl_func)
        df = read_csv(fname, {'ampcode': ampcode_dt, None: numpy.float64},
                      index='ampcode')
        self.af = AmplFunction.from_dframe(df)

    def test_get_max_sigma(self):
        """ Calculation of mmax """
        msg = 'Getting wrong max sigma'
        computed = self.af.get_max_sigma()
        self.assertEqual(computed, 0.33, msg)

    def test_get_median_std01(self):
        """ Calculation of median amplification + std """
        site = b'A'
        mag = 4.5
        imt = 'PGA'
        imls = 0.1
        rrups = 10.
        med, std = self.af.get_mean_std(site, imt, imls, mag, rrups)
        self.assertEqual(med, 1.30, 'wrong median af')
        self.assertEqual(std, 0.3, 'wrong std af')

    def test_get_median_std02(self):
        """ Calculation of median amplification + std """
        site = b'A'
        mag = 6.0
        imt = 'PGA'
        imls = 0.104
        rrups = 22.
        med, std = self.af.get_mean_std(site, imt, imls, mag, rrups)
        self.assertEqual(med, 1.33, 'wrong median af')
        self.assertEqual(std, 0.33, 'wrong std af')
