# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2023, GEM Foundation
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

import json
import numpy as np
import matplotlib.pyplot as plt
try:
    import rtgmpy
except ImportError:
    rtgmpy = None
from openquake.baselib.performance import Monitor
from openquake.hazardlib.calc.mrd import (
    update_mrd, get_uneven_bins_edges, calc_mean_rate_dist)
from openquake.hazardlib.contexts import read_cmakers, read_ctx_by_grp
from openquake.hazardlib.cross_correlation import BakerJayaram2008
from openquake.calculators.tests import CalculatorTestCase, strip_calc_id
from openquake.calculators.export import export
from openquake.qa_tests_data.postproc import (
    case_mrd, case_rtgm, case_median_spectrum)

PLOT = False

aae = np.testing.assert_almost_equal


def _test_indirect(ctx, cmaker, imts, crosscorr, mrd, c1, c2, afo1, afo2):
    # Bin edges
    lefts = [-3, -2, 1, 2]
    numb = [80, 80, 10]
    be_mea = get_uneven_bins_edges(lefts, numb)
    be_sig = np.arange(0.50, 0.90, 0.01)

    # Compute the MRD
    mon = Monitor('multivariate')
    mrdi = calc_mean_rate_dist(ctx, 1, cmaker, crosscorr,
                               imts[0], imts[1], be_mea, be_sig, mon)

    # Compute marginal
    marg1 = mrdi.sum(axis=0)
    marg2 = mrdi.sum(axis=1)

    marg1 = np.average(marg1, axis=2, weights=[0.5, 0.5])[:, 0]
    marg2 = np.average(marg2, axis=2, weights=[0.5, 0.5])[:, 0]
    mrdi = np.average(mrdi, axis=3, weights=[0.5, 0.5])[:, :, 0]

    c1_mask = (c1 > 1e-5) & (c1 < 1e-2)
    c2_mask = (c2 > 1e-5) & (c2 < 1e-2)

    # Test - Note that in this case we restain the test to the part of
    # the hazard curve which has better coverage since the marginals
    # computed using the indirect methos show a slight underestimation of
    # the rate of occurrence
    np.testing.assert_almost_equal(marg1[c1_mask], afo1[c1_mask], decimal=3)
    np.testing.assert_almost_equal(marg2[c2_mask], afo2[c2_mask], decimal=3)

    if PLOT:
        min_afo = np.min(afo1[afo1 > 1e-10])
        min_afo = np.min([np.min(afo2[afo2 > 1e-10]), min_afo])
        max_afo = np.max(afo1)
        max_afo = np.max([np.max(afo2), max_afo])

        plt.title('Indirect method test')
        plt.plot(c1, afo1, label=f'HC {imts[0]}')
        plt.plot(c1, marg1, 'o', mfc='None')
        plt.plot(c2, afo2, label=f'HC {imts[1]}')
        plt.plot(c2, marg2, 'o', mfc='None', )
        plt.xlabel('Spectral Acceleration, S$_a$ [g]')
        plt.ylabel('Annual Rate of Occurrence')
        plt.legend()
        plt.grid(which='minor', ls=':', color='lightgrey')
        plt.grid(which='major', ls='--', color='grey')
        plt.ylim([min_afo, max_afo])
        plt.xscale('log')
        plt.yscale('log')
        plt.show()

    # test_compare
    be_mea = get_uneven_bins_edges([-3, -2, 1, 2], [80, 80, 10])
    be_sig = np.arange(0.50, 0.70, 0.01)
    if PLOT:
        fig, axs = plt.subplots(1, 1)
        fig.set_size_inches(9, 6)
        plt1 = plt.contourf(np.log(c1), np.log(c2), mrd[:, :])
        _ = plt.contour(np.log(c1), np.log(c2), mrdi[:, :],
                        colors='orange', linestyles='dashed')
        _ = plt.colorbar(mappable=plt1)
        _ = plt.title('MRD')
        axs.set_xlabel(f'{imts[0]}')
        axs.set_ylabel(f'{imts[1]}')
        plt.show()


