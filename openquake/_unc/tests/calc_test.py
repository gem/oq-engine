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

import re
import os
import time
import pathlib
import unittest
import tempfile
import tracemalloc
import configparser
import pytest
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from openquake.baselib import hdf5
from openquake.calculators.base import dcache
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
NSAMPLES = [500, 1000, 10000]
# NSAMPLES = [500, 1000, 10000, 100000]


class ResultsCalculationTestCase01(unittest.TestCase):
    """
    We compare the hazard results from the OQ Engine against the ones computed
    by propagating epistemic uncertainties with the two methods supported in
    this library
    """
    def test_against_oq(self):
        # Convolution Vs OQ

        xlim = [1e-2, 5]

        # Convolution
        fname = os.path.join(TFF, 'data_calc', 'test_case01_convolution.ini')
        tmpdir = tempfile.mkdtemp()
        his, minp, nump, _ = propagate(fname, override_folder_out=tmpdir)

        # Read oq mean result
        ini = os.path.join(TFF, 'data_calc', 'test_case01', 'job_all.ini')
        dstore = dcache.get(ini)
        mean = dstore['hcurves-stats'][0, 0, 0, :]
        median = dstore['hcurves-stats'][0, 2, 0, :]
        oqp = dstore['oqparam']
        imls = oqp.hazard_imtls['PGA']

        # Mean and median from convolution
        res_conv, idxs = get_stats([-1, 0.50], his, minp, nump)

        # Testing the mean
        expected_mea = -np.log(1 - mean)
        aac(expected_mea, res_conv[:, 0], rtol=5e-3)

        # Plotting
        # ------------------------------------------------------------ FIGURE 1
        if PLOTTING:

            fig, axs = plt.subplots(1, 1)

            n_rlz = dstore['hcurves-rlzs'].shape[1]
            for i_rlz in range(0, n_rlz):
                poe = -np.log(1 - dstore['hcurves-rlzs'][0, i_rlz, 0, :])
                _ = plt.plot(imls, poe, '-', color='lightblue', alpha=0.8)

            # Plot mean from oq
            lbl = 'OQ Full Path Enumeration'
            _ = plt.plot(imls, expected_mea, '-', label=lbl)

            # Plot convolution results
            lab = 'Mean from POINT'
            plt.plot(imls, res_conv[:, 0], 'o', mfc='none', label=lab)
            plt.xscale('log')
            plt.yscale('log')
            plt.xlim(xlim)
            plt.legend()
            plt.xlabel('Intensity measure level, IML [g]')
            plt.ylabel('Annual Frequency of exceedance, AFoE []')
            plt.title('Test Case 01 - Mean PGA')
            plt.grid(which='major', ls='--', color='grey')
            plt.grid(which='minor', ls=':', color='lightgrey')
            tmp = os.path.join(TFF, 'figs', 'calc_test-case01_mean.png')
            plt.savefig(tmp)
            plt.show()

        # Testing the median
        expected_med = -np.log(1 - median)
        aac(expected_med, res_conv[:, 1], rtol=1e-1)

        # Plotting
        # ------------------------------------------------------------ FIGURE 2
        if PLOTTING:
            fig, axs = plt.subplots(1, 1)

            n_rlz = dstore['hcurves-rlzs'].shape[1]
            for i_rlz in range(0, n_rlz):
                poe = -np.log(1 - dstore['hcurves-rlzs'][0, i_rlz, 0, :])
                _ = plt.plot(imls, poe, '-', color='lightblue', alpha=0.8)

            lbl = 'OQ Full Path Enumeration'
            plt.plot(imls, expected_med, '-', label=lbl)

            lab = 'Median from POINT'
            plt.plot(imls, res_conv[:, 1], 'o', mfc='none', label=lab)
            plt.yscale('log')
            plt.xscale('log')
            plt.legend()
            plt.xlabel('Intensity measure level, IML [g]')
            plt.ylabel('Annual Frequency of exceedance, AFoE []')
            plt.title('Test Case 01 - PGA')
            plt.grid(which='major', ls='--', color='grey')
            plt.grid(which='minor', ls=':', color='lightgrey')
            plt.savefig(os.path.join(TFF, 'figs', 'calc_test-case01_median.png'))
            plt.show()

        # Plotting mean and median and percentiles
        # ------------------------------------------------------------ FIGURE 3
        if PLOTTING:
            fig, axs = plt.subplots(1, 1)

            # All realizations
            for i_rlz in range(0, n_rlz):
                poe = -np.log(1 - dstore['hcurves-rlzs'][0, i_rlz, 0, :])
                if i_rlz == 0:
                    plt.plot(imls, poe, '-', color='lightblue', alpha=0.8,
                             label='LT realization')
                else:
                    plt.plot(imls, poe, '-', color='lightblue', alpha=0.8)

            plt.plot(imls, expected_med, '-',
                         label='Median from OQ Full Path Enumeration')
            plt.plot(imls, expected_mea, '-',
                         label='Mean from OQ Full Path Enumeration')
            lab = '16th percentile from POINT'
            expected_pct = -np.log(1 - dstore['hcurves-stats'][0, 1, 0, :])
            _ = plt.plot(imls, expected_pct, '--r', mfc='none', label=lab,
                         lw=1)
            lab = '84th percentile from POINT'
            expected_pct = -np.log(1 - dstore['hcurves-stats'][0, 3, 0, :])
            plt.plot(imls, expected_pct, '-.r', mfc='none', label=lab, lw=1)

            # Plot convolution results - median
            lab = 'Median from POINT'
            plt.plot(imls, res_conv[:, 1], 'o', mfc='none', label=lab)

            # Plot convolution results - mean
            lab = 'Mean from POINT'
            plt.plot(imls, res_conv[:, 0], 'o', mfc='none', label=lab)

            plt.xlim(xlim)
            plt.yscale('log')
            plt.xscale('log')
            plt.legend()
            plt.xlabel('Intensity measure level, IML [g]')
            plt.ylabel('Annual Frequency of exceedance, AFoE []')
            plt.title('Test Case 01 - Median PGA')
            plt.grid(which='major', ls='--', color='grey')
            plt.grid(which='minor', ls=':', color='lightgrey')

            plt.savefig(os.path.join(TFF, 'figs', 'calc_test-case01_all.png'))
            plt.show()


