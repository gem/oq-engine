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

import os
import re
import unittest
import pandas as pd
import numpy
from openquake.hazardlib.const import TRT
from openquake.baselib import InvalidFile
from openquake.baselib.hdf5 import read_csv
from openquake.baselib.general import gettemp, DictArray
from openquake.hazardlib.site import ampcode_dt
from openquake.hazardlib.site_amplification import Amplifier
from openquake.hazardlib.probability_map import ProbabilityCurve
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
            poes, [0.981272, 0.975965, 0.96634, 0.937876, 0.886351, 0.790249,
                   0.63041], atol=1E-6)
        poes = a.amplify_one(b'A', 'SA(0.2)', self.hcurve[2]).flatten()
        numpy.testing.assert_allclose(
            poes, [0.981272, 0.975965, 0.96634, 0.937876, 0.886351, 0.790249,
                   0.63041], atol=1E-6)
        poes = a.amplify_one(b'A', 'SA(0.5)', self.hcurve[3]).flatten()
        numpy.testing.assert_allclose(
            poes, [0.981272, 0.975965, 0.96634, 0.937876, 0.886351, 0.790249,
                   0.63041], atol=1E-6)

    def test_simple(self):
        fname = gettemp(simple_ampl_func)
        df = read_csv(fname, {'ampcode': ampcode_dt, None: numpy.float64},
                      index='ampcode')
        a = Amplifier(self.imtls, df, self.soil_levels)
        # a.check(self.vs30, vs30_tolerance=1)
        poes = a.amplify_one(b'A', 'SA(0.1)', self.hcurve[1]).flatten()
        numpy.testing.assert_allclose(
            poes, [0.981141, 0.975771, 0.964955, 0.935616, 0.882413, 0.785659,
                   0.636667], atol=1e-6)

        poes = a.amplify_one(b'A', 'SA(0.2)', self.hcurve[2]).flatten()
        numpy.testing.assert_allclose(
            poes, [0.981141, 0.975771, 0.964955, 0.935616, 0.882413, 0.785659,
                   0.636667], atol=1e-6)

        poes = a.amplify_one(b'A', 'SA(0.5)', self.hcurve[3]).flatten()
        numpy.testing.assert_allclose(
            poes, [0.981681, 0.976563, 0.967238, 0.940109, 0.890456, 0.799286,
                   0.686047], atol=1e-6)

        # Amplify GMFs with sigmas
        rng = numpy.random.default_rng(42)
        gmvs = a._amplify_gmvs(
            b'A', numpy.array([.005, .010, .015]), 'PGA', rng)
        numpy.testing.assert_allclose(gmvs, [0.005298, 0.009463, 0.016876],
                                      atol=1E-5)

    def test_double(self):
        fname = gettemp(double_ampl_func)
        df = read_csv(fname, {'ampcode': ampcode_dt, None: numpy.float64},
                      index='ampcode')

        a = Amplifier(self.imtls, df, self.soil_levels)
        poes = a.amplify_one(b'A', 'SA(0.1)', self.hcurve[1]).flatten()
        numpy.testing.assert_allclose(
            poes, [0.985122, 0.979701, 0.975965, 0.96634, 0.922497, 0.886351,
                   0.790249], atol=1E-6)
        #    poes, [0.989, 0.985, 0.98, 0.97, 0.94, 0.89, 0.79], atol=1E-6)

        poes = a.amplify_one(b'A', 'SA(0.2)', self.hcurve[2]).flatten()
        numpy.testing.assert_allclose(
            poes, [0.985122, 0.979701, 0.975965, 0.96634, 0.922497, 0.886351,
                   0.790249], atol=1E-6)
        #    poes, [0.989, 0.985, 0.98, 0.97, 0.94, 0.89, 0.79], atol=1E-6)

        poes = a.amplify_one(b'A', 'SA(0.5)', self.hcurve[3]).flatten()
        numpy.testing.assert_allclose(
            poes, [0.985122, 0.979701, 0.975965, 0.96634, 0.922497, 0.886351,
                   0.790249], atol=1E-6)
        #    poes, [0.989, 0.985, 0.98, 0.97, 0.94, 0.89, 0.79], atol=1E-6)

        # amplify GMFs without sigmas
        rng = numpy.random.default_rng(42)
        gmvs = a._amplify_gmvs(b'A', numpy.array([.1, .2, .3]), 'SA(0.5)', rng)
        numpy.testing.assert_allclose(gmvs, [.2, .4, .6])

    def test_long_code(self):
        fname = gettemp(long_ampl_code)
        with self.assertRaises(InvalidFile) as ctx:
            read_csv(fname, {'ampcode': ampcode_dt, None: numpy.float64},
                     index='ampcode')
        self.assertIn("ampcode='long_code' has length 9 > 4",
                      str(ctx.exception))

    def test_dupl(self):
        fname = gettemp(dupl_ampl_func)
        df = read_csv(fname, {'ampcode': ampcode_dt, None: numpy.float64},
                      index='ampcode')
        with self.assertRaises(ValueError) as ctx:
            Amplifier(self.imtls, df, self.soil_levels)
        self.assertEqual(str(ctx.exception), "Found duplicates for b'A'")

    def test_resampling(self):
        path = os.path.dirname(os.path.abspath(__file__))

        # Read AF
        f_af = os.path.join(path, 'data', 'convolution', 'amplification.csv')
        df_af = read_csv(f_af, {'ampcode': ampcode_dt, None: numpy.float64},
                         index='ampcode')

        # Read hc
        f_hc = os.path.join(path, 'data', 'convolution', 'hazard_curve.csv')
        df_hc = pd.read_csv(f_hc, skiprows=1)

        # Get imls from the hc
        imls = []
        pattern = 'poe-(\\d*\\.\\d*)'
        for k in df_hc.columns:
            m = re.match(pattern, k)
            if m:
                imls.append(float(m.group(1)))
        imtls = DictArray({'PGA': imls})

        # Create a list with one ProbabilityCurve instance
        poes = numpy.squeeze(df_hc.iloc[0, 3:].to_numpy())
        tmp = numpy.expand_dims(poes, 1)
        pcurve = ProbabilityCurve(tmp)

        soil_levels = numpy.array(list(numpy.geomspace(0.001, 2, 50)))
        a = Amplifier(imtls, df_af, soil_levels)
        res = a.amplify(b'MQ15', pcurve)

        tmp = 'hazard_curve_expected.csv'
        fname_expected = os.path.join(path, 'data', 'convolution', tmp)
        expected = numpy.loadtxt(fname_expected)

        numpy.testing.assert_allclose(numpy.squeeze(res.array), expected)

    def test_gmf_with_uncertainty(self):
        fname = gettemp(gmf_ampl_func)
        df = read_csv(fname, {'ampcode': ampcode_dt, None: numpy.float64},
                      index='ampcode')
        imtls = DictArray({'PGA': self.imls})
        a = Amplifier(imtls, df)
        res = []
        nsim = 10000
        rng = numpy.random.default_rng(42)
        for i in range(nsim):
            gmvs = a._amplify_gmvs(b'A', numpy.array([.1, .2, .3]), 'PGA', rng)
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

        rng = numpy.random.default_rng(42)
        gmvs1 = a._amplify_gmvs(b'z1', numpy.array([.1, .2, .3]), 'PGA', rng)
        aac(gmvs1, [0.201073, 0.278387, 0.627798], atol=1E-5)
        gmvs2 = a._amplify_gmvs(b'z2', numpy.array([.1, .2, .3]), 'PGA', rng)
        aac(gmvs2, [0.211233, 0.168165, 0.333235], atol=1E-5)

        rng = numpy.random.default_rng(43)  # new seed, big diff
        gmvs1 = a._amplify_gmvs(b'z1', numpy.array([.1, .2, .3]), 'PGA', rng)
        aac(gmvs1, [0.196267, 0.553508, 0.367905], atol=1E-5)
        gmvs2 = a._amplify_gmvs(b'z2', numpy.array([.1, .2, .3]), 'PGA', rng)
        aac(gmvs2, [0.100813, 0.165443, 0.827468], atol=1E-5)
