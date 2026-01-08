# --------------- POINT - Propagation Of epIstemic uNcerTainty ----------------
# Copyright (C) 2026 GEM Foundation
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
import os
import pathlib
import unittest
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import EngFormatter

from openquake.calculators.base import dcache
from openquake._unc.convolution import HistoGroup
from openquake._unc.hazard_pmf import afes_matrix_from_dstore

# This file folder
TFF = pathlib.Path(__file__).parent.resolve()

# Testing
aae = np.testing.assert_almost_equal
aac = np.testing.assert_allclose

# Options
PLOTTING = 0
CLOSE_TO_ONE = 0.99999999999


def _test(dstore):
    # Single source disaggregation
    oqp = dstore['oqparam']
    realizations = dstore['disagg-rlzs/Mag'][0, :, 0, 0, :]
    rmap = dstore['best_rlzs'][0]
    weights = dstore['weights'][:][rmap]
    mags = dstore['disagg-bins/Mag']
    mean_dsg = dstore['disagg-stats/Mag'][0, :, 0, 0, :]
    mean_dsg = np.squeeze(mean_dsg)

    # For each magnitude we compute the average rate of exceedance
    oute = np.zeros((realizations.shape[0]))
    idxe = []
    cnt = 0
    for imag in range(realizations.shape[0]):
        poes = realizations[imag, :]
        poes[poes > CLOSE_TO_ONE] = CLOSE_TO_ONE
        afes = -np.log(1.-poes)/oqp.investigation_time
        tmp = np.sum(afes*weights)
        oute[imag] = tmp
        # This contains the indexes of the bins where the AfE is larger than 0
        if tmp > 0.0:
            idxe.append(cnt)
        cnt += 1

    # Set parameters
    imt = 'PGA'
    atype = 'm'
    res = 300
    iii = np.arange(0, realizations.shape[-1])

    # Read realizations and get the histogram (the one that we would use for
    # propagating epistemic uncertainties)
    _, afes, weights = afes_matrix_from_dstore(
            dstore, imtstr=imt, info=False, rlzs=iii, atype=atype)
    h = HistoGroup.new(afes, weights, res)

    # Get statistics out of the histogram. Mean and median
    hists = h.get_stats([-1, 0.50])

    # Check the sum of the AfE computed with the histograms and the
    # results computed from the various realisations
    print('')
    print('AfE from OQ rlzs  :', np.sum(oute[idxe]))
    print('AfE from unc hist :', np.sum(hists[:, 0]))
    tmp = np.sum(-np.log(1.-mean_dsg)/oqp.investigation_time)
    print('AfE from OQ mean  :', tmp)
    aac(np.sum(oute[idxe]), np.sum(hists[:, 0]), atol=1e-4, rtol=1e-4)

    # Check that mean disaggregation from histogram and realisation matches
    aac(hists[:, 0], oute[idxe], atol=1e-6, rtol=1e-3)

    # Plot results
    if PLOTTING:
        plot_comparison(hists, oute, idxe, mags, mean_dsg, oqp)


class SingleSourceTestCase(unittest.TestCase):

    def test_m_convolution_source_a(self):
        # Convolution m test case - source a
        # This is the disaggregation just for source a of the total hazard
        # i.e. source a + source b contributions
        dstore = dcache.get(os.path.join(TFF, 'data_calc', 'disaggregation',
                                         'test_case00', 'job_a.ini'))
        _test(dstore)

    def test_m_convolution_source_b(self):
        # Convolution m test case - source b
        # This is the disaggregation just for source a of the total hazard
        # i.e. source a + source b contributions
        dstore = dcache.get(os.path.join(TFF, 'data_calc', 'disaggregation',
                                         'test_case00', 'job_b.ini'))
        _test(dstore)

    def test_m_convolution_source_only_b(self):
        # Convolution m test case - source b only
        # This is the disaggregation just for source a of the hazard from
        # source b contributions
        dstore = dcache.get(os.path.join(TFF, 'data_calc', 'disaggregation',
                                         'test_case00', 'job_b_only.ini'))
        _test(dstore)


def plot_comparison(hists, oute, idxe, mags, mean, oqp):
    fig, axes = plt.subplots(1, 2)
    fig.set_size_inches(10, 6)
    fig.suptitle('Comparison between the AfE computed')

    # Centres of bins
    magc = mags[:-1] + np.diff(mags)/2

    plt.sca(axes[0])
    plt.plot(hists[:, 0], oute[idxe], 'o', label='oq mean from rlzs')
    plt.plot(hists[:, 0], mean[idxe], 'o', label='oq mean', mfc='none',
             mec='green')
    tmp = []
    for i in range(len(idxe)):
        plt.text(hists[i, 0], oute[idxe[i]], f'{i}', fontsize=8)
        tmp.append([magc[idxe[i]], hists[i, 0], oute[idxe[i]]])
    xlim = axes[0].get_xlim()
    ylim = axes[0].get_ylim()
    mn = np.min([xlim[0], ylim[0]])
    mx = np.max([xlim[1], ylim[1]])
    plt.plot([mn, mx], [mn, mx], '--r')

    params = {'mathtext.default': 'regular'}
    plt.rcParams.update(params)

    ticker = EngFormatter(unit='')
    ticker.ENG_PREFIXES = {i: f"10$^{{{i:d}}}$" if i else ""
                           for i in range(-24, 25, 3)}

    axes[0].yaxis.set_major_formatter(ticker)
    axes[0].xaxis.set_major_formatter(ticker)
    plt.grid(which='major', ls='--', color='grey')
    plt.xticks(fontsize=8)
    plt.yticks(fontsize=8)
    plt.xlabel('upro')
    plt.ylabel('oq')
    plt.legend()

    # Second plot
    plt.sca(axes[1])
    tmp = np.array(tmp)
    afes = -np.log(1.-mean)/oqp.investigation_time
    plt.bar(tmp[:, 0], tmp[:, 1], width=0.08, fc='green', ec='blue', alpha=0.5,
            label='uncp')
    plt.bar(magc, afes, width=0.1, fc='none', ec='red', label='oq mean', lw=2)
    plt.bar(tmp[:, 0], tmp[:, 2], width=0.1, fc='none', ec='purple',
            label='rlzs', hatch='\\', alpha=0.5)
    plt.legend()
    plt.show()