class ResultsCalculationTestCase02(unittest.TestCase):

    def test_convolution(self):
        # Convolution test case

        fname = os.path.join(TFF, 'data_calc', 'test_case02_convolution.ini')
        tmpdir = tempfile.mkdtemp()
        his, minp, nump, alys = propagate(fname, override_folder_out=tmpdir)

        # Results
        computed_mtx, afes = to_matrix(his, np.array(minp), np.array(nump))
        fname = os.path.join(tmpdir, 'res.hdf5')
        write_results_convolution(fname, his, minp, nump)

        # Expected results
        fname = os.path.join(
            TFF, 'data_calc', 'test_case02_expected_convolution.hdf5')
        with hdf5.File(fname, "r") as f:
            aae(computed_mtx, f["histograms"][:], decimal=2)

        # Mean and median from convolution
        res_conv, idxs = get_stats([-1, 0.50], his, minp, nump)

        if PLOTTING:
            imtls = alys.get_imtls()
            mtx = computed_mtx
            idx = np.where(np.isfinite(mtx))
            iii = mtx[idx[0], idx[1]] > 1e-20

            # Histogram
            x = np.tile(imtls['PGA'], reps=(mtx.shape[0], 1))
            y = np.tile(afes, reps=(mtx.shape[1], 1)).T
            fig, axs = plt.subplots(1, 1)
            plt.scatter(x[idx[0][iii], idx[1][iii]],
                        y[idx[0][iii], idx[1][iii]],
                        c=mtx[idx[0][iii], idx[1][iii]], marker='s', s=0.1)
            plt.plot(imtls['PGA'], res_conv[:, 0], '-', label='Mean')
            plt.yscale('log')
            plt.xscale('log')
            plt.legend()
            plt.title('Test Case 02 - Mean PGA')
            plt.grid(which='major', ls='--', color='grey')
            plt.grid(which='minor', ls=':', color='lightgrey')

            # Inset
            ins = axs.inset_axes([0.5, 0.25, 0.2, 0.4])
            j = 22
            tmpy = 10**np.linspace(minp[j], minp[j] + nump[j], num=len(his[j]))
            hei = list(np.diff(tmpy))
            hei.insert(0, hei[0])
            ins.barh(tmpy, his[j], height=hei, fc='none', ec='lightblue')
            ins.set_yscale('log')
            ins.set_ylim([1e-5, 5e-3])

            axs.plot([1e-1, 1], [3e-6, 1e-5], '--r', lw=0.5)
            axs.plot([1e-1, 1], [4e-3, 5e-3], '--r', lw=0.5)
            axs.plot([0.98, 1.1, 1.1, 0.98, 0.98],
                     [1e-5, 1e-5, 5e-3, 5e-3, 1e-5], '-r', lw=0.7)
            axs.set_xlabel('Intensity Measure Level, $\\kappa$ [g]')
            axs.set_ylabel('Annual Frequency of Exceedance')

            plt.savefig(
                os.path.join(TFF, 'figs', 'calc_test-case02_matrix.png'))
            plt.show()

    def test_sampling(self):
        # Sampling test case
        fname = os.path.join(TFF, 'data_calc', 'test_case02_sampling.ini')
        tmpdir = tempfile.mkdtemp()
        imls, afes, _ = propagate(fname, override_folder_out=tmpdir)

    def test_comparison(self):
        # Comparing results from convolution and sampling

        # Compute convolution
        fname = os.path.join(TFF, 'data_calc', 'test_case02_convolution.ini')
        tmpdir = tempfile.mkdtemp()
        his, minp, nump, _ = propagate(fname, override_folder_out=tmpdir)

        # Mean and median from convolution
        res_conv, idxs = get_stats([-1, 0.50], his, minp, nump)

        # Compute sampling
        fname = os.path.join(TFF, 'data_calc', 'test_case02_sampling.ini')
        tmpdir = tempfile.mkdtemp()
        imls, afes, _ = propagate(fname, override_folder_out=tmpdir)

        # Mean and median from sampling
        mean_sampl = np.mean(np.sum(afes[0, :, :, 0], axis=0), axis=0)
        median_sampl = np.median(np.sum(afes[0, :, :, 0], axis=0), axis=0)

        # Testing statistics
        aac(mean_sampl, res_conv[:, 0], rtol=1e-0)
        aac(median_sampl, res_conv[:, 1], rtol=1e-0)

        # Plotting
        if PLOTTING:
            fig, _ = plt.subplots(1, 1)

            plt.plot(imls['PGA'], mean_sampl, '-', label='Mean sampling')
            lab = 'Mean convolution'
            plt.plot(imls['PGA'], res_conv[:, 0], 'o', mfc='none', label=lab)

            lab = 'Median sampling'
            plt.plot(imls['PGA'], median_sampl, '-', label=lab)
            lab = 'Median convolution'
            plt.plot(imls['PGA'], res_conv[:, 1], 'o', mfc='none', label=lab)

            plt.yscale('log')
            plt.xscale('log')
            plt.legend()
            plt.xlabel('Intensity measure level, IML [g]')
            plt.ylabel('Annual probability of exceedance, APoE [g]')
            plt.title('Test Case 02 - Mean PGA')
            plt.grid(which='major', ls='--', color='grey')
            plt.grid(which='minor', ls=':', color='lightgrey')
            plt.savefig(os.path.join(TFF, 'figs', 'calc_test-case02.png'))
            plt.show()

        # Mean and median from sampling
        pct_16 = np.percentile(np.sum(afes[0, :, :, 0], axis=0), 16, axis=0)
        pct_84 = np.percentile(np.sum(afes[0, :, :, 0], axis=0), 84, axis=0)

        # Mean and median from convolution
        res_conv, idxs = get_stats([0.16, 0.84], his, minp, nump)

        # Plotting
        if PLOTTING:
            fig, _ = plt.subplots(1, 1)

            plt.plot(imls['PGA'], pct_16, '-', label='16th perc. sampling')
            lab = '16th perc. convolution'
            plt.plot(
                imls['PGA'], res_conv[:, 0], 'o', mfc='none', label=lab)

            lab = '84th perc. sampling'
            plt.plot(imls['PGA'], pct_84, '-', label=lab)
            lab = '84th perc. convolution'
            plt.plot(
                imls['PGA'], res_conv[:, 1], 'o', mfc='none', label=lab)

            plt.yscale('log')
            plt.xscale('log')
            plt.legend()
            plt.xlabel('Intensity measure level, IML [g]')
            plt.ylabel('Annual probability of exceedance, APoE [g]')
            plt.title('Test Case 02 - Mean PGA')
            plt.grid(which='major', ls='--', color='grey')
            plt.grid(which='minor', ls=':', color='lightgrey')
            plt.savefig(os.path.join(TFF, 'figs', 'calc_test-case02-pct.png'))
            plt.show()

    @pytest.mark.slow
    def test_02_performance(self):
        # Comparing results from convolution and sampling - test 02

        fname_c = os.path.join(TFF, 'data_calc', 'test_case02_convolution.ini')
        conf_conv = configparser.ConfigParser()
        conf_conv.read(fname_c)

        fname_s = os.path.join(TFF, 'data_calc', 'test_case02_sampling.ini')
        conf_samp = configparser.ConfigParser()
        conf_samp.read(fname_s)
        conf_samp = {s: dict(conf_samp.items(s)) for s in conf_samp.sections()}

        # Compute sampling
        results = []
        file_path = TFF / 'data_calc'
        for nsam in NSAMPLES:

            print(f"\n   Number of samples: {nsam}")

            conf_samp['analysis']['number_of_samples'] = f'{nsam}'
            conf_samp['analysis']['conf_file_path'] = file_path

            tracemalloc.start()
            start_time = time.time()

            tmpdir = tempfile.mkdtemp()
            imls, afes, _ = propagate(conf_samp, override_folder_out=tmpdir)

            # Mean and median from sampling
            mean_sampl = np.mean(np.sum(afes[0, :, :, 0], axis=0), axis=0)
            median_sampl = np.median(np.sum(afes[0, :, :, 0], axis=0), axis=0)
            tmp = np.sum(afes[0, :, :, 0], axis=0)
            pct_16 = np.percentile(tmp, 16, axis=0)
            pct_84 = np.percentile(tmp, 84, axis=0)

            exec_time = time.time() - start_time
            mem = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            results.append([nsam, exec_time, mem, mean_sampl, median_sampl,
                            pct_16, pct_84])

        # Compute convolution
        tracemalloc.start()
        start_time = time.time()

        tmpdir = tempfile.mkdtemp()
        conf_conv = {s: dict(conf_conv.items(s)) for s in conf_conv.sections()}
        conf_conv['analysis']['resolution'] = '100'
        conf_conv['analysis']['conf_file_path'] = file_path
        his, minp, nump, _ = propagate(conf_conv, override_folder_out=tmpdir)

        # Mean and median from convolution
        res_conv, idxs = get_stats([-1, 0.50, 0.16, 0.84], his, minp, nump)

        exec_time = time.time() - start_time
        mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        print(f"Execution time    : {exec_time}")
        print(f"Memory occupation : {mem}")

        if PLOTTING:

            fig, axs = plt.subplots(3, 1)
            fig.set_size_inches(7, 12)

            nsam = [row[0] for row in results]
            etim = [row[1] for row in results]
            memu = np.array([row[2] for row in results])

            plt.sca(axs[0])
            plt.plot(nsam, etim, '-')
            plt.plot(nsam, etim, 'o', label='sampl')

            xlim = axs[0].get_xlim()
            plt.hlines(exec_time, xlim[0], xlim[1], label='conv')

            plt.xlabel('Number of samples')
            plt.grid(which='major', ls='--', color='grey')
            plt.grid(which='minor', ls=':', color='lightgrey')
            plt.legend()

            plt.sca(axs[1])
            plt.plot(nsam, memu[:, 0], '-')
            plt.plot(nsam, memu[:, 0], 'o',  label='sampl - size')
            plt.plot(nsam, memu[:, 1], '-')
            plt.plot(nsam, memu[:, 1], 'x',  label='sampl - peak')

            xlim = axs[1].get_xlim()
            plt.hlines(mem[0], xlim[0], xlim[1], '--', label='conv - size')
            plt.hlines(mem[1], xlim[0], xlim[1], ':', label='conv - peak')

            plt.xlabel('Number of samples')
            plt.grid(which='major', ls='--', color='grey')
            plt.grid(which='minor', ls=':', color='lightgrey')
            plt.legend()

            plt.sca(axs[2])
            for row in results:
                ratio = row[3] / results[-1][3]
                plt.plot(imls['PGA'], ratio, label=f'# sampl {row[0]}')
            ratio = res_conv[:, 0] / results[-1][3]
            plt.plot(imls['PGA'], ratio, label='conv')
            plt.xlabel('IMT [g]')
            plt.ylabel('Ratio')
            plt.xscale('log')
            plt.yscale('log')
            plt.grid(which='major', ls='--', color='grey')
            plt.grid(which='minor', ls=':', color='lightgrey')
            plt.legend()

            """
            plt.sca(axs[2])
            idx = 6
            for row in results:
                ratio = row[idx]/results[-1][idx]
                plt.plot(imls['PGA'], ratio, label=f'# sampl {row[0]}')
            ratio = res_conv[:, 3]/results[-1][idx]
            plt.plot(imls['PGA'], ratio, label='conv')
            plt.xlabel('IMT [g]')
            plt.ylabel('Ratio')
            plt.xscale('log')
            plt.yscale('log')
            plt.grid(which='major', ls='--', color='grey')
            plt.grid(which='minor', ls=':', color='lightgrey')
            plt.legend()
            """

            plt.savefig(TFF / 'figs' / 'test02_performance.png')

    @pytest.mark.slow
    def test_01_performance(self):
        # Comparing results from convolution and sampling - test 01

        # Read oq mean result
        fname = TFF / 'data_calc' / 'test_case01' / 'out_all'
        fname = fname / 'hazard_curve-mean-PGA_944.csv'

        dfmean = pd.read_csv(fname, comment='#')
        imls = [float(re.sub('poe-', '', s)) for s in dfmean.columns if
                re.search('^poe', s)]

        dstore = dcache.get(str(TFF / 'data_calc/test_case01/job_all.ini'))
        mean = dstore['hcurves-stats'][0, 0, 0, :]
        afe = -np.log(1 - mean)

        # Convolution
        fname_c = os.path.join(TFF, 'data_calc', 'test_case01_convolution.ini')
        conf_conv = configparser.ConfigParser()
        conf_conv.read(fname_c)

        fname_s = os.path.join(TFF, 'data_calc', 'test_case01_sampling.ini')
        tmp_c = configparser.ConfigParser()
        tmp_c.read(fname_s)
        # Create a dictionary with the content of the file
        conf_sampl = {s: dict(tmp_c.items(s)) for s in tmp_c.sections()}

        # Compute sampling
        results = []
        file_path = TFF / 'data_calc'
        for nsam in NSAMPLES:

            print(f"\n   Number of samples: {nsam}")
            conf_sampl['analysis']['number_of_samples'] = f'{nsam}'
            conf_sampl['analysis']['conf_file_path'] = file_path

            tracemalloc.start()
            start_time = time.time()

            tmpdir = tempfile.mkdtemp()
            imls, afes, _ = propagate(conf_sampl, override_folder_out=tmpdir)

            # Mean and median from sampling
            mean_sampl = np.mean(np.sum(afes[0, :, :, 0], axis=0), axis=0)
            median_sampl = np.median(np.sum(afes[0, :, :, 0], axis=0), axis=0)
            tmp = np.sum(afes[0, :, :, 0], axis=0)
            pct_16 = np.percentile(tmp, 16, axis=0)
            pct_84 = np.percentile(tmp, 84, axis=0)

            exec_time = time.time() - start_time
            mem = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            results.append([nsam, exec_time, mem, mean_sampl, median_sampl,
                            pct_16, pct_84])

        # Compute convolution
        tracemalloc.start()
        start_time = time.time()

        tmpdir = tempfile.mkdtemp()
        conf_conv = {s: dict(conf_conv.items(s)) for s in conf_conv.sections()}
        conf_conv['analysis']['resolution'] = '100'
        conf_conv['analysis']['conf_file_path'] = file_path
        his, minp, nump, _ = propagate(conf_conv, override_folder_out=tmpdir)

        # Mean and median from convolution
        res_conv, idxs = get_stats([-1, 0.50, 0.16, 0.84], his, minp, nump)

        exec_time = time.time() - start_time
        mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        print(f"Execution time    : {exec_time}")
        print(f"Memory occupation : {mem}")

        if PLOTTING:

            fig, axs = plt.subplots(2, 2)
            fig.set_size_inches(10, 10)

            nsam = [row[0] for row in results]
            etim = [row[1] for row in results]
            memu = np.array([row[2] for row in results])

            plt.sca(axs[0, 0])
            plt.plot(nsam, etim, '-')
            plt.plot(nsam, etim, 'o', label='sampl')

            xlim = axs[0, 0].get_xlim()
            plt.hlines(exec_time, xlim[0], xlim[1], label='conv')

            plt.xlabel('Number of samples')
            plt.ylabel('Execution time [s]')
            plt.grid(which='major', ls='--', color='grey')
            plt.grid(which='minor', ls=':', color='lightgrey')
            plt.legend()

            plt.sca(axs[1, 0])
            plt.plot(nsam, memu[:, 0] / (1024 * 1024), '-')
            lab = 'sampl - size'
            plt.plot(nsam, memu[:, 0] / (1024 * 1024), 'o',  label=lab)
            plt.plot(nsam, memu[:, 1] / (1024 * 1024), '-')
            lab = 'sampl - peak'
            plt.plot(nsam, memu[:, 1] / (1024 * 1024), 'x',  label=lab)

            xlim = axs[1, 0].get_xlim()
            lab = 'conv - size'
            plt.hlines(mem[0] / (1024 * 1024), xlim[0], xlim[1], label=lab)
            lab = 'conv - peak'
            plt.hlines(mem[1] / (1024 * 1024), xlim[0], xlim[1], label=lab)

            plt.xlabel('Number of samples')
            plt.ylabel('Memory consumption [MB]')
            plt.grid(which='major', ls='--', color='grey')
            plt.grid(which='minor', ls=':', color='lightgrey')
            plt.legend()

            plt.sca(axs[0, 1])
            for row in results:
                ratio = row[3] / afe
                plt.plot(imls['PGA'], ratio, label=f'# sampl {row[0]}')

            ratio = res_conv[:, 0] / afe
            plt.plot(imls['PGA'], ratio, label='conv')

            plt.xlabel('IMT [g]')
            plt.ylabel('Ratio')
            plt.xscale('log')
            plt.yscale('log')
            plt.grid(which='major', ls='--', color='grey')
            plt.grid(which='minor', ls=':', color='lightgrey')
            plt.legend()

            plt.sca(axs[1, 1])
            plt.plot(imls['PGA'], afe, lw=2, label='oq')
            for row in results:
                plt.plot(imls['PGA'], row[3], label=f'# sampl {row[0]}')

            plt.plot(imls['PGA'], res_conv[:, 0], label='conv')

            plt.xlabel('IML [g]')
            plt.ylabel('Annual Frequency of Exceedance')
            plt.xscale('log')
            plt.yscale('log')
            plt.grid(which='major', ls='--', color='grey')
            plt.grid(which='minor', ls=':', color='lightgrey')
            plt.legend()

            """
            plt.sca(axs[2])
            idx = 6
            for row in results:
                ratio = row[idx]/results[-1][idx]
                plt.plot(imls['PGA'], ratio, label=f'# sampl {row[0]}')
            ratio = res_conv[:, 3]/results[-1][idx]
            plt.plot(imls['PGA'], ratio, label='conv')
            plt.xlabel('IMT [g]')
            plt.ylabel('Ratio')
            plt.xscale('log')
            plt.yscale('log')
            plt.grid(which='major', ls='--', color='grey')
            plt.grid(which='minor', ls=':', color='lightgrey')
            plt.legend()
            """

            plt.tight_layout()
            plt.savefig(TFF / 'figs' / 'test01_performance.png')
