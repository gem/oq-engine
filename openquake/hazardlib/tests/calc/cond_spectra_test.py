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
import numpy as np
from numpy.testing import assert_allclose as aac
import pandas
from openquake.baselib.general import AccumDict
from openquake.hazardlib import read_input, valid, contexts
from openquake.hazardlib.cross_correlation import BakerJayaram2008
from openquake.hazardlib.calc.filters import IntegrationDistance

OVERWRITE_EXPECTED = False

CWD = os.path.dirname(__file__)
SOURCES_XML = os.path.join(CWD, 'data', 'sm01.xml')
GSIM_XML = os.path.join(CWD, 'data', 'lt02.xml')
PARAM = dict(source_model_file=SOURCES_XML,
             gsim_logic_tree_file=GSIM_XML,
             sites=[(0, -0.8)],
             reference_vs30_value=600,
             reference_depth_to_2pt5km_per_sec=5,
             reference_depth_to_1pt0km_per_sec=100,
             maximum_distance=IntegrationDistance.new('200'),
             rupture_mesh_spacing=5.,
             width_of_mfd_bin=1.,
             investigation_time=1,
             truncation_level=3,
             cross_correl=BakerJayaram2008(),
             imtls={"SA(0.05)": valid.logscale(0.005, 2.13, 45),
                    "SA(0.075)": valid.logscale(0.005, 2.13, 45),
                    "SA(0.1)": valid.logscale(0.005, 2.13, 45),
                    "SA(0.15)": valid.logscale(0.005, 2.13, 45),
                    "SA(0.2)": valid.logscale(0.005, 2.13, 45),
                    "SA(0.25)": valid.logscale(0.005, 2.13, 45),
                    "SA(0.3)": valid.logscale(0.005, 2.13, 45),
                    "SA(0.5)": valid.logscale(0.005, 2.13, 45),
                    "SA(0.75)": valid.logscale(0.005, 2.13, 45),
                    "SA(1.0)": valid.logscale(0.005, 2.13, 45),
                    "SA(2.0)": valid.logscale(0.005, 2.13, 45)})
imti = 4  # corresponds to SA(0.2)
imls = [np.log(1.001392E-01)]


# useful while debugging
def plot(df, imts):
    import matplotlib.pyplot as plt
    periods = [im.period for im in imts]
    fig, axs = plt.subplots(1, 2)
    axs[0].plot(periods, df.cs_exp, 'x-')
    axs[1].plot(periods, df.cs_std, 'x-')
    axs[0].grid(which='both')
    axs[1].grid(which='both')
    axs[0].set_xscale('log')
    axs[1].set_xscale('log')
    axs[0].set_yscale('log')
    axs[0].set_ylim([1e-3, 10])
    axs[0].set_xlabel('Mean spectrum, Period[s]')
    axs[1].set_xlabel('Std spectrum, Period[s]')
    plt.show()


# used to create the expected file the first time
def csdic_to_dframe(csdic, imts, n, p):
    """
    :param csdic: a double dictionary g_ -> key -> array
    :param imts: M intensity measure types
    :param rlzs: R realization indices
    :param n: an index in the range 0..N-1 where N is the number of sites
    :param p: an index in the range 0..P-1 where P is the number of IMLs
    """
    dic = dict(rlz_id=[], period=[], cs_exp=[], cs_std=[])
    for r, cs in csdic.items():
        c = cs['_c']
        s = cs['_s']
        for m, imt in enumerate(imts):
            dic['rlz_id'].append(r)
            dic['period'].append(imt.period)
            dic['cs_exp'].append(np.exp(c[m, n, 0, p] / s[n, p]))
            dic['cs_std'].append(np.sqrt(c[m, n, 1, p] / s[n, p]))
    return pandas.DataFrame(dic)


