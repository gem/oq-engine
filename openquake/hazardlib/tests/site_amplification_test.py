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

import unittest
import numpy
from openquake.hazardlib.const import TRT
from openquake.baselib import InvalidFile
from openquake.baselib.hdf5 import read_csv
from openquake.baselib.general import gettemp, DictArray
from openquake.hazardlib.site import ampcode_dt
from openquake.hazardlib.site_amplification import Amplifier
from openquake.hazardlib.gsim.boore_atkinson_2008 import BooreAtkinson2008

aac = numpy.testing.assert_allclose

trivial_ampl_func = '''\
#,,,,,,"vs30_ref=760"
ampcode,PGA,SA(0.1),SA(0.2),SA(0.5),SA(1.5)
A,1,1,1,1,1
'''

simple_ampl_func = '''\
#,,,,,,,"vs30_ref=760"
ampcode,level,PGA,SA(0.1),SA(0.2),SA(0.5),SA(1.5),sigma_PGA,sigma_SA(0.1),sigma_SA(0.2),sigma_SA(0.5),sigma_SA(1.5)
A,.001,1.01,1,1,1.1,1.1,.1,.1,.1,.1,.1
A,.01,1.05,1,1,1.1,1.1,.1,.1,.1,.1,.1
A,.05,1,1,1,1.1,1.1,.1,.1,.1,.1,.1
A,.1,1,1,1,1.1,1.1,.1,.1,.1,.1,.1
A,.2,1,1,1,1.1,1.1,.1,.1,.1,.1,.1
A,.5,1,1,1,1.1,1.1,.1,.1,.1,.1,.1
A,1.,1,1,1,1.1,1.1,.1,.1,.1,.1,.1
A,1.21,1,1,1,1.1,1.1,.1,.1,.1,.1,.1
'''

double_ampl_func = '''\
#,,,,,,,"vs30_ref=760"
ampcode,PGA,SA(0.1),SA(0.2),SA(0.5),SA(1.0)
A,2,2,2,2,2
'''

long_ampl_code = '''\
#,,,,,,,"vs30_ref=760"
ampcode,PGA,SA(0.3),SA(0.6),SA(1.0),SA(1.5)
long_code,2,2,2,2,2
'''

dupl_ampl_func = '''\
#,,,,,,,"vs30_ref=760"
ampcode,PGA,SA(0.3),SA(0.6),SA(1.0),SA(1.5)
A,2,2,2,2,2
A,1,2,2,2,2
'''

gmf_ampl_func = '''#,,,,,,"vs30_ref=760"
ampcode,PGA,sigma_PGA
A,1,0.3
'''


# provided by Catalina
cata_ampl_func = '''\
#,,,,,"vs30_ref=760"
ampcode,level,PGA,SA(0.3),sigma_PGA,sigma_SA(0.3)
z1,0.050,1.45,2.22,0.4,0.4
z1,0.100,1.78,1.87,0.4,0.4
z1,0.200,2.11,2.66,0.4,0.4
z1,0.300,1.55,1.59,0.4,0.4
z2,0.075,1.33,1.79,0.4,0.4
z2,0.150,1.69,2.42,0.4,0.4
z2,0.250,1.98,2.58,0.4,0.4
z2,0.350,1.76,1.80,0.4,0.4
'''


