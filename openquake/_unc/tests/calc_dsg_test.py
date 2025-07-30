# --------------- POINT - Propagation Of epIstemic uNcerTainty ----------------
# Copyright (C) 2025 GEM Foundation
#
#                `.......      `....     `..`...     `..`... `......
#                `..    `..  `..    `..  `..`. `..   `..     `..
#                `..    `..`..        `..`..`.. `..  `..     `..
#                `.......  `..        `..`..`..  `.. `..     `..
#                `..       `..        `..`..`..   `. `..     `..
#                `..         `..     `.. `..`..    `. ..     `..
#                `..           `....     `..`..      `..     `..
#
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more
# details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# -----------------------------------------------------------------------------
# vim: tabstop=4 shiftwidth=4 softtabstop=4
# coding: utf-8

import os
import pathlib
import unittest
import tempfile
import numpy as np
import matplotlib.pyplot as plt

from openquake._unc.tests.utils_plot_dsg import plot_dsg_md
from openquake.calculators.base import dcache
from openquake._unc.hazard_pmf import get_md_from_1d
from openquake._unc.propagate_uncertainties import propagate

# This file folder
TFF = pathlib.Path(__file__).parent.resolve()

# Testing
aae = np.testing.assert_almost_equal
aac = np.testing.assert_allclose

# Options
PLOTTING = False


class BasicCalcsTestCase(unittest.TestCase):

    def test01(self):
        path = os.path.join(TFF, 'data_calc', 'disaggregation', 'test_case01')
        dstore = dcache.get(os.path.join(path, 'job_all.ini'))
        rmap = dstore['best_rlzs'][0]
        res_all = dstore['disagg-rlzs/Mag'][0, :, 0, 0, :]
        wei_all = dstore['weights'][:][rmap]

        dstore = dcache.get(os.path.join(path, 'job_a.ini'))
        rmap = dstore['best_rlzs'][0]
        res_a = dstore['disagg-rlzs/Mag'][0, :, 0, 0, :]
        wei_a = dstore['weights'][:]
        wei_a = wei_a[rmap]

        dstore = dcache.get(os.path.join(path, 'job_b.ini'))
        rmap = dstore['best_rlzs'][0]
        res_b = dstore['disagg-rlzs/Mag'][0, :, 0, 0, :]
        wei_b = dstore['weights'][:][rmap]

        mags_b = dstore.get('disagg-bins/Mag', None)
        mags_b = mags_b[:-1] + np.diff(mags_b) / 2

        idx = 15  # This is the m=7.95 bins
        res_all[res_all > 0.99999] = 0.99999
        res_b[res_b > 0.99999] = 0.99999
        mean_all = np.sum(-np.log(1. - res_all[idx, :]) * wei_all)
        mean_a = np.sum(-np.log(1. - res_a[idx, :]) * wei_a)
        mean_b = np.sum(-np.log(1. - res_b[idx, :]) * wei_b)
        print(mean_all, mean_a, mean_b)


class ResultsDisaggregationTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        figs = str(TFF / 'figs')
        if not os.path.exists(figs):
            os.mkdir(figs)

    @unittest.skip('not ready')
    def test_mde_convolution(self):
        pass

    def test_md_convolution(self):
        # Convolution md test case

        fname = os.path.join(TFF, 'data_calc', 'disaggregation', 'test_case01',
                             'test_case01_convolution_md.ini')

        tmpdir = tempfile.mkdtemp()
        h, alys = propagate(
            fname, calc_type='disaggregation', override_folder_out=tmpdir)

        # Save results
        fname = os.path.join(tmpdir, 'res.hdf5')
        print(f'Saving {fname}')
        h.save(fname)

        # Expected results
        ini = os.path.join(TFF, 'data_calc', 'disaggregation', 'test_case01',
                           'job_all.ini')
        dstore = dcache.get(ini)
        expct = dstore['disagg-rlzs/Mag_Dist'][0, :, :, 0, 0, :]  # mag,dist,rlz

        aae(expct.mean(), 7.41170608e-06)
        aae(expct.std(), 2.95703767e-05)

        rmap = dstore['best_rlzs'][:]
        weights = dstore['weights'][:][rmap]
        oute, idxe = alys.extract_afes_rlzs(expct, weights)

        # Mean and median from convolution
        mea, med = h.get_stats([-1, 0.50]).T

        # Test the indexes
        aae(h.idxs, idxe)
        assert len(oute) == len(mea)

        # Mean matrix (17 x 17)
        shape = alys.shapes[:-1]
        out = get_md_from_1d(mea, shape, h.idxs)

        # Expected mean
        mate = get_md_from_1d(oute, shape, h.idxs)

        # Test the mean
        rounded = np.round(mate[1], 10)
        expected = np.array(
            [0.00000e+00, 5.04794e-05, 2.25640e-05, 3.50510e-06, 5.54500e-07,
             6.16000e-08, 1.59000e-08, 3.00000e-10, 0.00000e+00, 0.00000e+00,
             0.00000e+00, 0.00000e+00, 0.00000e+00, 0.00000e+00, 0.00000e+00,
             0.00000e+00, 0.00000e+00])
        aae(rounded, expected)

        conf = {}
        conf['imt_lab'] = 'PGA'
        conf['site_lab'] = 'Test'
        conf['calc_id'] = ''
        conf['figure_folder'] = './figs/'
        conf['return_period'] = 475
        conf['site_condition'] = ''
        conf['fig_name'] = 'dsg_test01_md_conv.png'

        d_cen = alys.dsg_dst[:-1] + np.diff(alys.dsg_dst) / 2
        m_cen = alys.dsg_mag[:-1] + np.diff(alys.dsg_mag) / 2

        conf['fig_name'] = str(TFF / 'figs' / 'dsg_test01_md_conv.png')
        plot_dsg_md(d_cen, m_cen, out, conf)

        conf['fig_name'] = str(TFF / 'figs' / 'dsg_test01_md_oq.png')
        plot_dsg_md(d_cen, m_cen, mate, conf)

    def test_m_convolution(self):
        # Convolution m test case
        fname = os.path.join(TFF, 'data_calc', 'disaggregation',
                             'test_case01', 'test_case01_convolution_m.ini')
        tmpdir = tempfile.mkdtemp()
        h, alys = propagate(
            fname, calc_type='disaggregation', override_folder_out=tmpdir)

        # Save results
        fname = os.path.join(tmpdir, 'res.hdf5')
        print(f'Saving {fname}')
        h.save(fname)

        # Expected results - Realizations
        ini = os.path.join(TFF, 'data_calc', 'disaggregation', 'test_case01',
                           'job_all.ini')
        dstore = dcache.get(ini)
        res = dstore['disagg-stats/Mag'][0, :, 0, 0, 0]
        rmap = dstore['best_rlzs'][0]

        # Expected results - Mean disaggregation
        expct = dstore['disagg-rlzs/Mag'][0, :, 0, 0, :]
        weights = dstore['weights'][:][rmap]
        oute, idxe = alys.extract_afes_rlzs(expct[:, None], weights)

        # Mean and median from convolution
        mea, med = h.get_stats([-1, 0.50]).T

        # Test the indexes
        aae(h.idxs, idxe)
        assert len(oute) == len(mea)

        # Test the mean
        aac(oute, mea, atol=1e-5, rtol=1e-3)

        print('\nOQ rlzs ', sum(oute))
        print('Conv    ', mea.sum())

        if PLOTTING:
            mags = alys.dsg_mag[:-1] + np.diff(alys.dsg_mag) / 2
            fig, axs = plt.subplots(1, 1)
            fig.set_size_inches(8, 6)

            # plt.plot(oute, res_conv[:, 0], 'og', label='oq rlz Vs. conv')
            plt.plot(res[idxe], mea, 'or', mfc='None',
                     label='oq mean Vs. conv')
            # plt.plot(oute, res[idxe], 'bx', label='oq rlz Vs. oq mean')

            xlim = axs.get_xlim()
            ylim = axs.get_ylim()
            xli = [min([xlim[0], ylim[0]]), max([xlim[1], ylim[1]])]
            plt.plot(xli, xli, '--')
            plt.grid(which='major', color='lightgrey', ls='--')
            plt.grid(which='minor', color='lightgrey', ls=':')
            for i in range(len(oute)):
                plt.text(res[idxe[i]], mea[i], f'{i} - {mags[i]:.2f}',
                         fontsize=8)
            plt.xlabel('AfE - Convolution')
            plt.ylabel('AfE - OQ')
            plt.legend()
            plt.savefig(TFF / 'figs' / 'dsg_correlation_test01.png')
            plt.show()
