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
import sys
import unittest
import numpy as np
from numpy.testing import assert_allclose as aac
import pandas
from openquake.hazardlib import read_input, valid
from openquake.hazardlib.cross_correlation import BakerJayaram2008
from openquake.hazardlib.calc.filters import IntegrationDistance
from openquake.hazardlib.calc.cond_spectra import get_cs_out, cond_spectra

PLOT = False
OVERWRITE_EXPECTED = False

CWD = os.path.dirname(__file__)
SOURCES_XML = os.path.join(CWD, 'data', 'sm01.xml')
GSIM_XML = os.path.join(CWD, 'data', 'lt02.xml')
PARAM = dict(inputs=dict(source_model=SOURCES_XML,
                         gsim_logic_tree=GSIM_XML),
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
def outdic_to_dframe(outdic, imts, n, p):
    """
    :param outdic: a dictionary g_ -> array
    :param imts: M intensity measure types
    :param rlzs: R realization indices
    :param n: an index in the range 0..N-1 where N is the number of sites
    :param p: an index in the range 0..P-1 where P is the number of IMLs
    """
    dic = dict(rlz_id=[], period=[], cs_exp=[], cs_std=[])
    for r, c in outdic.items():
        for m, imt in enumerate(imts):
            dic['rlz_id'].append(r)
            dic['period'].append(imt.period)
            dic['cs_exp'].append(np.exp(c[m, n, 1, p] / c[m, n, 0, p]))
            dic['cs_std'].append(np.sqrt(c[m, n, 2, p] / c[m, n, 0, p]))
    return pandas.DataFrame(dic)


class CondSpectraTestCase(unittest.TestCase):

    def test_1_rlz(self):
        # test with one GMPE, 1 TRT, checking additivity
        inp = read_input(PARAM, inputs={
            'source_model': SOURCES_XML,
            'gsim_logic_tree': os.path.join(CWD, 'data', 'lt01.xml')})

        [ctx] = inp.cmaker.from_srcs(inp.group, inp.sitecol)
        tom = inp.group.temporal_occurrence_model
        assert len(ctx) == 100
        ctx1 = ctx[:50]
        ctx2 = ctx[50:]

        # The hazard for the target IMT and poe
        inp.cmaker.poes = [0.000404]
        imls = np.array([[0.394359437]])

        mom1 = get_cs_out(inp.cmaker, ctx1, imti, imls, tom)[0]
        mom2 = get_cs_out(inp.cmaker, ctx2, imti, imls, tom)[0]
        mom = get_cs_out(inp.cmaker, ctx, imti, imls, tom)[0]
        aac(mom1 + mom2, mom)

        spectra, s_sigma = cond_spectra(
            inp.cmaker, inp.group, inp.sitecol, 'SA(0.2)', imls)
        if sys.platform == 'darwin':
            raise unittest.SkipTest('skip on macOS')
        aac(spectra.flatten(), [0.19164881, 0.23852505, 0.27692626, 0.35103066,
                                0.39435944, 0.36436695, 0.34596382, 0.23299646,
                                0.15524817, 0.11027446, 0.04034665], rtol=7E-5)
        aac(s_sigma.flatten(), [0.33084368, 0.37107024, 0.389734, 0.27167148,
                                0.02817097, 0.23704353, 0.32075199, 0.46459039,
                                0.55801751, 0.59838493, 0.7080976], rtol=7E-5)

    def test_2_rlzs(self):
        # test with two GMPEs, 1 TRT
        inp = read_input(PARAM)
        cmaker = inp.cmaker
        src_group = inp.group
        [ctx] = cmaker.from_srcs(src_group, inp.sitecol)
        tom = src_group.temporal_occurrence_model

        # The hazard for the target IMT and poe=0.002105
        cmaker.poes = [0.002105]
        imls = np.array([[0.0483352]])

        # Compute mean CS
        outdic = get_cs_out(cmaker, ctx, imti, imls, tom)
        # 0, 1 -> array (M, N, O, P) = (11, 1, 3, 1)

        # Compute mean across rlzs
        gsim_lt = inp.full_lt.gsim_lt
        w1 = gsim_lt.branches[0].weight['weight']
        w2 = gsim_lt.branches[1].weight['weight']
        _c = outdic[0] * w1 + outdic[1] * w2

        # Compute std
        outdic = get_cs_out(cmaker, ctx, imti, imls, tom, _c)

        # Create DF for test
        df = outdic_to_dframe(outdic, cmaker.imts, 0, 0)

        # check the result
        if sys.platform == 'darwin':
            raise unittest.SkipTest('skip on macOS')
        expected = os.path.join(CWD, 'expected', 'spectra2.csv')
        if OVERWRITE_EXPECTED:
            df.to_csv(expected, index=False, lineterminator='\r\n',
                      float_format='%.6f')
        expdf = pandas.read_csv(expected)
        pandas.testing.assert_frame_equal(df, expdf, atol=1E-6)
        # Plot the spectra for the two sites
        if PLOT:
            plot(df, cmaker.imts)