class AmplifierTestCase(unittest.TestCase):
    vs30 = numpy.array([760])
    imls = [.001, .002, .005, .01, .02, .05, .1, .2, .5, 1., 1.2]
    soil_levels = numpy.array([.002, .005, .01, .02, .05, .1, .2])
    imtls = DictArray({'PGA': imls, 'SA(0.1)': imls, 'SA(0.2)': imls,
                       'SA(0.5)': imls})
    hcurve = [[.999, .995, .99, .98, .95, .9, .8, .7, .1, .05, .01],  # PGA
              [.999, .995, .99, .98, .95, .9, .8, .7, .1, .05, .01],  # SA(0.1)
              [.999, .995, .99, .98, .95, .9, .8, .7, .1, .05, .01],  # SA(0.2)
              [.999, .995, .99, .98, .95, .9, .8, .7, .1, .05, .01]]  # SA(0.5)

    def test_trivial(self):
        # using the heaviside function, i.e. `amplify_one` has contributions
        # only for soil_intensity < a * mid_intensity with a=1
        # in this case the minimimum mid_intensity is 0.0015 which is
        # smaller than the minimum soil intensity 0.0020, so some contribution
        # is lost and this is the reason why the first poe in 0.985
        # instead of 0.989
        fname = gettemp(trivial_ampl_func)
        df = read_csv(fname, {'ampcode': ampcode_dt, None: numpy.float64},
                      index='ampcode')
        a = Amplifier(self.imtls, df, self.soil_levels)
        gmm = BooreAtkinson2008()
        a.check(self.vs30, 0, {TRT.ACTIVE_SHALLOW_CRUST: [gmm]})
        numpy.testing.assert_allclose(
            a.midlevels, [0.0015, 0.0035, 0.0075, 0.015, 0.035, 0.075,
                          0.15, 0.35, 0.75, 1.1])
        poes = a.amplify_one(b'A', 'SA(0.1)', self.hcurve[1]).flatten()
        numpy.testing.assert_allclose(
            poes, [0.985, 0.98, 0.97, 0.94, 0.89, 0.79, 0.69],
            atol=1E-6)
        poes = a.amplify_one(b'A', 'SA(0.2)', self.hcurve[2]).flatten()
        numpy.testing.assert_allclose(
            poes, [0.985, 0.98, 0.97, 0.94, 0.89, 0.79, 0.69],
            atol=1E-6)
        poes = a.amplify_one(b'A', 'SA(0.5)', self.hcurve[3]).flatten()
        numpy.testing.assert_allclose(
            poes, [0.985, 0.98, 0.97, 0.94, 0.89, 0.79, 0.69],
            atol=1E-6)

    def test_simple(self):
        #
        # MP: checked using hand calculations some values of the poes computed
        # considering uncertainty
        #
        fname = gettemp(simple_ampl_func)
        df = read_csv(fname, {'ampcode': ampcode_dt, None: numpy.float64},
                      index='ampcode')
        a = Amplifier(self.imtls, df, self.soil_levels)
        # a.check(self.vs30, vs30_tolerance=1)
        poes = a.amplify_one(b'A', 'SA(0.1)', self.hcurve[1]).flatten()
        numpy.testing.assert_allclose(
            poes, [0.985008, 0.980001, 0.970019, 0.94006, 0.890007, 0.790198,
                   0.690201], atol=1E-6)

        poes = a.amplify_one(b'A', 'SA(0.2)', self.hcurve[2]).flatten()
        numpy.testing.assert_allclose(
            poes, [0.985008, 0.980001, 0.970019, 0.94006, 0.890007, 0.790198,
                   0.690201], atol=1E-6)

        poes = a.amplify_one(b'A', 'SA(0.5)', self.hcurve[3]).flatten()
        numpy.testing.assert_allclose(
            poes, [0.985109, 0.980022, 0.970272, 0.940816, 0.890224, 0.792719,
                   0.692719], atol=1E-6)

        # Amplify GMFs with sigmas
        numpy.random.seed(42)
        gmvs = a._amplify_gmvs(b'A', numpy.array([.005, .010, .015]), 'PGA')
        numpy.testing.assert_allclose(gmvs, [0.005401, 0.010356, 0.016704],
                                      atol=1E-5)

    def test_double(self):
        fname = gettemp(double_ampl_func)
        df = read_csv(fname, {'ampcode': ampcode_dt, None: numpy.float64},
                      index='ampcode')

        a = Amplifier(self.imtls, df, self.soil_levels)
        poes = a.amplify_one(b'A', 'SA(0.1)', self.hcurve[1]).flatten()
        numpy.testing.assert_allclose(
            poes, [0.989, 0.985, 0.98, 0.97, 0.94, 0.89, 0.79], atol=1E-6)

        poes = a.amplify_one(b'A', 'SA(0.2)', self.hcurve[2]).flatten()
        numpy.testing.assert_allclose(
            poes, [0.989, 0.985, 0.98, 0.97, 0.94, 0.89, 0.79], atol=1E-6)

        poes = a.amplify_one(b'A', 'SA(0.5)', self.hcurve[3]).flatten()
        numpy.testing.assert_allclose(
            poes, [0.989, 0.985, 0.98, 0.97, 0.94, 0.89, 0.79], atol=1E-6)

        # amplify GMFs without sigmas
        gmvs = a._amplify_gmvs(b'A', numpy.array([.1, .2, .3]), 'SA(0.5)')
        numpy.testing.assert_allclose(gmvs, [.2, .4, .6])

    def test_long_code(self):
        fname = gettemp(long_ampl_code)
        with self.assertRaises(InvalidFile) as ctx:
            read_csv(fname, {'ampcode': ampcode_dt, None: numpy.float64},
                     index='ampcode')
        self.assertIn("line 3: ampcode='long_code' has length 9 > 4",
                      str(ctx.exception))

    def test_dupl(self):
        fname = gettemp(dupl_ampl_func)
        df = read_csv(fname, {'ampcode': ampcode_dt, None: numpy.float64},
                      index='ampcode')
        with self.assertRaises(ValueError) as ctx:
            Amplifier(self.imtls, df, self.soil_levels)
        self.assertEqual(str(ctx.exception), "Found duplicates for b'A'")

    def test_gmf_with_uncertainty(self):
        fname = gettemp(gmf_ampl_func)
        df = read_csv(fname, {'ampcode': ampcode_dt, None: numpy.float64},
                      index='ampcode')
        imtls = DictArray({'PGA': self.imls})
        a = Amplifier(imtls, df)
        res = []
        nsim = 10000
        numpy.random.seed(42)  # must be fixed
        for i in range(nsim):
            gmvs = a._amplify_gmvs(b'A', numpy.array([.1, .2, .3]), 'PGA')
            res.append(list(gmvs))
        res = numpy.array(res)
        dat = numpy.reshape(numpy.tile([.1, .2, .3], nsim), (nsim, 3))
        computed = numpy.std(numpy.log(res/dat), axis=0)
        expected = numpy.array([0.3, 0.3, 0.3])
        msg = "Computed and expected std do not match"
        numpy.testing.assert_almost_equal(computed, expected, 2, err_msg=msg)

    def test_gmf_cata(self):
        fname = gettemp(cata_ampl_func)
        df = read_csv(fname, {'ampcode': ampcode_dt, None: numpy.float64},
                      index='ampcode')
        imtls = DictArray({'PGA': [numpy.nan]})
        a = Amplifier(imtls, df)

        numpy.random.seed(42)  # must be fixed
        gmvs1 = a._amplify_gmvs(b'z1', numpy.array([.1, .2, .3]), 'PGA')
        aac(gmvs1, [0.217124, 0.399295, 0.602515], atol=1E-5)
        gmvs2 = a._amplify_gmvs(b'z2', numpy.array([.1, .2, .3]), 'PGA')
        aac(gmvs2, [0.266652, 0.334187, 0.510845], atol=1E-5)

        numpy.random.seed(43)  # changing the seed the results change a lot
        gmvs1 = a._amplify_gmvs(b'z1', numpy.array([.1, .2, .3]), 'PGA')
        aac(gmvs1, [0.197304, 0.293422, 0.399669], atol=1E-5)
        gmvs2 = a._amplify_gmvs(b'z2', numpy.array([.1, .2, .3]), 'PGA')
        aac(gmvs2, [0.117069, 0.517284, 0.475571], atol=1E-5)