class CondSpectraTestCase(unittest.TestCase):

    def test_point(self):
        # point source with 3 ruptures and 2 sites, checking additivity
        inp = read_input(
            PARAM, source_model_file=os.path.join(CWD, 'data', 'point.xml'),
            gsim_logic_tree_file=os.path.join(CWD, 'data', 'lt01.xml'),
            sites=[(0, -0.8), (0, -0.4)])
        [cmaker] = inp.cmakerdict.values()
        [src_group] = inp.groups
        ctxs = cmaker.from_srcs(src_group, inp.sitecol)
        aac([ctx.occurrence_rate for ctx in ctxs], [0.00018, 0.00018, 0.00054])
        ctxs1 = ctxs[:2]
        ctxs2 = ctxs[2:]

        # check that the total spectra is a weighted mean of the two
        # rupture spectra; the weight is the same for all IMTs
        c1, s1 = cmaker.get_cs_contrib(ctxs1, imti, imls)[0].values()
        c2, s2 = cmaker.get_cs_contrib(ctxs2, imti, imls)[0].values()
        c, s = cmaker.get_cs_contrib(ctxs, imti, imls)[0].values()
        for n in [0, 1]:  # two sites
            comp_spectra = (c1[:, n] + c2[:, n]) / (s1[n, 0] + s2[n, 0])
            aac(comp_spectra, c[:, n] / s[n, 0])

    def test_1_rlz(self):
        # test with one GMPE, 1 TRT, checking additivity
        inp = read_input(
            PARAM, gsim_logic_tree_file=os.path.join(CWD, 'data', 'lt01.xml'))
        [cmaker] = inp.cmakerdict.values()
        [src_group] = inp.groups
        ctxs = cmaker.from_srcs(src_group, inp.sitecol)
        assert len(ctxs) == 100
        ctxs1 = ctxs[:50]
        ctxs2 = ctxs[50:]

        dic1 = cmaker.get_cs_contrib(ctxs1, imti, imls)[0]
        dic2 = cmaker.get_cs_contrib(ctxs2, imti, imls)[0]
        dic = cmaker.get_cs_contrib(ctxs, imti, imls)[0]
        aac((dic1['_c'] + dic2['_c']) / (dic1['_s'] + dic2['_s']),
            dic['_c'] / dic['_s'])

    def test_2_rlzs(self):
        # test with two GMPEs, 1 TRT
        inp = read_input(PARAM)
        [cmaker] = inp.cmakerdict.values()
        [src_group] = inp.groups
        ctxs = cmaker.from_srcs(src_group, inp.sitecol)
        csdic = cmaker.get_cs_contrib(ctxs, imti, imls)
        df = csdic_to_dframe(csdic, cmaker.imts, 0, 0)

        # check the result
        expected = os.path.join(CWD, 'expected', 'spectra2.csv')
        if OVERWRITE_EXPECTED:
            df.to_csv(expected, index=False, line_terminator='\r\n',
                      float_format='%.6f')
        expdf = pandas.read_csv(expected)
        pandas.testing.assert_frame_equal(df, expdf, atol=1E-6)
        # to plot the spectra uncomment the following line
        # plot(df, cmaker.imts)

    def test_6_rlzs(self):
        # test with 2x3 realizations and TRTA, TRTB
        # rlzs_by_g = 012, 345, 03, 14, 25
        inp = read_input(
            PARAM, source_model_file=os.path.join(CWD, 'data', 'sm02.xml'))
        R = inp.gsim_lt.get_num_paths()

        # compute the contributions by trt
        tot = AccumDict()  # g_ -> key -> array
        for src_group in inp.groups:
            cmaker = inp.cmakerdict[src_group.trt]
            ctxs = cmaker.from_srcs(src_group, inp.sitecol)
            tot += cmaker.get_cs_contrib(ctxs, imti, imls)

        # compose the contributions by rlz, 0+2, 0+3, 0+4, 1+2, 1+3, 1+4
        rlzs_by_g = inp.gsim_lt.get_rlzs_by_g()
        csdic = contexts.csdict(len(cmaker.imts), 1, 1, 0, R)
        for g_, rlz_ids in enumerate(rlzs_by_g):
            for r in rlz_ids:
                csdic[r] += tot[g_]
        df = csdic_to_dframe(csdic, cmaker.imts, 0, 0)

        # check the results
        expected = os.path.join(CWD, 'expected', 'spectra6.csv')
        if OVERWRITE_EXPECTED:
            df.to_csv(expected, index=False, line_terminator='\r\n',
                      float_format='%.6f')
        expdf = pandas.read_csv(expected)
        pandas.testing.assert_frame_equal(df, expdf, atol=1E-6)

        # to plot the spectra uncomment the following line
        # plot(df, cmaker.imts)
