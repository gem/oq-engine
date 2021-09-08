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

CWD = os.path.dirname(__file__)
SOURCES_XML = os.path.join(CWD, 'data', 'sm01.xml')
GSIM_XML = os.path.join(CWD, 'data', 'lt01.xml')

PARAM = dict(source_model_file=SOURCES_XML,
             gsim_logic_tree_file=GSIM_XML,
             sites=[(0, -0.8)],
             reference_vs30_value=600,
             reference_depth_to_2pt5km_per_sec=5,
             reference_depth_to_1pt0km_per_sec=100,
             maximum_distance=MagDepDistance.new('200'),
             investigation_time=1,
             truncation_level=3,
             correl_model=BakerJayaram2008(),
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


# useful while debugging
def plot(spectrum, imts):
    import matplotlib.pyplot as plt
    periods = [im.period for im in imts]
    fig, axs = plt.subplots(1, 2)
    print(np.exp(spectrum[0]))
    axs[0].plot(periods, np.exp(spectrum[0]), 'x-')
    axs[1].plot(periods, np.sqrt(spectrum[1]), 'x-')
    axs[0].grid(which='both')
    axs[1].grid(which='both')
    axs[0].set_xscale('log')
    axs[1].set_xscale('log')
    axs[0].set_yscale('log')
    axs[0].set_ylim([1e-3, 10])
    axs[0].set_xlabel('Mean spectrum, Period[s]')
    axs[1].set_xlabel('Std spectrum, Period[s]')
    plt.show()


def spectra_to_df(spectra, cmaker):
    dic = dict(gsim=[], period=[], cs_mean=[], cs_std=[])
    for g, gsim in enumerate(cmaker.gsims):
        gs = str(gsim)
        c, s = spectra[g]
        for m, imt in enumerate(cmaker.imts):
            dic['gsim'].append(gs)
            dic['period'].append(imt.period)
            dic['cs_mean'].append(np.exp(c[m]))
            dic['cs_std'].append(np.sqrt(s[m]))
    return pandas.DataFrame(dic)


class CondSpectraTestCase(unittest.TestCase):
    def test_1(self):
        # test with a single source producing 100 ruptures and a single
        # GMPE BooreAtkinson2008; there are 11 periods
        inp = read_input(PARAM)
        [cmaker] = inp.cmakerdict.values()
        [src_group] = inp.groups
        ctxs = cmaker.from_srcs(src_group, inp.sitecol)
        imti = 4  # corresponds to SA(0.2)
        iml = np.log(1.001392E-01)
        spectra = cmaker.get_cond_spectra(ctxs, imti, iml)
        # spectra_to_df(spectra, cmaker).to_csv(
        #    'expected/spectra1.csv', index=False, line_terminator='\r\n')

        # check the result
        expected = os.path.join(CWD, 'expected', 'spectra1.csv')
        df = pandas.read_csv(expected)
        aac(df.cs_mean, np.exp(spectra[0, 0]))
        aac(df.cs_std, np.sqrt(spectra[0, 1]))

        # to plot the spectra uncomment the following line
        # plot(spectra[0], cmaker.imts)
