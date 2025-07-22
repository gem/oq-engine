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
from openquake._unc.hazard_pmf import get_mde_from_2d, get_md_from_2d
from openquake._unc.hcurves_dist import to_matrix, get_stats
from openquake._unc.calc.propagate_uncertainties import (
    propagate, write_results_convolution)

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
        rmap = dstore.get('best_rlzs', None)[:][0]
        res_a = dstore.get('disagg-rlzs/Mag', None)[0, :, 0, 0, :]
        wei_a = dstore.get('weights', None)[:]
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

    @unittest.skip('not ready')
    def test_mde_convolution(self):
        pass

    def test_md_convolution(self):
        # Convolution md test case

        ini = os.path.join(TFF, 'data_calc', 'disaggregation', 'test_case01',
                           'test_case01_convolution_md.ini')

        tmpdir = tempfile.mkdtemp()
        his, minp, nump, alys = propagate(
            ini, calc_type='disaggregation', override_folder_out=tmpdir)

        # Results
        computed_mtx, afes = to_matrix(his, minp, nump)
        fname_out = os.path.join(tmpdir, 'res.hdf5')

        write_results_convolution(fname_out, his, np.array(minp, dtype=float),
                                  np.array(nump, dtype=float))

        # Expected results
        tpath = os.path.join(TFF, 'data_calc', 'disaggregation', 'test_case01')
        dstore = dcache.get(os.path.join(tpath, 'job_all.ini'))

        expct = dstore['disagg-rlzs/Mag_Dist'][0, :, :, 0, 0, :]
        rmap = dstore['best_rlzs'][:]
        weights = dstore['weights'][:][rmap]
        oqp = dstore['oqparam']

        oute = []
        idxe = []
        cnt = 0
        for imag in range(alys.shapes[0]):
            for idst in range(alys.shapes[1]):
                if np.all(np.isfinite(expct[imag, idst, :])):
                    poes = expct[imag, idst, :]
                    poes[poes > 0.99999] = 0.99999
                    afes = -np.log(1. - poes) / oqp.investigation_time
                    tmp = np.sum(afes * weights)
                    if tmp > 0.0:
                        oute.append(tmp)
                        idxe.append(cnt)
                cnt += 1

        # Mean and median from convolution
        res_conv, idxs = get_stats([-1, 0.50], his, minp, nump)

        # Test the indexes
        aae(idxs, idxe)

        assert len(oute) == len(res_conv[:, 0])

        # Mean matrix (17 x 17)
        tmp = alys.shapes[:-1]
        out = get_md_from_2d(res_conv[:, 0], tmp, idxs)

        # Expected mean
        mtxe = get_md_from_2d(oute, tmp, idxs)

        # Test the mean
        # aae(oute, res_conv[:, 0])

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
        plot_dsg_md(d_cen, m_cen, mtxe, conf)

    def test_m_convolution(self):
        # Convolution m test case
        ini = os.path.join(TFF, 'data_calc', 'disaggregation',
                                'test_case01', 'test_case01_convolution_m.ini')
        tmpdir = tempfile.mkdtemp()
        his, minp, nump, alys = propagate(
            ini, calc_type='disaggregation', override_folder_out=tmpdir)

        # Results
        computed_mtx, afes = to_matrix(his, minp, nump)
        fname_out = os.path.join(tmpdir, 'res.hdf5')

        write_results_convolution(fname_out, his, np.array(minp, dtype=float),
                                  np.array(nump, dtype=float))

        # Expected results - Realizations
        tpath = os.path.join(TFF, 'data_calc', 'disaggregation', 'test_case01')
        dstore = dcache.get(os.path.join(tpath, 'job_all.ini'))
        res = dstore['disagg-stats/Mag'][0, :, 0, 0, 0]
        rmap = dstore['best_rlzs'][0]

        # Expected results - Mean disaggregation
        expct = dstore['disagg-rlzs/Mag'][0, :, 0, 0, :]
        weights = dstore['weights'][:][rmap]

        # Open datastore and read oq params
        oqp = dstore['oqparam']

        oute = []
        idxe = []
        cnt = 0
        for imag in range(alys.shapes[0]):
            poes = expct[imag, :]
            poes[poes > 0.99999] = 0.99999
            afes = -np.log(1. - poes) / oqp.investigation_time
            tmp = np.sum(afes * weights)
            if tmp > 0.0:
                oute.append(tmp)
                idxe.append(cnt)
            cnt += 1

        # Mean and median from convolution
        res_conv, idxs = get_stats([-1, 0.50], his, minp, nump)

        # Test the indexes
        aae(idxs, idxe)
        assert len(oute) == len(res_conv[:, 0])

        # Test the mean
        aac(oute, res_conv[:, 0], atol=1e-5, rtol=1e-3)

        print('\nOQ rlzs ', sum(oute))
        print('Conv    ', sum(res_conv[:, 0]))

        if PLOTTING:
            mags = alys.dsg_mag[:-1] + np.diff(alys.dsg_mag) / 2
            fig, axs = plt.subplots(1, 1)
            fig.set_size_inches(8, 6)

            # plt.plot(oute, res_conv[:, 0], 'og', label='oq rlz Vs. conv')
            plt.plot(res[idxe], res_conv[:, 0], 'or', mfc='None',
                     label='oq mean Vs. conv')
            # plt.plot(oute, res[idxe], 'bx', label='oq rlz Vs. oq mean')

            xlim = axs.get_xlim()
            ylim = axs.get_ylim()
            xli = [min([xlim[0], ylim[0]]), max([xlim[1], ylim[1]])]
            plt.plot(xli, xli, '--')
            plt.grid(which='major', color='lightgrey', ls='--')
            plt.grid(which='minor', color='lightgrey', ls=':')
            for i in range(len(oute)):
                plt.text(res[idxe[i]], res_conv[i, 0], f'{i} - {mags[i]:.2f}',
                         fontsize=8)
            plt.xlabel('AfE - Convolution')
            plt.ylabel('AfE - OQ')
            plt.legend()
            plt.savefig(TFF / 'figs' / 'dsg_correlation_test01.png')
            plt.show()


def get_data(alys, out):
    mag = alys.dsg_mag[:-1] + np.diff(alys.dsg_mag) / 2
    dst = alys.dsg_dst[:-1] + np.diff(alys.dsg_dst) / 2
    data = []
    for imag in range(alys.shapes[0]):
        for idst in range(alys.shapes[1]):
            if np.isfinite(out[imag, idst]):
                data.append([mag[imag], dst[idst], out[imag, idst]])
    return np.array(data)