class PostProcTestCase(CalculatorTestCase):

    def test_mrd(self):
        # Computes the mean rate density using a simple PSHA input model
        self.run_calc(case_mrd.__file__, 'job.ini', postproc_func='dummy.main')
        fnames = export(('hcurves', 'csv'), self.calc.datastore)
        for fname in fnames:
            self.assertEqualFiles('expected/%s' % strip_calc_id(fname), fname)

        hc_id = str(self.calc.datastore.calc_id)
        self.run_calc(case_mrd.__file__, 'job.ini',
                      hazard_calculation_id=hc_id)
        mrd = self.calc.datastore['mrd'][:]
        # assert abs(mrd.mean() - 2.334333e-07) < 1e-12, mrd.mean()

        # Settings
        imts = ['SA(0.2)', 'SA(1.0)']  # subset of the parent IMTs

        # Load datastore
        dstore = self.calc.datastore
        oqp = dstore['oqparam']

        # Read the context maker and set the IMTLS
        cmaker = read_cmakers(dstore)[0].restrict(imts)

        # Read contexts
        ctx = read_ctx_by_grp(dstore)[0]

        # Set the cross correlation model
        self.crosscorr = BakerJayaram2008()

        # Compute the MRD
        imls1 = oqp.imtls[imts[0]]
        imls2 = oqp.imtls[imts[1]]
        len1 = len(imls1) - 1
        len2 = len(imls2) - 1
        mrd = np.zeros((len1, len2, len(cmaker.gsims)))
        update_mrd(ctx, cmaker, self.crosscorr, mrd)

        mrd = np.average(mrd, axis=2, weights=[0.5, 0.5])

        # Loading Hazard Curves.
        # The poes array is 4D: |sites| x |stats| x |IMTs| x |IMLs|
        poes = dstore['hcurves-stats'][:]
        afe = -np.log(1-poes)
        afo = afe[:, :, :, :-1] - afe[:, :, :, 1:]

        _imts = list(oqp.imtls)
        idx1 = _imts.index(imts[0])
        idx2 = _imts.index(imts[1])

        afo1 = afo[0, 0, idx1, :]
        afo2 = afo[0, 0, idx2, :]

        c1 = imls1[:-1] + np.diff(imls1) / 2
        c2 = imls2[:-1] + np.diff(imls2) / 2

        # Compute marginal
        marg1 = mrd.sum(axis=0)
        marg2 = mrd.sum(axis=1)

        # Test
        np.testing.assert_almost_equal(marg1, afo1, decimal=4)
        np.testing.assert_almost_equal(marg2, afo2, decimal=4)

        if PLOT:
            min_afo = np.min(afo1[afo1 > 1e-10])
            min_afo = np.min([np.min(afo2[afo2 > 1e-10]), min_afo])
            max_afo = np.max(afo1)
            max_afo = np.max([np.max(afo2), max_afo])
            plt.title('Direct method test')
            plt.plot(c1, afo1, label=f'HC {imts[0]}')
            plt.plot(c1, marg1, 'o', mfc='None', label='Marg 1')
            plt.plot(c2, afo2, label=f'HC {imts[1]}')
            plt.plot(c2, marg2, 'o', mfc='None', label='Marg 2')
            plt.xlabel('Spectral Acceleration, S$_a$ [g]')
            plt.ylabel('Annual Rate of Occurrence')
            plt.legend()
            plt.grid(which='minor', ls=':', color='lightgrey')
            plt.grid(which='major', ls='--', color='grey')
            plt.ylim([min_afo, max_afo])
            plt.xscale('log')
            plt.yscale('log')
            plt.show()

        _test_indirect(ctx, cmaker, imts, self.crosscorr,
                       mrd, c1, c2, afo1, afo2)

    def test_rtgm(self):
        self.run_calc(case_rtgm.__file__, 'job_vs30.ini')
        if rtgmpy is None:
            return
        
        [fname] = export(('mce_default', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/mce_default.csv', fname)
        
        asce07 = self.calc.datastore['asce07'][0].decode('ascii')
        dic07 = json.loads(asce07)

        # check float results
        lk = list(dic07)
        lk.remove('Ss_seismicity')
        lk.remove('S1_seismicity')
        dic07_float = [dic07[k] for k in lk]
        dic07_float_ref = [0.5, 0.5191, 0.383, 0.5, 1.5, 1.35, 0.9, 
                           1.5109, 0.973, 1.2636, 1.5, 0.4297, 0.4297, 
                           0.2864, 0.4297, 0.9326, 0.2555, 0.6]

        aae(dic07_float, dic07_float_ref, decimal=4)

        # check string results
        dic07_str = [dic07[k] for k in ['Ss_seismicity', 'S1_seismicity']]
        assert dic07_str == ['Very High', 'High']

        asce41 = self.calc.datastore['asce41'][0].decode('ascii')
        dic41 = json.loads(asce41)
        assert dic41 == {'BSE2N_Ss': 1.5, 'BSE2E_Ss': 1.22049,
                         'Ss_5_50': 1.22049, 'BSE1N_Ss': 1.0,
                         'BSE1E_Ss': 0.72663, 'Ss_20_50': 0.72663,
                         'BSE2N_S1': 0.42968, 'BSE2E_S1': 0.34593,
                         'S1_5_50': 0.34593, 'BSE1N_S1': 0.28645,
                         'BSE1E_S1': 0.18822, 'S1_20_50': 0.18822}

    def test_median_spectrum1(self):
        # test with a single site and many ruptures
        self.run_calc(case_median_spectrum.__file__, 'job1.ini')
        [fname] = export(('median_spectra', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/median_spectrum1.csv', fname)

        fnames = export(('median_spectrum_disagg', 'csv'), self.calc.datastore)
        for fname in fnames:
            self.assertEqualFiles('expected/' + strip_calc_id(fname), fname)

    def test_median_spectrum2(self):
        # test with two sites and two ruptures
        self.run_calc(case_median_spectrum.__file__, 'job2.ini')
        fnames = export(('median_spectra', 'csv'), self.calc.datastore)
        for fname in fnames:
            self.assertEqualFiles('expected/%s' % strip_calc_id(fname), fname)
