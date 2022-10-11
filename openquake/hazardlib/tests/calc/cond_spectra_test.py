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
from openquake.hazardlib import read_input, valid
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
poes = [0.000404]


# useful while debugging
def plot(df, imts):
    import matplotlib.pyplot as plt
    periods = [im.period for im in imts]
    fig, axs = plt.subplots(1, 2)
    axs[0].plot(df.period[:11], df.cs_exp[:11], 'x-')
    axs[0].plot(df.period[11:], df.cs_exp[11:], 'x-')
    axs[1].plot(df.period[:11], df.cs_std[:11], 'x-')
    axs[1].plot(df.period[11:], df.cs_std[11:], 'x-')
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

    def test_1_rlz(self):
        # test with one GMPE, 1 TRT, checking additivity
        inp = read_input(
            PARAM, gsim_logic_tree_file=os.path.join(CWD, 'data', 'lt01.xml'))
        [cmaker] = inp.cmakerdict.values()
        [src_group] = inp.groups
        [ctx] = cmaker.from_srcs(src_group, inp.sitecol)
        assert len(ctx) == 100
        ctx1 = ctx[:50]
        ctx2 = ctx[50:]

        # The hazard for the target IMT and poe
        poes = [0.000404]
        imls = [0.394359437]

        dic1 = cmaker.get_cs_contrib(ctx1, imti, imls, poes)[0]
        dic2 = cmaker.get_cs_contrib(ctx2, imti, imls, poes)[0]
        dic = cmaker.get_cs_contrib(ctx, imti, imls, poes)[0]
        aac((dic1['_c'] + dic2['_c']) / (dic1['_s'] + dic2['_s']),
            dic['_c'] / dic['_s'])

    def test_2_rlzs(self):
        # test with two GMPEs, 1 TRT
        inp = read_input(PARAM)
        [cmaker] = inp.cmakerdict.values()
        [src_group] = inp.groups
        [ctx] = cmaker.from_srcs(src_group, inp.sitecol)

        # The hazard for the target IMT and poe=0.002105
        poes = [0.002105]
        imls = [0.238531932]

        # Compute mean CS
        csdic = cmaker.get_cs_contrib(ctx, imti, imls, poes)

        # CS container
        S = csdic[0]['_c'].shape
        tmp = {0: AccumDict({'_c': np.zeros((S[0], S[1], 1, S[3])),
                             '_s': np.zeros((S[1], S[3]))})}
        w1 = inp.gsim_lt.branches[0].weight['weight']
        w2 = inp.gsim_lt.branches[1].weight['weight']

        tmp[0]['_c'][:, 0, 0, 0] = (
            csdic[0]['_c'][:, 0, 0, 0] * w1 + csdic[0]['_c'][:, 0, 1, 0] * w2)

        # Compute std
        csdic = cmaker.get_cs_contrib(ctx, imti, imls, poes, tmp)

        # Create DF for test
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
