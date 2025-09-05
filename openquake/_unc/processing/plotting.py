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

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

from openquake._unc.bins import get_bins_from_params
from openquake._unc.utils import weighted_percentile
from openquake._unc.hazard_pmf import afes_matrix_from_dstore


def _prepare_plot():
    mpl.rc('image', cmap='jet')
    fig, axs = plt.subplots(1, 1)
    fig.set_size_inches(10, 6)
    return fig, axs


def plot_results(fhis, fmin_pow, fnum_pow, res, analysis, axs):
    """
    Plot the results of the uncertainty propagation

    :param fhis:
    :param fmin_pow:
    :param fnum_pow:
    :param res:
    :param srcids:
    :param datastores:
    :return:
        Two handles for the figure and the axes
    """

    dstores = analysis.dstores
    for k, sid in enumerate(dstores):
        imls, afes, weights = afes_matrix_from_dstore(
            dstores[sid], 'PGA', False)
        imls = np.array(imls)
        for j in range(afes.shape[0]):
            idx = afes[j, :] > 1e-8
            plt.plot(imls[idx], afes[j, idx], '--', color='lightblue', lw=0.5)

    prc16 = []
    prc84 = []
    prc95 = []
    prc05 = []
    prc50 = []
    for iml, his, mpow, npow in zip(imls, fhis, fmin_pow, fnum_pow):

        bins = get_bins_from_params(mpow, res, npow)
        mids = bins[:-1]+np.diff(bins)/2

        axs.scatter(np.ones_like(mids)*iml, mids, marker='s', c=his, s=1.0,
                    vmin=0, vmax=0.05)
        mean = np.average(mids, weights=his)

        prc84.append(weighted_percentile(mids, weights=his, perc=0.84))
        prc16.append(weighted_percentile(mids, weights=his, perc=0.16))
        prc95.append(weighted_percentile(mids, weights=his, perc=0.95))
        prc05.append(weighted_percentile(mids, weights=his, perc=0.05))
        prc50.append(weighted_percentile(mids, weights=his, perc=0.50))

        axs.plot(iml, mean, 'ok', mfc='None')

    axs.plot(imls, prc16, '--', color='red')
    axs.plot(imls, prc84, '--', color='red')
    axs.plot(imls, prc95, '--', color='purple', lw=1)
    axs.plot(imls, prc05, '--', color='purple', lw=1)
    axs.plot(imls, prc50, 'dk', mfc='None')
