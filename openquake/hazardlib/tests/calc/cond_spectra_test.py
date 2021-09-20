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
from openquake.hazardlib import read_input, valid
from openquake.hazardlib.cross_correlation import BakerJayaram2008
from openquake.hazardlib.calc.filters import MagDepDistance

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
             maximum_distance=MagDepDistance.new('200'),
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
def plot(spectra, imts):
    import matplotlib.pyplot as plt
    periods = [im.period for im in imts]
    fig, axs = plt.subplots(1, 2)
    for spectrum in spectra:
        axs[0].plot(periods, np.exp(spectrum[0]), 'x-')
        axs[1].plot(periods, np.sqrt(spectrum[1]), 'x-')
    axs[0].grid(which='both')
    axs[1].grid(which='both')
    axs[0].set_xscale('log')
    axs[1].set_xscale('log')
    axs[0].set_yscale('log')
    axs[0].set_ylim([1e-3, 10])
    axs[0].set_xlabel('Mean spectra, Period[s]')
    axs[1].set_xlabel('Std spectra, Period[s]')
    plt.show()


# used to create the expected file the first time
def spectra_to_df(spectra, imts, rlzs):
    dic = dict(rlz_id=[], period=[], cs_exp=[], cs_std=[])
    for rlz in rlzs:
        mea, var = spectra[rlz.ordinal]
        for m, imt in enumerate(imts):
            dic['rlz_id'].append(rlz.ordinal)
            dic['period'].append(imt.period)
            dic['cs_exp'].append(np.exp(mea[m]))
            dic['cs_std'].append(np.sqrt(var[m]))
    return pandas.DataFrame(dic)


class CondSpectraTestCase(unittest.TestCase):

    def test_point(self):
        # point source with 3 ruptures, checking additivity
        inp = read_input(
            PARAM, source_model_file=os.path.join(CWD, 'data', 'point.xml'),
            gsim_logic_tree_file=os.path.join(CWD, 'data', 'lt01.xml'))
        [cmaker] = inp.cmakerdict.values()
        [src_group] = inp.groups
        ctxs = cmaker.from_srcs(src_group, inp.sitecol)
        aac([ctx.occurrence_rate for ctx in ctxs], [0.00018, 0.00018, 0.00054])
        ctxs1 = ctxs[:2]
        ctxs2 = ctxs[2:]

        # check that the total spectra is a weighted mean of the two
        # rupture spectra; the weight is the same for all IMTs
        c1, s1 = cmaker.get_cs_contrib(ctxs1, imti, imls)
        c2, s2 = cmaker.get_cs_contrib(ctxs2, imti, imls)
        comp_spectra = (c1 + c2) / (s1 + s2)
        c, s = cmaker.get_cs_contrib(ctxs, imti, imls)
        aac(comp_spectra, c / s)

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

        c1, s1 = cmaker.get_cs_contrib(ctxs1, imti, imls)
        c2, s2 = cmaker.get_cs_contrib(ctxs2, imti, imls)
        c, s = cmaker.get_cs_contrib(ctxs, imti, imls)
        aac((c1 + c2) / (s1 + s2), c / s)

    def test_2_rlzs(self):
        # test with two GMPEs, 1 TRT
        inp = read_input(PARAM)
        [cmaker] = inp.cmakerdict.values()
        [src_group] = inp.groups
        ctxs = cmaker.from_srcs(src_group, inp.sitecol)
        [c_], [s_] = cmaker.get_cs_contrib(ctxs, imti, imls)
        spectra = [c / s for c, s in zip(c_, s_)]

        # check the result
        expected = os.path.join(CWD, 'expected', 'spectra2.csv')
        if OVERWRITE_EXPECTED:
            rlzs = list(inp.gsim_lt)
            spectra_to_df(spectra, cmaker.imts, rlzs).to_csv(
                expected, index=False, line_terminator='\r\n',
                float_format='%.6f')
        df = pandas.read_csv(expected)
        for g, gsim in enumerate(cmaker.gsims):
            dfg = df[df.rlz_id == g]
            aac(dfg.cs_exp, np.exp(spectra[g][0]), atol=1e-6)
            aac(dfg.cs_std, np.sqrt(spectra[g][1]), atol=1e-6)

        # to plot the spectra uncomment the following line
        # plot(spectra, cmaker.imts)

    def test_6_rlzs(self):
        # test with 2x3 realizations and TRTA, TRTB
        # rlzs_by_g = 012, 345, 03, 14, 25
        inp = read_input(
            PARAM, source_model_file=os.path.join(CWD, 'data', 'sm02.xml'))
        rlzs = list(inp.gsim_lt)
        R = len(rlzs)

        # compute the contributions by trt
        all_cs = []
        for src_group in inp.groups:
            cmaker = inp.cmakerdict[src_group.trt]
            ctxs = cmaker.from_srcs(src_group, inp.sitecol)
            [c], [s] = cmaker.get_cs_contrib(ctxs, imti, imls)
            for cs in zip(c, s):
                all_cs.append(cs)

        # compose the contributions by rlz, 0+2, 0+3, 0+4, 1+2, 1+3, 1+4
        rlzs_by_g = inp.gsim_lt.get_rlzs_by_g()
        nums = np.zeros((R, 2, len(cmaker.imts)))
        denums = np.zeros(R)
        for g, rlz_ids in enumerate(rlzs_by_g):
            c, s = all_cs[g]
            for r in rlz_ids:
                nums[r] += c
                denums[r] += s
        spectra = [nums[r] / denums[r] for r in range(R)]

        # check the results
        expected = os.path.join(CWD, 'expected', 'spectra6.csv')
        if OVERWRITE_EXPECTED:
            spectra_to_df(spectra, cmaker.imts, rlzs).to_csv(
                expected, index=False, line_terminator='\r\n',
                float_format='%.6f')
        df = pandas.read_csv(expected)
        for rlz in rlzs:
            r = rlz.ordinal
            df_rlz = df[df.rlz_id == r]
            aac(df_rlz.cs_exp, np.exp(spectra[r][0]), atol=1e-6)
            aac(df_rlz.cs_std, np.sqrt(spectra[r][1]), atol=1e-6)

        # to plot the spectra uncomment the following line
        # plot(spectra, cmaker.imts)
